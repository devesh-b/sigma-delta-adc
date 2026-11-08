"""S4: corner-aware tier-0 model (WO-06). SPEC 3.0 limits mapped onto the SPEC 6 PVT points.

Usage: python3 -m model.studies.s4_corners --out DIR [--nonvac] [--procs 4] [--quick]
  (default)  63 analog PVT points x fs {0.25, 2} MHz: noise @15/@240 SPS, INL (N 4096), sys-pair offset, gain error,
             inter-conversion memory; CMRR on eps_eff (D30/D33; Vin_cm 0.2/1.0/2.0 V, Cs mismatch) in the MC sets; MC (tt/27/3.3 x200, worst-INL and worst-offset point x50); fast mode (4 MHz) table.
             Prints ACCEPT/REJECT naming the failing point; exit 1 on REJECT.
  --nonvac   broken copies that must REJECT at the named point (A(1.4 V) = 60 dB at ss/125/3.0; reset r = 1e-2; sys chop off;
             Cs/100 for noise; tau_in 2 us for gain; CM term flipping with the input
             (must fail CMRR sys-on); Cs mismatch 3 % and dCp,top 3 sigma 2 fF, both in eps_eff (must fail CMRR sys-off)). Exit 1 if they all reject, 0 (loudly) if any one is NOT rejected.
  --quick    9 corner points and fewer MC draws (smoke test only; never used for the verdict)

NO TRANSISTOR DATA EXISTS YET. Every mapping below is an explicit assumption (MAPPING table, written into the report):
nominal values at tt/27/3.3, the SPEC 3.0 limit at the worst corner for that mechanism, linear in a 0..1 stress between.
Expected pass limits come from SPEC 3.0 / the S3 review, never from the code under test.
"""
import argparse
import itertools
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from design import params as dp
from model import iadc as m
from model.studies import s1_vref as s1
from model.studies import s3_budget as s3

VREF, C1, C2, KK, N_PREC, LF = s3.VREF, s3.C1, s3.C2, s3.KK, s3.N_PREC, s3.LF
X1MAX_V = s3.X1MAX_V

# ----------------------------------------------------------------------------------------- limits (SPEC 3.0 / review)
LIM = {"n15": 2.5,        # uV rms @15 SPS, u = 0 (budget, SPEC 3.0 header)
       "n240": 5.0,       # uV rms @240 SPS, u = 0 (D29, SPEC 3.0 user decisions); gated only where 240 SPS is reachable (fs >= N240_MIN_FS)
       "inl": 20.0,       # ppm FSR, N 4096 (budget)
       "off": 5.0,        # uV, sys-pair offset incl. non-cancelling terms (budget; 2 uV of it is unmodelled reserve)
       "gain": 5000.0,    # ppm (0.5 %)
       "mem": 0.5}        # uV, inter-conversion memory after +-FS then 0 (review S3-5)
N15_LIM_LOW_FS_HOT = 3.0   # D27: fs < 2 MHz and T > 85 C only (S4 worst 2.98 uV); everywhere else LIM["n15"]
N15_HOT_C = 85
CMRR_ON_DB, CMRR_OFF_DB = 100.0, 60.0   # D30 as amended by D32 (sys-off 60 dB, was 40): sys chop on / off, at tt/27 and the worst MC draws
VREF_CM = 1.0              # V, ASSUMED reference common mode (SPEC 3.0 does not fix it); dVcm = Vin_cm - VREF_CM
VIN_CMS = (0.2, 1.0, 2.0)  # V, input-CM axis (D30)
EPS_FOR_OFF_GATE = 10 ** (-CMRR_OFF_DB / 20)   # mismatch at which sys-off CMRR = eps^-1 just meets the gate (0.1 %)
EPS_3SIGMA = 0.0075        # Cs+/Cs- mismatch 0.75 % 3 sigma (SPEC 3.0)
# D33/D36: D12 residual eps_eff = ((Cp/Cs) eps_Cs - dCp/Cs)/(1+Cp/Cs) + eps_inj (sign '-' confirmed by WO-09 --cm2); MC signed per draw, corner rows RSS + |inj|. C4 allocation:
CP_TOP = 20e-15            # F per side (fixed allocation)
DCP_TOP_3S = 0.25e-15      # F, 3 sigma of the Cp_top difference
EPS_INJ = 2.8e-4           # shorting-TG injection split allocation (fixed, worst sign)
CMRR_OFF_TARGET_DB = 66.0  # design target (eps_eff <= 5e-4), informational margin only
CMRR_FLOOR_V = 1e-12       # residual below this is reported as the cap (240 dB at dVcm 1 V)
N240_MIN_FS = 2 * 240 * 1024     # 240 SPS needs a sys-chop pair of N 1024 conversions: fs >= 0.49 MHz; below that the spec is not reachable (not gated)
UNITS = {"n15": "uV", "n240": "uV", "inl": "ppm", "off": "uV", "gain": "ppm", "mem": "uV"}

# ----------------------------------------------------------------------------------------- mapping
NOM_TABLE = ((0.0, 90.0), (1.4, 88.0), (2.0, 85.0), (3.1, 75.0))      # ASSUMED typical OTA gain curve (dB vs |Vout,diff| V)
WORST_TABLE = ((0.0, 80.0), (1.4, 75.0), (2.0, 70.0), (3.1, 60.0))    # SPEC 3.0: A(0) >= 80, A >= 75 to 1.4 V; beyond 1.4 V ASSUMED
MAPPING = [
    # block, parameter, nominal tt/27/3.3, worst (SPEC 3.0), stress, worst reached at
    ("OTA1/OTA2", "A(v) table (dB, |Vout,diff| 0/1.4/2.0/3.1 V)", "90/88/85/75", "80/75/70/60 (80 and 75 = SPEC; 70, 60 assumed)", "s_gain", "ss/125/3.0"),
    ("OTA1", "en white (kT/C excess = 1 + 0.5 (en/6.9)^2)", "7 nV/rtHz", "10 nV/rtHz (SPEC: info only, sampled noise <= 250 uV)", "s_gain", "ss/125/3.0"),
    ("OTA1", "1/f corner fc", "400 kHz", "631 kHz (SPEC info)", "s_gain", "ss/125/3.0"),
    ("OTA1", "lf_gain (input referral of slow errors)", "9.3", "9.3 (pessimistic bound, as S3)", "const", "all"),
    ("OTA1, OTA2", "Vos1, Vos2", "+-9 mV", "+-9 mV 3 sigma, 4 sign combinations", "const (mismatch)", "all"),
    ("Comparator", "offset", "+-20 mV", "+-20 mV 3 sigma, sign combinations with Vos", "const (mismatch)", "all"),
    ("Comparator", "input-referred noise rms", "2 mV", "5 mV", "s_gain", "ss/125/3.0"),
    ("Input TG", "tau_in = (Ron + 500 ohm + R_src)(5 pF + Cs)", "8 ns", "18.75 ns", "s_speed", "ss/-40/3.0"),
    ("Reference", "tau_ref (500 ohm, 5 pF pad)", "3 ns", "10 ns", "s_speed", "ss/-40/3.0"),
    ("Reset", "r on x1 and x2 at conversion start", "1e-5", "1e-4", "s_speed", "ss/-40/3.0"),
    ("Virtual ground", "leakage I (offset I/(fs Cs), non-cancelling fraction rho 0.1 %)", "~0.1 pA (tt/27/3.3)",
     "100 pA = 100 pA x 2^((T-125)/10) (V/3.6)^2 x proc{ff 1, fs/sf .7, tt/RC .5, ss .3}", "formula", "ff/125/3.6"),
    ("Capacitors", "Cs (kT/C)", "0.5 pF", "ss_hh x1.1, ff_ll x0.9 (ASSUMED +-10 % MIM corner)", "corner", "ff_ll"),
    ("kT/C", "temperature in kT", "T + 273.15 K", "398 K at 125 C", "T", "125 C"),
    ("Reference pins", "R_ext per pin (DC)", "10 ohm", "10 ohm (board spec)", "const", "all"),
    ("Cs+/Cs-", "mismatch (CMRR)", "-", "0.75 % 3 sigma (MC only)", "MC", "MC"),
]


def stress(proc, T, V):
    """0..1 stress variables; 0 at tt/27/3.3 (nominal), 1 at the worst corner of that mechanism. ASSUMED weights."""
    sp_g = {"ss": 1.0, "sf": 0.5, "fs": 0.5}.get(proc, 0.0)
    st_g = max(0.0, (T - 27) / 98.0)
    sv = min(1.0, max(0.0, round((3.3 - V) / 0.3, 9)))
    sp_s = {"ss": 1.0, "sf": 0.5, "fs": 0.5, "ss_hh": 0.5}.get(proc, 0.0)
    st_s = max(0.0, (27 - T) / 67.0)
    return {"gain": min(1.0, (sp_g + st_g + sv) / 3), "speed": min(1.0, (sp_s + st_s + sv) / 3)}


def lerp(a, b, s):
    return a + s * (b - a)


def leak_current(proc, T, V):
    pf = {"ff": 1.0, "fs": 0.7, "sf": 0.7, "tt": 0.5, "ss": 0.3, "ss_hh": 0.5, "ff_ll": 0.5}[proc]
    return 100e-12 * 2.0 ** ((T - 125) / 10.0) * (V / 3.6) ** 2 * pf


SIGNS = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))


def table_at(s, worst=WORST_TABLE):
    return tuple((v0, lerp(a0, a1, s)) for (v0, a0), (_, a1) in zip(NOM_TABLE, worst))


def point(proc, T, V, fs, sg=(1, 1, 1), N=N_PREC, ov=None, aux=None):
    """Params + auxiliary (non-model) terms for one PVT point. ov: Params overrides; aux: aux overrides (nonvac)."""
    st = stress(proc, T, V)
    g, sp = st["gain"], st["speed"]
    tab = table_at(g)
    en = lerp(7.0, 10.0, g)
    cs = 0.5e-12 * {"ss_hh": 1.1, "ff_ll": 0.9}.get(proc, 1.0)
    r = lerp(1e-5, 1e-4, sp)
    ax = {"r": r, "i_leak": leak_current(proc, T, V), "cs": cs}
    ax.update(aux or {})
    kw = dict(a0_db=np.inf, av_table1=tab, av_table2=tab, ktc_excess=s3.excess_from_en(en), flicker_on=True,
              ota_fc=lerp(400e3, 631e3, g), lf_gain=LF, vres=5e-6, vos=sg[0] * 9e-3, vos2=sg[1] * 9e-3,
              comp_offset=sg[2] * 20e-3 / VREF, comp_noise=lerp(2e-3, 5e-3, g) / VREF,
              tau_in=lerp(8e-9, 18.75e-9, sp), tau_ref=lerp(3e-9, 10e-9, sp), cd_ref=5e-12,
              x1_offset=ax["r"] * X1MAX_V, r_ext_ref=10.0, temp_k=T + 273.15, cs=ax["cs"], fs=fs, N=N)
    kw.update(ov or {})
    return s3.ideal_base(**kw), ax


def name(proc, T, V):
    return f"{proc}/{T}/{V:g}"


# ----------------------------------------------------------------------------------------- measurements
def noise_uv(p, rate, N, m_out=32):
    pl = m.with_(p, N=N)
    k = max(1, round(pl.fs / (rate * N)))
    return m.measure_noise(pl, k, m_out=m_out, u_dc=0.0)["rms_v"] * 1e6      # u = 0: review S3-10


def memory_uv(p, r):
    """Inter-conversion memory: conversion of u in {-0.5, 0, 0.5} after +-0.95 FS, with x1, x2 restarting at r * final
    state, minus the same conversion from a clean reset. Residue-corrected reconstruction removes the quantization error,
    so the difference is the memory alone (deterministic, no scatter). Returns max |difference| [uV]."""
    q = m.with_(p, ktc_on=False, flicker_on=False, vos=0.0, vres=0.0, reset_r=0.0)
    tg = np.array([-0.5, 0.0, 0.5])
    U = np.array([[pv, t] for pv in (0.95, -0.95) for t in tg])
    out, sts = m.convert_chain(m.with_(q, reset_r=r), U, return_state=True)
    mem = sts[1]["u_corr"]
    fresh_u, fst = m.convert(q, np.tile(tg, 2), return_state=True)
    base = fst["u_corr"]
    d = (mem - base) * q.vref * 1e6
    return float(np.max(np.abs(d)))


def static_err_corr(p, sys, B=96):
    """Mean error [uV] over stratified DC inputs, noise-free, residue-corrected; sys: pair of opposite input polarities."""
    q = m.with_(p, ktc_on=False, flicker_on=False)
    u = -0.5 + (np.arange(B) + 0.5) / B
    nz = m.ota_noise_block(q, B, np.random.default_rng(0))

    def run(sg):
        uh, st = m.convert(q, u, ota_noise=nz, sys_sign=sg, return_state=True)
        return st["u_corr"]
    uh = 0.5 * (run(np.ones(B)) + run(-np.ones(B))) if sys else run(None)
    return float(np.mean(uh - u)) * q.vref * 1e6


def offset_total(p, ax, sys, signs_ps):
    """sys-pair offset: model residual (max over the sign combinations) + non-cancelling terms:
    reset residue 2 r x1max/(c1 (N-1)) (theory; checked against the model in s3 theory checks and the hook test)
    + leakage I/(fs Cs) x rho (rho 0.1 % ASSUMED, SPEC 3.0)."""
    p0 = m.with_(p, **{f: 0.0 for f in s3.OFF_FIELDS})
    base = static_err_corr(p0, sys)
    res = max(abs(static_err_corr(pp, sys) - base) for pp in signs_ps)
    reset = 2 * ax["r"] * X1MAX_V / (C1 * (p.N - 1)) * 1e6
    leak = s3.leak_offset(ax["i_leak"], p.fs, ax["cs"]) * 1e6 * s3.RHO_LEAK
    return res + reset + leak, {"resid": res, "reset": reset, "leak": leak}


def grid_task(a):
    proc, T, V, fs, ov, ax_ov, sysflag = a
    nm = name(proc, T, V)
    t0 = time.time()
    ps = [point(proc, T, V, fs, sg, ov=ov, aux=ax_ov) for sg in SIGNS]
    p, ax = ps[0]
    r = {"point": nm, "fs": fs, "proc": proc, "T": T, "V": V}
    r["n15"] = noise_uv(p, 15, N_PREC)
    r["n240"] = noise_uv(p, 240, 1024)
    inl, gain = [], []
    for pp, _ in ps:
        v = s1.inl_v2(m.with_(pp, ktc_on=False, flicker_on=False), N_PREC, True)
        inl.append(v["inl_ppm"])
        gain.append(v["gain_err_ppm"])
    r["inl"], r["gain"] = float(max(inl)), float(max(abs(x) for x in gain))
    r["off"], r["off_parts"] = offset_total(p, ax, sysflag, [pp for pp, _ in ps])
    r["mem"] = memory_uv(p, ax["r"])
    r["secs"] = time.time() - t0
    return r


# ----------------------------------------------------------------------------------------- Monte Carlo
def _inl_rows(uh, u):
    gain = (uh[:, -1] - uh[:, 0]) / (u[-1] - u[0])
    off = uh[:, 0] - gain * u[0]
    inl = uh - (gain[:, None] * u[None, :] + off[:, None])
    return np.max(np.abs(inl), axis=1) / 2 * 1e6, (gain - 1) * 1e6


def mc_task(a):
    proc, T, V, fs, ndraw, seed, tag = a
    rng = np.random.default_rng(seed)
    d1, d2 = rng.normal(0, 9e-3 / 3, ndraw), rng.normal(0, 9e-3 / 3, ndraw)
    dc = rng.normal(0, 20e-3 / 3, ndraw)
    dcs = rng.normal(0, 0.0075 / 3, ndraw)                       # (Cs+ - Cs-)/Cs, 0.75 % 3 sigma
    dcp = rng.normal(0, DCP_TOP_3S / 3, ndraw)                   # D33: Cp_top(+) - Cp_top(-), 3 sigma 0.25 fF (drawn after the others: older draws unchanged)
    p, ax = point(proc, T, V, fs)
    inl = np.zeros(ndraw)
    gain = np.zeros(ndraw)
    npts, chunk = 161, 40
    u = np.linspace(-0.9, 0.9, npts)
    for i0 in range(0, ndraw, chunk):
        sl = slice(i0, min(ndraw, i0 + chunk))
        D = len(d2[sl])
        q = m.with_(p, ktc_on=False, flicker_on=False, vos=0.0, vres=0.0, vos2=np.repeat(d2[sl], npts),
                    comp_offset=np.repeat(dc[sl], npts) / VREF)
        uh, st = m.convert(q, np.tile(u, D), rng=np.random.default_rng(2), return_state=True)
        uh = st["u_corr"]
        inl[sl], gain[sl] = _inl_rows(uh.reshape(D, npts), u)
    # offsets: per-draw sys-pair residual and raw (sys-off) offset, 24 stratified inputs per draw
    no = 24
    uo = -0.5 + (np.arange(no) + 0.5) / no
    resid = np.zeros(ndraw)
    raw = np.zeros(ndraw)
    base_p = m.with_(p, ktc_on=False, flicker_on=False, **{f: 0.0 for f in s3.OFF_FIELDS})
    z = np.zeros((no, 1))
    one = np.ones(no)
    def cv(q, U, nz, sg):
        uh, st = m.convert(q, U, ota_noise=nz, sys_sign=sg, return_state=True)
        return st["u_corr"]
    b0 = 0.5 * (cv(base_p, uo, z, one) + cv(base_p, uo, z, -one)) - uo
    r0 = cv(base_p, uo, z, None) - uo
    for i0 in range(0, ndraw, chunk):
        sl = slice(i0, min(ndraw, i0 + chunk))
        D = len(d1[sl])
        q = m.with_(p, ktc_on=False, flicker_on=False, vres=5e-6, vos2=np.repeat(d2[sl], no), comp_offset=np.repeat(dc[sl], no) / VREF)
        nz = np.repeat(d1[sl], no)[:, None]
        U = np.tile(uo, D)
        a_ = cv(q, U, nz, np.tile(one, D))
        b_ = cv(q, U, nz, -np.tile(one, D))
        pair = (0.5 * (a_ + b_) - U).reshape(D, no).mean(axis=1) - b0.mean()
        rw = (cv(q, U, nz, None) - U).reshape(D, no).mean(axis=1) - r0.mean()
        resid[sl], raw[sl] = pair * VREF * 1e6, rw * VREF * 1e6
    reset = 2 * ax["r"] * X1MAX_V / (C1 * (p.N - 1)) * 1e6
    leak = s3.leak_offset(ax["i_leak"], fs, ax["cs"]) * 1e6 * s3.RHO_LEAK
    ee = np.array([eps_draw(ax["cs"], e_, d_) for e_, d_ in zip(dcs, dcp)])      # D36: signed per-draw sum, inj worst sign
    ee_lin = np.array([eps_eff_linear(ax["cs"], e_, d_) for e_, d_ in zip(dcs, dcp)])
    e3 = eps_eff(ax["cs"], EPS_3SIGMA)
    cmrr = {"3sigma": cmrr_eval(p, e3), "worst_draw": cmrr_eval(p, float(ee.max()))}
    superseded = {"3sigma": cmrr_eval(p, EPS_3SIGMA), "worst_draw": cmrr_eval(p, float(np.abs(dcs).max()))}   # old eps_Cs*dVcm term (D33: superseded)
    off = np.abs(resid) + reset + leak
    return {"tag": tag, "point": name(proc, T, V), "fs": fs, "ndraw": ndraw,
            "inl": inl.tolist(), "gain": np.abs(gain).tolist(), "off": off.tolist(), "resid": resid.tolist(),
            "raw_sysoff_uv": raw.tolist(), "cmrr_uv_per_v": (np.abs(dcs) * 1e6).tolist(), "eps_eff_uv_per_v": (ee * 1e6).tolist(), "eps_eff_linear_uv_per_v": (ee_lin * 1e6).tolist(), "eps_eff_3sigma": e3,
            "eps_eff_3sigma_linear": eps_eff_linear(ax["cs"], EPS_3SIGMA), "cs": ax["cs"],
            "cmrr": cmrr, "cmrr_superseded_eps_cs": superseded, "reset": reset, "leak": leak}


def mc_verdict(r):
    fails = []
    for tag_, rr in r.get("cmrr", {}).items():
        fails += cmrr_fails(rr, f"{r['tag']} {r['point']} fs {r['fs']/1e6:g} MHz {tag_}")
    for k in ("inl", "gain", "off"):
        x = np.array(r[k])
        mu, sd, mx = float(x.mean()), float(x.std(ddof=1)), float(x.max())
        if not (np.all(np.isfinite(x)) and mu + 3 * sd <= LIM[k] and mx <= LIM[k]):
            fails.append(f"MC {r['tag']} {r['point']} fs {r['fs']/1e6:g} MHz: {k} mu+3sigma {mu + 3 * sd:.3g} / max {mx:.3g} > {LIM[k]:g}")
    return fails


# ----------------------------------------------------------------------------------------- fast mode
def fast_task(a):
    proc, T, V, N, gbw = a
    p, ax = point(proc, T, V, 4e6, N=N)
    t_half = 0.45 / 4e6
    out = {"point": name(proc, T, V), "N": N, "gbw_MHz": gbw / 1e6}
    out["n"] = m.measure_noise(m.with_(p, flicker_on=True), 1, m_out=64, u_dc=0.0)["rms_v"] * 1e6
    base = m.with_(p, ktc_on=False, flicker_on=False)
    out["inl_model"] = s1.inl_v2(base, N, True)["inl_ppm"]
    uq = np.linspace(-0.9, 0.9, 401)
    out["quant_rms_uv"] = float(np.std(m.convert(base, uq, rng=np.random.default_rng(2)) - uq) * VREF * 1e6)    # raw accumulators, no residue correction
    # hand slew-then-settle penalty (ESTIMATE, not simulated): per-cycle error eps = exp(-(t_half - t_slew)/tau_ota),
    # lumped as a finite-gain-equivalent pole error: A_eq = (1 + c)/(eps_pole + eps_settle)
    res = {}
    for st, (c, beta, dv, sr) in {"1": (C1, 0.84, C1 * 2 * VREF, 12e6), "2": (C2, 0.61, C2 * (0.6 + KK) * VREF, 25e6)}.items():
        tau = 1.0 / (2 * math.pi * beta * gbw)
        t_sl = dv / sr
        eps = math.exp(-max(0.0, t_half - t_sl) / tau)
        a1 = 10 ** (float(np.interp(1.0, [t[0] for t in p.av_table1], [t[1] for t in p.av_table1])) / 20)   # A at ~1 V peak swing
        aeq = (1 + c) / ((1 + c) / a1 + eps)
        res[st] = {"t_slew_ns": t_sl * 1e9, "tau_ns": tau * 1e9, "eps": eps, "a_eq_dB": 20 * math.log10(aeq)}
    out["settle"] = res
    pen = m.with_(base, av_table1=None, av_table2=None, a0_db=res["1"]["a_eq_dB"], a0_db2=res["2"]["a_eq_dB"])
    v = s1.inl_v2(pen, N, True)
    out["inl_with_settle"], out["gain_with_settle"] = v["inl_ppm"], v["gain_err_ppm"]
    return out


# ----------------------------------------------------------------------------------------- verdict / report
def gated(r, k):
    return not (k == "n240" and r["fs"] < N240_MIN_FS)


def limit(r, k):
    """Applied limit for row r and spec k (D27: n15 is 3.0 uV only at fs < 2 MHz and T > 85 C)."""
    if k == "n15" and r["fs"] < 2e6 and r["T"] > N15_HOT_C:
        return N15_LIM_LOW_FS_HOT
    return LIM[k]


def spec_fails(rows):
    fails = []
    for r in rows:
        for k in LIM:
            if not gated(r, k):
                continue
            v, lim = r[k], limit(r, k)
            if not (np.isfinite(v) and abs(v) <= lim):
                fails.append(f"{r['point']} fs {r['fs']/1e6:g} MHz: {k} = {v:.4g} {UNITS[k]} > {lim:g}")
    return fails


def cm_err_v(p, e_v, sys, flip=False, B=96):
    """Input-referred error [V] from a CM->diff term e_v, mean over stratified DC inputs, noise-free, residue-corrected, all
    other offsets zero. Hypothesis (flip False): the Cs+/Cs- mismatch term is fixed in the modulator frame (same sign in both
    halves of a sys pair, like an OTA offset), the sys demodulation flips it, the pair cancels it. flip True (broken copy):
    the term rides on the input and flips with the pin-side swap, so the demodulation cannot remove it."""
    q = m.with_(p, ktc_on=False, flicker_on=False, **{f: 0.0 for f in s3.OFF_FIELDS})
    u = -0.5 + (np.arange(B) + 0.5) / B
    e = e_v / q.vref
    nz = m.ota_noise_block(q, B, np.random.default_rng(0))

    def run(sg):
        # the model computes u_in = u' * s (pin-side swap) and demodulates by s. Modulator-frame term (fixed in sign): u_in = s u + e
        # <=> u' = u + e s. Term that rides on the input (flips with the swap): u_in = s (u + e) <=> u' = u + e.
        s_ = np.ones(B) if sg is None else sg
        uh, st = m.convert(q, u + (e if flip else e * s_), ota_noise=nz, sys_sign=sg, return_state=True)
        return st["u_corr"]
    uh = 0.5 * (run(np.ones(B)) + run(-np.ones(B))) if sys else run(None)
    return float(np.mean(uh - u)) * q.vref


def eps_signed(cs, eps_cs, dcp, cp_top=CP_TOP):
    """D36 random part of the D12 residual, signed (WO-09 --cm2 confirmed the '-' sign): ((Cp/Cs) eps_Cs - dCp/Cs) / (1 + Cp/Cs)."""
    r = cp_top / cs
    return (r * eps_cs - dcp / cs) / (1 + r)


def eps_eff(cs, eps_cs, dcp=DCP_TOP_3S, cp_top=CP_TOP, inj=EPS_INJ):
    """D36 corner-row eps_eff (3 sigma inputs): RSS of the two independent random terms + |eps_inj| added linearly."""
    r = cp_top / cs
    return math.hypot(r * eps_cs / (1 + r), dcp / cs / (1 + r)) + inj


def eps_eff_linear(cs, eps_cs, dcp=DCP_TOP_3S, cp_top=CP_TOP, inj=EPS_INJ):
    """SUPERSEDED (D36) D33 linear worst-case sum: |dCp/Cs| + |(Cp/Cs) eps_Cs| + eps_inj. Reported for the record only."""
    return abs(dcp / cs) + abs(cp_top / cs * eps_cs) + inj


def eps_draw(cs, eps_cs, dcp, inj=EPS_INJ):
    """D36 per-draw |eps_eff|: signed random sum, eps_inj at its worst sign against the draw."""
    e = eps_signed(cs, eps_cs, dcp)
    return abs(e) + inj


def cmrr_eval(p, eps, vin_cms=VIN_CMS, flip=False):
    """CMRR table for one mismatch eps: per Vin_cm, input-referred error and CMRR = 20 log10(dVcm / error), sys on and off."""
    base = {s_: cm_err_v(p, 0.0, s_, flip) for s_ in (True, False)}
    rows = []
    for vc in vin_cms:
        dv = vc - VREF_CM
        row = {"eps": eps, "vin_cm": vc, "dvcm": dv}
        for s_, key in ((True, "on"), (False, "off")):
            if abs(dv) < 1e-9:
                row[key + "_err_v"], row[key + "_db"] = 0.0, math.inf
                continue
            err = abs(cm_err_v(p, eps * dv, s_, flip) - base[s_])
            row[key + "_err_v"] = err
            row[key + "_db"] = 20 * math.log10(abs(dv) / max(err, CMRR_FLOOR_V))
        rows.append(row)
    return rows


def cmrr_fails(rows, tag):
    f = []
    for r in rows:
        for key, lim in (("on", CMRR_ON_DB), ("off", CMRR_OFF_DB)):
            v = r[key + "_db"]
            if not (not math.isnan(v) and v >= lim):
                f.append(f"CMRR {tag} eps {r['eps']*1e6:.0f} uV/V Vin_cm {r['vin_cm']:g} V: sys {key} = {v:.1f} dB < {lim:g}")
    return f


def worst_table(rows):
    out = []
    for k in LIM:
        w = max([r for r in rows if gated(r, k)], key=lambda r: abs(r[k]) / limit(r, k))
        lim = limit(w, k)
        out.append((k, abs(w[k]), lim, lim / abs(w[k]) if w[k] else math.inf, w["point"], w["fs"]))
    return out


def fmt_table(head, body):
    return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "".join("| " + " | ".join(r) + " |\n" for r in body)


def run_nonvac(a, pool):
    bad_tab = ((0.0, 80.0), (1.4, 60.0), (2.0, 55.0), (3.1, 50.0))
    cases = [
        ("A(1.4 V) = 60 dB at ss/125/3.0", ("ss", 125, 3.0, 2e6, {"av_table1": bad_tab, "av_table2": bad_tab}, None, True), "inl"),
        ("reset r = 1e-2 at ss/-40/3.0", ("ss", -40, 3.0, 2e6, None, {"r": 1e-2}, True), "mem"),
        ("sys chop off (model offset not cancelled) at tt/27/3.3", ("tt", 27, 3.3, 2e6, None, None, False), "off"),
        ("Cs / 100 (noise) at tt/27/3.3", ("tt", 27, 3.3, 2e6, {"cs": 0.005e-12}, {"cs": 0.005e-12}, True), "n15"),
        ("tau_in 2 us (gain) at ss/-40/3.0", ("ss", -40, 3.0, 2e6, {"tau_in": 2e-6}, None, True), "gain"),
    ]
    good = pool.map(grid_task, [("ss", 125, 3.0, 2e6, None, None, True), ("ss", -40, 3.0, 2e6, None, None, True), ("tt", 27, 3.3, 2e6, None, None, True)])
    res = pool.map(grid_task, [c[1] for c in cases])
    L = ["# S4 non-vacuity: broken copies must REJECT at the named point", "",
         "Command: `python3 -m model.studies.s4_corners --out DIR --nonvac`", "", "Unbroken copies at the same points (all must pass):", ""]
    unbroken_fail = spec_fails(good)
    L.append(fmt_table(["point", "n15", "n240", "inl", "off", "gain", "mem"], [[r["point"]] + [f"{r[k]:.3g}" for k in ("n15", "n240", "inl", "off", "gain", "mem")] for r in good]))
    L += ["Broken copies:", ""]
    body, rej, notrej = [], [], []
    for (txt, _, key), r in zip(cases, res):
        v = abs(r[key])
        ok = (not np.isfinite(v)) or v > limit(r, key)
        body.append([txt, key, f"{v:.4g} {UNITS[key]}", f"{limit(r, key):g}", "REJECT" if ok else "NOT REJECTED"])
        (rej if ok else notrej).append(f"{r['point']} fs {r['fs']/1e6:g} MHz [{txt}]: {key} = {v:.4g} {UNITS[key]} > {limit(r, key):g}")
    # CMRR (D30): unbroken must pass; CM term applied so that it flips with the input must fail sys-on; 3 % mismatch must fail sys-off
    pcm, _ = point("tt", 27, 3.3, 2e6)
    good_cm = cmrr_eval(pcm, EPS_FOR_OFF_GATE * 0.9)      # a mismatch that meets both gates (0.09 %)
    unbroken_fail += cmrr_fails(good_cm, "unbroken tt/27/3.3")
    cs_ = pcm.cs
    for txt, rows_cm, key, lim in (("CM term applied after the pin-side swap (flips with the input) at tt/27/3.3", cmrr_eval(pcm, eps_eff(cs_, EPS_3SIGMA), flip=True), "on", CMRR_ON_DB),
                                   ("Cs+/Cs- mismatch 3 % (sys off) in eps_eff at tt/27/3.3", cmrr_eval(pcm, eps_eff(cs_, 0.03)), "off", CMRR_OFF_DB),
                                   ("dCp,top 3 sigma 2 fF (sys off) in eps_eff at tt/27/3.3", cmrr_eval(pcm, eps_eff(cs_, EPS_3SIGMA, dcp=2e-15)), "off", CMRR_OFF_DB)):
        w = min((r_ for r_ in rows_cm if math.isfinite(r_[key + "_db"])), key=lambda r_: r_[key + "_db"])
        ok = not (w[key + "_db"] >= lim)
        body.append([txt, "cmrr_" + key, f"{w[key + '_db']:.1f} dB (Vin_cm {w['vin_cm']:g} V)", f">= {lim:g}", "REJECT" if ok else "NOT REJECTED"])
        (rej if ok else notrej).append(f"tt/27/3.3 fs 2 MHz [{txt}]: sys {key} CMRR = {w[key + '_db']:.1f} dB < {lim:g}")
    L.append(fmt_table(["broken copy", "spec", "value", "limit", "result"], body))
    verdict = "REJECT" if rej and not notrej and not unbroken_fail else "ACCEPT (nonvac FAILED)"
    L += [verdict, ""] + [f"- {x}" for x in rej] + [f"- NOT REJECTED: {x}" for x in notrej] + [f"- unbroken copy fails: {x}" for x in unbroken_fail]
    (Path(a.out) / "s4_nonvac.md").write_text("\n".join(L) + "\n")
    (Path(a.out) / "s4_nonvac.json").write_text(json.dumps({"cases": [c[0] for c in cases], "results": res, "unbroken": good, "verdict": verdict}, indent=1, default=float))
    print(verdict)
    for x in rej:
        print("  -", x)
    for x in notrej:
        print("  - NOT REJECTED:", x)
    for x in unbroken_fail:
        print("  - unbroken copy fails:", x)
    sys.exit(1 if verdict == "REJECT" else 0)


# ----------------------------------------------------------------------------------------- R4 probe (WO-12)
PROBE_EPS = (0.0, 1e-4, 2e-4, 4e-4, 5.84e-4, 8e-4)
PROBE_DVCM = 0.8
IDEAL_A = dict(av_table1=None, av_table2=None, a0_db=np.inf)


def probe_rows(ns=(256, 1024, 4096)):
    """REVIEW R4 probe: sys-on error [V] of cm_err_v for a CM->diff term eps*dVcm (dVcm 0.8 V) at tt/27/3.3, 2 MHz, with the S4 A(v) table and with an
    ideal OTA. err = |cm_err_v(eps) - cm_err_v(0)| as in cmrr_eval (the eps = 0 baseline removes eps-independent terms)."""
    rows = []
    for n in ns:
        for tag, ov in (("table A(v)", None), ("ideal A", IDEAL_A)):
            p = point("tt", 27, 3.3, 2e6, N=n, ov=ov)[0]
            base = cm_err_v(p, 0.0, True)
            for e in PROBE_EPS:
                raw = cm_err_v(p, e * PROBE_DVCM, True)
                rows.append({"N": n, "A": tag, "eps": e, "raw_err_v": raw, "err_v": abs(raw - base)})
    return rows


def probe_verdict(rows, bound_v=1e-9, ideal_bound_v=1e-12, ideal_slope=1e-8):
    """Gates (D38/V1; expected values from theory, not from the code): after the residue-frame fix (C1) the sys-on error of a CM->diff term is second order
    (eps x dg_even/du): table-A(v) err <= 1e-3 uV (1e-9 V) at every N and eps; ideal OTA <= 1e-12 V and <= 1e-8 x eps (eps-scaling); the eps = 0 row is 0.
    NaN / missing / missing N fails. (The earlier 20 uV / 8 uV bounds could not see the C1 bug, 6.3 / 0.04 uV: REVIEW-S5d m4.)"""
    if not rows or not all(np.isfinite(r["err_v"]) for r in rows):
        return ["missing or non-finite probe value"]
    fails = []
    for r in rows:
        if r["eps"] == 0.0 and r["err_v"] != 0.0:
            fails.append(f"N{r['N']} {r['A']}: eps = 0 baseline row is not zero")
        if r["A"] == "table A(v)" and not r["err_v"] <= bound_v:
            fails.append(f"N{r['N']} eps {r['eps']:g}: table err {r['err_v']*1e6:.3g} uV > {bound_v*1e6:g}")
        if r["A"] == "ideal A" and not (r["err_v"] <= ideal_bound_v and r["err_v"] <= ideal_slope * r["eps"] + 1e-18):
            fails.append(f"N{r['N']} eps {r['eps']:g}: ideal-A err {r['err_v']*1e6:.3g} uV > {ideal_bound_v*1e6:g} uV or > {ideal_slope:g} x eps")
    for n in (256, 1024, 4096):
        if not any(r["N"] == n for r in rows):
            fails.append(f"probe lacks N {n} rows")
    return fails


def _pr(rows, n, a_, e):
    return next(r["err_v"] for r in rows if (r["N"], r["A"], r["eps"]) == (n, a_, e))


def run_probe(a):
    rows = probe_rows()
    fails = probe_verdict(rows)
    L = ["# S4 sys-on probe (R4, WO-12)", "", "Command: `python3 -m model.studies.s4_corners --out DIR --probe`", "",
         f"tt/27/3.3, 2 MHz, CM->diff term e = eps x {PROBE_DVCM:g} V, sys chop on, noise free, residue corrected. err = |e(eps) - e(0)|.", "",
         fmt_table(["N", "A", "eps", "err uV", "raw uV"], [[str(r["N"]), r["A"], f"{r['eps']:g}", f"{r['err_v']*1e6:.4g}", f"{r['raw_err_v']*1e6:.4g}"] for r in rows]),
         "Informational (not gated; the gates are in probe_verdict): " + "; ".join(f"eps {e:g}: N256/N1024 table err x{_pr(rows, 256, 'table A(v)', e) / max(_pr(rows, 1024, 'table A(v)', e), 1e-18):.3g}, N1024/N4096 x{_pr(rows, 1024, 'table A(v)', e) / max(_pr(rows, 4096, 'table A(v)', e), 1e-18):.3g}, ideal-A / table at N256 x{_pr(rows, 256, 'ideal A', e) / max(_pr(rows, 256, 'table A(v)', e), 1e-18):.3g}" for e in PROBE_EPS[1:]), "",
         "ACCEPT" if not fails else "REJECT", ""] + [f"- {f}" for f in fails]
    (Path(a.out) / "s4_probe.md").write_text("\n".join(L) + "\n")
    (Path(a.out) / "s4_probe.json").write_text(json.dumps({"rows": rows, "fails": fails}, indent=1, default=float))
    print("\n".join(L))
    sys.exit(1 if fails else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nonvac", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pool = Pool(min(4, a.procs))
    if a.probe:
        run_probe(a)
    if a.nonvac:
        run_nonvac(a, pool)
    pts = [(pv["proc"], pv["temp"], pv["vapwr"]) for pv in dp.PVT_LIST_ANALOG]
    assert len(pts) == 63
    if a.quick:
        pts = [pt for pt in pts if pt in {("tt", 27, 3.3), ("ss", 125, 3.0), ("ff", 125, 3.6), ("ss", -40, 3.0), ("ss_hh", -40, 3.0),
                                          ("ff_ll", 125, 3.6), ("sf", 27, 3.0), ("fs", 27, 3.6), ("ff", -40, 3.6)}]
    FSS = (0.25e6, 2e6)
    rows = pool.map(grid_task, [(pr, T, V, fs, None, None, True) for pr, T, V in pts for fs in FSS], chunksize=1)
    t_grid = time.time() - t0
    fails = spec_fails(rows)
    wt = worst_table(rows)
    # MC points: tt/27/3.3 and the empirically worst INL / offset points of the grid
    wi = max(rows, key=lambda r: r["inl"])
    wo = max(rows, key=lambda r: r["off"])
    nd = (40, 10) if a.quick else (200, 50)
    mc_jobs = [("tt", 27, 3.3, fs, nd[0], 11 + i, "tt/27") for i, fs in enumerate(FSS)]
    mc_jobs += [(wi["proc"], wi["T"], wi["V"], wi["fs"], nd[1], 21, "worst-INL"), (wo["proc"], wo["T"], wo["V"], wo["fs"], nd[1], 22, "worst-offset")]
    mcs = pool.map(mc_task, mc_jobs, chunksize=1)
    for r in mcs:
        fails += mc_verdict(r)
    t_mc = time.time() - t0 - t_grid
    fp = [(pr, T, V, N, g) for (pr, T, V) in (("tt", 27, 3.3), ("ss", 125, 3.0), ("ss", -40, 3.0)) for N in (64, 256, 1024) for g in (10e6, 20e6)]
    fast = pool.map(fast_task, fp, chunksize=1)
    total = time.time() - t0
    verdict = "REJECT" if fails else "ACCEPT"
    write_report(a, rows, wt, mcs, fast, fails, verdict, t_grid, t_mc, total, wi, wo)
    for r in rows:
        print(f"row {r['point']} fs {r['fs']/1e6:g} MHz: n15 {r['n15']:.4g} (lim {limit(r, 'n15'):g}) n240 {r['n240']:.4g} " + (f"(lim {LIM['n240']:g})" if gated(r, "n240") else "(NOT GATED, 240 SPS unreachable)"))
    print_cmrr(mcs)
    print(f"{len(rows)} grid evaluations ({len(pts)} PVT x {len(FSS)} fs), {sum(len(r['inl']) for r in mcs)} MC draws, wall {total:.0f} s")
    for k, w, lim, ratio, pn, fs in wt:
        print(f"worst {k}: {w:.4g} {UNITS[k]} (limit {lim:g}, margin x{ratio:.2f} = {(ratio - 1) * 100:+.0f} %) at {pn} fs {fs/1e6:g} MHz")
    gates = [("grid specs (n15, n240, INL, gain, offset, memory)", [f for f in fails if not f.startswith(("CMRR", "MC"))]),
             ("MC INL / gain / offset", [f for f in fails if f.startswith("MC")]),
             (f"CMRR sys chop on >= {CMRR_ON_DB:g} dB", [f for f in fails if f.startswith("CMRR") and "sys on" in f]),
             (f"CMRR sys chop off >= {CMRR_OFF_DB:g} dB (D32/D33, eps_eff)", [f for f in fails if f.startswith("CMRR") and "sys off" in f])]
    for g, fl in gates:
        print(f"GATE {g}: {'REJECT (%d)' % len(fl) if fl else 'ACCEPT'}")
    hand, code, parts, hok, db3 = eps_summary(mcs)
    lin = mcs[0]["eps_eff_3sigma_linear"]
    print(f"eps_eff (D36) superseded D33 linear sum: {lin:.3e} = {20*math.log10(1/lin):.1f} dB (superseded by D36, shown for the record)")
    print(f"eps_eff (D36, RSS + inj) at 3 sigma allocation: code {code:.3e}, hand {hand:.3e} (dCp/Cs/(1+Cp/Cs) {parts[0]:.2e}, Cp/Cs*eps_Cs/(1+Cp/Cs) {parts[1]:.2e}, inj {parts[2]:.2e}); agree within 10 %: {'yes' if hok else 'NO'}; sys-off {db3:.1f} dB, margin vs 60 dB gate {db3 - CMRR_OFF_DB:+.1f} dB, vs {CMRR_OFF_TARGET_DB:g} dB design target {db3 - CMRR_OFF_TARGET_DB:+.1f} dB (informational)")
    print(f"CMRR sys-off = 1/eps_eff (D33; old eps_Cs term superseded): eps needed for {CMRR_OFF_DB:g} dB = {EPS_FOR_OFF_GATE*100:.2g} % ({EPS_FOR_OFF_GATE*1e6:.0f} uV/V); old eps_Cs-only term at {EPS_3SIGMA*100:g} % gave {20*math.log10(1/EPS_3SIGMA):.1f} dB (superseded)")
    print(verdict)
    for f in fails:
        print("  -", f)
    sys.exit(1 if fails else 0)


def cmrr_table(mcs, key="cmrr"):
    body = []
    for r in mcs:
        for tag_, rr in r[key].items():
            for c in rr:
                f = lambda x: "n/a (dVcm 0)" if math.isinf(x) else (">= 240" if x >= 239.9 else f"{x:.1f}")
                body.append([r["tag"], f"{r['point']} @ {r['fs']/1e6:g} MHz", tag_, f"{c['eps']*1e6:.0f}", f"{c['vin_cm']:g}", f"{c['dvcm']:+.1f}",
                             f"{c['off_err_v']*1e6:.4g}", f(c["off_db"]), f"{c['on_err_v']*1e6:.3g}", f(c["on_db"])])
    return fmt_table(["set", "point", "eps", "eps uV/V", "Vin_cm V", "dVcm V", "sys-off err uV", "sys-off CMRR dB (gate >= 60)", "sys-on err uV", "sys-on CMRR dB (gate >= 100, all N)"], body)


def print_cmrr(mcs):
    print("CMRR table (input-referred error, CMRR dB = 20 log10(dVcm / error); VREF_CM %g V assumed):" % VREF_CM)
    for line in cmrr_table(mcs).splitlines():
        print("  " + line)


def gates_of(fails):
    return [("grid specs", [f for f in fails if not f.startswith(("CMRR", "MC"))]), ("MC INL/gain/offset", [f for f in fails if f.startswith("MC")]),
            (f"CMRR sys on >= {CMRR_ON_DB:g} dB", [f for f in fails if f.startswith("CMRR") and "sys on" in f]),
            (f"CMRR sys off >= {CMRR_OFF_DB:g} dB (D32)", [f for f in fails if f.startswith("CMRR") and "sys off" in f])]


def _marg(r, k):
    v = abs(r[k])
    return "n/a" if v == 0 else f"{(limit(r, k) / v - 1) * 100:+.0f} %"


def hand_check(mcs):
    """Hand calculation of eps_eff at the 3 sigma allocation (plain arithmetic from the C4 numbers, independent of eps_eff())."""
    cs = mcs[0]["cs"]
    k = 1 + 20e-15 / cs
    t1, t2, t3 = 0.25e-15 / cs / k, 20e-15 / cs * 0.0075 / k, 2.8e-4      # D36: both random terms divided by (1 + Cp/Cs)
    hand = (t1 ** 2 + t2 ** 2) ** 0.5 + t3                                  # RSS of the random terms + |inj|
    code = mcs[0]["eps_eff_3sigma"]
    return hand, code, (t1, t2, t3), abs(code / hand - 1) <= 0.10


def eps_summary(mcs):
    hand, code, (t1, t2, t3), ok = hand_check(mcs)
    db = 20 * math.log10(1 / code)
    return hand, code, (t1, t2, t3), ok, db


def write_report(a, rows, wt, mcs, fast, fails, verdict, t_grid, t_mc, total, wi, wo):
    out = Path(a.out)
    (out / "s4_corners.json").write_text(json.dumps({"limits": LIM, "mapping": MAPPING, "rows": rows, "worst": wt, "mc": mcs, "fast": fast,
                                                      "fails": fails, "verdict": verdict, "wall_s": total}, indent=1, default=float))
    L = ["# S4: corner-aware tier-0 model (WO-06, re-gated in WO-06a)", "",
         "Command: `python3 -m model.studies.s4_corners --out /home/mempool/regr/tt/WO-06a/s4`" + (" --quick" if a.quick else ""), "",
         f"Wall time {total:.0f} s on 4 processes (grid {t_grid:.0f} s, MC {t_mc:.0f} s). No transistor data exists: every mapping is an **assumption** "
         "(nominal at tt/27/3.3, the SPEC 3.0 limit at that mechanism's worst corner, linear in a 0..1 stress between). "
         "A result here says the budget closes if each block just meets SPEC 3.0; it is not a statement about a circuit.", "",
         "## Mapping (explicit)", "",
         fmt_table(["block", "parameter", "nominal (tt/27/3.3)", "worst", "stress", "worst at"], [list(r) for r in MAPPING]),
         "Stress variables: s_gain = (proc{ss 1, sf/fs .5} + max(0,(T-27)/98) + max(0,(3.3-V)/.3))/3; s_speed = (proc{ss 1, sf/fs/ss_hh .5} + max(0,(27-T)/67) + max(0,(3.3-V)/.3))/3. "
         "ff, ff_ll, tt and the RC points (MOS typical) carry no proc stress; nothing is better than nominal.", "",
         "## Limits (pass = every point inside)", "",
         fmt_table(["spec", "limit", "source"], [["noise @15 SPS (u = 0)", "2.5 uV; 3.0 uV at fs < 2 MHz and T > 85 C", "SPEC 3.0 budget; D27 (the applied limit is printed per row in the appendix)"], ["noise @240 SPS (u = 0)", "5 uV (gated only where 240 SPS is reachable, fs >= 0.49 MHz)", "D29"],
                                                 ["CMRR, sys chop on / off", ">= 100 dB / >= 60 dB at Vin_cm 0.2, 1.0, 2.0 V (VREF_CM 1.0 V assumed), tt/27 and worst MC draws", "D30, sys-off 60 dB per D32"],
                                                 ["INL, N 4096", "20 ppm", "SPEC 3.0 budget (4 ppm of it is unmodelled reserve)"], ["sys-pair offset", "5 uV",
                                                  "SPEC 3.0 budget = model residual + reset 2 r x1max/(c1(N-1)) + leakage x rho 0.1 % (2 uV of it unmodelled reserve)"],
                                                 ["gain error", "5000 ppm", "SPEC 3.0"], ["inter-conversion memory", "0.5 uV", "review S3-5 (+-FS then 0)"]]),
         f"## Corner grid: {len(rows)} evaluations = {len(rows)//2} analog PVT points x fs {{0.25, 2}} MHz", "",
         "Worst point per spec (over all points and both fs):", "",
         fmt_table(["spec", "worst value", "limit", "margin (limit/value)", "margin % (limit/value - 1)", "worst point", "fs [MHz]"],
                   [[k, f"{w:.4g} {UNITS[k]}", f"{lim:g}", f"x{ratio:.2f}", f"{(ratio - 1) * 100:+.0f} %", pn, f"{fs/1e6:g}"] for k, w, lim, ratio, pn, fs in wt]), ""]
    for fs in sorted({r["fs"] for r in rows}):
        sub = [r for r in rows if r["fs"] == fs]
        L += [f"Worst per spec at fs {fs/1e6:g} MHz:", "",
              fmt_table(["spec", "worst", "limit", "margin % (limit/value - 1)", "point"], [[k + ("" if gated(sub[0], k) else " (NOT GATED: 240 SPS unreachable below 0.49 MHz)"),
                                                           f"{abs(max(sub, key=lambda r: abs(r[k]) / limit(r, k))[k]):.4g} {UNITS[k]}", f"{limit(max(sub, key=lambda r: abs(r[k]) / limit(r, k)), k):g}",
                                                           _marg(max(sub, key=lambda r: abs(r[k]) / limit(r, k)), k),
                                                           max(sub, key=lambda r: abs(r[k]) / limit(r, k))["point"]] for k in LIM]), ""]
    L += ["## Monte Carlo (Vos1, Vos2 3 sigma 9 mV; comparator offset 3 sigma 20 mV; Cs+/Cs- 0.75 % 3 sigma)", "",
          "INL and gain per draw: 161-point sweep, residue-corrected; offset per draw: sys-pair residual (24 inputs) + reset + leakage x rho. Pass: mu + 3 sigma and every sample inside the limit. "
          "Worst-INL point = grid worst INL " f"({wi['point']}, {wi['fs']/1e6:g} MHz); worst-offset point = grid worst offset ({wo['point']}, {wo['fs']/1e6:g} MHz).", ""]
    body = []
    for r in mcs:
        row = [r["tag"], f"{r['point']} @ {r['fs']/1e6:g} MHz", str(r["ndraw"])]
        for k in ("inl", "gain", "off"):
            x = np.array(r[k])
            row.append(f"{x.mean():.3g} / {x.std(ddof=1):.2g} / {x.max():.3g} (lim {LIM[k]:g})")
        raw = np.array(r["raw_sysoff_uv"])
        row.append(f"{np.mean(np.abs(raw)):.3g} / {np.max(np.abs(raw)):.3g}")
        body.append(row)
    L.append(fmt_table(["set", "point", "draws", "INL ppm mu/sigma/max", "gain ppm mu/sigma/max", "offset uV mu/sigma/max", "raw sys-off offset uV mean|.|/max (info)"], body))
    cm = np.array(mcs[0]["cmrr_uv_per_v"])
    ee = np.array(mcs[0]["eps_eff_uv_per_v"])
    hand, code, (t1, t2, t3), hok, db3 = eps_summary(mcs)
    allrows = [c for r in mcs for rr in r["cmrr"].values() for c in rr if math.isfinite(c["off_db"])]
    wdb = min(c["off_db"] for c in allrows)
    L += ["## CMRR (D30, D33: on the D12 residual eps_eff)", "",
          "**This models the hypothesis; WO-08 checks it in SPICE.** D33 (REVIEW-S4S5b C-M3): D12 cancels the Cs+/Cs- mismatch term to first order, so the CM->diff coefficient is the D12 residual "
          "eps_eff = ((Cp,top/Cs) eps_Cs - dCp,top/Cs) / (1 + Cp,top/Cs) + eps_inj (D36: sign '-' confirmed by WO-09 --cm2, deck vs closed form 0.0 % in 12 cases). MC: signed per-draw sum of the two independent Gaussians, eps_inj at its worst sign against the draw; 3 sigma corner rows: RSS of the two random terms + |eps_inj| linearly. A CM change dVcm = Vin_cm - VREF_CM "
          f"(VREF_CM = {VREF_CM:g} V ASSUMED, SPEC 3.0 does not fix it) gives a differential term eps_eff*dVcm. "
          f"Allocation (C4): Cp,top {CP_TOP*1e15:g} fF per side (fixed), dCp,top Gaussian 3 sigma {DCP_TOP_3S*1e15:g} fF, eps_Cs Gaussian 3 sigma 0.75 %, eps_inj {EPS_INJ:g} (fixed, worst sign). "
          "Corner points use the 3 sigma values; the worst-draw row uses the largest per-draw |eps_eff| of the MC draws. "
          "Hypothesis for the sys-chop behaviour (unchanged): the pin-side swap does not change the pin CM, so the term is fixed in the modulator frame, with the same sign in both halves of a sys pair (like an OTA offset); "
          "it is modelled as an additive term e on the sampled input after the swap, u_in = s*u + e, demodulated exactly as the chip does (conversion with sys_sign +1 and -1, residue-corrected, averaged). "
          "Sys chop off: the term stays, error = eps_eff*dVcm (tested to 2 %). The --nonvac copy with the term flipping with the input fails the sys-on gate. "
          "D38(a): the earlier sys-on 'metric floor' (D37(b)) was a model bug in the S4 reconstruction (residue added in the modulator frame after demodulation, C1); iadc.convert now returns the demodulated residue-corrected u_corr and the sys-on gate is evaluated at every N. The tier-1 cm2 deck (137-173 dB) is independent evidence. "
          "CMRR = 20 log10(dVcm / input-referred error). Errors below 1e-12 V are capped (240 dB). Sets: tt/27 (both fs) and the worst-INL / worst-offset points.", "",
          "### Theory check (hand calculation)", "",
          f"At tt, Cs = {mcs[0]['cs']*1e12:g} pF, 1 + Cp,top/Cs = {1 + CP_TOP/mcs[0]['cs']:.2f}: dCp,top/Cs/(1+Cp/Cs) = {t1:.2e}; (Cp,top/Cs) eps_Cs/(1+Cp/Cs) = {t2:.2e}; eps_inj = {t3:.2e}. "
          f"RSS of the two random terms + |inj| = **{hand:.3e}** = {20*math.log10(1/hand):.1f} dB. Printed 3 sigma eps_eff = {code:.3e} = {db3:.1f} dB. Agreement within 10 %: **{'yes' if hok else 'NO'}**. "
          f"MC |eps_eff| (signed sum, inj worst sign): mean {ee.mean():.0f} uV/V, max of draws {ee.max():.0f} uV/V (eps_Cs-only mean {cm.mean():.0f}, max {cm.max():.0f}).", "",
          f"**Superseded (D36): D33 linear worst-case sum** = {mcs[0]['eps_eff_3sigma_linear']:.3e} = {20*math.log10(1/mcs[0]['eps_eff_3sigma_linear']):.1f} dB (REJECT). A linear sum of independent 3 sigma terms is about 4.2 sigma, beyond the MC pass rule; D36 uses RSS of the independent random terms plus |eps_inj|. "
          f"The result {db3:.1f} dB passes the {CMRR_OFF_DB:g} dB gate ({db3 - CMRR_OFF_DB:+.1f} dB) and misses the {CMRR_OFF_TARGET_DB:g} dB design target ({db3 - CMRR_OFF_TARGET_DB:+.1f} dB, informational). The target stays a C4/C10 layout goal (dCp,top 3 sigma <= 0.15 fF). The gate is not relaxed.", "",
          f"Worst sys-off CMRR over all rows below: {wdb:.1f} dB (gate {CMRR_OFF_DB:g} dB, margin {wdb - CMRR_OFF_DB:+.1f} dB; against the {CMRR_OFF_TARGET_DB:g} dB design target {wdb - CMRR_OFF_TARGET_DB:+.1f} dB, informational).", "",
          cmrr_table(mcs), "",
          "### Superseded (D33): old eps_Cs * dVcm term", "",
          "Kept for the record, not gated. 3 sigma 7500 uV/V gives 42.5 dB sys-off; it modelled a mechanism that D12 cancels to first order.", "",
          cmrr_table(mcs, "cmrr_superseded_eps_cs"), ""]
    L += ["## Fast mode (fs 4 MHz, informational, not gated)", "",
          "Thermal noise: u = 0, no averaging (k 1, sys-chop pair); at small N it is far below one LSB, so decisions rarely flip and the measured rms can be 0: the quantization column (raw accumulators, rms over a +-0.9 FS sweep) is the real fast-mode resolution limit. INL: ideal-OTA-table model (tables at the corner) with tau_in/tau_ref scaled to the 4 MHz t_half, residue-corrected. "
          "`with settle`: hand slew-then-settle penalty lumped as a finite-gain-equivalent pole error (ESTIMATE, not a simulation): eps = exp(-(t_half - dV/SR)/tau_ota), "
          "tau_ota = 1/(2 pi beta GBW), OTA1 beta .84, dV .512 V, SR 12 V/us; OTA2 beta .61, dV c2(.6+k)VREF, SR 25 V/us; A_eq = (1+c)/((1+c)/A(1 V) + eps).", ""]
    body, prop = [], {}
    for f in fast:
        body.append([f["point"], str(f["N"]), f"{f['gbw_MHz']:g}", f"{f['n']:.3g}", f"{f['quant_rms_uv']:.3g}", f"{f['inl_model']:.3g}", f"{f['inl_with_settle']:.3g}", f"{f['gain_with_settle']:.0f}",
                     f"{f['settle']['1']['eps']:.1e} / {f['settle']['2']['eps']:.1e}"])
        if f["gbw_MHz"] == 20:
            prop[f["N"]] = max(prop.get(f["N"], 0.0), f["inl_with_settle"])
    L.append(fmt_table(["point", "N", "GBW MHz", "thermal noise uV rms (u = 0)", "quantization rms uV (raw)", "INL ppm (no settle)", "INL ppm with settle", "gain ppm with settle", "eps OTA1 / OTA2"], body))

    def rnd(x):
        for c in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000):
            if c >= 1.5 * x:
                return c
        return int(2 * x)
    L += ["Proposed fast-mode INL targets (GBW 20 MHz design target, worst of the three points, 1.5x margin rounded up to 1-2-5): "
          + "; ".join(f"N {n}: <= {rnd(v)} ppm" for n, v in sorted(prop.items())) + ". Proposal only; the SPEC fast-mode target is not set.", ""]
    L += ["## Verdict", "", verdict, ""] + [f"GATE {g}: {'REJECT (%d)' % len(fl) if fl else 'ACCEPT'}" for g, fl in gates_of(fails)] + [""] + [f"- {f}" for f in fails] + [""]
    L += ["## Appendix: all grid evaluations", "",
          fmt_table(["point", "fs MHz", "n15", "n15 limit", "n240", "n240 limit", "INL", "gain", "offset", "memory"],
                    [[r["point"], f"{r['fs']/1e6:g}", f"{r['n15']:.3g}", f"{limit(r, 'n15'):g}", f"{r['n240']:.3g}", (f"{LIM['n240']:g}" if gated(r, "n240") else "not gated")]
                     + [f"{r[k]:.3g}" for k in ("inl", "gain", "off", "mem")] for r in rows])]
    (out / "s4_corners.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
