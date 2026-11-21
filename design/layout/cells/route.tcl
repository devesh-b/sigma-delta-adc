# WO-107: row placer + channel router for gencell FETs and hvl level shifters (Magic Tcl, um).
# Gencell geometry, from the WO-107 probe of the .mag views (magic 8.3.685; device centre = bbox centre):
#   S/D met1 strips at x = +-(L/2 + 0.145), full W high; top gate-contact met1 centred at y = W/2 + 0.275 (nfet) or
#   W/2 + 0.32 (pfet); guard-ring met1 column (viagl/viagr 100) at x = L/2 + 0.715 (1.8 V), L/2 + 0.825 (HV nfet),
#   L/2 + 0.815 (HV pfet). Gencell ring met1 is drawn only on the side asked for, so the gate escape (met1, from the
#   top gate contact, 0.16 above the strip ends) can cross the other ring side in li-free met1.
# Routing: each terminal gets via1 and a vertical met2 stub up to its net's met3 track in the channel above its row
# (one track per net per row, pitch 0.8). Nets on more than one row, and ports, get a vertical met4 spine (pitch 1.0)
# with via3 on each of their tracks. Metals are painted first, contacts last.
namespace eval rt {}
proc rt::r {layer x1 y1 x2 y2} {
    box [format %.3f $x1]um [format %.3f $y1]um [format %.3f $x2]um [format %.3f $y2]um
    paint $layer
}
proc rt::reset {} {
    variable TERMS {}; variable TRK {}; variable CONT {}; variable X 0.0; variable Y 0.0; variable TOP 0.0
    variable CH; array unset CH
}
proc rt::geom {model l} {
    set sx [expr {$l/2.0 + 0.145}]
    switch $model {
        nfet_01v8      { list $sx [expr {$l/2.0 + 0.715}] 0.275 }
        pfet_01v8      { list $sx [expr {$l/2.0 + 0.715}] 0.32 }
        nfet_g5v0d10v5 { list $sx [expr {$l/2.0 + 0.825}] 0.275 }
        pfet_g5v0d10v5 { list $sx [expr {$l/2.0 + 0.815}] 0.32 }
    }
}
proc rt::term {net x y kind} { variable TERMS; lappend TERMS [list $net $x $y $kind] }
proc rt::row {y} { variable X 0.0; variable Y $y; variable TOP $y }
# One FET at the row cursor. side r: gate escape to the right, bulk tap on the left ring column; side l: mirrored.
proc rt::fet {name model w l d g s b side gap} {
    variable X; variable Y; variable TOP
    box ${X}um ${Y}um ${X}um ${Y}um
    set vg [expr {$side eq "r" ? {viagl 100} : {viagr 100}}]
    magic::gencell sky130::sky130_fd_pr__$model $name w $w l $l nf 1 {*}$vg
    select cell $name; lassign [box values] x1 y1 x2 y2
    set dx [expr {round($X*200) - $x1}]; set dy [expr {round($Y*200) - $y1}]
    if {$dx > 0} { move e ${dx}i } elseif {$dx < 0} { move w [expr {-$dx}]i }
    if {$dy > 0} { move n ${dy}i } elseif {$dy < 0} { move s [expr {-$dy}]i }
    select cell $name; lassign [box values] x1 y1 x2 y2; select clear
    set cx [expr {($x1 + $x2)/400.0}]; set cy [expr {($y1 + $y2)/400.0}]
    set X [expr {$x2/200.0 + $gap}]
    if {$y2/200.0 > $TOP} { set TOP [expr {$y2/200.0}] }
    lassign [rt::geom $model $l] sx rx go
    set sg [expr {$side eq "r" ? 1 : -1}]
    rt::term $s [expr {$cx - $sg*$sx}] $cy v
    rt::term $d [expr {$cx + $sg*$sx}] $cy v
    rt::term $b [expr {$cx - $sg*$rx}] $cy v
    set gy [expr {$cy + $w/2.0 + $go}]; set gx [expr {$cx + $sg*($rx + 0.45)}]
    rt::r metal1 [expr {min($cx,$gx)}] [expr {$gy - 0.115}] [expr {max($cx,$gx)}] [expr {$gy + 0.115}]
    rt::term $g $gx $gy v
}
# lsbuflv2hv_1 (pins from its GDS: VPWR met1 rails y 3.445-3.815 / 4.325-4.695, VPB 3.955-4.185, VGND 0.255-0.625 /
# 7.515-7.885, LVPWR 3.02-3.305, A li x 2.555-2.725 y 1.58-2.12, X li x 10.235-10.405 y 5.28-6.93, cell 10.56 wide).
# The two VPWR rails and the two VGND rails are separate in the cell (extracted VPWR_uq0 / VGND_uq0): VPWR, VPB and
# VPWR_uq0 are joined by a met1 block east of the cell; VGND and VGND_uq0 by a met1 strap west of it (strap 0 = omit
# the west strap, broken copy).
proc rt::ls {a lv vgnd vpwr x gap {strap 1}} {
    variable X; variable Y; variable TOP
    set ox [expr {$X + 1.0}]; set oy [expr {$Y + 0.3}]
    box ${ox}um ${oy}um ${ox}um ${oy}um
    getcell sky130_fd_sc_hvl__lsbuflv2hv_1
    rt::r metal1 [expr {$ox - 0.8}] [expr {$oy + 0.255}] $ox [expr {$oy + 0.625}]
    if {$strap} {
        rt::r metal1 [expr {$ox - 0.8}] [expr {$oy + 7.515}] $ox [expr {$oy + 7.885}]
        rt::r metal1 [expr {$ox - 0.8}] [expr {$oy + 0.255}] [expr {$ox - 0.5}] [expr {$oy + 7.885}]
    }
    rt::r metal1 [expr {$ox + 10.56}] [expr {$oy + 3.445}] [expr {$ox + 11.4}] [expr {$oy + 4.695}]
    rt::term $vgnd [expr {$ox - 0.4}] [expr {$oy + 0.44}] h
    rt::term $vpwr [expr {$ox + 11.0}] [expr {$oy + 4.07}] v
    rt::term $lv   [expr {$ox + 1.5}]  [expr {$oy + 3.1625}] h
    rt::term $a    [expr {$ox + 2.64}] [expr {$oy + 1.68}] li
    rt::term $x    [expr {$ox + 10.32}] [expr {$oy + 5.9}] li
    set X [expr {$ox + 11.4 + $gap}]
    if {$oy + 8.14 > $TOP} { set TOP [expr {$oy + 8.14}] }
}
# Close the row: tracks in the channel above it, pads, via1, met2 stubs, via2. Returns the next row's y.
proc rt::row_end {} {
    variable TERMS; variable TOP; variable TRK; variable CONT; variable CH
    set nets [lsort -unique [lmap t $TERMS {lindex $t 0}]]
    set base [expr {$TOP + 1.0}]; set k 0
    foreach n $nets { set ty($n) [expr {$base + 0.8*$k}]; incr k; lappend CH($n) $ty($n); set xs($n) {} }
    foreach t $TERMS {
        lassign $t n x y kind
        set vy $y
        switch $kind {
            v  { rt::r metal1 [expr {$x-0.13}] [expr {$y-0.2}] [expr {$x+0.13}] [expr {$y+0.2}] }
            h  { rt::r metal1 [expr {$x-0.2}] [expr {$y-0.13}] [expr {$x+0.2}] [expr {$y+0.13}] }
            li { rt::r locali [expr {$x-0.085}] [expr {$y-0.1}] [expr {$x+0.085}] [expr {$y+0.1}]
                 rt::r metal1 [expr {$x-0.13}] [expr {$y-0.145}] [expr {$x+0.13}] [expr {$y+0.55}]
                 lappend CONT [list viali $x $y 0.085]; set vy [expr {$y + 0.37}] }
        }
        lappend CONT [list via1 $x $vy 0.13]
        rt::r metal2 [expr {$x-0.14}] [expr {$vy-0.2}] [expr {$x+0.14}] [expr {$ty($n)+0.2}]
        lappend CONT [list via2 $x $ty($n) 0.14]
        lappend xs($n) $x
    }
    foreach n $nets {
        set s [lsort -real $xs($n)]
        lappend TRK [list $n $ty($n) [lindex $s 0] [lindex $s end]]
    }
    set TERMS {}
    return [expr {$base + 0.8*$k + 1.5}]
}
# Tracks, spines, ports (labels on the met4 spines at ytop), then every contact.
proc rt::finish {ports ytop {x0 0.5}} {
    variable TRK; variable CONT; variable CH
    set k 0
    foreach n [lsort [array names CH]] {
        if {[llength $CH($n)] > 1 || $n in $ports} { set spx($n) [expr {$x0 + 1.0*$k}]; incr k }
    }
    foreach tr $TRK {
        lassign $tr n ty xa xb
        if {[info exists spx($n)]} {
            set xa [expr {min($xa, $spx($n))}]; set xb [expr {max($xb, $spx($n))}]
            lappend CONT [list via3 $spx($n) $ty 0.16]
        }
        rt::r metal3 [expr {$xa-0.3}] [expr {$ty-0.2}] [expr {$xb+0.3}] [expr {$ty+0.2}]
    }
    foreach n [array names spx] {
        set ys [lsort -real $CH($n)]
        set ya [lindex $ys 0]; set yb [lindex $ys end]
        if {$n in $ports} { set yb $ytop }
        rt::r metal4 [expr {$spx($n)-0.2}] [expr {$ya-0.3}] [expr {$spx($n)+0.2}] [expr {$yb+0.3}]
        if {$n in $ports} {
            box [format %.3f [expr {$spx($n)-0.2}]]um [format %.3f [expr {$yb-0.3}]]um [format %.3f [expr {$spx($n)+0.2}]]um [format %.3f [expr {$yb+0.3}]]um
            label $n FreeSans 0.3u -metal4
            port make
        }
    }
    foreach c $CONT {
        lassign $c lay x y h
        rt::r $lay [expr {$x-$h}] [expr {$y-$h}] [expr {$x+$h}] [expr {$y+$h}]
    }
    puts "RT spines [array size spx] tracks [llength $TRK] contacts [llength $CONT]"
}
