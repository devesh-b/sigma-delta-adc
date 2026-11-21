# WO-97 (C9): final PnR on the D85/D88 RTL, LVS, floating nets, D86 waiver record, GL/SDF sim

Coordinator-written, 2026-11-21. **Agent: pd-expert.** Fresh agent. Plan: `work/v1-design/TAPEOUT_10D.md`, track E.

## Inputs
- RTL at baa0706 or later: D85 counter, D88 restart on drop. WO-83 bench status: 123 of 124 jobs passed; the last job is rerunning.
- Flow from WO-73 (`results/wo73/README.md`, config 9def89a):
  - heuristic diodes off;
  - CTS clustering 8;
  - post-GRT repair on;
  - GRT_DESIGN_REPAIR_MAX_SLEW_PCT 40.
- D86 is the slew waiver at the ss_100C_1v40 stand-in only.

## Items
1. Add `bias_ok` to `pin_order.cfg`. Use the WO-73 flow unchanged otherwise, and run PnR from clean inputs.
2. **Checks:**
   - setup and hold at 12 corners;
   - DRV (fanout, cap, slew), with the slew judged under D86;
   - Magic and KLayout DRC;
   - LVS, extracted and clean (WO-73 had none);
   - antenna;
   - area and power.
3. **Name the 2 floating nets** (RSZ-0020), and say whether they are expected.
4. **Record the D86 waiver** in `design/c9_digital/HARDENING.md`, with the net list. The book found that it is missing.
5. **GL/SDF simulation:** the WO-83 gate-level quick tests at small widths, plus d_hold01/d_hold05 at real widths if the runtime allows, on the routed netlist with SDF at tt and ss. Use the rtl-verification bench `gl_job.sh`.
6. **Hand-off for WO-96:** the GDS, LEF and pin positions of the macro.
7. Write `results/wo97/README.md`: either a signoff-candidate summary, or what remains.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS `scripts/iic`. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Run detached with an EXIT marker. No wait loops and no `pkill -f`.
- Use lpool v3 `PRIO=high` for the GL sims.
- Write only `design/c9_digital/flow/`, `design/c9_digital/HARDENING.md` and `results/wo97/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 35 tool calls. Report in ≤ 20 lines.
