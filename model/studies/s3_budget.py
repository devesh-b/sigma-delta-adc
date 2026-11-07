"""S3: error budget -> per-block specs at the decided design point (WO-05).

Design point (D17, D22-D24): order 2 CIFB c1 0.125 c2 0.5 k 0.5, VREF 2.048 V, Cs 0.5 pF shared (input = DAC),
fs 2 MHz, N 4096 precision, ota+sys chop (sub-conversions averaged in pairs), 500 ohm + 5 pF pads.

Usage: python3 -m model.studies.s3_budget --out DIR [--reuse] [--nonvac] [--quick]
  (default)   sensitivity sweeps + theory checks + allocation + joint run; prints ACCEPT/REJECT, exit 1 on REJECT
  --reuse     reuse DIR/s3_sweeps.json (skip the sweep runs; theory checks and allocation are re-run)
  --nonvac    allocation rows + joint run with OTA A0 70 dB / drop 0.9 / vlin 0.8 V: must REJECT on INL (exit 1)
  --quick     shorter reset-residue check (N 256)

Expected values in the theory checks come from model/studies/s2_theory.py, SPEC and charge conservation,
never from iadc.py. Sweeps use one-at-a-time perturbations of an otherwise ideal loop (switch kT/C only).
"""
import argparse
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

from model import iadc as m
from model.studies import s1_vref as s1
from model.studies import s2_theory as th

K_B = 1.380649e-23
VREF = 2.048
C1, C2, KK = 0.125, 0.5, 0.5
CS = 0.5e-12
FS = 2e6
N_PREC = 4096
LF = 9.3                       # pessimistic bound (noise gain at c1 0.125); SPEC 2.2 nominal is ~1
X1MAX_V = 2 * 0.61             # differential peak of x1 [V] (SPEC 1, S1: 0.61 V/side)
M_OUT = 64                     # outputs per noise estimate (statistical error ~ 1/sqrt(2*64) = 9 %)
OFF_FIELDS = ("vos", "vos2", "vres", "x1_offset", "comp_offset")

# budgets (WO-05 table; stretch targets with margin: noise 2x under 5 uV, INL 1.5x under 30 ppm)
BUDGET = {"noise_uv": 2.5, "inl_ppm": 20.0, "offset_uv": 5.0, "gain_ppm": 5000.0}

# ----------------------------------------------------------------------------------------- spec candidates
SPEC_BLK = {"a0_db": 80.0, "a0_drop": 0.9, "vlin": 2.0, "ota_en": 10.0, "fc": 631e3, "lf": LF, "vres": 5e-6,
            "vos": 9e-3, "vos2": 9e-3, "comp_off": 20e-3, "comp_noise": 5e-3, "tau_in": 18.75e-9, "tau_ref": 10e-9,
            "r_reset": 1e-4, "i_leak": 100e-12, "r_ext": 10.0, "dcs_ratio": 0.0056}
# r_ext: DC resistance per reference pin (board spec, SPEC 3.0); dcs_ratio: PDK 3-sigma k/c1 ratio mismatch (review S3-6, 0.56 %)
RHO_LEAK = 1e-3                # ASSUMPTION: fraction of the leakage offset that does not cancel in sys pairs


def excess_from_en(en):
    """ktc_excess for an OTA white density en [nV/rtHz]. iadc.py calibrates excess = 1 (switch) + 0.5 (OTA at
    6.9 nV/rtHz referred through noise gain 5.3); OTA thermal power ~ en^2, so excess = 1 + 0.5*(en/6.9)^2,
    and the model scales the OTA part with noise_gain/5.3 (white_ng_ref). Model structure, not a derivation."""
    return 1.0 + 0.5 * (en / 6.9) ** 2


def ideal_base(**kw):
    """Ideal loop at the design point: switch kT/C only, chopping on, everything else perfect."""
    p = m.Params(order=2, N=N_PREC, fs=FS, vref=VREF, c1=C1, c2=C2, k=KK, cs=CS, a0_db=np.inf, a0_drop=0.0,
                 ktc_on=True, ktc_excess=1.0, flicker_on=False, vos=0.0, chop=True, sys_chop=True, vres=0.0,
                 ref_mode="shared", tau_in=0.0, tau_ref=0.0, lf_gain=1.0, white_ng_ref=m.Params().noise_gain)
    return m.with_(p, **kw)


def spec_point(**ov):
    """All blocks at their spec values together."""
    s = dict(SPEC_BLK)
    s.update(ov)
    return ideal_base(a0_db=s["a0_db"], a0_drop=s["a0_drop"], vlin_diff=s["vlin"], ktc_excess=excess_from_en(s["ota_en"]),
                      flicker_on=True, ota_fc=s["fc"], lf_gain=s["lf"], vres=s["vres"], vos=s["vos"], vos2=s["vos2"],
                      comp_offset=s["comp_off"] / VREF, comp_noise=s["comp_noise"] / VREF, tau_in=s["tau_in"],
                      tau_ref=s["tau_ref"], cd_ref=5e-12, x1_offset=s["r_reset"] * X1MAX_V, r_ext_ref=s["r_ext"])


# ----------------------------------------------------------------------------------------- measurements
def noise_uv(p, rate, N):
    pl = m.with_(p, N=N)
    k = max(1, round(pl.fs / (rate * N)))
    return m.measure_noise(pl, k, m_out=M_OUT)["rms_v"] * 1e6


def static_err_uv(p, sys, B=512):
    """Mean error [uV] over stratified DC inputs, noise-free; sys: pair of opposite input polarities."""
    q = m.with_(p, ktc_on=False, flicker_on=False)
    u = -0.5 + (np.arange(B) + 0.5) / B
    nz = m.ota_noise_block(q, B, np.random.default_rng(0))
    if sys:
        a = m.convert(q, u, ota_noise=nz, sys_sign=np.ones(B))
        b = m.convert(q, u, ota_noise=nz, sys_sign=-np.ones(B))
        uh = 0.5 * (a + b)
    else:
        uh = m.convert(q, u, ota_noise=nz)
    return float(np.mean(uh - u)) * q.vref * 1e6


def offset_uv(p, sys):
    """Paired offset: error with the offset sources on minus the same loop with them zeroed (cancels quantization)."""
    p0 = m.with_(p, **{f: 0.0 for f in OFF_FIELDS})
    return static_err_uv(p, sys) - static_err_uv(p0, sys)


def inl_gain(p, vlin=None):
    r = s1.inl_v2(m.with_(p, ktc_on=False, flicker_on=False), p.N, True, vlin=vlin or p.vlin_diff or 2.0)
    return r["inl_ppm"], r["gain_err_ppm"]


def metrics(p, noise=True):
    r = {}
    if noise:
        r["n15"] = noise_uv(p, 15, N_PREC)
        r["n240"] = noise_uv(p, 240, 1024)
    r["inl"], r["gain"] = inl_gain(p)
    r["off_nosys"] = offset_uv(p, False)
    r["off_sys"] = offset_uv(p, True)
    return r


def quant_floor_ppm(p):
    return s1.floor_ppm(p, p.N)


# ----------------------------------------------------------------------------------------- sweeps
def leak_offset(i, fs, cs):
    """Input-referred offset of a constant virtual-ground leakage: charge I/fs per cycle against Cs*u."""
    return i / (fs * cs)


def sweeps():
    en = excess_from_en
    sw = [
        ("A0 x a0_drop (vlin 2 V)", "dB/-", [(a, d) for d in (0.5, 0.9) for a in (70, 75, 80, 85, 90)],
         lambda v: ideal_base(a0_db=v[0], a0_drop=v[1], vlin_diff=2.0)),
        ("vlin_diff (A0 80, drop 0.9)", "V", [0.8, 1.0, 1.5, 2.0],
         lambda v: ideal_base(a0_db=80, a0_drop=0.9, vlin_diff=v)),
        ("OTA thermal en", "nV/rtHz", [5, 7, 10, 14, 20], lambda v: ideal_base(ktc_excess=en(v))),
        ("OTA 1/f corner (lf 9.3)", "Hz", [1e5, 631e3, 2e6],
         lambda v: ideal_base(flicker_on=True, ota_fc=v, lf_gain=LF)),
        ("lf (flicker 631k, Vos1 9 mV, vres 5 uV)", "-", [1.0, 9.3],
         lambda v: ideal_base(flicker_on=True, vos=9e-3, vres=5e-6, lf_gain=v)),
        ("vres (lf 9.3)", "V", [0.0, 5e-6, 20e-6], lambda v: ideal_base(vres=v, lf_gain=LF)),
        ("Vos2", "V", [1e-3, 9e-3, 20e-3], lambda v: ideal_base(vos2=v)),
        ("comp_offset (c2 0.5)", "V", [5e-3, 20e-3, 50e-3], lambda v: ideal_base(comp_offset=v / VREF)),
        ("comp_offset (c2 0.25)", "V", [5e-3, 20e-3, 50e-3], lambda v: ideal_base(comp_offset=v / VREF, c2=0.25)),
        ("comp_noise rms", "V", [0.1e-3, 1e-3, 5e-3], lambda v: ideal_base(comp_noise=v / VREF)),
        ("tau_in", "s", [1e-9, 10e-9, 45e-9], lambda v: ideal_base(tau_in=v)),
        ("tau_ref (cd_ref 5 pF pad)", "s", [2.5e-9, 10e-9, 45e-9], lambda v: ideal_base(tau_ref=v, cd_ref=5e-12)),
        ("reset residue r on x1", "-", [1e-2, 1e-3, 1e-4], lambda v: ideal_base(x1_offset=v * X1MAX_V)),
    ]
    for f in (0.25e6, 2e6):
        sw.append((f"leakage at fs {f/1e6:g} MHz", "A", [10e-12, 100e-12, 1e-9],
                   (lambda f_: lambda v: ideal_base(vres=leak_offset(v, f_, CS), fs=f_, chop=False))(f)))
    return sw


def run_sweeps():
    rows = []
    base = metrics(ideal_base())
    rows.append({"sweep": "base (ideal OTA, switch kT/C only)", "unit": "", "value": None, **base})
    for name, unit, vals, mk in sweeps():
        for v in vals:
            r = metrics(mk(v))
            rows.append({"sweep": name, "unit": unit, "value": list(v) if isinstance(v, tuple) else v, **r})
            print(f"sweep {name} {v}: " + " ".join(f"{k}={x:.3g}" for k, x in r.items()), flush=True)
    return rows


# ----------------------------------------------------------------------------------------- theory checks
def rel_ok(meas, theory, tol=0.10, floor=0.0):
    return bool(np.isfinite(meas) and abs(meas - theory) <= max(tol * abs(theory), floor))


def x1init_sim(u, N, x0):
    """Ideal order-2 loop (iadc ordering) with an initial x1 = x0 (normalised); the reset-residue model."""
    x1 = np.full_like(u, x0)
    x2 = np.zeros_like(u)
    S = np.zeros_like(u)
    sumS = np.zeros_like(u)
    for _ in range(N):
        y = np.where(x2 >= 0, 1.0, -1.0)
        sumS += S
        S += y
        x1, x2 = x1 + C1 * (u - y), x2 + C2 * (x1 - KK * y)
    return (sumS + KK / C1 * S) / (N * (N - 1) / 2)


def ktc_conv_rms_uv(cs, N=4096, B=512):
    p = ideal_base(cs=cs, N=N, sys_chop=False, chop=False)
    u = -0.5 + (np.arange(B) + 0.5) / B
    d = m.convert(p, u, rng=np.random.default_rng(5)) - m.convert(m.with_(p, ktc_on=False), u)
    return float(np.std(d)) * VREF * 1e6


def ktc_theory_uv(cs, N, events=2, T=300.0):
    """Per-cycle differential kT/C: 2kT/Cs per sampling event, `events` events; weighted by w=N-1-n."""
    sig = math.sqrt(events * 2 * K_B * T / cs)
    w = N - 1 - np.arange(N, dtype=float)
    return sig * math.sqrt(np.sum(w * w)) / np.sum(w) * 1e6


def theory_checks(quick=False):
    """List of (name, ok, text). Each expected value comes from s2_theory / SPEC / charge conservation."""
    out = []

    def rec(name, ok, text):
        out.append((name, bool(ok), text))

    N = N_PREC
    p = ideal_base(vos=9e-3, lf_gain=LF, sys_chop=False)
    meas = offset_uv(p, False)
    thy = th.predict(2, N, "ota", 9e-3, 0.0, LF) * 1e6
    rec("vos1_chop", rel_ok(meas, thy), f"lf*Vos1/(N-1), ota chop, sys off, lf 9.3, N 4096: model {meas:.2f} vs theory {thy:.2f} uV")
    pn = m.with_(p, chop=False)
    meas = offset_uv(pn, False)
    thy = th.predict(2, N, "none", 9e-3, 0.0, LF) * 1e6
    rec("vos1_nochop", rel_ok(meas, thy), f"lf*Vos1, no chop, sys off: model {meas:.1f} vs theory {thy:.1f} uV")
    p2 = ideal_base(vos2=9e-3, sys_chop=False)
    meas = offset_uv(p2, False)
    thy = th.e2_error(N, C1, 9e-3) * 1e6
    rec("vos2", rel_ok(meas, thy), f"2*Vos2/(c1(N-1)), sys off: model {meas:.2f} vs theory {thy:.2f} uV")
    for tag, pp in (("vos1", p), ("vos2", p2), ("vres", ideal_base(vres=5e-6, lf_gain=LF))):
        res = offset_uv(m.with_(pp, sys_chop=True), True)
        rec(f"sys_cancel_{tag}", abs(res) <= 0.5, f"sys pair cancels {tag}: residual {res:.3f} uV (theory 0, tol 0.5)")
    # kT/C ~ 1/sqrt(Cs)
    cs_set = (0.0625e-12, 0.125e-12, 0.25e-12)
    r = [ktc_conv_rms_uv(c) for c in cs_set]
    rec("ktc_scaling", rel_ok(r[0] / r[2], 2.0, 0.10), f"kT/C noise ratio Cs 0.0625/0.25 pF = {r[0]/r[2]:.3f} vs sqrt(4) = 2 (10 %)")
    for c, rv in zip(cs_set, r):
        t = ktc_theory_uv(c, N)
        rec(f"ktc_abs_{c*1e12:g}pF", rel_ok(rv, t, 0.15), f"kT/C per-conversion rms Cs {c*1e12:g} pF: model {rv:.2f} vs 2kT/C-weighted theory {t:.2f} uV (15 %)")
    # reset residue
    Nr = 1024 if quick else 4096          # N >= 1024: the quantization scatter of a paired difference is <~ 2 % there
    u = -0.5 + (np.arange(512) + 0.5) / 512
    for r_ in ((1e-2,) if quick else (1e-2, 3e-3)):
        x0 = r_ * X1MAX_V / VREF
        sim = float(np.mean(x1init_sim(u, Nr, x0) - x1init_sim(u, Nr, 0.0))) * VREF * 1e6
        thy = 2 * r_ * X1MAX_V / (C1 * (Nr - 1)) * 1e6
        mod = offset_uv(ideal_base(x1_offset=r_ * X1MAX_V, N=Nr, sys_chop=False), False)
        rec(f"reset_{r_:g}", rel_ok(sim, thy, 0.05) and rel_ok(mod, thy, 0.10),
            f"reset residue r {r_:g}, N {Nr}: x1-init sim {sim:.2f}, model x1_offset {mod:.2f} vs 2*r*x1max/(c1(N-1)) = {thy:.2f} uV")
    # leakage
    thy = None
    for f in (0.25e6, 2e6):
        i = 100e-12
        thy = i / (f * CS) * 1e6
        pl = ideal_base(vres=leak_offset(i, f, CS), fs=f, chop=False, sys_chop=False, lf_gain=1.0)
        meas = offset_uv(pl, False)
        res = offset_uv(m.with_(pl, sys_chop=True), True)
        rec(f"leak_{f/1e6:g}MHz", rel_ok(meas, thy, 0.05) and abs(res) <= 0.5,
            f"leakage 100 pA, fs {f/1e6:g} MHz: model {meas:.1f} vs I/(fs*Cs) = {thy:.1f} uV; sys-pair residual {res:.3f} uV (ASSUMES signal-independent)")
    rec("nonvac_compare", (not rel_ok(1.5 * thy, thy)) and (not rel_ok(0.5 * thy, thy)) and (not rel_ok(float('nan'), thy)),
        "comparison rejects theory x1.5, x0.5 and NaN")
    return out


# ----------------------------------------------------------------------------------------- hand calcs
CP_RATIO = 0.3
T_HALF = 0.45 / FS


def hand_calcs():
    cp = CP_RATIO * CS
    beta1 = 4e-12 / (4e-12 + CS + cp)
    cs2, cint2 = 0.5e-12, 1e-12
    beta2 = cint2 / (cint2 + cs2 + CP_RATIO * cs2)
    cl1 = cs2 + 0.2e-12 + (CS + cp) * 4e-12 / (CS + cp + 4e-12)       # OTA1 load: Cs2 + 0.2 pF wiring + series(Cs+Cp, Cint1)
    step = C1 * 2 * VREF                                           # max one-cycle diff output step [V]
    sr_min = step / (0.2 * T_HALF)                                  # slew in 20 % of t_half
    gbw_lin = 1 / (2 * math.pi * beta1 * 0.2 * T_HALF)             # tau <= 0.2 t_half
    gbw_full = 1 / (2 * math.pi * beta1 * T_HALF / 10)             # 10 tau in t_half
    kT = K_B * 300
    rows = {"beta1": beta1, "beta2": beta2, "cl1_pF": cl1 * 1e12, "step_diff_V": step,
            "sr_min_V_per_us": sr_min / 1e6, "gbw_lin_MHz": gbw_lin / 1e6, "gbw_full_MHz": gbw_full / 1e6}
    gm_p = {}
    for en in (7, 10, 14):
        gm = 4 * kT * (2 * (2 / 3)) * 1.5 / (en * 1e-9) ** 2        # gamma 2/3, gm_load/gm_in = 0.5
        itail = 2 * gm / 15.0                                       # gm/Id = 15 per input device, 2 devices
        gm_p[en] = {"gm_uS": gm * 1e6, "i_tail_uA": itail * 1e6, "i_ota1_uA": 2 * itail * 1e6 * 1.1,
                    "gbw_MHz": gm / (2 * math.pi * cl1) / 1e6,
                    "sr_diff_V_per_us": itail / cl1 / 1e6}
    rows["gm_noise"] = gm_p
    gm2 = 2 * math.pi * 10e6 * 0.3e-12                              # OTA2 at GBW 10 MHz, 0.3 pF load (comparator + wiring)
    i_ota2 = 2 * (gm2 / 15.0) * 2 * 1.1 * 1e6
    other = {"ota2_uA": i_ota2, "comparator_uA": 6.0, "bias_cmfb_refs_uA": 20.0}
    for en, d in gm_p.items():
        d["total_uA"] = d["i_ota1_uA"] + sum(other.values())
    rows["power_other"] = other
    # TG on-resistance, ss/-40/3.0 V, mid-range input (both devices weakest): W/L 20/0.5 each. ASSUMED device numbers.
    vt_n, vt_p, mun, mup = 0.95, 1.05, 45e-6, 16e-6
    vov = 3.0 / 2 - 0.5 * (vt_n + vt_p)
    ron_n = 1 / (mun * 40 * max(vov, 0.05))
    ron_p = 1 / (mup * 40 * max(vov, 0.05))
    rows["ron_ohm"] = 1 / (1 / ron_n + 1 / ron_p)
    rows["vov_V"] = vov
    c_node = 5e-12 + CS
    rows["tau_in_ns_rsrc0"] = (rows["ron_ohm"] + 500) * c_node * 1e9
    rows["rsrc_max_tau10_ohm"] = 10e-9 / c_node - 500 - rows["ron_ohm"]
    rows["rsrc_max_tau45_ohm"] = 45e-9 / c_node - 500 - rows["ron_ohm"]
    rows["rsrc_max_tau18_ohm"] = 18.75e-9 / c_node - 500 - rows["ron_ohm"]
    t4 = 0.45 / 4e6
    rows["fast_4MHz"] = {"t_half_ns": t4 * 1e9, "gbw_lin_MHz": 1 / (2 * math.pi * beta1 * 0.2 * t4) / 1e6,
                         "gbw_full_MHz": 1 / (2 * math.pi * beta1 * t4 / 10) / 1e6, "sr_min_V_per_us": step / (0.2 * t4) / 1e6}
    rows["tau_in_budget_t12_ns"] = T_HALF / 12 * 1e9
    rows["t_reset_15tau_ns"] = 15 * 1e3 * 4e-12 * 1e9
    rows["r_after_15tau"] = math.exp(-15)
    rows["tau_needed_for_r1e-4"] = math.log(1e4)
    opts = {}
    w = N_PREC - 1 - np.arange(N_PREC, dtype=float)
    for cs2_, c2_ in ((0.25e-12, 0.5), (0.5e-12, 0.5), (1e-12, 0.5), (1e-12, 0.25), (0.5e-12, 0.25)):
        ci = cs2_ / c2_
        sig = math.sqrt(2 * 2 * K_B * 300 / cs2_)
        u_err = math.sqrt(N_PREC) * sig / (C1 * np.sum(w))          # white e2 per cycle, unit weights
        opts[f"Cs2 {cs2_*1e12:g} / Cint2 {ci*1e12:g} pF, c2 {c2_}"] = {
            "ktc2_in_uV_per_conv": u_err * 1e6, "mim_um2_diff_x1.5": 2 * (cs2_ + ci) / 2e-15 * 1.5,
            "x2_step_V": c2_ * KK * VREF}
    rows["stage2"] = opts
    caps = {"Cs1": 0.5e-12, "Cint1": 4e-12, "Cs2": 0.5e-12, "Cint2": 1e-12}
    rows["mim_um2"] = {k: 2 * v / 2e-15 * 1.5 for k, v in caps.items()}
    rows["mim_total_um2"] = sum(rows["mim_um2"].values())
    rows["tile_um2"] = 334 * 225
    rows["kick_gain_ppm_per_mV"] = 2 * (1e-3 / (C2 * VREF)) / (C1 * N_PREC) * 1e6
    rows["x2_min_step_V"] = C2 * KK * VREF
    return rows


# ----------------------------------------------------------------------------------------- allocation
def contrib_noise(n, nbase):
    return math.sqrt(max(0.0, n * n - nbase * nbase))


@lru_cache(maxsize=None)
def _base():
    return metrics(ideal_base()), quant_floor_ppm(ideal_base(a0_db=np.inf))


def alloc_rows(spec=None):
    """Rows: dict(block, metric, share, spec, value, margin, kind). Values come from fresh model runs at the spec
    value (one block active, others ideal) or from hand calcs; shares are the allocation."""
    s = dict(SPEC_BLK)
    s.update(spec or {})
    hc = hand_calcs()
    base, floor = _base()
    nb = base["n15"]
    rows = []

    def add(block, metric, share, spec_txt, value, kind="model"):
        rows.append({"block": block, "metric": metric, "share": share, "spec": spec_txt, "value": float(value),
                     "margin": (share / value) if value > 0 else math.inf, "kind": kind})

    # --- noise (RSS)
    add("sampling switches kT/C (Cs 0.5 pF)", "noise_uv", 1.2, "Cs 0.5 pF, 2 events", nb)
    # same random draws in base and excess runs (ktc scales), so the RSS difference is clean
    n_en = noise_uv(ideal_base(ktc_excess=excess_from_en(s["ota_en"])), 15, N_PREC)
    add("OTA1 thermal", "noise_uv", 1.2, f"en <= {s['ota_en']:g} nV/rtHz", contrib_noise(n_en, nb))
    # 1/f and comparator noise measured alone (switch kT/C off): independent sources add in quadrature
    n_f = noise_uv(ideal_base(ktc_on=False, flicker_on=True, ota_fc=s["fc"], lf_gain=s["lf"], vres=s["vres"]), 15, N_PREC)
    add("OTA1 1/f + chopper residue", "noise_uv", 1.0, f"fc <= {s['fc']/1e3:g} kHz, lf <= {s['lf']:g}, vres <= {s['vres']*1e6:g} uV", n_f)
    n_cn = noise_uv(ideal_base(ktc_on=False, comp_noise=s["comp_noise"] / VREF), 15, N_PREC)
    add("comparator noise", "noise_uv", 0.3, f"<= {s['comp_noise']*1e3:g} mV rms (input-ref)", n_cn)
    sig2 = math.sqrt(2 * 2 * K_B * 300 / 0.5e-12) * 1.5
    w = N_PREC - 1 - np.arange(N_PREC, dtype=float)
    n2 = math.sqrt(N_PREC) * sig2 / (C1 * np.sum(w)) * 1e6 / math.sqrt(34 / 2)    # per conversion -> 17 pairs averaged
    add("OTA2 + stage-2 kT/C (hand)", "noise_uv", 0.3, "Cs2 0.5 pF, OTA2 same excess", n2, "hand")
    add("reserve: ref path, substrate, chopper spikes", "noise_uv", 1.0, "unmodelled; measure in C10/V", 0.0, "reserve")
    # --- INL
    m_o = metrics(ideal_base(a0_db=s["a0_db"], a0_drop=s["a0_drop"], vlin_diff=s["vlin"]), noise=False)
    add("OTA1+OTA2 gain and swing linearity", "inl_ppm", 8.0,
        f"A >= {s['a0_db']:g} dB, <= {s['a0_drop']*100:g} % drop at |Vout,diff| <= {s['vlin']:g} V", m_o["inl"])
    m_ti = metrics(ideal_base(tau_in=s["tau_in"]), noise=False)
    add("input sampling settling", "inl_ppm", 2.0, f"tau_in <= {s['tau_in']*1e9:g} ns", m_ti["inl"])
    m_tr = metrics(ideal_base(tau_ref=s["tau_ref"], cd_ref=5e-12), noise=False)
    add("reference path settling", "inl_ppm", 2.0, f"tau_ref <= {s['tau_ref']*1e9:g} ns (500 ohm + 5 pF pad)", m_tr["inl"])
    m_co = metrics(ideal_base(comp_offset=s["comp_off"] / VREF, c2=0.5), noise=False)
    add("comparator offset", "inl_ppm", 1.0, f"<= {s['comp_off']*1e3:g} mV", m_co["inl"])
    add("quantization floor (N 4096, raw accumulators)", "inl_ppm", 1.0, "N = 4096", floor)
    m_rx = metrics(ideal_base(r_ext_ref=s["r_ext"]), noise=False)
    add("reference current x external R (u^3)", "inl_ppm", 2.0, f"R_ext <= {s['r_ext']:g} ohm per pin, >= 100 nF decap (review S3-7a)", m_rx["inl"])
    add("reserve: MIM VCC, charge-inj. nonlinearity, substrate", "inl_ppm", 4.0, "unmodelled", 0.0, "reserve")
    # --- offset after sys chop (|residual|, uV)
    m_v1 = metrics(ideal_base(vos=s["vos"], vres=s["vres"], lf_gain=s["lf"]), noise=False)
    m_v2 = metrics(ideal_base(vos2=s["vos2"]), noise=False)
    m_cof = metrics(ideal_base(comp_offset=s["comp_off"] / VREF), noise=False)
    mod_res = abs(m_v1["off_sys"]) + abs(m_v2["off_sys"]) + abs(m_cof["off_sys"])
    add("Vos1, Vos2, vres, comp offset (model residual in sys pair)", "offset_uv", 1.0,
        f"Vos {s['vos']*1e3:g} mV, vres {s['vres']*1e6:g} uV, comp {s['comp_off']*1e3:g} mV", mod_res)
    m_rr = metrics(ideal_base(x1_offset=s["r_reset"] * X1MAX_V, sys_chop=False), noise=False)
    add("reset residue r (worst case, does NOT cancel)", "offset_uv", 1.0, f"r <= {s['r_reset']:g}, reset window >= 2 clock cycles (1 us at 2 MHz)",
        abs(m_rr["off_nosys"]))
    leak = leak_offset(s["i_leak"], 0.25e6, CS) * 1e6 * RHO_LEAK
    add("virtual-ground leakage (hand, rho 0.1 % ASSUMED)", "offset_uv", 1.0,
        f"I_leak <= {s['i_leak']*1e12:g} pA at 125 C, fs 0.25 MHz", leak, "hand")
    add("reserve: pair drift, chopper charge injection", "offset_uv", 2.0, "unmodelled; +--+ ordering helps", 0.0, "reserve")
    # --- gain error (ppm, absolute)
    add("finite A0 and swing (model)", "gain_ppm", 300.0, f"A >= {s['a0_db']:g} dB", abs(m_o["gain"]))
    ms = metrics(ideal_base(tau_in=s["tau_in"], tau_ref=s["tau_ref"], cd_ref=5e-12), noise=False)
    add("input + reference settling (model)", "gain_ppm", 500.0, "tau_in, tau_ref as above", abs(ms["gain"]))
    # with shared Cs only k/c1 enters the reconstruction: gain error = 2 k /(c1 N) * (k/c1 mismatch)   [theory]
    kc1 = 2 * KK / (C1 * N_PREC) * s["dcs_ratio"] * 1e6
    add("k/c1 ratio mismatch (hand, shared Cs)", "gain_ppm", 50.0, f"k/c1 3 sigma mismatch <= {s['dcs_ratio']*100:g} % (PDK, review S3-6)", kc1, "hand")
    add("reserve: pad/bond droop, 5 mV kickback", "gain_ppm", 4150.0, "calibratable", hc["kick_gain_ppm_per_mV"] * 5, "hand")
    return rows, {"nom_base": base, "floor": floor}


def combine(rows):
    """Sum per metric: noise RSS, others linear. Returns dict metric -> (sum_share, sum_value)."""
    tot = {}
    for mtr in BUDGET:
        rs = [r for r in rows if r["metric"] == mtr]
        if mtr == "noise_uv":
            tot[mtr] = (math.sqrt(sum(r["share"] ** 2 for r in rs)), math.sqrt(sum(r["value"] ** 2 for r in rs)))
        else:
            tot[mtr] = (sum(r["share"] for r in rs), sum(r["value"] for r in rs))
    return tot


def verdict(rows, joint, extra_fail=()):
    fails = list(extra_fail)
    for r in rows:
        if r["share"] > 0 and np.isfinite(r["value"]) and abs(r["value"] - r["share"]) <= 1e-9 * r["share"]:
            fails.append(f"row '{r['block']}' [{r['metric']}]: value == share ({r['share']:g}): circular, not a measurement")
        if not (np.isfinite(r["value"]) and r["margin"] >= 1.0):
            fails.append(f"row '{r['block']}' [{r['metric']}]: value {r['value']:.3g} vs share {r['share']:g} (margin {r['margin']:.2f})")
    for mtr, (ssh, _) in combine(rows).items():
        if ssh > BUDGET[mtr] + 1e-9:
            fails.append(f"allocation {mtr}: shares sum {ssh:.3g} > budget {BUDGET[mtr]:g}")
    for key, mtr in (("n15", "noise_uv"), ("inl", "inl_ppm"), ("off_sys", "offset_uv"), ("gain", "gain_ppm")):
        v = abs(joint[key])
        if not (np.isfinite(v) and v <= BUDGET[mtr]):
            fails.append(f"joint run {key} = {v:.3g} > budget {BUDGET[mtr]:g} [{mtr}]")
    return fails


# ----------------------------------------------------------------------------------------- report
def fmt_table(head, body):
    s = "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n"
    for r in body:
        s += "| " + " | ".join(r) + " |\n"
    return s


def g(x, nd=3):
    return "n/a" if x is None else (f"{x:.{nd}g}" if isinstance(x, (int, float)) else str(x))


def write_report(out, sw, checks, hc, rows, joint, fails):
    base = sw[0]
    L = ["# S3: error budget and per-block specs at the decided design point (WO-05)", ""]
    L += ["Command: `python3 -m model.studies.s3_budget --out /home/mempool/regr/tt/WO-05/run`", ""]
    L += ["## Design point", "",
          "Order 2 CIFB, c1 0.125, c2 0.5, k 0.5; VREF 2.048 V (REF+ ua2, REF- ua3, 500 ohm + 5 pF pads); Cs1 0.5 pF, Cint1 4 pF, shared Cs; "
          "fs 2 MHz (0.25-2 precision, 4 MHz fast); precision N 4096 with K sys-chop pairs, ota+sys chop; fast N 64/256/1024; "
          "A0 >= 80 dB, vlin in volts; Vos1 = Vos2 = 9 mV (3 sigma); overload 1.0-1.1 VREF. "
          "Sweeps: one parameter at a time on an otherwise ideal loop (switch kT/C only, shared Cs, chop+sys on). "
          "Noise: rms of 64 outputs at 15 SPS (statistical error ~9 %) (N 4096, K 34) and 240 SPS (N 1024, K 8). INL: endpoint, +-0.9 FS, N 4096, residue-corrected, ppm of FSR. "
          "Offset: paired difference (offset sources on minus zeroed), noise-free, mean over 512 DC points; `sys` = pair of opposite input polarities. "
          "lf = 9.3 is the pessimistic input-referral bound (SPEC 2.2 nominal ~1).", ""]
    L += ["## Theory checks", "", "```"]
    for n, ok, t in checks:
        L.append(f"{'PASS' if ok else 'FAIL'} {t}")
    L += ["```", ""]
    L += ["## Sensitivity sweeps", "",
          f"Base (ideal OTA, switch kT/C only): noise {g(base['n15'])} uV @15, {g(base['n240'])} uV @240, INL {g(base['inl'])} ppm, "
          f"gain {g(base['gain'])} ppm.", ""]
    body = []
    for r in sw[1:]:
        v = r["value"]
        vs = ", ".join(g(x) for x in v) if isinstance(v, list) else g(v)
        body.append([r["sweep"], vs, g(r["n15"]), g(r["n240"]), g(r["inl"]), g(r["gain"]), g(r["off_nosys"]), g(r["off_sys"])])
    L.append(fmt_table(["sweep", "value", "noise@15 uV", "noise@240 uV", "INL ppm", "gain err ppm", "offset sys-off uV", "offset sys-pair uV"], body))
    L += ["Notes: OTA thermal mapping `ktc_excess = 1 + 0.5 (en/6.9)^2` (calibration comment in iadc.py: 0.5 = OTA at 6.9 nV/rtHz, scaled by noise gain 9.3/5.3). "
          "Leakage rows inject the offset I/(fs Cs) as a constant input-referred offset; they cancel in the sys pair only if the leakage is signal-independent (ASSUMPTION; "
          "bottom-plate virtual ground sits at a fixed voltage, but junction leakage varies with temperature drift between sub-conversions). "
          "Reset-residue rows inject x1[0] = r x1max, equivalent to a constant stage-2 offset (verified against a local x1-init simulation); x1max = 1.22 V differential (S1). "
          "Reset residue tracks the previous conversion's final x1, so it is not guaranteed to cancel in a sys pair and is budgeted as non-cancelling.", ""]
    L += ["## Allocation table", "", "Noise: RSS of values and of shares. INL, offset, gain: linear sums. Margin = share / value (>= 1 required).", ""]
    body = [[r["block"], r["metric"], g(r["share"]), r["spec"], g(r["value"]), (">1000" if r["margin"] > 1000 else f"{r['margin']:.2f}") if np.isfinite(r["margin"]) else "inf", r["kind"]] for r in rows]
    L.append(fmt_table(["block", "metric", "share", "per-block spec", "measured/hand value", "margin", "kind"], body))
    tot = combine(rows)
    L.append(fmt_table(["metric", "budget", "sum of shares", "sum of values"], [[k, g(BUDGET[k]), g(v[0]), g(v[1])] for k, v in tot.items()]))
    L += ["Joint run (all blocks at spec together): " + ", ".join(f"{k} {g(v)}" for k, v in joint.items()), ""]
    L += findings(sw, hc)
    L += stage2_and_power_sections(hc)
    L += spec_table(hc, rows)
    L += ["## Hand calculations (marked hand; not model results)", "", "```", json.dumps(hc, indent=1, default=float), "```", ""]
    L += ["## Verdict", "", "ACCEPT" if not fails else "REJECT", ""] + [f"- {f}" for f in fails]
    (out / "s3_budget.md").write_text("\n".join(L) + "\n")


def _row(sw, name, value):
    for r in sw:
        if r["sweep"] == name and r["value"] == value:
            return r
    raise KeyError((name, value))


def findings(sw, hc):
    a = "A0 x a0_drop (vlin 2 V)"
    v = "vlin_diff (A0 80, drop 0.9)"
    en = "OTA thermal en"
    L = ["## Findings from the sweeps", "",
         f"- OTA linearity: INL {g(_row(sw, a, [80, 0.9])['inl'])} ppm at 80 dB / 90 % drop / 2 V (share 8 ppm, margin {8/_row(sw, a, [80, 0.9])['inl']:.1f}). "
         f"75 dB / 0.9 gives {g(_row(sw, a, [75, 0.9])['inl'])} ppm (still inside the share), 70 dB / 0.9 gives {g(_row(sw, a, [70, 0.9])['inl'])} ppm (outside). "
         f"The linear range matters more than A0: vlin 1.5 V gives {g(_row(sw, v, 1.5)['inl'])} ppm, 1.0 V gives {g(_row(sw, v, 1.0)['inl'])} ppm, 0.8 V gives {g(_row(sw, v, 0.8)['inl'])} ppm. "
         "Spec the swing in volts (m4): the x1 peak is 1.22 V diff, so 2.0 V keeps the gain-drop region away from the signal.",
         f"- OTA thermal noise: total noise @15 SPS {g(_row(sw, en, 5)['n15'])}/{g(_row(sw, en, 7)['n15'])}/{g(_row(sw, en, 10)['n15'])}/{g(_row(sw, en, 14)['n15'])}/{g(_row(sw, en, 20)['n15'])} uV for 5/7/10/14/20 nV/rtHz "
         "(12 % of statistical scatter). Even 20 nV/rtHz stays inside the 2.5 uV budget alone; the limit is set by current (see power table), not by noise.",
         "- Sampling kT/C of the switches at Cs 0.5 pF is the floor (0.56 uV @15 SPS) and not reducible without a larger Cs.",
         "- tau_in and tau_ref (shared Cs): INL stays below 0.01 ppm and gain error below 17 ppm up to 45 ns; the shared-Cs error is a gain error (review F6/m6). "
         "The binding limit on the input is the pad/source recharge (hand row), not the model's tau.",
         "- Comparator: noise up to 5 mV rms and offset up to 50 mV produce < 0.2 uV noise and < 0.2 uV offset. The comparator is not budget-limiting; "
         "its offset only matters through x2 swing (c2 0.25 makes 50 mV 0.2 uV instead of 0.02 uV).",
         "- The model's constant offsets (Vos1, Vos2, vres, comparator offset, reset residue, leakage) cancel exactly in a sys pair (residual 0.000 uV, numerical). "
         "The offset budget is therefore carried by the non-cancelling mechanisms: reset residue (worst case), leakage fraction (assumed) and pair drift (reserve).",
         f"- Leakage raw offsets I/(fs Cs): 100 pA gives {g(_row(sw, 'leakage at fs 0.25 MHz', 100e-12)['off_nosys'])} uV at 0.25 MHz and {g(_row(sw, 'leakage at fs 2 MHz', 100e-12)['off_nosys'])} uV at 2 MHz; "
         "1 nA gives 8 mV at 0.25 MHz (1 mV at 2 MHz). Without cancellation the leakage spec would be ~1 pA.",
         f"- Raw (sys-off) offsets at the SPEC values: lf*Vos1/(N-1) {g(9.3*9e-3/4095*1e6)} uV, 2*Vos2/(c1(N-1)) 35.2 uV, vres 5 uV x lf 9.3 = 46 uV: characterization-only modes carry these (SPEC 3.6).",
         f"- 4 MHz fast mode (hand): t_half {g(hc['fast_4MHz']['t_half_ns'])} ns needs GBW {g(hc['fast_4MHz']['gbw_lin_MHz'])}-{g(hc['fast_4MHz']['gbw_full_MHz'])} MHz and SR >= {g(hc['fast_4MHz']['sr_min_V_per_us'])} V/us; "
         "both are met by the noise-set OTA1 design (gm/GBW/SR columns in the power table).", ""]
    return L


def stage2_and_power_sections(hc):
    L = ["## Stage-2 sizing (item 3)", "",
         "Stage-2 white sampling error referred to the input is u_err = sqrt(N) sigma / (c1 sum w) (unit weights, because it enters x2 per cycle), "
         "with sigma = sqrt(2 events * 2kT/Cs2). (a) kT/C of stage 2 divided by the stage-1 gain is negligible at any plausible Cs2; "
         "(b) area is the only cost of larger Cs2; (c) x2 swing and comparator: c2 0.5 gives a feedback step c2 k VREF = 0.512 V (c2 0.25: 0.256 V), "
         "see the comp_offset (c2 0.5) and (c2 0.25) sweeps.", ""]
    body = [[k, g(v["ktc2_in_uV_per_conv"]), g(v["mim_um2_diff_x1.5"]), g(v["x2_step_V"])] for k, v in hc["stage2"].items()]
    L.append(fmt_table(["option", "stage-2 kT/C at input [uV/conv]", "MIM um2 (diff, x1.5)", "x2 min step [V]"], body))
    L += ["Proposal: **Cs2 0.5 pF, Cint2 1 pF (c2 0.5)**. The kT/C term is orders of magnitude under the stage-1 floor, so the choice is set by area, "
          "by keeping Cs2 well above the OTA1 load parasitics (0.25 pF would be dominated by wiring) and by matching. "
          "c2 = 0.25 (Cs2 0.5 / Cint2 2 pF) is allowed if the comparator offset sweep for c2 0.25 stays inside its share; it costs 1 pF more MIM per side and "
          "halves the x2 swing, so it is an option for OTA2 swing only (review E3: no INL benefit).", ""]
    L += ["## Area and power estimate (item 4b)", "", "All hand estimates, no simulation.", "",
          f"MIM (2 fF/um2, x1.5 overhead, differential): " + ", ".join(f"{k} {g(v)} um2" for k, v in hc["mim_um2"].items()) +
          f"; total {g(hc['mim_total_um2'])} um2 = {100*hc['mim_total_um2']/hc['tile_um2']:.1f} % of the 2x2 tile ({g(hc['tile_um2'])} um2).", ""]
    body = [[f"{en} nV/rtHz", g(d["gm_uS"]), g(d["i_tail_uA"]), g(d["i_ota1_uA"]), g(d["gbw_MHz"]), g(d["sr_diff_V_per_us"]), g(d["total_uA"]),
             "OK" if d["total_uA"] <= 200 else "OVER 200 uA"] for en, d in hc["gm_noise"].items()]
    L.append(fmt_table(["OTA1 en", "gm needed [uS]", "input tail [uA]", "OTA1 total [uA] (fold x2, +10 %)", "GBW at gm, CL1 [MHz]", "SR [V/us]", "chip analog total [uA]", "vs 200 uA"], body))
    L += [f"Assumptions: thermal en^2 = 4kT (2 gamma/gm)(1 + gm_load/gm_in), gamma 2/3, gm_load/gm_in 0.5; gm/Id 15 /V; folded cascode doubles the branch current. "
          f"Other consumers: {hc['power_other']}. Noise, not GBW or slew, sets the OTA1 current: GBW needed {g(hc['gbw_lin_MHz'])} MHz (tau <= 0.2 t_half) to {g(hc['gbw_full_MHz'])} MHz "
          f"(10 tau), slew needed {g(hc['sr_min_V_per_us'])} V/us diff (max step {g(hc['step_diff_V'])} V in 0.2 t_half), beta1 = {g(hc['beta1'])}, OTA1 load {g(hc['cl1_pF'])} pF. "
          "The 7 nV/rtHz inherited from the continuous-time spec does not fit the 200 uA budget with this estimate; 10-14 nV/rtHz does (review E2).", ""]
    return L


def spec_table(hc, rows):
    s = SPEC_BLK
    v = {r["block"]: r for r in rows}
    L = ["## Per-block spec table (paste-ready for SPEC section 3)", "",
         "All entries are limits at every corner of SPEC section 6. Margin = allocation share / value at the spec.", ""]
    T = [
        ["OTA1 (and OTA2 until separated)", "DC gain / linearity", f"A >= {s['a0_db']:g} dB with <= {s['a0_drop']*100:g} % gain drop at |Vout,diff| <= {s['vlin']:g} V", "INL share 8 ppm"],
        ["OTA1", "input white noise", f"<= {s['ota_en']:g} nV/rtHz (mapping in sweeps)", "noise share 1.2 uV"],
        ["OTA1", "1/f corner (with chop + sys)", f"<= {s['fc']/1e3:g} kHz, residual chopper offset vres <= {s['vres']*1e6:g} uV", "noise share 1.0 uV"],
        ["OTA1", "GBW / slew (hand)", f">= 10 MHz (needs {g(hc['gbw_lin_MHz'])}-{g(hc['gbw_full_MHz'])}), SR >= {max(10, math.ceil(hc['sr_min_V_per_us']))} V/us diff at beta {g(hc['beta1'])}, CL {g(hc['cl1_pF'])} pF", "hand"],
        ["OTA1/OTA2", "input offset", f"<= {s['vos']*1e3:g} mV (3 sigma); cancels with sys chop (constant)", "offset"],
        ["Comparator", "offset", f"<= {s['comp_off']*1e3:g} mV (3 sigma)", "INL share 1 ppm"],
        ["Comparator", "input-referred noise", f"<= {s['comp_noise']*1e3:g} mV rms (1 mV or less has no measurable effect: decisions never flip)", "noise share 0.3 uV"],
        ["Comparator", "decision time", f"< 0.3 t_half = {0.3*T_HALF*1e9:.0f} ns at 2 MHz ({0.3*0.45/4e6*1e9:.0f} ns at 4 MHz)", "hand"],
        ["Comparator", "kickback on x2", f"<= 1 % of the minimum x2 step ({0.01*hc['x2_min_step_V']*1e3:.1f} mV of {hc['x2_min_step_V']:.3f} V); "
                                         f"signal-dependent kickback gives {g(hc['kick_gain_ppm_per_mV'])} ppm gain error per mV", "hand"],
        ["Input switches", "settling tau_in (Ron + 500 ohm + source) x (5 pF + Cs)", f"<= {s['tau_in']*1e9:g} ns, i.e. source <= {max(0, hc['rsrc_max_tau18_ohm']):.0f} ohm (+ the 500 ohm pad); "
                                                                                      f"tau <= {g(hc['tau_in_budget_t12_ns'])} ns (t_half/12) is the outer limit", "INL share 2 ppm"],
        ["TG Ron (hand, ASSUMED device numbers)", "ss/-40 C/3.0 V mid-range", f"Ron ~ {hc['ron_ohm']:.0f} ohm at W/L 20/0.5 each; spec Ron <= 1.5 kohm", "hand"],
        ["Reference path", "tau_ref (500 ohm, 5 pF pad)", f"<= {s['tau_ref']*1e9:g} ns, pad path < 500 ohm and < 5 pF", "INL share 2 ppm"],
        ["Reset", "residue r on x1 at conversion start", f"<= {s['r_reset']:g}; reset window >= 2 clock cycles (1 us at 2 MHz; OTA slew + settle >= 250 ns, review S3-5); inter-conversion memory test", "offset share 1 uV"],
        ["Virtual ground", "leakage (125 C)", f"<= {s['i_leak']*1e12:g} pA total at the integrator input; non-cancelling fraction <= {RHO_LEAK*100:g} % (ASSUMED)", "offset share 1 uV"],
        ["Capacitors", "k/c1 ratio mismatch (shared Cs)", f"<= {s['dcs_ratio']*100:g} % (3 sigma, PDK) gives {v['k/c1 ratio mismatch (hand, shared Cs)']['value']:.1f} ppm gain error", "gain share 50 ppm"],
        ["Capacitors", "Cs+/Cs- mismatch (CMRR)", "<= 0.75 % (3 sigma); input-CM to differential conversion 0.75 %", "S4 MC"],
        ["Clock", "t_half / non-overlap", f"t_half {T_HALF*1e9:.0f} ns at 2 MHz, 0.45/fs after non-overlap; jitter-immune (SC)", "hand"],
    ]
    L.append(fmt_table(["block", "parameter", "spec", "budget line"], T))
    L += ["## Open risks (not modelled)", "",
          "- Substrate coupling from the decimator and clock drivers into the integrator virtual ground.",
          "- MIM voltage coefficient and bottom-plate parasitic (the sky130 MIM model has none): Cint VCC INL and Cp appear only in PEX/silicon.",
          "- Chopper charge-injection spikes and OTA settling with the chopper in place, chopping and parked.",
          "- OTA1 and OTA2 gain/linearity are applied together in the model (one `a0_db`); OTA2 cannot be relaxed on evidence until iadc.py has a separate a0_db2.",
          "- Leakage cancellation in sys pairs assumes a signal-independent leakage (rho = 0.1 % non-cancelling is an assumption).",
          "- Reset residue is budgeted as non-cancelling; a +--+ pair order and a >= 2-cycle reset window make it negligible.",
          "- Shared-Cs input: the source must settle a 5 pF pad plus Cs every half period; a 10 kohm source is not supported without an external buffer or decap.",
          "- Fast modes (N 64/256/1024, 4 MHz) have their own INL/noise targets and were not swept here.", ""]
    return L


# ----------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--nonvac", action="store_true")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.nonvac:
        bad = {"a0_db": 70.0, "a0_drop": 0.9, "vlin": 0.8}
        rows, _ = alloc_rows(bad)
        jm = metrics(spec_point(**bad), noise=False)
        fails = verdict(rows, {"n15": 0.0, "inl": jm["inl"], "off_sys": 0.0, "gain": 0.0})
        inl_fail = [f for f in fails if "[inl_ppm]" in f]
        verdict_txt = "REJECT" if inl_fail else "ACCEPT (nonvac FAILED to reject the broken OTA)"
        (out / "s3_nonvac.json").write_text(json.dumps({"broken": bad, "joint_inl_ppm": jm["inl"], "fails": fails, "verdict": verdict_txt}, indent=1, default=float))
        (out / "s3_nonvac.md").write_text("# S3 non-vacuity: broken OTA (A0 70 dB, drop 0.9, vlin 0.8 V)\n\n"
                                          f"Command: `python3 -m model.studies.s3_budget --out DIR --nonvac`\n\nJoint INL {jm['inl']:.3g} ppm.\n\n"
                                          + "\n".join(f"- {f}" for f in fails) + f"\n\n{verdict_txt}\n")
        if inl_fail:
            print("REJECT (nonvac: broken OTA 70 dB / drop 0.9 / vlin 0.8 V)")
            for f in inl_fail:
                print("  -", f)
            sys.exit(1)
        print("ACCEPT (nonvac FAILED to reject the broken OTA)")
        sys.exit(0)
    sj = out / "s3_sweeps.json"
    if a.reuse and sj.exists():
        sw = json.loads(sj.read_text())
    else:
        sw = run_sweeps()
        sj.write_text(json.dumps(sw, indent=1))
    checks = theory_checks(a.quick)
    for n, ok, t in checks:
        print(("PASS " if ok else "FAIL ") + t)
    hc = hand_calcs()
    rows, _ = alloc_rows()
    joint = metrics(spec_point())
    fails = verdict(rows, joint, [f"theory check '{n}' failed" for n, ok, _ in checks if not ok])
    if not all(np.isfinite(v) for r in sw for k, v in r.items() if isinstance(v, float)):
        fails.append("NaN/inf in sweep results")
    write_report(out, sw, checks, hc, rows, joint, fails)
    (out / "s3_budget.json").write_text(json.dumps({"budget": BUDGET, "spec": SPEC_BLK, "sweeps": sw, "checks": [list(c) for c in checks],
                                                    "hand": hc, "alloc": rows, "joint": joint, "fails": fails}, indent=1, default=float))
    if fails:
        print("REJECT")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("ACCEPT")


if __name__ == "__main__":
    main()
