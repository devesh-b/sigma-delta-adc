#!/usr/bin/env python3
"""WO-45 (C6a) spot sims: current-mode bandgap reference core (Banba type), 3-bit trim copies, start-up.

Stage-1 spot deck for DESIGN.md section 6 (not the final C6 netlist; the netlist + full tb come after the review).
Runs on the sandbox only (ngspice, sky130A via PDK_ROOT).

  python c6_spot.py tune OUT                       # tt/27: R2/R1 grid, slope-zero ratio -> OUT/tune.json
  python c6_spot.py jobs OUT JOBFILE               # stage-2 job list for scripts/lpool.sh
  python c6_spot.py run OUT KIND CORNER TEMP VDD [MUT] [TR]
        KIND dct  = .dc temp -40..125 (master current, 8 trim-code copies, own current)
             dcv  = .dc VDD 2.8..3.8 at TEMP (PSRR info)
             tran = VAPWR PWL 0 -> VDD over TR seconds, uic (no .op), start-up
        MUT  none | nosu (start-up pull-down removed) | ptat (both R2 open: PTAT-only core)
             | trim_open (LSB trim leg open in every copy)
  python c6_spot.py summary OUT                    # verdict table -> stdout

Core (DESIGN.md 2): M1/M2 = 17 PMOS units each from VG; Q1 1x and Q2 8x pnp_05v5 W3p40; R1 in series with Q2;
R2 from each of nodes A, B to ground. Amp: PMOS pair (gate A on the diode side, gate B on the output side), NMOS
mirror load, Cc on o1; stage 2 = NMOS M5 into PMOS diode M6 (8 units) on VG; Cvg 1 pF VG -> VDD (worst case for
start-up). Start-up: leaker (8 x PMOS L 20 series, gate 0) pulls tsu up; Mk (gate VN, master NMOS mirror) pulls tsu
down once the master runs; Ms (gate tsu) pulls VG down while tsu is high. bias_ok = NOT tsu.
Master leg = code 100 = G0 + 4 = 21 units into the NMOS diode VN. Trim copy k = G0 + k units (binary legs 1/2/4
through PMOS switches). Target (DESIGN.md 3) = GT = 19.8 units.
"""
import json
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
DCT = [("tt", 3.3), ("ss", 3.0), ("ff", 3.6), ("fs", 3.0), ("sf", 3.0)]
TRAN = [("tt", 27, 3.3), ("ss", -40, 3.0), ("ff", 125, 3.0)]   # SPEC row 104: 0 -> 3.0 V at ss/-40 and ff/125
TRS = (1e-6, 1e-2)
LIM_TC, LIM_STEP, COVER = 0.03, 0.06, 1.4126   # COVER = (G0+7)/G0 needed for +-20 % at +-3 % residual


def x(name, d, g, s, b, dev, w, l, m=1):
    return f"X{name} {d} {g} {s} {b} {dev} w={w:g} l={l:g} m={m}"


def deck(kind, corner, temp, vdd, mut="none", tr=1e-6, ratio=4.6, out="o.csv"):
    r2l = R1_L * ratio
    L = [f"* WO-45 c6_spot {kind} {corner} {temp} {vdd} {mut} {tr:g} ratio {ratio:.4f}", f".lib {LIB} {corner}",
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
    # amp: stage 1 (PMOS pair, self-biased tail from VG), stage 2 (M5 into diode M6 on VG)
    L += [x("mt", "t", "vg", "vdd", "vdd", P5, UW, UL, N_TAIL),
          x("ma", "n1", "a", "t", "t", P5, 4, 4), x("mb", "o1", "b", "t", "t", P5, 4, 4),
          x("ml1", "n1", "n1", "0", "0", N5, 1, 8), x("ml2", "o1", "n1", "0", "0", N5, 1, 8),
          f"Cc o1 0 {CC:g}", x("m5", "vg", "o1", "0", "0", N5, 2, 8),
          x("m6", "vg", "vg", "vdd", "vdd", P5, UW, UL, N_M6), f"Cvg vg vdd {CVG:g}"]
    # start-up + bias_ok
    nodes = ["vdd"] + [f"l{i}" for i in range(1, 8)] + ["tsu"]
    L += [x(f"lk{i}", nodes[i + 1], "0", nodes[i], "vdd", P5, UW, UL) for i in range(8)]
    L += [x("mk", "tsu", "vn", "0", "0", N5, 2, 4)]
    if mut != "nosu":
        L += [x("ms", "vg", "tsu", "0", "0", N5, 1, 1)]
    L += [x("mip", "ok", "tsu", "vdd", "vdd", P5, 1, 1), x("min", "ok", "tsu", "0", "0", N5, 1, 1)]
    # master leg (code 100) into the NMOS diode VN
    L += [x("mm", "mo", "vg", "vdd", "vdd", P5, UW, UL, G0 + CODE_RESET), "Vsm mo vn 0",
          x("mn", "vn", "vn", "0", "0", N5, 2, 4)]
    vecs = ["i(vsm)", "i(vdd)", "v(vg)", "v(tsu)", "v(ok)"]
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
        an = ".dc temp -40 125 5" if temp is None else f".dc temp {temp} {temp} 1"
    elif kind == "dcv":
        an = ".dc vdd 2.8 3.8 0.05"
    else:
        tstop = 10e-9 + tr + (60e-6 if tr < 1e-4 else 200e-6)
        tmax = 5e-9 if tr < 1e-4 else 2e-6
        an = f".tran {tmax:.3g} {tstop:.6g} 0 {tmax:.3g} uic"
        L.append(".option method=gear")
        vecs = ["i(vsm)", "v(ok)", "v(vdd)", "v(vg)", "v(tsu)"]
    L += [an, ".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=8", "run",
          f"wrdata {out} {' '.join(vecs)}", ".endc", ".end"]
    return "\n".join(L) + "\n", ["x"] + vecs


def sim(tv, path):
    text, names = tv
    with open(path + ".cir", "w") as f:
        f.write(text)
    p = subprocess.run(["ngspice", "-b", path + ".cir"], capture_output=True, text=True, timeout=3000)
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


def dc_point(out, tag, corner, temp, vdd, ratio):
    d = sim(deck("dct", corner, temp, vdd, ratio=ratio, out=os.path.join(out, tag + "_op.csv")),
            os.path.join(out, tag + "_op"))
    return None if d is None else d["i(vsm)"][0]


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
                        cover=I[7] / I[0], lo_pct=100 * (I[0] / I[CODE_RESET] - 1),
                        hi_pct=100 * (I[7] / I[CODE_RESET] - 1)))
    ok = all(r["step_min_u"] >= 0.5 and r["step_max_pct"] <= 100 * LIM_STEP and r["cover"] >= COVER for r in res)
    return res, ok


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
            r.update(i27_uA=i27 * 1e6, tc_max_pct=100 * dmax, tc_min_pct=100 * dmin, slope_pct=100 * slope,
                     own_uA_27=own * 1e6, own_uA_max=max(-v for v in d["i(vdd)"]) * 1e6,
                     tsu_max_on=max(d["v(tsu)"]), ok_min=min(d["v(ok)"]),
                     I_T={f"{t:g}": i * 1e6 for t, i in zip(T, d["i(vsm)"]) if t in TEMPS or t == 25},
                     tc_ok=tc_ok, trim=tr_res, trim_ok=tr_ok)
            r["verdict"] = "ACCEPT" if (tc_ok and tr_ok) else "REJECT"
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
                     psrr_dB=__import__("math").log10(abs((0.6 / 3.3) / rel)) * 20 if rel else 999,
                     verdict="INFO")
    else:
        idc = dc_point(out, tag, corner, temp, vdd, ratio)
        d = sim(deck("tran", corner, temp, vdd, mut, tr=tr, ratio=ratio, out=base + ".csv"), base)
        if d is None or idc is None:
            r["verdict"] = "SIMFAIL"
        else:
            t, I, ok, vd = d[list(d)[0]], d["i(vsm)"], d["v(ok)"], d["v(vdd)"]
            tend = 10e-9 + tr
            post = [k for k in range(len(t)) if t[k] >= tend]
            tail = [I[k] for k in post if t[k] >= t[-1] - 0.2 * (t[-1] - tend)]
            iend = I[-1]
            t90 = next((t[k] for k in range(len(t)) if I[k] >= 0.9 * idc), None)
            tok = next((t[k] for k in range(len(t)) if vd[k] > 1.0 and ok[k] > 0.5 * vd[k]), None)
            iok = I[t.index(tok)] / idc if tok is not None else None
            p2p = (max(tail) - min(tail)) / idc
            started = abs(iend / idc - 1) <= 0.02 and p2p <= 0.005 and ok[-1] > 0.9 * vd[-1]
            r.update(idc_uA=idc * 1e6, iend_uA=iend * 1e6, end_err_pct=100 * (iend / idc - 1), p2p_pct=100 * p2p,
                     t90_after_ramp_us=None if t90 is None else (t90 - tend) * 1e6,
                     tok_after_ramp_us=None if tok is None else (tok - tend) * 1e6, I_at_ok_frac=iok,
                     ok_end=ok[-1], vg_end=d["v(vg)"][-1], tsu_end=d["v(tsu)"][-1],
                     verdict="ACCEPT" if started else "REJECT")
    with open(base + ".json", "w") as f:
        json.dump(r, f, indent=1)
    print(json.dumps({k: v for k, v in r.items() if k not in ("trim", "I_T")}))
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
    for a, b in zip(ok, ok[1:]):                       # slope-zero crossing, linear interpolation
        if a["slope_pct"] * b["slope_pct"] <= 0:
            best = a["ratio"] + (b["ratio"] - a["ratio"]) * a["slope_pct"] / (a["slope_pct"] - b["slope_pct"])
            break
    json.dump(dict(ratio=best, grid=tab), open(os.path.join(out, "tune.json"), "w"), indent=1)
    print("ratio", best)


def jobs(out, jobfile):
    me = os.path.abspath(__file__)
    py = f"python {me} run {os.path.abspath(out)}"
    L = [f"{py} dct {c} 27 {v}" for c, v in DCT]
    L += [f"{py} dct tt 27 3.3 ptat", f"{py} dct tt 27 3.3 trim_open", f"{py} dcv tt 27 3.3",
          f"{py} dcv ss -40 3.0", f"{py} dcv ff 125 3.6"]
    L += [f"{py} tran {c} {t} {v} none {tr:g}" for c, t, v in TRAN for tr in TRS]
    L += [f"{py} tran {c} {t} {v} nosu {tr:g}" for c, t, v in TRAN[1:] for tr in TRS]
    with open(jobfile, "w") as f:
        f.write("\n".join(L) + "\n")


EXPECT = {"none": "ACCEPT", "nosu": "REJECT", "ptat": "REJECT", "trim_open": "REJECT"}


def summary(out):
    R = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out))
         if f.endswith(".json") and f != "tune.json"]
    print("tune ratio R2/R1 =", ratio_of(out))
    bad = 0
    for r in R:
        exp = EXPECT.get(r["mut"], "ACCEPT") if r["verdict"] != "INFO" else "INFO"
        good = r["verdict"] == exp
        bad += not good
        if r["kind"] == "dct":
            s = (f"I27 {r.get('i27_uA', 0):.4f} uA TC {r.get('tc_min_pct', 0):+.2f}/{r.get('tc_max_pct', 0):+.2f} % "
                 f"own {r.get('own_uA_27', 0):.2f} uA trim_ok {r.get('trim_ok')} ")
            for q in r.get("trim", []):
                s += (f"| T{q['T']:g}: stepmin {q['step_min_u']:.2f}u stepmax {q['step_max_pct']:.2f}% "
                      f"cover {q['cover']:.4f} c0 {q['lo_pct']:+.1f}% c7 {q['hi_pct']:+.1f}% ")
        elif r["kind"] == "dcv":
            s = (f"I 3.0/3.3/3.6 {r.get('i30_uA', 0):.4f}/{r.get('i33_uA', 0):.4f}/{r.get('i36_uA', 0):.4f} uA "
                 f"dI/I {r.get('dIrel_per_V_pct', 0):.2f} %/V PSRR {r.get('psrr_dB', 0):.1f} dB")
        else:
            s = (f"idc {r.get('idc_uA', 0):.4f} iend {r.get('iend_uA', 0):.4f} uA err {r.get('end_err_pct', 0):+.2f} % "
                 f"p2p {r.get('p2p_pct', 0):.3f} % t90 {r.get('t90_after_ramp_us')} us tok {r.get('tok_after_ramp_us')}"
                 f" us I@ok {r.get('I_at_ok_frac')} ok_end {r.get('ok_end', 0):.2f}")
        print(f"{r['tag']:<36} {r['verdict']:<7} (expect {exp}) {'OK' if good else 'MISMATCH'} :: {s}")
    print("VERDICT", "ACCEPT" if bad == 0 else f"MISMATCH {bad}")
    return bad


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
