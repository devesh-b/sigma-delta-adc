# WO-24 handoff, 2026-10-27: the state, the tested fix, and the lean plan to finish

The previous planner's context grew too large and too expensive. The user has
ordered a fresh start: **no more open-ended investigation**. Finish WO-24 cheaply,
with the fix already tested, under a hard time box. Unattended sandbox time is
cheap; agent tokens are not.

## Where things stand

- Spec: `build/wo/WO-24-eqy-rtl-vs-pnr.md`. Its acceptance and soundness wording
  still apply; the plan below replaces its open-ended triage rules.
- Coder commits (not pushed):

  | Commit | Content |
  |---|---|
  | ce54943 | lemma |
  | dd6419d | EQY config |
  | b89ed67 | mutator |
  | bd864cf | FSM nomatch + reset init, awk shim, pdr 600 s |
  | 85853f8 | verdict.py counts the real strategy |

- Read stage: done. Flop accounting is exact: 1286 direct, 5 renames, 8 gold / 16
  gate FSM bits, 184 constants, 2 unused gpio bits.
- Lemma stage: PROVED (k=2): the 184 constants, the 3 FSM invariants, and the
  supporting `ok_pc_aligned`.
- Prove run q1 (sandbox `~/regr/eqy/work/build/eqy/`, verdict in `verdict-q1.txt`),
  155 partitions:
  - 127 proved (51 by sat, 76 by pdr);
  - 6 FAIL;
  - 22 pdr TIMEOUT at 600 s.

## Root causes found and tested (previous planner, `~/regr/eqy/plan-exp2/`)

1. **Gold tie-order bug in the coder's `prove/gold_eqy.ys`, lines 4-8.**
   - What it does: one `cutpoint -undef` over all 189 bits, then
     `setundef -zero @tie0`, then `setundef -one @tie1`.
   - What goes wrong: the misa bits that are constant 1 (misa_reg[0, 8, 12, 20, 30])
     do not end up tied to 1.
   - Fixed script: `~/regr/eqy/plan-exp2/reg2/gold_eqy_fix.ys`. It runs
     `cutpoint -undef @tie1; setundef -one`, then `cutpoint -undef @tie0; setundef -zero`.
2. **Cut-boundary artefacts on incrementer and RF-port nets.** The fix is to
   nomatch these on both sides:
   - `soc.clint_inst.mtime_d*`
   - `soc.cpu.csr_unit.mcycle_d*`
   - `soc.cpu.csr_unit.minstret_d*`
   - `soc.cpu.rf.dIn*`
   - `soc.cpu.rf.w_ena*`
   - `soc.qspi.rd_late*`

   For the c32 pair the coder also showed, by SAT on the real design, that the
   counterexample state is unreachable.

   The tested config is `~/regr/eqy/plan-exp2/reg2/soc.eqy`.
3. **Result with fixes 1 and 2:**
   - `soc.bus.d_addr.2` and `soc.cpu.csr_unit.csr_new.2` are **PROVED by pdr**
     (`reg2/run2.log`); both were FAILs in q1.
   - Not yet rerun under the fix: rf.hit1/hit2, the c32 pair, and the 22 timeouts.

## Lean plan, in order

1. **Planner** (fresh rtl-verification-engineer, at most about 20 tool calls, no
   new experiments). Write a short dated amendment at the top of WO-24 that adopts
   fixes 1 and 2 and this plan. Check whether each nomatch is sound in one line
   (the flops become internal state with a free start, which can only add
   spurious FAILs, never hide a real one). Then stop.
2. **Coder** (Sonnet):
   - Move the fix into `tb/eqy/run.sh` and the soc.eqy template, then commit.
   - Run **q2**: the full prove stage, sat then pdr at 600 s, detached under the
     thermal watchdog. About 65 min, unattended.
   - Hand back with the sid and the STATUS path; don't wait on it.
3. **After q2** (coder, resumed by the coordinator):
   - Any partition still TIMEOUT gets **one** pdr pass at 3600 s, -j 4, unattended.
     No splits.
   - Any remaining FAIL gets one sat trace, read once:
     - If it starts in an unmatched flop with no init, it is a setup artefact;
       record it as such.
     - Otherwise it is a finding: report it and stop.
4. **Mutants** (coder): the 3 mutants, only in proved partitions; all must FAIL.
5. **Verdict:** `EQY PASS`, or `EQY UNPROVEN k of N`, with the open list (the
   name and the last strategy result), plus the soundness sentence.
   - Open partitions are covered by WO-25 (gate-level programs) and by
     river_core on the RTL. Say so; do not chase them further.
6. **Haiku** accepts from the logs.

## Rules (unchanged)

- Sandbox only, under the 80 C thermal watchdog, with resumable stages.
- Never edit `src/`.
- Commits:
  - use explicit paths only;
  - never stage README.md, .claude/, localFiles/ or scripts/sync-to-sandbox.sh;
  - end every message with the `Claude-Session: https://claude.ai/code/session_019AGtNpvpJiU7zQxfhZUJEn` trailer;
  - do not push.
- Never use a bare `make clean`, git stash, or pkill by name.
- Never touch <confidential-dir>/ or localFiles/alphaOneSoC-sky26d.
- After WO-24: WO-25 parts A-C (`build/wo/WO-25-gl-programs-at-the-pins.md`;
  part D was skipped by the user). Then **pause before SPI**.
