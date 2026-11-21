# WO-109: C1 OTA1 (frozen WO-52 netlist, design/c1_ota1/netlist.py default build: cmfb sc, base mode) as multi-finger
# gencell arrays routed by cells/route2.tcl. Device W/L and finger counts are the netlist's; the arrays only split m.
# Matching: sinks mn1/mn2 and loads mpl1/mpl2 are ABBA in 4 arrays of 16 fingers; mpc1/mpc2 ABBA (4 x 8, separate
# nwells on sa/sb); input pair min1/min2 ABBA (4 x nf 6) in one tail nwell with 2 end dummies (nf 2, all terminals on
# tail, added to the LVS reference as XDUMP m=4); the tail mt is 2 x 16 fingers between mtr and mrt.
# MIM (cap_mim_m3_1, 2.0 fF/um2 + 0.19 fF/um): Cint 2 pF = 2 x 22.17 (999.9 fF each), Cc 100 fF = 6.885 (100.04 fF),
# Cr 50 fF = 4.815 (50.03 fF). Top plate (met4) on the high-impedance side: Cint bli, Cc ctl, Cr rbp/rbn.
# Caps are in their own row (not over the circuit: route2 uses met3/met4 for tracks/spines; D93 stacking is open).
# Broken copies: drcbad (met1 sliver); swap (array XMN1b, 16 fingers of mn1, wired as mn2: d fb -> mn1 16, mn2 48).
source $env(LAYDIR)/cells/lib.tcl
source $env(LAYDIR)/cells/route2.tcl
set HN nfet_g5v0d10v5; set HP pfet_g5v0d10v5; set NL nfet_01v8; set PL pfet_01v8
set PORTS {vdd vss inp inn outp outn vicm vocm ibtp ibn ibp ivbnc ivbpc ivbl0 chp chn chlp chln isl ph1 ph1b ph2 ph2b rstb}
proc rows {broken} {
    global HN HP NL PL
    set n1b [expr {$broken eq "swap" ? "fb" : "fa"}]
    set G 1.2; set P 2.0
    return [list \
      [list {c 22.17 bli vdd 1.5} {c 22.17 bli vdd 1.5} {c 6.885 ctl outp 1.5} {c 6.885 ctl outn 1.5} \
            {c 4.815 rbp rap 1.5} {c 4.815 rbn ran 1.5}] \
      [list [list f XMN1a $HN 2.25 8 2 8 fa ibn vss vss $G] [list f XMN2a $HN 2.25 8 2 8 fb ibn vss vss $G] \
            [list f XMN2b $HN 2.25 8 2 8 fb ibn vss vss $G] [list f XMN1b $HN 2.25 8 2 8 $n1b ibn vss vss $G]] \
      [list [list f XMNR $HN 2.25 8 2 2 ibn ibn vss vss $G] [list f XMRN $HN 2.25 8 2 2 rnd ibn vss vss $G] \
            [list f XMIT $HN 2.25 8 1 1 cit ibn vss vss $G] [list f XMNC1 $HN 5 2 2 2 outn ivbnc xa vss $G] \
            [list f XMNC2 $HN 5 2 2 2 outp ivbnc xb vss $G] [list f XMRNC $HN 5 2 1 1 ivbpc rcb rnd vss $G] \
            [list f XMBND $HN 1.25 16 1 1 ivbnc ivbnc vss vss $G]] \
      [list [list f XMRCB $HN 0.47 16 1 1 rcb rcb vss vss $G] [list f XMIA1 $HN 2.5 14 1 2 cid ctl cit vss $G] \
            [list f XMIA2 $HN 2.5 14 1 2 bli bli cit vss $G] [list f XSCI1 $HN 4 0.5 1 1 inp chp gp vss $G] \
            [list f XSCI2 $HN 4 0.5 1 1 inn chp gm vss $G] [list f XSCI3 $HN 4 0.5 1 1 inp chn gm vss $G] \
            [list f XSCI4 $HN 4 0.5 1 1 inn chn gp vss $G] [list f XSISL1 $HN 2 0.5 1 1 inp isl vicm vss $G] \
            [list f XSISL2 $HN 2 0.5 1 1 inn isl vicm vss $G] [list f XSBKN $HN 1 0.5 1 1 gbk vss ivbpc vss $G]] \
      [list [list f XSCF1 $NL 4 0.15 1 1 fa chlp xa vss 1.4] [list f XSCF2 $NL 4 0.15 1 1 fb chlp xb vss 1.4] \
            [list f XSCF3 $NL 4 0.15 1 1 fa chln xb vss 1.4] [list f XSCF4 $NL 4 0.15 1 1 fb chln xa vss $P] \
            [list f XMRIN $HN 0.42 0.5 1 1 rst rstb vss vss $G] [list f XMRSOPN $HN 2 0.5 1 1 outp rst vocm vss $G] \
            [list f XMRSONN $HN 2 0.5 1 1 outn rst vocm vss $G] [list f XSR1APN $HN 1 0.5 1 1 rap ph1 vocm vss $G] \
            [list f XSR1BPN $HN 1 0.5 1 1 rbp ph1 bli vss $G] [list f XSR2APN $HN 1 0.5 1 1 rap ph2 outp vss $G] \
            [list f XSR2BPN $HN 1 0.5 1 1 rbp ph2 ctl vss $G] [list f XSR1ANN $HN 1 0.5 1 1 ran ph1 vocm vss $G] \
            [list f XSR1BNN $HN 1 0.5 1 1 rbn ph1 bli vss $G] [list f XSR2ANN $HN 1 0.5 1 1 ran ph2 outn vss $G] \
            [list f XSR2BNN $HN 1 0.5 1 1 rbn ph2 ctl vss $G]] \
      [list [list f XMTR $HP 3.75 6 2 2 ibtp ibtp vdd vdd $P] [list f XMTa $HP 3.75 6 4 4 tail ibtp vdd vdd $P] \
            [list f XMTb $HP 3.75 6 4 4 tail ibtp vdd vdd $P] [list f XMRT $HP 3.75 6 2 1 ivbpc ibtp vdd vdd $P]] \
      [list [list f XMPLR $HP 2.5 4 2 2 ibp ibp vdd vdd $P] [list f XMPL1a $HP 2.5 4 2 8 sa ibp vdd vdd $P] \
            [list f XMPL2a $HP 2.5 4 2 8 sb ibp vdd vdd $P] [list f XMPL2b $HP 2.5 4 2 8 sb ibp vdd vdd $P] \
            [list f XMPL1b $HP 2.5 4 2 8 sa ibp vdd vdd $P] [list f XMRCP $HP 2.5 4 1 1 rcb ibp vdd vdd $P]] \
      [list [list f XMPC1a $HP 5 2 4 2 outn ivbpc sa sa $P] [list f XMPC2a $HP 5 2 4 2 outp ivbpc sb sb $P] \
            [list f XMPC2b $HP 5 2 4 2 outp ivbpc sb sb $P] [list f XMPC1b $HP 5 2 4 2 outn ivbpc sa sa $P] \
            [list f XMPLC1 $HP 1.875 2 4 2 sa ctl vdd vdd $P] [list f XMPLC2 $HP 1.875 2 4 2 sb ctl vdd vdd $P] \
            [list f XMBL0 $HP 1.875 2 1 1 ivbl0 ivbl0 vdd vdd $P]] \
      [list [list f XMBPD $HP 1.5 15 1 4 ivbpc ivbpc vdd vdd $P] [list f XMBPDS $HP 1.5 15 1 3 ivbpc gbk vdd vdd $P] \
            [list f XMBPX $HP 0.75 15 1 4 ivbnc ivbpc vdd vdd $P] [list f XMBPXS $HP 0.75 15 1 3 ivbnc gbk vdd vdd $P] \
            [list f XMPP1 $HP 5 0.5 2 1 fa vss da da $P] [list f XMPP2 $HP 5 0.5 2 1 fb vss db db $P]] \
      [list [list f XMIL1 $HP 3 16 1 2 cid cid vdd vdd $P] [list f XMIL2 $HP 3 16 1 2 bli cid vdd vdd $P] \
            [list f XDUM1 $PL 10 0.5 2 1 tail tail tail tail 1.4] [list f XMIN1a $PL 10 0.5 6 1 da gp tail tail 1.4] \
            [list f XMIN2a $PL 10 0.5 6 1 db gm tail tail 1.4] [list f XMIN2b $PL 10 0.5 6 1 db gm tail tail 1.4] \
            [list f XMIN1b $PL 10 0.5 6 1 da gp tail tail 1.4] [list f XDUM2 $PL 10 0.5 2 1 tail tail tail tail $P]] \
      [list [list f XSBKP $HP 2 0.5 1 1 gbk vdd ivbpc vdd $P] [list f XMBKU $HP 2 0.5 1 1 gbk vss vdd vdd $P] \
            [list f XMRST $HP 1 0.5 1 1 ctl rstb ivbl0 vdd $P] [list f XMRSB $HP 1 0.5 1 1 bli rstb ivbl0 vdd $P] \
            [list f XMRIP $HP 0.84 0.5 1 1 rst rstb vdd vdd $P] [list f XMRSOPP $HP 4 0.5 1 1 outp rstb vocm vdd $P] \
            [list f XMRSONP $HP 4 0.5 1 1 outn rstb vocm vdd $P] [list f XSR1APP $HP 2 0.5 1 1 rap ph1b vocm vdd $P] \
            [list f XSR1BPP $HP 2 0.5 1 1 rbp ph1b bli vdd $P] [list f XSR2APP $HP 2 0.5 1 1 rap ph2b outp vdd $P] \
            [list f XSR2BPP $HP 2 0.5 1 1 rbp ph2b ctl vdd $P] [list f XSR1ANP $HP 2 0.5 1 1 ran ph1b vocm vdd $P] \
            [list f XSR1BNP $HP 2 0.5 1 1 rbn ph1b bli vdd $P] [list f XSR2ANP $HP 2 0.5 1 1 ran ph2b outn vdd $P] \
            [list f XSR2BNP $HP 2 0.5 1 1 rbn ph2b ctl vdd $P]]]
}
proc build {cell {broken none}} {
    global PORTS
    cellname create $cell
    load $cell
    r2::reset
    r2::build [rows $broken] $PORTS
    if {$broken eq "drc"} { rect metal1 -5.0 0 -4.95 3.0 }
    writeall force
}
build c1_ota1
build c1_ota1_drcbad drc
build c1_ota1_swap swap
puts "C1 BUILD DONE"
quit -noprompt
