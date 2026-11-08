* WO-14 item 1 (D40): gm/Id of sky130 nfet_01v8, corner ss, L 1 and 2 um, Vds 0.5 V, bulk = source = 0, 4 temperatures. Output: gmid_n01v8_ss_T<temp>.csv (Id1, Id2 vs Vgs)
.lib /home/mempool/.ciel/sky130A/libs.tech/ngspice/sky130.lib.spice ss
Vsg g 0 0
Vd1 d1 0 0.5
Vd2 d2 0 0.5
X1 d1 g 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1 ad=2.9 as=2.9 pd=20.6 ps=20.6
X2 d2 g 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2 ad=2.9 as=2.9 pd=20.6 ps=20.6
.option gmin=1e-18
.control
set wr_singlescale
foreach t -40 27 100 125
  set temp=$t
  dc Vsg 0 1.8 0.005
  wrdata gmid_n01v8_ss_T{$t}.csv i(Vd1) i(Vd2)
end
quit
.endc
.end
