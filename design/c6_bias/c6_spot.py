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
R1_L = 94.0                    # um of 0p69 xhrpoly; WO-64: default only, the tuned value comes from OUT/tune.json
I_TGT = 1.07e-6                # WO-64: master (code 100) current at tt/27/3.3 for the C1 port design currents
LIM_I0 = 0.02                  # tt/27 I0 within +-2 % of I_TGT
OWN_MAX = 6e-6                 # SPEC row 104
R1_S1 = 165.0                  # WO-64 tune stage-1 R1 (estimate: I ~ 1/R, zero-TC ratio ~2.2)
TUNE1 = [round(1.6 + 0.15 * i, 2) for i in range(9)]
CC = float(os.environ.get("C6_CC", 3e-12))     # env overrides: WO-55 smoke variants only
TRANFIX = os.environ.get("C6_TRANFIX", "op")   # WO-64: op = no uic (t=0 op at VAPWR 0); uic = WO-55; gmin = uic+gmin 1e-12
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
N_HY = 4                       # WO-64: hysteresis units into q while ok high (WO-55: 1 -> 3-4 ok rises); mut hy1 = 1
# gates
TSET, LIM_SU = 10e-6, 0.01     # (WO-55 window, superseded) / +-1 % band
H_HOLD = 256 / 4e6             # D78: C9 rstb hold after the final bias_ok rise, 256 fs cycles at 4 MHz = 64 us
T_CNT = 2 ** 16 / 4e6          # WO-64 VAPWR-good = C9 count: 2^16 fs cycles (16.4 ms) after rst_n release (ramp start)
# D89 (WO-87): start-up row = settle (+-1 %) after the FINAL bias_ok rise <= LIM_D89. The hold that must cover it is
# the C9 VAPWR-good count, 2^16 fs cycles after rst_n (16.4 ms at the fastest fs, 4 MHz; slower fs = longer hold).
# 25 % of it (4.1 ms) leaves 4x for fs/count uncertainty and model error; the WO-80 worst (sf/-40 10 ms) is 1.68 ms
# (41 % of the limit). Earlier bias_ok pulses are reported only (D88 restarts the C9 bias run on any drop).
LIM_D89 = 0.25 * T_CNT
EARLY_K = 16                   # early broken copy: Mk x16 (WO-55); earlyx: Mk x1000 (flag clear at ~zero current)
SLOW_TAU = 1.2e-3              # slow broken copy: master-leg gate RC (1 G x 1.2 pF); 1 % at ~4.6 tau = 5.5 ms > LIM_D89
VPRE = 0.05                    # tran: VAPWR before the ramp (V); below every device threshold
WIN_MIN = 20e-6               # at least this much simulated time after rstb release
HINT_AGREE = 0.005             # dct first point vs transient-from-0 current
IOK_MIN = 0.5                  # bias_ok's final assertion only with I >= 50 % of DC
IDC_MIN = 0.75e-6              # separator good / low state
THR_MAX = 0.8                  # core-off flag must be clear at the operating point: I_lk / (R_K I) <= 0.8
DCI_AGREE, DCI_P2P, DCI_OP = 0.005, 0.005, 0.01
LOOP_IMIN = 0.02e-6            # loop gate: no equilibrium between this and 0.9 I_good; exactly one stable above


def x(name, d, g, s, b, dev, w, l, m=1):
    return f"X{name} {d} {g} {s} {b} {dev} w={w:g} l={l:g} m={m}"


def deck(kind, corner, temp, vdd, mut="none", tr=1e-6, ratio=4.6, out="o.csv", init=None, r1=R1_L, hint=None):
    R1L = r1
    r2l = R1L * ratio
    if kind == "hint":                       # transient from all-0 at fixed VDD: physical state for the dct nodeset
        kind, init = "dci", "0"
        hint_run = True
    else:
        hint_run = False
    L = [f"* c6_spot {kind} {corner} {temp} {vdd} {mut} {tr:g} ratio {ratio:.4f} r1 {R1L:.4g} init {init}",
         f".lib {LIB} {corner}", ".option gmin=1e-15 reltol=1e-5 abstol=1e-14"]
    # WO-64: the ramp starts from 50 mV, not 0 V. From the exact all-0 state every 125 C ramp with the kick chain stopped
    # at t = 10 ns (vsm#branch, any tol/method/gmin/rshunt); without the chain, or from 50 mV, it runs (exp125 v10/v11).
    L.append(f"Vdd vdd 0 pwl(0 {VPRE} 10n {VPRE} {10e-9 + tr:.6g} {vdd})" if kind == "tran" else f"Vdd vdd 0 {vdd}")
    if kind != "dct":
        L.append(f".temp {temp}")
    nn = ["a", "b", "c", "t", "n1", "o1", "vg", "vn", "mo", "tsu", "ok", "sua"]
    # core
    L += [x("m1", "a", "vg", "vdd", "vdd", P5, UW, UL, N_CORE), x("m2", "b", "vg", "vdd", "vdd", P5, UW, UL, N_CORE),
          f"Xq1 0 0 a {PNP} m=1", f"Xq2 0 0 c {PNP} m={NPNP}", f"Xr1 b c 0 {RX} l={R1L:.4g}"]
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
    L.append(x("mk", "tsu", "vn", "0", "0", N5, MK_W * {"early": EARLY_K, "earlyx": 1000}.get(mut, 1), MK_L))
    if mut in ("early", "earlyx"):                     # broken copy: bias_ok straight from the leaker flag, released early
        nn.append("okx")                     # ok = NOT tsu (as in WO-50): okx = NOT tsu, sua = NOT okx
        L += [x("i0p", "okx", "tsu", "vdd", "vdd", P5, 1, 1), x("i0n", "okx", "tsu", "0", "0", N5, 1, 1),
              x("i1p", "sua", "okx", "vdd", "vdd", P5, 1, 1), x("i1n", "sua", "okx", "0", "0", N5, 1, 1)]
    else:                                    # pnp-on comparator V_B - V_C > ~nVT ln CMP_SKEW
        nn += ["tc", "q", "n2", "hy"]
        L += [x("mct", "tc", "vg", "vdd", "vdd", P5, UW, UL, N_CT),
              x("mcc", "q", "c", "tc", "tc", P5, 4, 4), x("mcb", "n2", "b", "tc", "tc", P5, 4 * CMP_SKEW, 4),
              x("ml3", "n2", "n2", "0", "0", N5, 1, 8), x("ml4", "q", "n2", "0", "0", N5, 1, 8),
              x("mqd", "q", "tsu", "0", "0", N5, 1, 1),
              x("mhy1", "hy", "vg", "vdd", "vdd", P5, UW, UL, 1 if mut == "hy1" else N_HY), x("mhy2", "q", "sua", "hy", "vdd", P5, 1, 1),
              x("i1p", "sua", "q", "vdd", "vdd", P5, UW, UL), x("i1n", "sua", "q", "0", "0", N5, 1, 1)]
    L += [x("i2p", "ok", "sua", "vdd", "vdd", P5, 1, 1), x("i2n", "ok", "sua", "0", "0", N5, 1, 1)]
    # kick into o1 while ok is low (not in the loop-break deck)
    if mut not in ("nosu", "zhintnk") and kind != "loop":
        kn = ["kq"] + [f"k{i}" for i in range(1, NKK)] + ["o1"]
        nn += kn[:-1]
        L += [x("mkw", "kq", "ok", "vdd", "vdd", P5, 1, 1)] + [x(f"kc{i}", kn[i + 1], "0", kn[i], "vdd", P5, UW, UL)
                                                              for i in range(NKK)]
    # master leg (code 100) into the NMOS diode VN
    if mut == "slow":                        # WO-87 broken copy for D89: the measured leg settles with tau SLOW_TAU
        nn.append("vgm")
        L += [f"Rgm vg vgm 1e9", f"Cgm vgm vdd {SLOW_TAU / 1e9:g}"]
    L += [x("mm", "mo", "vgm" if mut == "slow" else "vg", "vdd", "vdd", P5, UW, UL, G0 + CODE_RESET), "Vsm mo vn 0",
          x("mn", "vn", "vn", "0", "0", N5, MN_W, MN_L)]
    if init in ("0", "v"):                   # dci: .ic every node = 0 / = VDD (with uic)
        val = 0.0 if init == "0" else vdd            # pnp emitters capped at 0.8 V (3 V on a pnp is not a state)
        L.append(".ic " + " ".join(f"v({n})={(min(val, 0.8) if n in ('a', 'b', 'c') else val):g}" for n in nn))
    elif kind == "dct" and mut in ("zhint", "zhintnk"):  # WO-87: nodeset on the zero-current state (core off)
        z = dict(a=0, b=0, c=0, vg=vdd, o1=0, n1=0, t=vdd, vn=0, mo=0, tsu=vdd, ok=0, sua=vdd, q=0, tc=vdd, n2=0, hy=vdd)
        L.append(".nodeset " + " ".join(f"v({k})={v:g}" for k, v in z.items() if k in nn))
    elif kind == "dct" and hint and mut != "oldhint":   # WO-64: nodeset from the transient-from-0 state (physical)
        L.append(".nodeset " + " ".join(f"v({k})={v:.6g}" for k, v in hint.items() if k in nn))
    elif kind in ("dct", "dcv", "op"):       # static hint (WO-55; oldhint broken copy); result checked for physics
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
            # WO-64: run past rstb release (final ok + H_HOLD; slow ramps: the C9 VAPWR-good count T_CNT)
            tstop = 10e-9 + tr + 150e-6 if tr < 1e-4 else 10e-9 + T_CNT + 200e-6
            tmax = 5e-9 if tr < 1e-4 else 2e-6
        # WO-64: every 125 C ramp died at t = 10 ns (timestep too small, vsm#branch) from the uic all-0 state.
        # Default "op": no uic, the t = 0 operating point is solved at VAPWR = 0 (consistent leakage state).
        uic = " uic" if (kind == "dci" or TRANFIX in ("uic", "gmin")) else ""
        an = f".tran {tmax:.3g} {tstop:.6g} 0 {tmax:.3g}{uic}"
        L.append(".option method=gear rshunt=1e12 itl4=200")   # WO-55 smoke: ff/125 aborted at t = 10 ns without
        if kind == "tran":
            # WO-80 root cause of the 125 C SIMFAIL/timeouts: the deck-wide gmin 1e-15 (1000x below the ngspice default)
            # leaves the near-zero-bias matrix at VAPWR ~50 mV / 125 C ill-conditioned (timestep too small on vsm#branch
            # at 11 ns or 20 us, or > 5400 s runs). abstol 1e-12 alone, trap, or reltol 1e-4 do not fix it; gmin 1e-12 +
            # abstol 1e-12 does (exp/: s1, f2, t3 all complete, t3 254 s). Error: ~1e-12 S x 3 V = 3 pA per node vs 1 uA.
            L.append(".option gmin=1e-12 abstol=1e-12")
        vecs = ["i(vsm)", "v(ok)", "v(vdd)", "v(vg)", "v(tsu)", "v(a)", "v(b)", "v(o1)"]
        if hint_run:
            vecs = ["i(vsm)"] + [f"v({n})" for n in nn]
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
    return params_of(out)[0]


def params_of(out):
    """(R2/R1, R1 length um) from OUT/tune.json (WO-64 tune writes both)."""
    try:
        j = json.load(open(os.path.join(out, "tune.json")))
        return j["ratio"], j.get("r1", R1_L)
    except OSError:
        return 4.6, R1_L


def op_point(out, tag, corner, temp, vdd, ratio, mut="none", r1=R1_L):
    base = os.path.join(out, tag + "_op")
    return sim(deck("op", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv", r1=r1), base)


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


def tran_eval(d, idc, tr, mut="none"):
    t, I, ok, vd = d["x"], d["i(vsm)"], d["v(ok)"], d["v(vdd)"]
    tend = 10e-9 + tr
    hi = [vd[k] > 1.0 and ok[k] > 0.5 * vd[k] for k in range(len(t))]
    kf = len(t)
    while kf > 0 and hi[kf - 1]:
        kf -= 1
    rises = sum(1 for k in range(1, len(t)) if hi[k] and not hi[k - 1])
    # WO-80: every bias_ok high pulse (rise time after ramp end, width, VDD and I/Idc at the rise). Non-final pulses
    # are the glitch-highs the C9 256-cycle counter must reject: covered when width < H_HOLD.
    pulses, k0 = [], None
    for k in range(len(t) + 1):
        h = k < len(t) and hi[k]
        if h and k0 is None:
            k0 = k
        elif not h and k0 is not None:
            pulses.append(dict(rise_us=(t[k0] - tend) * 1e6, width_us=(t[k - 1] - t[k0]) * 1e6, vdd=vd[k0],
                               i_frac=I[k0] / idc, final=k == len(t)))
            k0 = None
    pre = [p for p in pulses if not p["final"]]
    win = [k for k in range(len(t)) if t[k] >= tend + TSET]
    dev = max((abs(I[k] / idc - 1) for k in win), default=1.0)   # WO-55 window (ramp end + 10 us), reported only
    t90 = next((t[k] for k in range(len(t)) if I[k] >= 0.9 * idc), None)
    t1 = None                                         # last entry into the +-1 % band
    for k in range(len(t) - 1, -1, -1):
        if abs(I[k] / idc - 1) > LIM_SU:
            # WO-87: still outside the band at the last sample = never settled (was None = "settled", a blind spot)
            t1 = t[k + 1] if k + 1 < len(t) else math.inf
            break
    tok = t[kf] if kf < len(t) else None
    iok = I[kf] / idc if kf < len(t) else None
    # WO-64 / D78 gate: settled +-1 % before rstb release and inside +-1 % from release to the end of the run.
    # release = final ok rise + H_HOLD (hold0: + 0); slow ramps also wait for the C9 VAPWR-good count (nocnt: not).
    rel = None
    if tok is not None:
        rel = tok + (0.0 if mut == "hold0" else H_HOLD)
        if tr >= 1e-4 and mut != "nocnt":
            rel = max(rel, 10e-9 + T_CNT)
    rwin = [k for k in range(len(t)) if rel is not None and t[k] >= rel]
    rdev = max((abs(I[k] / idc - 1) for k in rwin), default=1.0)
    settled = t1 is None or (rel is not None and t1 <= rel)
    longwin = rel is not None and t[-1] - rel >= WIN_MIN
    okw = bool(rwin) and all(ok[k] > 0.9 * vd[k] for k in rwin)
    # D89 (WO-87): the "one rise" and "I >= 50 % at the final rise" terms of the D78 row are replaced by the settle
    # from the final rise <= LIM_D89 (both still reported). Every other term is unchanged.
    sao = None if (tok is None or t1 is None) else max(t1 - tok, 0.0)
    d89 = tok is not None and t1 is not math.inf and (sao is None or sao <= LIM_D89)
    started = (rdev <= LIM_SU and settled and longwin and okw and d89 and idc >= IDC_MIN)
    if t1 is math.inf:
        t1 = None
    return dict(d89_ok=d89, settle_after_final_ms=None if sao in (None, math.inf) else sao * 1e3,
                lim_d89_ms=LIM_D89 * 1e3,rel_after_ramp_us=None if rel is None else (rel - tend) * 1e6, dev_rel_pct=100 * rdev,
                settled_before_rel=settled, win_after_rel_us=None if rel is None else (t[-1] - rel) * 1e6,
                margin_hold=None if (t1 is None or tok is None) else H_HOLD / max(t1 - tok, 1e-12),idc_uA=idc * 1e6, iend_uA=I[-1] * 1e6, end_err_pct=100 * (I[-1] / idc - 1), dev_win_pct=100 * dev,
                t90_after_ramp_us=None if t90 is None else (t90 - tend) * 1e6,
                t1pct_after_ramp_us=None if t1 is None else (t1 - tend) * 1e6,
                tok_after_ramp_us=None if tok is None else (tok - tend) * 1e6,
                settle_after_ok_us=None if (t1 is None or tok is None) else (t1 - tok) * 1e6,
                vdd_at_ok=vd[kf] if kf < len(t) else None, I_at_ok_frac=iok, ok_rises=rises, ok_pulses=pulses,
                pre_pulse_max_us=max((p["width_us"] for p in pre), default=0.0),
                pre_pulse_covered=all(p["width_us"] * 1e-6 < H_HOLD for p in pre),
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
    ratio, r1 = params_of(out)
    tag = f"{kind}_{corner}_{temp:g}_{vdd:g}_{mut}" + (f"_{tr:g}" if kind == "tran" else "")
    base = os.path.join(out, tag)
    r = dict(tag=tag, kind=kind, corner=corner, temp=temp, vdd=vdd, mut=mut, tr=tr, ratio=ratio, r1=r1)
    if kind == "dct":
        # WO-64: the sweep starts at -40 C; its nodeset comes from a 300 us transient from all-0 at -40 C (physical state)
        hb = base + "_hint"
        hd = sim(deck("hint", corner, -40, vdd, "none" if mut in ("oldhint", "zhint", "zhintnk") else mut, ratio=ratio, out=hb + ".csv",
                      r1=r1), hb)
        hint = None if hd is None else {k[2:-1]: v[-1] for k, v in hd.items() if k.startswith("v(")}
        i_hint = None if hd is None else hd["i(vsm)"][-1]
        d = sim(deck("dct", corner, None, vdd, mut, ratio=ratio, out=base + ".csv", r1=r1, hint=hint), base)
        if d is None:
            r["verdict"] = "SIMFAIL"
        else:
            i27, dmax, dmin, slope = tc_eval(d)
            T = d[list(d)[0]]
            j27 = T.index(min(T, key=lambda v: abs(v - 27)))
            tr_res, tr_ok = trim_eval(d, mut)
            tc_ok = max(dmax, -dmin) <= LIM_TC
            thr = [d["i(vlk)"][j] / (R_K * max(abs(d["i(vsm)"][j]), 1e-15)) for j in range(len(T))]
            vr1 = [1e3 * (b - c) for b, c in zip(d["v(b)"], d["v(c)"])]
            okmin = min(o / vdd for o in d["v(ok)"])
            ph = phys(d, vdd)
            r.update(i27_uA=i27 * 1e6, tc_max_pct=100 * dmax, tc_min_pct=100 * dmin, slope_pct=100 * slope,
                     own_uA_27=-d["i(vdd)"][j27] * 1e6, own_uA_max=max(-v for v in d["i(vdd)"]) * 1e6,
                     thr_min=min(thr), thr_max=max(thr), vr1_mV_min=min(vr1), vr1_mV_max=max(vr1), ok_min_frac=okmin,
                     phys=ph, I_T={f"{t:g}": i * 1e6 for t, i in zip(T, d["i(vsm)"]) if t in TEMPS or t == 25},
                     tc_ok=tc_ok, trim=tr_res, trim_ok=tr_ok)
            # WO-64 gates: first sweep point = transient-from-0 state; own current <= 6 uA; tt/27 I0 at I_TGT +-2 %
            hagree = 1.0 if not i_hint else abs(d["i(vsm)"][0] / i_hint - 1)
            own_ok = r["own_uA_max"] * 1e-6 <= OWN_MAX
            i0_ok = corner != "tt" or abs(i27 / I_TGT - 1) <= LIM_I0
            r.update(i_hint_uA=None if i_hint is None else i_hint * 1e6, hint_agree_pct=100 * hagree, own_ok=own_ok,
                     i0_err_pct=100 * (i27 / I_TGT - 1), i0_ok=i0_ok, r_len_um=r1 * (1 + 2 * ratio))
            r["verdict"] = "ACCEPT" if (ph and tc_ok and tr_ok and max(thr) <= THR_MAX and okmin > 0.9
                                        and hagree <= HINT_AGREE and own_ok and i0_ok) else "REJECT"
    elif kind == "dcv":
        d = sim(deck("dcv", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv", r1=r1), base)
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
            d = sim(deck("dci", corner, temp, vdd, mut, ratio=ratio, out=b + ".csv", init=init, r1=r1), b)
            res[init] = None if d is None else ic_eval(d)
        op = op_point(out, tag, corner, temp, vdd, ratio, mut, r1)
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
        d = sim(deck("loop", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv", r1=r1), base)
        r.update(loop_eval(d) if d else dict(verdict="SIMFAIL"))
    else:
        op = op_point(out, tag, corner, temp, vdd, ratio, "none" if mut == "nosu" else mut, r1)
        d = sim(deck("tran", corner, temp, vdd, mut, tr=tr, ratio=ratio, out=base + ".csv", r1=r1), base)
        if d is None or op is None or d["x"][-1] < 10e-9 + tr + 100e-6:
            r["verdict"] = "SIMFAIL"
            r["t_last"] = None if d is None else d["x"][-1]
        else:
            r.update(tran_eval(d, op["i(vsm)"][0], tr, mut), op_phys=phys(op, vdd))
            if not r["op_phys"]:
                r["verdict"] = "REJECT"
    with open(base + ".json", "w") as f:
        json.dump(r, f, indent=1)
    print(json.dumps({k: v for k, v in r.items() if k not in ("trim", "I_T", "crossings")}))
    return r


def tunept(out, stage, rt, r1):
    """WO-64: one tune point (tt/27/3.3 dct with the transient hint) -> OUT/tune_s<stage>_<rt>.json"""
    rt, r1 = float(rt), float(r1)
    base = os.path.join(out, f"tune_s{stage}_{rt:g}")
    hd = sim(deck("hint", "tt", -40, 3.3, ratio=rt, out=base + "_hint.csv", r1=r1), base + "_hint")
    hint = None if hd is None else {k[2:-1]: v[-1] for k, v in hd.items() if k.startswith("v(")}
    d = sim(deck("dct", "tt", None, 3.3, ratio=rt, out=base + ".csv", r1=r1, hint=hint), base)
    if d is None or not phys(d, 3.3):
        res = dict(ratio=rt, r1=r1, fail=True)
    else:
        i27, dmax, dmin, slope = tc_eval(d)
        res = dict(ratio=rt, r1=r1, i27_uA=i27 * 1e6, slope_pct=100 * slope, tc_max_pct=100 * dmax,
                   tc_min_pct=100 * dmin, tc_abs_pct=100 * max(dmax, -dmin))
    json.dump(res, open(base + ".tj", "w"))
    print(res)


def tunejobs(out, stage, jobfile):
    """Stage 1: R1 = R1_S1, ratio grid TUNE1. Stage 2: R1 rescaled to I_TGT, ratio best +-0.1 in 0.05 steps."""
    me = os.path.abspath(__file__)
    if stage == "1":
        pts = [(rt, R1_S1) for rt in TUNE1]
    else:
        s1 = json.load(open(os.path.join(out, "tune1.json")))
        pts = [(round(s1["ratio"] + 0.05 * k, 3), s1["r1"]) for k in range(-2, 3)]
    with open(jobfile, "w") as f:
        f.write("\n".join(f"python {me} tunept {os.path.abspath(out)} {stage} {rt:g} {r1:.5g}" for rt, r1 in pts) + "\n")


def tunepick(out, stage):
    tab = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out))
           if f.startswith(f"tune_s{stage}_") and f.endswith(".tj")]
    ok = sorted((t for t in tab if not t.get("fail")), key=lambda t: t["ratio"])
    best = min(ok, key=lambda t: t["tc_abs_pct"])
    # I ~ 1/R at fixed ratio: rescale R1 so the tt/27 master current lands on I_TGT
    r1 = best["r1"] * best["i27_uA"] * 1e-6 / I_TGT
    edge = best is ok[0] or best is ok[-1]
    res = dict(ratio=best["ratio"], r1=round(r1, 2), best=best, edge=edge, grid=tab)
    json.dump(res, open(os.path.join(out, "tune1.json" if stage == "1" else "tune.json"), "w"), indent=1)
    print(f"stage {stage}: ratio {best['ratio']} TC {best['tc_min_pct']:+.2f}/{best['tc_max_pct']:+.2f} % "
          f"I27 {best['i27_uA']:.4f} uA at R1 {best['r1']} -> R1 {r1:.2f}" + (" GRID EDGE" if edge else ""))


def jobs(out, jobfile):
    me = os.path.abspath(__file__)
    py = f"python {me} run {os.path.abspath(out)}"
    L = [f"{py} tran {c} {t} {v} none {tr:g}" for c, t, v in TRAN for tr in TRS]          # long ones first
    L += [f"{py} tran {c} {t} 3.0 nosu {tr:g}" for c, t in (("ss", -40), ("ff", 125)) for tr in TRS]
    L += [f"{py} tran {c} {t} 3.0 early 1e-06" for c, t in (("ss", -40), ("ff", 125))]
    L += [f"{py} tran tt 27 3.3 hy1 1e-06", f"{py} tran sf -40 3.0 hy1 1e-06", f"{py} tran tt 27 3.3 hold0 1e-06",
          f"{py} tran tt 27 3.3 nocnt 0.01", f"{py} tran ss -40 3.0 nocnt 0.01", f"{py} tran tt 27 3.3 slow 0.01",
          f"{py} tran sf -40 3.0 slow 0.01", f"{py} tran ss -40 3.0 earlyx 1e-06", f"{py} tran ff 125 3.0 earlyx 1e-06"]
    L += [f"{py} dci {c} {t} 3.0" for c in CORNERS for t in TEMPS] + [f"{py} dci ss -40 3.0 nosu"]
    L += [f"{py} dct {c} 27 {v}" for c, v in DCT]
    L += [f"{py} dct tt 27 3.3 ptat", f"{py} dct tt 27 3.3 trim_open", f"{py} dct sf 27 3.0 oldhint", f"{py} dct sf 27 3.0 zhint", f"{py} dct sf 27 3.0 zhintnk",
          f"{py} dct ff 27 3.6 zhint", f"{py} dct ss 27 3.0 zhint", f"{py} dcv tt 27 3.3",
          f"{py} dcv ss -40 3.0", f"{py} dcv ff 125 3.6"]
    L += [f"{py} loop {c} {t} 3.0" for c in CORNERS for t in TEMPS]
    L += [f"{py} loop sf 27 3.0 noskew", f"{py} loop ff 125 3.0 noskew"]
    with open(jobfile, "w") as f:
        f.write("\n".join(L) + "\n")


EXPECT = {"none": "ACCEPT", "nosu": "REJECT", "ptat": "REJECT", "trim_open": "REJECT", "early": "REJECT",
          "noskew": "REJECT", "hy1": "REJECT", "hold0": "REJECT", "nocnt": "REJECT", "oldhint": "INFO",   # WO-87: retired (lands on the physical point; zhint/zhintnk replace it)
          "slow": "REJECT", "earlyx": "REJECT", "zhint": "ACCEPT", "zhintnk": "REJECT"}


def summary(out):
    R = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out))
         if f.endswith(".json") and not f.startswith("tune")]
    print("tune ratio R2/R1, R1 um =", params_of(out), "| N_HY", N_HY, "TRANFIX", TRANFIX, "| R_K", round(R_K, 3), "SKEW", SKEW, "CMP_SKEW", CMP_SKEW)
    bad = 0
    for r in R:
        exp = "INFO" if r["kind"] == "dcv" else EXPECT.get(r["mut"], "ACCEPT")
        good = exp == "INFO" or r["verdict"] == exp
        bad += not good
        if r["kind"] == "dct":
            s = (f"I27 {r.get('i27_uA', 0):.4f} uA TC {r.get('tc_min_pct', 0):+.2f}/{r.get('tc_max_pct', 0):+.2f} % "
                 f"own {r.get('own_uA_27', 0):.2f}/{r.get('own_uA_max', 0):.2f} uA thr {r.get('thr_min', 0):.2f}.."
                 f"{r.get('thr_max', 0):.2f} VR1 {r.get('vr1_mV_min', 0):.1f}..{r.get('vr1_mV_max', 0):.1f} mV "
                 f"okmin {r.get('ok_min_frac', 0):.2f} phys {r.get('phys')} trim_ok {r.get('trim_ok')} "
                 f"I0err {r.get('i0_err_pct', 0):+.2f} % hint {fmt(r.get('i_hint_uA'))} uA agree "
                 f"{r.get('hint_agree_pct', 0):.3f} % Rlen {r.get('r_len_um', 0):.0f} um ")
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
            pl = " ".join(f"[{p['rise_us']:.1f}us w{p['width_us']:.1f} V{p['vdd']:.2f} I{p['i_frac']:.2f}"
                          f"{' F' if p['final'] else ''}]" for p in r.get("ok_pulses", []))
            s = (f"idc {r.get('idc_uA', 0):.4f} iend {r.get('iend_uA', 0):.4f} uA dev10us(info) {r.get('dev_win_pct', 0):.3f} % "
                 f"pulses {pl} pre-covered {r.get('pre_pulse_covered')} "
                 f"t90 {fmt(r.get('t90_after_ramp_us'))} t1% {fmt(r.get('t1pct_after_ramp_us'))} tok "
                 f"{fmt(r.get('tok_after_ramp_us'))} us settle-after-ok {fmt(r.get('settle_after_ok_us'))} us "
                 f"VDD@ok {fmt(r.get('vdd_at_ok'))} I@ok {fmt(r.get('I_at_ok_frac'))} rises {r.get('ok_rises')} "
                 f"Imax {fmt(r.get('i_max_frac'))} op_phys {r.get('op_phys')} rel {fmt(r.get('rel_after_ramp_us'))} us "
                 f"dev@rel {r.get('dev_rel_pct', 0):.3f} % settled {r.get('settled_before_rel')} "
                 f"win {fmt(r.get('win_after_rel_us'))} us hold/settle {fmt(r.get('margin_hold'))} "
                 f"D89 settle-after-final {fmt(r.get('settle_after_final_ms'))} ms <= {fmt(r.get('lim_d89_ms'))} {r.get('d89_ok')}")
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
    if a[0] == "tunept":
        tunept(*a[1:5])
    elif a[0] == "tunejobs":
        tunejobs(a[1], a[2], a[3])
    elif a[0] == "tunepick":
        tunepick(a[1], a[2])
    elif a[0] == "jobs":
        jobs(a[1], a[2])
    elif a[0] == "run":
        os.makedirs(a[1], exist_ok=True)
        run(*a[1:])
    elif a[0] == "summary":
        sys.exit(1 if summary(a[1]) else 0)
