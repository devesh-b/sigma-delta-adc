v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -440 0 -400 0 {lab=top}
C {iopin.sym} -440 0 0 0 {name=p0 lab=top}
C {lab_pin.sym} -400 0 0 0 {name=lp0 lab=top}
N -440 40 -400 40 {lab=bot}
C {iopin.sym} -440 40 0 0 {name=p1 lab=bot}
C {lab_pin.sym} -400 40 0 0 {name=lp1 lab=bot}
C {sky130_fd_pr/cap_mim_m3_1.sym} 100 60 0 0 {name=c W=11 L=11 MF=16 model=cap_mim_m3_1 spiceprefix=X}
N 100 30 100 10 {lab=top}
C {lab_pin.sym} 100 10 0 0 {name=l1 lab=top}
N 100 90 100 110 {lab=bot}
C {lab_pin.sym} 100 110 0 0 {name=l2 lab=bot}
