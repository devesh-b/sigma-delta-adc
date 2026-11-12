#!/usr/bin/env python3
"""C3 comparator sizes (WO-48, D74 set A'; DESIGN.md section 5). The netlist itself is built by netlist.py.

Topology (DESIGN.md section 1): NMOS-input StrongARM on VDPWR (1.8 V).
  * Input pair: 5 V devices (nfet_g5v0d10v5). The gates sit on x2 (OTA2 output, 3.3 V domain, up to VAPWR on
    overload / power-up). Accepted as a C3 exception to D40(a) (D74).
  * Tail: 1.8 V nfet_01v8 (D74, REVIEW-C3a item 4). Its drain `tl` is the common source of the input pair, whose
    drains are precharged to VDPWR, so tl <= VDPWR: no HV needed, and the 1.8 V gate gives more strobe overdrive.
  * Latch, precharge, buffers, NAND SR latch, output buffer: 1.8 V core devices.
Set A' (D74): set A input pair (5/0.5 x4 per side, CM kick ~45 mV as spotted) + set B latch (4/0.5): ~17.7 mV 3 sigma.
"""

PRE = "sky130_fd_pr__"
HVN, NF, PF = PRE + "nfet_g5v0d10v5", PRE + "nfet_01v8", PRE + "pfet_01v8"

# W, L in um; m = parallel instances. HV devices use 5 um unit fingers (width bins, as ttsky-sigma-delta).
SIZES = dict(
    IN=dict(W=5.0, L=0.5, m=4),    # HV input pair, per side: 10 um^2 (offset, DESIGN.md 3.1)
    TAIL=dict(W=4.0, L=0.5, m=2),  # 1.8 V clocked tail (D74), gate = strobe
    LN=dict(W=4.0, L=0.5, m=1),    # 1.8 V cross-coupled NMOS (sources on dp/dn), set B
    LP=dict(W=4.0, L=0.5, m=1),    # 1.8 V cross-coupled PMOS, set B
    RS=dict(W=1.0, L=0.15, m=1),   # 1.8 V PMOS precharge, 4x (op, on, dp, dn)
    BN=dict(W=0.5, L=0.15, m=1),   # regeneration-node buffers (2 inverters per side), NMOS
    BP=dict(W=1.0, L=0.15, m=1),   # same, PMOS
    SN=dict(W=1.0, L=0.15, m=1),   # NAND SR latch NMOS
    SP=dict(W=1.0, L=0.15, m=1),   # NAND SR latch PMOS
    O1N=dict(W=0.5, L=0.15, m=1),  # output buffer stage 1 (REVIEW-C3a item 7: drive the routed q net)
    O1P=dict(W=1.0, L=0.15, m=1),
    O2N=dict(W=2.0, L=0.15, m=1),  # output buffer stage 2
    O2P=dict(W=4.0, L=0.15, m=1),
)
# Routed q / qb load to the C9 capture flop (estimate until layout: ~300 um of met2 at ~0.2 fF/um + D pin, rounded
# up). The 5 fF of WO-44 was optimistic (REVIEW-C3a item 7); the output buffer makes the latch independent of it.
C_Q_LOAD = 100e-15

# Hand numbers used by the testbench gates (DESIGN.md 3.1 / 3.3)
SIGMA_OS_HAND = 17.7e-3 / 3        # set A' offset, 1 sigma (REVIEW-C3a item 2)
AVT_TOTAL_HV = 12.0                # mV*um, D74 basis for the HV input pair, total
AVT_TT_MM_HV = 9.3                 # mV*um equivalent the PDK tt_mm already gives the HV pair (toxe, WO-44 probe)
TDEC_SPOT_SS40 = 1.120e-9          # WO-44 spot t_dec at 1 mV, ss/-40/1.62 V (T2 band reference)

# Broken copies built into the subckt (netlist.py); tb-level ones live in c3_tb.py.
#   starve : tail 1/4 x1 instead of 4/0.5 x2 (64x less W/L)       -> T2 band row REJECT
#   qswap  : buffer outputs swapped into the SR latch (pthomas Q/QB) -> T1 polarity REJECT
#   nobuf  : SR latch gates directly on op/on (buffers removed)      -> T7 hysteresis/memory REJECT
#   nolatch: SR latch removed, q/qb = buffered on/op (transparent)   -> T10 near-zero / capture REJECT
#   in18   : input pair as nfet_01v8                                -> T8 device stress REJECT
MUTS = ("starve", "qswap", "nobuf", "nolatch", "in18")


def comp_subckt(mut=""):
    """Compatibility shim for spot_tran.py (WO-44): the netlist now lives in netlist.py."""
    from netlist import comp_subckt as _c
    return _c(mut=mut)
