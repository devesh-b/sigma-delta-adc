"""C2 OTA2 sizes (WO-98, D91): the OTA1 cell (design/c1_ota1/sizes_draft.py) scaled to 9/16 at the same unit fingers.

Option B of results/wo93/README.md: tail, sinks and fixed loads use 18 of OTA1's 32 unit fingers, m_pc 9 of 16 fingers,
m_nc 2 x 5.625, m_plc 4 x 2.1 (W 8.4 L 2, unit-finger density = the OTA1 V_BL0 replica within 0.4 %), input pair 70/0.5
(WF 10 M 7), protection cascode W 5.625. Same L and current density everywhere, so Vdsat, swing, A0 and fp2 carry over.
The mirror gates tie to OTA1's bias nets (ibtp, ibn, ibp, ivbnc, ivbpc, ivbl0): OTA2 has no reference, replica or
cascode-bias legs (netlist_ota2.py drops them). It keeps its own dual-path CMFB (Cc, Cr, gm-C integrator, C_INT as OTA1).
No chopper in OTA2 (SPEC: chopper on OTA1 only); netlist_ota2.py wires the chopper positions straight (chop=False).
src "hand" for every scaled entry until the C2 bench (c2_bench.py) confirms it. OTA1 sizes are not touched.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "c1_ota1"))
import sizes_draft as S  # noqa: E402

SCALE = 9 / 16
SIZES = {k: dict(v) for k, v in S.SIZES.items()}
_OVR = dict(m_t=dict(M=18), m_n=dict(M=18), m_pl=dict(M=18), m_pc=dict(M=9), m_nc=dict(WF=5.625, M=2),
            m_plc=dict(WF=2.1, M=4), m_in=dict(WF=10, M=7), m_pp=dict(WF=5.625, M=1))
for _k, _v in _OVR.items():
    SIZES[_k].update(_v, src="hand")

I_TAIL2 = S.I_TAIL * 18 / 32            # 10.4 uA base, x2 boost (through OTA1's references)
I_SINK2 = S.I_SINK * 18 / 32

# C2 slot (SPEC 3.0 OTA2 rows, results/wo93 section 1)
CS2, CK2, CINT2 = 0.5e-12, 0.25e-12, 1.0e-12
C_L2 = 0.7e-12            # loaded basis per side (SR = I_tail / C_L2, GBW into 0.7 pF)
C_EXT2 = 0.07e-12         # comparator input + junction/routing per side on top of the real feedback caps (CT bench)
BETA2 = 0.53              # design (Cp ~0.14 pF); SPEC floor 0.497
BETA2_MIN = 0.497

# Hand Pelgrom per device (project convention, sizes_draft: sigma(VT) = A / sqrt(W L) per device)
MC_DEV = {"min1": "m_in", "min2": "m_in", "mn1": "m_n", "mn2": "m_n", "mnc1": "m_nc", "mnc2": "m_nc",
          "mpc1": "m_pc", "mpc2": "m_pc", "mpl1": "m_pl", "mpl2": "m_pl", "mplc1": "m_plc", "mplc2": "m_plc"}


def sig_vt(key, sizes=None):
    p = (sizes or SIZES)[key]
    a = S.A_VT_PAIR if key == "m_in" else S.A_VT_HV
    return a / math.sqrt(p["WF"] * p["M"] * p["L"])


def gate_area_um2(sizes=None):
    """Gate-area sum of the OTA2 devices (both halves, tail once, CMFB integrator), no bias legs."""
    z = sizes or SIZES
    a = lambda k: z[k]["WF"] * z[k]["M"] * z[k]["L"]
    return a("m_t") + 2 * sum(a(k) for k in ("m_in", "m_pp", "m_n", "m_nc", "m_pc", "m_pl", "m_plc", "m_ia", "m_il")) + a("m_it")
