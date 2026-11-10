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
  mut="ref_composite" broken copy (WO-26): the D58 4 x 4 series-parallel composite references (c1b_opac ratio row)
  mut="kp_fixed"  broken copy (WO-25): old wiring, the vbpc / vbnc diodes fed from fixed I_REF ports (I_NC_design/16, x2
               boost) instead of the folded-branch replica (c1b_opac K_P row must REJECT at ff/-40)
  boost=True   builds the boost geometry: m_bpd / m_bpx banks at KP_BANK["boost"] fingers (the bank switch of C6/C8 is
               modelled as present / absent fingers; its Ron is neglected at < 2 uA)

WO-25 (D58) replica bias: node ivbpc carries the m_bpd diode bank, a tail replica (m_rt, gate ibtp, I_TAIL/32) and a sink
replica (m_rn, gate ibn, 2 x I_SINK/32): I(m_bpd) = (2 I_SINK - I_TAIL)/32 = I_NC/16 of the actual mirrors. The copy
bank m_bpx (gate ivbpc) feeds the same current to the vbnc diode m_bnd. ivbpc / ivbnc stay ports (observation, 0 A).

WO-26 (D59): references are parallel-only unit fingers at 1:8 (one instance, m = M_mirror/8, same WF/L/bulk as the
mirror finger; V_BL0 replica = 1 m_plc unit finger), no trim. Replica: 2 tail + 4 sink unit fingers, the sink replica
cascoded by one m_nc unit finger (gate REPLICA_CASC_GATE = rcb: diode m_rcb fed by one m_pl finger, gate ibp) so its drain sits near the fold node. Bank switch in the
gate path: the boost-only fingers mbpds / mbpxs have their gates on gbk; TG Sbk gbk <-> ivbpc (closed in boost) and the
pull-up mbku gbk -> vdd (on in base). The static switch states are wired to the rails per build(boost=...).
WO-27 (D60): CM error amplifier (sizes_draft CM_AMP, DESIGN.md 1.3a). Cc / Cr now sense onto node cms (Cr refreshed to
(vocm, vocm)); the amp (pair m_ca, tail m_cat on ibn, loads m_cad / m_cam / m_cal) drives ctl. Start-up clamps (rstb low):
ctl -> ivbl0 (D57, kept) and cms -> vocm. Tokens: cm_unity (broken copy: amp replaced by an ideal unity buffer
ctl = V(cms) - V(vocm) + V(ivbl0), the old passive loop), cm_open (AC loop break: m_plc gates on ctlg, 1 GOhm from ctl,
1 F to ground; DC unchanged, used for the f_cm return ratio), cc_div4 (Cc / 4), cmbw4 (CM_BW4_CAP on ctl), ibtp95.
WO-28 (D61): dual-path CMFB. Cc on ctl, Cr refreshed to (vocm, bli); gm-C follower-integrator ctl -> bli (m_ia / m_il /
m_it, C_INT to vdd); start-up clamps (rstb low) ctl, bli -> ivbl0 and outp, outn -> vocm. Tokens: int_off (broken copy:
bli tied to ivbl0, the WO-26 passive loop), cm_open (now with a dummy m_plc pair on ctl), cc_div4, vbl0x2 (ivbl0 x2),
cr_x2 (WO-30 info: Cr x 2). cr_x05 (WO-31: Cr / 2 = the pre-D64 0.025 pF, tb9 start-up broken copy).
The WO-27 tokens cm_unity / cmbw4 and node cms are gone.
mut is a '+'-joined token list: structural tokens nc_short, ref_composite (D58 4x4 composites, broken copy of the D59
ratio rows), kp_fixed; bias-scaling tokens (bias_currents only) ibn105 (ibn x1.05), ibtp90 / ibtp112 (ibtp x0.90 /
x1.12), vbl0x4 (ivbl0 x4).

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


def toks(mut):
    return set(mut.split("+")) if mut else set()


def ref(key, name, node, rail, bulk, sizes, mut):
    """D59: parallel-only unit-finger diode (m = M_ref). Broken copy ref_composite: D58 P x S composite of the same W/L."""
    p = sizes[key]
    if "ref_composite" in toks(mut):
        return composite(name, node, node, rail, bulk, p, S.REF_COMPOSITE["P"] * p["M"], S.REF_COMPOSITE["S"])
    return [mos(name, node, node, rail, bulk, p["dev"], p["WF"], p["L"], p["M"])]


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
    mt = toks(mut)
    gplc = "ctlg" if "cm_open" in mt else "ctl"
    # bias: composite 1:32 references (tail, sink, fixed load) and the cascode-bias diodes (K-density, single finger)
    w(ref("m_tr", "mtr", "ibtp", "vdd", "vdd", z, mut))
    w(ref("m_nr", "mnr", "ibn", "vss", "vss", z, mut))
    w(ref("m_plr", "mplr", "ibp", "vdd", "vdd", z, mut))
    nb0, nsw = S.KP_BANK["base"], S.KP_BANK["boost"] - S.KP_BANK["base"]
    bp, bx = z["m_bpd"], z["m_bpx"]
    w([mos("mbpd", "ivbpc", "ivbpc", "vdd", "vdd", bp["dev"], bp["WF"], bp["L"], nb0),
       mos("mbpds", "ivbpc", "gbk", "vdd", "vdd", bp["dev"], bp["WF"], bp["L"], nsw),
       dev("m_bnd", "mbnd", "ivbnc", "ivbnc", "vss", "vss", z)])
    # gate-path bank switch (review minor): static rails per mode (boost: TG closed, pull-up off; base: TG open, pull-up on)
    on, off = ("vdd", "vss") if boost else ("vss", "vdd")
    sp = S.BANK_SW["p"]
    w(tg("Sbk", "gbk", "ivbpc", on, off) + [mos("mbku", "gbk", on, "vdd", "vdd", sp["dev"], sp["W"], sp["L"])])
    if "kp_fixed" not in mt:   # D58/D59 replica of the folded branch (kp_fixed = old wiring: ports fed from fixed I_REF)
        w([dev("m_rcp", "mrcp", "rcb", "ibp", "vdd", "vdd", z), dev("m_rcb", "mrcb", "rcb", "rcb", "vss", "vss", z),
           dev("m_rt", "mrt", "ivbpc", "ibtp", "vdd", "vdd", z),
           dev("m_rnc", "mrnc", "ivbpc", S.REPLICA_CASC_GATE, "rnd", "vss", z),
           dev("m_rn", "mrn", "rnd", "ibn", "vss", "vss", z),
           mos("mbpx", "ivbnc", "ivbpc", "vdd", "vdd", bx["dev"], bx["WF"], bx["L"], nb0),
           mos("mbpxs", "ivbnc", "gbk", "vdd", "vdd", bx["dev"], bx["WF"], bx["L"], nsw)])
    w(ref("m_bl0", "mbl0", "ivbl0", "vdd", "vdd", z, None))   # V_BL0 replica: 1 m_plc unit finger, 1:8
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
       dev("m_plc", "mplc1", "sa", gplc, "vdd", "vdd", z), dev("m_plc", "mplc2", "sb", gplc, "vdd", "vdd", z)])
    if "nc_short" in mt:
        w(["Rmut1 outn xa 1", "Rmut2 outp xb 1"])
    if S.C_FOLD_EXTRA:
        w([f"Cfx1 fa vss {S.C_FOLD_EXTRA:g}", f"Cfx2 fb vss {S.C_FOLD_EXTRA:g}"])
    # CMFB, WO-28 (D61) dual path: fast passive SC path onto ctl (Cc, Cr refreshed to (vocm, bli)), slow gm-C
    # follower-integrator ctl -> bli (sizes_draft INTEG, DESIGN.md 1.3b)
    # WO-30: cr_x2 = Cr x 2 (info; the Cc charge mode decays with tau = T Cc / Cr). WO-31 (D64 default Cr 0.05 pF):
    # cr_x05 = Cr / 2 = the old 0.025 pF (tb9 start-up broken copy)
    cc = S.C_CMFB_SENSE / (4.0 if "cc_div4" in mt else 1.0)
    cr = S.C_CMFB_REFRESH * (2.0 if "cr_x2" in mt else 0.5 if "cr_x05" in mt else 1.0)
    w([f"Ccp outp ctl {cc:g}", f"Ccn outn ctl {cc:g}"])
    c, c2, co = S.CTL_RST, S.BLI_RST, S.OUT_RST
    w([mos("mrst", "ctl", "rstb", "ivbl0", "vdd", c["dev"], c["W"], c["L"]),
       mos("mrsb", "bli", "rstb", "ivbl0", "vdd", c2["dev"], c2["W"], c2["L"]),
       mos("mrsop", "outp", "rstb", "vocm", "vdd", co["dev"], co["W"], co["L"]),
       mos("mrson", "outn", "rstb", "vocm", "vdd", co["dev"], co["W"], co["L"])])
    if "cm_open" in mt:   # DC: ctlg = ctl; AC: m_plc gates grounded. Dummy m_plc pair keeps the ctl gate load (gate ctl,
        # drain forced to V(sa)/V(sb) by B sources, so Cgs/Cgd on ctl see the same AC voltages as in the closed copy)
        pc = z["m_plc"]
        w(["Rbrk ctl ctlg 1e9", "Cbrk ctlg vss 1", "Bdsa dsa vss V = V(sa)", "Bdsb dsb vss V = V(sb)",
           mos("mplcd1", "dsa", "ctl", "vdd", "vdd", pc["dev"], pc["WF"], pc["L"], pc["M"]),
           mos("mplcd2", "dsb", "ctl", "vdd", "vdd", pc["dev"], pc["WF"], pc["L"], pc["M"])])
    if "int_off" in mt:   # broken copy: no slow path, bli = V_BL0 replica (the WO-26 passive loop)
        w(["Rio bli ivbl0 1"])
    else:
        w([dev("m_it", "mit", "cit", "ibn", "vss", "vss", z),
           dev("m_ia", "mia1", "cid", "ctl", "cit", "vss", z), dev("m_ia", "mia2", "bli", "bli", "cit", "vss", z),
           dev("m_il", "mil1", "cid", "cid", "vdd", "vdd", z), dev("m_il", "mil2", "bli", "cid", "vdd", "vdd", z),
           f"Cint bli vdd {S.C_INT:g}"])
    if cmfb == "sc":
        # WO-29 diagnosis tokens (tb9 only; the deck defines .model SWI): sw_ideal = all CMFB TGs ideal (no charge
        # injection / feedthrough), sw_ideal_ctl = only the ctl-side share switch Sr2b ideal, sw_ideal_bli = only the
        # bli-side refresh switch Sr1b ideal, sw_min = every CMFB TG at minimum W (0.42 n and p)
        def cs(nm, a, b, g, gb):
            if "sw_ideal" in mt or ("sw_ideal_ctl" in mt and nm.startswith("Sr2b")) or \
                    ("sw_ideal_bli" in mt and nm.startswith("Sr1b")):
                return [f"S{nm} {a} {b} {g} vss SWI"]
            if "sw_min" in mt:
                n, p = S.CMFB_SW["n"], S.CMFB_SW["p"]
                return [mos(nm + "n", a, g, b, "vss", n["dev"], 0.42, n["L"]), mos(nm + "p", a, gb, b, "vdd", p["dev"], 0.42, p["L"])]
            return tg(nm, a, b, g, gb)
        for s_, o in (("p", "outp"), ("n", "outn")):
            w([f"Cr{s_} ra{s_} rb{s_} {cr:g}"])
            w(cs(f"Sr1a{s_}", f"ra{s_}", "vocm", "ph1", "ph1b") + cs(f"Sr1b{s_}", f"rb{s_}", "bli", "ph1", "ph1b")
              + cs(f"Sr2a{s_}", f"ra{s_}", o, "ph2", "ph2b") + cs(f"Sr2b{s_}", f"rb{s_}", "ctl", "ph2", "ph2b"))
    elif cmfb == "dc":   # averaged Cr pair: i = (V_outcm - V_ctl - V_vocm + V_bli) / R into ctl and out of bli
        r = 1.0 / (fs * 2 * cr)
        e = f"(0.5*(V(outp)+V(outn)) - V(ctl) - V(vocm) + V(bli))/{r:.6g}"
        w([f"Bscc vss ctl I = {e}", f"Bscb bli vss I = {e}"])
    else:
        raise ValueError(cmfb)
    L.append(f".ends {name}")
    return "\n".join(L) + "\n"


def bias_currents(boost, mut=None):
    """Reference currents per port [A] (C6 ideal sources in the testbenches), base or boost (x BOOST x BOOST_SCALE).
    D59: no trim. Tokens: kp_fixed = old wiring, vbpc / vbnc fed with the fixed design currents (I_BPD_FRAC / I_BND_FRAC
    x I_NC); ibn105 / ibtp90 / ibtp112 / vbl0x4 scale one port (broken copies and the K_P tracking copy)."""
    k = {"ibtp": "btp", "ibn": "bn", "ibp": "bp", "ivbnc": "vbnc", "ivbpc": "vbpc", "ivbl0": "vbl0"}
    m = S.BOOST if boost else 1.0
    out = {p: S.I_REF[r] * (m * S.BOOST_SCALE.get(r, 1.0) if boost else 1.0) for p, r in k.items()}
    t = toks(mut)
    if "kp_fixed" in t:
        out["ivbpc"], out["ivbnc"] = m * S.I_NC * S.I_BPD_FRAC, m * S.I_NC * S.I_BND_FRAC
    for tok, port, f in (("ibn105", "ibn", 1.05), ("ibtp90", "ibtp", 0.90), ("ibtp112", "ibtp", 1.12), ("vbl0x4", "ivbl0", 4.0),
                         ("ibtp95", "ibtp", 0.95), ("vbl0x2", "ivbl0", 2.0)):
        if tok in t:
            out[port] *= f
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
