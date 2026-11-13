# WO-71 (C9p): CTS sink clustering ≤ 10 (single change)

Coordinator-written, 2026-11-13. **Agent: pd-expert.** Fresh agent.

## Base
WO-69 (7841d57): heuristic diode insertion off. Status there:
- Setup and hold met at 12 corners; ss_1v40 slack +2.702 ns.
- Fanout: 10 violations, all clkbuf_leaf driving 12–13 sinks against the max_fanout of 10.
- Slew: 43 / 11 pins at ss_1v40, from fanout116, fanout68, fanout57 (buf_1) and `_1110_` (nor3b_2).
- Cap: 0.
- Physical checks clean.

Inputs: `results/wo69/README.md` and run `/home/mempool/regr/tt/WO-69/7841d57/` (read only).

## Change (one)
- Limit CTS sink clustering so that each clock leaf drives at most 10 sinks.
- Find the LibreLane 3.1 variable in the container (`steps/openroad.py` CTS step, e.g. `CTS_SINK_CLUSTERING_SIZE` / `CTS_CLK_MAX_WIRE_LENGTH` / `CTS_MAX_FANOUT`) and cite it.

## Items
1. Rerun PnR from clean inputs.
2. Re-check every category:
   - setup and hold at 12 corners;
   - DRV;
   - DRC (Magic and KLayout);
   - LVS;
   - antenna;
   - area, power and IR drop.

   Compare against WO-69.
3. If slew is still open, propose the next single change: `RUN_POST_GRT_DESIGN_REPAIR = true`. Do not run it.

## Rules
- Sandbox only, inside IIC-OSIC-TOOLS.
- Run detached with an EXIT= marker. No wait loops, and no `pkill -f` over ssh.
- No local runs, including no stray `python3 -`.
- Write only under `design/c9_digital/flow/`, `HARDENING.md` and `results/wo71/`.
- Commit by explicit path, no trailers, no push.

## Budget
At most 25 tool calls. Report in ≤ 15 lines.
