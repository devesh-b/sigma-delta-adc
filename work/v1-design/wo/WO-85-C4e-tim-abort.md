# WO-85 (C4e): fix the tim-deck HV body-node abort, rerun tim, collect the WO-79 pool

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent. This continues WO-79, whose budget ran out.

## Inputs
- WO-79 README: `results/wo79/README.md` (see its "Pickup" section); also `results/wo70/README.md` §4.
- Commits 139a29d (`soften()`, `drv()`, D82 rating) and a228a8f.
- Pool: `/home/mempool/regr/tt/WO-79-139a29d/run/pool`. At 15:34 IST, jobs 1–4 (tim) all show EXIT=1 with "Timestep too small, timestep 6.25e-23":
  - jobs 1, 3, 4 at `m.xg.xil.x2.msky130_fd_pr__nfet_g5v0d10v5#dbody`, at 40.8 ns and 44.7 ns;
  - job 2 at `m.xg.xls_dec.x18...#sbody`, at 155 ns.

  The rest of the pool (inj, settle, ramp, leak, tight) is queued and still running. The box load is about 11, so it runs one job at a time.
- The `exp/pool1` gear experiment does not appear to exist. Check this.

## Items
1. **Root cause** of the tim abort on the HV (g5v0d10v5) devices' body/junction nodes, inside the level shifter (xil, xls_dec). Use truncated runs as WO-79 did. Candidates:
   - LS input edges still ideal at the HV gate;
   - a floating or undriven HV internal node (no DC path);
   - the trap integrator ringing on the junction diodes (try method=gear).

   Make one change at a time, and do not silently loosen tolerances. If gear is the fix, show that the result does not move with a tighter reltol.
2. **Fix it in the bench,** or in the design if a node really floats (report that as a design finding).
3. **Rerun only the tim jobs,** good and broken copies, in a new frozen copy. Every broken copy must REJECT.
4. **When POOL_DONE exists** in the WO-79 pool:
   - run `c4_tb.py report .`;
   - diff `run_tight` against `run`;
   - fill `results/wo79/README.md`, including every row against the SPEC: injection, leakage (D78/D82 rating and the 20 pA ff/100 row), Ron, level shifter, phase non-overlap;
   - check each data file is non-empty.
5. The ff/100 20 pA row (expected 23.4 pA) is a user decision. Report the confirmed number. Do not loosen it.
6. End with a "ready for review" list.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-85-<sha>`. Do not stop or delete the WO-79 pool.
- Use lpool. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- Write only `design/c4_sw/`, `results/wo79/` and `results/wo85/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
