"""S4: corner-aware tier-0 model (WO-06). SPEC 3.0 limits mapped onto the SPEC 6 PVT points.

Usage: python3 -m model.studies.s4_corners --out DIR [--nonvac] [--procs 4] [--quick]
  (default)  63 analog PVT points x fs {0.25, 2} MHz: noise @15/@240 SPS, INL (N 4096), sys-pair offset, gain error,
             inter-conversion memory; MC (tt/27/3.3 x200, worst-INL and worst-offset point x50); fast mode (4 MHz) table.
             Prints ACCEPT/REJECT naming the failing point; exit 1 on REJECT.
  --nonvac   broken copies that must REJECT at the named point (A(1.4 V) = 60 dB at ss/125/3.0; reset r = 1e-2; sys chop off;
             Cs/100 for noise; tau_in 2 us for gain). Exit 1 if they all reject, 0 (loudly) if any one is NOT rejected.
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
       "n240": 5.0,       # uV rms @240 SPS: ASSUMPTION (SPEC has no 240 SPS limit; joint model at spec is 3.9 uV, SPEC 2.2 stretch 5 uV)
       "inl": 20.0,       # ppm FSR, N 4096 (budget)
       "off": 5.0,        # uV, sys-pair offset incl. non-cancelling terms (budget; 2 uV of it is unmodelled reserve)
       "gain": 5000.0,    # ppm (0.5 %)
       "mem": 0.5}        # uV, inter-conversion memory after +-FS then 0 (review S3-5)
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
    W = q.N * (q.N - 1) / 2

    def corr(uh, st):
        return uh + st["x2_final"] / (q.c1 * q.c2) / W

    tg = np.array([-0.5, 0.0, 0.5])
    U = np.array([[pv, t] for pv in (0.95, -0.95) for t in tg])
    out, sts = m.convert_chain(m.with_(q, reset_r=r), U, return_state=True)
    mem = corr(out[:, 1], sts[1])
    fresh_u, fst = m.convert(q, np.tile(tg, 2), return_state=True)
    base = corr(fresh_u, fst)
    d = (mem - base) * q.vref * 1e6
    return float(np.max(np.abs(d)))


def _corr(q, uh, st):
    """Residue-corrected reconstruction: removes the quantization error exactly, leaving the offset/gain terms."""
    return uh + st["x2_final"] / (q.c1 * q.c2) / (q.N * (q.N - 1) / 2)


def static_err_corr(p, sys, B=96):
    """Mean error [uV] over stratified DC inputs, noise-free, residue-corrected; sys: pair of opposite input polarities."""
    q = m.with_(p, ktc_on=False, flicker_on=False)
    u = -0.5 + (np.arange(B) + 0.5) / B
    nz = m.ota_noise_block(q, B, np.random.default_rng(0))

    def run(sg):
        uh, st = m.convert(q, u, ota_noise=nz, sys_sign=sg, return_state=True)
        return _corr(q, uh, st)
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
        uh = uh + st["x2_final"] / (q.c1 * q.c2) / (q.N * (q.N - 1) / 2)
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
        return _corr(q, uh, st)
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
    off = np.abs(resid) + reset + leak
    return {"tag": tag, "point": name(proc, T, V), "fs": fs, "ndraw": ndraw,
            "inl": inl.tolist(), "gain": np.abs(gain).tolist(), "off": off.tolist(), "resid": resid.tolist(),
            "raw_sysoff_uv": raw.tolist(), "cmrr_uv_per_v": (np.abs(dcs) * 1e6).tolist(), "reset": reset, "leak": leak}


def mc_verdict(r):
    fails = []
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


def spec_fails(rows):
    fails = []
    for r in rows:
        for k, lim in LIM.items():
            if not gated(r, k):
                continue
            v = r[k]
            if not (np.isfinite(v) and abs(v) <= lim):
                fails.append(f"{r['point']} fs {r['fs']/1e6:g} MHz: {k} = {v:.4g} {UNITS[k]} > {lim:g}")
    return fails


def worst_table(rows):
    out = []
    for k, lim in LIM.items():
        w = max([r for r in rows if gated(r, k)], key=lambda r: abs(r[k]))
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
        ok = (not np.isfinite(v)) or v > LIM[key]
        body.append([txt, key, f"{v:.4g} {UNITS[key]}", f"{LIM[key]:g}", "REJECT" if ok else "NOT REJECTED"])
        (rej if ok else notrej).append(f"{r['point']} fs {r['fs']/1e6:g} MHz [{txt}]: {key} = {v:.4g} {UNITS[key]} > {LIM[key]:g}")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nonvac", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pool = Pool(min(4, a.procs))
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
    print(f"{len(rows)} grid evaluations ({len(pts)} PVT x {len(FSS)} fs), {sum(len(r['inl']) for r in mcs)} MC draws, wall {total:.0f} s")
    for k, w, lim, ratio, pn, fs in wt:
        print(f"worst {k}: {w:.4g} {UNITS[k]} (limit {lim:g}, margin x{ratio:.2f}) at {pn} fs {fs/1e6:g} MHz")
    print(verdict)
    for f in fails:
        print("  -", f)
    sys.exit(1 if fails else 0)


def write_report(a, rows, wt, mcs, fast, fails, verdict, t_grid, t_mc, total, wi, wo):
    out = Path(a.out)
    (out / "s4_corners.json").write_text(json.dumps({"limits": LIM, "mapping": MAPPING, "rows": rows, "worst": wt, "mc": mcs, "fast": fast,
                                                      "fails": fails, "verdict": verdict, "wall_s": total}, indent=1, default=float))
    L = ["# S4: corner-aware tier-0 model (WO-06)", "",
         "Command: `python3 -m model.studies.s4_corners --out /home/mempool/regr/tt/WO-06/s4`" + (" --quick" if a.quick else ""), "",
         f"Wall time {total:.0f} s on 4 processes (grid {t_grid:.0f} s, MC {t_mc:.0f} s). No transistor data exists: every mapping is an **assumption** "
         "(nominal at tt/27/3.3, the SPEC 3.0 limit at that mechanism's worst corner, linear in a 0..1 stress between). "
         "A result here says the budget closes if each block just meets SPEC 3.0; it is not a statement about a circuit.", "",
         "## Mapping (explicit)", "",
         fmt_table(["block", "parameter", "nominal (tt/27/3.3)", "worst", "stress", "worst at"], [list(r) for r in MAPPING]),
         "Stress variables: s_gain = (proc{ss 1, sf/fs .5} + max(0,(T-27)/98) + max(0,(3.3-V)/.3))/3; s_speed = (proc{ss 1, sf/fs/ss_hh .5} + max(0,(27-T)/67) + max(0,(3.3-V)/.3))/3. "
         "ff, ff_ll, tt and the RC points (MOS typical) carry no proc stress; nothing is better than nominal.", "",
         "## Limits (pass = every point inside)", "",
         fmt_table(["spec", "limit", "source"], [["noise @15 SPS (u = 0)", "2.5 uV", "SPEC 3.0 budget"], ["noise @240 SPS", "5 uV", "ASSUMED (SPEC has no 240 SPS limit; joint run at spec 3.9 uV)"],
                                                 ["INL, N 4096", "20 ppm", "SPEC 3.0 budget (4 ppm of it is unmodelled reserve)"], ["sys-pair offset", "5 uV",
                                                  "SPEC 3.0 budget = model residual + reset 2 r x1max/(c1(N-1)) + leakage x rho 0.1 % (2 uV of it unmodelled reserve)"],
                                                 ["gain error", "5000 ppm", "SPEC 3.0"], ["inter-conversion memory", "0.5 uV", "review S3-5 (+-FS then 0)"]]),
         f"## Corner grid: {len(rows)} evaluations = {len(rows)//2} analog PVT points x fs {{0.25, 2}} MHz", "",
         "Worst point per spec (over all points and both fs):", "",
         fmt_table(["spec", "worst value", "limit", "margin (limit/value)", "worst point", "fs [MHz]"],
                   [[k, f"{w:.4g} {UNITS[k]}", f"{lim:g}", f"x{ratio:.2f}", pn, f"{fs/1e6:g}"] for k, w, lim, ratio, pn, fs in wt]), ""]
    for fs in sorted({r["fs"] for r in rows}):
        sub = [r for r in rows if r["fs"] == fs]
        L += [f"Worst per spec at fs {fs/1e6:g} MHz:", "",
              fmt_table(["spec", "worst", "limit", "point"], [[k + ("" if gated(sub[0], k) else " (NOT GATED: 240 SPS unreachable below 0.49 MHz)"),
                                                           f"{abs(max(sub, key=lambda r: abs(r[k]))[k]):.4g} {UNITS[k]}", f"{LIM[k]:g}",
                                                           max(sub, key=lambda r: abs(r[k]))["point"]] for k in LIM]), ""]
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
    L += [f"CMRR term (Cs+/Cs- mismatch, D12 switching): CM-to-differential gain |dCs/Cs| = {cm.mean():.0f} uV/V mean, 3 sigma point {cm.mean() + 3 * cm.std(ddof=1):.0f} uV/V (7500 uV/V = 0.75 %), "
          f"max of draws {cm.max():.0f} uV/V. This is a constant offset for a given input common-mode error dVcm that sys chop does NOT cancel: "
          f"the 5 uV offset budget is used up by dVcm = {5 / 7500 * 1e3:.2f} mV at the 3 sigma mismatch. SPEC 3.0 has no CM-dependent offset limit; this is a spec gap, not gated.", ""]
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
    L += ["## Verdict", "", verdict, ""] + [f"- {f}" for f in fails] + [""]
    L += ["## Appendix: all grid evaluations", "",
          fmt_table(["point", "fs MHz", "n15", "n240", "INL", "gain", "offset", "memory"],
                    [[r["point"], f"{r['fs']/1e6:g}"] + [f"{r[k]:.3g}" for k in ("n15", "n240", "inl", "gain", "off", "mem")] for r in rows])]
    (out / "s4_corners.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
