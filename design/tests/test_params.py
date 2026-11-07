import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "model"))
import params as P  # noqa: E402


def test_coefficients_from_spec_3_4():
    # expected values written from SPEC §3.4 (1/4 pF, 1/2 pF), not computed from P
    assert math.isclose(P.CS1 / P.CINT1, 0.25)
    assert math.isclose(P.C1, 0.25)
    assert math.isclose(P.C2, 0.5)
    assert math.isclose(P.CINT1, 4e-12) and math.isclose(P.CINT2, 2e-12)


def test_pvt_45_distinct():
    keys = [tuple(sorted(d.items())) for d in P.PVT_LIST]
    assert len(keys) == 45
    assert len(set(keys)) == 45


def test_spice_has_every_scalar():
    with tempfile.TemporaryDirectory() as d:
        path = P.write_spice(os.path.join(d, "params.spice"))
        txt = open(path).read()
    for k in P.scalars():
        assert f".param {k} =" in txt, k


def test_agrees_with_model_defaults():
    import iadc
    m = iadc.Params()
    known_diff = {"fs", "vref"}  # model 1 MHz / 2.048 V vs SPEC 2 MHz / 1.2 V
    mine = {"order": P.ORDER, "c1": P.C1, "c2": P.C2, "k": P.K, "cs": P.CS1,
            "fs": P.FS_NOM, "vref": P.VREF_NOM}
    bad = {k for k, v in mine.items()
           if not math.isclose(getattr(m, k), v, rel_tol=1e-9)}
    assert bad == known_diff, f"unexpected mismatch set {bad}"
