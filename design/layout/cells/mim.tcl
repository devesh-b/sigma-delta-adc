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

# WO-100 router: columns are paired (c even | gap | c odd) and share one routing gap; the odd column's stubs are
# mirrored (left side) and sit at different y than the even column's, so the two columns' met3 runs never meet.
# Top-plate nets: met4 tracks + met3 bus below the array; bottom-plate nets: met2 tracks + met1 bus.
# via3 stays >= 2.3 um from the capm edge (capm.2b_a, WO-96).
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
    set np [expr {($nc+1)/2}]
    # per column pair: top-net and bottom-net track lists (shared x slots)
    set gapw 0
    for {set p 0} {$p < $np} {incr p} {
        set tl {}; set bl {}
        foreach c [list [expr {2*$p}] [expr {2*$p+1}]] {
            if {$c >= $nc} continue
            for {set r 0} {$r < $nr} {incr r} {
                foreach n [nets_of [lindex $map $r $c]] {
                    if {[is_top $n]} { if {[lsearch $tl $n] < 0} {lappend tl $n} } else { if {[lsearch $bl $n] < 0} {lappend bl $n} }
                }
            }
        }
        set T($p) $tl; set B($p) $bl
        set w [expr {6.8 + (max([llength $tl],[llength $bl])-1)*$TP}]
        if {$w > $gapw} {set gapw $w}
    }
    set PP [expr {2*$PL + $gapw + 1.6}]
    set allnets {}
    for {set p 0} {$p < $np} {incr p} { foreach n [concat $T($p) $B($p)] { if {[lsearch $allnets $n] < 0} {lappend allnets $n} } }
    set allnets [lsort $allnets]
    set k 0
    foreach n $allnets { set YB($n) [expr {-3.0 - $k*$TP}]; incr k }
    foreach n $allnets { set XMIN($n) 1e9; set XMAX($n) -1e9 }
    for {set p 0} {$p < $np} {incr p} {
        set g0 [expr {$p*$PP + $PL}]; set g1 [expr {$g0 + $gapw}]
        foreach lst [list $T($p) $B($p)] {
            set i 0
            foreach n $lst { set XT($p,$n) [expr {$g0 + 3.4 + $i*$TP}]; incr i }
        }
        foreach n [concat $T($p) $B($p)] { set YTOP($p,$n) -1e9 }
        foreach c [list [expr {2*$p}] [expr {2*$p+1}]] {
            if {$c >= $nc} continue
            set odd [expr {$c % 2}]
            set x [expr {$odd ? $g1 : $p*$PP}]
            for {set r 0} {$r < $nr} {incr r} {
                set y [expr {$r*$RP}]
                unit_at $x $y
                lassign [nets_of [lindex $map $r $c]] nt nb
                set yt [expr {$y + ($odd ? 4.75 : 2.75)}]
                set yb [expr {$y + ($odd ? 6.65 : 8.65)}]
                set xt $XT($p,$nt); set xb $XT($p,$nb)
                if {!$odd} {
                    rect metal4 [expr {$x+11.0-0.1}] [expr {$yt-0.25}] [expr {$g0+2.25}] [expr {$yt+0.25}]
                    set xv [expr {$g0+2.0}]
                    rect metal3 [expr {$x+$PL-0.1}] [expr {$yb-0.25}] [expr {max($xb,$x+$PL)+0.25}] [expr {$yb+0.25}]
                } else {
                    rect metal4 [expr {$g1-2.25}] [expr {$yt-0.25}] [expr {$x+0.6+0.1}] [expr {$yt+0.25}]
                    set xv [expr {$g1-2.0}]
                    rect metal3 [expr {min($xb,$x)-0.25}] [expr {$yb-0.25}] [expr {$x+0.1}] [expr {$yb+0.25}]
                }
                via metal3 metal4 via3 $xv $yt
                rect metal3 [expr {min($xv,$xt)-0.25}] [expr {$yt-0.25}] [expr {max($xv,$xt)+0.25}] [expr {$yt+0.25}]
                via metal3 metal4 via3 $xt $yt
                if {[is_top $nb]} { via metal3 metal4 via3 $xb $yb } else { via metal2 metal3 via2 $xb $yb }
                if {$yt > $YTOP($p,$nt)} {set YTOP($p,$nt) $yt}
                if {$yb > $YTOP($p,$nb)} {set YTOP($p,$nb) $yb}
            }
        }
        foreach n [concat $T($p) $B($p)] {
            set xt $XT($p,$n)
            set lay [expr {[is_top $n] ? "metal4" : "metal2"}]
            rect $lay [expr {$xt-0.25}] [expr {$YB($n)-0.35}] [expr {$xt+0.25}] [expr {$YTOP($p,$n)+0.35}]
            if {[is_top $n]} { via metal3 metal4 via3 $xt $YB($n) } else { via metal1 metal2 via1 $xt $YB($n) }
            if {$xt < $XMIN($n)} {set XMIN($n) $xt}
            if {$xt > $XMAX($n)} {set XMAX($n) $xt}
        }
    }
    set xw -2.0
    foreach n $allnets {
        set lay [expr {[is_top $n] ? "metal3" : "metal1"}]
        rect $lay $xw [expr {$YB($n)-0.25}] [expr {$XMAX($n)+0.35}] [expr {$YB($n)+0.25}]
        pin $n $lay $xw [expr {$YB($n)-0.25}] [expr {$xw+0.5}] [expr {$YB($n)+0.25}]
    }
    if {$broken eq "drc"} { rect metal3 -4.0 -1.0 -3.9 2.0 }
    if {$broken eq "short"} {
        set tops [lsearch -all -inline $allnets *_t]; set a [lindex $tops 0]; set b [lindex $tops 1]
        rect metal3 -2.0 [expr {min($YB($a),$YB($b))-0.25}] -1.5 [expr {max($YB($a),$YB($b))+0.25}]
        puts "ARRAY $cell short between $a and $b"
    }
    writeall force
    puts "ARRAY $cell nets=[llength $allnets] pairpitch=$PP rowpitch=$RP gap=$gapw"
}
# stage 2 (WO-96 map, re-routed)
set MAP2 {
    {Bp Bn Bp Bn}
    {Kn Ap An Kp}
    {Dp An Ap Dn}
    {Bn Bp Bn Bp}
}
build_array mim_s2 $MAP2
build_array mim_s2_drcbad $MAP2 drc
build_array mim_s2_short $MAP2 short
# stage 1 (WO-100): Cs1 0.5 pF (2 units) and Cint1 4 pF (16 units) per side (SPEC 3.x), 36 units, 6x6.
# Common centroid: Cs1 on the 4 centre sites (diagonal pairs), Cint1 on the (r+c) parity checkerboard; every net is
# point-symmetric about the array centre, so all four centroids coincide. No dummy ring (area); edge units are
# shared equally by p and n (point symmetry). Map row 0 = bottom.
array set CAPN {A cs1 B ci1}
set MAP1 {}
for {set r 0} {$r < 6} {incr r} {
    set row {}
    for {set c 0} {$c < 6} {incr c} {
        set s [expr {(($r+$c) % 2) ? "n" : "p"}]
        set k [expr {($r in {2 3} && $c in {2 3}) ? "A" : "B"}]
        lappend row $k$s
    }
    lappend MAP1 $row
}
puts "MAP1 $MAP1"
build_array mim_s1 $MAP1
build_array mim_s1_drcbad $MAP1 drc
build_array mim_s1_short $MAP1 short
puts "MIM BUILD DONE"
quit -noprompt
