# WO-80 (C6e): WO-64 MISMATCH 18 (125 °C sim failures, fast-ramp rows), then close TC, I0 and current

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent.

## Input: WO-64 run (C6 option (c), two-stage tune)
Run: `/home/mempool/regr/tt/WO-64-e450ae2w/out`, which holds `summary.txt`, `tune.log` and `pool/POOL_DONE`.

- **Tune:**
  - stage 2: ratio 2.45, TC −2.14/+0.17 % (within ±3 %), I27 1.0996 µA at R1 140.9, so R1 → 144.8;
  - the final R1 144.8 has not been re-verified.
- **`VERDICT MISMATCH 18`:**
  - **SIMFAIL** (all metrics None): tran ff/125 none (0.01 and 1e-06), ff/125 nosu 0.01, fs/125 (both), sf/125 0.01, ss/125 1e-06. tt/125 0.01 and ss/125 0.01 have no .json. **Every SIMFAIL is at 125 °C.**
  - **Fast-ramp (1e-06) rows all REJECT** with `dev ≈ 100–114 %`, while `dev@rel ≈ 0.005 %` and `settled True`. That points at the deviation metric being sampled before release, or at a wrong reference: possibly a metric bug, not the circuit.
  - sf/−40 0.01 REJECTs with dev 0 and rises 2. Check the rises rule.
  - Expected REJECTs (nosu, early, nocnt, hold0, hy1) REJECT correctly.

## Items
1. **SIMFAIL at 125 °C.** Open the logs, find the cause (timestep abort, op fail, missing file), and fix it at the root. Lesson 2 applies.
2. **Fast-ramp `dev`.** Decide whether it is a metric bug or real behaviour. If it is the metric, define the deviation over the window the SPEC means (after bias_ok and the D85 hold; see CL-36), fix it, and show that a broken copy (e.g. hold0, early) still REJECTs. If it is real, explain it.
3. **sf/−40 0.01 rises=2:** same question as item 2.
4. **Verify R1 144.8:**
   - TC ±3 % over −40…125 °C at all corners;
   - I0 1.07 µA ±2 % after trim (D-trim ±19 %, calibration code +2);
   - C6 own current ≤ 6 µA;
   - start-up from every corner.
5. **D78 / D85:** check that `bias_ok` behaves as the C9 counter expects:
   - polarity, and the level at VAPWR ramp;
   - no glitch-high before the bias is valid; the hold covers glitches, but report it.
   - Then the Sg logic gating per D78, if it lives in C6.
6. Rerun everything through lpool. Write `results/wo80/README.md` and end with a "ready for review" list. Do not run the reviewer yourself.

## Rules
- Sandbox only. No local python.
- Make a new frozen copy `/home/mempool/regr/tt/WO-80-<sha>`.
- Use lpool. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute out paths.
- Make design changes one at a time, with a reason. A gate is never loosened; that is a coordinator/user question.
- Write only `design/c6_bias/`, `results/wo64/` and `results/wo80/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines.
