# WO-96: analog layout, tile floorplan and the first cells (agent-generated)

Coordinator-written, 2026-11-21. **Agent: pd-expert.** Fresh agent. Plan: `work/v1-design/TAPEOUT_10D.md`, track D. **User decision:** agents attempt all of the layout. The submission is due by 2026-12-01.

## Inputs
- TT analog 2×2 template `tt_analog_2x2_3v3.def`: the current TT tools copy is 319.24 × 225.76 µm. The reference flow is the Paul Thomas repo `repos/sd-analog/ttsky-sigma-delta/` (`tt_frame/build_frame.tcl`, `export.tcl`, `magic_init_project.tcl`, `info.yaml`, Makefile).
- The C9 hardened macro: `design/c9_digital/flow/`, die 190 × 150 µm. Final PnR comes from WO-97.
- The block netlists (Python generators; xschem from WO-94 later); the area budget is in DESIGN_BOOK V.4 and the Proposal summary.

## Items
1. **Floorplan the tile in Magic** (scripted Tcl, reproducible):
   - TT pins: ua[0..7] as used by SPEC (ua2/ua3 reference), the digital pins, VAPWR, VDPWR, VGND;
   - the power straps;
   - the C9 macro placement;
   - the MIM cap array areas (Cs, Cint1, Cint2, DAC);
   - a slot for each analog block, with guard rings and the digital/analog separation.

   Report the area use per block and the total against the tile. Flag the blocks that do not fit.
2. **Cell-generation approach.** Pick a scripted generator for sky130 analog cells (Magic Tcl with sky130 device generators / `sky130::` procs, or a Python PCell flow available in IIC-OSIC-TOOLS). Justify it. Common-centroid / interdigitated matching for the input pairs and mirrors, and dummies.
3. **First cells, simplest first:**
   - (a) a MIM cap unit plus an array (common centroid for Cs vs Cint ratios);
   - (b) the C4 switches/TGs plus the level shifters;
   - (c) the C6 bias resistor array.

   Each must pass Magic DRC and KLayout DRC (sky130 decks), plus netgen LVS against its block netlist.
4. **A per-cell status table** (area, DRC, LVS) and a day-by-day plan for the rest: comparator, OTA1, OTA2, then top routing. Name the risks.
5. Write `results/wo96/README.md` and `design/layout/`.

## Rules
- Sandbox only, via IIC-OSIC-TOOLS `scripts/iic`. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`; the container sees `/home/mempool/regr/tt` as `/foss/designs/regr`.
- No local runs.
- Do not change device sizes. Report layout-driven needs instead.
- Never touch the public TT submission repo.
- Write only `design/layout/` and `results/wo96/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 50 tool calls. Report in ≤ 25 lines, with the pickup and next-cell plan in the README.
