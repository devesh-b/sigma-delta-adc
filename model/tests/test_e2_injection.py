"""OTA2 offset / x1 output-offset injection vs theory (s2_theory.e2_error).

Theory is independent of iadc.py. Model error = paired difference (offset on vs
off, identical inputs, ideal OTA, no noise) averaged over stratified DC inputs.
"""
import math

import numpy as np
import pytest

from model import iadc as m
from model.studies import s2_theory as th

E2 = 9e-3
TOL = 0.10


def model_err_v(N, c1, kind, e2=E2, B=2048, sys_pair=False):
    k = 0.5 if c1 < 0.2 else 1.0
    p0 = m.Params(order=2, N=N, c1=c1, c2=0.5, k=k, xmax=100)
    u = -0.5 + (np.arange(B) + 0.5) / B
    on = m.with_(p0, **{kind: e2})
    d = m.convert(on, u) - m.convert(p0, u)
    return float(np.mean(d)) * p0.vref


def agrees(meas_v, theory_v):
    return abs(meas_v - theory_v) <= TOL * abs(theory_v)


@pytest.mark.parametrize("N", [256, 1024, 4096])
@pytest.mark.parametrize("c1", [0.25, 0.125])
@pytest.mark.parametrize("kind", ["vos2", "x1_offset"])
def test_e2_matches_theory(N, c1, kind):
    meas = model_err_v(N, c1, kind)
    assert agrees(meas, th.e2_error(N, c1, E2)), (meas, th.e2_error(N, c1, E2))


@pytest.mark.parametrize("N,c1", [(256, 0.25), (1024, 0.125), (4096, 0.25)])
def test_check_rejects_wrong_sign_or_scale(N, c1):
    # non-vacuity: a model injecting e2 with the wrong sign or scale must fail the comparison
    meas = model_err_v(N, c1, "vos2")
    th_v = th.e2_error(N, c1, E2)
    assert agrees(meas, th_v)
    for wrong in (-meas, 2 * meas, 0.5 * meas, 0.0):
        assert not agrees(wrong, th_v)
    # and the model with the opposite-sign offset really produces the opposite sign
    assert not agrees(model_err_v(N, c1, "vos2", e2=-E2), th_v)


def test_sys_chop_cancels_e2():
    N, c1 = 1024, 0.125
    B = 1024
    u = -0.5 + (np.arange(B) + 0.5) / B
    p0 = m.Params(order=2, N=N, c1=c1, c2=0.5, k=0.5, xmax=100, sys_chop=True)
    pe = m.with_(p0, vos2=E2)
    s = np.concatenate([np.ones(B), -np.ones(B)])
    uu = np.tile(u, 2)
    d = m.convert(pe, uu, sys_sign=s) - m.convert(p0, uu, sys_sign=s)
    pair = (d[:B] + d[B:]) / 2
    single = abs(float(np.mean(d[:B])))
    assert single > 10 * abs(float(np.mean(pair)))
    assert single * 2.048 == pytest.approx(th.e2_error(N, c1, E2), rel=TOL)


def test_defaults_off_bit_identical():
    p = m.Params(order=2, N=256, ktc_on=True)
    u = np.linspace(-0.8, 0.8, 33)
    a = m.convert(p, u, rng=np.random.default_rng(5))
    b = m.convert(m.with_(p, vos2=0.0, x1_offset=0.0), u, rng=np.random.default_rng(5))
    assert np.array_equal(a, b)
