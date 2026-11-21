# WO-96 tile floorplan (TT analog 2x2, 3.3 V). Run in magic -dnull -noconsole with the sky130A magicrc from the
# output dir; env(LAYDIR) = design/layout. Draws: template pins (def read), met4 power straps reaching both tile
# edges (precheck: port within 10 um of top and bottom), and block slots as comment-layer outlines with labels.
# Slot table: name x1 y1 x2 y2 need_lo need_hi (um / um2); needs from DESIGN_BOOK V.4, WO-93 (D91) and WO-96 cells.
set TOP tt_um_sd_adc_fp
def read $env(LAYDIR)/frame/tt_analog_2x2_3v3.def
cellname rename tt_um_template $TOP
load $TOP
proc strap {name x1 x2} {
    box ${x1}um 5um ${x2}um 220.76um
    paint metal4
    label $name FreeSans 0.25u -metal4
    port make
    port use [expr {$name eq "VGND" ? "ground" : "power"}]
    port class bidirectional
}
# C9 macro: D93 plans the WO-101 shrunk die, C9W x 150 um (env C9W, default 165), drawn as a slot outline until the
# WO-101 GDS lands. The WO-96 LEF abstract is no longer placed: its OBS on nwell (sd_adc_c9.lef line 416) became
# real nwell without taps, the source of the 2 nwell.4 errors. The real macro GDS is checked in cell c9_place.
set C9W [expr {[info exists env(C9W)] ? $env(C9W) : 165.0}]
set C9X2 [expr {4.0 + $C9W}]
# digital pair just east of the macro; analog pair on the east edge (unchanged)
strap VDPWR [expr {$C9X2+1.5}] [expr {$C9X2+3.5}]
strap VGND  [expr {$C9X2+4.5}] [expr {$C9X2+6.5}]
strap VGND  305.5 307.5
strap VAPWR 311.0 313.0
# D93 isolation C9 -> analog: p+ substrate-tap guard ring (psd 1.0 um, licon row, li; tied to VGND at assembly)
# in an empty moat. East leg 8 um past the digital straps, south leg 7 um below C9 (L shape, macro corner at 4,72).
set GX [expr {$C9X2+14.5}]; set GY 64.0
proc gseg {a b c d} {
    box ${a}um ${b}um ${c}um ${d}um; paint psd
    box [expr {$a+0.2}]um [expr {$b+0.2}]um [expr {$c-0.2}]um [expr {$d-0.2}]um; paint locali
    box [expr {$a+0.415}]um [expr {$b+0.415}]um [expr {$c-0.415}]um [expr {$d-0.415}]um; paint psc
}
gseg 2.0 $GY [expr {$GX+1.0}] [expr {$GY+1.0}]
gseg $GX $GY [expr {$GX+1.0}] 223.0
set AX [expr {$GX+4.5}]
puts "FP GUARD ring east leg x $GX..[expr {$GX+1}], south leg y $GY..[expr {$GY+1}]; C9 east edge $C9X2; analog column from x $AX ([expr {$AX-$C9X2}] um from C9, WO-96: 10 um)"
# D93: MIM arrays stacked over circuits (capm met3/met4 over li/met1 circuits, met2 shield plane under the MIM).
# Circuit slots must not overlap; MIM slots (prefix MIM_) overlay circuit slots and are excluded from the sum.
set SLOTS [list \
    [list C9_macro      4.0  72.0 $C9X2 222.0 [expr {$C9W*150}] [expr {$C9W*150}]] \
    [list OTA1          $AX   3.0 303.0 100.0  9100 13100] \
    [list OTA2          $AX 102.0 303.0 166.0  5350  7450] \
    [list C6_bias       $AX 168.0 303.0 222.0  5800  7000] \
    [list C3_comp       3.0   3.0  50.0  62.0  1500  3000] \
    [list SW_in_ref    52.0   3.0 100.0  62.0  1000  2000] \
    [list C4_phase_LS 102.0   3.0 [expr {$GX-1.0}] 62.0  3400  4600] \
    [list MIM_S1_over_OTA1 $AX 3.0 303.0 100.0 0 0] \
    [list MIM_S2_over_OTA2 $AX 102.0 303.0 166.0 0 0] \
]
set tile [expr {319.24*225.76}]
set sa 0; set nlo 0; set nhi 0
puts [format "FP %-20s %8s %8s %8s %s" slot slot_um2 need_lo need_hi status]
foreach s $SLOTS {
    lassign $s n x1 y1 x2 y2 lo hi
    set a [expr {($x2-$x1)*($y2-$y1)}]
    set st [expr {$a == 0 ? "NO SLOT" : ($a >= $hi ? "fits" : ($a >= $lo ? "fits only at low estimate" : "DOES NOT FIT"))}]
    puts [format "FP %-20s %8.0f %8.0f %8.0f %s" $n $a $lo $hi $st]
    if {![string match MIM_* $n]} { set sa [expr {$sa+$a}] }; set nlo [expr {$nlo+$lo}]; set nhi [expr {$nhi+$hi}]
    if {$a > 0} {
        foreach {bx1 by1 bx2 by2} [list $x1 $y1 $x2 [expr {$y1+0.5}] $x1 [expr {$y2-0.5}] $x2 $y2 $x1 $y1 [expr {$x1+0.5}] $y2 [expr {$x2-0.5}] $y1 $x2 $y2] {
            box ${bx1}um ${by1}um ${bx2}um ${by2}um; paint comment
        }
        box ${x1}um ${y1}um ${x1}um ${y1}um
        label $n FreeSans 1u comment
    }
}
puts [format "FP TOTAL slots %.0f um2 (%.1f %% of tile %.0f); need %.0f-%.0f um2 = %.1f-%.1f %% of tile before routing/guard rings" \
    $sa [expr {100*$sa/$tile}] $tile $nlo $nhi [expr {100*$nlo/$tile}] [expr {100*$nhi/$tile}]]
# slot overlap check
foreach a $SLOTS { foreach b $SLOTS {
    lassign $a na ax1 ay1 ax2 ay2; lassign $b nb bx1 by1 bx2 by2
    if {$na < $nb && ![string match MIM_* $na] && ![string match MIM_* $nb] && $ax2 > $bx1 && $bx2 > $ax1 && $ay2 > $by1 && $by2 > $ay1} { puts "FP OVERLAP $na $nb" }
}}
writeall force
puts "FP DONE"
quit -noprompt
