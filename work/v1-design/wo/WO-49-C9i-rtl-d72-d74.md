# WO-49 (C9i): RTL changes for D72 + D74, then bench rerun and WO-42 leftovers

Coordinator-written, 2026-11-13.

## Part A: RTL (tier: code, Sonnet)
Sources: D72, D74, SPEC §3.7a/§3.8a (+ CL list), `design/c9_digital/rtl/`, `HARDENING.md`.

1. **Narrow the accumulators (D72):**
   - acc1 to 14 bits and acc2 to 25 bits;
   - sign-extend both to 32 bits on readout, so the frame words do not change.
2. **Comparator capture (D74):**
   - remove `comp_s` (the s_tick flop);
   - capture `comp_in` straight into the DAC flop on fs_tick;
   - keep exactly one flop driving both the DAC and the decimator.
3. **Macro rename:**
   - rename the macro core top to `sd_adc_c9` (no `tt_um_` prefix);
   - keep a thin `tt_um_` wrapper for simulation only.
4. **SPEC change-log entries** for D72 and D74. The D74 entry replaces the CL-23 capture edge. Edit the §3.8a contract text.
5. **Checks:** lint clean and yosys synth clean. Report the cell and FF counts.

## Part B: bench (agent: rtl-verification-engineer)
Run after Part A lands.

1. Align Ref A to D74 (capture timing) and to D72 (widths are internal, so only width mutants are needed).
2. Run the full suite plus the 62 mutants on the new RTL. Add width mutants: acc1 at 13 bits must REJECT, acc2 at 24 bits must REJECT.
3. Close the WO-42 leftovers:
   - c03 CV-WRITE-PHASE bins over seeds 1–3, using a single-test job kind in `wo42_job.sh`;
   - rerun SOAK s1;
   - merge the bins.

## Rules
- Sandbox only, through IIC-OSIC-TOOLS (`scripts/iic`).
- Frozen copies `regr/tt/WO-49-<sha>-*`; parallel runs through lpool.
- No local python.
- Commits by explicit path, no trailers, no push.
- Part B never edits the RTL.

## Budget
- Part A: 30 tool calls.
- Part B: 40 tool calls.
- Report in ≤ 35 lines each.
