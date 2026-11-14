# WO-83 results: C9 bench for D88 / CL-37, RTL baa0706

Bench commits 9f4bab2 (bench) and the job-file commit after it. Frozen copy `/home/mempool/regr/tt/WO-83-9f4bab2`
(rtl + tb + golden). Golden v3.2 is still the arbiter from slot 0 on (option (a)). Plan text: C9_VERIF_PLAN section 15.

## What changed in the bench
- Verilator / X-01: `c9_tb.v` no longer uses `defparam`. `run_cocotb.py` now writes a copy of the RTL (or mutant)
  `tt_um_sd_adc_c9.v` with `#(.PW_BITS, .BIAS_BITS)` on `u_core` and builds that copy instead. Icarus and Verilator
  both build it.
- Ref A, CL-37: the bias run clears on any low sample until release, counts while high, saturates at 2^B, and is
  frozen after release. `exp_slot0()` is now written straight from the CL-37 wording (J = the first t >= 2^PW whose
  window t-2^B+1..t is all high; slot 0 = J + 1).
- New test d_hold05_d88 has six cases, each with a hand-derived slot-0 tick:
  - a drop after a completed run, before pw is done;
  - a drop on the last hold tick;
  - a drop on the slot-0 tick;
  - bias low after release;
  - a run of exactly 2^B - 1 vs exactly 2^B.
- Mutants:
  - M66 re-derived: no clear on a low sample;
  - M68 re-derived: the gate is removed, so the counter is not frozen after release;
  - M71: the old df9bded line (sticky at the first run);
  - M72: b_ctr wraps instead of saturating;
  - M73: a run of 2^B - 1 is accepted;
  - M74: the gate is on `boot`, i.e. 1 tick late.
- Formal: the F18 monitor now follows CL-37. New F19 checks that slot 0 is not late. New cover: a drop after a
  completed run, then slot 0. Widths are set with `-DF_PW/-DF_B`.

## Smoke (pool_smoke, all EXIT=0)
- The mutants M66, M68, M71, M72, M73 and M74 all build. Each edit matches exactly once.
- X-01 s1 on Verilator: 7/7 PASS. This is the first Verilator build of the c9_tb top since WO-75.
- d_hold05_d88 s1: PASS. d_hold02_bias_late s1: PASS. Both run at 4/2.
- Formal PDR at 3/2: F18 PASS (14 s), F19 PASS (19 s).

## Full regression (pool, 124 jobs): launched 2026-11-14 15:30 at load 10; results pending
Job file `design/c9_digital/tb/wo83_jobs.txt`:
- fmlw 16/8, F18 and F19 (4 h timeout each);
- real d_hold01_len and real d_hold05_d88 (16/8);
- GL at 16/8 (d_hold01 and d_hold05);
- fcov s1-3;
- C9_FULL, 4 shards plus other;
- all 79 mutants;
- fml on base plus 9 hold mutants;
- fmlw ladder 4/2, 6/3, 8/4, 10/5 and 12/6, F18 and F19 each;
- R-01 seeds 1-20;
- X-01 s1-3;
- cov s1;
- GL quick 4/2;
- suite agree, lint and formal.

Pickup (sandbox only):
```
ssh sandbox 'ls /home/mempool/regr/tt/WO-83-9f4bab2/pool/POOL_DONE'          # pool finished?
ssh sandbox 'cd /home/mempool/regr/tt/WO-83-9f4bab2/pool && grep -hE "^(MUT|FML|FMLW|FCOV|FULL|R01|X01|COV|GL|REAL|SUITE|TEST) |^EXIT=[^0]" job_*.log'
ssh sandbox 'cd /home/mempool/regr/tt/WO-83-9f4bab2/pool && grep -h "^MUT" job_*.log | grep -vc KILLED'   # survivors (M64 = known equivalent)
```
Expected:
- the FML lines on base are all PASS, and F18 or F19 FAIL on M66, M71, M72 and M73;
- F18 alone has no reason to catch M74 or M68, because they only act after release;
- the FMLW ladder: the widest width that PASSes is the bound reached at real widths.

## Open items
- RTL comment, not edited (verification never edits RTL): `c9_seq.v` line 29 still says "Bit PW_BITS / BIAS_BITS is
  the sticky done flag (counter freezes)". After D88 the bias bit is not sticky before release: it clears on a low
  sample. It is also not frozen at done; it saturates at done and freezes only after release.
