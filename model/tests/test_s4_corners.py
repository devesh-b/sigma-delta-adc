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
    r = {"point": "ss/125/3.0", "fs": 2e6, "n15": 1.0, "n240": 3.0, "inl": 5.0, "off": 2.0, "gain": 100.0, "mem": 0.1}
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
    low = _row(fs=0.25e6, n240=9.0)
    assert s4.spec_fails([low]) == []                                  # 240 SPS needs fs >= 2*240*1024 = 0.49 MHz
    assert s4.spec_fails([_row(fs=0.25e6, n15=3.0)])                   # n15 stays gated at 0.25 MHz
    assert s4.spec_fails([_row(fs=0.5e6, n240=9.0)])
