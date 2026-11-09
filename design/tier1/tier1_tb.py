#!/usr/bin/env python3
"""Tier-1 testbench / checker (WO-07 / S5). Runs ngspice on decks from gen_tier1.py.

Expected values come from theory (WORKFLOW 11 item 8): the ideal quantizer DC transfer u_hat = u_in,
using the residue reconstruction (SPEC 3.7)
    u = (sum S + (k/c1) S + x2[N]/(c1 c2)) / (N(N-1)/2),   x2[N] read from the simulation.
No import of model/iadc.py.

Modes: --null --options --dc --sweep --nonvac (WO-07) and --xcheck --av --knees2 --cm --offsets --rsrc --nonvac2 (WO-08).
WO-09 (S5c) adds --knees3 --cm2 --drift --rsrc2 --nonvac3.
Each prints ACCEPT/REJECT and exits nonzero on REJECT (--nonvac/--nonvac2 exit 1 when every broken case was rejected).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import params as P  # noqa: E402
import gen_tier1 as G  # noqa: E402

OUT = os.environ.get("TIER1_OUT", "/home/mempool/regr/tt/WO-09")
NGSPICE = os.environ.get("NGSPICE", "ngspice")
BAD_LOG = re.compile(r"(error|singular|timestep too small|no convergence|failed|fatal|unknown (model|param))", re.I)
FS_FULL = 2.0                       # full-scale range in u (+-1): INL "ppm of FSR" like the model


# ---------------------------------------------------------------- theory
def reconstruct(y, x2n_u, n, c1, c2, k):
    """SPEC 3.7 residue reconstruction. y: array of N bits (+-1), x2n_u: x2[N] in units of VREF."""
    y = np.asarray(y, float)
    s_excl = np.concatenate(([0.0], np.cumsum(y)[:-1]))     # exclusive S[n]
    return (s_excl.sum() + (k / c1) * y.sum() + x2n_u / (c1 * c2)) / (n * (n - 1) / 2.0)


def ideal_loop(u, n, c1, c2, k):
    """Hand-coded ideal discrete loop (theory recursion) used only to test reconstruct()."""
    x1 = x2 = 0.0
    ys = []
    y = 1.0
    for i in range(n):
        ys.append(y)
        x1n = x1 + c1 * (u - y)
        x2n = x2 + c2 * (x1 - k * y)
        x1, x2 = x1n, x2n
        y = 1.0 if x2 > 0 else -1.0
    return np.array(ys), x2


def inl_gain(u_in, u_hat):
    if len(np.atleast_1d(u_in)) < 3:                 # single-point decks (pointwise sweeps): no linearity metric
        return dict(inl_ep_ppm=float("nan"), inl_bf_ppm=float("nan"), gain_err=float("nan"), offset=float("nan"))
    """Endpoint INL (ppm of FSR=2), best-fit INL, gain error and offset."""
    u_in, u_hat = np.asarray(u_in, float), np.asarray(u_hat, float)
    i0, i1 = np.argmin(u_in), np.argmax(u_in)
    sl = (u_hat[i1] - u_hat[i0]) / (u_in[i1] - u_in[i0])
    ep = u_hat[i0] + sl * (u_in - u_in[i0])
    inl_ep = np.max(np.abs(u_hat - ep)) / FS_FULL * 1e6
    a, b = np.polyfit(u_in, u_hat, 1)
    inl_bf = np.max(np.abs(u_hat - (a * u_in + b))) / FS_FULL * 1e6
    return dict(inl_ep_ppm=float(inl_ep), inl_bf_ppm=float(inl_bf), gain_err=float(a - 1.0), offset=float(b))


# ---------------------------------------------------------------- run + checks
def audit_netlist(deck):
    """Inventory of intended ideal parts only; returns (ok, counts, msgs)."""
    counts, msgs = {}, []
    in_ctl = False
    for ln in deck.splitlines():
        ln = ln.strip()
        if ln.startswith(".control"):
            in_ctl = True
        if ln.startswith(".endc"):
            in_ctl = False
        if in_ctl or not ln or ln[0] in "*.+":
            continue
        pfx = ln[0].upper()
        counts[pfx] = counts.get(pfx, 0) + 1
    allowed = {"V", "R", "C", "S", "B"}
    bad = sorted(set(counts) - allowed)
    if bad:
        msgs.append(f"unexpected element types {bad}")
    if "SWM" not in deck or ".model SWM SW" not in deck:
        msgs.append("switch model missing")
    for banned in ("subckt", ".lib", ".include", "nfet", "pfet", "sky130"):
        if banned in deck.lower():
            msgs.append(f"banned token {banned}")
    return (not msgs), counts, msgs


def run_deck(cfg, tag, outdir=None, timeout=1500):
    """Run one deck; return dict with bits/x2 per conversion and all WORKFLOW-11 checks."""
    outdir = outdir or OUT
    os.makedirs(outdir, exist_ok=True)
    csv = os.path.join(outdir, f"{tag}.csv")
    cir = os.path.join(outdir, f"{tag}.cir")
    log = os.path.join(outdir, f"{tag}.log")
    deck, meta = G.build_deck(cfg, rawfile=csv)
    open(cir, "w").write(deck)
    ok_net, counts, nmsgs = audit_netlist(deck)
    t_start = time.time()
    p = subprocess.run(["nice", "-n", "10", "timeout", str(timeout), NGSPICE, "-b", "-o", log, cir],
                       capture_output=True, text=True)
    runtime = time.time() - t_start
    res = dict(tag=tag, meta=meta, runtime_s=runtime, netlist_ok=ok_net, netlist_counts=counts, problems=list(nmsgs))
    txt = open(log).read() if os.path.exists(log) else ""
    bad = [l for l in txt.splitlines() if BAD_LOG.search(l)]
    if p.returncode != 0 and not os.path.exists(csv):
        res["problems"].append(f"ngspice rc={p.returncode}")
    res["problems"] += [f"log: {l.strip()}" for l in bad[:5]]
    o = meta["options"]
    low = txt.lower()
    for needle in (f"reltol={o['reltol']:g}", f"method={o['method']}", ".model swm sw"):
        if needle not in low:
            res["problems"].append(f"log does not echo '{needle}' (options/models not loaded?)")
    if "Doing analysis" not in txt and "Transient" not in txt and "transient" not in txt:
        res["problems"].append("log shows no transient analysis")
    if not os.path.exists(csv):
        res["problems"].append("no data file")
        res["ok"] = False
        return res
    d = np.loadtxt(csv, skiprows=1)
    t = d[:, 0]
    res["tfinal"] = float(t[-1])
    res["npts"] = int(len(t))
    if abs(t[-1] - meta["tstop"]) > 1e-9 * meta["tstop"] + 1e-12:
        res["problems"].append(f"final time {t[-1]:.6e} != tstop {meta['tstop']:.6e}")
    if not np.all(np.isfinite(d)):
        res["problems"].append("NaN/inf in data")
    yq, o2p, o2n = d[:, 1], d[:, 2], d[:, 3]
    o1p, o1n = d[:, 4], d[:, 5]
    res["cols"] = dict(t=t, yq=yq, o2p=o2p, o2n=o2n, o1p=o1p, o1n=o1n)
    for i, nm in enumerate(cfg.get("extra", ())):
        res["cols"][nm] = d[:, 6 + i]
    T, n = meta["T"], meta["n"]
    cfgm = meta["cfg"]
    vref = cfgm["vref"]
    c1 = cfgm["cs1"] / cfgm["cint1"]
    c2 = cfgm["cs2"] / cfgm["cint2"]
    convs = []
    for m, t0 in enumerate(meta["t0"]):
        ts = t0 + np.arange(n) * T + 0.25 * T
        y = np.interp(ts, t, yq)
        if np.max(np.abs(np.abs(y) - 1.0)) > 0.05:
            res["problems"].append(f"conv {m}: comparator bits not +-1 (max dev {np.max(np.abs(np.abs(y) - 1)):.3f})")
        yb = np.where(y > 0, 1.0, -1.0)
        tend = t0 + n * T - 5e-9
        x2 = (np.interp(tend, t, o2p) - np.interp(tend, t, o2n)) / vref
        x1 = (np.interp(tend, t, o1p) - np.interp(tend, t, o1n)) / vref
        convs.append(dict(y=yb, x2n=float(x2), x1n=float(x1)))
    res["convs"] = convs
    res["ok"] = not res["problems"]
    return res


def u_hat_of(res, c1=None, c2=None, k=None):
    cfgm = res["meta"]["cfg"]
    c1 = c1 if c1 is not None else P.C1
    c2 = c2 if c2 is not None else P.C2
    k = k if k is not None else P.K
    n = res["meta"]["n"]
    return np.array([reconstruct(cv["y"], cv["x2n"], n, c1, c2, k) for cv in res["convs"]])


def u_points(m, span=0.9):
    return tuple(float(x) for x in np.linspace(-span, span, m))


def dc_metrics(cfg, tag, outdir=None):
    res = run_deck(cfg, tag, outdir)
    if not res.get("convs"):
        return res
    uin = np.array(res["meta"]["cfg"]["u_list"], float)
    uh = u_hat_of(res)
    res["u_in"], res["u_hat"] = uin.tolist(), uh.tolist()
    res["err"] = (uh - uin).tolist()
    res["max_abs_err"] = float(np.max(np.abs(uh - uin)))
    res.update(inl_gain(uin, uh))
    return res


def strip(res):
    r = {k: v for k, v in res.items() if k not in ("convs", "cols")}
    return r


# ---------------------------------------------------------------- modes
NULL_CFG = dict(a0_db=180.0, gbw=1e8, sr=1e9, vcl=1e3, ron=1.0)


def null_cfg(extra=None, n=256, m=5):
    c = dict(NULL_CFG)
    c.update(n=n, u_list=u_points(m, 0.9))
    c.update(extra or {})
    return c


def mode_null(args):
    r = dc_metrics(null_cfg(n=args.n, m=args.m), "null")
    ok = r.get("ok") and r["max_abs_err"] < P.TIER1_NULL_TOL
    print(f"null: N={args.n} runtime {r['runtime_s']:.1f}s for {args.m} conversions; "
          f"max |u_hat-u_in| = {r.get('max_abs_err', float('nan')):.3e} (tol {P.TIER1_NULL_TOL:g}); problems={r['problems']}")
    print("ACCEPT" if ok else "REJECT")
    json.dump(strip(r), open(os.path.join(OUT, "null.json"), "w"), indent=1, default=float)
    return 0 if ok else 1


def mode_options(args):
    combos = [dict(method=mt, reltol=rt, chgtol=ct)
              for rt in (1e-3, 1e-4, 1e-5) for ct in (1e-14, 1e-15, 1e-16) for mt in ("trap", "gear")]

    def one(i_o):
        i, o = i_o
        opts = dict(P.SPICE_OPTIONS_TIER1)
        opts.update(o)
        rn = dc_metrics(null_cfg(dict(options=opts), n=args.n, m=args.m), f"opt{i:02d}_null")
        rd = dc_metrics(spec_cfg(dict(options=opts), n=args.n, m=5), f"opt{i:02d}_spec")
        ok = bool(rn.get("ok") and rd.get("ok") and rn["max_abs_err"] < P.TIER1_NULL_TOL)
        return dict(opts=o, null_err=rn.get("max_abs_err", float("nan")), spec_inl=rd.get("inl_ep_ppm", float("nan")),
                    spec_gain=rd.get("gain_err", float("nan")), runtime_null_s=rn["runtime_s"],
                    runtime_spec_s=rd["runtime_s"], ok=ok, problems=rn["problems"] + rd["problems"])
    with ThreadPoolExecutor(3) as ex:
        rows = list(ex.map(one, enumerate(combos)))
    for r in rows:
        print(f"{r['opts']}  null err {r['null_err']:.3e}  spec INL {r['spec_inl']:.3f} gain {r['spec_gain']:+.3e}  "
              f"{r['runtime_null_s']:.1f}s/{r['runtime_spec_s']:.1f}s  ok={r['ok']} {r['problems'][:1]}")
    json.dump(rows, open(os.path.join(OUT, "options_sweep.json"), "w"), indent=1, default=float)
    good = [r for r in rows if r["ok"]]
    good.sort(key=lambda r: (-r["opts"]["reltol"], -r["opts"]["chgtol"], r["opts"]["method"] != "trap"))
    print("loosest passing:", good[0]["opts"] if good else None)
    print("ACCEPT" if good else "REJECT", f"({len(good)}/{len(rows)} settings pass)")
    return 0 if good else 1


def spec_cfg(extra=None, n=256, m=11, **kw):
    c = dict(n=n, u_list=u_points(m, 0.9), sr=P.TIER1_SR, vcl=P.TIER1_VCL, ron=P.TIER1_RON)
    c.update(kw)
    c.update(extra or {})
    return c


def mode_dc(args):
    r = dc_metrics(spec_cfg(n=args.n, m=args.m), "dc_spec")
    inl = r.get("inl_ep_ppm", float("nan"))
    ok = r.get("ok") and inl <= P.TIER1_INL_BUDGET_PPM
    print(f"dc spec OTA: INL(endpoint) {inl:.3f} ppm FSR, INL(best fit) {r.get('inl_bf_ppm', float('nan')):.3f}, "
          f"gain err {r.get('gain_err', float('nan')):+.3e}, offset {r.get('offset', float('nan')):+.2e}, "
          f"runtime {r['runtime_s']:.0f}s; problems={r['problems']}")
    print("ACCEPT" if ok else "REJECT")
    json.dump(strip(r), open(os.path.join(OUT, "dc_spec.json"), "w"), indent=1, default=float)
    return 0 if ok else 1


SWEEPS = {"a0_db": [50.0, 60.0, 70.0, 80.0], "gbw": [2e6, 5e6, 10e6, 20e6], "sr": [3e6, 6e6, 12e6, 25e6]}
SPEC_VAL = {"a0_db": 80.0, "gbw": 10e6, "sr": 12e6}
# (label, fs, baseline overrides). 4 MHz is run at the spec baseline and at the 20 MHz design-target baseline.
BASES = [("2M", 2e6, {}), ("4M_specbase", 4e6, {}), ("4M_gbw20base", 4e6, {"gbw": P.OTA_GBW_TARGET})]


def mode_sweep(args):
    jobs = [(lab, fs, base, pn, v) for lab, fs, base in BASES for pn, vals in SWEEPS.items() for v in vals]

    def one(j):
        lab, fs, base, pn, v = j
        extra = dict(base)
        extra.update({"fs": fs, pn: v})
        return dc_metrics(spec_cfg(extra, n=256, m=5), f"sw_{lab}_{pn}_{v:g}")
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(one, jobs))
    rows = []
    for (lab, fs, base, pn, v), r in zip(jobs, rs):
        rows.append(dict(base=lab, fs=fs, param=pn, value=v, ok=r.get("ok", False), inl_ep_ppm=r.get("inl_ep_ppm", float("nan")),
                         gain_err=r.get("gain_err", float("nan")), runtime_s=r["runtime_s"], problems=r["problems"]))
        print(f"{lab} {pn}={v:g}: INL {rows[-1]['inl_ep_ppm']:.2f} ppm, gain {rows[-1]['gain_err']:+.2e}, ok={r.get('ok')}")
    knees = {}
    for lab, fs, base in BASES:
        for pn in SWEEPS:
            sel = sorted((r for r in rows if r["base"] == lab and r["param"] == pn), key=lambda r: r["value"])
            good = [r["value"] for r in sel if r["ok"] and r["inl_ep_ppm"] <= P.TIER1_INL_BUDGET_PPM]
            knees[f"{lab}/{pn}"] = min(good) if good else None
    ok = all(r["ok"] for r in rows) and len(rows) == len(jobs) and all(math.isfinite(r["inl_ep_ppm"]) for r in rows)
    print("knees (lowest swept value with INL <= 8 ppm; other params at the base):", knees)
    for key, v in knees.items():
        pn = key.split("/")[1]
        if v is None or v > SPEC_VAL[pn]:
            print(f"FLAG knee {key} = {v} above SPEC 3.0 value {SPEC_VAL[pn]}")
    json.dump(dict(rows=rows, knees=knees), open(os.path.join(OUT, "sweep.json"), "w"), indent=1, default=float)
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


def mode_nonvac(args):
    """Each broken deck must be REJECTed by the check it targets."""
    fails = []
    # 1. DAC polarity flipped: null test must REJECT
    r1 = dc_metrics(null_cfg(dict(dac_flip=True), n=args.n, m=args.m), "nv_dacflip")
    rej1 = (not r1.get("ok")) or r1["max_abs_err"] >= P.TIER1_NULL_TOL
    # 2. c1 doubled (Cs1 x2): null test (gain vs theory) must REJECT
    r2 = dc_metrics(null_cfg(dict(cs1=2 * P.CS1), n=args.n, m=args.m), "nv_c1x2")
    rej2 = (not r2.get("ok")) or r2["max_abs_err"] >= P.TIER1_NULL_TOL
    # 3. A0 = 50 dB at spec: DC INL check must REJECT
    r3 = dc_metrics(spec_cfg(dict(a0_db=50.0), n=args.n, m=args.m), "nv_a050")
    rej3 = (not r3.get("ok")) or r3["inl_ep_ppm"] > P.TIER1_INL_BUDGET_PPM
    for name, r, rej, key in (("dac_flip", r1, rej1, "max_abs_err"), ("c1x2", r2, rej2, "max_abs_err"),
                              ("A0 50 dB", r3, rej3, "inl_ep_ppm")):
        print(f"nonvac {name}: {key}={r.get(key, float('nan')):.3e} ok={r.get('ok')} -> {'REJECT (as required)' if rej else 'ACCEPT (BAD: check is vacuous)'}")
        if not rej:
            fails.append(name)
    # 4. also: reconstruction without the x2 residue must fail the null test
    r0 = dc_metrics(null_cfg(n=args.n, m=args.m), "nv_ref")
    uh_no = np.array([reconstruct(cv["y"], 0.0, args.n, P.C1, P.C2, P.K) for cv in r0["convs"]])
    e_no = float(np.max(np.abs(uh_no - np.array(r0["u_in"]))))
    print(f"nonvac no-residue reconstruction: err {e_no:.3e} -> {'REJECT (as required)' if e_no >= P.TIER1_NULL_TOL else 'ACCEPT (BAD)'}")
    if e_no < P.TIER1_NULL_TOL:
        fails.append("no-residue")
    json.dump(dict(dac_flip=strip(r1), c1x2=strip(r2), a050=strip(r3), no_residue_err=e_no), open(os.path.join(OUT, "nonvac.json"), "w"), indent=1, default=float)
    print("REJECT-as-required for all broken decks" if not fails else f"VACUOUS: {fails}")
    return 1 if not fails else 0  # exit 1 = the broken decks were rejected (WO: "exit 1")


# =============================================================== WO-08 (S5b)
sys.path.insert(0, os.path.join(HERE, "..", "..", "model"))
VREF = P.VREF_NOM
VREF_CM = VREF / 2.0
V2BASE = dict(ota="v2", vrefp_v=P.VREF_NOM, vrefn_v=0.0, vin_cm=P.TIER1_VIN_CM, d12=True, sr=P.TIER1_SR,
              vcl=P.TIER1_VCL, ron=P.TIER1_RON, gbw=P.OTA_GBW_MIN)


def v2_cfg(extra=None, n=256, m=21, span=0.9, **kw):
    c = dict(V2BASE)
    c.update(n=n, u_list=u_points(m, span))
    c.update(kw)
    c.update(extra or {})
    return c


def rel_sym(a, b):
    """|a-b| over the mean of |a|,|b| (symmetric relative difference)."""
    den = 0.5 * (abs(a) + abs(b))
    return abs(a - b) / den if den > 0 else 0.0


def w_sum2(n):
    """Theory: sum of squared residue weights w_m = N-1-m."""
    return (n - 1) * n * (2 * n - 1) / 6.0


def noise_gain_u(n):
    """Theory: output rms in u per unit rms of a white per-cycle input-referred error e (in u)."""
    return math.sqrt(w_sum2(n)) / (n * (n - 1) / 2.0)


def e2_closed_V(vos2, c1, n, geom=1.0):
    """Constant OTA2 input offset -> input-referred error [V]: 2 e2/(c1 (N-1)), geom = (Cs2+Ck)/Cs2 charge factor."""
    return 2.0 * vos2 * geom / (c1 * (n - 1))


def chop_resid_V(vos, n, lf=1.0):
    """OTA-chop residual for order 2, N even, phase restarted each reset: lf*Vos/(N-1)."""
    return lf * vos / (n - 1)


def model_eval(U, n=256, **kw):
    import iadc as M
    p = M.with_(M.Params(order=2, N=n, c1=0.125, c2=0.5, k=0.5, vref=VREF), **kw)
    ub, st = M.convert(p, np.asarray(U, float), rng=np.random.default_rng(0), return_state=True)
    return np.asarray(st["u_corr"]), p


def jdump(obj, name):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=float)


# ---- item 1: cross-check table + noise transfer
IDEAL_OTA = dict(gbw=1e8, sr=1e9, vcl=1e3, ron=1.0)
# reviewer's probe numbers (REVIEW-S5): deck gain, deck INL ppm, model gain, model INL ppm
REV = {"A60_base": (-5.59e-4, 3.99, -5.47e-4, 3.09), "A60_k025": (-2.93e-4, 6.98, -2.88e-4, 5.90),
       "A60_c1_025": (-5.51e-4, 10.05, -5.43e-4, 7.43), "A80_base": (None, 0.29, None, 0.295),
       "A80_roff1e14": (None, 0.29, None, 0.295)}


XCHECK_REL = 0.05          # WO-13/V3: deck-vs-model INL rel_sym gate (tightened from 0.35 once the model carries Ck in its stage-2 topology)
XCHECK_GATED_EXTRA = ("A60_base_cpvg",)     # cp_hold gated row: Cp,vg 0.262 pF both stages of the deck


def xcheck_rows(no_ck=False, tagpfx="xc_"):
    """Deck-vs-model cross-check rows. The model side uses the iadc default (Ck loading derived from k). no_ck=True is the broken copy of the model with the
    Ck term removed from the stage-2 sampled capacitance (test-only monkeypatch of iadc._leaky)."""
    import iadc as M
    U = u_points(5, 0.9)
    cases = [("A60_base", dict(a0_db=60.0), {}), ("A60_k025", dict(a0_db=60.0, ck=0.125e-12), dict(k=0.25)),
             ("A60_c1_025", dict(a0_db=60.0, cint1=2e-12), dict(c1=0.25)), ("A80_base", dict(a0_db=80.0), {}),
             # m3 (WO-09): at A0 80 dB the compared quantity (~0.3 ppm) is the size of the Roff 1e12 null floor (0.46 ppm): rerun at Roff 1e14
             ("A80_roff1e14", dict(a0_db=80.0, roff=1e14), {})]
    # R9 (WO-12): decks with the explicit Cp,vg of the v2 decks (xcheck decks use the legacy OTA path, which has NO Cp,vg: cp = 0). WO-13: A60_base_cpvg is gated through cp_hold.
    diag = [("A60_base_cpvg", dict(a0_db=60.0, cp_vg=P.TIER1_CP_VG), {}), ("A60_c1_025_cpvg", dict(a0_db=60.0, cint1=2e-12, cp_vg=P.TIER1_CP_VG), dict(c1=0.25))]
    orig = M._leaky
    if no_ck:
        def _no_ck(a0_db, c, *a, **kw):
            return orig(a0_db, c / (1.0 + CUR_K[0]) if abs(c - CUR_C2[0] * (1.0 + CUR_K[0])) < 1e-12 else c, *a, **kw)
        M._leaky = _no_ck
    rows, ok = [], True
    try:
        for name, dk, mk in cases + diag:
            gated = name in REV or name in XCHECK_GATED_EXTRA
            cfg = dict(IDEAL_OTA, n=256, u_list=U)
            cfg.update(dk)
            r = run_deck(cfg, tagpfx + name)
            c1, k = mk.get("c1", P.C1), mk.get("k", P.K)
            CUR_K[0], CUR_C2[0] = k, P.C2
            uh = np.array([reconstruct(cv["y"], cv["x2n"], 256, c1, P.C2, k) for cv in r["convs"]])
            g = inl_gain(np.array(U), uh)
            cint1, cp = dk.get("cint1", P.CINT1), dk.get("cp_vg", 0.0)
            hold = dict(cp_hold1=cp / cint1, cp_hold2=cp / P.CINT2) if cp else {}
            um, p = model_eval(U, 256, a0_db=dk["a0_db"], **mk, **hold)
            gm_ = inl_gain(np.array(U), um)
            rv = REV.get(name, (None, None, None, None))
            rel = rel_sym(g["inl_ep_ppm"], gm_["inl_ep_ppm"])
            chk = []
            if gated:
                chk = [rel <= XCHECK_REL]
                if rv[1] is not None:
                    chk.append(rel_sym(g["inl_ep_ppm"], rv[1]) <= 0.35)
                if rv[0] is not None:
                    chk += [rel_sym(g["gain_err"], gm_["gain_err"]) <= 0.05, rel_sym(g["gain_err"], rv[0]) <= 0.05]
            row = dict(case=name, gated=gated, ok=bool(r["ok"] and all(chk)), deck_gain=g["gain_err"], model_gain=gm_["gain_err"], rev_deck_gain=rv[0],
                       deck_inl=g["inl_ep_ppm"], model_inl=gm_["inl_ep_ppm"], rev_deck_inl=rv[1], rev_model_inl=rv[3], checks=chk, problems=r["problems"],
                       rel_sym_inl=rel, ratio_inl=g["inl_ep_ppm"] / gm_["inl_ep_ppm"], cp_hold=hold)
            ok &= row["ok"]
            rows.append(row)
            print(f"xcheck{' [NO-Ck BROKEN MODEL]' if no_ck else ''} {name}{'' if gated else ' (diagnostic, not gated)'}: deck gain {g['gain_err']:+.3e} INL {g['inl_ep_ppm']:.3f} | model gain {gm_['gain_err']:+.3e} "
                  f"INL {gm_['inl_ep_ppm']:.3f} | deck/model INL {row['ratio_inl']:.3f} rel_sym {rel*100:.1f} % (gate {XCHECK_REL*100:g} %) gain rel_sym {rel_sym(g['gain_err'], gm_['gain_err'])*100:.1f} % "
                  f"| reviewer deck {rv[0]} / {rv[1]} -> {'ok' if row['ok'] else 'FAIL'} {chk}")
    finally:
        M._leaky = orig
    return rows, ok


CUR_K, CUR_C2 = [P.K], [P.C2]


def mode_xcheck(args):
    rows, ok = xcheck_rows()
    # noise transfer: trnoise at OTA1 input, per-cycle white, ~30 conversions
    nconv, sig = 32, 2e-3
    cfg = dict(IDEAL_OTA, a0_db=120.0, n=256, u_list=(0.0,) * nconv, noise1=sig)
    r = run_deck(cfg, "xc_noise")
    E = np.asarray(r["meta"]["noise_e"])
    uh = u_hat_of(r)
    import iadc as M
    _, p = model_eval(np.zeros(nconv), 256, a0_db=float("inf"))
    ub, st = M.convert(p, np.zeros(nconv), ota_noise=E, return_state=True)
    um = np.asarray(st["u_corr"])
    slope = float(np.dot(uh, um) / np.dot(um, um))
    corr = float(np.corrcoef(uh, um)[0, 1])
    rms_d, rms_th = float(np.sqrt(np.mean(uh ** 2))), noise_gain_u(256) * float(np.sqrt(np.mean(E ** 2))) / VREF
    nz_ok = bool(r["ok"] and abs(abs(slope) - 1) <= 0.30 and abs(rms_d / rms_th - 1) <= 0.30 and abs(corr) > 0.9)
    print(f"xcheck noise: sigma_in {np.sqrt(np.mean(E**2))*1e3:.3f} mV rms (set {sig*1e3} mV), {nconv} conv; deck rms {rms_d:.3e} u, theory {rms_th:.3e} "
          f"(ratio {rms_d/rms_th:.3f}); deck-vs-model per-conversion slope {slope:+.3f} corr {corr:+.3f}; model rms {np.sqrt(np.mean(um**2)):.3e} ok={nz_ok} {r['problems'][:1]}")
    ok &= nz_ok
    jdump(dict(rows=rows, noise=dict(sigma_v=float(np.sqrt(np.mean(E ** 2))), deck_rms_u=rms_d, theory_rms_u=rms_th, slope=slope, corr=corr, ok=nz_ok, problems=r["problems"])), "xcheck.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


def mode_nonvac5(args):
    """WO-13/V3 nonvacuity: the xcheck gate must pass on the unbroken model (control) and fail when the Ck term is removed from the model's stage-2 topology.
    Prints REJECT and exits 1 when the broken copy is rejected and the control is accepted (the nonvac convention); ACCEPT (exit 0) means the gate is vacuous."""
    _, ok_ctl = xcheck_rows(False, "nv5c_")
    rows_b, ok_brk = xcheck_rows(True, "nv5b_")
    bad = [r["case"] for r in rows_b if r["gated"] and not r["ok"]]
    print(f"nonvac5: control (Ck in model) gate ok={ok_ctl}; no-Ck broken model gate ok={ok_brk}; rejected rows: {bad}")
    verdict = (not ok_brk) and ok_ctl
    jdump(dict(control_ok=ok_ctl, broken_ok=ok_brk, rejected=bad, rows=rows_b), "nonvac5.json")
    print("REJECT" if verdict else ("ACCEPT (nonvac FAILED)" if ok_ctl else "control failed"))
    return 1 if verdict else 0


# ---- item 4: A(v)
def av_compare(vsw_deck, tag, m=11):
    cfg = v2_cfg(dict(IDEAL_OTA, avdrop=P.TIER1_AV_DROP, vsw=vsw_deck), n=256, m=m)
    r = dc_metrics(cfg, tag)
    U = np.array(r["meta"]["cfg"]["u_list"])
    um, _ = model_eval(U, 256, a0_db=80.0, a0_drop=P.TIER1_AV_DROP, vlin_diff=P.TIER1_AV_VSW)
    gm_ = inl_gain(U, um)
    rel = rel_sym(r["inl_ep_ppm"], gm_["inl_ep_ppm"])
    return r, gm_, rel


def av_table():
    a0 = 80.0
    return [(v, a0 + 20 * math.log10(max(0.02, 1 - P.TIER1_AV_DROP * (v / P.TIER1_AV_VSW) ** 2))) for v in (0.0, 0.4, 0.8, 1.2, 1.4, 1.6, 2.0)]


def mode_av(args):
    r0 = dc_metrics(v2_cfg(IDEAL_OTA, n=256, m=11), "av_flat")
    r, gm_, rel = av_compare(P.TIER1_AV_VSW, "av_drop09")
    ok = bool(r["ok"] and r0["ok"] and rel <= 0.30 and r["inl_ep_ppm"] > 3 * r0["inl_ep_ppm"])
    print(f"A(v) static table (vo_diff V -> dB, A0 80): {[(v, round(a, 2)) for v, a in av_table()]}")
    print(f"A(v): deck flat-A0 INL {r0['inl_ep_ppm']:.3f} ppm; deck A(v) drop {P.TIER1_AV_DROP} vsw {P.TIER1_AV_VSW} INL {r['inl_ep_ppm']:.3f} ppm gain {r['gain_err']:+.3e}; "
          f"model INL {gm_['inl_ep_ppm']:.3f} gain {gm_['gain_err']:+.3e}; rel diff {rel*100:.1f} % (limit 30)")
    jdump(dict(flat_inl=r0["inl_ep_ppm"], deck_inl=r["inl_ep_ppm"], deck_gain=r["gain_err"], model_inl=gm_["inl_ep_ppm"], model_gain=gm_["gain_err"],
               rel=rel, table=av_table(), problems=r["problems"] + r0["problems"]), "av.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 5: load-dependent OTA knees, 21 points
KNEE_SETS = [  # label, fs, extra cfg, n, target ppm, spec gbw, spec sr, gbw values, sr values
    ("2M", 2e6, {}, 256, P.TIER1_INL_BUDGET_PPM, 10e6, 12e6, (5e6, 7e6, 10e6, 20e6, 30e6), (6e6, 8e6, 10e6, 12e6, 25e6)),
    ("4M_boost", 4e6, {"boost": True}, 256, P.TIER1_INL_FAST[256], 10e6, 12e6, (5e6, 7.5e6, 10e6, 20e6), (6e6, 9e6, 12e6, 25e6)),
]
KNEE_EXTRA = [  # label, cfg extra, n, target
    ("4M_noboost_spec", {"fs": 4e6}, 256, P.TIER1_INL_FAST[256]),
    ("4M_boost_spec_N1024", {"fs": 4e6, "boost": True}, 1024, P.TIER1_INL_FAST[1024]),
    ("2M_spec_with_Av", {"avdrop": P.TIER1_AV_DROP, "vsw": P.TIER1_AV_VSW}, 256, P.TIER1_INL_BUDGET_PPM),
    ("2M_spec_asym_sr0.5", {"sr_asym": 0.5}, 256, P.TIER1_INL_BUDGET_PPM),
]


def mode_knees2(args):
    jobs = []
    for lab, fs, ex, n, tgt, sg, ss, gv, sv in KNEE_SETS:
        for pn, vals in (("gbw", gv), ("sr", sv)):
            for v in vals:
                e = dict(ex)
                e.update({"fs": fs, pn: v})
                jobs.append((f"{lab}/{pn}={v/1e6:g}M", lab, pn, v, e, n, tgt))
    for lab, ex, n, tgt in KNEE_EXTRA:
        jobs.append((lab, lab, "-", 0, dict(ex), n, tgt))

    def one(j):
        tag, lab, pn, v, e, n, tgt = j
        return dc_metrics(v2_cfg(e, n=n, m=21), "kn_" + re.sub(r"[^A-Za-z0-9.]", "_", tag))
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(one, jobs))
    rows = []
    for j, r in zip(jobs, rs):
        tag, lab, pn, v, e, n, tgt = j
        rows.append(dict(tag=tag, set=lab, param=pn, value=v, n=n, target=tgt, ok=bool(r.get("ok")), inl_ep_ppm=r.get("inl_ep_ppm", float("nan")),
                         gain_err=r.get("gain_err", float("nan")), runtime_s=r["runtime_s"], problems=r["problems"]))
        print(f"{tag} (N {n}, target {tgt:g} ppm): INL {rows[-1]['inl_ep_ppm']:.2f} ppm gain {rows[-1]['gain_err']:+.2e} pass={rows[-1]['inl_ep_ppm'] <= tgt} ok={r.get('ok')} {r['problems'][:1]}")
    knees, flags = {}, []
    for lab, fs, ex, n, tgt, sg, ss, gv, sv in KNEE_SETS:
        for pn, spec in (("gbw", sg), ("sr", ss)):
            sel = sorted((r for r in rows if r["set"] == lab and r["param"] == pn), key=lambda r: r["value"])
            good = [r["value"] for r in sel if r["ok"] and r["inl_ep_ppm"] <= tgt]
            kn = min(good) if good else None
            knees[f"{lab}/{pn}"] = kn
            if kn is None or kn > spec:
                flags.append(f"FLAG knee {lab}/{pn} = {kn} above SPEC 3.0 {'base ' if lab != '2M' else ''}value {spec:g}")
    for r in rows:
        if r["set"] in [x[0] for x in KNEE_EXTRA] and (not r["ok"] or r["inl_ep_ppm"] > r["target"]):
            flags.append(f"FLAG {r['tag']}: INL {r['inl_ep_ppm']:.2f} ppm > target {r['target']:g}")
    ok = all(r["ok"] for r in rows) and all(math.isfinite(r["inl_ep_ppm"]) for r in rows)
    print("knees:", knees)
    for f_ in flags:
        print(f_)
    print(f"spec FLAG count: {len(flags)} (the exit code reflects run health only, not the spec flags)")
    jdump(dict(rows=rows, knees=knees, flags=flags), "knees2.json")
    print("run-health ACCEPT" if ok else "run-health REJECT")
    return 0 if ok else 1


# ---- item 6: reference pins, common mode, CMRR
CMX = ("vg1p", "vg1n", "vg2p", "vg2n")


def cm_run(vin_cm, mm, d12, dem, tag, u0=0.08, **kw):
    cfg = v2_cfg(dict(vin_cm=vin_cm, cs1_mm=mm, d12=d12, dem=dem, nrst=4, u_list=(u0, -u0), extra=CMX), n=256, **kw)
    r = run_deck(cfg, tag)
    uh = u_hat_of(r)
    e0, e1 = uh[0] - u0, uh[1] + u0
    out = dict(vin_cm=vin_cm, mm=mm, d12=d12, dem=dem, ok=bool(r["ok"]), problems=r["problems"],
               off_V=float((e0 + e1) / 2 * VREF), pair_V=float((e0 - e1) / 2 * VREF))
    cols, T = r["cols"], r["meta"]["T"]
    t = cols["t"]
    post = np.zeros(len(t), bool)
    for t0 in r["meta"]["t0"]:
        post |= (t >= t0) & (t <= t0 + 256 * T)
    for k in (1, 2):
        cmv = 0.5 * (cols[f"vg{k}p"] + cols[f"vg{k}n"])
        out[f"vg{k}_cm_min_all"], out[f"vg{k}_cm_max_all"] = float(cmv.min()), float(cmv.max())
        out[f"vg{k}_cm_min_conv"], out[f"vg{k}_cm_max_conv"] = float(cmv[post].min()), float(cmv[post].max())
    ocm = 0.5 * (cols["o1p"] + cols["o1n"])
    ocm2 = 0.5 * (cols["o2p"] + cols["o2n"])
    out["o_cm_dev_max_V"] = float(max(np.max(np.abs(ocm[post] - P.CM)), np.max(np.abs(ocm2[post] - P.CM))))
    th = T / 2
    ts = np.array([t0 + j * T + off for t0 in r["meta"]["t0"] for j in range(2, 256) for off in (12.5e-9 + 0.2 * th, th + 12.5e-9 + 0.2 * th)])
    out["o_cm_dev_at_0p2th_V"] = float(max(np.max(np.abs(np.interp(ts, t, ocm) - P.CM)), np.max(np.abs(np.interp(ts, t, ocm2) - P.CM))))
    return out


def nod12_settle_ratio(n, cs1=P.CS1, cint1=P.CINT1, cp=P.TIER1_CP_VG):
    """Theory (no D12, tops tied to cm): the CM step across Cs1 pumps vg CM toward cm-Vin_cm+Vref_cm with a per-cycle factor a = 1 - Cs/(Cs+Cint+Cp),
    so the Cs mismatch term mm*Cs*(vg-vt+X) is nonzero only while vg settles. Its weighted sum is (2/(N-1)) sum_m (1-m/(N-1)) a^m of mm*X."""
    a = 1.0 - cs1 / (cs1 + cint1 + cp)
    m = np.arange(n)
    return float(2.0 / (n - 1) * np.sum((1 - m / (n - 1.0)) * a ** m))


def cmrr_db(x, err):
    return 20 * math.log10(abs(x) / max(abs(err), 1e-9))


def mode_cm(args):
    lo, hi = P.TIER1_VG_CM_RANGE
    vins = (0.2, 1.0, 2.0)
    jobs = [(v, mm, True, False) for v in vins for mm in (0.0, 0.0025, 0.0075)]
    jobs += [(v, mm, False, False) for v in vins for mm in (0.0, 0.0025, 0.0075)]
    jobs += [(v, mm, True, True) for v in vins for mm in (0.0025, 0.0075)]

    def one(j):
        v, mm, d12, dem = j
        return cm_run(v, mm, d12, dem, f"cm_v{v}_mm{mm}_d12{int(d12)}_dem{int(dem)}")
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(one, jobs))
    flat = {j: r for j, r in zip(jobs, rs)}
    rows = []
    for j, r in zip(jobs, rs):
        v, mm, d12, dem = j
        x = v - VREF_CM
        ref0 = flat[(v, 0.0, d12, False)]
        exp_off = mm * x if not d12 else 0.0          # D12 floating top plates: CM term cancels to first order (derivation in results)
        row = dict(r)
        row["x_V"], row["exp_off_V"] = x, exp_off
        if not d12 and not dem and mm and abs(x) > 0.1:
            row["exp_off_V"] = mm * x * nod12_settle_ratio(256)
            row["off_match"] = bool(abs(r["off_V"] - row["exp_off_V"]) <= 0.25 * abs(row["exp_off_V"]))
        if mm and abs(x) > 0.1:
            row["cmrr_off_db"] = cmrr_db(x, r["off_V"] - ref0["off_V"])
            row["cmrr_on_db"] = cmrr_db(x, r["pair_V"] - ref0["pair_V"])
        rows.append(row)
        print(f"cm vin_cm {v} mm {mm*100:.2f}% d12={int(d12)} dem={int(dem)}: off {r['off_V']*1e6:+.1f} uV (expect {exp_off*1e6:+.1f}), pair resid {r['pair_V']*1e6:+.3f} uV, "
              f"vg1 CM [{r['vg1_cm_min_conv']:.3f},{r['vg1_cm_max_conv']:.3f}] (all [{r['vg1_cm_min_all']:.3f},{r['vg1_cm_max_all']:.3f}]) "
              f"vg2 [{r['vg2_cm_min_conv']:.3f},{r['vg2_cm_max_conv']:.3f}] outCM dev max {r['o_cm_dev_max_V']*1e3:.1f} mV @0.2th {r['o_cm_dev_at_0p2th_V']*1e3:.1f} mV "
              f"CMRR off {row.get('cmrr_off_db', float('nan')):.1f} dB on {row.get('cmrr_on_db', float('nan')):.1f} dB ok={r['ok']}")
    d12on = [r for r in rows if r["d12"] and not r["dem"]]
    nod12 = [r for r in rows if not r["d12"] and not r["dem"]]
    allr = [r for r in rows if r["d12"]]
    vmin = min(min(r["vg1_cm_min_all"], r["vg2_cm_min_all"]) for r in allr)
    vmax = max(max(r["vg1_cm_max_all"], r["vg2_cm_max_all"]) for r in allr)
    cmin = min(min(r["vg1_cm_min_conv"], r["vg2_cm_min_conv"]) for r in allr)
    cmax = max(max(r["vg1_cm_max_conv"], r["vg2_cm_max_conv"]) for r in allr)
    print(f"REQUIRED PMOS-pair CM range (D12 on): whole run [{vmin:.3f}, {vmax:.3f}] V; inside conversions [{cmin:.3f}, {cmax:.3f}] V; assumed available [{lo}, {hi}]")
    chk = dict(runs_ok=all(r["ok"] for r in rows),
               ideal_match_floor=all(abs(r["off_V"]) < P.TIER1_NULL_TOL * VREF for r in d12on if r["mm"] == 0.0),
               closed_form_nod12=all(r.get("off_match", True) for r in nod12) and any("off_match" in r for r in nod12),
               d12_rejects_cm=all(r["cmrr_off_db"] >= P.TIER1_CMRR_TARGET_DB["sys_off"] for r in d12on if "cmrr_off_db" in r),
               d12_in_range=bool(vmin >= lo and vmax <= hi),
               sys_on_100=all(r["cmrr_on_db"] >= P.TIER1_CMRR_TARGET_DB["sys_on"] for r in d12on if "cmrr_on_db" in r))
    ok = all(chk.values())
    print("checks:", chk)
    for r in rows:
        if "cmrr_off_db" in r and not r["dem"] and r["cmrr_off_db"] < P.TIER1_CMRR_TARGET_DB["sys_off"]:
            print(f"FLAG CMRR sys-off {r['cmrr_off_db']:.1f} dB < {P.TIER1_CMRR_TARGET_DB['sys_off']} dB at mm {r['mm']*100:.2f}% vin_cm {r['vin_cm']} (eps needed <= 0.1 %)")
        if "cmrr_on_db" in r and r["cmrr_on_db"] < P.TIER1_CMRR_TARGET_DB["sys_on"]:
            print(f"FLAG CMRR sys-on {r['cmrr_on_db']:.1f} dB < {P.TIER1_CMRR_TARGET_DB['sys_on']} dB at mm {r['mm']*100:.2f}% vin_cm {r['vin_cm']} dem={r['dem']}")
    jdump(dict(rows=rows, required_range_all=[vmin, vmax], required_range_conv=[cmin, cmax], checks=chk), "cm.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 7: offsets and system chop
def err_stats(res, u):
    uh = u_hat_of(res)
    return uh - np.array(u), uh


def mode_offsets(args):
    n = args.n
    base = dict(NULL_CFG, roff=1e14, nrst=4, n=n, vcl=2.5)   # vcl: the 180 dB open-loop DC point with a 9 mV offset needs a clamp to converge
    c1 = P.C1
    geom = 1.0 + (P.K * P.CS2) / P.CS2          # (Cs2+Ck)/Cs2 charge factor of an OTA2 offset (separate k-DAC cap, D25)
    ul = (0.0, 0.3)
    rows, ok = [], True

    def run(tag, **kw):
        cfg = dict(base, u_list=ul)
        cfg.update(kw)
        return run_deck(cfg, "of_" + tag)

    def add(name, got_V, exp_V, tol, r, note=""):
        nonlocal ok
        good = bool(r["ok"] and abs(abs(got_V) - abs(exp_V)) <= tol * abs(exp_V) + 1e-9)
        ok &= good
        rows.append(dict(name=name, got_V=got_V, exp_V=exp_V, ok=good, note=note, problems=r["problems"]))
        print(f"offsets {name}: measured {got_V*1e6:+.3f} uV, expected |{exp_V*1e6:.3f}| uV {note} -> {'ok' if good else 'FAIL'} {r['problems'][:1]}")
    r = run("null")
    e, _ = err_stats(r, ul)
    floor = float(np.mean(np.abs(e)) * VREF)
    print(f"offsets baseline (roff 1e14, no offsets): |err| mean {floor*1e6:.4f} uV")
    r = run("vos2", vos2=P.VOS_3SIGMA)
    e, _ = err_stats(r, ul)
    add("Vos2=9mV unchopped", float(np.mean(e) * VREF), e2_closed_V(P.VOS_3SIGMA, c1, n, geom), 0.05, r,
        f"(S2 form 2*Vos2/(c1(N-1)) = {e2_closed_V(P.VOS_3SIGMA, c1, n)*1e6:.1f} uV x geometry factor {geom} for the separate Ck)")
    r = run("vos1", vos1=P.VOS_3SIGMA)
    e, _ = err_stats(r, ul)
    x1path = e2_closed_V(P.VOS_3SIGMA, c1, n, 1.0)    # OTA1 offset also appears at x1 (S2 x1_offset path), sampled by Cs2 only
    add("Vos1=9mV unchopped", float(np.mean(e) * VREF), P.VOS_3SIGMA + x1path, 0.02, r,
        f"(lf*Vos {P.VOS_3SIGMA*1e6:.0f} uV + S2 x1_offset path 2*Vos/(c1(N-1)) {x1path*1e6:.1f} uV, lf=1)")
    r = run("vos1_chop", vos1=P.VOS_3SIGMA, chop=True)
    e, _ = err_stats(r, ul)
    add("Vos1=9mV OTA-chop", float(np.mean(e) * VREF), chop_resid_V(P.VOS_3SIGMA, n), 0.10, r, "(lf*Vos/(N-1))")
    cv = r["convs"][1]
    ident = float(np.mean(cv["y"]) - (0.3 - cv["x1n"] / (c1 * n)))
    off_ro = P.VOS_3SIGMA / VREF / (c1 * n)       # readout x1 carries the last-cycle chopped offset Vos (not c1*Vos)
    res_ = min(abs(ident - off_ro), abs(ident + off_ro))
    okid = bool(res_ < 0.03 * off_ro)
    ok &= okid
    rows.append(dict(name="order-1 identity", ident=ident, offset_term=off_ro, ok=okid))
    print(f"offsets identity mean(y) = u - x1[N]/(c1 N) (mean(e)=0, N even): raw residual {ident:.3e}, equals the readout-offset term Vos/(VREF c1 N) = {off_ro:.3e} "
          f"(leftover {res_:.1e}) -> {'ok' if okid else 'FAIL'}; the S2 order-1 path lf*Vos/N = {P.VOS_3SIGMA/n*1e6:.1f} uV is c1 x that readout term (true state x1[N] = c1 e); "
          f"not separately testable in an order-2 deck")
    u3 = (0.0, 0.3, 0.77)
    r = run("vcmp", vcmp=P.COMP_OFFSET_MAX, u_list=u3)
    r0 = run("vcmp_ref", u_list=u3)
    e, _ = err_stats(r, u3)
    plain = np.array([reconstruct(cv["y"], 0.0, n, c1, P.C2, P.K) for cv in r["convs"]]) - np.array(u3)
    ndiff = int(sum(np.sum(a_["y"] != b_["y"]) for a_, b_ in zip(r["convs"], r0["convs"])))
    good = bool(r["ok"] and r0["ok"] and np.max(np.abs(e)) < P.TIER1_NULL_TOL and ndiff > 0)
    ok &= good
    rows.append(dict(name="comp offset 20mV", got_V=float(np.max(np.abs(e)) * VREF), plain_V=float(np.max(np.abs(plain)) * VREF), bits_changed=ndiff, ok=good))
    print(f"offsets comp 20 mV: bits changed vs no-offset run {ndiff} (offset is active); residue-reconstructed |err| max {np.max(np.abs(e))*VREF*1e6:.4f} uV (loop-suppressed, must be ~0), "
          f"plain CoI (no x2 term) {np.max(np.abs(plain))*VREF*1e6:.2f} uV -> {'ok' if good else 'FAIL'}")
    allo = dict(vos1=P.VOS_3SIGMA, vos2=P.VOS_3SIGMA, vcmp=P.COMP_OFFSET_MAX, chop=True)
    for u in (0.05, 0.3):
        r = run(f"pair{u}", u_list=(u, -u), **allo)
        uh = u_hat_of(r)
        resid, single = float(((uh[0] - uh[1]) / 2 - u) * VREF), float((uh[0] - u) * VREF)
        good = bool(r["ok"] and abs(resid) <= P.TIER1_PAIR_RESID_V)
        ok &= good
        rows.append(dict(name=f"sys pair u={u}", residual_V=resid, single_offset_V=single, ok=good))
        print(f"offsets sys-chop pair u={u}: single-conversion error {single*1e6:+.2f} uV, pair residual {resid*1e6:+.4f} uV (limit {P.TIER1_PAIR_RESID_V*1e6}) -> {'ok' if good else 'FAIL'}")
    jdump(dict(rows=rows, floor_V=floor), "offsets.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 8: source impedance
def mode_rsrc(args):
    cases = [("none", 0.0, 0.0), ("1k", 1e3, 0.0), ("10k", 1e4, 0.0), ("10k+10nF", 1e4, 1e-8)]
    def pointwise(c_):
        # a 10 nF pin cap is not settled between consecutive conversions in one deck (tau 100 us), so each input value is its own
        # single-conversion deck (the DC operating point starts the pin at the source value, as a settled board would)
        us = u_points(11, 0.9)
        rr = [dc_metrics(v2_cfg(dict(rsrc=c_[1], cext=c_[2], u_list=(u,)), n=256, m=1), f"rs_{c_[0].replace('+', '_')}_{i}") for i, u in enumerate(us)]
        m_ = inl_gain(np.array(us), np.array([x["u_hat"][0] for x in rr]))
        m_.update(ok=all(x.get("ok") for x in rr), problems=sum((x["problems"] for x in rr), []))
        return m_
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(lambda c_: dict(pointwise(c_), runtime_s=0.0), cases))
    rows = []
    for (nm, r_, c_), r in zip(cases, rs):
        tau = (P.TIER1_RON + P.PAD_R + r_) * (P.PAD_C + P.CS1)
        rows.append(dict(case=nm, rsrc=r_, cext=c_, inl_ep_ppm=r.get("inl_ep_ppm", float("nan")), gain_err=r.get("gain_err", float("nan")),
                         offset=r.get("offset", float("nan")), tau_ns=tau * 1e9, ok=bool(r.get("ok")), problems=r["problems"]))
        print(f"rsrc {nm}: INL {rows[-1]['inl_ep_ppm']:.2f} ppm gain {rows[-1]['gain_err']:+.3e} offset {rows[-1]['offset']*VREF*1e6:+.1f} uV tau_in(no cap) {tau*1e9:.1f} ns "
              f"(t_half 250 ns) ok={rows[-1]['ok']} {r['problems'][:1]}")
    base = rows[0]["inl_ep_ppm"]
    spec_ok = rows[1]["ok"] and rows[1]["inl_ep_ppm"] <= base + 2.0
    print(f"SPEC input-source row (1 kohm without board cap): INL delta {rows[1]['inl_ep_ppm']-base:+.2f} ppm vs 2 ppm line -> {'consistent' if spec_ok else 'FLAG: breaks SPEC row'}")
    jdump(dict(rows=rows), "rsrc.json")
    ok = all(r["ok"] for r in rows) and spec_ok and all(math.isfinite(r["inl_ep_ppm"]) for r in rows)
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 9: non-vacuity
def mode_nonvac2(args):
    fails, notes = [], []
    r, gm_, rel = av_compare(0.8, "nv2_av_vsw08")
    rej = (not r["ok"]) or rel > 0.30
    print(f"nonvac2 A(v) vsw 0.8: deck INL {r['inl_ep_ppm']:.2f} vs model {gm_['inl_ep_ppm']:.2f} rel {rel*100:.0f} % -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}")
    if not rej:
        fails.append("av_vsw")
    base = dict(NULL_CFG, vcl=2.5, roff=1e14, nrst=4, n=args.n, vos1=P.VOS_3SIGMA, vos2=P.VOS_3SIGMA, vcmp=P.COMP_OFFSET_MAX, chop=True)
    u = 0.3
    res = []
    for late in (False, True):
        r2 = run_deck(dict(base, u_list=(u, -u), late=late), f"nv2_pair_late{int(late)}")
        uh = u_hat_of(r2)
        res.append(float(((uh[0] - uh[1]) / 2 - u) * VREF))
        if not r2["ok"]:
            fails.append(f"pair_run_late{int(late)}_problems:{r2['problems'][:1]}")
    rej = abs(res[1]) > P.TIER1_PAIR_RESID_V and abs(res[0]) <= P.TIER1_PAIR_RESID_V
    print(f"nonvac2 sys pair: on-time residual {res[0]*1e6:+.4f} uV, one cycle late {res[1]*1e6:+.3f} uV (limit {P.TIER1_PAIR_RESID_V*1e6}) -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}")
    if not rej:
        fails.append("pair_late")
    lo, hi = P.TIER1_VG_CM_RANGE
    for v in (2.0, 0.2):
        c = cm_run(v, 0.0, False, False, f"nv2_nod12_v{v}")
        vmin = min(c["vg1_cm_min_all"], c["vg2_cm_min_all"])
        vmax = max(c["vg1_cm_max_all"], c["vg2_cm_max_all"])
        out = vmin < lo or vmax > hi
        print(f"nonvac2 no-D12 Vin_cm {v}: vg CM [{vmin:.3f},{vmax:.3f}] vs [{lo},{hi}] -> {'REJECT (leaves range)' if out else 'stays in range (reported, not a rejection)'}")
        if v == 0.2 and not out:
            fails.append("nod12_cm")
        notes.append((v, vmin, vmax, out))
    jdump(dict(av=rel, pair=res, nod12=notes, fails=fails), "nonvac2.json")
    print("REJECT-as-required for all broken decks" if not fails else f"VACUOUS: {fails}")
    return 1 if not fails else 0

# =============================================================== WO-09 (S5c)
# ---- item 1: separated OTA1 / OTA2 knees (C-M1)
KN3_GRID2 = (8, 9, 10, 11, 12, 13.5, 15)            # V/us, 2 MHz
KN3_GRID4 = (9, 10, 11, 12, 13.5, 15)               # V/us, 4 MHz boost, base values (before the x2)
KN3_SETS = [  # label, fs, extra, N list, grid, OTAs swept
    ("2M", 2e6, {}, (256, 1024), KN3_GRID2, ("ota1", "ota2")),
    ("4M_boost", 4e6, {"boost": True}, (256, 1024), KN3_GRID4, ("ota1", "ota2")),
    ("4M_boost_OTA1only", 4e6, {"boost": True, "boost1_only": True}, (1024,), KN3_GRID4, ("ota1",)),
]
SR1_SPEC, SR2_SPEC = 12.0, 25.0                      # V/us, SPEC 3.0


def knee_of(pairs, thr):
    """pairs [(sr, inl)]. Returns (grid knee, interpolated knee): the lowest SR such that it and every higher SR meet INL <= thr.
    Interpolated = log-log crossing between the last failing and the first passing grid point (None when the knee is at/below the lowest SR)."""
    pairs = sorted(pairs)
    ok_ = [all(math.isfinite(q[1]) and q[1] <= thr for q in pairs[i:]) for i in range(len(pairs))]
    idx = next((i for i, g in enumerate(ok_) if g), None)
    if idx is None:
        return None, None
    grid = pairs[idx][0]
    if idx == 0:
        return grid, None
    (s0, i0), (s1, i1) = pairs[idx - 1], pairs[idx]
    if i0 <= 0 or i1 <= 0 or i0 == i1:
        return grid, grid
    f = (math.log(thr) - math.log(i0)) / (math.log(i1) - math.log(i0))
    return grid, math.exp(math.log(s0) + f * (math.log(s1) - math.log(s0)))


def knee_thresholds(fs, n):
    """(primary, secondary) INL thresholds in ppm FSR. 2 MHz: 20/1.5 (WO-09 rule) and the 8 ppm OTA line. 4 MHz: D28 fast-mode target and target/1.5."""
    if fs < 3e6:
        return P.TIER1_KNEE_PPM, P.TIER1_INL_BUDGET_PPM
    t = P.TIER1_INL_FAST[n]
    return t, t / 1.5


def mode_knees3(args):
    jobs = []
    for lab, fs, ex, ns, grid, otas in KN3_SETS:
        for n in ns:
            for ota in otas:
                for v in grid:
                    e = dict(ex)
                    e["fs"] = fs
                    if ota == "ota1":
                        e["sr"] = v * 1e6                     # OTA2 stays at its own spec (sr2 default 25 V/us)
                    else:
                        e["sr"], e["sr2"] = SR1_SPEC * 1e6, v * 1e6   # OTA1 at spec
                    jobs.append((lab, fs, n, ota, v, e))

    def one(j):
        lab, fs, n, ota, v, e = j
        return dc_metrics(v2_cfg(e, n=n, m=21), f"kn3_{lab}_{ota}_{v:g}_N{n}")
    with ThreadPoolExecutor(3) as ex_:
        rs = list(ex_.map(one, jobs))
    rows = []
    for j, r in zip(jobs, rs):
        lab, fs, n, ota, v, e = j
        rows.append(dict(set=lab, fs=fs, n=n, ota=ota, sr_vus=v, ok=bool(r.get("ok")), inl_ep_ppm=r.get("inl_ep_ppm", float("nan")),
                         gain_err=r.get("gain_err", float("nan")), runtime_s=r["runtime_s"], problems=r["problems"]))
        print(f"{lab} N{n} {ota} SR={v:g} V/us: INL {rows[-1]['inl_ep_ppm']:.3f} ppm gain {rows[-1]['gain_err']:+.2e} ok={r.get('ok')} {r['problems'][:1]}")
    knees, flags = {}, []
    print("\nKNEE TABLES (lowest SR [V/us] with INL <= threshold at it and every higher grid point; interp = log-log crossing)")
    for lab, fs, ex, ns, grid, otas in KN3_SETS:
        for n in ns:
            for ota in otas:
                pairs = [(r["sr_vus"], r["inl_ep_ppm"]) for r in rows if r["set"] == lab and r["n"] == n and r["ota"] == ota]
                t1, t2 = knee_thresholds(fs, n)
                ent = {}
                for nm, thr in (("primary", t1), ("secondary", t2)):
                    g, it = knee_of(pairs, thr)
                    ent[nm] = dict(thr_ppm=thr, grid=g, interp=it)
                spec = SR1_SPEC if ota == "ota1" else SR2_SPEC
                p_ = ent["primary"]
                kn = p_["interp"] if p_["interp"] is not None else p_["grid"]
                ent["margin_spec_over_knee"] = (spec / kn - 1.0) if kn else None
                key = f"{lab}/{ota}/N{n}"
                knees[key] = ent
                mg = ent["margin_spec_over_knee"]
                print(f"  {key}: INL [" + ", ".join(f"{a:g}:{b:.2f}" for a, b in sorted(pairs)) + "] ppm; "
                      f"knee@{t1:.1f}ppm grid {p_['grid']} interp {None if p_['interp'] is None else round(p_['interp'], 2)}; "
                      f"knee@{t2:.2f}ppm grid {ent['secondary']['grid']} interp {None if ent['secondary']['interp'] is None else round(ent['secondary']['interp'], 2)}; "
                      f"margin of {spec:g} V/us over primary knee {'n/a' if mg is None else f'{mg*100:.0f} %'}")
                if p_["grid"] is None or p_["grid"] > spec:
                    flags.append(f"FLAG {key}: knee {p_['grid']} above SPEC {spec:g} V/us")
                elif ota == "ota1" and (mg is None or mg < P.TIER1_KNEE_MARGIN_MIN):
                    flags.append(f"FLAG {key}: margin of {spec:g} V/us over the knee {'n/a' if mg is None else f'{mg*100:.0f} %'} < {P.TIER1_KNEE_MARGIN_MIN*100:.0f} %")
    ok = all(r["ok"] for r in rows) and all(math.isfinite(r["inl_ep_ppm"]) for r in rows) and len(rows) == len(jobs)
    for f_ in flags:
        print(f_)
    print(f"spec FLAG count: {len(flags)} (the exit code reflects run health only, not the spec flags)")
    jdump(dict(rows=rows, knees=knees, flags=flags), "knees3.json")
    print("run-health ACCEPT" if ok else "run-health REJECT")
    return 0 if ok else 1


# ---- items 2, 3: CMRR slope metric and the D12 residual with Cp,top
CMRR_SLOPE_FLOOR = 1e-9            # V/V: measurement floor of the slope (~180 dB)
CM2_VINS = (0.2, 1.0, 2.0)


def slope_cmrr(vins, vals, floor=CMRR_SLOPE_FLOOR):
    """CMRR = |dVin_cm / dVoff| as the least-squares slope of the offset over Vin_cm at fixed mismatch. Returns (slope V/V, dB)."""
    sl = float(np.polyfit(np.asarray(vins, float), np.asarray(vals, float), 1)[0])
    return sl, 20.0 * math.log10(1.0 / max(abs(sl), floor))


def eps_eff_closed(cp, dcp, eps_cs, cs=P.CS1, plus=False):
    """D12 residual, input-referred slope d(off)/d(Vin_cm), from charge conservation on the shorted top node (Cp+- = cp +- dcp/2, Cs+- = cs(1 +- eps/2)):
        eps_eff = ((cp/cs)*eps_cs - dcp/cs) / (1 + cp/cs).   plus=True returns the other sign convention (REVIEW section 5), used by the sign test."""
    p = cp / cs
    return (p * eps_cs + (dcp / cs if plus else -dcp / cs)) / (1.0 + p)


V_ICM = P.CM                        # V, island CM the OTA input pair is designed around (ASSUMED = mid-supply; V_icm is chosen in C1)
VG_CM_TOL = 0.15                    # V, REVIEW R7: vg1,cm must stay within V_icm +- 0.15 V over Vin_cm 0.2-2.0 V


def vg_cm_ok(lo, hi, vicm=V_ICM, tol=VG_CM_TOL):
    """True when the observed virtual-ground CM range [lo, hi] lies inside vicm +- tol. NaN fails."""
    return bool(math.isfinite(lo) and math.isfinite(hi) and lo >= vicm - tol and hi <= vicm + tol)


def mode_cm2(args):
    cs = P.CS1
    cases = [dict(name="nod12_ref", d12=False, cp=0.0, dcp=0.0, mm=0.0075), dict(name="D12_cp0_mm0", d12=True, cp=0.0, dcp=0.0, mm=0.0),
             dict(name="D12_cp0_mm0.75", d12=True, cp=0.0, dcp=0.0, mm=0.0075)]
    for cp in (10e-15, 20e-15):
        for dcp in (0.0, 0.25e-15, 1e-15):
            for mm in (0.0, 0.0075):
                cases.append(dict(name=f"D12_cp{cp*1e15:g}_d{dcp*1e15:g}_mm{mm*100:g}", d12=True, cp=cp, dcp=dcp, mm=mm))
    jobs = [(i, v) for i in range(len(cases)) for v in CM2_VINS]

    def one(j):
        i, v = j
        c = cases[i]
        return cm_run(v, c["mm"], c["d12"], False, f"cm2_{c['name']}_v{v}", cptop=c["cp"], dcptop=c["dcp"])
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(one, jobs))
    byc = {}
    for (i, v), r in zip(jobs, rs):
        byc.setdefault(i, []).append(r)
    rows = []
    for i, c in enumerate(cases):
        rr = byc[i]
        offs, pairs = [r["off_V"] for r in rr], [r["pair_V"] for r in rr]
        s_off, db_off = slope_cmrr(CM2_VINS, offs)
        s_on, db_on = slope_cmrr(CM2_VINS, pairs)
        cf = eps_eff_closed(c["cp"], c["dcp"], c["mm"], cs)
        cfp = eps_eff_closed(c["cp"], c["dcp"], c["mm"], cs, plus=True)
        row = dict(c, ok=all(r["ok"] for r in rr), slope_off=s_off, cmrr_off_db=db_off, slope_on=s_on, cmrr_on_db=db_on, closed=cf, closed_plus_alt=cfp,
                   off_V=offs, pair_V=pairs, vg1_cm_range=[min(r["vg1_cm_min_all"] for r in rr), max(r["vg1_cm_max_all"] for r in rr)],
                   problems=sum((r["problems"] for r in rr), []))
        if c["d12"]:
            if abs(cf) >= 5e-5:
                row["rel_err"] = abs(s_off - cf) / abs(cf)
                row["match"] = bool(row["rel_err"] <= 0.25)
                row["plus_rel_err"] = abs(s_off - cfp) / abs(cfp) if abs(cfp) > 0 else float("nan")
            else:
                row["match"] = bool(abs(s_off) <= 2e-8)           # closed form 0: the deck slope must sit at its floor
        rows.append(row)
        print(f"cm2 {c['name']}: slope_off {s_off:+.3e} (closed {cf:+.3e}, alt-sign {cfp:+.3e}"
              + (f", err {row['rel_err']*100:.1f} %, alt-sign err {row['plus_rel_err']*100:.0f} %" if "rel_err" in row else "")
              + f") sys-off CMRR {db_off:.1f} dB; sys-on slope {s_on:+.2e} CMRR {db_on:.1f} dB; off_V {[round(x*1e6, 3) for x in offs]} uV "
              f"vg1 CM [{row['vg1_cm_range'][0]:.3f},{row['vg1_cm_range'][1]:.3f}] ok={row['ok']} match={row.get('match')}")
    d12r = [r for r in rows if r["d12"]]
    alloc = [r for r in d12r if r["dcp"] <= 0.25e-15 + 1e-21]
    sign_cases = [r for r in d12r if "rel_err" in r and r["rel_err"] <= 0.25 and r["plus_rel_err"] > 0.25]
    chk = dict(runs_ok=all(r["ok"] for r in rows),
               closed_form_25pct=all(r["match"] for r in d12r),
               sign_discriminates=len(sign_cases) > 0,
               sys_off_60_at_alloc_dcp_le_0p25fF=all(r["cmrr_off_db"] >= P.TIER1_CMRR_TARGET_DB["sys_off"] for r in alloc),
               sys_on_100=all(r["cmrr_on_db"] >= P.TIER1_CMRR_TARGET_DB["sys_on"] for r in d12r),
               vg1_cm_within_vicm_pm_0p15=all(vg_cm_ok(*r["vg1_cm_range"]) for r in d12r))
    print(f"vg1 CM over Vin_cm {CM2_VINS[0]}-{CM2_VINS[-1]} V, D12 rows: [{min(r['vg1_cm_range'][0] for r in d12r):.3f}, {max(r['vg1_cm_range'][1] for r in d12r):.3f}] V "
          f"vs gate V_icm {V_ICM:g} +- {VG_CM_TOL} = [{V_ICM - VG_CM_TOL:.3f}, {V_ICM + VG_CM_TOL:.3f}] V; no-D12 reference row (not gated, shows what D12 buys): "
          f"[{rows[0]['vg1_cm_range'][0]:.3f}, {rows[0]['vg1_cm_range'][1]:.3f}] V -> {'in' if vg_cm_ok(*rows[0]['vg1_cm_range']) else 'OUT of'} range")
    print("checks:", chk, f"; sign-discriminating cases (deck within 25 % of the '-' form, '+' form off by >25 %): {len(sign_cases)}")
    for r in d12r:
        if r["cmrr_off_db"] < P.TIER1_CMRR_TARGET_DB["sys_off"]:
            print(f"FLAG CMRR sys-off {r['cmrr_off_db']:.1f} dB < {P.TIER1_CMRR_TARGET_DB['sys_off']} dB at {r['name']} (dCp,top {r['dcp']*1e15:g} fF)")
        if r["cmrr_on_db"] < P.TIER1_CMRR_TARGET_DB["sys_on"]:
            print(f"FLAG CMRR sys-on {r['cmrr_on_db']:.1f} dB < {P.TIER1_CMRR_TARGET_DB['sys_on']} dB at {r['name']}")
    ok = all(chk.values())
    jdump(dict(rows=rows, checks=chk), "cm2.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 4: island CM drift from leakage
def drift_run(fs, n, ileak, tag, anchored=False, **kw):
    """One conversion at u = 0 with ileak drawn from each vg node (both sides, same sign). Returns the drift of the island CM per stage [V]:
    least-squares slope of the CM sampled once per cycle (0.4 T after the cycle start) times N T."""
    ex = dict(fs=fs, nrst=4, u_list=(0.0,), extra=CMX, ileak=ileak)
    if not anchored:
        ex.update(roff=1e16, rbl=1e16, rfl=1e16)       # WO-09: bleeders and switch Roff raised to 1e16 ohm so nothing anchors the island
    ex.update(kw)
    r = run_deck(v2_cfg(ex, n=n, m=1), tag)
    out = dict(ok=bool(r["ok"]), problems=r["problems"], runtime_s=r["runtime_s"])
    if "cols" not in r:
        out["ok"] = False
        return out
    T, t0 = r["meta"]["T"], r["meta"]["t0"][0]
    t = r["cols"]["t"]
    js = np.arange(2, n)
    ts = t0 + js * T + 0.4 * T
    for k in (1, 2):
        cmv = np.interp(ts, t, 0.5 * (r["cols"][f"vg{k}p"] + r["cols"][f"vg{k}n"]))
        sl = float(np.polyfit(ts, cmv, 1)[0])
        out[f"drift{k}_V"] = sl * n * T
        out[f"cm{k}_start_V"], out[f"cm{k}_end_V"] = float(cmv[0]), float(cmv[-1])
    return out


def drift_closed(fs, n, ileak, stage):
    """Island CM drift [V; negative for a current drawn out of the nodes] = I_total N / (fs C_island) with I_total = 2 ileak (both sides) and
    C_island = 2 C_side, C_side = Cs (+ Ck) + Cint + Cp,vg of that stage (Cs/Ck bottoms sit on hard sources while the tops connect to vg)."""
    cside = (P.CS1 + P.CINT1 + P.TIER1_CP_VG) if stage == 1 else (P.CS2 + P.K * P.CS2 + P.CINT2 + P.TIER1_CP_VG)
    return -(2 * ileak) * n / (fs * 2 * cside)


def drift_limit_ok(d):
    """Island CM excursion limit (informational, V_icm +- 0.2 V from REVIEW-S4S5b C-M4). Applies to either stage; NaN fails."""
    return bool(math.isfinite(d) and abs(d) <= P.TIER1_DRIFT_LIMIT_V)


CM_STEP_V = 0.13                    # V, D12 CM step (cm2 -0.10/+0.08 V) + 10 mV CMFB, REVIEW section 10 input-CM row


def drift_budget(d):
    """REVIEW R6: lower input-pair CM limit relative to V_icm for a drift d (negative = downward): V_icm - 0.13 - |d|. Informational; the
    limit itself is set in C1. Returns (lower offset from V_icm, upper offset) in V."""
    return -(CM_STEP_V + max(0.0, -d)), CM_STEP_V + max(0.0, d)


def mode_drift(args):
    il = P.TIER1_ILEAK
    cases = [("2M_N4096", 2e6, 4096, False), ("0p25M_N4096", 0.25e6, 4096, False), ("0p25M_N1024", 0.25e6, 1024, False),
             ("0p25M_N1024_anchored", 0.25e6, 1024, True)]

    def one(c):
        nm, fs, n, anch = c
        return drift_run(fs, n, il, f"dr_{nm}", anchored=anch)
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(one, cases))
    rows, ok = [], True
    for (nm, fs, n, anch), r in zip(cases, rs):
        row = dict(case=nm, fs=fs, n=n, anchored=anch, ileak=il, **r)
        for k in (1, 2):
            cf = drift_closed(fs, n, il, k)
            row[f"closed{k}_V"] = cf
            row[f"rel{k}"] = abs(r.get(f"drift{k}_V", float("nan")) - cf) / abs(cf)
        gated = not anch
        good = bool(r["ok"] and all(math.isfinite(row[f"rel{k}"]) for k in (1, 2)) and (not gated or all(row[f"rel{k}"] <= 0.25 for k in (1, 2))))
        row["gated"], row["good"] = gated, good
        ok &= good
        rows.append(row)
        d1 = r.get("drift1_V", float("nan"))
        d2 = r.get("drift2_V", float("nan"))
        print(f"drift {nm} (fs {fs/1e6:g} MHz, N {n}, {il*1e12:g} pA per side{', bleeders 1e12/1e13 + Roff 1e12 KEPT (contrast, not gated)' if anch else ''}): "
              f"stage 1 {d1*1e3:+.2f} mV (closed {row['closed1_V']*1e3:+.2f}, err {row['rel1']*100:.1f} %), "
              f"stage 2 {r.get('drift2_V', float('nan'))*1e3:+.2f} mV (closed {row['closed2_V']*1e3:+.2f}, err {row['rel2']*100:.1f} %) "
              f"| |drift| vs V_icm +- {P.TIER1_DRIFT_LIMIT_V} V: stage 1 {'ok' if drift_limit_ok(d1) else 'FLAG exceeded'}, stage 2 {'ok' if drift_limit_ok(d2) else 'FLAG exceeded'}; "
              f"input-pair CM window needed (V_icm +): stage 1 [{drift_budget(d1)[0]:+.3f}, {drift_budget(d1)[1]:+.3f}] V, stage 2 [{drift_budget(d2)[0]:+.3f}, {drift_budget(d2)[1]:+.3f}] V "
              f"(+-{CM_STEP_V} V CM step + drift; informational, limit set in C1); ok={r['ok']} {r['problems'][:1]}")
        row["limit_ok"] = [drift_limit_ok(d1), drift_limit_ok(d2)]
        row["cm_window_1"], row["cm_window_2"] = list(drift_budget(d1)), list(drift_budget(d2))
        if gated:
            for k_, d_ in ((1, d1), (2, d2)):
                if not drift_limit_ok(d_):
                    print(f"FLAG drift stage {k_} {d_*1e3:+.1f} mV exceeds {P.TIER1_DRIFT_LIMIT_V} V ({nm}); informational (exit code reflects run health and closed-form agreement)")
    print("note: I is the leakage of EACH island side (100 pA/side = 200 pA island total); the REVIEW's 21 mV / 170 mV figures count 100 pA for the whole island.")
    jdump(dict(rows=rows), "drift.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 5: pin-path CMRR (m6)
def pad_g(tau, t_s, T):
    """Steady-state pad-node deviation at the end of the sampling phase per unit (q/Cpad): exp(-t_s/tau)/(1-exp(-T/tau)); -> tau/T for tau >> T."""
    return math.exp(-t_s / tau) / (1.0 - math.exp(-T / tau))


def pin_eps_closed(rpad, dr, cpad, cp, fs, cs=P.CS1, rsrc=0.0):
    """Sys-on pin-path slope d(pair err)/d(Vin_cm) with dr on one pin only (D12: CM pin charge per cycle q = Cs Cp/(Cs+Cp) X, X = Vin_cm - Vref_cm).
    Settling-aware: eps = (q/X)/Cpad * (g(tau_n) - g(tau_p)). The tau >> T limit is dr*fs*Cp' (the review's 1/(dr fs Cp,top) bound)."""
    T = 1.0 / fs
    t_s = T / 2 - 2 * 12.5e-9               # length of phi1 = sample instant measured from its start
    qx = cs * cp / (cs + cp)
    tp, tn = (rpad + rsrc) * cpad, (rpad + rsrc + dr) * cpad
    return qx / cpad * (pad_g(tn, t_s, T) - pad_g(tp, t_s, T))


def pin_run(vin_cm, dr, pad_c, nrst, tag, u0=0.08, cp=None):
    """Sys-on pair with the pin-side swap modelled: conversion A has the extra R on VIN- and +u0; conversion B has it on VIN+ and -u0
    (the swap exchanges which chip node the pin R feeds). Returns the pair-demodulated error [V]."""
    cp = P.TIER1_CP_TOP if cp is None else cp
    res = []
    for sgn, nm in ((+1, "A"), (-1, "B")):
        cfg = v2_cfg(dict(vin_cm=vin_cm, d12=True, cptop=cp, drsrc=sgn * dr, pad_c=pad_c, nrst=nrst, u_list=(sgn * u0,)), n=256, m=1)
        res.append(run_deck(cfg, f"{tag}_{nm}"))
    uh = [u_hat_of(r)[0] for r in res]
    return dict(ok=all(r["ok"] for r in res), problems=sum((r["problems"] for r in res), []), pair_V=float(((uh[0] - uh[1]) / 2 - u0) * VREF),
                a_V=float((uh[0] - u0) * VREF), b_V=float((uh[1] + u0) * VREF))


RS2_CASES = [("A_pad5p", 5e-12, 4), ("B_pad2n", 2e-9, 16)]       # label, pad cap, reset cycles (B: the pad node must reach its periodic steady state)
RS2_DR = (0.0, 50.0)
RS2_VINS = (0.2, 2.0)


def mode_rsrc2(args):
    fs = P.FS_NOM
    jobs = [(lab, pc, nr, v, dr) for lab, pc, nr in RS2_CASES for dr in RS2_DR for v in RS2_VINS]

    def one(j):
        lab, pc, nr, v, dr = j
        return pin_run(v, dr, pc, nr, f"rs2_{lab}_dr{dr:g}_v{v}")
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(one, jobs))
    res = {j: r for j, r in zip(jobs, rs)}
    rows = []
    for lab, pc, nr in RS2_CASES:
        for dr in RS2_DR:
            vals = [res[(lab, pc, nr, v, dr)]["pair_V"] for v in RS2_VINS]
            sl = (vals[1] - vals[0]) / (RS2_VINS[1] - RS2_VINS[0])
            db = 20 * math.log10(1.0 / max(abs(sl), CMRR_SLOPE_FLOOR))
            cf = pin_eps_closed(P.PAD_R, dr, pc, P.TIER1_CP_TOP, fs)
            wo = dr * fs * P.TIER1_CP_TOP                                      # review form (tau >> T limit)
            row = dict(case=lab, pad_c=pc, dr=dr, pair_V=vals, slope=sl, cmrr_on_db=db, closed_settling=cf, wo_form=wo,
                       wo_cmrr_db=(20 * math.log10(1 / wo) if wo else float("inf")), ok=all(res[(lab, pc, nr, v, dr)]["ok"] for v in RS2_VINS),
                       problems=sum((res[(lab, pc, nr, v, dr)]["problems"] for v in RS2_VINS), []))
            if dr:
                row["rel_settling"] = abs(sl - cf) / abs(cf) if cf else float("inf")
                row["rel_wo"] = abs(sl - wo) / wo
            rows.append(row)
            print(f"rsrc2 {lab} dR {dr:g} ohm (pad {pc*1e12:g} pF, Cp,top {P.TIER1_CP_TOP*1e15:g} fF): pair err at Vin_cm {RS2_VINS} = {[round(x*1e9, 3) for x in vals]} nV, "
                  f"slope {sl:+.3e} sys-on CMRR {db:.1f} dB; closed (settling-aware) {cf:+.3e}; review form 1/(dR fs Cp) {wo:.3e} = {row['wo_cmrr_db']:.1f} dB"
                  + (f"; deck vs settling-aware {row['rel_settling']*100:.0f} %, vs review form {row['rel_wo']*100:.0f} %" if dr else "") + f" ok={row['ok']} {row['problems'][:1]}")
    A = next(r for r in rows if r["case"].startswith("A") and r["dr"])
    B = next(r for r in rows if r["case"].startswith("B") and r["dr"])
    chk = dict(runs_ok=all(r["ok"] for r in rows),
               B_within_30pct_of_settling_aware=bool(B["rel_settling"] <= 0.30),
               B_sign_ok=bool(B["slope"] * B["closed_settling"] > 0),
               A_deck_not_worse_than_review_bound=bool(A["cmrr_on_db"] >= A["wo_cmrr_db"] - 1.0),
               dr0_at_floor=all(abs(r["slope"]) <= 2e-8 for r in rows if not r["dr"]))
    if A["rel_wo"] > 0.30:
        print(f"FINDING: with the SPEC pad (5 pF, tau {P.PAD_R*5e-12*1e9:.1f} ns << t_half) the pin node settles inside the phase: deck CMRR {A['cmrr_on_db']:.1f} dB >= the review bound "
              f"{A['wo_cmrr_db']:.1f} dB, so 1/(dR fs Cp,top) is a bound valid only for tau_pin >~ T (board cap behind dR); case B (pad {RS2_CASES[1][1]*1e9:g} nF) is in that regime")
    print("checks:", chk)
    ok = all(chk.values())
    jdump(dict(rows=rows, checks=chk), "rsrc2.json")
    print("ACCEPT" if ok else "REJECT")
    return 0 if ok else 1


# ---- item 8: non-vacuity of the S5c checks
def mode_nonvac3(args):
    fails = []
    # (a) dCp,top 2 fF must REJECT the 60 dB sys-off gate; control: 0.25 fF passes it
    dbs = {}
    for dcp in (0.25e-15, 2e-15):
        rr = [cm_run(v, 0.0, True, False, f"nv3_dcp{dcp*1e15:g}_v{v}", cptop=20e-15, dcptop=dcp) for v in CM2_VINS]
        sl, db = slope_cmrr(CM2_VINS, [r["off_V"] for r in rr])
        dbs[dcp] = (db, sl, all(r["ok"] for r in rr))
    gate = P.TIER1_CMRR_TARGET_DB["sys_off"]
    rej = dbs[2e-15][0] < gate and dbs[2e-15][2]
    ctl = dbs[0.25e-15][0] >= gate and dbs[0.25e-15][2]
    print(f"nonvac3 dCp,top 2 fF (Cp 20 fF, eps_Cs 0): sys-off CMRR {dbs[2e-15][0]:.1f} dB vs gate {gate} dB -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}; "
          f"control dCp 0.25 fF {dbs[0.25e-15][0]:.1f} dB -> {'passes (good)' if ctl else 'FAILS (check is broken)'}")
    if not (rej and ctl):
        fails.append("dcp_2fF")
    # (b) OTA1 SR 6 V/us at 2 MHz N 256 must REJECT the knee gate; control: 12 V/us passes
    inl = {}
    for sr in (6e6, 12e6):
        r = dc_metrics(v2_cfg(dict(sr=sr), n=256, m=21), f"nv3_sr{sr/1e6:g}")
        inl[sr] = (r.get("inl_ep_ppm", float("nan")), bool(r.get("ok")))
    rej = inl[6e6][1] and inl[6e6][0] > P.TIER1_KNEE_PPM
    ctl = inl[12e6][1] and inl[12e6][0] <= P.TIER1_KNEE_PPM
    print(f"nonvac3 OTA1 SR 6 V/us (2 MHz, N 256): INL {inl[6e6][0]:.2f} ppm vs {P.TIER1_KNEE_PPM:.2f} -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}; "
          f"control SR 12 V/us {inl[12e6][0]:.2f} ppm -> {'passes (good)' if ctl else 'FAILS (check is broken)'}")
    if not (rej and ctl):
        fails.append("sr6")
    # (c) 10 nA leakage at 0.25 MHz must REJECT the island-drift limit; control: 100 pA passes
    dr = {}
    for il in (10e-9, P.TIER1_ILEAK):
        dr[il] = drift_run(0.25e6, 256, il, f"nv3_leak{il*1e12:g}p")
    rej = dr[10e-9]["ok"] and not drift_limit_ok(dr[10e-9]["drift1_V"])
    ctl = dr[P.TIER1_ILEAK]["ok"] and drift_limit_ok(dr[P.TIER1_ILEAK]["drift1_V"])
    print(f"nonvac3 leakage 10 nA (0.25 MHz, N 256): stage-1 drift {dr[10e-9]['drift1_V']:+.3f} V vs limit {P.TIER1_DRIFT_LIMIT_V} V -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}; "
          f"control 100 pA {dr[P.TIER1_ILEAK]['drift1_V']*1e3:+.1f} mV -> {'passes (good)' if ctl else 'FAILS (check is broken)'}")
    if not (rej and ctl):
        fails.append("leak10n")
    jdump(dict(dcp={str(k): v for k, v in dbs.items()}, sr={str(k): v for k, v in inl.items()}, leak={str(k): v for k, v in dr.items()}, fails=fails), "nonvac3.json")
    print("REJECT-as-required for all broken decks" if not fails else f"VACUOUS: {fails}")
    return 1 if not fails else 0


# =============================================================== WO-12 (S5d)
def mode_nonvac4(args):
    """Non-vacuity of the WO-12 gates: (a) no-D12 must REJECT the vg1 CM gate (control: D12 passes); (b) OTA1 SR 8 V/us must REJECT the slew-share
    knee threshold (control 12.5 V/us passes); (c) 10 nA leakage must REJECT the stage-2 drift limit (control 100 pA passes)."""
    fails = []
    rng_ = {}
    for d12 in (False, True):
        rr = [cm_run(v, 0.0075, d12, False, f"nv4_d12{int(d12)}_v{v}") for v in (0.2, 1.0, 2.0)]
        rng_[d12] = (min(r["vg1_cm_min_all"] for r in rr), max(r["vg1_cm_max_all"] for r in rr), all(r["ok"] for r in rr))
    rej = rng_[False][2] and not vg_cm_ok(rng_[False][0], rng_[False][1])
    ctl = rng_[True][2] and vg_cm_ok(rng_[True][0], rng_[True][1])
    print(f"nonvac4 no-D12 vg1 CM [{rng_[False][0]:.3f}, {rng_[False][1]:.3f}] V vs V_icm {V_ICM:g} +- {VG_CM_TOL} -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}; "
          f"control D12 [{rng_[True][0]:.3f}, {rng_[True][1]:.3f}] V -> {'passes (good)' if ctl else 'FAILS (check is broken)'}")
    if not (rej and ctl):
        fails.append("nod12_vg_cm")
    thr = SLEW_SHARE_PPM / KNEE_MARGIN_X
    inl = {}
    for sr in (8e6, 12.5e6):
        r = dc_metrics(v2_cfg(dict(sr=sr), n=256, m=21), f"nv4_sr{sr/1e6:g}")
        inl[sr] = (r.get("inl_ep_ppm", float("nan")), bool(r.get("ok")))
    rej = inl[8e6][1] and inl[8e6][0] > thr
    ctl = inl[12.5e6][1] and inl[12.5e6][0] <= thr
    print(f"nonvac4 OTA1 SR 8 V/us (2 MHz, N 256): INL {inl[8e6][0]:.2f} ppm vs slew-share threshold {thr:.3f} -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}; "
          f"control 12.5 V/us {inl[12.5e6][0]:.3f} ppm -> {'passes (good)' if ctl else 'FAILS (check is broken)'}")
    if not (rej and ctl):
        fails.append("sr8")
    dr = {il: drift_run(0.25e6, 256, il, f"nv4_leak{il*1e12:g}p") for il in (10e-9, P.TIER1_ILEAK)}
    rej = dr[10e-9]["ok"] and not drift_limit_ok(dr[10e-9]["drift2_V"])
    ctl = dr[P.TIER1_ILEAK]["ok"] and drift_limit_ok(dr[P.TIER1_ILEAK]["drift2_V"])
    print(f"nonvac4 leakage 10 nA (0.25 MHz, N 256): stage-2 drift {dr[10e-9]['drift2_V']:+.3f} V vs limit {P.TIER1_DRIFT_LIMIT_V} V -> {'REJECT (as required)' if rej else 'ACCEPT (BAD)'}; "
          f"control 100 pA {dr[P.TIER1_ILEAK]['drift2_V']*1e3:+.1f} mV -> {'passes (good)' if ctl else 'FAILS (check is broken)'}")
    if not (rej and ctl):
        fails.append("leak10n_stage2")
    jdump(dict(vg_cm={str(k): v for k, v in rng_.items()}, sr={str(k): v for k, v in inl.items()}, leak={str(k): v for k, v in dr.items()}, fails=fails), "nonvac4.json")
    print("REJECT-as-required for all broken decks" if not fails else f"VACUOUS: {fails}")
    return 1 if not fails else 0


# ---- R1, R2: knees at the slew INL share, OTA2 GBW fast-mode sweep
SLEW_SHARE_PPM = 2.0               # ppm FSR, REVIEW R1: slew gets its own INL line (from the 4 ppm reserve); the OTA line is used by A(v)
KNEE_MARGIN_X = 1.5                # the 1.5x margin of the knee rule
KN4_EXTRA = {"ota1": (9.5, 10.5), "ota2": (12.5,)}          # V/us, added to KN3_GRID2 at 2 MHz
R2_GBW2 = (10e6, 15e6, 20e6, 25e6)
R2_NS = (256, 1024)
R2_TARGET_PPM = 5.0                 # D28 provisional N 1024 fast-mode target (R10: user decision; used here only to answer the OTA2 GBW question)


def mode_knees4(args):
    prev = {}
    if getattr(args, "prev", None) and os.path.exists(args.prev):
        for r in json.load(open(args.prev))["rows"]:
            if r["set"] == "2M" and r["ok"] and math.isfinite(r["inl_ep_ppm"]):
                prev[(r["n"], r["ota"], float(r["sr_vus"]))] = r
    jobs = []        # (kind, key, cfg-extra, n)
    for n in (256, 1024):
        for ota in ("ota1", "ota2"):
            for v in sorted(set(KN3_GRID2) | set(KN4_EXTRA[ota])):
                e = {"fs": 2e6}
                if ota == "ota1":
                    e["sr"] = v * 1e6
                else:
                    e["sr"], e["sr2"] = SR1_SPEC * 1e6, v * 1e6
                jobs.append(("R1", (n, ota, float(v)), e, n))
    for n in R2_NS:
        for g in R2_GBW2:
            jobs.append(("R2", (n, g), {"fs": 4e6, "boost": True, "boost1_only": True, "sr": 12.5e6, "sr2": 13.5e6, "gbw2": g}, n))
    todo = [j for j in jobs if not (j[0] == "R1" and j[1] in prev)]
    print(f"knees4: {len(jobs)} points, {len(jobs) - len(todo)} reused from --prev, {len(todo)} to run")

    def one(j):
        kind, key, e, n = j
        tag = f"kn4_{kind}_" + "_".join(f"{x:g}" if not isinstance(x, str) else x for x in key)
        return dc_metrics(v2_cfg(e, n=n, m=21), tag)
    with ThreadPoolExecutor(3) as ex_:
        out = list(ex_.map(one, todo))
    res = {(j[0], j[1]): r for j, r in zip(todo, out)}
    rows = []
    for kind, key, e, n in jobs:
        if kind == "R1" and key in prev:
            r = prev[key]
            rows.append(dict(kind=kind, n=n, ota=key[1], sr_vus=key[2], ok=True, inl_ep_ppm=r["inl_ep_ppm"], source="prev"))
        else:
            r = res[(kind, key)]
            row = dict(kind=kind, n=n, ok=bool(r.get("ok")), inl_ep_ppm=r.get("inl_ep_ppm", float("nan")), gain_err=r.get("gain_err", float("nan")),
                       runtime_s=r["runtime_s"], problems=r["problems"], source="run")
            if kind == "R1":
                row.update(ota=key[1], sr_vus=key[2])
            else:
                row.update(gbw2_MHz=key[1] / 1e6)
            rows.append(row)
    thr = SLEW_SHARE_PPM / KNEE_MARGIN_X
    knees = {}
    print(f"\nR1: knee at the slew INL share {SLEW_SHARE_PPM:g} ppm / {KNEE_MARGIN_X:g} = {thr:.3f} ppm (2 MHz; lowest SR with INL <= threshold at it and every higher grid point; interp = log-log)")
    for n in (256, 1024):
        for ota in ("ota1", "ota2"):
            pairs = [(r["sr_vus"], r["inl_ep_ppm"]) for r in rows if r["kind"] == "R1" and r["n"] == n and r["ota"] == ota]
            g, it = knee_of(pairs, thr)
            kn = it if it is not None else g
            ent = dict(thr_ppm=thr, grid=g, interp=it, pairs=sorted(pairs))
            if ota == "ota1":
                ent["margin"] = {str(sv): (sv / kn - 1.0 if kn else None) for sv in (12.0, 12.5)}
            else:
                ent["margin"] = {str(sv): (sv / kn - 1.0 if kn else None) for sv in (13.5, 25.0)}
            knees[f"{ota}/N{n}"] = ent
            print(f"  {ota} N{n}: INL [" + ", ".join(f"{a:g}:{b:.3f}" for a, b in sorted(pairs)) + f"] ppm; knee grid {g} interp {None if it is None else round(it, 2)} V/us; margin "
                  + ", ".join(f"{k} V/us: {'n/a' if v is None else f'{v*100:.0f} %'}" for k, v in ent["margin"].items()))
    print("\nR2: 4 MHz, OTA1 boosted (base SR 12.5 -> 25 V/us), OTA2 unboosted SR 13.5 V/us, loaded GBW2 sweep, 21 DC points")
    for n in R2_NS:
        pr = sorted((r["gbw2_MHz"], r["inl_ep_ppm"]) for r in rows if r["kind"] == "R2" and r["n"] == n)
        print(f"  N{n}: " + ", ".join(f"GBW2 {a:g} MHz: {b:.2f} ppm" for a, b in pr))
    p1024 = sorted((r["gbw2_MHz"], r["inl_ep_ppm"]) for r in rows if r["kind"] == "R2" and r["n"] == 1024)
    first = next((a for a, b in p1024 if b <= R2_TARGET_PPM), None)
    print(f"R2 answer: lowest swept OTA2 GBW with N1024 INL <= {R2_TARGET_PPM:g} ppm (provisional D28 target): {first} MHz (fast-mode option (a): OTA1-only boost + OTA2 loaded GBW at base bias)")
    ok = all(r["ok"] for r in rows) and all(math.isfinite(r["inl_ep_ppm"]) for r in rows) and len(rows) == len(jobs)
    jdump(dict(rows=rows, knees=knees, thr_ppm=thr, r2_first_gbw_MHz=first, r2_target_ppm=R2_TARGET_PPM), "knees4.json")
    print("run-health ACCEPT" if ok else "run-health REJECT")
    return 0 if ok else 1


# ---- WO-13: V4 (2 MHz, N 4096, OTA2 SR) and V5 (fast-mode options)
V4_SR2 = (11.0, 13.5)                  # V/us
V5_TARGET = {256: 20.0, 1024: 5.0}     # provisional fast-mode INL targets [ppm FSR] (D28)
V5_I1, V5_I2, V5_IOTHER = 4.75, 2.4, 26.0   # review M2: uA per V/us (OTA1 CL 1.4 pF, OTA2 CL 0.7 pF) + other [uA]
V5_GBW1_FULL, V5_GBW2_FULL = (10e6, 16e6, 20e6), (10e6, 15e6, 20e6, 25e6)
V5_GBW2_BOOST15 = (10e6, 15e6, 20e6)   # base values, loaded = x1.5


def fast_current_uA(sr1_eff, sr2_eff):
    return V5_I1 * sr1_eff + V5_I2 * sr2_eff + V5_IOTHER


def mode_fast2(args):
    jobs = []      # (kind, key, extra, n, m)
    for sr2 in V4_SR2:
        jobs.append(("V4", (4096, sr2), {"fs": 2e6, "sr": 12.5e6, "sr2": sr2 * 1e6}, 4096, 11))
    for n in R2_NS:
        for g2 in V5_GBW2_BOOST15:
            jobs.append(("V5i", (n, g2), {"fs": 4e6, "bst1": 2.0, "bst2": 1.5, "sr": 12.5e6, "sr2": 13.5e6, "gbw": 10e6, "gbw2": g2}, n, 21))
    for n in R2_NS:
        for g1 in V5_GBW1_FULL:
            for g2 in V5_GBW2_FULL:
                jobs.append(("V5ii", (n, g1, g2), {"fs": 3e6, "sr": 12.5e6, "sr2": 13.5e6, "gbw": g1, "gbw2": g2}, n, 21))
    only = getattr(args, "only", None)
    if only:
        jobs = [j for j in jobs if j[0] in only.split(",")]
    print(f"fast2: {len(jobs)} deck jobs")

    def one(j):
        kind, key, e, n, m = j
        tag = f"f2_{kind}_" + "_".join(f"{x:g}" for x in key)
        return dc_metrics(v2_cfg(e, n=n, m=m), tag)
    with ThreadPoolExecutor(3) as ex_:
        out = list(ex_.map(one, jobs))
    rows = []
    for (kind, key, e, n, m), r in zip(jobs, out):
        rows.append(dict(kind=kind, key=list(key), n=n, m=m, ok=bool(r.get("ok")), inl_ep_ppm=r.get("inl_ep_ppm", float("nan")), inl_bf_ppm=r.get("inl_bf_ppm", float("nan")),
                         gain_err=r.get("gain_err", float("nan")), runtime_s=r.get("runtime_s", float("nan")), problems=r.get("problems", []), extra={k: v for k, v in e.items()}))
    thr13 = SLEW_SHARE_PPM / KNEE_MARGIN_X
    print(f"\nV4: 2 MHz, N 4096, OTA1 12.5 V/us, 11 DC points. Knee margin is against the slew INL share {SLEW_SHARE_PPM:g} ppm / {KNEE_MARGIN_X:g} = {thr13:.3f} ppm (= 1.333 ppm)")
    for r in rows:
        if r["kind"] == "V4":
            print(f"  OTA2 SR {r['key'][1]:g} V/us: INL(ep) {r['inl_ep_ppm']:.4f} ppm (best-fit {r['inl_bf_ppm']:.4f}), gain {r['gain_err']:+.3e}; headroom to {thr13:.3f}: {thr13 / r['inl_ep_ppm']:.2f}x; {r['runtime_s']:.0f} s")
    print("\nV5 (i): 4 MHz, OTA1 boost x2 (12.5 -> 25 V/us, base GBW1 10 -> 20 MHz), OTA2 boost x1.5 (13.5 -> 20.25 V/us), 21 DC points")
    i_fast = fast_current_uA(25.0, 20.25)
    i_prec = fast_current_uA(12.5, 13.5)
    print(f"  current (review M2 per-SR rule: OTA1 {V5_I1}, OTA2 {V5_I2} uA per V/us, + {V5_IOTHER:g} uA): fast {i_fast:.0f} uA, precision {i_prec:.0f} uA")
    for r in rows:
        if r["kind"] == "V5i":
            n, g2 = r["key"]
            print(f"  N{n:g} base GBW2 {g2/1e6:g} MHz (loaded {g2*1.5/1e6:g}): INL {r['inl_ep_ppm']:.3f} ppm vs target {V5_TARGET[int(n)]:g}: {'PASS' if r['inl_ep_ppm'] <= V5_TARGET[int(n)] else 'FAIL'}")
    print("\nV5 (ii): 3 MHz, no boost, OTA1 12.5, OTA2 13.5 V/us, 21 DC points")
    print(f"  current: {fast_current_uA(12.5, 13.5):.0f} uA (same as precision; D31 cap 200 uA)")
    for n in R2_NS:
        print(f"  N{n} (target {V5_TARGET[n]:g} ppm) INL ppm, rows GBW1, cols GBW2 {[g/1e6 for g in V5_GBW2_FULL]} MHz")
        for g1 in V5_GBW1_FULL:
            vals = []
            for g2 in V5_GBW2_FULL:
                rr = next(r for r in rows if r["kind"] == "V5ii" and r["key"] == [n, g1, g2])
                vals.append(rr["inl_ep_ppm"])
            print(f"    GBW1 {g1/1e6:g}: " + "  ".join(f"{v:8.3f}" for v in vals))
    ok = all(r["ok"] for r in rows) and all(math.isfinite(r["inl_ep_ppm"]) for r in rows) and len(rows) == len(jobs)
    jdump(dict(rows=rows, v4_threshold_ppm=thr13, current_uA=dict(fast_i=i_fast, precision=i_prec)), "fast2.json")
    print("run-health ACCEPT" if ok else "run-health REJECT")
    return 0 if ok else 1


# ---- WO-14: gm/Id table (item 1), gm-boost realism (item 2), V4 margin point (item 3)
GMID_DEVS = ("01v8", "n01v8", "g5v0d10v5")      # D40: pfet_01v8 primary, nfet_01v8, pfet_g5v0d10v5 comparison
GMID_PRIMARY = "01v8"
GMID_CORNERS = ("tt", "ss", "ff")
GMID_TEMPS = (-40, 27, 100, 125)
GMID_LS = (1.0, 2.0, 0.35, 0.5)
GMID_W = 10.0
GMID_J = (1e-9, 1e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5)     # Id/(W/L) [A] columns of the table
GMID_BASES = {"OTA1": ((10.0,), (2.0,)), "OTA2": ((14.0, 17.0), (1.5, 2.0))}
GMID_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "work", "v1-design", "results", "gmid_table.json")
V4_MARGIN_SR2 = 13.5 / 1.25            # V/us: OTA2 SR 25 % below the confirmed 13.5 (D39)
V4_MARGIN_INL_MAX = SLEW_SHARE_PPM / KNEE_MARGIN_X   # 1.333 ppm


def gmid_curve(path, col):
    """(J = Id/(W/L), gm/Id) from one wrdata csv written with wr_singlescale (cols: Vsg, Id1, Id2); gm = dId/dVsg."""
    d = np.loadtxt(path)
    v, i = d[:, 0], np.abs(d[:, 1 + col])
    gm = np.gradient(i, v)
    ok = i > 1e-13
    wl = GMID_W / GMID_LS[col]
    return i[ok] / wl, gm[ok] / i[ok]


def gmid_at(J, g, j):
    """gm/Id at current density j (log-interp, strong-inversion side of the peak so the curve is monotone). nan outside the range."""
    pk = int(np.argmax(g))
    J, g = J[pk:], g[pk:]
    if j < J[0] or j > J[-1]:
        return float("nan")
    return float(np.interp(math.log(j), np.log(J), g))


def j_for_gmid(J, g, target):
    pk = int(np.argmax(g))
    J, g = J[pk:], g[pk:]
    if target > g[0] or target < g[-1]:
        return float("nan")
    return float(math.exp(np.interp(-target, -g, np.log(J))))


def gm_ratio(J, g, base, k):
    """gm(k Id)/gm(Id) at the same W/L, starting from gm/Id = base: k * gmid(k J0) / base."""
    j0 = j_for_gmid(J, g, base)
    if not math.isfinite(j0):
        return float("nan")
    g1 = gmid_at(J, g, k * j0)
    return k * g1 / base if math.isfinite(g1) else float("nan")


GMID_LS_DEV = {"g5v0d10v5": (1.0, 2.0)}      # pfet_g5v0d10v5 has no model bin below L 0.5 um at W 10 (0.35 fails to load): L 1 and 2 only


def gmid_ls(dev):
    return GMID_LS_DEV.get(dev, GMID_LS)


GMID_OP_V = {"01v8": (0.6, 0.9, 1.3), "n01v8": (0.6, 0.9, 1.3), "g5v0d10v5": (0.9, 1.4, 2.2)}    # Vsg of the .op points (must match the decks)
GMID_OP_TOL = 0.02          # numerical gm vs BSIM gm from .op
GMID_MONO_TOL = 0.01        # strong-inversion side of the gm/Id peak must not rise by more than this (relative) between points
GMID_WBINS = (2.0, 5.0, 20.0)
GMID_TARGETS = (("OTA1 (x2 current, I_tail 35 uA)", 10.05, 35e-6), ("OTA2 x1.5 (I_tail 14.2 uA)", 13.96, 14.2e-6), ("OTA2 x2 (I_tail 18.9 uA)", 10.47, 18.9e-6))


def per_device_current(i_tail):
    """Differential pair: each input device carries I_tail/2 (G-M2; the old table used I_tail and doubled every W/L)."""
    return 0.5 * i_tail


def gmid_mono_violations(J, g, tol=GMID_MONO_TOL):
    """Count points on the strong-inversion side of the peak where gm/Id rises (or Id falls) between neighbours."""
    pk = int(np.argmax(g))
    gg, jj = g[pk:], J[pk:]
    return int(np.sum(gg[1:] > gg[:-1] * (1.0 + tol)) + np.sum(jj[1:] < jj[:-1] * (1.0 - tol)))


def gmid_op_errors(src, dev, corner="tt", T=27, shift=0, op_dev=None):
    """Relative error numerical gm (dId/dVsg of the sweep) vs BSIM gm from .op, per (L, Vsg). shift/op_dev build the broken copies (wrong column / wrong device)."""
    n = len(gmid_ls(dev))
    od = op_dev or dev
    if len(gmid_ls(od)) != n:
        return None, [f"{od} and {dev} have different L sets"]
    op = np.loadtxt(os.path.join(src, f"gmid_{od}_{corner}_op.csv"), ndmin=2)
    if op.shape[1] != 4 * n:
        return None, [f"{od} op file has {op.shape[1]} columns, expected {4 * n}"]
    y = op[:, 1::2]
    gm_b = np.abs(y[:, :n])
    d = np.loadtxt(os.path.join(src, f"gmid_{dev}_{corner}_T{T}.csv"))
    v = d[:, 0]
    errs = []
    for k, vop in enumerate(GMID_OP_V[od]):
        i0 = int(np.argmin(np.abs(v - vop)))
        for col in range(n):
            gn = np.gradient(np.abs(d[:, 1 + (col + shift) % n]), v)[i0]
            errs.append((gmid_ls(dev)[col], float(v[i0]), float(gn), float(gm_b[k, col]), abs(gn / gm_b[k, col] - 1.0)))
    return errs, []


def gmid_min_wl(src, target, id_a, dev=GMID_PRIMARY):
    """Minimum W/L meeting gm/Id >= target at every corner/T for Id = id_a: W/L >= id_a / J_max(target), worst over corners; per L."""
    out = {}
    for col, L in enumerate(GMID_LS):
        worst, nanc = None, []
        for c in GMID_CORNERS:
            for t in GMID_TEMPS:
                J, g = gmid_curve(os.path.join(src, f"gmid_{dev}_{c}_T{t}.csv"), col)
                jm = j_for_gmid(J, g, target)
                if not math.isfinite(jm):
                    nanc.append(f"{c}/{t}")
                    continue
                wl = id_a / jm
                if worst is None or wl > worst[0]:
                    worst = (wl, c, t)
        out[f"{L:g}"] = dict(L=L, wl=(worst[0] if worst and not nanc else float("nan")), wl_ex_unreachable=(worst[0] if worst else float("nan")), corner=(worst[1] if worst else ""), T=(worst[2] if worst else 0),
                             wl_area=((worst[0] * L * L) if worst and not nanc else float("nan")), unreachable=nanc)
    return out


def mode_gmid(args):
    src = args.src or os.path.join(OUT, "gmid")
    rows, bad, wbin = [], [], []
    for dev in GMID_DEVS:
        for c in GMID_CORNERS:
            for t in GMID_TEMPS:
                f = os.path.join(src, f"gmid_{dev}_{c}_T{t}.csv")
                if not os.path.exists(f):
                    bad.append(f"missing {f}")
                    continue
                for col, L in enumerate(gmid_ls(dev)):
                    J, g = gmid_curve(f, col)
                    ut = 8.617333e-5 * (t + 273.15)
                    bound = 1.0 / ut                                    # n = 1 (physical limit gm/Id < 1/(n UT), n >= 1)
                    pkv = float(np.max(g))
                    if not (np.all(np.isfinite(g)) and pkv < bound):
                        bad.append(f"{dev} {c} {t} L{L:g}: peak gm/Id {pkv:.2f} not below 1/UT {bound:.2f}")
                    nv = gmid_mono_violations(J, g)
                    if nv:
                        bad.append(f"{dev} {c} {t} L{L:g}: {nv} monotonicity violation(s) on the strong-inversion side")
                    rows.append(dict(dev=dev, corner=c, T=t, L=L, peak=pkv, bound=bound, n_eff=bound / pkv, mono_violations=nv,
                                     gmid={f"{j:g}": gmid_at(J, g, j) for j in GMID_J},
                                     ratios={f"{o}_{b:g}_x{k:g}": gm_ratio(J, g, b, k) for o, (bs, ks) in GMID_BASES.items() for b in bs for k in ks}))
    worst = {}
    for dev in GMID_DEVS:
        rr = [r for r in rows if r["dev"] == dev]
        worst[dev] = {}
        for key in rr[0]["ratios"] if rr else []:
            vals = [(r["ratios"][key], r["corner"], r["T"], r["L"]) for r in rr]
            fin = [v for v in vals if math.isfinite(v[0])]
            nan = [v for v in vals if not math.isfinite(v[0])]
            w = min(fin) if fin else (float("nan"), "", 0, 0)
            worst[dev][key] = dict(ratio=w[0], corner=w[1], T=w[2], L=w[3], unreachable_corners=len(nan))
    # .op cross-check (3 Vsg points per device and L, tt, 27 C)
    opx = {}
    for dev in GMID_DEVS:
        errs, msgs = gmid_op_errors(src, dev) if os.path.exists(os.path.join(src, f"gmid_{dev}_tt_op.csv")) else (None, [f"missing {dev} op file"])
        bad += msgs
        if errs:
            opx[dev] = errs
            m = max(e[4] for e in errs)
            if not m <= GMID_OP_TOL:
                bad.append(f"{dev}: numerical gm vs BSIM .op gm max error {m:.3%} > {GMID_OP_TOL:.0%}")
    # broken copies: each must be flagged
    selftest = {}
    if "01v8" in opx:
        e1, _ = gmid_op_errors(src, "01v8", shift=1)                  # wrong column
        e2, _ = gmid_op_errors(src, "01v8", op_dev="n01v8")           # nfet BSIM gm against the pfet sweep
        selftest["wrong_column_maxerr"] = max(e[4] for e in e1)
        selftest["nfet_op_vs_pfet_maxerr"] = max(e[4] for e in e2)
        Jb, gb = gmid_curve(os.path.join(src, "gmid_01v8_tt_T27.csv"), 0)
        gbump = gb.copy()
        gbump[int(np.argmax(gb)) + int(np.argmax(gb[int(np.argmax(gb)):] < 0.6 * np.max(gb)))] *= 1.2          # bump (below the peak) on the strong-inversion side
        selftest["bumped_curve_violations"] = gmid_mono_violations(Jb, gbump)
        selftest["clean_curve_violations"] = gmid_mono_violations(Jb, gb)
        for k, okk in (("wrong column", selftest["wrong_column_maxerr"] > GMID_OP_TOL), ("nfet vs pfet", selftest["nfet_op_vs_pfet_maxerr"] > GMID_OP_TOL), ("bumped curve", selftest["bumped_curve_violations"] > 0)):
            if not okk:
                bad.append(f"broken copy '{k}' was NOT rejected")
    # W-bin check (pfet_01v8, tt)
    for t in GMID_TEMPS:
        f = os.path.join(src, f"gmid_wbin_01v8_tt_T{t}.csv")
        if not os.path.exists(f):
            bad.append(f"missing {f}")
            continue
        d = np.loadtxt(f)
        for k, (lj, w) in enumerate((l, w) for l in (1.0, 2.0) for w in GMID_WBINS):
            v, i = d[:, 0], np.abs(d[:, 1 + k])
            gm = np.gradient(i, v)
            ok_ = i > 1e-13
            J, g = i[ok_] / (w / lj), gm[ok_] / i[ok_]
            nv = gmid_mono_violations(J, g)
            if nv or not np.all(np.isfinite(g)):
                bad.append(f"wbin W{w:g} L{lj:g} T{t}: {nv} monotonicity violation(s) or non-finite")
            wbin.append(dict(T=t, L=lj, W=w, peak=float(np.max(g)), gmid={f"{j:g}": gmid_at(J, g, j) for j in GMID_J}))
    # boosted-point minimum W/L (m1)
    minwl = {}
    if all(os.path.exists(os.path.join(src, f"gmid_{GMID_PRIMARY}_{c}_T{t}.csv")) for c in GMID_CORNERS for t in GMID_TEMPS):
        for name, tg, ida in GMID_TARGETS:
            minwl[name] = dict(target=tg, id_uA=per_device_current(ida) * 1e6, per_L=gmid_min_wl(src, tg, per_device_current(ida)))
    out = dict(rows=rows, worst=worst, op_crosscheck={k: [list(e) for e in v] for k, v in opx.items()}, selftest=selftest, wbin=wbin, min_wl=minwl, problems=bad)
    os.makedirs(os.path.dirname(os.path.abspath(GMID_JSON)), exist_ok=True)
    json.dump(out, open(os.path.abspath(GMID_JSON), "w"), indent=1, default=float)
    jdump(out, "gmid_table.json")
    md = ["# gm/Id table (WO-14 item 1, extended in WO-15)", "", "sky130A pfet_01v8 (primary, D40), nfet_01v8 and pfet_g5v0d10v5 (comparison), W 10 um, L 1, 2, 0.35 and 0.5 um, |Vds| 0.5 V, bulk at source, `.option gmin=1e-18`, DC sweep of Vsg. gm = dId/dVsg (numerical).",
          "Columns: gm/Id [1/V] at Id/(W/L) [A]. `peak` = max gm/Id; `1/UT` = n = 1 limit.", ""]
    for dev in GMID_DEVS:
        md += [f"## {'nfet_01v8' if dev == 'n01v8' else 'pfet_' + dev}", "", "| corner | T | L | peak | 1/UT | " + " | ".join(f"{j:g}" for j in GMID_J) + " |", "|---|---|---|---|---|" + "---|" * len(GMID_J)]
        for r in rows:
            if r["dev"] == dev:
                md.append(f"| {r['corner']} | {r['T']} | {r['L']:g} | {r['peak']:.1f} | {r['bound']:.1f} | " + " | ".join(f"{v:.1f}" for v in r["gmid"].values()) + " |")
        md.append("")
    md += ["## gm(xk)/gm(base) at the worst corner (same W/L, Id x k; worst over all L)", "", "| device | key | ratio | corner | T | L | unreachable corners |", "|---|---|---|---|---|---|---|"]
    for dev in GMID_DEVS:
        for key, w in worst[dev].items():
            md.append(f"| {dev} | {key} | {w['ratio']:.3f} | {w['corner']} | {w['T']} | {w['L']:g} | {w['unreachable_corners']} |")
    md += ["", "## Minimum W/L meeting the boosted gm/Id target at every corner and temperature (pfet_01v8)", "",
           "W/L >= Id / J_max(target), worst over ss/tt/ff x -40/27/100/125 C. W.L = (W/L) L^2 [um^2]. `unreachable` = corners whose peak gm/Id is below the target.", ""]
    for name, v in minwl.items():
        md += [f"### {name}: gm/Id >= {v['target']} at {v['id_uA']:g} uA per input device (I_tail/2)", "", "| L [um] | W/L | W.L [um^2] | worst corner | unreachable corners |", "|---|---|---|---|---|"]
        for k, e in v["per_L"].items():
            md.append(f"| {e['L']:g} | {e['wl']:.1f} | {e['wl_area']:.1f} | {e['corner']}/{e['T']} | {', '.join(e['unreachable']) or 'none'} |" if math.isfinite(e["wl"]) else f"| {e['L']:g} | unreachable | - | - | {', '.join(e['unreachable'])} |")
        md.append("")
    md += ["## Numerical gm vs BSIM gm from .op (tt, 27 C; max relative error over the 3 Vsg points x 4 L per device)", ""]
    for dev, errs in opx.items():
        md.append(f"- {dev}: {max(e[4] for e in errs):.3%} (limit {GMID_OP_TOL:.0%}); points: " + ", ".join(f"L{e[0]:g}@{e[1]:.3f} V {e[4]:.2%}" for e in errs))
    md += ["", f"Broken copies (must exceed the limit / flag): {selftest}", "", "## W-bin check (pfet_01v8 tt): gm/Id at J = Id/(W/L)", "", "| T | L | W | peak | " + " | ".join(f"{j:g}" for j in GMID_J) + " |", "|---|---|---|---|" + "---|" * len(GMID_J)]
    for w_ in wbin:
        md.append(f"| {w_['T']} | {w_['L']:g} | {w_['W']:g} | {w_['peak']:.1f} | " + " | ".join(f"{v:.1f}" for v in w_["gmid"].values()) + " |")
    md += ["", f"Problems: {bad if bad else 'none'}"]
    open(os.path.abspath(GMID_JSON).replace(".json", ".md"), "w").write("\n".join(md) + "\n")
    print("\n".join(l for l in md if l.startswith(("###", "| 0.", "| 1", "| 2", "- ", "Broken", "Problems"))))
    print("gmid ACCEPT" if not bad and rows else "gmid REJECT: " + "; ".join(bad[:6]))
    return 0 if (not bad and rows) else 1


def _gm_ratios():
    t = json.load(open(os.path.abspath(GMID_JSON)))["worst"][GMID_PRIMARY]
    return {k: v["ratio"] for k, v in t.items()}


def mode_fast3(args):
    r = _gm_ratios()
    r1 = r["OTA1_10_x2"]
    base = {"fs": 4e6, "bst1": 2.0, "sr": 12.5e6, "sr2": 13.5e6, "gbw": 10e6}
    jobs = []      # (kind, key, extra, n, m)
    for n in R2_NS:
        for g2 in (15e6, 20e6):
            for b2 in (14, 17):
                jobs.append(("V5i_gm", (n, g2, b2), dict(base, bst2=1.5, bstgm1=r1, bstgm2=r[f"OTA2_{b2}_x1.5"], gbw2=g2), n, 21))
        jobs.append(("V5i_x2", (n, 15e6, 14), dict(base, bst2=2.0, bstgm1=r1, bstgm2=r["OTA2_14_x2"], gbw2=15e6, sr2=13.5e6), n, 21))
    jobs.append(("NV_same", (1024, 15e6), dict(base, bst2=1.5, bstgm1=2.0, bstgm2=1.5, gbw2=15e6), 1024, 21))      # gm boost = current boost: s5e 3.7 ppm
    jobs.append(("NV_one", (1024, 15e6), dict(base, bst2=1.5, bstgm1=1.0, bstgm2=1.0, gbw2=15e6), 1024, 21))      # gm ratio 1: must fail
    jobs.append(("V4m", (4096, V4_MARGIN_SR2), {"fs": 2e6, "sr": 12.5e6, "sr2": V4_MARGIN_SR2 * 1e6}, 4096, 11))
    only = getattr(args, "only", None)
    if only:
        jobs = [j for j in jobs if j[0] in only.split(",")]
    print(f"fast3: {len(jobs)} deck jobs; gm ratios (worst corner): OTA1 {r1:.3f}, " + ", ".join(f"{k} {v:.3f}" for k, v in r.items() if k.startswith("OTA2")))

    def one(j):
        kind, key, e, n, m = j
        return dc_metrics(v2_cfg(e, n=n, m=m), f"f3_{kind}_" + "_".join(f"{x:g}" for x in key))
    with ThreadPoolExecutor(2) as ex_:
        out = list(ex_.map(one, jobs))
    rows = []
    for (kind, key, e, n, m), o in zip(jobs, out):
        rows.append(dict(kind=kind, key=list(key), n=n, m=m, ok=bool(o.get("ok")), inl_ep_ppm=o.get("inl_ep_ppm", float("nan")), gain_err=o.get("gain_err", float("nan")),
                         runtime_s=o.get("runtime_s", float("nan")), problems=o.get("problems", []), extra=dict(e)))
    print("\nV5(i) with realistic gm ratios (4 MHz, OTA1 x2 current, OTA2 x1.5 / x2 current):")
    for x in rows:
        if x["kind"].startswith("V5i"):
            n = int(x["n"])
            print(f"  {x['kind']} N{n} base GBW2 {x['key'][1]/1e6:g} MHz, OTA2 base gm/Id {x['key'][2]}: gm ratios {x['extra']['bstgm1']:.3f}/{x['extra']['bstgm2']:.3f}: INL {x['inl_ep_ppm']:.3f} ppm vs {V5_TARGET[n]:g}: {'PASS' if x['inl_ep_ppm'] <= V5_TARGET[n] else 'FAIL'}")
    problems = []
    nv_same = next((x for x in rows if x["kind"] == "NV_same"), None)
    nv_one = next((x for x in rows if x["kind"] == "NV_one"), None)
    if nv_same:
        okv = abs(nv_same["inl_ep_ppm"] - 3.7) <= 0.02 * 3.7 + 0.05      # 3.7 is quoted to 0.1 ppm: 2 % plus its rounding
        print(f"  non-vacuity bstgm = bst: {nv_same['inl_ep_ppm']:.3f} ppm vs s5e 3.7 (2 %): {'ok' if okv else 'MISMATCH'}")
        if not okv:
            problems.append("bstgm=bst row does not reproduce 3.7 ppm")
    if nv_one:
        okv = nv_one["inl_ep_ppm"] > V5_TARGET[1024]
        print(f"  non-vacuity gm ratio 1.0: {nv_one['inl_ep_ppm']:.3f} ppm vs target 5: {'FAILS target as required' if okv else 'PASSES (check is vacuous)'}")
        if not okv:
            problems.append("gm ratio 1.0 row does not fail the N1024 target")
    for x in rows:
        if x["kind"] == "V4m":
            print(f"\nV4 margin: 2 MHz N4096 OTA1 12.5, OTA2 {x['key'][1]:.2f} V/us: INL {x['inl_ep_ppm']:.4f} ppm vs <= {V4_MARGIN_INL_MAX:.3f}: {'PASS' if x['inl_ep_ppm'] <= V4_MARGIN_INL_MAX else 'FAIL'}")
    ok = all(x["ok"] for x in rows) and all(math.isfinite(x["inl_ep_ppm"]) for x in rows) and len(rows) == len(jobs) and not problems
    jdump(dict(rows=rows, ratios=r, problems=problems), "fast3.json")
    print("run-health ACCEPT" if ok else "run-health REJECT: " + "; ".join(problems))
    return 0 if ok else 1


# ---- WO-15 (S5g): boosted operating points (absolute), trend discrimination, fp2 sensitivity
F4_FS = 4e6
F4_PTS = {  # absolute operating points: label -> (GBW1 [Hz], SR1 [V/s], GBW2 [Hz], SR2 [V/s]); bst = bstgm = 1 (absolute)
    "a_D39_hot": (20e6, 25e6, 22.5e6, 20.25e6),
    "b_cold_A": (30e6, 25e6, 34e6, 20.25e6),
    "c_cold_Ap": (30e6, 25e6, 34e6, 27e6),
    "d_hot_Ap": (20e6, 25e6, 22.5e6, 27e6),
}
F4_CONTROL_PPM = 3.686          # s5f NV_same row (bstgm = bst), N 1024
F4_BASE_FP2 = (10e6, 15e6)      # base GBW1, GBW2 [Hz] whose gm sets the held second pole (fp2_fixed rows)
F4_S5F_R1, F4_S5F_R2 = 1.423, 1.283    # s5f worst-corner gm ratios (OTA1 x2 at gm/Id 10, OTA2 x1.5 at gm/Id 14)
F4_S5F_REF = {(15e6, 256): 6.70, (15e6, 1024): 9.95, (20e6, 256): 14.4, (20e6, 1024): 12.5}   # s5f INL [ppm], 21 points, default options
F4_NS = (256, 1024)


def f4_abs(label, **kw):
    g1, s1, g2, s2 = F4_PTS[label]
    return dict(fs=F4_FS, bst1=1.0, bst2=1.0, gbw=g1, sr=s1, gbw2=g2, sr2=s2, **kw)


def f4_s5f(g2, **kw):
    return dict(fs=F4_FS, bst1=2.0, bst2=1.5, bstgm1=F4_S5F_R1, bstgm2=F4_S5F_R2, sr=12.5e6, sr2=13.5e6, gbw=10e6, gbw2=g2, **kw)


def f4_jobs():
    jobs = []      # (group, kind, key, extra, n, m)
    for n in F4_NS:
        for lab in F4_PTS:
            jobs.append(("A", lab, (n,), f4_abs(lab), n, 21))
    for n in F4_NS:
        for g2 in (15e6, 20e6, 25e6):
            jobs.append(("T1", "ideal_ota1", (n, g2), dict(fs=F4_FS, bst1=1.0, bst2=1.0, gbw=1e9, sr=1e9, gbw2=g2, sr2=20.25e6), n, 21))
    tight = dict(P.SPICE_OPTIONS_TIER1, reltol=1e-5, tmax_ns=P.SPICE_OPTIONS_TIER1["tmax_ns"] / 2)
    for n in F4_NS:
        for g2 in (15e6, 20e6):
            jobs.append(("T2", "tight", (n, g2), f4_s5f(g2, options=dict(tight)), n, 21))
            jobs.append(("T3", "fp2x30", (n, g2), f4_s5f(g2, fp2_mult=30.0), n, 21))
            jobs.append(("T4", "m101", (n, g2), f4_s5f(g2), n, 101))
    for n in F4_NS:
        for lab in ("a_D39_hot", "c_cold_Ap"):
            jobs.append(("S", lab + "_fp2base", (n,), f4_abs(lab, fp2_fixed=F4_BASE_FP2), n, 21))
    for n in F4_NS:      # extra (not in the WO): item-1 rows again at reltol 1e-5, maxstep halved, because T2 shows the default options move the s5f rows by several ppm
        for lab in F4_PTS:
            jobs.append(("Z", lab + "_tight", (n,), f4_abs(lab, options=dict(tight)), n, 21))
    return jobs


def f4_signed(u, uh):
    """Signed endpoint-line residual [ppm FSR] vs u and the residual after a third-order fit of that error."""
    u, uh = np.asarray(u, float), np.asarray(uh, float)
    i0, i1 = np.argmin(u), np.argmax(u)
    ep = uh[i0] + (uh[i1] - uh[i0]) / (u[i1] - u[i0]) * (u - u[i0])
    e = (uh - ep) / FS_FULL * 1e6
    res = e - np.polyval(np.polyfit(u, e, 3), u)
    return e, float(np.sqrt(np.mean(res ** 2))), float(np.max(np.abs(res)))


def mode_fast4(args):
    jobs = f4_jobs()
    only = getattr(args, "only", None)
    if only:
        jobs = [j for j in jobs if j[0] in only.split(",")]
    print(f"fast4: {len(jobs)} deck jobs")

    def one(j):
        grp, kind, key, e, n, m = j
        return dc_metrics(v2_cfg(e, n=n, m=m), f"f4_{grp}_{kind}_" + "_".join(f"{x:g}" for x in key))
    with ThreadPoolExecutor(2) as ex_:
        out = list(ex_.map(one, jobs))
    rows = []
    for (grp, kind, key, e, n, m), o in zip(jobs, out):
        r = dict(group=grp, kind=kind, key=list(key), n=n, m=m, ok=bool(o.get("ok")), inl_ep_ppm=o.get("inl_ep_ppm", float("nan")), inl_bf_ppm=o.get("inl_bf_ppm", float("nan")),
                 gain_err=o.get("gain_err", float("nan")), runtime_s=o.get("runtime_s", float("nan")), problems=o.get("problems", []),
                 extra={k: v for k, v in e.items() if k != "options"})
        if grp == "T4" and o.get("u_in"):
            sg, rms, mx = f4_signed(o["u_in"], o["u_hat"])
            r.update(u=o["u_in"], signed_ppm=sg.tolist(), cubic_resid_rms_ppm=rms, cubic_resid_max_ppm=mx)
        rows.append(r)
    problems = []
    tgt = lambda n: V5_TARGET[n]
    print("\nItem 1: absolute boosted points, 4 MHz (GBW/SR are the boosted values; bst = bstgm = 1), INL endpoint ppm")
    for r in rows:
        if r["group"] == "A":
            n = r["n"]
            print(f"  {r['kind']:<10} OTA1 {r['extra']['gbw']/1e6:g} MHz/{r['extra']['sr']/1e6:g}, OTA2 {r['extra']['gbw2']/1e6:g} MHz/{r['extra']['sr2']/1e6:g}: N{n} INL {r['inl_ep_ppm']:.3f} vs {tgt(n):g}: {'PASS' if r['inl_ep_ppm'] <= tgt(n) else 'FAIL'}")
    ctl = next((r for r in rows if r["group"] == "A" and r["kind"] == "a_D39_hot" and r["n"] == 1024), None)
    if ctl:
        okc = abs(ctl["inl_ep_ppm"] - F4_CONTROL_PPM) <= 0.02 * F4_CONTROL_PPM
        print(f"  control (a) N1024 {ctl['inl_ep_ppm']:.3f} vs s5f {F4_CONTROL_PPM} (2 %): {'ok' if okc else 'MISMATCH'}")
        if not okc:
            problems.append("control (a) not within 2 % of 3.686 ppm")
    for r in rows:
        if r["group"] == "Z":
            n = r["n"]
            base = next((x for x in rows if x["group"] == "A" and x["kind"] + "_tight" == r["kind"] and x["n"] == n), None)
            print(f"  [tight options] {r['kind']:<16} N{n} INL {r['inl_ep_ppm']:.3f} vs {tgt(n):g}: {'PASS' if r['inl_ep_ppm'] <= tgt(n) else 'FAIL'}" + (f" (default options {base['inl_ep_ppm']:.3f})" if base else ""))
    print("\nItem 2: trend discrimination (4 MHz)")
    for r in rows:
        if r["group"] in ("T1", "T2", "T3"):
            n, g2 = r["key"]
            ref = F4_S5F_REF.get((g2, int(n)))
            print(f"  {r['group']} {r['kind']:<10} N{int(n)} GBW2 {g2/1e6:g} MHz: INL {r['inl_ep_ppm']:.3f} ppm" + (f" (s5f default-options 21-pt: {ref})" if ref and r['group'] != 'T1' else ""))
    for r in rows:
        if r["group"] == "T4":
            n, g2 = r["key"]
            print(f"  T4 m101 N{int(n)} GBW2 {g2/1e6:g} MHz: INL ep {r['inl_ep_ppm']:.3f} ppm; signed min/max {min(r['signed_ppm']):+.3f}/{max(r['signed_ppm']):+.3f}; cubic-fit residual rms {r['cubic_resid_rms_ppm']:.4f}, max {r['cubic_resid_max_ppm']:.4f} ppm")
    print("\nItem 3: second pole held at the base gm (GBW 10 / 15 MHz x fp2_mult), INL ppm vs second pole tracking")
    for r in rows:
        if r["group"] == "S":
            n = r["n"]
            base = next((x for x in rows if x["group"] == "A" and x["kind"] == r["kind"].replace("_fp2base", "") and x["n"] == n), None)
            print(f"  {r['kind']} N{n}: {r['inl_ep_ppm']:.3f}" + (f" vs tracking {base['inl_ep_ppm']:.3f}" if base else ""))
    ok = all(r["ok"] for r in rows) and all(math.isfinite(r["inl_ep_ppm"]) for r in rows) and len(rows) == len(jobs) and not problems
    jdump(dict(rows=rows, problems=problems), "fast4" + ("_" + only.replace(",", "") if only else "") + ".json")
    print("run-health ACCEPT" if ok else "run-health REJECT: " + "; ".join(problems))
    return 0 if ok else 1


def converge_verdict(inl_o1, inl_o2, gate):
    """D43c acceptance rule. Converged iff |O2-O1| <= max(10 % INL(O2), 0.1 (gate - INL(O2))); verdict on INL(O2) (1 + |d|/INL(O2)) <= gate.
    Returns (converged, delta, inl_verdict, passes). NaN in -> not converged, not passing."""
    if not all(math.isfinite(x) for x in (inl_o1, inl_o2, gate)):
        return False, float("nan"), float("nan"), False
    d = abs(inl_o2 - inl_o1)
    allow = max(0.1 * inl_o2, 0.1 * (gate - inl_o2))
    conv = d <= allow
    v = inl_o2 * (1.0 + d / inl_o2) if inl_o2 > 0 else inl_o2 + d
    return bool(conv), d, v, bool(conv and v <= gate)


def main():
    ap = argparse.ArgumentParser()
    for m in ("null", "options", "dc", "sweep", "nonvac", "xcheck", "av", "knees2", "cm", "offsets", "rsrc", "nonvac2",
              "knees3", "cm2", "drift", "rsrc2", "nonvac3", "nonvac4", "knees4", "fast2", "nonvac5", "fast3", "gmid", "fast4"):
        ap.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--only", default=None, help="fast2: comma list of V4,V5i,V5ii")
    ap.add_argument("--src", default=None, help="gmid: directory with the gmid_*.csv files")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--m", type=int, default=None, help="number of DC points")
    ap.add_argument("--out", default=None)
    ap.add_argument("--prev", default=None, help="knees4: knees3.json whose 2 MHz rows are reused")
    ap.add_argument("--opt", action="append", default=[], help="O0|O1|O2 option ladder (D43c) or override a SPICE option, e.g. --opt method=gear")
    ap.add_argument("--method", default=None, choices=("trap", "gear"))
    ap.add_argument("--reltol-only", default=None, choices=("O0", "O1", "O2"), help="ladder characterisation: take only reltol (and chgtol) from this level")
    ap.add_argument("--tmax-only", default=None, choices=("O0", "O1", "O2"), help="ladder characterisation: take only tmax (with the tau floor) from this level")
    a = ap.parse_args()
    for kv in a.opt:
        if kv in ("O0", "O1", "O2"):
            P.SPICE_OPTIONS_TIER1.update(P.option_ladder(kv))
            continue
        k, v = kv.split("=")
        P.SPICE_OPTIONS_TIER1[k] = v if k == "method" else float(v)
    if a.reltol_only:
        lo = P.option_ladder(a.reltol_only)
        P.SPICE_OPTIONS_TIER1.update(reltol=lo["reltol"], chgtol=lo["chgtol"], trtol=lo["trtol"])
    if a.tmax_only:
        lo = P.option_ladder(a.tmax_only)
        P.SPICE_OPTIONS_TIER1.update(tmax_ns=lo["tmax_ns"], tau_floor_div=lo.get("tau_floor_div", 0))
    if a.method:
        P.SPICE_OPTIONS_TIER1["method"] = a.method
    global OUT
    if a.out:
        OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    if a.m is None:
        a.m = {"null": 5, "options": 5, "dc": 11, "nonvac": 5}.get(next((m for m in ("null", "options", "dc", "nonvac") if getattr(a, m)), ""), 5)
    if a.null:
        return mode_null(a)
    if a.options:
        return mode_options(a)
    if a.dc:
        return mode_dc(a)
    if a.sweep:
        return mode_sweep(a)
    if a.nonvac:
        return mode_nonvac(a)
    for nm, fn in (("xcheck", mode_xcheck), ("av", mode_av), ("knees2", mode_knees2), ("cm", mode_cm), ("offsets", mode_offsets),
                   ("rsrc", mode_rsrc), ("nonvac2", mode_nonvac2), ("knees3", mode_knees3), ("cm2", mode_cm2),
                   ("drift", mode_drift), ("rsrc2", mode_rsrc2), ("nonvac3", mode_nonvac3), ("nonvac4", mode_nonvac4), ("knees4", mode_knees4), ("fast2", mode_fast2), ("nonvac5", mode_nonvac5), ("fast3", mode_fast3), ("gmid", mode_gmid), ("fast4", mode_fast4)):
        if getattr(a, nm):
            return fn(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
