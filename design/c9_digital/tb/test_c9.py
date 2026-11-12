"""C9 cocotb bench (WO-38), written from SPEC 3.7a/3.8/3.8a, D45-D48, D66, D67 and golden v3.1 only.

DUT: the TT pins (clk, rst_n, ena, ui_in, uo_out, uio_in, uio_out, uio_oe) plus the C9 digital<->analog port
contract of SPEC 3.8a (comparator in; rst_analog, sys_swap, ota_chop_phase, short, order, boost, trim,
y_force, bit_valid, fs bit clock, DAC y out).  The SPEC names the signals but not the HDL port names, so
they are resolved from candidate lists (top level, then one/two scopes down; override with
C9_PORTMAP="logical=hdl_name,...").  A missing contract port is a FAIL ("PORT-CONTRACT"), not a skip.

Always-on checkers (every test, every clk):
  * analog-side control ports == Ref A, clk-exact (one release-alignment, bounded and determinism-checked);
  * read bus (uo:uio) == Ref A at one fixed lag d <= 3 clk (CL-21), except 3 clk after an addr/dbg change;
  * uio_oe == 0xFF; no X/Z on uo_out / uio_out / uio_oe after the first clk with rst_n low;
  * host-read frames == Ref A frame, and == golden where a vector exists; empty compares fail.
Seeds: C9_SEED (default 1).  Long items: C9_FULL=1.
"""
import copy
import os
import random
import sys
from collections import deque

import cocotb
from cocotb.clock import Clock
from cocotb.handle import Force
from cocotb.triggers import Event, FallingEdge, Timer

import golden_harness as gh
from fcov import FCov
from ref_a import DIV, N_OF, RESET_CFG, RefA, eff, fields

FULL = os.environ.get("C9_FULL", "0") == "1"
SEED = int(os.environ.get("C9_SEED", "1"))
CTL = ("rst_analog", "sys_swap", "ota_chop_phase", "short", "order", "boost", "trim", "y_force", "bit_valid",
       "fs_clk")
OPT = ("dac_y", "acc_clear", "cfg_latch", "tag_chop")
CAND = {
    "comp": ["comp", "comp_in", "comp_i", "cmp", "cmp_in", "cmp_i", "comp_out", "comparator", "comp_y"],
    "rst_analog": ["rst_analog", "rst_analog_o", "ana_rst"],
    "sys_swap": ["sys_swap", "sys_swap_o", "swap"],
    "ota_chop_phase": ["ota_chop_phase", "ota_chop_phase_o", "ota_chop", "ota_phase", "ota_ph"],
    "short": ["short", "short_o", "ana_short", "short_en", "in_short"],
    "order": ["order", "order_o", "ana_order", "order2", "int2_en"],
    "boost": ["boost", "boost_o", "ana_boost"],
    "trim": ["trim", "trim_o", "ana_trim", "bias_trim"],
    "y_force": ["y_force", "y_force_o"],
    "bit_valid": ["bit_valid", "bit_valid_o"],
    "fs_clk": ["fs_clk", "fs_clk_o", "bit_clk", "bitclk", "fs_bit_clk", "fs_bitclk", "fsclk"],
    "dac_y": ["dac_y", "y_dac", "dac_o", "y_o", "y_out", "dac", "y", "ybit", "y_q"],
    "acc_clear": ["acc_clear"], "cfg_latch": ["cfg_latch"], "tag_chop": ["tag_chop"],
}


def lv(h):
    s = str(h.value).lower()
    if "x" in s or "z" in s or "u" in s or "w" in s:
        return None
    return int(s, 2)


class TB:
    def __init__(self, dut):
        self.dut = dut
        self.err, self.nerr, self.nchk = [], 0, {}
        self.ports, self.forced = {}, set()
        over = dict(kv.split("=") for kv in os.environ.get("C9_PORTMAP", "").split(",") if "=" in kv)
        for name in list(CTL) + list(OPT) + ["comp"]:
            h = self._find(over.get(name), CAND[name])
            if h is not None:
                self.ports[name] = h
        self.missing = [n for n in list(CTL) + ["comp"] if n not in self.ports]
        self.ref = RefA(rst_lat="d70", rd_lag=int(os.environ.get("C9_RD_LAG", "1")))
        self.ui, self.rst_n, self.comp = 0, 0, 0
        self.a_ui, self.a_rst_n = 0, 0       # values actually on the DUT pins at the next rising edge
        self.yb = {}                 # absolute slot -> golden bits for the comparator BFM
        self.comp_mode = os.environ.get("C9_COMP", "window")
        self.rng = random.Random(SEED)
        self.tasks = []
        self.tick = Event()
        self.lat_hist = []
        self.hist = deque(maxlen=6)   # ref pin-level bus values, newest last
        self.bus_lag = None
        self.settle = 0
        self.last = {}
        self.reads = []               # host frames: dict(words, status, ref_frame, discard)
        self.host_auto = False
        self.host_ack = True
        self.loads_seen = 0
        self.edges = 0
        self.first_rst_seen = False
        self.ctl_strict = True
        self.cov = FCov()
        self.place_n = self.place_miss = 0

    def _find(self, forced, cands):
        names = [forced] if forced else cands
        scopes = [self.dut]
        try:
            kids = [k for k in self.dut if hasattr(k, "_sub_handles") or True]
        except Exception:
            kids = []
        for k in kids:
            scopes.append(k)
        for sc in scopes:
            for n in names:
                try:
                    h = getattr(sc, n)
                    _ = h.value
                    return h
                except Exception:
                    continue
        return None

    def fail(self, msg):
        self.nerr += 1
        if len(self.err) < 40:
            self.err.append(f"[edge {self.edges} slot {self.ref.slot} c {self.ref.c}] {msg}")

    def chk(self, k):
        self.nchk[k] = self.nchk.get(k, 0) + 1

    async def start(self):
        d = self.dut
        cocotb.start_soon(Clock(d.clk, 20, unit="ns").start())
        d.ena.value = 1
        d.uio_in.value = 0
        d.ui_in.value = 0
        d.rst_n.value = 0
        self._drive_comp(0)
        cocotb.start_soon(self._loop())
        await self.clks(3)

    def _drive_comp(self, v):
        h = self.ports.get("comp")
        if h is None:
            return
        try:
            h.value = v
        except Exception:
            h.value = Force(v)

    # ------------------------------------------------------------------ the clk loop
    async def _loop(self):
        d, r = self.dut, self.ref
        while True:
            await FallingEdge(d.clk)
            self.edges += 1
            out = {k: lv(h) for k, h in self.ports.items()}
            uo, uio, oe = lv(d.uo_out), lv(d.uio_out), lv(d.uio_oe)
            if self.rst_n == 0:
                self.first_rst_seen = True
            if self.first_rst_seen:
                if None in (uo, uio, oe):
                    self.fail(f"X/Z on outputs uo={d.uo_out.value} uio={d.uio_out.value} oe={d.uio_oe.value}")
                self.chk("x")
                if oe != 0xFF:
                    self.fail(f"uio_oe = {oe}")
            # release latency (CL-19, CL-27 / D70): Ref A starts slot 0 itself at e(1 + div); the DUT fs bit
            # clock must first rise on exactly that edge (no bench alignment)
            start_now = False
            if self.a_rst_n and not r.started and out.get("fs_clk") == 1:
                lat = (r.rel_cnt + 1) if not r.in_rst else 0
                self.lat_hist.append(lat)
                if lat != r.lat():
                    self.fail(f"release-to-slot latency {lat} != {r.lat()} (D70; history {self.lat_hist})")
                    start_now = True
                self.chk("rst_lat")
            if self.a_rst_n and not r.started and not start_now and r.rel_cnt > 192 + 6:
                self.fail("no fs bit clock rise after rst_n release")
                start_now = True
            self.cov.pre(self)
            r.step(self.a_rst_n, self.a_ui, self.comp, start_now=start_now)
            self.cov.post(self)
            # ---- control ports, clk-exact
            if not self.missing:
                k = r.ctl()
                for name in CTL + OPT:
                    if name in out and name in k and not (name == "dac_y" and not k["bit_valid"]):
                        if out[name] != k[name]:
                            self.fail(f"{name} dut={out[name]} ref={k[name]}")
                        self.chk(name)
            # ---- bus (fixed lag <= 3)
            pin_val = r.dbg_word() if (self.a_ui >> 7) & 1 else r.word(self.a_ui & 7)
            self.hist.append(pin_val)
            bus = None if None in (uo, uio) else (uo << 8) | uio
            if self.settle > 0:
                self.settle -= 1
            elif bus is not None and len(self.hist) >= 4 and r.started:
                hl = list(self.hist)[-4:][::-1]
                if self.bus_lag is None:
                    m = [lag for lag in range(4) if hl[lag] == bus]
                    if len(m) == 1 and len(set(hl)) == 4:
                        self.bus_lag = m[0]
                    ok = bool(m)
                else:
                    ok = hl[self.bus_lag] == bus
                if not ok:
                    self.fail(f"bus {bus:04x} != ref {[hex(x) for x in list(self.hist)[-4:]]} "
                              f"(ui {self.ui:02x}, lag {self.bus_lag})")
                    self.bus_lag = None
                self.chk("bus")
            self.last = dict(out, bus=bus)
            if "load" in r.events:
                self.loads_seen += 1
                if self.host_auto:
                    self.tasks.append(self._host_read(r.frames[-1]))
            # ---- comparator BFM for the next edge (from Ref A's position, contract CL-23)
            self.comp = self._comp_next()
            self._drive_comp(self.comp)
            # ---- drivers (generators, one step per clk)
            for t in list(self.tasks):
                try:
                    next(t)
                except StopIteration:
                    self.tasks.remove(t)
            d.ui_in.value = self.ui
            d.rst_n.value = self.rst_n
            self.a_ui, self.a_rst_n = self.ui, self.rst_n
            self.tick.set()
            self.tick.clear()

    def _comp_next(self):
        r = self.ref
        if not r.started:
            return self.edges & 1 if self.comp_mode != "plain" else 0
        c, N, cnt, div = r.c, r.N, r.cnt, r.div
        n = c - 1
        bits = self.yb.get(r.slot)
        good = None
        if 1 <= n <= N - 1:
            good = bits[n] if (bits is not None and n < len(bits)) else self.rng.getrandbits(1)
            if bits is None:
                self.yb.setdefault(("rand", r.slot), {})[n] = good
        samp = div // 2 - 1                      # Ref A samples at the edge after pre-state cnt == samp
        nxt_cnt = cnt + 1 if cnt < div - 1 else 0
        if good is None:
            return (self.edges & 1) if self.comp_mode != "plain" else 0   # reset window / c = N+1: junk
        if self.comp_mode == "plain":
            return good
        return good if abs(nxt_cnt - samp) <= 1 else (1 - good)          # correct only at fall edge +-1 clk

    # ------------------------------------------------------------------ utilities
    async def clks(self, n):
        for _ in range(n):
            await self.tick.wait()

    async def until(self, cond, max_clk, what):
        for _ in range(max_clk):
            if cond():
                return True
            await self.tick.wait()
        self.fail(f"watchdog: {what} not reached in {max_clk} clk")
        return False

    def set_ui(self, mask, val):
        self.ui = (self.ui & ~mask) | (val & mask)
        if mask & 0x87:
            self.settle = 4

    async def reset(self, n=10):
        self.tasks = []                    # no driver or host read survives a reset
        self.set_ui(0xFF, 0)
        self.rst_n = 0
        await self.clks(n)
        self.rst_n = 1
        await self.until(lambda: self.ref.started, 60, "slot 0 start")

    def slot_clks(self):
        return (self.ref.N + 2) * self.ref.div

    async def to_slot(self, s, c=0):
        r = self.ref
        await self.until(lambda: r.slot > s or (r.slot == s and r.c >= c), (abs(s - r.slot) + 2) * 4098 * 192,
                         f"slot {s} c {c}")

    # ------------------------------------------------------------------ drivers (generators)
    def g_cfg_write(self, word, half=2, ld=True):
        """MSB first, cfg_dat set half clk before the cfg_clk rise and held half clk after (>= 2 clk, 3.8a)."""
        for i in range(15, -1, -1):
            self.set_ui(0x30, ((word >> i) & 1) << 5)
            for _ in range(half):
                yield
            self.set_ui(0x10, 0x10)
            for _ in range(half):
                yield
            self.set_ui(0x10, 0)
        for _ in range(half):
            yield
        if ld:
            self.set_ui(0x40, 0x40)
            for _ in range(4):
                yield
            self.set_ui(0x40, 0)
            yield

    def g_rd(self, width=4):
        self.set_ui(0x08, 0x08)
        for _ in range(width):
            yield
        self.set_ui(0x08, 0)
        yield

    def _host_read(self, ref_frame):
        words = []
        for a in (0, 1, 2, 3, 4, 5):
            self.set_ui(0x07, a)
            for _ in range(4):
                yield
            words.append(self.last.get("bus"))
        st, tg = words[5], words[4]
        discard = None if None in (st, tg) else bool((st >> 14) & 1 or (tg & 0xFF) != (st & 0xFF))
        self.reads.append(dict(words=words, ref=ref_frame, discard=discard))
        h = ref_frame
        a1, a2 = h["acc1"] & 0xFFFFFFFF, h["acc2"] & 0xFFFFFFFF
        exp = [a1 >> 16, a1 & 0xFFFF, a2 >> 16, a2 & 0xFFFF, h["tag"]]
        if not discard and words[:5] != exp:
            self.fail(f"host frame slot {h['slot']} {['%04x' % w if w is not None else 'X' for w in words]} "
                      f"!= ref {['%04x' % w for w in exp]}")
        self.chk("host_frame")
        if self.host_ack:
            yield from self.g_rd()

    def report(self, need=()):
        for k in need:
            if self.nchk.get(k, 0) == 0:
                self.fail(f"vacuous: checker '{k}' never ran")
        if self.missing:
            self.fail(f"PORT-CONTRACT: no HDL port found for {self.missing} (set C9_PORTMAP)")
        self.dut._log.info(f"checks {self.nchk}; loads {self.loads_seen}; host reads {len(self.reads)}; "
                           f"bus lag {self.bus_lag}; release latency {self.lat_hist}; seed {SEED}")
        if self.place_n:
            self.dut._log.info(f"placed writes/rd {self.place_n}, off-target {self.place_miss} (TB aim; bins record actual)")
        self.cov.dump(sys._getframe(1).f_code.co_name, SEED)
        for e in self.err:
            self.dut._log.error(e)
        assert self.nerr == 0, f"{self.nerr} failures (first: {self.err[:1]})"


async def mk(dut, host=True):
    tb = TB(dut)
    await tb.start()
    tb.host_auto = host
    return tb


async def cfg_base(tb, word):
    """Write `word` now; return the even slot where it latches (not waited for)."""
    tb.tasks.append(tb.g_cfg_write(word))
    await tb.clks(90)
    r = tb.ref
    return r.slot + 1 if r.slot % 2 else r.slot + 2


async def set_cfg(tb, word):
    """Write `word` in the current slot so it latches at the next even slot; return that slot."""
    r = tb.ref
    tgt = r.slot + 1 if r.slot % 2 == 1 else r.slot + 2
    tb.tasks.append(tb.g_cfg_write(word))
    await tb.to_slot(tgt, 2)
    return tgt


def gold_cmp(tb, gframes, slot_ofs, ctr_ofs, check_inv=True):
    n = 0
    by = {f["slot"]: f for f in tb.ref.frames}
    for g in gframes:
        f = by.get(g["slot"] + slot_ofs)
        if f is None:
            tb.fail(f"golden slot {g['slot']}: no frame"); continue
        gt = gh.h16(g["tag_word"])
        mask = 0xFF00 if check_inv else 0xFE00
        exp = (gt & mask) | ((gt + ctr_ofs) & 0xFF if True else 0)
        got = f["tag"] & (mask | 0xFF)
        if (f["acc1"], f["acc2"]) != (g["acc1"], g["acc2"]) or got != (exp & (mask | 0xFF)):
            tb.fail(f"golden {g['slot']}: acc {f['acc1']},{f['acc2']} tag {got:04x} != {g['acc1']},{g['acc2']} {exp:04x}")
        n += 1
    # the host frames were already compared to Ref A word-by-word; make sure they cover these slots
    read_slots = {x["ref"]["slot"] for x in tb.reads}
    for g in gframes:
        if g["slot"] + slot_ofs not in read_slots:
            tb.fail(f"golden slot {g['slot']}: never read by the host")
    tb.chk("golden") if n else tb.fail("golden compare empty")
    return n


# ====================================================================== tests
@cocotb.test()
async def s01_reset_idle(dut):
    """S-01 / RST-02, BUS-01/05, CFG-04, CL-17: reset values, hold reset tag 0x0100, status 0x0800."""
    tb = await mk(dut, host=False)
    await tb.clks(10)
    in_rst = []
    for a in range(8):
        tb.set_ui(0x07, a)
        await tb.clks(5)
        in_rst.append(tb.last.get("bus"))
    tb.dut._log.info(f"bus while rst_n low (SPEC silent, logged only): {in_rst}")
    k0 = dict(tb.last)
    tb.rst_n = 1
    await tb.until(lambda: tb.ref.started, 60, "slot 0 start")
    for a, exp in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0x0100), (5, 0x0800), (6, 0), (7, 0)):
        tb.set_ui(0x07, a)
        await tb.clks(5)
        if tb.last.get("bus") != exp:
            tb.fail(f"reset addr {a}: {tb.last.get('bus')} != {exp:04x}")
        tb.chk("reset_word")
    k = k0
    for name, exp in (("rst_analog", 1), ("order", 1), ("boost", 0), ("trim", 4), ("short", 0),
                      ("bit_valid", 0), ("y_force", 0)):
        if k.get(name) != exp:
            tb.fail(f"in reset {name}={k.get(name)} != {exp}")
    tb.report(need=("x", "reset_word"))


@cocotb.test()
async def s02_reset_pair_golden(dut):
    """S-02: default config pair after rst_n == golden rst_default (frame_ctr 0/1, invalid 1)."""
    tb = await mk(dut)
    g = gh.load_golden()
    v = [x for x in g["vectors"] if x["kind"] == "reset"][0]
    for f in v["frames"]:
        tb.yb[f["slot"]] = gh.ybits(f["ybits"], f["n"])
    await tb.reset()
    await tb.to_slot(len(v["frames"]), 2)
    await tb.clks(60)
    gold_cmp(tb, v["frames"], 0, 0)
    tb.report(need=("bus", "host_frame", "rst_analog", "golden", "rst_lat"))


async def replay_vectors(tb, vecs, g):
    """Chain vectors: write the vector's config, run it in the next pair (frame_ctr offset = base slot)."""
    await tb.reset()
    r = tb.ref
    for v in vecs:
        cw, _ = gh.cfg_word(v["config"])
        tb.tasks.append(tb.g_cfg_write(cw))
        await tb.clks(90)
        base = r.slot + 1 if r.slot % 2 else r.slot + 2
        for f in v["frames"]:
            tb.yb[base + f["slot"]] = gh.ybits(f["ybits"], f["n"])
        nf = len(v["frames"]) + (len(v["frames"]) & 1)
        await tb.to_slot(base + nf, 0)
        await tb.clks(60)
        if fields(r.active) != fields(eff(cw)) and nf == 2:
            tb.fail(f"{v['id']}: config not active in its pair")
        gold_cmp(tb, v["frames"], base, base, check_inv=False)


def g_golden_writes(tb, writes, base, state):
    """Issue golden writes {(t, off): [words]} through the serial pins (cfg_clk = clk/4, 3.8a limit).
    The synchronised update is aimed mid-cycle `off` (3 clk after the start edge for off 0, i.e. on/after the
    latch edge).  Writes closer than one serial word (72 clk) cannot exist on silicon: the earlier one is
    dropped and the sequence is marked degraded (Ref A still checks it; golden compare is skipped)."""
    r = tb.ref
    planned = {}
    while True:
        if r.started and r.cnt == 0 and r.c == 0:
            e0, s = tb.edges, r.slot
            for t in (s, s + 1):
                if t == s:
                    st, dv = e0, r.div
                else:
                    st = e0 + (r.N + 2) * r.div
                    dv = r.div if (t % 2) else DIV.get(fields(eff(r.shadow))["fs_div"], 24)
                for (wt, off), wl in writes.items():
                    if wt + base == t and (wt, off) not in planned:
                        planned[(wt, off)] = [st + off * dv + (dv // 2 if off else 3), wl[-1], False]
            ks = sorted(planned, key=lambda k: planned[k][0])
            for a, b in zip(ks, ks[1:]):
                if planned[b][0] - planned[a][0] < 72 and not planned[a][2] and planned[a][1] is not None:
                    planned[a][1] = None
                    state["degraded"] = state.get("degraded", 0) + 1
        for p in planned.values():
            if not p[2] and p[1] is not None and tb.edges >= p[0] - 70:
                tb.tasks.append(tb.g_cfg_write(p[1]))
                p[2] = True
        yield


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def d_dec01_golden_vectors(dut):
    """D-DEC-01/02/06, Y-01, FRM-01: golden mode/offset/boosttrim vectors (quick: N 64/256; C9_FULL: all)."""
    tb = await mk(dut)
    g = gh.load_golden()
    vecs = [v for v in g["vectors"] if v["kind"] in ("mode", "offset", "boosttrim")
            and (FULL or v["config"]["N"] <= 64 or v["kind"] == "boosttrim")]
    if not FULL:
        vecs = vecs[:40]
    sh = os.environ.get("C9_VSHARD")              # "i/n": every n-th vector from i (parallel FULL runs)
    if sh:
        i, n = (int(x) for x in sh.split("/"))
        vecs = vecs[i::n]
    tb.dut._log.info(f"vectors in this run: {len(vecs)} (shard {sh})")
    await replay_vectors(tb, vecs, g)
    tb.dut._log.info(f"vectors replayed: {len(vecs)}")
    tb.report(need=("golden", "host_frame", "bus"))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def d_dec03_streams(dut):
    """D-DEC-03/04: N 4096 width and sign-extension streams (acc2 hi word 0x007F / 0xFF80)."""
    tb = await mk(dut)
    g = gh.load_golden()
    await replay_vectors(tb, g["streams"], g)
    tb.report(need=("golden", "host_frame"))


@cocotb.test()
async def a_seq01_trace_ctl(dut):
    """A-SEQ-01/02/04, SEQ-01..04, CFG-05: golden control trace, per fs cycle, from the DUT ports."""
    tb = await mk(dut)
    g = gh.load_golden()
    tr = g["traces"][0]
    await tb.reset()
    cw, _ = gh.cfg_word(tr["config0"])
    base = await cfg_base(tb, cw)
    writes, _ = gh.seq_inputs(tr)
    for f in tr["frames"]:
        tb.yb[base + f["slot"]] = gh.ybits(f["ybits"], f["n"])
    rows = tr["trace"]["rows"]
    got = []
    fl = tr["trace"]["fields"]
    r = tb.ref
    prev = None
    nsl = len(rows) // 66
    stt = {}
    tb.tasks.append(g_golden_writes(tb, writes, base, stt))
    while r.slot < base + nsl:
        await tb.tick.wait()
        key = (r.slot, r.c)
        if key != prev and r.cnt == 1 and r.slot >= base:
            prev = key
            o = tb.last
            row = []
            for name in fl:
                if name == "raw_pin":
                    v = (o.get("dac_y") or 0) & (o.get("bit_valid") or 0) if "dac_y" in o else r.ctl()["raw_pin"]
                elif name in o:
                    v = o[name]
                else:
                    v = r.ctl()[name]            # not exposed: Ref A (logged below)
                row.append(str(v))
            got.append("".join(row))
    bad = [(i, a, b) for i, (a, b) in enumerate(zip(got, rows)) if a != b]
    for i, a, b in bad[:10]:
        tb.fail(f"trace row {i} (slot {i // 66} c {i % 66}): dut {a} golden {b} fields {fl}")
    if len(got) < len(rows):
        tb.fail(f"trace rows {len(got)} < {len(rows)}")
    tb.chk("trace") if got else None
    tb.dut._log.info(f"trace rows compared {min(len(got), len(rows))}; not exposed (Ref A used): "
                     f"{[f for f in fl if f not in tb.last and f != 'raw_pin']}")
    tb.report(need=("trace",))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def d_cfg05_sequences(dut):
    """D-CFG-05, FRM-02..06, CL-12..16, CL-24: golden sequences through the serial pins and the host."""
    tb = await mk(dut, host=False)
    g = gh.load_golden()
    seqs = g["sequences"] if FULL else [s for s in g["sequences"] if s["id"] != "seq_wrap"]
    for s in seqs:
        await tb.reset()
        cw, _ = gh.cfg_word(s["config0"])
        base = 0 if eff(cw) == eff(RESET_CFG) else await cfg_base(tb, cw)
        writes, rd_plan = gh.seq_inputs(s)
        for f in s["frames"]:
            tb.yb[base + f["slot"]] = gh.ybits(f["ybits"], f["n"])
        r = tb.ref
        hold_st = {}
        stt = {}
        wg = g_golden_writes(tb, writes, base, stt)
        tb.tasks.append(wg)
        tb.reads = []
        while r.slot < base + len(s["slots"]) + 1:
            await tb.tick.wait()
            if "load" in r.events:
                t = r.frames[-1]["slot"] - base
                hold_st[t] = r.status()
                rel = rd_plan.get(t)
                tb.host_ack = rel == "after" or t < 0
                tb.tasks.append(tb._host_read(r.frames[-1]))
                nrel = rd_plan.get(t + 1)
                if nrel in ("before", "on"):             # rd pin so Ref A's synchronised rise is load-4 / load
                    nload = tb.edges + (r.N + 2) * r.div
                    det = nload - (4 if nrel == "before" else 0)

                    def g_pin(det=det):
                        while tb.edges < det - 3:
                            yield
                        yield from tb.g_rd(width=3)
                    tb.tasks.append(g_pin())
        tb.tasks.remove(wg) if wg in tb.tasks else None
        tb.host_ack = True
        if stt.get("degraded"):
            tb.dut._log.warning(f"{s['id']}: {stt['degraded']} writes closer than one serial word: dropped; "
                                f"golden compare skipped, Ref A compare kept")
            continue
        gold_cmp(tb, [f for f in s["frames"] if f["slot"] not in s.get("dropped", [])], base, base)
        for h in s.get("hold", []):
            if h.get("status_full") and h["slot"] in hold_st and h.get("rd_rel") in ("after", None):
                if hold_st[h["slot"]] & 0xDFFF & ~0xFF != gh.h16(h["status_full"]) & 0xDFFF & ~0xFF:
                    tb.fail(f"{s['id']} hold {h['slot']}: ref status {hold_st[h['slot']]:04x} vs golden {h['status_full']}")
                tb.chk("hold")
    tb.report(need=("golden", "hold", "host_frame"))


@cocotb.test()
async def d_cfg02_shift(dut):
    """D-CFG-01/02, CL-18: golden cfg_shift cases via the serial pins; the loaded word is observed after the latch."""
    tb = await mk(dut)
    g = gh.load_golden()
    await tb.reset()
    await set_cfg(tb, 0x0000)                     # N 64, fs/12: fast slots
    for case in g["cfg_shift"]:
        if case["id"] == "rst_clears" and not FULL:
            continue
        for op in case["ops"]:
            if op.startswith("s:"):
                bits = op[2:]
                def gen(bits=bits):
                    for b in bits:
                        tb.set_ui(0x30, int(b) << 5)
                        yield; yield
                        tb.set_ui(0x10, 0x10)
                        yield; yield
                        tb.set_ui(0x10, 0)
                    yield; yield
                tb.tasks.append(gen())
                await tb.clks(len(bits) * 4 + 4)
            elif op == "ld":
                def gl():
                    tb.set_ui(0x40, 0x40)
                    for _ in range(4):
                        yield
                    tb.set_ui(0x40, 0)
                tb.tasks.append(gl())
                await tb.clks(10)
            elif op == "rst":
                await tb.reset()
        exp = int(case["expect"][-1], 16)
        if eff(tb.ref.shadow) != eff(exp):
            tb.fail(f"ref shadow {tb.ref.shadow:04x} != golden {exp:04x} ({case['id']})")
        nxt = tb.ref.slot + (1 if tb.ref.slot % 2 else 2)
        await tb.to_slot(nxt, 2)
        await tb.clks(4)
        f = fields(eff(exp))
        o = tb.last
        for name in ("order", "short", "boost", "trim"):
            if o.get(name) != f[name]:
                tb.fail(f"{case['id']}: {name} {o.get(name)} != {f[name]}")
        tb.chk("cfg_shift")
        await set_cfg(tb, 0x0000)
    tb.report(need=("cfg_shift",))


@cocotb.test()
async def a_cfg01_edge_sweep(dut):
    """A-CFG-01, CL-14: cfg_ld pin edge at clk offsets around the even-slot latch edge.  Ref A latches iff the
    synchronised update precedes the edge; a DUT/ref disagreement shows on the control ports (clk-exact)."""
    tb = await mk(dut)
    await tb.reset()
    await set_cfg(tb, 0x0000)
    r = tb.ref
    for k, ofs in enumerate(range(-6, 7)):
        word = 0x0000 | ((k & 1) << 4) | (1 << 3)     # alternate short; boost 1
        if eff(word) == r.active:
            word ^= 0x0001
        # bits first, ld held back
        tb.tasks.append(tb.g_cfg_write(word, ld=False))
        await tb.clks(80)
        while not (r.slot % 2 == 1 and r.c == r.N + 1):
            await tb.tick.wait()
        # remaining clk to the latch edge from the current pre-state
        to_edge = r.div - r.cnt
        await tb.clks(max(to_edge + ofs - 1, 0))
        def gl():
            tb.set_ui(0x40, 0x40)
            for _ in range(4):
                yield
            tb.set_ui(0x40, 0)
        tb.tasks.append(gl())
        await tb.to_slot(r.slot + 2, 3)
        tb.chk("edge_sweep")
    tb.report(need=("edge_sweep", "short"))


@cocotb.test()
async def a_frm02_rd_race(dut):
    """A-FRM-02/03/05, CL-12/13, FRM-04/05: rd pin edge at clk offsets -8..+8 around the load; host off."""
    tb = await mk(dut, host=False)
    await tb.reset()
    await set_cfg(tb, 0x0000)
    r = tb.ref
    for ofs in range(-8, 9):
        while not (r.c == r.N + 1):
            await tb.tick.wait()
        await tb.clks(max(r.div - r.cnt + ofs - 1, 0))
        tb.tasks.append(tb.g_rd(width=2 if ofs % 3 == 0 else 3))
        await tb.clks(40)
        tb.chk("rd_race")
    # rd held high across 3 loads: one edge, one clear only (level-sensitive mutant)
    tb.set_ui(0x08, 0x08)
    await tb.to_slot(r.slot + 3, 2)
    tb.set_ui(0x08, 0)
    await tb.clks(10)
    if not r.frame_ready or not r.overrun:
        tb.fail("ref: rd held high should leave frame_ready and overrun set")
    tb.report(need=("rd_race", "bus"))


@cocotb.test()
async def d_frm04_overrun(dut):
    """D-FRM-04, A-FRM-06: unread frames for 3 slots, then a read+rd; overrun across frame_ctr wrap (FULL)."""
    tb = await mk(dut, host=False)
    await tb.reset()
    await set_cfg(tb, 0x0000)
    r = tb.ref
    await tb.to_slot(r.slot + 3, 2)
    tb.set_ui(0x07, 5)
    await tb.clks(5)
    st = tb.last.get("bus")
    if st is None or not (st >> 15) & 1 or not (st >> 14) & 1:
        tb.fail(f"status after 3 unread loads {st}")
    tb.tasks.append(tb._host_read(r.frames[-1]))
    await tb.clks(60)
    tb.set_ui(0x07, 5)
    await tb.clks(5)
    st = tb.last.get("bus")
    if st is None or (st >> 14) & 3:
        tb.fail(f"status after rd {st}")
    tb.chk("overrun")
    if FULL:
        await tb.to_slot(258, 2)
    tb.report(need=("overrun", "host_frame"))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def d_fs01_div_codes(dut):
    """D-FS-01/02, CL-15, CL-16, BUS-04: every fs_div code 0..7 (5-7 = /24), changes with no runt period."""
    tb = await mk(dut)
    await tb.reset()
    for code in (0, 4, 0, 1, 5, 2, 6, 3, 7, 0):
        await set_cfg(tb, (code << 7))
        await tb.to_slot(tb.ref.slot + 1, 2)
        tb.chk("fsdiv")
    tb.report(need=("fsdiv", "fs_clk"))


@cocotb.test()
async def a_rst01_async_mid(dut):
    """A-RST-01..04, RST-01/03, CL-19: rst_n mid-slot at random points (async assert), release determinism."""
    tb = await mk(dut)
    rng = random.Random(SEED)
    await tb.reset()
    await set_cfg(tb, 0x0000)
    for i in range(6):
        await tb.clks(rng.randrange(1, 700))
        await Timer(3, unit="ns")                # mid clk-low phase: no clk edge until the next rise
        dut.rst_n.value = 0
        tb.a_rst_n = 0                           # the pin is low at the next rising edge (async assert)
        await Timer(2, unit="ns")
        if lv(tb.ports["rst_analog"]) != 1 if "rst_analog" in tb.ports else False:
            tb.fail("rst_analog not asserted asynchronously")
        tb.chk("async_rst")
        tb.rst_n = 0
        tb.tasks.append(tb.g_cfg_write(0x1234))   # writes during rst_n have no effect (RST-04)
        await tb.clks(30)
        await tb.reset(n=1)
        if tb.ref.active != eff(RESET_CFG):
            tb.fail("ref active not reset")
        await tb.clks(rng.randrange(50, 400))
    tb.report(need=("async_rst", "rst_lat"))


@cocotb.test()
async def d_bus03_debug(dut):
    """D-BUS-03, A-BUS-04, Y-04: debug bus vs Ref A per clk at every chop mode; dbg toggled every 5 clk."""
    tb = await mk(dut)
    await tb.reset()
    for word in (0x0060, 0x0040, 0x0020, 0x0000):     # ota+sys, sys, ota, off at N 64 /12
        await set_cfg(tb, word)
        tb.host_auto = False
        tb.set_ui(0x80, 0x80)
        await tb.to_slot(tb.ref.slot + 2, 0)
        for _ in range(40):
            tb.set_ui(0x80, tb.ui ^ 0x80)
            await tb.clks(5)
        tb.set_ui(0x80, 0)
        tb.host_auto = True
        tb.chk("debug")
    tb.report(need=("debug", "bus"))


@cocotb.test()
async def d_inv02_each_field(dut):
    """D-INV-02/03/04, INV-03, CFG-06: change one latched field at a time; equal rewrite is not a change."""
    tb = await mk(dut)
    await tb.reset()
    base = 0x0000
    await set_cfg(tb, base)
    for bit in (12, 10, 7, 6, 5, 4, 3, 0, None):
        w = base ^ (1 << bit) if bit is not None else base
        await set_cfg(tb, w)
        await tb.to_slot(tb.ref.slot + 2, 2)
        await set_cfg(tb, base)
        await tb.to_slot(tb.ref.slot + 2, 2)
        tb.chk("inv_field")
    await tb.clks(60)
    inv = [(f["slot"], (f["tag"] >> 8) & 1) for f in tb.ref.frames]
    tb.dut._log.info(f"invalid per slot {inv}")
    tb.report(need=("inv_field", "host_frame"))


@cocotb.test()
async def d_bus02_latency(dut):
    """D-BUS-02, CL-21: addr changes at every clk phase; the word must be right <= 3 clk after the change."""
    tb = await mk(dut, host=False)
    await tb.reset()
    await set_cfg(tb, 0x0000)
    worst = 0
    for i in range(48):
        a = (i * 5) % 8
        tb.ui = (tb.ui & ~7) | a                    # no settle mask: measure
        exp = tb.ref.word(a)
        for k in range(1, 8):
            await tb.clks(1)
            if tb.last.get("bus") == tb.ref.word(a):
                worst = max(worst, k - 1)      # first tick only applies the pin (test-coroutine write)
                break
        else:
            tb.fail(f"addr {a}: word never appeared")
        await tb.clks(i % 4)
    if worst > 3:
        tb.fail(f"bus latency {worst} clk > 3 (CL-21)")
    tb.dut._log.info(f"worst bus latency {worst} clk")
    tb.chk("lat")
    tb.report(need=("lat",))


# ====================================================================== WO-42: placement helpers
K_SYNC = 3      # a pin level set by a driver in loop iteration i is acted on by Ref A at edge i + 3 (2-FF + edge)


def predict(tb, pred, lo, hi):
    """Absolute edge E (now+lo .. now+hi) whose Ref A post-state satisfies pred; a Ref A copy is stepped with
    the current pins (no ld).  Position only depends on the active config, so pending shifts/reads don't matter."""
    fr = tb.ref.frames
    tb.ref.frames = []
    rc = copy.deepcopy(tb.ref)
    tb.ref.frames = fr
    ui = tb.ui & ~0x48
    for k in range(1, hi + 1):
        rc.step(1, ui, 0)
        if k >= lo and pred(rc):
            return tb.edges + k
    return None


def g_place(tb, words, E):
    """Shift words[0], then len(words) cfg_ld pulses (2 clk high, 2 low: >= 4 clk apart) so the last synchronised
    shadow update is at edge E.  Later lds load the cleared shift register (0, CL-18)."""
    first = E - 4 * (len(words) - 1)
    start = first - K_SYNC - 72
    while tb.edges < start:
        yield
    yield from tb.g_cfg_write(words[0], ld=False)
    while tb.edges < first - K_SYNC:
        yield
    for _ in words:
        tb.set_ui(0x40, 0x40); yield; yield
        tb.set_ui(0x40, 0); yield; yield
    while tb.edges < E:
        yield
    tb.place_n += 1
    if "ld" not in tb.ref.events:
        tb.place_miss += 1


def g_rd_at(tb, P, width=2):
    """rd pin so its synchronised rise acts at edge P + 1 (pre-state = post-state of P)."""
    while tb.edges < P - 2:
        yield
    tb.set_ui(0x08, 0x08)
    for _ in range(width):
        yield
    tb.set_ui(0x08, 0)
    yield
    tb.place_n += 1


def p_wphase(ph):
    """Post-state predicate for a write phase (fcov.PHASES) at any config."""
    if ph.startswith("e"):
        d = int(ph[1:])
        if d < 0:
            return lambda rc: rc.slot % 2 == 1 and rc.c == rc.N + 1 and rc.cnt == rc.div + d
        return lambda rc: rc.slot % 2 == 0 and rc.c == 0 and rc.cnt == d
    par = 0 if ph.startswith("even") else 1
    pos = ph.split("_")[1]
    cnt = {"c0": 6}.get(pos, 5)
    cf = {"c0": lambda rc: 0, "c1": lambda rc: 1, "c2": lambda rc: 2, "mid": lambda rc: rc.N // 2,
          "N1": lambda rc: rc.N + 1}[pos]
    if ph == "odd_N1":
        cnt = 2
    return lambda rc: rc.slot % 2 == par and rc.c == cf(rc) and rc.cnt == cnt


def p_load(d):
    """Post-state P such that the next edge's pre-state is d clk from the load edge (d 0 = the load edge)."""
    if d <= 0:
        return lambda rc: rc.c == rc.N + 1 and rc.cnt - (rc.div - 1) == d
    return lambda rc: rc.c == 0 and rc.slot > 0 and rc.cnt + 1 == d


async def settle_cfg(tb, word):
    for _ in range(3):
        await set_cfg(tb, word)
        if tb.ref.active == eff(word):
            return
    tb.fail(f"could not settle config {word:04x}")


R01_SLOTS = int(os.environ.get("C9_R01_SLOTS", "64"))


@cocotb.test(timeout_time=float(os.environ.get("C9_R01_TO", "20")), timeout_unit="sec")
async def r01_random(dut):
    """R-01 (plan 4.7): >= C9_R01_SLOTS slots; N 64 (70 %) / 256; writes aimed at the latch edge +-3 (40 %), the
    last cycle of an odd slot (20 %), anywhere (40 %); equal and multi writes; host acks randomly; extra rd edges
    aimed at load +-4.  Ref A compares every clk.  SOAK-01 = this test with large C9_R01_SLOTS on Verilator."""
    tb = await mk(dut)
    rng = random.Random(SEED)
    tb.dut._log.info(f"R-01 seed {SEED} slots {R01_SLOTS}")
    await tb.reset()
    await set_cfg(tb, 0x0000)
    r = tb.ref
    l0 = tb.loads_seen
    while tb.loads_seen - l0 < R01_SLOTS:
        n = 0 if rng.random() < 0.7 else 1
        fd = rng.choice([0, 0, 0, 0, 1, 2, 5, 7])
        w = (rng.getrandbits(1) << 12) | (n << 10) | (fd << 7) | rng.getrandbits(7)
        if rng.random() < 0.1:
            w |= rng.getrandbits(3) << 13                # reserved bits: not a change (CL-16)
        if rng.random() < 0.15:
            w = r.active
        words = [w, 0] if rng.random() < 0.15 else [w]
        p = rng.random()
        if p < 0.4:
            pred = p_wphase(f"e{rng.randint(-3, 3):+d}")
        elif p < 0.6:
            k = rng.randrange(192)
            pred = (lambda k: lambda rc: rc.slot % 2 == 1 and rc.c == rc.N + 1 and rc.cnt == k % rc.div)(k)
        else:
            par, cc, k = rng.getrandbits(1), rng.randrange(260), rng.randrange(192)
            pred = (lambda par, cc, k: lambda rc: rc.slot % 2 == par and rc.c == cc % (rc.N + 2)
                    and rc.cnt == k % rc.div)(par, cc, k)
        E = predict(tb, pred, 80 + 4 * len(words), 3 * 258 * 48)
        if E is None:
            await tb.clks(100)
            continue
        tb.tasks.append(g_place(tb, words, E))
        tb.host_ack = rng.random() > 0.2
        if rng.random() < 0.3:
            P = predict(tb, p_load(rng.randint(-4, 4)), 10, 3 * 258 * 48)
            if P is not None:
                tb.tasks.append(g_rd_at(tb, P, width=rng.choice([1, 2, 3, 4])))
        await tb.until(lambda: tb.edges >= E + 1, 4 * 258 * 192, "placed write")
        await tb.clks(rng.randrange(1, 300))
        if rng.random() < 0.03:
            await tb.reset(n=rng.randrange(1, 20))
            await set_cfg(tb, 0x0000)
    tb.host_ack = True
    await tb.clks(2000)
    tb.report(need=("bus", "host_frame", "rst_analog"))


# ====================================================================== WO-42 directed coverage tests (7.1 bins)
@cocotb.test(timeout_time=20, timeout_unit="sec")
async def c01_mode_sweep(dut):
    """CV-MODE (64), CV-BT, CV-DATA: every order x N x chop x short at fs/12, boost/trim cycled, comparator
    patterns all +1 / all -1 / (+--+) / random; host reads and checks every frame."""
    tb = await mk(dut)
    await tb.reset()
    r = tb.ref
    await set_cfg(tb, 0x0000)
    BT = [(0, 0), (0, 4), (0, 7), (1, 0), (1, 4), (1, 7)]
    k = 0
    for n in range(4):
        for o in (0, 1):
            for (sy, ot) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                for s in (0, 1):
                    b, t = BT[k % 6]
                    w = (o << 12) | (n << 10) | (sy << 6) | (ot << 5) | (s << 4) | (b << 3) | t
                    N = N_OF[n]
                    nxt = r.slot + 2 if r.slot % 2 == 0 else r.slot + 1
                    pat = k % 4
                    for sl in (nxt, nxt + 1):
                        if pat == 0:
                            tb.yb[sl] = [1] * N
                        elif pat == 1:
                            tb.yb[sl] = [1] + [0] * (N - 1)
                        elif pat == 2:
                            tb.yb[sl] = [(1, 0, 0, 1)[i % 4] for i in range(N)]
                    await set_cfg(tb, w)
                    k += 1
    await tb.to_slot(r.slot + 2, 2)
    await tb.clks(60)
    tb.report(need=("host_frame", "bus"))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def c02_fs_sweep(dut):
    """CV-FS: fs_div 0..7 x N 64 / 4096 and transitions 0>4, 4>0, 1>0, any>reserved."""
    tb = await mk(dut)
    await tb.reset()
    for n, codes in ((0, (0, 4, 0, 1, 0, 5, 2, 6, 3, 7)), (3, (0, 1, 2, 3, 4, 5, 6, 7))):
        for code in codes:
            await set_cfg(tb, (n << 10) | (code << 7))
            tb.chk("fsdiv")
    tb.report(need=("fsdiv", "fs_clk"))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def c03_write_phase(dut):
    """CV-WRITE-PHASE: every phase x {single, equal, multi, write-back}, each field changed (single writes cycle
    the 8 fields).  Writes are placed clk-exact through the pins; the collector records the actual phase."""
    from fcov import PHASES
    tb = await mk(dut)
    await tb.reset()
    r = tb.ref
    fbits = (12, 10, 7, 6, 5, 4, 3, 0)
    i = 0
    for kind in ("single", "equal", "multi", "writeback"):
        base = 0x0010 if kind == "multi" else 0x0000
        for ph in PHASES:
            if kind in ("multi", "writeback") and ph in ("e+0", "e+1", "e+2", "e+3"):
                continue
            await settle_cfg(tb, base)
            words = {"single": [base ^ (1 << fbits[i % 8])], "equal": [base], "multi": [0x0001],
                     "writeback": [0x0010]}[kind]
            if kind in ("multi", "writeback"):
                words = words + [0]
            i += kind == "single"
            E = predict(tb, p_wphase(ph), 80 + 4 * len(words), 6 * 66 * 12)
            if E is None:
                tb.fail(f"no target for {ph}")
                continue
            tb.tasks.append(g_place(tb, words, E))
            await tb.until(lambda: tb.edges >= E + 1, 7 * 66 * 12, f"place {ph} {kind}")
            tb.chk("wphase")
    tb.report(need=("wphase",))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def c04_rd_bins(dut):
    """CV-RD / CV-OVR: rd rise at load -8..+8, state {status read} x {frame_ready, overrun}, widths 1..4 and
    held, 1/2/3/>=10 unread loads.  Host off; Ref A checks frame_ready/overrun through the bus every clk."""
    tb = await mk(dut, host=False)
    await tb.reset()
    r = tb.ref
    await set_cfg(tb, 0x0000)
    for d in range(-8, 9):
        P = predict(tb, p_load(d), 10, 3 * 66 * 12)
        tb.tasks.append(g_rd_at(tb, P, width=1 + (d & 3)))
        await tb.until(lambda: tb.edges >= P + 10, 4 * 66 * 12, "rd ofs")
        await tb.clks(30)
    for sr in (0, 1):
        for st in ("fr0", "fr1_ov0", "fr1_ov1"):
            await tb.to_slot(r.slot + 1, 3)                  # just after a load
            if st == "fr1_ov1":
                await tb.to_slot(r.slot + 1, 3)              # second unread load
            if st != "fr1_ov1":
                tb.tasks.append(tb.g_rd(width=2))            # clear: frame_ready 0, overrun 0
                await tb.clks(12)
            if st == "fr1_ov0":
                await tb.to_slot(r.slot + 1, 3)
            if sr:
                tb.set_ui(0x87, 5)
                await tb.clks(8)
                tb.set_ui(0x87, 0)
            await tb.clks(4)
            tb.tasks.append(tb.g_rd(width=2))
            await tb.clks(20)
            tb.chk("rd_state")
    tb.set_ui(0x08, 0x08)                                    # held across a load
    await tb.to_slot(r.slot + 2, 2)
    tb.set_ui(0x08, 0)
    await tb.clks(10)
    await tb.to_slot(r.slot + 11, 2)                         # >= 10 unread loads
    tb.report(need=("rd_state", "bus"))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def c05_ctr_wrap(dut):
    """CV-CTR / CV-OVR: frame_ctr 254, 255 -> 0 with overrun set across the wrap, a config change latched at
    frame_ctr 0 (slot 256).  Host off until after the wrap."""
    tb = await mk(dut, host=False)
    await tb.reset()
    r = tb.ref
    await set_cfg(tb, 0x0000)
    await tb.to_slot(255, 2)
    await set_cfg(tb, 0x0010)                     # written in slot 255, latches at slot 256 (frame_ctr 0)
    await tb.to_slot(258, 2)
    tb.tasks.append(tb._host_read(r.frames[-1]))
    await tb.clks(80)
    tb.chk("wrap")
    tb.report(need=("wrap", "host_frame"))


@cocotb.test(timeout_time=20, timeout_unit="sec")
async def c06_rst_pos(dut):
    """CV-RST: rst_n asserted at c 0, c 1, n 0, mid, n N-1, load -1/0/+1, before slot 0, during a cfg shift,
    with rd high, with dbg 1, and with a write pending.  Reset config (N 4096, fs/24): no rewrite needed."""
    tb = await mk(dut)
    await tb.reset()
    r = tb.ref
    cases = [("c0", lambda rc: rc.c == 0 and rc.cnt == 5), ("c1", lambda rc: rc.c == 1 and rc.cnt == 3),
             ("n0", lambda rc: rc.c == 2 and rc.cnt == 3), ("mid", lambda rc: rc.c == 100),
             ("nNm1", lambda rc: rc.c == rc.N + 1 and rc.cnt == 5),
             ("load-1", p_load(-1)), ("load0", p_load(0)), ("load+1", p_load(1))]
    for name, pred in cases:
        P = predict(tb, pred, 5, 2 * 4098 * 24 + 100)
        if P is None:
            tb.fail(f"no target {name}")
            continue

        def g(P=P):
            while tb.edges < P:
                yield
            tb.rst_n = 0
        tb.tasks.append(g())
        await tb.until(lambda: tb.rst_n == 0, 2 * 4098 * 24 + 200, name)
        await tb.clks(4)
        await tb.reset(n=3)
        tb.chk("rst_pos")
    # before slot 0 (release window), during a shift, rd high, dbg 1, pending write
    tb.rst_n = 0
    await tb.clks(3)
    tb.rst_n = 1
    await tb.clks(8)
    await tb.reset(n=3)
    for setup in ("shift", "rd", "dbg", "pending"):
        if setup == "shift":
            tb.tasks.append(tb.g_cfg_write(0x0001, ld=False))
            await tb.clks(30)
        elif setup == "rd":
            tb.set_ui(0x08, 0x08)
            await tb.clks(5)
        elif setup == "dbg":
            tb.set_ui(0x80, 0x80)
            await tb.clks(8)
        else:
            tb.tasks.append(tb.g_cfg_write(0x0001))
            await tb.clks(100)
        tb.rst_n = 0
        await tb.clks(4)
        await tb.reset(n=3)
        tb.chk("rst_pos")
    await tb.clks(200)
    tb.report(need=("rst_pos", "rst_lat"))


@cocotb.test()
async def c07_addr(dut):
    """CV-ADDR: every addr x dbg held stable and as a 1-clk glitch; bus == Ref A outside the 3-clk settle."""
    tb = await mk(dut, host=False)
    await tb.reset()
    tb.set_ui(0x87, 7)                       # start away from 0 so a0_d0 also gets a glitch run
    await tb.clks(5)
    for v in [a | (d << 7) for d in (0, 1) for a in range(8)]:
        tb.set_ui(0x87, v)
        await tb.clks(1)
        tb.set_ui(0x87, v ^ 1)
        await tb.clks(5)
        tb.set_ui(0x87, v)
        await tb.clks(6)
        tb.chk("addr")
    tb.set_ui(0x87, 0)
    await tb.clks(10)
    tb.report(need=("addr", "bus"))
