# WO-75 results: C9 bench for D85 (bias_ok, VAPWR-good hold), RTL df9bded

Frozen copies: `/home/mempool/regr/tt/WO-75-6e61895-b` (main pool, 101 jobs) and `WO-75-87a05a2-c` (rerun after
bench fixes, 8 jobs). Bench commits 2e0a43c, 6e61895, 87a05a2. Golden v3.2 unchanged (option a, C9_VERIF_PLAN 14).

| Item | Result |
|---|---|
| agree (Ref A vs golden v3.2, Ref A mutants) | PASS (b) |
| lint + yosys check | PASS (b) |
| suite seeds 1-3 (27 tests incl. d_hold01-04, c01-c07, r01) | 27/27 PASS each (b); s1 27/27 PASS again on c |
| C9_FULL (4 vector shards + other) | all PASS (b) |
| d_hold01 at real 16/8 (2^16 + 1 ticks) | PASS (b and c) |
| R-01 seeds 1-20 | 20/20 PASS (b) |
| GL quick (yosys generic netlist, chparam 4/2) | 27/27 PASS (b) |
| formal sby (bmc, prove, cover) | b: FAIL only on the new cover (depth 100 too short for the hold); c (depth 240): PASS |
| formal per-property PDR, base | F01-F18 all PASS (F18 = no slot / rst_analog 1 until both counts done, chparam 3/2) |
| F18 on mutants | FAIL on M65, M66 (and others in pool logs), i.e. live |
| F18 at real 16/8 widths (fmlreal) | no result: PDR killed at 5400 s timeout |
| Mutants | 75/77 killed on b; M45 survived (bench top bypassed the tt_um wrapper, fixed in c: KILLED); M64 survived = known equivalent (WO-60B). New M65, M66, M67, M67b, M68, M69, M70 all KILLED |
| X-01 | b: s1 7/7 PASS, s2 s01 FAIL at edge 1 (TB-10, rand-init flops never saw an rst_n negedge at t = 0; fixed in c). c: Verilator build error, it rejects `defparam` with a parameter value in tb/hdl/c9_tb.v, so X-01 was not rerun |

No RTL bug found. Open: X-01 on the c bench top (needs a Verilator-legal parameter path), F18 at real widths.
Spec ambiguities: AMB-30 (the bias done flag is sticky before pw is done; the bench follows the CL-36 J formula),
AMB-31 (fs_clk toggles during the hold; the bench assumes the divider runs).
