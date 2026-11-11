"""S6b golden-vector generator (v3, WO-33; v2 rows unchanged) for the C9 decimator, frame and sequencer (tier 0, ideal-A).

Tier 0 = model/iadc.py with no noise, no leakage, no OTA non-idealities (Params defaults, xmax opened so nothing
clips), at the v1 loop coefficients option B (c1 = 1/8, c2 = 1/2, k = 1/2, so k/c1 = 4).

Every u is quantised to a multiple of 2^-20, so every float step of the loop is exact and the bitstream is
reproducible bit-for-bit by integer arithmetic (the independent checker in tests/test_golden.py does exactly that).

Conventions are SPEC section 3.7a (D45); see golden/README.md for the file format:
  - y[0] forced to +1 at reset release; the cycle-0 comparator bit is junk (frame field comp_raw0 = inverse of y[0]).
  - exclusive S: acc2 += acc1 before acc1 += y; order 1 keeps accumulating acc2 = sum S.
  - accumulators are emitted in the modulator frame (no sys sign); num_signed = chop_sign * num is a reference value.
  - 16-bit tag word, MSB first: chop, order, n_code(2), sys_en, ota_en, short, invalid, frame_ctr(8).
  - config latch on the clock edge that starts the reset window of an even slot; last write before it wins.
  - invalid: both frames of the first pair after rst_n and of the first pair after a change of the latched set.
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
CHOPS = ("off", "sys", "ota+sys", "ota")
GRID = 2 ** 20
LATCHED = ("order", "N", "fs_div", "sys_en", "ota_en", "short", "boost", "trim")
TRIM_RESET = 4               # binary 100 (D42)
# v3 (G3): config reset values (SPEC 3.8a register map), fs_div code table at clk 48 MHz, word order, debug bus, status
CLK_HZ = 48_000_000
RESET = {"order": 2, "n_code": 3, "N": 4096, "fs_div": 1, "sys_en": 1, "ota_en": 1, "short": 0, "boost": 0,
         "trim": TRIM_RESET}
FS_DIV_TABLE = {str(i): {"div": d, "fs_hz": CLK_HZ // d} for i, d in enumerate((12, 24, 48, 96, 192))}
FS_DIV_TABLE["reserved_5_7_as"] = 1
WORD_ORDER = ["acc1_hi", "acc1_lo", "acc2_hi", "acc2_lo", "tag", "status"]       # addr 0..5; 6, 7 read 0
DEBUG_BUS = {"uo_out": ["raw_y", "bit_valid", "valid_frame_ready", "fs_bit_clock", "rst_analog", "sys_swap",
                        "ota_chop_phase", "invalid_hold"], "uio": "status[7:0] = frame_ctr",
             "y_changes_on": "falling edge of the exported bit clock"}
STATUS_LAYOUT = {"15": "frame_ready", "14": "overrun", "13": "cfg_pending (host-timing dependent: golden holds 0)",
                 "12": "boost of hold-register frame", "11:9": "trim of hold-register frame", "8": "0",
                 "7:0": "frame_ctr of hold-register frame"}
RST_LEN = 2                 # reset window, fs cycles (D45 i)
TRACE_FIELDS = ["rst_analog", "acc_clear", "sys_swap", "ota_chop_phase", "y_force", "bit_valid", "raw_pin",
                "tag_chop", "cfg_latch"]
_CACHE = {}


def q(u):
    """Quantise to a multiple of 2^-20 (exact in float)."""
    return round(float(u) * GRID) / GRID


def params(order, N):
    return iadc.Params(order=order, N=N, c1=C1, c2=C2, k=K, xmax=1e6)


def cfg_word(c):
    """16-bit serial config register (SPEC 3.8a): order 12, n_code 11:10, fs_div 9:7, sys_en 6, ota_en 5, short 4,
    boost 3, trim 2:0; order bit 1 = order 2."""
    return ((int(c["order"] == 2) << 12) | (c["n_code"] << 10) | (c["fs_div"] << 7) | (c["sys_en"] << 6)
            | (c["ota_en"] << 5) | (c["short"] << 4) | (c["boost"] << 3) | c["trim"])


def cfg(order, N, chop, short, fs_div=0, boost=0, trim=TRIM_RESET):
    c = {"order": order, "N": N, "n_code": NCODE[N], "fs_div": fs_div,
         "sys_en": int(chop in ("sys", "ota+sys")), "ota_en": int(chop in ("ota", "ota+sys")),
         "short": int(bool(short)), "chop_mode": chop, "boost": boost, "trim": trim}
    c["cfg_word"] = cfg_word(c)
    return c


def status_word(ready, overrun, boost, trim, ctr):
    """SPEC 3.8a status (addr 5). cfg_pending (bit 13) depends on host timing and is held 0 in the golden."""
    return (ready << 15) | (overrun << 14) | (boost << 12) | (trim << 9) | (ctr & 255)


def extras(c, f):
    """G3 per-frame fields: boost/trim of the frame, the 5 readout words (addr 0..4), status word as read right
    after the load with frame_ready 1, overrun 0 (sequences carry the real hold-register history in `hold`)."""
    f["boost"], f["trim"] = c["boost"], c["trim"]
    f["words"] = [f["wire"][4 * i:4 * i + 4] for i in range(5)]
    f["status_word"] = "%04x" % status_word(1, 0, c["boost"], c["trim"], f["tags"]["frame_ctr"])
    return f


def changed(a, b):
    return any(a[k] != b[k] for k in LATCHED)


def hexbits(y):
    b = "".join("1" if v > 0 else "0" for v in y)
    return "%0*x" % (len(b) // 4, int(b, 2))


def accumulate(y):
    a1 = a2 = 0
    for v in y:
        a2 += a1
        a1 += v
    return a1, a2


def tag_word(t):
    return ((t["chop"] << 15) | (t["order"] << 14) | (t["n_code"] << 12) | (t["sys_en"] << 11) | (t["ota_en"] << 10)
            | (t["short"] << 9) | (t["invalid"] << 8) | t["frame_ctr"])


def frame_core(c, y, s):
    """Accumulator words and reference values from a +-1 stream y (list) and sys sign s."""
    N = c["N"]
    assert len(y) == N and y[0] == 1
    a1, a2 = accumulate(y)
    if c["order"] == 2:
        num, den = a2 + KC1 * a1, N * (N - 1) // 2
    else:
        num, den = a1, N
    return {"n": N, "ybits": hexbits(y), "comp_raw0": 1 if y[0] < 0 else 0, "acc1": a1, "acc2": a2,
            "num": num, "den": den, "num_signed": s * num}


def model_frame(c, u, off, s):
    """Tier-0 model for one sub-conversion. Modulator input = s*u + off (the offset is added after the swap)."""
    if c["short"]:
        u, off = 0.0, 0.0
    uf = u + s * off                       # input-frame value; the model applies s itself (sys_sign)
    key = (c["order"], c["N"], uf, s)
    if key not in _CACHE:
        p = params(c["order"], c["N"])
        uh, st = iadc.convert(p, np.array([uf]), sys_sign=np.array([float(s)]), return_state=True)
        y = [int(v) for v in st["y"][:, 0]]
        assert y[0] == 1, "tier-0 y[0] must be +1 (forced value)"
        ref = {"u_hat_signed": float(uh[0]), "u_corr": float(st["u_corr"][0]),
               "x1_final": float(st["x1_final"][0]), "x2_final": float(st["x2_final"][0]), "u_frame": uf}
        _CACHE[key] = (y, ref)
    y, ref = _CACHE[key]
    d = frame_core(c, y, s)
    assert abs(ref["u_hat_signed"] * d["den"] - d["num_signed"]) < 1e-6, (key, ref["u_hat_signed"], d)
    d["model_ref"] = ref
    return d


def tag_fields(c, t, inv):
    return {"chop": int(bool(c["sys_en"]) and t % 2 == 1), "order": int(c["order"] == 2), "n_code": c["n_code"],
            "sys_en": c["sys_en"], "ota_en": c["ota_en"], "short": c["short"], "invalid": int(inv),
            "frame_ctr": t & 255}


def sequencer(config0, slots):
    """Reference sequencer (D45 c, d, e). slots[t] = {"writes": [{"off": cycle in slot, "cfg": cfg}]}.
    Latch: shadow -> active on the clock edge that starts the reset window of an even slot. All writes made
    before that edge (earlier slots, any offset) count, the last wins; a write in the even slot itself (offset >= 0,
    on or after the edge) applies to the next pair. Invalid: pair 0 (after rst_n) and the first pair after a change."""
    active, pending, inv, out = config0, None, False, []
    for t, sl in enumerate(slots):
        if t % 2 == 0:
            inv = t == 0
            if pending is not None:
                inv = inv or changed(pending, active)
                active, pending = pending, None
        out.append((active, tag_fields(active, t, inv)))
        for w in sorted(sl.get("writes", []), key=lambda w: w["off"]):
            assert 0 <= w["off"] <= active["N"] + RST_LEN - 1, "write offset outside the slot"
            pending = w["cfg"]
    return out


def make_frame(c, u, off, t, tags):
    s = -1 if tags["chop"] else 1
    f = {"slot": t, "tags": tags, "tag_word": tag_word(tags)}
    f.update(model_frame(c, u, off, s))
    f["wire"] = "%08x%08x%04x" % (f["acc1"] & 0xFFFFFFFF, f["acc2"] & 0xFFFFFFFF, f["tag_word"])
    return extras(c, f)


def pair_value(fa, fb):
    return {"pair_num": fa["num_signed"] + fb["num_signed"], "pair_den": 2 * fa["den"]}


def u_list(N, rng):
    return [-0.9, -0.5, -1.3 / N, 0.0, 1.3 / N, 0.5, 0.9] + [float(rng.uniform(-0.9, 0.9)) for _ in range(2)]


def vector_mode(vid, kind, order, N, chop, short, u_req, off=0.0, boost=0, trim=TRIM_RESET, fs_div=0):
    c = cfg(order, N, chop, short, fs_div, boost, trim)
    u = 0.0 if short else q(u_req)
    fr = [make_frame(a, u, off, t, tags) for t, (a, tags) in enumerate(sequencer(c, [{}, {}]))]
    return {"id": vid, "kind": kind, "config": c, "u_requested": q(u_req), "u": u, "off": 0.0 if short else off,
            "frames": fr, "pair": pair_value(*fr)}


def stream_vector(sid, order, y, note):
    c = cfg(order, 4096, "off", 0)
    (a, tags), = sequencer(c, [{}])
    s = 1
    f = {"slot": 0, "tags": tags, "tag_word": tag_word(tags)}
    f.update(frame_core(c, y, s))
    f["wire"] = "%08x%08x%04x" % (f["acc1"] & 0xFFFFFFFF, f["acc2"] & 0xFFFFFFFF, f["tag_word"])
    extras(c, f)
    return {"id": sid, "kind": "stream", "loop_valid": False, "note": note, "config": c, "frames": [f]}


def sequence(sid, config0, slots, us, dropped, note, kind="sequence"):
    tg = sequencer(config0, slots)
    frames = [make_frame(a, us[t], 0.0, t, tags) for t, (a, tags) in enumerate(tg)]
    recv = [f for f in frames if f["slot"] not in dropped]
    pairs = []
    for a in range(0, len(slots) - 1, 2):
        fa, fb = frames[a], frames[a + 1]
        complete = a not in dropped and a + 1 not in dropped
        d = {"slots": [a, a + 1], "complete": complete, "valid": not fa["tags"]["invalid"]}
        if complete:
            d.update(pair_value(fa, fb))
        pairs.append(d)
    return {"id": sid, "kind": kind, "note": note, "config0": config0,
            "slots": [{"writes": sl.get("writes", []), "u": us[i]} for i, sl in enumerate(slots)],
            "dropped": sorted(dropped), "frames_sent": [f["slot"] for f in recv], "frames": frames, "pairs": pairs,
            "hold": hold_history(frames, dropped)}


def hold_history(frames, dropped):
    """Hold-register / status history (SPEC 3.8a buffering). One load per slot (end of slot): frame_ready = 1; if the
    previous frame was never rd-acked (it is in `dropped`) the load overwrites it and sets overrun. A `rd` edge
    clears frame_ready and overrun (the hold register keeps the frame, so boost/trim/frame_ctr stay)."""
    out, unread = [], False
    for f in frames:
        t, b, tr, ctr = f["slot"], f["boost"], f["trim"], f["tags"]["frame_ctr"]
        h = {"slot": t, "overrun": int(unread), "status_word": "%04x" % status_word(1, int(unread), b, tr, ctr)}
        h["rd"] = int(t not in dropped)
        h["status_after_rd"] = "%04x" % status_word(0, 0, b, tr, ctr) if h["rd"] else None
        unread = not h["rd"]
        out.append(h)
    return out


def control_trace(seq):
    """Cycle-level control trace (D45 i). Slot = reset window (cycles 0, 1) then N conversion cycles (n = c - 2).
    One 9-character row per fs cycle, field order TRACE_FIELDS:
      rst_analog 1 on cycles 0-1; acc_clear 1 on cycle 1 (the edge that releases reset clears the accumulators);
      sys_swap = swap level, set from cycle 0 of the slot (inside the reset window), held to the slot end;
      ota_chop_phase 0 in reset, then n mod 2 (fch = fs/2) when ota_en, else 0; y_force 1 on n = 0;
      bit_valid 1 on n = 0..N-1; raw_pin = retimed y (y[0] forced +1), 0 when bit_valid is 0;
      tag_chop = chop bit of the frame (same flop as sys_swap); cfg_latch 1 on cycle 0 of even slots."""
    cfgs = sequencer(seq["config0"], [{"writes": sl["writes"]} for sl in seq["slots"]])
    rows = []
    for t, (c, tg) in enumerate(cfgs):
        f = seq["frames"][t]
        y = [1 if ch == "1" else 0 for ch in bin(int(f["ybits"], 16))[2:].zfill(c["N"])]
        swap = int(c["sys_en"] and t % 2 == 1)
        for cyc in range(c["N"] + RST_LEN):
            n = cyc - RST_LEN
            rows.append("".join(str(int(v)) for v in (
                cyc < RST_LEN, cyc == RST_LEN - 1, swap, (n % 2 if c["ota_en"] and n >= 0 else 0), n == 0, n >= 0,
                (y[n] if n >= 0 else 0), tg["chop"], t % 2 == 0 and cyc == 0)))
    return {"fields": TRACE_FIELDS, "rst_len": RST_LEN, "rows": rows}


def build():
    _CACHE.clear()
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
                        vecs.append(vector_mode(vid, "mode", order, N, chop, short, u))
    # m10: dyadic offset added after the swap, u_eff = s*u + off; a correct pair returns u
    for order in (1, 2):
        for chop in ("sys", "ota+sys"):
            for N in (64, 256, 1024):
                for u in (0.25, -0.5):
                    for off in (0.125, -0.125):
                        vid = "off_o%d_%s_N%d_u%s_off%s" % (order, chop.replace("+", "p"), N, u, off)
                        vecs.append(vector_mode(vid, "offset", order, N, chop, 0, u, off))
    streams = []
    n = 4096
    streams.append(stream_vector("st_o2_allp", 2, [1] * n, "y all +1 (acc1 = 4096, acc2 = N(N-1)/2)"))
    streams.append(stream_vector("st_o2_pm", 2, [1] + [-1] * (n - 1), "y[0] = +1 then all -1 (acc2 about -N^2/2)"))
    streams.append(stream_vector("st_o2_alt", 2, [1 if i % 2 == 0 else -1 for i in range(n)], "alternating +1, -1"))
    streams.append(stream_vector("st_o1_allp", 1, [1] * n, "order 1, y all +1"))

    c0 = cfg(2, 64, "sys", 0)
    cA = cfg(1, 256, "ota+sys", 0, fs_div=2)
    cB = cfg(2, 1024, "ota+sys", 0, fs_div=1)
    sl = [{} for _ in range(12)]
    sl[3]["writes"] = [{"off": 10, "cfg": cA}]
    sl[4]["writes"] = [{"off": 3, "cfg": cB}]
    seqs = [sequence("seq_cfgchange", c0, sl, [q(0.3)] * 12, [],
                     "write A in slot 3 latches at slot 4 (pair 2, invalid); write B in slot 4 (after the edge) "
                     "latches at slot 6 (pair 3, invalid); slot 5 still runs config A.")]
    sl = [{} for _ in range(8)]
    seqs.append(sequence("seq_drop", cfg(2, 256, "sys", 0), sl, [q(-0.25)] * 8, [3],
                         "frame of slot 3 is dropped on the link: frame_ctr jumps 2 -> 4; pair 1 is incomplete "
                         "and must be discarded, pairs 0, 2, 3 demodulate."))
    c64 = cfg(2, 64, "ota+sys", 0)
    c64s = cfg(2, 64, "ota+sys", 1)
    sl = [{} for _ in range(10)]
    sl[2]["writes"] = [{"off": 30, "cfg": c64s}]
    sl[7]["writes"] = [{"off": 40, "cfg": c64}]
    seqs.append(sequence("seq_short", c64, sl, [q(0.3)] * 10, [],
                         "short written mid-slot 2 (first slot of pair 1): pair 1 (slots 2,3) is unchanged and valid, "
                         "the short applies from slot 4 (pair 2, invalid, u forced to 0). Written back to 0 in slot 7: "
                         "applies from slot 8 (invalid)."))
    x1, x2 = cfg(1, 64, "sys", 0), cfg(2, 256, "sys", 0)
    x3, y = cfg(2, 64, "sys", 0, fs_div=1), cfg(2, 64, "sys", 0, fs_div=2)
    sl = [{} for _ in range(8)]
    sl[1]["writes"] = [{"off": 5, "cfg": x1}, {"off": 20, "cfg": x2}, {"off": 40, "cfg": x3}]
    sl[2]["writes"] = [{"off": 0, "cfg": y}]
    seqs.append(sequence("seq_multiwrite", c0, sl, [q(0.3)] * 8, [],
                         "three writes in slot 1: the last (x3, fs_div 1) wins and latches at slot 2 (invalid pair 1). "
                         "A write in slot 2 at offset 0 (y, fs_div 2) is on the edge or later: it latches at slot 4."))
    a = cfg(1, 64, "sys", 0)
    b = cfg(2, 64, "sys", 0, fs_div=3)
    sl = [{} for _ in range(8)]
    sl[3]["writes"] = [{"off": 65, "cfg": a}]
    sl[4]["writes"] = [{"off": 0, "cfg": b}]
    seqs.append(sequence("seq_edge", c0, sl, [q(0.3)] * 8, [],
                         "write A at the last cycle of slot 3 (before the slot-4 edge) latches at slot 4; "
                         "write B at offset 0 of slot 4 (on the edge) latches at slot 6, so A runs in pair 2."))
    sl = [{} for _ in range(262)]
    seqs.append(sequence("seq_wrap", cfg(2, 64, "ota+sys", 0), sl, [q(0.3)] * 262, [],
                         "262 slots (131 pairs) at N 64, constant u: frame_ctr wraps 255 -> 0 at slot 256; "
                         "the two ybits (s = +1, -1) are reused by every frame."))
    sl = [{} for _ in range(6)]
    sl[2]["writes"] = [{"off": 10, "cfg": cfg(1, 64, "ota+sys", 0)}]
    tr = sequence("trace_ctl", c64, sl, [q(0.3)] * 6, [],
                  "N 64, sys + ota chop, pairs 0 and 1, write (order 1) in slot 2 latching at slot 4, then pair 2. "
                  "Control trace per fs cycle, 66 cycles per slot.", kind="trace")
    tr["trace"] = control_trace(tr)
    # ---- G3 (v3) additions, appended so every v2 row is unchanged ----
    vecs.append(vector_mode("rst_default", "reset", RESET["order"], RESET["N"], "ota+sys", 0, 0.3, 0.0,
                            fs_div=RESET["fs_div"]))      # the whole reset config: boost 0, trim 100
    for boost in (0, 1):
        for trim in range(8):
            vecs.append(vector_mode("bt_b%d_t%d" % (boost, trim), "boosttrim", 2, 64, "ota+sys", 0, 0.3, 0.0,
                                    boost=boost, trim=trim))
    cb = cfg(2, 64, "sys", 0, boost=1)
    sl = [{} for _ in range(10)]
    sl[0]["writes"] = [{"off": 10, "cfg": cb}]
    sl[3]["writes"] = [{"off": 5, "cfg": cb}]
    sl[4]["writes"] = [{"off": 3, "cfg": cfg(2, 64, "sys", 0, boost=1, trim=6)}]
    sl[5]["writes"] = [{"off": 20, "cfg": cfg(2, 64, "sys", 0, boost=1, trim=2)}]
    sl[6]["writes"] = [{"off": 65, "cfg": cfg(2, 64, "sys", 0, boost=0, trim=2)}]
    seqs.append(sequence("seq_boosttrim", c0, sl, [q(0.3)] * 10, [3],
                         "boost written in slot 0 latches at slot 2 (pair 1, invalid), never mid-pair (slot 1 still "
                         "boost 0); the same value again in slot 3 is not a change; trim 6 then trim 2 written in "
                         "slots 4, 5 (last wins) latch at slot 6 (pair 3, invalid); boost 0 written at the last cycle "
                         "of slot 6 latches at slot 8 (pair 4, invalid). Slot 3 is not read: slot 4 loads with "
                         "overrun, status [12:9] follows the hold-register frame."))
    return {"format": 3, "seed": SEED, "grid": "u multiples of 2^-20", "reset": RESET, "clk_hz": CLK_HZ,
            "fs_div_table": FS_DIV_TABLE, "word_order": WORD_ORDER, "debug_bus": DEBUG_BUS,
            "status_layout": STATUS_LAYOUT,
            "model": {"c1": C1, "c2": C2, "k": K, "k_over_c1": KC1, "tier": 0}, "vectors": vecs, "streams": streams,
            "sequences": seqs, "traces": [tr]}


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
    nfr = (sum(len(v["frames"]) for v in d["vectors"]) + len(d["streams"])
           + sum(len(s["frames"]) for s in d["sequences"] + d["traces"]))
    print(len(d["vectors"]), "vectors,", len(d["streams"]), "streams,", len(d["sequences"]), "sequences,",
          len(d["traces"]), "trace,", nfr, "frames,", len(d["traces"][0]["trace"]["rows"]), "trace cycles,",
          len(txt), "bytes, sha256", hashlib.sha256(txt.encode()).hexdigest())
