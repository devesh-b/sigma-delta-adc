# WO-64 (C6d) results: close C6 option (c)

2026-11-13. Status: **deck fixed for all seven WO items; the full pool is running and not finished** (the sandbox is at load 7–9, so lpool gives it 1 slot). No verdicts yet.

- Deck: `design/c6_bias/c6_spot.py`; launcher `design/c6_bias/run_wo64.sh` (`smoke` | `full`).
- Frozen copy: `/home/mempool/regr/tt/WO-64-e450ae2w` (HEAD e450ae2 + the uncommitted WO-64 deck; `.spiceinit` num_threads=1).
  - `out/`: full run (tune stage 1 → stage 2 → 77 jobs).
  - `out_smoke/`, `out_t1/`: smoke (guess ratio 2.2 / R1 165).
  - `exp125/`: 125 °C convergence experiments.
  - `PATCH.txt`: the deck was patched once in the frozen copy (VPRE, item 5) at 4/9 tune-1 points, before any tran job. The tune `dct` decks do not use that line.

## Diagnoses
1. **I0 1.45 µA instead of 1.07 (item 1) and TC −3.7…−4.2 % (item 3) have one cause.** WO-55 `tune.log`: the R2/R1 grid was 3.0–6.6, and the end-point slope is positive at every point (+5.3 % at 3.0, rising). So the zero-TC ratio lies below the grid, and `tune` returned the edge, 3.0.
   - The 2:1 skew adds n·VT·ln 2 (PTAT) to ΔVBE, which moves the zero-TC ratio to ≈ 2.2 (fit I = 0.34 + 3.34/r µA).
   - At r ≈ 2.2 and R1 94 µm, I0 would be ≈ 1.9 µA. So R1 must also scale (≈ ×1.76, ≈ 165 µm).
   - The comparator is not the cause: it loads only gates of the core.
   - Fix: a two-stage tune through lpool. Stage 1: R1 165, r 1.6–2.8. Stage 2: R1 rescaled to I_TGT 1.07 µA, r ±0.1. `tunepick` flags a grid edge.
   - Gates added: tt/27 I0 within ±2 % of 1.07 µA.
   - Resistor length ≈ R1·(1 + 2r) ≈ 890 µm, against 836 µm in the DESIGN area estimate (+≈ 150 µm²).
2. **Own current (item 2):** it scales with I0 (≈ 80 unit-legs plus leakers). At 1.07 µA the estimate is ≈ 4.6 µA, including the 4-unit hysteresis. Gate added: own current ≤ 6 µA at every T.
3. **sf/27 non-physical DC (item 4):** this is a solver artefact, not a third state.
   - WO-55 dci sf/27 lands on 1.4566 µA from both 0 and VDD, with op_phys True.
   - The dct "solution" has V_R1 ≈ 0 and draws 5.7 mA, which is off the rails.
   - Fix: the dct nodeset now comes from a 300 µs transient from all-0 at −40 °C (the sweep start). Gate added: first sweep point within 0.5 % of that transient's current.
   - Broken copy: `oldhint` (the WO-55 static nodeset, sf/27), expected REJECT.
4. **125 °C SIMFAIL (item 5):** a testbench numerics problem.
   - The sim stops at t = 10 ns (`vsm#branch`) from the exact VAPWR = 0 state. This holds with uic or without it, and for gmin 1e-12, abstol 1e-12, reltol 1e-3/1e-4, trap, rshunt 1e9, and a 1 Ω supply resistor (exp125 v0–v8).
   - It runs with the kick chain removed (v10, diagnostic only) and with VAPWR starting at 50 mV (v11).
   - Fix: the ramp starts at 50 mV (`VPRE`), which is below every threshold. Default `C6_TRANFIX=op` (no uic). Smoke ff/125 `nosu` already ran.
5. **D78 (item 6):**
   - The tran gate is now "settled ±1 % before rstb release, and inside ±1 % from release to the end (≥ 20 µs)". Release = final bias_ok rise + H_HOLD (256 fs cycles = 64 µs at 4 MHz).
   - The run reports `hold/settle` = H / (t(±1 %) − t_ok).
   - The single final rise is gated as before. Hysteresis is raised from 1 to 4 VG units (N_HY).
   - Broken copies: `hold0` (release at ok) and `hy1` (WO-55 hysteresis), both expected REJECT.
6. **VAPWR-good (item 7): a C9 count, not a C6 detector.**
   - Rule: rstb stays low until 2^16 fs cycles (16.4 ms at 4 MHz) after rst_n release, AND the bias_ok hold.
   - Why not a C6 detector: it needs a threshold inside [core headroom knee + margin, 3.0 V − margin]. MOS/pnp stacks spread ±0.3 V or more over T, and an I0·R threshold carries xhrpoly's −1470 ppm/K and costs resistor area and current.
   - Cost of the count: there is no brown-out detection, and it assumes VAPWR starts ramping no later than rst_n release (on TT the RP2040 releases rst_n well after board power-up).
   - Slow-ramp tran runs go to 16.6 ms. Broken copy: `nocnt` (10 ms, release = ok + H), expected REJECT. This is the WO-55 failure mode (bias_ok at 1.38–1.69 V).

## Pickup
1. `ssh sandbox 'ls /home/mempool/regr/tt/WO-64-e450ae2w/out/pool/POOL_DONE && cat /home/mempool/regr/tt/WO-64-e450ae2w/out/tune.log /home/mempool/regr/tt/WO-64-e450ae2w/out/summary.txt'`
2. If it is absent: `tail -2 .../out/pool_run/pool.status` (or `out/tune2_run`, `out/tune1_run`).
3. Check `tune.log` for `GRID EDGE`. If it is there, the zero-TC ratio lies outside 1.6–2.8: widen TUNE1 and rerun.
4. Expected:
   - ACCEPT: every `none` row.
   - REJECT: nosu, early, noskew, ptat, trim_open, hy1, hold0, nocnt, oldhint.
   - INFO: dcv.
5. A MISMATCH on `oldhint` or `hy1` means that copy is not broken at the new operating point. Report it; do not drop the gate.
6. Fill SPEC 102–104: I0 / TC / own current from the `dct` rows, area from `Rlen`. Set the C9 hold from `WORST settle after bias_ok`.
