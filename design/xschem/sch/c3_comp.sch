v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -440 0 -400 0 {lab=inp}
C {iopin.sym} -440 0 0 0 {name=p0 lab=inp}
C {lab_pin.sym} -400 0 0 0 {name=lp0 lab=inp}
N -440 40 -400 40 {lab=inn}
C {iopin.sym} -440 40 0 0 {name=p1 lab=inn}
C {lab_pin.sym} -400 40 0 0 {name=lp1 lab=inn}
N -440 80 -400 80 {lab=clk}
C {iopin.sym} -440 80 0 0 {name=p2 lab=clk}
C {lab_pin.sym} -400 80 0 0 {name=lp2 lab=clk}
N -440 120 -400 120 {lab=q}
C {iopin.sym} -440 120 0 0 {name=p3 lab=q}
C {lab_pin.sym} -400 120 0 0 {name=lp3 lab=q}
N -440 160 -400 160 {lab=qb}
C {iopin.sym} -440 160 0 0 {name=p4 lab=qb}
C {lab_pin.sym} -400 160 0 0 {name=lp4 lab=qb}
N -440 200 -400 200 {lab=vdd}
C {iopin.sym} -440 200 0 0 {name=p5 lab=vdd}
C {lab_pin.sym} -400 200 0 0 {name=lp5 lab=vdd}
N -440 240 -400 240 {lab=vss}
C {iopin.sym} -440 240 0 0 {name=p6 lab=vss}
C {lab_pin.sym} -400 240 0 0 {name=lp6 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 60 0 0 {name=T L=0.5 W=5.0 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 30 140 30 {lab=tl}
C {lab_pin.sym} 140 30 0 0 {name=l1 lab=tl}
N 80 60 60 60 {lab=clk}
C {lab_pin.sym} 60 60 0 0 {name=l2 lab=clk}
N 120 90 140 90 {lab=vss}
C {lab_pin.sym} 140 90 0 0 {name=l3 lab=vss}
N 120 60 140 60 {lab=vss}
C {lab_pin.sym} 140 60 0 0 {name=l4 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 220 0 0 {name=M1 L=0.5 W=5.0 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 190 140 190 {lab=ap}
C {lab_pin.sym} 140 190 0 0 {name=l5 lab=ap}
N 80 220 60 220 {lab=inp}
C {lab_pin.sym} 60 220 0 0 {name=l6 lab=inp}
N 120 250 140 250 {lab=tl}
C {lab_pin.sym} 140 250 0 0 {name=l7 lab=tl}
N 120 220 140 220 {lab=vss}
C {lab_pin.sym} 140 220 0 0 {name=l8 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 380 0 0 {name=M2 L=0.5 W=5.0 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 350 140 350 {lab=an}
C {lab_pin.sym} 140 350 0 0 {name=l9 lab=an}
N 80 380 60 380 {lab=inn}
C {lab_pin.sym} 60 380 0 0 {name=l10 lab=inn}
N 120 410 140 410 {lab=tl}
C {lab_pin.sym} 140 410 0 0 {name=l11 lab=tl}
N 120 380 140 380 {lab=vss}
C {lab_pin.sym} 140 380 0 0 {name=l12 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 540 0 0 {name=K1 L=0.5 W=5.0 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 510 140 510 {lab=dp}
C {lab_pin.sym} 140 510 0 0 {name=l13 lab=dp}
N 80 540 60 540 {lab=vdd}
C {lab_pin.sym} 60 540 0 0 {name=l14 lab=vdd}
N 120 570 140 570 {lab=ap}
C {lab_pin.sym} 140 570 0 0 {name=l15 lab=ap}
N 120 540 140 540 {lab=vss}
C {lab_pin.sym} 140 540 0 0 {name=l16 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 700 0 0 {name=K2 L=0.5 W=5.0 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 670 140 670 {lab=dn}
C {lab_pin.sym} 140 670 0 0 {name=l17 lab=dn}
N 80 700 60 700 {lab=vdd}
C {lab_pin.sym} 60 700 0 0 {name=l18 lab=vdd}
N 120 730 140 730 {lab=an}
C {lab_pin.sym} 140 730 0 0 {name=l19 lab=an}
N 120 700 140 700 {lab=vss}
C {lab_pin.sym} 140 700 0 0 {name=l20 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 860 0 0 {name=P1 L=0.5 W=2.0 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 890 140 890 {lab=ap}
C {lab_pin.sym} 140 890 0 0 {name=l21 lab=ap}
N 80 860 60 860 {lab=clk}
C {lab_pin.sym} 60 860 0 0 {name=l22 lab=clk}
N 120 830 140 830 {lab=vdd}
C {lab_pin.sym} 140 830 0 0 {name=l23 lab=vdd}
N 120 860 140 860 {lab=vdd}
C {lab_pin.sym} 140 860 0 0 {name=l24 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1020 0 0 {name=P2 L=0.5 W=2.0 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1050 140 1050 {lab=an}
C {lab_pin.sym} 140 1050 0 0 {name=l25 lab=an}
N 80 1020 60 1020 {lab=clk}
C {lab_pin.sym} 60 1020 0 0 {name=l26 lab=clk}
N 120 990 140 990 {lab=vdd}
C {lab_pin.sym} 140 990 0 0 {name=l27 lab=vdd}
N 120 1020 140 1020 {lab=vdd}
C {lab_pin.sym} 140 1020 0 0 {name=l28 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 100 1180 0 0 {name=M3 L=0.5 W=4.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 120 1150 140 1150 {lab=op}
C {lab_pin.sym} 140 1150 0 0 {name=l29 lab=op}
N 80 1180 60 1180 {lab=on}
C {lab_pin.sym} 60 1180 0 0 {name=l30 lab=on}
N 120 1210 140 1210 {lab=dp}
C {lab_pin.sym} 140 1210 0 0 {name=l31 lab=dp}
N 120 1180 140 1180 {lab=vss}
C {lab_pin.sym} 140 1180 0 0 {name=l32 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 100 1340 0 0 {name=M4 L=0.5 W=4.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 120 1310 140 1310 {lab=on}
C {lab_pin.sym} 140 1310 0 0 {name=l33 lab=on}
N 80 1340 60 1340 {lab=op}
C {lab_pin.sym} 60 1340 0 0 {name=l34 lab=op}
N 120 1370 140 1370 {lab=dn}
C {lab_pin.sym} 140 1370 0 0 {name=l35 lab=dn}
N 120 1340 140 1340 {lab=vss}
C {lab_pin.sym} 140 1340 0 0 {name=l36 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 100 1500 0 0 {name=M5 L=0.5 W=4.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 1530 140 1530 {lab=op}
C {lab_pin.sym} 140 1530 0 0 {name=l37 lab=op}
N 80 1500 60 1500 {lab=on}
C {lab_pin.sym} 60 1500 0 0 {name=l38 lab=on}
N 120 1470 140 1470 {lab=vdd}
C {lab_pin.sym} 140 1470 0 0 {name=l39 lab=vdd}
N 120 1500 140 1500 {lab=vdd}
C {lab_pin.sym} 140 1500 0 0 {name=l40 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 100 1660 0 0 {name=M6 L=0.5 W=4.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 1690 140 1690 {lab=on}
C {lab_pin.sym} 140 1690 0 0 {name=l41 lab=on}
N 80 1660 60 1660 {lab=op}
C {lab_pin.sym} 60 1660 0 0 {name=l42 lab=op}
N 120 1630 140 1630 {lab=vdd}
C {lab_pin.sym} 140 1630 0 0 {name=l43 lab=vdd}
N 120 1660 140 1660 {lab=vdd}
C {lab_pin.sym} 140 1660 0 0 {name=l44 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 100 1820 0 0 {name=R0 L=0.3 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 1850 140 1850 {lab=op}
C {lab_pin.sym} 140 1850 0 0 {name=l45 lab=op}
N 80 1820 60 1820 {lab=clk}
C {lab_pin.sym} 60 1820 0 0 {name=l46 lab=clk}
N 120 1790 140 1790 {lab=vdd}
C {lab_pin.sym} 140 1790 0 0 {name=l47 lab=vdd}
N 120 1820 140 1820 {lab=vdd}
C {lab_pin.sym} 140 1820 0 0 {name=l48 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 100 1980 0 0 {name=R1 L=0.3 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 2010 140 2010 {lab=on}
C {lab_pin.sym} 140 2010 0 0 {name=l49 lab=on}
N 80 1980 60 1980 {lab=clk}
C {lab_pin.sym} 60 1980 0 0 {name=l50 lab=clk}
N 120 1950 140 1950 {lab=vdd}
C {lab_pin.sym} 140 1950 0 0 {name=l51 lab=vdd}
N 120 1980 140 1980 {lab=vdd}
C {lab_pin.sym} 140 1980 0 0 {name=l52 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 100 2140 0 0 {name=R2 L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 2170 140 2170 {lab=dp}
C {lab_pin.sym} 140 2170 0 0 {name=l53 lab=dp}
N 80 2140 60 2140 {lab=clk}
C {lab_pin.sym} 60 2140 0 0 {name=l54 lab=clk}
N 120 2110 140 2110 {lab=vdd}
C {lab_pin.sym} 140 2110 0 0 {name=l55 lab=vdd}
N 120 2140 140 2140 {lab=vdd}
C {lab_pin.sym} 140 2140 0 0 {name=l56 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 100 2300 0 0 {name=R3 L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 2330 140 2330 {lab=dn}
C {lab_pin.sym} 140 2330 0 0 {name=l57 lab=dn}
N 80 2300 60 2300 {lab=clk}
C {lab_pin.sym} 60 2300 0 0 {name=l58 lab=clk}
N 120 2270 140 2270 {lab=vdd}
C {lab_pin.sym} 140 2270 0 0 {name=l59 lab=vdd}
N 120 2300 140 2300 {lab=vdd}
C {lab_pin.sym} 140 2300 0 0 {name=l60 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 100 2460 0 0 {name=Bo1n L=0.15 W=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 120 2430 140 2430 {lab=ob1}
C {lab_pin.sym} 140 2430 0 0 {name=l61 lab=ob1}
N 80 2460 60 2460 {lab=op}
C {lab_pin.sym} 60 2460 0 0 {name=l62 lab=op}
N 120 2490 140 2490 {lab=vss}
C {lab_pin.sym} 140 2490 0 0 {name=l63 lab=vss}
N 120 2460 140 2460 {lab=vss}
C {lab_pin.sym} 140 2460 0 0 {name=l64 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 100 2620 0 0 {name=Bo1p L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 2650 140 2650 {lab=ob1}
C {lab_pin.sym} 140 2650 0 0 {name=l65 lab=ob1}
N 80 2620 60 2620 {lab=op}
C {lab_pin.sym} 60 2620 0 0 {name=l66 lab=op}
N 120 2590 140 2590 {lab=vdd}
C {lab_pin.sym} 140 2590 0 0 {name=l67 lab=vdd}
N 120 2620 140 2620 {lab=vdd}
C {lab_pin.sym} 140 2620 0 0 {name=l68 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 100 2780 0 0 {name=Bo2n L=0.15 W=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 120 2750 140 2750 {lab=ob2}
C {lab_pin.sym} 140 2750 0 0 {name=l69 lab=ob2}
N 80 2780 60 2780 {lab=ob1}
C {lab_pin.sym} 60 2780 0 0 {name=l70 lab=ob1}
N 120 2810 140 2810 {lab=vss}
C {lab_pin.sym} 140 2810 0 0 {name=l71 lab=vss}
N 120 2780 140 2780 {lab=vss}
C {lab_pin.sym} 140 2780 0 0 {name=l72 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 100 2940 0 0 {name=Bo2p L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 120 2970 140 2970 {lab=ob2}
C {lab_pin.sym} 140 2970 0 0 {name=l73 lab=ob2}
N 80 2940 60 2940 {lab=ob1}
C {lab_pin.sym} 60 2940 0 0 {name=l74 lab=ob1}
N 120 2910 140 2910 {lab=vdd}
C {lab_pin.sym} 140 2910 0 0 {name=l75 lab=vdd}
N 120 2940 140 2940 {lab=vdd}
C {lab_pin.sym} 140 2940 0 0 {name=l76 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 500 60 0 0 {name=KPo L=0.15 W=0.84 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 90 540 90 {lab=op}
C {lab_pin.sym} 540 90 0 0 {name=l77 lab=op}
N 480 60 460 60 {lab=ob1}
C {lab_pin.sym} 460 60 0 0 {name=l78 lab=ob1}
N 520 30 540 30 {lab=vdd}
C {lab_pin.sym} 540 30 0 0 {name=l79 lab=vdd}
N 520 60 540 60 {lab=vdd}
C {lab_pin.sym} 540 60 0 0 {name=l80 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 500 220 0 0 {name=Bn1n L=0.15 W=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 190 540 190 {lab=nb1}
C {lab_pin.sym} 540 190 0 0 {name=l81 lab=nb1}
N 480 220 460 220 {lab=on}
C {lab_pin.sym} 460 220 0 0 {name=l82 lab=on}
N 520 250 540 250 {lab=vss}
C {lab_pin.sym} 540 250 0 0 {name=l83 lab=vss}
N 520 220 540 220 {lab=vss}
C {lab_pin.sym} 540 220 0 0 {name=l84 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 500 380 0 0 {name=Bn1p L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 410 540 410 {lab=nb1}
C {lab_pin.sym} 540 410 0 0 {name=l85 lab=nb1}
N 480 380 460 380 {lab=on}
C {lab_pin.sym} 460 380 0 0 {name=l86 lab=on}
N 520 350 540 350 {lab=vdd}
C {lab_pin.sym} 540 350 0 0 {name=l87 lab=vdd}
N 520 380 540 380 {lab=vdd}
C {lab_pin.sym} 540 380 0 0 {name=l88 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 500 540 0 0 {name=Bn2n L=0.15 W=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 510 540 510 {lab=nb2}
C {lab_pin.sym} 540 510 0 0 {name=l89 lab=nb2}
N 480 540 460 540 {lab=nb1}
C {lab_pin.sym} 460 540 0 0 {name=l90 lab=nb1}
N 520 570 540 570 {lab=vss}
C {lab_pin.sym} 540 570 0 0 {name=l91 lab=vss}
N 520 540 540 540 {lab=vss}
C {lab_pin.sym} 540 540 0 0 {name=l92 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 500 700 0 0 {name=Bn2p L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 730 540 730 {lab=nb2}
C {lab_pin.sym} 540 730 0 0 {name=l93 lab=nb2}
N 480 700 460 700 {lab=nb1}
C {lab_pin.sym} 460 700 0 0 {name=l94 lab=nb1}
N 520 670 540 670 {lab=vdd}
C {lab_pin.sym} 540 670 0 0 {name=l95 lab=vdd}
N 520 700 540 700 {lab=vdd}
C {lab_pin.sym} 540 700 0 0 {name=l96 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 500 860 0 0 {name=KPn L=0.15 W=0.84 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 890 540 890 {lab=on}
C {lab_pin.sym} 540 890 0 0 {name=l97 lab=on}
N 480 860 460 860 {lab=nb1}
C {lab_pin.sym} 460 860 0 0 {name=l98 lab=nb1}
N 520 830 540 830 {lab=vdd}
C {lab_pin.sym} 540 830 0 0 {name=l99 lab=vdd}
N 520 860 540 860 {lab=vdd}
C {lab_pin.sym} 540 860 0 0 {name=l100 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 500 1020 0 0 {name=Sq1 L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 1050 540 1050 {lab=ql}
C {lab_pin.sym} 540 1050 0 0 {name=l101 lab=ql}
N 480 1020 460 1020 {lab=ob2}
C {lab_pin.sym} 460 1020 0 0 {name=l102 lab=ob2}
N 520 990 540 990 {lab=vdd}
C {lab_pin.sym} 540 990 0 0 {name=l103 lab=vdd}
N 520 1020 540 1020 {lab=vdd}
C {lab_pin.sym} 540 1020 0 0 {name=l104 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 500 1180 0 0 {name=Sq2 L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 1210 540 1210 {lab=ql}
C {lab_pin.sym} 540 1210 0 0 {name=l105 lab=ql}
N 480 1180 460 1180 {lab=qlb}
C {lab_pin.sym} 460 1180 0 0 {name=l106 lab=qlb}
N 520 1150 540 1150 {lab=vdd}
C {lab_pin.sym} 540 1150 0 0 {name=l107 lab=vdd}
N 520 1180 540 1180 {lab=vdd}
C {lab_pin.sym} 540 1180 0 0 {name=l108 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 500 1340 0 0 {name=Sq3 L=0.15 W=1.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 1310 540 1310 {lab=ql}
C {lab_pin.sym} 540 1310 0 0 {name=l109 lab=ql}
N 480 1340 460 1340 {lab=ob2}
C {lab_pin.sym} 460 1340 0 0 {name=l110 lab=ob2}
N 520 1370 540 1370 {lab=sq}
C {lab_pin.sym} 540 1370 0 0 {name=l111 lab=sq}
N 520 1340 540 1340 {lab=vss}
C {lab_pin.sym} 540 1340 0 0 {name=l112 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 1500 0 0 {name=Sq4 L=0.15 W=1.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 1470 540 1470 {lab=sq}
C {lab_pin.sym} 540 1470 0 0 {name=l113 lab=sq}
N 480 1500 460 1500 {lab=qlb}
C {lab_pin.sym} 460 1500 0 0 {name=l114 lab=qlb}
N 520 1530 540 1530 {lab=vss}
C {lab_pin.sym} 540 1530 0 0 {name=l115 lab=vss}
N 520 1500 540 1500 {lab=vss}
C {lab_pin.sym} 540 1500 0 0 {name=l116 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 1660 0 0 {name=Sq5 L=0.15 W=0.42 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 1630 540 1630 {lab=sq}
C {lab_pin.sym} 540 1630 0 0 {name=l117 lab=sq}
N 480 1660 460 1660 {lab=ob1}
C {lab_pin.sym} 460 1660 0 0 {name=l118 lab=ob1}
N 520 1690 540 1690 {lab=vss}
C {lab_pin.sym} 540 1690 0 0 {name=l119 lab=vss}
N 520 1660 540 1660 {lab=vss}
C {lab_pin.sym} 540 1660 0 0 {name=l120 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 500 1820 0 0 {name=Sb1 L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 1850 540 1850 {lab=qlb}
C {lab_pin.sym} 540 1850 0 0 {name=l121 lab=qlb}
N 480 1820 460 1820 {lab=nb2}
C {lab_pin.sym} 460 1820 0 0 {name=l122 lab=nb2}
N 520 1790 540 1790 {lab=vdd}
C {lab_pin.sym} 540 1790 0 0 {name=l123 lab=vdd}
N 520 1820 540 1820 {lab=vdd}
C {lab_pin.sym} 540 1820 0 0 {name=l124 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 500 1980 0 0 {name=Sb2 L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 2010 540 2010 {lab=qlb}
C {lab_pin.sym} 540 2010 0 0 {name=l125 lab=qlb}
N 480 1980 460 1980 {lab=ql}
C {lab_pin.sym} 460 1980 0 0 {name=l126 lab=ql}
N 520 1950 540 1950 {lab=vdd}
C {lab_pin.sym} 540 1950 0 0 {name=l127 lab=vdd}
N 520 1980 540 1980 {lab=vdd}
C {lab_pin.sym} 540 1980 0 0 {name=l128 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 500 2140 0 0 {name=Sb3 L=0.15 W=1.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2110 540 2110 {lab=qlb}
C {lab_pin.sym} 540 2110 0 0 {name=l129 lab=qlb}
N 480 2140 460 2140 {lab=nb2}
C {lab_pin.sym} 460 2140 0 0 {name=l130 lab=nb2}
N 520 2170 540 2170 {lab=sb}
C {lab_pin.sym} 540 2170 0 0 {name=l131 lab=sb}
N 520 2140 540 2140 {lab=vss}
C {lab_pin.sym} 540 2140 0 0 {name=l132 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 2300 0 0 {name=Sb4 L=0.15 W=1.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2270 540 2270 {lab=sb}
C {lab_pin.sym} 540 2270 0 0 {name=l133 lab=sb}
N 480 2300 460 2300 {lab=ql}
C {lab_pin.sym} 460 2300 0 0 {name=l134 lab=ql}
N 520 2330 540 2330 {lab=vss}
C {lab_pin.sym} 540 2330 0 0 {name=l135 lab=vss}
N 520 2300 540 2300 {lab=vss}
C {lab_pin.sym} 540 2300 0 0 {name=l136 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 2460 0 0 {name=Sb5 L=0.15 W=0.42 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2430 540 2430 {lab=sb}
C {lab_pin.sym} 540 2430 0 0 {name=l137 lab=sb}
N 480 2460 460 2460 {lab=nb1}
C {lab_pin.sym} 460 2460 0 0 {name=l138 lab=nb1}
N 520 2490 540 2490 {lab=vss}
C {lab_pin.sym} 540 2490 0 0 {name=l139 lab=vss}
N 520 2460 540 2460 {lab=vss}
C {lab_pin.sym} 540 2460 0 0 {name=l140 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 2620 0 0 {name=Oq1n L=0.15 W=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2590 540 2590 {lab=qo1}
C {lab_pin.sym} 540 2590 0 0 {name=l141 lab=qo1}
N 480 2620 460 2620 {lab=ql}
C {lab_pin.sym} 460 2620 0 0 {name=l142 lab=ql}
N 520 2650 540 2650 {lab=vss}
C {lab_pin.sym} 540 2650 0 0 {name=l143 lab=vss}
N 520 2620 540 2620 {lab=vss}
C {lab_pin.sym} 540 2620 0 0 {name=l144 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 500 2780 0 0 {name=Oq1p L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 520 2810 540 2810 {lab=qo1}
C {lab_pin.sym} 540 2810 0 0 {name=l145 lab=qo1}
N 480 2780 460 2780 {lab=ql}
C {lab_pin.sym} 460 2780 0 0 {name=l146 lab=ql}
N 520 2750 540 2750 {lab=vdd}
C {lab_pin.sym} 540 2750 0 0 {name=l147 lab=vdd}
N 520 2780 540 2780 {lab=vdd}
C {lab_pin.sym} 540 2780 0 0 {name=l148 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 500 2940 0 0 {name=Oq2n L=0.15 W=2.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2910 540 2910 {lab=q}
C {lab_pin.sym} 540 2910 0 0 {name=l149 lab=q}
N 480 2940 460 2940 {lab=qo1}
C {lab_pin.sym} 460 2940 0 0 {name=l150 lab=qo1}
N 520 2970 540 2970 {lab=vss}
C {lab_pin.sym} 540 2970 0 0 {name=l151 lab=vss}
N 520 2940 540 2940 {lab=vss}
C {lab_pin.sym} 540 2940 0 0 {name=l152 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 900 60 0 0 {name=Oq2p L=0.15 W=4.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 920 90 940 90 {lab=q}
C {lab_pin.sym} 940 90 0 0 {name=l153 lab=q}
N 880 60 860 60 {lab=qo1}
C {lab_pin.sym} 860 60 0 0 {name=l154 lab=qo1}
N 920 30 940 30 {lab=vdd}
C {lab_pin.sym} 940 30 0 0 {name=l155 lab=vdd}
N 920 60 940 60 {lab=vdd}
C {lab_pin.sym} 940 60 0 0 {name=l156 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 900 220 0 0 {name=Ob1n L=0.15 W=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 920 190 940 190 {lab=qbo1}
C {lab_pin.sym} 940 190 0 0 {name=l157 lab=qbo1}
N 880 220 860 220 {lab=qlb}
C {lab_pin.sym} 860 220 0 0 {name=l158 lab=qlb}
N 920 250 940 250 {lab=vss}
C {lab_pin.sym} 940 250 0 0 {name=l159 lab=vss}
N 920 220 940 220 {lab=vss}
C {lab_pin.sym} 940 220 0 0 {name=l160 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 900 380 0 0 {name=Ob1p L=0.15 W=1.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 920 410 940 410 {lab=qbo1}
C {lab_pin.sym} 940 410 0 0 {name=l161 lab=qbo1}
N 880 380 860 380 {lab=qlb}
C {lab_pin.sym} 860 380 0 0 {name=l162 lab=qlb}
N 920 350 940 350 {lab=vdd}
C {lab_pin.sym} 940 350 0 0 {name=l163 lab=vdd}
N 920 380 940 380 {lab=vdd}
C {lab_pin.sym} 940 380 0 0 {name=l164 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 900 540 0 0 {name=Ob2n L=0.15 W=2.0 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 920 510 940 510 {lab=qb}
C {lab_pin.sym} 940 510 0 0 {name=l165 lab=qb}
N 880 540 860 540 {lab=qbo1}
C {lab_pin.sym} 860 540 0 0 {name=l166 lab=qbo1}
N 920 570 940 570 {lab=vss}
C {lab_pin.sym} 940 570 0 0 {name=l167 lab=vss}
N 920 540 940 540 {lab=vss}
C {lab_pin.sym} 940 540 0 0 {name=l168 lab=vss}
C {sky130_fd_pr/pfet_01v8.sym} 900 700 0 0 {name=Ob2p L=0.15 W=4.0 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
N 920 730 940 730 {lab=qb}
C {lab_pin.sym} 940 730 0 0 {name=l169 lab=qb}
N 880 700 860 700 {lab=qbo1}
C {lab_pin.sym} 860 700 0 0 {name=l170 lab=qbo1}
N 920 670 940 670 {lab=vdd}
C {lab_pin.sym} 940 670 0 0 {name=l171 lab=vdd}
N 920 700 940 700 {lab=vdd}
C {lab_pin.sym} 940 700 0 0 {name=l172 lab=vdd}
