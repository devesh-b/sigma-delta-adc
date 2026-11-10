"""C1 OTA1 SIZES, rev C (+ WO-27 / D60 at the end of this docstring) + WO-24 (C1b part 1) candidate. Fully differential folded cascode, PMOS pfet_01v8 input pair on 3.3 V.

Status legend per entry (the "src" field):
  hand  = hand-derived in design/c1_ota1/DESIGN.md, not yet simulated
  op    = checked by a spot run (WO-21 op_ac_check.py / WO-23 revc_check.py), ideal reference currents, ideal CMFB
  open  = placeholder, sized in C1b/C6 (needs its own tb)

Devices: W_TOT = WF x M [um] (M fingers of WF; sky130 3.3 V fets are width-binned), L [um].
Names follow DESIGN.md section 1 (half circuit; every device except the tail and the bias diodes exists twice).
Currents are BASE (boost=0). boost=1 scales every reference by BOOST = 2 (D41, D43b: one switched reference leg).

Rev C (WO-23) vs rev B:
  - input pair 80/0.5 -> 120/0.5 at the same current (D54);
  - m_pc 40/2 -> 80/2 (swing fix, REVIEW-C1a-revB Q2);
  - cascode-bias diodes narrowed so that K holds at I_nc/32 (RB-M1): m_bnc W 0.625 L 16 (K_N 8), m_bpc W 1.25 L 7
    at I_nc/32 against m_pc 80/2 (K_P 7; K_P = (I_d/(W/L)_d) / (I_nc/(W/L)_pc));
  - reference diodes of the mirrors at 1:32 (CL-7 relaxed toggle settling, D53), narrow single fingers;
  - CMFB split derived from LOAD_FIXED (was CMFB_SPLIT 0.5, inconsistent: RB-m3);
  - chopper input switch W 4 (was 2.0 here, 4 in the note: RB-m3); island switch = shunt to V_ICM (RB-m4).

WO-24 (REVIEW-C1a-revC RC-M1 / RC-M2, D55, D56; src "hand" until the WO-24 sweep / netlisted op confirm it):
  - K_P base 8 -> 10 (vbpc base I_NC/22.4); boost stays at K_P 7 (BOOST_SCALE vbpc 0.7, CL-8 increment x1.4);
  - D55 (user): m_plc 15/2 -> 30/4 (WF 5 M 6 L 4, same W/L), Cc 0.1 -> 0.2 pF, Cr 25 -> 50 fF;
  - RC-M2: the 1:32 mirror references (m_tr, m_nr, m_plr) are series-parallel composites of REF_COMPOSITE unit fingers
    (same WF and L as the mirror finger): P in parallel x S in series -> W/L of one finger, 16 x the gate area (sigma/4);
  - V_BL0 replica = VBL0_SERIES m_plc fingers in series (ratio M_plc x VBL0_SERIES : 1), current I_REF["vbl0"];
  - netlist: design/c1_ota1/netlist.py builds the subckt from this file (no sizes live in the generator).

WO-25 (D58, user 2026-11-10):
  - REF_TRIM: the I_REF ports are scaled by 1 / (composite-to-mirror ratio at tt) so the tail / sink / fixed-load /
    V_BL0 currents sit on the design values at tt (the 4x4 composites with bulk at the rail mirror ~+20 %, WO-24);
  - cascode-bias diodes fed from a REPLICA of the folded branch: tail replica (1 m_t unit finger, gate ibtp) and sink
    replica (2 m_n unit fingers, gate ibn) on node ivbpc, so the vbpc diode bank m_bpd carries (2 I_SINK - I_TAIL)/32
    = I_NC/16 of the ACTUAL mirrors; a copy bank m_bpx (same unit, same switching) feeds I_NC/16 to the vbnc diode
    m_bnd. K_P / K_N then track the real I_NC over PVT. Boost (CL-8): the m_bpd / m_bpx banks go 5 -> 7 unit
    fingers (K_P 10 -> 7.14; K_N stays 8 since the copy bank switches with it). The ivbpc / ivbnc ports stay for
    observation; their reference current is 0. Legacy m_bpc / m_bnc stay for the revc spot deck only;
  - D55 reverted: m_plc 30/4 -> 15/2 (WF 5 M 3 L 2), Cc 0.2 -> 0.1 pF, Cr 50 -> 25 fF.

WO-26 (D59, user 2026-11-10; supersedes the D58 trim, the D58 replica cascode bias stays):
  - references m_tr, m_nr, m_plr and the V_BL0 replica are PARALLEL-ONLY unit fingers at RATIO 1:8 (M_ref = M_mirror / 8,
    same WF / L / bulk as the mirror finger); REF_TRIM removed; I_REF = design current / 8. m_plc re-fingered 3 x 5/2 ->
    8 x 1.875/2 (same W 15 L 2) so the V_BL0 replica is 1 unit finger (1:8). Layout intent: DESIGN.md 1.1 (C7);
  - K_P base 12.5 (KP_BANK base 5 -> 4), boost stays 7 fingers (K_P 7.14);
  - replica: REPLICA tail 2 / sink 4 unit fingers (2x WO-25), derived from m_t / m_n in code; the sink replica is cascoded
    by one m_nc unit finger (m_rnc) so its drain sits near the fold node instead of ~2 V. m_rnc gate = rcb, an NMOS
    diode with the m_bnc geometry (K_N ~6) fed by ONE m_pl unit finger (gate ibp, I_NC*0.75/32, +0.37 uA base): it
    tracks ivbnc over PVT and boost without the ivbnc loop (an ivbnc-gated cascode adds a zero-current state). WO-26 run 1
    used gate V_ICM: the replica drain fell to 0.09-0.16 V in boost / cold while fa rose (K_P boost 3.6-6.2, REJECTED); m_bpd unit 1.5/15 (I_NC/8), copy bank m_bpx 0.75/15 (half width -> I_NC/16
    to m_bnd, K_N 8, no extra copy-leg current);
  - bank switch in the GATE path: the boost-only fingers of m_bpd / m_bpx (KP_BANK boost - base) have their gates on
    node gbk, a TG to ivbpc (closed in boost) and a pull-up to vdd (on in base); no switch in series with a diode.

WO-27 (D60, user 2026-11-10):
  - I_REF_btp recentred +1.9 % (BTP_RECENTRE); the mirror-ratio rows are info-only (systematic CLM/DIBL accepted);
  - hand-Pelgrom mismatch allotments (A_VT_HV, A_B_HV, N_SIGMA) on the SR / ceiling / V_OCM rows (DESIGN.md 2.11);
  - continuous-time CM error amplifier inside the SC CMFB loop (CM_AMP, DESIGN.md 1.3a); m_rcb narrowed to W 0.47.

WO-28 (D61, user 2026-11-10):
  - CMFB = dual path (INTEG, DESIGN.md 1.3b): passive SC fast path onto ctl + gm-C follower-integrator ctl -> bli (the Cr
    refresh level); the WO-27 CM amp is removed. Start-up clamps ctl / bli -> ivbl0 and outputs -> vocm (rstb low);
  - tail unit finger 1.25/2 -> 3.75/6 (m_t and, derived, m_tr / m_rt): reference area x9 at the same current density.
"""

BOOST = 2.0

# Bias currents (base). I_TAIL from SR 12.5 V/us x C_L 1.4 pF = 17.5 uA, plus 5.7 % for trim residual (3 %) and mirror error.
I_TAIL = 18.5e-6          # src hand
K_FOLD = 1.35             # I_SINK / I_TAIL (SPEC >= 1.2, kept >= 1.2 with 10 % mirror error); src hand
I_SINK = K_FOLD * I_TAIL  # per side, 24.98 uA; src hand
I_NC = I_SINK - I_TAIL / 2     # cascode / load current per side at balance, 15.73 uA (set by CMFB); src hand
I_LOAD = I_NC                  # legacy name

# Operating-point targets.
V_ICM = 1.20       # island / input CM [V]; src hand (D34 range 1.1-1.3)
V_OCM = 1.50       # output CM [V]; src hand
V_PC = 0.0         # protection-cascode gate [V] (VSS); src hand, M3
K_BIAS_N = 8.0     # NMOS cascode bias density factor; src op (WO-23 K sweep)
K_BIAS_P = 12.5    # WO-26 (D59): base K_P 12.5 (KP_BANK base 4), boost 12.5 x 4 / 7 = 7.14. WO-24: base K_P 10 (RC-M1), boost K_P 7 (BOOST_SCALE vbpc 0.7); rev C was 8 base / 7 boost. Old note:
                   # PMOS cascode bias density factor in BOOST (geometry L 7 at I_NC/16); BASE runs at 8 (I_NC/28); src op
                   # (run 3 K 6: m_pl 0.015-0.107 V; run 4 K 7 / K 8 rows; WO-23 K run 2: K 4 -> m_pl in
                   # triode by 0.04-0.06 V, K 5 -> +0.01-0.04 V; the narrow W 1.25 diode tracks weaker than the rev B finger copy)
LOAD_FIXED = 0.75  # share of the load current in the fixed mirror half m_pl
CMFB_SPLIT = 1.0 - LOAD_FIXED   # share in the CMFB-driven section m_plc (0.25); derived, do not set separately

# Reference ratios (reference diode current : mirrored current). 1:32 everywhere (CL-7 / D53: 0.1 % in <= 4 us).
RATIO = 8                # WO-26 (D59): 1:8 parallel-only unit-finger references (was 1:32 composites)
I_REF = dict(            # base reference currents [A]; boost x2. src hand (settling: DESIGN.md 2.9)
    btp=I_TAIL / RATIO * 1.019,         # tail reference m_tr          2.357 uA (D60: recentred +1.9 %, BTP_RECENTRE)
    bn=I_SINK / RATIO,                  # sink reference m_nr          3.122 uA
    bp=I_NC * LOAD_FIXED / RATIO,       # fixed-load reference m_plr   1.475 uA
    vbnc=0.0,                           # WO-25 (D58): replica-fed (m_bpx -> m_bnd), no reference current
    vbpc=0.0,                           # WO-25 (D58): replica-fed (tail + sink replica on ivbpc), no reference current
    vbl0=None,                          # V_BL0 replica current, set below from the m_plc geometry
)
# Per-reference boost scale on top of BOOST (default 1). vbpc: boost current = 2 x 0.875 x I_NC/28 = I_NC/16
# -> K_P 7 in boost. Run 4: one K cannot serve both modes: K_P 7 leaves m_pl 0.043/0.049 V at fs/-40 and ff/-40 BASE,
# K_P 8 cuts the ss/125 BOOST span to 1.355 V (< 1.40). Base has >= 1.8 V span, so base runs at K 8, boost at K 7.
BOOST_SCALE = dict()   # WO-25: the CL-8 boost step is the m_bpd bank switch (KP_BANK), not a reference current
I_VCM_SRC = dict(vicm=1.0e-6, vocm=1.0e-6)   # V_ICM / V_OCM source allowance per OTA1 [A], NOT boosted; src open (C6)

# Devices. Rev C. REV_B / REV_A keep earlier sizes for comparison.
SIZES = dict(
    m_in=dict(dev="pfet_01v8",      WF=10,  M=12, L=0.5, src="op"),   # input pair W 120 L 0.5 (D54: +1.5 % GBW at fs/125, beta1 0.838-0.842); bulk = tail
    m_pp=dict(dev="pfet_g5v0d10v5", WF=5,   M=2,  L=0.5, src="op"),   # protection cascode, gate = V_PC
    # Mirrors are unit-finger: the reference diode is ONE finger of the mirrored device (same WF, L), the device has
    # 32 fingers -> 1:32. (First rev C K run used narrower single-finger references with WF != device WF: the
    # narrow-width Vth shift gave I_fold/I_tail 1.7-2.6 instead of 1.35 and put m_pl/m_plc in triode. REJECTed, fixed.)
    m_t=dict(dev="pfet_g5v0d10v5",  WF=3.75, M=32, L=6.0, src="hand"),  # tail W 120 L 6, 32 unit fingers. WO-28 (D61):
    # unit finger x3 in W and L (was 1.25/2: same W/L, same current density, 9x area) -> m_t 720 um2, m_tr 90 um2,
    # sigma(I_tail) / 2.9 for the SR - 3 sigma / ceiling + 3 sigma rows
    m_n=dict(dev="nfet_g5v0d10v5",  WF=2.25, M=32, L=4.0, src="op"),  # fold sinks W 72 L 4 (M1), 32 unit fingers
    m_nc=dict(dev="nfet_g5v0d10v5", WF=5,   M=4,  L=2.0, src="op"),   # NMOS cascodes W 20 L 2
    m_pc=dict(dev="pfet_g5v0d10v5", WF=5,   M=16, L=2.0, src="op"),   # PMOS cascodes W 80 L 2 (rev C, was 40/2)
    m_pl=dict(dev="pfet_g5v0d10v5", WF=2.5, M=32, L=4.0, src="op"),  # PMOS load, fixed half (75 %), W 80 L 4, 32 unit fingers
    m_plc=dict(dev="pfet_g5v0d10v5", WF=1.875, M=8, L=2.0, src="hand"),  # PMOS load, CMFB section (25 %), W 15 L 2; D59: 8 unit fingers
    m_bnc=dict(dev="nfet_g5v0d10v5", WF=0.625, M=1, L=16.0, src="op"),  # NMOS cascode bias diode at I_NC/32: K_N 8
    m_bpc=dict(dev="pfet_g5v0d10v5", WF=1.25, M=1, L=7.0, src="op"),    # PMOS cascode bias diode at I_NC/32: K_P 7
    # WO-25 (D58) replica-fed cascode bias (see docstring). M = base fingers; boost uses KP_BANK["boost"] fingers.
    m_bpd=dict(dev="pfet_g5v0d10v5", WF=1.5, M=4, L=15.0, src="hand"),   # vbpc diode bank, I_NC/8: K_P 12.5 base, 7.14 boost
    m_bpx=dict(dev="pfet_g5v0d10v5", WF=0.75, M=4, L=15.0, src="hand"),  # copy bank (gate vbpc, half width) -> m_bnd, I_NC/16
    m_bnd=dict(dev="nfet_g5v0d10v5", WF=1.25, M=1, L=16.0, src="hand"),  # vbnc diode at I_NC/16: K_N 8
)


def k_density(diode, cas, i_diode, i_cas):
    """Density factor K = (I/(W/L)) of the bias diode over that of the cascode it biases."""
    wl = lambda d: d["WF"] * d["M"] / d["L"]
    return (i_diode / wl(diode)) / (i_cas / wl(cas))


REV_B = dict(
    m_pc=dict(dev="pfet_g5v0d10v5", WF=5, M=8, L=2.0, src="op"),
    m_bnc=dict(dev="nfet_g5v0d10v5", WF=5, M=1, L=16.0, src="op"),   # ran at I_NC/4 (K 8); at I_NC/32 K 1 (RB-M1)
    m_bpc=dict(dev="pfet_g5v0d10v5", WF=5, M=1, L=10.0, src="op"),   # ran at I_NC/8 (K 5); at I_NC/32 K 1.25
)
REV_A = dict(
    m_in=dict(dev="pfet_01v8",      WF=10, M=4, L=1.0, src="op"),
    m_n=dict(dev="nfet_g5v0d10v5",  WF=5,  M=8, L=4.0, src="op"),
    m_nc=dict(dev="nfet_g5v0d10v5", WF=5,  M=2, L=1.0, src="op"),
    m_pc=dict(dev="pfet_g5v0d10v5", WF=5,  M=4, L=1.0, src="op"),
    m_pl=dict(dev="pfet_g5v0d10v5", WF=5,  M=8, L=4.0, src="op"),
)

# Load and feedback network (tb values; SPEC 3.0)
C_L = 1.4e-12      # per side, loaded, incl. feedback network and CMFB caps (SPEC 3.0 OTA1 row)
BETA1 = 0.84       # SPEC (CL-4 proposal >= 0.83); design value 0.846 (Cp_vg 0.23 pF, DESIGN.md 2.2)

# SC CMFB (DESIGN.md 1.3); src hand, all open until the C1b CMFB tb. Drives m_plc only (CMFB_SPLIT of the load).
C_CMFB_SENSE = 0.10e-12     # Cc per side, output -> CMFB control node (inside C_L); D58: D55 reverted (back to rev C)
C_CMFB_REFRESH = 0.025e-12  # Cr per side, switched between (V_OCM, V_BL0) and (out, ctl) every cycle; D58 (rev C value)
CMFB_SW = dict(n=dict(dev="nfet_g5v0d10v5", W=1.0, L=0.5), p=dict(dev="pfet_g5v0d10v5", W=2.0, L=0.5), src="hand")  # TG, 3.3 V
CTL_RST = dict(dev="pfet_g5v0d10v5", W=1.0, L=0.5, src="hand")   # ctl -> V_BL0 clamp while rst (gate rst_b low = closed)

BTP_RECENTRE = 1.019   # D60 (WO-27): I_REF_btp +1.9 % (mirror ratio m_t/m_tr sits ~2 % low, systematic CLM/DIBL, accepted)

# D60 (WO-27) mismatch allotments, HAND Pelgrom (REVIEW-WO26 M1: the sky130 HV MC has no Vth term, vth0_slope = 0).
# sigma(dVT) = A_VT * sqrt(1/WL_a + 1/WL_b) [V, um^2]; sigma(dI/I) = sqrt((gm/I * sigma_dVT)^2 + (A_B * sqrt(..))^2).
A_VT_HV = 12e-3      # V.um, g5v0d10v5 (conservative end of 8-12 mV.um); the rows gate at this value
A_VT_HV_LO = 8e-3    # V.um, info column (optimistic end)
A_B_HV = 0.01        # 1 %.um current-factor mismatch
N_SIGMA = 3.0

# D59 references (WO-26): parallel-only unit fingers of the mirror, 1:RATIO. DERIVED, do not size by hand.
for _ref, _mir in (("m_tr", "m_t"), ("m_nr", "m_n"), ("m_plr", "m_pl"), ("m_bl0", "m_plc")):
    assert SIZES[_mir]["M"] % RATIO == 0, _mir
    SIZES[_ref] = dict(SIZES[_mir], M=SIZES[_mir]["M"] // RATIO, src="hand")
I_REF["vbl0"] = I_NC * CMFB_SPLIT / RATIO   # V_BL0 replica, 1 m_plc unit finger: 0.492 uA base
# D59 replica (WO-26): REPLICA unit fingers of m_t / m_n (sink = 2 x tail so I(m_bpd) = tail x I_NC/16); sink replica
# cascoded by one m_nc unit finger with gate REPLICA_CASC_GATE. DERIVED from m_t / m_n / m_nc, do not size by hand.
REPLICA = dict(tail=2, sink=4)
REPLICA_CASC_GATE = "rcb"     # WO-26 run 2 (run 1: "vicm", rejected)
SIZES["m_rcp"] = dict(SIZES["m_pl"], M=1, src="hand")    # rcb feed: 1 m_pl unit finger, gate ibp
SIZES["m_rcb"] = dict(SIZES["m_bnc"], WF=0.47, src="hand")   # rcb diode: m_bnc L 16, W 0.47 (WO-27 review minor: was 0.625)
SIZES["m_rt"] = dict(SIZES["m_t"], M=REPLICA["tail"], src="hand")
SIZES["m_rn"] = dict(SIZES["m_n"], M=REPLICA["sink"], src="hand")
SIZES["m_rnc"] = dict(SIZES["m_nc"], M=1, src="hand")
I_BPD_FRAC = REPLICA["tail"] / 16            # I(m_bpd) / I_NC = (sink I_SINK - tail I_TAIL) / 32 / I_NC = 1/8
I_BND_FRAC = I_BPD_FRAC * SIZES["m_bpx"]["WF"] / SIZES["m_bpd"]["WF"]   # copy bank -> m_bnd: 1/16
BANK_SW = dict(CMFB_SW, src="hand")          # gate-path bank switch (TG gbk <-> ivbpc) and gbk pull-up (p)
# Broken-copy geometry only (mut "ref_composite"): the D58 4 x 4 series-parallel composites
REF_COMPOSITE = dict(P=4, S=4)

# Chopper and vg switches (DESIGN.md 1.4), 3.3 V devices with 3.3 V clocks (M5)
CHOP_SW = dict(
    input=dict(dev="nfet_g5v0d10v5", W=4.0, L=0.5, src="op"),   # at the gates; nfet_01v8 at 1.62 V is off (Ron > 60 MOhm)
    island=dict(dev="nfet_g5v0d10v5", W=2.0, L=0.5, src="op",  # SHUNT from each vg island node to V_ICM (RB-m4), closed by
                topology="shunt to V_ICM", ron_ohm_max=5e3,      # default (M4, Q1). Ron ~5 kOhm (2x the W 4 row); own row:
                reset_residue_max=1e-4),                         # reset residue <= 1e-4 within the reset window (216 ns at 4 MHz)
    fold=dict(dev="nfet_01v8", W=4.0, L=0.15, src="open"))      # between fold node and NMOS cascode source

# Fold-node MIM placeholder for fp2 placement (DESIGN.md 2.6); src open, value set from WO-22 / C1b (B)
C_FOLD_EXTRA = 0.0

# WO-25 (D58): replica bank switching and reference trim
KP_BANK = dict(base=4, boost=7)   # m_bpd / m_bpx unit fingers per mode (D59: K_P 12.5 base -> 7.14 boost, CL-8 step x1.75)
# D59: REF_TRIM removed (parallel-only 1:8 references track by construction)

# WO-28 (D61): DUAL-PATH CMFB (DESIGN.md 1.3b). The WO-27 CT CM amp is removed.
#  fast path = the passive SC CMFB of WO-26: Cc (outputs -> ctl, m_plc gates), Cr refreshed to (V_OCM, bli) and shared
#    with (out, ctl): averaged, ctl = V_outcm - V_OCM + V(bli);
#  slow path = gm-C follower-integrator from ctl into bli: a 5T NMOS-pair OTA (pair m_ia, gate ctl -> diode side cid,
#    gate bli -> drain bli; PMOS mirror loads m_il; tail = INTEG["tail"] m_n unit fingers on ibn, x2 in boost with the
#    sink reference) with C_INT from bli to vdd. At DC bli = ctl - V_os,int - (V_need - V_dio)/A_int, so
#    V_outcm - V_OCM = V_os,int + (V_need - V_dio)/A_int: the integrator pair offset is the V_OCM sigma, everything the
#    passive loop used to pass 1:1 (V_BL0 replica error, sink / load / tail mismatch, PVT drift of V_need) is divided by
#    A_int. In the CM loop the slow path is a PI zero at f_z = gm_ia / (2 pi C_INT), kept <= f_cm / 10.
#  loads are sized at the m_plc current density (V_dio ~ V_need: small systematic term) and long L (low gm_il / gm_ia).
#  Start-up (rstb low, D57 start-up clamp, tb9 fix): ctl -> ivbl0, bli -> ivbl0 and both outputs -> vocm, so Cc stores
#    the operating charge (V_OCM - V_BL0) and Cr / C_INT start at the operating point (WO-27 tb9: the unclamped output
#    CM sat at 2.9 V during the clamp and relaxed at the Cr refresh rate).
INTEG = dict(tail=1)
SIZES["m_ia"] = dict(dev="nfet_g5v0d10v5", WF=2.5, M=2, L=14.0, src="hand")    # pair, W 5 L 14 (70 um2) per side
SIZES["m_il"] = dict(dev="pfet_g5v0d10v5", WF=3.0, M=2, L=16.0, src="hand")    # loads, W 6 L 16 (96 um2) per side
SIZES["m_it"] = dict(SIZES["m_n"], M=INTEG["tail"], src="hand")                 # tail: m_n unit finger(s), gate ibn
C_INT = 2.0e-12          # bli MIM to vdd (~1000 um2): f_z = gm_ia / (2 pi C_INT) ~0.4 MHz base / ~0.75 MHz boost (hand, <= f_cm / 10)
BLI_RST = dict(CTL_RST)  # bli -> ivbl0 clamp while rstb low (start-up only, D57)
OUT_RST = dict(dev="pfet_g5v0d10v5", W=4.0, L=0.5, src="hand")   # outp / outn -> vocm while rstb low (start-up only)
REPLICA_DV_MAX = 0.15    # WO-28 item 4: |V_rnd - V_fa| (sink replica drain vs m_n drain) [V]
