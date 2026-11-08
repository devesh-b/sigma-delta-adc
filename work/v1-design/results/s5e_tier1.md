# S5e (WO-13): model fixes + fast-mode option runs, results

Written by the coordinator from the logs in `/home/mempool/regr/tt/WO-13/`.
- **Coder:** stopped after a 1Password signing failure. 85e9e24 is committed; the rest was committed by the coordinator once signing worked.
- **Runners:**
  - Coder: `tier1_tb.py --fast2`.
  - Coordinator: `rerun.sh` = pytest; s4 + `--nonvac` (`--procs 2`); `s3_budget`; `tier1_tb.py --xcheck` and `--nonvac5`. All with the venv python, PYTHONPATH set, nix ngspice and PDK_ROOT `.ciel`.

| Run | Exit | Verdict |
|---|---|---|
| pytest model + design | 0 | 99 passed |
| fast2 (V4, V5) | 0 | run-health ACCEPT |
| s4 | 0 | ACCEPT, all 4 gates |
| s4 --nonvac | 1 | REJECT, 8/8 |
| s3_budget | 0 | ACCEPT |
| xcheck | 0 | ACCEPT at rel_sym ≤ 5 % (tightened from 35 %) |
| nonvac5 | 1 | REJECT: the no-Ck model fails the gate in every row; the control passes |

## C1 fix (residue frame): S4 sys-on now tests the hypothesis
- Sys-on errors are 3.6e-5 to 5.8e-5 µV, giving **sys-on CMRR ≈ 205 dB** at the worst-offset point. That is the real second-order term.
- The "metric floor" label is gone and the gate applies at all N.
- Sys-off is unchanged: 61.5 dB at 3σ, 62.1 dB at the worst draw.

## M1 / Ck topology default
- xcheck deck/model: every gated row passes at **≤ 5 % rel_sym**, including A60_base_cpvg with `cp_hold1`.
- The no-Ck copy is rejected in all rows (nonvac5).
- The old→new diff is recorded in the commit message:
  - ideal-A runs are bit-identical;
  - gain moves ≤ 2 %;
  - A(v)-limited INL moves +7 % at N 256 and +0.4 % at N 4096.

## V4: OTA2 at N 4096, 2 MHz (OTA1 12.5 V/µs)
| OTA2 SR | INL (endpoint) | Headroom to 1.333 ppm |
|---|---|---|
| 11 V/µs | 0.557 ppm | 2.4× |
| 13.5 V/µs | 0.393 ppm | **3.4×** |

OTA2 13.5 V/µs is confirmed for precision.

## V5(i): 4 MHz, OTA1 boost ×2, OTA2 boost ×1.5 (13.5 → 20.25 V/µs)
Current (review M2 rule): **fast 193 µA, precision 118 µA. Inside D31.**

| OTA2 base GBW (loaded, boosted) | N 256 (target 20 ppm) | N 1024 (target 5 ppm) |
|---|---|---|
| 10 MHz (15) | 30.9 ppm, FAIL | 11.3 ppm, FAIL |
| **15 MHz (22.5)** | **7.8 ppm, PASS** | **3.7 ppm, PASS** |
| 20 MHz (30) | 1.6 ppm, PASS | 1.8 ppm, PASS |

- **This option meets the targets inside 200 µA, provided OTA2's base loaded GBW is ≥ 15 MHz.**
- Caveat: the current rule is SR-based. GBW2 15 MHz at OTA2's SR-sized tail (≈ 9.5 µA) needs gm/Id ≈ 14 (moderate inversion). That is plausible, but C1 must confirm it.

## V5(ii): 3 MHz, no boost. **Explained: OTA1 slew-limited at 3 MHz; option dominated by V5(i) and dropped (D39).**
INL ranges from 110 to 280 ppm across GBW1 {10, 16, 20} x GBW2 {10, 15, 20, 25} MHz.
- Cause (REVIEW-S5e C-M2, REASONED from scaling against deck data): OTA1 at 12.5 V/us and 3 MHz is equivalent to about 7.9 V/us at 2 MHz, which measured 143 ppm. The earlier "suspect deck / phase plan" label was wrong.
- Making 3 MHz work unboosted needs OTA1 SR of about 20 V/us always on (about +36 uA in precision mode: about 154 uA instead of 118 uA), so the option is dominated by V5(i).
- Comparison wording fixed: the 21-56 ppm quoted earlier was the 4 MHz run with the same OTAs *unboosted* (OTA2 at its precision SR, no current boost), not "option (a)" of the fast-mode list (option (a) is the OTA1-only boost).
- The 3 MHz point at OTA1 20 V/us was not run (WO-14 item 7).

## Scope notes (REVIEW-S5e m5, m6)
- **xcheck coverage (m5):** the 5 % rel_sym xcheck gate covers only the legacy OTA at N 256 (`tier1_tb.py` xcheck). The fast-mode and SR results above rest on the v2 OTA path, which has no model cross-check.
- **Sys-on CMRR (m6):** the 205 dB figure is the model's symmetric-pair-mean metric (the real second-order term e^2 f''/2), not a silicon number. A per-point figure (2 a e |u| about 4 nV at u = 1) is about 165-170 dB. Silicon-limited figures: pin-path dR*fs*Cp,top about 116 dB at 50 ohm (R8); tier-1 cm2 deck 137-173 dB. SPEC cites the 100 dB gate and the tier-1 evidence, not 205 dB.

## Other
- `fast_task` hand constants updated: β2 0.55, OTA2 SR 27e6 boosted (V7).
- `s3_budget` and `s4_corners` md/json are refreshed in `results/`.
