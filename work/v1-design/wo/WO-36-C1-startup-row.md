# WO-36 (C1, small): D68 start-up row + close the WO-32 gate B

Coordinator-written, 2026-11-11. **Tier: design (Opus), narrow scope.** Sources: D68, `results/wo32/README.md`, `design/c1_ota1/c1b_tb9.py`, `/home/mempool/regr/tt/WO-32-df4e30d` (gate B running there, read-only).

## Items
1. Implement the D68 start-up row in `c1b_tb9.py` (absolute term added).
2. Add the broken copies: clamp never released, clamp stuck on, clamp to the wrong level (e.g. V_OCM + 50 mV). Each must REJECT. mio must REJECT.
3. Rerun tb9 for 4 corners + mut in a new frozen copy (single-thread `.spiceinit`, ≤ 3 processes).
4. When WO-32's `GB_DONE` exists, read both combines (fs/125 TG nominal, srknee) into `results/wo32/README.md`. Do not wait in a loop: if it is not done, report that.

## Rules
Same as WO-32: sandbox only, no local python, explicit-path commits, no push.

## Budget
At most 20 tool calls. Report in ≤ 30 lines.
