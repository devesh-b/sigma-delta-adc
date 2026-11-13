# WO-69 (C9o): turn off heuristic diode insertion (single change)

Coordinator-written, 2026-11-13. **Agent: pd-expert.** Fresh agent.

## Base
- WO-66 state: retimed RTL, flow `e450ae2`.
- WO-67's `buf_1` ban was reverted, because the resizer switched to `dlygate4sd3_1` fanout buffers and ss_1v40 slack fell from +2.58 to +0.17 ns.
- Inputs: `results/wo66/README.md`, `results/wo67/README.md`, and runs `WO-66/e450ae2-r60b` and `WO-67/9413a36-r60b` (read only).

## Change (one)
- `RUN_HEURISTIC_DIODE_INSERTION = false` (the LibreLane default). Cite where it is defined and where it is used.
- Expected effect: fanout violations drop from 46 to about 10 (clock-leaf only), and diode pin loads drop.
- Risk: antenna. Antenna repair stays on, and post-route CheckAntennas must report 0.

## Items
1. Rerun PnR from clean inputs. Re-run every check:
   - setup and hold at 12 corners;
   - DRV (fanout, slew, cap), with diode pins counted separately;
   - DRC (Magic and KLayout), LVS;
   - antenna;
   - area and power.

   Compare against WO-66.
2. If DRV is still open, trace what remains and propose the next single change. Do not run it. Candidate levers:
   - CTS clustering, for the clock-leaf fanout;
   - a repair-design buffer choice, without cell bans;
   - turning post-route repair on.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS. Run detached with an EXIT= marker.
- No wait loops and no `pkill -f` over ssh.
- No local runs.
- Write only under `design/c9_digital/flow/`, `HARDENING.md` and `results/wo69/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 30 tool calls. Report in ≤ 20 lines.
