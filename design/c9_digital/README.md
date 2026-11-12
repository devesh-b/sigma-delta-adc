# C9 digital (WO-37)

RTL in `rtl/` (Verilog-2005, one clock domain, clk 48 MHz). Top `tt_um_sd_adc_c9` wraps `c9_core`; the analog-side
pins (comparator in, control outs) are extra ports of the wrapper. `smoke/` is a one-vector elaboration check
(golden `rst_default` frame 0), not the verification TB (`tb/` is a separate agent's).

Hierarchy: `c9_core` = `c9_fsdiv` (divider, fs_tick, bit clock) + `c9_cfg` (serial shift, shadow, active, cfg_pending)
+ `c9_seq` (slot counter, reset window, chop, forced y[0] / DAC flop, control outputs) + `c9_dec` (acc1/acc2, hold,
frame_ready/overrun, rd guard) + `c9_rdbus` (addr sync, registered word, debug mux).

Interpretations (SPEC gaps, see the WO-37 report): comparator for bit y[n] is sampled in conv cycle n-1 (c = n+1; the
sample in c = 1 is the junk bit, overridden by y_force); the rd clear runs one clk after the rd edge; debug uo/uio is a
mux of flops by a flop select; debug y is the DAC flop (D67).

Run (sandbox, IIC-OSIC-TOOLS): `verilator --lint-only -Wall --top-module tt_um_sd_adc_c9 rtl/*.v`;
`yosys -p "read_verilog rtl/*.v; synth -top tt_um_sd_adc_c9 -flatten; check -assert; stat"`;
`python3 smoke/gen_vec.py ../../golden/s6_vectors.json smoke/vec.vh; iverilog -g2005 -Ismoke -o s.vvp smoke/smoke_tb.v rtl/*.v; vvp s.vvp`.

## Firmware-visible facts (WO-42, verification; not SPEC changes)
- **acc LSBs are always 0 for even N.** acc1 = sum of N values of +-1, so it is even. acc2 = sum of the partial sums S_0..S_{N-1}
  (exclusive); S_k has the parity of k, so there are N/2 odd terms, and N/2 is even for N >= 4, so acc2 is even too. Bit 0 of word 1 (acc1[15:0]) and of word 3
  (acc2[15:0]) reads 0 in every frame (N 64/256/1024/4096 are all even). Verilator toggle coverage confirms
  this: hold_acc1[0] and hold_acc2[0] never toggle (WO-40). Firmware must not treat a stuck LSB as a fault.
- **status[8] is tied to 0** (SPEC 3.8a status word: [8] = 0). Do not use it as a flag.
