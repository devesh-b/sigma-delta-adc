"""Behavioural model of a switched-capacitor incremental delta-sigma ADC.

Discrete-time, one step per modulator clock, vectorised over a batch of
independent conversions. All voltages are normalised to VREF (the
differential full scale is +/-1 == +/-VREF).

Loop (CIFB, delaying integrators, 1-bit quantiser, reset every conversion):

    order 1:  y[n] = sign(x1[n])
              x1[n+1] = p1*x1[n] + g1*c1*(u_s[n] - y[n]*r[n] + e[n])

    order 2:  y[n] = sign(x2[n])
              x1[n+1] = p1*x1[n] + g1*c1*(u_s[n] - y[n]*r[n] + e[n])
              x2[n+1] = p2*x2[n] + g2*c2*(x1[n] - k*y[n])

u_s is the sampled input (with incomplete-settling error), r is the
delivered reference (with reference-node droop), e is input-referred noise
(kT/C, OTA flicker, offset). p, g model finite OTA DC gain.

Reconstruction (cascade-of-integrators, exact for the ideal loop):

    order 1:  u_hat = sum(y) / N
    order 2:  u_hat = (sum_n S[n] + (k/c1) * sum(y)) / (N(N-1)/2),
              S[n] = sum_{m<n} y[m]

The residual quantisation error is bounded by the final integrator state:
x1[N]/(c1 N) for order 1 and x2[N]/(c1 c2 N(N-1)/2) for order 2.
"""

from dataclasses import dataclass, replace
from typing import Optional, Tuple

import numpy as np

K_B = 1.380649e-23


@dataclass(frozen=True)
class Params:
    order: int = 2
    N: int = 1024                # cycles per (sub-)conversion
    fs: float = 1e6              # modulator clock [Hz]
    vref: float = 2.048          # [V]; full scale is +/-vref differential
    c1: float = 0.25             # Cs/Cf stage 1 (bounded swing, see report)
    c2: float = 0.5              # stage 2 gain
    k: float = 1.0               # stage 2 feedback coefficient
    xmax: float = 1.5            # integrator swing limit (units of vref)

    a0_db: float = np.inf        # OTA DC gain (both stages)
    a0_drop: float = 0.0         # fractional gain loss at |x| = xswing
    xswing: float = 1.2          # swing at which gain has dropped by a0_drop
                                 # (units of vref; legacy, scales with VREF)
    vlin_diff: float = 0.0       # [V] if > 0: differential output voltage at
                                 # which gain has dropped by a0_drop. Overrides
                                 # xswing (= vlin_diff / vref) so the OTA
                                 # linear range is fixed in volts, not VREF.
    # S4 hooks (all default off => legacy behaviour, bit-identical)
    a0_db2: Optional[float] = None    # OTA2 DC gain [dB]; None = same as a0_db
    a0_drop2: Optional[float] = None  # OTA2 quadratic drop; None = same as a0_drop
    av_table1: Optional[Tuple[Tuple[float, float], ...]] = None
    av_table2: Optional[Tuple[Tuple[float, float], ...]] = None
                                 # tabulated gain: ((|Vout,diff| [V], gain [dB]), ...), V ascending. Replaces
                                 # a0_db/a0_drop for that stage; a stage with no table uses a0_db(2)/a0_drop(2).
                                 # Gain is held at the end values outside the table range. x [vref] * vref = V diff.
    av_strict: bool = False      # WO-23 (CL-1b): if True, a table lookup outside the table's V range raises
                                 # AvTableRangeError instead of the silent np.interp end-value clamp. Default off.
    r_ext_ref: float = 0.0       # external DC resistance per reference pin [ohm]. Reference current per pin
                                 # I = fs*Cs*(vref/2)*u^2, so delivered ref = 1 - 2*R*I/vref = 1 - R*fs*Cs*u_s^2
    reset_r: float = 0.0         # fraction of final x1/x2 left after reset; carried across consecutive
                                 # conversions of a batch (batch = one chain, in order). See convert_chain.

    cp_ratio: float = 0.3        # parasitic at OTA input / Cs (noise gain)
    # M1 (WO-13/D38(b)): permanent capacitance on the OTA virtual-ground node of stage 1 / 2, as a ratio to that stage's integrating cap.
    # It is never reset, so it lowers the gain g only: g = 1/(1 + (1 + c_samp + cp)/A), p = (1 + (1 + cp)/A) g. The leak 1 - p ~ c_samp/A is unchanged.
    # Default 0.0. (Replaces the WO-12 cp_vg hook, which modelled it as a sampled cap and so overstated the leak.)
    cp_hold1: float = 0.0
    cp_hold2: float = 0.0
    # Stage-2 sampled capacitance (cleared every cycle): Cs2 (c2) plus the separate k-DAC cap Ck = c2*k (D25), so c_samp2 = c2 (1 + k),
    # derived from k (not a stored ratio) and always on. Stage 1 samples c1 only.

    cs: float = 1e-12            # sampling cap per side [F]
    temp_k: float = 300.0
    ktc_events: float = 2.0      # sampling events per cycle (input + ref)
    ktc_excess: float = 1.5      # OTA thermal contribution factor
    # White-noise accounting (do not double count): sampled white noise is
    # sqrt(events * 2kT/Cs * ktc_excess); ktc_excess = 1 (switch kT/C) + 0.5
    # (OTA white, referred through noise gain ng_ref = 5.3, i.e. c1=0.25,
    # cp_ratio=0.3). flicker_series is pure 1/f (no white floor), so OTA white
    # is counted ONLY via ktc_excess. If white_ng_ref > 0 the OTA part scales
    # with the actual noise_gain: excess = 1 + (ktc_excess-1)*noise_gain/ng_ref.
    # At c1=0.25 this is identical to the legacy value; 0 = legacy behaviour.
    white_ng_ref: float = 0.0
    ktc_on: bool = False

    ota_white: float = 6.9e-9    # OTA input white noise [V/rtHz] (pthomas)
    ota_fc: float = 631e3        # OTA 1/f corner [Hz] (pthomas, PMOS 250um)
    flicker_on: bool = False
    vos: float = 0.0             # OTA input offset [V]
    chop: bool = False           # OTA chopping at fs/2
    vres: float = 0.0            # residual offset left by the chopper [V]
    sys_chop: bool = False       # swap input polarity every sub-conversion
    lf_gain: float = 1.0         # input referral of slow OTA errors (offset,
                                 # 1/f, chopper residual). Bottom-plate SC: Cp
                                 # never switches, so ~1. Set to noise_gain
                                 # (1 + Cf/Cs + Cp/Cs) for a pessimistic bound.

    vos2: float = 0.0            # OTA2 input offset [V]; adds vos2/vref to the
                                 # x2 integrator input (constant, not chopped)
    x1_offset: float = 0.0       # constant offset on x1 as seen by stage 2 [V]
                                 # (OTA1 output-referred offset). Same effect as
                                 # vos2 on u_hat: 2*e2/(c1(N-1)) input-referred.

    comp_offset: float = 0.0     # comparator offset (units of vref)
    comp_noise: float = 0.0      # comparator rms noise (units of vref)

    ref_mode: str = "shared"     # "shared": one Cs samples vin then +/-vref
                                 # "separate": Cin and Cref reset to CM
    tau_in: float = 0.0          # input sampling time constant [s]
    tau_ref: float = 0.0         # reference node recovery time constant [s]
    cd_ref: float = 20e-12       # reference decoupling cap [F]

    @property
    def t_half(self):
        # half period minus ~10% non-overlap
        return 0.45 / self.fs

    @property
    def noise_gain(self):
        return 1.0 + 1.0 / self.c1 + self.cp_ratio


def with_(p, **kw):
    return replace(p, **kw)


class AvTableRangeError(ValueError):
    """Strict mode (Params.av_strict): an integrator state left the measured A(v) table range."""


# Max |x1| / |x2| of the last convert() call, differential volts (x * vref); WO-23 report hook.
LAST_RUN = {"x1max_v": float("nan"), "x2max_v": float("nan")}


def _check_range(x, table, vref, stage):
    vmax = float(table[-1][0])
    xv = float(np.max(np.abs(x))) * vref
    if xv > vmax * (1 + 1e-12):
        raise AvTableRangeError(f"stage {stage}: |x| {xv:.4f} V diff outside A(v) table range {vmax:.4f} V (no extrapolation)")


def _leaky(a0_db, c, x=None, drop=0.0, xswing=1.0, table=None, vref=1.0, cp=0.0):
    """Pole p and gain g of an SC integrator with finite OTA gain.

    c = total sampled (reset every cycle) capacitance on the OTA input node / Cint; cp = permanent virtual-ground
    capacitance / Cint. Charge conservation at vg = -vo/A gives
    vo' (1 + (1 + c + cp)/A) = vo (1 + (1 + cp)/A) + c vin, so g = 1/(1 + (1 + c + cp)/A), p = (1 + (1 + cp)/A) g.

    With drop > 0 the gain falls quadratically with the output state x,
    A(x) = A0 * max(0.02, 1 - drop * (x / xswing)^2): the usual source of
    INL in a real OTA (output stage leaving saturation).
    """
    if table is not None:
        tv = np.array([t[0] for t in table], dtype=float)
        td = np.array([t[1] for t in table], dtype=float)
        xv = 0.0 if x is None else np.abs(x) * vref
        a = 10 ** (np.interp(xv, tv, td) / 20)
        g = 1.0 / (1.0 + (1.0 + c + cp) / a)
        p = (1.0 + (1.0 + cp) / a) * g
        return p, g
    if not np.isfinite(a0_db):
        return 1.0, 1.0
    a = 10 ** (a0_db / 20)
    if drop and x is not None:
        a = a * np.maximum(0.02, 1.0 - drop * (x / xswing) ** 2)
    g = 1.0 / (1.0 + (1.0 + c + cp) / a)
    p = (1.0 + (1.0 + cp) / a) * g
    return p, g


def flicker_series(n, fs, white, fc, rng):
    """Real series of length n with one-sided PSD white^2 * fc / f [V^2/Hz]."""
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    s = np.zeros_like(freqs)
    s[1:] = white ** 2 * fc / freqs[1:]
    mag = np.sqrt(s * fs * n / 2.0)
    spec = mag * (rng.standard_normal(len(freqs)) + 1j * rng.standard_normal(len(freqs))) / np.sqrt(2)
    spec[0] = 0.0
    if n % 2 == 0:
        spec[-1] = mag[-1] * rng.standard_normal()
    return np.fft.irfft(spec, n=n)


def convert_chain(p, U, rng=None, sys_sign=None, ota_noise=None, return_state=False):
    """C independent chains of L consecutive conversions, U shape (C, L). Conversion l of a chain starts with
    x1, x2 = reset_r * (final x1, x2 of conversion l-1 of the same chain) (zero for l = 0). Returns (C, L)."""
    U = np.asarray(U, dtype=float)
    C, L = U.shape
    rng = rng or np.random.default_rng(0)
    q = replace(p, reset_r=0.0)
    x1i = x2i = None
    out = np.zeros((C, L))
    states = []
    for l in range(L):
        init = None if x1i is None else (p.reset_r * x1i, p.reset_r * x2i)
        sg = None if sys_sign is None else np.asarray(sys_sign)[:, l]
        on = None if ota_noise is None else ota_noise[:, l]
        uh, st = convert(q, U[:, l], rng=rng, ota_noise=on, sys_sign=sg, return_state=True, x_init=init)
        out[:, l] = uh
        x1i, x2i = st["x1_final"], st["x2_final"]
        states.append(st)
    if return_state:
        return out, states
    return out


def convert(p, u, rng=None, ota_noise=None, sys_sign=None, return_state=False, x_init=None):
    """Run one conversion per batch element.

    u          : (B,) normalised DC inputs
    ota_noise  : (B, N) OTA input-referred noise in volts (flicker + offset),
                 before noise gain and chopping; None = none
    sys_sign   : (B,) +/-1 input polarity for system-level chopping
    returns u_hat (B,) normalised.
    """
    rng = rng or np.random.default_rng(0)
    u = np.asarray(u, dtype=float)
    if p.reset_r and x_init is None:
        # batch = one chain of consecutive conversions
        ss = None if sys_sign is None else np.asarray(sys_sign, dtype=float)[None, :]
        on = None if ota_noise is None else np.asarray(ota_noise)[None]
        # ota_noise rows are per conversion: reshape (B, N) -> (1, B, N); convert_chain wants (C, L, N)
        res, sts = convert_chain(p, u[None, :], rng=rng, sys_sign=ss, ota_noise=on, return_state=True)
        uh = res[0]
        if return_state:
            return uh, {"u_corr": np.concatenate([s_["u_corr"] for s_ in sts]),
                        "x1max": max(s_["x1max"] for s_ in sts), "x2max": max(s_["x2max"] for s_ in sts),
                        "x1_final": np.concatenate([s_["x1_final"] for s_ in sts]),
                        "x2_final": np.concatenate([s_["x2_final"] for s_ in sts])}
        return uh
    B, N = u.size, p.N
    s = np.ones(B) if sys_sign is None else np.asarray(sys_sign, dtype=float)
    u_in = u * s

    a0_2 = p.a0_db if p.a0_db2 is None else p.a0_db2
    drop2 = p.a0_drop if p.a0_drop2 is None else p.a0_drop2
    dyn1 = bool(p.a0_drop) or p.av_table1 is not None
    dyn2 = bool(drop2) or p.av_table2 is not None
    cs2 = p.c2 * (1.0 + p.k)          # stage-2 sampled cap (Cs2 + Ck), D25
    p1, g1 = _leaky(p.a0_db, p.c1, table=p.av_table1, vref=p.vref, cp=p.cp_hold1)
    p2, g2 = _leaky(a0_2, cs2, table=p.av_table2, vref=p.vref, cp=p.cp_hold2)

    e_in = np.exp(-p.t_half / p.tau_in) if p.tau_in > 0 else 0.0
    e_ref = np.exp(-p.t_half / p.tau_ref) if p.tau_ref > 0 else 0.0
    share = p.cs / (p.cs + p.cd_ref)

    sig_ktc = 0.0
    if p.ktc_on:
        exc = p.ktc_excess
        if p.white_ng_ref > 0:
            exc = 1.0 + (p.ktc_excess - 1.0) * p.noise_gain / p.white_ng_ref
        sig_ktc = np.sqrt(p.ktc_events * 2 * K_B * p.temp_k / p.cs * exc) / p.vref
    ng = p.lf_gain / p.vref

    x1 = np.zeros(B)
    x2 = np.zeros(B)
    if x_init is not None:
        x1 = x1 + x_init[0]
        x2 = x2 + x_init[1]
    vnode = np.ones(B)           # reference node (normalised)
    cap_prev = np.zeros(B)       # shared Cs bottom-plate state after transfer
    S = np.zeros(B)
    sumS = np.zeros(B)
    xm1 = xm2 = 0.0
    ys = []                      # S6: per-cycle quantiser decisions (+/-1), exposed via return_state
    xsw = p.vlin_diff / p.vref if p.vlin_diff > 0 else p.xswing
    e2_off = (p.vos2 + p.x1_offset) / p.vref      # 0.0 => skipped (bit-identical)

    for n in range(N):
        q = x2 if p.order == 2 else x1
        dec = q + p.comp_offset
        if p.comp_noise:
            dec = dec + p.comp_noise * rng.standard_normal(B)
        y = np.where(dec >= 0, 1.0, -1.0)
        ys.append(y)
        sumS += S
        S += y

        # input sampling (phase 1)
        if p.ref_mode == "shared":
            u_s = u_in + (cap_prev - u_in) * e_in
        else:
            u_s = u_in * (1.0 - e_in)

        # reference transfer (phase 2)
        if p.ref_mode == "shared":
            v = (vnode * (1 - share) + share * y * u_s)
        else:
            v = vnode * (1 - share)
        v_end = 1.0 + (v - 1.0) * e_ref
        r = v_end
        vnode = 1.0 + (v_end - 1.0) * e_ref     # recovers again during phase 1
        cap_prev = y * v_end

        if p.r_ext_ref:
            r = r * (1.0 - p.r_ext_ref * p.fs * p.cs * u_s ** 2)
        e = 0.0
        if p.ktc_on:
            e = sig_ktc * rng.standard_normal(B)
        if ota_noise is not None:
            v_ota = ota_noise[:, n if ota_noise.shape[1] > 1 else 0]
            if p.chop:
                v_ota = v_ota * (1.0 if n % 2 == 0 else -1.0)
            e = e + ng * v_ota
        if p.vres:
            e = e + ng * p.vres

        if p.av_strict:
            if p.av_table1 is not None:
                _check_range(x1, p.av_table1, p.vref, 1)
            if p.av_table2 is not None and p.order == 2:
                _check_range(x2, p.av_table2, p.vref, 2)
        if dyn1:
            p1, g1 = _leaky(p.a0_db, p.c1, x1, p.a0_drop, xsw, p.av_table1, p.vref, p.cp_hold1)
        if dyn2:
            p2, g2 = _leaky(a0_2, cs2, x2, drop2, xsw, p.av_table2, p.vref, p.cp_hold2)
        x1_old = x1
        x1 = np.clip(p1 * x1 + g1 * p.c1 * (u_s - y * r + e), -p.xmax, p.xmax)
        xm1 = max(xm1, float(np.max(np.abs(x1))))
        if p.order == 2:
            x2in = x1_old - p.k * y
            if np.any(e2_off):
                x2in = x2in + e2_off
            x2 = np.clip(p2 * x2 + g2 * p.c2 * x2in, -p.xmax * 2, p.xmax * 2)
            xm2 = max(xm2, float(np.max(np.abs(x2))))

    if p.av_strict:   # the final state is an OTA output level too
        if p.av_table1 is not None:
            _check_range(x1, p.av_table1, p.vref, 1)
        if p.av_table2 is not None and p.order == 2:
            _check_range(x2, p.av_table2, p.vref, 2)
    LAST_RUN.update(x1max_v=xm1 * p.vref, x2max_v=xm2 * p.vref)
    if p.order == 1:
        u_hat = S / N
    else:
        u_hat = (sumS + (p.k / p.c1) * S) / (N * (N - 1) / 2)
    # Residue-corrected estimate in the INPUT frame (C1, WO-13): the final integrator state is in the modulator frame, so it
    # is added before the demodulation by s. order 2: + x2[N]/(c1 c2 W), W = N(N-1)/2; order 1: + x1[N]/(c1 N).
    if p.order == 1:
        u_corr = (u_hat + x1 / (p.c1 * N)) * s
    else:
        u_corr = (u_hat + x2 / (p.c1 * p.c2 * (N * (N - 1) / 2))) * s
    u_hat = u_hat * s
    if return_state:
        # units of vref (differential); per-side volts = 0.5 * x * vref
        return u_hat, {"u_corr": u_corr, "x1max": xm1, "x2max": xm2,
                       "x1max_v_side": 0.5 * xm1 * p.vref,
                       "x2max_v_side": 0.5 * xm2 * p.vref,
                       "x1_final": x1, "x2_final": x2, "y": np.array(ys)}   # y: (N, B)
    return u_hat


def ota_noise_block(p, n_conv, rng):
    """OTA flicker + offset for n_conv consecutive conversions, shape (n_conv, N)."""
    total = n_conv * p.N
    v = np.zeros(total)
    if p.flicker_on:
        v = flicker_series(total, p.fs, p.ota_white, p.ota_fc, rng)
    v = v + p.vos
    return v.reshape(n_conv, p.N)


def measure_noise(p, k_avg, m_out=24, u_dc=0.1, seed=1):
    """Output noise for m_out results, each the mean of k_avg sub-conversions.

    Sub-conversions are consecutive in time, so 1/f noise is correlated as on
    silicon. With sys_chop the input polarity alternates per sub-conversion
    (k_avg rounded up to even). Returns dict with rms/mean error in volts.
    """
    rng = np.random.default_rng(seed)
    if p.sys_chop and k_avg % 2:
        k_avg += 1
    n_conv = m_out * k_avg
    noise = None
    if p.flicker_on or p.vos:
        noise = ota_noise_block(p, n_conv, rng)
    sign = None
    if p.sys_chop:
        sign = np.tile(np.array([1.0, -1.0]), n_conv // 2)
    u = np.full(n_conv, u_dc)
    uh = convert(p, u, rng=rng, ota_noise=noise, sys_sign=sign)
    out = uh.reshape(m_out, k_avg).mean(axis=1)
    err = (out - u_dc) * p.vref
    return {
        "rms_v": float(np.std(err)),
        "mean_v": float(np.mean(err)),
        "k_avg": k_avg,
        "rate": p.fs / (p.N * k_avg),
    }


def dc_sweep(p, umax=0.9, npts=401, seed=2):
    u = np.linspace(-umax, umax, npts)
    uh, st = convert(p, u, rng=np.random.default_rng(seed), return_state=True)
    return u, uh, st


def linearity(u, uh):
    """INL (endpoint fit) in ppm of FSR (FSR = 2 normalised), gain err, offset."""
    gain = (uh[-1] - uh[0]) / (u[-1] - u[0])
    off = uh[0] - gain * u[0]
    inl = uh - (gain * u + off)
    return {
        "inl_ppm": float(np.max(np.abs(inl)) / 2 * 1e6),
        "gain_err_ppm": float((gain - 1) * 1e6),
        "offset_ppm": float(off / 2 * 1e6),
        "max_abs_err": float(np.max(np.abs(uh - u))),
    }


def resolution_bits(max_abs_err):
    """Bits such that the peak error is half an LSB over a normalised FSR of 2."""
    if max_abs_err <= 0:
        return np.inf
    return float(np.log2(2.0 / (2 * max_abs_err)))


def eff_res_bits(rms_v, vref=2.048):
    """ADI/TI 'effective resolution' = log2(FSR / rms noise)."""
    return float(np.log2(2 * vref / rms_v)) if rms_v > 0 else np.inf
