#!/usr/bin/env python3
"""Tier-1 testbench / checker (WO-07 / S5). Runs ngspice on decks from gen_tier1.py.

Expected values come from theory (WORKFLOW 11 item 8): the ideal quantizer DC transfer u_hat = u_in,
using the residue reconstruction (SPEC 3.7)
    u = (sum S + (k/c1) S + x2[N]/(c1 c2)) / (N(N-1)/2),   x2[N] read from the simulation.
No import of model/iadc.py.

Modes: --null  --options  --dc  --sweep  --nonvac  (each prints ACCEPT/REJECT, exits nonzero on REJECT).
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

OUT = os.environ.get("TIER1_OUT", "/home/mempool/regr/tt/WO-07")
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
        convs.append(dict(y=yb, x2n=float(x2)))
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
    r = {k: v for k, v in res.items() if k not in ("convs",)}
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
        opts = dict(P.SPICE_OPTIONS)
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


def main():
    ap = argparse.ArgumentParser()
    for m in ("null", "options", "dc", "sweep", "nonvac"):
        ap.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--m", type=int, default=None, help="number of DC points")
    ap.add_argument("--out", default=None)
    ap.add_argument("--opt", action="append", default=[], help="override a SPICE option, e.g. --opt method=gear")
    a = ap.parse_args()
    for kv in a.opt:
        k, v = kv.split("=")
        P.SPICE_OPTIONS[k] = v if k == "method" else float(v)
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
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
