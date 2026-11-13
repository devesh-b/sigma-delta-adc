#!/usr/bin/env python3
"""C4b netlist (WO-54): switch sizes, the phase generator with level shifters and the VDPWR detector.

    python netlist.py [OUT.spice]     # writes the c4_gen subckt (default mut, stdout if no file)

Subckt `c4_gen` (all logic in sky130_fd_sc_hvl cells, VAPWR domain; DESIGN.md sections 5-7):

  .subckt c4_gen vdd vdl vss fs y swap short chop rst <x>_t <x>_c (x in PH) isl rstb chp chn chlp chln phc pwrok fsh

  vdd / vdl        VAPWR (3.3 V) / VDPWR (1.8 V)
  fs y swap short chop rst   1.8 V inputs from C9 (bit clock, DAC bit, sys-chop swap, internal short, OTA-chop state,
                   rst_analog). Each crosses up through lsbuflv2hv_clkiso_hlkg_3 with SLEEP_B = pwrok (D76).
  <x>_t / <x>_c    3.3 V phase nets, true (NMOS gates) and complement (PMOS gates), x in PH:
                   ie / il  integrate early / late (C1 ph1 = il), se / sl  sample early / late (C1 ph2 = sl),
                   pas / swp / sho  = sl . pass / swap / short  (merged input switch #1, m1 rule: controls change
                   only on the fs rising edge, i.e. while sl is off),
                   dh / dl  = il . y / il . not y  (DAC #2 and Ck2 DAC #10)
  isl, rstb        island shunt (high = closed) = rst OR NOT pwrok; C1 output clamp rstb = NOT isl
  chp, chn         OTA input chopper (3.3 V), retimed: latched in the S->I gap (NOR(sl, ie)), break-before-make
  chlp, chln       fold chopper (1.8 V) = chp / chn through lsbufhv2lv_1
  phc              comparator strobe (1.8 V): se delayed by K_S inverters, through lsbufhv2lv_1 (m4: counted in C7)
  pwrok            VDPWR-present detector output (3.3 V): HV NMOS gated by VDPWR against a long PMOS load
  fsh              fs after its level shifter (probe for the LS rows)

When pwrok is low the generator NANDs see 0 on both inputs, so every phase is off (sampling, DAC, top short, vg),
the islands are closed and the output clamps are on; the chopper latch is transparent and parks at the isolated
LS value. Order 1 (rst2_o1, Ck2 rest in order 1) is a placeholder pending WO-53 (D76): not generated here.

mut is a '+'-joined token list (broken copies used by c4_tb.py):
  overlap   feedback chains removed (phases = fs / not fs)       gbig      gap chain x4 (g ~ 0.05/fs)
  noearly   late phase = early phase                            edge1     final drivers inv_1 instead of inv_8
  lsload    +1 pF on the fs LS output                           wrongstrobe  strobe taken from ie (phase I)
  rawchop   chopper not latched (C9 edge passes straight)       nodet     detector removed (pwrok tied high)
  hvfold    fold-chopper clocks from 3.3 V inverters (no hv2lv)  plainls   lsbuflv2hv_1 without SLEEP_B
  o1early   rst2_o1 not gated by the comparator decision (starts with se, overlaps the strobe)
Order 1 (WO-53 passed, coordinator 2026-11-13): comparator always on x2, int2 as follower with rst2_o1 = order 1 AND
se AND dec (inputs `order` high = order 2, `dec` = C3 decision-done NAND(q, qb), 1.8 V). Nets kh / kl / k0 / r2 are
the Ck2 DAC, Ck2 rest and int2 reset (C2 switch) gates.
"""
import os
import sys

PDK = os.path.join(os.environ.get("PDK_ROOT", "/home/mempool/.ciel"), os.environ.get("PDK", "sky130A"))
LIB = PDK + "/libs.tech/ngspice/sky130.lib.spice"
HVL = PDK + "/libs.ref/sky130_fd_sc_hvl/spice/sky130_fd_sc_hvl.spice"
PRE = "sky130_fd_pr__"
HVN, HVP = "nfet_g5v0d10v5", "pfet_g5v0d10v5"
DIFF_EXT = 0.29
L_SW = 0.5

# Switch sizes (W_n, W_p) um at L 0.5; W_p = 0 means NMOS only. DESIGN.md 2/3, REVIEW-C4a m3 / m7, D76.
SW = dict(
    sin=(12.0, 36.0),    # 1  input / swap / short TG (merged), on pas / swp / sho
    sdh=(4.0, 12.0),     # 2  DAC to VREF+ (m7: 4/12)
    sdl=(4.0, 0.0),      # 2  DAC to VREF- (m7: NMOS only, VREF- ~ 0 V)
    stp=(2.0, 4.0),      # 3/8 D12 top-plate short, <= 2/4 (injection rule, DESIGN.md 4.2)
    sg=(5.0, 0.0),       # 4/9 vg connect, NMOS only, W 4-6 (m3, D76)
    s2in=(4.0, 12.0),    # 6  Cs2 sample, on sl
    s2cm=(4.0, 12.0),    # 7  Cs2 plate short (CL-2), on il (m6)
    skh=(4.0, 12.0),     # 10 Ck2 DAC to VREF+
    skl=(4.0, 0.0),      # 10 Ck2 DAC to VREF- (NMOS only)
    sk0=(4.0, 12.0),     # 11 Ck2 rest p<->n short, on sl (m6)
)

# Generator knobs (C4a spot values, revised per REVIEW-C4a M2: early->late ~1.5 ns at ff/-40)
K_G, C_G = 4, 55e-15     # gap chain (spot 70 fF; the gated nets add ~ one stage on the 'on' side)
K_E, C_E = 2, 100e-15    # early -> late chain (spot 40 fF gave 0.70 ns at ff/-40)
K_S, C_S = 2, 40e-15     # strobe delay after se (C3: fire ~ 1 ns after the se rising edge)
DET = dict(p=(0.42, 20.0), n=(2.0, 0.5))   # VDPWR detector: PMOS load W/L, NMOS sense W/L

PH = ("ie", "il", "se", "sl", "pas", "swp", "sho", "dh", "dl", "kh", "kl", "k0", "r2")
GATED = dict(pas=("sl", "selp"), swp=("sl", "sels"), sho=("sl", "shorth"), dh=("il", "yh"), dl=("il", "yb"),
             kh=("ilo", "yh"), kl=("ilo", "yb"))
PORTS = ("vdd vdl vss fs y swap short chop rst order dec " + " ".join(f"{x}_t {x}_c" for x in PH)
         + " isl rstb chp chn chlp chln phc pwrok fsh")


def mos(name, d, g, s, b, dev, w, l):
    return (f"X{name} {d} {g} {s} {b} {PRE}{dev} w={w:g} l={l:g} m=1 ad={w * DIFF_EXT:.4g} as={w * DIFF_EXT:.4g} "
            f"pd={2 * (w + DIFF_EXT):.4g} ps={2 * (w + DIFF_EXT):.4g}")


def switch(name, a, b, gt, gc, key=None, wn=None, wp=None, pdev_only=False):
    """3.3 V switch a <-> b. TG: NMOS gate gt (bulk 0), PMOS gate gc (bulk vdd). NMOS-only if W_p = 0.
    pdev_only: replace the device set by a single PMOS of W_n on gate gc (broken copy 'onetype' for NMOS-only rows)."""
    if key:
        wn, wp = SW[key]
    if pdev_only:
        return [mos(name + "p", a, gc, b, "vdd", HVP, wn, L_SW)]
    out = [mos(name + "n", a, gt, b, "0", HVN, wn, L_SW)]
    if wp:
        out.append(mos(name + "p", a, gc, b, "vdd", HVP, wp, L_SW))
    return out


def inv(nm, a, y, sz=1):
    return f"X{nm} {a} vss vss vdd vdd {y} sky130_fd_sc_hvl__inv_{sz}"


def nand(nm, a, b, y):
    return f"X{nm} {a} {b} vss vss vdd vdd {y} sky130_fd_sc_hvl__nand2_1"


def nor(nm, a, b, y):
    return f"X{nm} {a} {b} vss vss vdd vdd {y} sky130_fd_sc_hvl__nor2_1"


def latch(nm, d, g, q):
    return f"X{nm} {d} {g} vss vss vdd vdd {q} sky130_fd_sc_hvl__dlxtp_1"


def ls_up(nm, a, y, iso):
    if iso:
        return f"X{nm} {a} pwrok vdl vss vss vdd vdd {y} sky130_fd_sc_hvl__lsbuflv2hv_clkiso_hlkg_3"
    return f"X{nm} {a} vdl vss vss vdd vdd {y} sky130_fd_sc_hvl__lsbuflv2hv_1"


def ls_dn(nm, a, y):
    return f"X{nm} {a} vdl vss vss vdd vdd {y} sky130_fd_sc_hvl__lsbufhv2lv_1"


def chain(pfx, a, y, k, cap):
    out, prev = [], a
    for i in range(k):
        nxt = y if i == k - 1 else f"{pfx}{i}"
        out += [inv(f"{pfx}i{i}", prev, nxt), f"C{pfx}{i} {nxt} vss {cap:g}"]
        prev = nxt
    return out


def toks(mut):
    return set(mut.split("+")) if mut and mut != "none" else set()


def gen(mut=None, name="c4_gen"):
    t = toks(mut)
    kg = K_G * (4 if "gbig" in t else 1)
    fin = 1 if "edge1" in t else 8
    L = [f"* C4 phase generator (design/c4_sw/netlist.py, mut={mut}) - generated, do not edit", f".subckt {name} {PORTS}"]
    # VDPWR-present detector (D76): dn high while VDPWR is missing -> pwrok low
    if "nodet" in t:
        L += ["Rpk pwrok vdd 1", "Rpkb pwrokb vss 1"]
    else:
        L += [mos("mdp", "dn", "vss", "vdd", "vdd", HVP, *DET["p"]), mos("mdn", "dn", "vdl", "vss", "vss", HVN, *DET["n"]),
              inv("dt1", "dn", "dt1"), inv("dt2", "dt1", "pwrokb"), inv("dt3", "pwrokb", "pwrok", 2)]
    # WO-54 smoke: lsbuflv2hv_clkiso_hlkg_3 holds X high with SLEEP_B low and does not pass the clock / stalls the
    # transient with SLEEP_B high in the PDK spice; default is lsbuflv2hv_1 with the pwrok gating behind it
    # (token isols = the D76 isolation cell, for the record)
    iso = "isols" in t
    for s in ("fs", "y", "swap", "short", "chop", "rst", "order", "dec"):
        L.append(ls_up(f"ls_{s}", s, s + "h", iso))
    if "lsload" in t:
        L.append("Cls fsh vss 1p")
    # fs gated by pwrok: both NAND inputs low while pwrok is low -> all phases off
    L += [inv("fsb", "fsh", "fshb"), nor("fsg", "fshb", "pwrokb", "fsg"), nor("fsbg", "fsh", "pwrokb", "fsbg")]
    if "overlap" in t:
        sfb, ifb = "vdd", "vdd"
    else:
        sfb, ifb = "sfb", "ifb"
        L += [inv("sli", "sl", "slb")] + chain("cs", "slb", "sfb", kg, C_G)
        L += [inv("ili", "il", "ilb")] + chain("ci", "ilb", "ifb", kg, C_G)
    L += [nand("a1", "fsg", sfb, "a1"), inv("ie", "a1", "ie"), nand("a2", "fsbg", ifb, "a2"), inv("se", "a2", "se")]
    if "noearly" in t:
        L += [nand("il", "a1", "vdd", "il"), nand("sl", "a2", "vdd", "sl")]
    else:
        L += chain("e1", "a1", "a1e", K_E, C_E) + [nand("il", "a1", "a1e", "il")]
        L += chain("e2", "a2", "a2e", K_E, C_E) + [nand("sl", "a2", "a2e", "sl")]
    # controls (3.3 V): pass = NOT swap AND NOT short, swap = swap AND NOT short, short
    L += [inv("swb", "swaph", "swapb"), inv("yb", "yh", "yb"),
          nor("selp", "swaph", "shorth", "selp"), nor("sels", "swapb", "shorth", "sels")]
    # order (high = order 2): Ck2 DAC on il . order (kh / kl); Ck2 rest short k0 = sl OR NOT order (m6; held in
    # order 1); int2 reset r2 = rst OR (order 1 AND se AND comparator decided): rst2_o1 late in phase S, after the
    # strobe decision (dec = NAND(q, qb) from C3), off with se, i.e. first thing in the S->I transition (WO-53 / D76)
    L += [nand("gilo", "il", "orderh", "nilo"), inv("ilo", "nilo", "ilo"), inv("ordb", "orderh", "orderb"),
          nor("gk0", "sl", "orderb", "nk0"),
          nand("go1", "se", "vdd" if "o1early" in t else "dech", "no1"), nor("o1", "no1", "orderh", "o1"),
          nor("gr2", "o1", "rsth", "nr2")]
    for x, (ph, sel) in GATED.items():
        L.append(nand("g" + x, ph, sel, "n" + x))
    # drivers: ungated true 2 stages / complement 3; gated (from the NAND = NOT x) true 3 / complement 2
    for x in PH:
        if x in GATED or x in ("k0", "r2"):
            n = "n" + x
            L += [inv(x + "b0", n, x + "q"), inv(x + "b1", x + "q", x + "m", 2), inv(x + "b2", x + "m", x + "_t", fin),
                  inv(x + "c1", n, x + "k", 2), inv(x + "c2", x + "k", x + "_c", fin)]
        else:
            L += [inv(x + "b1", x, x + "m", 2), inv(x + "b2", x + "m", x + "_t", fin),
                  inv(x + "c0", x, x + "n"), inv(x + "c1", x + "n", x + "k", 2), inv(x + "c2", x + "k", x + "_c", fin)]
    # OTA chopper (rule 13): latch transparent in the gaps (sl and ie both off), cross-coupled NOR break-before-make
    L.append(nor("gch", "sl", "ie", "gch"))
    cq = "choph" if "rawchop" in t else "cq"
    if "rawchop" not in t:
        L.append(latch("lch", "choph", "gch", "cq"))
    L += [inv("cqb", cq, "cqb"), nor("bp", "cqb", "chni", "chpi"), nor("bn", cq, "chpi", "chni"),
          inv("op1", "chpi", "op1", 2), inv("op2", "op1", "chp", 4), inv("on1", "chni", "on1", 2), inv("on2", "on1", "chn", 4)]
    if "hvfold" in t:
        L += [inv("fh1", "chp", "fh1"), inv("fh2", "fh1", "chlp"), inv("fh3", "chn", "fh3"), inv("fh4", "fh3", "chln")]
    else:
        L += [ls_dn("lfp", "chp", "chlp"), ls_dn("lfn", "chn", "chln")]
    # comparator strobe (D74): from the se rising edge (wrongstrobe: from ie), down to 1.8 V
    L += chain("st", "ie" if "wrongstrobe" in t else "se", "phch", K_S, C_S) + [ls_dn("lst", "phch", "phc")]
    # islands / output clamp: isl = rst OR NOT pwrok
    L += [inv("rb", "rsth", "rstbh"), nand("gisl", "rstbh", "pwrok", "isli"),
          inv("is1", "isli", "is1", 2), inv("is2", "is1", "isl", 4), inv("rs1", "isli", "rstb", 4)]
    L.append(f".ends {name}")
    return "\n".join(L) + "\n"


def inst(name="Xg", ins="fsin yin swin shin chin rsin ordin decin", sub="c4_gen"):
    return f"{name} vdd vdl 0 {ins} " + " ".join(f"{x}_t {x}_c" for x in PH) + f" isl rstb chp chn chlp chln phc pwrok fsh {sub}"


if __name__ == "__main__":
    txt = gen()
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(txt)
    else:
        sys.stdout.write(txt)
