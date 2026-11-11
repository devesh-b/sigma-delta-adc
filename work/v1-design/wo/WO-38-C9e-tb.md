# WO-38 (C9e): C9 cocotb testbench (independent)

Coordinator-written, 2026-11-11. **Agent: rtl-verification-engineer.** Builds the bench from `C9_VERIF_PLAN.md` and the SPEC (§3.7a, §3.8, §3.8a incl. CL-12..26, D66, D67) plus golden v3.1. It runs in parallel with the RTL (WO-37) and **does not read the RTL**. The port list is the SPEC §3.8a pin table plus the port contract.

## Items
1. `design/c9_digital/tb/`:
   - Ref A (clk-level reference model written from the SPEC);
   - Ref A vs golden v3.1 agreement test (no RTL needed: run it now);
   - cocotb drivers (comparator BFM, serial config, host read) and checkers;
   - the directed and adversarial tests from the plan;
   - formal property file(s) for sby (on fs_tick).
2. Make the Ref A ↔ golden agreement pass now; report any disagreement as a SPEC or golden issue.
3. Hand-off: a `make` / `run.sh` that runs the whole suite against the RTL top named in the SPEC; run it once WO-37's RTL lands. List the mutants to apply after.

## Sandbox
- IIC-OSIC-TOOLS via `scripts/iic`, frozen copy `regr/tt/WO-38-<sha>`, at most 2 processes.
- No local runs.

## Git
Explicit-path commits, no trailers, no push. You may write files only under `design/c9_digital/tb/` and your agent memory.

## Budget
At most 50 tool calls. Report in ≤ 40 lines.
