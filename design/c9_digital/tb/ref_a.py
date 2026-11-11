"""Ref A: clk-level reference model of C9, written by verification from the SPEC only.

Sources: SPEC.md 3.6 (rules 7-12), 3.7, 3.7a (a)-(k), 3.8a (pins, debug, status, buffering, config,
rst_n, port contract CL-12..CL-26), DECISIONS D45-D48, D66, D67.  It does NOT import model/ and was not
derived from any RTL.  One call of step() = one rising clk edge; every register updates from pre-edge values.

Interpretation choices (where the SPEC leaves a free parameter; each is a bench knob, see README):
  * 2-FF synchronisers + edge detect on rd, cfg_clk, cfg_ld: a pin level first sampled at edge j is acted
    on at edge j+2 (CL-14 "2-3 clk after the pin edge").
  * addr and dbg: 2-FF sync, then the registered bus: word visible after edge j+2 (CL-21 "<= 3 clk").
  * fs divider: cnt 0..div-1, fs-cycle start edge = cnt wraps to 0 = bit clock rising (CL-23); bit clock
    high for cnt < div/2; comparator sampled on the edge where cnt becomes div/2 (bit clock falling, CL-23);
    the DAC flop (y) updates on the next start edge (D67: debug y = DAC flop).
  * The decision sampled in fs cycle c is y for cycle c+1 (n = c-1).  Decisions of c = 0, 1, N+1 are ignored
    (3.7a a: n = 0 forced to +1).
  * Release: the slot-0 start edge is aligned to the DUT by the bench (one free, bounded, determinism-checked
    latency, CL-19).  Ref A's own default is `rst_lat` edges after the first edge that samples rst_n = 1.
"""

DIV = {0: 12, 1: 24, 2: 48, 3: 96, 4: 192}
N_OF = (64, 256, 1024, 4096)
RESET_CFG = (1 << 12) | (3 << 10) | (1 << 7) | (1 << 6) | (1 << 5) | 0b100   # 0x1CE4 (3.8a table)
HOLD_RESET_TAG = 0x0100                                                     # CL-17
M32 = 0xFFFFFFFF

MUTANTS = ("incl", "y0pass", "swap_late", "latch_odd", "latch_all", "inv_first_only", "no_rst_inv",
           "rd_on_clears", "no_ovr", "hold_inv0", "sr_noclr", "fsdiv_raw", "pending_pre", "ctr_rst_on_change",
           "bt_not_in_set", "acc_noclr", "nminus1", "tagchop_parity", "trim_rst0")


def eff(word):
    """Effective config (CL-16): bits 12:0 only, fs_div 5-7 normalised to 1."""
    w = word & 0x1FFF
    fd = (w >> 7) & 7
    if fd > 4:
        fd = 1
    return (w & ~(7 << 7)) | (fd << 7)


def fields(w):
    return dict(order=(w >> 12) & 1, n_code=(w >> 10) & 3, fs_div=(w >> 7) & 7, sys_en=(w >> 6) & 1,
                ota_en=(w >> 5) & 1, short=(w >> 4) & 1, boost=(w >> 3) & 1, trim=w & 7)


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


class Sync:
    """2-FF synchroniser + rising-edge detect (s3 is the edge-detect history flop)."""
    __slots__ = ("s1", "s2", "s3")

    def __init__(self):
        self.s1 = self.s2 = self.s3 = 0

    def step(self, pin):
        rise = self.s2 and not self.s3
        lvl = self.s2
        self.s3, self.s2, self.s1 = self.s2, self.s1, pin
        return rise, lvl


class RefA:
    def __init__(self, mut=None, rst_lat=2, cfg0=None, rd_lag=0):
        self.rd_lag = rd_lag      # clk from the synchronised rd rise to the clear (CL-12 allows a later clear)
        assert mut is None or mut in MUTANTS, mut
        self.mut = mut
        self.rst_lat = rst_lat
        self.cfg0 = cfg0          # golden-agreement hook only: "config present at reset" (golden config0)
        self.edge = 0
        self.reset()

    # ------------------------------------------------------------------ reset (async assert)
    def reset(self):
        rc = RESET_CFG if self.mut != "trim_rst0" else (RESET_CFG & ~7)
        if self.cfg0 is not None:
            rc = self.cfg0
        self.shadow = rc
        self.active = eff(rc)
        self.active_raw = rc & 0x1FFF
        self.pre_latch_active = self.active
        self.sr = 0
        self.ss_clk, self.ss_dat, self.ss_ld, self.ss_rd = Sync(), Sync(), Sync(), Sync()
        self.a1 = self.a2 = 0              # addr / dbg sync flops
        self.d1 = self.d2 = 0
        self.bus = 0                       # registered 16-bit bus (uo:uio)
        self.started = False
        self.rel_cnt = -1                  # edges since rst_n sampled high
        self.div = DIV.get(fields(self.active)["fs_div"], 24)
        self.cnt = self.div - 1            # divider held; bit clock low
        self.slot = -1
        self.c = 0
        self.sys_swap = 0
        self.pair_inv = 1
        self.after_rst = True
        self.y = 0
        self.comp_q = 0
        self.acc1 = self.acc2 = 0
        self.hold = dict(acc1=0, acc2=0, tag=HOLD_RESET_TAG if self.mut != "hold_inv0" else 0,
                         boost=0, trim=0b100)
        self.frame_ready = 0
        self.overrun = 0
        self.ctr = 0                       # slot counter mod 256 (frame_ctr)
        self.events = []                   # per-edge event names (load, latch, rd_clear, rd_supp, ld)
        self.frames = []                   # every hold load, in order
        self.in_rst = True
        self.rd_pend = False

    # ------------------------------------------------------------------ derived combinational values
    @property
    def cfg(self):
        return fields(self.active)

    @property
    def N(self):
        return N_OF[self.cfg["n_code"]]

    def bitclk(self):
        return 1 if (self.started and self.cnt < self.div // 2) else 0

    def ctl(self):
        """Analog-side control levels (port contract, all active high) after the last edge."""
        if not self.started:
            f = self.cfg
            return dict(rst_analog=1, acc_clear=0, sys_swap=0, ota_chop_phase=0, y_force=0, bit_valid=0,
                        raw_pin=0, tag_chop=0, cfg_latch=0, short=f["short"], order=f["order"],
                        boost=f["boost"], trim=f["trim"], fs_clk=0, dac_y=self.y)
        c, N, f = self.c, self.N, self.cfg
        bv = 1 if 2 <= c <= N + 1 else 0
        ota = ((c - 2) & 1) if (c >= 2 and f["ota_en"]) else 0
        return dict(rst_analog=1 if c < 2 else 0, acc_clear=1 if c == 1 else 0, sys_swap=self.sys_swap,
                    ota_chop_phase=ota, y_force=1 if c == 2 else 0, bit_valid=bv, raw_pin=self.y & bv,
                    tag_chop=self.sys_swap, cfg_latch=1 if (c == 0 and self.slot % 2 == 0) else 0,
                    short=f["short"], order=f["order"], boost=f["boost"], trim=f["trim"],
                    fs_clk=self.bitclk(), dac_y=self.y)

    def status(self):
        act = self.pre_latch_active if (self.mut == "pending_pre" and "latch" in self.events) else self.active
        pend = 1 if eff(self.shadow) != act else 0
        h = self.hold
        return ((self.frame_ready << 15) | (self.overrun << 14) | (pend << 13) | (h["boost"] << 12)
                | (h["trim"] << 9) | (h["tag"] & 0xFF))

    def word(self, addr):
        h = self.hold
        a1, a2 = h["acc1"] & M32, h["acc2"] & M32
        return {0: a1 >> 16, 1: a1 & 0xFFFF, 2: a2 >> 16, 3: a2 & 0xFFFF, 4: h["tag"],
                5: self.status()}.get(addr, 0)

    def dbg_word(self):
        k = self.ctl()
        uo = (k["raw_pin"] | (k["bit_valid"] << 1) | (self.frame_ready << 2) | (k["fs_clk"] << 3)
              | (k["rst_analog"] << 4) | (k["sys_swap"] << 5) | (k["ota_chop_phase"] << 6)
              | (((self.hold["tag"] >> 8) & 1) << 7))
        return (uo << 8) | (self.status() & 0xFF)

    def sample_point(self):
        """Pre-edge position (slot, c, cnt) the next edge will act on."""
        return self.slot, self.c, self.cnt

    # ------------------------------------------------------------------ one clk edge
    def step(self, rst_n=1, ui=0, comp=0, force_ld=None, start_now=False):
        """ui = ui_in byte. comp = comparator level (1 = +1). force_ld = golden-agreement backdoor: act as if
        the synchronised cfg_ld edge fires at this edge with shift register = force_ld (same code path)."""
        self.edge += 1
        self.events = []
        if not rst_n:
            self.reset()
            return
        if self.in_rst:                    # synchronous release
            self.in_rst = False
            self.rel_cnt = 0
        else:
            self.rel_cnt += 1 if self.rel_cnt >= 0 else 0

        addr, rd, cclk, cdat, cld, dbg = ui & 7, (ui >> 3) & 1, (ui >> 4) & 1, (ui >> 5) & 1, (ui >> 6) & 1, (ui >> 7) & 1
        # ---- pre-edge snapshot for the registered bus
        bus_next = self.dbg_word() if self.d2 else self.word(self.a2)
        # ---- synchronisers
        clk_rise, _ = self.ss_clk.step(cclk)
        _, dat_lvl = self.ss_dat.step(cdat)
        ld_rise, _ = self.ss_ld.step(cld)
        rd_rise, _ = self.ss_rd.step(rd)
        self.a2, self.a1 = self.a1, addr
        self.d2, self.d1 = self.d1, dbg
        self.bus = bus_next

        pre_shadow = self.shadow
        pre_active = self.active
        pre_ready = self.frame_ready
        # ---- serial config
        if force_ld is not None:
            ld_rise, sr_val = True, force_ld & 0xFFFF
        else:
            sr_val = self.sr
        if clk_rise:
            self.sr = ((self.sr << 1) | dat_lvl) & 0xFFFF
        if ld_rise:
            self.shadow = sr_val
            if self.mut != "sr_noclr":
                self.sr = 0
            self.events.append("ld")

        # ---- fs divider / sequencer
        if not self.started:
            if start_now or (self.rst_lat is not None and self.rel_cnt >= self.rst_lat):
                self._start_edge(first=True, pre_shadow=pre_shadow)
            self._rd(rd_rise, load=False)
            return
        tick = self.cnt == self.div - 1
        if self.cnt == self.div // 2 - 1:
            self.comp_q = comp & 1                  # bit-clock falling edge: comparator sample (CL-23)
        if not tick:
            self.cnt += 1
            self._rd(rd_rise, load=False)
            return
        # ---- fs-cycle start edge: end of cycle (slot, c)
        c, N = self.c, self.N
        last = N + 1 if self.mut != "nminus1" else N
        if 2 <= c <= last:                          # accumulate y[n], exclusive S (3.7, 3.7a k)
            yv = 1 if self.y else -1
            if self.mut == "incl":
                self.acc1 += yv
                self.acc2 += self.acc1
            else:
                self.acc2 += self.acc1
                self.acc1 += yv
        if c == 1 and self.mut != "acc_noclr":      # acc_clear: clear on the edge releasing rst_analog
            self.acc1 = self.acc2 = 0
        load = c == N + 1
        if load:
            f = fields(pre_active)
            chop = self.sys_swap if self.mut != "tagchop_parity" else (self.slot & 1)
            tag = ((chop << 15) | (f["order"] << 14) | (f["n_code"] << 12) | (f["sys_en"] << 11)
                   | (f["ota_en"] << 10) | (f["short"] << 9) | (self.pair_inv << 8) | (self.ctr & 0xFF))
            if self.mut == "inv_first_only" and (self.slot & 1):
                tag &= ~0x100
            self.hold = dict(acc1=s32(self.acc1), acc2=s32(self.acc2), tag=tag, boost=f["boost"], trim=f["trim"])
            if pre_ready and self.mut != "no_ovr":
                self.overrun = 1
            self.frame_ready = 1
            self.frames.append(dict(slot=self.slot, edge=self.edge, **self.hold))
            self.events.append("load")
        # next cycle
        if c + 1 >= N + 2:
            self._start_edge(first=False, pre_shadow=pre_shadow)
        else:
            self.c = c + 1
            self.cnt = 0
            if self.c == 1 and self.mut == "swap_late":
                self.sys_swap = (self.slot & 1) & self.cfg["sys_en"]
            if self.c == 2:
                self.y = 1 if self.mut != "y0pass" else self.comp_q   # forced y[0] = +1 (3.7a a)
            else:
                self.y = self.comp_q
        self._rd(rd_rise, load=load)

    def _start_edge(self, first, pre_shadow):
        self.slot += 1
        self.c = 0
        self.ctr = (self.ctr + 1) & 0xFF if not first else 0
        self.started = True
        self.y = self.comp_q
        even = self.slot % 2 == 0
        do_latch = even
        if self.mut == "latch_odd":
            do_latch = not even
        if self.mut == "latch_all":
            do_latch = True
        if do_latch:
            new = eff(pre_shadow) if self.mut != "fsdiv_raw" else (pre_shadow & 0x1FFF)
            cmp_new, cmp_old = new, (self.active if self.mut != "fsdiv_raw" else self.active_raw)
            if self.mut == "bt_not_in_set":
                cmp_new, cmp_old = new & ~0xF, self.active & ~0xF
            changed = cmp_new != cmp_old
            self.pre_latch_active = self.active
            self.active = eff(pre_shadow)
            self.active_raw = pre_shadow & 0x1FFF
            if changed and self.mut == "ctr_rst_on_change":
                self.ctr = 0
            rst_inv = self.after_rst and self.mut != "no_rst_inv"
            self.pair_inv = 1 if (changed or rst_inv) else 0
            self.after_rst = False
            self.events.append("latch")
        self.div = DIV.get(self.cfg["fs_div"], 24)  # CL-15: new divider from c = 0 of the new pair
        self.cnt = 0
        if self.mut != "swap_late":
            self.sys_swap = (self.slot & 1) & self.cfg["sys_en"]

    def _rd(self, rd_rise, load):
        if self.rd_lag and (rd_rise or self.rd_pend):
            pend, self.rd_pend = self.rd_pend, False
            if load and self.mut != "rd_on_clears":
                self.events.append("rd_supp")      # a load at the rise or between rise and clear
                return
            if rd_rise and not pend:
                self.rd_pend = True
                return
            rd_rise = True
        if not rd_rise:
            return
        if load and self.mut != "rd_on_clears":     # CL-13: rd on the load clk is suppressed
            self.events.append("rd_supp")
            return
        self.frame_ready = 0
        self.overrun = 0
        self.events.append("rd_clear")

