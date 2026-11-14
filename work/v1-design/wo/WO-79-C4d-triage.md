# WO-79 (C4d): triage the WO-70 failures, fix the injection-deck abort, apply the D82 rating

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent.

## Input: WO-70 pool (C4 rev b)
Run: `/home/mempool/regr/tt/WO-70-01fc505/run`, pool `run/pool`, POOL_DONE present. **61 jobs EXIT=0, 28 EXIT=1.**
Known before the run: the injection decks abort with a vinn#branch timestep failure at 20 ns. "Empty netlist" in batch ngspice means a timestep abort (lesson 2).

## Items
1. **Collect.** Run `c4_tb.py report .` in the run dir (on the sandbox, with the env). Fill `results/wo70/README.md`.
2. **Group the 28 EXIT=1 jobs by cause.** For each group, say which it is:
   - a bench/sim artefact (timestep abort, missing data, relative path, op fallback);
   - a REJECT that was expected (broken copy, good);
   - a real design failure.

   Check each data file is non-empty before using its numbers.
3. **Fix the injection-deck abort** at the root: source impedance, ideal-switch edges, a missing DC path, or tmax/rise times. Do not silently loosen ngspice tolerances. If a tolerance change is needed, justify it and show that the result does not move with a tighter setting.
4. **D82:** add the virtual-ground leakage rating check. The 0.25 MHz, N 1024, ≤ 100 °C derate is in SPEC (CL-34). The check needs a broken copy that REJECTs.
5. Rerun the failed and changed decks through lpool. Report every row against the SPEC: charge injection, leakage per D78/D82, Ron, level shifter, phase non-overlap.
6. End with a "ready for review" list. Do not run the reviewer yourself.

## Rules
- Sandbox only. No local python.
- Make a new frozen copy `/home/mempool/regr/tt/WO-79-<sha>`.
- Use lpool. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute out paths.
- Make design changes one at a time, each stated with its reason.
- Write only `design/c4_sw/`, `results/wo70/` and `results/wo79/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines.
