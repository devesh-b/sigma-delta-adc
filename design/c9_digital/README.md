# C9 digital (WO-37)

RTL in `rtl/` (Verilog-2005, one clock domain, clk 48 MHz). Macro top `sd_adc_c9` (module in `c9_core.v`, D72, no `tt_um_` prefix); `tt_um_sd_adc_c9` is a thin simulation-only wrapper. The analog-side
pins (comparator in, control outs) are extra ports of the wrapper. `smoke/` is a one-vector elaboration check
(golden `rst_default` frame 0), not the verification TB (`tb/` is a separate agent's).

Hierarchy: `sd_adc_c9` = `c9_fsdiv` (divider, fs_tick, bit clock) + `c9_cfg` (serial shift, shadow, active, cfg_pending)
+ `c9_seq` (slot counter, reset window, chop, forced y[0] / DAC flop, control outputs) + `c9_dec` (acc1/acc2, hold,
frame_ready/overrun, rd guard) + `c9_rdbus` (addr sync, registered word, debug mux).

Interpretations (SPEC gaps, see the WO-37 report): comparator for bit y[n] is captured straight into the DAC flop on the fs_tick ending conv cycle n-1 (c = n+1, D74; no comp_s flop; the
sample in c = 1 is the junk bit, overridden by y_force); the rd clear runs one clk after the rd edge; debug uo/uio is a
mux of flops by a flop select; debug y is the DAC flop (D67).

Run (sandbox, IIC-OSIC-TOOLS): `verilator --lint-only -Wall --top-module sd_adc_c9 rtl/*.v`;
`yosys -p "read_verilog rtl/*.v; synth -top sd_adc_c9 -flatten; check -assert; stat"`;
`python3 smoke/gen_vec.py ../../golden/s6_vectors.json smoke/vec.vh; iverilog -g2005 -Ismoke -o s.vvp smoke/smoke_tb.v rtl/*.v; vvp s.vvp`.

## Firmware-visible facts (WO-42, verification; not SPEC changes)
- **acc LSBs are always 0 for even N.** acc1 = sum of N values of +-1, so it is even. acc2 = sum of the partial sums S_0..S_{N-1}
  (exclusive); S_k has the parity of k, so there are N/2 odd terms, and N/2 is even for N >= 4, so acc2 is even too. Bit 0 of word 1 (acc1[15:0]) and of word 3
  (acc2[15:0]) reads 0 in every frame (N 64/256/1024/4096 are all even). Verilator toggle coverage confirms
  this: hold_acc1[0] and hold_acc2[0] never toggle (WO-40). Firmware must not treat a stuck LSB as a fault.
- **status[8] is tied to 0** (SPEC 3.8a status word: [8] = 0). Do not use it as a flag.

## WO-49 (D72, D74)
- acc1 is 14 b and acc2 24 b on chip (D77, CL-29: max |acc2| = N(N-1)/2 < 2^23, exact; the width mutant that must REJECT is acc2 at 23 b) (N <= 4096), sign-extended to 32 b on the hold outputs; hold registers are narrow too. Frame words unchanged.
- `comp_in` goes straight into the DAC flop on fs_tick (CL-28); `comp_s` and the s_tick port of `c9_seq` are gone (s_tick stays internal to `c9_fsdiv` for the bit-clock fall).
- WO-60B: `fs_tick` and `s_tick` in `c9_fsdiv` are flops: the terminal-count compare runs one clk ahead against registered constants `tc_fs`/`tc_half` (+18 FF), so `act[9:7]` no longer feeds the compare combinationally. Pin timing is unchanged.

## WO-74 (D85, CL-36): VAPWR-good counter (not yet linted/synthesised: sandbox ssh refused the key, see WO report)
- New input `bias_ok` (2-FF synced in `c9_core.v`, `sbias`), new ports on `sd_adc_c9` and the sim wrapper. `c9_seq` has two sticky counters on `fs_tick`: `pw_ctr` (PW_BITS+1 = 17 b, counts 2^16 fs cycles from the synchronised release) and `b_ctr` (BIAS_BITS+1 = 9 b, counts consecutive `bias_ok_s` high ticks, clears on a low sample). `pwr_ok` = both done flags; `boot <= ~pwr_ok` on every tick, so rst_analog stays 1 and no slot starts until `pwr_ok`.
- Parameters `PW_BITS` (16) and `BIAS_BITS` (8) on `sd_adc_c9` / `c9_seq` let a TB shorten the hold; defaults are the D85 values.
- First-slot timing: the boot tick (slot 0, c = 0) is the first fs_tick after both counters are done: tick max(2^16, J) + 1, i.e. (2^16 + 1)·div clk after release with `bias_ok` high (was `div` clk). During the hold every tick re-latches shadow into active (boot) and keeps inv_pair = 1, so cfg writes made in the hold take effect at slot 0.
- Estimated cost: +26 FF (17 + 9, plus 2 sync) before synthesis; sandbox numbers pending.
- Golden v3.2 impact (not edited): `hold_reset` and every sequence that starts from rst_n release assume slot 0 at `div` clk after release with no `bias_ok`; they need `bias_ok = 1` driven and the slot-0 offset moved to (2^16+1)·div clk (or the TB overrides PW_BITS/BIAS_BITS). Frame tag/status contents at reset are unchanged.
