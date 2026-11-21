# C3 rev g StrongARM comparator (WO-107 item 2): devices and sizes of design/c3_comp/netlist.py (sizes_draft.py rev g:
# KP 0.84/0.15, RSO 1.0/0.3), drawn as sky130 gencells, routed by cells/route.tcl. No external cell reuse (D96).
# Row A: input pair M1/M2 as 8 x 5/0.5 unit fingers, ABBA ABBA, end dummies (all terminals vss), mirror about the
#   row centre (left half gate escape left, right half right). Row B: cascodes K1/K2 ABBA ABBA with the tail T x4
#   in the middle, same pitch. Row C: ap/an precharge P1/P2. Rows D/E: mirror-symmetric latch rows (o side left,
#   n side right): M3/M4, M5/M6, R0..R3, KPo/KPn, first/second buffers. Rows F/G: SR latch, clamps, output buffers.
# Broken copies: drcbad (met1 sliver); swap (finger 1 of the pair wired as M2: d an, g inn -> M1 3, M2 5 fingers).
source $env(LAYDIR)/cells/lib.tcl
source $env(LAYDIR)/cells/route.tcl
set HN nfet_g5v0d10v5; set HP pfet_g5v0d10v5; set NF nfet_01v8; set PF pfet_01v8
proc lvrow {devs} {
    # devs: {name model w l d g s b side}; LV gap 1.4 (nwell spacing 1.27)
    foreach d $devs { lassign $d n m w l dd g s b side; rt::fet $n $m $w $l $dd $g $s $b $side 1.4 }
}
proc build {cell {broken none}} {
    global HN HP NF PF
    cellname create $cell
    load $cell
    rt::reset
    # Row A: D A B B A | A B B A D
    rt::row 0
    set i 0
    foreach f {D A B B A A B B A D} {
        set side [expr {$i < 5 ? "l" : "r"}]
        if {$f eq "D"} {
            rt::fet XD$i $HN 5 0.5 vss vss vss vss $side 1.6
        } else {
            set n [expr {$f eq "A" ? {ap inp tl} : {an inn tl}}]
            if {$broken eq "swap" && $i == 1} { set n {an inn tl} }
            lassign $n d g s
            rt::fet XP$f$i $HN 5 0.5 $d $g $s vss $side 1.6
        }
        incr i
    }
    set y [rt::row_end]
    # Row B: K1 K2 K2 K1 T T | T T K1 K2 K2 K1
    rt::row $y
    set i 0
    foreach f {1 2 2 1 T T T T 1 2 2 1} {
        set side [expr {$i < 6 ? "l" : "r"}]
        switch $f {
            1 { rt::fet XK1_$i $HN 5 0.5 dp vdd ap vss $side 1.6 }
            2 { rt::fet XK2_$i $HN 5 0.5 dn vdd an vss $side 1.6 }
            T { rt::fet XT_$i  $HN 5 0.5 tl clk vss vss $side 1.6 }
        }
        incr i
    }
    set y [rt::row_end]
    # Row C: HV PMOS precharge of ap/an
    rt::row [expr {$y + 1.0}]
    rt::fet XP1 $HP 2 0.5 ap clk vdd vdd l 2.5
    rt::fet XP2 $HP 2 0.5 an clk vdd vdd r 2.5
    set y [rt::row_end]
    # Row D: LV NMOS latch row (mirror)
    rt::row [expr {$y + 1.5}]
    lvrow [list [list XBo2n $NF 0.5 0.15 ob2 ob1 vss vss l] [list XBo1n $NF 0.5 0.15 ob1 op vss vss l] \
               [list XM3 $NF 4 0.5 op on dp vss l] [list XM4 $NF 4 0.5 on op dn vss r] \
               [list XBn1n $NF 0.5 0.15 nb1 on vss vss r] [list XBn2n $NF 0.5 0.15 nb2 nb1 vss vss r]]
    set y [rt::row_end]
    # Row E: LV PMOS latch row (mirror)
    rt::row $y
    lvrow [list [list XBo2p $PF 1 0.15 ob2 ob1 vdd vdd l] [list XBo1p $PF 1 0.15 ob1 op vdd vdd l] \
               [list XKPo $PF 0.84 0.15 op ob1 vdd vdd l] [list XR2 $PF 1 0.15 dp clk vdd vdd l] \
               [list XR0 $PF 1 0.3 op clk vdd vdd l] [list XM5 $PF 4 0.5 op on vdd vdd l] \
               [list XM6 $PF 4 0.5 on op vdd vdd r] [list XR1 $PF 1 0.3 on clk vdd vdd r] \
               [list XR3 $PF 1 0.15 dn clk vdd vdd r] [list XKPn $PF 0.84 0.15 on nb1 vdd vdd r] \
               [list XBn1p $PF 1 0.15 nb1 on vdd vdd r] [list XBn2p $PF 1 0.15 nb2 nb1 vdd vdd r]]
    set y [rt::row_end]
    # Row F: SR latch NMOS, stack clamps, output buffer NMOS
    rt::row $y
    lvrow [list [list XSq3 $NF 1 0.15 ql ob2 sq vss r] [list XSq4 $NF 1 0.15 sq qlb vss vss r] \
               [list XSq5 $NF 0.42 0.15 sq ob1 vss vss r] [list XSb3 $NF 1 0.15 qlb nb2 sb vss r] \
               [list XSb4 $NF 1 0.15 sb ql vss vss r] [list XSb5 $NF 0.42 0.15 sb nb1 vss vss r] \
               [list XOq1n $NF 0.5 0.15 qo1 ql vss vss r] [list XOq2n $NF 2 0.15 q qo1 vss vss r] \
               [list XOb1n $NF 0.5 0.15 qbo1 qlb vss vss r] [list XOb2n $NF 2 0.15 qb qbo1 vss vss r]]
    set y [rt::row_end]
    # Row G: SR latch PMOS, output buffer PMOS
    rt::row $y
    lvrow [list [list XSq1 $PF 1 0.15 ql ob2 vdd vdd r] [list XSq2 $PF 1 0.15 ql qlb vdd vdd r] \
               [list XSb1 $PF 1 0.15 qlb nb2 vdd vdd r] [list XSb2 $PF 1 0.15 qlb ql vdd vdd r] \
               [list XOq1p $PF 1 0.15 qo1 ql vdd vdd r] [list XOq2p $PF 4 0.15 q qo1 vdd vdd r] \
               [list XOb1p $PF 1 0.15 qbo1 qlb vdd vdd r] [list XOb2p $PF 4 0.15 qb qbo1 vdd vdd r]]
    set y [rt::row_end]
    rt::finish {inp inn clk q qb vdd vss} $y
    if {$broken eq "drc"} { rect metal1 -5.0 0 -4.95 3.0 }
    writeall force
}
build c3_comp
build c3_comp_drcbad drc
build c3_comp_swap swap
puts "C3 BUILD DONE"
quit -noprompt
