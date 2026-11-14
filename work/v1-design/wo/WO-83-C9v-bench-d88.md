# WO-83 (C9v): bench update for D88, Verilator/X-01 fix, regression on baa0706

Coordinator-written, 2026-11-14. **Agent: rtl-verification-engineer.** Fresh agent.

## Inputs
- RTL at **baa0706** (WO-82). The b_ctr update in `c9_seq.v` is now gated by `!pwr_ok`:
  - a low `bias_ok_s` clears it until release;
  - it saturates at done;
  - it freezes after release.
  - 259 FF, 1077 cells.
- SPEC: CL-37 and the §3.8a rst_n paragraph. Decision D88 (AMB-30 restart on drop, AMB-31 fs_clk toggles in the hold).
- WO-75 report: `results/wo75/README.md`, C9_VERIF_PLAN §14, and your agent memory.
- **Open from WO-75:**
  - Verilator rejects `defparam` with a parameter value, so X-01, the Verilator coverage and the soak runs are broken on the `c9_tb.v` bench;
  - F18 at the real 16/8 widths timed out;
  - gate-level only ran at small widths.

## Items
1. Fix the bench parameter mechanism so that both Verilator and Icarus build it, for example with a `-G` / `-pvalue` top override or a generated wrapper. Rerun X-01 at seeds 1–3 and confirm the Verilator coverage builds.
2. **Ref A and the bench, per CL-37.** Before release, the bias run clears on a low sample. Slot 0 = max(2^16, J)+1, with J the last uninterrupted 256-run, as SPEC words it. Golden v3.2 stays the arbiter from slot 0 on (option (a), as in WO-75).
3. **Directed tests:**
   - a drop after a completed run and before pw done (slot 0 is delayed);
   - a drop just before release;
   - a drop after release (no effect);
   - a run of exactly 255 vs 256.
4. **Mutants that must REJECT:**
   - the old sticky-at-first-run behaviour;
   - a b_ctr wrap (no saturation);
   - M66 and M68 re-derived against the new line.
5. **F18:** add the drop-before-release property and its cover. Retry F18 at real widths with a better engine or an induction strengthening; if it is still infeasible, state the bound reached.
6. **Regression through lpool:**
   - full suite, seeds 1–3;
   - C9_FULL;
   - all mutants;
   - formal;
   - R-01 at 20 seeds;
   - X-01;
   - gate-level quick (also at real widths if runtime allows).
7. **RTL comment:** `c9_seq.v` line ~29 still says "sticky done flag". Report it; do not edit RTL.

## Rules
- Sandbox only, via IIC-OSIC-TOOLS. No local runs, not even an empty `python3 -`.
- Never write in `/home/mempool/tt`.
- Do not export OMP_NUM_THREADS before calling lpool. Wait on markers only.
- Never edit RTL; report RTL bugs instead.
- Write only under `design/c9_digital/tb/`, `C9_VERIF_PLAN.md` and `results/wo83/`, plus your agent memory.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
