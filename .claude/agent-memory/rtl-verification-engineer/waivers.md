# waivers (C9)
- Golden sequences whose writes are < 72 clk apart (seq_multiwrite, seq_edge at fs/12) cannot be issued through
  the serial pins at the 3.8a limit cfg_clk <= clk/4; the earlier write is dropped, golden compare skipped for that
  sequence, Ref A compare kept. The exact latch-edge boundary is covered by A-CFG-01 and the Ref A agreement.
- Metastability (2-FF syncs): structural only (M39 static review), not simulated.
- WO-40: functional bins of C9_VERIF_PLAN 7.1 not collected (no collector written); only nchk counters. Open, not waived by user.
