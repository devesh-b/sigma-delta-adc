# MIM unit (cap_mim_m3_1, 0.25 pF) and the stage-2 common-centroid array (WO-96 cell a).
# Drawn directly (met3 plate / mimcap / mimcc / met4) for full geometric control; extracts as
# sky130_fd_pr__cap_mim_m3_1 w=U l=U. Run in magic -dnull -noconsole with the sky130A magicrc,
# from the output dir; env(LAYDIR) = design/layout. Map (row 0 bottom) and nets: see design/layout/README.md.
source $env(LAYDIR)/cells/lib.tcl
set U 11.0                ;# capm side (um): 2.0*121 + 0.19*44 = 250 fF
set PL [expr {$U + 0.6}]  ;# met3 plate side
set RP [expr {$PL + 1.6}] ;# row pitch
set TP 1.2                ;# track pitch in the column gaps and bus pitch below the array

proc unit_at {x y} {
    global U PL
    rect metal3 $x $y [expr {$x+$PL}] [expr {$y+$PL}]
    rect mimcap [expr {$x+0.3}] [expr {$y+0.3}] [expr {$x+0.3+$U}] [expr {$y+0.3+$U}]
    rect metal4 [expr {$x+0.6}] [expr {$y+0.6}] [expr {$x+$U}] [expr {$y+$U}]
    rect mimcc  [expr {$x+0.8}] [expr {$y+0.8}] [expr {$x+$U-0.2}] [expr {$y+$U-0.2}]
}

# --- unit cell (for the extraction / DRC check of one device) ---
cellname create mim_u250
load mim_u250
unit_at 0 0
pin t metal4 4 4 6 6
pin b metal3 0 0 0.5 0.5
save mim_u250

# --- stage-2 array: sites map[r][c] = "<cap><p|n>" ; A Cs2 0.5 pF (2u), B Cint2 1 pF (4u), K Ck2 0.25 pF (1u), D dummy
set MAP {
    {Bp Bn Bp Bn}
    {Kn Ap An Kp}
    {Dp An Ap Dn}
    {Bn Bp Bn Bp}
}
array set CAPN {A cs2 B ci2 K ck2}
proc nets_of {s} {
    global CAPN
    set k [string index $s 0]; set side [string index $s 1]
    if {$k eq "D"} { return {dmy dmy} }
    set n $CAPN($k)$side
    return [list ${n}_t ${n}_b]
}
proc is_top {net} { return [expr {[string match *_t $net] || $net eq "dmy"}] }

proc build_array {cell map {broken none}} {
    global PL RP TP
    cellname create $cell
    load $cell
    set nr [llength $map]; set nc [llength [lindex $map 0]]
    # per column: track slots (top nets on met4, bottom nets on met2 share slot positions)
    set gapw 0
    for {set c 0} {$c < $nc} {incr c} {
        set tl {}; set bl {}
        for {set r 0} {$r < $nr} {incr r} {
            foreach n [nets_of [lindex $map $r $c]] {
                if {[is_top $n]} { if {[lsearch $tl $n] < 0} {lappend tl $n} } else { if {[lsearch $bl $n] < 0} {lappend bl $n} }
            }
        }
        set T($c) $tl; set B($c) $bl
        set w [expr {3.4 + [expr {max([llength $tl],[llength $bl])}]*$TP + 0.8}]
        if {$w > $gapw} {set gapw $w}
    }
    set CP [expr {$PL + $gapw}]
    set allnets {}
    for {set c 0} {$c < $nc} {incr c} { foreach n [concat $T($c) $B($c)] { if {[lsearch $allnets $n] < 0} {lappend allnets $n} } }
    set allnets [lsort $allnets]
    set k 0
    foreach n $allnets { set YB($n) [expr {-3.0 - $k*$TP}]; incr k }
    foreach n $allnets { set XMIN($n) 1e9; set XMAX($n) -1e9 }
    for {set c 0} {$c < $nc} {incr c} {
        set x [expr {$c*$CP}]
        set g0 [expr {$x + $PL}]
        foreach lst [list $T($c) $B($c)] {
            set i 0
            foreach n $lst { set XT($c,$n) [expr {$g0 + 3.4 + $i*$TP}]; incr i }
        }
        foreach n [concat $T($c) $B($c)] { set YTOP($c,$n) -1e9 }
        for {set r 0} {$r < $nr} {incr r} {
            set y [expr {$r*$RP}]
            unit_at $x $y
            lassign [nets_of [lindex $map $r $c]] nt nb
            # top stub: met4 out of the plate, via3 to a met3 run, then onto the track
            set yt [expr {$y + 2.75}]
            rect metal4 [expr {$x+11.0-0.1}] [expr {$yt-0.25}] [expr {$g0+2.25}] [expr {$yt+0.25}]
            via metal3 metal4 via3 [expr {$g0+2.0}] $yt
            set xt $XT($c,$nt)
            rect metal3 [expr {$g0+2.0}] [expr {$yt-0.25}] $xt [expr {$yt+0.25}]
            via metal3 metal4 via3 $xt $yt
            if {$yt > $YTOP($c,$nt)} {set YTOP($c,$nt) $yt}
            # bottom stub: met3 plate extension onto the track (via3 for dmy, via2 to met2 otherwise)
            set yb [expr {$y + 8.65}]
            set xb $XT($c,$nb)
            rect metal3 [expr {$x+$PL-0.1}] [expr {$yb-0.25}] $xb [expr {$yb+0.25}]
            if {[is_top $nb]} { via metal3 metal4 via3 $xb $yb } else { via metal2 metal3 via2 $xb $yb }
            if {$yb > $YTOP($c,$nb)} {set YTOP($c,$nb) $yb}
        }
        # vertical tracks down to each net's bus
        foreach n [concat $T($c) $B($c)] {
            set xt $XT($c,$n)
            set lay [expr {[is_top $n] ? "metal4" : "metal2"}]
            rect $lay [expr {$xt-0.25}] [expr {$YB($n)-0.35}] [expr {$xt+0.25}] [expr {$YTOP($c,$n)+0.35}]
            if {[is_top $n]} { via metal3 metal4 via3 $xt $YB($n) } else { via metal1 metal2 via1 $xt $YB($n) }
            if {$xt < $XMIN($n)} {set XMIN($n) $xt}
            if {$xt > $XMAX($n)} {set XMAX($n) $xt}
        }
    }
    # horizontal buses (met3 for top-plate nets, met1 for bottom-plate nets), pins at the west end
    set xw -2.0
    foreach n $allnets {
        set lay [expr {[is_top $n] ? "metal3" : "metal1"}]
        rect $lay $xw [expr {$YB($n)-0.25}] [expr {$XMAX($n)+0.35}] [expr {$YB($n)+0.25}]
        pin $n $lay $xw [expr {$YB($n)-0.25}] [expr {$xw+0.5}] [expr {$YB($n)+0.25}]
    }
    if {$broken eq "drc"} {
        # deliberate DRC error: a 0.1 um met3 sliver next to the west bus ends (width + spacing violation)
        rect metal3 -4.0 -1.0 -3.9 2.0
    }
    if {$broken eq "short"} {
        # deliberate LVS error: met3 strap shorts cs2p_t's and cs2n_t's buses at their west ends
        rect metal3 -2.0 [expr {min($YB(cs2p_t),$YB(cs2n_t))-0.25}] -1.5 [expr {max($YB(cs2p_t),$YB(cs2n_t))+0.25}]
    }
    writeall force
    puts "ARRAY $cell nets=[llength $allnets] colpitch=$CP rowpitch=$RP gap=$gapw"
}
build_array mim_s2 $MAP
build_array mim_s2_drcbad $MAP drc
build_array mim_s2_short $MAP short
puts "MIM BUILD DONE"
quit -noprompt
