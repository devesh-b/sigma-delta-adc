# Acceptance: WO-01 and WO-02 at d6a86b2 (Haiku, 2026-11-07)

- Frozen copy: `/home/mempool/regr/tt/acc-d6a86b2`
- Evidence: `/home/mempool/regr/tt/acc-d6a86b2/out/`
- Result: **11 of 11 rows PASS**

| WO | # | Verdict | Deciding line |
|---|---|---|---|
| 01 | 1 | PASS | `4 passed in 0.05s` |
| 01 | 2 | PASS | broken Cint1 = 2 pF: `2 failed, 2 passed` (test_coefficients_from_spec_3_4, test_agrees_with_model_defaults) |
| 01 | 3 | PASS | `iic: Id=4.679873e-05 expect 4.68e-05 +-1.0% -> ok`, nix same, `ACCEPT` |
| 01 | 4 | PASS | ff: `Id=6.954016e-05 ... -> bad`, `REJECT`, RC = 1 |
| 01 | 5 | PASS | `ACCEPT: TT precheck passed (ok)` |
| 01 | 6 | PASS | `REJECT: TT precheck failed (met5)`; KLayout Checks: forbidden layer met5.drawing |
| 02 | 1 | PASS | `4 passed in 3.26s` |
| 02 | 2 | PASS | `REGRESS_A0_DROP=0`: test_design_point_reproduced FAILED |
| 02 | 3 | PASS | A, A2, B ACCEPT; C REJECT (INL 942 ppm); all 11 theory checks PASS |
| 02 | 4 | PASS | `--vlin 0.5`: option A REJECT (INL 2246 ppm) |
| 02 | 5 | PASS | design report unchanged: 2.51/1.31/0.51/0.26 µV, 71.3 ppm, −459 ppm |

## Caveats
- **S0 scripts hard-code `/home/mempool/regr/tt/WO-01` as W/OUT.** The acceptance run overwrote the coder's `s0_tools.json`, `proj_ok` and `proj_met5` there. The iic wrapper mounts `tt-sd`, not the frozen copy. The fix was sent to WO-01a as item 8.
- **Not a verdict on the gate's strength.** pd-expert found that S0's negative tests are too weak (REVIEW-WO01-pd). WO-01a fixes that, and S0 is re-accepted after it.
- **Option B is correct.** The coordinator checked it against the WO-02 report: c1 = 0.125, c2 = 0.5, k = 0.5.

## Disposition
- **WO-02: ACCEPTED** pending the design review, which is batched with WO-03.
- **WO-01: ACCEPTED as plumbing.** The S0 gate closes after WO-01a and its acceptance.
