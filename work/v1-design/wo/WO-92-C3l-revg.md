# WO-92 (C3l): pick rev g from the WO-88 sweep, run the full C3 set, prepare for review

Coordinator-written, 2026-11-15. **Tier: design (Opus).** Fresh agent. This continues WO-88, whose budget ran out.

## Inputs
- `results/wo88/README.md`, "Pickup" steps 1–7. Commits 2a923df, bfc8611, accb2bc.
- runA pool: `/home/mempool/regr/tt/WO-88-2a923df/runA` (15 of 17 OK and 1 failed at 05:50; check POOL_DONE).
- Leak probe output: `/home/mempool/regr/tt/WO-88-bfc8611/runI/st_sw_icur/dpost.txt` (written 01:43).
- Decisions D80, D83, D87, D90 (sustained ≤ 1.981 V). REVIEW-BOOK M11: R0 shares the clk gate with R1, so a narrower R0/R1 is ambiguous.

## Items
Follow WO-88 pickup steps 1–7:
1. **Collect runA.** Explain the failed job.
2. **Name the leak device** from `dpost.txt`.
3. **Choose rev g:** the candidate that gives P ≤ 2.2 V at ff/−40 b, with T5 diff kick ≤ 5 mV, T2band passing, and S ≤ 1.981 V.
   - Report its CM kick into OTA2.
   - If no candidate meets all of these, report the trade-off and stop. Do not change any limit.
4. **Make rev g the default,** and keep rev f as a `revf` mutation for an info row.
5. **Launch pool B,** the full set on the stiff pin at 5 corners: one, cyc, MC (including the sens/plaus decks, which REVIEW-BOOK M2 found missing), st, and every checker and broken copy. Use the repo lpool.
6. **Fill the verdict table.** Every checker copy (sus195, sus1985, cap20, dur01, noclamp, vdd200) must REJECT for its own reason against the passing rev g base.
7. Write the "ready for review" list for sd-adc-design-reviewer.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-92-<sha>`.
- Use the **repo `scripts/lpool.sh`** (global cap). Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- No limit changes. One design change.
- Write only `design/c3_comp/` and `results/wo88/` and `results/wo92/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
