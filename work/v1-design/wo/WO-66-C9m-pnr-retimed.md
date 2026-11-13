# WO-66 (C9m): PnR rerun on the retimed RTL (D79 second change)

Coordinator-written, 2026-11-13. **Agent: pd-expert.** Fresh agent.

## Inputs
- **RTL:** the working tree's `design/c9_digital/rtl/` (the WO-60B retime of `c9_fsdiv.v`). It is uncommitted because git signing is blocked; frozen on the sandbox at `/home/mempool/regr/tt/WO-60B-e450ae2-dirty`. It is proven cycle-exact by formal (EQ-DIV + EQ-ENV).
- **Flow:** the WO-60A baseline at e450ae2 (`EXTRA_EXCLUDED_CELLS` = `clkdlybuf4s*` + `dlymetal6s*`).
- **Previous results:** `results/wo58b` and `results/wo60a`.

## Items
1. **Rerun PnR from clean inputs:** retimed RTL plus the WO-60A flow. This run has one change only, the RTL.
2. **Re-run every check:**
   - setup and hold at 12 corners;
   - slew, cap and fanout;
   - DRC (Magic and KLayout), LVS, antenna;
   - area and IR drop.
   - Compare against WO-60A.
3. **If ss_100C_1v40 setup and the tt period/2 rule pass, report it.** If slew or fanout still fail, propose (do not run) the single-variable repair-setting change for the next run. If setup still fails, show the new critical path.
4. **Note** where the post-route netlist and SDF are, for the GL/SDF sim.

## Rules
- Sandbox only, via IIC-OSIC-TOOLS (`/foss/designs/regr` mount).
- Launch detached with an `EXIT=` marker. No wait loops, and no `pkill -f` over ssh.
- No local runs. Nothing outward-facing.
- Write only under `design/c9_digital/flow/`, `HARDENING.md` and `results/wo66/`.
- Commit by explicit path, no trailers, no push. If signing blocks, leave the changes and list the paths.

## Budget
At most 30 tool calls. Report in ≤ 25 lines.
