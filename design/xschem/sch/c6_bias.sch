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
N -440 80 -400 80 {lab=vdl}
C {iopin.sym} -440 80 0 0 {name=p2 lab=vdl}
C {lab_pin.sym} -400 80 0 0 {name=lp2 lab=vdl}
N -440 120 -400 120 {lab=boost}
C {iopin.sym} -440 120 0 0 {name=p3 lab=boost}
C {lab_pin.sym} -400 120 0 0 {name=lp3 lab=boost}
N -440 160 -400 160 {lab=trim0}
C {iopin.sym} -440 160 0 0 {name=p4 lab=trim0}
C {lab_pin.sym} -400 160 0 0 {name=lp4 lab=trim0}
N -440 200 -400 200 {lab=trim1}
C {iopin.sym} -440 200 0 0 {name=p5 lab=trim1}
C {lab_pin.sym} -400 200 0 0 {name=lp5 lab=trim1}
N -440 240 -400 240 {lab=trim2}
C {iopin.sym} -440 240 0 0 {name=p6 lab=trim2}
C {lab_pin.sym} -400 240 0 0 {name=lp6 lab=trim2}
N -440 280 -400 280 {lab=ibtp}
C {iopin.sym} -440 280 0 0 {name=p7 lab=ibtp}
C {lab_pin.sym} -400 280 0 0 {name=lp7 lab=ibtp}
N -440 320 -400 320 {lab=ibn}
C {iopin.sym} -440 320 0 0 {name=p8 lab=ibn}
C {lab_pin.sym} -400 320 0 0 {name=lp8 lab=ibn}
N -440 360 -400 360 {lab=ibp}
C {iopin.sym} -440 360 0 0 {name=p9 lab=ibp}
C {lab_pin.sym} -400 360 0 0 {name=lp9 lab=ibp}
N -440 400 -400 400 {lab=ivbl0}
C {iopin.sym} -440 400 0 0 {name=p10 lab=ivbl0}
C {lab_pin.sym} -400 400 0 0 {name=lp10 lab=ivbl0}
N -440 440 -400 440 {lab=ok}
C {iopin.sym} -440 440 0 0 {name=p11 lab=ok}
C {lab_pin.sym} -400 440 0 0 {name=lp11 lab=ok}
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
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 860 0 0 {name=mk L=4 W=2.1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
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
C {cells/sky130_fd_sc_hvl__lsbuflv2hv_1.sym} 900 1340 0 0 {name=Xls_boost}
N 820 1360 800 1360 {lab=boost}
C {lab_pin.sym} 800 1360 0 0 {name=l176 lab=boost}
N 820 1380 800 1380 {lab=vdl}
C {lab_pin.sym} 800 1380 0 0 {name=l177 lab=vdl}
N 820 1400 800 1400 {lab=vss}
C {lab_pin.sym} 800 1400 0 0 {name=l178 lab=vss}
N 820 1420 800 1420 {lab=vss}
C {lab_pin.sym} 800 1420 0 0 {name=l179 lab=vss}
N 980 1360 1000 1360 {lab=vdd}
C {lab_pin.sym} 1000 1360 0 0 {name=l180 lab=vdd}
N 980 1380 1000 1380 {lab=vdd}
C {lab_pin.sym} 1000 1380 0 0 {name=l181 lab=vdd}
N 980 1400 1000 1400 {lab=boost_h}
C {lab_pin.sym} 1000 1400 0 0 {name=l182 lab=boost_h}
C {cells/sky130_fd_sc_hvl__inv_1.sym} 900 1540 0 0 {name=Xiv_boost}
N 820 1560 800 1560 {lab=boost_h}
C {lab_pin.sym} 800 1560 0 0 {name=l183 lab=boost_h}
N 820 1580 800 1580 {lab=vss}
C {lab_pin.sym} 800 1580 0 0 {name=l184 lab=vss}
N 820 1600 800 1600 {lab=vss}
C {lab_pin.sym} 800 1600 0 0 {name=l185 lab=vss}
N 980 1560 1000 1560 {lab=vdd}
C {lab_pin.sym} 1000 1560 0 0 {name=l186 lab=vdd}
N 980 1580 1000 1580 {lab=vdd}
C {lab_pin.sym} 1000 1580 0 0 {name=l187 lab=vdd}
N 980 1600 1000 1600 {lab=boost_b}
C {lab_pin.sym} 1000 1600 0 0 {name=l188 lab=boost_b}
C {cells/sky130_fd_sc_hvl__lsbuflv2hv_1.sym} 900 1720 0 0 {name=Xls_trim0}
N 820 1740 800 1740 {lab=trim0}
C {lab_pin.sym} 800 1740 0 0 {name=l189 lab=trim0}
N 820 1760 800 1760 {lab=vdl}
C {lab_pin.sym} 800 1760 0 0 {name=l190 lab=vdl}
N 820 1780 800 1780 {lab=vss}
C {lab_pin.sym} 800 1780 0 0 {name=l191 lab=vss}
N 820 1800 800 1800 {lab=vss}
C {lab_pin.sym} 800 1800 0 0 {name=l192 lab=vss}
N 980 1740 1000 1740 {lab=vdd}
C {lab_pin.sym} 1000 1740 0 0 {name=l193 lab=vdd}
N 980 1760 1000 1760 {lab=vdd}
C {lab_pin.sym} 1000 1760 0 0 {name=l194 lab=vdd}
N 980 1780 1000 1780 {lab=trim0_h}
C {lab_pin.sym} 1000 1780 0 0 {name=l195 lab=trim0_h}
C {cells/sky130_fd_sc_hvl__inv_1.sym} 900 1920 0 0 {name=Xiv_trim0}
N 820 1940 800 1940 {lab=trim0_h}
C {lab_pin.sym} 800 1940 0 0 {name=l196 lab=trim0_h}
N 820 1960 800 1960 {lab=vss}
C {lab_pin.sym} 800 1960 0 0 {name=l197 lab=vss}
N 820 1980 800 1980 {lab=vss}
C {lab_pin.sym} 800 1980 0 0 {name=l198 lab=vss}
N 980 1940 1000 1940 {lab=vdd}
C {lab_pin.sym} 1000 1940 0 0 {name=l199 lab=vdd}
N 980 1960 1000 1960 {lab=vdd}
C {lab_pin.sym} 1000 1960 0 0 {name=l200 lab=vdd}
N 980 1980 1000 1980 {lab=trim0_b}
C {lab_pin.sym} 1000 1980 0 0 {name=l201 lab=trim0_b}
C {cells/sky130_fd_sc_hvl__lsbuflv2hv_1.sym} 900 2100 0 0 {name=Xls_trim1}
N 820 2120 800 2120 {lab=trim1}
C {lab_pin.sym} 800 2120 0 0 {name=l202 lab=trim1}
N 820 2140 800 2140 {lab=vdl}
C {lab_pin.sym} 800 2140 0 0 {name=l203 lab=vdl}
N 820 2160 800 2160 {lab=vss}
C {lab_pin.sym} 800 2160 0 0 {name=l204 lab=vss}
N 820 2180 800 2180 {lab=vss}
C {lab_pin.sym} 800 2180 0 0 {name=l205 lab=vss}
N 980 2120 1000 2120 {lab=vdd}
C {lab_pin.sym} 1000 2120 0 0 {name=l206 lab=vdd}
N 980 2140 1000 2140 {lab=vdd}
C {lab_pin.sym} 1000 2140 0 0 {name=l207 lab=vdd}
N 980 2160 1000 2160 {lab=trim1_h}
C {lab_pin.sym} 1000 2160 0 0 {name=l208 lab=trim1_h}
C {cells/sky130_fd_sc_hvl__inv_1.sym} 900 2300 0 0 {name=Xiv_trim1}
N 820 2320 800 2320 {lab=trim1_h}
C {lab_pin.sym} 800 2320 0 0 {name=l209 lab=trim1_h}
N 820 2340 800 2340 {lab=vss}
C {lab_pin.sym} 800 2340 0 0 {name=l210 lab=vss}
N 820 2360 800 2360 {lab=vss}
C {lab_pin.sym} 800 2360 0 0 {name=l211 lab=vss}
N 980 2320 1000 2320 {lab=vdd}
C {lab_pin.sym} 1000 2320 0 0 {name=l212 lab=vdd}
N 980 2340 1000 2340 {lab=vdd}
C {lab_pin.sym} 1000 2340 0 0 {name=l213 lab=vdd}
N 980 2360 1000 2360 {lab=trim1_b}
C {lab_pin.sym} 1000 2360 0 0 {name=l214 lab=trim1_b}
C {cells/sky130_fd_sc_hvl__lsbuflv2hv_1.sym} 900 2480 0 0 {name=Xls_trim2}
N 820 2500 800 2500 {lab=trim2}
C {lab_pin.sym} 800 2500 0 0 {name=l215 lab=trim2}
N 820 2520 800 2520 {lab=vdl}
C {lab_pin.sym} 800 2520 0 0 {name=l216 lab=vdl}
N 820 2540 800 2540 {lab=vss}
C {lab_pin.sym} 800 2540 0 0 {name=l217 lab=vss}
N 820 2560 800 2560 {lab=vss}
C {lab_pin.sym} 800 2560 0 0 {name=l218 lab=vss}
N 980 2500 1000 2500 {lab=vdd}
C {lab_pin.sym} 1000 2500 0 0 {name=l219 lab=vdd}
N 980 2520 1000 2520 {lab=vdd}
C {lab_pin.sym} 1000 2520 0 0 {name=l220 lab=vdd}
N 980 2540 1000 2540 {lab=trim2_h}
C {lab_pin.sym} 1000 2540 0 0 {name=l221 lab=trim2_h}
C {cells/sky130_fd_sc_hvl__inv_1.sym} 900 2680 0 0 {name=Xiv_trim2}
N 820 2700 800 2700 {lab=trim2_h}
C {lab_pin.sym} 800 2700 0 0 {name=l222 lab=trim2_h}
N 820 2720 800 2720 {lab=vss}
C {lab_pin.sym} 800 2720 0 0 {name=l223 lab=vss}
N 820 2740 800 2740 {lab=vss}
C {lab_pin.sym} 800 2740 0 0 {name=l224 lab=vss}
N 980 2700 1000 2700 {lab=vdd}
C {lab_pin.sym} 1000 2700 0 0 {name=l225 lab=vdd}
N 980 2720 1000 2720 {lab=vdd}
C {lab_pin.sym} 1000 2720 0 0 {name=l226 lab=vdd}
N 980 2740 1000 2740 {lab=trim2_b}
C {lab_pin.sym} 1000 2740 0 0 {name=l227 lab=trim2_b}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 2860 0 0 {name=mm L=20 W=0.42 nf=1 mult=17 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 2890 940 2890 {lab=vnc}
C {lab_pin.sym} 940 2890 0 0 {name=l228 lab=vnc}
N 880 2860 860 2860 {lab=vg}
C {lab_pin.sym} 860 2860 0 0 {name=l229 lab=vg}
N 920 2830 940 2830 {lab=vdd}
C {lab_pin.sym} 940 2830 0 0 {name=l230 lab=vdd}
N 920 2860 940 2860 {lab=vdd}
C {lab_pin.sym} 940 2860 0 0 {name=l231 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 60 0 0 {name=mt0 L=20 W=0.42 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 90 1340 90 {lab=ts0}
C {lab_pin.sym} 1340 90 0 0 {name=l232 lab=ts0}
N 1280 60 1260 60 {lab=vg}
C {lab_pin.sym} 1260 60 0 0 {name=l233 lab=vg}
N 1320 30 1340 30 {lab=vdd}
C {lab_pin.sym} 1340 30 0 0 {name=l234 lab=vdd}
N 1320 60 1340 60 {lab=vdd}
C {lab_pin.sym} 1340 60 0 0 {name=l235 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 220 0 0 {name=mw0 L=0.5 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 250 1340 250 {lab=vnc}
C {lab_pin.sym} 1340 250 0 0 {name=l236 lab=vnc}
N 1280 220 1260 220 {lab=trim0_b}
C {lab_pin.sym} 1260 220 0 0 {name=l237 lab=trim0_b}
N 1320 190 1340 190 {lab=ts0}
C {lab_pin.sym} 1340 190 0 0 {name=l238 lab=ts0}
N 1320 220 1340 220 {lab=vdd}
C {lab_pin.sym} 1340 220 0 0 {name=l239 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 380 0 0 {name=mt1 L=20 W=0.42 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 410 1340 410 {lab=ts1}
C {lab_pin.sym} 1340 410 0 0 {name=l240 lab=ts1}
N 1280 380 1260 380 {lab=vg}
C {lab_pin.sym} 1260 380 0 0 {name=l241 lab=vg}
N 1320 350 1340 350 {lab=vdd}
C {lab_pin.sym} 1340 350 0 0 {name=l242 lab=vdd}
N 1320 380 1340 380 {lab=vdd}
C {lab_pin.sym} 1340 380 0 0 {name=l243 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 540 0 0 {name=mw1 L=0.5 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 570 1340 570 {lab=vnc}
C {lab_pin.sym} 1340 570 0 0 {name=l244 lab=vnc}
N 1280 540 1260 540 {lab=trim1_b}
C {lab_pin.sym} 1260 540 0 0 {name=l245 lab=trim1_b}
N 1320 510 1340 510 {lab=ts1}
C {lab_pin.sym} 1340 510 0 0 {name=l246 lab=ts1}
N 1320 540 1340 540 {lab=vdd}
C {lab_pin.sym} 1340 540 0 0 {name=l247 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 700 0 0 {name=mt2 L=20 W=0.42 nf=1 mult=4 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 730 1340 730 {lab=ts2}
C {lab_pin.sym} 1340 730 0 0 {name=l248 lab=ts2}
N 1280 700 1260 700 {lab=vg}
C {lab_pin.sym} 1260 700 0 0 {name=l249 lab=vg}
N 1320 670 1340 670 {lab=vdd}
C {lab_pin.sym} 1340 670 0 0 {name=l250 lab=vdd}
N 1320 700 1340 700 {lab=vdd}
C {lab_pin.sym} 1340 700 0 0 {name=l251 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 860 0 0 {name=mw2 L=0.5 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 890 1340 890 {lab=vnc}
C {lab_pin.sym} 1340 890 0 0 {name=l252 lab=vnc}
N 1280 860 1260 860 {lab=trim2_b}
C {lab_pin.sym} 1260 860 0 0 {name=l253 lab=trim2_b}
N 1320 830 1340 830 {lab=ts2}
C {lab_pin.sym} 1340 830 0 0 {name=l254 lab=ts2}
N 1320 860 1340 860 {lab=vdd}
C {lab_pin.sym} 1340 860 0 0 {name=l255 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1020 0 0 {name=mdc1 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 990 1340 990 {lab=vnc}
C {lab_pin.sym} 1340 990 0 0 {name=l256 lab=vnc}
N 1280 1020 1260 1020 {lab=vnc}
C {lab_pin.sym} 1260 1020 0 0 {name=l257 lab=vnc}
N 1320 1050 1340 1050 {lab=vn}
C {lab_pin.sym} 1340 1050 0 0 {name=l258 lab=vn}
N 1320 1020 1340 1020 {lab=vss}
C {lab_pin.sym} 1340 1020 0 0 {name=l259 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1180 0 0 {name=mdm1 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1150 1340 1150 {lab=vn}
C {lab_pin.sym} 1340 1150 0 0 {name=l260 lab=vn}
N 1280 1180 1260 1180 {lab=vn}
C {lab_pin.sym} 1260 1180 0 0 {name=l261 lab=vn}
N 1320 1210 1340 1210 {lab=vss}
C {lab_pin.sym} 1340 1210 0 0 {name=l262 lab=vss}
N 1320 1180 1340 1180 {lab=vss}
C {lab_pin.sym} 1340 1180 0 0 {name=l263 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1340 0 0 {name=msb L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1310 1340 1310 {lab=vnc}
C {lab_pin.sym} 1340 1310 0 0 {name=l264 lab=vnc}
N 1280 1340 1260 1340 {lab=boost_b}
C {lab_pin.sym} 1260 1340 0 0 {name=l265 lab=boost_b}
N 1320 1370 1340 1370 {lab=vns}
C {lab_pin.sym} 1340 1370 0 0 {name=l266 lab=vns}
N 1320 1340 1340 1340 {lab=vss}
C {lab_pin.sym} 1340 1340 0 0 {name=l267 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1500 0 0 {name=mdc2 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1470 1340 1470 {lab=vns}
C {lab_pin.sym} 1340 1470 0 0 {name=l268 lab=vns}
N 1280 1500 1260 1500 {lab=vnc}
C {lab_pin.sym} 1260 1500 0 0 {name=l269 lab=vnc}
N 1320 1530 1340 1530 {lab=vn2}
C {lab_pin.sym} 1340 1530 0 0 {name=l270 lab=vn2}
N 1320 1500 1340 1500 {lab=vss}
C {lab_pin.sym} 1340 1500 0 0 {name=l271 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1660 0 0 {name=mdm2 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1630 1340 1630 {lab=vn2}
C {lab_pin.sym} 1340 1630 0 0 {name=l272 lab=vn2}
N 1280 1660 1260 1660 {lab=vn}
C {lab_pin.sym} 1260 1660 0 0 {name=l273 lab=vn}
N 1320 1690 1340 1690 {lab=vss}
C {lab_pin.sym} 1340 1690 0 0 {name=l274 lab=vss}
N 1320 1660 1340 1660 {lab=vss}
C {lab_pin.sym} 1340 1660 0 0 {name=l275 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1820 0 0 {name=mibtp0 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1790 1340 1790 {lab=ibtpm}
C {lab_pin.sym} 1340 1790 0 0 {name=l276 lab=ibtpm}
N 1280 1820 1260 1820 {lab=vn}
C {lab_pin.sym} 1260 1820 0 0 {name=l277 lab=vn}
N 1320 1850 1340 1850 {lab=vss}
C {lab_pin.sym} 1340 1850 0 0 {name=l278 lab=vss}
N 1320 1820 1340 1820 {lab=vss}
C {lab_pin.sym} 1340 1820 0 0 {name=l279 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1980 0 0 {name=cibtp0 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1950 1340 1950 {lab=ibtp}
C {lab_pin.sym} 1340 1950 0 0 {name=l280 lab=ibtp}
N 1280 1980 1260 1980 {lab=vnc}
C {lab_pin.sym} 1260 1980 0 0 {name=l281 lab=vnc}
N 1320 2010 1340 2010 {lab=ibtpm}
C {lab_pin.sym} 1340 2010 0 0 {name=l282 lab=ibtpm}
N 1320 1980 1340 1980 {lab=vss}
C {lab_pin.sym} 1340 1980 0 0 {name=l283 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2140 0 0 {name=mibtp1 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2110 1340 2110 {lab=ibtpm}
C {lab_pin.sym} 1340 2110 0 0 {name=l284 lab=ibtpm}
N 1280 2140 1260 2140 {lab=vn}
C {lab_pin.sym} 1260 2140 0 0 {name=l285 lab=vn}
N 1320 2170 1340 2170 {lab=vss}
C {lab_pin.sym} 1340 2170 0 0 {name=l286 lab=vss}
N 1320 2140 1340 2140 {lab=vss}
C {lab_pin.sym} 1340 2140 0 0 {name=l287 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2300 0 0 {name=cibtp1 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2270 1340 2270 {lab=ibtp}
C {lab_pin.sym} 1340 2270 0 0 {name=l288 lab=ibtp}
N 1280 2300 1260 2300 {lab=vnc}
C {lab_pin.sym} 1260 2300 0 0 {name=l289 lab=vnc}
N 1320 2330 1340 2330 {lab=ibtpm}
C {lab_pin.sym} 1340 2330 0 0 {name=l290 lab=ibtpm}
N 1320 2300 1340 2300 {lab=vss}
C {lab_pin.sym} 1340 2300 0 0 {name=l291 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2460 0 0 {name=mibtp2 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2430 1340 2430 {lab=ibtpm}
C {lab_pin.sym} 1340 2430 0 0 {name=l292 lab=ibtpm}
N 1280 2460 1260 2460 {lab=vn}
C {lab_pin.sym} 1260 2460 0 0 {name=l293 lab=vn}
N 1320 2490 1340 2490 {lab=vss}
C {lab_pin.sym} 1340 2490 0 0 {name=l294 lab=vss}
N 1320 2460 1340 2460 {lab=vss}
C {lab_pin.sym} 1340 2460 0 0 {name=l295 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2620 0 0 {name=cibtp2 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2590 1340 2590 {lab=ibtp}
C {lab_pin.sym} 1340 2590 0 0 {name=l296 lab=ibtp}
N 1280 2620 1260 2620 {lab=vnc}
C {lab_pin.sym} 1260 2620 0 0 {name=l297 lab=vnc}
N 1320 2650 1340 2650 {lab=ibtpm}
C {lab_pin.sym} 1340 2650 0 0 {name=l298 lab=ibtpm}
N 1320 2620 1340 2620 {lab=vss}
C {lab_pin.sym} 1340 2620 0 0 {name=l299 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2780 0 0 {name=mibtp3 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2750 1340 2750 {lab=ibtpm}
C {lab_pin.sym} 1340 2750 0 0 {name=l300 lab=ibtpm}
N 1280 2780 1260 2780 {lab=vn}
C {lab_pin.sym} 1260 2780 0 0 {name=l301 lab=vn}
N 1320 2810 1340 2810 {lab=vss}
C {lab_pin.sym} 1340 2810 0 0 {name=l302 lab=vss}
N 1320 2780 1340 2780 {lab=vss}
C {lab_pin.sym} 1340 2780 0 0 {name=l303 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2940 0 0 {name=cibtp3 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2910 1340 2910 {lab=ibtp}
C {lab_pin.sym} 1340 2910 0 0 {name=l304 lab=ibtp}
N 1280 2940 1260 2940 {lab=vnc}
C {lab_pin.sym} 1260 2940 0 0 {name=l305 lab=vnc}
N 1320 2970 1340 2970 {lab=ibtpm}
C {lab_pin.sym} 1340 2970 0 0 {name=l306 lab=ibtpm}
N 1320 2940 1340 2940 {lab=vss}
C {lab_pin.sym} 1340 2940 0 0 {name=l307 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 60 0 0 {name=mibtp4 L=4 W=0.809 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 30 1740 30 {lab=ibtpm}
C {lab_pin.sym} 1740 30 0 0 {name=l308 lab=ibtpm}
N 1680 60 1660 60 {lab=vn}
C {lab_pin.sym} 1660 60 0 0 {name=l309 lab=vn}
N 1720 90 1740 90 {lab=vss}
C {lab_pin.sym} 1740 90 0 0 {name=l310 lab=vss}
N 1720 60 1740 60 {lab=vss}
C {lab_pin.sym} 1740 60 0 0 {name=l311 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 220 0 0 {name=cibtp4 L=1 W=0.809 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 190 1740 190 {lab=ibtp}
C {lab_pin.sym} 1740 190 0 0 {name=l312 lab=ibtp}
N 1680 220 1660 220 {lab=vnc}
C {lab_pin.sym} 1660 220 0 0 {name=l313 lab=vnc}
N 1720 250 1740 250 {lab=ibtpm}
C {lab_pin.sym} 1740 250 0 0 {name=l314 lab=ibtpm}
N 1720 220 1740 220 {lab=vss}
C {lab_pin.sym} 1740 220 0 0 {name=l315 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 380 0 0 {name=mibp0 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 350 1740 350 {lab=ibpm}
C {lab_pin.sym} 1740 350 0 0 {name=l316 lab=ibpm}
N 1680 380 1660 380 {lab=vn}
C {lab_pin.sym} 1660 380 0 0 {name=l317 lab=vn}
N 1720 410 1740 410 {lab=vss}
C {lab_pin.sym} 1740 410 0 0 {name=l318 lab=vss}
N 1720 380 1740 380 {lab=vss}
C {lab_pin.sym} 1740 380 0 0 {name=l319 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 540 0 0 {name=cibp0 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 510 1740 510 {lab=ibp}
C {lab_pin.sym} 1740 510 0 0 {name=l320 lab=ibp}
N 1680 540 1660 540 {lab=vnc}
C {lab_pin.sym} 1660 540 0 0 {name=l321 lab=vnc}
N 1720 570 1740 570 {lab=ibpm}
C {lab_pin.sym} 1740 570 0 0 {name=l322 lab=ibpm}
N 1720 540 1740 540 {lab=vss}
C {lab_pin.sym} 1740 540 0 0 {name=l323 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 700 0 0 {name=mibp1 L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 670 1740 670 {lab=ibpm}
C {lab_pin.sym} 1740 670 0 0 {name=l324 lab=ibpm}
N 1680 700 1660 700 {lab=vn}
C {lab_pin.sym} 1660 700 0 0 {name=l325 lab=vn}
N 1720 730 1740 730 {lab=vss}
C {lab_pin.sym} 1740 730 0 0 {name=l326 lab=vss}
N 1720 700 1740 700 {lab=vss}
C {lab_pin.sym} 1740 700 0 0 {name=l327 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 860 0 0 {name=cibp1 L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 830 1740 830 {lab=ibp}
C {lab_pin.sym} 1740 830 0 0 {name=l328 lab=ibp}
N 1680 860 1660 860 {lab=vnc}
C {lab_pin.sym} 1660 860 0 0 {name=l329 lab=vnc}
N 1720 890 1740 890 {lab=ibpm}
C {lab_pin.sym} 1740 890 0 0 {name=l330 lab=ibpm}
N 1720 860 1740 860 {lab=vss}
C {lab_pin.sym} 1740 860 0 0 {name=l331 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 1020 0 0 {name=mibp2 L=4 W=1.511 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 990 1740 990 {lab=ibpm}
C {lab_pin.sym} 1740 990 0 0 {name=l332 lab=ibpm}
N 1680 1020 1660 1020 {lab=vn}
C {lab_pin.sym} 1660 1020 0 0 {name=l333 lab=vn}
N 1720 1050 1740 1050 {lab=vss}
C {lab_pin.sym} 1740 1050 0 0 {name=l334 lab=vss}
N 1720 1020 1740 1020 {lab=vss}
C {lab_pin.sym} 1740 1020 0 0 {name=l335 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 1180 0 0 {name=cibp2 L=1 W=1.511 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 1150 1740 1150 {lab=ibp}
C {lab_pin.sym} 1740 1150 0 0 {name=l336 lab=ibp}
N 1680 1180 1660 1180 {lab=vnc}
C {lab_pin.sym} 1660 1180 0 0 {name=l337 lab=vnc}
N 1720 1210 1740 1210 {lab=ibpm}
C {lab_pin.sym} 1740 1210 0 0 {name=l338 lab=ibpm}
N 1720 1180 1740 1180 {lab=vss}
C {lab_pin.sym} 1740 1180 0 0 {name=l339 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 1340 0 0 {name=mivbl00 L=4 W=1.837 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 1310 1740 1310 {lab=ivbl0m}
C {lab_pin.sym} 1740 1310 0 0 {name=l340 lab=ivbl0m}
N 1680 1340 1660 1340 {lab=vn}
C {lab_pin.sym} 1660 1340 0 0 {name=l341 lab=vn}
N 1720 1370 1740 1370 {lab=vss}
C {lab_pin.sym} 1740 1370 0 0 {name=l342 lab=vss}
N 1720 1340 1740 1340 {lab=vss}
C {lab_pin.sym} 1740 1340 0 0 {name=l343 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 1500 0 0 {name=civbl00 L=1 W=1.837 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 1470 1740 1470 {lab=ivbl0}
C {lab_pin.sym} 1740 1470 0 0 {name=l344 lab=ivbl0}
N 1680 1500 1660 1500 {lab=vnc}
C {lab_pin.sym} 1660 1500 0 0 {name=l345 lab=vnc}
N 1720 1530 1740 1530 {lab=ivbl0m}
C {lab_pin.sym} 1740 1530 0 0 {name=l346 lab=ivbl0m}
N 1720 1500 1740 1500 {lab=vss}
C {lab_pin.sym} 1740 1500 0 0 {name=l347 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 1660 0 0 {name=mfm L=4 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 1630 1740 1630 {lab=vfm}
C {lab_pin.sym} 1740 1630 0 0 {name=l348 lab=vfm}
N 1680 1660 1660 1660 {lab=vn}
C {lab_pin.sym} 1660 1660 0 0 {name=l349 lab=vn}
N 1720 1690 1740 1690 {lab=vss}
C {lab_pin.sym} 1740 1690 0 0 {name=l350 lab=vss}
N 1720 1660 1740 1660 {lab=vss}
C {lab_pin.sym} 1740 1660 0 0 {name=l351 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1700 1820 0 0 {name=mfc L=1 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1720 1790 1740 1790 {lab=vp}
C {lab_pin.sym} 1740 1790 0 0 {name=l352 lab=vp}
N 1680 1820 1660 1820 {lab=vnc}
C {lab_pin.sym} 1660 1820 0 0 {name=l353 lab=vnc}
N 1720 1850 1740 1850 {lab=vfm}
C {lab_pin.sym} 1740 1850 0 0 {name=l354 lab=vfm}
N 1720 1820 1740 1820 {lab=vss}
C {lab_pin.sym} 1740 1820 0 0 {name=l355 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 1980 0 0 {name=mvp L=16 W=2 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2010 1740 2010 {lab=vp}
C {lab_pin.sym} 1740 2010 0 0 {name=l356 lab=vp}
N 1680 1980 1660 1980 {lab=vp}
C {lab_pin.sym} 1660 1980 0 0 {name=l357 lab=vp}
N 1720 1950 1740 1950 {lab=vdd}
C {lab_pin.sym} 1740 1950 0 0 {name=l358 lab=vdd}
N 1720 1980 1740 1980 {lab=vdd}
C {lab_pin.sym} 1740 1980 0 0 {name=l359 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 2140 0 0 {name=mibn0 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2170 1740 2170 {lab=ibn}
C {lab_pin.sym} 1740 2170 0 0 {name=l360 lab=ibn}
N 1680 2140 1660 2140 {lab=vp}
C {lab_pin.sym} 1660 2140 0 0 {name=l361 lab=vp}
N 1720 2110 1740 2110 {lab=vdd}
C {lab_pin.sym} 1740 2110 0 0 {name=l362 lab=vdd}
N 1720 2140 1740 2140 {lab=vdd}
C {lab_pin.sym} 1740 2140 0 0 {name=l363 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 2300 0 0 {name=mibn1 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2330 1740 2330 {lab=ibn}
C {lab_pin.sym} 1740 2330 0 0 {name=l364 lab=ibn}
N 1680 2300 1660 2300 {lab=vp}
C {lab_pin.sym} 1660 2300 0 0 {name=l365 lab=vp}
N 1720 2270 1740 2270 {lab=vdd}
C {lab_pin.sym} 1740 2270 0 0 {name=l366 lab=vdd}
N 1720 2300 1740 2300 {lab=vdd}
C {lab_pin.sym} 1740 2300 0 0 {name=l367 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 2460 0 0 {name=mibn2 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2490 1740 2490 {lab=ibn}
C {lab_pin.sym} 1740 2490 0 0 {name=l368 lab=ibn}
N 1680 2460 1660 2460 {lab=vp}
C {lab_pin.sym} 1660 2460 0 0 {name=l369 lab=vp}
N 1720 2430 1740 2430 {lab=vdd}
C {lab_pin.sym} 1740 2430 0 0 {name=l370 lab=vdd}
N 1720 2460 1740 2460 {lab=vdd}
C {lab_pin.sym} 1740 2460 0 0 {name=l371 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 2620 0 0 {name=mibn3 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2650 1740 2650 {lab=ibn}
C {lab_pin.sym} 1740 2650 0 0 {name=l372 lab=ibn}
N 1680 2620 1660 2620 {lab=vp}
C {lab_pin.sym} 1660 2620 0 0 {name=l373 lab=vp}
N 1720 2590 1740 2590 {lab=vdd}
C {lab_pin.sym} 1740 2590 0 0 {name=l374 lab=vdd}
N 1720 2620 1740 2620 {lab=vdd}
C {lab_pin.sym} 1740 2620 0 0 {name=l375 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 2780 0 0 {name=mibn4 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2810 1740 2810 {lab=ibn}
C {lab_pin.sym} 1740 2810 0 0 {name=l376 lab=ibn}
N 1680 2780 1660 2780 {lab=vp}
C {lab_pin.sym} 1660 2780 0 0 {name=l377 lab=vp}
N 1720 2750 1740 2750 {lab=vdd}
C {lab_pin.sym} 1740 2750 0 0 {name=l378 lab=vdd}
N 1720 2780 1740 2780 {lab=vdd}
C {lab_pin.sym} 1740 2780 0 0 {name=l379 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1700 2940 0 0 {name=mibn5 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1720 2970 1740 2970 {lab=ibn}
C {lab_pin.sym} 1740 2970 0 0 {name=l380 lab=ibn}
N 1680 2940 1660 2940 {lab=vp}
C {lab_pin.sym} 1660 2940 0 0 {name=l381 lab=vp}
N 1720 2910 1740 2910 {lab=vdd}
C {lab_pin.sym} 1740 2910 0 0 {name=l382 lab=vdd}
N 1720 2940 1740 2940 {lab=vdd}
C {lab_pin.sym} 1740 2940 0 0 {name=l383 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 2100 60 0 0 {name=mibn6 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 2120 90 2140 90 {lab=ibn}
C {lab_pin.sym} 2140 90 0 0 {name=l384 lab=ibn}
N 2080 60 2060 60 {lab=vp}
C {lab_pin.sym} 2060 60 0 0 {name=l385 lab=vp}
N 2120 30 2140 30 {lab=vdd}
C {lab_pin.sym} 2140 30 0 0 {name=l386 lab=vdd}
N 2120 60 2140 60 {lab=vdd}
C {lab_pin.sym} 2140 60 0 0 {name=l387 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 2100 220 0 0 {name=mibn7 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 2120 250 2140 250 {lab=ibn}
C {lab_pin.sym} 2140 250 0 0 {name=l388 lab=ibn}
N 2080 220 2060 220 {lab=vp}
C {lab_pin.sym} 2060 220 0 0 {name=l389 lab=vp}
N 2120 190 2140 190 {lab=vdd}
C {lab_pin.sym} 2140 190 0 0 {name=l390 lab=vdd}
N 2120 220 2140 220 {lab=vdd}
C {lab_pin.sym} 2140 220 0 0 {name=l391 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 2100 380 0 0 {name=mibn8 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 2120 410 2140 410 {lab=ibn}
C {lab_pin.sym} 2140 410 0 0 {name=l392 lab=ibn}
N 2080 380 2060 380 {lab=vp}
C {lab_pin.sym} 2060 380 0 0 {name=l393 lab=vp}
N 2120 350 2140 350 {lab=vdd}
C {lab_pin.sym} 2140 350 0 0 {name=l394 lab=vdd}
N 2120 380 2140 380 {lab=vdd}
C {lab_pin.sym} 2140 380 0 0 {name=l395 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 2100 540 0 0 {name=mibn9 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 2120 570 2140 570 {lab=ibn}
C {lab_pin.sym} 2140 570 0 0 {name=l396 lab=ibn}
N 2080 540 2060 540 {lab=vp}
C {lab_pin.sym} 2060 540 0 0 {name=l397 lab=vp}
N 2120 510 2140 510 {lab=vdd}
C {lab_pin.sym} 2140 510 0 0 {name=l398 lab=vdd}
N 2120 540 2140 540 {lab=vdd}
C {lab_pin.sym} 2140 540 0 0 {name=l399 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 2100 700 0 0 {name=mibn10 L=16 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 2120 730 2140 730 {lab=ibn}
C {lab_pin.sym} 2140 730 0 0 {name=l400 lab=ibn}
N 2080 700 2060 700 {lab=vp}
C {lab_pin.sym} 2060 700 0 0 {name=l401 lab=vp}
N 2120 670 2140 670 {lab=vdd}
C {lab_pin.sym} 2140 670 0 0 {name=l402 lab=vdd}
N 2120 700 2140 700 {lab=vdd}
C {lab_pin.sym} 2140 700 0 0 {name=l403 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 2100 860 0 0 {name=mibn11 L=16 W=1.341 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 2120 890 2140 890 {lab=ibn}
C {lab_pin.sym} 2140 890 0 0 {name=l404 lab=ibn}
N 2080 860 2060 860 {lab=vp}
C {lab_pin.sym} 2060 860 0 0 {name=l405 lab=vp}
N 2120 830 2140 830 {lab=vdd}
C {lab_pin.sym} 2140 830 0 0 {name=l406 lab=vdd}
N 2120 860 2140 860 {lab=vdd}
C {lab_pin.sym} 2140 860 0 0 {name=l407 lab=vdd}
