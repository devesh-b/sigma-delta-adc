"""C1a OTA1 SIZES draft (WO-20). Fully differential folded cascode, PMOS pfet_01v8 input pair on 3.3 V.

Status legend per entry (the "src" field):
  hand  = hand-derived in design/c1_ota1/DESIGN.md, not yet simulated
  op    = checked by the WO-20 .op/.ac/.noise spot runs (op_ac_check.py), tt + 4 extreme corners, ideal bias/CMFB
  open  = placeholder, sized in C1b/C6 (needs its own tb)

Devices: W_TOT = total width [um] built from M fingers of WF [um] (sky130 3.3 V fets are width-binned), L [um].
Names follow DESIGN.md section 1 (half circuit; every device except the tail exists twice, side a / side b).
Currents are BASE (boost=0). boost=1 scales every mirror by BOOST = 2 (D41, D43b: one switched reference leg).
"""

BOOST = 2.0

# Bias currents (base). I_TAIL from SR 12.5 V/us x C_L 1.4 pF = 17.5 uA, plus 5.7 % for trim residual (3 %) and mirror error.
I_TAIL = 18.5e-6          # src hand
K_FOLD = 1.35             # I_SINK / I_TAIL (SPEC >= 1.2, kept >= 1.2 with 10 % mirror error); src hand
I_SINK = K_FOLD * I_TAIL  # per side, 24.98 uA; src hand
I_LOAD = I_SINK - I_TAIL / 2   # per side at balance, 15.73 uA (set by CMFB); src hand

# Operating-point targets.
V_ICM = 1.20       # island / input CM [V]; src hand (D34 range 1.1-1.3)
V_OCM = 1.50       # output CM [V]; src hand
# Rev B (REVIEW-C1a M1/M3): no fixed V_FOLD / V_SDL / V_DIN any more.
#  - fold node and load-drain node come from Vdsat-tracking diode biases (wide-swing type): a diode copy of the
#    cascode at K_BIAS x its current density (same W per finger, L x K_BIAS) sets the cascode gate, so the
#    sink / load Vds = dVgs(K) which scales with Vov over corners (DESIGN.md 2.4).  src op (WO-21 unit run)
#  - m_pp gate tied to V_PC (fixed, ground); V_DIN floats at Vsg_pp (0.8-1.3 V).
K_BIAS_N = 8.0     # NMOS cascode bias density factor; src op (revb_unit_checks.py: K 4 -> 0.01 V, K 6 -> 0.05-0.09 V margin)
K_BIAS_P = 5.0     # PMOS cascode bias density factor; src op (K 4 -> 0.07-0.12 V, K 6 -> 0.16-0.27 V)
V_PC = 0.0         # protection-cascode gate [V] (VSS); src hand, M3
LOAD_FIXED = 0.75  # share of the load current in the fixed mirror half; the rest is the CMFB section m_plc (m2)

# Devices. Rev B = the proposal; REV_A keeps the WO-20 sizes for comparison.
SIZES = dict(
    m_in=dict(dev="pfet_01v8",      WF=10,  M=8,  L=0.5, src="op"),   # input pair W 80 L 0.5 (gm first, D51(2)); bulk = tail
    m_pp=dict(dev="pfet_g5v0d10v5", WF=5,   M=2,  L=0.5, src="op"),   # protection cascode, gate = V_PC
    m_t=dict(dev="pfet_g5v0d10v5",  WF=5,   M=8,  L=2.0, src="op"),   # tail, mirror 1:4 from m_tr
    m_tr=dict(dev="pfet_g5v0d10v5", WF=5,   M=2,  L=2.0, src="op"),   # tail reference diode (I_TAIL/4)
    m_n=dict(dev="nfet_g5v0d10v5",  WF=4.5, M=16, L=4.0, src="op"),   # fold sinks W 72 L 4 (M1), mirror 1:4
    m_nr=dict(dev="nfet_g5v0d10v5", WF=4.5, M=4,  L=4.0, src="op"),   # sink reference diode (I_SINK/4)
    m_nc=dict(dev="nfet_g5v0d10v5", WF=5,   M=4,  L=2.0, src="op"),   # NMOS cascodes W 20 L 2 (W x2, L 2)
    m_pc=dict(dev="pfet_g5v0d10v5", WF=5,   M=8,  L=2.0, src="op"),   # PMOS cascodes W 40 L 2
    m_pl=dict(dev="pfet_g5v0d10v5", WF=5,   M=16, L=4.0, src="op"),   # PMOS load, fixed half (75 %), W 80 L 4
    m_plc=dict(dev="pfet_g5v0d10v5", WF=5,  M=3,  L=2.0, src="op"),   # PMOS load, CMFB section (25 %), W 15 L 2
    m_bnc=dict(dev="nfet_g5v0d10v5", WF=5,  M=1,  L=16.0, src="op"),  # NMOS cascode bias diode, I_nc/4, L = K_BIAS_N x L_nc
    m_bpc=dict(dev="pfet_g5v0d10v5", WF=5,  M=1,  L=10.0, src="op"),  # PMOS cascode bias diode, I_nc/8, L = K_BIAS_P x L_pc
)
# Total load W at L 4 equivalent: 80 + 15*(4/2)*(1/3)... = about 107 um (DESIGN.md 2.4).

REV_A = dict(
    m_in=dict(dev="pfet_01v8",      WF=10, M=4, L=1.0, src="op"),
    m_n=dict(dev="nfet_g5v0d10v5",  WF=5,  M=8, L=4.0, src="op"),
    m_nc=dict(dev="nfet_g5v0d10v5", WF=5,  M=2, L=1.0, src="op"),
    m_pc=dict(dev="pfet_g5v0d10v5", WF=5,  M=4, L=1.0, src="op"),
    m_pl=dict(dev="pfet_g5v0d10v5", WF=5,  M=8, L=4.0, src="op"),
)

# Load and feedback network (tb values; SPEC 3.0)
C_L = 1.4e-12      # per side, loaded, incl. feedback network and CMFB caps (SPEC 3.0 OTA1 row)
BETA1 = 0.84       # SPEC; rev B design value 0.846 (Cp_vg 0.23 pF, DESIGN.md 2.2)

# SC CMFB (DESIGN.md 2.8); src hand, all open until the C1b CMFB tb
C_CMFB_SENSE = 0.10e-12   # Cc per side, output -> CMFB control node (inside C_L)
C_CMFB_REFRESH = 0.025e-12  # Cr per side, switched between (V_OCM, V_BL0) and (out, ctl) every phase
CMFB_SPLIT = 0.5          # fraction of each PMOS load driven by the CMFB node (the rest from a fixed mirror)

# Chopper (DESIGN.md 1.3); src open
CHOP_SW = dict(input=dict(dev="nfet_g5v0d10v5", W=2.0, L=0.5, src="op"),   # at the gates, 3.3 V clocks (M5); nfet_01v8 at 1.62 V is off (Ron > 60 MOhm)
               island=dict(dev="nfet_g5v0d10v5", W=2.0, L=0.5, src="op"),  # vg island / reset, closed by default (M4, Q1)
               fold=dict(dev="nfet_01v8", W=4.0, L=0.15, src="open"))    # between fold node and NMOS cascode source

# Fold-node MIM placeholder for fp2 placement (DESIGN.md 2.6); src open, value set from WO-22 / C1b (B)
C_FOLD_EXTRA = 0.0
