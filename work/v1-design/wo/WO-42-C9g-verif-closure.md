# WO-42 (C9g): verification closure before hardening

Coordinator-written, 2026-11-12. **Agent: rtl-verification-engineer.** Sources: WO-40 report (`6575b78`, `6aeea82`, `042ae50`), `C9_VERIF_PLAN.md` §6–§7, agent memory (waivers, coverage-holes).

## Items
1. **F01 strengthening:** the swap may change only on the cycle-0 edge of a slot (pin it to the first rst_analog rising edge, or equivalent).
   - It must fail on M07 (and on M07b and M19).
   - Re-prove the other properties.
2. **Functional bins (§7.1):** implement the bin collector and report hit/miss per bin across seeds 1–3. Add directed tests for missed bins.
3. **Randomised:**
   - R-01 at 200 seeds;
   - SOAK-01;
   - X-01 random-init (Icarus 4-state, or Verilator `--x-initial unique`);
   - C9_FULL golden (the N 1024/4096 vectors replayed on the RTL).

   Use `scripts/lpool.sh` (load-adaptive) for the seed sweep.
4. **CDC note:** a static review of the async inputs (cfg_clk, cfg_dat, cfg_ld, rd, addr, dbg, rst_n), recorded in the plan. No tool is required; a structural check with yosys is fine.
5. **Firmware-visible facts:** note in SPEC-adjacent docs, not SPEC, that the acc LSB is always 0 for even N, and that status[8] is tied to 0. Append them to `design/c9_digital/README.md`.

## Rules
- Sandbox only (IIC-OSIC-TOOLS), frozen copies `regr/tt/WO-42-<sha>-*`, lpool for parallel runs.
- No local python. Never edit the RTL; report bugs instead.
- Explicit-path commits, no trailers, no push.

## Budget
At most 50 tool calls. Report in ≤ 40 lines.
