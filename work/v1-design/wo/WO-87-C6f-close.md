# WO-87 (C6f): apply D89, fix the 125 °C fast-ramp SIMFAILs, replace the oldhint copy, close C6 for review

Coordinator-written, 2026-11-15. **Tier: design (Opus).** Fresh agent.

## Inputs
- WO-80 README `results/wo80/README.md`; commits 1153e82, c4f73c2.
- Final summary `/home/mempool/regr/tt/WO-80-1153e82/out/summary.txt`: `VERDICT MISMATCH 16`. All 77 jobs ran with EXIT=0; POOL_DONE was missing at 00:40.
- Decisions D78, D85, D88, **D89**. SPEC CL-36 and CL-37.

## Items
1. **D89 in `c6_spot.py`.**
   - Remove the `rises == 1` gate.
   - New gate: time from the final bias_ok rise to the bias settled ±1 % ≤ a hold-margin limit. Propose the margin, e.g. ≤ 25 % of the 2^16-cycle hold at the fastest fs (4 MHz → 16.4 ms), and justify it.
   - Keep reporting every pulse as info.
   - **Broken copy:** a deck that settles slower than the limit must REJECT. Expected REJECTs (nosu, early, nocnt, hold0, hy1) must still REJECT, each for a valid reason under the new gate; re-derive any whose reason was the rises rule.
2. **SIMFAIL at 125 °C on the fast ramp (1e-06):** ff (none, early, nosu), fs, sf and tt.
   - The WO-80 gmin fix covered the slow decks only.
   - Find the cause (log the abort node/time) and fix it in the bench, one change at a time.
   - Show that a tighter setting does not move the result.
3. **dct_sf_27_3_oldhint** now ACCEPTs, so it is a blind broken copy. Build a nodeset/hint that really lands on the wrong equilibrium and REJECTs, or show why no such wrong equilibrium exists. If none exists, the copy is retired with that argument, reviewed.
4. **SPEC:** add a CL-38 change-log entry for D89, replacing the start-up row wording. Edit only that row and the change log.
5. **Rerun** the changed rows and copies through the repo lpool (global cap). Write `results/wo87/README.md` with a full verdict table. Target: no MISMATCH.
6. End with a "ready for review" list: files, numbers, open items.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-87-<sha>`.
- Use the **repo `scripts/lpool.sh`** (global GMAX cap). Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- Never loosen any other gate.
- Write only `design/c6_bias/`, `SPEC.md` (CL-38 and the row), and `results/wo80/` and `results/wo87/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
