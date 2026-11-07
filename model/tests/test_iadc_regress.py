"""Backward-compat regression: new iadc fields unset => report_design.md numbers.

Expected values are the pre-change numbers in model/out/report_design.md
(not recomputed from the code). REGRESS_A0_DROP env var overrides a0_drop so
the non-vacuity run (a0_drop=0 must fail) can be done from the command line.
"""
import os

import pytest

from model import iadc as m

EXPECT_NOISE = {240: 2.51, 60: 1.31, 15: 0.51, 3.75: 0.26}   # uV rms
EXPECT_INL = 71.0                                             # ppm (71.3)
EXPECT_GAIN = -459.0                                          # ppm
TOL = 0.10


def design_params(a0_drop):
    return m.with_(m.Params(), fs=2e6, N=1024, cs=1e-12, a0_db=75, a0_drop=a0_drop, ktc_on=True,
                   flicker_on=True, vos=3e-3, chop=True, vres=5e-6, sys_chop=True,
                   ref_mode="separate", tau_in=20e-9, tau_ref=10e-9)


def measure(a0_drop, noise=True):
    p0 = design_params(a0_drop)
    u, uh, _ = m.dc_sweep(m.with_(p0, ktc_on=False, flicker_on=False, vos=0, vres=0), umax=0.9, npts=401)
    lin = m.linearity(u, uh)
    out = {"inl": lin["inl_ppm"], "gain": lin["gain_err_ppm"], "noise": {}}
    if noise:
        for rate in EXPECT_NOISE:
            k = max(1, round(p0.fs / (rate * p0.N)))
            out["noise"][rate] = m.measure_noise(p0, k, m_out=24)["rms_v"] * 1e6
    return out


def failures(res, check_noise=True):
    bad = []
    if abs(res["inl"] - EXPECT_INL) > TOL * EXPECT_INL:
        bad.append(f"INL {res['inl']:.1f}")
    if abs(res["gain"] - EXPECT_GAIN) > TOL * abs(EXPECT_GAIN):
        bad.append(f"gain {res['gain']:.0f}")
    if check_noise:
        for r, e in EXPECT_NOISE.items():
            v = res["noise"].get(r)
            if v is None or v != v or abs(v - e) > TOL * e:
                bad.append(f"noise@{r} {v}")
    return bad


def test_design_point_reproduced():
    drop = float(os.environ.get("REGRESS_A0_DROP", "0.9"))
    assert failures(measure(drop)) == []


def test_check_is_not_vacuous_a0_drop_zero():
    # static part only: with a0_drop=0 the INL/gain check must reject
    assert failures(measure(0.0, noise=False), check_noise=False) != []


def test_vlin_equivalent_to_xswing():
    # vlin_diff = xswing*vref must reproduce the legacy xswing behaviour
    p = m.with_(design_params(0.9), ktc_on=False, flicker_on=False, vos=0, vres=0)
    _, a, _ = m.dc_sweep(p, npts=101)
    _, b, _ = m.dc_sweep(m.with_(p, vlin_diff=p.xswing * p.vref, xswing=99.0), npts=101)
    assert abs(a - b).max() == 0.0
    _, c, _ = m.dc_sweep(m.with_(p, vlin_diff=0.5), npts=101)
    assert abs(a - c).max() > 1e-4


def test_white_split_identity_at_c1_025_and_scaling():
    p = m.with_(design_params(0.9), flicker_on=False, vos=0, vres=0, chop=False)
    a = m.measure_noise(p, 8)["rms_v"]
    ref = m.with_(p, white_ng_ref=m.Params().noise_gain)   # c1=0.25 -> identical
    b = m.measure_noise(ref, 8)["rms_v"]
    assert a == b
    c = m.measure_noise(m.with_(ref, c1=0.125), 8)["rms_v"]
    assert c > a
