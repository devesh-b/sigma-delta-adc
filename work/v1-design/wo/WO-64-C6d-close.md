# WO-64 (C6d): close the C6 option (c) design

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Sources
- `work/v1-design/results/wo55/{README.md,summary.txt}` and the WO-55 frozen run `/home/mempool/regr/tt/WO-55-2662364` (read only)
- `design/c6_bias/*`
- D42, D47, D73, D78
- SPEC rows 100–104

## Open failures from the WO-55 full pool
1. **I0 = 1.44–1.46 µA instead of ~1.07 µA.** The R2/R1 re-tune did not land. Find out why, and fix it so I0 meets the C1 port design currents.
2. **Own current 5.7–6.4 µA, against the 6 µA limit.** Bring it under with margin.
3. **TC −3.7 … −4.2 %, against ±3 % over −40…125 °C.** This regressed from WO-45's −2.4/+0.25 %. Find the cause (the skewed amp? the comparator?) and fix it.
4. **sf/27: the DC result is non-physical again** (I 10.2 µA, own 5.7 mA, phys False). Fix the deck's start hint for that corner, or find a real third state. Prove which it is.
5. **Every 125 °C transient fails with SIMFAIL.** Diagnose (op or convergence) and fix the testbench or the circuit.
6. **D78 rows to implement:**
   - start-up = "settled ±1 % before rstb release", with the C9 hold set from the measured worst settle-after-bias_ok;
   - a single final bias_ok rise (comparator hysteresis).
7. **bias_ok asserts at VDD 1.38–1.69 V during the 10 ms ramps.** Add the VAPWR-good condition and say what it is: a supply detector in C6, or a C9 count.

Rerun the full pool through `scripts/lpool.sh`. Source the venv and nix PATH in the launcher, and do not export OMP_NUM_THREADS.

## Exit
- Every nominal row ACCEPTs.
- Every broken copy REJECTs: nosu, early, PTAT-only, trim leg open, un-skewed.
- Report I0, TC, own current and area against SPEC rows 102–104.

## Rules
- Run on the sandbox only, from a frozen copy with a single-thread `.spiceinit`. Wait for POOL_DONE.
- No local python.
- Write only under `design/c6_bias/` and `results/wo64/`.
- Commit by explicit path, no trailers, no push. If signing blocks, leave the changes and list the paths.

## Budget
At most 50 tool calls. Report in ≤ 30 lines. If it cannot be met, stop and report the options.
