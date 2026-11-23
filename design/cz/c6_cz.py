#!/usr/bin/env python3
"""BIAS_EXT wrapper `c6_cz` around `c6_bias` (WO-108, D99b, review-1 revision). Sandbox only (ngspice, sky130A via PDK_ROOT).
c6_final.py is imported unchanged (WO-104 owns it).

  python c6_cz.py netlist [OUT.spice] [MUT]          # c6_bias + c6_cz subckts (default: stdout)
  python c6_cz.py jobs OUT FROZEN JOBFILE            # lpool job list
  python c6_cz.py run OUT KIND CORNER TEMP VDD [MUT] # one transient bench -> OUT/<tag>.json
        KIND s0 | s0e5 | s0e20 = sel 0, OTA1 bias diodes as loads, bare c6_bias next to the wrapper; bias_ext at 0 V /
                                 5.35 uA / 20 uA (harness current left on while sel 0) (G1)
             lk | lke5 | lke20 = same, ports held at fixed voltages (worst off-switch Vds) (G4)
             s1  = sel 1, bias_ext stepped (open start, 5.35, 2.5, 10, 1, 20, 5.35, boost, 10 boost, open), pin = 10 pF + 5 nA
                   leakage into the pin; off state = open (G2, G3)
             s1z = as s1 with the off state a hard 0 V on the pin
  python c6_cz.py summary OUT                        # verdict table -> stdout

Subckt: .subckt c6_cz vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok bias_ext bias_sel
  The c6_bias ports plus bias_ext (current into the pin) and bias_sel. bias_sel is a 1.8 V control (VDPWR domain) like boost and
  trim: lsbuflv2hv_1 + inv_1 inside the wrapper. TT: bias_sel 0, bias_ext VSSA. c6_cz is CZ-only; TT uses c6_bias directly.
Topology (results/wo108/README.md): c6_bias unchanged; every port through two 3.3 V transmission gates (5 V devices): c6 path (sel 0)
  and ext path (sel 1). The ext path is a replica of the mirror side of C6 scaled by K = 5 (integer, unit fingers):
  bias_ext = 5 x I_TGT = 5.35 uA gives the C6 design port currents. bias_ok: sel 0 = c6 ok; sel 1 = ext-present detect (16-unit
  mirror leg vs xhigh-poly pull-up, schmittbuf + inverter), ok = 1 above about 1.2 uA.
Gates (corners: tt/27/3.3, ss/-40 at 3.0+3.6, ff/125 at 3.0+3.6, fs/-40/3.0 on s1; resistor corners ff_ll/125/3.6, ss_hh/-40/3.0 on s1):
  G1 (s0, s0e5, s0e20): wrapper = bare c6_bias within 0.1 % (base, boost), ok high from 140 us.
  G4 (lk, lke5, lke20): same with ports held at VDD-0.3 (sinks) / 0.3 V (ibn).
  G2 (s1): gated range 2.5-10 uA (0.5x..2x). Tracking (p(I)/p(5.35 uA))/(I/5.35 uA) - 1 <= 2 % at 2.5, 10 and the repeat; port ratios
           +-3 %; boost/base 2 +-4 % at 5.35 uA; absolute at 5.35 uA +-3 % (tt) / +-4 % (other corners). 1 uA, 20 uA, boost at 10 uA,
           and port headroom at 10/20 uA are info rows. Compliance through the TGs at the top of the range: the tracking at 10 uA.
  G3 (s1, s1z): open from power-up: ok < 0.1 VDD, ports < 20 nA; ok >= 0.9 VDD at 2.5 and 5.35 uA; lost current (open 60 us after
           good current): ok < 0.1 VDD, ports < 20 nA.
  stress: every recorded node within [-0.6, VDD+0.6] V and max(v) - min(v) <= 4.95 V (SPEC row 99 pair rule).
WO-108c (analysis work/v1-design/results/wo108/ANALYSIS_ff125.md): D1 output enable `ecg` (TG from bias_ext, en = sel_i AND ok_e,
  pull-down ecg, pull-up vpe); D2 150 fF esn cap (opt `cap`, default off); B1 convergence options (CZ_OPT rs/ab/ramp/ladder);
  B2 boost off at 265 us (CZ_OPT oldboost = 270 us); G2 absolute limb also at 5.25 and 5.5 uA (windows at 186-190, 196-200 us);
  G3 early lost window 276-280 us <= 20 nA; kind s1c = s1 with a 100 pF pin. Mutants noen (796658b topology), nopu, nocap.
Broken copies (each must REJECT its gate): swapsel (G1), noiso (one ext TG shorted: G1 on s0e5, G4 on lke20), kwrong (G2), efinger
(G2), nodetect (G3), rupq (R_UP/4: ok low at 2.5 uA, G3), leaky (G4), overv (stress). Variant, must ACCEPT: nosu (core without
start-up kick, sel 1).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "design", "c6_bias"))
sys.path.insert(0, os.path.join(ROOT, "design", "c1_ota1"))
import c6_final as F  # noqa: E402
import c6_spot as B  # noqa: E402

x, P5, N5 = B.x, B.P5, B.N5
PORT_I = F.PORT_I
SINKS, PORTS_ALL = F.SINKS, tuple(F.PORT_I)
K_EXT = 5                          # ext diode = K units of the C6 VN diode (integer, m=K)
I_NOM = K_EXT * B.I_TGT            # 5.35 uA: bias_ext giving the C6 design currents
N_SENSE = 16                       # sense leg units (NW/NL unit each)
R_UP_L = 300.0                     # um xhigh_po 0p69 (~0.87 MOhm): ext-present threshold ~1.2 uA (resistor +-30 % -> 0.9..1.7 uA)
HVL = F.HVL
LS, INV, MUX = F.LS, F.INV, "sky130_fd_sc_hvl__mux2_1"
SCH = "sky130_fd_sc_hvl__schmittbuf_1"
NAND = "sky130_fd_sc_hvl__nand2_1"       # pins A B VGND VNB VPB VPWR Y
CPORTS = "vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok bias_ext bias_sel"
MUTS = ("swapsel", "noiso", "kwrong", "efinger", "nodetect", "rupq", "leaky", "overv", "noen", "nopu", "nocap")
VARIANTS = ("nosu",)
MUT_KINDS = dict(swapsel=("s0",), noiso=("s0e5", "lke20"), kwrong=("s1",), efinger=("s1",), nodetect=("s1",), rupq=("s1",),
                 leaky=("lk",), overv=("s1",), nosu=("s1",), noen=("lke20", "s1c"), nopu=("s1z",), nocap=("s1z",))
# WO-108c options, env CZ_OPT = comma list (default empty = behaviour of 796658b except the topology/gate changes):
#   rs      rshunt=1e12 itl4=200 at temp > 100 (c6_spot.py:201 precedent)         [B1 step 1]
#   ab      abstol 1e-12 instead of 1e-14                                          [B1 step 2]
#   ramp    lk kinds: fixed port sources ramp with VDD (no forward-biased TG junctions while VDD is low) [B1 step 3]
#   ladder  = rs + ab + ramp
#   cap     D2: 150 fF esn -> vss (default OFF; mutant nocap = flag on, cap removed)
#   oldboost  boost-off edge at 270 us (796658b) instead of 265 us (B2)
OPT = set(os.environ.get("CZ_OPT", "").replace(" ", "").split(",")) - {""}
if "ladder" in OPT:
    OPT |= {"rs", "ab", "ramp"}
C_ESN = 150e-15                    # D2 esn capacitor (F)
CORNERS5 = [("tt", 27, 3.3), ("ss", -40, 3.0), ("ss", -40, 3.6), ("ff", 125, 3.0), ("ff", 125, 3.6)]
S1_EXTRA = [("fs", -40, 3.0), ("ff_ll", 125, 3.6), ("ss_hh", -40, 3.0)]
MUT_CORNERS = [("tt", 27, 3.3), ("ff", 125, 3.6)]
MUT_CORNERS_RUPQ = [("tt", 27, 3.3), ("ss_hh", -40, 3.0)]
# per-(mutant, kind) corner lists that differ from MUT_CORNERS (review m2)
MUT_RUNS = {("noen", "lke20"): [("ff", 125, 3.6)], ("noen", "s1c"): MUT_CORNERS, ("nocap", "s1z"): [("ff", 125, 3.6)]}
# m3: nopu (s1z, tt) rejects only through the early 276-280 us window (about 1.4x margin over the 20 nA limit).
LIM = dict(g1=1e-3, track=0.02, ratio=0.03, boost=0.04, tt=0.03, absn=0.04, ok_lo=0.1, ok_hi=0.9, i_open=20e-9, g4=1e-3,
           rail=0.6,   # worst pair = VDD + 2 x 0.6 = 4.8 V <= 4.95 V; floating mirror outputs undershoot to ~-0.45 V at power-up
           span=4.95,  # WO-108c: SPEC row 99 pair rule on the recorded nodes, max(v) - min(v) <= 4.95 V (added, nothing loosened)
           i_early=20e-9)   # WO-108c: lost current at 276-280 us (6-10 us after removal), independent of the board capacitance
U = 1e-6
I_LO, I_HI = 5.25, 5.5             # WO-108c harness steps around the 5.35 uA design point (analysis section 5)
# 5.25 and 5.5 uA inside the 180-210 us boost-off stretch, 10 us each (window = last 4 us); 5.35 uA returns at 200 us (window 206-210 = "5b")
STEPS = [(0, 0.0), (20, I_NOM * 1e6), (60, 2.5), (90, 10.0), (120, 1.0), (150, 20.0), (180, I_LO), (190, I_HI), (200, I_NOM * 1e6),
         (240, 10.0), (270, 0.0)]
END = {I_NOM * 1e6: 60, 2.5: 90, 10.0: 120, 1.0: 150, 20.0: 180, I_LO: 190, I_HI: 200}     # window end (us) of each current
T_BOOST = (210, 270) if "oldboost" in OPT else (210, 265)       # B2: boost-off edge moved away from the 270 us pin event
T_END = 330
WIN = 4.0                          # us averaging window at the end of each step
EXT_ON = dict(e5=I_NOM * 1e6, e20=20.0)


def target(mut, kind):
    if mut == "noiso":
        return "G1" if kind.startswith("s0") else "G4"
    if mut == "noen":
        return "G4" if kind.startswith("lk") else "G3"
    return dict(swapsel="G1", kwrong="G2", efinger="G2", nodetect="G3", rupq="G3", leaky="G4", overv="stress", nopu="G3",
                nocap="stress").get(mut)


def tg(name, a, b, gn, gp):
    return [x(f"{name}n", a, gn, b, "vss", N5, 2.0, 0.5), x(f"{name}p", a, gp, b, "vdd", P5, 4.0, 0.5)]


def build_cz(mut="none"):
    """The c6_cz subckt text (c6_bias must be defined alongside); the ext diode node IS bias_ext."""
    k = K_EXT * (0.9 if mut == "kwrong" else 1.0)
    L = [f".subckt c6_cz {CPORTS}", f"* WO-108 BIAS_EXT wrapper; mut {mut}; K_ext {k:g} (bias_ext {I_NOM * 1e6:.2f} uA = C6 master)",
         "Xcore vdd vss vdl boost trim0 trim1 trim2 c_ibtp c_ibn c_ibp c_ivbl0 c_ok c6_bias",
         f"Xlss bias_sel vdl vss vss vdd vdd sel_h {LS}", f"Xsi0 sel_h vss vss vdd vdd sel_b {INV}",
         f"Xsi1 sel_b vss vss vdd vdd sel_i {INV}"]
    for p in PORTS_ALL:
        cn, cp = ("sel_i", "sel_b") if (mut == "swapsel" and p == "ibp") else ("sel_b", "sel_i")
        L += tg(f"tc_{p}", f"c_{p}", p, cn, cp)
        if mut == "noiso" and p == "ivbl0":
            L.append(f"Rnoiso e_{p} {p} 1")
        else:
            L += tg(f"te_{p}", f"e_{p}", p, "sel_i", "sel_b")
    L += [f"Xlsb boost vdl vss vss vdd vdd eboost_h {LS}", f"Xivb eboost_h vss vss vdd vdd eboost_b {INV}"]
    # D1 (WO-108c): the output cascode gates (emc*, emfc) sit on `ecg`, fed from bias_ext through a TG enabled by sel_i AND ok_e;
    # disabled: ecg pulled to vss (en_b) and vpe pulled to vdd. Diode stack, sense leg and emsb stay on bias_ext/vne.
    # mut noen = 796658b topology (ecg IS bias_ext, no enable devices).
    cg = "bias_ext" if mut == "noen" else "ecg"
    if mut != "noen":
        L += [f"Xen_n sel_i ok_e vss vss vdd vdd en_b {NAND}", f"Xen_i en_b vss vss vdd vdd en {INV}"]
        L += tg("tcg", "bias_ext", "ecg", "en", "en_b")                                   # N 2/0.5, P 4/0.5
        L.append(x("emcgpd", "ecg", "en_b", "vss", "vss", N5, 1.0, 0.5))                  # pull-down, on when disabled
        if mut != "nopu":
            L.append(x("emvpu", "vpe", "en", "vdd", "vdd", P5, 2.0, 0.5))                 # vpe pull-up, on when disabled (en low)
    L += [x("emdc1", "bias_ext", "bias_ext", "vne", "vss", N5, F.NW, F.NCL, k), x("emdm1", "vne", "vne", "vss", "vss", N5, F.NW, F.NL, k),
          x("emsb", "bias_ext", "eboost_b", "vnse", "vss", N5, 2, 0.5, k),
          x("emdc2", "vnse", "bias_ext", "vn2e", "vss", N5, F.NW, F.NCL, k), x("emdm2", "vn2e", "vne", "vss", "vss", N5, F.NW, F.NL, k)]
    for p in SINKS:
        ws = F.fingers(F.units(p), F.NW)
        if mut == "efinger" and p == "ibp":
            ws = ws[1:]
        for i, w in enumerate(ws):
            L += [x(f"emm{p}{i}", f"e{p}m", "vne", "vss", "vss", N5, w, F.NL),
                  x(f"emc{p}{i}", f"e_{p}", cg, f"e{p}m", "vss", N5, w, F.NCL)]
    L += [x("emfm", "vfme", "vne", "vss", "vss", N5, F.NW, F.NL), x("emfc", "vpe", cg, "vfme", "vss", N5, F.NW, F.NCL),
          x("emvp", "vpe", "vpe", "vdd", "vdd", P5, F.PW, F.PL, F.N_VP)]
    for i, w in enumerate(F.fingers(F.units("ibn"), F.PW)):
        L.append(x(f"emibn{i}", "e_ibn", "vpe", "vdd", "vdd", P5, w, F.PL))
    rl = R_UP_L / 4 if mut == "rupq" else R_UP_L
    L += [x("esm", "esd", "vne", "vss", "vss", N5, F.NW, F.NL, N_SENSE), x("esc", "esn", "bias_ext", "esd", "vss", N5, F.NW, F.NCL, N_SENSE),
          f"Xrup vdd esn vss {B.RX} l={rl:g}"]
    if mut == "nodetect":
        L.append("Rnd ok_e vdd 1m")
    else:
        L += [f"Xsch esn vss vss vdd vdd esn_s {SCH}", f"Xdet esn_s vss vss vdd vdd ok_e {INV}"]
    if "cap" in OPT and mut != "nocap":                                           # D2 (default off): esn damping capacitor
        L.append(f"Cesn esn vss {C_ESN:g}")
    L.append(f"Xmx c_ok ok_e sel_i vss vss vdd vdd ok {MUX}")
    if mut == "leaky":
        L.append(f"Rleak ibtp vss {2.0 / (0.005 * PORT_I['ibtp']):.6g}")
    if mut == "overv":
        L += ["Vhi hi vss 5.2", "Rhi hi vne 1k"]
    return "\n".join(L + [".ends c6_cz"]) + "\n"


def netlist(mut="none"):
    return F.build("nosu" if mut == "nosu" else "none") + build_cz(mut)


def load_lines(pre):
    """OTA1 bias diodes (c6_final.ota_diodes) with instance and node names prefixed."""
    ren = {"dtp", "dn", "dp", "dbl"}
    out = []
    for ln in F.ota_diodes():
        t = ln.split()
        t[0] = "X" + pre + t[0][1:]
        out.append(" ".join(pre + s if s in ren else s for s in t))
    return out


def fixed_lines(pre, vdd):
    out = []
    rp = "ramp" in OPT       # B1 step 3: the port sources follow VDD (same 1.01 us ramp, scaled to the final value)
    for p, node in (("ibtp", "dtp"), ("ibp", "dp"), ("ivbl0", "dbl")):
        v = f"pwl(0 0 10n 0 1.01u {vdd - 0.3:g})" if rp else f"{vdd - 0.3:g}"
        out.append(f"V{pre}fx_{p} {pre}{node} 0 {v}")
    out.append(f"V{pre}fx_ibn {pre}dn 0 " + ("pwl(0 0 10n 0 1.01u 0.3)" if rp else "0.3"))
    return out


def stepwave(vals_us):
    """PWL (seconds, amps) with 1 ns edges from [(t_us, I_uA)]."""
    pts, cur = [(0, vals_us[0][1] * 1e-6)], vals_us[0][1] * 1e-6
    for t, v in vals_us[1:]:
        pts += [(t * U, cur), (t * U + 1e-9, v * 1e-6)]
        cur = v * 1e-6
    return F.pwl(pts)


def deck(kind, corner, temp, vdd, mut, csv, only=None):
    base = kind[:2]
    L = [f"* c6_cz {kind} {corner} {temp} {vdd} {mut}", f".lib {B.LIB} {corner}", f".include {HVL}", f".temp {temp}",
         f".option gmin={1e-11 if temp > 100 else 1e-15} reltol=1e-5 abstol={1e-12 if 'ab' in OPT else 1e-14:g} method={F.METHOD}"]
    if "rs" in OPT and temp > 100:       # B1 step 1: c6_spot.py:201 (WO-55/64/80/87 precedent), the `_b` and `_z` decks alike
        L.append(".option rshunt=1e12 itl4=200")
    ramp = f"pwl(0 {B.VPRE} 10n {B.VPRE} 1.01u {vdd})"
    L += [f"Vdd vdd 0 {ramp}", f"Vdo vdo 0 {ramp}"]
    for b in range(3):
        L.append(f"Vt{b} trim{b} 0 {1.8 * ((4 >> b) & 1):g}")
    if base == "s1":
        # VDPWR ramps with VAPWR; bias_sel (1.8 V domain) comes from the same VDPWR source
        L += ["Vdl vdl 0 pwl(0 0 10n 0 1.01u 1.8)", "Vsel bias_sel 0 pwl(0 0 10n 0 1.01u 1.8)"]
        L.append(f"Vbst boost 0 PWL({F.pwl(F.steps([(T_BOOST[0] * U, 1.8), (T_BOOST[1] * U, 0)], 0))})")
        L += [f"Iext 0 bias_ext PWL({stepwave(STEPS)})", "Ipl 0 bias_ext 5n",
              f"Cpad bias_ext 0 {'100p' if kind == 's1c' else '10p'}"]       # s1c: board capacitance 100 pF (fail-safe independent of it)
        if kind == "s1z":
            L += ["Sz bias_ext 0 zc 0 swz", ".model swz sw vt=0.5 vh=0 ron=1 roff=1e13",
                  f"Vzc zc 0 PWL(0 1 {20 * U:.9g} 1 {20 * U + 1e-9:.9g} 0 {270 * U:.9g} 0 {270 * U + 1e-9:.9g} 1)"]
        L.append("Xz vdd 0 vdl boost trim0 trim1 trim2 zibtp zibn zibp zivbl0 zok bias_ext bias_sel c6_cz")
        L += ["Vzmtp zdtp zibtp 0", "Vzmp zdp zibp 0", "Vzmbl zdbl zivbl0 0", "Vzmn zibn zdn 0"] + load_lines("z")
        vecs = ("i(vzmtp) i(vzmp) i(vzmbl) i(vzmn) v(zok) v(bias_ext) v(zibtp) v(zibp) v(zivbl0) v(zibn) "
                "v(xz.vne) v(xz.vn2e) v(xz.vpe) v(xz.esn) v(xz.ok_e) v(xz.e_ibtp) v(xz.e_ibn) v(xz.c_ibn) "
                + ("v(bias_ext)" if mut == "noen" else "v(xz.ecg)"))     # last column: ecg (noen: the shared net bias_ext)
        tend = T_END
    else:
        L += ["Vdl vdl 0 1.8", "Vsel bias_sel 0 0"]
        L.append(f"Vbst boost 0 PWL({F.pwl(F.steps([(250 * U, 1.8)], 0))})")
        ext = EXT_ON.get(kind[2:]) if len(kind) > 2 else None
        pres = ("b", "z") if only is None else (only,)
        if "z" in pres:
            if ext is None:
                L.append("Vext bias_ext 0 0")
            else:
                L += [f"Iext 0 bias_ext {ext * 1e-6:.6g}", "Cpad bias_ext 0 10p"]
        if "b" in pres:
            L.append("Xb vdd 0 vdl boost trim0 trim1 trim2 bibtp bibn bibp bivbl0 bok c6_bias")
        if "z" in pres:
            L.append("Xz vdd 0 vdl boost trim0 trim1 trim2 zibtp zibn zibp zivbl0 zok bias_ext bias_sel c6_cz")
        for pre in pres:
            L += ["V%smtp %sdtp %sibtp 0" % (pre, pre, pre), "V%smp %sdp %sibp 0" % (pre, pre, pre),
                  "V%smbl %sdbl %sivbl0 0" % (pre, pre, pre), "V%smn %sibn %sdn 0" % (pre, pre, pre)]
            L += load_lines(pre) if base == "s0" else fixed_lines(pre, vdd)
        vb = "i(vbmtp) i(vbmp) i(vbmbl) i(vbmn) v(bok) v(bibtp)"
        vz = "i(vzmtp) i(vzmp) i(vzmbl) i(vzmn) v(zok) v(zibtp) v(zibn) v(xz.vne) v(xz.esn) v(xz.e_ibn)"
        vecs = ("i(vbmtp) i(vbmp) i(vbmbl) i(vbmn) i(vzmtp) i(vzmp) i(vzmbl) i(vzmn) v(bok) v(zok) v(bibtp) v(zibtp) "
                "v(zibn) v(xz.vne) v(xz.esn) v(xz.e_ibn)") if only is None else (vb if only == "b" else vz)
        tend = 270
    L += [".control", "set wr_singlescale", "set wr_vecnames", f"tran 20n {tend}u 0 20n", f"wrdata {csv} {vecs}", ".endc"]
    return "\n".join(L) + "\n" + netlist(mut) + ".end\n"


def run(out, kind, corner, temp, vdd, mut="none"):
    import numpy as np
    temp, vdd = float(temp), float(vdd)
    tag = f"cz_{kind}_{corner}_{temp:g}_{vdd:g}_{mut}"
    if OPT:
        tag += "_o-" + "-".join(sorted(OPT - {"ladder"} if "ladder" in OPT else OPT))   # option runs never overwrite default ones
    base = os.path.join(out, tag)
    r = dict(tag=tag, kind=kind, corner=corner, temp=temp, vdd=vdd, mut=mut)
    if mut == "nocap" and "cap" not in OPT:        # without the flag nocap is identical to none: invalid, never a pass (review M2)
        r.update(verdict="REJECT", error="invalid: nocap needs CZ_OPT=cap (otherwise identical to none)")
        json.dump(r, open(base + ".json", "w"), indent=1)
        return r
    # kinds s0*: bare and wrapper in ONE deck aborted the transient at ~1.23 us (timestep too small, OTA-diode loads, WO-108
    # first pool); each is simulated alone and the wrapper columns are interpolated onto the bare time grid.
    parts = ("b", "z") if kind[:2] == "s0" else (None,)
    try:
        arrs = []
        for pt in parts:
            sfx = f"_{pt}" if pt else ""
            with open(base + sfx + ".cir", "w") as f:
                f.write(deck(kind, corner, temp, vdd, mut, base + sfx + ".txt", only=pt))
            p = subprocess.run(["ngspice", "-b", base + sfx + ".cir"], capture_output=True, text=True, timeout=5400)
            open(base + sfx + ".log", "w").write(p.stdout[-6000:] + p.stderr[-4000:])
            arrs.append(np.loadtxt(base + sfx + ".txt", skiprows=1))
        if kind[:2] == "s0":
            db, dz = arrs
            tt_ = db[:, 0]
            zi = [np.interp(tt_, dz[:, 0], dz[:, i]) for i in range(1, dz.shape[1])]
            # layout of the combined deck: t, 4 bare i, 4 wrapper i, bok, zok, v(bibtp), v(zibtp), v(zibn), vne, esn, e_ibn
            d = np.column_stack([tt_] + [db[:, i] for i in range(1, 5)] + zi[0:4] + [db[:, 5], zi[4], db[:, 6]] + zi[5:])
        else:
            d = arrs[0]
    except Exception as e:                     # noqa: BLE001
        r.update(verdict="REJECT", error=f"no data: {e}")
        json.dump(r, open(base + ".json", "w"), indent=1)
        return r
    t = d[:, 0]

    def win(y, a, b):
        m = (t >= a * U) & (t <= b * U)
        return float(y[m].mean())

    def mx(y, a, b):
        m = (t >= a * U) & (t <= b * U)
        return float(y[m].max()), float(y[m].min())
    g = {}
    names = ("ibtp", "ibp", "ivbl0", "ibn")
    if kind[:2] in ("s0", "lk"):
        bare = {n: d[:, 1 + i] for i, n in enumerate(names)}
        wrap = {n: d[:, 5 + i] for i, n in enumerate(names)}
        bok, zok = d[:, 9], d[:, 10]
        res = {}
        for lab, (a, b) in dict(base=(140, 150), boost=(256, 260)).items():
            for n in names:
                ib, iz = win(bare[n], a, b), win(wrap[n], a, b)
                res[f"{lab}_{n}"] = dict(bare=ib, wrap=iz, dev=(iz / ib - 1) if ib > 0 else 1.0, diff_nA=(iz - ib) * 1e9)
        alive = res["base_ibtp"]["bare"] > 0.3e-6
        okmin = float(min(bok[t >= 140 * U].min(), zok[t >= 140 * U].min()))
        lim = LIM["g1"] if kind[:2] == "s0" else LIM["g4"]
        worst = max(abs(v["dev"]) for v in res.values())
        gate = "G1" if kind[:2] == "s0" else "G4"
        g[gate] = dict(rows=res, worst=worst, ok_min=okmin, pass_=bool(alive and worst <= lim and okmin >= 0.9 * vdd))
        nodes = [d[:, 11 + i] for i in range(6)]
    else:
        col = {n: d[:, 1 + i] for i, n in enumerate(names)}
        ok = d[:, 5]
        vpt = {n: d[:, 7 + i] for i, n in enumerate(("ibtp", "ibp", "ivbl0", "ibn"))}
        inom = I_NOM * 1e6
        cur = {I: {n: win(col[n], e - WIN, e) for n in names} for I, e in END.items()}
        cur["5b"] = {n: win(col[n], T_BOOST[0] - WIN, T_BOOST[0]) for n in names}      # 5.35 uA again, boost still off
        cur["bst"] = {n: win(col[n], 240 - WIN, 240) for n in names}                   # boost on, 5.35 uA
        cur["bst10"] = {n: win(col[n], T_BOOST[1] - WIN, T_BOOST[1]) for n in names}   # boost on, 10 uA (info)
        trk, info = {}, {}
        for I in (2.5, 10.0, 1.0, 20.0, "5b"):
            Iv = inom if I == "5b" else I
            for n in names:
                v = (cur[I][n] / cur[inom][n]) / (Iv / inom) - 1 if cur[inom][n] > 0 else 1.0
                (info if I in (1.0, 20.0) else trk)[f"{I}_{n}"] = v
        # absolute limb: the harness value is a known input, expectation = PORT_I x I / 5.35 uA (at 5.35, 5.25 and 5.5 uA)
        rel = {n: cur[inom][n] / PORT_I[n] for n in names}
        rel_h = {f"{I}_{n}": cur[I][n] / (PORT_I[n] * I / inom) for I in (I_LO, I_HI) for n in names}
        rat = {n: (cur[inom][n] / cur[inom]["ibtp"]) / (PORT_I[n] / PORT_I["ibtp"]) - 1 for n in names if n != "ibtp"}
        br = {n: cur["bst"][n] / cur[inom][n] if cur[inom][n] > 0 else 0 for n in names}
        br10 = {n: cur["bst10"][n] / cur[10.0][n] if cur[10.0][n] > 0 else 0 for n in names}
        labs = lambda I: {n: (win(vpt[n], END[I] - WIN, END[I])) for n in names}   # noqa: E731
        lim_abs = LIM["tt"] if corner == "tt" else LIM["absn"]
        pp = (max(abs(v) for v in trk.values()) <= LIM["track"] and all(abs(v) <= LIM["ratio"] for v in rat.values())
              and all(abs(v / 2 - 1) <= LIM["boost"] / 2 for v in br.values())
              and all(abs(v - 1) <= lim_abs for v in rel.values()) and all(abs(v - 1) <= lim_abs for v in rel_h.values()))
        g["G2"] = dict(I=cur, track=trk, worst_track=max(abs(v) for v in trk.values()), rel=rel, rel_525_550=rel_h, ratio_err=rat,
                       boost_ratio=br,
                       info_track=info, info_boost10=br10, info_port_v=dict(i10=labs(10.0), i20=labs(20.0)), abs_lim=lim_abs,
                       pass_=bool(pp) or kind == "s1c", pass_info=bool(pp))   # s1c (100 pF): detect delay scales with C, the 5.25 uA
        # step (tau ~2.3 us) leaves a 6-11 % residual in its 4 us window -> G2 is info only there (review M1)
        ok_open = mx(ok, 10, 20)[0]
        i_open = max(abs(win(col[n], 10, 20)) for n in names)
        ok_hi = min(win(ok, END[inom] - WIN, END[inom]), win(ok, END[2.5] - WIN, END[2.5]), win(ok, T_BOOST[0] - WIN, T_BOOST[0]))
        ok_re = mx(ok, T_END - WIN, T_END)[0]
        i_re = max(abs(win(col[n], T_END - WIN, T_END)) for n in names)
        i_early = max(abs(win(col[n], 276, 280)) for n in names)       # 6-10 us after removal at 270 us (the 1/t tail of the pin)
        ok_early = win(ok, 276, 280)                                   # info only
        fall = (t >= 270 * U) & (ok < 0.5 * vdd)
        t_det = float((t[fall][0] - 270 * U) / U) if fall.any() else None   # info: us from removal until ok falls below VDD/2
        # s1c (100 pF): t_det ~ 7-18 us puts 276-280 us inside the tail (0.4-0.8 uA), so only the +60 us limb gates (review M1)
        early_ok = (i_early <= LIM["i_early"]) or kind == "s1c"
        g["G3"] = dict(ok_open_max=ok_open, i_open=i_open, ok_present_min=ok_hi, ok_info_1uA=win(ok, END[1.0] - WIN, END[1.0]),
                       ok_lost_max=ok_re, i_lost=i_re, i_lost_early=i_early, ok_early_info=ok_early, t_det_us=t_det,
                       pass_=bool(ok_open <= LIM["ok_lo"] * vdd and i_open <= LIM["i_open"] and ok_hi >= LIM["ok_hi"] * vdd
                                  and ok_re <= LIM["ok_lo"] * vdd and i_re <= LIM["i_open"] and early_ok))
        nodes = [d[:, 6 + i] for i in range(14)]
    hi = max(float(n.max()) for n in nodes)
    lo = min(float(n.min()) for n in nodes)
    # span_info is NOT part of the verdict: the rail limits already imply span <= VDD + 1.2 V = 4.8 V < 4.95 V (it can never decide).
    # TODO: real SPEC row 99 device-pair check on esc (drain esn vs gate bias_ext and source esd), needs those vectors recorded.
    g["stress"] = dict(v_max=hi, v_min=lo, span_info=hi - lo, span_info_lim=LIM["span"],
                       pass_=bool(hi <= vdd + LIM["rail"] and lo >= -LIM["rail"]))
    r["gates"] = g
    r["verdict"] = "ACCEPT" if all(v["pass_"] for v in g.values()) else "REJECT"
    tg_ = target(mut, kind) if mut in MUTS else None
    if tg_:
        r["target"] = tg_
        r["target_rejects"] = (tg_ in g) and not g[tg_]["pass_"]
    json.dump(r, open(base + ".json", "w"), indent=1)
    return r


def summary(out):
    rows = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out)) if f.startswith("cz_") and f.endswith(".json")]
    print("| run | detail | verdict |")
    print("|---|---|---|")
    for r in rows:
        if "gates" not in r:
            print(f"| {r['tag']} | {r.get('error')} | {r['verdict']} |")
            continue
        g = r["gates"]
        det = []
        for k in ("G1", "G4"):
            if k in g:
                det.append(f"{k} {'ok' if g[k]['pass_'] else 'FAIL'} worst {g[k]['worst']:.2e} okmin {g[k]['ok_min']:.2f}")
        if "G2" in g:
            det.append(f"G2 {'ok' if g['G2']['pass_'] else 'FAIL'} track {g['G2']['worst_track']:.3f}")
            c = g["G3"]
            det.append(f"G3 {'ok' if c['pass_'] else 'FAIL'} open {c['ok_open_max']:.2f}/{c['i_open'] * 1e9:.1f}nA on {c['ok_present_min']:.2f} "
                       f"lost {c['ok_lost_max']:.2f}/{c['i_lost'] * 1e9:.1f}nA early {c.get('i_lost_early', float('nan')) * 1e9:.1f}nA")
        det.append(f"stress {'ok' if g['stress']['pass_'] else 'FAIL'} [{g['stress']['v_min']:.2f},{g['stress']['v_max']:.2f}]")
        v = r["verdict"] if "target" not in r else ("REJECTS target " + r["target"] if r["target_rejects"]
                                                 else "DOES NOT REJECT " + r["target"])
        print(f"| {r['tag']} | {'; '.join(det)} | {v} |")


def job_list():
    L = [(k, c, t, v, "none") for c, t, v in CORNERS5 for k in ("s0", "lk", "s0e5", "s0e20", "lke5", "lke20", "s1")]
    L += [("s1", c, t, v, "none") for c, t, v in S1_EXTRA]
    L += [("s1z", c, t, v, "none") for c, t, v in (("tt", 27, 3.3), ("ff", 125, 3.6), ("ss", -40, 3.0))]
    L += [("s1c", c, t, v, "none") for c, t, v in (("tt", 27, 3.3), ("ss", -40, 3.0), ("ff", 125, 3.6))]
    L += [("s1", c, t, v, "nosu") for c, t, v in MUT_CORNERS]
    for m in MUTS:
        cs = MUT_CORNERS_RUPQ if m == "rupq" else MUT_CORNERS
        L += [(k, c, t, v, m) for k in MUT_KINDS[m] for c, t, v in MUT_RUNS.get((m, k), cs)]
    return L


def job_list_c():
    """WO-108c run list: (CZ_OPT, kind, corner, temp, vdd, mut), in the order B1 ladder, G1, G4, G3/G2, G2 mutants, stress."""
    tt, ss3, ff6 = ("tt", 27, 3.3), ("ss", -40, 3.0), ("ff", 125, 3.6)
    L = [(o, "s0", "ff", 125, 3.0, "none") for o in ("rs", "ab", "rs,ab")]                       # 1. B1 ladder
    L += [(o, "lk", "ff", 125, 3.6, "none") for o in ("rs", "rs,ab", "rs,ab,ramp", "ramp")]
    for c, t, v in (tt, ("ss", -40, 3.6)):                                                         # 1b. neutrality
        for k in ("s0", "lk"):
            L += [("", k, c, t, v, "none"), ("ladder", k, c, t, v, "none")]
    L += [("ladder", k, c, t, v, "none") for c, t, v in CORNERS5 for k in ("s0", "s0e5", "s0e20")]   # 2. G1
    L += [("ladder", "s0", c, t, v, "swapsel") for c, t, v in (tt, ff6)]
    L += [("ladder", "s0e5", c, t, v, "noiso") for c, t, v in (tt, ff6)]
    L += [("ladder", k, c, t, v, "none") for c, t, v in CORNERS5 for k in ("lk", "lke5", "lke20")]   # 3. G4
    L += [("ladder", "lke20", "ff", 125, 3.6, "noen")]
    L += [("ladder", k, c, t, v, m) for k, m in (("lk", "leaky"), ("lke20", "noiso")) for c, t, v in (tt, ff6)]
    L += [("ladder", "s1", c, t, v, "none") for c, t, v in CORNERS5 + S1_EXTRA]                   # 4. G3 (+G2 at 5.25/5.5 uA)
    L += [("ladder", "s1z", c, t, v, "none") for c, t, v in CORNERS5]
    L += [("ladder", "s1c", c, t, v, "none") for c, t, v in (tt, ss3, ff6)]
    L += [("ladder", "s1c", c, t, v, "noen") for c, t, v in MUT_RUNS[("noen", "s1c")]]
    L += [("ladder", "s1", c, t, v, "nodetect") for c, t, v in MUT_CORNERS]
    L += [("ladder", "s1z", c, t, v, "nopu") for c, t, v in MUT_CORNERS]
    L += [("ladder", "s1", c, t, v, "rupq") for c, t, v in MUT_CORNERS_RUPQ]
    L += [("ladder", "s1", c, t, v, m) for m in ("kwrong", "efinger", "nosu") for c, t, v in MUT_CORNERS]   # 5. G2 / variant
    L += [("ladder,cap", "s1z", c, t, v, "none") for c, t, v in (tt, ss3, ff6)]                  # 6. stress (cap on)
    L += [("ladder", "s1", c, t, v, "overv") for c, t, v in MUT_CORNERS]
    L += [("ladder,cap", "s1z", c, t, v, "nocap") for c, t, v in MUT_RUNS[("nocap", "s1z")]]
    return L


def gen_jobs():
    """Print one self-contained command per run (the committed design/cz/jobs_wo108c.txt is this output). <FROZEN> is a placeholder
    on purpose: `cd <FROZEN>` fails until it is replaced by the frozen tree."""
    pre = ("cd <FROZEN> && mkdir -p out/cz && . /home/mempool/tt-sd/.venv-sbx/bin/activate && "
           "export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A && ")
    for o, k, c, t, v, m in job_list_c():
        heavy = k.startswith("s1") or t > 100
        print(f"{pre}{'CZ_OPT=' + o + ' ' if o else ''}nice python design/cz/c6_cz.py run out/cz {k} {c} {t} {v} {m}"
              f"   # {'heavy' if heavy else 'light'}")


def jobs(out, frozen, jobfile):
    env = (". /home/mempool/tt-sd/.venv-sbx/bin/activate; "
           f"export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A; cd {frozen}")
    cmd = f"{env}; nice python design/cz/c6_cz.py run {out}"
    open(jobfile, "w").write("\n".join(f"{cmd} {k} {c} {t} {v} {m}" for k, c, t, v, m in job_list()) + "\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "netlist":
        txt = netlist(a[2] if len(a) > 2 else "none")
        (open(a[1], "w").write(txt) if len(a) > 1 and a[1] != "-" else sys.stdout.write(txt))
    elif a[0] == "gen-jobs":
        gen_jobs()
    elif a[0] == "jobs":
        jobs(*a[1:4])
    elif a[0] == "run":
        print(json.dumps(run(*a[1:]).get("verdict")))
    elif a[0] == "summary":
        summary(a[1])
