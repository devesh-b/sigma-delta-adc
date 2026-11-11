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
