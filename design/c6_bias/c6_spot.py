#!/usr/bin/env python3
"""C6 spot sims: current-mode bandgap reference core (Banba type), 3-bit trim copies, start-up.

WO-45 (C6a) deck, extended in WO-50 (C6b, start-up fix). Stage-1 spot deck for DESIGN.md section 6 (not the final
C6 netlist; the netlist + full tb come after the review). Runs on the sandbox only (ngspice, sky130A via PDK_ROOT).

  python c6_spot.py tune OUT                       # tt/27: R2/R1 grid, slope-zero ratio -> OUT/tune.json
  python c6_spot.py jobs OUT JOBFILE               # job list for scripts/lpool.sh
  python c6_spot.py run OUT KIND CORNER TEMP VDD [MUT] [TR]
        KIND dct  = .dc temp -40..125 (master current, 8 trim-code copies, own current, leaker/threshold)
             dcv  = .dc VDD 2.8..3.8 at TEMP (PSRR info)
             dci  = DC initial-state test: one-point .dc from .nodeset all nodes = 0 and = VDD
             tran = VAPWR PWL 0 -> VDD over TR seconds, uic (no .op), start-up
             loop = loop broken at the M5 gate (o1 -> o1x), .dc Vx: equilibria + core differential vs current (INFO)
        MUT  none | nosu (start-up removed: Mpo) | early (start-up released early: Mk/Mkh x16)
             | su45 (the WO-45 start-up, proportional Ms on tsu) | ptat (both R2 open) | trim_open (LSB leg open)
  python c6_spot.py summary OUT                    # verdict table -> stdout

Core (DESIGN.md 2): M1/M2 = 17 PMOS units each from VG; Q1 1x and Q2 8x pnp_05v5 W3p40; R1 in series with Q2;
R2 from each of nodes A, B to ground. Amp: PMOS pair (gate A on the diode side, gate B on the output side), NMOS
mirror load, Cc on o1; stage 2 = NMOS M5 into PMOS diode M6 (8 units) on VG; Cvg 1 pF VG -> VDD.

Start-up (WO-50, DESIGN.md 6): leaker (8 x PMOS L 20 in series, gate 0) pulls tsu up; Mk (gate VN, 0.21 x the
master diode) pulls tsu down, so tsu falls once I_master > I_lk / 0.21 (release threshold); Mkh (0.105 x, switched
in by ok) adds hysteresis once released. ok = NOT tsu (bias_ok), sua = NOT ok (start-up active, rail-to-rail).
While ok is low, Mpo (one unit PMOS, ~1 uA) pulls the amp output o1 up (M5 on); no device forces VG (WO-50 smoke:
a hard VG pull-down Ms drove I to 20x, the amp slammed o1 to 0 on release and the start-up relaxed 41 times). The amp
overpowers Mpo once the core is in its normal region, so the current stays bounded and the loop settles from above, never through the low-current region where the core differential
V_B - V_A is ~0 (both pnps off, both branches are just R2; WO-50 finding). After release Mpo is off (gate
at VDD): nothing is injected into the core.
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
R1_L = 82.0                    # um of 0p69 xhrpoly (~238 kOhm)
CC, CVG = 3e-12, 1e-12
VSENSE = 0.9                   # trim-copy drain sense voltage
TEMPS = (-40, 27, 125)
CORNERS = ("tt", "ss", "ff", "sf", "fs")
DCT = [("tt", 3.3), ("ss", 3.0), ("ff", 3.6), ("fs", 3.0), ("sf", 3.0)]
TRAN = [("tt", 27, 3.3)] + [(c, t, 3.0) for c in CORNERS for t in (-40, 125)]   # SPEC row 104 + WO-50 item 3
TRS = (1e-6, 1e-2)
LIM_TC, LIM_STEP = 0.03, 0.06
EPS_TRIM, RESID = 0.19, 0.03
COVER = (1 + EPS_TRIM) / (1 - EPS_TRIM) * (1 - RESID) / (1 + RESID)
# start-up (WO-50)
NLK = 8                        # leaker: NLK x unit PMOS in series, gate 0
MN_W, MN_L = 2.0, 4.0          # master NMOS diode
MK_W, MK_L = 0.42, 4.0         # Mk: 0.21 x master diode -> release at I_lk / 0.21
MKH_W, MKH_L = 0.42, 8.0       # Mkh: +0.105 x when ok is high (hysteresis 1.5 : 1)
MPO_W, MPO_L = 0.42, 20.0      # o1 pull-up while sua is high: one unit PMOS, ~1 uA, the amp can overpower it
R_K = (MK_W / MK_L) / (MN_W / MN_L)
R_KH = (MKH_W / MKH_L) / (MN_W / MN_L)
# gates (WO-50 exit + DESIGN.md 6)
TSET, LIM_SU = 10e-6, 0.01     # within +-1 % of DC from end of ramp + 10 us to the end
IOK_MIN = 0.5                  # bias_ok's final assertion only with I >= 50 % of DC
IDC_MIN = 0.75e-6              # separator good / low state (low states seen 0.11-0.51 uA, good 1.04-1.08 uA)
THR_MAX = 0.8                  # release threshold I_lk / (R_K * I_master) at the operating point
DCI_AGREE = 0.005


def x(name, d, g, s, b, dev, w, l, m=1):
    return f"X{name} {d} {g} {s} {b} {dev} w={w:g} l={l:g} m={m}"


def deck(kind, corner, temp, vdd, mut="none", tr=1e-6, ratio=4.6, out="o.csv", init=None):
    r2l = R1_L * ratio
    L = [f"* c6_spot {kind} {corner} {temp} {vdd} {mut} {tr:g} ratio {ratio:.4f} init {init}", f".lib {LIB} {corner}",
         ".option gmin=1e-15 reltol=1e-5 abstol=1e-14"]
    if kind == "tran":
        L.append(f"Vdd vdd 0 pwl(0 0 10n 0 {10e-9 + tr:.6g} {vdd})")
    else:
        L.append(f"Vdd vdd 0 {vdd}")
    if kind != "dct":
        L.append(f".temp {temp}")
    # core
    L += [x("m1", "a", "vg", "vdd", "vdd", P5, UW, UL, N_CORE), x("m2", "b", "vg", "vdd", "vdd", P5, UW, UL, N_CORE),
          f"Xq1 0 0 a {PNP} m=1", f"Xq2 0 0 c {PNP} m={NPNP}", f"Xr1 b c 0 {RX} l={R1_L:.4g}"]
    if mut != "ptat":
        L += [f"Xr2a a 0 0 {RX} l={r2l:.4g}", f"Xr2b b 0 0 {RX} l={r2l:.4g}"]
    g5 = "o1x" if kind == "loop" else "o1"
    L += [x("mt", "t", "vg", "vdd", "vdd", P5, UW, UL, N_TAIL),
          x("ma", "n1", "a", "t", "t", P5, 4, 4), x("mb", "o1", "b", "t", "t", P5, 4, 4),
          x("ml1", "n1", "n1", "0", "0", N5, 1, 8), x("ml2", "o1", "n1", "0", "0", N5, 1, 8),
          f"Cc o1 0 {CC:g}", x("m5", "vg", g5, "0", "0", N5, 2, 8),
          x("m6", "vg", "vg", "vdd", "vdd", P5, UW, UL, N_M6), f"Cvg vg vdd {CVG:g}"]
    if kind == "loop":
        L.append("Vx o1x 0 0")
    # start-up + bias_ok
    nodes = ["lk0"] + [f"l{i}" for i in range(1, NLK)] + ["tsu"]
    L += ["Vlk vdd lk0 0"] + [x(f"lk{i}", nodes[i + 1], "0", nodes[i], "vdd", P5, UW, UL) for i in range(NLK)]
    L += [x("mip", "ok", "tsu", "vdd", "vdd", P5, 1, 1), x("min", "ok", "tsu", "0", "0", N5, 1, 1)]
    if mut == "su45":
        L += [x("mk", "tsu", "vn", "0", "0", N5, 2, 4), x("ms", "vg", "tsu", "0", "0", N5, 1, 1)]
    else:
        kw = 16 if mut == "early" else 1
        L += [x("mk", "tsu", "vn", "0", "0", N5, MK_W * kw, MK_L), x("mkh", "tsu", "vn", "hk", "0", N5, MKH_W * kw, MKH_L),
              x("mhs", "hk", "ok", "0", "0", N5, 1, 1),
              x("mip2", "sua", "ok", "vdd", "vdd", P5, 1, 1), x("min2", "sua", "ok", "0", "0", N5, 1, 1)]
        if mut != "nosu":
            L += [x("mpo", "o1", "ok", "vdd", "vdd", P5, MPO_W, MPO_L)]
    # master leg (code 100) into the NMOS diode VN
    L += [x("mm", "mo", "vg", "vdd", "vdd", P5, UW, UL, G0 + CODE_RESET), "Vsm mo vn 0",
          x("mn", "vn", "vn", "0", "0", N5, MN_W, MN_L)]
    if init is not None:
        nn = ["a", "b", "c", "t", "n1", "o1", "vg", "tsu", "ok", "vn", "mo"] + nodes[1:-1]
        if mut != "su45":
            nn += ["sua", "hk"]
        val = 0.0 if init == "0" else vdd
        L.append(".nodeset " + " ".join(f"v({n})={val:g}" for n in nn))
    vecs = ["i(vsm)", "i(vdd)", "v(vg)", "v(tsu)", "v(ok)", "i(vlk)"]
    if kind in ("dct", "dci"):
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
        vecs += [f"i(vs{k})" for k in range(8)] + ["v(a)", "v(b)", "v(o1)"]
        an = ".dc temp -40 125 5" if temp is None else f".dc temp {temp} {temp} 1"
    elif kind == "dcv":
        an = ".dc vdd 2.8 3.8 0.05"
    elif kind == "loop":
        an = ".dc vx 0 2.0 0.002"
        vecs = ["i(vsm)", "v(o1)", "v(a)", "v(b)", "v(vg)", "v(tsu)"]
    else:
        tstop = 10e-9 + tr + (60e-6 if tr < 1e-4 else 200e-6)
        tmax = 5e-9 if tr < 1e-4 else 2e-6
        an = f".tran {tmax:.3g} {tstop:.6g} 0 {tmax:.3g} uic"
        L.append(".option method=gear")
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


def ratio_of(out):
    try:
        return json.load(open(os.path.join(out, "tune.json")))["ratio"]
    except OSError:
        return 4.6


def dc_point(out, tag, corner, temp, vdd, ratio, mut="none", init=None):
    sfx = "_op" if init is None else f"_op{init}"
    d = sim(deck("dci", corner, temp, vdd, mut, ratio=ratio,
                 out=os.path.join(out, tag + sfx + ".csv"), init=init), os.path.join(out, tag + sfx))
    return d


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
                        cover=I[7] / I[0], eps_lo_pct=100 * (itgt * (1 - RESID) / I[7] - 1),
                        eps_hi_pct=100 * (itgt * (1 + RESID) / I[0] - 1),
                        adj_max=max(I[k + 1] / I[k] for k in range(7)), lo_pct=100 * (I[0] / I[CODE_RESET] - 1),
                        hi_pct=100 * (I[7] / I[CODE_RESET] - 1)))
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
                           stable=s1 < s0, va=d["v(a)"][k], vb=d["v(b)"][k]))
    st = [c for c in cr if c["stable"] and c["i_uA"] > 0.01]
    ig = max((c["i_uA"] for c in st), default=None)
    prof = {}
    if ig:
        for fr in (0.1, 0.25, 0.5, 0.75, 0.9):
            k = min(range(len(I)), key=lambda j: abs(I[j] * 1e6 - fr * ig))
            prof[f"{fr:g}"] = dict(dv_mV=1e3 * dv[k], va=d["v(a)"][k])
    return dict(crossings=cr, i_good_uA=ig, n_stable=len(st), dv_profile=prof)


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
    started = (dev <= LIM_SU and okw and iok is not None and iok >= IOK_MIN and idc >= IDC_MIN)
    return dict(idc_uA=idc * 1e6, iend_uA=I[-1] * 1e6, end_err_pct=100 * (I[-1] / idc - 1), dev_win_pct=100 * dev,
                t90_after_ramp_us=None if t90 is None else (t90 - tend) * 1e6,
                t1pct_after_ramp_us=None if t1 is None else (t1 - tend) * 1e6,
                tok_after_ramp_us=None if tok is None else (tok - tend) * 1e6, I_at_ok_frac=iok, ok_rises=rises,
                i_max_frac=max(I) / idc, ok_end=ok[-1], vg_end=d["v(vg)"][-1], tsu_end=d["v(tsu)"][-1],
                va_end=d["v(a)"][-1], vb_end=d["v(b)"][-1], o1_end=d["v(o1)"][-1],
                verdict="ACCEPT" if started else "REJECT")


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
            own = -d["i(vdd)"][j27]
            tr_res, tr_ok = trim_eval(d, mut)
            tc_ok = max(dmax, -dmin) <= LIM_TC
            thr = [d["i(vlk)"][j] / (R_K * d["i(vsm)"][j]) for j in range(len(T))]
            r.update(i27_uA=i27 * 1e6, tc_max_pct=100 * dmax, tc_min_pct=100 * dmin, slope_pct=100 * slope,
                     own_uA_27=own * 1e6, own_uA_max=max(-v for v in d["i(vdd)"]) * 1e6,
                     tsu_max_on=max(d["v(tsu)"]), ok_min=min(d["v(ok)"]), ilk_uA=[1e6 * v for v in d["i(vlk)"]][::11],
                     thr_min=min(thr), thr_max=max(thr),
                     I_T={f"{t:g}": i * 1e6 for t, i in zip(T, d["i(vsm)"]) if t in TEMPS or t == 25},
                     tc_ok=tc_ok, trim=tr_res, trim_ok=tr_ok)
            r["verdict"] = "ACCEPT" if (tc_ok and tr_ok and max(thr) <= THR_MAX) else "REJECT"
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
                     psrr_dB=math.log10(abs((0.6 / 3.3) / rel)) * 20 if rel else 999, verdict="INFO")
    elif kind == "dci":
        res = {}
        for init in ("0", "v"):
            d = dc_point(out, tag, corner, temp, vdd, ratio, mut, init)
            res[init] = None if d is None else dict(i_uA=1e6 * d["i(vsm)"][0], vg=d["v(vg)"][0], tsu=d["v(tsu)"][0],
                                                    ok=d["v(ok)"][0], va=d["v(a)"][0], vb=d["v(b)"][0],
                                                    o1=d["v(o1)"][0])
        if None in res.values():
            r["verdict"] = "SIMFAIL"
        else:
            i0, iv = res["0"]["i_uA"], res["v"]["i_uA"]
            agree = abs(i0 - iv) / max(i0, iv, 1e-9)
            r.update(init0=res["0"], initv=res["v"], agree_pct=100 * agree,
                     verdict="ACCEPT" if (agree <= DCI_AGREE and min(i0, iv) * 1e-6 >= IDC_MIN
                                          and min(res["0"]["ok"], res["v"]["ok"]) > 0.9 * vdd) else "REJECT")
    elif kind == "loop":
        d = sim(deck("loop", corner, temp, vdd, mut, ratio=ratio, out=base + ".csv"), base)
        r.update(loop_eval(d) if d else {}, verdict="INFO" if d else "SIMFAIL")
    else:
        dd = dc_point(out, tag, corner, temp, vdd, ratio, mut if mut in ("su45", "early") else "none")
        d = sim(deck("tran", corner, temp, vdd, mut, tr=tr, ratio=ratio, out=base + ".csv"), base)
        if d is None or dd is None:
            r["verdict"] = "SIMFAIL"
        else:
            r.update(tran_eval(d, dd["i(vsm)"][0], tr))
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
        if d is None:
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
    L += [f"{py} tran {c} {t} 3.0 {m} {tr:g}" for m in ("nosu", "early") for c, t in (("ss", -40), ("ff", 125))
          for tr in TRS]
    L += [f"{py} tran tt 27 3.3 su45 {tr:g}" for tr in TRS]
    L += [f"{py} dct {c} 27 {v}" for c, v in DCT]
    L += [f"{py} dct tt 27 3.3 ptat", f"{py} dct tt 27 3.3 trim_open", f"{py} dcv tt 27 3.3",
          f"{py} dcv ss -40 3.0", f"{py} dcv ff 125 3.6"]
    L += [f"{py} dci {c} {t} 3.0" for c in CORNERS for t in TEMPS]
    L += [f"{py} dci sf 27 3.0 su45", f"{py} dci ss -40 3.0 nosu"]
    L += [f"{py} loop {c} {t} {v} nosu" for c, t, v in (("tt", 27, 3.3), ("ss", -40, 3.0), ("sf", 27, 3.0),
                                                        ("ff", 125, 3.0))]
    with open(jobfile, "w") as f:
        f.write("\n".join(L) + "\n")


EXPECT = {"none": "ACCEPT", "nosu": "REJECT", "ptat": "REJECT", "trim_open": "REJECT", "early": "REJECT",
          "su45": "REJECT"}


def summary(out):
    R = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out))
         if f.endswith(".json") and f != "tune.json"]
    print("tune ratio R2/R1 =", ratio_of(out), "| R_K", round(R_K, 3), "R_KH", round(R_KH, 3))
    bad = 0
    for r in R:
        exp = "INFO" if r["kind"] in ("dcv", "loop") else EXPECT.get(r["mut"], "ACCEPT")
        good = r["verdict"] == exp
        bad += not good
        if r["kind"] == "dct":
            s = (f"I27 {r.get('i27_uA', 0):.4f} uA TC {r.get('tc_min_pct', 0):+.2f}/{r.get('tc_max_pct', 0):+.2f} % "
                 f"own {r.get('own_uA_27', 0):.2f}/{r.get('own_uA_max', 0):.2f} uA thr {r.get('thr_min', 0):.2f}.."
                 f"{r.get('thr_max', 0):.2f} trim_ok {r.get('trim_ok')} ")
            for q in r.get("trim", []):
                s += (f"| T{q['T']:g}: stepmin {q['step_min_u']:.2f}u stepmax {q['step_max_pct']:.2f}% "
                      f"cover {q['cover']:.4f} ")
        elif r["kind"] == "dcv":
            s = (f"I 3.0/3.3/3.6 {r.get('i30_uA', 0):.4f}/{r.get('i33_uA', 0):.4f}/{r.get('i36_uA', 0):.4f} uA "
                 f"PSRR {r.get('psrr_dB', 0):.1f} dB")
        elif r["kind"] == "dci":
            a, b = r.get("init0") or {}, r.get("initv") or {}
            s = (f"I from 0 / VDD {a.get('i_uA', 0):.4f} / {b.get('i_uA', 0):.4f} uA agree {r.get('agree_pct', 0):.3f} % "
                 f"vg {a.get('vg', 0):.3f}/{b.get('vg', 0):.3f} tsu {a.get('tsu', 0):.2f}/{b.get('tsu', 0):.2f} "
                 f"va {a.get('va', 0):.3f}/{b.get('va', 0):.3f}")
        elif r["kind"] == "loop":
            s = (f"stable eq {r.get('n_stable')} I_good {r.get('i_good_uA')} uA crossings "
                 + "; ".join(f"{c['i_uA']:.4f}uA {'S' if c['stable'] else 'U'}" for c in r.get("crossings", []))
                 + " | dV(B-A) mV at I/Igood " + " ".join(f"{k}:{v['dv_mV']:+.4f}(va {v['va']:.3f})"
                                                       for k, v in r.get("dv_profile", {}).items()))
        else:
            s = (f"idc {r.get('idc_uA', 0):.4f} iend {r.get('iend_uA', 0):.4f} uA dev(ramp+10us..) "
                 f"{r.get('dev_win_pct', 0):.3f} % t90 {fmt(r.get('t90_after_ramp_us'))} t1% "
                 f"{fmt(r.get('t1pct_after_ramp_us'))} tok {fmt(r.get('tok_after_ramp_us'))} us I@ok "
                 f"{fmt(r.get('I_at_ok_frac'))} rises {r.get('ok_rises')} Imax {fmt(r.get('i_max_frac'))} "
                 f"end vg/tsu/o1/va/vb {fmt(r.get('vg_end'))}/{fmt(r.get('tsu_end'))}/{fmt(r.get('o1_end'))}/"
                 f"{fmt(r.get('va_end'))}/{fmt(r.get('vb_end'))}")
        print(f"{r['tag']:<36} {r['verdict']:<7} (expect {exp}) {'OK' if good else 'MISMATCH'} :: {s}")
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
