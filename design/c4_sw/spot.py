#!/usr/bin/env python3
"""WO-46 (C4a) spot simulations: design-note support only, NOT the C4 gate testbench (that comes after review).

    python spot.py jobs OUTDIR                    # writes OUTDIR/jobs.txt, one `run` line per job (feed to lpool.sh)
    python spot.py run KIND CORNER MUT OUTDIR     # one job -> OUTDIR/<KIND>_<CORNER>_<MUT>.json (+ .log, csv deleted)
    python spot.py report OUTDIR                  # tables + verdicts -> OUTDIR/summary.md / summary.json; exit 2 if
                                                  # a job is missing, errored, or a broken copy fails to REJECT

KIND ron: DC sweep of 3.3 V TG candidates (nfet/pfet_g5v0d10v5, L 0.5) with bulks at the rails (body effect in),
          Ron = 1 mV / I. Variants in TGS; `nonly8` (NMOS only) is the broken copy of the Ron check.
KIND tim: 1.8 V fs clock (4 MHz, 10 ohm source) -> sky130_fd_sc_hvl__lsbuflv2hv_1 -> delay-based cross-coupled NAND
          non-overlap generator in hvl cells (VAPWR domain) with early/late phases for both halves, buffered outputs
          (true + complement) into CLOAD each. fs high = integrate half (C1 ph1), fs low = sample half (C1 ph2).
          MUT: none | overlap (feedback chains removed) | gbig (gap chain x4) | noearly (late phase = early) |
          lsload (+1 pF on the LS output).
Every metric is computed from waveform crossings; a missing crossing is an error, never a default (WORKFLOW 11.1).
"""
import json
import os
import subprocess
import sys

import numpy as np

PDK = os.path.join(os.environ.get("PDK_ROOT", "/home/mempool/.ciel"), os.environ.get("PDK", "sky130A"))
LIB = PDK + "/libs.tech/ngspice/sky130.lib.spice"
HVL = PDK + "/libs.ref/sky130_fd_sc_hvl/spice/sky130_fd_sc_hvl.spice"
PRE = "sky130_fd_pr__"
DIFF_EXT = 0.29
FS = 4e6
T = 1.0 / FS
VREF_MAX = 1.1 * 2.048            # overload 1.1 VREF on VREF+ / VIN
TOP_RANGE = (0.18, 2.22)          # D12 top-plate short: tp CM = V_ICM + Vin_cm - Vref_cm, Vin_cm 0..VREF (DESIGN.md 2.3)

# corner: (process, T degC, VAPWR, VDPWR)
CORNERS = {
    "tt_27": ("tt", 27, 3.3, 1.8), "ss_m40": ("ss", -40, 3.0, 1.62), "ss_125": ("ss", 125, 3.0, 1.62),
    "ff_m40": ("ff", -40, 3.6, 1.98), "ff_125": ("ff", 125, 3.6, 1.98), "sf_27": ("sf", 27, 3.3, 1.8),
    "fs_27": ("fs", 27, 3.3, 1.8), "ss_m40_ls": ("ss", -40, 3.6, 1.62), "ff_m40_ls": ("ff", -40, 3.0, 1.98)}
RON_CORNERS = ("tt_27", "ss_m40", "ss_125", "ff_125")
TIM_CORNERS = tuple(CORNERS)
BROKEN = {"overlap": ("g_min", ("tt_27", "ss_m40", "ff_m40")), "gbig": ("g50_max", ("tt_27", "ff_m40")),
          "noearly": ("early_min", ("tt_27", "ff_m40")), "lsload": ("ls_edge_max", ("tt_27", "ff_m40"))}

# TG candidates: name -> (W_n, W_p) um, L 0.5 both
TGS = {"in4": (4.0, 8.0), "in8": (8.0, 16.0), "in8p3": (8.0, 24.0), "ref2": (2.0, 4.0), "top1": (1.0, 2.0),
       "nonly8": (8.0, 0.0)}
INPUT_TGS = ("in4", "in8", "in8p3")

# generator knobs
K_G, C_G = 4, 70e-15              # gap chain: inverters (even), cap per node (smoke tt: 30 fF gave g50 1.85 ns, g 1.0 ns)
K_E, C_E = 2, 40e-15              # early->late chain (smoke tt: 10 fF gave 0.44 ns)
CLOAD = 200e-15                   # per phase output (true and complement)

LIM = dict(ron_max=1500.0, g_min=1.0e-9, g50_max=0.025 / FS, early_min=0.5e-9, t_half_min=0.45 / FS,
           edge_max=1.0e-9, ls_edge_max=1.0e-9)


def mos(name, d, g, s, b, dev, w, l):
    return (f"X{name} {d} {g} {s} {b} {PRE}{dev} w={w:g} l={l:g} m=1 ad={w * DIFF_EXT:.4g} as={w * DIFF_EXT:.4g} "
            f"pd={2 * (w + DIFF_EXT):.4g} ps={2 * (w + DIFF_EXT):.4g}")


def ctrl(csv, vecs):
    return [".control", "set wr_singlescale", "set wr_vecnames", "set numdgt=10", "run",
            f"wrdata {csv} {vecs}", ".endc", ".end"]


def deck_ron(corner, csv):
    p, t, va, _ = CORNERS[corner]
    L = [f"* WO-46 ron {corner}", f'.lib "{LIB}" {p}', f".temp {t}",
         ".option gmin=1e-15 reltol=1e-6 abstol=1e-15",
         f"Vdd vdd 0 {va}", "Vsig a 0 0", "Bb b 0 V = V(a) - 1e-3", "Vc c 0 1.0"]
    names = list(TGS) + ["off"]
    for k, (wn, wp) in TGS.items():
        L.append(f"Vm_{k} a am_{k} 0")
        L.append(mos(f"n_{k}", f"am_{k}", "vdd", "b", "0", "nfet_g5v0d10v5", wn, 0.5))
        if wp:
            L.append(mos(f"p_{k}", f"am_{k}", "0", "b", "vdd", "pfet_g5v0d10v5", wp, 0.5))
    # off-state leakage of the in8 TG (gates reversed), far side held at 1.0 V
    L += ["Vm_off a am_off 0", mos("n_off", "am_off", "0", "c", "0", "nfet_g5v0d10v5", 8.0, 0.5),
          mos("p_off", "am_off", "vdd", "c", "vdd", "pfet_g5v0d10v5", 16.0, 0.5)]
    L.append(f".dc Vsig 0 {va} 0.01")
    L += ctrl(csv, "v(a) " + " ".join(f"i(Vm_{k})" for k in names))
    return "\n".join(L) + "\n", names


def inv(nm, a, y, sz=1):
    return f"X{nm} {a} 0 0 vdd vdd {y} sky130_fd_sc_hvl__inv_{sz}"


def nand(nm, a, b, y):
    return f"X{nm} {a} {b} 0 0 vdd vdd {y} sky130_fd_sc_hvl__nand2_1"


def chain(pfx, a, y, k, cap):
    out, prev = [], a
    for i in range(k):
        nxt = y if i == k - 1 else f"{pfx}{i}"
        out += [inv(f"{pfx}i{i}", prev, nxt), f"C{pfx}{i} {nxt} 0 {cap:g}"]
        prev = nxt
    return out


PH = ("ie", "il", "se", "sl")


def deck_tim(corner, mut, csv):
    p, t, va, vd = CORNERS[corner]
    kg = K_G * (4 if mut == "gbig" else 1)
    L = [f"* WO-46 tim {corner} {mut}", f'.lib "{LIB}" {p}', f".include {HVL}", f".temp {t}",
         ".option reltol=1e-4", f"Vdd vdd 0 {va}", f"Vdl vdl 0 {vd}",
         f"Vclk clk0 0 PULSE(0 {vd} 20n 0.2n 0.2n {T / 2 - 0.2e-9:.6e} {T:.6e})", "Rclk clk0 fs1 10", "Cfs1 fs1 0 5f",
         "XLS fs1 vdl 0 0 vdd vdd fsh sky130_fd_sc_hvl__lsbuflv2hv_1", inv("fb", "fsh", "fshb")]
    if mut == "lsload":
        L.append("Cls fsh 0 1p")
    if mut == "overlap":
        sfb, ifb = "vdd", "vdd"                      # no feedback: phases = buffered fs / fs_b
    else:
        sfb, ifb = "sfb", "ifb"
        L += [inv("sli", "sl", "slb")] + chain("cs", "slb", "sfb", kg, C_G)
        L += [inv("ili", "il", "ilb")] + chain("ci", "ilb", "ifb", kg, C_G)
    # integrate half (fs high): a1 low = active. early ie = NOT a1; late il = NAND(a1, a1 delayed)
    L += [nand("a1", "fsh", sfb, "a1"), inv("ie", "a1", "ie")]
    L += [nand("a2", "fshb", ifb, "a2"), inv("se", "a2", "se")]
    if mut == "noearly":
        L += [nand("il", "a1", "vdd", "il"), nand("sl", "a2", "vdd", "sl")]
    else:
        L += chain("e1", "a1", "a1e", K_E, C_E) + [nand("il", "a1", "a1e", "il")]
        L += chain("e2", "a2", "a2e", K_E, C_E) + [nand("sl", "a2", "a2e", "sl")]
    for x in PH:   # true = 2 stages, complement = 3 stages (skew is measured, not hidden)
        L += [inv(f"{x}b1", x, f"{x}m", 2), inv(f"{x}b2", f"{x}m", f"{x}o", 4), f"C{x}o {x}o 0 {CLOAD:g}",
              inv(f"{x}c0", x, f"{x}n"), inv(f"{x}c1", f"{x}n", f"{x}k", 2), inv(f"{x}c2", f"{x}k", f"{x}c", 4),
              f"C{x}c {x}c 0 {CLOAD:g}"]
    tstop = 20e-9 + 3 * T
    L.append(f".tran 10p {tstop:.6e} 0 10p")
    vecs = ["fs1", "fsh"] + [f"{x}o" for x in PH] + [f"{x}c" for x in PH]
    L += ctrl(csv, " ".join(f"v({v})" for v in vecs))
    return "\n".join(L) + "\n", vecs, tstop


def cross(t, v, th, rising, t0, t1):
    m = np.nonzero((t >= t0) & (t <= t1))[0]
    if len(m) < 2:
        return None
    tt, vv = t[m], v[m]
    s = ((vv[:-1] < th) & (vv[1:] >= th)) if rising else ((vv[:-1] > th) & (vv[1:] <= th))
    k = np.nonzero(s)[0]
    if not len(k):
        return None
    i = k[0]
    return float(tt[i] + (th - vv[i]) * (tt[i + 1] - tt[i]) / (vv[i + 1] - vv[i]))


def sub(a, b):
    return None if a is None or b is None else a - b


def mn(xs):
    return None if any(x is None for x in xs) else min(xs)


def mx(xs):
    return None if any(x is None for x in xs) else max(xs)


def spice(deck, tag, out):
    open(os.path.join(out, ".spiceinit"), "w").write("set num_threads=1\n")
    fn = os.path.join(out, tag + ".sp")
    open(fn, "w").write(deck)
    env = dict(os.environ, OMP_NUM_THREADS="1")
    r = subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=900, env=env)
    log = r.stdout + r.stderr
    open(os.path.join(out, tag + ".log"), "w").write(log)
    bad = [ln for ln in log.splitlines() if ln.lower().startswith("error") or "timestep too small" in ln
           or "singular matrix" in ln.lower()]
    return r.returncode, bad


def run(kind, corner, mut, out):
    os.makedirs(out, exist_ok=True)
    tag = f"{kind}_{corner}_{mut}"
    csv = tag + ".csv"
    cp = os.path.join(out, csv)
    if os.path.exists(cp):
        os.remove(cp)          # never parse a stale csv
    res = dict(kind=kind, corner=corner, mut=mut, cond=CORNERS[corner], ok=False, err=None, m={})
    try:
        if kind == "ron":
            deck, names = deck_ron(corner, csv)
            stop = CORNERS[corner][2]
        else:
            deck, vecs, stop = deck_tim(corner, mut, csv)
        rc, bad = spice(deck, tag, out)
        if rc or bad or not os.path.exists(cp):
            raise RuntimeError(f"ngspice rc={rc} bad={bad[:3]} csv={os.path.exists(cp)}")
        d = np.loadtxt(cp, skiprows=1)
        os.remove(cp)
        x = d[:, 0]
        if abs(x[-1] - stop) > 1e-4 * stop:      # truncated run (WORKFLOW 11.2)
            raise RuntimeError(f"run ended at {x[-1]:g}, requested {stop:g}")
        res["m"] = metrics_ron(d, names, corner) if kind == "ron" else metrics_tim(d, vecs, corner)
        res["ok"] = True
    except Exception as e:     # recorded, report() fails on it
        res["err"] = repr(e)
    json.dump(res, open(os.path.join(out, tag + ".json"), "w"), indent=1)
    return res


def metrics_ron(d, names, corner):
    v = d[:, 1]
    m = {}
    for j, k in enumerate(names):
        i = np.abs(d[:, 2 + j])
        if k == "off":
            m["off_leak_max_A"] = float(i.max())
            continue
        ron = np.where(i > 0, 1e-3 / np.maximum(i, 1e-30), np.inf)
        rng = (v >= TOP_RANGE[0]) & (v <= TOP_RANGE[1]) if k == "top1" else (v <= VREF_MAX + 1e-9)
        jm = int(np.argmax(np.where(rng, ron, -1)))
        m[k] = dict(ron0=float(ron[0]), ron_max=float(ron[jm]), v_at_max=float(v[jm]),
                    ron_max_full=float(ron.max()), v_full=float(v[int(np.argmax(ron))]))
    return m


def metrics_tim(d, vecs, corner):
    va, vd = CORNERS[corner][2], CORNERS[corner][3]
    t = d[:, 0]
    w = {n: d[:, 1 + j] for j, n in enumerate(vecs)}
    te_r = 20e-9 + 2 * T
    te_f, te_f0 = te_r + T / 2, te_r - T / 2
    W = 80e-9
    lo, mid, hi = 0.1 * va, 0.5 * va, 0.9 * va

    def c(n, th, rising, t0):
        return cross(t, w[n], th, rising, t0 - 2e-9, t0 + W)

    m = {}
    tin_r, tin_f = c("fs1", vd / 2, True, te_r), c("fs1", vd / 2, False, te_f)
    tls_r, tls_f = c("fsh", mid, True, te_r), c("fsh", mid, False, te_f)
    m["ls_delay_r"], m["ls_delay_f"] = sub(tls_r, tin_r), sub(tls_f, tin_f)
    m["ls_edge"] = mx([sub(c("fsh", hi, True, te_r), c("fsh", lo, True, te_r)),
                       sub(c("fsh", lo, False, te_f), c("fsh", hi, False, te_f))])
    m["ls_duty_err"] = None if tls_r is None or tls_f is None else (tls_f - tls_r) / T - 0.5
    # transitions: at fs rise, sample (se, sl) off and integrate (ie, il) on; at fs fall the reverse
    for tag, te, off, on in (("r", te_r, ("se", "sl"), ("ie", "il")), ("f", te_f, ("ie", "il"), ("se", "sl"))):
        m[f"g_n_{tag}"] = sub(mn([c(x + "o", lo, True, te) for x in on]), mx([c(x + "o", lo, False, te) for x in off]))
        m[f"g_p_{tag}"] = sub(mn([c(x + "c", hi, False, te) for x in on]), mx([c(x + "c", hi, True, te) for x in off]))
        m[f"g50_{tag}"] = sub(mn([c(x + "o", mid, True, te) for x in on]), mx([c(x + "o", mid, False, te) for x in off]))
        m[f"early_{tag}"] = sub(c(off[1] + "o", mid, False, te), c(off[0] + "o", mid, False, te))
    m["t_half_il"] = sub(c("ilo", mid, False, te_f), c("ilo", mid, True, te_r))
    m["t_half_sl"] = sub(c("slo", mid, False, te_r), c("slo", mid, True, te_f0))
    edges = []
    for x in PH:
        for s in ("o", "c"):
            for te in (te_r, te_f):
                edges.append(sub(c(x + s, hi, True, te), c(x + s, lo, True, te)) if c(x + s, lo, True, te) else
                             sub(c(x + s, lo, False, te), c(x + s, hi, False, te)))
    m["edge_max"] = mx(edges)
    m["skew_tc_max"] = mx([abs(sub(c(x + "c", mid, False, te_r) or c(x + "c", mid, True, te_r),
                                   c(x + "o", mid, True, te_r) or c(x + "o", mid, False, te_r)) or 0) for x in PH])
    return m


def checks(m):
    """name -> (value, pass) for the tim gates proposed in DESIGN.md section 8 (spot limits)."""
    g = mn([m.get(k) for k in ("g_n_r", "g_n_f", "g_p_r", "g_p_f")])
    g50 = mx([m.get("g50_r"), m.get("g50_f")])
    e = mn([m.get("early_r"), m.get("early_f")])
    th = mn([m.get("t_half_il"), m.get("t_half_sl")])
    out = dict(g_min=(g, g is not None and g >= LIM["g_min"]), g50_max=(g50, g50 is not None and g50 <= LIM["g50_max"]),
               early_min=(e, e is not None and e >= LIM["early_min"]),
               t_half_min=(th, th is not None and th >= LIM["t_half_min"]),
               edge_max=(m.get("edge_max"), m.get("edge_max") is not None and m["edge_max"] <= LIM["edge_max"]),
               ls_edge_max=(m.get("ls_edge"), m.get("ls_edge") is not None and m["ls_edge"] <= LIM["ls_edge_max"]))
    return out


def joblist():
    j = [("ron", c, "none") for c in RON_CORNERS] + [("tim", c, "none") for c in TIM_CORNERS]
    for mut, (_, cs) in BROKEN.items():
        j += [("tim", c, mut) for c in cs]
    return j


def ns(x):
    return "MISSING" if x is None else f"{x * 1e9:.2f}"


def report(out):
    rows, fail = {}, []
    for k, c, mu in joblist():
        fn = os.path.join(out, f"{k}_{c}_{mu}.json")
        if not os.path.exists(fn):
            fail.append(f"missing {k}_{c}_{mu}")
            continue
        r = json.load(open(fn))
        if not r["ok"]:
            fail.append(f"error {k}_{c}_{mu}: {r['err']}")
        rows[(k, c, mu)] = r
    L = ["# WO-46 spot sims (generated by design/c4_sw/spot.py report)", "",
         f"Limits (spot, proposed in DESIGN.md 8): {json.dumps(LIM)}", "",
         "## TG Ron (DC, body effect in), ohm: Ron at 0 V / max over 0..1.1 VREF (top1: 0.18..2.22 V) @ V / max over 0..VAPWR",
         "", "| corner | " + " | ".join(TGS) + " | off leak in8 (A) |", "|---" * (len(TGS) + 2) + "|"]
    for c in RON_CORNERS:
        r = rows.get(("ron", c, "none"))
        if not r or not r["ok"]:
            continue
        m = r["m"]
        cells = [f"{m[k]['ron0']:.0f} / **{m[k]['ron_max']:.0f}** @{m[k]['v_at_max']:.2f} / {m[k]['ron_max_full']:.3g}"
                 for k in TGS]
        L.append(f"| {c} {r['cond']} | " + " | ".join(cells) + f" | {m['off_leak_max_A']:.2e} |")
    rg = rows.get(("ron", "ss_m40", "none"))
    if rg and rg["ok"]:
        L.append("")
        for k in INPUT_TGS:
            v = rg["m"][k]["ron_max"]
            L.append(f"- input TG {k} @ ss/-40/3.0: Ron_max {v:.0f} ohm -> {'PASS' if v <= LIM['ron_max'] else 'FAIL'} (<= 1500)")
        v = rg["m"]["nonly8"]["ron_max"]
        ok = v > LIM["ron_max"]
        L.append(f"- broken copy nonly8 (no PMOS) @ ss/-40/3.0: Ron_max {v:.3g} ohm -> {'REJECT (good)' if ok else 'PASSES (check is blind)'}")
        if not ok:
            fail.append("broken copy nonly8 not rejected")
    L += ["", "## LS + non-overlap generator, 4 MHz, ns (g: switch-threshold gap 10 %/90 %, g50: 50 % gap)", "",
          "| corner | mut | LS d r/f | LS edge | duty err % | g_n r/f | g_p r/f | g50 r/f | early r/f | t_half il/sl | edge max | skew t-c | verdict |",
          "|---" * 13 + "|"]
    for k, c, mu in joblist():
        r = rows.get((k, c, mu))
        if k != "tim" or not r or not r["ok"]:
            continue
        m = r["m"]
        ck = checks(m)
        bad = [n for n, (_, ok) in ck.items() if not ok]
        if mu == "none":
            verdict = "PASS" if not bad else "FAIL: " + ",".join(bad)
        else:
            tgt = BROKEN[mu][0]
            verdict = f"REJECT on {tgt} (good)" if tgt in bad else f"NOT REJECTED on {tgt}"
            if tgt not in bad:
                fail.append(f"broken copy {mu}@{c} not rejected")
        de = m["ls_duty_err"]
        L.append(f"| {c} {r['cond']} | {mu} | {ns(m['ls_delay_r'])}/{ns(m['ls_delay_f'])} | {ns(m['ls_edge'])} | "
                 f"{'MISSING' if de is None else f'{de * 100:.2f}'} | {ns(m['g_n_r'])}/{ns(m['g_n_f'])} | "
                 f"{ns(m['g_p_r'])}/{ns(m['g_p_f'])} | {ns(m['g50_r'])}/{ns(m['g50_f'])} | "
                 f"{ns(m['early_r'])}/{ns(m['early_f'])} | {ns(m['t_half_il'])}/{ns(m['t_half_sl'])} | "
                 f"{ns(m['edge_max'])} | {ns(m['skew_tc_max'])} | {verdict} |")
    L += ["", "## Problems", ""] + ([f"- {f}" for f in fail] or ["- none"])
    open(os.path.join(out, "summary.md"), "w").write("\n".join(L) + "\n")
    json.dump({f"{k}_{c}_{mu}": r for (k, c, mu), r in rows.items()}, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print("\n".join(L))
    return 2 if fail else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "jobs":
        out = os.path.abspath(a[1])
        os.makedirs(out, exist_ok=True)
        me = os.path.abspath(__file__)
        with open(os.path.join(out, "jobs.txt"), "w") as f:
            for k, c, mu in joblist():
                f.write(f"python {me} run {k} {c} {mu} {out}\n")
        print(len(joblist()), "jobs ->", os.path.join(out, "jobs.txt"))
    elif a[0] == "run":
        r = run(a[1], a[2], a[3], os.path.abspath(a[4]))
        print(r["ok"], r["err"])
        sys.exit(0 if r["ok"] else 1)
    elif a[0] == "report":
        sys.exit(report(os.path.abspath(a[1])))
    else:
        sys.exit(__doc__)
