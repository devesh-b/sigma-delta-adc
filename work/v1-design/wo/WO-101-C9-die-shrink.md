# WO-101 (C9): die shrink to about 0.85 utilisation (D93), single change, every check re-run

Coordinator-written, 2026-11-21. **Agent: pd-expert.** Fresh agent.

## Base
WO-97, commit 6b474df, `results/wo97/README.md`:
- die 190×150, utilisation 0.739;
- setup at the ss_1v40 stand-in +0.753 ns; slew waived there (D92);
- DRC, LVS and antenna clean;
- `bias_ok` on the south edge.

## Items
1. **One change:** a smaller die for a target utilisation of about 0.85, keeping the 150 µm height if the tile floorplan allows (ask WO-100 via the README, or keep the height). Keep the pin order. Cite the config keys.
2. **Re-run every check:**
   - setup and hold at 12 corners;
   - DRV (fanout, cap, slew);
   - Magic and KLayout DRC, LVS and antenna;
   - power and IR drop.
3. **Exit:**
   - If ss_1v40 setup stays ≥ 0 and the real corners are clean, D92 carries over; hand off the new GDS, LEF and pins.
   - If setup goes negative or DRC/LVS breaks, report it and keep 190×150. Do not iterate more than once.
4. Rerun the WO-97 GL/SDF jobs on the new netlist (lpool `PRIO=high`).
5. Write `results/wo101/README.md`.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-101-<sha>`. Run detached with an EXIT marker.
- Write only `design/c9_digital/flow/`, `design/c9_digital/HARDENING.md` and `results/wo101/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 30 tool calls. Report in ≤ 15 lines.
