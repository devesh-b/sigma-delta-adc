# WO-61 (C1, small): finish the WO-52 reruns. Fix the op/AC path bug and the tb7 summary crash

Coordinator-written, 2026-11-13. **Tier: code (Sonnet).** Fresh agent.

## Context
WO-52 ran in the frozen copy `/home/mempool/regr/tt/WO-52-bf4a565`. Job lines are in `jobs.txt` / `jobs_rest.txt`; logs are in `out/logs`, `out/logs4` and `out/logs*_failed_noenv`.

Already done:
- Gate B passes: fs/125 at 3.14 ppm and ss/−40 at 0.71 ppm.
- tb9 passes at 4 corners plus mut.
- All tb7 jobs ran (EXIT=0).

## Items
1. **op/AC:** `python design/c1_ota1/c1b_opac.py out/opac <idx>` failed with "no data FileNotFoundError('out/opac/c1b_..._ac.csv not found.')". ngspice runs from a different cwd, so the relative out path breaks.
   - Rerun the 9 jobs (idx 0..8) with an absolute out path, through `/home/mempool/tt-sd/scripts/lpool.sh`.
   - In the launcher, source `/home/mempool/tt-sd/.venv-sbx/bin/activate`, then export `PATH=$HOME/.nix-profile/bin:$PATH`, `PDK_ROOT=/home/mempool/.ciel`, `PDK=sky130A` and `PYTHONPATH=<frozen>`.
   - Do not export OMP_NUM_THREADS.
   - If the tool itself should resolve paths, fix that in `design/c1_ota1/c1b_opac.py` (make the out dir absolute), then commit and sync.
2. **tb7 summary:** `python design/c1_ota1/c1b_tb7.py --summary out/tb7` crashes with `KeyError: 'en_white_nV'` (line ~442).
   - Find which corner or copy lacks the open-loop row. Make the summary report that as a missing-data REJECT for that row instead of crashing.
   - Then produce `out/tb7_summary.txt`.
   - Fix it in `design/c1_ota1/c1b_tb7.py`, commit, and copy the fixed file into the frozen copy. Note that you did this in the README.
3. Write `work/v1-design/results/wo52/README.md` with:
   - the op/AC VERDICT per corner;
   - the tb7 per-corner table (v_vg vs the 390 µV limit, tier-0 direct path, broken copies mrg/msink);
   - tb9;
   - gate B numbers.
   Delete the CSVs afterwards.

## Rules
- Sandbox only.
- No local python. Edit with Edit/Write.
- Never touch `/home/mempool/tt`.
- No pgrep/pkill wait loops over ssh. If something is not done when you check, report the state and the pickup command.
- Commits use explicit paths, no trailers, no push.

## Budget
At most 30 tool calls. Report in ≤ 25 lines.
