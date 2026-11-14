# WO-77 (C1): tb7 noise bench and op/AC mutant bench fixes (WO-61 results)

Coordinator-written, 2026-11-14. **Tier: code (Sonnet).** Fresh agent.

## Input: WO-61 run
Run: `/home/mempool/regr/tt/WO-52-bf4a565`, logs in `out/logs61`, summary `out/tb7_summary.txt`.

1. **tb7: all 18 corner × (b/f) rows REJECT on one lint: `'noise op != op'`.** Every row shows `opFalse/True/False`.
   - Thermal fint is 168–242 µV. The direct-path model rows all ACCEPT.
   - Find why the operating point used by the .noise deck differs from the op deck. It could be a different deck, a transient-op fallback, different options, or a comparison tolerance that is too tight.
   - Fix the cause in the bench, not the tolerance, unless the tolerance is provably the bug.
2. **tb7 broken copies are blind (green is not proof):**
   - `mrg`: thermal 561 µV against nominal 154, "NOT REJECTED".
   - `msink` (sink W ×4): "NOT REJECTED (op False)".

   A broken copy that does not REJECT is a finding. Make each one REJECT for the right reason, with its op valid.
3. **op/AC job 11 (mutants mtlo, mthi):** `MUTANT INVALID`, because of the lint `Note: Transient op started/finished`.
   - That lint is meant to catch silent fallback. Here the op converged only through transient op.
   - Make the mutant op converge directly (nodesets or ic from the nominal op), or document why the transient-op result is valid and restrict the lint accordingly.
   - The mutants must then REJECT on their target rows (SR and I_tail ceiling).
4. **Rerun** tb7 at all corners plus its broken copies, and op/AC job 11, through lpool. Report the per-corner thermal noise against the current SPEC rows (D75 / CL-31), and the verdicts.

## Rules
- Sandbox only. No local python.
- Make a new frozen copy `/home/mempool/regr/tt/WO-77-<sha>`.
- Use `scripts/lpool.sh`. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute out paths.
- Do not change the OTA netlist sizing. Bench and checker code only: `design/c1_ota1/c1b_tb7.py`, `c1b_opac.py`, and helpers.
- Write `results/wo77/README.md`. Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 20 lines.
