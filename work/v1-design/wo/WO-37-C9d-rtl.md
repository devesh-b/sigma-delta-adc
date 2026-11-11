# WO-37 (C9d): C9 RTL

Coordinator-written, 2026-11-11. **Tier: code (Sonnet).** Sources:
- SPEC.md §3.7a, §3.8, §3.8a (incl. the C9 port contract and CL-12..26), D45–D48, D66, D67;
- `golden/README.md` + `golden/s6_vectors.json` (v3.1);
- `work/v1-design/C9_VERIF_PLAN.md` (requirements list, DFV requests: fs_tick enable, observable points).

Write the RTL from the SPEC. A separate verification agent (WO-38) builds the testbench in parallel, from the SPEC only. Do not write their testbench, and do not read their files.

## Items
1. `design/c9_digital/rtl/` (Verilog-2005, synthesizable, TT-style top `tt_um_<name>` wrapper kept separate from the core). Blocks:
   - fs divider;
   - fs_tick sequencer (slot = N+2, reset window, chop sequencer);
   - forced y[0] / retime (comparator sampled on the falling edge, DAC flop on the rising edge);
   - CoI accumulators (exclusive acc2, 32-bit);
   - frame + tag;
   - hold / overrun / rd guard (D66);
   - serial config (2-FF sync, shadow / active, pair-boundary latch);
   - registered 16-bit read bus;
   - debug bus;
   - analog control outputs, active-high.
   One clock domain (clk 48 MHz); synchronisers on the async inputs.
2. A minimal smoke test of your own: a yosys synth check plus one iverilog run of one golden vector. That is enough to prove it elaborates. The full verification is WO-38's job.
3. Lint clean (verilator `--lint-only -Wall`) and yosys `synth` clean. Report the gate count.

## Sandbox
- Run inside IIC-OSIC-TOOLS via `~/bin/rta-tt 'scripts/iic "<cmd>"'` (WORKFLOW §4), from a frozen copy `regr/tt/WO-37-<sha>`.
- At most 2 processes. No local tool runs at all.

## Git
Explicit-path commits, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 40 lines with any SPEC ambiguity (do not edit SPEC).
