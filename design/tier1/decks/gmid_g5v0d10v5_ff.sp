* WO-14 item 1: gm/Id of sky130 pfet_g5v0d10v5, corner ff, L 1 and 2 um, Vsd 0.5 V, bulk = source, 4 temperatures. Output: gmid_g5v0d10v5_ff_T<temp>.csv (Vsg, Id1, Id2)
.lib /home/mempool/.ciel/sky130A/libs.tech/ngspice/sky130.lib.spice ff
Vs s 0 3.3
Vsg s g 0
Vd1 s d1 0.5
Vd2 s d2 0.5
X1 d1 g s s sky130_fd_pr__pfet_g5v0d10v5 w=10 l=1 ad=2.9 as=2.9 pd=20.6 ps=20.6
X2 d2 g s s sky130_fd_pr__pfet_g5v0d10v5 w=10 l=2 ad=2.9 as=2.9 pd=20.6 ps=20.6
.option gmin=1e-18
.control
set wr_singlescale
foreach t -40 27 100 125
  set temp=$t
  dc Vsg 0 3.3 0.005
  wrdata gmid_g5v0d10v5_ff_T{$t}.csv i(Vd1) i(Vd2)
end
quit
.endc
.end
