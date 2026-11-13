#!/usr/bin/env python3
"""C4b gate testbench (WO-54): switches, phase generator, level shifters, VDPWR detector. Netlist: netlist.py.

    python c4_tb.py jobs OUTDIR                        # OUTDIR/jobs.txt, one `run` line per job (feed to lpool.sh)
    python c4_tb.py run KIND CORNER FS MUT OUTDIR      # one job -> OUTDIR/<KIND>_<CORNER>_<FS>_<MUT>.json (csv deleted)
    python c4_tb.py report OUTDIR                      # summary.md / summary.json; exit 2 if a job is missing or errored
                                                       # or a broken copy does not REJECT on its target row

KIND (DESIGN.md 8, C4b plan + REVIEW-C4a additions):
  ron     #1  DC Ron of every switch over its range, body effect in. Copy `onetype`: TGs lose the PMOS, NMOS-only
              switches become PMOS-only.
  tim     #2/#5/#6/#10/#11 + m1/m2/M2: generator through the LS cells, 4 cycles, y / chop toggling, swap / short
              schedule, order 1 (rst2_o1 after the decision). Rows: g at switch thresholds on the gated nets incl.
              cross terms (n gate of one phase vs p gate of the other), g50 <= 0.025/fs, t_half >= 0.45/fs, early
              fully off before late starts (eb >= 0), LS edge, gated-control glitch, DAC-net glitch (y race), rule 13,
              strobe placement, order-1 reset placement. Edge rate is info (D76).
  injdm   M3: differential input sweep (+-VREF at Vin_cm = VREF/2), real switches + 3 sigma Cs mismatch vs an
              ideal-switch copy in the same deck; INL of the difference in ppm of 2 VREF. Copy `order_inv`.
  injcm   CM sweep 0..VREF at Vd = 0: CM->DM slope = eps_inj <= 2.8e-4. Copy `top8` (8/24 top short).
  settle  #4  input settling with the pad model (R_src 1k + 500 ohm + 5 pF) from VREF- at 4 MHz: tau_eff <= 18.75 ns.
              Copy `ronx3` (input TG W / 3).
  leak    #9  Sg off leakage into vg vs Vin_cm (tp 0.18..2.22 V), sign recorded. Copy `tg` (PMOS added).
  rampa / rampb  #8 power-up, order a (VAPWR first) / b (VDPWR first), fs running: safe states while VDPWR is
              missing, no VIN<->VREF crowbar, 1.8 V nets <= VDPWR, release. Copies `nodet`, `overlap`, `hvfold`.
Every metric comes from waveform crossings; a missing crossing is MISSING (fails the row), never a default.
#7 (reset residue, D46a) needs the C2 reset switch with OTA2 and runs at C1/C2 integration (not here).
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netlist as N  # noqa: E402

CORNERS = {
    "tt_27": ("tt", 27, 3.3, 1.8), "ss_m40": ("ss", -40, 3.0, 1.62), "ss_125": ("ss", 125, 3.0, 1.62),
    "ff_m40": ("ff", -40, 3.6, 1.98), "ff_125": ("ff", 125, 3.6, 1.98), "sf_27": ("sf", 27, 3.3, 1.8),
    "fs_27": ("fs", 27, 3.3, 1.8), "ss_m40_ls": ("ss", -40, 3.6, 1.62), "ff_m40_ls": ("ff", -40, 3.0, 1.98),
    "sf_m40_ls": ("sf", -40, 3.6, 1.62), "ff_100": ("ff", 100, 3.6, 1.98)}
FSS = {"4M": 4e6, "2M": 2e6, "0M25": 0.25e6, "x": 4e6}
VREF = 2.048
VMAX = 1.1 * VREF
TCQ = 0.6e-9            # C9 DAC flop clk->q, ss/1.62 (DESIGN.md 6)
TDEC = 3.4e-9           # C3 decision time, T2band upper bound (3.36 ns)
CLOAD = 200e-15
T0 = 20e-9
CS, CINT = 0.5e-12, 1.0e-12
DCS = 0.0075 / 2        # Cs+/Cs- = 1 +- DCS (0.75 % 3 sigma total)
RDAC = (10e-9 - 500 * 5.75e-12) / 0.75e-12      # tau_ref <= 10 ns: Ron * 0.75 pF + 500 ohm * 5.75 pF pad
R2 = 0.5 * 112.5e-9 / 14 / 0.5e-12              # 14 tau inside half of t_half(4 MHz) on 0.5 pF -> ~8 kOhm
RON = dict(sin=(0.0, VMAX, 1500.0), sdh=(1.0, VMAX, RDAC), sdl=(0.0, 0.1, RDAC), stp=(0.18, 2.22, 31e3),
           sg=(1.07, 1.33, 4000.0), s2in=(0.89, 2.11, R2), s2cm=(0.89, 2.11, R2), skh=(1.0, VMAX, RDAC),
           skl=(0.0, 0.1, RDAC), sk0=(0.0, VMAX, R2))
LEAK_ROW = {"ff_125": 90e-12, "ff_100": 20e-12}  # SPEC vg row per node. D78: Sg limit = row - C1 measured share
#                                                 (same deck, metrics_leak); replaces the 50 % proposal (45 / 10 pA)
LIM = dict(g_min=1.0e-9, eb_min=0.0, ls_edge_max=1.0e-9, inl_ppm=2.0, eps_inj=2.8e-4, tau_in=18.75e-9,
           r2_width=15e-9, crowbar_q=50e-15, safe_v=0.3, v18_over=0.05)
GEN_MUTS = ("overlap", "gbig", "noearly", "edge1", "lsload", "wrongstrobe", "rawchop", "nodet", "hvfold", "o1early")

# broken copy -> (target row, [(kind, corner, fs)])
BROKEN = {
    "onetype": ("ron", [("ron", "ss_m40", "x"), ("ron", "tt_27", "x")]),
    "overlap": ("g_min", [("tim", c, "4M") for c in ("tt_27", "ss_m40", "ff_m40")]),
    "gbig": ("g50_max", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "noearly": ("eb_min", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "edge1": ("eb_min", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "lsload": ("ls_edge_max", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "wrongstrobe": ("strobe", [("tim", c, "4M") for c in ("tt_27", "ff_m40", "ss_125")]),
    "rawchop": ("rule13", [("tim", c, "4M") for c in ("tt_27", "ff_m40", "ss_125")]),
    "ylate": ("glitch_d", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "ctlmid": ("glitch_s", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "o1early": ("order1", [("tim", c, "4M") for c in ("tt_27", "ff_m40")]),
    "order_inv": ("inl", [("injdm", c, "4M") for c in ("tt_27", "ff_125")]),
    "top8": ("eps_inj", [("injcm", c, "4M") for c in ("tt_27", "ff_125")]),
    "ronx3": ("tau_in", [("settle", "ss_m40", "4M")]),
    "tg": ("leak", [("leak", "ff_125", "x")]),
    "nodet": ("safe", [("rampa", c, "4M") for c in ("tt_27", "ss_m40")]),
    "overlapr": ("crowbar", [("rampb", "tt_27", "4M")]),
    "hvfold": ("stress", [("rampa", "tt_27", "4M")]),
}
TIM_CORNERS = ("tt_27", "ss_m40", "ss_125", "ff_m40", "ff_125", "sf_27", "fs_27", "ss_m40_ls", "ff_m40_ls", "sf_m40_ls")
RAMP_CORNERS = ("tt_27", "ss_m40", "ff_m40", "sf_m40_ls")


def joblist():
    j = [("ron", c, "x", "none") for c in ("tt_27", "ss_m40", "ss_125", "ff_m40", "ff_125")]
    j += [("tim", c, f, "none") for c in TIM_CORNERS for f in ("4M", "2M", "0M25")]
    j += [(k, c, "4M", "none") for k in ("injdm", "injcm") for c in ("tt_27", "ss_m40", "ff_125")]
    j += [("settle", c, "4M", "none") for c in ("tt_27", "ss_m40", "ss_125")]
    j += [("leak", c, "x", "none") for c in ("ff_125", "ff_100")]
    j += [(k, c, "4M", "none") for k in ("rampa", "rampb") for c in RAMP_CORNERS]
    for mut, (_, lst) in BROKEN.items():
        j += [(k, c, f, mut) for k, c, f in lst]
    return j


# ---------------------------------------------------------------- decks
def head(title, corner, extra=".option reltol=1e-4"):
    p, t, _, _ = CORNERS[corner]
    return [f"* WO-54 {title}", f'.lib "{N.LIB}" {p}', f".include {N.HVL}", f".temp {t}", extra]


def pulse(name, node, v, td, width, per):
    return f"{name} {node} 0 PULSE(0 {v} {td:.6e} 0.2n 0.2n {width - 0.2e-9:.6e} {per:.6e})"


def dec_line():
    """C3 decision-done (NAND(q, qb)) modelled as the 1.8 V strobe delayed by TDEC (ideal line, matched)."""
    return ["Edec dbuf 0 phc 0 2", "Rdb dbuf dtl 50", f"Tdec dtl 0 decin 0 Z0=50 TD={TDEC:.4g}", "Rdl decin 0 50"]


def loads():
    L = [f"Cl{x}t {x}_t 0 {CLOAD:g}" for x in N.PH] + [f"Cl{x}c {x}_c 0 {CLOAD:g}" for x in N.PH]
    return L + ["Clchp chp 0 100f", "Clchn chn 0 100f", "Clchlp chlp 0 50f", "Clchln chln 0 50f", "Clphc phc 0 50f",
                "Clisl isl 0 100f", "Clrstb rstb 0 100f"]


def gen_block(mut):
    gm = "+".join(x for x in N.toks(mut) if x in GEN_MUTS) or None
    if mut == "overlapr":
        gm = "overlap"
    return [N.gen(gm), N.inst()]


def ctrl(csv, vecs):
    return [".control", "set wr_singlescale", "set wr_vecnames", "set numdgt=12", "run",
            f"wrdata {csv} {' '.join(vecs)}", ".endc", ".end"]


def deck_ron(corner, mut, csv):
    _, _, va, _ = CORNERS[corner]
    one = mut == "onetype"
    L = head("ron " + corner, corner, ".option gmin=1e-15 reltol=1e-6 abstol=1e-15")
    L += [f"Vdd vdd 0 {va}", "Vsig a 0 0", "Bb b 0 V = V(a) - 1e-3"]
    for k, (wn, wp) in N.SW.items():
        L.append(f"Vm_{k} a am_{k} 0")
        if one and not wp:
            L += N.switch("s" + k, f"am_{k}", "b", "vdd", "0", wn=wn, wp=0, pdev_only=True)
        else:
            L += N.switch("s" + k, f"am_{k}", "b", "vdd", "0", wn=wn, wp=0 if one else wp)
    L.append(f".dc Vsig 0 {va} 0.01")
    vecs = ["v(a)"] + [f"i(Vm_{k})" for k in N.SW]
    return "\n".join(L + ctrl(csv, vecs)) + "\n", vecs, va


def deck_tim(corner, fsk, mut, csv):
    _, _, va, vd = CORNERS[corner]
    T = 1.0 / FSS[fsk]
    dly = 8e-9 if mut == "ylate" else 0.0
    dm = 0.75 * T if mut == "ctlmid" else 0.0
    L = head(f"tim {corner} {fsk} {mut}", corner)
    L += [f"Vdd vdd 0 {va}", f"Vdl vdl 0 {vd}",
          f"Vclk clk0 0 PULSE(0 {vd} {T0:.4g} 0.2n 0.2n {T / 2 - 0.2e-9:.6e} {T:.6e})", "Rclk clk0 fsin 10",
          "Cfs fsin 0 5f",
          pulse("Vy", "yin", vd, T0 + TCQ + dly, T, 2 * T), pulse("Vsw", "swin", vd, T0 + T + TCQ + dm, 2 * T, 4 * T),
          pulse("Vsh", "shin", vd, T0 + 3 * T + TCQ + dm, T, 8 * T), pulse("Vch", "chin", vd, T0 + TCQ, T, 2 * T),
          "Vrs rsin 0 0", "Vord ordin 0 0"]
    L += dec_line() + gen_block(mut) + loads()
    tstop = T0 + 4 * T
    tmax = 50e-12 if FSS[fsk] >= 2e6 else 100e-12
    L.append(f".tran {tmax:.3g} {tstop:.6e} 0 {tmax:.3g}")
    vecs = ["fsin", "fsh"] + [f"{x}_{s}" for x in N.PH for s in "tc"] + ["chp", "chn", "chlp", "chln", "phc", "decin"]
    return "\n".join(L + ctrl(csv, [f"v({v})" for v in vecs])) + "\n", vecs, tstop


def drv(node):
    """WO-70: digital pad input = source -> 100 ohm -> node, 5 fF. A bare ideal source on an LS input stopped the
    inj / settle / ramp decks on 'Timestep too small' at the LS input snap (node vord#branch / brs#branch)."""
    return [f"Rdrv_{node} {node}_s {node} 100", f"Cdrv_{node} {node} 0 5f"]


def common_src(corner, T, order_v=None, y_v=0.0):
    _, _, va, vd = CORNERS[corner]
    L = [f"Vdd vdd 0 {va}", f"Vdl vdl 0 {vd}",
         f"Vclk clk0 0 PULSE(0 {vd} {T0:.4g} 0.2n 0.2n {T / 2 - 0.2e-9:.6e} {T:.6e})", "Rclk clk0 fsin 10",
         "Cfs fsin 0 5f", f"Vy yin_s 0 {y_v}", "Vsw swin_s 0 0", "Vsh shin_s 0 0", "Vch chin_s 0 0", "Vrs rsin_s 0 0",
         f"Vord ordin_s 0 {vd if order_v is None else order_v}"]
    for n in ("yin", "swin", "shin", "chin", "rsin", "ordin"):
        L += drv(n)
    return L + dec_line()


def inj_points(kind):
    if kind == "injdm":
        return [VREF / 2] * 17, [VREF * (i - 8) / 8 for i in range(17)]
    return [VREF * i / 8 for i in range(9)], [0.0] * 9


def deck_inj(kind, corner, mut, csv):
    _, _, va, _ = CORNERS[corner]
    T = 1.0 / FSS["4M"]
    cms, dms = inj_points(kind)
    pts = list(zip(cms, dms))
    seq = [pts[0]] + pts                                   # cycle 0 = warm-up
    tR = lambda k: T0 + k * T                              # noqa: E731
    # WO-70: ideal-switch roff/ron <= 1e11 (ngspice limit ~1e12; 1e13 stopped every inj deck on 'Timestep too
    # small' at the first fs edge, node vinn#branch); both integrators held in reset until T0 - 5 ns (the 1e5-gain
    # E-source integrators otherwise start from an undefined DC point at ~13 V). Same models on the real and the
    # ideal copy, so the residual roff leakage cancels in the difference.
    L = head(f"{kind} {corner} {mut}", corner, ".option reltol=1e-6 abstol=1e-15 vntol=1e-9 chgtol=1e-18 method=gear")
    L += common_src(corner, T) + [f".model SWI sw vt={va / 2:.4g} vh=0.01 ron=10 roff=1e12",
                                  ".model SWR sw vt=0.5 vh=0.01 ron=10 roff=1e12",
                                  "Vicm vicm 0 1.2", f"Vbi vbi 0 {VREF / 2}", f"Vcmin vcmin 0 {VREF / 2}",
                                  f"Vrst rstc 0 PULSE(0 1 {T0 + T / 2 + 40e-9:.6e} 0.1n 0.1n {T / 2 - 55e-9:.6e} {T:.6e})",
                                  f"Vrst0 rst0 0 PWL(0 1 {T0 - 5e-9:.6e} 1 {T0 - 4.9e-9:.6e} 0)"]
    for s, sg in (("p", 0.5), ("n", -0.5)):
        pw = [f"0 {seq[0][0] + sg * seq[0][1]:.6f}"]
        for k in range(1, len(seq)):
            pw += [f"{tR(k) + 5e-9:.6e} {seq[k - 1][0] + sg * seq[k - 1][1]:.6f}",
                   f"{tR(k) + 10e-9:.6e} {seq[k][0] + sg * seq[k][1]:.6f}"]
        L.append(f"Vin{s} vin{s} 0 PWL({' '.join(pw)})")
    gi, gt = ("se", "sl") if mut == "order_inv" else ("pas", "se")      # input TG gate / top short gate
    for s, o, cs in (("p", "n", CS * (1 + DCS)), ("n", "p", CS * (1 - DCS))):
        L += N.switch(f"sin{s}", f"vin{s}", f"b{s}", f"{gi}_t", f"{gi}_c", key="sin")
        L += N.switch(f"ssw{s}", f"vin{o}", f"b{s}", "swp_t", "swp_c", key="sin")
        L += N.switch(f"ssh{s}", "vcmin", f"b{s}", "sho_t", "sho_c", key="sin")
        L += [f"Sbi{s} b{s} vbi il_t 0 SWI", f"Ccs{s} b{s} tp{s} {cs:.6g}"]
        L += N.switch(f"sg{s}", f"tp{s}", f"vg{s}", "ie_t", "ie_c", key="sg")
        L += [f"Eop{s} ox{s} 0 vicm vg{s} 1e5", f"Cint{s} vg{s} ox{s} {CINT:g}", f"Srs{s} vg{s} ox{s} rstc 0 SWR",
              f"Sr0{s} vg{s} ox{s} rst0 0 SWR"]
        # ideal copy
        L += [f"Sisin{s} vin{s} ib{s} pas_t 0 SWI", f"Sibi{s} ib{s} vbi il_t 0 SWI", f"Cics{s} ib{s} itp{s} {cs:.6g}",
              f"Sisg{s} itp{s} ivg{s} ie_t 0 SWI", f"Eiop{s} iox{s} 0 vicm ivg{s} 1e5", f"Ciint{s} ivg{s} iox{s} {CINT:g}",
              f"Sirs{s} ivg{s} iox{s} rstc 0 SWR", f"Sir0{s} ivg{s} iox{s} rst0 0 SWR"]
    wn, wp = (8.0, 24.0) if mut == "top8" else N.SW["stp"]
    L += N.switch("stp", "tpp", "tpn", f"{gt}_t", f"{gt}_c", wn=wn, wp=wp) + ["Sistp itpp itpn se_t 0 SWI"]
    L += gen_block(None) + loads()
    tstop = tR(len(seq) + 1)
    L.append(f".tran 50p {tstop:.6e} 0 50p")
    vecs = ["v(oxp)", "v(oxn)", "v(ioxp)", "v(ioxn)", "v(fsin)"]
    return "\n".join(L + ctrl(csv, vecs)) + "\n", vecs, tstop, pts


def deck_settle(corner, mut, csv):
    T = 1.0 / FSS["4M"]
    L = head(f"settle {corner} {mut}", corner, ".option reltol=1e-6 abstol=1e-15 vntol=1e-9 method=gear")
    L += common_src(corner, T)
    wn, wp = (4.0, 12.0) if mut == "ronx3" else N.SW["sin"]
    for s, v in (("a", VMAX), ("b", 1.65)):
        L += [f"Vs{s} s{s} 0 {v}", f"Rs{s} s{s} pd{s} 1k", f"Cp{s} pd{s} 0 5p", f"Rp{s} pd{s} pin{s} 500"]
        L += N.switch(f"sin{s}", f"pin{s}", f"b{s}", "pas_t", "pas_c", wn=wn, wp=wp)
        L += N.switch(f"sdl{s}", f"b{s}", "0", "dl_t", "dl_c", key="sdl")
        L += [f"Cs{s} b{s} tp{s} {CS:g}", f"Vtp{s} tp{s} 0 1.2"]
    L += gen_block(None) + loads()
    tstop = T0 + 7 * T
    L.append(f".tran 50p {tstop:.6e} 0 50p")
    vecs = ["v(ba)", "v(bb)", "v(pas_t)"]
    return "\n".join(L + ctrl(csv, vecs)) + "\n", vecs, tstop


def deck_leak(corner, mut, csv):
    _, _, va, _ = CORNERS[corner]
    L = head(f"leak {corner} {mut}", corner, ".option gmin=1e-15 reltol=1e-6 abstol=1e-16")
    L += [f"Vdd vdd 0 {va}", "Vvg vgx 0 1.2", "Vam vgx vg 0", "Vtp tp 0 1.2"]
    L += N.switch("sg", "vg", "tp", "0", "vdd", key="sg")
    if mut == "tg":
        L += [N.mos("sgx", "vg", "vdd", "tp", "vdd", N.HVP, 15.0, N.L_SW)]
    # D78 (WO-70): C1's share of the same vg node, measured in the same deck on its own ammeter. C1 DESIGN.md M5:
    # island switch nfet_g5v0d10v5 W 2/L 0.5 (off, gate 0, far side V_ICM 1.2 V); input chopper W 4/L 0.5, two per
    # vg node: one on (gate VAPWR) to the pair gate (node gpa, only that device), one off (gate 0) to the other
    # side's gate held at 1.2 V. Junction-dominated (leak_temp.md), so both shares have the same sign and add.
    L += ["Vamc vgx vgc 0", "Vicm1 vicm1 0 1.2",
          N.mos("c1isl", "vgc", "0", "vicm1", "0", N.HVN, 2.0, 0.5),
          N.mos("c1cha", "vgc", "vdd", "gpa", "0", N.HVN, 4.0, 0.5), "Cgpa gpa 0 1f",
          N.mos("c1chb", "vgc", "0", "vicm1", "0", N.HVN, 4.0, 0.5)]
    L.append(".dc Vtp 0.18 2.22 0.01")
    vecs = ["v(tp)", "i(Vam)", "i(Vamc)"]
    return "\n".join(L + ctrl(csv, vecs)) + "\n", vecs, 2.22


def deck_ramp(kind, corner, mut, csv):
    _, _, va, vd = CORNERS[corner]
    T = 1.0 / FSS["4M"]
    up1, up2 = "0 0 1u 0 6u", "0 0 10u 0 15u"
    pa, pd = (up1, up2) if kind == "rampa" else (up2, up1)
    L = head(f"{kind} {corner} {mut}", corner, ".option reltol=1e-4 method=gear")
    L += [f"Vdd vdd 0 PWL({pa} {va})", f"Vdl vdl 0 PWL({pd} {vd})",
          f"Vck ck 0 PULSE(0 1 {T0:.4g} 0.2n 0.2n {T / 2 - 0.2e-9:.6e} {T:.6e})", "Bfs fsin_s 0 V = V(vdl)*V(ck)",
          f"Vyk yk 0 PULSE(0 1 {T0 + TCQ:.4g} 0.2n 0.2n {T - 0.2e-9:.6e} {2 * T:.6e})", "Byy yin_s 0 V = V(vdl)*V(yk)",
          "Bch chin_s 0 V = V(vdl)*V(yk)", "Vsw swin_s 0 0", "Vsh shin_s 0 0", "Vord ordin_s 0 0",
          "Vrk rk 0 PWL(0 1 20u 1 20.01u 0)", "Brs rsin_s 0 V = V(vdl)*V(rk)",
          "Vinp vinp 0 0.3", "Vinn vinn 0 1.7", "Vrp vrp 0 2.0", "Vrm vrm 0 0", "Vtp vtp 0 1.2"]
    for n in ("fsin", "yin", "chin", "swin", "shin", "ordin", "rsin"):
        L += drv(n)
    L += dec_line()
    for s, vin, vo in (("p", "vinp", "vinn"), ("n", "vinn", "vinp")):
        L += [f"Vai{s} xi{s} b{s} 0", f"Vad{s} xd{s} b{s} 0"]
        L += N.switch(f"sin{s}", vin, f"xi{s}", "pas_t", "pas_c", key="sin")
        L += N.switch(f"ssw{s}", vo, f"xi{s}", "swp_t", "swp_c", key="sin")
        L += N.switch(f"sdh{s}", "vrp", f"xd{s}", "dh_t", "dh_c", key="sdh")
        L += N.switch(f"sdl{s}", "vrm", f"xd{s}", "dl_t", "dl_c", key="sdl")
        L += [f"Cs{s} b{s} tp{s} {CS:g}", f"Rtp{s} tp{s} vtp 1k"]
    L += gen_block(mut) + loads()
    tstop = 25e-6
    L.append(f".tran 0.2n {tstop:.6e} 0 0.2n")
    nets = ["ie_t", "il_t", "se_t", "sl_t", "pas_t", "swp_t", "sho_t", "dh_t", "dl_t", "r2_t"]
    vecs = ["v(vdd)", "v(vdl)", "v(isl)", "v(pwrok)", "v(chlp)", "v(chln)", "v(phc)"] + [f"v({n})" for n in nets] + \
        ["i(Vaip)", "i(Vadp)", "i(Vain)", "i(Vadn)", "i(Vrp)"]
    return "\n".join(L + ctrl(csv, vecs)) + "\n", vecs, tstop


# ---------------------------------------------------------------- helpers
def cross(t, v, th, rising, t0, t1):
    m = np.nonzero((t >= t0) & (t <= t1))[0]
    if len(m) < 2:
        return None
    tt, vv = t[m], v[m]
    s = ((vv[:-1] < th) & (vv[1:] >= th)) if rising else ((vv[:-1] > th) & (vv[1:] <= th))
    k = np.nonzero(s)[0]
    if not len(k):
        return None
    i = k[0]
    return float(tt[i] + (th - vv[i]) * (tt[i + 1] - tt[i]) / (vv[i + 1] - vv[i]))


def sub(a, b):
    return None if a is None or b is None else a - b


def mn(xs):
    xs = list(xs)
    return None if not xs or any(x is None for x in xs) else min(xs)


def mx(xs):
    xs = list(xs)
    return None if not xs or any(x is None for x in xs) else max(xs)


def wmax(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    return float(v[m].max()) if m.any() else None


def spice(deck, tag, out):
    open(os.path.join(out, ".spiceinit"), "w").write("set num_threads=1\n")
    open(os.path.join(out, tag + ".sp"), "w").write(deck)
    env = dict(os.environ, OMP_NUM_THREADS="1")
    r = subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=5400, env=env)
    log = r.stdout + r.stderr
    open(os.path.join(out, tag + ".log"), "w").write(log)
    # WO-70: case-insensitive match. ngspice prints "Timestep too small" and then the follow-on "Error: incomplete
    # or empty netlist" (batch mode, aborted run), and only the follow-on was caught, so WO-54 reported an empty deck.
    lo = [ln for ln in log.splitlines()]
    bad = [ln for ln in lo if "timestep too small" in ln.lower() or "singular matrix" in ln.lower()
           or "unknown subckt" in ln.lower() or "could not find" in ln.lower() or "aborted" in ln.lower()]
    bad += [ln for ln in lo if ln.lower().startswith("error")]
    return r.returncode, bad


# ---------------------------------------------------------------- metrics
def metrics_ron(d, corner, mut):
    v = d[:, 1]
    m = {}
    for j, k in enumerate(N.SW):
        i = np.abs(d[:, 2 + j])
        ron = np.where(i > 0, 1e-3 / np.maximum(i, 1e-30), np.inf)
        lo, hi, lim = RON[k]
        rng = (v >= lo - 1e-9) & (v <= hi + 1e-9)
        if not rng.any():
            m[k] = dict(ron_max=None, lim=lim)
            continue
        jm = int(np.argmax(np.where(rng, ron, -1)))
        m[k] = dict(ron_max=float(ron[jm]), v_at=float(v[jm]), lim=lim)
    return m


def metrics_tim(d, vecs, corner, fsk, mut):
    _, _, va, vd = CORNERS[corner]
    T = 1.0 / FSS[fsk]
    t = d[:, 0]
    w = {n: d[:, 1 + j] for j, n in enumerate(vecs)}
    lo, mid, hi = 0.1 * va, 0.5 * va, 0.9 * va
    W = 60e-9
    tR = lambda k: T0 + k * T            # noqa: E731
    tF = lambda k: T0 + k * T + T / 2    # noqa: E731
    ysch = [1, 0, 1, 0]
    swsch, shsch = [0, 1, 1, 0], [0, 0, 0, 1]
    snet = ["sho" if shsch[k] else "swp" if swsch[k] else "pas" for k in range(4)]
    dnet = ["dh" if ysch[k] else "dl" for k in range(4)]

    def c(n, th, rising, t0, t1=None):
        return cross(t, w[n], th, rising, t0 - 2e-9, t0 + W if t1 is None else t1)

    def off_end(x, te):
        return mx([c(x + "_t", lo, False, te), c(x + "_c", hi, True, te)])

    def on_start(x, te):
        return mn([c(x + "_t", lo, True, te), c(x + "_c", hi, False, te)])

    def late_start(x, te):
        return mn([c(x + "_t", hi, False, te), c(x + "_c", lo, True, te)])

    m = {}
    g, g50, eb, th = [], [], [], []
    for k in (2, 3):
        for te, off, on, early, lates in ((tR(k), ("se", "sl", snet[k - 1]), ("ie", "il", dnet[k]), "se", ("sl", snet[k - 1])),
                                          (tF(k), ("ie", "il", dnet[k]), ("se", "sl", snet[k]), "ie", ("il", dnet[k]))):
            g.append(sub(mn(on_start(x, te) for x in on), mx(off_end(x, te) for x in off)))
            g50.append(sub(mn(c(x + "_t", mid, True, te) for x in on), mx(c(x + "_t", mid, False, te) for x in off)))
            eb.append(sub(mn(late_start(x, te) for x in lates), off_end(early, te)))
    for x, ks in (("il", 2), ("sl", 2), (dnet[2], 2), (snet[2], 2)):
        rise_t = tR(ks) if x in ("il", dnet[2]) else tF(ks)
        th.append(sub(c(x + "_t", mid, False, rise_t + T / 2), c(x + "_t", mid, True, rise_t)))
    m["g_min"], m["g50_max"], m["eb_min"], m["t_half_min"] = mn(g), mx(g50), mn(eb), mn(th)
    # LS
    tin_r, tin_f = c("fsin", vd / 2, True, tR(2)), c("fsin", vd / 2, False, tF(2))
    tls_r, tls_f = c("fsh", mid, True, tR(2)), c("fsh", mid, False, tF(2))
    m["ls_delay_r"], m["ls_delay_f"] = sub(tls_r, tin_r), sub(tls_f, tin_f)
    m["ls_edge"] = mx([sub(c("fsh", hi, True, tR(2)), c("fsh", lo, True, tR(2))),
                       sub(c("fsh", lo, False, tF(2)), c("fsh", hi, False, tF(2)))])
    m["ls_duty_err"] = None if tls_r is None or tls_f is None else (tls_f - tls_r) / T - 0.5
    edges = []
    for x in ("ie", "il", "se", "sl", snet[2], dnet[2]):
        for s in "tc":
            for te in (tR(2), tF(2)):
                a, b = c(f"{x}_{s}", lo, True, te), c(f"{x}_{s}", hi, True, te)
                edges.append(sub(b, a) if a is not None else sub(c(f"{x}_{s}", lo, False, te), c(f"{x}_{s}", hi, False, te)))
    m["edge_max_info"] = mx(edges)
    # gated-control glitch (m1): per phase S exactly the scheduled net, aligned with sl; all S nets off in phase I
    gs_bad, gs_max, gs_align = [], 0.0, 0.0
    for k in range(4):
        a0, a1 = tF(k) - 1e-9, tR(k + 1) + 15e-9
        for x in ("pas", "swp", "sho"):
            v = wmax(t, w[x + "_t"], a0, a1)
            if x == snet[k]:
                if v is None or v < hi:
                    gs_bad.append(f"{x} not on in S{k}")
                else:
                    al = sub(c(x + "_t", mid, True, tF(k)), c("sl_t", mid, True, tF(k)))
                    gs_align = max(gs_align, abs(al) if al is not None else 1.0)
                    if al is None or abs(al) > 3e-9:
                        gs_bad.append(f"{x} misaligned in S{k}")
            elif v is None or v > lo:
                gs_bad.append(f"{x} glitch {v} in S{k}")
                gs_max = max(gs_max, v or 0.0)
            vi = wmax(t, w[x + "_t"], tR(k) + 15e-9, tF(k) - 1e-9)
            if vi is None or vi > lo:
                gs_bad.append(f"{x} on in I{k}")
                gs_max = max(gs_max, vi or 0.0)
    m["glitch_s"] = gs_bad
    m["glitch_s_max"], m["glitch_s_align"] = gs_max, gs_align
    # DAC nets (y race): in phase I of cycles 1..3 only the scheduled net, the other below 10 %
    gd_bad, gd_max = [], 0.0
    for k in (1, 2, 3):
        for x in ("dh", "dl"):
            v = wmax(t, w[x + "_t"], tR(k) - 1e-9, tF(k) + 15e-9)
            if x == dnet[k]:
                if v is None or v < hi:
                    gd_bad.append(f"{x} not on in I{k}")
            elif v is None or v > lo:
                gd_bad.append(f"{x} glitch {v} in I{k}")
                gd_max = max(gd_max, v or 0.0)
    m["glitch_d"], m["glitch_d_max"] = gd_bad, gd_max
    # rule 13: chopper edges inside the S->I gap (after S fully off, before I starts)
    pre, post = [], []
    for k in (1, 2, 3):
        te = tR(k)
        starts, ends = [], []
        for n, vv in (("chp", va), ("chn", va), ("chlp", vd), ("chln", vd)):
            r10, r90 = c(n, 0.1 * vv, True, te), c(n, 0.9 * vv, True, te)
            f90, f10 = c(n, 0.9 * vv, False, te), c(n, 0.1 * vv, False, te)
            if r10 is not None:
                starts.append(r10)
                ends.append(r90)
            elif f90 is not None:
                starts.append(f90)
                ends.append(f10)
            else:
                starts.append(None)
                ends.append(None)
        pre.append(sub(mn(starts), mx(off_end(x, te) for x in ("se", "sl", snet[k - 1]))))
        post.append(sub(mn(on_start(x, te) for x in ("ie", "il", dnet[k])), mx(ends)))
    m["r13_pre"], m["r13_post"] = mn(pre), mn(post)
    # strobe (D74): fires after phase I fully off, with >= 0.3 t_half + 1 ns to the next fs_tick
    sp, sq, fire = [], [], []
    for k in (1, 2):
        tf = c("phc", vd / 2, True, tR(k) + 0.5e-9, tR(k + 1))
        fire.append(sub(tf, tF(k)))
        sp.append(sub(tf, mx(off_end(x, tF(k)) for x in ("ie", "il", dnet[k]))))
        nxt = c("fsin", vd / 2, True, tR(k + 1) - 3e-9, tR(k + 1) + 5e-9)
        sq.append(None if sub(nxt, tf) is None else sub(nxt, tf) - (0.3 * 0.45 * T + 1e-9))
    m["strobe_pre"], m["strobe_post"], m["strobe_fire_after_fall"] = mn(sp), mn(sq), mx(fire)
    # order 1: rst2_o1 (r2) starts after the decision, ends before ie starts, width >= 15 ns
    op, oq, owd = [], [], []
    for k in (1, 2):
        tdn = c("decin", vd / 2, True, tF(k), tR(k + 1))
        op.append(sub(on_start("r2", tF(k) + 1e-9) if tdn is None else
                      mn([c("r2_t", lo, True, tF(k), tR(k + 1)), c("r2_c", hi, False, tF(k), tR(k + 1))]), tdn))
        oq.append(sub(on_start("ie", tR(k + 1)), off_end("r2", tR(k + 1))))
        owd.append(sub(c("r2_t", mid, False, tR(k + 1)), c("r2_t", mid, True, tF(k), tR(k + 1))))
    m["o1_pre"], m["o1_post"], m["o1_width"] = mn(op), mn(oq), mn(owd)
    return m


def checks_tim(m, fsk):
    T = 1.0 / FSS[fsk]

    def ge(v, lim):
        return v is not None and v >= lim

    return dict(
        g_min=(m["g_min"], ge(m["g_min"], LIM["g_min"])),
        g50_max=(m["g50_max"], m["g50_max"] is not None and m["g50_max"] <= 0.025 * T),
        t_half_min=(m["t_half_min"], ge(m["t_half_min"], 0.45 * T)),
        eb_min=(m["eb_min"], ge(m["eb_min"], LIM["eb_min"])),
        ls_edge_max=(m["ls_edge"], m["ls_edge"] is not None and m["ls_edge"] <= LIM["ls_edge_max"]),
        glitch_s=(len(m["glitch_s"]), not m["glitch_s"]),
        glitch_d=(len(m["glitch_d"]), not m["glitch_d"]),
        rule13=(mn([m["r13_pre"], m["r13_post"]]), ge(m["r13_pre"], 0) and ge(m["r13_post"], 0)),
        strobe=(mn([m["strobe_pre"], m["strobe_post"]]), ge(m["strobe_pre"], 0) and ge(m["strobe_post"], 0)),
        order1=(mn([m["o1_pre"], m["o1_post"]]), ge(m["o1_pre"], 0) and ge(m["o1_post"], 0)
                and ge(m["o1_width"], LIM["r2_width"])))


def metrics_inj(d, kind, pts, corner):
    T = 1.0 / FSS["4M"]
    t = d[:, 0]
    out_r, out_i = d[:, 1] - d[:, 2], d[:, 3] - d[:, 4]
    err = []
    for j in range(len(pts)):
        tm = T0 + (j + 2) * T + T / 2 + 20e-9
        err.append(float(np.interp(tm, t, out_r - out_i)) / (CS / CINT))   # input-referred, V
    err = np.array(err)
    x = np.array([p[1] for p in pts]) if kind == "injdm" else np.array([p[0] for p in pts])
    a, b = np.polyfit(x, err, 1)
    res = err - (a * x + b)
    m = dict(err_uV=[float(e * 1e6) for e in err], x=[float(v) for v in x], slope=float(a), offset_uV=float(b * 1e6))
    if kind == "injdm":
        m["inl_ppm"] = float(np.abs(res).max() / (2 * VREF) * 1e6)
    else:
        m["eps_inj"] = float(abs(a))
        m["cm_resid_uV"] = float(np.abs(res).max() * 1e6)
    return m


def metrics_settle(d, corner):
    T = 1.0 / FSS["4M"]
    t = d[:, 0]
    va = CORNERS[corner][2]
    m = {}
    taus = []
    for j, (s, v) in enumerate((("a", VMAX), ("b", 1.65))):
        for k in (4, 5):
            ton = cross(t, d[:, 3], va / 2, True, T0 + k * T + T / 2 - 2e-9, T0 + k * T + T / 2 + 40e-9)
            toff = cross(t, d[:, 3], va / 2, False, T0 + (k + 1) * T - 2e-9, T0 + (k + 1) * T + 40e-9)
            if ton is None or toff is None:
                taus.append(None)
                continue
            e = abs(float(np.interp(toff, t, d[:, 1 + j])) - v)
            taus.append((toff - ton) / np.log(v / max(e, 1e-15)))
            m[f"err_{s}{k}_V"] = e
    m["tau_eff"] = mx(taus)
    return m


def metrics_leak(d, corner):
    leak = -d[:, 2]           # into the vg node (+ charges vg up)
    m = dict(leak_max_abs=float(np.abs(leak).max()), leak_at_018=float(leak[0]), leak_at_222=float(leak[-1]),
             leak_span=float(leak.max() - leak.min()))
    m["sign"] = "+" if leak.mean() > 0 else "-"
    c1 = -d[:, 3]
    m["c1_share"] = float(np.abs(c1).max())
    m["c1_sign"] = "+" if c1.mean() > 0 else "-"
    m["sg_lim"] = LEAK_ROW[corner] - m["c1_share"]          # D78 re-split: row minus C1's measured share
    return m


def metrics_ramp(d, vecs, kind, corner):
    T = 1.0 / FSS["4M"]
    t = d[:, 0]
    w = {v: d[:, 1 + j] for j, v in enumerate(vecs)}
    vdd, vdl = w["v(vdd)"], w["v(vdl)"]
    va = CORNERS[corner][2]
    nets = [v for v in vecs if v.endswith("_t)") and "r2" not in v]   # int2 reset closed is a safe state
    m = {}
    mask = (vdl < 1.0) & (vdd >= 1.5)
    if mask.any():
        m["safe_on_max"] = float(max(w[n][mask].max() for n in nets))
        m["safe_isl_margin"] = float((w["v(isl)"][mask] - 0.8 * vdd[mask]).min())
        m["safe_window_us"] = float(mask.sum() and (t[mask][-1] - t[mask][0]) * 1e6)
        m["safe_net_max"] = {n: float(w[n][mask].max()) for n in nets + ["v(pwrok)"]}
    else:
        m["safe_on_max"] = m["safe_isl_margin"] = None
        m["safe_window_us"] = 0.0
    # crowbar: charge through a VIN switch and a DAC switch at the same time, per fs period
    cb = np.minimum(np.abs(w["i(Vaip)"]), np.abs(w["i(Vadp)"])) + np.minimum(np.abs(w["i(Vain)"]), np.abs(w["i(Vadn)"]))
    q = np.concatenate([[0.0], np.cumsum(0.5 * (cb[1:] + cb[:-1]) * np.diff(t))])
    qT = np.interp(t + T, t, q, right=q[-1]) - q
    m["crowbar_q_max"] = float(qT.max())
    m["crowbar_t_us"] = float(t[int(np.argmax(qT))] * 1e6)
    v18 = np.maximum.reduce([w["v(chlp)"], w["v(chln)"], w["v(phc)"]])
    m["v18_over_max"] = float((v18 - vdl).max())
    m["v18_abs_max"] = float(v18.max())
    m["vref_well_i_max"] = float(np.abs(w["i(Vrp)"]).max())
    end = t >= t[-1] - 2e-6
    il = w["v(il_t)"][end]
    m["rel_pwrok"] = float(w["v(pwrok)"][end].min() / va)
    m["rel_il_toggles"] = int(np.sum((il[:-1] < 0.5 * va) & (il[1:] >= 0.5 * va)))
    m["rel_isl_end"] = float(w["v(isl)"][-1])
    return m


def checks_ramp(m, kind, corner):
    va = CORNERS[corner][2]
    if kind == "rampa":
        safe = m["safe_on_max"] is not None and m["safe_on_max"] <= LIM["safe_v"] and m["safe_isl_margin"] >= 0
    else:
        safe = True        # order b: VDPWR is up before VAPWR, the window is empty by construction
    rel = m["rel_pwrok"] >= 0.9 and m["rel_il_toggles"] >= 4 and m["rel_isl_end"] <= 0.1 * va
    return dict(safe=(m["safe_on_max"], safe), crowbar=(m["crowbar_q_max"], m["crowbar_q_max"] <= LIM["crowbar_q"]),
                stress=(m["v18_over_max"], m["v18_over_max"] <= LIM["v18_over"]), release=(m["rel_il_toggles"], rel))


def checks(kind, corner, fsk, m):
    if kind == "ron":
        return {k: (v["ron_max"], v["ron_max"] is not None and v["ron_max"] <= v["lim"]) for k, v in m.items()}
    if kind == "tim":
        return checks_tim(m, fsk)
    if kind == "injdm":
        return dict(inl=(m["inl_ppm"], m["inl_ppm"] <= LIM["inl_ppm"]))
    if kind == "injcm":
        return dict(eps_inj=(m["eps_inj"], m["eps_inj"] <= LIM["eps_inj"]))
    if kind == "settle":
        return dict(tau_in=(m["tau_eff"], m["tau_eff"] is not None and m["tau_eff"] <= LIM["tau_in"]))
    if kind == "leak":
        return dict(leak=(m["leak_max_abs"], m["leak_max_abs"] <= m["sg_lim"]))
    return checks_ramp(m, kind, corner)


# ---------------------------------------------------------------- run / report
def run(kind, corner, fsk, mut, out):
    os.makedirs(out, exist_ok=True)
    tag = f"{kind}_{corner}_{fsk}_{mut}"
    csv = tag + ".csv"
    cp = os.path.join(out, csv)
    if os.path.exists(cp):
        os.remove(cp)
    res = dict(kind=kind, corner=corner, fs=fsk, mut=mut, cond=CORNERS[corner], ok=False, err=None, m={})
    try:
        pts = None
        if kind == "ron":
            deck, vecs, stop = deck_ron(corner, mut, csv)
        elif kind == "tim":
            deck, vecs, stop = deck_tim(corner, fsk, mut, csv)
        elif kind in ("injdm", "injcm"):
            deck, vecs, stop, pts = deck_inj(kind, corner, mut, csv)
        elif kind == "settle":
            deck, vecs, stop = deck_settle(corner, mut, csv)
        elif kind == "leak":
            deck, vecs, stop = deck_leak(corner, mut, csv)
        else:
            deck, vecs, stop = deck_ramp(kind, corner, mut, csv)
        rc, bad = spice(deck, tag, out)
        if rc or bad or not os.path.exists(cp):
            raise RuntimeError(f"ngspice rc={rc} bad={bad[:3]} csv={os.path.exists(cp)}")
        d = np.loadtxt(cp, skiprows=1)
        os.remove(cp)
        if abs(d[-1, 0] - stop) > 1e-4 * stop:
            raise RuntimeError(f"run ended at {d[-1, 0]:g}, requested {stop:g}")
        if kind == "ron":
            m = metrics_ron(d, corner, mut)
        elif kind == "tim":
            m = metrics_tim(d, vecs, corner, fsk, mut)
        elif pts is not None:
            m = metrics_inj(d, kind, pts, corner)
        elif kind == "settle":
            m = metrics_settle(d, corner)
        elif kind == "leak":
            m = metrics_leak(d, corner)
        else:
            m = metrics_ramp(d, vecs, kind, corner)
        res["m"] = m
        res["ck"] = {k: [v, bool(p)] for k, (v, p) in checks(kind, corner, fsk, m).items()}
        res["ok"] = True
    except Exception as e:
        res["err"] = repr(e)
    json.dump(res, open(os.path.join(out, tag + ".json"), "w"), indent=1, default=float)
    return res


def fmt(v):
    if v is None:
        return "MISSING"
    if isinstance(v, (int, np.integer)):
        return str(v)
    a = abs(v)
    if a == 0:
        return "0"
    if a < 1e-6 and a >= 1e-13:
        return f"{v * 1e9:.3g}n" if a >= 1e-10 else f"{v * 1e12:.3g}p" if a >= 1e-13 else f"{v:.3g}"
    return f"{v:.4g}"


def report(out):
    rows, fail, findings = {}, [], []
    for job in joblist():
        tag = "_".join(job)
        fn = os.path.join(out, tag + ".json")
        if not os.path.exists(fn):
            fail.append(f"missing {tag}")
            continue
        r = json.load(open(fn))
        if not r["ok"]:
            fail.append(f"error {tag}: {r['err']}")
            continue
        rows[job] = r
    L = ["# WO-54 C4b gate (generated by design/c4_sw/c4_tb.py report)", "",
         f"Limits: {json.dumps(LIM)}; Ron limits per switch: " +
         ", ".join(f"{k} {v[2]:.0f} ohm over {v[0]:.2f}..{v[1]:.2f} V" for k, v in RON.items()) +
         f"; leak row per vg node {LEAK_ROW}, Sg limit = row - C1 measured share (D78)", ""]
    for kind in ("ron", "tim", "injdm", "injcm", "settle", "leak", "rampa", "rampb"):
        sel = [(j, r) for j, r in rows.items() if j[0] == kind]
        if not sel:
            continue
        L += [f"## {kind}", ""]
        for j, r in sel:
            ck = r["ck"]
            bad = [n for n, (_, p) in ck.items() if not p]
            mut = j[3]
            if mut == "none":
                verdict = "PASS" if not bad else "FAIL: " + ",".join(bad)
                if bad:
                    findings.append(f"{'_'.join(j)}: FAIL {','.join(bad)}")
            else:
                tgt = BROKEN[mut][0]
                hit = (bad if kind == "ron" else [b for b in bad if b == tgt])
                if kind == "ron":
                    miss = [k for k in ck if k not in bad]
                    verdict = "REJECT on every switch row (good)" if not miss else f"NOT REJECTED on {miss}"
                    if miss:
                        fail.append(f"broken copy {mut}@{j[1]} not rejected on {miss}")
                else:
                    verdict = f"REJECT on {tgt} (good)" if hit else f"NOT REJECTED on {tgt}"
                    if not hit:
                        fail.append(f"broken copy {mut}@{j[1]} not rejected on {tgt}")
            cells = "; ".join(f"{n} {fmt(v)}{'' if p else ' X'}" for n, (v, p) in ck.items())
            info = ""
            m = r["m"]
            if kind == "tim":
                info = (f" | LS d {fmt(m['ls_delay_r'])}/{fmt(m['ls_delay_f'])} duty {fmt(m['ls_duty_err'])} edge(info) "
                        f"{fmt(m['edge_max_info'])} r13 {fmt(m['r13_pre'])}/{fmt(m['r13_post'])} strobe "
                        f"{fmt(m['strobe_pre'])}/{fmt(m['strobe_post'])} o1 {fmt(m['o1_pre'])}/{fmt(m['o1_post'])}/"
                        f"{fmt(m['o1_width'])} gs {m['glitch_s'][:2]} gd {m['glitch_d'][:2]}")
            elif kind in ("injdm", "injcm"):
                info = f" | offset {m['offset_uV']:.2f} uV, slope {m['slope']:.3e}"
            elif kind == "leak":
                info = f" | Sg lim {fmt(m['sg_lim'])} (C1 share {fmt(m['c1_share'])} sign {m['c1_sign']}); Sg sign {m['sign']}, at tp 0.18 {fmt(m['leak_at_018'])} A, at 2.22 {fmt(m['leak_at_222'])} A, span {fmt(m['leak_span'])} A"
            elif kind.startswith("ramp"):
                info = (f" | isl margin {fmt(m['safe_isl_margin'])} window {m['safe_window_us']:.2f} us, v18 abs "
                        f"{fmt(m['v18_abs_max'])}, VREF+ well current {fmt(m['vref_well_i_max'])} A, pwrok {m['rel_pwrok']:.2f}")
            L.append(f"- `{'_'.join(j)}` {r['cond']}: {cells} -> **{verdict}**{info}")
        L.append("")
    L += ["## Findings (good rows that FAIL)", ""] + ([f"- {f}" for f in findings] or ["- none"])
    L += ["", "## Problems (missing / errored jobs, broken copies not rejected)", ""] + ([f"- {f}" for f in fail] or ["- none"])
    open(os.path.join(out, "summary.md"), "w").write("\n".join(L) + "\n")
    json.dump({"_".join(j): r for j, r in rows.items()}, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print("\n".join(L))
    return 2 if fail else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "jobs":
        out = os.path.abspath(a[1])
        os.makedirs(out, exist_ok=True)
        me = os.path.abspath(__file__)
        sel = a[2] if len(a) > 2 else None
        with open(os.path.join(out, "jobs.txt"), "w") as f:
            for j in joblist():
                if sel is None or sel in "_".join(j):
                    f.write(f"python {me} run {' '.join(j)} {out}\n")
        print(len(joblist()), "jobs ->", os.path.join(out, "jobs.txt"))
    elif a and a[0] == "run":
        r = run(a[1], a[2], a[3], a[4], os.path.abspath(a[5]))
        print(r["ok"], r["err"], json.dumps(r.get("ck"), default=str))
        sys.exit(0 if r["ok"] else 1)
    elif a and a[0] == "report":
        sys.exit(report(os.path.abspath(a[1])))
    else:
        sys.exit(__doc__)
