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
N -440 80 -400 80 {lab=inp}
C {iopin.sym} -440 80 0 0 {name=p2 lab=inp}
C {lab_pin.sym} -400 80 0 0 {name=lp2 lab=inp}
N -440 120 -400 120 {lab=inn}
C {iopin.sym} -440 120 0 0 {name=p3 lab=inn}
C {lab_pin.sym} -400 120 0 0 {name=lp3 lab=inn}
N -440 160 -400 160 {lab=outp}
C {iopin.sym} -440 160 0 0 {name=p4 lab=outp}
C {lab_pin.sym} -400 160 0 0 {name=lp4 lab=outp}
N -440 200 -400 200 {lab=outn}
C {iopin.sym} -440 200 0 0 {name=p5 lab=outn}
C {lab_pin.sym} -400 200 0 0 {name=lp5 lab=outn}
N -440 240 -400 240 {lab=vicm}
C {iopin.sym} -440 240 0 0 {name=p6 lab=vicm}
C {lab_pin.sym} -400 240 0 0 {name=lp6 lab=vicm}
N -440 280 -400 280 {lab=vocm}
C {iopin.sym} -440 280 0 0 {name=p7 lab=vocm}
C {lab_pin.sym} -400 280 0 0 {name=lp7 lab=vocm}
N -440 320 -400 320 {lab=ibtp}
C {iopin.sym} -440 320 0 0 {name=p8 lab=ibtp}
C {lab_pin.sym} -400 320 0 0 {name=lp8 lab=ibtp}
N -440 360 -400 360 {lab=ibn}
C {iopin.sym} -440 360 0 0 {name=p9 lab=ibn}
C {lab_pin.sym} -400 360 0 0 {name=lp9 lab=ibn}
N -440 400 -400 400 {lab=ibp}
C {iopin.sym} -440 400 0 0 {name=p10 lab=ibp}
C {lab_pin.sym} -400 400 0 0 {name=lp10 lab=ibp}
N -440 440 -400 440 {lab=ivbnc}
C {iopin.sym} -440 440 0 0 {name=p11 lab=ivbnc}
C {lab_pin.sym} -400 440 0 0 {name=lp11 lab=ivbnc}
N -440 480 -400 480 {lab=ivbpc}
C {iopin.sym} -440 480 0 0 {name=p12 lab=ivbpc}
C {lab_pin.sym} -400 480 0 0 {name=lp12 lab=ivbpc}
N -440 520 -400 520 {lab=ivbl0}
C {iopin.sym} -440 520 0 0 {name=p13 lab=ivbl0}
C {lab_pin.sym} -400 520 0 0 {name=lp13 lab=ivbl0}
N -440 560 -400 560 {lab=chp}
C {iopin.sym} -440 560 0 0 {name=p14 lab=chp}
C {lab_pin.sym} -400 560 0 0 {name=lp14 lab=chp}
N -440 600 -400 600 {lab=chn}
C {iopin.sym} -440 600 0 0 {name=p15 lab=chn}
C {lab_pin.sym} -400 600 0 0 {name=lp15 lab=chn}
N -440 640 -400 640 {lab=chlp}
C {iopin.sym} -440 640 0 0 {name=p16 lab=chlp}
C {lab_pin.sym} -400 640 0 0 {name=lp16 lab=chlp}
N -440 680 -400 680 {lab=chln}
C {iopin.sym} -440 680 0 0 {name=p17 lab=chln}
C {lab_pin.sym} -400 680 0 0 {name=lp17 lab=chln}
N -440 720 -400 720 {lab=isl}
C {iopin.sym} -440 720 0 0 {name=p18 lab=isl}
C {lab_pin.sym} -400 720 0 0 {name=lp18 lab=isl}
N -440 760 -400 760 {lab=ph1}
C {iopin.sym} -440 760 0 0 {name=p19 lab=ph1}
C {lab_pin.sym} -400 760 0 0 {name=lp19 lab=ph1}
N -440 800 -400 800 {lab=ph1b}
C {iopin.sym} -440 800 0 0 {name=p20 lab=ph1b}
C {lab_pin.sym} -400 800 0 0 {name=lp20 lab=ph1b}
N -440 840 -400 840 {lab=ph2}
C {iopin.sym} -440 840 0 0 {name=p21 lab=ph2}
C {lab_pin.sym} -400 840 0 0 {name=lp21 lab=ph2}
N -440 880 -400 880 {lab=ph2b}
C {iopin.sym} -440 880 0 0 {name=p22 lab=ph2b}
C {lab_pin.sym} -400 880 0 0 {name=lp22 lab=ph2b}
N -440 920 -400 920 {lab=rstb}
C {iopin.sym} -440 920 0 0 {name=p23 lab=rstb}
C {lab_pin.sym} -400 920 0 0 {name=lp23 lab=rstb}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 60 0 0 {name=mtr L=6 W=3.75 nf=1 mult=4 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 90 140 90 {lab=ibtp}
C {lab_pin.sym} 140 90 0 0 {name=l1 lab=ibtp}
N 80 60 60 60 {lab=ibtp}
C {lab_pin.sym} 60 60 0 0 {name=l2 lab=ibtp}
N 120 30 140 30 {lab=vdd}
C {lab_pin.sym} 140 30 0 0 {name=l3 lab=vdd}
N 120 60 140 60 {lab=vdd}
C {lab_pin.sym} 140 60 0 0 {name=l4 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 220 0 0 {name=mnr L=8 W=2.25 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 190 140 190 {lab=ibn}
C {lab_pin.sym} 140 190 0 0 {name=l5 lab=ibn}
N 80 220 60 220 {lab=ibn}
C {lab_pin.sym} 60 220 0 0 {name=l6 lab=ibn}
N 120 250 140 250 {lab=vss}
C {lab_pin.sym} 140 250 0 0 {name=l7 lab=vss}
N 120 220 140 220 {lab=vss}
C {lab_pin.sym} 140 220 0 0 {name=l8 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 380 0 0 {name=mplr L=4 W=2.5 nf=1 mult=4 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 410 140 410 {lab=ibp}
C {lab_pin.sym} 140 410 0 0 {name=l9 lab=ibp}
N 80 380 60 380 {lab=ibp}
C {lab_pin.sym} 60 380 0 0 {name=l10 lab=ibp}
N 120 350 140 350 {lab=vdd}
C {lab_pin.sym} 140 350 0 0 {name=l11 lab=vdd}
N 120 380 140 380 {lab=vdd}
C {lab_pin.sym} 140 380 0 0 {name=l12 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 540 0 0 {name=mbpd L=15 W=1.5 nf=1 mult=4 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 570 140 570 {lab=ivbpc}
C {lab_pin.sym} 140 570 0 0 {name=l13 lab=ivbpc}
N 80 540 60 540 {lab=ivbpc}
C {lab_pin.sym} 60 540 0 0 {name=l14 lab=ivbpc}
N 120 510 140 510 {lab=vdd}
C {lab_pin.sym} 140 510 0 0 {name=l15 lab=vdd}
N 120 540 140 540 {lab=vdd}
C {lab_pin.sym} 140 540 0 0 {name=l16 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 700 0 0 {name=mbpds L=15 W=1.5 nf=1 mult=3 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 730 140 730 {lab=ivbpc}
C {lab_pin.sym} 140 730 0 0 {name=l17 lab=ivbpc}
N 80 700 60 700 {lab=gbk}
C {lab_pin.sym} 60 700 0 0 {name=l18 lab=gbk}
N 120 670 140 670 {lab=vdd}
C {lab_pin.sym} 140 670 0 0 {name=l19 lab=vdd}
N 120 700 140 700 {lab=vdd}
C {lab_pin.sym} 140 700 0 0 {name=l20 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 860 0 0 {name=mbnd L=16 W=1.25 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 830 140 830 {lab=ivbnc}
C {lab_pin.sym} 140 830 0 0 {name=l21 lab=ivbnc}
N 80 860 60 860 {lab=ivbnc}
C {lab_pin.sym} 60 860 0 0 {name=l22 lab=ivbnc}
N 120 890 140 890 {lab=vss}
C {lab_pin.sym} 140 890 0 0 {name=l23 lab=vss}
N 120 860 140 860 {lab=vss}
C {lab_pin.sym} 140 860 0 0 {name=l24 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1020 0 0 {name=Sbkn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 990 140 990 {lab=gbk}
C {lab_pin.sym} 140 990 0 0 {name=l25 lab=gbk}
N 80 1020 60 1020 {lab=vss}
C {lab_pin.sym} 60 1020 0 0 {name=l26 lab=vss}
N 120 1050 140 1050 {lab=ivbpc}
C {lab_pin.sym} 140 1050 0 0 {name=l27 lab=ivbpc}
N 120 1020 140 1020 {lab=vss}
C {lab_pin.sym} 140 1020 0 0 {name=l28 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1180 0 0 {name=Sbkp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1210 140 1210 {lab=gbk}
C {lab_pin.sym} 140 1210 0 0 {name=l29 lab=gbk}
N 80 1180 60 1180 {lab=vdd}
C {lab_pin.sym} 60 1180 0 0 {name=l30 lab=vdd}
N 120 1150 140 1150 {lab=ivbpc}
C {lab_pin.sym} 140 1150 0 0 {name=l31 lab=ivbpc}
N 120 1180 140 1180 {lab=vdd}
C {lab_pin.sym} 140 1180 0 0 {name=l32 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1340 0 0 {name=mbku L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1370 140 1370 {lab=gbk}
C {lab_pin.sym} 140 1370 0 0 {name=l33 lab=gbk}
N 80 1340 60 1340 {lab=vss}
C {lab_pin.sym} 60 1340 0 0 {name=l34 lab=vss}
N 120 1310 140 1310 {lab=vdd}
C {lab_pin.sym} 140 1310 0 0 {name=l35 lab=vdd}
N 120 1340 140 1340 {lab=vdd}
C {lab_pin.sym} 140 1340 0 0 {name=l36 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1500 0 0 {name=mrcp L=4 W=2.5 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1530 140 1530 {lab=rcb}
C {lab_pin.sym} 140 1530 0 0 {name=l37 lab=rcb}
N 80 1500 60 1500 {lab=ibp}
C {lab_pin.sym} 60 1500 0 0 {name=l38 lab=ibp}
N 120 1470 140 1470 {lab=vdd}
C {lab_pin.sym} 140 1470 0 0 {name=l39 lab=vdd}
N 120 1500 140 1500 {lab=vdd}
C {lab_pin.sym} 140 1500 0 0 {name=l40 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1660 0 0 {name=mrcb L=16 W=0.47 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1630 140 1630 {lab=rcb}
C {lab_pin.sym} 140 1630 0 0 {name=l41 lab=rcb}
N 80 1660 60 1660 {lab=rcb}
C {lab_pin.sym} 60 1660 0 0 {name=l42 lab=rcb}
N 120 1690 140 1690 {lab=vss}
C {lab_pin.sym} 140 1690 0 0 {name=l43 lab=vss}
N 120 1660 140 1660 {lab=vss}
C {lab_pin.sym} 140 1660 0 0 {name=l44 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1820 0 0 {name=mrt L=6 W=3.75 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1850 140 1850 {lab=ivbpc}
C {lab_pin.sym} 140 1850 0 0 {name=l45 lab=ivbpc}
N 80 1820 60 1820 {lab=ibtp}
C {lab_pin.sym} 60 1820 0 0 {name=l46 lab=ibtp}
N 120 1790 140 1790 {lab=vdd}
C {lab_pin.sym} 140 1790 0 0 {name=l47 lab=vdd}
N 120 1820 140 1820 {lab=vdd}
C {lab_pin.sym} 140 1820 0 0 {name=l48 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1980 0 0 {name=mrnc L=2 W=5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1950 140 1950 {lab=ivbpc}
C {lab_pin.sym} 140 1950 0 0 {name=l49 lab=ivbpc}
N 80 1980 60 1980 {lab=rcb}
C {lab_pin.sym} 60 1980 0 0 {name=l50 lab=rcb}
N 120 2010 140 2010 {lab=rnd}
C {lab_pin.sym} 140 2010 0 0 {name=l51 lab=rnd}
N 120 1980 140 1980 {lab=vss}
C {lab_pin.sym} 140 1980 0 0 {name=l52 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2140 0 0 {name=mrn L=8 W=2.25 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2110 140 2110 {lab=rnd}
C {lab_pin.sym} 140 2110 0 0 {name=l53 lab=rnd}
N 80 2140 60 2140 {lab=ibn}
C {lab_pin.sym} 60 2140 0 0 {name=l54 lab=ibn}
N 120 2170 140 2170 {lab=vss}
C {lab_pin.sym} 140 2170 0 0 {name=l55 lab=vss}
N 120 2140 140 2140 {lab=vss}
C {lab_pin.sym} 140 2140 0 0 {name=l56 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2300 0 0 {name=mbpx L=15 W=0.75 nf=1 mult=4 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2330 140 2330 {lab=ivbnc}
C {lab_pin.sym} 140 2330 0 0 {name=l57 lab=ivbnc}
N 80 2300 60 2300 {lab=ivbpc}
C {lab_pin.sym} 60 2300 0 0 {name=l58 lab=ivbpc}
N 120 2270 140 2270 {lab=vdd}
C {lab_pin.sym} 140 2270 0 0 {name=l59 lab=vdd}
N 120 2300 140 2300 {lab=vdd}
C {lab_pin.sym} 140 2300 0 0 {name=l60 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2460 0 0 {name=mbpxs L=15 W=0.75 nf=1 mult=3 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2490 140 2490 {lab=ivbnc}
C {lab_pin.sym} 140 2490 0 0 {name=l61 lab=ivbnc}
N 80 2460 60 2460 {lab=gbk}
C {lab_pin.sym} 60 2460 0 0 {name=l62 lab=gbk}
N 120 2430 140 2430 {lab=vdd}
C {lab_pin.sym} 140 2430 0 0 {name=l63 lab=vdd}
N 120 2460 140 2460 {lab=vdd}
C {lab_pin.sym} 140 2460 0 0 {name=l64 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2620 0 0 {name=mbl0 L=2 W=1.875 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2650 140 2650 {lab=ivbl0}
C {lab_pin.sym} 140 2650 0 0 {name=l65 lab=ivbl0}
N 80 2620 60 2620 {lab=ivbl0}
C {lab_pin.sym} 60 2620 0 0 {name=l66 lab=ivbl0}
N 120 2590 140 2590 {lab=vdd}
C {lab_pin.sym} 140 2590 0 0 {name=l67 lab=vdd}
N 120 2620 140 2620 {lab=vdd}
C {lab_pin.sym} 140 2620 0 0 {name=l68 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2780 0 0 {name=Sci1 L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2750 140 2750 {lab=inp}
C {lab_pin.sym} 140 2750 0 0 {name=l69 lab=inp}
N 80 2780 60 2780 {lab=chp}
C {lab_pin.sym} 60 2780 0 0 {name=l70 lab=chp}
N 120 2810 140 2810 {lab=gp}
C {lab_pin.sym} 140 2810 0 0 {name=l71 lab=gp}
N 120 2780 140 2780 {lab=vss}
C {lab_pin.sym} 140 2780 0 0 {name=l72 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2940 0 0 {name=Sci2 L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2910 140 2910 {lab=inn}
C {lab_pin.sym} 140 2910 0 0 {name=l73 lab=inn}
N 80 2940 60 2940 {lab=chp}
C {lab_pin.sym} 60 2940 0 0 {name=l74 lab=chp}
N 120 2970 140 2970 {lab=gm}
C {lab_pin.sym} 140 2970 0 0 {name=l75 lab=gm}
N 120 2940 140 2940 {lab=vss}
C {lab_pin.sym} 140 2940 0 0 {name=l76 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 60 0 0 {name=Sci3 L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 30 540 30 {lab=inp}
C {lab_pin.sym} 540 30 0 0 {name=l77 lab=inp}
N 480 60 460 60 {lab=chn}
C {lab_pin.sym} 460 60 0 0 {name=l78 lab=chn}
N 520 90 540 90 {lab=gm}
C {lab_pin.sym} 540 90 0 0 {name=l79 lab=gm}
N 520 60 540 60 {lab=vss}
C {lab_pin.sym} 540 60 0 0 {name=l80 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 220 0 0 {name=Sci4 L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 190 540 190 {lab=inn}
C {lab_pin.sym} 540 190 0 0 {name=l81 lab=inn}
N 480 220 460 220 {lab=chn}
C {lab_pin.sym} 460 220 0 0 {name=l82 lab=chn}
N 520 250 540 250 {lab=gp}
C {lab_pin.sym} 540 250 0 0 {name=l83 lab=gp}
N 520 220 540 220 {lab=vss}
C {lab_pin.sym} 540 220 0 0 {name=l84 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 380 0 0 {name=Sisl1 L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 350 540 350 {lab=inp}
C {lab_pin.sym} 540 350 0 0 {name=l85 lab=inp}
N 480 380 460 380 {lab=isl}
C {lab_pin.sym} 460 380 0 0 {name=l86 lab=isl}
N 520 410 540 410 {lab=vicm}
C {lab_pin.sym} 540 410 0 0 {name=l87 lab=vicm}
N 520 380 540 380 {lab=vss}
C {lab_pin.sym} 540 380 0 0 {name=l88 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 540 0 0 {name=Sisl2 L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 510 540 510 {lab=inn}
C {lab_pin.sym} 540 510 0 0 {name=l89 lab=inn}
N 480 540 460 540 {lab=isl}
C {lab_pin.sym} 460 540 0 0 {name=l90 lab=isl}
N 520 570 540 570 {lab=vicm}
C {lab_pin.sym} 540 570 0 0 {name=l91 lab=vicm}
N 520 540 540 540 {lab=vss}
C {lab_pin.sym} 540 540 0 0 {name=l92 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 700 0 0 {name=mt L=6 W=3.75 nf=1 mult=32 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 730 540 730 {lab=tail}
C {lab_pin.sym} 540 730 0 0 {name=l93 lab=tail}
N 480 700 460 700 {lab=ibtp}
C {lab_pin.sym} 460 700 0 0 {name=l94 lab=ibtp}
N 520 670 540 670 {lab=vdd}
C {lab_pin.sym} 540 670 0 0 {name=l95 lab=vdd}
N 520 700 540 700 {lab=vdd}
C {lab_pin.sym} 540 700 0 0 {name=l96 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 500 860 0 0 {name=min1 L=0.5 W=10 nf=1 mult=12 model=pfet_01v8 spiceprefix=X}
N 520 890 540 890 {lab=da}
C {lab_pin.sym} 540 890 0 0 {name=l97 lab=da}
N 480 860 460 860 {lab=gp}
C {lab_pin.sym} 460 860 0 0 {name=l98 lab=gp}
N 520 830 540 830 {lab=tail}
C {lab_pin.sym} 540 830 0 0 {name=l99 lab=tail}
N 520 860 540 860 {lab=tail}
C {lab_pin.sym} 540 860 0 0 {name=l100 lab=tail}
C {sky130_fd_pr/pfet_01v8.sym} 500 1020 0 0 {name=min2 L=0.5 W=10 nf=1 mult=12 model=pfet_01v8 spiceprefix=X}
N 520 1050 540 1050 {lab=db}
C {lab_pin.sym} 540 1050 0 0 {name=l101 lab=db}
N 480 1020 460 1020 {lab=gm}
C {lab_pin.sym} 460 1020 0 0 {name=l102 lab=gm}
N 520 990 540 990 {lab=tail}
C {lab_pin.sym} 540 990 0 0 {name=l103 lab=tail}
N 520 1020 540 1020 {lab=tail}
C {lab_pin.sym} 540 1020 0 0 {name=l104 lab=tail}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1180 0 0 {name=mpp1 L=0.5 W=5 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1210 540 1210 {lab=fa}
C {lab_pin.sym} 540 1210 0 0 {name=l105 lab=fa}
N 480 1180 460 1180 {lab=vss}
C {lab_pin.sym} 460 1180 0 0 {name=l106 lab=vss}
N 520 1150 540 1150 {lab=da}
C {lab_pin.sym} 540 1150 0 0 {name=l107 lab=da}
N 520 1180 540 1180 {lab=da}
C {lab_pin.sym} 540 1180 0 0 {name=l108 lab=da}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1340 0 0 {name=mpp2 L=0.5 W=5 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1370 540 1370 {lab=fb}
C {lab_pin.sym} 540 1370 0 0 {name=l109 lab=fb}
N 480 1340 460 1340 {lab=vss}
C {lab_pin.sym} 460 1340 0 0 {name=l110 lab=vss}
N 520 1310 540 1310 {lab=db}
C {lab_pin.sym} 540 1310 0 0 {name=l111 lab=db}
N 520 1340 540 1340 {lab=db}
C {lab_pin.sym} 540 1340 0 0 {name=l112 lab=db}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1500 0 0 {name=mn1 L=8 W=2.25 nf=1 mult=32 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1470 540 1470 {lab=fa}
C {lab_pin.sym} 540 1470 0 0 {name=l113 lab=fa}
N 480 1500 460 1500 {lab=ibn}
C {lab_pin.sym} 460 1500 0 0 {name=l114 lab=ibn}
N 520 1530 540 1530 {lab=vss}
C {lab_pin.sym} 540 1530 0 0 {name=l115 lab=vss}
N 520 1500 540 1500 {lab=vss}
C {lab_pin.sym} 540 1500 0 0 {name=l116 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1660 0 0 {name=mn2 L=8 W=2.25 nf=1 mult=32 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1630 540 1630 {lab=fb}
C {lab_pin.sym} 540 1630 0 0 {name=l117 lab=fb}
N 480 1660 460 1660 {lab=ibn}
C {lab_pin.sym} 460 1660 0 0 {name=l118 lab=ibn}
N 520 1690 540 1690 {lab=vss}
C {lab_pin.sym} 540 1690 0 0 {name=l119 lab=vss}
N 520 1660 540 1660 {lab=vss}
C {lab_pin.sym} 540 1660 0 0 {name=l120 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 1820 0 0 {name=Scf1 L=0.15 W=4 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 1790 540 1790 {lab=fa}
C {lab_pin.sym} 540 1790 0 0 {name=l121 lab=fa}
N 480 1820 460 1820 {lab=chlp}
C {lab_pin.sym} 460 1820 0 0 {name=l122 lab=chlp}
N 520 1850 540 1850 {lab=xa}
C {lab_pin.sym} 540 1850 0 0 {name=l123 lab=xa}
N 520 1820 540 1820 {lab=vss}
C {lab_pin.sym} 540 1820 0 0 {name=l124 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 1980 0 0 {name=Scf2 L=0.15 W=4 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 1950 540 1950 {lab=fb}
C {lab_pin.sym} 540 1950 0 0 {name=l125 lab=fb}
N 480 1980 460 1980 {lab=chlp}
C {lab_pin.sym} 460 1980 0 0 {name=l126 lab=chlp}
N 520 2010 540 2010 {lab=xb}
C {lab_pin.sym} 540 2010 0 0 {name=l127 lab=xb}
N 520 1980 540 1980 {lab=vss}
C {lab_pin.sym} 540 1980 0 0 {name=l128 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 2140 0 0 {name=Scf3 L=0.15 W=4 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2110 540 2110 {lab=fa}
C {lab_pin.sym} 540 2110 0 0 {name=l129 lab=fa}
N 480 2140 460 2140 {lab=chln}
C {lab_pin.sym} 460 2140 0 0 {name=l130 lab=chln}
N 520 2170 540 2170 {lab=xb}
C {lab_pin.sym} 540 2170 0 0 {name=l131 lab=xb}
N 520 2140 540 2140 {lab=vss}
C {lab_pin.sym} 540 2140 0 0 {name=l132 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 500 2300 0 0 {name=Scf4 L=0.15 W=4 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
N 520 2270 540 2270 {lab=fb}
C {lab_pin.sym} 540 2270 0 0 {name=l133 lab=fb}
N 480 2300 460 2300 {lab=chln}
C {lab_pin.sym} 460 2300 0 0 {name=l134 lab=chln}
N 520 2330 540 2330 {lab=xa}
C {lab_pin.sym} 540 2330 0 0 {name=l135 lab=xa}
N 520 2300 540 2300 {lab=vss}
C {lab_pin.sym} 540 2300 0 0 {name=l136 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2460 0 0 {name=mnc1 L=2 W=5 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2430 540 2430 {lab=outn}
C {lab_pin.sym} 540 2430 0 0 {name=l137 lab=outn}
N 480 2460 460 2460 {lab=ivbnc}
C {lab_pin.sym} 460 2460 0 0 {name=l138 lab=ivbnc}
N 520 2490 540 2490 {lab=xa}
C {lab_pin.sym} 540 2490 0 0 {name=l139 lab=xa}
N 520 2460 540 2460 {lab=vss}
C {lab_pin.sym} 540 2460 0 0 {name=l140 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2620 0 0 {name=mnc2 L=2 W=5 nf=1 mult=4 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2590 540 2590 {lab=outp}
C {lab_pin.sym} 540 2590 0 0 {name=l141 lab=outp}
N 480 2620 460 2620 {lab=ivbnc}
C {lab_pin.sym} 460 2620 0 0 {name=l142 lab=ivbnc}
N 520 2650 540 2650 {lab=xb}
C {lab_pin.sym} 540 2650 0 0 {name=l143 lab=xb}
N 520 2620 540 2620 {lab=vss}
C {lab_pin.sym} 540 2620 0 0 {name=l144 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2780 0 0 {name=mpc1 L=2 W=5 nf=1 mult=16 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2810 540 2810 {lab=outn}
C {lab_pin.sym} 540 2810 0 0 {name=l145 lab=outn}
N 480 2780 460 2780 {lab=ivbpc}
C {lab_pin.sym} 460 2780 0 0 {name=l146 lab=ivbpc}
N 520 2750 540 2750 {lab=sa}
C {lab_pin.sym} 540 2750 0 0 {name=l147 lab=sa}
N 520 2780 540 2780 {lab=sa}
C {lab_pin.sym} 540 2780 0 0 {name=l148 lab=sa}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2940 0 0 {name=mpc2 L=2 W=5 nf=1 mult=16 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2970 540 2970 {lab=outp}
C {lab_pin.sym} 540 2970 0 0 {name=l149 lab=outp}
N 480 2940 460 2940 {lab=ivbpc}
C {lab_pin.sym} 460 2940 0 0 {name=l150 lab=ivbpc}
N 520 2910 540 2910 {lab=sb}
C {lab_pin.sym} 540 2910 0 0 {name=l151 lab=sb}
N 520 2940 540 2940 {lab=sb}
C {lab_pin.sym} 540 2940 0 0 {name=l152 lab=sb}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 60 0 0 {name=mpl1 L=4 W=2.5 nf=1 mult=32 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 90 940 90 {lab=sa}
C {lab_pin.sym} 940 90 0 0 {name=l153 lab=sa}
N 880 60 860 60 {lab=ibp}
C {lab_pin.sym} 860 60 0 0 {name=l154 lab=ibp}
N 920 30 940 30 {lab=vdd}
C {lab_pin.sym} 940 30 0 0 {name=l155 lab=vdd}
N 920 60 940 60 {lab=vdd}
C {lab_pin.sym} 940 60 0 0 {name=l156 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 220 0 0 {name=mpl2 L=4 W=2.5 nf=1 mult=32 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 250 940 250 {lab=sb}
C {lab_pin.sym} 940 250 0 0 {name=l157 lab=sb}
N 880 220 860 220 {lab=ibp}
C {lab_pin.sym} 860 220 0 0 {name=l158 lab=ibp}
N 920 190 940 190 {lab=vdd}
C {lab_pin.sym} 940 190 0 0 {name=l159 lab=vdd}
N 920 220 940 220 {lab=vdd}
C {lab_pin.sym} 940 220 0 0 {name=l160 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 380 0 0 {name=mplc1 L=2 W=1.875 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 410 940 410 {lab=sa}
C {lab_pin.sym} 940 410 0 0 {name=l161 lab=sa}
N 880 380 860 380 {lab=ctl}
C {lab_pin.sym} 860 380 0 0 {name=l162 lab=ctl}
N 920 350 940 350 {lab=vdd}
C {lab_pin.sym} 940 350 0 0 {name=l163 lab=vdd}
N 920 380 940 380 {lab=vdd}
C {lab_pin.sym} 940 380 0 0 {name=l164 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 540 0 0 {name=mplc2 L=2 W=1.875 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 570 940 570 {lab=sb}
C {lab_pin.sym} 940 570 0 0 {name=l165 lab=sb}
N 880 540 860 540 {lab=ctl}
C {lab_pin.sym} 860 540 0 0 {name=l166 lab=ctl}
N 920 510 940 510 {lab=vdd}
C {lab_pin.sym} 940 510 0 0 {name=l167 lab=vdd}
N 920 540 940 540 {lab=vdd}
C {lab_pin.sym} 940 540 0 0 {name=l168 lab=vdd}
C {capa.sym} 900 700 0 0 {name=Ccp value=1e-13 m=1}
N 900 670 900 650 {lab=outp}
C {lab_pin.sym} 900 650 0 0 {name=l169 lab=outp}
N 900 730 900 750 {lab=ctl}
C {lab_pin.sym} 900 750 0 0 {name=l170 lab=ctl}
C {capa.sym} 900 860 0 0 {name=Ccn value=1e-13 m=1}
N 900 830 900 810 {lab=outn}
C {lab_pin.sym} 900 810 0 0 {name=l171 lab=outn}
N 900 890 900 910 {lab=ctl}
C {lab_pin.sym} 900 910 0 0 {name=l172 lab=ctl}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1020 0 0 {name=mrst L=0.5 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1050 940 1050 {lab=ctl}
C {lab_pin.sym} 940 1050 0 0 {name=l173 lab=ctl}
N 880 1020 860 1020 {lab=rstb}
C {lab_pin.sym} 860 1020 0 0 {name=l174 lab=rstb}
N 920 990 940 990 {lab=ivbl0}
C {lab_pin.sym} 940 990 0 0 {name=l175 lab=ivbl0}
N 920 1020 940 1020 {lab=vdd}
C {lab_pin.sym} 940 1020 0 0 {name=l176 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1180 0 0 {name=mrsb L=0.5 W=1 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1210 940 1210 {lab=bli}
C {lab_pin.sym} 940 1210 0 0 {name=l177 lab=bli}
N 880 1180 860 1180 {lab=rstb}
C {lab_pin.sym} 860 1180 0 0 {name=l178 lab=rstb}
N 920 1150 940 1150 {lab=ivbl0}
C {lab_pin.sym} 940 1150 0 0 {name=l179 lab=ivbl0}
N 920 1180 940 1180 {lab=vdd}
C {lab_pin.sym} 940 1180 0 0 {name=l180 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1340 0 0 {name=mrin L=0.5 W=0.42 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1310 940 1310 {lab=rst}
C {lab_pin.sym} 940 1310 0 0 {name=l181 lab=rst}
N 880 1340 860 1340 {lab=rstb}
C {lab_pin.sym} 860 1340 0 0 {name=l182 lab=rstb}
N 920 1370 940 1370 {lab=vss}
C {lab_pin.sym} 940 1370 0 0 {name=l183 lab=vss}
N 920 1340 940 1340 {lab=vss}
C {lab_pin.sym} 940 1340 0 0 {name=l184 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1500 0 0 {name=mrip L=0.5 W=0.84 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1530 940 1530 {lab=rst}
C {lab_pin.sym} 940 1530 0 0 {name=l185 lab=rst}
N 880 1500 860 1500 {lab=rstb}
C {lab_pin.sym} 860 1500 0 0 {name=l186 lab=rstb}
N 920 1470 940 1470 {lab=vdd}
C {lab_pin.sym} 940 1470 0 0 {name=l187 lab=vdd}
N 920 1500 940 1500 {lab=vdd}
C {lab_pin.sym} 940 1500 0 0 {name=l188 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1660 0 0 {name=mrsopn L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1630 940 1630 {lab=outp}
C {lab_pin.sym} 940 1630 0 0 {name=l189 lab=outp}
N 880 1660 860 1660 {lab=rst}
C {lab_pin.sym} 860 1660 0 0 {name=l190 lab=rst}
N 920 1690 940 1690 {lab=vocm}
C {lab_pin.sym} 940 1690 0 0 {name=l191 lab=vocm}
N 920 1660 940 1660 {lab=vss}
C {lab_pin.sym} 940 1660 0 0 {name=l192 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1820 0 0 {name=mrsonn L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1790 940 1790 {lab=outn}
C {lab_pin.sym} 940 1790 0 0 {name=l193 lab=outn}
N 880 1820 860 1820 {lab=rst}
C {lab_pin.sym} 860 1820 0 0 {name=l194 lab=rst}
N 920 1850 940 1850 {lab=vocm}
C {lab_pin.sym} 940 1850 0 0 {name=l195 lab=vocm}
N 920 1820 940 1820 {lab=vss}
C {lab_pin.sym} 940 1820 0 0 {name=l196 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1980 0 0 {name=mrsopp L=0.5 W=4 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 2010 940 2010 {lab=outp}
C {lab_pin.sym} 940 2010 0 0 {name=l197 lab=outp}
N 880 1980 860 1980 {lab=rstb}
C {lab_pin.sym} 860 1980 0 0 {name=l198 lab=rstb}
N 920 1950 940 1950 {lab=vocm}
C {lab_pin.sym} 940 1950 0 0 {name=l199 lab=vocm}
N 920 1980 940 1980 {lab=vdd}
C {lab_pin.sym} 940 1980 0 0 {name=l200 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 2140 0 0 {name=mrsonp L=0.5 W=4 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 2170 940 2170 {lab=outn}
C {lab_pin.sym} 940 2170 0 0 {name=l201 lab=outn}
N 880 2140 860 2140 {lab=rstb}
C {lab_pin.sym} 860 2140 0 0 {name=l202 lab=rstb}
N 920 2110 940 2110 {lab=vocm}
C {lab_pin.sym} 940 2110 0 0 {name=l203 lab=vocm}
N 920 2140 940 2140 {lab=vdd}
C {lab_pin.sym} 940 2140 0 0 {name=l204 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 2300 0 0 {name=mit L=8 W=2.25 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 2270 940 2270 {lab=cit}
C {lab_pin.sym} 940 2270 0 0 {name=l205 lab=cit}
N 880 2300 860 2300 {lab=ibn}
C {lab_pin.sym} 860 2300 0 0 {name=l206 lab=ibn}
N 920 2330 940 2330 {lab=vss}
C {lab_pin.sym} 940 2330 0 0 {name=l207 lab=vss}
N 920 2300 940 2300 {lab=vss}
C {lab_pin.sym} 940 2300 0 0 {name=l208 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 2460 0 0 {name=mia1 L=14 W=2.5 nf=1 mult=2 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 2430 940 2430 {lab=cid}
C {lab_pin.sym} 940 2430 0 0 {name=l209 lab=cid}
N 880 2460 860 2460 {lab=ctl}
C {lab_pin.sym} 860 2460 0 0 {name=l210 lab=ctl}
N 920 2490 940 2490 {lab=cit}
C {lab_pin.sym} 940 2490 0 0 {name=l211 lab=cit}
N 920 2460 940 2460 {lab=vss}
C {lab_pin.sym} 940 2460 0 0 {name=l212 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 2620 0 0 {name=mia2 L=14 W=2.5 nf=1 mult=2 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 2590 940 2590 {lab=bli}
C {lab_pin.sym} 940 2590 0 0 {name=l213 lab=bli}
N 880 2620 860 2620 {lab=bli}
C {lab_pin.sym} 860 2620 0 0 {name=l214 lab=bli}
N 920 2650 940 2650 {lab=cit}
C {lab_pin.sym} 940 2650 0 0 {name=l215 lab=cit}
N 920 2620 940 2620 {lab=vss}
C {lab_pin.sym} 940 2620 0 0 {name=l216 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 2780 0 0 {name=mil1 L=16 W=3 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 2810 940 2810 {lab=cid}
C {lab_pin.sym} 940 2810 0 0 {name=l217 lab=cid}
N 880 2780 860 2780 {lab=cid}
C {lab_pin.sym} 860 2780 0 0 {name=l218 lab=cid}
N 920 2750 940 2750 {lab=vdd}
C {lab_pin.sym} 940 2750 0 0 {name=l219 lab=vdd}
N 920 2780 940 2780 {lab=vdd}
C {lab_pin.sym} 940 2780 0 0 {name=l220 lab=vdd}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 2940 0 0 {name=mil2 L=16 W=3 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 2970 940 2970 {lab=bli}
C {lab_pin.sym} 940 2970 0 0 {name=l221 lab=bli}
N 880 2940 860 2940 {lab=cid}
C {lab_pin.sym} 860 2940 0 0 {name=l222 lab=cid}
N 920 2910 940 2910 {lab=vdd}
C {lab_pin.sym} 940 2910 0 0 {name=l223 lab=vdd}
N 920 2940 940 2940 {lab=vdd}
C {lab_pin.sym} 940 2940 0 0 {name=l224 lab=vdd}
C {capa.sym} 1300 60 0 0 {name=Cint value=2e-12 m=1}
N 1300 30 1300 10 {lab=bli}
C {lab_pin.sym} 1300 10 0 0 {name=l225 lab=bli}
N 1300 90 1300 110 {lab=vdd}
C {lab_pin.sym} 1300 110 0 0 {name=l226 lab=vdd}
C {capa.sym} 1300 220 0 0 {name=Crp value=5e-14 m=1}
N 1300 190 1300 170 {lab=rap}
C {lab_pin.sym} 1300 170 0 0 {name=l227 lab=rap}
N 1300 250 1300 270 {lab=rbp}
C {lab_pin.sym} 1300 270 0 0 {name=l228 lab=rbp}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 380 0 0 {name=Sr1apn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 350 1340 350 {lab=rap}
C {lab_pin.sym} 1340 350 0 0 {name=l229 lab=rap}
N 1280 380 1260 380 {lab=ph1}
C {lab_pin.sym} 1260 380 0 0 {name=l230 lab=ph1}
N 1320 410 1340 410 {lab=vocm}
C {lab_pin.sym} 1340 410 0 0 {name=l231 lab=vocm}
N 1320 380 1340 380 {lab=vss}
C {lab_pin.sym} 1340 380 0 0 {name=l232 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 540 0 0 {name=Sr1app L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 570 1340 570 {lab=rap}
C {lab_pin.sym} 1340 570 0 0 {name=l233 lab=rap}
N 1280 540 1260 540 {lab=ph1b}
C {lab_pin.sym} 1260 540 0 0 {name=l234 lab=ph1b}
N 1320 510 1340 510 {lab=vocm}
C {lab_pin.sym} 1340 510 0 0 {name=l235 lab=vocm}
N 1320 540 1340 540 {lab=vdd}
C {lab_pin.sym} 1340 540 0 0 {name=l236 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 700 0 0 {name=Sr1bpn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 670 1340 670 {lab=rbp}
C {lab_pin.sym} 1340 670 0 0 {name=l237 lab=rbp}
N 1280 700 1260 700 {lab=ph1}
C {lab_pin.sym} 1260 700 0 0 {name=l238 lab=ph1}
N 1320 730 1340 730 {lab=bli}
C {lab_pin.sym} 1340 730 0 0 {name=l239 lab=bli}
N 1320 700 1340 700 {lab=vss}
C {lab_pin.sym} 1340 700 0 0 {name=l240 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 860 0 0 {name=Sr1bpp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 890 1340 890 {lab=rbp}
C {lab_pin.sym} 1340 890 0 0 {name=l241 lab=rbp}
N 1280 860 1260 860 {lab=ph1b}
C {lab_pin.sym} 1260 860 0 0 {name=l242 lab=ph1b}
N 1320 830 1340 830 {lab=bli}
C {lab_pin.sym} 1340 830 0 0 {name=l243 lab=bli}
N 1320 860 1340 860 {lab=vdd}
C {lab_pin.sym} 1340 860 0 0 {name=l244 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1020 0 0 {name=Sr2apn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 990 1340 990 {lab=rap}
C {lab_pin.sym} 1340 990 0 0 {name=l245 lab=rap}
N 1280 1020 1260 1020 {lab=ph2}
C {lab_pin.sym} 1260 1020 0 0 {name=l246 lab=ph2}
N 1320 1050 1340 1050 {lab=outp}
C {lab_pin.sym} 1340 1050 0 0 {name=l247 lab=outp}
N 1320 1020 1340 1020 {lab=vss}
C {lab_pin.sym} 1340 1020 0 0 {name=l248 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 1180 0 0 {name=Sr2app L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 1210 1340 1210 {lab=rap}
C {lab_pin.sym} 1340 1210 0 0 {name=l249 lab=rap}
N 1280 1180 1260 1180 {lab=ph2b}
C {lab_pin.sym} 1260 1180 0 0 {name=l250 lab=ph2b}
N 1320 1150 1340 1150 {lab=outp}
C {lab_pin.sym} 1340 1150 0 0 {name=l251 lab=outp}
N 1320 1180 1340 1180 {lab=vdd}
C {lab_pin.sym} 1340 1180 0 0 {name=l252 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1340 0 0 {name=Sr2bpn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1310 1340 1310 {lab=rbp}
C {lab_pin.sym} 1340 1310 0 0 {name=l253 lab=rbp}
N 1280 1340 1260 1340 {lab=ph2}
C {lab_pin.sym} 1260 1340 0 0 {name=l254 lab=ph2}
N 1320 1370 1340 1370 {lab=ctl}
C {lab_pin.sym} 1340 1370 0 0 {name=l255 lab=ctl}
N 1320 1340 1340 1340 {lab=vss}
C {lab_pin.sym} 1340 1340 0 0 {name=l256 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 1500 0 0 {name=Sr2bpp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 1530 1340 1530 {lab=rbp}
C {lab_pin.sym} 1340 1530 0 0 {name=l257 lab=rbp}
N 1280 1500 1260 1500 {lab=ph2b}
C {lab_pin.sym} 1260 1500 0 0 {name=l258 lab=ph2b}
N 1320 1470 1340 1470 {lab=ctl}
C {lab_pin.sym} 1340 1470 0 0 {name=l259 lab=ctl}
N 1320 1500 1340 1500 {lab=vdd}
C {lab_pin.sym} 1340 1500 0 0 {name=l260 lab=vdd}
C {capa.sym} 1300 1660 0 0 {name=Crn value=5e-14 m=1}
N 1300 1630 1300 1610 {lab=ran}
C {lab_pin.sym} 1300 1610 0 0 {name=l261 lab=ran}
N 1300 1690 1300 1710 {lab=rbn}
C {lab_pin.sym} 1300 1710 0 0 {name=l262 lab=rbn}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 1820 0 0 {name=Sr1ann L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 1790 1340 1790 {lab=ran}
C {lab_pin.sym} 1340 1790 0 0 {name=l263 lab=ran}
N 1280 1820 1260 1820 {lab=ph1}
C {lab_pin.sym} 1260 1820 0 0 {name=l264 lab=ph1}
N 1320 1850 1340 1850 {lab=vocm}
C {lab_pin.sym} 1340 1850 0 0 {name=l265 lab=vocm}
N 1320 1820 1340 1820 {lab=vss}
C {lab_pin.sym} 1340 1820 0 0 {name=l266 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 1980 0 0 {name=Sr1anp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 2010 1340 2010 {lab=ran}
C {lab_pin.sym} 1340 2010 0 0 {name=l267 lab=ran}
N 1280 1980 1260 1980 {lab=ph1b}
C {lab_pin.sym} 1260 1980 0 0 {name=l268 lab=ph1b}
N 1320 1950 1340 1950 {lab=vocm}
C {lab_pin.sym} 1340 1950 0 0 {name=l269 lab=vocm}
N 1320 1980 1340 1980 {lab=vdd}
C {lab_pin.sym} 1340 1980 0 0 {name=l270 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2140 0 0 {name=Sr1bnn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2110 1340 2110 {lab=rbn}
C {lab_pin.sym} 1340 2110 0 0 {name=l271 lab=rbn}
N 1280 2140 1260 2140 {lab=ph1}
C {lab_pin.sym} 1260 2140 0 0 {name=l272 lab=ph1}
N 1320 2170 1340 2170 {lab=bli}
C {lab_pin.sym} 1340 2170 0 0 {name=l273 lab=bli}
N 1320 2140 1340 2140 {lab=vss}
C {lab_pin.sym} 1340 2140 0 0 {name=l274 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 2300 0 0 {name=Sr1bnp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 2330 1340 2330 {lab=rbn}
C {lab_pin.sym} 1340 2330 0 0 {name=l275 lab=rbn}
N 1280 2300 1260 2300 {lab=ph1b}
C {lab_pin.sym} 1260 2300 0 0 {name=l276 lab=ph1b}
N 1320 2270 1340 2270 {lab=bli}
C {lab_pin.sym} 1340 2270 0 0 {name=l277 lab=bli}
N 1320 2300 1340 2300 {lab=vdd}
C {lab_pin.sym} 1340 2300 0 0 {name=l278 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2460 0 0 {name=Sr2ann L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2430 1340 2430 {lab=ran}
C {lab_pin.sym} 1340 2430 0 0 {name=l279 lab=ran}
N 1280 2460 1260 2460 {lab=ph2}
C {lab_pin.sym} 1260 2460 0 0 {name=l280 lab=ph2}
N 1320 2490 1340 2490 {lab=outn}
C {lab_pin.sym} 1340 2490 0 0 {name=l281 lab=outn}
N 1320 2460 1340 2460 {lab=vss}
C {lab_pin.sym} 1340 2460 0 0 {name=l282 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 2620 0 0 {name=Sr2anp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 2650 1340 2650 {lab=ran}
C {lab_pin.sym} 1340 2650 0 0 {name=l283 lab=ran}
N 1280 2620 1260 2620 {lab=ph2b}
C {lab_pin.sym} 1260 2620 0 0 {name=l284 lab=ph2b}
N 1320 2590 1340 2590 {lab=outn}
C {lab_pin.sym} 1340 2590 0 0 {name=l285 lab=outn}
N 1320 2620 1340 2620 {lab=vdd}
C {lab_pin.sym} 1340 2620 0 0 {name=l286 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1300 2780 0 0 {name=Sr2bnn L=0.5 W=1 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 1320 2750 1340 2750 {lab=rbn}
C {lab_pin.sym} 1340 2750 0 0 {name=l287 lab=rbn}
N 1280 2780 1260 2780 {lab=ph2}
C {lab_pin.sym} 1260 2780 0 0 {name=l288 lab=ph2}
N 1320 2810 1340 2810 {lab=ctl}
C {lab_pin.sym} 1340 2810 0 0 {name=l289 lab=ctl}
N 1320 2780 1340 2780 {lab=vss}
C {lab_pin.sym} 1340 2780 0 0 {name=l290 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1300 2940 0 0 {name=Sr2bnp L=0.5 W=2 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 1320 2970 1340 2970 {lab=rbn}
C {lab_pin.sym} 1340 2970 0 0 {name=l291 lab=rbn}
N 1280 2940 1260 2940 {lab=ph2b}
C {lab_pin.sym} 1260 2940 0 0 {name=l292 lab=ph2b}
N 1320 2910 1340 2910 {lab=ctl}
C {lab_pin.sym} 1340 2910 0 0 {name=l293 lab=ctl}
N 1320 2940 1340 2940 {lab=vdd}
C {lab_pin.sym} 1340 2940 0 0 {name=l294 lab=vdd}
