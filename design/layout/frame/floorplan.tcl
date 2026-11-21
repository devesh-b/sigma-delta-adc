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
# digital pair between the C9 macro and the analog column; analog pair on the east edge
strap VDPWR 196.5 198.5
strap VGND  200.5 202.5
strap VGND  305.5 307.5
strap VAPWR 311.0 313.0
set SLOTS {
    {C9_macro      4.0  72.0 194.0 222.0 28500 28500}
    {OTA1        205.0   3.0 303.0 109.0  9100 13100}
    {MIM1_Cs1_Cint1 205.0 111.0 303.0 180.0  5700  8800}
    {MIM2_Cs2_Cint2_Ck2 205.0 182.0 303.0 222.0 1800  5300}
    {C6_bias       3.0   3.0  73.0  69.0  5800  7000}
    {SW_in_ref    75.0   3.0 145.0  28.0  1000  2000}
    {C3_comp      75.0  30.0 145.0  69.0  1500  3000}
    {C4_phase_LS 147.0   3.0 194.0  69.0  2000  4000}
    {OTA2          0.0   0.0   0.0   0.0  5350  7450}
}
set tile [expr {319.24*225.76}]
set sa 0; set nlo 0; set nhi 0
puts [format "FP %-20s %8s %8s %8s %s" slot slot_um2 need_lo need_hi status]
foreach s $SLOTS {
    lassign $s n x1 y1 x2 y2 lo hi
    set a [expr {($x2-$x1)*($y2-$y1)}]
    set st [expr {$a == 0 ? "NO SLOT" : ($a >= $hi ? "fits" : ($a >= $lo ? "fits only at low estimate" : "DOES NOT FIT"))}]
    puts [format "FP %-20s %8.0f %8.0f %8.0f %s" $n $a $lo $hi $st]
    set sa [expr {$sa+$a}]; set nlo [expr {$nlo+$lo}]; set nhi [expr {$nhi+$hi}]
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
    if {$na < $nb && $ax2 > $bx1 && $bx2 > $ax1 && $ay2 > $by1 && $by2 > $ay1} { puts "FP OVERLAP $na $nb" }
}}
save $TOP
puts "FP DONE"
quit -noprompt
