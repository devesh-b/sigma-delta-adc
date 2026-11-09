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

# Operating-point targets (drive the replica bias generators of DESIGN.md section 2.5)
V_ICM = 1.20       # island / input CM [V]; src hand (D34 range 1.1-1.3)
V_OCM = 1.50       # output CM [V]; src hand
V_FOLD = 0.45      # fold node = sink Vds [V]; src hand
V_DIN = 1.10       # input-pair drain = protection-cascode source [V]; src hand
V_SDL = 0.45       # PMOS load |Vds| [V]; src hand

# Devices. Variant "long" is the proposal; "short" is the comparison point of DESIGN.md section 2.4.
SIZES = dict(
    m_in=dict(dev="pfet_01v8",      WF=10, M=4, L=1.0, src="op"),   # input pair, bulk = tail (D40a)
    m_pp=dict(dev="pfet_g5v0d10v5", WF=5,  M=2, L=0.5, src="op"),   # protection cascode (D40a)
    m_t=dict(dev="pfet_g5v0d10v5",  WF=5,  M=8, L=2.0, src="op"),   # tail, mirror 1:4 from m_tr
    m_tr=dict(dev="pfet_g5v0d10v5", WF=5,  M=2, L=2.0, src="op"),   # tail reference diode (I_TAIL/4)
    m_n=dict(dev="nfet_g5v0d10v5",  WF=5,  M=8, L=4.0, src="op"),   # fold sinks, mirror 1:4 from m_nr
    m_nr=dict(dev="nfet_g5v0d10v5", WF=5,  M=2, L=4.0, src="op"),   # sink reference diode (I_SINK/4)
    m_nc=dict(dev="nfet_g5v0d10v5", WF=5,  M=2, L=1.0, src="op"),   # NMOS cascodes
    m_pc=dict(dev="pfet_g5v0d10v5", WF=5,  M=4, L=1.0, src="op"),   # PMOS cascodes
    m_pl=dict(dev="pfet_g5v0d10v5", WF=5,  M=8, L=4.0, src="op"),   # PMOS loads, gates = CMFB control
)

SIZES_SHORT = dict(SIZES)
SIZES_SHORT.update(
    m_n=dict(SIZES["m_n"], L=2.0), m_nr=dict(SIZES["m_nr"], L=2.0),
    m_nc=dict(SIZES["m_nc"], L=0.5), m_pc=dict(SIZES["m_pc"], L=0.5),
    m_pl=dict(SIZES["m_pl"], L=2.0),
)

# Load and feedback network (tb values; SPEC 3.0)
C_L = 1.4e-12      # per side, loaded, incl. feedback network and CMFB caps (SPEC 3.0 OTA1 row)
BETA1 = 0.84       # SPEC; DESIGN.md 2.2 shows the input-pair Cgs pushes it to about 0.82

# SC CMFB (DESIGN.md 2.8); src hand, all open until the C1b CMFB tb
C_CMFB_SENSE = 0.10e-12   # Cc per side, output -> CMFB control node (inside C_L)
C_CMFB_REFRESH = 0.025e-12  # Cr per side, switched between (V_OCM, V_BL0) and (out, ctl) every phase
CMFB_SPLIT = 0.5          # fraction of each PMOS load driven by the CMFB node (the rest from a fixed mirror)

# Chopper (DESIGN.md 1.3); src open
CHOP_SW = dict(input=dict(dev="nfet_01v8", W=1.0, L=0.15, src="open"),   # at the gates (vg side)
               fold=dict(dev="nfet_01v8", W=4.0, L=0.15, src="open"))    # between fold node and NMOS cascode source

# Fold-node capacitor for fp2 placement (DESIGN.md 2.7); src open, value from the C1b in-loop gate
C_FOLD_EXTRA = 0.0
