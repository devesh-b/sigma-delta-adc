v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -440 0 -400 0 {lab=ua0}
C {iopin.sym} -440 0 0 0 {name=p0 lab=ua0}
C {lab_pin.sym} -400 0 0 0 {name=lp0 lab=ua0}
N -440 40 -400 40 {lab=ua1}
C {iopin.sym} -440 40 0 0 {name=p1 lab=ua1}
C {lab_pin.sym} -400 40 0 0 {name=lp1 lab=ua1}
N -440 80 -400 80 {lab=ua2}
C {iopin.sym} -440 80 0 0 {name=p2 lab=ua2}
C {lab_pin.sym} -400 80 0 0 {name=lp2 lab=ua2}
N -440 120 -400 120 {lab=ua3}
C {iopin.sym} -440 120 0 0 {name=p3 lab=ua3}
C {lab_pin.sym} -400 120 0 0 {name=lp3 lab=ua3}
N -440 160 -400 160 {lab=VAPWR}
C {iopin.sym} -440 160 0 0 {name=p4 lab=VAPWR}
C {lab_pin.sym} -400 160 0 0 {name=lp4 lab=VAPWR}
N -440 200 -400 200 {lab=VDPWR}
C {iopin.sym} -440 200 0 0 {name=p5 lab=VDPWR}
C {lab_pin.sym} -400 200 0 0 {name=lp5 lab=VDPWR}
N -440 240 -400 240 {lab=VGND}
C {iopin.sym} -440 240 0 0 {name=p6 lab=VGND}
C {lab_pin.sym} -400 240 0 0 {name=lp6 lab=VGND}
N -440 280 -400 280 {lab=fs}
C {iopin.sym} -440 280 0 0 {name=p7 lab=fs}
C {lab_pin.sym} -400 280 0 0 {name=lp7 lab=fs}
N -440 320 -400 320 {lab=y}
C {iopin.sym} -440 320 0 0 {name=p8 lab=y}
C {lab_pin.sym} -400 320 0 0 {name=lp8 lab=y}
N -440 360 -400 360 {lab=swap}
C {iopin.sym} -440 360 0 0 {name=p9 lab=swap}
C {lab_pin.sym} -400 360 0 0 {name=lp9 lab=swap}
N -440 400 -400 400 {lab=short}
C {iopin.sym} -440 400 0 0 {name=p10 lab=short}
C {lab_pin.sym} -400 400 0 0 {name=lp10 lab=short}
N -440 440 -400 440 {lab=chop}
C {iopin.sym} -440 440 0 0 {name=p11 lab=chop}
C {lab_pin.sym} -400 440 0 0 {name=lp11 lab=chop}
N -440 480 -400 480 {lab=rst_analog}
C {iopin.sym} -440 480 0 0 {name=p12 lab=rst_analog}
C {lab_pin.sym} -400 480 0 0 {name=lp12 lab=rst_analog}
N -440 520 -400 520 {lab=order}
C {iopin.sym} -440 520 0 0 {name=p13 lab=order}
C {lab_pin.sym} -400 520 0 0 {name=lp13 lab=order}
N -440 560 -400 560 {lab=boost}
C {iopin.sym} -440 560 0 0 {name=p14 lab=boost}
C {lab_pin.sym} -400 560 0 0 {name=lp14 lab=boost}
N -440 600 -400 600 {lab=trim0}
C {iopin.sym} -440 600 0 0 {name=p15 lab=trim0}
C {lab_pin.sym} -400 600 0 0 {name=lp15 lab=trim0}
N -440 640 -400 640 {lab=trim1}
C {iopin.sym} -440 640 0 0 {name=p16 lab=trim1}
C {lab_pin.sym} -400 640 0 0 {name=lp16 lab=trim1}
N -440 680 -400 680 {lab=trim2}
C {iopin.sym} -440 680 0 0 {name=p17 lab=trim2}
C {lab_pin.sym} -400 680 0 0 {name=lp17 lab=trim2}
N -440 720 -400 720 {lab=comp_out}
C {iopin.sym} -440 720 0 0 {name=p18 lab=comp_out}
C {lab_pin.sym} -400 720 0 0 {name=lp18 lab=comp_out}
N -440 760 -400 760 {lab=bias_ok}
C {iopin.sym} -440 760 0 0 {name=p19 lab=bias_ok}
C {lab_pin.sym} -400 760 0 0 {name=lp19 lab=bias_ok}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 60 0 0 {name=sinpn L=0.5 W=12 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 30 140 30 {lab=ua0}
C {lab_pin.sym} 140 30 0 0 {name=l1 lab=ua0}
N 80 60 60 60 {lab=pas_t}
C {lab_pin.sym} 60 60 0 0 {name=l2 lab=pas_t}
N 120 90 140 90 {lab=b1p}
C {lab_pin.sym} 140 90 0 0 {name=l3 lab=b1p}
N 120 60 140 60 {lab=VGND}
C {lab_pin.sym} 140 60 0 0 {name=l4 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 220 0 0 {name=sinpp L=0.5 W=36 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 250 140 250 {lab=ua0}
C {lab_pin.sym} 140 250 0 0 {name=l5 lab=ua0}
N 80 220 60 220 {lab=pas_c}
C {lab_pin.sym} 60 220 0 0 {name=l6 lab=pas_c}
N 120 190 140 190 {lab=b1p}
C {lab_pin.sym} 140 190 0 0 {name=l7 lab=b1p}
N 120 220 140 220 {lab=VAPWR}
C {lab_pin.sym} 140 220 0 0 {name=l8 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 380 0 0 {name=sswpn L=0.5 W=12 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 350 140 350 {lab=ua1}
C {lab_pin.sym} 140 350 0 0 {name=l9 lab=ua1}
N 80 380 60 380 {lab=swp_t}
C {lab_pin.sym} 60 380 0 0 {name=l10 lab=swp_t}
N 120 410 140 410 {lab=b1p}
C {lab_pin.sym} 140 410 0 0 {name=l11 lab=b1p}
N 120 380 140 380 {lab=VGND}
C {lab_pin.sym} 140 380 0 0 {name=l12 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 540 0 0 {name=sswpp L=0.5 W=36 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 570 140 570 {lab=ua1}
C {lab_pin.sym} 140 570 0 0 {name=l13 lab=ua1}
N 80 540 60 540 {lab=swp_c}
C {lab_pin.sym} 60 540 0 0 {name=l14 lab=swp_c}
N 120 510 140 510 {lab=b1p}
C {lab_pin.sym} 140 510 0 0 {name=l15 lab=b1p}
N 120 540 140 540 {lab=VAPWR}
C {lab_pin.sym} 140 540 0 0 {name=l16 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 700 0 0 {name=sshpn L=0.5 W=12 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 670 140 670 {lab=vscm}
C {lab_pin.sym} 140 670 0 0 {name=l17 lab=vscm}
N 80 700 60 700 {lab=sho_t}
C {lab_pin.sym} 60 700 0 0 {name=l18 lab=sho_t}
N 120 730 140 730 {lab=b1p}
C {lab_pin.sym} 140 730 0 0 {name=l19 lab=b1p}
N 120 700 140 700 {lab=VGND}
C {lab_pin.sym} 140 700 0 0 {name=l20 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 860 0 0 {name=sshpp L=0.5 W=36 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 890 140 890 {lab=vscm}
C {lab_pin.sym} 140 890 0 0 {name=l21 lab=vscm}
N 80 860 60 860 {lab=sho_c}
C {lab_pin.sym} 60 860 0 0 {name=l22 lab=sho_c}
N 120 830 140 830 {lab=b1p}
C {lab_pin.sym} 140 830 0 0 {name=l23 lab=b1p}
N 120 860 140 860 {lab=VAPWR}
C {lab_pin.sym} 140 860 0 0 {name=l24 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1020 0 0 {name=sdhpn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 990 140 990 {lab=ua2}
C {lab_pin.sym} 140 990 0 0 {name=l25 lab=ua2}
N 80 1020 60 1020 {lab=dh_t}
C {lab_pin.sym} 60 1020 0 0 {name=l26 lab=dh_t}
N 120 1050 140 1050 {lab=b1p}
C {lab_pin.sym} 140 1050 0 0 {name=l27 lab=b1p}
N 120 1020 140 1020 {lab=VGND}
C {lab_pin.sym} 140 1020 0 0 {name=l28 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 1180 0 0 {name=sdhpp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 1210 140 1210 {lab=ua2}
C {lab_pin.sym} 140 1210 0 0 {name=l29 lab=ua2}
N 80 1180 60 1180 {lab=dh_c}
C {lab_pin.sym} 60 1180 0 0 {name=l30 lab=dh_c}
N 120 1150 140 1150 {lab=b1p}
C {lab_pin.sym} 140 1150 0 0 {name=l31 lab=b1p}
N 120 1180 140 1180 {lab=VAPWR}
C {lab_pin.sym} 140 1180 0 0 {name=l32 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1340 0 0 {name=sdlpn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1310 140 1310 {lab=ua3}
C {lab_pin.sym} 140 1310 0 0 {name=l33 lab=ua3}
N 80 1340 60 1340 {lab=dl_t}
C {lab_pin.sym} 60 1340 0 0 {name=l34 lab=dl_t}
N 120 1370 140 1370 {lab=b1p}
C {lab_pin.sym} 140 1370 0 0 {name=l35 lab=b1p}
N 120 1340 140 1340 {lab=VGND}
C {lab_pin.sym} 140 1340 0 0 {name=l36 lab=VGND}
C {mim_cs.sym} 100 1500 0 0 {name=Xcs1p}
N 20 1520 0 1520 {lab=tp1p}
C {lab_pin.sym} 0 1520 0 0 {name=l37 lab=tp1p}
N 180 1520 200 1520 {lab=b1p}
C {lab_pin.sym} 200 1520 0 0 {name=l38 lab=b1p}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1640 0 0 {name=sg1pn L=0.5 W=5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1610 140 1610 {lab=tp1p}
C {lab_pin.sym} 140 1610 0 0 {name=l39 lab=tp1p}
N 80 1640 60 1640 {lab=ie_t}
C {lab_pin.sym} 60 1640 0 0 {name=l40 lab=ie_t}
N 120 1670 140 1670 {lab=vg1p}
C {lab_pin.sym} 140 1670 0 0 {name=l41 lab=vg1p}
N 120 1640 140 1640 {lab=VGND}
C {lab_pin.sym} 140 1640 0 0 {name=l42 lab=VGND}
C {mim_cint1.sym} 100 1800 0 0 {name=Xci1p}
N 20 1820 0 1820 {lab=vg1p}
C {lab_pin.sym} 0 1820 0 0 {name=l43 lab=vg1p}
N 180 1820 200 1820 {lab=x1n}
C {lab_pin.sym} 200 1820 0 0 {name=l44 lab=x1n}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 1940 0 0 {name=s2inpn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 1910 140 1910 {lab=x1p}
C {lab_pin.sym} 140 1910 0 0 {name=l45 lab=x1p}
N 80 1940 60 1940 {lab=sl_t}
C {lab_pin.sym} 60 1940 0 0 {name=l46 lab=sl_t}
N 120 1970 140 1970 {lab=b2p}
C {lab_pin.sym} 140 1970 0 0 {name=l47 lab=b2p}
N 120 1940 140 1940 {lab=VGND}
C {lab_pin.sym} 140 1940 0 0 {name=l48 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2100 0 0 {name=s2inpp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2130 140 2130 {lab=x1p}
C {lab_pin.sym} 140 2130 0 0 {name=l49 lab=x1p}
N 80 2100 60 2100 {lab=sl_c}
C {lab_pin.sym} 60 2100 0 0 {name=l50 lab=sl_c}
N 120 2070 140 2070 {lab=b2p}
C {lab_pin.sym} 140 2070 0 0 {name=l51 lab=b2p}
N 120 2100 140 2100 {lab=VAPWR}
C {lab_pin.sym} 140 2100 0 0 {name=l52 lab=VAPWR}
C {mim_cs.sym} 100 2260 0 0 {name=Xcs2p}
N 20 2280 0 2280 {lab=tp2p}
C {lab_pin.sym} 0 2280 0 0 {name=l53 lab=tp2p}
N 180 2280 200 2280 {lab=b2p}
C {lab_pin.sym} 200 2280 0 0 {name=l54 lab=b2p}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2400 0 0 {name=sg2pn L=0.5 W=5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2370 140 2370 {lab=tp2p}
C {lab_pin.sym} 140 2370 0 0 {name=l55 lab=tp2p}
N 80 2400 60 2400 {lab=ie_t}
C {lab_pin.sym} 60 2400 0 0 {name=l56 lab=ie_t}
N 120 2430 140 2430 {lab=vg2p}
C {lab_pin.sym} 140 2430 0 0 {name=l57 lab=vg2p}
N 120 2400 140 2400 {lab=VGND}
C {lab_pin.sym} 140 2400 0 0 {name=l58 lab=VGND}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2560 0 0 {name=skhpn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2530 140 2530 {lab=ua2}
C {lab_pin.sym} 140 2530 0 0 {name=l59 lab=ua2}
N 80 2560 60 2560 {lab=kl_t}
C {lab_pin.sym} 60 2560 0 0 {name=l60 lab=kl_t}
N 120 2590 140 2590 {lab=bkp}
C {lab_pin.sym} 140 2590 0 0 {name=l61 lab=bkp}
N 120 2560 140 2560 {lab=VGND}
C {lab_pin.sym} 140 2560 0 0 {name=l62 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 100 2720 0 0 {name=skhpp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 120 2750 140 2750 {lab=ua2}
C {lab_pin.sym} 140 2750 0 0 {name=l63 lab=ua2}
N 80 2720 60 2720 {lab=kl_c}
C {lab_pin.sym} 60 2720 0 0 {name=l64 lab=kl_c}
N 120 2690 140 2690 {lab=bkp}
C {lab_pin.sym} 140 2690 0 0 {name=l65 lab=bkp}
N 120 2720 140 2720 {lab=VAPWR}
C {lab_pin.sym} 140 2720 0 0 {name=l66 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 100 2880 0 0 {name=sklpn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 120 2850 140 2850 {lab=ua3}
C {lab_pin.sym} 140 2850 0 0 {name=l67 lab=ua3}
N 80 2880 60 2880 {lab=kh_t}
C {lab_pin.sym} 60 2880 0 0 {name=l68 lab=kh_t}
N 120 2910 140 2910 {lab=bkp}
C {lab_pin.sym} 140 2910 0 0 {name=l69 lab=bkp}
N 120 2880 140 2880 {lab=VGND}
C {lab_pin.sym} 140 2880 0 0 {name=l70 lab=VGND}
C {mim_ck2.sym} 500 60 0 0 {name=Xck2p}
N 420 80 400 80 {lab=vg2p}
C {lab_pin.sym} 400 80 0 0 {name=l71 lab=vg2p}
N 580 80 600 80 {lab=bkp}
C {lab_pin.sym} 600 80 0 0 {name=l72 lab=bkp}
C {mim_cint2.sym} 500 200 0 0 {name=Xci2p}
N 420 220 400 220 {lab=vg2p}
C {lab_pin.sym} 400 220 0 0 {name=l73 lab=vg2p}
N 580 220 600 220 {lab=x2n}
C {lab_pin.sym} 600 220 0 0 {name=l74 lab=x2n}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 340 0 0 {name=sinnn L=0.5 W=12 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 310 540 310 {lab=ua1}
C {lab_pin.sym} 540 310 0 0 {name=l75 lab=ua1}
N 480 340 460 340 {lab=pas_t}
C {lab_pin.sym} 460 340 0 0 {name=l76 lab=pas_t}
N 520 370 540 370 {lab=b1n}
C {lab_pin.sym} 540 370 0 0 {name=l77 lab=b1n}
N 520 340 540 340 {lab=VGND}
C {lab_pin.sym} 540 340 0 0 {name=l78 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 500 0 0 {name=sinnp L=0.5 W=36 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 530 540 530 {lab=ua1}
C {lab_pin.sym} 540 530 0 0 {name=l79 lab=ua1}
N 480 500 460 500 {lab=pas_c}
C {lab_pin.sym} 460 500 0 0 {name=l80 lab=pas_c}
N 520 470 540 470 {lab=b1n}
C {lab_pin.sym} 540 470 0 0 {name=l81 lab=b1n}
N 520 500 540 500 {lab=VAPWR}
C {lab_pin.sym} 540 500 0 0 {name=l82 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 660 0 0 {name=sswnn L=0.5 W=12 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 630 540 630 {lab=ua0}
C {lab_pin.sym} 540 630 0 0 {name=l83 lab=ua0}
N 480 660 460 660 {lab=swp_t}
C {lab_pin.sym} 460 660 0 0 {name=l84 lab=swp_t}
N 520 690 540 690 {lab=b1n}
C {lab_pin.sym} 540 690 0 0 {name=l85 lab=b1n}
N 520 660 540 660 {lab=VGND}
C {lab_pin.sym} 540 660 0 0 {name=l86 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 820 0 0 {name=sswnp L=0.5 W=36 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 850 540 850 {lab=ua0}
C {lab_pin.sym} 540 850 0 0 {name=l87 lab=ua0}
N 480 820 460 820 {lab=swp_c}
C {lab_pin.sym} 460 820 0 0 {name=l88 lab=swp_c}
N 520 790 540 790 {lab=b1n}
C {lab_pin.sym} 540 790 0 0 {name=l89 lab=b1n}
N 520 820 540 820 {lab=VAPWR}
C {lab_pin.sym} 540 820 0 0 {name=l90 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 980 0 0 {name=sshnn L=0.5 W=12 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 950 540 950 {lab=vscm}
C {lab_pin.sym} 540 950 0 0 {name=l91 lab=vscm}
N 480 980 460 980 {lab=sho_t}
C {lab_pin.sym} 460 980 0 0 {name=l92 lab=sho_t}
N 520 1010 540 1010 {lab=b1n}
C {lab_pin.sym} 540 1010 0 0 {name=l93 lab=b1n}
N 520 980 540 980 {lab=VGND}
C {lab_pin.sym} 540 980 0 0 {name=l94 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1140 0 0 {name=sshnp L=0.5 W=36 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1170 540 1170 {lab=vscm}
C {lab_pin.sym} 540 1170 0 0 {name=l95 lab=vscm}
N 480 1140 460 1140 {lab=sho_c}
C {lab_pin.sym} 460 1140 0 0 {name=l96 lab=sho_c}
N 520 1110 540 1110 {lab=b1n}
C {lab_pin.sym} 540 1110 0 0 {name=l97 lab=b1n}
N 520 1140 540 1140 {lab=VAPWR}
C {lab_pin.sym} 540 1140 0 0 {name=l98 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1300 0 0 {name=sdhnn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1270 540 1270 {lab=ua2}
C {lab_pin.sym} 540 1270 0 0 {name=l99 lab=ua2}
N 480 1300 460 1300 {lab=dl_t}
C {lab_pin.sym} 460 1300 0 0 {name=l100 lab=dl_t}
N 520 1330 540 1330 {lab=b1n}
C {lab_pin.sym} 540 1330 0 0 {name=l101 lab=b1n}
N 520 1300 540 1300 {lab=VGND}
C {lab_pin.sym} 540 1300 0 0 {name=l102 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 1460 0 0 {name=sdhnp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 1490 540 1490 {lab=ua2}
C {lab_pin.sym} 540 1490 0 0 {name=l103 lab=ua2}
N 480 1460 460 1460 {lab=dl_c}
C {lab_pin.sym} 460 1460 0 0 {name=l104 lab=dl_c}
N 520 1430 540 1430 {lab=b1n}
C {lab_pin.sym} 540 1430 0 0 {name=l105 lab=b1n}
N 520 1460 540 1460 {lab=VAPWR}
C {lab_pin.sym} 540 1460 0 0 {name=l106 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1620 0 0 {name=sdlnn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1590 540 1590 {lab=ua3}
C {lab_pin.sym} 540 1590 0 0 {name=l107 lab=ua3}
N 480 1620 460 1620 {lab=dh_t}
C {lab_pin.sym} 460 1620 0 0 {name=l108 lab=dh_t}
N 520 1650 540 1650 {lab=b1n}
C {lab_pin.sym} 540 1650 0 0 {name=l109 lab=b1n}
N 520 1620 540 1620 {lab=VGND}
C {lab_pin.sym} 540 1620 0 0 {name=l110 lab=VGND}
C {mim_cs.sym} 500 1780 0 0 {name=Xcs1n}
N 420 1800 400 1800 {lab=tp1n}
C {lab_pin.sym} 400 1800 0 0 {name=l111 lab=tp1n}
N 580 1800 600 1800 {lab=b1n}
C {lab_pin.sym} 600 1800 0 0 {name=l112 lab=b1n}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 1920 0 0 {name=sg1nn L=0.5 W=5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 1890 540 1890 {lab=tp1n}
C {lab_pin.sym} 540 1890 0 0 {name=l113 lab=tp1n}
N 480 1920 460 1920 {lab=ie_t}
C {lab_pin.sym} 460 1920 0 0 {name=l114 lab=ie_t}
N 520 1950 540 1950 {lab=vg1n}
C {lab_pin.sym} 540 1950 0 0 {name=l115 lab=vg1n}
N 520 1920 540 1920 {lab=VGND}
C {lab_pin.sym} 540 1920 0 0 {name=l116 lab=VGND}
C {mim_cint1.sym} 500 2080 0 0 {name=Xci1n}
N 420 2100 400 2100 {lab=vg1n}
C {lab_pin.sym} 400 2100 0 0 {name=l117 lab=vg1n}
N 580 2100 600 2100 {lab=x1p}
C {lab_pin.sym} 600 2100 0 0 {name=l118 lab=x1p}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2220 0 0 {name=s2innn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2190 540 2190 {lab=x1n}
C {lab_pin.sym} 540 2190 0 0 {name=l119 lab=x1n}
N 480 2220 460 2220 {lab=sl_t}
C {lab_pin.sym} 460 2220 0 0 {name=l120 lab=sl_t}
N 520 2250 540 2250 {lab=b2n}
C {lab_pin.sym} 540 2250 0 0 {name=l121 lab=b2n}
N 520 2220 540 2220 {lab=VGND}
C {lab_pin.sym} 540 2220 0 0 {name=l122 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 2380 0 0 {name=s2innp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 2410 540 2410 {lab=x1n}
C {lab_pin.sym} 540 2410 0 0 {name=l123 lab=x1n}
N 480 2380 460 2380 {lab=sl_c}
C {lab_pin.sym} 460 2380 0 0 {name=l124 lab=sl_c}
N 520 2350 540 2350 {lab=b2n}
C {lab_pin.sym} 540 2350 0 0 {name=l125 lab=b2n}
N 520 2380 540 2380 {lab=VAPWR}
C {lab_pin.sym} 540 2380 0 0 {name=l126 lab=VAPWR}
C {mim_cs.sym} 500 2540 0 0 {name=Xcs2n}
N 420 2560 400 2560 {lab=tp2n}
C {lab_pin.sym} 400 2560 0 0 {name=l127 lab=tp2n}
N 580 2560 600 2560 {lab=b2n}
C {lab_pin.sym} 600 2560 0 0 {name=l128 lab=b2n}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2680 0 0 {name=sg2nn L=0.5 W=5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2650 540 2650 {lab=tp2n}
C {lab_pin.sym} 540 2650 0 0 {name=l129 lab=tp2n}
N 480 2680 460 2680 {lab=ie_t}
C {lab_pin.sym} 460 2680 0 0 {name=l130 lab=ie_t}
N 520 2710 540 2710 {lab=vg2n}
C {lab_pin.sym} 540 2710 0 0 {name=l131 lab=vg2n}
N 520 2680 540 2680 {lab=VGND}
C {lab_pin.sym} 540 2680 0 0 {name=l132 lab=VGND}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 500 2840 0 0 {name=skhnn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 520 2810 540 2810 {lab=ua2}
C {lab_pin.sym} 540 2810 0 0 {name=l133 lab=ua2}
N 480 2840 460 2840 {lab=kh_t}
C {lab_pin.sym} 460 2840 0 0 {name=l134 lab=kh_t}
N 520 2870 540 2870 {lab=bkn}
C {lab_pin.sym} 540 2870 0 0 {name=l135 lab=bkn}
N 520 2840 540 2840 {lab=VGND}
C {lab_pin.sym} 540 2840 0 0 {name=l136 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 500 3000 0 0 {name=skhnp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 520 3030 540 3030 {lab=ua2}
C {lab_pin.sym} 540 3030 0 0 {name=l137 lab=ua2}
N 480 3000 460 3000 {lab=kh_c}
C {lab_pin.sym} 460 3000 0 0 {name=l138 lab=kh_c}
N 520 2970 540 2970 {lab=bkn}
C {lab_pin.sym} 540 2970 0 0 {name=l139 lab=bkn}
N 520 3000 540 3000 {lab=VAPWR}
C {lab_pin.sym} 540 3000 0 0 {name=l140 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 60 0 0 {name=sklnn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 30 940 30 {lab=ua3}
C {lab_pin.sym} 940 30 0 0 {name=l141 lab=ua3}
N 880 60 860 60 {lab=kl_t}
C {lab_pin.sym} 860 60 0 0 {name=l142 lab=kl_t}
N 920 90 940 90 {lab=bkn}
C {lab_pin.sym} 940 90 0 0 {name=l143 lab=bkn}
N 920 60 940 60 {lab=VGND}
C {lab_pin.sym} 940 60 0 0 {name=l144 lab=VGND}
C {mim_ck2.sym} 900 220 0 0 {name=Xck2n}
N 820 240 800 240 {lab=vg2n}
C {lab_pin.sym} 800 240 0 0 {name=l145 lab=vg2n}
N 980 240 1000 240 {lab=bkn}
C {lab_pin.sym} 1000 240 0 0 {name=l146 lab=bkn}
C {mim_cint2.sym} 900 360 0 0 {name=Xci2n}
N 820 380 800 380 {lab=vg2n}
C {lab_pin.sym} 800 380 0 0 {name=l147 lab=vg2n}
N 980 380 1000 380 {lab=x2p}
C {lab_pin.sym} 1000 380 0 0 {name=l148 lab=x2p}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 500 0 0 {name=stp1n L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 470 940 470 {lab=tp1p}
C {lab_pin.sym} 940 470 0 0 {name=l149 lab=tp1p}
N 880 500 860 500 {lab=se_t}
C {lab_pin.sym} 860 500 0 0 {name=l150 lab=se_t}
N 920 530 940 530 {lab=tp1n}
C {lab_pin.sym} 940 530 0 0 {name=l151 lab=tp1n}
N 920 500 940 500 {lab=VGND}
C {lab_pin.sym} 940 500 0 0 {name=l152 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 660 0 0 {name=stp1p L=0.5 W=4 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 690 940 690 {lab=tp1p}
C {lab_pin.sym} 940 690 0 0 {name=l153 lab=tp1p}
N 880 660 860 660 {lab=se_c}
C {lab_pin.sym} 860 660 0 0 {name=l154 lab=se_c}
N 920 630 940 630 {lab=tp1n}
C {lab_pin.sym} 940 630 0 0 {name=l155 lab=tp1n}
N 920 660 940 660 {lab=VAPWR}
C {lab_pin.sym} 940 660 0 0 {name=l156 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 820 0 0 {name=s2cmn L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 790 940 790 {lab=b2p}
C {lab_pin.sym} 940 790 0 0 {name=l157 lab=b2p}
N 880 820 860 820 {lab=il_t}
C {lab_pin.sym} 860 820 0 0 {name=l158 lab=il_t}
N 920 850 940 850 {lab=b2n}
C {lab_pin.sym} 940 850 0 0 {name=l159 lab=b2n}
N 920 820 940 820 {lab=VGND}
C {lab_pin.sym} 940 820 0 0 {name=l160 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 980 0 0 {name=s2cmp L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1010 940 1010 {lab=b2p}
C {lab_pin.sym} 940 1010 0 0 {name=l161 lab=b2p}
N 880 980 860 980 {lab=il_c}
C {lab_pin.sym} 860 980 0 0 {name=l162 lab=il_c}
N 920 950 940 950 {lab=b2n}
C {lab_pin.sym} 940 950 0 0 {name=l163 lab=b2n}
N 920 980 940 980 {lab=VAPWR}
C {lab_pin.sym} 940 980 0 0 {name=l164 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1140 0 0 {name=stp2n L=0.5 W=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1110 940 1110 {lab=tp2p}
C {lab_pin.sym} 940 1110 0 0 {name=l165 lab=tp2p}
N 880 1140 860 1140 {lab=se_t}
C {lab_pin.sym} 860 1140 0 0 {name=l166 lab=se_t}
N 920 1170 940 1170 {lab=tp2n}
C {lab_pin.sym} 940 1170 0 0 {name=l167 lab=tp2n}
N 920 1140 940 1140 {lab=VGND}
C {lab_pin.sym} 940 1140 0 0 {name=l168 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1300 0 0 {name=stp2p L=0.5 W=4 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1330 940 1330 {lab=tp2p}
C {lab_pin.sym} 940 1330 0 0 {name=l169 lab=tp2p}
N 880 1300 860 1300 {lab=se_c}
C {lab_pin.sym} 860 1300 0 0 {name=l170 lab=se_c}
N 920 1270 940 1270 {lab=tp2n}
C {lab_pin.sym} 940 1270 0 0 {name=l171 lab=tp2n}
N 920 1300 940 1300 {lab=VAPWR}
C {lab_pin.sym} 940 1300 0 0 {name=l172 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1460 0 0 {name=sk0n L=0.5 W=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1430 940 1430 {lab=bkp}
C {lab_pin.sym} 940 1430 0 0 {name=l173 lab=bkp}
N 880 1460 860 1460 {lab=k0_t}
C {lab_pin.sym} 860 1460 0 0 {name=l174 lab=k0_t}
N 920 1490 940 1490 {lab=bkn}
C {lab_pin.sym} 940 1490 0 0 {name=l175 lab=bkn}
N 920 1460 940 1460 {lab=VGND}
C {lab_pin.sym} 940 1460 0 0 {name=l176 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1620 0 0 {name=sk0p L=0.5 W=12 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1650 940 1650 {lab=bkp}
C {lab_pin.sym} 940 1650 0 0 {name=l177 lab=bkp}
N 880 1620 860 1620 {lab=k0_c}
C {lab_pin.sym} 860 1620 0 0 {name=l178 lab=k0_c}
N 920 1590 940 1590 {lab=bkn}
C {lab_pin.sym} 940 1590 0 0 {name=l179 lab=bkn}
N 920 1620 940 1620 {lab=VAPWR}
C {lab_pin.sym} 940 1620 0 0 {name=l180 lab=VAPWR}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 1780 0 0 {name=sr2n L=0.5 W=8 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
N 920 1750 940 1750 {lab=x2p}
C {lab_pin.sym} 940 1750 0 0 {name=l181 lab=x2p}
N 880 1780 860 1780 {lab=r2_t}
C {lab_pin.sym} 860 1780 0 0 {name=l182 lab=r2_t}
N 920 1810 940 1810 {lab=x2n}
C {lab_pin.sym} 940 1810 0 0 {name=l183 lab=x2n}
N 920 1780 940 1780 {lab=VGND}
C {lab_pin.sym} 940 1780 0 0 {name=l184 lab=VGND}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 1940 0 0 {name=sr2p L=0.5 W=24 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
N 920 1970 940 1970 {lab=x2p}
C {lab_pin.sym} 940 1970 0 0 {name=l185 lab=x2p}
N 880 1940 860 1940 {lab=r2_c}
C {lab_pin.sym} 860 1940 0 0 {name=l186 lab=r2_c}
N 920 1910 940 1910 {lab=x2n}
C {lab_pin.sym} 940 1910 0 0 {name=l187 lab=x2n}
N 920 1940 940 1940 {lab=VAPWR}
C {lab_pin.sym} 940 1940 0 0 {name=l188 lab=VAPWR}
C {ota1.sym} 900 2100 0 0 {name=Xota1}
N 820 2120 800 2120 {lab=VAPWR}
C {lab_pin.sym} 800 2120 0 0 {name=l189 lab=VAPWR}
N 820 2140 800 2140 {lab=VGND}
C {lab_pin.sym} 800 2140 0 0 {name=l190 lab=VGND}
N 820 2160 800 2160 {lab=vg1p}
C {lab_pin.sym} 800 2160 0 0 {name=l191 lab=vg1p}
N 820 2180 800 2180 {lab=vg1n}
C {lab_pin.sym} 800 2180 0 0 {name=l192 lab=vg1n}
N 820 2200 800 2200 {lab=x1p}
C {lab_pin.sym} 800 2200 0 0 {name=l193 lab=x1p}
N 820 2220 800 2220 {lab=x1n}
C {lab_pin.sym} 800 2220 0 0 {name=l194 lab=x1n}
N 820 2240 800 2240 {lab=vicm}
C {lab_pin.sym} 800 2240 0 0 {name=l195 lab=vicm}
N 820 2260 800 2260 {lab=vocm}
C {lab_pin.sym} 800 2260 0 0 {name=l196 lab=vocm}
N 820 2280 800 2280 {lab=o1_ibtp}
C {lab_pin.sym} 800 2280 0 0 {name=l197 lab=o1_ibtp}
N 820 2300 800 2300 {lab=o1_ibn}
C {lab_pin.sym} 800 2300 0 0 {name=l198 lab=o1_ibn}
N 820 2320 800 2320 {lab=o1_ibp}
C {lab_pin.sym} 800 2320 0 0 {name=l199 lab=o1_ibp}
N 820 2340 800 2340 {lab=o1_ivbnc}
C {lab_pin.sym} 800 2340 0 0 {name=l200 lab=o1_ivbnc}
N 980 2120 1000 2120 {lab=o1_ivbpc}
C {lab_pin.sym} 1000 2120 0 0 {name=l201 lab=o1_ivbpc}
N 980 2140 1000 2140 {lab=o1_ivbl0}
C {lab_pin.sym} 1000 2140 0 0 {name=l202 lab=o1_ivbl0}
N 980 2160 1000 2160 {lab=chp}
C {lab_pin.sym} 1000 2160 0 0 {name=l203 lab=chp}
N 980 2180 1000 2180 {lab=chn}
C {lab_pin.sym} 1000 2180 0 0 {name=l204 lab=chn}
N 980 2200 1000 2200 {lab=chlp}
C {lab_pin.sym} 1000 2200 0 0 {name=l205 lab=chlp}
N 980 2220 1000 2220 {lab=chln}
C {lab_pin.sym} 1000 2220 0 0 {name=l206 lab=chln}
N 980 2240 1000 2240 {lab=isl}
C {lab_pin.sym} 1000 2240 0 0 {name=l207 lab=isl}
N 980 2260 1000 2260 {lab=il_t}
C {lab_pin.sym} 1000 2260 0 0 {name=l208 lab=il_t}
N 980 2280 1000 2280 {lab=il_c}
C {lab_pin.sym} 1000 2280 0 0 {name=l209 lab=il_c}
N 980 2300 1000 2300 {lab=sl_t}
C {lab_pin.sym} 1000 2300 0 0 {name=l210 lab=sl_t}
N 980 2320 1000 2320 {lab=sl_c}
C {lab_pin.sym} 1000 2320 0 0 {name=l211 lab=sl_c}
N 980 2340 1000 2340 {lab=rstb}
C {lab_pin.sym} 1000 2340 0 0 {name=l212 lab=rstb}
C {ota2.sym} 900 2460 0 0 {name=Xota2}
N 820 2480 800 2480 {lab=VAPWR}
C {lab_pin.sym} 800 2480 0 0 {name=l213 lab=VAPWR}
N 820 2500 800 2500 {lab=VGND}
C {lab_pin.sym} 800 2500 0 0 {name=l214 lab=VGND}
N 820 2520 800 2520 {lab=vg2p}
C {lab_pin.sym} 800 2520 0 0 {name=l215 lab=vg2p}
N 820 2540 800 2540 {lab=vg2n}
C {lab_pin.sym} 800 2540 0 0 {name=l216 lab=vg2n}
N 820 2560 800 2560 {lab=x2p}
C {lab_pin.sym} 800 2560 0 0 {name=l217 lab=x2p}
N 820 2580 800 2580 {lab=x2n}
C {lab_pin.sym} 800 2580 0 0 {name=l218 lab=x2n}
N 820 2600 800 2600 {lab=vicm}
C {lab_pin.sym} 800 2600 0 0 {name=l219 lab=vicm}
N 820 2620 800 2620 {lab=vocm}
C {lab_pin.sym} 800 2620 0 0 {name=l220 lab=vocm}
N 820 2640 800 2640 {lab=o1_ibtp}
C {lab_pin.sym} 800 2640 0 0 {name=l221 lab=o1_ibtp}
N 820 2660 800 2660 {lab=o1_ibn}
C {lab_pin.sym} 800 2660 0 0 {name=l222 lab=o1_ibn}
N 820 2680 800 2680 {lab=o1_ibp}
C {lab_pin.sym} 800 2680 0 0 {name=l223 lab=o1_ibp}
N 820 2700 800 2700 {lab=o1_ivbnc}
C {lab_pin.sym} 800 2700 0 0 {name=l224 lab=o1_ivbnc}
N 980 2480 1000 2480 {lab=o1_ivbpc}
C {lab_pin.sym} 1000 2480 0 0 {name=l225 lab=o1_ivbpc}
N 980 2500 1000 2500 {lab=o1_ivbl0}
C {lab_pin.sym} 1000 2500 0 0 {name=l226 lab=o1_ivbl0}
N 980 2520 1000 2520 {lab=chp}
C {lab_pin.sym} 1000 2520 0 0 {name=l227 lab=chp}
N 980 2540 1000 2540 {lab=chn}
C {lab_pin.sym} 1000 2540 0 0 {name=l228 lab=chn}
N 980 2560 1000 2560 {lab=chlp}
C {lab_pin.sym} 1000 2560 0 0 {name=l229 lab=chlp}
N 980 2580 1000 2580 {lab=chln}
C {lab_pin.sym} 1000 2580 0 0 {name=l230 lab=chln}
N 980 2600 1000 2600 {lab=r2_t}
C {lab_pin.sym} 1000 2600 0 0 {name=l231 lab=r2_t}
N 980 2620 1000 2620 {lab=il_t}
C {lab_pin.sym} 1000 2620 0 0 {name=l232 lab=il_t}
N 980 2640 1000 2640 {lab=il_c}
C {lab_pin.sym} 1000 2640 0 0 {name=l233 lab=il_c}
N 980 2660 1000 2660 {lab=sl_t}
C {lab_pin.sym} 1000 2660 0 0 {name=l234 lab=sl_t}
N 980 2680 1000 2680 {lab=sl_c}
C {lab_pin.sym} 1000 2680 0 0 {name=l235 lab=sl_c}
N 980 2700 1000 2700 {lab=rstb}
C {lab_pin.sym} 1000 2700 0 0 {name=l236 lab=rstb}
C {c3_comp.sym} 900 2820 0 0 {name=Xcmp}
N 820 2840 800 2840 {lab=x2p}
C {lab_pin.sym} 800 2840 0 0 {name=l237 lab=x2p}
N 820 2860 800 2860 {lab=x2n}
C {lab_pin.sym} 800 2860 0 0 {name=l238 lab=x2n}
N 820 2880 800 2880 {lab=phc}
C {lab_pin.sym} 800 2880 0 0 {name=l239 lab=phc}
N 820 2900 800 2900 {lab=comp_out}
C {lab_pin.sym} 800 2900 0 0 {name=l240 lab=comp_out}
N 980 2840 1000 2840 {lab=qb}
C {lab_pin.sym} 1000 2840 0 0 {name=l241 lab=qb}
N 980 2860 1000 2860 {lab=VDPWR}
C {lab_pin.sym} 1000 2860 0 0 {name=l242 lab=VDPWR}
N 980 2880 1000 2880 {lab=VGND}
C {lab_pin.sym} 1000 2880 0 0 {name=l243 lab=VGND}
C {cells/sky130_fd_sc_hd__nand2_1.sym} 1300 60 0 0 {name=Xdec}
N 1220 80 1200 80 {lab=comp_out}
C {lab_pin.sym} 1200 80 0 0 {name=l244 lab=comp_out}
N 1220 100 1200 100 {lab=qb}
C {lab_pin.sym} 1200 100 0 0 {name=l245 lab=qb}
N 1220 120 1200 120 {lab=VGND}
C {lab_pin.sym} 1200 120 0 0 {name=l246 lab=VGND}
N 1220 140 1200 140 {lab=VGND}
C {lab_pin.sym} 1200 140 0 0 {name=l247 lab=VGND}
N 1380 80 1400 80 {lab=VDPWR}
C {lab_pin.sym} 1400 80 0 0 {name=l248 lab=VDPWR}
N 1380 100 1400 100 {lab=VDPWR}
C {lab_pin.sym} 1400 100 0 0 {name=l249 lab=VDPWR}
N 1380 120 1400 120 {lab=dec}
C {lab_pin.sym} 1400 120 0 0 {name=l250 lab=dec}
C {c4_gen.sym} 1300 260 0 0 {name=Xgen}
N 1220 280 1200 280 {lab=VAPWR}
C {lab_pin.sym} 1200 280 0 0 {name=l251 lab=VAPWR}
N 1220 300 1200 300 {lab=VDPWR}
C {lab_pin.sym} 1200 300 0 0 {name=l252 lab=VDPWR}
N 1220 320 1200 320 {lab=VGND}
C {lab_pin.sym} 1200 320 0 0 {name=l253 lab=VGND}
N 1220 340 1200 340 {lab=fs}
C {lab_pin.sym} 1200 340 0 0 {name=l254 lab=fs}
N 1220 360 1200 360 {lab=y}
C {lab_pin.sym} 1200 360 0 0 {name=l255 lab=y}
N 1220 380 1200 380 {lab=swap}
C {lab_pin.sym} 1200 380 0 0 {name=l256 lab=swap}
N 1220 400 1200 400 {lab=short}
C {lab_pin.sym} 1200 400 0 0 {name=l257 lab=short}
N 1220 420 1200 420 {lab=chop}
C {lab_pin.sym} 1200 420 0 0 {name=l258 lab=chop}
N 1220 440 1200 440 {lab=rst_analog}
C {lab_pin.sym} 1200 440 0 0 {name=l259 lab=rst_analog}
N 1220 460 1200 460 {lab=order}
C {lab_pin.sym} 1200 460 0 0 {name=l260 lab=order}
N 1220 480 1200 480 {lab=dec}
C {lab_pin.sym} 1200 480 0 0 {name=l261 lab=dec}
N 1220 500 1200 500 {lab=ie_t}
C {lab_pin.sym} 1200 500 0 0 {name=l262 lab=ie_t}
N 1220 520 1200 520 {lab=ie_c}
C {lab_pin.sym} 1200 520 0 0 {name=l263 lab=ie_c}
N 1220 540 1200 540 {lab=il_t}
C {lab_pin.sym} 1200 540 0 0 {name=l264 lab=il_t}
N 1220 560 1200 560 {lab=il_c}
C {lab_pin.sym} 1200 560 0 0 {name=l265 lab=il_c}
N 1220 580 1200 580 {lab=se_t}
C {lab_pin.sym} 1200 580 0 0 {name=l266 lab=se_t}
N 1220 600 1200 600 {lab=se_c}
C {lab_pin.sym} 1200 600 0 0 {name=l267 lab=se_c}
N 1220 620 1200 620 {lab=sl_t}
C {lab_pin.sym} 1200 620 0 0 {name=l268 lab=sl_t}
N 1220 640 1200 640 {lab=sl_c}
C {lab_pin.sym} 1200 640 0 0 {name=l269 lab=sl_c}
N 1220 660 1200 660 {lab=pas_t}
C {lab_pin.sym} 1200 660 0 0 {name=l270 lab=pas_t}
N 1220 680 1200 680 {lab=pas_c}
C {lab_pin.sym} 1200 680 0 0 {name=l271 lab=pas_c}
N 1220 700 1200 700 {lab=swp_t}
C {lab_pin.sym} 1200 700 0 0 {name=l272 lab=swp_t}
N 1220 720 1200 720 {lab=swp_c}
C {lab_pin.sym} 1200 720 0 0 {name=l273 lab=swp_c}
N 1380 280 1400 280 {lab=sho_t}
C {lab_pin.sym} 1400 280 0 0 {name=l274 lab=sho_t}
N 1380 300 1400 300 {lab=sho_c}
C {lab_pin.sym} 1400 300 0 0 {name=l275 lab=sho_c}
N 1380 320 1400 320 {lab=dh_t}
C {lab_pin.sym} 1400 320 0 0 {name=l276 lab=dh_t}
N 1380 340 1400 340 {lab=dh_c}
C {lab_pin.sym} 1400 340 0 0 {name=l277 lab=dh_c}
N 1380 360 1400 360 {lab=dl_t}
C {lab_pin.sym} 1400 360 0 0 {name=l278 lab=dl_t}
N 1380 380 1400 380 {lab=dl_c}
C {lab_pin.sym} 1400 380 0 0 {name=l279 lab=dl_c}
N 1380 400 1400 400 {lab=kh_t}
C {lab_pin.sym} 1400 400 0 0 {name=l280 lab=kh_t}
N 1380 420 1400 420 {lab=kh_c}
C {lab_pin.sym} 1400 420 0 0 {name=l281 lab=kh_c}
N 1380 440 1400 440 {lab=kl_t}
C {lab_pin.sym} 1400 440 0 0 {name=l282 lab=kl_t}
N 1380 460 1400 460 {lab=kl_c}
C {lab_pin.sym} 1400 460 0 0 {name=l283 lab=kl_c}
N 1380 480 1400 480 {lab=k0_t}
C {lab_pin.sym} 1400 480 0 0 {name=l284 lab=k0_t}
N 1380 500 1400 500 {lab=k0_c}
C {lab_pin.sym} 1400 500 0 0 {name=l285 lab=k0_c}
N 1380 520 1400 520 {lab=r2_t}
C {lab_pin.sym} 1400 520 0 0 {name=l286 lab=r2_t}
N 1380 540 1400 540 {lab=r2_c}
C {lab_pin.sym} 1400 540 0 0 {name=l287 lab=r2_c}
N 1380 560 1400 560 {lab=isl}
C {lab_pin.sym} 1400 560 0 0 {name=l288 lab=isl}
N 1380 580 1400 580 {lab=rstb}
C {lab_pin.sym} 1400 580 0 0 {name=l289 lab=rstb}
N 1380 600 1400 600 {lab=chp}
C {lab_pin.sym} 1400 600 0 0 {name=l290 lab=chp}
N 1380 620 1400 620 {lab=chn}
C {lab_pin.sym} 1400 620 0 0 {name=l291 lab=chn}
N 1380 640 1400 640 {lab=chlp}
C {lab_pin.sym} 1400 640 0 0 {name=l292 lab=chlp}
N 1380 660 1400 660 {lab=chln}
C {lab_pin.sym} 1400 660 0 0 {name=l293 lab=chln}
N 1380 680 1400 680 {lab=phc}
C {lab_pin.sym} 1400 680 0 0 {name=l294 lab=phc}
N 1380 700 1400 700 {lab=pwrok}
C {lab_pin.sym} 1400 700 0 0 {name=l295 lab=pwrok}
N 1380 720 1400 720 {lab=fsh}
C {lab_pin.sym} 1400 720 0 0 {name=l296 lab=fsh}
C {c6_bias.sym} 1300 840 0 0 {name=Xbias}
N 1220 860 1200 860 {lab=VAPWR}
C {lab_pin.sym} 1200 860 0 0 {name=l297 lab=VAPWR}
N 1220 880 1200 880 {lab=VGND}
C {lab_pin.sym} 1200 880 0 0 {name=l298 lab=VGND}
N 1220 900 1200 900 {lab=VDPWR}
C {lab_pin.sym} 1200 900 0 0 {name=l299 lab=VDPWR}
N 1220 920 1200 920 {lab=boost}
C {lab_pin.sym} 1200 920 0 0 {name=l300 lab=boost}
N 1220 940 1200 940 {lab=trim0}
C {lab_pin.sym} 1200 940 0 0 {name=l301 lab=trim0}
N 1220 960 1200 960 {lab=trim1}
C {lab_pin.sym} 1200 960 0 0 {name=l302 lab=trim1}
N 1380 860 1400 860 {lab=trim2}
C {lab_pin.sym} 1400 860 0 0 {name=l303 lab=trim2}
N 1380 880 1400 880 {lab=o1_ibtp}
C {lab_pin.sym} 1400 880 0 0 {name=l304 lab=o1_ibtp}
N 1380 900 1400 900 {lab=o1_ibn}
C {lab_pin.sym} 1400 900 0 0 {name=l305 lab=o1_ibn}
N 1380 920 1400 920 {lab=o1_ibp}
C {lab_pin.sym} 1400 920 0 0 {name=l306 lab=o1_ibp}
N 1380 940 1400 940 {lab=o1_ivbl0}
C {lab_pin.sym} 1400 940 0 0 {name=l307 lab=o1_ivbl0}
N 1380 960 1400 960 {lab=ok}
C {lab_pin.sym} 1400 960 0 0 {name=l308 lab=ok}
C {c5c7_ref.sym} 1300 1080 0 0 {name=Xref}
N 1220 1100 1200 1100 {lab=ua2}
C {lab_pin.sym} 1200 1100 0 0 {name=l309 lab=ua2}
N 1220 1120 1200 1120 {lab=VGND}
C {lab_pin.sym} 1200 1120 0 0 {name=l310 lab=VGND}
N 1220 1140 1200 1140 {lab=vocm}
C {lab_pin.sym} 1200 1140 0 0 {name=l311 lab=vocm}
N 1380 1100 1400 1100 {lab=vicm}
C {lab_pin.sym} 1400 1100 0 0 {name=l312 lab=vicm}
N 1380 1120 1400 1120 {lab=vscm}
C {lab_pin.sym} 1400 1120 0 0 {name=l313 lab=vscm}
C {cells/sky130_fd_sc_hvl__lsbufhv2lv_1.sym} 1300 1260 0 0 {name=Xlsok}
N 1220 1280 1200 1280 {lab=ok}
C {lab_pin.sym} 1200 1280 0 0 {name=l314 lab=ok}
N 1220 1300 1200 1300 {lab=VDPWR}
C {lab_pin.sym} 1200 1300 0 0 {name=l315 lab=VDPWR}
N 1220 1320 1200 1320 {lab=VGND}
C {lab_pin.sym} 1200 1320 0 0 {name=l316 lab=VGND}
N 1220 1340 1200 1340 {lab=VGND}
C {lab_pin.sym} 1200 1340 0 0 {name=l317 lab=VGND}
N 1380 1280 1400 1280 {lab=VAPWR}
C {lab_pin.sym} 1400 1280 0 0 {name=l318 lab=VAPWR}
N 1380 1300 1400 1300 {lab=VAPWR}
C {lab_pin.sym} 1400 1300 0 0 {name=l319 lab=VAPWR}
N 1380 1320 1400 1320 {lab=bias_ok}
C {lab_pin.sym} 1400 1320 0 0 {name=l320 lab=bias_ok}
