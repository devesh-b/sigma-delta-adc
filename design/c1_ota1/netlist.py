#!/usr/bin/env python3
"""C1b OTA1 netlist generator (WO-24 item 2). Reads every size from sizes_draft.py; no sizes live here.

    python netlist.py [OUT.spice]          # writes the .subckt (default: stdout)

Subckt `ota1` (fully differential folded cascode, PMOS pfet_01v8 input pair, DESIGN.md section 1):

  .subckt ota1 vdd vss inp inn outp outn vicm vocm
  +            ibtp ibn ibp ivbnc ivbpc ivbl0
  +            chp chn chlp chln isl ph1 ph1b ph2 ph2b rstb

  inp/inn      vg island nodes (OTA inputs before the input chopper)
  ibtp, ibp    PMOS reference diodes (tail, fixed load): C6 SINKS the reference current out of these nodes
  ibn, ivbnc   NMOS reference / cascode-bias diodes: C6 SOURCES current into these nodes
  ivbpc, ivbl0 PMOS cascode-bias diode and V_BL0 replica: C6 SINKS current out of these nodes
  chp/chn      input chopper, 3.3 V level-shifted (C8), non-overlapping, nfet_g5v0d10v5 (CL-5)
  chlp/chln    fold chopper, 1.8 V clocks, nfet_01v8 4/0.15 (between fold node and NMOS cascode source)
  isl          island shunt (vg -> V_ICM), 3.3 V, high = closed (closed by default while rst / bias invalid, CL-5)
  ph1/ph1b     CMFB refresh phase (OTA1 integrate): Cr -> (V_OCM, V_BL0); 3.3 V and its complement (TG switches)
  ph2/ph2b     CMFB share phase (OTA1 hold): Cr -> (out, ctl)
  rstb         3.3 V, low = ctl clamped to V_BL0 (start-up, DESIGN.md 1.3)

Options (build(...)):
  cmfb="sc"    real SC CMFB: Cc, Cr, TG switches on ph1/ph2 (tier-1 transient, gate B)
  cmfb="dc"    DC equivalent for .op/.ac: Cc real; each Cr replaced by its averaged CM action, a resistor
               R = 1/(fs * 2 Cr) from ctl to the CM target  V(outcm) - V(vocm) + V(vbl0). CM only: the averaged
               differential charge of Cr is a per-phase settling load (it is in the transient, gate B), not a DC
               conductance, so it is not put on the differential output here (would read as a false A0 loss).
  mut="nc_short"  broken copy: NMOS cascode drain-source shorted (A0 collapses -> op/AC must REJECT)
  mut="ref_single" broken copy: single-finger 1:32 references (rev C) instead of composites (unit test; c1b_opac I_tail row)
  mut="kp_fixed"  broken copy (WO-25): old wiring, the vbpc / vbnc diodes fed from fixed I_REF ports (I_NC_design/16, x2
               boost) instead of the folded-branch replica (c1b_opac K_P row must REJECT at ff/-40)
  boost=True   builds the boost geometry: m_bpd / m_bpx banks at KP_BANK["boost"] fingers (the bank switch of C6/C8 is
               modelled as present / absent fingers; its Ron is neglected at < 2 uA)

WO-25 (D58) replica bias: node ivbpc carries the m_bpd diode bank, a tail replica (m_rt, gate ibtp, I_TAIL/32) and a sink
replica (m_rn, gate ibn, 2 x I_SINK/32): I(m_bpd) = (2 I_SINK - I_TAIL)/32 = I_NC/16 of the actual mirrors. The copy
bank m_bpx (gate ivbpc) feeds the same current to the vbnc diode m_bnd. ivbpc / ivbnc stay ports (observation, 0 A).

Every MOSFET carries ad/as/pd/ps (one finger of width WF per instance, multiplier m = fingers): diffusion extension
DIFF_EXT um, i.e. ad = as = WF*DIFF_EXT, pd = ps = 2*(WF + DIFF_EXT). The junction caps then come from the model.
Composite references (RC-M2): P parallel x S series unit fingers with a common gate, top drain = gate (diode).
W/L of the composite = P*WF/(S*L) = one finger, so the mirror ratio stays 1:M_mirror (1:32), with 16 x the area.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sizes_draft as S  # noqa: E402

DIFF_EXT = 0.29          # um, sky130 source/drain diffusion length past the gate (xschem sky130 symbol default)
PRE = "sky130_fd_pr__"


def geom(wf):
    return f"ad={wf * DIFF_EXT:.4g} as={wf * DIFF_EXT:.4g} pd={2 * (wf + DIFF_EXT):.4g} ps={2 * (wf + DIFF_EXT):.4g}"


def mos(name, d, g, s, b, dev, wf, l, m=1):
    return f"X{name} {d} {g} {s} {b} {PRE}{dev} w={wf:g} l={l:g} m={m} {geom(wf)}"


def dev(key, name, d, g, s, b, sizes):
    p = sizes[key]
    return mos(name, d, g, s, b, p["dev"], p["WF"], p["L"], p["M"])


def composite(name, top, gate, rail, bulk, p, P, Sn):
    """P parallel x Sn series unit fingers of size p (WF, L); diode: top drain tied to the gate by the caller."""
    out, nodes = [], [top] + [f"{name}_s{i}" for i in range(1, Sn)] + [rail]
    for i in range(Sn):
        out.append(mos(f"{name}_{i}", nodes[i], gate, nodes[i + 1], bulk, p["dev"], p["WF"], p["L"], P))
    return out


def ref(key, name, node, rail, bulk, sizes, mut):
    p = sizes[key]
    if mut == "ref_single":
        return [mos(name, node, node, rail, bulk, p["dev"], p["WF"], p["L"], 1)]
    return composite(name, node, node, rail, bulk, p, S.REF_COMPOSITE["P"], S.REF_COMPOSITE["S"])


def sw(name, a, b, g, kind, sizes=None):
    """Switches. kind: in (input chopper), isl (island shunt), fold (fold chopper), tg (CMFB transmission gate)."""
    if kind == "in":
        c = S.CHOP_SW["input"]
        return [mos(name, a, g, b, "vss", c["dev"], c["W"], c["L"])]
    if kind == "isl":
        c = S.CHOP_SW["island"]
        return [mos(name, a, g, b, "vss", c["dev"], c["W"], c["L"])]
    if kind == "fold":
        c = S.CHOP_SW["fold"]
        return [mos(name, a, g, b, "vss", c["dev"], c["W"], c["L"])]
    raise ValueError(kind)


def tg(name, a, b, g, gb):
    n, p = S.CMFB_SW["n"], S.CMFB_SW["p"]
    return [mos(name + "n", a, g, b, "vss", n["dev"], n["W"], n["L"]),
            mos(name + "p", a, gb, b, "vdd", p["dev"], p["W"], p["L"])]


PORTS = ("vdd vss inp inn outp outn vicm vocm ibtp ibn ibp ivbnc ivbpc ivbl0 "
         "chp chn chlp chln isl ph1 ph1b ph2 ph2b rstb")


def build(name="ota1", cmfb="sc", fs=4e6, mut=None, sizes=None, boost=False):
    z = {k: dict(v) for k, v in (sizes or S.SIZES).items()}
    L = [f"* OTA1 (generated by design/c1_ota1/netlist.py from sizes_draft.py; cmfb={cmfb}, mut={mut}) - do not edit",
         f".subckt {name} {PORTS}"]
    w = L.extend
    # bias: composite 1:32 references (tail, sink, fixed load) and the cascode-bias diodes (K-density, single finger)
    w(ref("m_tr", "mtr", "ibtp", "vdd", "vdd", z, mut))
    w(ref("m_nr", "mnr", "ibn", "vss", "vss", z, mut))
    w(ref("m_plr", "mplr", "ibp", "vdd", "vdd", z, mut))
    nb = S.KP_BANK["boost" if boost else "base"]
    bp, bx = z["m_bpd"], z["m_bpx"]
    w([mos("mbpd", "ivbpc", "ivbpc", "vdd", "vdd", bp["dev"], bp["WF"], bp["L"], nb),
       dev("m_bnd", "mbnd", "ivbnc", "ivbnc", "vss", "vss", z)])
    if mut != "kp_fixed":   # D58 replica of the folded branch (kp_fixed = old wiring: ports fed from fixed I_REF)
        w([dev("m_rt", "mrt", "ivbpc", "ibtp", "vdd", "vdd", z), dev("m_rn", "mrn", "ivbpc", "ibn", "vss", "vss", z),
           mos("mbpx", "ivbnc", "ivbpc", "vdd", "vdd", bx["dev"], bx["WF"], bx["L"], nb)])
    pc = z["m_plc"]   # V_BL0 replica: VBL0_SERIES m_plc fingers in series, diode
    w(composite("mbl0", "ivbl0", "ivbl0", "vdd", "vdd", pc, 1, S.VBL0_SERIES))
    # input chopper (vg side) and island shunts
    w(sw("Sci1", "inp", "gp", "chp", "in") + sw("Sci2", "inn", "gm", "chp", "in")
      + sw("Sci3", "inp", "gm", "chn", "in") + sw("Sci4", "inn", "gp", "chn", "in"))
    w(sw("Sisl1", "inp", "vicm", "isl", "isl") + sw("Sisl2", "inn", "vicm", "isl", "isl"))
    # core
    w([dev("m_t", "mt", "tail", "ibtp", "vdd", "vdd", z),
       dev("m_in", "min1", "da", "gp", "tail", "tail", z), dev("m_in", "min2", "db", "gm", "tail", "tail", z),
       dev("m_pp", "mpp1", "fa", "vss", "da", "da", z), dev("m_pp", "mpp2", "fb", "vss", "db", "db", z),
       dev("m_n", "mn1", "fa", "ibn", "vss", "vss", z), dev("m_n", "mn2", "fb", "ibn", "vss", "vss", z)])
    # fold chopper: fa/fb -> NMOS cascode sources xa/xb (chlp straight, chln crossed)
    w(sw("Scf1", "fa", "xa", "chlp", "fold") + sw("Scf2", "fb", "xb", "chlp", "fold")
      + sw("Scf3", "fa", "xb", "chln", "fold") + sw("Scf4", "fb", "xa", "chln", "fold"))
    w([dev("m_nc", "mnc1", "outn", "ivbnc", "xa", "vss", z), dev("m_nc", "mnc2", "outp", "ivbnc", "xb", "vss", z),
       dev("m_pc", "mpc1", "outn", "ivbpc", "sa", "sa", z), dev("m_pc", "mpc2", "outp", "ivbpc", "sb", "sb", z),
       dev("m_pl", "mpl1", "sa", "ibp", "vdd", "vdd", z), dev("m_pl", "mpl2", "sb", "ibp", "vdd", "vdd", z),
       dev("m_plc", "mplc1", "sa", "ctl", "vdd", "vdd", z), dev("m_plc", "mplc2", "sb", "ctl", "vdd", "vdd", z)])
    if mut == "nc_short":
        w(["Rmut1 outn xa 1", "Rmut2 outp xb 1"])
    if S.C_FOLD_EXTRA:
        w([f"Cfx1 fa vss {S.C_FOLD_EXTRA:g}", f"Cfx2 fb vss {S.C_FOLD_EXTRA:g}"])
    # CMFB
    cc, cr = S.C_CMFB_SENSE, S.C_CMFB_REFRESH
    w([f"Ccp outp ctl {cc:g}", f"Ccn outn ctl {cc:g}"])
    c = S.CTL_RST
    w([mos("mrst", "ctl", "rstb", "ivbl0", "vdd", c["dev"], c["W"], c["L"])])
    if cmfb == "sc":
        for s_, o in (("p", "outp"), ("n", "outn")):
            w([f"Cr{s_} ra{s_} rb{s_} {cr:g}"])
            w(tg(f"Sr1a{s_}", f"ra{s_}", "vocm", "ph1", "ph1b") + tg(f"Sr1b{s_}", f"rb{s_}", "ivbl0", "ph1", "ph1b")
              + tg(f"Sr2a{s_}", f"ra{s_}", o, "ph2", "ph2b") + tg(f"Sr2b{s_}", f"rb{s_}", "ctl", "ph2", "ph2b"))
    elif cmfb == "dc":
        r = 1.0 / (fs * 2 * cr)
        w([f"Bcmt cmt vss V = 0.5*(V(outp)+V(outn)) - V(vocm) + V(ivbl0)", f"Rcmeq cmt ctl {r:.6g}"])
    else:
        raise ValueError(cmfb)
    L.append(f".ends {name}")
    return "\n".join(L) + "\n"


def bias_currents(boost, mut=None):
    """Reference currents per port [A] (C6 ideal sources in the testbenches), base or boost (x BOOST x BOOST_SCALE),
    times REF_TRIM (D58). mut="kp_fixed": the old wiring, vbpc / vbnc fed with the fixed design current I_NC/16."""
    k = {"ibtp": "btp", "ibn": "bn", "ibp": "bp", "ivbnc": "vbnc", "ivbpc": "vbpc", "ivbl0": "vbl0"}
    m = S.BOOST if boost else 1.0
    out = {p: S.I_REF[r] * S.REF_TRIM.get(r, 1.0) * (m * S.BOOST_SCALE.get(r, 1.0) if boost else 1.0) for p, r in k.items()}
    if mut == "kp_fixed":
        out["ivbpc"] = out["ivbnc"] = m * S.I_NC / 16
    return out


SINK_PORTS = ("ibtp", "ibp", "ivbpc", "ivbl0")   # PMOS diodes: the source pulls current out of the node to ground


def count(text):
    """Device census of a generated subckt: {dev type: instances, 'fingers': sum m}."""
    out = {}
    for ln in text.splitlines():
        if ln.startswith("X") and PRE in ln:
            d = ln.split()[5].replace(PRE, "")
            out[d] = out.get(d, 0) + 1
    return out


if __name__ == "__main__":
    txt = build()
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(txt)
    else:
        sys.stdout.write(txt)
