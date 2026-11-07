#!/usr/bin/env python3
"""S2 chopping study (WO-03): OTA chop vs system chop in incremental mode.

  python3 model/studies/s2_chop.py --out /home/mempool/regr/tt/WO-03 [--m-out 32] [--offset-pairs 8192]
  python3 model/studies/s2_chop.py --nonvac     # broken-copy checks, must print REJECT

Offset: deterministic (flicker off, kT/C on as dither) over M random DC inputs
in +/-0.5 FS, measured DIFFERENTIALLY vs the same config with vos=vres=0 and
identical random numbers, so quantisation/gain error cancels. For sys modes
each input is converted with both polarities and averaged.
Noise: iadc.measure_noise with flicker + kT/C on (std removes any DC offset).
Expected offsets come from s2_theory.py (independent of iadc.py).
"""
import argparse, itertools, json, math, os, subprocess, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import iadc                                  # noqa: E402
import s2_theory as th                       # noqa: E402

MODES = {"none": (False, False), "ota": (True, False), "sys": (False, True), "ota+sys": (True, True)}
VOS = (1e-3, 3e-3, 9e-3)
NS = (256, 1024, 4096)
VRES = (0.0, 5e-6, 20e-6)
ORDERS = (1, 2)
LFS = (1.0, 5.3)
RATES = (240.0, 15.0)
FS, CS = 2e6, 1e-12
OFF_LIM_UV = 5.0


def base(order, N, lf, **kw):
    return iadc.Params(order=order, N=N, fs=FS, cs=CS, ktc_on=True, lf_gain=lf, **kw)


def offset_est(order, N, mode, vos, vres, lf, M, seed=7, break_sys=False):
    """returns (offset_uV, sem_uV) of input-referred mean offset, differential vs zero-offset run."""
    chop, sc = MODES[mode]
    if break_sys:
        sc = False
    rng0 = np.random.default_rng(1234)
    B = 2 * M
    n0 = M if sc else B                      # stratified inputs: kills quantisation-sawtooth boundary terms
    u0 = -0.5 + (np.arange(n0) + rng0.uniform(0, 1, n0)) / n0
    u = np.tile(u0, 2) if sc else u0
    sign = np.concatenate([np.ones(M), -np.ones(M)]) if sc else None
    outs = []
    for v, r in ((vos, vres), (0.0, 0.0)):
        p = base(order, N, lf, chop=chop, sys_chop=sc, vos=v, vres=r)
        on = np.broadcast_to(np.float64(v), (B, N)) if v else None
        uh = iadc.convert(p, u, rng=np.random.default_rng(seed), ota_noise=on, sys_sign=sign)
        outs.append((uh[:M] + uh[M:]) / 2 if sc else uh)
    d = (outs[0] - outs[1]) * 2.048 * 1e6
    return float(np.mean(d)), float(np.std(d) / math.sqrt(len(d)))


def noise_uV(order, N, mode, lf, rate, m_out, vos=9e-3, vres=5e-6):
    chop, sc = MODES[mode]
    k = max(2, 2 * round(FS / (N * rate) / 2))
    p = base(order, N, lf, chop=chop, sys_chop=sc, vos=vos, vres=vres, flicker_on=True)
    r = iadc.measure_noise(p, k, m_out=m_out, u_dc=0.1, seed=3)
    return r["rms_v"] * 1e6, r["rate"]


def verdict(vals, lim=OFF_LIM_UV):
    return "ACCEPT" if (vals and all(np.isfinite(v) and abs(v) <= lim for v in vals)) else "REJECT"


def theory_ok(meas, sem, pred):
    return (np.isfinite(meas) and abs(meas - pred) <= max(0.2 * abs(pred), 4 * sem, 0.5))


def nonvac(M):
    print("NON-VACUITY (broken copies; each must print REJECT)")
    vals = [offset_est(2, N, "sys", 3e-3, 0.0, 1.0, M, break_sys=True)[0] for N in NS]
    v1 = verdict(vals)
    print(f"  sys-mode with sys_chop DISABLED, Vos=3 mV, offsets uV {['%.1f' % x for x in vals]} -> {v1}")
    vn = [offset_est(2, N, "none", 3e-3, 0.0, 1.0, M)[0] for N in NS]
    print(f"  none mode, Vos=3 mV, offsets uV {['%.1f' % x for x in vn]} -> {verdict(vn)}")
    m, s = offset_est(2, 1024, "ota", 9e-3, 0.0, 1.0, M)
    wrong = th.predict(1, 1024, "ota", 9e-3, 0.0, 1.0) * 1e6         # order-1 (equal-weight) theory
    t1 = "ACCEPT" if theory_ok(m, s, wrong) else "REJECT"
    print(f"  model-vs-theory using the WRONG (equal-weight) kernel: meas {m:.2f} uV vs {wrong:.2f} -> {t1}")
    allrej = v1 == "REJECT" and verdict(vn) == "REJECT" and t1 == "REJECT"
    print("NONVAC-CONFIRMED (all checks reject broken copies)" if allrej else "NONVAC-FAILED (a check is vacuous)")
    print("REJECT" if allrej else "ACCEPT")          # REJECT = criterion rejects the broken copy
    return 1 if allrej else 2


def fmt(x):
    return "nan" if not np.isfinite(x) else f"{x:.2f}"


def collect_verdicts(rows):
    v = {}
    for mode in MODES:
        for order in ORDERS:
            sel = [r["off_uV"] for r in rows if r["mode"] == mode and r["order"] == order
                   and r["vos_mV"] == 9 and r["vres_uV"] <= 5]
            worst = max(abs(x) for x in sel)
            v[f"{mode}|o{order}"] = dict(verdict=verdict(sel), worst_uV=worst)
    return v


def render(res, out):
    rows, noise, mv = res["offset"], res["noise"], res["theory_vs_model_ota"]
    verd = res["verdict"]
    mv_bad = [r for r in mv if not r["ok"]]
    L = ["# S2 chopping study (WO-03)", "",
         f"fs = 2 MHz, Cs = 1 pF, kT/C on, flicker on (noise runs). iadc.py blob hash `{res['iadc_blob_hash']}`. "
         f"Offset: {2*res['offset_pairs']} stratified-DC conversions/point, differential vs a zero-offset run with "
         f"identical random numbers (flicker off: it is zero-mean); noise: m_out = {res['m_out']}, flicker + kT/C on.", "",
         "## Verdicts: |offset| <= 5 uV at Vos = 9 mV, vres <= 5 uV, all N, lf 1 and 5.3", "",
         "Targets apply to sys and ota+sys at order 2 (the v1 mode, gates the exit code). Order 1 is informational: its differential estimate is quantisation-limited (see notes).", "",
         "| mode | order 2 | worst uV | order 1 | worst uV |", "|---|---|---|---|---|"]
    for mode in MODES:
        a, b = verd[f"{mode}|o2"], verd[f"{mode}|o1"]
        tag = "" if mode in ("sys", "ota+sys") else " (no target)"
        L.append(f"| {mode} | {a['verdict']}{tag} | {fmt(a['worst_uV'])} | {b['verdict']}{tag} | {fmt(b['worst_uV'])} |")
    for order in (2, 1):
        L += ["", f"## Mean offset, order {order}, Vos = 9 mV, vres = 5 uV [uV], model / theory", "",
              "| mode | lf | N=256 | N=1024 | N=4096 |", "|---|---|---|---|---|"]
        for mode in MODES:
            for lf in LFS:
                c = []
                for N in NS:
                    r = [x for x in rows if (x["order"], x["N"], x["mode"], x["lf"], x["vos_mV"], x["vres_uV"]) == (order, N, mode, lf, 9, 5)][0]
                    c.append(f"{fmt(r['off_uV'])} / {fmt(r['theory_uV'])} (sem {fmt(r['sem_uV'])})")
                L.append(f"| {mode} | {lf} | " + " | ".join(c) + " |")
    for order in (2, 1):
        sub = [r for r in mv if r["order"] == order]
        bad = [r for r in sub if not r["ok"]]
        big = [r for r in sub if abs(r["theory_uV"]) >= 10]
        wr = max((abs(r["off_uV"] - r["theory_uV"]) / abs(r["theory_uV"]) for r in big), default=float("nan"))
        L += ["", f"## Model vs theory, OTA chop only, order {order}", "",
              f"Theory (s2_theory.py): offset = lf*(Vos*r(N) + vres), r = 1/(N-1) for order 2, 0 for order 1 (N even). "
              f"{len(sub)-len(bad)} of {len(sub)} grid points agree (within 20 %, or 4 sem, or 0.5 uV). "
              f"Worst relative deviation where |theory| >= 10 uV: {100*wr:.1f} %."]
        for r in bad[:8]:
            L.append(f"- DISAGREE N {r['N']} lf {r['lf']} Vos {r['vos_mV']} mV vres {r['vres_uV']} uV: "
                     f"model {fmt(r['off_uV'])} theory {fmt(r['theory_uV'])} (sem {fmt(r['sem_uV'])})")
    L += ["", "## rms noise [uV], order 2 (Vos 9 mV, vres 5 uV; rms excludes DC offset)", "",
          "N = 256 rows are quantisation-limited (order 2, ~12 b): values there are not OTA-noise. "
          "Order-1 noise is not tabulated: its quantisation error (about 1/N of FS) is deterministic at a fixed DC input, "
          "so the sample rms is 0 or dominated by code flips (raw values are in the json).", "",
          "| mode | lf | N | 240 SPS (actual) | 15 SPS (actual) |", "|---|---|---|---|---|"]
    for mode in MODES:
        for lf in LFS:
            for N in NS:
                q = {x["rate_nom"]: x for x in noise if (x["order"], x["N"], x["mode"], x["lf"]) == (2, N, mode, lf)}
                L.append(f"| {mode} | {lf} | {N}{' (quant-limited)' if N == 256 else ''} | {fmt(q[240.0]['rms_uV'])} ({q[240.0]['rate']:.0f}) | "
                         f"{fmt(q[15.0]['rms_uV'])} ({q[15.0]['rate']:.1f}) |")
    L += [""] + NOTES
    with open(os.path.join(out, "s2_chop.md"), "w") as f:
        f.write("\n".join(L) + "\n")


# ---------------------------------------------------------------- v2 (WO-04)
V2_NS = (256, 1024, 4096)
V2_C1 = ((0.25, 1.0), (0.125, 0.5))          # (c1, k)
RATES4 = (240.0, 60.0, 15.0, 3.75)


def e2_offset_est(N, c1, k, kind, sc, e2, M, seed=7):
    """mean input-referred error [uV] and sem of constant e2 [V] injected via `kind` (vos2|x1_offset),
    differential vs e2=0 with identical random numbers; sc: pair-average with swapped input polarity."""
    rng0 = np.random.default_rng(1234)
    u0 = -0.5 + (np.arange(M) + rng0.uniform(0, 1, M)) / M
    u = np.tile(u0, 2) if sc else u0
    sign = np.concatenate([np.ones(M), -np.ones(M)]) if sc else None
    outs = []
    for v in (e2, 0.0):
        p = iadc.Params(order=2, N=N, fs=FS, cs=CS, ktc_on=True, c1=c1, c2=0.5, k=k, sys_chop=sc, **{kind: v})
        uh = iadc.convert(p, u, rng=np.random.default_rng(seed), sys_sign=sign)
        outs.append((uh[:M] + uh[M:]) / 2 if sc else uh)
    d = (outs[0] - outs[1]) * 2.048 * 1e6
    return float(np.mean(d)), float(np.std(d) / math.sqrt(len(d)))


def noise_d17(N, mode, lf, cs, rate, m_out):
    chop, sc = MODES[mode]
    k = max(2, 2 * round(FS / (N * rate) / 2))
    p = iadc.Params(order=2, N=N, fs=FS, vref=2.048, c1=0.125, c2=0.5, k=0.5, cs=cs, a0_db=80, a0_drop=0.9,
                    vlin_diff=2.0, ktc_on=True, flicker_on=True, vos=9e-3, chop=chop, vres=5e-6, sys_chop=sc,
                    ref_mode="shared", tau_in=20e-9, tau_ref=10e-9, lf_gain=lf,
                    white_ng_ref=iadc.Params().noise_gain)
    r = iadc.measure_noise(p, k, m_out=m_out, u_dc=0.1, seed=3)
    return r["rms_v"] * 1e6, r["rate"]


def main_v2(a):
    out = a.out or os.path.join(HERE, "..", "out", "s2v2")
    os.makedirs(out, exist_ok=True)
    M = a.offset_pairs
    t0 = time.time()
    lines, fails = [], []

    def rec(ok, text):
        lines.append(f"{'PASS' if ok else 'FAIL'} {text}")
        if not ok:
            fails.append(text)

    # 1. OTA2 offset / x1 output offset
    E2 = 9e-3
    e2rows = []
    for (c1, k), N, kind in itertools.product(V2_C1, V2_NS, ("vos2", "x1_offset")):
        mm, ss = e2_offset_est(N, c1, k, kind, False, E2, M)
        ms, sss = e2_offset_est(N, c1, k, kind, True, E2, M)
        pred = th.e2_error(N, c1, E2) * 1e6
        okm = np.isfinite(mm) and abs(mm - pred) <= max(0.10 * abs(pred), 4 * ss)
        oks = np.isfinite(ms) and abs(ms) <= max(0.5, 4 * sss)
        wrong = abs(-mm - pred) > max(0.10 * abs(pred), 4 * ss)       # non-vacuity: flipped sign rejects
        e2rows.append(dict(c1=c1, k=k, N=N, kind=kind, model_uV=mm, sem_uV=ss, theory_uV=pred, sys_uV=ms, sys_sem_uV=sss))
        rec(okm, f"e2 model-vs-theory {kind} c1 {c1} N {N}: model {mm:.2f} (sem {ss:.2f}) vs theory {pred:.2f} uV (10 %)")
        rec(oks, f"e2 sys-chop cancels {kind} c1 {c1} N {N}: pair-averaged {ms:.2f} uV (sem {sss:.2f}), single {mm:.1f}")
        rec(wrong, f"e2 non-vacuity (sign-flipped model rejected) {kind} c1 {c1} N {N}")
    print(f"e2 done t={time.time()-t0:.0f}s", flush=True)

    # 2. order-1 residue lf*Vos/N (N even), 0 (N odd)
    o1rows = []
    VOS = 9e-3
    for N in (256, 512, 255, 511):
        mm, ss = offset_est(1, N, "ota", VOS, 0.0, 1.0, a.o1_pairs)
        pred = th.order1_residue(N, VOS, 1.0) * 1e6
        old = th.predict(1, N, "ota", VOS, 0.0, 1.0) * 1e6 if N % 2 == 0 else float("nan")
        ok = np.isfinite(mm) and abs(mm - pred) <= max(0.20 * abs(pred), 4 * ss)
        o1rows.append(dict(N=N, model_uV=mm, sem_uV=ss, theory_uV=pred, old_kernel_uV=old))
        rec(ok, f"order-1 OTA-chop residue N {N}: model {mm:.2f} (sem {ss:.2f}) vs theory lf*Vos/N = {pred:.2f} uV")
    for N in (256, 512):
        mm, ss = offset_est(1, N, "sys", VOS, 0.0, 1.0, a.o1_pairs // 2)
        rec(abs(mm) <= max(1.0, 4 * ss), f"order-1 sys-chop cancels residue N {N}: {mm:.2f} uV (sem {ss:.2f})")
    old512 = [r for r in o1rows if r["N"] == 512][0]
    rec(abs(old512["model_uV"] - old512["old_kernel_uV"]) > 4 * old512["sem_uV"],
        f"order-1 non-vacuity: old kernel (0) rejected at N 512 (model {old512['model_uV']:.2f} vs {old512['old_kernel_uV']:.2f})")
    print(f"order-1 done t={time.time()-t0:.0f}s", flush=True)

    # 6. noise at the D17 point
    noise = []
    for N, mode, lf, cs, rate in itertools.product(a.v2_ns, ("ota+sys", "sys"), (1.0, 9.3), (1e-12, 0.5e-12), RATES4):
        r, act = noise_d17(N, mode, lf, cs, rate, a.m_out)
        noise.append(dict(N=N, mode=mode, lf=lf, cs_pF=cs * 1e12, rate_nom=rate, rate=act, rms_uV=r))
        print(f"noise N={N} {mode} lf={lf} cs={cs*1e12} {rate}: {r:.2f} uV t={time.time()-t0:.0f}s", flush=True)
    rec(all(np.isfinite(r["rms_uV"]) for r in noise), "noise: all measurements finite")
    for r in noise:
        if r["rate_nom"] == 15.0 and r["lf"] == 9.3 and r["N"] == max(a.v2_ns):
            rec(r["rms_uV"] <= 50.0, f"noise <= 50 uV @15 SPS, lf 9.3, N {r['N']}, {r['mode']}, Cs {r['cs_pF']} pF: {r['rms_uV']:.2f} uV")

    L = ["# S2 v2: OTA2 offset, order-1 residue, noise at the D17 point (WO-04)", "",
         f"Command: `python3 model/studies/s2_chop.py --v2 --out {out} --offset-pairs {M} --o1-pairs {a.o1_pairs} --m-out {a.m_out}`", "",
         "```"] + lines + ["```", "",
         "## OTA2 offset / x1 output offset, 9 mV, no sys chop [uV], model (sem) / theory 2*e2/(c1(N-1))", "",
         "| c1 | injected at | N=256 | N=1024 | N=4096 |", "|---|---|---|---|---|"]
    for (c1, k) in V2_C1:
        for kind in ("vos2", "x1_offset"):
            c = []
            for N in V2_NS:
                r = [x for x in e2rows if (x["c1"], x["N"], x["kind"]) == (c1, N, kind)][0]
                c.append(f"{r['model_uV']:.2f} ({r['sem_uV']:.2f}) / {r['theory_uV']:.2f}")
            L.append(f"| {c1} | {kind} | " + " | ".join(c) + " |")
    L += ["", "## Order-1 OTA-chop-only residue, Vos 9 mV, lf 1 [uV]", "",
          "| N | model (sem) | theory lf*Vos/N (even) / 0 (odd) |", "|---|---|---|"]
    for r in o1rows:
        L.append(f"| {r['N']} | {r['model_uV']:.2f} ({r['sem_uV']:.2f}) | {r['theory_uV']:.2f} |")
    L += ["", "## rms noise at the D17 point [uV]", "",
          "B (VREF 2.048, c1 .125, c2 .5, k .5), shared Cs, A0 80 dB, a0_drop 0.9 at vlin 2.0 V, flicker + kT/C on, Vos 9 mV, vres 5 uV. "
          f"m_out {a.m_out} (about 12 % statistical error). Actual rates in brackets.", "",
          "| N | mode | lf | Cs pF | " + " | ".join(f"{r:g} SPS" for r in RATES4) + " |", "|---|---|---|---|" + "---|" * len(RATES4)]
    for N, mode, lf, cs in itertools.product(a.v2_ns, ("ota+sys", "sys"), (1.0, 9.3), (1.0, 0.5)):
        c = []
        for rt in RATES4:
            r = [x for x in noise if (x["N"], x["mode"], x["lf"], x["cs_pF"], x["rate_nom"]) == (N, mode, lf, cs, rt)][0]
            c.append(f"{r['rms_uV']:.2f} ({r['rate']:.1f})")
        L.append(f"| {N} | {mode} | {lf:g} | {cs:g} | " + " | ".join(c) + " |")
    L += [""]
    open(os.path.join(out, "s2_chop_v2.md"), "w").write("\n".join(L) + "\n")
    json.dump(dict(e2=e2rows, order1=o1rows, noise=noise, lines=lines, offset_pairs=M, o1_pairs=a.o1_pairs,
                   m_out=a.m_out, runtime_s=time.time() - t0), open(os.path.join(out, "s2_chop_v2.json"), "w"), indent=1)
    print("\n".join(lines))
    print("REJECT" if fails else "ACCEPT")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--nonvac", action="store_true")
    ap.add_argument("--render-only", action="store_true", help="regenerate md from existing json in --out")
    ap.add_argument("--m-out", type=int, default=32)
    ap.add_argument("--offset-pairs", type=int, default=8192)
    ap.add_argument("--v2", action="store_true", help="WO-04: OTA2/x1 offset, order-1 residue, D17-point noise")
    ap.add_argument("--o1-pairs", type=int, default=65536)
    ap.add_argument("--v2-ns", type=int, nargs="+", default=[1024, 4096])
    a = ap.parse_args()
    if a.v2:
        sys.exit(main_v2(a))
    if a.nonvac:
        sys.exit(nonvac(a.offset_pairs))
    out = a.out or os.path.join(HERE, "..", "out", "s2")
    os.makedirs(out, exist_ok=True)
    jpath = os.path.join(out, "s2_chop.json")
    if a.render_only:
        res = json.load(open(jpath))
    else:
        t0 = time.time()
        rows, noise = [], []
        for order, N, mode, lf in itertools.product(ORDERS, NS, MODES, LFS):
            for vos, vres in itertools.product(VOS, VRES):
                m, s = offset_est(order, N, mode, vos, vres, lf, a.offset_pairs)
                rows.append(dict(order=order, N=N, mode=mode, lf=lf, vos_mV=vos * 1e3, vres_uV=vres * 1e6,
                                 off_uV=m, sem_uV=s, theory_uV=th.predict(order, N, mode, vos, vres, lf) * 1e6))
            print(f"offset done order={order} N={N} {mode} lf={lf} t={time.time()-t0:.0f}s", flush=True)
        for order, N, mode, lf, rate in itertools.product(ORDERS, NS, MODES, LFS, RATES):
            r, act = noise_uV(order, N, mode, lf, rate, a.m_out)
            noise.append(dict(order=order, N=N, mode=mode, lf=lf, rate_nom=rate, rate=act, rms_uV=r))
        print(f"noise done t={time.time()-t0:.0f}s", flush=True)
        mv = [dict(r, ok=bool(theory_ok(r["off_uV"], r["sem_uV"], r["theory_uV"]))) for r in rows if r["mode"] == "ota"]
        githash = subprocess.run(["git", "hash-object", os.path.join(HERE, "..", "iadc.py")],
                                 capture_output=True, text=True).stdout.strip()
        res = dict(iadc_blob_hash=githash, fs=FS, cs=CS, offset_pairs=a.offset_pairs, m_out=a.m_out,
                   verdict=collect_verdicts(rows), offset=rows, noise=noise, theory_vs_model_ota=mv,
                   runtime_s=time.time() - t0)
        with open(jpath, "w") as f:
            json.dump(res, f, indent=1)
    render(res, out)
    verd = res["verdict"]
    for k, v in verd.items():
        print(f"{k}: {v['verdict']} (worst {fmt(v['worst_uV'])} uV)")
    ok = all(verd[f"{m}|o{o}"]["verdict"] == "ACCEPT" for m in ("sys", "ota+sys") for o in (2,))   # order 1: informational (measurement-limited)
    print("ACCEPT" if ok else "REJECT")
    sys.exit(0 if ok else 1)


NOTES = [
    "## Reading the results",
    "- Order 2 (the v1 mode): sys and ota+sys ACCEPT (worst 0.7-0.8 uV, inside the measurement resolution, at Vos = 9 mV, lf 1 and 5.3, N = 256..4096). none and ota REJECT as expected: none leaves lf*(Vos+vres) (9.0 mV at lf 1); ota leaves lf*Vos/(N-1)+lf*vres = 7.2 uV (N=4096) to 38 uV (N=256) at lf 1, 38-214 uV at lf 5.3. OTA chop alone does NOT remove offset in incremental mode, as feared in SPEC 3.6.",
    "- Model vs theory (ota only, order 2): 54 of 54 points agree, worst deviation 9.6 % where |theory| >= 10 uV (N=256 points, within their 1-2 uV sem). The 1/(N-1) CoI-weight law is confirmed.",
    "- Order 1: the differential offset estimate is quantisation-limited (sem 0.3 to 83 uV, N=256 worst), so the order-1 sys and ota+sys REJECT rows are a measurement-resolution failure, not evidence of a residual: every sys-mode order-1 value is within about 2 sem of 0. Order-1 ota values sit about Vos/N above the equal-weight theory (7.8 vs 5.0 uV at N=4096, 4 sem); unresolved, probably a last-sample term of the final integrator state. Order 1 is a secondary mode; not pursued within this WO.",
    "- Noise (order 2, N >= 1024, lf 1): none 12-13 uV; sys 2.6/0.8 uV (N=1024, 240/15 SPS), 4.7/1.1 uV (N=4096); ota 2.1/0.4-0.6; ota+sys 2.1/0.6 (N=1024), 1.7/0.5 (N=4096). With the pessimistic lf = 5.3: none 65-70 uV, sys 9.8-25.6 uV at 240 SPS, ota+sys 1.8-1.9 uV. So OTA chop adds a 1.2x (lf 1, N=1024) to 14x (lf 5.3, N=4096) noise gain over sys-only at 240 SPS; sys-only has too few sub-conversions at 240 SPS to average 1/f. Rms values carry about 12 % statistical error (m_out = 32) and N = 256 rows are quantisation-limited.",
    "- Not modelled: the real chopper residual (charge-injection spikes, fs-dependent vres) beyond a constant vres, the SC sampling of OTA noise by the chop phase, and OTA-chop settling cost. The model puts the chopped noise straight at the input with perfect sign inversion; fs/2 = 1 MHz is only 1.6x the 631 kHz 1/f corner.",
    "",
    "## Sequencing rules for the digital sequencer (C9), reasoned not modelled",
    "1. System-chop swaps only at conversion boundaries, never mid-conversion. The CoI weights are (N-1-n); changing the input polarity mid-run makes u_hat = sum w_n s_n u / sum w_n, a wrong-gain, input-dependent result. One sub-conversion has one polarity for all N cycles.",
    "2. Integrator reset (both caps, plus input/ref sampling-cap precharge) between swapped sub-conversions. Incremental decoding assumes x1 = x2 = 0 at n = 0; any leftover state adds a term x2[0]-dependent error of the order of the leftover over N(N-1)/2. Reset also removes memory of the other polarity (a swap with no reset puts +-2u of step on the integrators).",
    "3. Input polarity swap and the reset share a settle slot: swap while the integrators are in reset and let the input cap settle before cycle 0 (swap-induced charge goes to the reset, not to the first sample). Mux switches in the first phase only.",
    "4. OTA-chop phase restarts at the same value at cycle 0 of every sub-conversion, and N is even. With N even and the same starting phase the residual lf*Vos/(N-1) is identical in both sub-conversions and sys averaging cancels it. If N is odd or the phase is continued across the reset, the residual flips sign between sub-conversions and sys averaging doubles it (2*lf*Vos/(N-1)): it adds instead of cancelling.",
    "5. Sub-conversions are averaged in pairs: always an even count, strictly alternating polarity, same N, same fs. An odd count leaves a net offset of one sub-conversion; the sequencer must refuse or round up (iadc.measure_noise rounds up).",
    "6. Chop clock (fs/2) is derived from the same divider as the modulator clock and is phase-locked to the non-overlapping phases; changing the chop phase relative to the sampling phase mid-conversion injects a charge step.",
    "",
    "## Recommendation (D4: the user and the reviewer decide)",
    "Keep OTA chop in v1 as a config bit, always paired with system chop (even N, chop phase restarted at each reset), with sys-only as the fallback mode. Numbers: the pair costs nothing in offset (0.8 uV worst vs 0.7 uV for sys) and lowers 240 SPS noise from 4.7 to 1.7 uV (lf 1, N=4096) and from 9.8-25.6 to 1.8-1.9 uV (lf 5.3). OTA chop alone is not a way to remove offset: it leaves Vos/(N-1) (7.2 to 38 uV at Vos 9 mV, lf 1-5.3, N=4096), so it must never be the only offset canceller. Drop it if the OTA-chop switches or their charge injection cost more area or residual than the 1/f benefit warrants once the OTA noise is characterised (unchopped OTA noise at lf 1 is already about 12 uV, inside the 50 uV v1 target).",
]

if __name__ == "__main__":
    main()
