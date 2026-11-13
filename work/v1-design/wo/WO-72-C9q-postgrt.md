# WO-72 (C9q): post-route design repair (single change)

Coordinator-written, 2026-11-13. **Agent: pd-expert.** Fresh agent.

## Base
WO-71 (fe8b8bf): heuristic diodes off and CTS_SINK_CLUSTERING_SIZE 8.
- Setup and hold met at 12 corners (ss_1v40 +2.777 ns).
- Fanout 0, cap 0, physical clean.
- **Open:** slew, 43/11 pins at ss_1v40. Worst is 1.72 ns against 1.5 ns, from the buf_1 fanout buffers (fanout116/68/57) and `_1110_` nor3b_2.

Inputs:
- `results/wo71/README.md`
- run `/home/mempool/regr/tt/WO-71/fe8b8bf/` (read only)

## Change (one)
- Set `RUN_POST_GRT_DESIGN_REPAIR = true` (classic.py:139). Cite it.
- If this needs related variables (for example post-GRT repair margins), keep the defaults and say so.

## Items
1. Rerun PnR from clean inputs.
2. Re-check every category:
   - setup and hold at 12 corners;
   - DRV (fanout, slew, cap);
   - DRC (Magic and KLayout), LVS, antenna;
   - area, power, IR drop.

   Compare against WO-71.
3. Exit target: 0 setup, 0 hold and 0 DRV at every corner, with physical checks clean.
   - If met, write a short signoff-candidate summary in `results/wo72/`, plus the GL/SDF file paths.
   - If not met, trace what remains and propose the next change. Do not run it.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS (`scripts/iic`).
- Run detached with an EXIT= marker. No wait loops and no `pkill -f` over ssh.
- No local runs.
- Write only under `design/c9_digital/flow/`, `HARDENING.md` and `results/wo72/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 25 tool calls. Report in ≤ 15 lines.
