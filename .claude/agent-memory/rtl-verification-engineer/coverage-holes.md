# coverage-holes (C9) — WO-38 state
- No functional-coverage collector yet (plan §7.1 bins): untested, not unreachable.
- No Verilator --coverage run yet.
- acc_clear / cfg_latch / tag_chop not observable at ports (AMB-17): M12 equivalent-mutant waiver path applies.
- N 4096 golden mode vectors only in C9_FULL runs; quick runs replay 40 N 64 vectors + 16 boosttrim + streams.
## WO-40 Verilator merge (seeds 1-3): 68 zero points of 1962, all explained, none untested logic
- hold_acc1[0], hold_acc2[0] (c9_dec/rdbus/core) never toggle: structurally even (N even: acc1 = sum of N +-1;
  acc2 = sum of S_{k-1}, N/2 odd terms) -> unreachable, not a hole. Firmware-visible LSB always 0.
- status[8] tied 0; c_last/div_m1/half_m1 constant bits per code (only codes used); uio_in, ena, uio_oe constant
  (TT pins unused/ignored, CL-20); `_unused` reduction expr.  c9_cfg.v: 0 zero points.
## WO-42: fcov.py bins defined (plan §11.2); unreachable: RDST fr0_ov1, WP e+0..e+3 multi/writeback. No hit data yet.

## cz_spi (D102), 2026-11-24: nothing run. Single-FF sync removal not killable in RTL sim (CDC lint/STA); 3rd capture
attempt unreachable (792-clk frame); SCLK-domain flops have no rst_n (X-init not exercised in Icarus); no GL.
