# S5d tier-1 + S4 refresh (WO-12): results

Written by the coordinator from the logs in `/home/mempool/regr/tt/WO-12/`. The WO-12 coder ran out of budget after the runs had been launched.
- Code: 61022f0, c33c0de, 0633796.
- Runner: `/home/mempool/regr/tt/WO-12/run.sh`.
  - Queue A: `tier1_tb.py --{cm2,drift,nonvac4,xcheck,knees4}`. knees4 is run with `--prev …/acc0911-d3ab346/out_knees3/knees3.json` (28 points reused, 14 new).
  - Queue B: `python3 -m model.studies.s4_corners --procs 2 --out <dir> [--probe | --nonvac]`.
- Every run finished with no traceback.

| Mode | Exit | Verdict |
|---|---|---|
| cm2 | 0 | ACCEPT (adds the vg1 CM ∈ V_icm ± 0.15 V check) |
| drift | 0 | ACCEPT (run health + closed form); both stages reported |
| nonvac4 | 1 | REJECT-as-required |
| xcheck | 0 | ACCEPT |
| knees4 | 0 | run-health ACCEPT |
| s4 probe | 0 | ACCEPT (SPEC-bound gate only) |
| s4 | 0 | ACCEPT, all 4 gates |
| s4 --nonvac | 1 | REJECT, 8/8 broken copies |

`pytest1.log` (EXIT 1) is from an earlier test revision that asserted the disproven R4 explanation. The current test records the finding instead.

## R1: slew knee at the slew INL share (2 ppm / 1.5 = 1.333 ppm), 2 MHz
| OTA | N | INL at SR (V/µs) → ppm | Knee (interp) | Margin |
|---|---|---|---|---|
| OTA1 | 256 | 9: 10.4, 9.5: 3.57, 10: 1.334, 10.5: 0.644, 12: 0.289 | 10.0 | 12 → 20 %, **12.5 → 25 %** |
| OTA1 | 1024 | 9: 8.79, 9.5: 3.15, 10: 1.18, 12: 0.31 | 9.94 | 12 → 21 %, **12.5 → 26 %** |
| OTA2 | 256 | 12: 1.69, 12.5: 1.48, 13.5: 1.155, 15: 0.854 | 12.9 | **13.5 → 5 %**, 25 → 94 % |
| OTA2 | 1024 | 10: 1.27, 12: 0.78, 13.5: 0.60 | 9.85 | 13.5 → 37 %, 25 → 154 % |

- OTA1 12.5 V/µs meets the 25 % margin rule.
- OTA2 13.5 V/µs has only 5 % margin at N 256 against 37 % at N 1024. OTA2 errors fall as 1/N, so at the precision N of 4096 the margin is larger. A 2 MHz N 256 mode would need about 16 V/µs.

## R2: fast-mode option (a), 4 MHz
Setup: OTA1 boosted (base 12.5, giving 25 V/µs); OTA2 not boosted, SR 13.5 V/µs; loaded GBW2 swept. Values are INL in ppm.

| N | GBW2 10 | 15 | 20 | 25 MHz |
|---|---|---|---|---|
| 256 | 182 | 120 | 73.4 | 49.0 |
| 1024 | 56.4 | 40.5 | 28.9 | 21.1 |

- **Option (a) fails.** No GBW2 up to 25 MHz reaches the provisional 5 ppm at N 1024.
- Compare knees3, which used OTA1-only boost with OTA2 at 25 V/µs and 10 MHz: 12.9 ppm. OTA2 slew therefore matters at 4 MHz too. An unboosted OTA2 at 13.5 V/µs is too slow, so R2's "GBW only" diagnosis is incomplete.

## R9: deck vs model INL bias is explained
Adding the k-DAC cap Ck to the stage-2 node loading in the model (`cp_plus_ck`) brings deck/model to **ratio 0.99–1.007 (rel_sym 0.0–0.7 %)** in every xcheck row. Before the change the ratio was 1.18–1.40.
- Cp,vg alone does nothing on these decks: the legacy OTA path has Cp,vg = 0.
- **Consequence:** model-based INL (S3/S4) underestimates by ×1.2–1.4 until the model's default includes Ck loading. The S4 worst INL of 5.2 ppm becomes about 7 ppm, still under the 8 ppm OTA line and the 20 ppm budget. This must be rerun with the corrected default.

## R7: D12 is now discriminated
- With D12: vg1 CM [1.554, 1.728] V, inside 1.65 ± 0.15. Passes.
- Without D12: [0.673, 2.538] V. REJECT.

## R6: drift, both stages (100 pA per side)
| Case | Stage 1 | Stage 2 |
|---|---|---|
| 2 MHz, N 4096 | −43 mV | −102 mV |
| 0.25 MHz, N 1024 | −86 mV | **−204 mV** (FLAG > 0.2 V) |
| 0.25 MHz, N 4096 | **−344 mV** | **−814 mV** |

The "50 mV row" is removed (D37c).

## R4: the S4 sys-on floor
Probe at tt/27/3.3, 2 MHz, dVcm 0.8 V. Values are the sys-on error in µV at ε = 1e-4 / 4e-4 / 8e-4.

| Case | N 256 | N 1024 |
|---|---|---|
| S4 A(v) | 1.05 / 2.35 / 2.09 | 1.23 / 0.14 / 0.53 |
| ideal A | 6.3 / 4.2 / 6.0 | 0.007 / 0.30 / 0.52 |

- **The review's explanation (finite A(v) causes the floor) is not supported.** The ideal-A error is not about zero; at N 256 it is larger.
- The suspected cause is the residue correction `_corr`, which uses x2_final only. This is untested.
- The probe gates only SPEC-derived bounds: ≤ 20 µV at N 256, and ≤ 8 µV at N 4096 (the 100 dB gate). These pass.

## nonvac4
Each broken case REJECTs and its control passes:
- no-D12 CM: vg1 CM out of range;
- OTA1 SR 8 V/µs: 143 ppm (control at 12.5 V/µs: 0.21 ppm);
- 10 nA leakage: stage 2 drifts −5.09 V (control at 100 pA: −50.9 mV).

## S4 refresh
`s4_corners.{md,json}` were refreshed from `WO-12/out_s4`. All 4 gates ACCEPT, with the sys-on column relabelled as a metric floor. `--nonvac` gives 8/8 REJECT.
