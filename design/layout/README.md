# design/layout (WO-96)
Scripted Magic Tcl layout for the tile. Approach: sky130 `magic::gencell` devices for FETs and resistors (DRC-aware
PCells, matching Paul Thomas's flow), direct-drawn MIM units and arrays (full control of the plate and route
geometry for common centroid), and PDK hvl std cells for the level shifters and logic. Every cell gets fresh-process
Magic DRC, KLayout DRC, ext2spice and netgen LVS against `cells/*_ref.spice`, with a broken copy for each check.
- `frame/floorplan.tcl`: tile floorplan (template DEF, met4 straps, C9 LEF mirrored, slot table and fit check).
- `cells/mim.tcl`, `cells/c6_res.tcl`, `cells/c4_sw.tcl`: generators; `cells/lib.tcl`: helpers.
- `scripts/run.sh <frozen dir>`: everything, on the sandbox via `scripts/iic`; `scripts/area_est.py`: pre-layout estimate.
Status and pickup: `work/v1-design/results/wo96/README.md`.
