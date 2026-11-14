# WO-78 (C3g): apply D83 to T8, resolve the WO-68 off-expectation rows, prepare for review

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent.

## Input: WO-68 pool (rev e, latch clamp)
Run: `/home/mempool/regr/tt/WO-68-764fd1c/run`, read `run/collect.log`. Result: `SUMMARY REJECT (4 deck rows off expectation)`.

- **T3 offset:** passes. tt `|μ|+3σ` 49.6 mV, ss/−40 49.3 mV, against the 60 mV limit (D75). Broken copy x6 REJECTs.
- **T5 kick:** passes at all corners. Checker copies kick1/rec02 REJECT. `asym10` is info only.
- **T8 stress:** every st_* row REJECTs `over:18`.
  - 1.8 V oxide max 2.26–2.32 V (st_m4_gb), junction 2.37–2.39 V (st_m4_sb).
  - Rows marked (p) were expected to pass.
  - The checker still uses the single-peak rule. **D83 (sustained limit plus an overshoot cap) is not yet implemented** (see DECISIONS.md D80, D83 and SPEC CL-33/CL-35).

## Items
1. **Implement D83 in the T8 checker,** exactly as CL-35 words it:
   - the sustained-level limit and the window that defines "sustained";
   - the overshoot amplitude and duration cap;
   - junction to rating per D80.

   Report, per st_* row and per device, the sustained level, the overshoot peak and the overshoot duration.
2. **Checker copies that must REJECT (D81):**
   - a sustained overstress;
   - an overshoot over the cap;
   - an overshoot longer than the duration cap.

   Reuse or extend `st_chk_*` and `st_brk_*`.
3. **List the 4 rows off expectation and resolve each one.** For each, say whether it is a checker/expectation bug or a design issue. Do not change the design to make an expectation pass without saying so.
4. If any row still fails under D83 as a real design issue, propose the smallest rev f change and run it, keeping to one change at a time.
5. Rerun T8 (all st_*) plus the affected rows through lpool, and update `results/wo68/` or write `results/wo78/`.
6. **Do not run the reviewer yourself.** End with a short "ready for review" list: files, numbers, open items.

## Rules
- Sandbox only. No local python.
- Make a new frozen copy `/home/mempool/regr/tt/WO-78-<sha>`.
- Use lpool. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute out paths.
- Do not loosen any limit beyond what D80/D83 state. Anything stricter or looser goes to the coordinator as a question.
- Write only `design/c3_comp/`, `results/wo78/` and `results/wo68/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines.
