"""WO-24 item 2: structure of the generated OTA1 netlist (design/c1_ota1/netlist.py). Pure text, no simulator.
Each check fails on a broken copy: the rev C single-finger references (mut="ref_single") must fail the composite test."""
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "c1_ota1"))
import netlist as NL  # noqa: E402
import sizes_draft as S  # noqa: E402

PC = S.REF_COMPOSITE["P"] * S.REF_COMPOSITE["S"]


def refs_ok(text):
    """Every 1:32 reference (mtr, mnr, mplr) is P x S unit fingers of the mirror's WF/L, series chain to the rail."""
    for key, nm in (("m_tr", "mtr"), ("m_nr", "mnr"), ("m_plr", "mplr")):
        u = S.SIZES[key]
        lines = [l for l in text.splitlines() if re.match(rf"X{nm}(_\d+)? ", l)]
        if len(lines) != S.REF_COMPOSITE["S"]:
            return False
        for l in lines:
            if f"w={u['WF']:g} l={u['L']:g} m={S.REF_COMPOSITE['P']} " not in l:
                return False
        if sum(int(re.search(r" m=(\d+)", l).group(1)) for l in lines) != PC:
            return False
    return True


def test_composite_refs():
    assert refs_ok(NL.build())


def test_single_finger_ref_fails():
    assert not refs_ok(NL.build(mut="ref_single"))


def test_device_count():
    c = NL.count(NL.build(cmfb="sc"))
    s_ = S.REF_COMPOSITE["S"]
    # core: m_t 1, m_in 2, m_pp 2, m_n 2, m_nc 2, m_pc 2, m_pl 2, m_plc 2; refs 3 x S; m_bnc, m_bpc; V_BL0 replica;
    # switches: input chopper 4 + island 2 (3.3 V n), fold chopper 4 (nfet_01v8), CMFB 8 TGs (n + p), ctl reset 1 (p)
    assert c.get("pfet_01v8") == 2
    assert c.get("nfet_01v8") == 4
    assert c.get("nfet_g5v0d10v5") == 2 + 2 + s_ + 1 + 4 + 2 + 8
    assert c.get("pfet_g5v0d10v5") == 1 + 2 + 2 + 2 + 2 + 2 * s_ + 1 + S.VBL0_SERIES + 8 + 1


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
    assert f["ivbpc"] / b["ivbpc"] == pytest.approx(S.BOOST * S.BOOST_SCALE["vbpc"])   # CL-8 x1.4
