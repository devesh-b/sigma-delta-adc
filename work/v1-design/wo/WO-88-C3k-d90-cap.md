# WO-88 (C3k): apply D90, name the leak path, fix the ff/−40 precharge-edge cap, close C3 for review

Coordinator-written, 2026-11-15. **Tier: design (Opus).** Fresh agent.

## Inputs
- WO-86 README `results/wo86/README.md` (tables, the +0.344 mV result, the kp2 verdict, item 6); commits 7d9e174, 67e104b.
- Probe deck `/home/mempool/regr/tt/WO-86-7d9e174/run/st_sw_icur`: its `write` failed with "no writable vector found" because of the device-current vector names.
- Decisions D80, D83, D87, **D90**. The basis is the stiff switched pin.

## Items
1. **D90 in `c3_tb.py`.**
   - The sustained limb and the duration-threshold limb use 1.981 V (1.98 V + 1 mV).
   - The new checker copy `st_chk_sus1985` (a judged S of 1.985 V) must REJECT.
   - Fix the `why[:3]` truncation at c3_tb.py:757 so all reasons are shown.
2. **Name the leak path,** for the record (D90).
   - Run a 10 ns smoke with `display` to get the real ngspice device-current vector names.
   - Rerun one st_sw deck saving `[id]`, `[is]` and `[ib]` (about 12 min).
   - Name the device and mechanism.
3. **Cap limb, P ≤ 2.2 V for < 1 ns at the precharge edge.**
   - Results: rev f 2.224 V; kp2 2.1792 V at tt/27 but **2.2062 V at ff/−40 b**.
   - Choose one change and justify it: a slower precharge edge on top of kp2, or something else.
   - Report its effect on T2 (decision time), T5 (diff kick against 5 mV, and CM kick into OTA2) and T3 offset.
   - Re-run all st_* corners.
4. **Checker copies, judged against a base row that now passes:** sus195 (now relative to 1.981), cap20, dur01, sus1985, st_brk_noclamp and st_brk_vdd200. Each must REJECT for its own reason. Missing cyc rows for rev f: run them.
5. **SPEC:** add a CL-39 change-log entry for D90, updating the D83 row wording.
6. Write `results/wo88/README.md` with the full C3 verdict table: T2, T3, T5, T8 and the info rows. Target: everything ACCEPT and every copy REJECT. End with a "ready for review" list for the sd-adc-design-reviewer.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-88-<sha>`.
- Use the **repo `scripts/lpool.sh`** (global cap). Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- No limit changes beyond D90. Make design changes one at a time.
- Write only `design/c3_comp/`, `SPEC.md` (CL-39 and the D83 row), and `results/wo86/` and `results/wo88/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
