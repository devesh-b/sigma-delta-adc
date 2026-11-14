# WO-86 (C3j): collect every C3 pool, name the over-supply injection path, give the kp2 verdict

Coordinator-written, 2026-11-15. **Tier: design (Opus).** Fresh agent. This continues WO-84, whose budget ran out.

## Inputs
- READMEs `results/wo78/`, `results/wo81/` and `results/wo84/`. Decisions D80, D83, D87.
- **Coordinator basis (D87a):** the stiff switched supply pin (`sup="sw"`, 10 Ω ramp then a 1 mΩ switch) replaces the drop subtraction.
- **Pools, all DONE (check POOL_DONE):**
  - `/home/mempool/regr/tt/WO-78-1f18fa6`
  - `/home/mempool/regr/tt/WO-81-fe9e787` (one, mc, cyc rows; its st rows are invalid)
  - `/home/mempool/regr/tt/WO-81-600c547`
  - `/home/mempool/regr/tt/WO-84-d651488`
  - `/home/mempool/regr/tt/WO-84-7e83397`

  Pickup commands are in the READMEs.

## Items
1. **Collect everything.**
   - Write `results/wo78/summary.txt` and the WO-81 and WO-84 tables.
   - Give the rev f vs rev e deltas: offset (T3 MC), kick, CM kick and decision time (T2).
   - Give the kp2 rows.
   - Check each data file is non-empty and each `tend` is reached.
2. **Stiff-supply robustness.** Use the tighter rows (0.1 mΩ switch, reltol 1e-6) if they ran. Does S = 1.98034 V hold?
3. **Name the path** that holds op/on and nb2/ob2 sub-mV above 1.98 V for 100+ ns.
   - Save the device terminal currents (`save @m.<dev>[id]`, `[is]`, `[ib]`) on one st_sw deck; ammeters abort this deck.
   - Say whether the path is physical (e.g. the HV ap/an kicked by x2 leaking through K1/K2 and M3/M4).
4. **kp2 verdict:** does the stronger keeper bring P under 2.2 V? What does it cost in decision time, kick and CM kick?
5. **Checker copies:** sus195, cap20, dur01, st_brk_noclamp and st_brk_vdd200. Each must REJECT for its own reason, judged against a base row that passes. If no base row passes, say so plainly.
6. **Decision input for the user,** if S stays above 1.98 V by under 1 mV on a physical path. Write 2–3 options, each with cost and risk, and a recommendation:
   - a circuit fix (name it);
   - a stated sub-mV tolerance in the D83 sustained rule;
   - other.

   **Do not change any limit.**
7. End with a "ready for review" list.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- New runs only if needed, and at most a few decks, in a new frozen copy `/home/mempool/regr/tt/WO-86-<sha>`.
- Use **the repo's `scripts/lpool.sh` (global cap GMAX 5)**. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- Write only `design/c3_comp/` and `results/wo78/`, `wo81/`, `wo84/`, `wo86/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines.
