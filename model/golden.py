"""S6 golden-vector generator for the C9 decimator, frame and sequencer (tier 0, ideal-A).

Tier 0 = model/iadc.py with no noise, no leakage, no OTA non-idealities (Params defaults, xmax opened so nothing
clips), at the v1 loop coefficients option B (c1 = 1/8, c2 = 1/2, k = 1/2, so k/c1 = 4).

Every u is quantised to a multiple of 2^-20, so every float step of the loop is exact and the bitstream is
reproducible bit-for-bit by integer arithmetic (the independent checker in tests/test_golden.py does exactly that).

Conventions (see golden/README.md for the full format):
  - y[0] is forced to +1 at reset release (SPEC 3.6 rule 9, SPEC 3.2). SPEC does not state the value; +1 is what the
    model produces at x = 0 (comparator tie goes to +1) and is the choice made here.
  - exclusive S: acc2 += acc1 before acc1 += y.
  - decimator output is bitstream only (no u_corr), sys sign applied: num_signed = s * num, num = acc2 + 4 acc1
    (order 2, den = N(N-1)/2) or acc1 (order 1, den = N).
Usage: python -m model.golden [--out golden/s6_vectors.json]
"""
import argparse
import hashlib
import json

import numpy as np

from model import iadc

SEED = 20261109
N_SET = (64, 256, 1024, 4096)
NCODE = {n: i for i, n in enumerate(N_SET)}
C1, C2, K = 0.125, 0.5, 0.5
KC1 = 4                      # k / c1, exact integer for option B
CHOPS = ("off", "sys", "ota+sys")
GRID = 2 ** 20


def q(u):
    """Quantise to a multiple of 2^-20 (exact in float)."""
    return round(float(u) * GRID) / GRID


def params(order, N):
    return iadc.Params(order=order, N=N, c1=C1, c2=C2, k=K, xmax=1e6)


def cfg(order, N, chop, short, fs_div=0):
    return {"order": order, "N": N, "n_code": NCODE[N], "fs_div": fs_div,
            "ota_chop": chop == "ota+sys", "sys_chop": chop != "off", "short": bool(short), "chop_mode": chop,
            "pga": None}


def hexbits(y):
    b = "".join("1" if v > 0 else "0" for v in y)
    return "%0*x" % (len(b) // 4, int(b, 2))


def model_frame(c, u_eff, s):
    """Run the tier-0 model for one sub-conversion; return the frame payload (no tags)."""
    p = params(c["order"], c["N"])
    uh, st = iadc.convert(p, np.array([u_eff]), sys_sign=np.array([float(s)]), return_state=True)
    y = [int(v) for v in st["y"][:, 0]]
    assert y[0] == 1, "tier-0 y[0] must be +1 (forced value)"
    N = c["N"]
    acc1 = acc2 = 0
    for v in y:
        acc2 += acc1
        acc1 += v
    if c["order"] == 2:
        num, den = acc2 + KC1 * acc1, N * (N - 1) // 2
    else:
        acc2, num, den = None, acc1, N
    return {"n": N, "ybits": hexbits(y), "acc1": acc1, "acc2": acc2, "num": num, "den": den,
            "num_signed": s * num,
            "model_ref": {"u_hat_signed": float(uh[0]), "u_corr": float(st["u_corr"][0]),
                          "x1_final": float(st["x1_final"][0]), "x2_final": float(st["x2_final"][0])}}


def sign_of(c, slot):
    return -1 if (c["sys_chop"] and slot % 2 == 1) else 1


def sequencer(config0, slots):
    """Reference sequencer. slots[t] = {"request": cfg or None}; a request written during slot t latches at the
    next pair boundary (even slot) > t. Returns per-slot (active cfg, tags)."""
    active, pending = config0, None
    ctr, pair_idx, inv = 0, 0, False
    out = []
    for t, sl in enumerate(slots):
        if t % 2 == 0:
            if pending is not None:
                active, pending, pair_idx, inv = pending, None, 0, True
            elif t > 0:
                pair_idx, inv = pair_idx + 1, False
        tags = {"chop_sign": sign_of(active, t), "order": active["order"], "n_code": active["n_code"],
                "frame_ctr": ctr % 256, "pair_idx": pair_idx, "invalid": inv}
        out.append((active, tags))
        ctr += 1
        if sl.get("request") is not None:
            pending = sl["request"]
    return out


def make_frame(c, u_eff, t, tags):
    s = tags["chop_sign"]
    f = {"slot": t, "tags": tags}
    f.update(model_frame(c, u_eff, s))
    return f


def pair_value(fa, fb):
    return {"pair_num": fa["num_signed"] + fb["num_signed"], "pair_den": 2 * fa["den"]}


def u_list(N, rng):
    return [-0.9, -0.5, -1.3 / N, 0.0, 1.3 / N, 0.5, 0.9] + [float(rng.uniform(-0.9, 0.9)) for _ in range(2)]


def vector_mode(vid, order, N, chop, short, u_req):
    c = cfg(order, N, chop, short)
    u_eff = 0.0 if short else q(u_req)
    slots = [{}, {}]
    fr = [make_frame(a, u_eff, t, tags) for t, (a, tags) in enumerate(sequencer(c, slots))]
    return {"id": vid, "kind": "mode", "config": c, "u_requested": q(u_req), "u": u_eff, "frames": fr,
            "pair": pair_value(*fr)}


def sequence(sid, config0, slots, us, dropped, note):
    tg = sequencer(config0, slots)
    frames = [make_frame(a, us[t], t, tags) for t, (a, tags) in enumerate(tg)]
    recv = [f for f in frames if f["slot"] not in dropped]
    pairs = []
    for a in range(0, len(slots) - 1, 2):
        fa, fb = frames[a], frames[a + 1]
        complete = a not in dropped and a + 1 not in dropped
        d = {"slots": [a, a + 1], "complete": complete, "valid": not fa["tags"]["invalid"]}
        if complete:
            d.update(pair_value(fa, fb))
        pairs.append(d)
    return {"id": sid, "kind": "sequence", "note": note, "config0": config0,
            "slots": [{"request": sl.get("request"), "u": us[i]} for i, sl in enumerate(slots)],
            "dropped": sorted(dropped), "frames_sent": [f["slot"] for f in recv], "frames": frames, "pairs": pairs}


def build():
    rng = np.random.default_rng(SEED)
    vecs = []
    for order in (1, 2):
        for chop in CHOPS:
            for N in N_SET:
                us = u_list(N, rng)
                for short in (0, 1):
                    for i, u in enumerate(us):
                        if short and i != 3:       # internal short: input is CM, u is forced to 0, one vector
                            continue
                        vid = "o%d_%s_N%d_%s_u%d" % (order, chop.replace("+", "p"), N, "short" if short else "in", i)
                        vecs.append(vector_mode(vid, order, N, chop, short, u))
    c0 = cfg(2, 64, "sys", 0)
    cA = cfg(1, 256, "ota+sys", 0, fs_div=2)
    cB = cfg(2, 1024, "ota+sys", 0, fs_div=1)
    sl = [{} for _ in range(12)]
    sl[3]["request"], sl[4]["request"] = cA, cB
    seqs = [sequence("seq_cfgchange", c0, sl, [q(0.3)] * 12, [],
                     "request A written in slot 3 latches at slot 4 (pair 2, invalid); request B written in slot 4 "
                     "(just after the boundary) latches at slot 6 (pair 3, invalid); slot 5 still runs config A.")]
    sl = [{} for _ in range(8)]
    seqs.append(sequence("seq_drop", cfg(2, 256, "sys", 0), sl, [q(-0.25)] * 8, [3],
                         "frame of slot 3 is dropped on the link: frame_ctr jumps 2 -> 4; pair 1 is incomplete "
                         "and must be discarded, pairs 0, 2, 3 demodulate."))
    return {"format": 1, "seed": SEED, "grid": "u multiples of 2^-20",
            "model": {"c1": C1, "c2": C2, "k": K, "k_over_c1": KC1, "tier": 0}, "vectors": vecs, "sequences": seqs}


def dumps(doc):
    return json.dumps(doc, separators=(",", ":"), sort_keys=True) + "\n"


def sha(doc):
    return hashlib.sha256(dumps(doc).encode()).hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="golden/s6_vectors.json")
    a = ap.parse_args()
    d = build()
    txt = dumps(d)
    open(a.out, "w").write(txt)
    print(len(d["vectors"]), "mode vectors,", len(d["sequences"]), "sequences,", len(txt), "bytes, sha256",
          hashlib.sha256(txt.encode()).hexdigest())
