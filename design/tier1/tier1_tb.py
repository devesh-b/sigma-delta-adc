#!/usr/bin/env python3
"""Tier-1 testbench / checker (WO-07 / S5). Runs ngspice on decks from gen_tier1.py.

Expected values come from theory (WORKFLOW 11 item 8): the ideal quantizer DC transfer u_hat = u_in,
using the residue reconstruction (SPEC 3.7)
    u = (sum S + (k/c1) S + x2[N]/(c1 c2)) / (N(N-1)/2),   x2[N] read from the simulation.
No import of model/iadc.py.

Modes: --null --options --dc --sweep --nonvac (WO-07) and --xcheck --av --knees2 --cm --offsets --rsrc --nonvac2 (WO-08).
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

OUT = os.environ.get("TIER1_OUT", "/home/mempool/regr/tt/WO-08")
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
    uh = ub + np.asarray(st["x2_final"]) / (p.c1 * p.c2 * n * (n - 1) / 2.0)
    return uh, p


def jdump(obj, name):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=float)


# ---- item 1: cross-check table + noise transfer
IDEAL_OTA = dict(gbw=1e8, sr=1e9, vcl=1e3, ron=1.0)
# reviewer's probe numbers (REVIEW-S5): deck gain, deck INL ppm, model gain, model INL ppm
REV = {"A60_base": (-5.59e-4, 3.99, -5.47e-4, 3.09), "A60_k025": (-2.93e-4, 6.98, -2.88e-4, 5.90),
       "A60_c1_025": (-5.51e-4, 10.05, -5.43e-4, 7.43), "A80_base": (None, 0.29, None, 0.295)}


def mode_xcheck(args):
    U = u_points(5, 0.9)
    cases = [("A60_base", dict(a0_db=60.0), {}), ("A60_k025", dict(a0_db=60.0, ck=0.125e-12), dict(k=0.25)),
             ("A60_c1_025", dict(a0_db=60.0, cint1=2e-12), dict(c1=0.25)), ("A80_base", dict(a0_db=80.0), {})]
    rows, ok = [], True
    for name, dk, mk in cases:
        cfg = dict(IDEAL_OTA, n=256, u_list=U)
        cfg.update(dk)
        r = run_deck(cfg, "xc_" + name)
        c1, k = mk.get("c1", P.C1), mk.get("k", P.K)
        uh = np.array([reconstruct(cv["y"], cv["x2n"], 256, c1, P.C2, k) for cv in r["convs"]])
        g = inl_gain(np.array(U), uh)
        um, p = model_eval(U, 256, a0_db=dk["a0_db"], **mk)
        gm_ = inl_gain(np.array(U), um)
        rv = REV[name]
        chk = [rel_sym(g["inl_ep_ppm"], gm_["inl_ep_ppm"]) <= 0.35, rel_sym(g["inl_ep_ppm"], rv[1]) <= 0.35]
        if rv[0] is not None:
            chk += [rel_sym(g["gain_err"], gm_["gain_err"]) <= 0.05, rel_sym(g["gain_err"], rv[0]) <= 0.05]
        row = dict(case=name, ok=bool(r["ok"] and all(chk)), deck_gain=g["gain_err"], model_gain=gm_["gain_err"], rev_deck_gain=rv[0],
                   deck_inl=g["inl_ep_ppm"], model_inl=gm_["inl_ep_ppm"], rev_deck_inl=rv[1], rev_model_inl=rv[3], checks=chk, problems=r["problems"])
        ok &= row["ok"]
        rows.append(row)
        print(f"xcheck {name}: deck gain {g['gain_err']:+.3e} INL {g['inl_ep_ppm']:.3f} | model gain {gm_['gain_err']:+.3e} INL {gm_['inl_ep_ppm']:.3f} "
              f"| reviewer deck {rv[0]} / {rv[1]} model {rv[2]} / {rv[3]} -> {'ok' if row['ok'] else 'FAIL'} {chk}")
    # noise transfer: trnoise at OTA1 input, per-cycle white, ~30 conversions
    nconv, sig = 32, 2e-3
    cfg = dict(IDEAL_OTA, a0_db=120.0, n=256, u_list=(0.0,) * nconv, noise1=sig)
    r = run_deck(cfg, "xc_noise")
    E = np.asarray(r["meta"]["noise_e"])
    uh = u_hat_of(r)
    import iadc as M
    _, p = model_eval(np.zeros(nconv), 256, a0_db=float("inf"))
    ub, st = M.convert(p, np.zeros(nconv), ota_noise=E, return_state=True)
    um = ub + np.asarray(st["x2_final"]) / (p.c1 * p.c2 * 256 * 255 / 2.0)
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
    jdump(dict(rows=rows, knees=knees, flags=flags), "knees2.json")
    print("ACCEPT" if ok else "REJECT")
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


def main():
    ap = argparse.ArgumentParser()
    for m in ("null", "options", "dc", "sweep", "nonvac", "xcheck", "av", "knees2", "cm", "offsets", "rsrc", "nonvac2"):
        ap.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--m", type=int, default=None, help="number of DC points")
    ap.add_argument("--out", default=None)
    ap.add_argument("--opt", action="append", default=[], help="override a SPICE option, e.g. --opt method=gear")
    a = ap.parse_args()
    for kv in a.opt:
        k, v = kv.split("=")
        P.SPICE_OPTIONS_TIER1[k] = v if k == "method" else float(v)
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
                   ("rsrc", mode_rsrc), ("nonvac2", mode_nonvac2)):
        if getattr(a, nm):
            return fn(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
