# WO-100: layout continued, D93 floorplan (MIM over circuits), fix the blocked cells, then the comparator

Coordinator-written, 2026-11-21. **Agent: pd-expert.** Fresh agent. This continues WO-96 (`results/wo96/README.md`, pickup and next-cell plan). Plan: `TAPEOUT_10D.md`. Submission is due by 2026-12-01.

## Decisions (D93)
- **MIM over circuits:** the MIM arrays are stacked over the OTA/C6/C4 circuits (capm on met3/met4; circuits on li/met1/met2; met2/met3 shield).
- **C9 die shrink to ~0.85 utilisation**, handled in WO-101. Plan for about 165×150 µm until it lands, with the macro LEF from WO-101.
- **C4 delay caps become MOS caps** (WO-99 changes the netlist). They do not need MIM area.

## Items
1. **Re-floorplan under D93.** Put the MIM arrays over the analog circuits and give OTA2 a slot (D91 area 5,350–7,450 µm²; OTA2 subckt `design/c2_ota2/ota2.spice`). Add more OTA1-to-macro isolation than 10 µm: a guard ring plus spacing. Report the slot table with % of the tile. If it still does not close, report by how much and stop for a decision.
2. **Fix the WO-96 blockers:**
   - (a) c6_res rpm.1 / urpm.1a: single-segment resistors joined in met1;
   - (b) the c4_sw extraction stop;
   - (c) the LVS harness regex;
   - (d) the 2 nwell.4 errors after the macro is placed.
3. **Finish the cells:** wire the c4_sw TGs; densify the MIM routing; build the stage-1 MIM array (36 units, common centroid).
4. **Comparator layout (C3 rev g):** input-pair matching, symmetric latch, and the keeper/precharge sizes from `design/c3_comp/sizes_draft.py`. DRC (Magic plus KLayout) and LVS against the generator netlist, each shown to fail on a broken copy.
5. **Use the TT precheck DRC deck** where possible, or state which deck you used and how it differs.
6. Update the per-cell status table and the D4–D5 fallback assessment in `results/wo100/README.md`.

## Rules
- Sandbox only, via IIC-OSIC-TOOLS `scripts/iic`. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-100-<sha>`. Run long jobs detached with an EXIT marker. No wait loops and no `pkill -f`.
- No local runs, not even an empty `python3 -`.
- Do not change device sizes.
- Write only `design/layout/` and `results/wo100/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 50 tool calls. Report in ≤ 25 lines.
