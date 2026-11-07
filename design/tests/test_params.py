import math
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "model"))
import pytest  # noqa: E402
import params as P  # noqa: E402


def test_coefficients_from_spec_3_4():
    # option B + D22 (SPEC §1/§3.4): Cs1 0.5 pF, Cint1 4 pF; stage 2 0.5/1 pF (S3 item 3); written, not computed
    assert math.isclose(0.5e-12 / 4e-12, 0.125) and math.isclose(P.CS1 / P.CINT1, 0.125)
    assert math.isclose(P.C1, 0.125)
    assert math.isclose(P.C2, 0.5)
    assert math.isclose(P.K, 0.5) and math.isclose(P.K / P.C1, 4.0)
    assert math.isclose(P.CS1, 0.5e-12) and math.isclose(P.CINT1, 4e-12)
    assert math.isclose(P.CS2 / P.CINT2, 0.5)             # c2 = 0.5 whatever Cs2 is chosen
    assert P.CS2 > 0 and P.CINT2 > 0
    assert math.isclose(P.VREF_NOM, 2.048) and P.VREF_OPTION == "B"
    assert P.VREF_OPTIONS["B_2p048V"]["vref"] == P.VREF_NOM
    assert P.VREF_OPTIONS["B_2p048V"]["c1"] == P.C1


def test_chop_config_and_even_n():
    assert all(n % 2 == 0 for n in P.N_SET)
    assert P.chop_config_valid(P.CHOP_SYSTEM, P.CHOP_OTA, 64)
    # non-vacuity: each rule rejects its own violation
    assert not P.chop_config_valid(False, True, 64)    # OTA chop without system chop
    assert not P.chop_config_valid(True, True, 63)     # odd N
    assert P.chop_config_valid(True, False, 64) and P.chop_config_valid(False, False, 64)


def test_pvt_counts_and_distinct():
    # counts from SPEC §6: (5+2)*3*3 = 63 analog, 5*3*3*3 = 135 digital
    ka = [tuple(sorted(d.items())) for d in P.PVT_LIST_ANALOG]
    kd = [tuple(sorted(d.items())) for d in P.PVT_LIST_DIGITAL]
    assert len(ka) == 63 and len(set(ka)) == 63
    assert len(kd) == 135 and len(set(kd)) == 135
    procs = {d["proc"] for d in P.PVT_LIST_ANALOG}
    assert len(procs) == 7 and {"tt", "ss", "ff", "sf", "fs"} <= procs
    assert {d["vdpwr"] for d in P.PVT_LIST_DIGITAL} == {1.62, 1.8, 1.98}


def test_vref_options_k_over_c1_is_4():
    # SPEC §3.4: k/c1 == 4 for options A and B (values written from the spec, not from P)
    for name in ("A_1p2V", "B_2p048V"):
        o = P.VREF_OPTIONS[name]
        assert math.isclose(o["k"] / o["c1"], 4.0), name
    assert P.VREF_OPTIONS["A_1p2V"] == {"vref": 1.2, "c1": 0.25, "c2": 0.5, "k": 1.0}
    assert P.VREF_OPTIONS["A2_1p2V"] == {"vref": 1.2, "c1": 0.25, "c2": 0.25, "k": 1.0}
    assert P.VREF_OPTIONS["B_2p048V"] == {"vref": 2.048, "c1": 0.125, "c2": 0.5, "k": 0.5}


def test_n_pins_offsets():
    assert P.N_PRECISION == 4096 and P.N_FAST == (64, 256, 1024)
    assert set(P.N_SET) == {P.N_PRECISION, *P.N_FAST}
    assert P.PINS == {"ua0": "VIN+", "ua1": "VIN-", "ua2": "VREF+", "ua3": "VREF-"}   # D24
    assert math.isclose(P.VOS_3SIGMA, 9e-3)                                           # D21
    assert P.OVERLOAD_RANGE == (1.0, 1.1)
    assert math.isclose(P.PAD_R, 500.0) and math.isclose(P.PAD_C, 5e-12)


def test_cint1_2pF_copy_is_rejected():
    # non-vacuity: the coefficient rule (c1 == 0.125, k/c1 == 4) fails for CINT1 = 2 pF
    def ok(cs1, cint1, k):
        return math.isclose(cs1 / cint1, 0.125) and math.isclose(k / (cs1 / cint1), 4.0)
    assert ok(0.5e-12, 4e-12, 0.5)
    assert not ok(0.5e-12, 2e-12, 0.5)


def test_a0_and_fs():
    assert P.OTA_A0_DB_MIN >= 80.0                      # SPEC §3.1
    assert P.FS_PRECISION == (0.25e6, 2e6) and P.FS_FAST == 4e6


def _lib_sections():
    root = os.environ.get("PDK_ROOT")
    if not root:
        pytest.skip("PDK_ROOT unset: cannot parse sky130.lib.spice section names (sandbox has it)")
    path = os.path.join(root, "sky130A", "libs.tech", "combined", "sky130.lib.spice")
    assert os.path.exists(path), path
    names = set()
    for line in open(path):
        m = re.match(r"\s*\.lib\s+(\S+)\s*$", line)
        if m:
            names.add(m.group(1))
    assert len(names) > 10, "parsed too few .lib sections"
    return names


def _section_problems(sections, corners, mc_runs, placeholders):
    """Return the list of corner / MC names that do not exist in the PDK .lib."""
    want = set(corners) | {k for k in mc_runs if k not in placeholders}
    return sorted(want - sections)


def test_corner_and_mc_section_names_exist_in_pdk():
    sec = _lib_sections()
    probs = _section_problems(
        sec, P.CORNERS_PROCESS + P.CORNERS_RC, P.MC_RUNS, P.MC_PLACEHOLDERS)
    assert not probs, f"names missing from sky130.lib.spice: {probs}"
    assert set(P.MC_RUNS) == {"tt_mm", "<worst>_mm"} and P.MC_RUNS == {"tt_mm": 200, "<worst>_mm": 50}


def test_section_name_check_is_not_vacuous():
    # non-vacuity: a typo'd section name (ss_hhh) must be reported; real names must not be
    sec = _lib_sections()
    assert _section_problems(sec, ("ss_hhh",), {}, ()) == ["ss_hhh"]
    assert _section_problems(sec, ("ss_hh",), {"tt_mmm": 1}, ()) == ["tt_mmm"]
    assert _section_problems(sec, ("ss_hh", "ff_ll", "tt"), {"tt_mm": 1}, ()) == []


def test_spice_has_every_scalar():
    with tempfile.TemporaryDirectory() as d:
        path = P.write_spice(os.path.join(d, "params.spice"))
        txt = open(path).read()
    for k in P.scalars():
        assert f".param {k} =" in txt, k


def test_agrees_with_model_defaults():
    import iadc
    m = iadc.Params()
    # iadc.Params defaults are the old option C (fs 1 MHz, c1 0.25, k 1.0); model/ is not edited here. cs: model default 1 pF, D22 is 0.5 pF.
    # Listed explicitly. vref 2.048 is the same in both (the WO expected a vref mismatch; it is not one).
    known_diff = {"fs", "c1", "k", "cs"}
    mine = {"order": P.ORDER, "c1": P.C1, "c2": P.C2, "k": P.K, "cs": P.CS1,
            "fs": P.FS_NOM, "vref": P.VREF_NOM}
    bad = {k for k, v in mine.items()
           if not math.isclose(getattr(m, k), v, rel_tol=1e-9)}
    assert bad == known_diff, f"unexpected mismatch set {bad}"
