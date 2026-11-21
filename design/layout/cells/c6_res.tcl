# C6 bias resistors (WO-96 cell c, WO-100 rework): R1 144.8 um, R2a = R2b = 2.45 x R1 = 354.76 um of res_xhigh_po_0p69
# (design/c6_bias/c6_spot.py RX; tuned values per results/wo80 README, WO-64 tune.json). Device sizes unchanged.
# WO-100: the snake gencell failed rpm.1/urpm.1a (WO-96). A lone nx=1 gencell also fails rpm.1 (marker 0.69 wide);
# nx>=2 with snake 0 (separate parallel legs under one marker) is clean in both decks (probe WO-100-probe/probe2).
# So: R1 = 4 legs, R2a/R2b = 10 legs each, joined in series by met1 straps across the head contacts (alternating
# top/bottom). netgen sky130A_setup combines series xhrpoly (l add, w critical), so LVS sees one device per resistor.
# NOTE: each leg has its own two head contacts, so the absolute R differs from one l=144.8 device (head resistance);
# the C6 owner must re-simulate with the segmented netlist (legs printed below). The R2/R1 ratio stays near 2.45 since
# leg counts (10 vs 4) scale with length.
source $env(LAYDIR)/cells/lib.tcl
set NX1 4; set NX2 10; set T1 144.8; set T2 354.76
# leg centres in parent internal units: inst = instance name, returns {xs ytop ybot}
# leg centres (internal units) of the gencell placed with its lower-left at (x0 um, 0): search the mcon heads in
# a window around it (a3e721f used `select cell <name>`, but gencell instance names are not the given names, so
# the window was wrong and R2b's straps landed on R2a: LVS saw R2a || R2b).
proc legs {parent x0 nx} {
    load $parent
    select top cell; expand
    set xa [expr {$x0-0.3}]; set xb [expr {$x0+$nx*1.17+0.6}]
    box ${xa}um 20um ${xb}um 45um; select clear; select area mcon; lassign [select bbox] mx1 my1 mx2 my2
    box ${xa}um -1um ${xb}um 20um; select clear; select area mcon; lassign [select bbox] bx1 by1 bx2 by2
    select clear
    set wm 106
    set p [expr {$nx > 1 ? double($mx2-$mx1-$wm)/($nx-1) : 0}]
    set xs {}
    for {set k 0} {$k < $nx} {incr k} { lappend xs [expr {round($mx1+$wm/2.0+$k*$p)}] }
    puts "C6 LEGS x0 $x0 x [expr {$mx1/200.0}]-[expr {$mx2/200.0}] pitch [expr {$p/200.0}] um top [expr {$my1/200.0}]-[expr {$my2/200.0}] bot [expr {$by1/200.0}]-[expr {$by2/200.0}]"
    return [list $xs [expr {($my1+$my2)/2}] [expr {($by1+$by2)/2}]]
}
proc irect {layer x1 y1 x2 y2} { box ${x1}i ${y1}i ${x2}i ${y2}i; paint $layer }
proc ipin {name x y} { box [expr {$x-40}]i [expr {$y-40}]i [expr {$x+40}]i [expr {$y+40}]i; label $name FreeSans 0.3u -metal1; port make }
# series-join the legs of one instance; skip = index of a join to leave out (broken copy "open")
proc series {parent x0 nx a b {skip -1}} {
    lassign [legs $parent $x0 $nx] xs yt yb
    for {set k 0} {$k < $nx-1} {incr k} {
        if {$k == $skip} continue
        set y [expr {$k % 2 == 0 ? $yt : $yb}]
        irect metal1 [expr {[lindex $xs $k]-50}] [expr {$y-50}] [expr {[lindex $xs [expr {$k+1}]]+50}] [expr {$y+50}]
    }
    ipin $a [lindex $xs 0] $yb
    ipin $b [lindex $xs end] [expr {($nx-1) % 2 == 0 ? $yt : $yb}]
}
proc build {cell s1 s2 {broken none} {which all}} {
    global NX1 NX2
    cellname create $cell
    load $cell
    if {$which in {all r1}} {
        box 0um 0um 0um 0um
        magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p69 R1 w 0.69 l $s1 nx $NX1 snake 0 guard 0
        series $cell 0 $NX1 r1a r1b
    }
    if {$which in {all r2}} {
        box 10um 0um 10um 0um
        magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p69 R2a w 0.69 l $s2 nx $NX2 snake 0 guard 0
        series $cell 10 $NX2 r2a r2b [expr {$broken eq "open" ? 4 : -1}]
    }
    if {$which eq "all"} {
        box 26um 0um 26um 0um
        magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p69 R2b w 0.69 l $s2 nx $NX2 snake 0 guard 0
        series $cell 26 $NX2 r3a r3b
    }
    if {$broken eq "drc"} { rect metal1 -5.0 0 -4.95 3.0 }
    writeall force
}
proc ext_sum {cell} {
    load $cell
    extract do local
    extract all
    ext2spice lvs
    ext2spice -o ${cell}.spice
    set f [open ${cell}.spice]; set s 0; set n 0
    foreach ln [split [read $f] "\n"] {
        if {[string match *xhigh_po* $ln] && [regexp { l=([0-9.eE+-]+)} $ln -> v]} {
            if {$v < 1e-3} {set v [expr {$v*1e6}]}
            set s [expr {$s+$v}]; incr n
        }
    }
    close $f
    return [list $s $n]
}
# calibrate the drawn leg length so the extracted series sum hits the target (2 passes, secant)
set s1 [expr {$T1/$NX1}]; set s2 [expr {$T2/$NX2}]
for {set it 1} {$it <= 2} {incr it} {
    build c6_cal1_$it $s1 $s2 none r1; lassign [ext_sum c6_cal1_$it] l1 n1
    build c6_cal2_$it $s1 $s2 none r2; lassign [ext_sum c6_cal2_$it] l2 n2
    puts "C6 CAL$it leg $s1 $s2 extracted sums $l1 ($n1 legs) $l2 ($n2 legs)"
    set s1 [expr {round(($s1 + ($T1-$l1)/$NX1)/0.005)*0.005}]
    set s2 [expr {round(($s2 + ($T2-$l2)/$NX2)/0.005)*0.005}]
}
build c6_res $s1 $s2
build c6_res_drcbad $s1 $s2 drc
build c6_res_open $s1 $s2 open
puts "C6 FINAL leg $s1 $s2 extracted sum/legs [ext_sum c6_res]"
puts "C6 BUILD DONE"
quit -noprompt
