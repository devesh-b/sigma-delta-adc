* components: Xj = junction only (Vds 0); Xs = one off device, other side 0.5 V below vg
.lib /home/mempool/.ciel/sky130A/libs.tech/ngspice/sky130.lib.spice ff
.param wn=1 lch=0.5
Vj vj 0 1.65
Vs vs 0 1.65
Vo o 0 1.15
Vg g 0 0
Xj vj g vj 0 sky130_fd_pr__nfet_g5v0d10v5 w={wn} l={lch} ad={wn*0.29} as={wn*0.29} pd={2*(wn+0.29)} ps={2*(wn+0.29)}
Xs o g vs 0 sky130_fd_pr__nfet_g5v0d10v5 w={wn} l={lch} ad={wn*0.29} as={wn*0.29} pd={2*(wn+0.29)} ps={2*(wn+0.29)}
.option gmin=1e-18
.control
foreach t -40 27 85 100 125
  set temp=$t
  op
  echo T=$t
  print -i(Vj)*1e12
  print -i(Vs)*1e12
end
.endc
.end
