# WO-107: layout of the active cells, C4 LVS-clean, then the C3 rev g comparator (no external reuse, D96)

Coordinator-written, 2026-11-21. **Agent: pd-expert.** Fresh agent. This continues WO-100 (`results/wo100/README.md`, next-cell plan). Due D4.

## Items, in order
1. **C4:** tie the level shifter's split VPWR/VGND rails, wire the TGs, and get C4 LVS-clean against the netlist. WO-103 is converting the delay caps to MOS; use its netlist when committed, or leave the delay-cap slots parameterised. DRC 0/0. Broken copies must fail.
2. **C3 rev g comparator:**
   - the input pair as 8 unit fingers in ABBA ABBA order with end dummies;
   - a mirror-symmetric latch row;
   - keeper 0.84/0.15 and precharge 1.0/0.3 per `design/c3_comp/sizes_draft.py`.

   DRC (Magic plus KLayout) 0, and LVS against the `netlist.py` output. Broken copies: a swapped finger and a wrong keeper W.
3. Explain the Magic 512 errors on the placed macro, fix the KLayout control run on the WO-97 GDS, then run the **TT precheck DRC deck** on the frame.
4. Update the cell status table and the D4 assessment.

## Rules
- Sandbox only, via `scripts/iic`. Connect with `S=(ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox)` (a zsh array).
- Frozen copy `/home/mempool/regr/tt/WO-107-<sha>`. Run detached with an EXIT marker.
- No local runs and no local python. Do not change device sizes. **No external cell reuse** (D96).
- Write only `design/layout/` and `results/wo107/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 50 tool calls. Report in ≤ 20 lines.
