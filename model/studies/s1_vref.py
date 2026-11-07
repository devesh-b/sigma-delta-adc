"""S1: VREF / integrator-swing study (WO-02).

Options (fs 2 MHz, Cs 1 pF, OTA+system chop, vos 3 mV, vres 5 uV, A0 75 dB, a0_drop 0.9):
  A: VREF 1.2 V,   c1 0.25,  c2 0.5, k 1
  A2: A with c2 0.25 (x2 halved, identical bitstream; sizes OTA2)
  B: VREF 2.048 V, c1 0.125, c2 0.5, k 0.5 (x1,x2 halved, bitstream == A)
  C: VREF 2.048 V, c1 0.25   (today's model, reference)

Usage: python3 -m model.studies.s1_vref --out DIR [--vlin V]
  --vlin  differential linear range used by the INL pass criterion (default 2.0 V)
Exit code 1 if a theory check, the non-vacuity self-check or a measurement
(NaN/missing) fails. Option REJECTs are results, not errors.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from model import iadc as m

RATES = [240, 60, 15, 3.75]
VLINS = [1.5, 2.0, 2.5, 3.0]
MIM_F_PER_UM2 = 2e-15          # 2 fF/um^2
NOISE_MAX_UV = 50.0            # @15 SPS, lf_gain 5.3
INL_MAX_PPM = 100.0            # at vlin
SWING_MAX_V = 0.9              # per side
LF_PESS = 5.3
RES_MIN_N1024 = 2 * math.log2(1024) - 4   # 16 b
X_LIMIT = 1.2                  # units of VREF


def base(vref, c1, c2, k, lf=1.0, **kw):
    p = m.Params(order=2, N=1024, fs=2e6, vref=vref, c1=c1, c2=c2, k=k, cs=1e-12, a0_db=75, a0_drop=0.9,
                 ktc_on=True, flicker_on=True, vos=3e-3, chop=True, vres=5e-6, sys_chop=True,
                 ref_mode="separate", tau_in=20e-9, tau_ref=10e-9, lf_gain=lf,
                 white_ng_ref=m.Params().noise_gain)       # 5.3: legacy-equal at c1=0.25
    return m.with_(p, **kw)


def ideal(p, N):
    return m.with_(p, N=N, a0_db=np.inf, a0_drop=0.0, ktc_on=False, flicker_on=False, vos=0.0, vres=0.0,
                   chop=False, sys_chop=False, ref_mode="shared", tau_in=0.0, tau_ref=0.0, xmax=100)


def quant(p, N):
    u, uh, st = m.dc_sweep(ideal(p, N), umax=0.9, npts=801)
    return {"bits": m.resolution_bits(np.max(np.abs(uh - u))), "x1max": st["x1max"], "x2max": st["x2max"],
            "x1_v_side": st["x1max_v_side"], "x2_v_side": st["x2max_v_side"]}


def inl(p, vlin):
    pp = m.with_(p, ktc_on=False, flicker_on=False, vos=0.0, vres=0.0, vlin_diff=vlin)
    u, uh, _ = m.dc_sweep(pp, umax=0.9, npts=401)
    return m.linearity(u, uh)["inl_ppm"]


def noise(p):
    out = {}
    for lf in (1.0, LF_PESS):
        pl = m.with_(p, lf_gain=lf)
        for r in RATES:
            k = max(1, round(pl.fs / (r * pl.N)))
            rms = m.measure_noise(pl, k, m_out=24)["rms_v"]
            out[f"lf{lf:g}@{r}"] = {"rms_uv": rms * 1e6, "eff_bits": m.eff_res_bits(rms, pl.vref)}
    return out


def bitstream_equiv():
    """Algebra (coordinator amendment F1): scaling c1 by 1/2 and k by 1/2 (c2 fixed)
    halves x1 and x2, y=sign(x2) unchanged => identical bitstream; (0.125, k=1)
    changes k/c1 and therefore the NTF. u_hat is a function of the bitstream, so
    identical u_hat on a dense sweep <=> identical y (tolerance 1e-9)."""
    def uh(c1, c2, k):
        p = ideal(base(2.048, c1, c2, k), 1024)
        return m.dc_sweep(p, umax=0.9, npts=801)[1]
    ref = uh(0.25, 0.5, 1.0)
    return {"B(0.125,0.5,k0.5) vs A": float(np.max(np.abs(uh(0.125, 0.5, 0.5) - ref))),
            "A2(0.25,c2 0.25,k1) vs A": float(np.max(np.abs(uh(0.25, 0.25, 1.0) - ref))),
            "wrong B(0.125,0.5,k1) vs A": float(np.max(np.abs(uh(0.125, 0.5, 1.0) - ref)))}


def evaluate(name, p, vlin_crit):
    res = {"name": name, "vref": p.vref, "c1": p.c1, "c2": p.c2, "k": p.k}
    res["noise"] = noise(p)
    res["quant"] = {str(N): quant(p, N) for N in (1024, 4096)}
    q = res["quant"]["1024"]
    res["peak_v_side"] = {"x1": q["x1_v_side"], "x2": q["x2_v_side"], "max": max(q["x1_v_side"], q["x2_v_side"])}
    res["inl_ppm"] = {f"{v:g}": inl(p, v) for v in VLINS}
    res["inl_at_crit"] = inl(p, vlin_crit)
    cint = p.cs / p.c1
    res["cint1_pF_side"] = cint * 1e12
    res["cint1_area_um2_side"] = cint / MIM_F_PER_UM2
    res["cint1_area_um2_total"] = 2 * cint / MIM_F_PER_UM2
    return res


def criteria(res, vlin_crit):
    n15 = res["noise"][f"lf{LF_PESS:g}@15"]["rms_uv"]
    c = {"noise": (n15 <= NOISE_MAX_UV, f"{n15:.2f} uV <= {NOISE_MAX_UV:g} @15 SPS lf {LF_PESS:g}"),
         "inl": (res["inl_at_crit"] <= INL_MAX_PPM, f"{res['inl_at_crit']:.1f} ppm <= {INL_MAX_PPM:g} @ vlin {vlin_crit:g} V"),
         "swing": (res["peak_v_side"]["max"] <= SWING_MAX_V, f"{res['peak_v_side']['max']:.3f} V/side <= {SWING_MAX_V:g}")}
    return c


def finite(o):
    if isinstance(o, dict):
        return all(finite(v) for v in o.values())
    if isinstance(o, (list, tuple)):
        return all(finite(v) for v in o)
    if isinstance(o, float):
        return math.isfinite(o)
    return o is not None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--vlin", type=float, default=2.0)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    fails, lines = [], []

    tuned_ok = True
    opts = {"A": base(1.2, 0.25, 0.5, 1.0),
            "A2": base(1.2, 0.25, 0.25, 1.0),
            "B": base(2.048, 0.125, 0.5, 0.5),
            "C": base(2.048, 0.25, 0.5, 1.0)}
    R = {n: evaluate(n, p, a.vlin) for n, p in opts.items()}
    verdict = {}
    for n in R:
        c = criteria(R[n], a.vlin)
        ok = all(v[0] for v in c.values())
        if n == "B" and not tuned_ok:
            ok = False
        verdict[n] = {"accept": ok, "criteria": {k: {"pass": bool(v[0]), "detail": v[1]} for k, v in c.items()}}
        lines.append(f"{'ACCEPT' if ok else 'REJECT'} option {n}: " + "; ".join(
            f"{k} {'ok' if v[0] else 'FAIL'} ({v[1]})" for k, v in c.items()))

    # theory checks (expected from theory, not from the model)
    th = []
    be = bitstream_equiv()
    th.append(("bitstream B(c1 .125,k .5) == A", be["B(0.125,0.5,k0.5) vs A"] < 1e-9, f"max|du_hat| {be['B(0.125,0.5,k0.5) vs A']:.2e}"))
    th.append(("bitstream A2(c2 .25) == A", be["A2(0.25,c2 0.25,k1) vs A"] < 1e-9, f"max|du_hat| {be['A2(0.25,c2 0.25,k1) vs A']:.2e}"))
    th.append(("bitstream wrong-B(c1 .125,k 1) != A", be["wrong B(0.125,0.5,k1) vs A"] > 1e-6, f"max|du_hat| {be['wrong B(0.125,0.5,k1) vs A']:.2e}"))
    th.append(("B swing = A swing x (2.048/1.2) x 0.5 (algebra)", abs(R["B"]["peak_v_side"]["x2"] - R["A"]["peak_v_side"]["x2"] * 2.048 / 1.2 * 0.5) < 0.02 and abs(R["B"]["peak_v_side"]["x1"] - R["A"]["peak_v_side"]["x1"] * 2.048 / 1.2 * 0.5) < 0.02,
               f"B x1 {R['B']['peak_v_side']['x1']:.3f} x2 {R['B']['peak_v_side']['x2']:.3f}; A x1 {R['A']['peak_v_side']['x1']:.3f} x2 {R['A']['peak_v_side']['x2']:.3f}"))
    th.append(("A2 x2 swing = A x2 / 2, x1 unchanged", abs(R["A2"]["peak_v_side"]["x2"] - R["A"]["peak_v_side"]["x2"] / 2) < 0.01 and abs(R["A2"]["peak_v_side"]["x1"] - R["A"]["peak_v_side"]["x1"]) < 0.01,
               f"A2 x1 {R['A2']['peak_v_side']['x1']:.3f} x2 {R['A2']['peak_v_side']['x2']:.3f}"))
    d = (R["A"]["noise"]["lf1@15"]["eff_bits"] - R["C"]["noise"]["lf1@15"]["eff_bits"])
    exp = math.log2(2.048 / 1.2)
    th.append(("eff-bit difference C-A", abs((-d) - exp) <= 0.05,
               f"A-C = {d:+.3f} b, theory -{exp:.3f} +-0.05"))
    sw = R["C"]["peak_v_side"]["max"]
    th.append(("C peak swing/side ~ 1.23 V (SPEC 2.1)", abs(sw - 1.23) <= 0.15 * 1.23, f"measured {sw:.3f} V (x1 {R['C']['peak_v_side']['x1']:.3f}, x2 {R['C']['peak_v_side']['x2']:.3f}), expected 1.23 +-15 %"))
    # non-vacuity: with vlin 0.5 V option A's INL criterion must REJECT
    inl05 = inl(opts["A"], 0.5)
    th.append(("non-vacuity: A INL at vlin 0.5 V rejects", inl05 > INL_MAX_PPM, f"INL {inl05:.0f} ppm > {INL_MAX_PPM:g}"))
    # sanity from SPEC 2.3 / design report: option C at its legacy range is the 71 ppm design point
    inlc = inl(opts["C"], 1.2 * 2.048)
    th.append(("C at legacy xswing-equivalent vlin 2.46 V ~ 71 ppm (report_design.md)", abs(inlc - 71.3) <= 7.1, f"{inlc:.1f} ppm"))
    # non-vacuity of the noise and swing criteria: doctored copies must REJECT
    import copy
    bad = copy.deepcopy(R["A"])
    bad["noise"][f"lf{LF_PESS:g}@15"]["rms_uv"] = 60.0
    bad["peak_v_side"]["max"] = 1.0
    cb = criteria(bad, a.vlin)
    th.append(("non-vacuity: noise criterion rejects 60 uV", not cb["noise"][0], cb["noise"][1]))
    th.append(("non-vacuity: swing criterion rejects 1.0 V/side", not cb["swing"][0], cb["swing"][1]))
    for nme, ok, det in th:
        lines.append(f"{'PASS' if ok else 'FAIL'} theory-check {nme}: {det}")
        if not ok:
            fails.append(nme)
    if not finite(R) or not finite(be):
        fails.append("NaN/missing measurement")
        lines.append("FAIL measurement: NaN or missing value")

    # recommendation
    acc = [n for n in R if verdict[n]["accept"]]
    if acc:
        rec = (f"Options passing the criteria: {', '.join(acc)}. ")
        if "A" in acc:
            rec += ("A has the smallest Cint1 (4 pF/side) and the lowest white noise gain (5.3) but gives up "
                    f"{exp:.2f} b of effective bits vs 2.048 V (same uV noise). ")
        if "B" in acc:
            rec += (f"B keeps the 2.048 V FSR and has the least swing; it needs Cint1 = {R['B']['cint1_pF_side']:.0f} pF/side "
                    f"({R['B']['cint1_area_um2_side']:.0f} um2/side) and raises white noise gain to {opts['B'].noise_gain:.1f}. ")
    else:
        rec = "No option passes all criteria. "
    rec += "The study does not choose; D3 is the user's call."

    # write md/json
    def f(x, n=2):
        return f"{x:.{n}f}"
    md = ["# S1: VREF / integrator-swing study", "",
          f"Command: `python3 -m model.studies.s1_vref --out {a.out} --vlin {a.vlin:g}`", "",
          "Setup: fs 2 MHz, N 1024, Cs 1 pF, OTA+system chop, vos 3 mV, vres 5 uV, A0 75 dB, a0_drop 0.9, "
          "linear range `vlin_diff` in volts (differential). White noise: OTA part of ktc_excess scaled by noise_gain/5.3 "
          "(identical to legacy at c1=0.25; B: noise gain 9.3, excess 1.88 vs 1.5).", "",
          "## Verdicts", "", "```"] + lines + ["```", "", "## Option B definition", "", "B = c1 0.125, c2 0.5, k 0.5 (coordinator amendment F1: x1, x2 halve, bitstream identical to A, k/c1 = 4). "
          "A2 = A with c2 0.25 (x2 halved, same bitstream; sizes OTA2)."]
    md += ["", "## Per option", "",
           "| opt | VREF | c1 | c2 | k | peak x1 / x2 (V/side) | bits N=1024 / 4096 | Cint1 pF/side | Cint1 um2 (side / both) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for n, r in R.items():
        md.append(f"| {n} | {r['vref']} | {r['c1']} | {r['c2']} | {r['k']} | {f(r['peak_v_side']['x1'],3)} / {f(r['peak_v_side']['x2'],3)} | "
                  f"{f(r['quant']['1024']['bits'],1)} / {f(r['quant']['4096']['bits'],1)} | {f(r['cint1_pF_side'],1)} | "
                  f"{r['cint1_area_um2_side']:.0f} / {r['cint1_area_um2_total']:.0f} |")
    md += ["", "## Noise (uV rms) and effective bits over FSR = 2 VREF", "",
           "| opt | lf_gain | " + " | ".join(f"{r} SPS uV (bits)" for r in RATES) + " |", "|---|---|" + "---|" * len(RATES)]
    for n, r in R.items():
        for lf in (1.0, LF_PESS):
            md.append(f"| {n} | {lf:g} | " + " | ".join(
                f"{f(r['noise'][f'lf{lf:g}@{x}']['rms_uv'])} ({f(r['noise'][f'lf{lf:g}@{x}']['eff_bits'],1)})" for x in RATES) + " |")
    md += ["", "## INL (ppm FSR) vs OTA linear range vlin_diff (V differential)", "",
           "| opt | " + " | ".join(f"{v:g} V" for v in VLINS) + " |", "|---|" + "---|" * len(VLINS)]
    for n, r in R.items():
        md.append(f"| {n} | " + " | ".join(f(r["inl_ppm"][f"{v:g}"], 1) for v in VLINS) + " |")
    md += ["", "## Recommendation", "", rec, ""]
    (out / "s1_vref.md").write_text("\n".join(md))
    (out / "s1_vref.json").write_text(json.dumps(
        {"vlin_crit": a.vlin, "options": R, "verdict": verdict, "bitstream_maxdiff": be,
         "theory": [{"name": n, "pass": bool(o), "detail": d_} for n, o, d_ in th], "recommendation": rec},
        indent=1, default=float))
    print("\n".join(lines)); print("\n" + rec)
    if fails:
        print("FAILED CHECKS:", fails); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
