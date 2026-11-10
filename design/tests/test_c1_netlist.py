"""WO-24 item 2: structure of the generated OTA1 netlist (design/c1_ota1/netlist.py). Pure text, no simulator.
Each check fails on a broken copy (WO-26 / D59: the D58 composites, hand-typed replica sizes, old wiring, a bank switch
in the diode path)."""
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "c1_ota1"))
import netlist as NL  # noqa: E402
import sizes_draft as S  # noqa: E402

def refs_ok(text, sizes=None):
    """D59: every reference (mtr, mnr, mplr, mbl0) is ONE parallel-only diode instance of the mirror's unit finger
    (same dev / WF / L), m = M_mirror / RATIO, drain = gate. Broken copy: the D58 series-parallel composites."""
    z = sizes or S.SIZES
    for ref, mir, nm, node, rail in (("m_tr", "m_t", "mtr", "ibtp", "vdd"), ("m_nr", "m_n", "mnr", "ibn", "vss"),
                                     ("m_plr", "m_pl", "mplr", "ibp", "vdd"), ("m_bl0", "m_plc", "mbl0", "ivbl0", "vdd")):
        u = z[mir]
        lines = [l for l in text.splitlines() if re.match(rf"X{nm}(_\d+)? ", l)]
        want = f"X{nm} {node} {node} {rail} {rail} "   # WO-27: source and bulk on the mirror's rail (review blind spot)
        if len(lines) != 1 or not lines[0].startswith(want):
            return False
        if f"{u['dev']} w={u['WF']:g} l={u['L']:g} m={u['M'] // S.RATIO} " not in lines[0] or u["M"] // S.RATIO * S.RATIO != u["M"]:
            return False
    return S.RATIO == 8


def test_parallel_refs():
    assert refs_ok(NL.build())


def test_composite_ref_fails():
    assert not refs_ok(NL.build(mut="ref_composite"))


def test_ref_terminals_fail_on_broken_copy():
    assert not refs_ok(NL.build().replace("Xmtr ibtp ibtp vdd vdd", "Xmtr ibtp ibtp vdd tail"))   # bulk off the rail
    assert not refs_ok(NL.build().replace("Xmnr ibn ibn vss vss", "Xmnr ibn ibn xa vss"))         # source off the rail


def rcb_ok(text):
    """WO-27 review minor: rcb diode = m_bnc type / L with W 0.47 (narrowed), one finger; rcb feed = one m_pl unit finger."""
    f = lambda pat: re.search(pat, text, re.M) is not None
    pl, bc = S.SIZES["m_pl"], S.SIZES["m_bnc"]
    return (f(rf"^Xmrcb rcb rcb vss vss \S*{bc['dev']} w=0.47 l={bc['L']:g} m=1 ")
            and f(rf"^Xmrcp rcb ibp vdd vdd \S*{pl['dev']} w={pl['WF']:g} l={pl['L']:g} m=1 "))


def test_rcb_geometry():
    assert rcb_ok(NL.build())


def test_rcb_geometry_fails_on_broken_copy():
    assert not rcb_ok(NL.build().replace("w=0.47 l=16 m=1", "w=0.625 l=16 m=1"))     # WO-26 width
    assert not rcb_ok(NL.build().replace("Xmrcp rcb ibp vdd vdd sky130_fd_pr__pfet_g5v0d10v5 w=2.5 l=4 m=1",
                                         "Xmrcp rcb ibp vdd vdd sky130_fd_pr__pfet_g5v0d10v5 w=2.5 l=4 m=2"))


def dualpath_ok(text):
    """WO-28 (D61) dual-path CMFB: Cc outputs -> ctl, Cr refreshed to (vocm, bli) and shared with (out, ctl); 5T
    follower-integrator ctl -> bli (pair gate ctl / gate=drain bli on a tail of INTEG m_n unit fingers, gate ibn; PMOS
    mirror loads cid -> bli), C_INT bli -> vdd; m_plc gates on ctl; start-up clamps ctl/bli -> ivbl0, outputs -> vocm."""
    f = lambda pat: re.search(pat, text, re.M) is not None
    n = S.SIZES["m_n"]
    return (f(rf"^Xmit cit ibn vss vss \S*{n['dev']} w={n['WF']:g} l={n['L']:g} m={S.INTEG['tail']} ")
            and f(r"^Xmia1 cid ctl cit vss ") and f(r"^Xmia2 bli bli cit vss ")
            and f(r"^Xmil1 cid cid vdd vdd ") and f(r"^Xmil2 bli cid vdd vdd ") and f(rf"^Cint bli vdd {S.C_INT:g}$")
            and f(r"^Ccp outp ctl ") and f(r"^Ccn outn ctl ") and f(r"^XSr1apn rap ph1 vocm ") and f(r"^XSr1bpn rbp ph1 bli ")
            and f(r"^XSr2apn rap ph2 outp ") and f(r"^XSr2bpn rbp ph2 ctl ") and f(r"^Xmplc1 sa ctl vdd vdd ")
            and f(r"^Xmrst ctl rstb ivbl0 vdd ") and f(r"^Xmrsb bli rstb ivbl0 vdd ")
            and f(r"^Xmrsop outp rstb vocm vdd ") and f(r"^Xmrson outn rstb vocm vdd ") and not f(r"cms"))


def test_dualpath_structure():
    assert dualpath_ok(NL.build()) and dualpath_ok(NL.build(boost=True))


def test_dualpath_fails_on_broken_copy():
    assert not dualpath_ok(NL.build(mut="int_off"))                                     # slow path removed
    assert not dualpath_ok(NL.build(mut="cm_open"))                                     # loop break left in
    assert not dualpath_ok(NL.build().replace("Xmia2 bli bli cit", "Xmia2 bli ctl cit"))  # follower feedback lost
    assert not dualpath_ok(NL.build().replace("XSr1bpn rbp ph1 bli", "XSr1bpn rbp ph1 ivbl0"))  # WO-26 refresh level
    assert not dualpath_ok(NL.build().replace("Xmrsop outp rstb vocm", "Xmrsop outp rstb outp"))  # no output clamp


def test_dc_cmfb_averages_onto_ctl_and_bli():
    t = NL.build(cmfb="dc")
    assert re.search(r"^Bscc vss ctl I = \(0\.5\*\(V\(outp\)\+V\(outn\)\) - V\(ctl\) - V\(vocm\) \+ V\(bli\)\)/", t, re.M)
    assert re.search(r"^Bscb bli vss I = ", t, re.M)
    assert not re.search(r"^Bscb bli vss I = ", NL.build(cmfb="dc").replace("Bscb bli vss", "Bscb vss bli"), re.M)


def test_tail_reference_area_grown():
    """WO-28 item 2: tail unit finger 3.75/6 (x9 area of 1.25/2, same W/L), reference and replica derived from it."""
    t, r = S.SIZES["m_t"], S.SIZES["m_tr"]
    assert t["WF"] / t["L"] == pytest.approx(1.25 / 2.0) and t["WF"] * t["L"] == pytest.approx(9 * 1.25 * 2.0)
    assert r["WF"] == t["WF"] and r["L"] == t["L"] and r["M"] * S.RATIO == t["M"]
    z = dict(t, WF=1.25, L=2.0)
    assert not (z["WF"] * z["L"] == pytest.approx(9 * 1.25 * 2.0))


def replica_sizes_ok(z):
    """D59 review minor: replica / reference sizes are derived from the mirror unit fingers (equality, not hand-typed)."""
    same = lambda a, b: all(z[a][k] == z[b][k] for k in ("dev", "WF", "L"))
    return (same("m_rt", "m_t") and same("m_rn", "m_n") and same("m_rnc", "m_nc") and same("m_tr", "m_t")
            and same("m_nr", "m_n") and same("m_plr", "m_pl") and same("m_bl0", "m_plc")
            and z["m_rn"]["M"] == 2 * z["m_rt"]["M"] and 2 <= z["m_rt"]["M"] <= 4)


def test_replica_sizes_derived():
    assert replica_sizes_ok(S.SIZES)


def test_replica_sizes_fail_on_hand_typed_copy():
    z = {k: dict(v) for k, v in S.SIZES.items()}
    z["m_rn"]["WF"] = 2.0
    assert not replica_sizes_ok(z)
    z = {k: dict(v) for k, v in S.SIZES.items()}
    z["m_rt"]["M"] = 1   # WO-25 single tail finger
    assert not replica_sizes_ok(z)


def test_device_count():
    c = NL.count(NL.build(cmfb="sc"))
    assert c.get("pfet_01v8") == 2
    assert c.get("nfet_01v8") == 4
    # m_n 2, m_nc 2, refs m_nr 1, m_bnd 1, replica m_rn + cascode m_rnc 2, input chopper 4, island 2, CMFB TG n 8, bank TG n 1
    assert c.get("nfet_g5v0d10v5") == 2 + 2 + 1 + 1 + 2 + 4 + 2 + 8 + 1 + 1 + 3   # + rcb diode m_rcb, + integrator pair/tail
    # m_t 1, m_pp 2, m_pc 2, m_pl 2, m_plc 2, refs m_tr/m_plr/mbl0 3, mbpd/mbpds 2, mbpx/mbpxs 2, m_rt 1, bank TG p 1,
    # pull-up mbku 1, CMFB TG p 8, ctl reset 1
    assert c.get("pfet_g5v0d10v5") == 1 + 2 + 2 + 2 + 2 + 3 + 2 + 2 + 1 + 1 + 1 + 8 + 1 + 1 + 2 + 1 + 2   # + m_rcp, integrator loads, bli clamp, output clamps


def test_geometry_on_every_device():
    for l in NL.build().splitlines():
        if l.startswith("X") and "sky130_fd_pr__" in l:
            for k in ("ad=", "as=", "pd=", "ps="):
                assert k in l, l


def test_dc_cmfb_has_no_switches_and_mutant_shorts_nc():
    t = NL.build(cmfb="dc")
    assert "Bscc" in t and "XSr1ap" not in t
    assert "Rmut1 outn xa" in NL.build(mut="nc_short")


def test_bias_boost_kp():
    b, f = NL.bias_currents(False), NL.bias_currents(True)
    assert f["ibtp"] == pytest.approx(2 * b["ibtp"])
    assert b["ibtp"] == pytest.approx(S.I_TAIL / 8 * 1.019) and S.BTP_RECENTRE == 1.019 and b["ivbl0"] == pytest.approx(S.I_NC * 0.25 / 8)   # D59 1:8, no trim
    assert b["ivbpc"] == 0 and b["ivbnc"] == 0           # D58: replica-fed, no reference current
    kf = NL.bias_currents(True, "kp_fixed")
    assert kf["ivbpc"] == pytest.approx(2 * S.I_NC / 8) and kf["ivbnc"] == pytest.approx(2 * S.I_NC / 16)
    assert NL.bias_currents(False, "kp_fixed+ibn105")["ibn"] == pytest.approx(1.05 * b["ibn"])


def replica_ok(text):
    """D59: tail replica on ibtp, sink replica (ibn) cascoded by mrnc (gate rcb from the ibp leg, not the ivbnc loop), both on ivbpc; copy
    bank m_bpx (gate ivbpc) and its switched fingers feed ivbnc."""
    f = lambda pat: re.search(pat, text, re.M) is not None
    return (f(r"^Xmrcp rcb ibp vdd vdd ") and f(r"^Xmrcb rcb rcb vss vss ") and f(r"^Xmrt ivbpc ibtp vdd vdd ") and f(rf"^Xmrnc ivbpc {S.REPLICA_CASC_GATE} rnd vss ")
            and f(r"^Xmrn rnd ibn vss vss ") and f(r"^Xmbpx ivbnc ivbpc vdd vdd ") and f(r"^Xmbpxs ivbnc gbk vdd vdd ")
            and S.REPLICA_CASC_GATE != "ivbnc")


def test_replica_bias():
    assert replica_ok(NL.build())


def test_replica_bias_fails_on_old_wiring():
    assert not replica_ok(NL.build(mut="kp_fixed"))
    assert not replica_ok(NL.build().replace("Xmrnc ivbpc rcb rnd", "Xmrnc ivbpc ivbnc rnd"))   # zero-state loop


def bank_ok(text, boost):
    """Gate-path bank switch: KP_BANK base fingers always on ivbpc; the boost-only fingers have gate gbk; TG gbk<->ivbpc
    closed only in boost; pull-up gbk->vdd on only in base. No switch in series with a diode."""
    m = lambda nm: re.search(rf"^X{nm} (\S+) (\S+) .* m=(\d+) ", text, re.M)
    d, ds, tn, tp, pu = m("mbpd"), m("mbpds"), m("Sbkn"), m("Sbkp"), m("mbku")
    x, xs = m("mbpx"), m("mbpxs")
    if not all((d, ds, tn, tp, pu, x, xs)):
        return False
    on, off = ("vdd", "vss") if boost else ("vss", "vdd")
    # WO-27 review blind spots: the TG's PMOS gate is the complement, and the copy bank has the same finger split
    if tp.group(2) != off or int(x.group(3)) != S.KP_BANK["base"] or int(xs.group(3)) != S.KP_BANK["boost"] - S.KP_BANK["base"]:
        return False
    return (d.group(1) == d.group(2) == "ivbpc" and int(d.group(3)) == S.KP_BANK["base"]
            and ds.group(1) == "ivbpc" and ds.group(2) == "gbk" and int(ds.group(3)) == S.KP_BANK["boost"] - S.KP_BANK["base"]
            and tn.group(2) == on and pu.group(2) == on)


def test_kp_bank_switch():
    assert bank_ok(NL.build(), False) and bank_ok(NL.build(boost=True), True)


def test_kp_bank_switch_fails_on_broken_copy():
    assert not bank_ok(NL.build(), True)                                             # wrong mode state
    assert not bank_ok(NL.build().replace("Xmbpds ivbpc gbk", "Xmbpds ivbpc ivbpc"), False)   # always-on fingers
    t = NL.build()
    sp = [l for l in t.splitlines() if l.startswith("XSbkp ")][0]
    assert not bank_ok(t.replace(sp, sp.replace("XSbkp gbk vdd ivbpc", "XSbkp gbk vss ivbpc")), False)   # PMOS gate = n gate
    xs = [l for l in t.splitlines() if l.startswith("Xmbpxs ")][0]
    assert not bank_ok(t.replace(xs, xs.replace(" m=3 ", " m=2 ")), False)                                # copy bank count
