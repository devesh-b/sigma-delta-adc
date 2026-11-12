#!/usr/bin/env python3
"""C3 comparator draft sizes + subckt (WO-44, stage 1 of the block recipe; DESIGN.md section 5).

Draft only: the golden netlist / xschem / full tb come in the next WO, after review.

Topology (DESIGN.md section 1): NMOS-input StrongARM on VDPWR (1.8 V). The input pair and the clocked
tail are 5 V devices (nfet_g5v0d10v5) because the gates sit on x2 (OTA2 output, 3.3 V domain, up to
VAPWR on overload / power-up; D40 limits 1.8 V devices to 1.98 V on every terminal pair) and the tail
drain follows the input to Vin - Vth while the tail is off. Everything else is 1.8 V core devices.
Regeneration nodes op/on -> two identical inverter buffers each -> cross-coupled NAND SR latch -> q/qb
(LEARNINGS-pthomas: buffers, not the latch gates, load the regeneration nodes, so the loading is
symmetric whatever the held state). q = 1 when inp > inn. clk high = evaluate, clk low = precharge.

    .subckt c3_comp inp inn clk q qb vdd vss
"""

PRE = "sky130_fd_pr__"
HVN, NF, PF = PRE + "nfet_g5v0d10v5", PRE + "nfet_01v8", PRE + "pfet_01v8"

# W, L in um; m = parallel instances. HV devices use 5 um unit fingers (width bins, as ttsky-sigma-delta).
SIZES = dict(
    IN=dict(W=5.0, L=0.5, m=4),    # HV input pair, per side: 10 um^2 (offset, DESIGN.md 3.1)
    TAIL=dict(W=5.0, L=0.5, m=4),  # HV clocked tail (gate = 1.8 V clk)
    LN=dict(W=2.0, L=0.3, m=1),    # 1.8 V cross-coupled NMOS (sources on dp/dn)
    LP=dict(W=2.0, L=0.3, m=1),    # 1.8 V cross-coupled PMOS
    RS=dict(W=1.0, L=0.15, m=1),   # 1.8 V PMOS precharge, 4x (op, on, dp, dn)
    BN=dict(W=0.5, L=0.15, m=1),   # buffer inverters (2 per side), NMOS
    BP=dict(W=1.0, L=0.15, m=1),   # buffer inverters, PMOS
    SN=dict(W=1.0, L=0.15, m=1),   # NAND SR latch NMOS
    SP=dict(W=1.0, L=0.15, m=1),   # NAND SR latch PMOS
)
C_Q_LOAD = 5e-15                   # retime-FF D input + wire (C9 boundary), tb load on q and qb

# Broken copies (spot tb, DESIGN.md section 6):
#   starve : tail 5/8 um x1 instead of 5/0.5 x4 (~64x less current): decision-time row must REJECT
#   qswap  : buffer outputs swapped into the latch (Q/QB swap, the pthomas bug): polarity row must REJECT
MUTS = ("starve", "qswap")


def _x(name, d, g, s, b, model, p):
    return f"X{name} {d} {g} {s} {b} {model} W={p['W']} L={p['L']} nf=1 m={p['m']}"


def comp_subckt(sizes=SIZES, mut=""):
    s = dict(sizes)
    if "starve" in mut:
        s["TAIL"] = dict(W=5.0, L=8.0, m=1)
    sa, sb = ("nb2", "ob2") if "qswap" in mut else ("ob2", "nb2")
    L = [".subckt c3_comp inp inn clk q qb vdd vss",
         _x("T", "tl", "clk", "vss", "vss", HVN, s["TAIL"]),
         _x("M1", "dp", "inp", "tl", "vss", HVN, s["IN"]),
         _x("M2", "dn", "inn", "tl", "vss", HVN, s["IN"]),
         _x("M3", "op", "on", "dp", "vss", NF, s["LN"]),
         _x("M4", "on", "op", "dn", "vss", NF, s["LN"]),
         _x("M5", "op", "on", "vdd", "vdd", PF, s["LP"]),
         _x("M6", "on", "op", "vdd", "vdd", PF, s["LP"])]
    for i, n in enumerate(("op", "on", "dp", "dn")):
        L.append(_x(f"R{i}", n, "clk", "vdd", "vdd", PF, s["RS"]))
    for side in ("o", "n"):
        src = "op" if side == "o" else "on"
        L += [_x(f"B{side}1n", f"{side}b1", src, "vss", "vss", NF, s["BN"]),
              _x(f"B{side}1p", f"{side}b1", src, "vdd", "vdd", PF, s["BP"]),
              _x(f"B{side}2n", f"{side}b2", f"{side}b1", "vss", "vss", NF, s["BN"]),
              _x(f"B{side}2p", f"{side}b2", f"{side}b1", "vdd", "vdd", PF, s["BP"])]
    # NAND SR latch: q = NAND(sa, qb), qb = NAND(sb, q). inp > inn -> op falls -> ob2 falls -> q = 1.
    for out, a, b, tag in (("q", sa, "qb", "q"), ("qb", sb, "q", "b")):
        L += [_x(f"S{tag}1", out, a, "vdd", "vdd", PF, s["SP"]),
              _x(f"S{tag}2", out, b, "vdd", "vdd", PF, s["SP"]),
              _x(f"S{tag}3", out, a, f"s{tag}", "vss", NF, s["SN"]),
              _x(f"S{tag}4", f"s{tag}", b, "vss", "vss", NF, s["SN"])]
    L.append(".ends c3_comp")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    import sys
    print(comp_subckt(mut=sys.argv[1] if len(sys.argv) > 1 else ""))
