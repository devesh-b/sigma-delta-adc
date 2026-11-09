"""WO-17 / S6: independent check of the golden vectors + non-vacuity (mutants).

The checker below is written from the SPEC text (3.6 rules 9-11, 3.7, F4) and does NOT call model/iadc.py or
model/golden.py. Expected values: acc1 = S, acc2 = sum S with exclusive S, num = acc2 + 4 acc1, den = N(N-1)/2.
Each mutant is a switch in the checker; the golden set must disagree with it (REJECT).
"""
import json
import os
import hashlib

import pytest

from model import golden as G

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "..", "..", "golden", "s6_vectors.json")
# sha256 of the canonical serialisation of the seed-20261109 set (pinned; regenerate => same bytes)
PINNED_SHA = "b8bd7a93b82b999556cc7a2f07fd1644af82d2881daa03ff961b374ecef9053b"


# ---------------- independent reference (integer arithmetic, option B: c1 = 1/8, c2 = 1/2, k = 1/2) ----------------
def unhex(h, n):
    return [1 if b == "1" else -1 for b in bin(int(h, 16))[2:].zfill(n)]


def ref_loop(order, N, u, s, y0=1, s_first=None):
    """Bitstream of the ideal loop by exact integers. u dyadic. y0 forced at cycle 0 (rule 9).
    s_first: input sign used on cycle 0 only (chop-swap-late mutant)."""
    a, b = u.as_integer_ratio()
    X1 = X2 = 0       # X1 = 8 b x1, X2 = 16 b x2
    ys = []
    for n in range(N):
        q = X2 if order == 2 else X1
        y = y0 if n == 0 else (1 if q >= 0 else -1)
        ys.append(y)
        sn = s_first if (n == 0 and s_first is not None) else s
        X1n = X1 + sn * a - y * b
        if order == 2:
            X2 = X2 + X1 - 4 * b * y
        X1 = X1n
    return ys


def ref_acc(y, inclusive=False):
    a1 = a2 = 0
    for v in y:
        if inclusive:
            a1 += v
            a2 += a1
        else:
            a2 += a1
            a1 += v
    return a1, a2


def wrap(v, bits):
    m = 1 << bits
    v &= m - 1
    return v - m if v >= m >> 1 else v


def ref_values(order, N, y, s, mut=None):
    a1, a2 = ref_acc(y, inclusive=(mut == "inclusive"))
    if mut == "acc23":
        a2 = wrap(a2, 23)
    if mut == "acc24":
        a2 = wrap(a2, 24)
    if order == 2:
        num, den = a2 + 4 * a1, N * (N - 1) // 2
    else:
        a2, num, den = None, a1, N
    sg = 1 if mut == "nosign" else s
    return a1, a2, sg * num, den


def ref_tags(config0, slots):
    """Independent sequencer: latch only at even slots, first pair after a change invalid."""
    active, pending, out = config0, None, []
    pair, invalid, since = 0, False, 0
    for t, sl in enumerate(slots):
        if t % 2 == 0 and pending is not None:
            active, pending, pair, invalid = pending, None, 0, True
        elif t % 2 == 0 and t > 0:
            pair += 1
            invalid = False
        sign = -1 if (active["sys_chop"] and t % 2) else 1
        out.append((active, dict(chop_sign=sign, order=active["order"], n_code=active["n_code"],
                                 frame_ctr=t & 0xFF, pair_idx=pair, invalid=invalid)))
        if sl.get("request"):
            pending = sl["request"]
    return out


def frames_of(doc):
    for v in doc["vectors"]:
        for f in v["frames"]:
            yield v["config"], v["u"], f
    for sq in doc["sequences"]:
        tg = ref_tags(sq["config0"], sq["slots"])
        for (c, _), f in zip(tg, sq["frames"]):
            yield c, sq["slots"][f["slot"]]["u"], f


def check(doc, mut=None):
    """Return the number of frames whose recomputed values disagree with the golden record."""
    bad = 0
    for c, u, f in frames_of(doc):
        N, order, s = f["n"], c["order"], f["tags"]["chop_sign"]
        if mut in ("nm1", "np1"):
            y = ref_loop(order, N + (1 if mut == "np1" else -1), u, s)
        elif mut == "yflip":
            y = [-v for v in unhex(f["ybits"], N)]
        elif mut == "y0free":
            # decimator takes the raw (metastable) first decision while DAC/loop used the forced +1: review F8
            y = unhex(f["ybits"], N)
            y[0] = -y[0]
        elif mut == "y0alt":
            # whole loop self-consistently started with y[0] = -1 (an alternative valid stream; not the golden one)
            y = ref_loop(order, N, u, s, y0=-1)
        elif mut == "swaplate":
            y = ref_loop(order, N, u, s, s_first=(-s if c["sys_chop"] else s))
        else:
            y = unhex(f["ybits"], N)
        a1, a2, ns, den = ref_values(order, N, y, s, mut)
        if (a1, a2, ns, den) != (f["acc1"], f["acc2"], f["num_signed"], f["den"]) or (mut in ("y0alt", "swaplate") and y != unhex(f["ybits"], N)):
            bad += 1
    return bad


def check_all(doc, mut=None):
    bad = check(doc, mut)
    return bad


def check_tags_and_pairs(doc):
    bad = 0
    for v in doc["vectors"]:
        tg = ref_tags(v["config"], [{}, {}])
        for (c, t), f in zip(tg, v["frames"]):
            bad += t != f["tags"]
        fa, fb = v["frames"]
        bad += (fa["num_signed"] + fb["num_signed"], 2 * fa["den"]) != (v["pair"]["pair_num"], v["pair"]["pair_den"])
    for sq in doc["sequences"]:
        tg = ref_tags(sq["config0"], sq["slots"])
        for (c, t), f in zip(tg, sq["frames"]):
            bad += t != f["tags"]
        sent = [f["tags"]["frame_ctr"] for f in sq["frames"] if f["slot"] in sq["frames_sent"]]
        assert sent == [t["frame_ctr"] for (_, t), f in zip(tg, sq["frames"]) if f["slot"] not in sq["dropped"]]
        for p in sq["pairs"]:
            a, b = p["slots"]
            comp = a not in sq["dropped"] and b not in sq["dropped"]
            bad += comp != p["complete"]
            bad += (tg[a][1]["invalid"] == p["valid"])
            if comp:
                fa, fb = sq["frames"][a], sq["frames"][b]
                bad += (fa["num_signed"] + fb["num_signed"], 2 * fa["den"]) != (p["pair_num"], p["pair_den"])
    return bad


@pytest.fixture(scope="module")
def doc():
    with open(GOLD) as f:
        return json.load(f)


def test_det_hash():
    d1, d2 = G.build(), G.build()
    assert G.sha(d1) == G.sha(d2)
    with open(GOLD) as f:
        assert hashlib.sha256(f.read().encode()).hexdigest() == G.sha(d1)
    assert G.sha(d1) == PINNED_SHA


def test_independent_bit_exact(doc):
    assert check(doc) == 0               # acc1, acc2, num, den, sign, from y alone
    assert check_tags_and_pairs(doc) == 0


def test_loop_bitstream_reproduced(doc):
    """Bonus: the integer reference loop regenerates every golden bitstream (so the stored y is the ideal loop)."""
    for c, u, f in frames_of(doc):
        N = f["n"]
        assert ref_loop(c["order"], N, u, f["tags"]["chop_sign"]) == unhex(f["ybits"], N)


MUT = ["inclusive", "nm1", "np1", "yflip", "acc23", "nosign", "y0free", "y0alt", "swaplate"]


@pytest.mark.parametrize("mut", MUT)
def test_mutant_rejected(doc, mut):
    assert check(doc, mut) > 0


def test_acc24_accepts_and_acc23_overflows_only_at_4096(doc):
    assert check(doc, "acc24") == 0
    hit = set()
    for c, u, f in frames_of(doc):
        if f["acc2"] is not None and abs(f["acc2"]) > (1 << 22) - 1:
            hit.add(f["n"])
    assert hit == {4096}
    assert max(abs(f["acc2"]) for _, _, f in frames_of(doc) if f["acc2"] is not None) < (1 << 23) - 1


def test_checker_fails_on_corrupted_copy(doc):
    bad = json.loads(json.dumps(doc))
    bad["vectors"][200]["frames"][0]["acc2"] += 1
    assert check(bad) > 0
    bad = json.loads(json.dumps(doc))
    bad["sequences"][0]["frames"][5]["tags"]["invalid"] ^= True
    assert check_tags_and_pairs(bad) > 0


def test_coverage_matrix(doc):
    got = {(v["config"]["order"], v["config"]["chop_mode"], v["config"]["N"], v["config"]["short"]) for v in doc["vectors"]}
    want = {(o, c, n, sh) for o in (1, 2) for c in G.CHOPS for n in G.N_SET for sh in (False, True)}
    assert got == want
    for v in doc["vectors"]:
        if not v["config"]["short"]:
            pass
    inp = [v for v in doc["vectors"] if not v["config"]["short"]]
    assert len(inp) == 2 * 3 * 4 * 9


def test_order1_ucorr_identity(doc):
    """Theory: ideal loop => (u_hat_bits + x_final/(c1 N)) = u exactly (order 1) and with x2/(c1 c2 W) (order 2),
    in the input frame (times s). Pins the order-1 u_corr branch (REVIEW-S5h)."""
    n1 = n2 = 0
    for c, u, f in frames_of(doc):
        s = f["tags"]["chop_sign"]
        N = f["n"]
        r = f["model_ref"]
        if c["order"] == 1:
            exp = (f["acc1"] / N + r["x1_final"] / (0.125 * N)) * s
            n1 += 1
        else:
            W = N * (N - 1) / 2
            exp = (f["num"] / W + r["x2_final"] / (0.125 * 0.5 * W)) * s
            n2 += 1
        assert abs(r["u_corr"] - exp) < 1e-12
        assert abs(r["u_corr"] - u) < 1e-9 * 1 + 1e-12, (r["u_corr"], u)
    assert n1 > 0 and n2 > 0


def test_iadc_y_exposed():
    import numpy as np
    from model import iadc
    p = iadc.Params(order=1, N=64, c1=0.125)
    uh, st = iadc.convert(p, np.array([0.3, -0.2]), return_state=True)
    assert st["y"].shape == (64, 2)
    assert np.allclose(st["y"].sum(axis=0) / 64, uh)
    assert iadc.convert(p, np.array([0.3, -0.2])).shape == (2,)


def test_sequence_semantics(doc):
    cc = doc["sequences"][0]
    inv = [f["tags"]["invalid"] for f in cc["frames"]]
    assert inv == [False] * 4 + [True] * 4 + [False] * 4
    assert [f["tags"]["n_code"] for f in cc["frames"]] == [0] * 4 + [1] * 2 + [2] * 6
    dr = doc["sequences"][1]
    assert [f["tags"]["frame_ctr"] for f in dr["frames"] if f["slot"] in dr["frames_sent"]] == [0, 1, 2, 4, 5, 6, 7]
    assert [p["complete"] for p in dr["pairs"]] == [True, False, True, True]


if __name__ == "__main__":
    with open(GOLD) as f:
        d = json.load(f)
    n = sum(1 for _ in frames_of(d))
    print("frames", n, "nominal mismatches", check(d))
    for m in MUT + ["acc24"]:
        b = check(d, m)
        print("%-10s %s  (%d/%d frames differ)" % (m, "REJECT" if b else "ACCEPT", b, n))
