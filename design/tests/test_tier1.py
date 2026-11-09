"""Tests for the tier-1 SC modulator generator and checker (WO-07).

Fast unit tests need no simulator. The integration tests run ngspice (skipped when absent).
Expected values are theory (SPEC 3.7 reconstruction, ideal loop recursion), not model/iadc.py.
"""
import os
import shutil
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "tier1"))
import params as P  # noqa: E402
import gen_tier1 as G  # noqa: E402
import tier1_tb as TB  # noqa: E402

HAVE_NGSPICE = shutil.which(os.environ.get("NGSPICE", "ngspice")) is not None


def test_reconstruct_exact_against_ideal_loop():
    for u in (-0.9, -0.31, 0.0, 0.2718, 0.9):
        for n in (16, 64, 256):
            y, x2 = TB.ideal_loop(u, n, P.C1, P.C2, P.K)
            assert abs(TB.reconstruct(y, x2, n, P.C1, P.C2, P.K) - u) < 1e-12


def test_reconstruct_check_is_not_vacuous():
    y, x2 = TB.ideal_loop(0.7, 256, P.C1, P.C2, P.K)
    # dropping the residue, a wrong k/c1, or a wrong c1 must each exceed the null tolerance
    assert abs(TB.reconstruct(y, 0.0, 256, P.C1, P.C2, P.K) - 0.7) > 10 * P.TIER1_NULL_TOL
    assert abs(TB.reconstruct(y, x2, 256, P.C1, P.C2, 0.25) - 0.7) > 10 * P.TIER1_NULL_TOL
    assert abs(TB.reconstruct(y, x2, 256, 2 * P.C1, P.C2, P.K) - 0.7) > 10 * P.TIER1_NULL_TOL


def test_inl_gain_metric():
    u = np.linspace(-0.9, 0.9, 11)
    m = TB.inl_gain(u, 1.0003 * u + 5e-6)
    assert m["inl_ep_ppm"] < 1e-6 and abs(m["gain_err"] - 3e-4) < 1e-9
    bow = 1.0 * u + 40e-6 * (1 - (u / 0.9) ** 2)          # 40e-6 u bow at mid-scale
    assert TB.inl_gain(u, bow)["inl_ep_ppm"] > 15


def test_deck_matches_design_point_and_audit():
    deck, meta = G.build_deck({"u_list": (0.1, -0.2), "n": 32})
    ok, counts, msgs = TB.audit_netlist(deck)
    assert ok, msgs
    assert "M" not in counts and "X" not in counts and "D" not in counts and "Q" not in counts
    low = deck.lower()
    assert deck.count(" SWM\n") == 28                      # 14 switches per differential side
    for line in ("cs1p b1p tp1p 5e-13", "cint1p vg1p o1p 4e-12", "cs2p b2p tp2p 5e-13",
                 "cint2p vg2p o2p 1e-12", "ckp bkp tp2p 2.5e-13"):
        assert line in low, line
    assert "rpad_vinp vinp_s vinp 500" in low and "cpad_vrefn vrefn 0 5e-12" in low
    assert abs(meta["T"] - 0.5e-6) < 1e-15 and meta["nrst"] >= 2
    assert abs(meta["cfg"]["cs1"] / meta["cfg"]["cint1"] - 0.125) < 1e-12
    assert abs(meta["cfg"]["ck"] / meta["cfg"]["cint2"] - P.C2 * P.K) < 1e-12


def test_audit_rejects_foreign_parts():
    deck, _ = G.build_deck({"n": 8})
    bad = deck.replace(".tran", "M1 a b c d nfet W=1u L=1u\n.tran")
    assert not TB.audit_netlist(bad)[0]
    assert not TB.audit_netlist(deck.replace(".model SWM SW", ".model SWX SW"))[0]


def test_dac_flip_swaps_steering():
    a, _ = G.build_deck({"n": 8})
    b, _ = G.build_deck({"n": 8, "dac_flip": True})
    assert "V(ypos)" in a.split("Bd_p_hi")[1].split("\n")[0]
    assert "V(yneg)" in b.split("Bd_p_hi")[1].split("\n")[0]


def test_frozen_options_present():
    o = P.SPICE_OPTIONS_TIER1
    assert o["method"] in ("trap", "gear") and 0 < o["reltol"] <= 1e-3 and o["chgtol"] > 0


@pytest.mark.skipif(not HAVE_NGSPICE, reason="ngspice not installed")
def test_ngspice_null_and_broken(tmp_path):
    out = str(tmp_path)
    good = TB.dc_metrics(TB.null_cfg(n=32, m=3), "t_null", out)
    assert good["ok"], good["problems"]
    assert good["max_abs_err"] < P.TIER1_NULL_TOL
    bad = TB.dc_metrics(TB.null_cfg(dict(dac_flip=True), n=32, m=3), "t_flip", out)
    assert (not bad["ok"]) or bad["max_abs_err"] > 100 * P.TIER1_NULL_TOL
    c1 = TB.dc_metrics(TB.null_cfg(dict(cs1=2 * P.CS1), n=32, m=3), "t_c1", out)
    assert c1["max_abs_err"] > 10 * P.TIER1_NULL_TOL


@pytest.mark.skipif(not HAVE_NGSPICE, reason="ngspice not installed")
def test_truncated_run_is_caught(tmp_path):
    # trap + reltol 1e-5 ends with "timestep too small" on the spec deck: the run checks must flag it
    # (final time != tstop and a log error), not return numbers as if the run were good.
    opts = dict(P.SPICE_OPTIONS_TIER1, method="trap", reltol=1e-5)
    r = TB.dc_metrics(TB.spec_cfg(dict(options=opts), n=256, m=2), "t_trunc", str(tmp_path))
    assert not r["ok"]
    assert any("final time" in p for p in r["problems"]) and any("timestep" in p.lower() for p in r["problems"])


# ---------------------------------------------------------------- WO-08 additions
def test_closed_forms_match_brute_force_sums():
    for n in (64, 256, 1024):
        w = np.arange(n - 1, -1, -1, dtype=float)
        assert abs(TB.noise_gain_u(n) - np.sqrt(np.sum(w ** 2)) / np.sum(w)) < 1e-12
        alt = np.sum(w * (-1.0) ** np.arange(n)) / np.sum(w)
        assert abs(TB.chop_resid_V(1.0, n) - alt) < 1e-12              # lf*Vos/(N-1), N even
        assert abs(TB.e2_closed_V(1.0, 0.125, n) - 2.0 / (0.125 * (n - 1))) < 1e-9


def test_rel_sym_rejects_factor_two():
    assert TB.rel_sym(1.0, 1.1) < 0.1 and TB.rel_sym(1.0, 2.0) > 0.30 and TB.rel_sym(0.0, 0.0) == 0.0


def test_v2_deck_options_present_and_audited():
    deck, meta = G.build_deck(TB.v2_cfg(dict(avdrop=0.9, boost=True, cs1_mm=0.0025, rsrc=1e3, cext=1e-8, chop=True, nrst=4, noise1=1e-3), n=8, m=2))
    ok, counts, msgs = TB.audit_netlist(deck)
    assert ok, msgs
    low = deck.lower()
    for tok in ("stp1d tp1p tp1n", "rsrc_vinp", "cext_vinp", "vchp chp", "vnz1 nz1 0 pwl", "cpv1p vg1p 0", "max(0.02,1-0.9"):
        assert tok in low, tok
    assert "stp1p tp1p cm" not in low                               # D12: no top-plate tie to cm
    assert "cs1p b1p tp1p 5.00625e-13" in low and "cs1n b1n tp1n 4.99375e-13" in low
    assert abs(P.TIER1_CP_VG - 0.2619e-12) < 1e-15


def test_boost_doubles_gm_and_tail():
    a, _ = G.build_deck(TB.v2_cfg(dict(), n=8, m=2))
    b, _ = G.build_deck(TB.v2_cfg(dict(boost=True), n=8, m=2))
    ga = float(a.split("Bgp1 0 o1p I = -0.5*(u(")[1].split("*V(f1)")[0])
    gb = float(b.split("Bgp1 0 o1p I = -0.5*(u(")[1].split("*V(f1)")[0])
    assert abs(gb / ga - 2.0) < 1e-6


def test_chop_requires_even_cycles():
    with pytest.raises(ValueError):
        G.build_deck({"chop": True, "nrst": 3, "n": 256})


@pytest.mark.skipif(not HAVE_NGSPICE, reason="ngspice not installed")
def test_late_swap_breaks_pair_residual(tmp_path):
    base = dict(TB.NULL_CFG, roff=1e14, nrst=4, n=64, u_list=(0.3, -0.3), vos1=9e-3, chop=True)
    res = []
    for late in (False, True):
        r = TB.run_deck(dict(base, late=late), f"t_late{int(late)}", str(tmp_path))
        assert r["ok"], r["problems"]
        uh = TB.u_hat_of(r)
        res.append(abs((uh[0] - uh[1]) / 2 - 0.3) * P.VREF_NOM)
    assert res[0] < P.TIER1_PAIR_RESID_V < res[1]


def test_nod12_settle_ratio_limits():
    r = TB.nod12_settle_ratio(256)
    assert 0.05 < r < 0.09                                  # about 2*tau/N with tau 9.5 cycles
    assert TB.nod12_settle_ratio(4096) < r / 10             # falls as 1/N


# ---------------------------------------------------------------- WO-09 (S5c) additions
def _gm_ip(deck, k):
    """(gm, i_tail) of OTAk from the v2 deck text: Bgp = -0.5*(u(gm*V(f))*ip*tanh(...) + ...)."""
    ln = [l for l in deck.splitlines() if l.startswith(f"Bgp{k} ")][0]
    gm = float(ln.split("(u(")[1].split("*V(f")[0])
    ip = float(ln.split(")*")[1].split("*tanh")[0])
    return gm, ip


def test_separate_ota_sr_gbw_and_boost_scope():
    cl1, cl2 = P.TIER1_CL1, P.TIER1_CL2
    a, _ = G.build_deck(TB.v2_cfg(dict(), n=8, m=2))
    g1, i1 = _gm_ip(a, 1)
    g2, i2 = _gm_ip(a, 2)
    assert abs(i1 / (12e6 * cl1) - 1) < 1e-6 and abs(i2 / (P.TIER1_SR2 * cl2) - 1) < 1e-6      # OTA1 12 V/us, OTA2 25 V/us
    assert abs(g1 / (6.283185307179586 * 10e6 * cl1) - 1) < 1e-6 and abs(g2 / (6.283185307179586 * 10e6 * cl2) - 1) < 1e-6
    b, _ = G.build_deck(TB.v2_cfg(dict(boost=True), n=8, m=2))
    c, _ = G.build_deck(TB.v2_cfg(dict(boost=True, boost1_only=True), n=8, m=2))
    assert abs(_gm_ip(b, 1)[1] / i1 - 2) < 1e-6 and abs(_gm_ip(b, 2)[1] / i2 - 2) < 1e-6      # boost scales both
    assert abs(_gm_ip(c, 1)[1] / i1 - 2) < 1e-6 and abs(_gm_ip(c, 2)[1] / i2 - 1) < 1e-6      # OTA1 only
    d, _ = G.build_deck(TB.v2_cfg(dict(sr=9e6, sr2=15e6, gbw2=20e6), n=8, m=2))
    assert abs(_gm_ip(d, 1)[1] / (9e6 * cl1) - 1) < 1e-6 and abs(_gm_ip(d, 2)[1] / (15e6 * cl2) - 1) < 1e-6
    assert abs(_gm_ip(d, 2)[0] / (6.283185307179586 * 20e6 * cl2) - 1) < 1e-6
    e, _ = G.build_deck(TB.v2_cfg(dict(sr=1e9), n=8, m=2))                                    # ideal OTA1 must not cap OTA2
    assert _gm_ip(e, 2)[1] > P.TIER1_SR2 * cl2 * 0.99


def test_knee_of_uses_all_higher_points_and_interpolates():
    pairs = [(8, 100.0), (10, 20.0), (12, 5.0), (15, 1.0)]
    g, it = TB.knee_of(pairs, 13.3)
    assert g == 12 and 10 < it < 12
    assert TB.knee_of([(8, 1.0), (10, 50.0), (12, 2.0)], 13.3)[0] == 12      # a failing higher point moves the knee up
    assert TB.knee_of(pairs, 0.1) == (None, None)
    assert TB.knee_of([(8, 1.0), (10, 0.5)], 13.3) == (8, None)


def test_eps_eff_sign_and_limits():
    cs = P.CS1
    assert TB.eps_eff_closed(0, 0, 0.0075, cs) == 0.0                         # Cp,top = 0: first-order cancellation
    assert abs(TB.eps_eff_closed(20e-15, 0, 0.0075, cs) - 0.04 * 0.0075 / 1.04) < 1e-12
    m, p = TB.eps_eff_closed(20e-15, 0.25e-15, 0.0075, cs), TB.eps_eff_closed(20e-15, 0.25e-15, 0.0075, cs, plus=True)
    assert abs(m - (3e-4 - 5e-4) / 1.04) < 1e-9 and abs(p - (3e-4 + 5e-4) / 1.04) < 1e-9 and abs(p - m) > 0.25 * abs(m)   # the sign test can discriminate


def test_slope_cmrr_is_a_slope_not_an_offset():
    v = (0.2, 1.0, 2.0)
    sl, db = TB.slope_cmrr(v, [5e-6 + 1e-3 * x for x in v])                    # constant 5 uV is ignored
    assert abs(sl - 1e-3) < 1e-12 and abs(db - 60.0) < 1e-6
    assert TB.slope_cmrr(v, [5e-6] * 3)[1] > 179                              # flat: sits at the floor
    assert TB.slope_cmrr(v, [0.0, 4e-3, 8e-3])[1] < 52                        # 2 fF / 0.5 pF = 4e-3 -> 48 dB class


def test_pin_closed_form_limit_and_drift_closed_form():
    fs, cp, dr = 2e6, 15e-15, 50.0
    big = TB.pin_eps_closed(500.0, dr, 1e-6, cp, fs)                          # tau >> T: review form dr fs Cp'
    assert abs(big / (dr * fs * (P.CS1 * cp / (P.CS1 + cp))) - 1) < 0.30
    assert abs(TB.pin_eps_closed(500.0, dr, 5e-12, cp, fs)) < 1e-12           # settled pad: no pin-path error
    assert abs(TB.drift_closed(2e6, 4096, 100e-12, 1) + 100e-12 * 4096 / 2e6 / (P.CS1 + P.CINT1 + P.TIER1_CP_VG)) < 1e-9
    assert TB.drift_limit_ok(-0.086) and not TB.drift_limit_ok(-2.1)


def test_s5c_deck_options_audited():
    deck, _ = G.build_deck(TB.v2_cfg(dict(cptop=20e-15, dcptop=1e-15, ileak=1e-10, rbl=0, rfl=1e16, drsrc=50.0, roff=1e16), n=8, m=2))
    ok, counts, msgs = TB.audit_netlist(deck)
    assert ok, msgs
    low = deck.lower()
    assert "cptop1p tp1p 0 2.050000e-14" in low and "cptop1n tp1n 0 1.950000e-14" in low
    assert "blk1p vg1p 0 i = 1.0" in low and "rbl1p" not in low and "rfl_tp1p tp1p cm 1e+16" in low
    assert "rsrc_vinn vinn_s vinn_pin 50" in low and "rsrc_vinp" not in low
    d0, _ = G.build_deck(TB.v2_cfg(dict(), n=8, m=2))
    assert "cptop1" not in d0.lower() and "blk1" not in d0.lower() and "rbl1p vg1p cm 1e+12" in d0.lower().replace("1e12", "1e+12")


def test_s5c_defaults_leave_wo08_deck_elements():
    deck, _ = G.build_deck(TB.v2_cfg(dict(), n=8, m=2))
    low = deck.lower()
    assert "rbl1p vg1p cm 1e+12" in low and "rfl_tp1p tp1p cm 1e+13" in low


# ---------------------------------------------------------------- WO-12 (S5d) additions
def test_vg_cm_gate_window_and_nonvacuity():
    # REVIEW R7: window = V_icm +- 0.15 V. The measured cm2 D12 range [1.554, 1.728] V at V_icm 1.65 passes; the no-D12 range [0.673, 2.538] V is rejected.
    assert abs(TB.V_ICM - 1.65) < 1e-12 and abs(TB.VG_CM_TOL - 0.15) < 1e-12
    assert TB.vg_cm_ok(1.554, 1.728)
    assert not TB.vg_cm_ok(0.673, 2.538)
    assert not TB.vg_cm_ok(1.40, 1.70) and not TB.vg_cm_ok(1.60, 1.81)      # either edge alone rejects
    assert not TB.vg_cm_ok(float("nan"), 1.7) and not TB.vg_cm_ok(1.6, float("nan"))


def test_drift_limit_both_stages_and_budget_no_50mv_row():
    assert not TB.drift_limit_ok(-0.204) and TB.drift_limit_ok(-0.102) and not TB.drift_limit_ok(float("nan"))     # stage-2 values from the REVIEW table
    lo, hi = TB.drift_budget(-0.204)
    assert abs(lo - (-0.334)) < 1e-9 and abs(hi - 0.13) < 1e-9             # V_icm - 0.13 - 0.204 ; V_icm + 0.13
    lo, hi = TB.drift_budget(+0.05)
    assert abs(lo + 0.13) < 1e-9 and abs(hi - 0.18) < 1e-9
    src = open(TB.__file__).read()
    assert "50 mV row" not in src                                           # D37(c): the invented row is gone
    # stage-2 closed form, SPEC C_side2 = 0.5 + 0.25 + 1 + 0.26 = 2.01 pF: 2 MHz N4096 -> 102 mV
    assert abs(TB.drift_closed(2e6, 4096, 100e-12, 2) + 0.102) < 0.002


def test_slew_share_threshold_and_knee_grid():
    assert abs(TB.SLEW_SHARE_PPM / TB.KNEE_MARGIN_X - 4.0 / 3.0) < 1e-12
    # knees3 data, 2 MHz N256 OTA1: 10 V/us gives 1.334 ppm, just above the 1.3333 ppm line, so the grid knee is 11 and the log-log crossing is at 10.0 V/us
    g, it = TB.knee_of([(8, 143.1), (9, 10.412), (10, 1.334), (11, 0.557), (12, 0.289)], TB.SLEW_SHARE_PPM / TB.KNEE_MARGIN_X)
    assert g == 11 and 10.0 <= it < 10.05
    assert TB.knee_of([(9, 10.4), (10, 1.4), (11, 0.5)], 4.0 / 3.0)[0] == 11   # 1.4 ppm at 10 fails the 1.33 ppm line
    assert set(TB.KN4_EXTRA["ota1"]) == {9.5, 10.5} and TB.R2_GBW2 == (10e6, 15e6, 20e6, 25e6)


def test_knees4_r2_deck_scopes_boost_to_ota1():
    cl1, cl2 = P.TIER1_CL1, P.TIER1_CL2
    d, _ = G.build_deck(TB.v2_cfg(dict(fs=4e6, boost=True, boost1_only=True, sr=12.5e6, sr2=13.5e6, gbw2=20e6), n=8, m=2))
    g1, i1 = _gm_ip(d, 1)
    g2, i2 = _gm_ip(d, 2)
    assert abs(i1 / (2 * 12.5e6 * cl1) - 1) < 1e-6 and abs(i2 / (13.5e6 * cl2) - 1) < 1e-6          # OTA1 boosted to 25 V/us, OTA2 base 13.5
    assert abs(g2 / (6.283185307179586 * 20e6 * cl2) - 1) < 1e-6                                   # OTA2 loaded GBW 20 MHz
    assert abs(g1 / (2 * 6.283185307179586 * P.OTA_GBW_MIN * cl1) - 1) < 1e-6


def test_model_cp_hold_default_off_is_bit_identical_and_enters_g_only():
    import iadc as M
    U = np.linspace(-0.9, 0.9, 7)
    a, _ = TB.model_eval(U, 256, a0_db=60.0)
    b, _ = TB.model_eval(U, 256, a0_db=60.0, cp_hold1=0.0, cp_hold2=0.0)
    assert np.array_equal(a, b)                                                                      # default off => bit-identical
    assert M.Params().cp_hold1 == 0.0 and M.Params().cp_hold2 == 0.0 and not hasattr(M.Params(), "cp_vg1")
    # theory (charge conservation at vg): g = 1/(1+(1+c+cp)/A), p = (1+(1+cp)/A) g, so 1 - p = (c/A) g independent of cp apart from g itself
    A, c, cp = 1000.0, 0.75, 0.5
    p0, g0 = M._leaky(20 * np.log10(A), c)
    p1, g1 = M._leaky(20 * np.log10(A), c, cp=cp)
    assert abs(g1 - 1.0 / (1 + (1 + c + cp) / A)) < 1e-15 and abs(p1 - (1 + (1 + cp) / A) * g1) < 1e-15
    assert abs((1 - p1) / g1 - c / A) < 1e-12 and abs((1 - p0) / g0 - c / A) < 1e-12              # the leak per unit gain is c/A with or without cp
    c_, _ = TB.model_eval(U, 256, a0_db=60.0, cp_hold1=0.0625, cp_hold2=0.25)
    ge = lambda x: abs(TB.inl_gain(U, x)["gain_err"])
    assert 1.001 < ge(c_) / ge(a) < 1.02                                                             # cp lowers g only: a ~0.3 % gain-error change (a sampled-cap hook would give > 1.02)


def test_stage2_sampled_cap_is_derived_from_k():
    import iadc as M
    # Hand recursion for N = 2 (theory: charge conservation, c_samp2 = c2 (1 + k)): cycle 0: x1 = 0, x2 = 0 -> y0 = +1;
    # x1' = g1 c1 (u - 1), x2' = g2 c2 (0 - k); cycle 1: y1 = sign(x2'), x2'' = p2 x2' + g2 c2 (x1' - k y1).
    A = 10 ** (60.0 / 20)
    for k in (0.25, 0.5):
        c1, c2, u = 0.125, 0.5, np.array([0.4])
        p = M.Params(order=2, N=2, c1=c1, c2=c2, k=k, a0_db=60.0)
        _, st = M.convert(p, u, return_state=True)
        g1 = 1.0 / (1.0 + (1.0 + c1) / A)
        g2 = 1.0 / (1.0 + (1.0 + c2 * (1.0 + k)) / A)
        p2 = (1.0 + 1.0 / A) * g2
        x1 = g1 * c1 * (0.4 - 1.0)
        x2 = g2 * c2 * (0.0 - k)
        y1 = 1.0 if x2 >= 0 else -1.0
        x2n = p2 * x2 + g2 * c2 * (x1 - k * y1)
        assert abs(st["x2_final"][0] - x2n) < 1e-14, k
        old = (1.0 / (1.0 + (1.0 + c2) / A))                      # the pre-WO-13 stage-2 gain (Ck not loading) differs at the 1e-4 level
        assert abs(g2 / old - 1.0) > 1e-4


def test_bstgm_default_is_bit_identical_and_separates_gm_from_current():
    e = dict(fs=4e6, bst1=2.0, bst2=1.5, sr=12.5e6, sr2=13.5e6, gbw=10e6, gbw2=15e6)
    d0, _ = G.build_deck(TB.v2_cfg(e, n=8, m=2))
    d1, _ = G.build_deck(TB.v2_cfg(dict(e, bstgm1=2.0, bstgm2=1.5), n=8, m=2))
    assert d0 == d1                                                                                  # default bstgm = bst: bit-identical deck
    d2, _ = G.build_deck(TB.v2_cfg(dict(e, bstgm1=1.8, bstgm2=1.3), n=8, m=2))
    g1, i1 = _gm_ip(d2, 1)
    g2, i2 = _gm_ip(d2, 2)
    cl1, cl2 = P.TIER1_CL1, P.TIER1_CL2
    assert abs(g1 / (1.8 * 6.283185307179586 * 10e6 * cl1) - 1) < 1e-6 and abs(i1 / (2.0 * 12.5e6 * cl1) - 1) < 1e-6      # gm follows bstgm, tail current still follows bst
    assert abs(g2 / (1.3 * 6.283185307179586 * 15e6 * cl2) - 1) < 1e-6 and abs(i2 / (1.5 * 13.5e6 * cl2) - 1) < 1e-6
    assert d2 != d0


def test_gmid_ratio_helper_nonvacuous():
    # synthetic curve gm/Id = 25/sqrt(1+J/1e-7). Analytic: base 10 -> J0 = 5.25e-7; gm/Id(2 J0) = 25/sqrt(11.5) = 7.372; ratio = 2 * 7.372 / 10 = 1.4744
    J = np.logspace(-9, -4, 4000)
    g = 25.0 / np.sqrt(1.0 + J / 1e-7)
    r = TB.gm_ratio(J, g, 10.0, 2.0)
    assert abs(r / (2.0 * 25.0 / np.sqrt(1.0 + 2 * 5.25) / 10.0) - 1) < 0.01          # 1.474 +- 1 %
    assert abs(r - 1.474) < 0.015
    assert abs(TB.gm_ratio(J, 1e-6 / J, 10.0, 2.0) - 1.0) < 0.01          # gm independent of Id (gm/Id = c/J) -> ratio 1
    assert abs(TB.gm_ratio(J, np.linspace(30, 1, 4000), 10.0, 2.0) - 1.0) > 0.01


def test_gmid_ratio_plateau_curve():
    # pfet-like plateau: gm/Id rises slightly (20.9 -> 21.3) below the peak, then falls. The strong-inversion search must ignore the rising front.
    J = np.logspace(-9, -4, 4000)
    g_front = np.where(J < 1e-7, 20.9 + 0.4 * np.log10(J / 1e-9) / 2.0, 21.3 * np.sqrt(1.0 + 1e-7 / 1e-7) / np.sqrt(1.0 + J / 1e-7))
    g_flat = np.where(J < 1e-7, 21.3, g_front)
    for base in (10.0, 15.0):
        assert abs(TB.gm_ratio(J, g_front, base, 2.0) - TB.gm_ratio(J, g_flat, base, 2.0)) < 1e-6
    assert not np.isfinite(TB.gm_ratio(J, g_front, 25.0, 2.0))                  # base above the peak: unreachable, not extrapolated


def test_gmid_checks_reject_broken_copies():
    J = np.logspace(-9, -5, 400)
    g = 25.0 / np.sqrt(1.0 + J / 1e-7)
    assert TB.gmid_mono_violations(J, g) == 0
    gb = g.copy()
    gb[250] *= 1.2                                                              # bump on the strong-inversion side
    assert TB.gmid_mono_violations(J, gb) > 0
    Jr = J[::-1].copy()                                                         # Id decreasing with Vsg after the peak (wrong column / orientation)
    assert TB.gmid_mono_violations(Jr, g) > 0


def test_gmid_op_check_synthetic(tmp_path):
    # square-law-ish synthetic device: Id = k (Vsg-0.4)^2, gm = 2 k (Vsg - 0.4); the check passes on a faithful op file and rejects shifted / foreign columns
    n = len(TB.GMID_LS)
    v = np.arange(0, 1.8 + 1e-9, 0.005)
    ks = [1e-3 * (1 + c) for c in range(n)]
    ids = [k * np.clip(v - 0.4, 0, None) ** 2 for k in ks]
    np.savetxt(tmp_path / "gmid_01v8_tt_T27.csv", np.column_stack([v] + ids))
    def op_file(name, scale=1.0, order=None):
        rows = []
        for vop in TB.GMID_OP_V["01v8"]:
            gm = [2 * k * (vop - 0.4) * scale for k in ks]
            idv = [k * (vop - 0.4) ** 2 for k in ks]
            vals = gm + idv
            rows.append(sum(([0.0, x] for x in vals), []))
        np.savetxt(tmp_path / name, np.array(rows))
    op_file("gmid_01v8_tt_op.csv")
    e, msg = TB.gmid_op_errors(str(tmp_path), "01v8")
    assert not msg and max(x[4] for x in e) < 0.005
    e2, _ = TB.gmid_op_errors(str(tmp_path), "01v8", shift=1)
    assert max(x[4] for x in e2) > TB.GMID_OP_TOL
    op_file("gmid_n01v8_tt_op.csv", scale=1.1)                                   # a "foreign" op file 10 % off
    e3, _ = TB.gmid_op_errors(str(tmp_path), "01v8", op_dev="n01v8")
    assert max(x[4] for x in e3) > TB.GMID_OP_TOL


def test_gmid_min_wl_target(tmp_path):
    # gm/Id = 25/sqrt(1+J/1e-7) at all corners: target 10 at J_max = 5.25e-7 -> W/L = Id/J_max
    J = np.logspace(-10, -4, 600)
    g = 25.0 / np.sqrt(1.0 + J / 1e-7)
    for c in TB.GMID_CORNERS:
        for t in TB.GMID_TEMPS:
            wl = TB.GMID_W / np.array(TB.GMID_LS)
            ids = np.column_stack([J * w for w in wl])
            # build an Id(Vsg) table whose per-L gm/Id(J) is g: Id = J*W/L, gm = g*Id; integrate gm over Vsg
            v = np.cumsum(np.gradient(J) / (g * J))                              # dV = dJ / (gm/Id * J)
            np.savetxt(tmp_path / f"gmid_{TB.GMID_PRIMARY}_{c}_T{t}.csv", np.column_stack([v] + [ids[:, k] for k in range(len(wl))]))
    out = TB.gmid_min_wl(str(tmp_path), 10.0, 35e-6)
    assert abs(out["1"]["wl"] / (35e-6 / 5.25e-7) - 1) < 0.03
    out2 = TB.gmid_min_wl(str(tmp_path), 30.0, 35e-6)                            # above the peak 25: unreachable
    assert not np.isfinite(out2["1"]["wl"])


def test_fp2_fixed_default_bit_identical_and_holds_pole():
    e = dict(fs=4e6, bst1=1.0, bst2=1.0, gbw=20e6, sr=25e6, gbw2=22.5e6, sr2=20.25e6)
    d0, _ = G.build_deck(TB.v2_cfg(e, n=8, m=2))
    d1, _ = G.build_deck(TB.v2_cfg(dict(e, fp2_fixed=None), n=8, m=2))
    assert d0 == d1
    d2, _ = G.build_deck(TB.v2_cfg(dict(e, fp2_fixed=(20e6, 22.5e6)), n=8, m=2))
    assert d2 == d0                                                              # held at the same gm as the absolute point: identical
    d3, _ = G.build_deck(TB.v2_cfg(dict(e, fp2_fixed=(10e6, 15e6)), n=8, m=2))
    assert d3 != d0
    cf0 = [l for l in d0.splitlines() if l.startswith("Cf1 ")][0].split()[-1]
    cf3 = [l for l in d3.splitlines() if l.startswith("Cf1 ")][0].split()[-1]
    assert abs(float(cf3) / float(cf0) - 2.0) < 1e-5                             # pole at half the frequency -> twice the capacitor


def test_fast4_jobs_and_signed_inl():
    jobs = TB.f4_jobs()
    assert {j[0] for j in jobs} == {"A", "T1", "T2", "T3", "T4", "S", "Z"}
    assert len([j for j in jobs if j[0] == "A"]) == 8
    ctl = [j for j in jobs if j[0] == "A" and j[1] == "a_D39_hot"]
    assert all(j[3]["gbw"] == 20e6 and j[3]["gbw2"] == 22.5e6 and j[3]["sr2"] == 20.25e6 and j[3]["bst1"] == 1.0 for j in ctl)
    assert all(j[5] == 101 for j in jobs if j[0] == "T4")
    # signed INL: a pure cubic error is removed by the third-order fit (resid ~ 0); a jagged error is not
    u = np.linspace(-0.9, 0.9, 101)
    e, rms, mx = TB.f4_signed(u, u + 1e-6 * (u ** 3 - 0.5 * u))
    assert rms < 1e-6 and mx < 1e-6
    rng = np.random.default_rng(1)
    e, rms, mx = TB.f4_signed(u, u + 2e-6 * rng.standard_normal(101))
    assert rms > 0.5


def test_gmid_min_wl_per_device_hand_values():
    """G-M2: W/L at L 1 um from the committed table vs hand values (id = I_tail/2, gm/Id target, J_max from the sweep): OTA1 ~29, OTA2 x2 ~18, OTA2 x1.5 ~106, +-15 %."""
    import json, os
    tbl = json.load(open(os.path.abspath(TB.GMID_JSON)))["min_wl"]
    hand = {"OTA1 (x2 current, I_tail 35 uA)": 29.0, "OTA2 x2 (I_tail 18.9 uA)": 18.0, "OTA2 x1.5 (I_tail 14.2 uA)": 106.0}
    for name, h in hand.items():
        e = tbl[name]
        assert abs(e["per_L"]["1"]["wl"] / h - 1) <= 0.15, (name, e["per_L"]["1"]["wl"], h)
        assert abs(e["id_uA"] - {"OTA1": 17.5, "OTA2 x2": 9.45, "OTA2 x1.5": 7.1}[name.split(" (")[0]]) < 1e-6
    # the old I_tail convention would give twice these values: it must be rejected by the same bounds
    for name, h in hand.items():
        assert abs(2 * tbl[name]["per_L"]["1"]["wl"] / h - 1) > 0.15
    assert TB.per_device_current(35e-6) == 17.5e-6


def test_option_ladder_and_converge_rule():
    o0, o1, o2 = (P.option_ladder(k) for k in ("O0", "O1", "O2"))
    assert o0 == P.SPICE_OPTIONS_TIER1
    assert abs(o1["reltol"] - o0["reltol"] / 10) < 1e-15 and o1["tmax_ns"] == o0["tmax_ns"] / 2 and abs(o1["chgtol"] / o0["chgtol"] - 0.1) < 1e-9 and P.option_ladder("O2")["chgtol"] >= P.CHGTOL_FLOOR
    assert abs(o2["reltol"] - o0["reltol"] / 100) < 1e-15 and o2["tmax_ns"] == o0["tmax_ns"] / 4 and o2["trtol"] == 1.0 and o1["trtol"] == o0["trtol"]
    assert P.option_ladder("O1", "trap")["method"] == "trap"
    # tau floor: GBW 10 MHz, beta 0.84 -> tau 18.9 ns -> tmax <= 1.89 ns (O0 10 ns is untouched)
    cfg = dict(gbw=10e6, gbw2=None, options=o1)
    assert G.merged(cfg)["tmax"] <= 1.9e-9
    assert G.merged(dict(gbw=10e6, options=o0))["tmax"] == 10e-9
    # rule: gate 10; INL 5 -> allow max(0.5, 0.5) = 0.5
    ok, d, v, ps = TB.converge_verdict(4.8, 5.0, 10.0)
    assert ok and abs(d - 0.2) < 1e-12 and abs(v - 5.2) < 1e-12 and ps
    # non-vacuity: an O0 -> O1 step that moves INL by 3 ppm at INL 5 / gate 10 fails the rule
    ok, d, v, ps = TB.converge_verdict(8.0, 5.0, 10.0)
    assert not ok and not ps
    # verdict inflation: converged but INL(1+d/INL) over the gate fails
    ok, d, v, ps = TB.converge_verdict(9.0, 9.6, 10.0)
    assert ok and v > 10.0 and not ps
    assert not TB.converge_verdict(float("nan"), 5.0, 10.0)[0]


def _cf(deck, k):
    import re
    return float(re.search(rf"^Cf{k} f{k} 0 (\S+)", deck, re.M).group(1))


def test_fp2_mult_per_ota_and_point_parser():
    base, _ = G.build_deck(TB.v2_cfg({}, n=8, m=2))
    d, _ = G.build_deck(TB.v2_cfg({"fp2_mult1": 30.0}, n=8, m=2))
    e, _ = G.build_deck(TB.v2_cfg({"fp2_mult2": 6.0}, n=8, m=2))
    # default unchanged; Cf is 1/fp2: x30 vs x3 -> Cf/10 on the chosen OTA only
    assert abs(_cf(d, 1) / _cf(base, 1) - 0.1) < 1e-6 and _cf(d, 2) == _cf(base, 2)
    assert abs(_cf(e, 2) / _cf(base, 2) - 0.5) < 1e-6 and _cf(e, 1) == _cf(base, 1)
    assert TB.parse_point("fs=2e6, sr=9.5e6,fp2_mult1=3") == {"fs": 2e6, "sr": 9.5e6, "fp2_mult1": 3.0}
    # non-vacuity: a point that sets nothing equals the base deck
    z, _ = G.build_deck(TB.v2_cfg(TB.parse_point(""), n=8, m=2))
    assert _cf(z, 1) == _cf(base, 1)


def test_deck_timeout_knob(tmp_path, monkeypatch):
    """--deck-timeout: run_deck passes DECK_TIMEOUT_S to timeout(1); an explicit timeout= still wins."""
    seen = []

    class R:
        returncode = 124
        stdout = stderr = ""

    monkeypatch.setattr(TB.subprocess, "run", lambda cmd, **kw: (seen.append(cmd), R())[1])
    cfg = TB.v2_cfg({}, n=8, m=2)
    TB.run_deck(cfg, "t0", outdir=str(tmp_path))
    assert seen[-1][4] == "1500"  # default unchanged
    monkeypatch.setattr(TB, "DECK_TIMEOUT_S", 7000)
    TB.run_deck(cfg, "t1", outdir=str(tmp_path))
    assert seen[-1][4] == "7000"
    TB.run_deck(cfg, "t2", outdir=str(tmp_path), timeout=9)
    assert seen[-1][4] == "9"
