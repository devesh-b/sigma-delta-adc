"""S4 corner mapping and pass rule, against SPEC 3.0 / 6 numbers (written from the SPEC, not from the code under test)."""
import math

import numpy as np

from model.studies import s4_corners as s4


def test_mapping_hits_spec_limits_at_worst_corner_and_nominal_at_tt27():
    p, ax = s4.point("ss", -40, 3.0, 2e6)
    assert math.isclose(p.tau_in, 18.75e-9, rel_tol=1e-9)              # SPEC 3.0: tau <= 18.75 ns at ss/-40/3.0
    assert math.isclose(p.tau_ref, 10e-9, rel_tol=1e-9)                # on-chip tau_ref <= 10 ns
    assert math.isclose(ax["r"], 1e-4, rel_tol=1e-9)                   # reset r <= 1e-4
    q, _ = s4.point("ss", 125, 3.0, 2e6)
    tab = dict(q.av_table1)
    assert tab[0.0] == 80.0 and tab[1.4] == 75.0                       # A(0) >= 80 dB, A >= 75 dB to 1.4 V
    assert math.isclose(q.comp_offset * q.vref, 20e-3) and abs(q.vos) == 9e-3 and abs(q.vos2) == 9e-3
    _, ax = s4.point("ff", 125, 3.6, 0.25e6)
    assert math.isclose(ax["i_leak"], 100e-12, rel_tol=1e-9)           # leakage <= 100 pA at ff/125/3.6
    n, axn = s4.point("tt", 27, 3.3, 2e6)
    assert dict(n.av_table1)[0.0] == 90.0 and math.isclose(n.tau_in, 8e-9) and axn["r"] == 1e-5
    assert math.isclose(n.temp_k, 300.15) and math.isclose(s4.point("ss", 125, 3.0, 2e6)[0].temp_k, 398.15)


def test_stress_bounds_and_63_points():
    from design import params as dp
    assert len(dp.PVT_LIST_ANALOG) == 63
    for pv in dp.PVT_LIST_ANALOG:
        st = s4.stress(pv["proc"], pv["temp"], pv["vapwr"])
        assert 0.0 <= st["gain"] <= 1.0 and 0.0 <= st["speed"] <= 1.0
    assert s4.stress("tt", 27, 3.3) == {"gain": 0.0, "speed": 0.0}
    assert s4.stress("ss", 125, 3.0)["gain"] == 1.0 and s4.stress("ss", -40, 3.0)["speed"] == 1.0


def _row(**kw):
    r = {"point": "ss/125/3.0", "T": 125, "fs": 2e6, "n15": 1.0, "n240": 3.0, "inl": 5.0, "off": 2.0, "gain": 100.0, "mem": 0.1}
    r.update(kw)
    return r


def test_pass_rule_rejects_each_spec_and_nan():
    assert s4.spec_fails([_row()]) == []
    for k, bad in (("n15", 2.6), ("n240", 5.1), ("inl", 20.5), ("off", 5.1), ("gain", 5001.0), ("mem", 0.6), ("inl", float("nan"))):
        f = s4.spec_fails([_row(**{k: bad})])
        assert f and "ss/125/3.0" in f[0] and k in f[0]


def test_mc_rule_needs_mu_plus_3sigma_and_every_sample():
    ok = {"tag": "t", "point": "tt/27/3.3", "fs": 2e6, "inl": [5.0] * 10 + [5.2] * 10, "gain": [1.0] * 20, "off": [2.0] * 20}
    assert s4.mc_verdict(ok) == []
    one_out = dict(ok, inl=[5.0] * 19 + [21.0])                         # a single sample outside (mu+3 sigma also fails)
    assert s4.mc_verdict(one_out)
    wide = dict(ok, off=[0.0] * 10 + [4.9] * 10)                        # every sample inside, but mu + 3 sigma = 2.45 + 3*2.5 > 5
    assert s4.mc_verdict(wide)


def test_memory_metric_sees_reset_residue():
    p, ax = s4.point("tt", 27, 3.3, 2e6, N=1024)
    lo = s4.memory_uv(p, 1e-4)
    hi = s4.memory_uv(p, 1e-2)
    assert 90 < hi / lo < 110                                          # linear in r (theory: 2 r x1_prev / (c1 (N-1)))
    # theory bound: |x1_prev| <= x1max 1.22 V => memory <= 2 r 1.22/(c1 (N-1)) = 2*1e-2*1.22/(0.125*1023) = 191 uV
    assert 0 < hi <= 191.0 * 1.05
    assert s4.memory_uv(p, 0.0) < 0.01                                  # clean reset: no memory


def test_n240_not_gated_where_unreachable_but_n15_is():
    low = _row(fs=0.25e6, T=27, n240=9.0)
    assert s4.spec_fails([low]) == []                                  # 240 SPS needs fs >= 2*240*1024 = 0.49 MHz
    assert s4.spec_fails([_row(fs=0.25e6, T=27, n15=3.0)])             # n15 stays gated at 0.25 MHz
    assert s4.spec_fails([_row(fs=0.5e6, n240=9.0)])


def test_n15_limits_per_d27():
    # D27: 2.5 uV at fs >= 2 MHz at every T; at 0.25 MHz 2.5 up to 85 C and 3.0 at 125 C
    assert s4.spec_fails([_row(fs=2e6, T=125, n15=2.6)])
    assert not s4.spec_fails([_row(fs=2e6, T=125, n15=2.5)])
    assert s4.spec_fails([_row(fs=0.25e6, T=27, n15=2.6, n240=1.0)])
    assert s4.spec_fails([_row(fs=0.25e6, T=85, n15=2.6, n240=1.0)])
    assert not s4.spec_fails([_row(fs=0.25e6, T=125, n15=2.98, n240=1.0)])
    assert s4.spec_fails([_row(fs=0.25e6, T=125, n15=3.01, n240=1.0)])
    assert s4.limit(_row(fs=0.25e6, T=125), "n15") == 3.0 and s4.limit(_row(fs=2e6, T=125), "n15") == 2.5


def test_n240_gated_at_5uv_where_reachable():
    assert s4.spec_fails([_row(fs=2e6, n240=5.1)]) and not s4.spec_fails([_row(fs=2e6, n240=4.9)])
    assert not s4.spec_fails([_row(fs=0.25e6, T=27, n240=20.0)])        # unreachable below 0.49 MHz: reported, not gated


def _pq():
    return s4.point("tt", 27, 3.3, 2e6, N=256)[0]


def test_cmrr_theory_sysoff_equals_eps_dvcm_and_sys_on_cancels():
    eps = 0.0075
    rows = s4.cmrr_eval(_pq(), eps)
    by = {r["vin_cm"]: r for r in rows}
    assert math.isinf(by[1.0]["on_db"])                                 # dVcm = 0: nothing to reject
    for vc in (0.2, 2.0):
        dv = vc - 1.0
        assert math.isclose(by[vc]["off_err_v"], eps * abs(dv), rel_tol=0.02)     # theory: sys-off error = eps * dVcm
        assert by[vc]["on_err_v"] < 1e-2 * by[vc]["off_err_v"]                    # sys-on residual ~ 0
        assert 40 < by[vc]["off_db"] < 60   # D32: 42.5 dB at 0.75 % FAILS the 60 dB gate and by[vc]["on_db"] > 80
        assert math.isclose(by[vc]["off_db"], 20 * math.log10(1 / eps), abs_tol=0.3)   # 42.5 dB


def test_cmrr_flip_copy_fails_sys_on_and_big_mismatch_fails_sys_off():
    bad = s4.cmrr_eval(_pq(), 0.0075, flip=True)
    assert all(r["on_db"] < 100 for r in bad if r["dvcm"])             # term flips with the input: sys chop cannot remove it
    assert s4.cmrr_fails(bad, "t") and "sys on" in s4.cmrr_fails(bad, "t")[0]
    big = s4.cmrr_eval(_pq(), 0.03)
    assert s4.cmrr_fails(big, "t") and any("sys off" in f for f in s4.cmrr_fails(big, "t"))
    assert s4.cmrr_fails([{"eps": 0.0, "vin_cm": 0.2, "on_db": float("nan"), "off_db": 90.0}], "t")        # NaN fails


def test_cmrr_gate_is_60_db_sys_off_and_eps_for_it_is_0p1_percent():
    assert s4.CMRR_OFF_DB == 60.0 and s4.CMRR_ON_DB == 100.0 and math.isclose(s4.EPS_FOR_OFF_GATE, 1e-3)
    ok = [{"eps": 1e-3, "vin_cm": 2.0, "on_db": 120.0, "off_db": 60.5}]
    assert not s4.cmrr_fails(ok, "t")
    assert s4.cmrr_fails([dict(ok[0], off_db=59.0)], "t") and s4.cmrr_fails([dict(ok[0], on_db=99.0)], "t")
    assert s4.cmrr_fails(s4.cmrr_eval(_pq(), 0.0075), "t")       # spec 3 sigma mismatch: sys-off 42.5 dB < 60 -> REJECT


def test_eps_eff_d33_hand_values_and_gate_behaviour():
    cs = 0.5e-12
    # hand: 0.25 fF / 0.5 pF = 5.0e-4; (20 fF / 0.5 pF) * 0.0075 = 3.0e-4; injection 2.8e-4; linear worst-case sum 1.08e-3
    assert math.isclose(s4.eps_eff(cs, 0.0075), 5.0e-4 + 3.0e-4 + 2.8e-4, rel_tol=1e-9)
    assert math.isclose(20 * math.log10(1 / s4.eps_eff(cs, 0.0075)), 59.33, abs_tol=0.05)
    # terms are absolute values (worst-case signs)
    assert math.isclose(s4.eps_eff(cs, -0.0075, dcp=-0.25e-15), s4.eps_eff(cs, 0.0075), rel_tol=1e-12)
    # dCp,top 2 fF (hand: 4e-3 + 3e-4 + 2.8e-4 = 4.58e-3 = 46.8 dB) must fail sys-off; a small asymmetry (0.05 fF: 1e-4+3e-4+2.8e-4 = 6.8e-4, 63.3 dB) passes
    bad = s4.cmrr_eval(_pq(), s4.eps_eff(cs, 0.0075, dcp=2e-15))
    assert any("sys off" in f for f in s4.cmrr_fails(bad, "t"))
    good = s4.cmrr_eval(_pq(), s4.eps_eff(cs, 0.0075, dcp=0.05e-15))
    assert not s4.cmrr_fails(good, "t")
    # the sys-off CMRR follows 1/eps_eff (theory), not the old eps_Cs term
    by = {r["vin_cm"]: r for r in bad}
    assert math.isclose(by[2.0]["off_db"], 20 * math.log10(1 / 4.58e-3), abs_tol=0.3)


def test_margin_helper():
    assert s4._marg({"n15": 1.25, "fs": 2e6, "T": 27, "point": "x"}, "n15") == "+100 %"       # limit 2.5 / 1.25 - 1
    assert s4._marg({"n15": 0.0, "fs": 2e6, "T": 27, "point": "x"}, "n15") == "n/a"
