# WO-104 (C6): fix the C6 final failures (port check at cold, trim step, boost toggle), finish the WO-99 pool

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. Inputs: `results/wo99/README.md` §6 (8df28c5), `design/c6_bias/c6_final.py`, D73, D85, D89.

## Failures (WO-99)
- **Port check fails at ss/−40 and fs/−40** (precision-critical). The failing part was not separated.
- **Trim max step 5.7–6.1 %** against the 6 % limit (D73). It fails at tt/27, ss/−40 and fs/−40. Cover 1.41 passes.
- **Boost toggle fails at all 9 corners:** 6–15 % off in the 4–10 µs window, against 0.1 %. Not diagnosed: either a slow node or the bench window. Boost is fast mode only, so this comes **after** the precision items.
- The stack3 broken copy does not fail compliance at tt/27.
- job_5 (`tap`) and job_41 (`nosr2`) did not finish, so those broken copies are missing.

## Items, in order
1. **Port check at cold.** Find which port and which row fail, and the mechanism. Fix it with one sizing change and justify it.
2. **Trim step.** Re-size the trim units so the max step is ≤ 6 % with margin, with cover ≥ 1.38 (±19 %) still met. Verify at 9 corners.
3. Rerun the `tap` and `nosr2` broken copies. Make stack3 a real compliance copy at tt.
4. **Boost toggle.** Probe vn/vnc/vn2 and the OTA diode nodes. Say whether it is the bench window or a slow node, and fix the right one. The limit stays 0.1 % within 4 µs.
5. Coordinator ruling: the vscm loaded-shift limit is the 10 mV CM tolerance, not the self-set 2 mV. Re-judge with that.
6. Write `results/wo104/README.md` with the full C6 + C5/C7 + sr2 verdict table and a "ready for review" list.

## Rules
- Sandbox only. Connect with `S=(ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox)` (a zsh array).
- Frozen copy `/home/mempool/regr/tt/WO-104-<sha>`. Use lpool v3 with `PRIO=high`. Wait on markers only.
- No local python. Make one change at a time.
- Write only `design/c6_bias/`, `design/c5c7_ref/` and `results/wo104/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 20 lines.
