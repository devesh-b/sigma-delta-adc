"""S3 budget helpers vs theory. Expected numbers are written from SPEC / charge conservation, not computed by the code under test."""
import math

import numpy as np
import pytest

from model.studies import s3_budget as s3


def test_budget_constants_from_wo05():
    assert s3.BUDGET == {"noise_uv": 2.5, "inl_ppm": 20.0, "offset_uv": 5.0, "gain_ppm": 5000.0}


def test_leakage_formula():
    # 100 pA / (0.25 MHz * 0.5 pF) = 0.8 mV ; 1 nA at 2 MHz, 0.5 pF = 1 mV
    assert math.isclose(s3.leak_offset(100e-12, 0.25e6, 0.5e-12), 0.8e-3, rel_tol=1e-9)
    assert math.isclose(s3.leak_offset(1e-9, 2e6, 0.5e-12), 1e-3, rel_tol=1e-9)


def test_ota_thermal_mapping():
    assert math.isclose(s3.excess_from_en(6.9), 1.5)          # iadc.py calibration point
    assert s3.excess_from_en(14) > s3.excess_from_en(10) > s3.excess_from_en(5) > 1.0


def test_rel_ok_rejects_wrong_values():
    assert s3.rel_ok(10.5, 10.0) and not s3.rel_ok(15.0, 10.0) and not s3.rel_ok(5.0, 10.0)
    assert not s3.rel_ok(float("nan"), 10.0)


def test_reset_residue_closed_form():
    # 2 r x1max / (c1 (N-1)): r 1e-2, x1max 1.22 V, c1 0.125, N 1024 -> 2*12.2e-3/(0.125*1023) = 190.8 uV
    N, r = 1024, 1e-2
    u = -0.5 + (np.arange(512) + 0.5) / 512
    x0 = r * s3.X1MAX_V / s3.VREF
    sim = float(np.mean(s3.x1init_sim(u, N, x0) - s3.x1init_sim(u, N, 0.0))) * s3.VREF * 1e6
    assert math.isclose(sim, 190.8, rel_tol=0.05)
    assert not math.isclose(sim, 2 * 190.8, rel_tol=0.1)       # check is not vacuous
    mod = s3.offset_uv(s3.ideal_base(x1_offset=r * s3.X1MAX_V, N=N, sys_chop=False), False)
    assert math.isclose(mod, 190.8, rel_tol=0.10)


def test_ktc_theory_formula():
    # per-cycle diff sigma = sqrt(2 events * 2kT/Cs); Cs 0.5 pF, 300 K: 181.6 uV ; weighted by sqrt(sum w^2)/sum w ~ 2/sqrt(3N)
    N = 4096
    assert math.isclose(s3.ktc_theory_uv(0.5e-12, N), 181.6 * 2 / math.sqrt(3 * N), rel_tol=0.02)


def test_offset_sys_pair_cancels_and_nonvac():
    p = s3.ideal_base(vos2=9e-3, sys_chop=False)
    assert math.isclose(s3.offset_uv(p, False), 35.16, rel_tol=0.05)     # 2*9e-3/(0.125*4095)
    assert abs(s3.offset_uv(p, True)) < 0.5
    assert not abs(s3.offset_uv(p, False)) < 0.5                         # the cancel check can fail


def test_bad_ota_rejects_on_inl_and_spec_ota_passes():
    bad = s3.ideal_base(a0_db=70, a0_drop=0.9, vlin_diff=0.8)
    good = s3.ideal_base(a0_db=80, a0_drop=0.9, vlin_diff=2.0)
    assert s3.inl_gain(bad)[0] > 20.0
    assert s3.inl_gain(good)[0] < 20.0
