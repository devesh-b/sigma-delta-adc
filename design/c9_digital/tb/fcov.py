"""C9 functional-coverage collector (C9_VERIF_PLAN 7.1), WO-42.  Written from the plan bins, not from the RTL.

Sampling: from the pins actually applied (tb.a_ui / tb.a_rst_n) and Ref A state.  Ref A is checked clk-exact
against the DUT by the always-on checkers, so a bin hit here is a stimulus the DUT really saw and passed.
pre(tb) runs before Ref A steps an edge (pre-state), post(tb) after it (post-state, events).
Dump: <C9_OUT>/fcov/<test>_s<seed>.json.  Merge:  python3 fcov.py merge <dir-or-json> ...   (prints hit/miss).

Reductions (recorded in C9_VERIF_PLAN 7.1): the 3-way write cross is split into phase x kind plus field;
the rd cross is split into offset and state; the CV-RST release-phase bins are dropped (D70: the divider
restarts at the synchronised release and the reset config is always fs_div 1, so no phase exists).
Write phase = Ref A post-state of the edge with the synchronised shadow update (CL-14):
e-3..e-1 = 3..1 clk before the even-slot latch edge, e+0 = on it (goes to the next pair), e+1..e+3 after.
"""
import json
import os
import sys

from ref_a import eff, fields

KINDS = ("single", "equal", "multi", "writeback")
PHASES = ("e-3", "e-2", "e-1", "e+0", "e+1", "e+2", "e+3", "even_c0", "even_c1", "even_c2", "even_mid",
          "even_N1", "odd_c0", "odd_mid", "odd_N1")
FIELDS = ("order", "n_code", "fs_div", "sys_en", "ota_en", "short", "boost", "trim")
CHOP = {(0, 0): "off", (1, 0): "sys", (1, 1): "otasys", (0, 1): "ota"}


def universe():
    U = {
        "MODE": [f"ord{o + 1}_n{n}_{ch}_s{s}" for o in (0, 1) for n in range(4) for ch in CHOP.values()
                 for s in (0, 1)],
        "BT": [f"n{n}_b{b}_t{t}" for n in (0, 3) for b in (0, 1) for t in (0, 4, 7)],
        "FS": [f"d{d}_n{n}" for d in range(8) for n in (0, 3)],
        "FST": ["0>4", "4>0", "1>0", "any>res"],
        "WP": [f"{p}_{k}" for p in PHASES for k in KINDS],
        "WF": list(FIELDS),
        "WRST": ["pending_at_rst"],
        "RDOFS": [f"ofs{d:+d}" for d in range(-8, 9)],
        "RDST": [f"sr{a}_fr{b}_ov{c}" for a in (0, 1) for b in (0, 1) for c in (0, 1)],
        "RDW": ["w1", "w2", "w3", "w4+", "held"],
        "OVR": ["u1", "u2", "u3", "u10+", "ovr_wrap"],
        "CTR": ["c0", "c1", "c254", "c255", "wrap255_0", "chg_at_wrap"],
        "RST": ["pre_start", "c0", "c1", "n0", "mid", "nNm1", "load-1", "load0", "load+1", "shift", "rd_high",
                "dbg1"],
        "ADDR": [f"a{a}_d{d}_{st}" for a in range(8) for d in (0, 1) for st in ("stable", "glitch")],
        "DATA": ["acc1_pos", "acc1_neg", "acc1_zero", "acc2_lt_m2p22", "acc2_gt_2p22", "acc2_zero",
                 "hi0000", "hiFFFF", "hi007F", "hiFF80"],
    }
    return U


# bins that cannot be hit by legal stimulus, with the reason (reported, not counted as holes)
UNREACH = {
    **{f"RDST:sr{a}_fr0_ov1": "overrun is set only by a load that also sets frame_ready; rd clears both"
       for a in (0, 1)},
    **{f"WP:e+{d}_{k}": "needs an earlier write after the latch edge: cfg_ld high/low >= 2 clk (3.8a pin rate, "
       "as cfg_clk) puts two synchronised updates >= 4 clk apart" for d in range(4) for k in ("multi", "writeback")},
}


class FCov:
    def __init__(self):
        self.h = {}
        self.prev_rst = 1
        self.pre_shadow = 0
        self.pre_raw = 0
        self.lds_pair = 0
        self.unread = 0
        self.st_read = False
        self.last_ctr = None
        self.rd_w = 0
        self.rd_held = False
        self.addr_v, self.addr_run = None, 0
        self.last_shift = -100

    def hit(self, g, b):
        d = self.h.setdefault(g, {})
        d[b] = d.get(b, 0) + 1

    def pre(self, tb):
        r, ui, e = tb.ref, tb.a_ui, tb.edges
        self.pre_shadow, self.pre_raw = r.shadow, r.active_raw
        if (ui >> 4) & 1 != getattr(self, "_cclk", 0):
            self.last_shift = e
        self._cclk = (ui >> 4) & 1
        # ---- rst_n assertion position (pre-state)
        if self.prev_rst and not tb.a_rst_n:
            if eff(r.shadow) != r.active:
                self.hit("WRST", "pending_at_rst")
            if not r.started:
                self.hit("RST", "pre_start")
            else:
                c, N, cnt, div = r.c, r.N, r.cnt, r.div
                pos = {0: "c0", 1: "c1", 2: "n0"}.get(c)
                if pos is None:
                    pos = "nNm1" if c == N + 1 else "mid"
                self.hit("RST", pos)
                dl = (cnt - (div - 1)) if c == N + 1 else (cnt + 1 if (c == 0 and r.slot > 0) else None)
                if dl in (-1, 0, 1):
                    self.hit("RST", f"load{dl:+d}" if dl else "load0")
            if e - self.last_shift <= 8:
                self.hit("RST", "shift")
            if (ui >> 3) & 1:
                self.hit("RST", "rd_high")
            if (ui >> 7) & 1:
                self.hit("RST", "dbg1")
        self.prev_rst = tb.a_rst_n
        if not tb.a_rst_n:
            self.unread, self.lds_pair, self.st_read, self.rd_w, self.addr_v = 0, 0, False, 0, None
            return
        # ---- synchronised rd rise (pre-state of the edge that acts on it)
        if r.started and r.ss_rd.s2 and not r.ss_rd.s3:
            c, N, cnt, div = r.c, r.N, r.cnt, r.div
            d = (cnt - (div - 1)) if c == N + 1 else (cnt + 1 if (c == 0 and r.slot > 0) else None)
            if d is not None and -8 <= d <= 8:
                self.hit("RDOFS", f"ofs{d:+d}")
            self.hit("RDST", f"sr{int(self.st_read)}_fr{r.frame_ready}_ov{r.overrun}")
        if r.a2 == 5 and not r.d2:
            self.st_read = True
        # ---- rd pin width
        if (ui >> 3) & 1:
            self.rd_w += 1
        elif self.rd_w:
            self.hit("RDW", "held" if self.rd_held else ("w4+" if self.rd_w >= 4 else f"w{self.rd_w}"))
            self.rd_w, self.rd_held = 0, False
        # ---- addr/dbg pin runs
        v = ui & 0x87
        if v != self.addr_v:
            if self.addr_v is not None and r.started:
                a, dg = self.addr_v & 7, self.addr_v >> 7
                self.hit("ADDR", f"a{a}_d{dg}_{'stable' if self.addr_run >= 3 else 'glitch'}")
            self.addr_v, self.addr_run = v, 1
        else:
            self.addr_run += 1

    def post(self, tb):
        r = tb.ref
        if not tb.a_rst_n:
            return
        ev = r.events
        if "latch" in ev:
            self.lds_pair = 0
            o, n = fields(self.pre_raw)["fs_div"], fields(r.active_raw)["fs_div"]
            if o != n:
                if f"{o}>{n}" in ("0>4", "4>0", "1>0"):
                    self.hit("FST", f"{o}>{n}")
                if n >= 5:
                    self.hit("FST", "any>res")
            if r.ctr == 0 and r.slot > 0 and r.pair_inv:
                self.hit("CTR", "chg_at_wrap")
        if "ld" in ev and r.started:
            self.lds_pair += 1
            new, act = eff(r.shadow), r.active
            if new == act:
                kind = "writeback" if eff(self.pre_shadow) != act else "equal"
            else:
                kind = "multi" if self.lds_pair >= 2 else "single"
            ev_ = r.slot % 2 == 0
            c, N, cnt, div = r.c, r.N, r.cnt, r.div
            if ev_ and c == 0 and cnt <= 3:
                ph = f"e+{cnt}"
            elif (not ev_) and c == N + 1 and cnt >= div - 3:
                ph = f"e{cnt - div:+d}"
            elif ev_:
                ph = {0: "even_c0", 1: "even_c1", 2: "even_c2"}.get(c, "even_N1" if c == N + 1 else "even_mid")
            else:
                ph = "odd_c0" if c == 0 else ("odd_N1" if c == N + 1 else "odd_mid")
            self.hit("WP", f"{ph}_{kind}")
            if kind in ("single", "multi"):
                fn, fa = fields(new), fields(act)
                for k in FIELDS:
                    if fn[k] != fa[k]:
                        self.hit("WF", k)
        if "rd_clear" in ev:
            self.unread = 0
        if (tb.a_ui >> 3) & 1 and "load" in ev:
            self.rd_held = True
        if "load" in ev:
            f = r.frames[-1]
            t = f["tag"]
            o, n, sy, ot, sh, ctr = (t >> 14) & 1, (t >> 12) & 3, (t >> 11) & 1, (t >> 10) & 1, (t >> 9) & 1, t & 0xFF
            self.hit("MODE", f"ord{o + 1}_n{n}_{CHOP[(sy, ot)]}_s{sh}")
            if n in (0, 3) and f["trim"] in (0, 4, 7):
                self.hit("BT", f"n{n}_b{f['boost']}_t{f['trim']}")
            a1, a2 = f["acc1"], f["acc2"]
            self.hit("DATA", "acc1_pos" if a1 > 0 else ("acc1_neg" if a1 < 0 else "acc1_zero"))
            if a2 < -(1 << 22):
                self.hit("DATA", "acc2_lt_m2p22")
            elif a2 > (1 << 22):
                self.hit("DATA", "acc2_gt_2p22")
            elif a2 == 0:
                self.hit("DATA", "acc2_zero")
            hi = (a2 & 0xFFFFFFFF) >> 16
            if hi in (0x0000, 0xFFFF, 0x007F, 0xFF80):
                self.hit("DATA", f"hi{hi:04X}")
            self.unread += 1
            u = self.unread
            if u in (1, 2, 3):
                self.hit("OVR", f"u{u}")
            elif u >= 10:
                self.hit("OVR", "u10+")
            if ctr in (0, 1, 254, 255) and r.slot > 1:
                self.hit("CTR", f"c{ctr}")
            if ctr == 0 and self.last_ctr == 255:
                self.hit("CTR", "wrap255_0")
                if r.overrun:
                    self.hit("OVR", "ovr_wrap")
            self.last_ctr = ctr
            self.st_read = False
        if r.started and r.c == 2 and r.cnt == 0:
            n = r.cfg["n_code"]
            if n in (0, 3):
                self.hit("FS", f"d{fields(r.active_raw)['fs_div']}_n{n}")

    def dump(self, name, seed):
        d = os.path.join(os.environ.get("C9_OUT", "."), "fcov")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{name}_s{seed}.json"), "w") as fh:
            json.dump(dict(test=name, seed=seed, hits=self.h), fh)


def merge(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                files += [os.path.join(root, f) for f in fs if f.endswith(".json") and "/fcov" in root]
        else:
            files.append(p)
    tot, by = {}, {}
    for f in sorted(files):
        j = json.load(open(f))
        for g, bins in j["hits"].items():
            for b, n in bins.items():
                tot.setdefault(g, {})
                tot[g][b] = tot[g].get(b, 0) + n
                by.setdefault((g, b), set()).add(j["test"])
    U = universe()
    nh = nt = 0
    print(f"FCOV files {len(files)}")
    for g, bins in U.items():
        miss = [b for b in bins if not tot.get(g, {}).get(b) and f"{g}:{b}" not in UNREACH]
        unr = [b for b in bins if f"{g}:{b}" in UNREACH]
        reach = len(bins) - len(unr)
        nh += reach - len(miss)
        nt += reach
        print(f"FCOV {g}: {reach - len(miss)}/{reach} hit ({len(unr)} unreachable){' MISS ' + ' '.join(miss) if miss else ''}")
    print(f"FCOV TOTAL {nh}/{nt} reachable bins hit ({100.0 * nh / max(nt, 1):.1f} %)")
    extra = sorted(f"{g}:{b}" for g in tot for b in tot[g] if b not in U.get(g, []))
    if extra:
        print("FCOV extra (outside universe):", " ".join(extra[:30]))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "merge":
        merge(sys.argv[2:])
    else:
        print("usage: fcov.py merge <dir|json> ...")
