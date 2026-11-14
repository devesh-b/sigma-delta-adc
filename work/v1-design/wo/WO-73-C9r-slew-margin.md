# WO-73 (C9r): D84 PnR slew-margin run (single change)

Coordinator-written, 2026-11-14. **Agent: pd-expert.** Fresh agent.

## Base
WO-72 (8898159), with these settings:
- heuristic diodes off;
- CTS clustering 8;
- post-GRT repair on.

Results in `results/wo72/README.md`. Run: `/home/mempool/regr/tt/WO-72/8898159/` (read only; includes `diag.tcl`).

## Items
1. **Measure** the resizer's estimated slew against the routed (signoff) slew on the worst nets at ss_1v40:
   - `fanout116`;
   - `fanout68`;
   - `fanout57`;
   - `_1110_`.

   Fix `diag.tcl` first (it hit a report_net bug).
2. **Change one setting:** `GRT_DESIGN_REPAIR_MAX_SLEW_PCT` from 10 to 30. Size the value from step 1 if it shows a different number is needed. Cite the source in the container.
3. **Rerun PnR from clean inputs.** Re-check every category: setup and hold at 12 corners, DRV, DRC, LVS, antenna, area and power. Compare against WO-72.
4. **Look into the 2 floating nets** (`timing__drv__floating__nets`). Name them and say whether they are expected (for example unused tie or analog-facing outputs).
5. **Exit:**
   - If DRV reaches 0, write a signoff-candidate summary.
   - If not, report and propose next steps.

   Note: the RTL will change again for D85 (VAPWR counter), so a final PnR follows later. This run fixes the flow settings.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS (`scripts/iic`).
- Run detached with an EXIT= marker. No wait loops, and no `pkill -f` over ssh.
- No local runs.
- Write only under `design/c9_digital/flow/`, `HARDENING.md` and `results/wo73/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 25 tool calls. Report in ≤ 15 lines.
