# C6 bias resistors (WO-96 cell c): R1 144.8 um, R2a = R2b = 2.45 x R1 = 354.76 um of res_xhigh_po_0p69
# (design/c6_bias/c6_spot.py RX; tuned values per results/wo80 README, WO-64 tune.json). Device sizes unchanged.
# Serpentines from the sky130 gencell; two passes: pass 1 extracts the effective l, pass 2 rescales the segment.
source $env(LAYDIR)/cells/lib.tcl
set NX1 4; set NX2 10; set T1 144.8; set T2 354.76
proc build {cell s1 s2 {broken none}} {
    global NX1 NX2
    cellname create $cell
    load $cell
    box 0um 0um 0um 0um
    magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p69 R1 w 0.69 l $s1 nx $NX1 snake 1
    box 40um 0um 40um 0um
    magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p69 R2a w 0.69 l $s2 nx $NX2 snake 1
    box 100um 0um 100um 0um
    magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p69 R2b w 0.69 l $s2 nx $NX2 snake 1
    if {$broken eq "drc"} { rect metal1 -5.0 0 -4.95 3.0 }
    save $cell
}
proc ext_l {cell} {
    load $cell
    extract all
    ext2spice lvs
    ext2spice -o ${cell}.spice
    set f [open ${cell}.spice]; set ls {}
    foreach ln [split [read $f] "\n"] {
        if {[string match *xhigh_po* $ln] && [regexp { l=([0-9.eE+-]+)} $ln -> v]} {
            if {$v < 1e-3} {set v [expr {$v*1e6}]}
            lappend ls $v
        }
    }
    close $f
    return [lsort -real $ls]
}
set s1 [expr {$T1/$NX1}]; set s2 [expr {$T2/$NX2}]
build c6_res_p1 $s1 $s2
set ls [ext_l c6_res_p1]
puts "C6 PASS1 seg $s1 $s2 extracted l = $ls"
set l1 [lindex $ls 0]; set l2 [lindex $ls end]
set s1 [expr {round($s1*$T1/$l1/0.005)*0.005}]; set s2 [expr {round($s2*$T2/$l2/0.005)*0.005}]
build c6_res $s1 $s2
build c6_res_drcbad $s1 $s2 drc
puts "C6 PASS2 seg $s1 $s2 extracted l = [ext_l c6_res]"
puts "C6 BUILD DONE"
quit -noprompt
