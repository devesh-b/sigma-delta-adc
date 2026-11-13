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
from sizes_draft import SIZES, HVN, HVP, NF, PF  # noqa: E402

PORTS = ("inp", "inn", "clk", "q", "qb", "vdd", "vss")


def devices(sizes=SIZES, mut=""):
    """Device list: (name, model, d, g, s, b, params) with subckt-local node names."""
    s = {k: dict(v) for k, v in sizes.items()}
    if "starve" in mut:   # 64x less W/L than the HV tail
        s["TAIL"] = dict(W=1.25, L=2.0, m=1)
    pair = NF if "in18" in mut else HVN
    # WO-51 (T8): HV cascode (gate = vdd) between each pair drain (ap/an) and dp/dn. When x2 moves while the strobe
    # is high and the pair device is off, its Cgd kick lands on ap/an (HV), not on the floating 1.8 V node dp/dn
    # (WO-48/51: dp reached 2.35-2.44 V, clamped only by the precharge PMOS drain-body diode). "nocas" = rev b.
    # WO-56 (rev d): (1) ap/an precharged to vdd by HV PMOS (gate = clk). In rev c they were only charged through the
    # cascode to vdd - VT,HV, slowly in subthreshold, so after a big decision ap/an started the next strobe unequal:
    # memory (T7/T2 failed every cycle after a +-0.3 V one). (2) Tail is HV: tl is the common source of the pair and
    # floats up with ap/an (rev c: tail Vds 2.38-2.55 V); with an HV tail tl touches only HV devices.
    # "revc" = WO-51 netlist (cascode, 1.8 V tail, no ap/an precharge), "nocas" = rev b; both info copies.
    tail = NF if ("nocas" in mut or "revc" in mut) else HVN
    tsz = s["TAIL"] if tail == HVN else s["TAIL18"]
    # WO-65 (T5 broken copies on rev d): "nohvc" = rev d with the HV cascode K1/K2 and the ap/an precharge removed,
    # pair drains straight on dp/dn (HV tail kept); "nopa" = rev d with only the ap/an precharge P1/P2 removed.
    if "nocas" in mut or "nohvc" in mut:
        D = [("T", tail, "tl", "clk", "vss", "vss", tsz),
             ("M1", pair, "dp", "inp", "tl", "vss", s["IN"]),
             ("M2", pair, "dn", "inn", "tl", "vss", s["IN"])]
    else:
        D = [("T", tail, "tl", "clk", "vss", "vss", tsz),
             ("M1", pair, "ap", "inp", "tl", "vss", s["IN"]),
             ("M2", pair, "an", "inn", "tl", "vss", s["IN"]),
             ("K1", HVN, "dp", "vdd", "ap", "vss", s["CAS"]),
             ("K2", HVN, "dn", "vdd", "an", "vss", s["CAS"])]
        if "revc" not in mut and "nopa" not in mut:
            D += [("P1", HVP, "ap", "clk", "vdd", "vdd", s["PA"]),
                  ("P2", HVP, "an", "clk", "vdd", "vdd", s["PA"])]
    D += [
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
        # WO-68 (rev e): stack-node clamp S{tag}5, sq/sb -> vss, gate = the complement of the set input (ob1/nb1).
        # Rev d: on a flip, ql falls while nb2 is low, so sb floats (Sb3, Sb4 off) and takes Sb4's channel charge:
        # -0.345 V (junction-clamped) for the whole strobe phase, Vds(Sb3) = qlb - sb = 2.32 V. The clamp holds the
        # node at vss exactly while the top device is off, so the logic is unchanged (pull-down needs the set input
        # high, then the clamp is off). "noclamp" = rev d latch (T8 info copy).
        cpl = {"ob2": "ob1", "nb2": "nb1"}
        for out, a, b, tag in (("ql", sa, "qlb", "q"), ("qlb", sb, "ql", "b")):
            D += [(f"S{tag}1", PF, out, a, "vdd", "vdd", s["SP"]),
                  (f"S{tag}2", PF, out, b, "vdd", "vdd", s["SP"]),
                  (f"S{tag}3", NF, out, a, f"s{tag}", "vss", s["SN"]),
                  (f"S{tag}4", NF, f"s{tag}", b, "vss", "vss", s["SN"])]
            if a in cpl and "noclamp" not in mut:
                D.append((f"S{tag}5", NF, f"s{tag}", cpl[a], "vss", "vss", s["SC"]))
    D += inv("Oq1", "qo1", lq, "O1N", "O1P") + inv("Oq2", "q", "qo1", "O2N", "O2P")
    D += inv("Ob1", "qbo1", lqb, "O1N", "O1P") + inv("Ob2", "qb", "qbo1", "O2N", "O2P")
    return D


def comp_subckt(sizes=SIZES, mut="", name="c3_comp", dvt=None):
    """dvt: {device name: volts} -> an ideal source in series with that gate, V(gate) = V(net) - dv, i.e. the
    device's VT raised by dv (WO-51 per-device offset sensitivity; labelled probe, not part of the design)."""
    L = [f".subckt {name} " + " ".join(PORTS)]
    for (n, model, d, g, s_, b, p) in devices(sizes, mut):
        if dvt and n in dvt:
            gx = f"gx_{n.lower()}"
            L.append(f"VDVT{n} {g} {gx} {dvt[n]:.6e}")
            g = gx
        L.append(f"X{n} {d} {g} {s_} {b} {model} W={p['W']} L={p['L']} nf=1 m={p['m']}")
    L.append(f".ends {name}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    print(comp_subckt(mut=sys.argv[1] if len(sys.argv) > 1 else ""))
