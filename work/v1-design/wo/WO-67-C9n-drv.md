# WO-67 (C9n): close the remaining DRV violations on the retimed C9 macro

Coordinator-written, 2026-11-13. **Agent: pd-expert.** Fresh agent.

## Inputs
- WO-66 run `/home/mempool/regr/tt/WO-66/e450ae2-r60b/` (read-only).
  - Timing is met at all 12 corners; physical checks are clean.
  - Open: 46 max-fanout violations; 256 max-slew at ss_1v40 plus 44 at max_ss_1v60; 3 max-cap at max_ss_1v60.
- `results/wo66/README.md`, `HARDENING.md`, `flow/config.json` (e450ae2), and the retimed RTL (working tree, identical md5).

## Items
1. **Trace the violations.** Read `checks.rpt` per corner and list the violating nets and their drivers. Check which corners the repair steps actually ran on: `RSZ_CORNERS` / `STA_CORNERS`, `steps/openroad.py:2439`.
2. **Pick one change for this run** and justify it from the trace. Examples:
   - exclude `buf_1` from fanout buffering;
   - a max-fanout or max-slew constraint;
   - a repair-design margin variable.

   Cite the LibreLane variable source inside the container.
3. **Rerun PnR from clean inputs.** Re-check every category:
   - setup and hold at 12 corners;
   - DRV (fanout, slew, cap);
   - DRC (Magic and KLayout), LVS, antenna;
   - area, power, IR drop.

   Compare against WO-66.
4. **Exit:** 0 setup, 0 hold and 0 DRV at every corner, with physical checks clean. If DRVs remain, report what is left and propose the next single change, but do not run it.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS. Use a detached run with an EXIT= marker. No wait loops, and no `pkill -f` over ssh.
- No local runs, including python.
- Write only under `design/c9_digital/flow/`, `HARDENING.md` and `results/wo67/`.
- Commit by explicit path, no trailers, no push. If signing blocks, leave the changes and list the paths.

## Budget
At most 30 tool calls. Report in ≤ 20 lines.
