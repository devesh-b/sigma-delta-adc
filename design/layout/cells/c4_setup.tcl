# WO-107 netgen setup for c4_sw: the PDK setup, then compare lsbuflv2hv_1 at transistor level on both sides. Its GDS
# has split VPWR/VGND rails (extracted pins VPWR_uq0 / VGND_uq0) that the library spice does not have, so the
# subcircuit pin lists can never match; the straps join the rails at block level, and the flat transistor compare
# is the stronger check (every LS device and net is matched individually).
source $::env(PDKPATH)/libs.tech/netgen/sky130A_setup.tcl
flatten class "-circuit1 sky130_fd_sc_hvl__lsbuflv2hv_1"
flatten class "-circuit2 sky130_fd_sc_hvl__lsbuflv2hv_1"
