# S3 A/B: what moved the S3 numbers in a8449b4 (REVIEW-S5e m1)

Same current `s3_budget.py` (af85d1e rows included), run against `model/iadc.py` from a3ea4eb^ (= 85e9e24: C1 frame fix, no Ck) and from a3ea4eb (Ck default + cp_hold). Copies: `/home/mempool/regr/tt/acc14-cb14f34/ab/{pre,post}`.

| Quantity | pre (a3ea4eb^) | post (a3ea4eb) | Move |
|---|---|---|---|
| OTA gain+swing INL row (A0 80, drop 0.9) | 3.25 ppm | 3.27 ppm | +0.6 % |
| A0 75 / 0.9 INL | 5.78 | 5.81 | +0.5 % |
| A0 70 / 0.9 INL | 10.3 | 10.3 | 0 |
| finite-A0 gain row | 62.0 ppm | 62.1 ppm | +0.2 % |
| Joint run INL | 2.03 ppm | 2.03 ppm | 0 |

**Conclusion**
- The Ck fix moves S3 by ≤ 0.6 %, as expected (at N 4096 the stage-2 leak is small).
- The 3.41 → 2.03 ppm joint INL and the 3.08e3 → 92 ppm gain moves in a8449b4 come from the script changes since d3fdf8b (af85d1e: new k/c1, reference u³ and reset-window rows) together with the C1 residue-frame fix (85e9e24, present in both A and B). They do not come from Ck.
- The direction is consistent: the C1 fix removed the frame error that inflated the residue-corrected INL and gain.
