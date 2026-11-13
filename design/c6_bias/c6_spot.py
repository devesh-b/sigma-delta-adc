#!/usr/bin/env python3
"""C6 spot sims: current-mode bandgap reference core (Banba type), 3-bit trim copies, start-up.

WO-45 (C6a) deck, extended in WO-50 (C6b) and re-architected in WO-55 (C6c, robust start-up; DESIGN.md 6.6).
Stage-1 spot deck (not the final C6 netlist). Sandbox only (ngspice, sky130A via PDK_ROOT).

  python c6_spot.py tune OUT                       # tt/27: R2/R1 grid, slope-zero ratio -> OUT/tune.json
  python c6_spot.py jobs OUT JOBFILE               # job list for scripts/lpool.sh
  python c6_spot.py run OUT KIND CORNER TEMP VDD [MUT] [TR]
        KIND dct  = .dc temp -40..125 (master current, 8 trim-code copies, own current, detector levels)
             dcv  = .dc VDD 2.8..3.8 at TEMP (PSRR info)
             dci  = initial-state test: transient at fixed VDD from .ic all nodes = 0 and = VDD (uic, 300 us);
                    both must land on the one DC operating point
             tran = VAPWR PWL 0 -> VDD over TR seconds, uic (no .op), start-up
             loop = loop broken at the M5 gate (o1 -> o1x), .dc Vx 0..2 V: count every equilibrium (gated)
        MUT  none | nosu (kick removed) | early (bias_ok from the leaker detector only, Mk x16)
             | noskew (main-amp input pair un-skewed: the WO-50 core) | ptat (both R2 open) | trim_open (LSB leg open)
  python c6_spot.py summary OUT                    # verdict table -> stdout

Core (DESIGN.md 2): M1/M2 = 17 PMOS units from VG; Q1 1x / Q2 8x pnp; R1 in series with Q2; R2 from A and B to 0.
Amp: PMOS pair, NMOS mirror load, Cc on o1; M5 into the PMOS diode M6 on VG; Cvg 1 pF VG -> VDD.

WO-55 changes (DESIGN.md 6.6):
 * Built-in amp offset: mb (gate B, output side) is SKEW x wider than ma, so the amp balances at V_B - V_A = +Voff
   (~ n VT ln SKEW, PTAT-like). In the low-current region where both pnps are off, V_B - V_A ~ 0 < Voff, so the
   amp always drives the current UP: the only non-zero equilibrium is the operating point (loop-break gate).
 * Kick: while ok is low, a gate-0 PMOS chain (NKK units, ~I_lk, less than half the amp tail) pushes current
   into o1 through a PMOS switch (gate ok). It cannot overpower the amp, so no overshoot; off (gate VDD) after ok.
 * bias_ok from a pnp-on comparator: q high when V_B - V_C (= I_Q2 R1, ~0 while the pnps are off, ~55-90 mV at the
   operating point) exceeds the comparator's own built-in threshold (diode-side input CMP_SKEW x wider, ~nVT ln 3).
   Threshold and signal both come from the core, so bias_ok tracks the core state over VDD, corner and T.
   Default-low: Mqd (gate tsu, the WO-50 leaker detector, now only a "core off" flag) pulls q low while the master
   current is below I_lk / R_K. Hysteresis: one VG unit into q while ok is high.
"""
import json
import math
import os
import subprocess
import sys

LIB = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.tech/ngspice/sky130.lib.spice"
P5, N5 = "sky130_fd_pr__pfet_g5v0d10v5", "sky130_fd_pr__nfet_g5v0d10v5"
PNP, RX = "sky130_fd_pr__pnp_05v5_W3p40L3p40", "sky130_fd_pr__res_xhigh_po_0p69"
UW, UL = 0.42, 20.0            # PMOS unit (all VG-gated legs)
N_CORE, N_TAIL, N_M6 = 17, 8, 8
G0, GT, CODE_RESET = 17, 19.8, 4
NPNP = 8
R1_L = 94.0                    # um of 0p69 xhrpoly (WO-55: x1.15 vs WO-45 82 um, recentres I0 after the amp skew)
CC = float(os.environ.get("C6_CC", 3e-12))     # env overrides: WO-55 smoke variants only
CVG = 1e-12
VSENSE = 0.9                   # trim-copy drain sense voltage
TEMPS = (-40, 27, 125)
CORNERS = ("tt", "ss", "ff", "sf", "fs")
DCT = [("tt", 3.3), ("ss", 3.0), ("ff", 3.6), ("fs", 3.0), ("sf", 3.0)]
TRAN = [("tt", 27, 3.3)] + [(c, t, 3.0) for c in CORNERS for t in (-40, 125)]
TRS = (1e-6, 1e-2)
LIM_TC, LIM_STEP = 0.03, 0.06
EPS_TRIM, RESID = 0.19, 0.03
COVER = (1 + EPS_TRIM) / (1 - EPS_TRIM) * (1 - RESID) / (1 + RESID)
# WO-55 start-up
SKEW = 2.0                     # main amp: mb W = 4 * SKEW (built-in Voff, V_B > V_A at balance)
CMP_SKEW = 3.0                 # pnp-on comparator: diode-side input (gate B) W = 4 * CMP_SKEW
N_CT = 8                       # comparator tail units from VG
NKK = int(os.environ.get("C6_NKK", 8))         # kick chain: NKK x unit PMOS in series, gate 0
NLK = 8                        # core-off leaker: NLK x unit PMOS in series, gate 0
MN_W, MN_L = 2.0, 4.0          # master NMOS diode
MK_W, MK_L = 1.05, 4.0         # Mk: R_K = 0.525 -> core-off flag clears at I_lk / 0.525
R_K = (MK_W / MK_L) / (MN_W / MN_L)
# gates
TSET, LIM_SU = 10e-6, 0.01     # within +-1 % of DC from end of ramp + 10 us to the end
IOK_MIN = 0.5                  # bias_ok's final assertion only with I >= 50 % of DC
IDC_MIN = 0.75e-6              # separator good / low state
THR_MAX = 0.8                  # core-off flag must be clear at the operating point: I_lk / (R_K I) <= 0.8
DCI_AGREE, DCI_P2P, DCI_OP = 0.005, 0.005, 0.01
LOOP_IMIN = 0.02e-6            # loop gate: no equilibrium between this and 0.9 I_good; exactly one stable above


def x(name, d, g, s, b, dev, w, l, m=1):
    return f"X{name} {d} {g} {s} {b} {dev} w={w:g} l={l:g} m={m}"


def deck(kind, corner, temp, vdd, mut="none", tr=1e-6, ratio=4.6, out="o.csv", init=None):
    r2l = R1_L * ratio
    L = [f"* c6_spot {kind} {corner} {temp} {vdd} {mut} {tr:g} ratio {ratio:.4f} init {init}", f".lib {LIB} {corner}",
         ".option gmin=1e-15 reltol=1e-5 abstol=1e-14"]
    L.append(f"Vdd vdd 0 pwl(0 0 10n 0 {10e-9 + tr:.6g} {vdd})" if kind == "tran" else f"Vdd vdd 0 {vdd}")
    if kind != "dct":
        L.append(f".temp {temp}")
    nn = ["a", "b", "c", "t", "n1", "o1", "vg", "vn", "mo", "tsu", "ok", "sua"]
    # core
    L += [x("m1", "a", "vg", "vdd", "vdd", P5, UW, UL, N_CORE), x("m2", "b", "vg", "vdd", "vdd", P5, UW, UL, N_CORE),
          f"Xq1 0 0 a {PNP} m=1", f"Xq2 0 0 c {PNP} m={NPNP}", f"Xr1 b c 0 {RX} l={R1_L:.4g}"]
    if mut != "ptat":
        L += [f"Xr2a a 0 0 {RX} l={r2l:.4g}", f"Xr2b b 0 0 {RX} l={r2l:.4g}"]
    sk = 1.0 if mut == "noskew" else SKEW
    g5 = "o1x" if kind == "loop" else "o1"
    L += [x("mt", "t", "vg", "vdd", "vdd", P5, UW, UL, N_TAIL),
          x("ma", "n1", "a", "t", "t", P5, 4, 4), x("mb", "o1", "b", "t", "t", P5, 4 * sk, 4),
          x("ml1", "n1", "n1", "0", "0", N5, 1, 8), x("ml2", "o1", "n1", "0", "0", N5, 1, 8),
          f"Cc o1 0 {CC:g}", x("m5", "vg", g5, "0", "0", N5, 2, 8),
          x("m6", "vg", "vg", "vdd", "vdd", P5, UW, UL, N_M6), f"Cvg vg vdd {CVG:g}"]
    if kind == "loop":
        L.append("Vx o1x 0 0")
    # core-off flag: leaker pulls tsu up, Mk (0.525 x master) pulls it down
    lk = ["lk0"] + [f"l{i}" for i in range(1, NLK)] + ["tsu"]
    nn += lk[1:-1]
    L += ["Vlk vdd lk0 0"] + [x(f"lk{i}", lk[i + 1], "0", lk[i], "vdd", P5, UW, UL) for i in range(NLK)]
    L.append(x("mk", "tsu", "vn", "0", "0", N5, MK_W * (16 if mut == "early" else 1), MK_L))
    if mut == "early":                       # broken copy: bias_ok straight from the leaker flag, released early
        nn.append("okx")                     # ok = NOT tsu (as in WO-50): okx = NOT tsu, sua = NOT okx
        L += [x("i0p", "okx", "tsu", "vdd", "vdd", P5, 1, 1), x("i0n", "okx", "tsu", "0", "0", N5, 1, 1),
              x("i1p", "sua", "okx", "vdd", "vdd", P5, 1, 1), x("i1n", "sua", "okx", "0", "0", N5, 1, 1)]
    else:                                    # pnp-on comparator V_B - V_C > ~nVT ln CMP_SKEW
        nn += ["tc", "q", "n2", "hy"]
        L += [x("mct", "tc", "vg", "vdd", "vdd", P5, UW, UL, N_CT),
              x("mcc", "q", "c", "tc", "tc", P5, 4, 4), x("mcb", "n2", "b", "tc", "tc", P5, 4 * CMP_SKEW, 4),
              x("ml3", "n2", "n2", "0", "0", N5, 1, 8), x("ml4", "q", "n2", "0", "0", N5, 1, 8),
              x("mqd", "q", "tsu", "0", "0", N5, 1, 1),
              x("mhy1", "hy", "vg", "vdd", "vdd", P5, UW, UL), x("mhy2", "q", "sua", "hy", "vdd", P5, 1, 1),
              x("i1p", "sua", "q", "vdd", "vdd", P5, UW, UL), x("i1n", "sua", "q", "0", "0", N5, 1, 1)]
    L += [x("i2p", "ok", "sua", "vdd", "vdd", P5, 1, 1), x("i2n", "ok", "sua", "0", "0", N5, 1, 1)]
    # kick into o1 while ok is low (not in the loop-break deck)
    if mut != "nosu" and kind != "loop":
        kn = ["kq"] + [f"k{i}" for i in range(1, NKK)] + ["o1"]
        nn += kn[:-1]
        L += [x("mkw", "kq", "ok", "vdd", "vdd", P5, 1, 1)] + [x(f"kc{i}", kn[i + 1], "0", kn[i], "vdd", P5, UW, UL)
                                                              for i in range(NKK)]
    # master leg (code 100) into the NMOS diode VN
    L += [x("mm", "mo", "vg", "vdd", "vdd", P5, UW, UL, G0 + CODE_RESET), "Vsm mo vn 0",
          x("mn", "vn", "vn", "0", "0", N5, MN_W, MN_L)]
    if init in ("0", "v"):                   # dci: .ic every node = 0 / = VDD (with uic)
        val = 0.0 if init == "0" else vdd            # pnp emitters capped at 0.8 V (3 V on a pnp is not a state)
        L.append(".ic " + " ".join(f"v({n})={(min(val, 0.8) if n in ('a', 'b', 'c') else val):g}" for n in nn))
    elif kind in ("dct", "dcv", "op"):       # hint towards the operating point; the result is checked for physics
        hint = dict(a=0.6, b=0.6, c=0.54, vg=vdd - 1.3, o1=0.9, n1=0.9, t=1.9, vn=0.9, mo=0.9, tsu=0.05, ok=vdd,
                    sua=0, q=vdd - 1, tc=2.0)
        L.append(".nodeset " + " ".join(f"v({k})={v:g}" for k, v in hint.items() if k in nn))
    vecs = ["i(vsm)", "i(vdd)", "v(vg)", "v(tsu)", "v(ok)", "i(vlk)", "v(a)", "v(b)", "v(c)", "v(o1)"]
    if kind == "dct":
        L.append(f"Vddx vddx 0 {vdd}")
        for k in range(8):
            L.append(x(f"b{k}", f"d{k}", "vg", "vddx", "vddx", P5, UW, UL, G0))
            for bit, w in ((0, 1), (1, 2), (2, 4)):
                if mut == "trim_open" and bit == 0:
                    continue
                g = "0" if (k >> bit) & 1 else "vddx"
                L += [x(f"t{k}_{bit}", f"s{k}_{bit}", "vg", "vddx", "vddx", P5, UW, UL, w),
                      x(f"w{k}_{bit}", f"d{k}", g, f"s{k}_{bit}", "vddx", P5, 1, 0.5)]
            L.append(f"Vs{k} d{k} 0 {VSENSE}")
        vecs += [f"i(vs{k})" for k in range(8)]
        an = ".dc temp -40 125 5"
    elif kind == "op":
        an = f".dc temp {temp} {temp} 1"
    elif kind == "dcv":
        an = ".dc vdd 2.8 3.8 0.05"
    elif kind == "loop":
        an = ".dc vx 0 2.0 0.002"
        vecs = ["i(vsm)", "v(o1)", "v(a)", "v(b)", "v(vg)", "v(tsu)"]
    else:                                    # tran or dci (transient)
        if kind == "dci":
            tstop, tmax = 300e-6, 20e-9
        else:
            tstop = 10e-9 + tr + (60e-6 if tr < 1e-4 else 200e-6)
            tmax = 5e-9 if tr < 1e-4 else 2e-6
        an = f".tran {tmax:.3g} {tstop:.6g} 0 {tmax:.3g} uic"
        L.append(".option method=gear rshunt=1e12 itl4=200")   # WO-55 smoke: ff/125 aborted at t = 10 ns without
        vecs = ["i(vsm)", "v(ok)", "v(vdd)", "v(vg)", "v(tsu)", "v(a)", "v(b)", "v(o1)"]
    L += [an, ".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=8", "run",
          f"wrdata {out} {' '.join(vecs)}", ".endc", ".end"]
    return "\n".join(L) + "\n", ["x"] + vecs


def sim(tv, path):
    text, names = tv
    with open(path + ".cir", "w") as f:
        f.write(text)
    p = subprocess.run(["ngspice", "-b", path + ".cir"], capture_output=True, text=True, timeout=5400)
    with open(path + ".log", "w") as f:
        f.write(p.stdout[-4000:] + p.stderr[-4000:])
    csv = path + ".csv"
    if not os.path.exists(csv):
        return None
    rows = [ln.split() for ln in open(csv)]
    os.remove(csv)                                   # raw csv is deleted (WO rule)
    data = [list(map(float, r)) for r in rows[1:] if r]
    return {h: [r[i] for r in data] for i, h in enumerate(names)}


def phys(d, vdd):
    """WO-50 found .dc 'solutions' with V_A ~ -1400 V (5.5 mA own current). Reject anything off the rails."""
    return all(-0.1 <= v <= vdd + 0.1 for v in d["v(a)"]) and all(-0.1 <= v <= vdd + 0.1 for v in d["v(vg)"])


def ratio_of(out):
    try:
        return json.load(open(os.path.join(out, "tune.json")))["ratio"]
    except OSError:
        return 4.6


def op_point(out, tag, corner, temp, vdd, ratio, mut="none"):
    base = os.path.join(out, tag + "_op")
    return sim(deck("op", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv"), base)


def tc_eval(d):
    T, I = d["x"], d["i(vsm)"]
    i27 = I[T.index(min(T, key=lambda t: abs(t - 27)))]
    dev = [i / i27 - 1 for i in I]
    return i27, max(dev), min(dev), (I[-1] - I[0]) / i27


def trim_eval(d, mut):
    T = d[list(d)[0]]
    res = []
    for t in TEMPS:
        j = T.index(min(T, key=lambda v: abs(v - t)))
        I = [d[f"i(vs{k})"][j] for k in range(8)]
        u = I[CODE_RESET] / (G0 + CODE_RESET)
        itgt = u * GT
        steps = [I[k + 1] - I[k] for k in range(7)]
        res.append(dict(T=t, I=I, step_min_u=min(steps) / u, step_max_pct=100 * max(steps) / itgt,
                        cover=I[7] / I[0], adj_max=max(I[k + 1] / I[k] for k in range(7))))
    ok = all(r["step_min_u"] >= 0.5 and r["step_max_pct"] <= 100 * LIM_STEP and r["cover"] >= COVER
             and r["adj_max"] <= (1 + RESID) / (1 - RESID) for r in res)
    return res, ok


def loop_eval(d):
    V, O, I = d["x"], d["v(o1)"], d["i(vsm)"]
    dv = [b - a for a, b in zip(d["v(a)"], d["v(b)"])]
    cr = []
    for k in range(len(V) - 1):
        s0, s1 = O[k] - V[k], O[k + 1] - V[k + 1]
        if s0 == 0 or s0 * s1 < 0:
            f = s0 / (s0 - s1) if s0 != s1 else 0
            cr.append(dict(vx=V[k] + f * (V[k + 1] - V[k]), i_uA=1e6 * (I[k] + f * (I[k + 1] - I[k])),
                           stable=s1 < s0))
    st = [c for c in cr if c["stable"] and c["i_uA"] * 1e-6 > LOOP_IMIN]
    ig = max((c["i_uA"] for c in st), default=None)
    mid = [c for c in cr if ig and LOOP_IMIN < c["i_uA"] * 1e-6 < 0.9 * ig * 1e-6]
    prof = {}
    if ig:
        for fr in (0.1, 0.25, 0.5, 0.75, 0.9):
            k = min(range(len(I)), key=lambda j: abs(I[j] * 1e6 - fr * ig))
            prof[f"{fr:g}"] = dict(dv_mV=1e3 * dv[k], va=d["v(a)"][k])
    ok = ig is not None and len(st) == 1 and not mid and ig * 1e-6 >= IDC_MIN
    return dict(crossings=cr, i_good_uA=ig, n_stable=len(st), n_mid=len(mid), dv_profile=prof,
                verdict="ACCEPT" if ok else "REJECT")


def tran_eval(d, idc, tr):
    t, I, ok, vd = d["x"], d["i(vsm)"], d["v(ok)"], d["v(vdd)"]
    tend = 10e-9 + tr
    hi = [vd[k] > 1.0 and ok[k] > 0.5 * vd[k] for k in range(len(t))]
    kf = len(t)
    while kf > 0 and hi[kf - 1]:
        kf -= 1
    rises = sum(1 for k in range(1, len(t)) if hi[k] and not hi[k - 1])
    win = [k for k in range(len(t)) if t[k] >= tend + TSET]
    dev = max(abs(I[k] / idc - 1) for k in win)
    t90 = next((t[k] for k in range(len(t)) if I[k] >= 0.9 * idc), None)
    t1 = None                                         # last entry into the +-1 % band
    for k in range(len(t) - 1, -1, -1):
        if abs(I[k] / idc - 1) > LIM_SU:
            t1 = t[k + 1] if k + 1 < len(t) else None
            break
    tok = t[kf] if kf < len(t) else None
    iok = I[kf] / idc if kf < len(t) else None
    okw = all(ok[k] > 0.9 * vd[k] for k in win)
    started = (dev <= LIM_SU and okw and iok is not None and iok >= IOK_MIN and idc >= IDC_MIN and rises == 1)
    return dict(idc_uA=idc * 1e6, iend_uA=I[-1] * 1e6, end_err_pct=100 * (I[-1] / idc - 1), dev_win_pct=100 * dev,
                t90_after_ramp_us=None if t90 is None else (t90 - tend) * 1e6,
                t1pct_after_ramp_us=None if t1 is None else (t1 - tend) * 1e6,
                tok_after_ramp_us=None if tok is None else (tok - tend) * 1e6,
                settle_after_ok_us=None if (t1 is None or tok is None) else (t1 - tok) * 1e6,
                vdd_at_ok=vd[kf] if kf < len(t) else None, I_at_ok_frac=iok, ok_rises=rises,
                i_max_frac=max(I) / idc, ok_end=ok[-1], vg_end=d["v(vg)"][-1], tsu_end=d["v(tsu)"][-1],
                va_end=d["v(a)"][-1], vb_end=d["v(b)"][-1], o1_end=d["v(o1)"][-1],
                verdict="ACCEPT" if started else "REJECT")


def ic_eval(d):
    t, I = d["x"], d["i(vsm)"]
    last = [I[k] for k in range(len(t)) if t[k] >= t[-1] - 10e-6]
    w50 = [I[k] for k in range(len(t)) if t[k] >= t[-1] - 50e-6]
    iend = sum(last) / len(last)
    return dict(i_uA=iend * 1e6, p2p_pct=100 * (max(w50) - min(w50)) / max(abs(iend), 1e-12), ok_end=d["v(ok)"][-1],
                imax_frac=max(I) / max(abs(iend), 1e-12), va_end=d["v(a)"][-1], vg_end=d["v(vg)"][-1])


def run(out, kind, corner, temp, vdd, mut="none", tr=1e-6):
    temp, vdd, tr = float(temp), float(vdd), float(tr)
    ratio = ratio_of(out)
    tag = f"{kind}_{corner}_{temp:g}_{vdd:g}_{mut}" + (f"_{tr:g}" if kind == "tran" else "")
    base = os.path.join(out, tag)
    r = dict(tag=tag, kind=kind, corner=corner, temp=temp, vdd=vdd, mut=mut, tr=tr, ratio=ratio)
    if kind == "dct":
        d = sim(deck("dct", corner, None, vdd, mut, ratio=ratio, out=base + ".csv"), base)
        if d is None:
            r["verdict"] = "SIMFAIL"
        else:
            i27, dmax, dmin, slope = tc_eval(d)
            T = d[list(d)[0]]
            j27 = T.index(min(T, key=lambda v: abs(v - 27)))
            tr_res, tr_ok = trim_eval(d, mut)
            tc_ok = max(dmax, -dmin) <= LIM_TC
            thr = [d["i(vlk)"][j] / (R_K * d["i(vsm)"][j]) for j in range(len(T))]
            vr1 = [1e3 * (b - c) for b, c in zip(d["v(b)"], d["v(c)"])]
            okmin = min(o / vdd for o in d["v(ok)"])
            ph = phys(d, vdd)
            r.update(i27_uA=i27 * 1e6, tc_max_pct=100 * dmax, tc_min_pct=100 * dmin, slope_pct=100 * slope,
                     own_uA_27=-d["i(vdd)"][j27] * 1e6, own_uA_max=max(-v for v in d["i(vdd)"]) * 1e6,
                     thr_min=min(thr), thr_max=max(thr), vr1_mV_min=min(vr1), vr1_mV_max=max(vr1), ok_min_frac=okmin,
                     phys=ph, I_T={f"{t:g}": i * 1e6 for t, i in zip(T, d["i(vsm)"]) if t in TEMPS or t == 25},
                     tc_ok=tc_ok, trim=tr_res, trim_ok=tr_ok)
            r["verdict"] = "ACCEPT" if (ph and tc_ok and tr_ok and max(thr) <= THR_MAX and okmin > 0.9) else "REJECT"
    elif kind == "dcv":
        d = sim(deck("dcv", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv"), base)
        if d is None:
            r["verdict"] = "SIMFAIL"
        else:
            V, I = d[list(d)[0]], d["i(vsm)"]
            pick = lambda v: I[V.index(min(V, key=lambda q: abs(q - v)))]
            i30, i33, i36 = pick(3.0), pick(3.3), pick(3.6)
            rel = (i36 - i30) / i33
            r.update(i30_uA=i30 * 1e6, i33_uA=i33 * 1e6, i36_uA=i36 * 1e6, dIrel_per_V_pct=100 * rel / 0.6,
                     phys=phys(d, 3.8), psrr_dB=math.log10(abs((0.6 / 3.3) / rel)) * 20 if rel else 999,
                     verdict="INFO")
    elif kind == "dci":
        res = {}
        for init in ("0", "v"):
            b = f"{base}_ic{init}"
            d = sim(deck("dci", corner, temp, vdd, mut, ratio=ratio, out=b + ".csv", init=init), b)
            res[init] = None if d is None else ic_eval(d)
        op = op_point(out, tag, corner, temp, vdd, ratio, mut)
        if None in res.values() or op is None:
            r["verdict"] = "SIMFAIL"
        else:
            i0, iv, iop = res["0"]["i_uA"], res["v"]["i_uA"], 1e6 * op["i(vsm)"][0]
            agree = abs(i0 - iv) / max(i0, iv, 1e-9)
            aop = abs(i0 / iop - 1) if iop > 0 else 1.0
            ph = phys(op, vdd)
            r.update(init0=res["0"], initv=res["v"], i_op_uA=iop, op_phys=ph, agree_pct=100 * agree,
                     op_agree_pct=100 * aop)
            good = (agree <= DCI_AGREE and aop <= DCI_OP and ph and min(i0, iv) * 1e-6 >= IDC_MIN
                    and max(res["0"]["p2p_pct"], res["v"]["p2p_pct"]) <= 100 * DCI_P2P
                    and min(res["0"]["ok_end"], res["v"]["ok_end"]) > 0.9 * vdd)
            r["verdict"] = "ACCEPT" if good else "REJECT"
    elif kind == "loop":
        d = sim(deck("loop", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv"), base)
        r.update(loop_eval(d) if d else dict(verdict="SIMFAIL"))
    else:
        op = op_point(out, tag, corner, temp, vdd, ratio, "none" if mut == "nosu" else mut)
        d = sim(deck("tran", corner, temp, vdd, mut, tr=tr, ratio=ratio, out=base + ".csv"), base)
        if d is None or op is None or d["x"][-1] < 10e-9 + tr + TSET:
            r["verdict"] = "SIMFAIL"
            r["t_last"] = None if d is None else d["x"][-1]
        else:
            r.update(tran_eval(d, op["i(vsm)"][0], tr), op_phys=phys(op, vdd))
            if not r["op_phys"]:
                r["verdict"] = "REJECT"
    with open(base + ".json", "w") as f:
        json.dump(r, f, indent=1)
    print(json.dumps({k: v for k, v in r.items() if k not in ("trim", "I_T", "crossings")}))
    return r


def tune(out):
    os.makedirs(out, exist_ok=True)
    grid = [round(3.0 + 0.3 * i, 2) for i in range(13)]
    tab = []
    for rt in grid:
        base = os.path.join(out, f"tune_{rt:g}")
        d = sim(deck("dct", "tt", None, 3.3, ratio=rt, out=base + ".csv"), base)
        if d is None or not phys(d, 3.3):
            tab.append(dict(ratio=rt, fail=True))
            continue
        i27, dmax, dmin, slope = tc_eval(d)
        tab.append(dict(ratio=rt, i27_uA=i27 * 1e6, slope_pct=100 * slope, tc_max_pct=100 * dmax,
                        tc_min_pct=100 * dmin))
        print(tab[-1])
    ok = [t for t in tab if not t.get("fail")]
    best = min(ok, key=lambda t: max(t["tc_max_pct"], -t["tc_min_pct"]))["ratio"]
    for a, b in zip(ok, ok[1:]):
        if a["slope_pct"] * b["slope_pct"] <= 0:
            best = a["ratio"] + (b["ratio"] - a["ratio"]) * a["slope_pct"] / (a["slope_pct"] - b["slope_pct"])
            break
    json.dump(dict(ratio=best, grid=tab), open(os.path.join(out, "tune.json"), "w"), indent=1)
    print("ratio", best)


def jobs(out, jobfile):
    me = os.path.abspath(__file__)
    py = f"python {me} run {os.path.abspath(out)}"
    L = [f"{py} tran {c} {t} {v} none {tr:g}" for c, t, v in TRAN for tr in TRS]          # long ones first
    L += [f"{py} tran {c} {t} 3.0 nosu {tr:g}" for c, t in (("ss", -40), ("ff", 125)) for tr in TRS]
    L += [f"{py} tran {c} {t} 3.0 early 1e-06" for c, t in (("ss", -40), ("ff", 125))]
    L += [f"{py} dci {c} {t} 3.0" for c in CORNERS for t in TEMPS] + [f"{py} dci ss -40 3.0 nosu"]
    L += [f"{py} dct {c} 27 {v}" for c, v in DCT]
    L += [f"{py} dct tt 27 3.3 ptat", f"{py} dct tt 27 3.3 trim_open", f"{py} dcv tt 27 3.3",
          f"{py} dcv ss -40 3.0", f"{py} dcv ff 125 3.6"]
    L += [f"{py} loop {c} {t} 3.0" for c in CORNERS for t in TEMPS]
    L += [f"{py} loop sf 27 3.0 noskew", f"{py} loop ff 125 3.0 noskew"]
    with open(jobfile, "w") as f:
        f.write("\n".join(L) + "\n")


EXPECT = {"none": "ACCEPT", "nosu": "REJECT", "ptat": "REJECT", "trim_open": "REJECT", "early": "REJECT",
          "noskew": "REJECT"}


def summary(out):
    R = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out))
         if f.endswith(".json") and f != "tune.json"]
    print("tune ratio R2/R1 =", ratio_of(out), "| R_K", round(R_K, 3), "SKEW", SKEW, "CMP_SKEW", CMP_SKEW)
    bad = 0
    for r in R:
        exp = "INFO" if r["kind"] == "dcv" else EXPECT.get(r["mut"], "ACCEPT")
        good = r["verdict"] == exp
        bad += not good
        if r["kind"] == "dct":
            s = (f"I27 {r.get('i27_uA', 0):.4f} uA TC {r.get('tc_min_pct', 0):+.2f}/{r.get('tc_max_pct', 0):+.2f} % "
                 f"own {r.get('own_uA_27', 0):.2f}/{r.get('own_uA_max', 0):.2f} uA thr {r.get('thr_min', 0):.2f}.."
                 f"{r.get('thr_max', 0):.2f} VR1 {r.get('vr1_mV_min', 0):.1f}..{r.get('vr1_mV_max', 0):.1f} mV "
                 f"okmin {r.get('ok_min_frac', 0):.2f} phys {r.get('phys')} trim_ok {r.get('trim_ok')} ")
            for q in r.get("trim", []):
                s += f"| T{q['T']:g}: stepmin {q['step_min_u']:.2f}u stepmax {q['step_max_pct']:.2f}% cover {q['cover']:.4f} "
        elif r["kind"] == "dcv":
            s = (f"I 3.0/3.3/3.6 {r.get('i30_uA', 0):.4f}/{r.get('i33_uA', 0):.4f}/{r.get('i36_uA', 0):.4f} uA "
                 f"PSRR {r.get('psrr_dB', 0):.1f} dB phys {r.get('phys')}")
        elif r["kind"] == "dci":
            a, b = r.get("init0") or {}, r.get("initv") or {}
            s = (f"I from 0 / VDD / op {a.get('i_uA', 0):.4f} / {b.get('i_uA', 0):.4f} / {r.get('i_op_uA', 0):.4f} uA "
                 f"agree {r.get('agree_pct', 0):.3f} % vs op {r.get('op_agree_pct', 0):.3f} % p2p "
                 f"{a.get('p2p_pct', 0):.3f}/{b.get('p2p_pct', 0):.3f} % ok {a.get('ok_end', 0):.2f}/{b.get('ok_end', 0):.2f} "
                 f"Imax {a.get('imax_frac', 0):.2f}/{b.get('imax_frac', 0):.2f} op_phys {r.get('op_phys')}")
        elif r["kind"] == "loop":
            s = (f"stable {r.get('n_stable')} mid {r.get('n_mid')} I_good {fmt(r.get('i_good_uA'))} uA crossings "
                 + "; ".join(f"{c['i_uA']:.4f}uA {'S' if c['stable'] else 'U'}" for c in r.get("crossings", []))
                 + " | dV(B-A) mV at I/Igood " + " ".join(f"{k}:{v['dv_mV']:+.3f}(va {v['va']:.3f})"
                                                       for k, v in r.get("dv_profile", {}).items()))
        else:
            s = (f"idc {r.get('idc_uA', 0):.4f} iend {r.get('iend_uA', 0):.4f} uA dev {r.get('dev_win_pct', 0):.3f} % "
                 f"t90 {fmt(r.get('t90_after_ramp_us'))} t1% {fmt(r.get('t1pct_after_ramp_us'))} tok "
                 f"{fmt(r.get('tok_after_ramp_us'))} us settle-after-ok {fmt(r.get('settle_after_ok_us'))} us "
                 f"VDD@ok {fmt(r.get('vdd_at_ok'))} I@ok {fmt(r.get('I_at_ok_frac'))} rises {r.get('ok_rises')} "
                 f"Imax {fmt(r.get('i_max_frac'))} op_phys {r.get('op_phys')}")
        print(f"{r['tag']:<36} {r['verdict']:<7} (expect {exp}) {'OK' if good else 'MISMATCH'} :: {s}")
    tr = [r for r in R if r["kind"] == "tran" and r["mut"] == "none" and r["verdict"] == "ACCEPT"]
    if tr:
        w = max(tr, key=lambda r: r.get("settle_after_ok_us") or 0)
        print(f"WORST settle after bias_ok (ACCEPT none runs): {fmt(w.get('settle_after_ok_us'))} us at {w['tag']}; "
              f"VDD@ok range {min(r['vdd_at_ok'] for r in tr):.2f}..{max(r['vdd_at_ok'] for r in tr):.2f} V; "
              f"I@ok min {min(r['I_at_ok_frac'] for r in tr):.3f}")
    print("VERDICT", "ACCEPT" if bad == 0 else f"MISMATCH {bad}")
    return bad


def fmt(v):
    return "None" if v is None else f"{v:.3f}"


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "tune":
        tune(a[1])
    elif a[0] == "jobs":
        jobs(a[1], a[2])
    elif a[0] == "run":
        os.makedirs(a[1], exist_ok=True)
        run(*a[1:])
    elif a[0] == "summary":
        sys.exit(1 if summary(a[1]) else 0)
