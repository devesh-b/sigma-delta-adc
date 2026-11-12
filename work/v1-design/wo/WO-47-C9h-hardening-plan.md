# WO-47 (C9h): hardening plan for the C9 digital block (pd-expert)

Coordinator-written, 2026-11-12, parallel (user). **Agent: pd-expert. Plan first; run only what is listed.** Sources:
- SPEC §3.9 (tt_analog_2x2_3v3 template, met5 forbidden, power on met4, guard rings, keep digital away from integrator 1);
- design/c9_digital/ (RTL, README, the 1174-cell generic synth);
- pthomas learnings (TT/flow section);
- the TT support-tools docs in repos/ (read only).

## Items
1. `design/c9_digital/HARDENING.md`:
   - how a digital block is hardened and placed inside a TT analog 2×2 tile (separate macro vs top-level flow), with evidence from TT docs or reference repos;
   - LibreLane config draft: clock 48 MHz, corners, utilisation, PDN on met4 with no met5, pin placement toward the analog macro;
   - STA corners and the SDF gate-level plan;
   - the analog/digital interface nets (CL-23 port contract) and isolation from integrator 1;
   - info.yaml implications (uses_vapwr / uses_3v3, tied unused outputs);
   - precheck traps (antenna, power labels, tied outputs, pinned tools version).
2. **Feasibility probe on the sandbox:** run LibreLane synthesis only, or a first floorplan if cheap, on the RTL to get the real sky130 cell count and area.
   - Use IIC-OSIC-TOOLS via `scripts/iic`, frozen copy `regr/tt/WO-47-<sha>`. No local runs.
3. No full PnR yet. Do not edit the RTL.

## Rules
Explicit-path commits, no trailers, no push.

## Budget
At most 35 tool calls. Report in ≤ 35 lines.
