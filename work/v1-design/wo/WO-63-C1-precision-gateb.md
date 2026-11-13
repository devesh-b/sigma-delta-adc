# WO-63 (C1): precision-mode gate B at 2 MHz, the missing authoritative gate (D48(1), SPEC row 94)

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Context
Every gate B run so far has been in boost: 4 MHz, limit 5 ppm. SPEC row 94 also requires precision mode: transistor OTA1 in the tier-1 deck, 2 MHz, N 1024 (and N 4096 if feasible), INL ≤ 1.333 ppm, converged at O1/O2. That run has never been done. The only 2 MHz in-loop result on record is the tier-1 macromodel (D44: 0.098 / 0.101 ppm at 12.5 V/µs).

## Items
1. **Extend `design/c1_ota1/c1b_gateb.py`** to run precision mode:
   - base bias (boost 0);
   - fs 2 MHz;
   - matching OTA2 macromodel point: 13.5 V/µs, 10 MHz, β2 0.497;
   - reuse the WO-31 / WO-52 config and the `combine()` broken-copy rule.

   Then:
   - run a smoke first;
   - check the expected runtime: 2 MHz runs are 2× the simulated time per slot.
2. **Corners:** SPEC row 94 lists tt/27 and ss/−40 for V3c, plus fs/125 and ss/125 from C1 history. Run them at N 1024, m 21, O1. Use O2 if O1 ≥ gate/2.
3. **Broken copy:** the precision SR knee copy, about 0.8 × the 10.3 V/µs base floor. It must REJECT (> 1.333 ppm).
4. **Netlist:** use the current C1 netlist from WO-52 (sink L 8, D59–D64, D71/D75).
5. **Runs:** all through `scripts/lpool.sh` (load-adaptive).
   - Source the venv and the nix PATH in the launcher.
   - Do not export OMP_NUM_THREADS.
   - Use absolute out paths.
   - Write the results to `results/wo63/`.

## Rules
- Sandbox only. Use a frozen copy with golden/ and a single-thread `.spiceinit`.
- No local python.
- Commit by explicit path, no trailers, no push. If signing blocks, leave the changes and list the paths.
- No OTA current changes. If the gate fails, stop and report the options.

## Budget
At most 40 tool calls. Report in ≤ 25 lines.
