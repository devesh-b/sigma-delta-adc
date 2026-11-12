"""WO-53 / D76: golden v3.2 o1d_vectors (order 1 with the extra loop delay y[n+1] = sign(x1[n])), independent integer check."""
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "..", "..", "golden", "s6_vectors.json")
D = 1 << 20


def unhex(h, n):
    return [1 if b == "1" else -1 for b in bin(int(h, 16))[2:].zfill(n)]


def ref_o1(N, u_eff, delay=True):
    """Exact integers: X1 = 8 D x1. Decision on the previous state when delay; y[0] = +1 forced."""
    X1 = Xp = 0
    ys = []
    for n in range(N):
        q = Xp if delay else X1
        y = 1 if (n == 0 or q >= 0) else -1
        ys.append(y)
        Xp, X1 = X1, X1 + round(u_eff * D) - y * D
    return ys


@pytest.fixture(scope="module")
def doc():
    with open(GOLD) as f:
        return json.load(f)


def rows(doc):
    for v in doc["o1d_vectors"]:
        for f in v["frames"]:
            s = -1 if f["tags"]["chop"] else 1
            yield v, f, s


def test_o1d_bits_match_delay_reference(doc):
    n = 0
    for v, f, s in rows(doc):
        assert v["config"]["order"] == 1 and v["o1_delay"] == 1
        N = f["n"]
        assert unhex(f["ybits"], N) == ref_o1(N, s * v["u"] + 0.0)
        a1 = sum(unhex(f["ybits"], N))
        assert f["acc1"] == a1 and f["den"] == N and f["num"] == a1
        n += 1
    assert n == 2 * 4 * 9 * 2


def test_o1d_differs_from_nodelay_and_mutant_rejected(doc):
    """Non-vacuity: the no-delay reference disagrees with some rows (the rows are not the legacy bitstreams)."""
    bad = sum(unhex(f["ybits"], f["n"]) != ref_o1(f["n"], s * v["u"], delay=False) for v, f, s in rows(doc))
    assert bad > 10


def test_o1d_pair_returns_u(doc):
    for v in doc["o1d_vectors"]:
        N = v["frames"][0]["n"]
        if v["config"]["sys_en"]:
            assert abs(v["pair"]["pair_num"] / v["pair"]["pair_den"] - v["u"]) < 4.0 / N + 1e-9
