# S5f (WO-14): fast mode with realistic gm boost, V4 margin point

Run: `tier1_tb.py --fast3` on frozen copy `/home/mempool/regr/tt/acc14c-05cbab2`, exit 0, run-health ACCEPT.
- gm ratios: worst corner of `results/gmid_table.md`, pfet_01v8 (D40).
  - OTA1 ×2 current at base gm/Id 10: **1.423**.
  - OTA2 ×1.5 at gm/Id 14: 1.283; at 17: 1.328.
  - OTA2 ×2 at gm/Id 14: 1.513.
  - All worst cases are at ff/−40 °C.
- Deck: 4 MHz; OTA1 base 12.5 V/µs, GBW1 base 10 MHz; OTA2 base 13.5 V/µs. The second pole tracks the boosted GBW (`fp2 ∝ bstgm`).

## V5(i): option A with real gm ratios (INL endpoint, ppm)
| OTA2 boost | GBW2 base | OTA2 base gm/Id | N 256 (≤ 20) | N 1024 (≤ 5) |
|---|---|---|---|---|
| ×1.5 | 15 MHz | 14 | 6.70 PASS | **9.95 FAIL** |
| ×1.5 | 15 MHz | 17 | 8.08 PASS | **10.7 FAIL** |
| ×1.5 | 20 MHz | 14 | 14.4 PASS | **12.5 FAIL** |
| ×1.5 | 20 MHz | 17 | 14.2 PASS | **12.0 FAIL** |
| ×2 | 15 MHz | 14 | 7.75 PASS | **7.57 FAIL** |

**Non-vacuity**
- With `bstgm = bst` (gm ∝ I, the s5e assumption) the result is 3.686 ppm; s5e gave 3.7. The run reproduces it.
- With gm ratio 1.0 the result is 27.2 ppm, which fails as required.

**Reading the result**
- Option A built from the minimum base GBWs (OTA1 10 MHz, OTA2 15 MHz) fails N 1024.
  - Its boosted GBWs are 14.2 MHz (OTA1) and 19.2 MHz (OTA2). Both are below the D39 absolute rows (≥ 20 / ≥ 22.5 MHz).
  - The boosted-OTA1 shortfall applies to every row in the table.
- The deck point that *meets* the D39 rows is the `bstgm = bst` row: 20 / 22.5 MHz boosted, 3.7 ppm, PASS.
  - **So the SPEC rows are sufficient, but the base GBWs must rise.**
  - Bases needed with these ratios: OTA1 ≥ 20/1.42 ≈ 14 MHz (inside the existing 20 MHz design target); OTA2 ≥ 22.5/1.28 ≈ 17.5 MHz at ×1.5, or ≥ 22.5/1.51 ≈ 15 MHz at ×2.
  - These ratios are worst-corner values at the base gm/Id assumed here. A higher base gm/Id changes the ratio. C1 must iterate against the gm/Id table.
- **Open oddity (for review):** INL is not monotonic in GBW2. At N 256 / ×1.5, base 20 MHz gives 14.4 ppm against 6.7 ppm at 15 MHz. The second pole tracks GBW, so phase margin is constant. The suspects are partial cancellation between the stage-1 and stage-2 settling errors, or a deck artefact. Not investigated.

## V4 margin point (REVIEW-S5e m2)
2 MHz, N 4096, OTA1 12.5 V/µs, OTA2 10.8 V/µs (= 13.5/1.25): **INL 0.579 ppm ≤ 1.333, PASS.** This shows the 25 % SR margin on OTA2 directly.
