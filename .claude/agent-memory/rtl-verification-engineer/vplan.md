# vplan (C9) — requirement IDs: work/v1-design/C9_VERIF_PLAN.md §1 (REQ-C9-*), tests §4, mutants §6
Bench: design/c9_digital/tb (commit 5c57793 + fixes), DUT tt_um_sd_adc_c9 (WO-37, commit 25be205).
| Item | Owner test | Status 2026-11-11 |
|---|---|---|
| Ref A == golden v3.1 (774 vec frames, 344 seq frames, 338 hold, 396 trace rows, 5 cfg_shift, junk raw0+toggle, rd_lag 0 and 1) | test_refa_golden.py | passing; 19/19 Ref A mutants rejected |
| RST-02, BUS-01/05, CFG-04, CL-17 | s01_reset_idle | passing |
| DEC-01..06, Y-01, FRM-01 (golden replay: rst_default, 40 N64 + 16 boosttrim, 4 N4096 streams) | s02, d_dec01, d_dec03 | passing (quick set; C9_FULL not run) |
| SEQ-01..04 trace (396 rows from ports; acc_clear/cfg_latch/tag_chop via Ref A only) | a_seq01_trace_ctl | passing |
| CFG-01/02 CL-18 | d_cfg02_shift | passing (rst_clears only in FULL) |
| CFG-05 CL-14 edge sweep -6..+6 | a_cfg01_edge_sweep | passing vs Ref A (2-FF+edge) |
| FRM-04..06 CL-12/13 rd race -8..+8, rd held | a_frm02_rd_race | passing (Ref A rd_lag 1) |
| FRM-05 overrun | d_frm04_overrun | passing |
| FS-01/02 CL-15/16 | d_fs01_div_codes | passing |
| RST-01/03/04 CL-19 | a_rst01_async_mid | passing |
| BUS-03 debug, dbg toggling | d_bus03_debug | passing |
| INV-02..04 each field | d_inv02_each_field | passing |
| golden sequences via pins | d_cfg05_sequences | see bugs.md / last run |
| BUS-02 CL-21 latency | d_bus02_latency | see last run |
| R-01 random | r01_random (seed 1 only) | see last run |
| formal F01,F02,F03,F05,F06,F08,F09,F10,F16,F17 + 3 covers | formal/c9_props.sby | proven (abc pdr), covers hit; NOT yet mutant-checked |
| mutation M01..M59 on RTL | — | not started |
| functional coverage bins, Verilator coverage, X-01, GL | — | not started |
## WO-40 (2026-11-12, frozen /home/mempool/regr/tt/WO-40-7865218-a, bench commits 6575b78, 6aeea82 + run_cocotb Path fix)
- D70: Ref A rst_lat "d70" = e(1+div); bench requires DUT latency == Ref A exactly. Base run.sh all: agree/lint/yosys/cocotb 16/16/formal PASS.
- Mutation M01-M59+M07b: 60/60 killed in RTL sim (M01 log shows FAIL=1; harness mislabelled ERROR via Path bug). M60/M61 added for F17/F10.
- Formal per-property (abc pdr, one assert per run) on 19 mutants: F01 M07b,M19; F02 M19; F03 M53; F05 M03,M53; F06 M10;
  F08 M03; F09 M15,M53; F16 M45; F10, F17 no plan mutant -> M60/M61. F01 PASSES on M07 (swap at c=1 still inside rst window): F01 weaker than SPEC "swap on cycle 0".
- Verilator coverage seeds 1-3, 16/16 each: 1962 points, 68 zero, all structural (see coverage-holes.md).
- GL: yosys generic netlist (flops as always blocks, gates as assigns) + icarus quick suite 16/16.
- NOT done: functional-bin collector (C9_VERIF_PLAN 7.1), R-01 200 seeds, SOAK, X-01, LibreLane GL/SDF, C9_FULL.
- M60 killed (s01) + F17 FAIL; M61 killed (a_seq01) + F10/F08 FAIL -> every F-property fails on >= 1 mutant. 62/62 mutants killed.
## WO-42 (2026-11-12) — code written, NOT run (sandbox ssh + git signing down: 1Password agent not responding)
- Uncommitted bench edits: tb/fcov.py (7.1 collector + merge), test_c9.py (hooks, VSHARD, R-01 rewritten per 4.7,
  c01..c07 directed bin tests), run_cocotb.py (C9_PLUSARGS), formal F01 (rst_analog rise && fs_clk rise),
  wo42_job.sh + wo42_jobs.txt (33 lpool lines, @FROZEN@ placeholder), README firmware facts, plan §11.
- Pickup: commit those paths, sync, freeze regr/tt/WO-42-<sha>-a, sed @FROZEN@, ssh -f lpool; then `wo42_job.sh merge`.
- Never executed: expect TB bugs in c01-c07 / new r01 first run (placement K_SYNC=3 assumed from Ref A Sync, unverified).
## WO-42 results (2026-11-13; frozen regr/tt/WO-42-f5b26f6-a pool A done, WO-42-36b3642-b pool B done; commits 8f4db5b f5b26f6 36b3642 a429510)
- F01 strengthened: base 10/10 props PASS (pdr); F01 FAIL on M07, M07b, M19 (F02 also FAIL on M19). Closed.
- C9_FULL d_dec01 4 shards + other FULL (d_dec03, d_cfg05 incl seq_wrap, d_cfg02 rst_clears, d_frm04 to slot 258): all PASS.
- R-01 (plan-4.7 version): seeds 1-200 PASS (+ s1,s2 on 36b3642). X-01 Verilator rand-init seeds 1-8: 7/7 tests PASS each.
- SOAK: s2 3000 slots PASS; s1 FAIL = TB-7 (stale host read across a reset), fixed a429510, NOT rerun. SOAK << plan 10^6 slots.
- fcov seeds 1-3 + r01: 230/250 reachable (92 %). All groups 100 % except WP 32/52, because c03 crashed (TB bug, fixed 36b3642)
  and its rerun jobs failed to start (job-file quoting, EXIT=2). Next: rerun c03 seeds 1-3 via wo42_job.sh (add a 'test' kind), soak s1, merge.
## WO-49B results (2026-11-13; D72/D74 RTL 953624e; frozen regr/tt/WO-49B-968bd7a-a + -61ceeb8-b; bench 968bd7a d104ed1 61ceeb8)
- Ref A + BFM on CL-28 (strict capture clk). Golden expectations unchanged (fs-granular, n = c-1). agree PASS 19/19 Ref A mutants.
- lint + yosys PASS; sby formal PASS; per-property base 10/10 PASS; F01 FAIL on M07b, F06 FAIL on M10 (re-anchored).
- fcov s1-3 full suite 23/23 each PASS; c03 s1-3 PASS; SOAK s1 3000 slots PASS (TB-7 closed); C9_FULL 4 shards + other PASS;
  R-01 s4-20 17/17 PASS; X-01 s1-2 7/7 PASS. Merged bins 250/250 reachable (100 %), WP 52/52.
- Mutation 64/65 killed (M01-M61, M07b, M57, M57b, W1); W2 SURVIVED = equivalent (AMB-25). M05 needed re-anchor (rerun in -b).
## WO-58 Part A (2026-11-13; D77 RTL 346995c; frozen regr/tt/WO-58-a166371-a; bench 80bb23e mutants, 0a71ece job file)
- Pool: 100 jobs in tb/wo58_jobs.txt (agree, lint, formal, fml base, 65 mutants, fcov 1-3, GL, fml M07b/M10, C9_FULL 4 shards
  + other, R-01 1-200 in 8 lines, X-01 1-8, SOAK s11-14 x 4000 slots). Box load ~6.5-7.8 (Part B PnR) -> lpool ran 1 job at a time.
- Done early: agree PASS (Ref A 19/19 mutants killed), lint+yosys PASS, sby formal PASS, W2 (acc2 23 b) KILLED by d_dec03_streams.
- State 15:21: 50/100 jobs done, all clean: fml base 10/10 PASS; fcov s1-3 23/23 PASS each; GL (yosys generic) 23/23 PASS
  ("cell instances: 0" is the grep on write_verilog's expanded always/assign form, not an empty netlist);
  mutants 46/46 run so far KILLED (W1, W2 23 b, M01-M38 incl M07b). Not yet run: M39-M61, M57/M57b, fml M07b/M10,
  C9_FULL, R-01 1-200, X-01 1-8, SOAK s11-14 x 4000. Pickup: wait for pool/POOL_DONE, then collect + `wo42_job.sh merge`.
## WO-60B (2026-11-13; retimed c9_fsdiv, working tree on e450ae2; frozen regr/tt/WO-60B-v-1, jobs tb/wo60b_jobs.txt, pool ../../../pool)
- New: tb/formal/eq/ (eq_props.sv, eq_job.sh, c9_fsdiv_e450ae2.v = pre-retime ref). EQ-DIV PASS (pdr, under latch-edge env),
  EQ-ENV PASS on real core; fail evidence: unconstr FAIL, M62 FAIL, M63 FAIL, envmut FAIL; M64 (1 clk staler) PASS = equivalent.
- Full-chip miter: pdr ERR (timeout 40 min), BMC only ~46 steps in 90 min -> full-chip miter not tractable; proof = EQ-DIV + EQ-ENV.
- agree/lint/yosys/sby formal PASS, fml base 10/10 PASS. Sim M62, M63 KILLED (d_fs01). M46/M58 re-anchored to fs_c constants.
- Pool serial (load ~5, 1 slot); at 17:55 job 16/101 (M64 sim, expected SURVIVE -> runs every test). Rest pending.
## WO-75 (D85 / CL-36, RTL df9bded; bench 2e0a43c 6e61895 + job file)
- Option (a): golden v3.2 unchanged; Ref A models the hold (pw_bits/bias_bits; None = no hold for agreement).
- H-01..H-04 = d_hold01_len, d_hold02_bias_late, d_hold03_glitch, d_hold04_cfg_sticky; F18 formal; mutants M65-M70, M67b.
- Smoke on 2e0a43c: s01, d_hold01..04, a_rst01, c06 PASS. Full pool results: see bugs.md / next entry.
- Weakness found while writing: with b sticky once done, lows after b done are no-ops; only J > 2^PW cases kill M66.
- WO-75 results (results/wo75/README.md): all suites PASS; 77 mutants: all killed except M64 (equivalent); M45 needed bench top
  to wrap tt_um (87a05a2). OPEN: Verilator rejects defparam-with-param in tb/hdl/c9_tb.v -> X-01/cov/soak on Verilator broken
  until fixed (e.g. generate two tops or -G on a top that instantiates sd_adc_c9 + a copy of wrapper logic checked by M45).
  fmlreal (F18 16/8) PDR timeout 5400 s.

## WO-83 (2026-11-14): D88/CL-37 rows
- H-05 d_hold05_d88 written, s1 PASS at 4/2 (smoke); 16/8 run, mutant kills (M66/M68/M71-M74), F19 at widths: pending in pool WO-83-9f4bab2/pool.
- F19 (no late slot 0) + drop cover written; F18/F19 PASS at 3/2 PDR.

## cz_spi (D102) — 2026-11-24, written, NOT RUN (user: no sims yet)
- Plan: design/cz/tb/VPLAN_cz_spi.md (REQ-FRM/SNAP/M0/TIM/CDC/ACK/ABT/EN0/EN1/RST, 27 REQs). Bench tb_cz_spi.v (real C9 x2:
  DUT side + lockstep twin without wrapper), run_spi.sh, 16 sed mutants in mutants_spi/. All status = written.
