v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -440 0 -400 0 {lab=vdd}
C {iopin.sym} -440 0 0 0 {name=p0 lab=vdd}
C {lab_pin.sym} -400 0 0 0 {name=lp0 lab=vdd}
N -440 40 -400 40 {lab=vss}
C {iopin.sym} -440 40 0 0 {name=p1 lab=vss}
C {lab_pin.sym} -400 40 0 0 {name=lp1 lab=vss}
N -440 80 -400 80 {lab=vg}
C {iopin.sym} -440 80 0 0 {name=p2 lab=vg}
C {lab_pin.sym} -400 80 0 0 {name=lp2 lab=vg}
N -440 120 -400 120 {lab=vn}
C {iopin.sym} -440 120 0 0 {name=p3 lab=vn}
C {lab_pin.sym} -400 120 0 0 {name=lp3 lab=vn}
N -440 160 -400 160 {lab=ok}
C {iopin.sym} -440 160 0 0 {name=p4 lab=ok}
C {lab_pin.sym} -400 160 0 0 {name=lp4 lab=ok}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 60 0 0 {name=m1 L=20 W=0.42 nf=1 mult=17 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 90 140 90 {lab=a}
C {lab_pin.sym} 140 90 0 0 {name=l1 lab=a}
N 80 60 60 60 {lab=vg}
C {lab_pin.sym} 60 60 0 0 {name=l2 lab=vg}
N 120 30 140 30 {lab=vdd}
C {lab_pin.sym} 140 30 0 0 {name=l3 lab=vdd}
N 120 60 140 60 {lab=vdd}
C {lab_pin.sym} 140 60 0 0 {name=l4 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 220 0 0 {name=m2 L=20 W=0.42 nf=1 mult=17 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 250 140 250 {lab=b}
C {lab_pin.sym} 140 250 0 0 {name=l5 lab=b}
N 80 220 60 220 {lab=vg}
C {lab_pin.sym} 60 220 0 0 {name=l6 lab=vg}
N 120 190 140 190 {lab=vdd}
C {lab_pin.sym} 140 190 0 0 {name=l7 lab=vdd}
N 120 220 140 220 {lab=vdd}
C {lab_pin.sym} 140 220 0 0 {name=l8 lab=vdd}
C {sky130_fd_pr/pnp_05v5.sym} 100 380 0 0 {name=q1 model=pnp_05v5_W3p40L3p40 m=1 spiceprefix=X}
N 120 410 140 410 {lab=vss}
C {lab_pin.sym} 140 410 0 0 {name=l9 lab=vss}
N 80 380 60 380 {lab=vss}
C {lab_pin.sym} 60 380 0 0 {name=l10 lab=vss}
N 120 350 140 350 {lab=a}
C {lab_pin.sym} 140 350 0 0 {name=l11 lab=a}
C {sky130_fd_pr/pnp_05v5.sym} 100 540 0 0 {name=q2 model=pnp_05v5_W3p40L3p40 m=8 spiceprefix=X}
N 120 570 140 570 {lab=vss}
C {lab_pin.sym} 140 570 0 0 {name=l12 lab=vss}
N 80 540 60 540 {lab=vss}
C {lab_pin.sym} 60 540 0 0 {name=l13 lab=vss}
N 120 510 140 510 {lab=c}
C {lab_pin.sym} 140 510 0 0 {name=l14 lab=c}
C {sky130_fd_pr/res_xhigh_po_0p69.sym} 100 700 0 0 {name=r1 L=144.8 mult=1 model=res_xhigh_po_0p69 spiceprefix=X}
N 100 670 100 650 {lab=b}
C {lab_pin.sym} 100 650 0 0 {name=l15 lab=b}
N 100 730 100 750 {lab=c}
C {lab_pin.sym} 100 750 0 0 {name=l16 lab=c}
N 80 700 60 700 {lab=vss}
C {lab_pin.sym} 60 700 0 0 {name=l17 lab=vss}
C {sky130_fd_pr/res_xhigh_po_0p69.sym} 100 860 0 0 {name=r2a L=354.8 mult=1 model=res_xhigh_po_0p69 spiceprefix=X}
N 100 830 100 810 {lab=a}
C {lab_pin.sym} 100 810 0 0 {name=l18 lab=a}
N 100 890 100 910 {lab=vss}
C {lab_pin.sym} 100 910 0 0 {name=l19 lab=vss}
N 80 860 60 860 {lab=vss}
C {lab_pin.sym} 60 860 0 0 {name=l20 lab=vss}
C {sky130_fd_pr/res_xhigh_po_0p69.sym} 100 1020 0 0 {name=r2b L=354.8 mult=1 model=res_xhigh_po_0p69 spiceprefix=X}
N 100 990 100 970 {lab=b}
C {lab_pin.sym} 100 970 0 0 {name=l21 lab=b}
N 100 1050 100 1070 {lab=vss}
C {lab_pin.sym} 100 1070 0 0 {name=l22 lab=vss}
N 80 1020 60 1020 {lab=vss}
C {lab_pin.sym} 60 1020 0 0 {name=l23 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1180 0 0 {name=mt L=20 W=0.42 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1210 140 1210 {lab=t}
C {lab_pin.sym} 140 1210 0 0 {name=l24 lab=t}
N 80 1180 60 1180 {lab=vg}
C {lab_pin.sym} 60 1180 0 0 {name=l25 lab=vg}
N 120 1150 140 1150 {lab=vdd}
C {lab_pin.sym} 140 1150 0 0 {name=l26 lab=vdd}
N 120 1180 140 1180 {lab=vdd}
C {lab_pin.sym} 140 1180 0 0 {name=l27 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1340 0 0 {name=ma L=4 W=4 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1370 140 1370 {lab=n1}
C {lab_pin.sym} 140 1370 0 0 {name=l28 lab=n1}
N 80 1340 60 1340 {lab=a}
C {lab_pin.sym} 60 1340 0 0 {name=l29 lab=a}
N 120 1310 140 1310 {lab=t}
C {lab_pin.sym} 140 1310 0 0 {name=l30 lab=t}
N 120 1340 140 1340 {lab=t}
C {lab_pin.sym} 140 1340 0 0 {name=l31 lab=t}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1500 0 0 {name=mb L=4 W=8 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1530 140 1530 {lab=o1}
C {lab_pin.sym} 140 1530 0 0 {name=l32 lab=o1}
N 80 1500 60 1500 {lab=b}
C {lab_pin.sym} 60 1500 0 0 {name=l33 lab=b}
N 120 1470 140 1470 {lab=t}
C {lab_pin.sym} 140 1470 0 0 {name=l34 lab=t}
N 120 1500 140 1500 {lab=t}
C {lab_pin.sym} 140 1500 0 0 {name=l35 lab=t}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1660 0 0 {name=ml1 L=8 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1630 140 1630 {lab=n1}
C {lab_pin.sym} 140 1630 0 0 {name=l36 lab=n1}
N 80 1660 60 1660 {lab=n1}
C {lab_pin.sym} 60 1660 0 0 {name=l37 lab=n1}
N 120 1690 140 1690 {lab=vss}
C {lab_pin.sym} 140 1690 0 0 {name=l38 lab=vss}
N 120 1660 140 1660 {lab=vss}
C {lab_pin.sym} 140 1660 0 0 {name=l39 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1820 0 0 {name=ml2 L=8 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1790 140 1790 {lab=o1}
C {lab_pin.sym} 140 1790 0 0 {name=l40 lab=o1}
N 80 1820 60 1820 {lab=n1}
C {lab_pin.sym} 60 1820 0 0 {name=l41 lab=n1}
N 120 1850 140 1850 {lab=vss}
C {lab_pin.sym} 140 1850 0 0 {name=l42 lab=vss}
N 120 1820 140 1820 {lab=vss}
C {lab_pin.sym} 140 1820 0 0 {name=l43 lab=vss}
C {capa.sym} 100 1980 0 0 {name=Cc value=3e-12 m=1}
N 100 1950 100 1930 {lab=o1}
C {lab_pin.sym} 100 1930 0 0 {name=l44 lab=o1}
N 100 2010 100 2030 {lab=vss}
C {lab_pin.sym} 100 2030 0 0 {name=l45 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2140 0 0 {name=m5 L=8 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2110 140 2110 {lab=vg}
C {lab_pin.sym} 140 2110 0 0 {name=l46 lab=vg}
N 80 2140 60 2140 {lab=o1}
C {lab_pin.sym} 60 2140 0 0 {name=l47 lab=o1}
N 120 2170 140 2170 {lab=vss}
C {lab_pin.sym} 140 2170 0 0 {name=l48 lab=vss}
N 120 2140 140 2140 {lab=vss}
C {lab_pin.sym} 140 2140 0 0 {name=l49 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2300 0 0 {name=m6 L=20 W=0.42 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2330 140 2330 {lab=vg}
C {lab_pin.sym} 140 2330 0 0 {name=l50 lab=vg}
N 80 2300 60 2300 {lab=vg}
C {lab_pin.sym} 60 2300 0 0 {name=l51 lab=vg}
N 120 2270 140 2270 {lab=vdd}
C {lab_pin.sym} 140 2270 0 0 {name=l52 lab=vdd}
N 120 2300 140 2300 {lab=vdd}
C {lab_pin.sym} 140 2300 0 0 {name=l53 lab=vdd}
C {capa.sym} 100 2460 0 0 {name=Cvg value=1e-12 m=1}
N 100 2430 100 2410 {lab=vg}
C {lab_pin.sym} 100 2410 0 0 {name=l54 lab=vg}
N 100 2490 100 2510 {lab=vdd}
C {lab_pin.sym} 100 2510 0 0 {name=l55 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2620 0 0 {name=lk0 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2650 140 2650 {lab=l1}
C {lab_pin.sym} 140 2650 0 0 {name=l56 lab=l1}
N 80 2620 60 2620 {lab=vss}
C {lab_pin.sym} 60 2620 0 0 {name=l57 lab=vss}
N 120 2590 140 2590 {lab=vdd}
C {lab_pin.sym} 140 2590 0 0 {name=l58 lab=vdd}
N 120 2620 140 2620 {lab=vdd}
C {lab_pin.sym} 140 2620 0 0 {name=l59 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2780 0 0 {name=lk1 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2810 140 2810 {lab=l2}
C {lab_pin.sym} 140 2810 0 0 {name=l60 lab=l2}
N 80 2780 60 2780 {lab=vss}
C {lab_pin.sym} 60 2780 0 0 {name=l61 lab=vss}
N 120 2750 140 2750 {lab=l1}
C {lab_pin.sym} 140 2750 0 0 {name=l62 lab=l1}
N 120 2780 140 2780 {lab=vdd}
C {lab_pin.sym} 140 2780 0 0 {name=l63 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2940 0 0 {name=lk2 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2970 140 2970 {lab=l3}
C {lab_pin.sym} 140 2970 0 0 {name=l64 lab=l3}
N 80 2940 60 2940 {lab=vss}
C {lab_pin.sym} 60 2940 0 0 {name=l65 lab=vss}
N 120 2910 140 2910 {lab=l2}
C {lab_pin.sym} 140 2910 0 0 {name=l66 lab=l2}
N 120 2940 140 2940 {lab=vdd}
C {lab_pin.sym} 140 2940 0 0 {name=l67 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 60 0 0 {name=lk3 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 90 540 90 {lab=l4}
C {lab_pin.sym} 540 90 0 0 {name=l68 lab=l4}
N 480 60 460 60 {lab=vss}
C {lab_pin.sym} 460 60 0 0 {name=l69 lab=vss}
N 520 30 540 30 {lab=l3}
C {lab_pin.sym} 540 30 0 0 {name=l70 lab=l3}
N 520 60 540 60 {lab=vdd}
C {lab_pin.sym} 540 60 0 0 {name=l71 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 220 0 0 {name=lk4 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 250 540 250 {lab=l5}
C {lab_pin.sym} 540 250 0 0 {name=l72 lab=l5}
N 480 220 460 220 {lab=vss}
C {lab_pin.sym} 460 220 0 0 {name=l73 lab=vss}
N 520 190 540 190 {lab=l4}
C {lab_pin.sym} 540 190 0 0 {name=l74 lab=l4}
N 520 220 540 220 {lab=vdd}
C {lab_pin.sym} 540 220 0 0 {name=l75 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 380 0 0 {name=lk5 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 410 540 410 {lab=l6}
C {lab_pin.sym} 540 410 0 0 {name=l76 lab=l6}
N 480 380 460 380 {lab=vss}
C {lab_pin.sym} 460 380 0 0 {name=l77 lab=vss}
N 520 350 540 350 {lab=l5}
C {lab_pin.sym} 540 350 0 0 {name=l78 lab=l5}
N 520 380 540 380 {lab=vdd}
C {lab_pin.sym} 540 380 0 0 {name=l79 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 540 0 0 {name=lk6 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 570 540 570 {lab=l7}
C {lab_pin.sym} 540 570 0 0 {name=l80 lab=l7}
N 480 540 460 540 {lab=vss}
C {lab_pin.sym} 460 540 0 0 {name=l81 lab=vss}
N 520 510 540 510 {lab=l6}
C {lab_pin.sym} 540 510 0 0 {name=l82 lab=l6}
N 520 540 540 540 {lab=vdd}
C {lab_pin.sym} 540 540 0 0 {name=l83 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 700 0 0 {name=lk7 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 730 540 730 {lab=tsu}
C {lab_pin.sym} 540 730 0 0 {name=l84 lab=tsu}
N 480 700 460 700 {lab=vss}
C {lab_pin.sym} 460 700 0 0 {name=l85 lab=vss}
N 520 670 540 670 {lab=l7}
C {lab_pin.sym} 540 670 0 0 {name=l86 lab=l7}
N 520 700 540 700 {lab=vdd}
C {lab_pin.sym} 540 700 0 0 {name=l87 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 860 0 0 {name=mk L=4 W=1.05 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 830 540 830 {lab=tsu}
C {lab_pin.sym} 540 830 0 0 {name=l88 lab=tsu}
N 480 860 460 860 {lab=vn}
C {lab_pin.sym} 460 860 0 0 {name=l89 lab=vn}
N 520 890 540 890 {lab=vss}
C {lab_pin.sym} 540 890 0 0 {name=l90 lab=vss}
N 520 860 540 860 {lab=vss}
C {lab_pin.sym} 540 860 0 0 {name=l91 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1020 0 0 {name=mct L=20 W=0.42 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1050 540 1050 {lab=tc}
C {lab_pin.sym} 540 1050 0 0 {name=l92 lab=tc}
N 480 1020 460 1020 {lab=vg}
C {lab_pin.sym} 460 1020 0 0 {name=l93 lab=vg}
N 520 990 540 990 {lab=vdd}
C {lab_pin.sym} 540 990 0 0 {name=l94 lab=vdd}
N 520 1020 540 1020 {lab=vdd}
C {lab_pin.sym} 540 1020 0 0 {name=l95 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1180 0 0 {name=mcc L=4 W=4 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1210 540 1210 {lab=q}
C {lab_pin.sym} 540 1210 0 0 {name=l96 lab=q}
N 480 1180 460 1180 {lab=c}
C {lab_pin.sym} 460 1180 0 0 {name=l97 lab=c}
N 520 1150 540 1150 {lab=tc}
C {lab_pin.sym} 540 1150 0 0 {name=l98 lab=tc}
N 520 1180 540 1180 {lab=tc}
C {lab_pin.sym} 540 1180 0 0 {name=l99 lab=tc}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1340 0 0 {name=mcb L=4 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1370 540 1370 {lab=n2}
C {lab_pin.sym} 540 1370 0 0 {name=l100 lab=n2}
N 480 1340 460 1340 {lab=b}
C {lab_pin.sym} 460 1340 0 0 {name=l101 lab=b}
N 520 1310 540 1310 {lab=tc}
C {lab_pin.sym} 540 1310 0 0 {name=l102 lab=tc}
N 520 1340 540 1340 {lab=tc}
C {lab_pin.sym} 540 1340 0 0 {name=l103 lab=tc}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1500 0 0 {name=ml3 L=8 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1470 540 1470 {lab=n2}
C {lab_pin.sym} 540 1470 0 0 {name=l104 lab=n2}
N 480 1500 460 1500 {lab=n2}
C {lab_pin.sym} 460 1500 0 0 {name=l105 lab=n2}
N 520 1530 540 1530 {lab=vss}
C {lab_pin.sym} 540 1530 0 0 {name=l106 lab=vss}
N 520 1500 540 1500 {lab=vss}
C {lab_pin.sym} 540 1500 0 0 {name=l107 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1660 0 0 {name=ml4 L=8 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1630 540 1630 {lab=q}
C {lab_pin.sym} 540 1630 0 0 {name=l108 lab=q}
N 480 1660 460 1660 {lab=n2}
C {lab_pin.sym} 460 1660 0 0 {name=l109 lab=n2}
N 520 1690 540 1690 {lab=vss}
C {lab_pin.sym} 540 1690 0 0 {name=l110 lab=vss}
N 520 1660 540 1660 {lab=vss}
C {lab_pin.sym} 540 1660 0 0 {name=l111 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1820 0 0 {name=mqd L=1 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1790 540 1790 {lab=q}
C {lab_pin.sym} 540 1790 0 0 {name=l112 lab=q}
N 480 1820 460 1820 {lab=tsu}
C {lab_pin.sym} 460 1820 0 0 {name=l113 lab=tsu}
N 520 1850 540 1850 {lab=vss}
C {lab_pin.sym} 540 1850 0 0 {name=l114 lab=vss}
N 520 1820 540 1820 {lab=vss}
C {lab_pin.sym} 540 1820 0 0 {name=l115 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1980 0 0 {name=mhy1 L=20 W=0.42 nf=1 mult=4 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2010 540 2010 {lab=hy}
C {lab_pin.sym} 540 2010 0 0 {name=l116 lab=hy}
N 480 1980 460 1980 {lab=vg}
C {lab_pin.sym} 460 1980 0 0 {name=l117 lab=vg}
N 520 1950 540 1950 {lab=vdd}
C {lab_pin.sym} 540 1950 0 0 {name=l118 lab=vdd}
N 520 1980 540 1980 {lab=vdd}
C {lab_pin.sym} 540 1980 0 0 {name=l119 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2140 0 0 {name=mhy2 L=1 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2170 540 2170 {lab=q}
C {lab_pin.sym} 540 2170 0 0 {name=l120 lab=q}
N 480 2140 460 2140 {lab=sua}
C {lab_pin.sym} 460 2140 0 0 {name=l121 lab=sua}
N 520 2110 540 2110 {lab=hy}
C {lab_pin.sym} 540 2110 0 0 {name=l122 lab=hy}
N 520 2140 540 2140 {lab=vdd}
C {lab_pin.sym} 540 2140 0 0 {name=l123 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2300 0 0 {name=i1p L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2330 540 2330 {lab=sua}
C {lab_pin.sym} 540 2330 0 0 {name=l124 lab=sua}
N 480 2300 460 2300 {lab=q}
C {lab_pin.sym} 460 2300 0 0 {name=l125 lab=q}
N 520 2270 540 2270 {lab=vdd}
C {lab_pin.sym} 540 2270 0 0 {name=l126 lab=vdd}
N 520 2300 540 2300 {lab=vdd}
C {lab_pin.sym} 540 2300 0 0 {name=l127 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2460 0 0 {name=i1n L=1 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2430 540 2430 {lab=sua}
C {lab_pin.sym} 540 2430 0 0 {name=l128 lab=sua}
N 480 2460 460 2460 {lab=q}
C {lab_pin.sym} 460 2460 0 0 {name=l129 lab=q}
N 520 2490 540 2490 {lab=vss}
C {lab_pin.sym} 540 2490 0 0 {name=l130 lab=vss}
N 520 2460 540 2460 {lab=vss}
C {lab_pin.sym} 540 2460 0 0 {name=l131 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2620 0 0 {name=i2p L=1 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2650 540 2650 {lab=ok}
C {lab_pin.sym} 540 2650 0 0 {name=l132 lab=ok}
N 480 2620 460 2620 {lab=sua}
C {lab_pin.sym} 460 2620 0 0 {name=l133 lab=sua}
N 520 2590 540 2590 {lab=vdd}
C {lab_pin.sym} 540 2590 0 0 {name=l134 lab=vdd}
N 520 2620 540 2620 {lab=vdd}
C {lab_pin.sym} 540 2620 0 0 {name=l135 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2780 0 0 {name=i2n L=1 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2750 540 2750 {lab=ok}
C {lab_pin.sym} 540 2750 0 0 {name=l136 lab=ok}
N 480 2780 460 2780 {lab=sua}
C {lab_pin.sym} 460 2780 0 0 {name=l137 lab=sua}
N 520 2810 540 2810 {lab=vss}
C {lab_pin.sym} 540 2810 0 0 {name=l138 lab=vss}
N 520 2780 540 2780 {lab=vss}
C {lab_pin.sym} 540 2780 0 0 {name=l139 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2940 0 0 {name=mkw L=1 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2970 540 2970 {lab=kq}
C {lab_pin.sym} 540 2970 0 0 {name=l140 lab=kq}
N 480 2940 460 2940 {lab=ok}
C {lab_pin.sym} 460 2940 0 0 {name=l141 lab=ok}
N 520 2910 540 2910 {lab=vdd}
C {lab_pin.sym} 540 2910 0 0 {name=l142 lab=vdd}
N 520 2940 540 2940 {lab=vdd}
C {lab_pin.sym} 540 2940 0 0 {name=l143 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 60 0 0 {name=kc0 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 90 940 90 {lab=k1}
C {lab_pin.sym} 940 90 0 0 {name=l144 lab=k1}
N 880 60 860 60 {lab=vss}
C {lab_pin.sym} 860 60 0 0 {name=l145 lab=vss}
N 920 30 940 30 {lab=kq}
C {lab_pin.sym} 940 30 0 0 {name=l146 lab=kq}
N 920 60 940 60 {lab=vdd}
C {lab_pin.sym} 940 60 0 0 {name=l147 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 220 0 0 {name=kc1 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 250 940 250 {lab=k2}
C {lab_pin.sym} 940 250 0 0 {name=l148 lab=k2}
N 880 220 860 220 {lab=vss}
C {lab_pin.sym} 860 220 0 0 {name=l149 lab=vss}
N 920 190 940 190 {lab=k1}
C {lab_pin.sym} 940 190 0 0 {name=l150 lab=k1}
N 920 220 940 220 {lab=vdd}
C {lab_pin.sym} 940 220 0 0 {name=l151 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 380 0 0 {name=kc2 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 410 940 410 {lab=k3}
C {lab_pin.sym} 940 410 0 0 {name=l152 lab=k3}
N 880 380 860 380 {lab=vss}
C {lab_pin.sym} 860 380 0 0 {name=l153 lab=vss}
N 920 350 940 350 {lab=k2}
C {lab_pin.sym} 940 350 0 0 {name=l154 lab=k2}
N 920 380 940 380 {lab=vdd}
C {lab_pin.sym} 940 380 0 0 {name=l155 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 540 0 0 {name=kc3 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 570 940 570 {lab=k4}
C {lab_pin.sym} 940 570 0 0 {name=l156 lab=k4}
N 880 540 860 540 {lab=vss}
C {lab_pin.sym} 860 540 0 0 {name=l157 lab=vss}
N 920 510 940 510 {lab=k3}
C {lab_pin.sym} 940 510 0 0 {name=l158 lab=k3}
N 920 540 940 540 {lab=vdd}
C {lab_pin.sym} 940 540 0 0 {name=l159 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 700 0 0 {name=kc4 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 730 940 730 {lab=k5}
C {lab_pin.sym} 940 730 0 0 {name=l160 lab=k5}
N 880 700 860 700 {lab=vss}
C {lab_pin.sym} 860 700 0 0 {name=l161 lab=vss}
N 920 670 940 670 {lab=k4}
C {lab_pin.sym} 940 670 0 0 {name=l162 lab=k4}
N 920 700 940 700 {lab=vdd}
C {lab_pin.sym} 940 700 0 0 {name=l163 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 860 0 0 {name=kc5 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 890 940 890 {lab=k6}
C {lab_pin.sym} 940 890 0 0 {name=l164 lab=k6}
N 880 860 860 860 {lab=vss}
C {lab_pin.sym} 860 860 0 0 {name=l165 lab=vss}
N 920 830 940 830 {lab=k5}
C {lab_pin.sym} 940 830 0 0 {name=l166 lab=k5}
N 920 860 940 860 {lab=vdd}
C {lab_pin.sym} 940 860 0 0 {name=l167 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1020 0 0 {name=kc6 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1050 940 1050 {lab=k7}
C {lab_pin.sym} 940 1050 0 0 {name=l168 lab=k7}
N 880 1020 860 1020 {lab=vss}
C {lab_pin.sym} 860 1020 0 0 {name=l169 lab=vss}
N 920 990 940 990 {lab=k6}
C {lab_pin.sym} 940 990 0 0 {name=l170 lab=k6}
N 920 1020 940 1020 {lab=vdd}
C {lab_pin.sym} 940 1020 0 0 {name=l171 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1180 0 0 {name=kc7 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1210 940 1210 {lab=o1}
C {lab_pin.sym} 940 1210 0 0 {name=l172 lab=o1}
N 880 1180 860 1180 {lab=vss}
C {lab_pin.sym} 860 1180 0 0 {name=l173 lab=vss}
N 920 1150 940 1150 {lab=k7}
C {lab_pin.sym} 940 1150 0 0 {name=l174 lab=k7}
N 920 1180 940 1180 {lab=vdd}
C {lab_pin.sym} 940 1180 0 0 {name=l175 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1340 0 0 {name=mm L=20 W=0.42 nf=1 mult=21 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1370 940 1370 {lab=vn}
C {lab_pin.sym} 940 1370 0 0 {name=l176 lab=vn}
N 880 1340 860 1340 {lab=vg}
C {lab_pin.sym} 860 1340 0 0 {name=l177 lab=vg}
N 920 1310 940 1310 {lab=vdd}
C {lab_pin.sym} 940 1310 0 0 {name=l178 lab=vdd}
N 920 1340 940 1340 {lab=vdd}
C {lab_pin.sym} 940 1340 0 0 {name=l179 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1500 0 0 {name=mn L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1470 940 1470 {lab=vn}
C {lab_pin.sym} 940 1470 0 0 {name=l180 lab=vn}
N 880 1500 860 1500 {lab=vn}
C {lab_pin.sym} 860 1500 0 0 {name=l181 lab=vn}
N 920 1530 940 1530 {lab=vss}
C {lab_pin.sym} 940 1530 0 0 {name=l182 lab=vss}
N 920 1500 940 1500 {lab=vss}
C {lab_pin.sym} 940 1500 0 0 {name=l183 lab=vss}
