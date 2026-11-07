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
    cp_ratio: float = 0.3        # parasitic at OTA input / Cs (noise gain)

    cs: float = 1e-12            # sampling cap per side [F]
    temp_k: float = 300.0
    ktc_events: float = 2.0      # sampling events per cycle (input + ref)
    ktc_excess: float = 1.5      # OTA thermal contribution factor
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


def _leaky(a0_db, c, x=None, drop=0.0, xswing=1.0):
    """Pole p and gain g of an SC integrator with finite OTA gain.

    With drop > 0 the gain falls quadratically with the output state x,
    A(x) = A0 * max(0.02, 1 - drop * (x / xswing)^2): the usual source of
    INL in a real OTA (output stage leaving saturation).
    """
    if not np.isfinite(a0_db):
        return 1.0, 1.0
    a = 10 ** (a0_db / 20)
    if drop and x is not None:
        a = a * np.maximum(0.02, 1.0 - drop * (x / xswing) ** 2)
    g = 1.0 / (1.0 + (1.0 + c) / a)
    p = (1.0 + 1.0 / a) * g
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


def convert(p, u, rng=None, ota_noise=None, sys_sign=None, return_state=False):
    """Run one conversion per batch element.

    u          : (B,) normalised DC inputs
    ota_noise  : (B, N) OTA input-referred noise in volts (flicker + offset),
                 before noise gain and chopping; None = none
    sys_sign   : (B,) +/-1 input polarity for system-level chopping
    returns u_hat (B,) normalised.
    """
    rng = rng or np.random.default_rng(0)
    u = np.asarray(u, dtype=float)
    B, N = u.size, p.N
    s = np.ones(B) if sys_sign is None else np.asarray(sys_sign, dtype=float)
    u_in = u * s

    p1, g1 = _leaky(p.a0_db, p.c1)
    p2, g2 = _leaky(p.a0_db, p.c2)

    e_in = np.exp(-p.t_half / p.tau_in) if p.tau_in > 0 else 0.0
    e_ref = np.exp(-p.t_half / p.tau_ref) if p.tau_ref > 0 else 0.0
    share = p.cs / (p.cs + p.cd_ref)

    sig_ktc = 0.0
    if p.ktc_on:
        sig_ktc = np.sqrt(p.ktc_events * 2 * K_B * p.temp_k / p.cs * p.ktc_excess) / p.vref
    ng = p.lf_gain / p.vref

    x1 = np.zeros(B)
    x2 = np.zeros(B)
    vnode = np.ones(B)           # reference node (normalised)
    cap_prev = np.zeros(B)       # shared Cs bottom-plate state after transfer
    S = np.zeros(B)
    sumS = np.zeros(B)
    xm1 = xm2 = 0.0

    for n in range(N):
        q = x2 if p.order == 2 else x1
        dec = q + p.comp_offset
        if p.comp_noise:
            dec = dec + p.comp_noise * rng.standard_normal(B)
        y = np.where(dec >= 0, 1.0, -1.0)
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

        e = 0.0
        if p.ktc_on:
            e = sig_ktc * rng.standard_normal(B)
        if ota_noise is not None:
            v_ota = ota_noise[:, n]
            if p.chop:
                v_ota = v_ota * (1.0 if n % 2 == 0 else -1.0)
            e = e + ng * v_ota
        if p.vres:
            e = e + ng * p.vres

        if p.a0_drop:
            p1, g1 = _leaky(p.a0_db, p.c1, x1, p.a0_drop, p.xswing)
            p2, g2 = _leaky(p.a0_db, p.c2, x2, p.a0_drop, p.xswing)
        x1_old = x1
        x1 = np.clip(p1 * x1 + g1 * p.c1 * (u_s - y * r + e), -p.xmax, p.xmax)
        xm1 = max(xm1, float(np.max(np.abs(x1))))
        if p.order == 2:
            x2 = np.clip(p2 * x2 + g2 * p.c2 * (x1_old - p.k * y), -p.xmax * 2, p.xmax * 2)
            xm2 = max(xm2, float(np.max(np.abs(x2))))

    if p.order == 1:
        u_hat = S / N
    else:
        u_hat = (sumS + (p.k / p.c1) * S) / (N * (N - 1) / 2)
    u_hat = u_hat * s
    if return_state:
        return u_hat, {"x1max": xm1, "x2max": xm2}
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
