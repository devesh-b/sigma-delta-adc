# spec-ambiguities (C9)
SPEC-AMB-01..16: C9_VERIF_PLAN §8; answered by D66/D67 (CL-12..26) except as below.
## Open (WO-38, 2026-11-11)
- AMB-17 Port names of the C9 analog-side contract are not in SPEC (signal names only). Bench resolves by
  candidate lists (comp_in, short_o, order_o, boost_o, trim_o, y_dac in tt_um_sd_adc_c9). No acc_clear/
  cfg_latch/tag_chop ports: those 3 trace fields are only checked through Ref A + frames.
- AMB-18 SPEC §3.8a debug text still says "y changes on the falling edge of the exported bit clock" while
  D67 says debug y = DAC flop, changes on the rising (start) edge; golden `debug_bus.y_changes_on` also says
  falling. D67 claims the SPEC sentence was fixed; it was not. Bench follows D67/CL-23.
- AMB-19 Comparator index: "ybits for cycles 1..N-1, comp_raw0 at cycle 0" (golden README) is in DAC-cycle
  numbering; with CL-23 the decision for y[n] is sampled in fs cycle c = n+1. Bench drives it that way.
- AMB-20 Read bus while rst_n is low: SPEC defines hold/status values during reset but not whether the
  registered bus shows them while rst_n = 0 (DUT reads 0). Logged only; checked after release.
- AMB-21 rd clear latency: CL-12 allows a clear after the synchronised rise; Ref A has rd_lag 0/1 (bench uses
  1 = DUT choice, in the SPEC envelope; golden agreement must hold for both).
- AMB-22 Golden frame-level `status_word` holds overrun (bit 14) at 0 even when hold[t] has overrun 1
  (seq_drop slot 4, seq_rd, seq_boosttrim). Documented convention, but a trap; bench compares hold[t].
- AMB-23 debug uo[3] "qualified by bit_valid and the reset window": Ref A uses the raw free-running clock.
- AMB-24 (WO-42) cfg_ld / rd minimum high/low width not stated (only cfg_clk <= clk/4). Bench uses 2 clk high/low
  for cfg_ld (makes multi/write-back at latch edge +0..+3 unreachable); rd width 1 clk tested as stress.
- AMB-25 (WO-49B) CL-29 says "acc2 24 b must REJECT". Exclusive acc2 max |N(N-1)/2| = 8 386 560 < 2^23 at N 4096,
  so a 24-bit signed acc2 (wrap + sign-extend from bit 23) is exact for every legal stream: W2 is an equivalent
  mutant. acc1 needs 14 b only because all-+1 at N 4096 gives +4096. Coordinator: fix CL-29 wording or accept 24 b.
## WO-75
- AMB-30 (CL-36): is the bias count done flag sticky before pw is done? "counter clears on a low sample" vs
  "J = the tick at which (b) completes" + max(2^16, J). Bench follows the J formula (sticky). Harm: a bias_ok drop
  in the remaining ~16 ms of the pw hold is ignored; slot 0 can start with bias low. Coordinator to confirm.
- AMB-31 (CL-36): fs_clk during the hold. Bench assumes the divider runs (fs_clk toggles from the first tick,
  "first fs_tick is still div clk after release"). SPEC does not say what the analog sees on fs_clk in the hold.

## cz_spi (D102), 2026-11-24 — details in design/cz/tb/VPLAN_cz_spi.md §6
- SA-SPI-1 re-read pulses rd again (every CS_n fall = snapshot = ack); bench default allows if harmless, +STRICT_ONE_ACK fails.
- SA-SPI-2 "same data" on re-read: status[15:14] live; new frame if one loaded in between.
- SA-SPI-3 DRDY pin missing in SPI mode. SA-SPI-4 residual window "about 5 clk" -> bench limit 6 clk from CS_n fall.
- SA-SPI-5 bits after 96 unspecified. SA-SPI-6 reset release with CS_n low unspecified.
