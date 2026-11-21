# C4 test cell (WO-107 item 1): the sg vg-connect NMOS 5/0.5 and the sin input TG (NMOS 12 / PMOS 36, L 0.5) from
# design/c4_sw/netlist.py SW, wired as a TG (shared a/b, gates pas_t/pas_c), plus one lsbuflv2hv_1 level shifter
# (netlist.py default ls_up cell, D78) with its split VPWR/VGND rails strapped. Routing: cells/route.tcl.
# Delay caps (WO-103 DCAP MOS pairs) are not in this cell yet. Broken copies: drcbad (met1 sliver), nostrap (VGND
# west strap omitted: VGND_uq0 floats -> LVS must fail).
source $env(LAYDIR)/cells/lib.tcl
source $env(LAYDIR)/cells/route.tcl
gds readonly true
gds read $::env(PDKPATH)/libs.ref/sky130_fd_sc_hvl/gds/sky130_fd_sc_hvl.gds
set HN nfet_g5v0d10v5; set HP pfet_g5v0d10v5
proc build {cell {broken none}} {
    global HN HP
    cellname create $cell
    load $cell
    rt::reset
    rt::row 0
    rt::fet Msg   $HN 5  0.5 vg sg_t  xs vss r 2.0
    rt::fet Msinn $HN 12 0.5 a  pas_t b  vss r 2.5
    rt::fet Msinp $HP 36 0.5 a  pas_c b  vdd r 2.0
    set y [rt::row_end]
    rt::row $y
    rt::ls fs vdl vss vdd fsh 2.0 [expr {$broken ne "nostrap"}]
    set y [rt::row_end]
    rt::finish {a b pas_t pas_c vg sg_t xs fs fsh vdd vdl vss} $y
    if {$broken eq "drc"} { rect metal1 -5.0 0 -4.95 3.0 }
    writeall force
}
build c4_sw
build c4_sw_drcbad drc
build c4_sw_nostrap nostrap
puts "C4 BUILD DONE"
quit -noprompt
