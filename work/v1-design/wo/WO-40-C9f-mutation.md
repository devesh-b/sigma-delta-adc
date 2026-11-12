# WO-40 (C9f): D70 alignment, then RTL mutation + coverage

Coordinator-written, 2026-11-12. **Agent: rtl-verification-engineer.** Sources:
- D66, D67, D70;
- `C9_VERIF_PLAN.md` §6 (M01–M59, M07b) and §7;
- the bench under `design/c9_digital/tb/` (yours);
- agent memory.

## Items
1. **D70:**
   - Update Ref A to the reset latency (2-FF sync, then exactly `div` clk to the first fs_tick).
   - Add the SPEC change-log entry (next free CL number, D70), plus the AMB-18 fix in the SPEC §3.8a debug sentence.
   - The golden `debug_bus.y_changes_on` → rising is a golden-file change. Do it through `model/golden.py` on the sandbox with a re-pinned sha, keeping the v3.1 subset proof. If that is too much, list it for the coordinator instead.
   - Rerun the full quick suite. Exit: 16/16.
2. **Mutation:**
   - Apply M01–M59 + M07b to the RTL, each as a copy in the frozen tree (never edit `design/c9_digital/rtl/` itself).
   - Run the killing test(s) for each mutant and report killed / survived.
   - Every formal property must fail on at least one mutant.
   - Each surviving mutant needs a reason (equivalent, or a test gap) and a fix plan.
3. **Coverage:** Verilator line/toggle coverage on the full suite, plus the functional bins. Seeds 1–3.
4. **Gate-level:** a yosys-synth netlist (generic cells is fine) running the quick suite; or say why not.

## Rules
- Sandbox only (IIC-OSIC-TOOLS via `scripts/iic`), frozen copies `regr/tt/WO-40-<sha>-*`, at most 3 processes.
- No local python.
- Explicit-path commits, no trailers, no push.
- You may edit `design/c9_digital/tb/`, `model/golden.py` + `golden/` + `model/tests/test_golden.py` (D70 golden fix only), SPEC.md (change log + the §3.8a debug sentence only), and your agent memory. Never the RTL.

## Budget
At most 60 tool calls. Report in ≤ 50 lines: killed/survived table, coverage, gate-level, D70 results.
