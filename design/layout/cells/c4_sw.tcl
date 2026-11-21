# C4 first devices (WO-96 cell b): sg vg-connect NMOS 5/0.5 and the sin input TG devices 12/36 at L 0.5
# (design/c4_sw/netlist.py SW, nfet/pfet_g5v0d10v5), plus one lsbuflv2hv_clkiso_hlkg_3 level shifter (PDK hvl cell).
# Devices from the sky130 gencell (guard rings on); TG wiring is the next step (README).
source $env(LAYDIR)/cells/lib.tcl
proc build {cell {broken none}} {
    cellname create $cell
    load $cell
    box 0um 0um 0um 0um
    magic::gencell sky130::sky130_fd_pr__nfet_g5v0d10v5 Msg w 5 l 0.5 nf 1
    box 20um 0um 20um 0um
    magic::gencell sky130::sky130_fd_pr__nfet_g5v0d10v5 Msinn w 12 l 0.5 nf 1
    box 45um 0um 45um 0um
    magic::gencell sky130::sky130_fd_pr__pfet_g5v0d10v5 Msinp w 36 l 0.5 nf 1
    addpath $::env(PDKPATH)/libs.ref/sky130_fd_sc_hvl/mag
    box 75um 0um 75um 0um
    getcell sky130_fd_sc_hvl__lsbuflv2hv_clkiso_hlkg_3
    if {$broken eq "drc"} { rect metal1 -5.0 0 -4.95 3.0 }
    save $cell
}
build c4_sw
build c4_sw_drcbad drc
puts "C4 BUILD DONE"
quit -noprompt
