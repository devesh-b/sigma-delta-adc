"""Drive Ref A (or a Ref A mutant) through golden v3.1 items at clk level and collect mismatches.

Shared by test_refa_golden.py (agreement) and by the cocotb bench (expected-value generation).
Golden is fs-cycle granular; this harness maps a golden write at (slot t, cycle off) to a synchronised
shadow update on the edge that starts cycle `off` (the harmful boundary: off 0 = on the latch edge).
"""
import json
import os

from ref_a import RefA, RESET_CFG, DIV, fields

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.environ.get("C9_GOLDEN", os.path.join(HERE, "..", "..", "..", "golden", "s6_vectors.json"))


def load_golden(path=GOLDEN):
    with open(path) as f:
        return json.load(f)


def ybits(hexs, n):
    b = bin(int(hexs, 16))[2:].zfill(4 * len(hexs))
    assert len(b) >= n, (len(b), n)
    return [int(ch) for ch in b[:n]]


def h16(v):
    return v if isinstance(v, int) else int(v, 16)


def cfg_word(cfg):
    w = cfg.get("cfg_word")
    calc = ((cfg["order"] - 1) << 12) | (cfg["n_code"] << 10) | (cfg["fs_div"] << 7) | (cfg["sys_en"] << 6) \
        | (cfg["ota_en"] << 5) | (cfg["short"] << 4) | (cfg.get("boost", 0) << 3) | cfg.get("trim", 4) \
        | (cfg.get("rsv", 0) << 13)
    return calc if w is None else w, calc


class Run:
    """Clk-level driver for Ref A over a list of slots."""

    def __init__(self, ref, ybits_by_slot, writes=None, rd_plan=None, junk="raw0", wofs=1):
        self.wofs = wofs                   # write placement: clk after the start edge of cycle `off` (0 = on it)
        self.deferred = None
        self.end_probe = {}
        self.ends = {}
        self.ref = ref
        self.yb = ybits_by_slot            # slot -> list of N bits (missing slot: junk/alternating)
        self.writes = writes or {}         # (slot, off) -> [cfg words] (last applied wins on that edge)
        self.rd_plan = rd_plan or {}       # slot -> "before" | "on" | "after"
        self.junk = junk
        self.rows = []                     # control trace rows (post-state at every fs-cycle start)
        self.loads = {}                    # slot -> dict(pre_ready, pre_ovr, status, frame)
        self.after_rd = {}                 # slot of hold frame -> status after an rd clear
        self.rd_pin = {}                   # edge index -> 1
        self.n_edges = 0

    def comp_for(self, slot, c, N):
        n = c - 1                          # decision sampled in cycle c is y[n] with n = c - 1
        if 1 <= n <= N - 1 and slot in self.yb and n < len(self.yb[slot]):
            return self.yb[slot][n]
        if self.junk == "toggle":
            return self.ref.edge & 1
        return 0                           # golden comp_raw0 (always 0 = -1)

    def next_start(self):
        r = self.ref
        if not r.started:
            nxt = 0 if r.in_rst else r.rel_cnt + 1
            return (0, 0) if (r.rst_lat is not None and nxt >= r.lat()) else None
        if r.cnt != r.div - 1:
            return None
        if r.c + 1 >= r.N + 2:
            return (r.slot + 1, 0)
        return (r.slot, r.c + 1)

    def run(self, n_slots, ui_base=0, max_edges=50_000_000):
        r = self.ref
        while True:
            if r.started and r.slot >= n_slots:
                break
            self.n_edges += 1
            if self.n_edges > max_edges:
                raise RuntimeError("watchdog")
            ns = self.next_start()
            fl, self.deferred = self.deferred, None
            if ns is not None and ns in self.writes:
                if self.wofs == 0:
                    fl = self.writes[ns][-1]
                else:
                    self.deferred = self.writes[ns][-1]
            if ns is not None and ns[1] == 0 and ns[0] >= 0:
                # schedule rd pin for the load that ends slot ns[0] (new slot length is known after start)
                pass
            ui = ui_base | ((1 << 3) if self.rd_pin.get(r.edge + 1) else 0)
            slot, c = r.slot, r.c
            comp = self.comp_for(slot, c, r.N) if r.started else 0
            pre_ready, pre_ovr = r.frame_ready, r.overrun
            r.step(1, ui, comp, force_ld=fl)
            if ns is not None:
                k = r.ctl()
                self.rows.append("".join(str(k[f]) for f in ("rst_analog", "acc_clear", "sys_swap",
                                 "ota_chop_phase", "y_force", "bit_valid", "raw_pin", "tag_chop", "cfg_latch")))
                if ns[1] == 0:
                    self._plan_rd(r.slot)
            if "load" in r.events:
                fr = r.frames[-1]
                self.loads[fr["slot"]] = dict(pre_ready=pre_ready, pre_ovr=pre_ovr, status=r.status(), frame=fr,
                                              words=[r.word(a) for a in range(5)])
            if r.edge in self.end_probe:
                self.ends[self.end_probe[r.edge]] = (r.frame_ready, r.overrun)
            if "rd_clear" in r.events and r.frames:
                self.after_rd[r.frames[-1]["slot"]] = r.status()

    def _plan_rd(self, slot):
        r = self.ref
        load_edge = r.edge + (r.N + 2) * r.div      # this step started c = 0 (cnt 0); load = end of c = N+1
        self.end_probe[load_edge - 6] = slot - 1   # end state of slot-1 frame: after its rd, before ours
        rel = self.rd_plan.get(slot)
        if rel is None:
            return
        det = load_edge + {"before": -4, "on": 0, "after": 6}[rel]
        for e in range(det - 2, det + 2):           # pin high 4 clk; first sampled at det-2 -> act at det
            self.rd_pin[e] = 1


RD_LAG = int(os.environ.get("C9_RD_LAG", "0"))


def released_ref(mut=None, cfg0=None):
    ref = RefA(mut=mut, rst_lat=2, cfg0=cfg0, rd_lag=RD_LAG)
    for _ in range(3):
        ref.step(0)
    return ref


def run_vector(vec, mut=None, junk="raw0"):
    cw, calc = cfg_word(vec["config"])
    ref = released_ref(mut, None if cw == RESET_CFG else cw)
    yb = {f["slot"]: ybits(f["ybits"], f["n"]) for f in vec["frames"]}
    run = Run(ref, yb, rd_plan={s: "after" for s in yb}, junk=junk)   # host acks every frame
    run.run(max(yb) + 1)
    return run


def cmp_frames(tag, gframes, run, mism, slot_ofs=0, check_status=True):
    n = 0
    for g in gframes:
        ld = run.loads.get(g["slot"] + slot_ofs)
        if ld is None:
            mism.append(f"{tag} slot {g['slot']}: no load")
            continue
        fr = ld["frame"]
        got = dict(acc1=fr["acc1"], acc2=fr["acc2"], tag=fr["tag"], boost=fr["boost"], trim=fr["trim"],
                   words=["%04x" % w for w in ld["words"]])
        exp = dict(acc1=g["acc1"], acc2=g["acc2"], tag=h16(g["tag_word"]), boost=g.get("boost", 0),
                   trim=g.get("trim", 4), words=g.get("words"))
        if exp["words"] is None:
            got.pop("words"); exp.pop("words")
        wire = "".join(got.get("words", [])) if "words" in got else None
        if wire is not None and g.get("wire") and wire != g["wire"]:
            mism.append(f"{tag} slot {g['slot']}: wire {wire} != {g['wire']}")
        if check_status and "status_word" in g:
            sw = ld["status"] & ~(3 << 13)        # frame-level status_word: golden holds bits 14,13 at 0
            if sw != h16(g["status_word"]) & ~(3 << 13):
                mism.append(f"{tag} slot {g['slot']}: status {sw:04x} != {g['status_word']}")
        for k in exp:
            if got[k] != exp[k]:
                mism.append(f"{tag} slot {g['slot']}: {k} {got[k]} != {exp[k]}")
        n += 1
    return n


def seq_inputs(seq):
    writes = {}
    for t, s in enumerate(seq["slots"]):
        for w in s.get("writes", []):
            cw, _ = cfg_word(w["cfg"])
            writes.setdefault((t, w["off"]), []).append(cw)
    rd_plan = {}
    for h in seq.get("hold", []):
        if h.get("rd_rel"):
            rd_plan[h["slot"]] = h["rd_rel"]
        elif h.get("rd"):
            rd_plan[h["slot"]] = "after"
    return writes, rd_plan


def run_sequence(seq, mut=None, wofs=1):
    cw, _ = cfg_word(seq["config0"])
    ref = released_ref(mut, None if cw == RESET_CFG else cw)
    writes, rd_plan = seq_inputs(seq)
    yb = {}
    last = None
    for f in seq["frames"]:
        yb[f["slot"]] = ybits(f["ybits"], f["n"])
    run = Run(ref, yb, writes, rd_plan, wofs=wofs)
    # dropped slots have no golden frame: feed the previous frame's bits (not compared)
    nsl = len(seq["slots"])
    for t in range(nsl):
        if t not in yb:
            prev = [s for s in yb if s < t]
            last = yb[max(prev)] if prev else None
            if last is not None:
                yb[t] = last
    run.run(nsl + 1)
    return run


def cmp_hold(tag, seq, run, mism):
    n = 0
    for h in seq.get("hold", []):
        t = h["slot"]
        ld = run.loads.get(t)
        nxt = run.loads.get(t + 1)
        if ld is None:
            mism.append(f"{tag} hold {t}: no load"); continue
        st = ld["status"]
        chk = [("status_full", st, h16(h["status_full"]) if h.get("status_full") else None),
               ("status_word", st & ~(1 << 13), h16(h["status_word"]) if h.get("status_word") else None),
               ("cfg_pending", (st >> 13) & 1, h.get("cfg_pending")),
               ("overrun", (st >> 14) & 1, h.get("overrun")),
               ("ready_pre_load", ld["pre_ready"], h.get("ready_pre_load"))]
        if t in run.ends:
            chk += [("ready_end", run.ends[t][0], h.get("ready_end")),
                    ("overrun_end", run.ends[t][1], h.get("overrun_end"))]
        if h.get("status_after_rd"):
            chk.append(("status_after_rd", run.after_rd.get(t, -1) & ~(1 << 13), h16(h["status_after_rd"])))
        for name, got, exp in chk:
            if exp is None:
                continue
            if got != exp:
                mism.append(f"{tag} hold {t}: {name} {got:#x} != {exp:#x}")
        n += 1
    return n


def run_cfg_shift(case, mut=None):
    """ops 's:<bits>' / 'ld' / 'rst' through the serial pins (cfg_clk = clk/8, data stable 4 clk each side)."""
    ref = released_ref(mut)
    got = []

    def edge(ui, rst_n=1):
        ref.step(rst_n, ui, 0)
        if "ld" in ref.events:
            got.append("%04x" % ref.shadow)

    for op in case["ops"]:
        if op.startswith("s:"):
            for b in op[2:]:
                d = int(b) << 5
                for _ in range(4):
                    edge(d)
                for _ in range(4):
                    edge(d | (1 << 4))
            for _ in range(4):
                edge(0)
        elif op == "ld":
            for _ in range(4):
                edge(1 << 6)
            for _ in range(6):
                edge(0)
        elif op == "rst":
            for _ in range(3):
                edge(0, rst_n=0)
            for _ in range(4):
                edge(0)
    return got


def run_trace(tr, mut=None):
    run = run_sequence(tr, mut)
    return run
