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


# ---------------------------------------------------------------- v2 (WO-04)
EXPECT_INL_4096 = {"A": 9.3, "A_half": 1.4, "B": 3.7, "C": 541.0}     # review probes, A0 80 dB
EXPECT_FLOOR = 0.5                                                    # ppm, ideal OTA, N 4096
V2_TOL = 0.20
DECAPS_PF = (0, 2, 5, 10, 20)
PAD_PF, R_REF = 5.0, 500.0
INL_BUDGET = 100.0


def v2_base(vref, c1, c2, k, cs=1e-12, **kw):
    return m.with_(base(vref, c1, c2, k), a0_db=80, ref_mode="shared", cs=cs, **kw)


def v2_opts():
    return {"A": v2_base(1.2, 0.25, 0.5, 1.0),
            "A_half": v2_base(1.2, 0.125, 0.5, 0.5),
            "B": v2_base(2.048, 0.125, 0.5, 0.5),
            "B_half-Cs": v2_base(2.048, 0.125, 0.5, 0.5, cs=0.5e-12),
            "C": v2_base(2.048, 0.25, 0.5, 1.0)}


def inl_v2(p, N, residue, vlin=2.0, npts=401):
    """INL/gain of the static sweep (no noise/offset). residue: add x2[N]/(c1 c2)/(N(N-1)/2) to u_hat."""
    pp = m.with_(p, N=N, ktc_on=False, flicker_on=False, vos=0.0, vres=0.0, vlin_diff=vlin)
    u = np.linspace(-0.9, 0.9, npts)
    uh, st = m.convert(pp, u, rng=np.random.default_rng(2), return_state=True)
    if residue:
        uh = uh + st["x2_final"] / (pp.c1 * pp.c2) / (N * (N - 1) / 2)
    return m.linearity(u, uh)


def floor_ppm(p, N):
    u, uh, _ = m.dc_sweep(ideal(p, N), umax=0.9, npts=801)
    return m.linearity(u, uh)["inl_ppm"]


def within(v, exp, tol=V2_TOL):
    return bool(np.isfinite(v) and abs(v - exp) <= tol * abs(exp))


def avg_floor(p0, N, Ks, G=65, R=8, seed=11):
    """Deterministic error that averaging does not remove (B point, ideal OTA, sys-chop pairs).
    nf: noise-free max|err| over a fine DC grid (identical in every K by construction).
    For each K: kT/C-dithered pair averages, per-DC bias = mean over R repeats; max|bias| over G DC values
    (resolution: std/sqrt(R)), and rms of the repeat scatter (white-noise rms)."""
    pi = m.with_(ideal(p0, N), sys_chop=True)
    ug = np.linspace(-0.9, 0.9, 4001)
    nf = float(np.max(np.abs(m.convert(m.with_(pi, sys_chop=False), ug) - ug))) * p0.vref * 1e6
    nf_pair = None
    rows = []
    for K in Ks:
        pk = m.with_(pi, ktc_on=True, cs=p0.cs)
        rng = np.random.default_rng(seed)
        u0 = np.linspace(-0.9, 0.9, G) + rng.uniform(-0.5, 0.5, G) * (1.8 / G)
        u = np.repeat(u0, R * K)
        sign = np.tile(np.array([1.0, -1.0]), len(u) // 2)
        uh = m.convert(pk, u, rng=rng, sys_sign=sign).reshape(G, R, K).mean(axis=2)
        err = (uh - u0[:, None]) * p0.vref * 1e6
        bias = err.mean(axis=1)
        rows.append({"K": K, "max_abs_bias_uV": float(np.max(np.abs(bias))),
                     "rms_scatter_uV": float(np.sqrt(np.mean(err.var(axis=1, ddof=1)))),
                     "bias_resolution_uV": float(np.sqrt(np.mean(err.var(axis=1, ddof=1)) / R)),
                     "rate_sps": p0.fs / (N * K)})
    return {"N": N, "noise_free_max_uV": nf, "rows": rows}


def main_v2(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    lines, fails = [], []

    def rec(ok, text):
        lines.append(f"{'PASS' if ok else 'FAIL'} {text}")
        if not ok:
            fails.append(text)

    opts = v2_opts()
    inl_tab = {}
    for n, p in opts.items():
        l4 = inl_v2(p, 4096, False)
        l1r = inl_v2(p, 1024, True)
        l1 = inl_v2(p, 1024, False)
        inl_tab[n] = {"inl_4096": l4["inl_ppm"], "gain_4096": l4["gain_err_ppm"], "inl_1024_residue": l1r["inl_ppm"],
                      "inl_1024_plain": l1["inl_ppm"], "floor_4096": floor_ppm(p, 4096), "floor_1024": floor_ppm(p, 1024),
                      "cint1_pF": p.cs / p.c1 * 1e12}
    for n, e in EXPECT_INL_4096.items():
        v = inl_tab[n]["inl_4096"]
        rec(within(v, e), f"INL N 4096 A0 80 shared {n}: {v:.2f} ppm vs expected {e} (+-20 %)")
    for n in inl_tab:
        v = inl_tab[n]["floor_4096"]
        rec(within(v, EXPECT_FLOOR), f"ideal-OTA quantization floor N 4096 {n}: {v:.2f} ppm vs expected {EXPECT_FLOOR} (+-20 %)")
    rec(inl_tab["B_half-Cs"]["inl_4096"] <= 1.2 * inl_tab["B"]["inl_4096"],
        f"B_half-Cs INL ({inl_tab['B_half-Cs']['inl_4096']:.2f}) ~ unchanged vs B ({inl_tab['B']['inl_4096']:.2f}) (review E1)")
    rec(all(inl_tab[n]["inl_1024_residue"] < inl_tab[n]["inl_1024_plain"] or n == "C" for n in inl_tab),
        "residue reconstruction lowers N 1024 INL (except C where OTA nonlinearity dominates)")
    # non-vacuity: the +-20 % comparator rejects a doctored expectation
    rec(not within(inl_tab["B"]["inl_4096"], 1.5 * EXPECT_INL_4096["B"]) and not within(inl_tab["A"]["inl_4096"], 0.5 * EXPECT_INL_4096["A"]),
        "non-vacuity: comparator rejects expected values doctored by x1.5 / x0.5")
    # non-vacuity: with A0 40 dB the A INL must be far outside the expected value
    bad = inl_v2(m.with_(opts["A"], a0_db=40), 4096, False)["inl_ppm"]
    rec(not within(bad, EXPECT_INL_4096["A"]), f"non-vacuity: A at A0 40 dB rejects ({bad:.0f} ppm)")
    print(f"inl done", flush=True)

    # 4. reference recovery at the B point
    refrows = []
    for dc in DECAPS_PF:
        cd = (PAD_PF + dc) * 1e-12
        pr = m.with_(opts["B"], cd_ref=cd, tau_ref=R_REF * cd)
        l = inl_v2(pr, 4096, False)
        refrows.append({"decap_pF": dc, "tau_ref_ns": R_REF * cd * 1e9, "inl_ppm": l["inl_ppm"], "gain_err_ppm": l["gain_err_ppm"],
                        "decap_area_um2": dc * 1e-12 / MIM_F_PER_UM2})
    ok_rows = [r for r in refrows if r["inl_ppm"] <= INL_BUDGET / 3]
    min_decap = ok_rows[0] if ok_rows else None
    rec(all(np.isfinite(r["inl_ppm"]) and np.isfinite(r["gain_err_ppm"]) for r in refrows), "ref recovery: all measurements finite")
    rec(min_decap is not None, "ref recovery: some decap in the grid keeps INL <= 100/3 ppm" +
        (f" (smallest {min_decap['decap_pF']} pF = {min_decap['decap_area_um2']:.0f} um2)" if min_decap else ""))
    # sensitivity: at R = 500 ohm tau_ref <= 12.5 ns << t_half (225 ns), so the sweep is flat. Show where recovery starts to matter.
    taurows = []
    for tau_ns in (12.5, 30, 60, 100, 200):
        for cd_pf in (2, 10):
            pr = m.with_(opts["B"], cd_ref=cd_pf * 1e-12, tau_ref=tau_ns * 1e-9)
            l = inl_v2(pr, 4096, False)
            taurows.append({"tau_ref_ns": tau_ns, "cd_pF": cd_pf, "inl_ppm": l["inl_ppm"], "gain_err_ppm": l["gain_err_ppm"]})
    g0 = refrows[0]["gain_err_ppm"]
    g100 = [r for r in taurows if r["tau_ref_ns"] == 100 and r["cd_pF"] == 2][0]["gain_err_ppm"]
    rec(abs(g100 - g0) > 10, f"non-vacuity: ref-recovery sweep reacts to a slow reference (tau 100 ns / 2 pF: gain err {g100:.0f} vs settled {g0:.0f} ppm)")
    print("ref done", flush=True)

    # 5. quantization floor of averaged modes
    qf = {str(N): avg_floor(opts["B"], N, (2, 4, 8, 16, 32, 64)) for N in (1024, 4096)}
    th_floor = {"1024": 6.8, "4096": 0.5}
    for N in qf:
        rec(np.isfinite(qf[N]["noise_free_max_uV"]) and all(np.isfinite(r["max_abs_bias_uV"]) for r in qf[N]["rows"]),
            f"quant floor N {N}: finite (noise-free max|err| {qf[N]['noise_free_max_uV']:.1f} uV)")
    rec(qf["1024"]["noise_free_max_uV"] > 4 * qf["4096"]["noise_free_max_uV"],
        f"quant floor scales down with N: {qf['1024']['noise_free_max_uV']:.1f} uV (1024) vs {qf['4096']['noise_free_max_uV']:.1f} (4096)")
    print("avg floor done", flush=True)

    ref_txt = (f"smallest decap with INL <= {INL_BUDGET/3:.1f} ppm: {min_decap['decap_pF']} pF "
               f"(tau_ref {min_decap['tau_ref_ns']:.1f} ns, {min_decap['decap_area_um2']:.0f} um2 MIM at 2 fF/um2)" if min_decap
               else f"no decap in {DECAPS_PF} reaches INL <= {INL_BUDGET/3:.1f} ppm")
    L = ["# S1 v2: INL at the D17 point (WO-04)", "",
         f"Command: `python3 -m model.studies.s1_vref --v2 --out {a.out}`", "",
         "Setup: fs 2 MHz, A0 80 dB (D15), a0_drop 0.9 with vlin 2.0 V, ref_mode shared (D14), tau_in 20 ns, tau_ref 10 ns / cd_ref 20 pF "
         "(items 3, 5), no noise/offset in the INL sweep, 401 points in +-0.9. INL is the endpoint-fit INL in ppm of FSR (2 normalised). "
         "Residue column: u = (sum S + (k/c1) S + x2[N]/(c1 c2)) / (N(N-1)/2) from the final x2 state. Floor: the same sweep with an ideal OTA, ideal references.", "",
         "```"] + lines + ["```", "",
         "## INL (ppm FSR) and quantization floor", "",
         "| option | VREF | c1 | k | Cs pF | Cint1 pF | INL N4096 | floor N4096 | INL N1024 residue | INL N1024 plain | floor N1024 | gain err N4096 ppm |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, p in opts.items():
        t = inl_tab[n]
        L.append(f"| {n} | {p.vref} | {p.c1} | {p.k} | {p.cs*1e12:g} | {t['cint1_pF']:.1f} | {t['inl_4096']:.2f} | {t['floor_4096']:.2f} | "
                 f"{t['inl_1024_residue']:.2f} | {t['inl_1024_plain']:.2f} | {t['floor_1024']:.2f} | {t['gain_4096']:.0f} |")
    L += ["", f"Expected (review probes, N 4096, A0 80): " + ", ".join(f"{k} {v}" for k, v in EXPECT_INL_4096.items()) + f", floor {EXPECT_FLOOR} ppm.", "",
          "## Reference recovery at the B point (shared Cs, N 4096)", "",
          f"R = {R_REF:g} ohm, node C = {PAD_PF:g} pF pad + on-chip decap; tau_ref = R C. Model: cd_ref = C, share = Cs/(Cs+C).", "",
          "| decap pF | tau_ref ns | INL ppm | gain err ppm | decap MIM um2 (2 fF/um2) |", "|---|---|---|---|---|"]
    for r in refrows:
        L.append(f"| {r['decap_pF']} | {r['tau_ref_ns']:.1f} | {r['inl_ppm']:.2f} | {r['gain_err_ppm']:.0f} | {r['decap_area_um2']:.0f} |")
    L += ["", ref_txt + ".", "",
          "At R = 500 ohm the reference node settles to e^-18 within a half period (t_half 225 ns), so INL and gain error do not depend on the decap in this model; "
          "decap sizing is then set by other effects (pad/bond droop between cycles, noise), not modelled here. Where recovery starts to matter (B point, shared Cs, N 4096):", "",
          "| tau_ref ns | cd_ref pF | INL ppm | gain err ppm |", "|---|---|---|---|"] + [
          f"| {r['tau_ref_ns']:g} | {r['cd_pF']} | {r['inl_ppm']:.2f} | {r['gain_err_ppm']:.0f} |" for r in taurows] + ["",
          "## Quantization floor of averaged modes (B point, ideal OTA, sys-chop pairs)", "",
          "Noise-free max|error| over 4001 DC values in +-0.9 is identical for every K (averaging identical conversions removes nothing). "
          "With kT/C dither (white, Cs 1 pF; flicker not included, which is conservative) the per-DC bias is estimated from 8 repeats at 65 DC values; "
          "its resolution is std/sqrt(8), shown as 'res'. Rates are fs/(N K).", ""]
    for N in qf:
        d = qf[N]
        L += [f"N = {N}: noise-free max|err| = {d['noise_free_max_uV']:.2f} uV", "",
              "| K pairs | rate SPS | max abs bias uV | res uV | rms scatter uV |", "|---|---|---|---|---|"]
        for r in d["rows"]:
            L.append(f"| {r['K']} | {r['rate_sps']:.2f} | {r['max_abs_bias_uV']:.2f} | {r['bias_resolution_uV']:.2f} | {r['rms_scatter_uV']:.2f} |")
        L.append("")
    (out / "s1_vref_v2.md").write_text("\n".join(L) + "\n")
    (out / "s1_vref_v2.json").write_text(json.dumps({"inl": inl_tab, "ref_recovery": refrows, "ref_tau_sweep": taurows, "min_decap": min_decap,
                                                    "avg_floor": qf, "lines": lines}, indent=1, default=float))
    print("\n".join(lines)); print(ref_txt)
    print("REJECT" if fails else "ACCEPT")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--vlin", type=float, default=2.0)
    ap.add_argument("--v2", action="store_true", help="WO-04: INL at the D17 point, ref recovery, quant floor")
    a = ap.parse_args(argv)
    if a.v2:
        return main_v2(a)
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
