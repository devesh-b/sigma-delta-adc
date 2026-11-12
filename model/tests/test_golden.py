"""WO-18 / S6b: independent check of the golden vectors v2/v3 + non-vacuity (mutants).

The checker below is written from the SPEC text (3.6 rules 9-11, 3.7, 3.7a D45) and does NOT call model/iadc.py or
model/golden.py (golden is imported only for the determinism hash). Expected values: acc1 = S, acc2 = sum S with
exclusive S (order 1 keeps it too), num = acc2 + 4 acc1, den = N(N-1)/2 (order 1: num = acc1, den = N).
Each mutant is a switch in the checker; the golden set must disagree with it (REJECT).
"""
import hashlib
import json
import os
from collections import namedtuple

import pytest

from model import golden as G

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "..", "..", "golden", "s6_vectors.json")
# sha256 of the canonical serialisation of the seed-20261109 set (pinned; regenerate => same bytes)
PINNED_SHA = "04bcce89b48975fe1e8c3597b637b0bc4d0e577399cad6498c6d199c4f1ba0c0"   # D70: debug y edge -> rising
D = 1 << 20
M32 = 0xFFFFFFFF
LATCHED = ("order", "N", "fs_div", "sys_en", "ota_en", "short", "boost", "trim")


# ---------------- independent reference (integer arithmetic, option B: c1 = 1/8, c2 = 1/2, k = 1/2) ----------------
def unhex(h, n):
    return [1 if b == "1" else -1 for b in bin(int(h, 16))[2:].zfill(n)]


def ref_loop(order, N, u, s, off=0.0, y0=1, s_first=None):
    """Bitstream of the ideal loop by exact integers. Input per cycle = s*u + off (dyadic). y0 forced at cycle 0.
    s_first: sign used on cycle 0 only (chop-swap-late mutant)."""
    X1 = X2 = 0       # X1 = 8 D x1, X2 = 16 D x2
    ys = []
    offi = round(off * D)
    for n in range(N):
        q = X2 if order == 2 else X1
        y = y0 if n == 0 else (1 if q >= 0 else -1)
        ys.append(y)
        sn = s_first if (n == 0 and s_first is not None) else s
        X1n = X1 + sn * round(u * D) + offi - y * D
        if order == 2:
            X2 = X2 + X1 - 4 * D * y
        X1 = X1n
    return ys


def wrap(v, bits):
    m = 1 << bits
    v &= m - 1
    return v - m if v >= m >> 1 else v


def ref_acc(y, inclusive=False, w1=None, init=(0, 0)):
    a1, a2 = init
    for v in y:
        if inclusive:
            a1 += v
            a2 += a1
        else:
            a2 += a1
            a1 += v
        if w1:
            a1 = wrap(a1, w1)
    return a1, a2


def ref_values(order, N, y, s, mut=None, init=(0, 0)):
    a1, a2 = ref_acc(y, inclusive=(mut == "inclusive"), w1={"acc1_13": 13, "acc1_14": 14}.get(mut), init=init)
    if mut == "acc23":
        a2 = wrap(a2, 23)
    if mut == "acc24":
        a2 = wrap(a2, 24)
    if order == 2:
        num, den = a2 + 4 * a1, N * (N - 1) // 2
    else:
        num, den = a1, N
    sg = 1 if mut == "nosign" else s
    return a1, a2, sg * num, den


def pack_tag(chop, order2, n_code, sys_en, ota_en, short, invalid, ctr):
    """Tag word from the SPEC 3.7a(c) table: chop(15) order(14) n_code(13:12) sys_en(11) ota_en(10) short(9)
    invalid(8) frame_ctr(7:0); order bit 0 = order 1."""
    w = 0
    for val, wd in ((chop, 1), (order2, 1), (n_code, 2), (sys_en, 1), (ota_en, 1), (short, 1), (invalid, 1), (ctr, 8)):
        w = (w << wd) | (int(val) & ((1 << wd) - 1))
    return w


def _fs_norm(d):
    return d if d <= 4 else 1          # SPEC 3.8a (D66 AMB-05): codes 5-7 read as 1


def _neq(a, b, k, mut=None):
    """Effective difference of one latched field; fs_div compared normalised (mutant fs5chg: raw code)."""
    if k == "fs_div" and mut != "fs5chg":
        return _fs_norm(a[k]) != _fs_norm(b[k])
    return a[k] != b[k]


def ref_tags(config0, slots, mut=None):
    """Independent sequencer (D45 c, d, e). Latch at the even-slot reset-window edge; writes in earlier slots count,
    last wins; writes in the even slot itself are on or after the edge."""
    active, pending, inv, ctr, out = config0, None, False, 0, []
    for t, sl in enumerate(slots):
        if mut == "boostmid" and t % 2 == 1 and pending is not None:
            active = dict(active, boost=pending["boost"], trim=pending["trim"])
        edge_writes = sorted(sl.get("writes", []), key=lambda w: w["off"])
        if mut == "latchedge" and t % 2 == 0:
            for w in edge_writes:
                if w["off"] == 0:
                    pending = w["cfg"]
        if t % 2 == 0 or mut == "immediate":
            if t % 2 == 0:
                inv = t == 0 and mut != "noinvrst"
            if pending is not None:
                inv = inv or any(_neq(pending, active, k, mut) for k in (LATCHED[:-2] if mut == "bt_noinv" else LATCHED))
                active, pending = pending, None
                if mut == "ctrreset":
                    ctr = 0
        chop = int(bool(active["sys_en"]) and t % 2 == 1)
        invf = inv and (t % 2 == 0 if mut == "invfirst" else True)
        tg = dict(chop=chop, order=int(active["order"] == 2), n_code=active["n_code"], sys_en=int(active["sys_en"]),
                  ota_en=int(active["ota_en"]), short=int(active["short"]), invalid=int(invf), frame_ctr=ctr & 255)
        out.append((active, tg))
        ctr += 1
        for w in edge_writes:
            if not (mut == "latchedge" and t % 2 == 0 and w["off"] == 0):
                pending = w["cfg"]
    return out


F = namedtuple("F", "rid c u off s f lv")


def frames_of(doc):
    for v in doc["vectors"]:
        for f in v["frames"]:
            s = -1 if f["tags"]["chop"] else 1
            c = v["config"]
            yield F(v["id"], c, 0.0 if c["short"] else v["u"], 0.0 if c["short"] else v["off"], s, f, True)
    for st in doc["streams"]:
        for f in st["frames"]:
            yield F(st["id"], st["config"], None, 0.0, 1, f, False)
    for sq in doc["sequences"] + doc["traces"]:
        tg = ref_tags(sq["config0"], sq["slots"])
        for (c, _), f in zip(tg, sq["frames"]):
            s = -1 if f["tags"]["chop"] else 1
            yield F(sq["id"], c, 0.0 if c["short"] else sq["slots"][f["slot"]]["u"], 0.0, s, f, True)


def check(doc, mut=None):
    """Return the number of frames whose recomputed values disagree with the golden record."""
    bad, carry = 0, {}
    for r in frames_of(doc):
        f, c, N, order, s = r.f, r.c, r.f["n"], r.c["order"], r.s
        stored = unhex(f["ybits"], N)
        y = stored
        if mut in ("nm1", "np1", "y0alt", "swaplate") and not r.lv:
            continue
        if mut in ("nm1", "np1"):
            y = ref_loop(order, N + (1 if mut == "np1" else -1), r.u, s, r.off)
        elif mut == "yflip":
            y = [-v for v in stored]
        elif mut == "y0free":
            # decimator takes the raw (metastable) first decision while DAC/loop used the forced +1: review F8
            y = [-stored[0]] + stored[1:]
        elif mut == "y0pass":
            # RTL passes the cycle-0 comparator bit through instead of forcing +1 (M1)
            y = [1 if f["comp_raw0"] else -1] + stored[1:]
        elif mut == "y0alt":
            y = ref_loop(order, N, r.u, s, r.off, y0=-1)
        elif mut == "swaplate":
            y = ref_loop(order, N, r.u, s, r.off, s_first=(-s if c["sys_en"] else s))
        elif mut == "trunc1":
            y = stored[:-1]
        elif mut == "ext1":
            y = stored + [1]
        a1, a2, ns, den = ref_values(order, N, y, s, mut, carry.get(r.rid, (0, 0)) if mut == "noclear" else (0, 0))
        if mut == "noclear":
            carry[r.rid] = ref_acc(y, init=carry.get(r.rid, (0, 0)))
        wire = "%08x%08x%04x" % (a1 & M32, a2 & M32, f["tag_word"])
        if (a1, a2, ns, den, wire) != (f["acc1"], f["acc2"], f["num_signed"], f["den"], f["wire"]):
            bad += 1
        elif mut in ("y0alt", "swaplate") and y != stored:
            bad += 1
        elif mut is None:
            bad += stored[0] != 1 or f["comp_raw0"] != 0
            if r.lv:
                bad += abs(f["model_ref"]["u_hat_signed"] * den - ns) > 1e-6
    return bad


def tag_check(c, t, f):
    return (f["tags"] != t or f["tag_word"] != pack_tag(t["chop"], t["order"], t["n_code"], t["sys_en"], t["ota_en"],
                                                        t["short"], t["invalid"], t["frame_ctr"])
            or f["n"] != c["N"] or bool(c["short"]) != bool(t["short"]))


def check_tags_and_pairs(doc, mut=None):
    bad = 0
    for v in doc["vectors"]:
        tg = ref_tags(v["config"], [{}, {}], mut)
        for (c, t), f in zip(tg, v["frames"]):
            bad += tag_check(c, t, f)
        fa, fb = v["frames"]
        bad += (fa["num_signed"] + fb["num_signed"], 2 * fa["den"]) != (v["pair"]["pair_num"], v["pair"]["pair_den"])
    for st in doc["streams"]:
        (c, t), = ref_tags(st["config"], [{}], mut)
        bad += tag_check(c, t, st["frames"][0])
    for sq in doc["sequences"] + doc["traces"]:
        tg = ref_tags(sq["config0"], sq["slots"], mut)
        for (c, t), f in zip(tg, sq["frames"]):
            bad += tag_check(c, t, f)
        sent = [f["tags"]["frame_ctr"] for f in sq["frames"] if f["slot"] in sq["frames_sent"]]
        bad += sent != [t["frame_ctr"] for (_, t), f in zip(tg, sq["frames"]) if f["slot"] not in sq["dropped"]]
        for p in sq["pairs"]:
            a, b = p["slots"]
            comp = a not in sq["dropped"] and b not in sq["dropped"]
            bad += comp != p["complete"]
            bad += (tg[a][1]["invalid"] == p["valid"])
            if comp:
                fa, fb = sq["frames"][a], sq["frames"][b]
                bad += (fa["num_signed"] + fb["num_signed"], 2 * fa["den"]) != (p["pair_num"], p["pair_den"])
    return bad


def ref_trace(tr, mut=None):
    """Control trace from the SPEC text (3.7a i): reset window 2 fs cycles; swap from cycle 0 (inside the window);
    acc_clear on the cycle whose closing edge releases the analog reset (cycle 1); OTA phase 0 in reset then
    n mod 2 (fch = fs/2); y_force on n = 0; bit_valid n = 0..N-1; raw pin = retimed y; cfg_latch on cycle 0 of
    even slots. One row string per cycle, fields: rst, clr, swap, ota, force, valid, raw, tag_chop, latch."""
    rows, prev = [], 0
    for t, (c, tg) in enumerate(ref_tags(tr["config0"], tr["slots"])):
        y = [1 if v > 0 else 0 for v in unhex(tr["frames"][t]["ybits"], c["N"])]
        swap = int(bool(c["sys_en"]) and t % 2 == 1)
        for cyc in range(c["N"] + 2):
            n = cyc - 2
            sw = prev if (mut == "swaplate" and cyc == 0) else swap
            clr = {"clr_early": cyc == 0, "clr_late": cyc == 2}.get(mut, cyc == 1)
            ota = (cyc % 2 if mut == "otaphase" else (n % 2 if n >= 0 else 0)) if c["ota_en"] else 0
            tagc = 1 - swap if mut == "tagflop" else swap
            rows.append("".join(str(int(v)) for v in (cyc < 2, clr, sw, ota, n == 0, n >= 0, y[n] if n >= 0 else 0,
                                                      tagc, t % 2 == 0 and cyc == 0)))
        prev = swap
    return rows


def check_trace(doc, mut=None):
    bad = 0
    for tr in doc["traces"]:
        exp, got = ref_trace(tr, mut), tr["trace"]["rows"]
        bad += abs(len(exp) - len(got)) + sum(a != b for a, b in zip(exp, got))
        n = 0
        for t, f in enumerate(tr["frames"]):          # tag chop bit and swap level come from one flop
            L = f["n"] + 2
            for row in got[n:n + L]:
                bad += row[2] != row[7] or int(row[7]) != f["tags"]["chop"]
            n += L
    return bad


def pair_u(fa, fb, mut=None):
    """Pair demodulation from unsigned num: (s_a num_a + s_b num_b) / (2 den); mutants break the sign source."""
    sa, sb = (-1 if fa["tags"]["chop"] else 1), (-1 if fb["tags"]["chop"] else 1)
    if mut == "tagstuck":
        sa = sb = 1
    if mut == "taginv":
        sa, sb = -sa, -sb
    return (sa * fa["num"] + sb * fb["num"]) / (2 * fa["den"])


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
    assert check(doc) == 0               # acc1, acc2, num, den, wire word, comp_raw0, u_hat assertion
    assert check_tags_and_pairs(doc) == 0
    assert check_trace(doc) == 0


def test_loop_bitstream_reproduced(doc):
    """The integer reference loop regenerates every loop-valid golden bitstream; edge streams are RTL-only."""
    n = 0
    for r in frames_of(doc):
        if r.lv:
            n += 1
            assert ref_loop(r.c["order"], r.f["n"], r.u, r.s, r.off) == unhex(r.f["ybits"], r.f["n"])
        else:
            assert r.f["n"] == 4096
    assert n > 1000


DATA_MUT = ["inclusive", "nm1", "np1", "yflip", "acc23", "nosign", "y0free", "y0alt", "swaplate", "y0pass",
            "trunc1", "ext1", "acc1_13", "noclear"]
TAG_MUT = ["immediate", "invfirst", "ctrreset", "noinvrst", "latchedge"]
TRACE_MUT = ["swaplate", "clr_early", "clr_late", "otaphase", "tagflop"]


@pytest.mark.parametrize("mut", DATA_MUT)
def test_mutant_rejected(doc, mut):
    assert check(doc, mut) > 0


@pytest.mark.parametrize("mut", TAG_MUT)
def test_sequencer_mutant_rejected(doc, mut):
    assert check_tags_and_pairs(doc, mut) > 0


@pytest.mark.parametrize("mut", TRACE_MUT)
def test_trace_mutant_rejected(doc, mut):
    assert check_trace(doc, mut) > 0


def test_offset_pairs_and_tag_mutants(doc):
    offs = [v for v in doc["vectors"] if v["kind"] == "offset"]
    assert len(offs) == 48
    for v in offs:
        fa, fb = v["frames"]
        assert abs(pair_u(fa, fb) - v["u"]) < 0.05, v["id"]          # correct tags return u
        assert abs(pair_u(fa, fb, "tagstuck") - v["u"]) > 0.05, v["id"]   # stuck sign returns about off
        assert abs(pair_u(fa, fb, "taginv") - v["u"]) > 0.05, v["id"]     # inverted sign returns about -u
        assert abs(pair_u(fa, fb, "tagstuck") - v["off"]) < 0.05, v["id"]


def test_acc_width_edges(doc):
    assert check(doc, "acc24") == 0 and check(doc, "acc1_14") == 0
    assert check(doc, "acc1_13") > 0
    loop_hits = {r.f["n"] for r in frames_of(doc) if r.lv and abs(r.f["acc2"]) > (1 << 22) - 1}
    assert loop_hits == {4096}
    assert max(abs(r.f["acc2"]) for r in frames_of(doc)) < (1 << 23) - 1
    # acc1 13-bit mutant is rejected only by the synthetic RTL-only streams (loop acc1 stays small)
    assert max(abs(r.f["acc1"]) for r in frames_of(doc) if r.lv) < 4096
    assert {r.rid for r in frames_of(doc) if not r.lv} == {"st_o2_allp", "st_o2_pm", "st_o2_alt", "st_o1_allp"}
    assert all(not st["loop_valid"] for st in doc["streams"])


def test_checker_fails_on_corrupted_copy(doc):
    bad = json.loads(json.dumps(doc))
    bad["vectors"][200]["frames"][0]["acc2"] += 1
    assert check(bad) > 0
    bad = json.loads(json.dumps(doc))
    bad["sequences"][0]["frames"][5]["tags"]["invalid"] ^= 1
    assert check_tags_and_pairs(bad) > 0
    bad = json.loads(json.dumps(doc))
    r = bad["traces"][0]["trace"]["rows"]
    r[70] = r[70][:1] + ("0" if r[70][1] == "1" else "1") + r[70][2:]
    assert check_trace(bad) > 0


def test_coverage_matrix(doc):
    md = [v for v in doc["vectors"] if v["kind"] == "mode"]
    got = {(v["config"]["order"], v["config"]["chop_mode"], v["config"]["N"], bool(v["config"]["short"])) for v in md}
    want = {(o, c, n, sh) for o in (1, 2) for c in G.CHOPS for n in G.N_SET for sh in (False, True)}
    assert got == want
    assert len([v for v in md if not v["config"]["short"]]) == 2 * 4 * 4 * 9
    assert {(v["config"]["sys_en"], v["config"]["ota_en"]) for v in md} == {(0, 0), (1, 0), (1, 1), (0, 1)}


def test_order1_ucorr_identity(doc):
    """Theory: ideal loop => (u_hat_bits + x_final/(c1 N)) = u_frame exactly (order 1) and with x2/(c1 c2 W) (order 2),
    in the input frame. u_frame = u + s*off."""
    n1 = n2 = 0
    for r in frames_of(doc):
        if not r.lv:
            continue
        f, N = r.f, r.f["n"]
        m = f["model_ref"]
        if r.c["order"] == 1:
            exp = (f["acc1"] / N + m["x1_final"] / (0.125 * N)) * r.s
            n1 += 1
        else:
            W = N * (N - 1) / 2
            exp = (f["num"] / W + m["x2_final"] / (0.125 * 0.5 * W)) * r.s
            n2 += 1
        assert abs(m["u_corr"] - exp) < 1e-12
        assert abs(m["u_corr"] - (r.u + r.s * r.off)) < 1e-9
    assert n1 > 0 and n2 > 0


def test_iadc_y_exposed():
    import numpy as np
    from model import iadc
    p = iadc.Params(order=1, N=64, c1=0.125)
    uh, st = iadc.convert(p, np.array([0.3, -0.2]), return_state=True)
    assert st["y"].shape == (64, 2)
    assert np.allclose(st["y"].sum(axis=0) / 64, uh)
    assert iadc.convert(p, np.array([0.3, -0.2])).shape == (2,)


def seq(doc, sid):
    return next(s for s in doc["sequences"] + doc["traces"] if s["id"] == sid)


def test_sequence_semantics(doc):
    inv = lambda s: [f["tags"]["invalid"] for f in s["frames"]]
    cc = seq(doc, "seq_cfgchange")
    assert inv(cc) == [1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]
    assert [f["tags"]["n_code"] for f in cc["frames"]] == [0] * 4 + [1] * 2 + [2] * 6
    dr = seq(doc, "seq_drop")
    assert [f["tags"]["frame_ctr"] for f in dr["frames"] if f["slot"] in dr["frames_sent"]] == [0, 1, 2, 4, 5, 6, 7]
    assert [p["complete"] for p in dr["pairs"]] == [True, False, True, True]
    # M3: short toggled mid-pair is deferred to the pair boundary and the pair after it is invalid
    sh = seq(doc, "seq_short")
    assert [f["tags"]["short"] for f in sh["frames"]] == [0] * 4 + [1] * 4 + [0] * 2
    assert inv(sh) == [1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
    # m3: last write wins; a write on the edge goes to the next pair
    mw = seq(doc, "seq_multiwrite")
    assert [f["tags"]["order"] for f in mw["frames"]] == [1] * 8 and inv(mw) == [1, 1, 1, 1, 1, 1, 0, 0]
    ed = seq(doc, "seq_edge")
    assert [f["tags"]["order"] for f in ed["frames"]] == [1, 1, 1, 1, 0, 0, 1, 1]
    assert inv(ed) == [1, 1, 0, 0, 1, 1, 1, 1]
    # m9: frame_ctr wrap
    w = seq(doc, "seq_wrap")
    ctr = [f["tags"]["frame_ctr"] for f in w["frames"]]
    assert len(ctr) >= 258 and ctr[255] == 255 and ctr[256] == 0 and ctr[257] == 1
    assert ctr == [i % 256 for i in range(len(ctr))]


def test_order1_acc2_defined(doc):
    o1 = [r for r in frames_of(doc) if r.c["order"] == 1]
    assert o1 and all(r.f["acc2"] is not None for r in o1)
    assert any(r.f["acc2"] != 0 for r in o1)


def test_size_and_readme():
    assert os.path.getsize(GOLD) < 1_000_000
    with open(os.path.join(HERE, "..", "..", "golden", "README.md")) as f:
        txt = f.read()
    assert "RTL-observable" in txt and "Reference-only" in txt and "comp_raw0" in txt


if __name__ == "__main__":
    with open(GOLD) as f:
        d = json.load(f)
    n = sum(1 for _ in frames_of(d))
    print("frames", n, "nominal mismatches", check(d), check_tags_and_pairs(d), "trace", check_trace(d))
    for m in DATA_MUT + ["acc24", "acc1_14"]:
        b = check(d, m)
        print("%-10s %s  (%d/%d frames differ)" % (m, "REJECT" if b else "ACCEPT", b, n))
    for m in TAG_MUT:
        b = check_tags_and_pairs(d, m)
        print("seq:%-10s %s  (%d mismatches)" % (m, "REJECT" if b else "ACCEPT", b))
    for m in TRACE_MUT:
        b = check_trace(d, m)
        print("trace:%-10s %s  (%d mismatches)" % (m, "REJECT" if b else "ACCEPT", b))


# ======================= golden v3 (WO-33, G3): boost/trim, reset, words, status/hold =======================
GOLD_V2 = os.path.join(HERE, "..", "..", "golden", "s6_vectors_v2.json")
V2_SHA = "f08faffe17ceea91f31920f66bf3d4ac263c62e4b575432b5154aea7b90c938f"
# independent constants typed from SPEC 3.8a (not imported from model.golden)
REF_RESET = {"order": 2, "n_code": 3, "N": 4096, "fs_div": 1, "sys_en": 1, "ota_en": 1, "short": 0, "boost": 0,
             "trim": 4}
REF_DEBUG_UO = ["raw_y", "bit_valid", "valid_frame_ready", "fs_bit_clock", "rst_analog", "sys_swap",
                "ota_chop_phase", "invalid_hold"]
REF_WORDS = ["acc1_hi", "acc1_lo", "acc2_hi", "acc2_lo", "tag", "status"]


def ref_cfg_word(c):
    w = 0
    for val, wd in ((c.get("rsv", 0), 3), (c["order"] == 2, 1), (c["n_code"], 2), (c["fs_div"], 3), (c["sys_en"], 1),
                    (c["ota_en"], 1), (c["short"], 1), (c["boost"], 1), (c["trim"], 3)):
        w = (w << wd) | (int(val) & ((1 << wd) - 1))
    return w


def ref_status(ready, ov, boost, trim, ctr, pend=0):
    return (ready << 15) | (ov << 14) | (pend << 13) | (boost << 12) | (trim << 9) | (ctr & 255)


def ref_words(f, mut=None):
    a1, a2, tg = f["acc1"] & M32, f["acc2"] & M32, f["tag_word"]
    w = [a1 >> 16, a1 & 0xFFFF, a2 >> 16, a2 & 0xFFFF, tg]
    if mut == "wordswap":
        w[1], w[2] = w[2], w[1]
    return "".join("%04x" % x for x in w)


def ref_hold(sq, mut=None):
    """Independent hold-register model (SPEC 3.8a, D66). One load per slot. The rd position per slot is the stimulus
    (hold[t].rd_rel: "before" / "on" / "after" / None relative to the load clk): before clears the old frame, on is
    suppressed (post-load frame_ctr differs from the snapshot), after clears the new frame. Load with ready 1 sets
    overrun. Returns (load state, end state, rd-acked, ready before the load, rel) per slot."""
    out, ready, ov = [], 0, 0
    for f in sq["frames"]:
        rel = sq["hold"][f["slot"]]["rd_rel"]
        if rel == "before":
            ready = ov = 0
        pre = ready
        ov = 1 if (ready and mut != "nooverrun") else 0
        ready = 1
        load = (ready, ov)
        if rel == "after" or (rel == "on" and mut == "rdon_clears"):
            ready = 1 if mut == "rdnoclear" else 0
            ov = 0
        out.append((load, (ready, ov), rel == "after", pre, rel))
    return out


def ref_pend(sq, mut=None):
    """cfg_pending right after the load edge at the end of slot t: shadow differs from active (effective fields),
    evaluated post-latch when slot t+1 is even (same clk, no mask). Mutant pendmask: pre-latch value."""
    act, shadow, out = sq["config0"], None, []
    for t, sl in enumerate(sq["slots"]):
        if t % 2 == 0 and shadow is not None:
            act, shadow = shadow, None
        for w in sorted(sl["writes"], key=lambda w: w["off"]):
            shadow = w["cfg"]
        d = shadow is not None and any(_neq(shadow, act, k) for k in LATCHED)
        out.append(int(d and ((t + 1) % 2 == 1 or mut == "pendmask")))
    return out


def all_cfgs(doc):
    for v in doc["vectors"]:
        yield v["config"]
    for st in doc["streams"]:
        yield st["config"]
    for sq in doc["sequences"] + doc["traces"]:
        yield sq["config0"]
        for sl in sq["slots"]:
            for w in sl["writes"]:
                yield w["cfg"]


def check_g3(doc, mut=None):
    bad = check_tags_and_pairs(doc, mut if mut in ("bt_noinv", "boostmid") else None)
    reset = dict(REF_RESET, trim=3) if mut == "trimreset" else REF_RESET
    bad += doc["reset"] != reset
    rv = next(v for v in doc["vectors"] if v["id"] == "rst_default")
    bad += any(rv["config"][k] != reset[k] for k in reset)
    bad += any(f["boost"] != reset["boost"] or f["trim"] != reset["trim"] for f in rv["frames"])
    for c in all_cfgs(doc):
        bad += c["cfg_word"] != ref_cfg_word(c)
    tab = doc["fs_div_table"]
    bad += any(tab[str(i)] != {"div": d, "fs_hz": 48_000_000 // d} or 48_000_000 % d for i, d in
               enumerate((12, 24, 48, 96, 192))) or tab["reserved_5_7_as"] != 1
    bad += doc["word_order"] != REF_WORDS or doc["debug_bus"]["uo_out"] != REF_DEBUG_UO
    for v in doc["vectors"] + doc["streams"]:
        tg = ref_tags(v["config"], [{}] * len(v["frames"]), mut)
        for (c, _), f in zip(tg, v["frames"]):
            bad += _frame_g3(c, f, mut)
    for sq in doc["sequences"] + doc["traces"]:
        tg = ref_tags(sq["config0"], sq["slots"], mut)
        for (c, t), f in zip(tg, sq["frames"]):
            bad += _frame_g3(c, f, mut)
        for (c, t), f, h, (load, end, rd, pre, rel) in zip(tg, sq["frames"], sq["hold"], ref_hold(sq, mut)):
            bad += h["status_word"] != "%04x" % ref_status(load[0], load[1], c["boost"], c["trim"],
                                                           t["frame_ctr"])
            bad += h["rd"] != int(rd)
            bad += h["status_after_rd"] != ("%04x" % ref_status(0, 0, c["boost"], c["trim"],
                                                                t["frame_ctr"]) if rd else None)
    return bad


def check_g31(doc, mut=None):
    """v3.1 (D66): hold reset, cfg_pending, rd before/on/after, fs_div normalisation, reserved bits, shift register."""
    bad = check_g3(doc, mut if mut in ("nooverrun", "rdnoclear") else None)
    # AMB-08: hold tag invalid 1 after rst_n, status shows the reset trim 100, nothing ready
    hr = doc["hold_reset"]
    inv = 0 if mut == "holdinv0" else 1
    bad += hr != {"frame_ready": 0, "overrun": 0, "cfg_pending": 0, "acc1": 0, "acc2": 0,
                  "tag_word": "%04x" % (inv << 8), "status_word": "%04x" % ref_status(0, 0, 0, 4, 0)}
    # AMB-05 reserved bits and fs_div codes: the write is not a change; cfg_word keeps the raw bits
    for c in all_cfgs(doc):
        bad += c["fs_div_eff"] != _fs_norm(c["fs_div"])
    # AMB-02/06/10, cfg_pending
    for sq in doc["sequences"]:
        tg = ref_tags(sq["config0"], sq["slots"], mut)
        pend = ref_pend(sq, mut)
        rows = ref_hold(sq, mut)
        lost = [t - 1 for t, r in enumerate(rows) if r[0][1]]
        bad += sorted(sq["dropped"]) != lost
        for (c, t), f, h, p, (load, end, rd, pre, rel) in zip(tg, sq["frames"], sq["hold"], pend, rows):
            bad += (h["cfg_pending"], h["ready_pre_load"], h["overrun"]) != (p, pre, load[1])
            bad += h["status_full"] != "%04x" % ref_status(load[0], load[1], c["boost"], c["trim"], t["frame_ctr"],
                                                           p)
            bad += (h["ready_end"], h["overrun_end"]) != end
        for p in sq["pairs"]:
            bad += tg[p["slots"][0]][1]["invalid"] == p["valid"]
    # AMB-07: serial shift register cleared by rst_n and after each ld
    for cs in doc["cfg_shift"]:
        sr, out = 0, []
        for op in cs["ops"]:
            if op.startswith("s:"):
                for b in op[2:]:
                    sr = ((sr << 1) | int(b)) & 0xFFFF
            elif op == "ld":
                out.append("%04x" % sr)
                sr = sr if mut == "noclear_ld" else 0
            else:
                sr = 0
        bad += out != cs["expect"]
    return bad


def _frame_g3(c, f, mut):
    return ((f["boost"], f["trim"]) != (c["boost"], c["trim"]) or "".join(f["words"]) != f["wire"]
            or "".join(f["words"]) != ref_words(f, mut)
            or f["status_word"] != "%04x" % ref_status(1, 0, c["boost"], c["trim"], f["tags"]["frame_ctr"]))


G3_MUT = ["boostmid", "trimreset", "wordswap", "rdnoclear", "nooverrun", "bt_noinv"]


def test_g3_nominal(doc):
    assert doc["format"] == 3
    assert check_g3(doc) == 0
    assert check(doc) == 0 and check_trace(doc) == 0


@pytest.mark.parametrize("mut", G3_MUT)
def test_g3_mutant_rejected(doc, mut):
    assert check_g3(doc, mut) > 0


def test_g3_semantics(doc):
    s = seq(doc, "seq_boosttrim")
    assert [f["boost"] for f in s["frames"]] == [0, 0, 1, 1, 1, 1, 1, 1, 0, 0]
    assert [f["trim"] for f in s["frames"]] == [4, 4, 4, 4, 4, 4, 2, 2, 2, 2]
    assert [f["tags"]["invalid"] for f in s["frames"]] == [1, 1, 1, 1, 0, 0, 1, 1, 1, 1]
    dr = seq(doc, "seq_drop")
    assert [h["overrun"] for h in dr["hold"]] == [0, 0, 0, 0, 1, 0, 0, 0]       # slot 3 unread, slot 4 overruns
    assert dr["hold"][3]["rd"] == 0 and dr["hold"][3]["status_after_rd"] is None
    assert int(dr["hold"][4]["status_word"], 16) >> 14 == 3                      # ready + overrun
    assert int(dr["hold"][4]["status_after_rd"], 16) >> 14 == 0                  # rd clears both
    assert len([v for v in doc["vectors"] if v["kind"] == "boosttrim"]) == 16
    assert {(v["config"]["boost"], v["config"]["trim"]) for v in doc["vectors"] if v["kind"] == "boosttrim"} == \
        {(b, t) for b in (0, 1) for t in range(8)}
    assert all(c["boost"] == 0 and c["trim"] == 4 for v in doc["vectors"] if v["kind"] == "mode"
               for c in [v["config"]])


def subset(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and all(k in b and subset(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(subset(x, y) for x, y in zip(a, b))
    return a == b


def test_v2_rows_unchanged_in_v3(doc):
    with open(GOLD_V2) as f:
        txt = f.read()
    assert hashlib.sha256(txt.encode()).hexdigest() == V2_SHA
    v2 = json.loads(txt)
    assert v2["format"] == 2 and doc["format"] == 3
    for key in ("vectors", "streams", "sequences", "traces"):
        new = {r["id"]: r for r in doc[key]}
        assert len(v2[key]) <= len(new)
        for r in v2[key]:
            assert subset(r, new[r["id"]]), (key, r["id"])
        # order preserved: v2 rows are the leading rows
        assert [r["id"] for r in doc[key]][:len(v2[key])] == [r["id"] for r in v2[key]]
    # a broken v3 (one accumulator word changed) must not satisfy the subset relation
    bad = json.loads(json.dumps(doc))
    bad["vectors"][10]["frames"][0]["acc1"] += 1
    assert not subset(v2["vectors"][10], bad["vectors"][10])


# ======================= golden v3.1 (WO-35, D66): contract rows =======================
GOLD_V3 = os.path.join(HERE, "..", "..", "golden", "s6_vectors_v3.json")
V3_SHA = "27d9d2d36efc6673f9268d059cd73eece157f8a43ebfa76e3b249d1975f2b88e"
G31_MUT = ["holdinv0", "rdon_clears", "fs5chg", "noclear_ld", "pendmask", "nooverrun", "rdnoclear"]


def test_g31_nominal(doc):
    assert doc["rev"] == "3.1" and doc["format"] == 3
    assert check_g31(doc) == 0


@pytest.mark.parametrize("mut", G31_MUT)
def test_g31_mutant_rejected(doc, mut):
    assert check_g31(doc, mut) > 0


def test_g31_semantics(doc):
    rd = seq(doc, "seq_rd")
    h = rd["hold"]
    assert [x["rd_rel"] for x in h] == ["after", "before", "on", "before", "on", None, "after", "after", "after",
                                        "after"]
    assert rd["dropped"] == [1, 3, 4, 5]
    assert [x["overrun"] for x in h] == [0, 0, 1, 0, 1, 1, 1, 0, 0, 0]
    assert [x["ready_end"] for x in h] == [0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    # on the load clk the rd is suppressed: the new frame stays ready (and keeps its overrun)
    assert h[2]["ready_end"] == 1 and h[2]["overrun_end"] == 1 and h[4]["ready_pre_load"] == 1
    assert h[3]["ready_pre_load"] == 0 and h[3]["overrun"] == 0          # before: old frame acked first
    # cfg_pending is the post-latch value: slots 1 and 3 load on a latch clk and show 0
    assert [x["cfg_pending"] for x in h][:6] == [0, 0, 1, 0, 1, 0]
    assert int(h[2]["status_full"], 16) >> 13 & 1 == 1 and int(h[2]["status_word"], 16) >> 13 & 1 == 0
    rs = seq(doc, "seq_reserved")
    assert [f["tags"]["invalid"] for f in rs["frames"]] == [1, 1, 0, 0, 0, 0, 1, 1, 1, 1]
    assert [x["cfg_pending"] for x in rs["hold"]][:8] == [0, 0, 0, 0, 0, 0, 1, 0]
    assert [f["tags"]["n_code"] for f in rs["frames"]] == [0] * 10        # fs_div is not in the tag
    hr = doc["hold_reset"]
    assert hr["tag_word"] == "0100" and hr["status_word"] == "0800" and hr["frame_ready"] == 0
    cs = {c["id"]: c["expect"] for c in doc["cfg_shift"]}
    assert cs["short_short"] == ["0016", "0007"] and cs["ld_ld"] == ["0003", "0000"] and cs["rst_clears"] == ["0005"]


def test_v3_rows_unchanged_in_v31(doc):
    """Every v3 row is a subset of the v3.1 row with the same id (v3.1 only adds keys and rows); a broken v3.1 fails."""
    with open(GOLD_V3) as f:
        txt = f.read()
    assert hashlib.sha256(txt.encode()).hexdigest() == V3_SHA
    v3 = json.loads(txt)
    assert v3["format"] == 3 and "rev" not in v3 and doc["rev"] == "3.1"
    for key in ("vectors", "streams", "sequences", "traces"):
        new = {r["id"]: r for r in doc[key]}
        assert len(v3[key]) < len(new) or key in ("vectors", "streams", "traces")
        for r in v3[key]:
            assert subset(r, new[r["id"]]), (key, r["id"])
        assert [r["id"] for r in doc[key]][:len(v3[key])] == [r["id"] for r in v3[key]]
    assert [r["id"] for r in doc["sequences"]][-2:] == ["seq_rd", "seq_reserved"]
    for k in ("reset", "fs_div_table", "word_order", "model", "seed"):
        assert doc[k] == v3[k]
    # D70 / AMB-18: the only debug_bus change since v3 is the y edge (falling -> rising, per D67)
    dv3 = {k: v for k, v in v3["debug_bus"].items() if k != "y_changes_on"}
    assert {k: v for k, v in doc["debug_bus"].items() if k != "y_changes_on"} == dv3
    assert v3["debug_bus"]["y_changes_on"].startswith("falling")
    assert doc["debug_bus"]["y_changes_on"].startswith("rising")
    bad = json.loads(json.dumps(doc))
    bad["sequences"][0]["hold"][3]["status_word"] = "0000"
    assert not subset(v3["sequences"][0], bad["sequences"][0])
