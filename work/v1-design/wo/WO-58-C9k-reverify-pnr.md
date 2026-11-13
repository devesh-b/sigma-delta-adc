# WO-58 (C9k): re-verify the D77 RTL, then a first full place-and-route of the C9 macro

Coordinator-written, 2026-11-13. Two fresh agents in parallel.

## Part A: re-verification (agent: rtl-verification-engineer)
Run against the RTL at 346995c (D77: acc2 24 b).

1. Full suite at seeds 1–3, plus C9_FULL.
2. All mutants. The width mutants change: acc2 23 b must REJECT; W2 (24 b) is retired as equivalent. Update `mutants.py` to match.
3. R-01 at seeds 1–200 and X-01 at seeds 1–8.
4. SOAK at a larger scale: as many slots as fit in about 2 h of pool time. Report the slot count against the plan's 10⁶.
5. Formal re-prove.
6. Generic gate-level quick suite on the yosys netlist.

## Part B: PnR (agent: pd-expert)
Inputs: `design/c9_digital/flow/` (config, sdc, pin order), `HARDENING.md`, D72, D77 and the macro name `sd_adc_c9`.

1. Fix the config items from WO-47:
   - rename the deprecated `FP_PDN_MULTILAYER`;
   - set DIE_AREA to about 190 × 150 µm, or derive it from the new 223-FF / 929-cell synth.
2. Run one full LibreLane flow on the sandbox inside IIC-OSIC-TOOLS:
   - synth → floorplan → place → CTS → route → signoff STA at tt / ss_100C_1v40 (the 125 °C stand-in, D72) / ff;
   - DRC (magic + klayout), LVS, antenna;
   - no met5, PDN on met4.
3. Report:
   - die area, utilisation, worst setup and hold slack per corner, and the fmax margin at 48 MHz;
   - DRC, LVS and antenna counts;
   - every waiver;
   - the post-route gate-level netlist plus SDF location, for a later GL/SDF sim.

## Rules
- Sandbox only.
- Note: the IIC container cannot mount `/home/mempool/regr`, so run from a frozen copy placed where the container can see it, or from the synced `tt-sd` tree at the pinned commit. State which.
- No local runs.
- Nothing outward-facing.
- Commits by explicit path, no trailers, no push.

## Budget
- Part A: at most 35 tool calls.
- Part B: at most 40 tool calls.
- Each report: ≤ 30 lines.
