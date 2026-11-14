# WO-75 (C9t): bench update for D85 (bias_ok + VAPWR-good counter), full regression

Coordinator-written, 2026-11-14. **Agent: rtl-verification-engineer.** Fresh agent.

## Inputs
- RTL at df9bded (WO-74). Changes:
  - new input `bias_ok`;
  - sticky counters, parameters `PW_BITS` 16 and `BIAS_BITS` 8;
  - slot 0 at tick max(2^16, J)+1;
  - SPEC CL-36 and the rst_n paragraph.
- Earlier changes the bench must keep covering:
  - D72/D77 widths;
  - D74 capture;
  - D79 retime.
- Your bench and agent memory.

## Items
1. Decide how golden v3.2 stays the arbiter, and state why. Choose either:
   - (a) test-only parameter overrides (small `PW_BITS`/`BIAS_BITS`), plus a matching Ref A model with `bias_ok` driven high, and the golden slot-0 offset adjusted in the harness; or
   - (b) a golden v3.3 update through `model/golden.py` on the sandbox: re-pinned sha, subset proof kept.
2. New directed tests for D85, written from SPEC CL-36:
   - full-length 2^16 hold, at least once at real parameters, or by a formal property;
   - `bias_ok` low, high late, and glitching (the count restarts on a low sample);
   - the hold is sticky after release;
   - config writes made during the hold apply at slot 0;
   - the first pair after release is invalid.
3. New mutants, each of which must REJECT:
   - `pw_ctr` one bit short;
   - `b_ctr` not cleared on a low sample;
   - `bias_ok` unsynchronised;
   - the hold not sticky.
4. Formal property: no slot starts and `rst_analog` = 1 until both counts are done.
5. Run on the new RTL, through lpool:
   - the full suite at seeds 1–3, plus C9_FULL;
   - all mutants;
   - formal;
   - R-01 at 20 seeds;
   - X-01;
   - a generic gate-level quick run.

## Rules
- Sandbox only, via IIC-OSIC-TOOLS. Do not export OMP_NUM_THREADS before calling lpool.
- No local runs.
- Never edit the RTL. Report RTL bugs instead.
- Write only under `design/c9_digital/tb/`, `C9_VERIF_PLAN.md`, `model/golden.py` + `golden/` + `model/tests` (if 1b), and your agent memory.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 25 lines.
