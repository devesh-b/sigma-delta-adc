# WO-81 (C3h): D87 bench basis plus the rev f op/on clamp

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent.

## Inputs
- WO-78 report and README: `results/wo78/README.md`. Commits 1f18fa6, b1a7e63, 4c1a9b5, ba68dc2.
- WO-78 pool: `/home/mempool/regr/tt/WO-78-1f18fa6`. **Collect it first:**
  `ls $F/run/pool_logs/POOL_DONE && cat $F/run/collect.log $F/run/t8_devices.txt`
  Copy `collect.log` to `results/wo78/summary.txt` and commit.
- DECISIONS D80, D81, D83, **D87**. SPEC CL-33 and CL-35.

## Items
1. **Bench basis per D87** (in `design/c3_comp/c3_tb.py`). Each change needs a broken copy that still REJECTs.
   - **(a) Supply:** drive an ideal 1.98 V at the max-supply pin.
   - **(b) Edge:** take the strobe/phiC edge from C4's real phase-generator edge rate per corner; read it from `design/c4_sw/` or the WO-70/79 results, and cite the source. Keep the 0.1 ns ideal edge as an info row.
   - **(c) x2 swing:** bound the stimulus by OTA2's real output range plus a margin. C2 is not designed yet, so state the range you assume: x2 peak 1.41 V and the SPEC OTA2 swing rows, with a ~100–200 mV margin. Keep the −0.5 V both-sides step as an info row.
2. **Rev f, a single circuit change:** a clamp or pull-down so op/on cannot sit above VDPWR while the input pair is off. Choose the smallest device that holds S ≤ 1.98 V, and give its size and the reasoning.
3. **Rerun on rev f through lpool:**
   - T8, all st_* rows;
   - T3 offset MC, tt and ss/−40;
   - T5 kick, all corners;
   - T2 decision time.

   Report the change in offset, kick, CM kick and decision time against rev e.
4. **Re-judge the checker copies** `st_chk_sus195`, `st_chk_cap20` and `st_chk_dur01` against a base row that passes. Each must REJECT for its own reason only. Also confirm `st_brk_noclamp` REJECTs.
5. End with a "ready for review" list. Do not run the reviewer yourself.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-81-<sha>`.
- Use lpool. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute out paths.
- Wait on markers only. No pgrep/pkill loops.
- Do not change limits. Write only `design/c3_comp/`, `results/wo78/` and `results/wo81/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
