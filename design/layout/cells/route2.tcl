# WO-109: multi-finger row placer + two-sided channel router (Magic Tcl, um). route.tcl (WO-107, one gencell per
# finger, C3/C4) is left unchanged; this file is used by c1_ota1.tcl.
# Devices are sky130 gencells with nf fingers on shared diffusion and m rows in one guard ring (conn_gates 1, top gate
# contact only). Geometry from the WO-109 probe (WO-109-probe/p1, magic 8.3.685, DRC 0 on nf 4 m 2 HV/LV cells):
#   finger (contact column) pitch p = L + 0.29; columns j = 0..nf at cx + (j - nf/2) p, even j = drain, odd j = source;
#   row pitch W + 0.78 (nfet) / W + 0.825 (pfet); contact row centre offset -0.155 (n) / -0.1775 (p) from cy;
#   top gate contact at row y + W/2 + 0.275 (n) / 0.32 (p); guard-ring met1 column at column 0 - 0.57 (1.8 V) /
#   0.68 (HV n) / 0.67 (HV p). viagl 0: our via1 lands on the ring met1 (gencell ring via1 arrays, partly overlapped
#   by ours, gave via.1a slivers).
# Routing: source/drain columns get a met2 strap (via1 on every row) DOWN to the channel below the row; gate (a met2
# strap through the row gate bars, at gate 0) and bulk (ring) go UP to the channel above. In each channel the tracks of
# the row below's up-nets lie under the tracks of the row above's down-nets, so up- and down-stubs never meet. A net
# on more than one track, and every port, gets a met4 spine (pitch 1.0, from x0) with via3 on its tracks.
# m > 1 with nf > 1 needs p >= 0.84 (the gate strap runs between two S/D straps).
# MIM caps (cap_mim_m3_1, direct draw as mim.tcl): bottom plate met3 tab and top plate met4 tab (via3 >= 2.8 um from
# capm) on the top edge, both routed up. Place cap rows first (bottom), below every spine.
namespace eval r2 {}
proc r2::r {layer x1 y1 x2 y2} {
    box [format %.3f $x1]um [format %.3f $y1]um [format %.3f $x2]um [format %.3f $y2]um
    paint $layer
}
proc r2::reset {} {
    variable TRK {}; variable CONT {}; variable CH; array unset CH; variable NDEV 0; variable AREA 0.0
}
proc r2::geom {model} {
    switch $model {
        nfet_01v8      { list 0.78 -0.155 0.275 0.57 }
        pfet_01v8      { list 0.825 -0.1775 0.32 0.57 }
        nfet_g5v0d10v5 { list 0.78 -0.155 0.275 0.68 }
        pfet_g5v0d10v5 { list 0.825 -0.1775 0.32 0.67 }
    }
}
# One gencell at lower-left (X, Y). Returns {x2 y2 upterms dnterms}; term = {net x {ys} padkind}.
proc r2::fet {X Y name model w l nf m d g s b} {
    variable NDEV
    set p [expr {$l + 0.29}]
    if {$nf > 1 && $m > 1 && $p < 0.84} { error "r2::fet $name: m > 1 with nf > 1 needs L >= 0.55" }
    if {$nf == 1 && $m > 1 && $p < 0.84} { error "r2::fet $name: m > 1 needs L >= 0.55" }
    box ${X}um ${Y}um ${X}um ${Y}um
    magic::gencell sky130::sky130_fd_pr__$model $name w $w l $l nf $nf m $m conn_gates 1 topc 1 botc 0 \
        guard 1 viagl 0 viagr 0 viagt 0 viagb 0 full_metal 1
    select cell $name; lassign [box values] x1 y1 x2 y2
    set dx [expr {round($X*200) - $x1}]; set dy [expr {round($Y*200) - $y1}]
    if {$dx > 0} { move e ${dx}i } elseif {$dx < 0} { move w [expr {-$dx}]i }
    if {$dy > 0} { move n ${dy}i } elseif {$dy < 0} { move s [expr {-$dy}]i }
    select cell $name; lassign [box values] x1 y1 x2 y2; select clear
    set cx [expr {($x1 + $x2)/400.0}]; set cy [expr {($y1 + $y2)/400.0}]
    lassign [r2::geom $model] rpa yoff go dl
    set rp [expr {$w + $rpa}]
    set ys {}
    for {set r 0} {$r < $m} {incr r} { lappend ys [expr {$cy + $yoff + ($r - ($m - 1)/2.0)*$rp}] }
    set gys [lmap y $ys {expr {$y + $w/2.0 + $go}}]
    set dn {}
    for {set j 0} {$j <= $nf} {incr j} {
        lappend dn [list [expr {$j % 2 == 0 ? $d : $s}] [expr {$cx + ($j - $nf/2.0)*$p}] $ys v]
    }
    set up [list [list $g [expr {$cx + (0.5 - $nf/2.0)*$p}] $gys h] \
                 [list $b [expr {$cx - ($nf/2.0)*$p - $dl}] [list $cy] v]]
    incr NDEV [expr {$nf*$m}]; variable AREA; set AREA [expr {$AREA + ($x2-$x1)*($y2-$y1)/40000.0}]
    return [list [expr {$x2/200.0}] [expr {$y2/200.0}] $up $dn]
}
# MIM cap, capm side s (extracts as cap_mim_m3_1 w=s l=s), top = met4 net, bot = met3 net.
proc r2::cap {X Y s top bot} {
    variable CONT
    set x $X; set y $Y; set pl [expr {$s + 0.6}]
    r2::r metal3 $x $y [expr {$x+$pl}] [expr {$y+$pl}]
    r2::r mimcap [expr {$x+0.3}] [expr {$y+0.3}] [expr {$x+0.3+$s}] [expr {$y+0.3+$s}]
    r2::r metal4 [expr {$x+0.6}] [expr {$y+0.6}] [expr {$x+$s}] [expr {$y+$s}]
    r2::r mimcc [expr {$x+0.8}] [expr {$y+0.8}] [expr {$x+$s-0.2}] [expr {$y+$s-0.2}]
    set yt [expr {$y + $pl + 3.0}]
    r2::r metal3 $x [expr {$y+$pl-0.1}] [expr {$x+0.6}] $yt
    r2::r metal4 [expr {$x+$s-0.6}] [expr {$y+$s-0.1}] [expr {$x+$s}] $yt
    r2::r metal3 [expr {$x+$s-0.7}] [expr {$y+$pl+2.1}] [expr {$x+$s+0.1}] $yt
    lappend CONT [list via3 [expr {$x+$s-0.3}] [expr {$y+$pl+2.55}] 0.16]
    set up [list [list $bot [expr {$x+0.3}] [list [expr {$y+$pl+2.6}]] m3] \
                 [list $top [expr {$x+$s-0.3}] [list [expr {$y+$pl+2.55}]] m3]]
    variable AREA; set AREA [expr {$AREA + $pl*($yt-$y)}]
    return [list [expr {$x+$pl}] $yt $up {}]
}
# Pads, via1 on every y, the met2 stub to track ty (dir up / dn), via2 on the track.
proc r2::stub {t ty dir} {
    variable CONT
    lassign $t n x ys kind
    foreach y $ys {
        switch $kind {
            v  { r2::r metal1 [expr {$x-0.13}] [expr {$y-0.2}] [expr {$x+0.13}] [expr {$y+0.2}]
                 lappend CONT [list via1 $x $y 0.13] }
            h  { r2::r metal1 [expr {$x-0.2}] [expr {$y-0.13}] [expr {$x+0.2}] [expr {$y+0.13}]
                 lappend CONT [list via1 $x $y 0.13] }
            m3 { lappend CONT [list via2 $x $y 0.14] }
        }
    }
    set s [lsort -real $ys]
    if {$dir eq "up"} { set y1 [expr {[lindex $s 0]-0.2}]; set y2 [expr {$ty+0.2}] } \
    else { set y1 [expr {$ty-0.2}]; set y2 [expr {[lindex $s end]+0.2}] }
    r2::r metal2 [expr {$x-0.14}] $y1 [expr {$x+0.14}] $y2
    lappend CONT [list via2 $x $ty 0.14]
}
# Allocate one channel at base: nets of group a (lower) then group b (upper). Returns {dict-a dict-b height}.
proc r2::channel {base na nb} {
    variable CH
    set i 0; set da {}; set db {}
    foreach n $na { dict set da $n [expr {$base + 0.8*$i}]; lappend CH($n) [expr {$base + 0.8*$i}]; incr i }
    foreach n $nb { dict set db $n [expr {$base + 0.8*$i}]; lappend CH($n) [expr {$base + 0.8*$i}]; incr i }
    return [list $da $db $i]
}
proc r2::addtrk {tv n ty x} { upvar $tv T; dict lappend T "$n $ty" $x }
# rows: list of rows (bottom first); item = {f name model w l nf m d g s b gap} or {c s top bot gap}.
proc r2::build {rows ports {x0 0.5}} {
    variable TRK
    set prevup {}; set top 0.0; set k 0; set T {}; set xmax 0.0
    foreach row $rows {
        set dnn {}
        foreach it $row { if {[lindex $it 0] eq "f"} { lappend dnn [lindex $it 7] [lindex $it 9] } }
        set dnn [lsort -unique $dnn]
        set upn [lsort -unique [lmap t $prevup {lindex $t 0}]]
        set base [expr {$k == 0 ? 0.0 : $top + 1.0}]
        lassign [r2::channel $base $upn $dnn] da db nt
        set y [expr {$nt > 0 ? $base + 0.8*($nt - 1) + 1.2 : $base}]
        set X 0.0; set up {}; set dn {}
        foreach it $row {
            if {[lindex $it 0] eq "f"} {
                lassign $it _ nm mo w l nf m d g s b gap
                lassign [r2::fet $X $y $nm $mo $w $l $nf $m $d $g $s $b] x2 y2 u dd
            } else {
                lassign $it _ s tp bt gap
                lassign [r2::cap $X $y $s $tp $bt] x2 y2 u dd
            }
            lappend up {*}$u; lappend dn {*}$dd
            set X [expr {$x2 + $gap}]
            if {$y2 > $top} { set top $y2 }
            if {$x2 > $xmax} { set xmax $x2 }
        }
        foreach t $prevup { set ty [dict get $da [lindex $t 0]]; r2::stub $t $ty up; r2::addtrk T [lindex $t 0] $ty [lindex $t 1] }
        foreach t $dn { set ty [dict get $db [lindex $t 0]]; r2::stub $t $ty dn; r2::addtrk T [lindex $t 0] $ty [lindex $t 1] }
        puts "R2ROW $k y [format %.2f $y] top [format %.2f $top] tracks $nt items [llength $row] xend [format %.2f $X]"
        set prevup $up; incr k
    }
    set base [expr {$top + 1.0}]
    lassign [r2::channel $base [lsort -unique [lmap t $prevup {lindex $t 0}]] {}] da db nt
    foreach t $prevup { set ty [dict get $da [lindex $t 0]]; r2::stub $t $ty up; r2::addtrk T [lindex $t 0] $ty [lindex $t 1] }
    dict for {key xs} $T { lassign $key n ty; set s [lsort -real $xs]; lappend TRK [list $n $ty [lindex $s 0] [lindex $s end]] }
    set ytop [expr {$base + 0.8*$nt + 1.0}]
    r2::finish $ports $ytop $x0
    variable NDEV
    variable AREA; puts "R2 fingers $NDEV device+cap bbox area [format %.0f $AREA] um2 xmax [format %.2f $xmax] ytop [format %.2f $ytop]"
}
proc r2::finish {ports ytop x0} {
    variable TRK; variable CONT; variable CH
    set k 0
    foreach n [lsort [array names CH]] {
        if {[llength $CH($n)] > 1 || $n in $ports} { set spx($n) [expr {$x0 + 1.0*$k}]; incr k }
    }
    foreach p $ports { if {![info exists spx($p)]} { error "r2::finish: port $p has no track" } }
    foreach tr $TRK {
        lassign $tr n ty xa xb
        if {[info exists spx($n)]} {
            set xa [expr {min($xa, $spx($n))}]; set xb [expr {max($xb, $spx($n))}]
            lappend CONT [list via3 $spx($n) $ty 0.16]
        }
        r2::r metal3 [expr {$xa-0.3}] [expr {$ty-0.2}] [expr {$xb+0.3}] [expr {$ty+0.2}]
    }
    foreach n [array names spx] {
        set ys [lsort -real $CH($n)]
        set ya [lindex $ys 0]; set yb [lindex $ys end]
        if {$n in $ports} { set yb $ytop }
        r2::r metal4 [expr {$spx($n)-0.2}] [expr {$ya-0.3}] [expr {$spx($n)+0.2}] [expr {$yb+0.3}]
        if {$n in $ports} {
            box [format %.3f [expr {$spx($n)-0.2}]]um [format %.3f [expr {$yb-0.3}]]um [format %.3f [expr {$spx($n)+0.2}]]um [format %.3f [expr {$yb+0.3}]]um
            label $n FreeSans 0.3u -metal4
            port make
        }
    }
    foreach c $CONT {
        lassign $c lay x y h
        r2::r $lay [expr {$x-$h}] [expr {$y-$h}] [expr {$x+$h}] [expr {$y+$h}]
    }
    puts "R2 spines $k tracks [llength $TRK] contacts [llength $CONT]"
}
