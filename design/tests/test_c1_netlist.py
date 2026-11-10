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
    for ref, mir, nm, node in (("m_tr", "m_t", "mtr", "ibtp"), ("m_nr", "m_n", "mnr", "ibn"), ("m_plr", "m_pl", "mplr", "ibp"),
                               ("m_bl0", "m_plc", "mbl0", "ivbl0")):
        u = z[mir]
        lines = [l for l in text.splitlines() if re.match(rf"X{nm}(_\d+)? ", l)]
        want = f"X{nm} {node} {node} "
        if len(lines) != 1 or not lines[0].startswith(want):
            return False
        if f"{u['dev']} w={u['WF']:g} l={u['L']:g} m={u['M'] // S.RATIO} " not in lines[0] or u["M"] // S.RATIO * S.RATIO != u["M"]:
            return False
    return S.RATIO == 8


def test_parallel_refs():
    assert refs_ok(NL.build())


def test_composite_ref_fails():
    assert not refs_ok(NL.build(mut="ref_composite"))


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
    assert c.get("nfet_g5v0d10v5") == 2 + 2 + 1 + 1 + 2 + 4 + 2 + 8 + 1
    # m_t 1, m_pp 2, m_pc 2, m_pl 2, m_plc 2, refs m_tr/m_plr/mbl0 3, mbpd/mbpds 2, mbpx/mbpxs 2, m_rt 1, bank TG p 1,
    # pull-up mbku 1, CMFB TG p 8, ctl reset 1
    assert c.get("pfet_g5v0d10v5") == 1 + 2 + 2 + 2 + 2 + 3 + 2 + 2 + 1 + 1 + 1 + 8 + 1


def test_geometry_on_every_device():
    for l in NL.build().splitlines():
        if l.startswith("X") and "sky130_fd_pr__" in l:
            for k in ("ad=", "as=", "pd=", "ps="):
                assert k in l, l


def test_dc_cmfb_has_no_switches_and_mutant_shorts_nc():
    t = NL.build(cmfb="dc")
    assert "Rcmeq" in t and "XSr1ap" not in t
    assert "Rmut1 outn xa" in NL.build(mut="nc_short")


def test_bias_boost_kp():
    b, f = NL.bias_currents(False), NL.bias_currents(True)
    assert f["ibtp"] == pytest.approx(2 * b["ibtp"])
    assert b["ibtp"] == pytest.approx(S.I_TAIL / 8) and b["ivbl0"] == pytest.approx(S.I_NC * 0.25 / 8)   # D59 1:8, no trim
    assert b["ivbpc"] == 0 and b["ivbnc"] == 0           # D58: replica-fed, no reference current
    kf = NL.bias_currents(True, "kp_fixed")
    assert kf["ivbpc"] == pytest.approx(2 * S.I_NC / 8) and kf["ivbnc"] == pytest.approx(2 * S.I_NC / 16)
    assert NL.bias_currents(False, "kp_fixed+ibn105")["ibn"] == pytest.approx(1.05 * b["ibn"])


def replica_ok(text):
    """D59: tail replica on ibtp, sink replica (ibn) cascoded by mrnc (gate vicm, not the ivbnc loop), both on ivbpc; copy
    bank m_bpx (gate ivbpc) and its switched fingers feed ivbnc."""
    f = lambda pat: re.search(pat, text, re.M) is not None
    return (f(r"^Xmrt ivbpc ibtp vdd vdd ") and f(rf"^Xmrnc ivbpc {S.REPLICA_CASC_GATE} rnd vss ")
            and f(r"^Xmrn rnd ibn vss vss ") and f(r"^Xmbpx ivbnc ivbpc vdd vdd ") and f(r"^Xmbpxs ivbnc gbk vdd vdd ")
            and S.REPLICA_CASC_GATE != "ivbnc")


def test_replica_bias():
    assert replica_ok(NL.build())


def test_replica_bias_fails_on_old_wiring():
    assert not replica_ok(NL.build(mut="kp_fixed"))
    assert not replica_ok(NL.build().replace("Xmrnc ivbpc vicm rnd", "Xmrnc ivbpc ivbnc rnd"))   # zero-state loop


def bank_ok(text, boost):
    """Gate-path bank switch: KP_BANK base fingers always on ivbpc; the boost-only fingers have gate gbk; TG gbk<->ivbpc
    closed only in boost; pull-up gbk->vdd on only in base. No switch in series with a diode."""
    m = lambda nm: re.search(rf"^X{nm} (\S+) (\S+) .* m=(\d+) ", text, re.M)
    d, ds, tn, tp, pu = m("mbpd"), m("mbpds"), m("Sbkn"), m("Sbkp"), m("mbku")
    if not all((d, ds, tn, tp, pu)):
        return False
    on = "vdd" if boost else "vss"
    return (d.group(1) == d.group(2) == "ivbpc" and int(d.group(3)) == S.KP_BANK["base"]
            and ds.group(1) == "ivbpc" and ds.group(2) == "gbk" and int(ds.group(3)) == S.KP_BANK["boost"] - S.KP_BANK["base"]
            and tn.group(2) == on and pu.group(2) == on)


def test_kp_bank_switch():
    assert bank_ok(NL.build(), False) and bank_ok(NL.build(boost=True), True)


def test_kp_bank_switch_fails_on_broken_copy():
    assert not bank_ok(NL.build(), True)                                             # wrong mode state
    assert not bank_ok(NL.build().replace("Xmbpds ivbpc gbk", "Xmbpds ivbpc ivbpc"), False)   # always-on fingers
