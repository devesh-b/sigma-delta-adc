#!/usr/bin/env python3
"""C3 comparator netlist generator (WO-48, D74). Golden source of the c3_comp subckt.

    python netlist.py [mut]        # print the subckt (mut: one of sizes_draft.MUTS, or empty)

    .subckt c3_comp inp inn clk q qb vdd vss
        inp/inn : x2p / x2n (3.3 V domain, HV gates)      clk : strobe phiC (1.8 V, from C4; high = evaluate)
        q / qb  : buffered SR-latch outputs (1.8 V) to C9  q = 1 <=> inp > inn at the strobe; held through precharge

StrongARM: tail T (1.8 V) -> tl; input pair M1/M2 (HV) tl -> dp/dn; NMOS cross pair M3/M4 (sources on dp/dn);
PMOS cross pair M5/M6 to vdd; precharge R0..R3 (op, on, dp, dn) to vdd while clk low. Each of op/on drives two
inverters (symmetric load, LEARNINGS-pthomas), then a NAND SR latch (both inputs high in precharge = hold), then a
two-inverter output buffer per side driving the routed C9 net.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sizes_draft import SIZES, HVN, NF, PF  # noqa: E402

PORTS = ("inp", "inn", "clk", "q", "qb", "vdd", "vss")


def devices(sizes=SIZES, mut=""):
    """Device list: (name, model, d, g, s, b, params) with subckt-local node names."""
    s = {k: dict(v) for k, v in sizes.items()}
    if "starve" in mut:
        s["TAIL"] = dict(W=1.0, L=4.0, m=1)
    pair = NF if "in18" in mut else HVN
    D = [("T", NF, "tl", "clk", "vss", "vss", s["TAIL"]),
         ("M1", pair, "dp", "inp", "tl", "vss", s["IN"]),
         ("M2", pair, "dn", "inn", "tl", "vss", s["IN"]),
         ("M3", NF, "op", "on", "dp", "vss", s["LN"]),
         ("M4", NF, "on", "op", "dn", "vss", s["LN"]),
         ("M5", PF, "op", "on", "vdd", "vdd", s["LP"]),
         ("M6", PF, "on", "op", "vdd", "vdd", s["LP"])]
    for i, n in enumerate(("op", "on", "dp", "dn")):
        D.append((f"R{i}", PF, n, "clk", "vdd", "vdd", s["RS"]))

    def inv(tag, out, inp, kn, kp):
        return [(f"{tag}n", NF, out, inp, "vss", "vss", s[kn]), (f"{tag}p", PF, out, inp, "vdd", "vdd", s[kp])]

    if "nobuf" not in mut:
        for side, src in (("o", "op"), ("n", "on")):
            D += inv(f"B{side}1", f"{side}b1", src, "BN", "BP") + inv(f"B{side}2", f"{side}b2", f"{side}b1", "BN", "BP")
        sa, sb = ("ob2", "nb2")
    else:
        sa, sb = ("op", "on")          # broken copy: latch gates load the regeneration nodes
    if "qswap" in mut:
        sa, sb = sb, sa
    if "nolatch" in mut:
        lq, lqb = ("nb2", "ob2")       # broken copy: transparent, both high in precharge
    else:
        lq, lqb = ("ql", "qlb")
        # NAND SR latch: ql = NAND(sa, qlb), qlb = NAND(sb, ql). inp > inn -> op falls -> ob2 falls -> ql = 1.
        for out, a, b, tag in (("ql", sa, "qlb", "q"), ("qlb", sb, "ql", "b")):
            D += [(f"S{tag}1", PF, out, a, "vdd", "vdd", s["SP"]),
                  (f"S{tag}2", PF, out, b, "vdd", "vdd", s["SP"]),
                  (f"S{tag}3", NF, out, a, f"s{tag}", "vss", s["SN"]),
                  (f"S{tag}4", NF, f"s{tag}", b, "vss", "vss", s["SN"])]
    D += inv("Oq1", "qo1", lq, "O1N", "O1P") + inv("Oq2", "q", "qo1", "O2N", "O2P")
    D += inv("Ob1", "qbo1", lqb, "O1N", "O1P") + inv("Ob2", "qb", "qbo1", "O2N", "O2P")
    return D


def comp_subckt(sizes=SIZES, mut="", name="c3_comp"):
    L = [f".subckt {name} " + " ".join(PORTS)]
    for (n, model, d, g, s_, b, p) in devices(sizes, mut):
        L.append(f"X{n} {d} {g} {s_} {b} {model} W={p['W']} L={p['L']} nf=1 m={p['m']}")
    L.append(f".ends {name}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    print(comp_subckt(mut=sys.argv[1] if len(sys.argv) > 1 else ""))
