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
    o = P.SPICE_OPTIONS
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
    opts = dict(P.SPICE_OPTIONS, method="trap", reltol=1e-5)
    r = TB.dc_metrics(TB.spec_cfg(dict(options=opts), n=256, m=2), "t_trunc", str(tmp_path))
    assert not r["ok"]
    assert any("final time" in p for p in r["problems"]) and any("timestep" in p.lower() for p in r["problems"])
