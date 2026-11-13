# WO-68 (C3f): latch Vds overstress + T5 per D81, then close C3

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Sources
- `results/wo65/{README.md,summary.txt}`
- WO-65 run `/home/mempool/regr/tt/WO-65-e450ae2-wt` (read only)
- WO-56 run `/home/mempool/regr/tt/WO-56-2e55372/run` (has `st_tt27_a`)
- `design/c3_comp/*`
- D40, D74, D75, D80, D81
- SPEC rows 99, 105–108 (CL-33)

## Items
1. **Diagnose the SR-latch NMOS Sq3/Sb3 Vds of 2.32–2.33 V (oxide class).**
   - The 1.8 V supply caps at 1.98 V, so some node must leave the 0…VDPWR range. Find which node and when: the supply ramp, the x2 −0.5 V step, or clock coupling.
   - Probe the ql/sq/qlb/sb waveforms.
   - Fix it in the circuit and show the fix. Rev b/c show the same issue, so it is not new in rev d.
2. **T5 per D81.**
   - Declare margin by construction: worst case is 2.7 mV even without isolation.
   - Add a checker copy that judges the T5 data at a tight limit (for example 1 mV), to show the row is live.
   - Keep the 40 mV CM kick as a reported number for C2.
3. **Rerun the affected decks** (st, plus anything the fix touches) through lpool.
   - Exit: every nominal row ACCEPTs and every broken or checker copy REJECTs.
   - Then request the sd-adc-design-reviewer pass on rev d (state it in the report).

## Rules
- Run on the sandbox only. Use a frozen copy with a single-thread `.spiceinit`.
- Source the venv and nix PATH in the launcher. Do not export OMP_NUM_THREADS.
- No local python.
- Write only under `design/c3_comp/` and `results/wo68/`.
- Commit by explicit path, with no trailers and no push.

## Budget
At most 35 tool calls. Report in ≤ 20 lines.
