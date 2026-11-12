#!/usr/bin/env python3
"""C3 comparator full testbench (WO-48, D74; DESIGN.md section 6). Sandbox only.

    python c3_tb.py gen OUTDIR       # one dir + deck.sp + meta.json per deck, OUTDIR/jobs.txt for scripts/lpool.sh
    python c3_tb.py collect OUTDIR   # parse deck.log -> OUTDIR/c3_tb.json + summary, exit 1 if any deck is off expectation
    C3_SMOKE=1 python c3_tb.py gen OUTDIR   # tiny decks (2 cycles, 2 MC instances, 2 bisection steps): syntax smoke only

Deck families (each row ACCEPT/REJECT; every row has a broken copy that must REJECT):
  cyc  : full fs cycles referenced to the C9 48 MHz clk (capture = next fs_tick = clk edge). x2 from a behavioural
         OTA2 node (ideal step at phiI start through R_X2 / C_X2), strobe phiC in phiS (D74). Rows T1 polarity,
         T2 decision time (requirement), T7 memory, T10 capture window + glitch, T10nz (near-zero: q/qb never both
         high at capture), T9 current (report). Broken: qswap (T1), weak strobe 0.6 V (T2), strobe in phiI (T10),
         nolatch (T10nz), nobuf (T7).
  one  : single fire from reset at constant x2 (WO-44 spot conditions). Rows T5 kickback (diff peak / recovery at
         both edges, CM reported), T2band (ss/-40/1.62, 4 MHz: t_dec(1 mV) within [0.5, 3] x the WO-44 spot value).
         Variant asym (+-10 % R/C per side). Broken: starve (T2band), cl10 (T5).
  st   : T8 device stress, both power-up orders, x2 0..3.6 V and -0.5 V. Broken: in18 (input pair 1.8 V).
  mc   : T3 offset MC at the D74 basis (tt_mm / ss_mm + injected HV-pair dVT 7.6 mV*um so the HV pair totals 12),
         25 instances per deck, bisection inside ngspice. Broken: pair mismatch x3 (A_VT 36 total).
Numerical rules: gear, reltol 1e-5, tmax 1 ps on every decision deck (stress: 5 ps), 10 ohm on ideal sources,
tstop reached, every measurement present, temperature and VDPWR read back from the run (WORKFLOW 11.1-3).
Ideal parts: only stimulus sources, the behavioural x2 R/C, and labelled probes (Bqm, Btmp, VOS injection).
"""
import json, math, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netlist import comp_subckt, devices  # noqa: E402
from sizes_draft import (C_Q_LOAD, MUTS, SIZES, NF, PF, HVN, SIGMA_OS_HAND, AVT_TOTAL_HV,  # noqa: E402
                         AVT_TT_MM_HV, TDEC_SPOT_SS40)

LIB = os.path.join(os.environ.get("PDK_ROOT", "/home/mempool/.ciel"), os.environ.get("PDK", "sky130A"),
                   "libs.tech/ngspice/sky130.lib.spice")
SPICEINIT = "set ngbehavior=hsa\nset skywaterpdk\nset ng_nomodcheck\nset num_threads=1\n"
OPTS = ".options method=gear reltol=1e-5 vntol=1e-9 abstol=1e-14"
SMOKE = os.environ.get("C3_SMOKE") == "1"
F_CLK = 48e6                      # TT clk (SPEC 3.8a); fs = clk/12 (4 MHz) or clk/24 (2 MHz)
T_SU, T_H = 1e-9, 1e-9            # capture-flop setup / hold allowance (F-IF-1, SDC 1 ns); window adds 1 ns each side
RX2 = {4e6: 20e3, 2e6: 46e3}      # OTA2 closed-loop output resistance (DESIGN.md 3.4)
C_X2 = 0.7e-12
OS_MAX = 60e-3                    # SPEC row 105 after D75 (WO-51): |mu| + 3 sigma <= 60 mV, loop-derived (DESIGN.md 3.1b)
KICK_MAX, KICK_REC = 5e-3, 0.5e-3 # SPEC row 108
V18_MAX, VHV_MAX = 1.98, 5.5      # D40 / HV gate oxide (never loosened)
SR_X2 = 27e6                      # V/s, OTA2 boost slew (SPEC OTA2 row), applied per side (conservative: diff SR)
# T5 asymmetry (WO-51 item 3): gate = per-side R +-5 % (OTA2 closed-loop gm mismatch), C +-1 % (MIM + routing);
# the +-10 % R/C of WO-48 stays as an info copy.
ASYM = {"real": (0.05, 0.01), "x10": (0.10, 0.10)}
# per-device offset sensitivity (WO-51 item 1): device -> PDK mismatch probe type
SENS = [("M1", "hv"), ("M3", "ln"), ("M5", "lp"), ("R0", "rs"), ("R2", "rs"), ("Bo1n", "bn"), ("Bo1p", "rs")]
SENS_DV = 5e-3
PDK_TYPES = {  # type: (model, W, L, m, I_bias, nmos) -- probe bias near each device's operating density
    "hv": (HVN, 5.0, 0.5, 4, 10e-6, True), "ln": (NF, 4.0, 0.5, 1, 4e-6, True), "lp": (PF, 4.0, 0.5, 1, 2e-6, False),
    "rs": (PF, 1.0, 0.15, 1, 1e-6, False), "bn": (NF, 0.5, 0.15, 1, 0.5e-6, True)}
PDK_N = 60
PVT9 = [("tt", 27, 1.80), ("ss", -40, 1.62), ("ss", 125, 1.62), ("ff", -40, 1.98), ("ff", 125, 1.98),
        ("sf", -40, 1.62), ("sf", 125, 1.98), ("fs", -40, 1.62), ("fs", 125, 1.98)]
SS40 = ("ss", -40, 1.62)
# cycle sequence: signs alternate every cycle (a wrong-phase strobe then reads the previous x2 and flips sign)
SEQ = [(+0.3, "big"), (-0.5e-3, "t7"), (+1e-3, "t1"), (-0.3, "big"), (+0.5e-3, "t7"), (-1e-3, "t1"),
       (+1e-6, "nz"), (-1e-6, "nz")]
if SMOKE:
    SEQ = SEQ[:2]
MC_PER, MC_STEPS, MC_RANGE = (2, 2, 0.2) if SMOKE else (25, 12, 0.2)   # +-200 mV, 0.1 mV (WO-48 clipped at 40)
MC_GROUPS = {  # name: (lib corner, temp, vdd, decks, A_VT total of the HV pair, expect)
    "mc_tt": ("tt_mm", 27, 1.80, 8, AVT_TOTAL_HV, "pass"),
    "mc_ss40": ("ss_mm", -40, 1.62, 2, AVT_TOTAL_HV, "pass"),
    "mc_brk_x6": ("tt_mm", 27, 1.80, 2, 6 * AVT_TOTAL_HV, "reject"),   # x3 (~62 mV) no longer exceeds 60 mV
    "mc_info_x3": ("tt_mm", 27, 1.80, 2, 3 * AVT_TOTAL_HV, "info"),
}
MC_MIN = {"mc_tt": 200, "mc_ss40": 50, "mc_brk_x6": 50, "mc_info_x3": 50}
MC_SEED = {"mc_tt": 1000, "mc_ss40": 2000, "mc_info_x3": 3000, "mc_brk_x6": 4000}


def _f(x):
    return f"{x:.6e}"


def tim(fs):
    T = 1 / fs
    n = round(F_CLK / fs)
    assert abs(n / F_CLK - T) < 1e-15
    return T, 0.05 * T, 0.45 * T, 2 / F_CLK      # period, I/S gap g, t_half, T0 (cycle 0 starts on a clk edge)


def _pwl(pts):
    return "PWL(" + " ".join(f"{_f(t)} {v:.9f}" for t, v in pts) + ")"


def _hdr(title, corner, temp, mut):
    return [f"* {title}", f".lib {LIB} {corner}", f".temp {temp}",
            comp_subckt(mut=mut if mut in MUTS else "").rstrip(), OPTS]


def _echo(names):
    return [f'echo "RES {n} $&{n}"' for n in names]


def _ic(inst, vdd, mut, q0=0):
    if mut == "nolatch":
        return []
    return [f".ic v({inst}.ql)={q0 * vdd} v({inst}.qlb)={(1 - q0) * vdd}"]


# ---------------------------------------------------------------- cyc
def cyc_deck(corner, temp, vdd, vcm, fs, mut=""):
    T, g, th, T0 = tim(fs)
    R, N = RX2[fs], len(SEQ)
    vck = 0.6 if mut == "weak" else vdd
    pts, prev = [(0.0, 0.0)], 0.0
    for n, (d, _) in enumerate(SEQ):
        tn = T0 + n * T
        pts += [(tn + g, prev), (tn + g + 2e-9, d)]
        prev = d
    ck, fires, fnom = [(0.0, 0.0)], [], []
    for n in range(N):
        tn = T0 + n * T
        r, f = (tn + g + 1e-9, tn + T / 2 - g / 2) if mut == "phase" else (tn + T / 2 + g + 1e-9, tn + T - g / 2)
        ck += [(r, 0.0), (r + 0.1e-9, vck), (f, vck), (f + 0.1e-9, 0.0)]
        fires.append(r + 0.05e-9)
        fnom.append(tn + T / 2 + g + 1.05e-9)
    tstop = T0 + N * T + T / 2 + g + 1e-9
    tdmax = 0.3 * th
    L = _hdr(f"C3 cyc {corner}/{temp}/{vdd} cm {vcm} fs {fs:g} mut {mut}", corner, temp, mut) + [
        f"VDDS vdds 0 {vdd}", "RVDD vdds vdd 10", "CDD vdd 0 2p",
        f"VCLK clkr 0 {_pwl(ck)}", "RCLK clkr clk 10",
        f"VXP sxp 0 {_pwl([(t, vcm + d / 2) for t, d in pts])}", f"RXP sxp x2p {R}", f"CXP x2p 0 {C_X2}",
        f"VXN sxn 0 {_pwl([(t, vcm - d / 2) for t, d in pts])}", f"RXN sxn x2n {R}", f"CXN x2n 0 {C_X2}",
        "XC x2p x2n clk q qb vdd 0 c3_comp", f"CQ q 0 {C_Q_LOAD}", f"CQB qb 0 {C_Q_LOAD}",
        "Bqm qm 0 V=min(v(q),v(qb))", "Btmp tmp 0 V=temper"] + _ic("xc", vdd, mut) + [
        ".save v(q) v(qb) v(qm) v(vdd) v(tmp) v(clk) vdds#branch", ".control", f"tran 5p {_f(tstop)} 0 1p"]
    names = []
    for n, (d, kind) in enumerate(SEQ):
        cap = T0 + (n + 1) * T
        w0, w1 = cap - T_SU - 1e-9, cap + T_H + 1e-9
        g0, g1 = fnom[n] + tdmax, min(fnom[n + 1] if n + 1 < N else tstop, tstop)
        if kind != "nz":
            L.append(f"meas tran tq{n} when v(q)={vdd / 2} cross=1 td={_f(fires[n])}")
            names.append(f"tq{n}")
        for v, tag in (("q", "q"), ("qb", "b")):
            L += [f"meas tran {tag}mn{n} min v({v}) from={_f(w0)} to={_f(w1)}",
                  f"meas tran {tag}mx{n} max v({v}) from={_f(w0)} to={_f(w1)}",
                  f"meas tran g{tag}mn{n} min v({v}) from={_f(g0)} to={_f(g1)}",
                  f"meas tran g{tag}mx{n} max v({v}) from={_f(g0)} to={_f(g1)}"]
            names += [f"{tag}mn{n}", f"{tag}mx{n}", f"g{tag}mn{n}", f"g{tag}mx{n}"]
        L.append(f"meas tran bh{n} max v(qm) from={_f(w0)} to={_f(w1)}")
        names.append(f"bh{n}")
    L += [f"meas tran vddav avg v(vdd) from=10n to={_f(tstop)}", "meas tran tempr find v(tmp) at=1n",
          f"meas tran qdd integ i(vdds) from=0 to={_f(tstop)}", "let tend = vecmax(time)"]
    L += _echo(names + ["vddav", "tempr", "qdd", "tend"]) + [".endc", ".end"]
    meta = dict(fam="cyc", corner=corner, temp=temp, vdd=vdd, vcm=vcm, fs=fs, mut=mut, fires=fires, tstop=tstop)
    return "\n".join(L) + "\n", meta


# ---------------------------------------------------------------- one (kickback, T2 band)
def one_deck(corner, temp, vdd, vcm, fs, mut="", asym=""):
    T, g, th, T0 = tim(fs)
    R = RX2[fs]
    C = C_X2 / 10 if mut == "cl10" else C_X2
    dr, dc = ASYM[asym] if asym else (0.0, 0.0)
    rp, cp, rn, cn = (1 + dr) * R, (1 + dc) * C, (1 - dr) * R, (1 - dc) * C
    tf, dlt = 20e-9, 1e-3
    tr = tf + th
    tstop = tr + th / 2 + 6e-9
    L = _hdr(f"C3 one {corner}/{temp}/{vdd} fs {fs:g} mut {mut} asym {asym}", corner, temp, mut) + [
        f"VDDS vdds 0 {vdd}", "RVDD vdds vdd 10", "CDD vdd 0 2p",
        f"VCLK clkr 0 PULSE(0 {vdd} {_f(tf)} 0.1n 0.1n {_f(th - 0.1e-9)} {_f(T)})", "RCLK clkr clk 10",
        f"VXP sxp 0 {vcm + dlt / 2:.9f}", f"RXP sxp x2p {rp}", f"CXP x2p 0 {cp}",
        f"VXN sxn 0 {vcm - dlt / 2:.9f}", f"RXN sxn x2n {rn}", f"CXN x2n 0 {cn}",
        "XC x2p x2n clk q qb vdd 0 c3_comp", f"CQ q 0 {C_Q_LOAD}", f"CQB qb 0 {C_Q_LOAD}",
        f"Bkd kd 0 V=abs(v(x2p)-v(x2n)-({dlt:.9f}))", f"Bkc kc 0 V=abs((v(x2p)+v(x2n))/2-{vcm})",
        "Btmp tmp 0 V=temper"] + _ic("xc", vdd, mut) + [".control", f"tran 5p {_f(tstop)} 0 1p",
        f"meas tran tq when v(q)={vdd / 2} rise=1 td={_f(tf)}",
        f"meas tran q_end find v(q) at={_f(tr - 1e-9)}", f"meas tran qb_end find v(qb) at={_f(tr - 1e-9)}",
        f"meas tran kpk1 max v(kd) from={_f(tf)} to={_f(tr)}", f"meas tran krec1 find v(kd) at={_f(tf + th / 2)}",
        f"meas tran kpk2 max v(kd) from={_f(tr)} to={_f(tstop)}", f"meas tran krec2 find v(kd) at={_f(tr + th / 2)}",
        f"meas tran kcm max v(kc) from={_f(tf)} to={_f(tstop)}",
        f"meas tran kcr1 find v(kc) at={_f(tf + th / 2)}", f"meas tran kcr2 find v(kc) at={_f(tr + th / 2)}",
        f"meas tran vddav avg v(vdd) from=1n to={_f(tstop)}", "meas tran tempr find v(tmp) at=1n",
        "let tend = vecmax(time)"]
    L += _echo(["tq", "q_end", "qb_end", "kpk1", "krec1", "kpk2", "krec2", "kcm", "kcr1", "kcr2", "vddav", "tempr",
                "tend"]) + [".endc", ".end"]
    meta = dict(fam="one", corner=corner, temp=temp, vdd=vdd, vcm=vcm, fs=fs, mut=mut, asym=asym,
                fires=[tf + 0.05e-9], tstop=tstop)
    return "\n".join(L) + "\n", meta


# ---------------------------------------------------------------- st (T8 stress)
def _slew_follow(events, tstop, fs, locked, dt=1e-9):
    """x2 per side from target events [(t, target)], slewing at SR_X2; locked: moves only in phiI (OTA2 integrates),
    held in phiS (OTA2 hold, strobe high), as the phase plan does (C4 section 1)."""
    T, g, th, _ = tim(fs)
    n = int(round(tstop / dt))
    v, out, tgt, k = 0.0, [], 0.0, 0
    for i in range(n + 1):
        t = i * dt
        while k < len(events) and events[k][0] <= t:
            tgt = events[k][1]
            k += 1
        ph = t % T
        if not locked or (g <= ph < g + th):
            v = min(tgt, v + SR_X2 * dt) if tgt > v else max(tgt, v - SR_X2 * dt)
        out.append((t, round(v, 9)))
    keep = [out[0]] + [out[i] for i in range(1, len(out) - 1)
                       if out[i][1] != out[i - 1][1] or out[i + 1][1] != out[i][1]] + [out[-1]]
    return keep


def st_deck(corner, temp, order, mut="", stim="slew"):
    """stim: 'slew' (gate) x2 at the OTA2 slew rate through R_X2/C_X2, moving only in phiI, strobe on the 4 MHz
    phase plan (phiS); 'async' (info) same slew but x2 also moves while the strobe is high; 'fast' (info) the WO-48
    stimulus (4.1 V in 20 ns through 10 ohm, free-running 100 ns strobe)."""
    vd, fs = 1.98, 4e6
    if stim == "fast":
        if order == "a":     # VAPWR (x2) first, VDPWR later
            vdp = [(0, 0), (300e-9, 0), (400e-9, vd)]
            x0 = [(0, 0), (100e-9, 0), (200e-9, 3.6)]
        else:                # VDPWR first, then x2
            vdp = [(0, 0), (100e-9, 0), (200e-9, vd)]
            x0 = [(0, 0), (300e-9, 0), (400e-9, 3.6)]
        xp = x0 + [(500e-9, 3.6), (720e-9, 3.6), (740e-9, -0.5), (900e-9, -0.5), (920e-9, -0.5), (1000e-9, -0.5),
                   (1050e-9, 1.5)]
        xn = x0 + [(500e-9, 3.6), (520e-9, -0.5), (720e-9, -0.5), (740e-9, 3.6), (900e-9, 3.6), (920e-9, -0.5),
                   (1000e-9, -0.5), (1050e-9, 1.5)]
        tstop = 1100e-9
        clk = "VCP cp 0 PULSE(0 1 50n 0.1n 0.1n 100n 250n)"
        rx, cx = "10", None
    else:
        tstop = 2700e-9
        if order == "a":
            vdp, t36 = [(0, 0), (400e-9, 0), (500e-9, vd)], 0.0
        else:
            vdp, t36 = [(0, 0), (100e-9, 0), (200e-9, vd)], 300e-9
        ev_p = [(t36, 3.6), (1250e-9, -0.5), (1800e-9, -0.5), (2250e-9, 1.5)]
        ev_n = [(t36, 3.6), (700e-9, -0.5), (1250e-9, 3.6), (1800e-9, -0.5), (2250e-9, 1.5)]
        xp = _slew_follow(ev_p, tstop, fs, stim == "slew")
        xn = _slew_follow(ev_n, tstop, fs, stim == "slew")
        T, g, th, _ = tim(fs)
        ck = [(0.0, 0.0)]
        for n in range(int(tstop / T) + 1):
            r, f = n * T + T / 2 + g + 1e-9, n * T + T - g / 2
            ck += [(r, 0.0), (r + 0.1e-9, 1.0), (f, 1.0), (f + 0.1e-9, 0.0)]
        clk = f"VCP cp 0 {_pwl([p for p in ck if p[0] <= tstop])}"
        rx, cx = str(RX2[fs]), C_X2
    L = _hdr(f"C3 stress {corner}/{temp} order {order} mut {mut} stim {stim}", corner, temp, mut) + [
        f"VDDS vdds 0 {_pwl(vdp)}", "RVDD vdds vdd 10", "CDD vdd 0 2p",
        clk, "Bclk clkr 0 V=v(vdd)*v(cp)", "RCLK clkr clk 10",
        f"VXP sxp 0 {_pwl(xp)}", f"RXP sxp x2p {rx}", f"VXN sxn 0 {_pwl(xn)}", f"RXN sxn x2n {rx}"] + (
        [f"CXP x2p 0 {cx}", f"CXN x2n 0 {cx}"] if cx else []) + [
        "XC x2p x2n clk q qb vdd 0 c3_comp", f"CQ q 0 {C_Q_LOAD}", f"CQB qb 0 {C_Q_LOAD}",
        "Btmp tmp 0 V=temper", ".control", f"tran 10p {_f(tstop)} 0 5p"]
    port = dict(inp="x2p", inn="x2n", clk="clk", q="q", qb="qb", vdd="vdd", vss="0")
    nd = lambda n: "0" if port.get(n) == "0" else f"v({port[n]})" if n in port else f"v(xc.{n})"
    names, devs = [], {}
    for (n, model, d, g_, s, b, _) in devices(mut=mut if mut in MUTS else ""):
        devs[n] = model
        for pr, (a, c) in (("dg", (d, g_)), ("gs", (g_, s)), ("ds", (d, s)), ("gb", (g_, b)), ("db", (d, b)),
                           ("sb", (s, b))):
            if a == c:
                continue
            v = f"st_{n.lower()}_{pr}"
            L.append(f"let {v} = vecmax(abs({nd(a)}-{nd(c)}))")
            names.append(v)
    L += ["meas tran tempr find v(tmp) at=1n", "let tend = vecmax(time)"]
    L += _echo(names + ["tempr", "tend"]) + [".endc", ".end"]
    meta = dict(fam="st", corner=corner, temp=temp, vdd=vd, order=order, mut=mut, stim=stim, devs=devs, tstop=tstop)
    return "\n".join(L) + "\n", meta


# ---------------------------------------------------------------- sens / pdk (T3 dominant device, WO-51 item 1)
def _bisect(L, n, vdd, steps, rng_v):
    """bisection on VDL{i} (DC on inp) for n instances; trip in mid{i}."""
    L += [".save " + " ".join(f"v(q{i})" for i in range(n)), ".control", "set curplot = new", "set scratch = $curplot"]
    for i in range(n):
        L += [f"let lo{i} = {-rng_v}", f"let hi{i} = {rng_v}", f"let mid{i} = 0"]
    for k in range(steps):
        L += [f"alter @vdl{i}[dc] = $&mid{i}" for i in range(n)]
        L += ["tran 2p 5n 0 1p"]
        L += [f"meas tran r{i} find v(q{i}) at=4.9n" for i in range(n)]
        L += [f'set s{i} = "$&r{i}"' for i in range(n)]
        L += ["set tp = $curplot", "setplot $scratch"]
        for i in range(n):
            L += [f"if $s{i} > {vdd / 2}", f"let hi{i} = mid{i}", "else", f"let lo{i} = mid{i}", "end",
                  f"let mid{i} = (lo{i} + hi{i}) / 2"]
        L += ["destroy $tp", f"echo \"RES step {k}\""]
    L += _echo([f"mid{i}" for i in range(n)]) + ['echo "RES done 1"', ".endc", ".end"]
    return L


def sens_deck(corner="tt", temp=27, vdd=1.8):
    """instance 0 nominal, instance j: SENS[j-1] device VT raised by SENS_DV (gate-series source)."""
    pert = [None] + [d for d, _ in SENS]
    L = [f"* C3 offset sensitivity {corner}/{temp}/{vdd} dv {SENS_DV}", f".lib {LIB} {corner}", f".temp {temp}"]
    for j, d in enumerate(pert):
        L.append(comp_subckt(name=f"c3_s{j}", dvt=None if d is None else {d: SENS_DV}).rstrip())
    L += [OPTS, f"VDDS vdds 0 {vdd}", f"VCLK clks 0 PULSE(0 {vdd} 0.3n 0.1n 0.1n 20n 40n)", "VCM cm 0 1.5"]
    for i in range(len(pert)):
        L += [f"RVDD{i} vdds vdd{i} 10", f"CDD{i} vdd{i} 0 2p", f"RCLK{i} clks clk{i} 10",
              f"VDL{i} dl{i} cm 0", f"RXP{i} dl{i} x{i}p 10", f"RXN{i} cm x{i}n 10",
              f"X{i} x{i}p x{i}n clk{i} q{i} qb{i} vdd{i} 0 c3_s{i}", f"CQ{i} q{i} 0 {C_Q_LOAD}",
              f"CQB{i} qb{i} 0 {C_Q_LOAD}"] + _ic(f"x{i}", vdd, "")
    L = _bisect(L, len(pert), vdd, 3 if SMOKE else 14, 0.04)
    return "\n".join(L) + "\n", dict(fam="sens", corner=corner, temp=temp, vdd=vdd, pert=pert, n=len(pert))


def pdk_deck(seed=5000):
    """tt_mm: PDK_N diode-connected instances per device type at its probe current; sigma(Vgs) per type."""
    n = 3 if SMOKE else PDK_N
    L = [f"* C3 PDK mismatch probe tt_mm seed {seed}", f".lib {LIB} tt_mm", ".temp 27", "VDD vdd 0 1.8"]
    names = []
    for t, (model, W, Lg, m, ib, nmos) in PDK_TYPES.items():
        for i in range(n):
            g = f"g{t}{i}"
            if nmos:
                L += [f"X{t}{i} {g} {g} 0 0 {model} W={W} L={Lg} nf=1 m={m}", f"I{t}{i} 0 {g} {ib}"]
            else:
                L += [f"X{t}{i} {g} {g} vdd vdd {model} W={W} L={Lg} nf=1 m={m}", f"I{t}{i} {g} 0 {ib}"]
            names.append((f"p_{t}_{i}", g, nmos))
    L += [OPTS, ".control", "op"]
    L += [f"let {v} = {'v(' + g + ')' if nmos else '1.8 - v(' + g + ')'}" for v, g, nmos in names]
    L += _echo([v for v, _, _ in names]) + ['echo "RES done 1"', ".endc", ".end"]
    return "\n".join(L) + "\n", dict(fam="pdk", seed=seed, n=n, types=list(PDK_TYPES))


# ---------------------------------------------------------------- mc (T3)
def mc_deck(group, j):
    corner, temp, vdd, _, avt, _ = MC_GROUPS[group]
    seed = MC_SEED[group] + j
    rng = random.Random(seed)
    a_inj = math.sqrt(avt ** 2 - AVT_TT_MM_HV ** 2)                     # mV*um on top of the PDK tt_mm draw
    p = SIZES["IN"]
    sig = math.sqrt(2) * a_inj * 1e-3 / math.sqrt(p["W"] * p["L"] * p["m"])  # differential, V
    vos = [rng.gauss(0, sig) for _ in range(MC_PER)]
    L = _hdr(f"C3 MC {group} deck {j} seed {seed} A_inj {a_inj:.2f} mV*um sig_inj {sig * 1e3:.3f} mV",
             corner, temp, "") + [
        f"VDDS vdds 0 {vdd}", f"VCLK clks 0 PULSE(0 {vdd} 0.3n 0.1n 0.1n 20n 40n)", "VCM cm 0 1.5"]
    for i in range(MC_PER):
        L += [f"RVDD{i} vdds vdd{i} 10", f"CDD{i} vdd{i} 0 2p", f"RCLK{i} clks clk{i} 10",
              f"VDL{i} dl{i} cm 0", f"RXP{i} dl{i} x{i}p 10", f"RXN{i} cm x{i}n 10",
              f"VOS{i} xi{i} x{i}p {vos[i]:.6e}",   # injected HV-pair dVT (D74 basis), labelled ideal source
              f"X{i} xi{i} x{i}n clk{i} q{i} qb{i} vdd{i} 0 c3_comp", f"CQ{i} q{i} 0 {C_Q_LOAD}",
              f"CQB{i} qb{i} 0 {C_Q_LOAD}"] + _ic(f"x{i}", vdd, "")
    L += [".save " + " ".join(f"v(q{i})" for i in range(MC_PER)), ".control", "set curplot = new",
          "set scratch = $curplot"]
    for i in range(MC_PER):
        L += [f"let lo{i} = {-MC_RANGE}", f"let hi{i} = {MC_RANGE}", f"let mid{i} = 0"]
    for k in range(MC_STEPS):
        L += [f"alter @vdl{i}[dc] = $&mid{i}" for i in range(MC_PER)]
        L += ["tran 2p 5n 0 1p"]
        L += [f"meas tran r{i} find v(q{i}) at=4.9n" for i in range(MC_PER)]
        L += [f'set s{i} = "$&r{i}"' for i in range(MC_PER)]
        L += ["set tp = $curplot", "setplot $scratch"]
        for i in range(MC_PER):
            L += [f"if $s{i} > {vdd / 2}", f"let hi{i} = mid{i}", "else", f"let lo{i} = mid{i}", "end",
                  f"let mid{i} = (lo{i} + hi{i}) / 2"]
        L += ["destroy $tp", f"echo \"RES step {k}\""]
    L += _echo([f"mid{i}" for i in range(MC_PER)]) + ['echo "RES done 1"', ".endc", ".end"]
    meta = dict(fam="mc", group=group, corner=corner, temp=temp, vdd=vdd, seed=seed, a_inj=a_inj,
                sig_inj=sig, vos=vos, n=MC_PER)
    return "\n".join(L) + "\n", meta


# ---------------------------------------------------------------- deck list
def deck_list():
    D = {}
    nm = lambda c, t, v: f"{c}{t:+d}_{int(round(v * 100))}"
    for c, t, v in PVT9:                                   # one: T5 at 9 PVT, T2band at ss40
        D[f"one_{nm(c, t, v)}"] = (one_deck, (c, t, v, 1.5, 4e6), {}, {"T5": "pass", **(
            {"T2band": "pass"} if (c, t, v) == SS40 else {})})
    D["one_ss40_2MHz"] = (one_deck, (*SS40, 1.5, 2e6), {}, {"T5": "pass"})
    D["one_ss40_asym"] = (one_deck, (*SS40, 1.5, 4e6), {"asym": "real"}, {"T5": "pass"})
    D["one_ss40_asym10"] = (one_deck, (*SS40, 1.5, 4e6), {"asym": "x10"}, {"T5": "info"})
    D["one_brk_starve"] = (one_deck, (*SS40, 1.5, 4e6), {"mut": "starve"}, {"T2band": "reject"})
    D["one_brk_cl10"] = (one_deck, (*SS40, 1.5, 4e6), {"mut": "cl10"}, {"T5": "reject"})
    for o in ("a", "b"):                                   # st: T8 (gate: OTA2 slew, phase plan)
        D[f"st_tt27_{o}"] = (st_deck, ("tt", 27, o), {}, {"T8": "pass"})
        D[f"st_ff-40_{o}"] = (st_deck, ("ff", -40, o), {}, {"T8": "pass"})
    D["st_brk_in18"] = (st_deck, ("tt", 27, "a"), {"mut": "in18"}, {"T8": "reject"})
    D["st_nocas_tt27_a"] = (st_deck, ("tt", 27, "a"), {"mut": "nocas"}, {"T8": "info"})   # rev b, gate stimulus
    for c, t, o in (("tt", 27, "a"), ("ff", -40, "b")):    # info copies
        D[f"st_fast_{c}{t}_{o}"] = (st_deck, (c, t, o), {"stim": "fast"}, {"T8": "info"})
        D[f"st_async_{c}{t}_{o}"] = (st_deck, (c, t, o), {"stim": "async"}, {"T8": "info"})
    D["sens_tt"] = (sens_deck, (), {}, {})
    D["pdk_tt"] = (pdk_deck, (), {}, {})
    for g, (_, _, _, nd, _, exp) in MC_GROUPS.items():    # mc: T3
        for j in range(1 if SMOKE else nd):
            D[f"{g}_{j}"] = (mc_deck, (g, j), {}, {"T3": exp})
    cyc_rows = {"T1": "pass", "T2": "pass", "T7": "pass", "T10": "pass", "T10nz": "pass"}
    for m, row in (("qswap", "T1"), ("weak", "T2"), ("phase", "T10"), ("nolatch", "T10nz"), ("nobuf", "T7")):
        D[f"cyc_brk_{m}"] = (cyc_deck, (*SS40, 1.5, 4e6), {"mut": m}, {row: "reject"})
    order = [SS40] + [p for p in PVT9 if p != SS40]
    for c, t, v in order:
        D[f"cyc_{nm(c, t, v)}"] = (cyc_deck, (c, t, v, 1.5, 4e6), {}, cyc_rows)
    D["cyc_ss40_cm12"] = (cyc_deck, (*SS40, 1.2, 4e6), {}, cyc_rows)
    D["cyc_ss40_cm18"] = (cyc_deck, (*SS40, 1.8, 4e6), {}, cyc_rows)
    D["cyc_ss40_2MHz"] = (cyc_deck, (*SS40, 1.5, 2e6), {}, cyc_rows)
    if SMOKE:
        keep = ("one_ss40_asym", "st_tt27_a", "st_async_tt27_a", "mc_tt_0", "sens_tt", "pdk_tt")
        D = {k: v for k, v in D.items() if k in keep}
    return D


def gen(out):
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    jobs = []
    for k, (fn, args, kw, exp) in deck_list().items():
        text, meta = fn(*args, **kw)
        meta["expect"] = exp
        d = os.path.join(out, k)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "deck.sp"), "w").write(text)
        open(os.path.join(d, ".spiceinit"), "w").write(
            SPICEINIT + (f"set rndseed={meta['seed']}\n" if meta["fam"] in ("mc", "pdk") else ""))
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
        if os.path.exists(os.path.join(d, "deck.log")):
            os.remove(os.path.join(d, "deck.log"))
        to = {"one": 1800, "st": 7200, "mc": 14400, "cyc": 21600, "sens": 3600, "pdk": 1800}[meta["fam"]]
        jobs.append(f"cd {d} && timeout {to} ngspice -b deck.sp > deck.log 2>&1")
    open(os.path.join(out, "jobs.txt"), "w").write("\n".join(jobs) + "\n")
    print(f"{len(jobs)} decks -> {out}/jobs.txt")


# ---------------------------------------------------------------- collect
def _res(log):
    r = {}
    if not os.path.exists(log):
        return r
    for ln in open(log, errors="replace"):
        m = re.match(r"RES (\w+) (\S+)", ln.strip())
        if m:
            try:
                r[m.group(1)] = float(m.group(2))
            except ValueError:
                r[m.group(1)] = None
    return r


def _sanity(r, m):
    bad = []
    if r.get("tend") is None or r["tend"] < m["tstop"] * (1 - 1e-6):
        bad.append("tend")
    if r.get("tempr") is None or abs(r["tempr"] - m["temp"]) > 0.01:
        bad.append("temp")
    if m["fam"] in ("cyc", "one") and (r.get("vddav") is None or abs(r["vddav"] / m["vdd"] - 1) > 0.02):
        bad.append("vdd")
    return bad


def eval_cyc(r, m):
    vdd, (T, g, th, T0) = m["vdd"], tim(m["fs"])
    hi, lo, tdmax = 0.9 * vdd, 0.1 * vdd, 0.3 * th
    rows = {k: [True, []] for k in ("T1", "T2", "T7", "T10", "T10nz")}
    have = lambda *ks: all(r.get(k) is not None for k in ks)
    tds = []

    def upd(row, ok, n, why):
        if not ok:
            rows[row][0] = False
            rows[row][1].append(f"c{n}:{why}")
    for n, (d, kind) in enumerate(SEQ):
        q0, q1, b0, b1 = (r.get(f"{t}{n}") for t in ("qmn", "qmx", "bmn", "bmx"))
        G = [r.get(f"{t}{n}") for t in ("gqmn", "gqmx", "gbmn", "gbmx")]
        if kind == "nz":
            ok = have(f"qmn{n}", f"qmx{n}", f"bmn{n}", f"bmx{n}", f"bh{n}") and r[f"bh{n}"] <= lo and (
                (q0 >= hi and b1 <= lo) or (q1 <= lo and b0 >= hi))
            upd("T10nz", ok, n, f"bh={r.get(f'bh{n}')}")
            continue
        up = d > 0
        pol = None not in (q0, q1, b0, b1) and ((q0 >= hi and b1 <= lo) if up else (q1 <= lo and b0 >= hi))
        upd("T7" if kind == "t7" else "T1", pol, n, "pol")
        gl = None not in G and ((G[0] >= hi and G[3] <= lo) if up else (G[1] <= lo and G[2] >= hi))
        upd("T10", pol and gl, n, "win" if not pol else "glitch")
        tq = r.get(f"tq{n}")
        td = None if tq is None else tq - m["fires"][n]
        tds.append(td)
        upd("T2", td is not None and 0 < td < tdmax, n, f"tdec={td}")
    info = dict(tdec_ns=[None if t is None else round(t * 1e9, 3) for t in tds],
                i_uA=None if r.get("qdd") is None else abs(r["qdd"]) / m["tstop"] * 1e6)
    return rows, info


def eval_one(r, m):
    rows = {}
    k = [r.get(x) for x in ("kpk1", "kpk2", "krec1", "krec2")]
    rows["T5"] = [None not in k and max(k[:2]) <= KICK_MAX and max(k[2:]) <= KICK_REC, []]
    tq = r.get("tq")
    td = None if tq is None else tq - m["fires"][0]
    rows["T2band"] = [td is not None and 0.5 * TDEC_SPOT_SS40 <= td <= 3 * TDEC_SPOT_SS40, [f"tdec={td}"]]
    info = dict(tdec_ns=None if td is None else round(td * 1e9, 3),
                kick_mV=[None if x is None else round(x * 1e3, 3) for x in k],
                cm_peak_mV=None if r.get("kcm") is None else round(r["kcm"] * 1e3, 2),
                cm_rec_mV=[None if r.get(x) is None else round(r[x] * 1e3, 3) for x in ("kcr1", "kcr2")])
    return rows, info


def eval_st(r, m):
    worst = {"18": (0.0, ""), "hv": (0.0, "")}
    miss = 0
    for n, model in m["devs"].items():
        cls = "hv" if "g5v0" in model else "18"
        for k, v in r.items():
            if k.startswith(f"st_{n.lower()}_"):
                if v is None:
                    miss += 1
                elif v > worst[cls][0]:
                    worst[cls] = (v, k)
    n_exp = sum(1 for x in open(m["deck"]) if x.startswith("let st_")) if "deck" in m else None
    n_got = sum(1 for k in r if k.startswith("st_") and r[k] is not None)
    ok = miss == 0 and n_got == n_exp and n_got > 0 and worst["18"][0] <= V18_MAX and worst["hv"][0] <= VHV_MAX
    return {"T8": [ok, [f"n={n_got}/{n_exp}"]]}, dict(max18=worst["18"], maxhv=worst["hv"])


def collect(out):
    out = os.path.abspath(out)
    res, lines, off = {}, [], 0
    mc, aux = {}, {}
    for k in sorted(os.listdir(out)):
        mp = os.path.join(out, k, "meta.json")
        if not os.path.exists(mp):
            continue
        m = json.load(open(mp))
        m["deck"] = os.path.join(out, k, "deck.sp")
        r = _res(os.path.join(out, k, "deck.log"))
        if m["fam"] == "mc":
            trips = [r.get(f"mid{i}") for i in range(m["n"])]
            mc.setdefault(m["group"], []).append((k, trips, r.get("done") == 1.0, m))
            continue
        if m["fam"] in ("sens", "pdk"):
            aux[m["fam"]] = (r, m)
            continue
        bad = _sanity(r, m)
        rows, info = {"cyc": eval_cyc, "one": eval_one, "st": eval_st}[m["fam"]](r, m)
        verd = {}
        for row, exp in m["expect"].items():
            ok = rows[row][0] and not bad
            verd[row] = "ACCEPT" if ok else "REJECT"
            if exp != "info" and (exp == "pass") != ok:
                off += 1
        res[k] = dict(verdict=verd, expect=m["expect"], sanity=bad, detail={x: rows[x][1][:4] for x in rows},
                      info=info)
        lines.append(f"{k:18s} " + " ".join(f"{x}={v}({m['expect'][x][0]})" for x, v in verd.items()) +
                     f" sanity={bad or 'ok'} info={info}" +
                     ("" if all(rows[x][0] for x in verd) else f" why={ {x: rows[x][1][:3] for x in verd} }"))
    # dominant device (WO-51 item 1): sensitivity d(trip)/d(VT) x PDK sigma(dVT) per device, plus the HV injection
    sig_est, contrib = float("nan"), {}
    if "sens" in aux and "pdk" in aux:
        (rs, ms), (rp, mp_) = aux["sens"], aux["pdk"]
        trips = [rs.get(f"mid{i}") for i in range(ms["n"])]
        sdv = {}
        for t in mp_["types"]:
            v = [rp.get(f"p_{t}_{i}") for i in range(mp_["n"])]
            v = [x for x in v if x is not None]
            mu_ = sum(v) / len(v) if v else float("nan")
            sdv[t] = math.sqrt(2) * math.sqrt(sum((x - mu_) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else float("nan")
        if rs.get("done") == 1.0 and None not in trips and rp.get("done") == 1.0:
            p = SIZES["IN"]
            s_inj = math.sqrt(2) * math.sqrt(AVT_TOTAL_HV ** 2 - AVT_TT_MM_HV ** 2) * 1e-3 / math.sqrt(p["W"] * p["L"] * p["m"])
            tot = 0.0
            for j, (d, t) in enumerate(SENS, start=1):
                s = (trips[j] - trips[0]) / SENS_DV
                contrib[d] = dict(sens=round(s, 4), sigma_dVT_mV=round(sdv[t] * 1e3, 3), contrib_mV=round(abs(s) * sdv[t] * 1e3, 3))
                tot += (s * sdv[t]) ** 2
            s1 = (trips[1] - trips[0]) / SENS_DV
            contrib["M1_inj"] = dict(sens=round(s1, 4), sigma_dVT_mV=round(s_inj * 1e3, 3), contrib_mV=round(abs(s1) * s_inj * 1e3, 3))
            tot += (s1 * s_inj) ** 2
            sig_est = math.sqrt(tot)
        lines.append(f"T3 sensitivity tt/27/1.8: trip0={None if trips[0] is None else round(trips[0] * 1e3, 4)}mV "
                     f"sigma_est={sig_est * 1e3:.2f}mV per device (|s|, sigma dVT, contribution): {contrib}")
        res["T3_sens"] = dict(sigma_est_mV=sig_est * 1e3, contrib=contrib, sigma_dVT_mV={t: x * 1e3 for t, x in sdv.items()})
    else:
        lines.append("T3 sensitivity: sens/pdk decks missing -> sigma_est NaN, plaus fails")
    for gname, decks in sorted(mc.items()):
        corner, temp, vdd, nd, avt, exp = MC_GROUPS[gname]
        vals = [t for (_, trips, done, _) in decks if done for t in trips if t is not None]
        clip = sum(1 for t in vals if abs(t) >= MC_RANGE * (1 - 2 ** -(MC_STEPS - 1)))
        n = len(vals)
        mu = sum(vals) / n if n else float("nan")
        sd = math.sqrt(sum((t - mu) ** 2 for t in vals) / (n - 1)) if n > 1 else float("nan")
        mx = max((abs(t) for t in vals), default=float("nan"))
        need = 4 if SMOKE else MC_MIN[gname]
        checks = dict(count=n >= need, clip=clip == 0, mu3s=n > 1 and abs(mu) + 3 * sd <= OS_MAX,
                      every=n > 0 and mx <= OS_MAX, plaus=n > 1 and 0.5 * sig_est <= sd <= 2 * sig_est)
        ok = all(checks.values())
        if exp != "info" and (exp == "pass") != ok:
            off += 1
        inj = [x for (_, _, _, m) in decks for x in m["vos"]]
        sinj = math.sqrt(sum(x * x for x in inj) / len(inj)) if inj else float("nan")
        res[gname] = dict(verdict={"T3": "ACCEPT" if ok else "REJECT"}, expect={"T3": exp}, n=n,
                          mu_mV=mu * 1e3, sigma_mV=sd * 1e3, max_mV=mx * 1e3, clipped=clip, checks=checks,
                          inj_rms_mV=sinj * 1e3, a_inj=decks[0][3]["a_inj"])
        lines.append(f"{gname:18s} T3={'ACCEPT' if ok else 'REJECT'}({exp[0]}) {corner}/{temp}/{vdd} n={n} "
                     f"mu={mu * 1e3:.3f}mV sigma={sd * 1e3:.3f}mV |mu|+3s={(abs(mu) + 3 * sd) * 1e3:.2f}mV "
                     f"max|x|={mx * 1e3:.2f}mV clip={clip} inj_rms={sinj * 1e3:.3f}mV "
                     f"(A_inj {decks[0][3]['a_inj']:.2f}) fail={[c for c, v in checks.items() if not v]}")
    lines.append("T4 noise (report only, REVIEW-C3a 6): hand sigma_n ~0.3-0.6 mV rms (gm 1 mS/side, t_int 0.1-0.3 ns)"
                 " vs 5 mV rms: ~10x margin; .noise is a poor proxy for a regenerative comparator.")
    lines.append(f"SUMMARY {'ACCEPT' if off == 0 else 'REJECT'} ({off} deck rows off expectation)")
    json.dump(res, open(os.path.join(out, "c3_tb.json"), "w"), indent=1, default=str)
    open(os.path.join(out, "summary.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if off else 0)


if __name__ == "__main__":
    {"gen": gen, "collect": collect}[sys.argv[1]](sys.argv[2])
