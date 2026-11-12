# WO-39 (C1, small): D69 clamp broken copies in the tb9 event deck

Coordinator-written, 2026-11-12. **Tier: design (Opus), narrow scope.** Sources: D68, D69, `results/wo36/README.md`, `design/c1_ota1/c1b_tb9.py`, `netlist.py`.

## Items
1. Run mcnr (rst_never) and mcst (clamp_stuck) as **event-deck copies**: diff step, CM step, reset events, plus the CM-to-DM twins as needed. They must REJECT on a differential row (diff-step settling, or DM collapse).
2. Drop mclv. Record in DESIGN.md and results/wo36 the evidence that it is harmless by design: released at 2 T, then CMFB-corrected.
3. Rerun tb9 for 4 corners + mut in a new frozen copy (single-thread `.spiceinit`, ≤ 3 processes).
   - Exit: nominal ACCEPT;
   - mio, mcc4, masy, mcnr and mcst each REJECT on their intended row.

## Rules
As in WO-36: sandbox only, no local python, explicit-path commits, no push, markers, no wait loops.

## Budget
At most 20 tool calls. Report in ≤ 25 lines.
