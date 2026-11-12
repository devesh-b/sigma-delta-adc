# WO-52 (C1): D75: sink L 8, noise row re-base, tb7 op fix, full reruns

Coordinator-written, 2026-11-13. **Tier: design (Opus).**

## Sources
- D71, D75
- `work/v1-design/results/wo43/{README.md,sweep_summary.txt}`
- `design/c1_ota1/*`
- `design/tests/test_c1_netlist.py`
- SPEC rows 85–93 and the change log

## Items
1. Put sink L 8 (candidate c1) into SIZES, keeping the replica/K_N tracking.
2. **Noise row (D75).**
   - Derive the OTA1 thermal limit at the virtual ground from the 1.2 µV direct-path share at 15 SPS. Do the derivation in DESIGN.md.
   - Add a SPEC change-log entry.
   - Gate: the direct path ≤ 1.2 µV, plus the derived v_vg limit.
   - Keep the 250 µV row as info, or replace it; say which.
3. **tb7 op fix.** The int copy still falls back to "transient op" at nearly every corner; the WO-43 nodeset fix did not take.
   - Find out why, for example node-name mismatch, or the nodeset not reaching the subckt.
   - Fix it so op_ok holds at all 9 PVT.
4. **Fix the 2 pre-existing failures in `test_c1_netlist.py`** (dualpath_structure, device_count). Each needs a broken copy that still fails.
5. **Reruns,** as one lpool job file:
   - tb7 at 9 PVT × 2, plus msink and mrg;
   - op/AC at 9 PVT;
   - tb9 at 4 corners plus mut;
   - gate B at fs/125 and ss/−40, 6 parts each, then combine.

   Exit: every row ACCEPTs and every broken copy REJECTs.

## Rules
- Run everything on the sandbox. Use a frozen copy with a single-thread `.spiceinit`. Run in parallel through lpool and wait for POOL_DONE.
- No local python. Write files with the Write tool.
- Do not touch any other block's directory.
- Commit by explicit path, with no trailers and no push.

## Budget
At most 50 tool calls. Report in ≤ 35 lines.
