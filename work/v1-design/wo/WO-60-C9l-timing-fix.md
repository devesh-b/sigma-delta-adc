# WO-60 (C9l): D79 timing fixes, one change per run

Coordinator-written, 2026-11-13. Fresh agents.

## Part A: flow only (agent: pd-expert), now
1. Find the don't-use / exclude variable for the resizer in LibreLane v3.1.0.dev3 and ban `sky130_fd_sc_hd__clkdlybuf*` (and any other delay cells) from data-path buffering. Cite the source of the variable.
2. Rerun PnR from clean inputs: RTL 346995c, flow `a166371`/`3e1e9ea` plus this one change.
3. Re-run every check:
   - setup and hold at 12 corners;
   - slew/cap/fanout;
   - DRC (magic + klayout);
   - LVS;
   - antenna;
   - area.
4. Compare against `results/wo58b`.

Report whether ss_100C_1v40 setup and the tt period/2 rule now pass.

## Part B: RTL (code tier: Sonnet), after WO-58A (re-verify) finishes
1. Register `fs_tick`/`s_tick` one clk early so the fs_div compare is off the critical path. Behaviour at the pins must not change (cycle-exact).
2. Lint and synth.
3. The verification agent then reruns the suite plus mutants on the new RTL.
4. Then a PnR rerun with Part A's flow.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS (the regr/tt mount works as `/foss/designs/regr`).
- No local runs and no local python.
- No `pkill -f` over ssh.
- Commits use explicit paths, no trailers, no push.

## Budget
- Part A: at most 30 tool calls.
- Report in ≤ 25 lines.
