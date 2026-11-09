* WO-15 item 4 (m6): W-bin check, pfet_01v8 tt, W 2/5/20 um at L 1 and 2 um, |Vsd| 0.5 V. Output: gmid_wbin_01v8_tt_T<temp>.csv (Vsg, Id for W2L1 W5L1 W20L1 W2L2 W5L2 W20L2)
.lib /home/mempool/.ciel/sky130A/libs.tech/ngspice/sky130.lib.spice tt
Vs s 0 1.8
Vsg s g 0
Vd1 s d1 0.5
Vd2 s d2 0.5
Vd3 s d3 0.5
Vd4 s d4 0.5
Vd5 s d5 0.5
Vd6 s d6 0.5
X1 d1 g s s sky130_fd_pr__pfet_01v8 w=2 l=1 ad=0.58 as=0.58 pd=4.6 ps=4.6
X2 d2 g s s sky130_fd_pr__pfet_01v8 w=5 l=1 ad=1.45 as=1.45 pd=10.6 ps=10.6
X3 d3 g s s sky130_fd_pr__pfet_01v8 w=20 l=1 ad=5.8 as=5.8 pd=40.6 ps=40.6
X4 d4 g s s sky130_fd_pr__pfet_01v8 w=2 l=2 ad=0.58 as=0.58 pd=4.6 ps=4.6
X5 d5 g s s sky130_fd_pr__pfet_01v8 w=5 l=2 ad=1.45 as=1.45 pd=10.6 ps=10.6
X6 d6 g s s sky130_fd_pr__pfet_01v8 w=20 l=2 ad=5.8 as=5.8 pd=40.6 ps=40.6
.option gmin=1e-18
.control
set wr_singlescale
foreach t -40 27 100 125
  set temp=$t
  dc Vsg 0 1.8 0.005
  wrdata gmid_wbin_01v8_tt_T{$t}.csv i(Vd1) i(Vd2) i(Vd3) i(Vd4) i(Vd5) i(Vd6)
end
quit
.endc
.end
