# S5h (WO-16 items 3-4): convergence ladder, knees, V4, A', fp2 window

Source: sandbox `/home/mempool/regr/tt/WO-16-run-6a96cb3` (47 jobs + 2 extras, all rc 0 except `r6_T4`, see below). Numbers are read from `out/<name>/point.json` (`inl_ep_ppm`, endpoint, ppm FSR) and `xcheck.json`; nothing estimated unless marked HAND or EXTRAP. Options: gear unless stated; O0 = reltol 1e-3, tmax 10 ns, chgtol 1e-14, trtol 7; O1 = 1e-4, 5 ns, 1e-15, 7; O2 = 1e-5, 2.5 ns, 1e-15, trtol 1. O1/O2 also cap tmax at tau_cl/10, which is **1.895 ns** on the r1 deck (`cfg.tmax`), below both 5 and 2.5 ns.
Rule (`TB.converge_verdict`): converged iff |INL(O2)-INL(O1)| <= max(10 % INL(O2), 0.1 (gate - INL(O2))); verdict INL(O2) (1 + |d|/INL(O2)) <= gate.
Status: 4 of 4 items done except T4 (pending rerun `regr/tt/WO-16-t4-677b39f`).

## 1. Ladder (r1): s5f x1.5 row, 4 MHz, N 256, GBW 10/15 MHz, SR 12.5/13.5, 21 points
| job | what moves | reltol | cap on tmax (cfg) | INL ep ppm | INL bf ppm |
|---|---|---|---|---|---|
| r1_O0 | nothing | 1e-3 | 10 ns | **6.686** | 5.19 |
| r1_rel_O1 | reltol only | 1e-4 | 10 ns | 17.06 | 14.72 |
| r1_rel_O2 | reltol only | 1e-5 | 10 ns | 18.77 | 16.33 |
| r1_tmax_O1 | tmax only | 1e-3 | 1.895 ns (floor) | 16.94 | 14.75 |
| r1_tmax_O2 | tmax only | 1e-3 | 1.895 ns (floor) | 16.94 | 14.75 |
| r1_full_O1 | both | 1e-4 | 1.895 ns | 17.28 | 14.90 |
| r1_full_O2 | both | 1e-5 | 1.895 ns | **18.77** | 16.34 |
| r1_trap_O1 | trap, O1 | 1e-4 | 1.895 ns | 18.59 | 16.18 |
| r1_gear_O1 | gear, O1 | 1e-4 | 1.895 ns | 17.28 | 14.90 |

- **Which knob moves INL:** each of the two moves it alone, from 6.69 to about 17. Reltol 1e-3 -> 1e-4 gives +10.4 ppm with tmax at 10 ns; the tmax cap (here the tau floor, 10 ns -> 1.895 ns) gives +10.3 ppm at reltol 1e-3. The two do not add: together they give 17.28 (O1). The step to O2 then adds +1.5 ppm, all through reltol (rel_O1 -> rel_O2 +1.7; full_O1 -> full_O2 +1.5).
- `r1_tmax_O1` and `r1_tmax_O2` are bit-identical (16.936...), because the 1.895 ns floor, not the 5 / 2.5 ns option, sets the cap at both levels. So the tmax half of the ladder has converged by O1 on this deck.
- O0 is unconverged on this row (6.69 vs 18.77 at O2): its signed INL is jagged noise, while O1/O2 give a smooth odd S-curve, and the gain error doubles. Across rows the O0 error has either sign (high-INL 4 MHz rows rise at O2, low-INL 2 MHz rows fall), so O0 is not systematically optimistic (REVIEW-S5h H-m1). It matches s5f (6.70) and the s5g "tight" value (18.61) within 1 %.
- trap vs gear at O1: 18.59 vs 17.28 (trap +7.6 %). The O2 gear value (18.77) is above both, so method is not the dominant uncertainty, but the 7.6 % gap is of the same order as the O1->O2 step (8.6 %).
- Rule on this row, gate 20 (N 256 fast): d = 1.494, allowance 1.877 -> converged; verdict **20.27 ppm > 20, FAIL by 1.4 %**. This is the s5f x1.5 15 MHz base-GBW row, a characterisation row; the SPEC evidence row is the D39 boosted point (section 5), which passes.

## 2. Convergence verdicts (O1/O2 pairs)
| row | gate | INL O1 | INL O2 | d | allowed | converged | verdict | passes |
|---|---|---|---|---|---|---|---|---|
| r1 N256 s5f x1.5 15 MHz | 20 | 17.28 | 18.77 | 1.494 | 1.877 | yes | 20.27 | **no** |
| r2 N1024 SR2 12 (2 MHz) | 1.333 | 0.4523 | 0.4434 | 0.0089 | 0.0890 | yes | 0.452 | yes |
| r2 N1024 SR2 13.5 | 1.333 | 0.2595 | 0.2529 | 0.0066 | 0.108 | yes | 0.260 | yes |
| r2 N1024 SR2 15 | 1.333 | 0.1457 | 0.1369 | 0.0087 | 0.120 | yes | 0.146 | yes |
| D39 control (fp2 x3/x3), N1024 4 MHz | 5 | 3.292 | 3.363 | 0.071 | 0.336 | yes | 3.434 | yes |
| fp2 OTA1 x30 | 5 (informational) | 28.28 | 28.52 | 0.24 | 2.85 | yes | 28.76 | no |
| fp2 OTA2 x30 | 5 | 4.737 | 4.785 | 0.048 | 0.479 | yes | 4.833 | yes (3.3 % margin) |
| fp2 OTA2 x1.5 | 5 | 1.381 | 1.425 | 0.044 | 0.358 | yes | 1.469 | yes |

Unpaired (O2 only, no O1 sibling run; the rule cannot be applied, so these are O2 values, caveat noted):
| row | gate | INL O2 | note |
|---|---|---|---|
| r2 N256 SR2 12 / 13.5 / 15 | informational (D38c) | 1.471 / 0.864 / 0.576 | no N 256 O1 |
| r3 OTA1 N256 SR1 9.5 / 10 / 10.5 | 1.333 (knee def.) | 5.703 / 2.449 / 1.176 | |
| r3 OTA1 N1024 SR1 9.5 / 10 / 10.5 | 1.333 | 4.576 / 1.925 / 0.859 | |
| r4 V4 / V4m N4096 | 1.333 | 0.315 / 0.339 | |
| r5 (c) cold / (d) hot A' N1024 | 5 | 0.144 / 1.450 | |
| t3 fp2 x30, s5f x1.5 15 MHz, N1024 | none (informational) | 137.2 | no O1 |
| r7 xcheck A60_base | rel_sym <= 5 % | at O1 only | see section 4 |

- In every pair the O1->O2 step is <= 8.6 % (r1) and <= 6 % elsewhere. For unpaired rows the paired steps are the only guide; none of the unpaired rows passes or fails by less than that, except r5(d) and r3 near the knee, which the margins below treat as is.
- Not run at both levels: the s5f 15 MHz N1024 base-GBW rows (9.95 ppm at O0, FAIL already), so no O2 restatement exists for them.

## 3. Knees and SR margin (2 MHz, slew INL share 1.333 ppm = 2 ppm / 1.5)
Knee = SR at which INL crosses 1.333 (linear interpolation of the O2 points, as in s5d R1); 25 % rule: SR >= 1.25 x knee.

**OTA2 (r2, SR1 12 V/us fixed)**
| N | INL O1 at 12 / 13.5 / 15 | INL O2 at 12 / 13.5 / 15 | s5d (default opts) at 12 / 13.5 / 15 | knee O2 | margin at 13.5 |
|---|---|---|---|---|---|
| 1024 | 0.452 / 0.259 / 0.146 | 0.443 / 0.253 / 0.137 | 0.78 / 0.60 / n.a. | below 12: all points under 1.333; log-linear EXTRAP of 12 -> 13.5 gives about 9.1 | >= 12.5 % measured bound (knee < 12); about 49 % by EXTRAP |
| 256 (D38c, informational) | not run | 1.471 / 0.864 / 0.576 | 1.69 / 1.155 / 0.854 | 12.3 (12 -> 13.5 interp) | 9 % (s5d: 5 %) |
- N1024 is the gated N. The directly measured 25 % check is V4m (OTA2 10.8 V/us = 13.5 / 1.25) at N 4096: 0.339 ppm vs 1.333 (section 4). A direct N1024 point at 10.8 V/us was not run.
- At N 256 the O2 curve sits 13-25 % below the s5d numbers (opposite to the r1 direction), and 13.5 V/us stays below the 25 % rule (needs about 15.4 for knee 12.3). Characterisation only.

**OTA1-only (r3: sr2 unset, so OTA2 runs at max(sr, 25 V/us), GBW2 = GBW1 = 10 MHz, gen_tier1.py:256-257), O2 only**
| N | 9.5 | 10 | 10.5 | knee O2 | s5d knee | margin at 12.5 | SR1 required for 25 % |
|---|---|---|---|---|---|---|---|
| 256 | 5.703 | 2.449 | 1.176 | 10.44 | 10.0 | 19.7 % | 13.05 |
| 1024 | 4.576 | 1.925 | 0.859 | 10.28 | 9.94 | 21.6 % | 12.85 |
- OTA1 knee moves up by 0.3-0.4 V/us at O2. **12.5 V/us no longer meets the 25 % rule at either N** (19.7-21.6 %); the rule needs 12.85 (N1024) to 13.05 (N256), i.e. about 13, as the WO anticipated. Nothing was run at 12.5-13 V/us itself, so the INL at 12.5 is an interpolation only (no point above 10.5 in r3; s5d had 0.31 ppm at 12 at O0).
- **D39 SR rows:** OTA2 13.5 holds at N1024 and at N4096 (V4m). OTA1 12.5 gives 20-22 % margin, short of the 25 % rule on the O2 knee; the rule would move it to about 13 V/us (cost about +2.4 µA per REVIEW-S5g). This is an option for the coordinator, not a failure: 12.5 V/us still sits 20 % above the knee, and the INL at the knee is itself only the slew share.

## 4. V4 / V4m, A', xcheck at O2 vs provisional
| row | gate | provisional | O2 (this run) | margin vs gate |
|---|---|---|---|---|
| V4 OTA2 11 V/us, N4096, 2 MHz | 1.333 | 0.557 (s5e) | **0.315** | 4.2x |
| V4m OTA2 10.8 V/us, N4096 | 1.333 | 0.579 (s5f) | **0.339** | 3.9x |
| A' (c) cold N1024 (30/34 MHz, 25/27 V/us) | 5 | 0.880 default / 0.188 tight (s5g) | **0.144** | 35x |
| A' (d) hot N1024 (20/22.5 MHz, 25/27) | 5 | 1.079 default / 1.375 tight | **1.450** | 3.4x |
| xcheck A60_base (deck vs model, O1) | rel_sym <= 5 % | deck 3.99 (S5b), S5b pre-Ck-fix model 3.09 | deck 3.993, model 3.991, rel_sym 0.064 %, ratio 1.0006, 4 checks true, ok | n/a (O1 only) |
- V4/V4m drop by 43 % and 41 % at O2; they have no O1 sibling. Pass with margin larger than any O1->O2 step seen (<= 9 %).
- A'(d) hot rises to 1.450 (from tight 1.375, +5 %); this is the smallest margin of the A' rows (3.4x), still passing.
- xcheck note: `model_inl` printed in the json is 3.9907, whereas the review column holds `rev_model_inl` 3.09; I report the json fields as read, and the agreement of deck and model (3.993 vs 3.991) is a property of this run's model value.
- T4 (101-point, N1024 / 20 MHz GBW2, O2): **pending rerun** (`WO-16-t4-677b39f`, deck timeout 14000 s). The first attempt hit the 1500 s deck timeout (rc 124, no data file). The question (does the ~5 ppm cubic-fit residual shrink at O2?) is not answered. Related data at m = 21: cubic-residual max is 6.31 ppm at r1 O2 vs 4.89 at O0 (N 256, so it grows with the option level on that row, not shrinks); the m = 21 N1024 rows have 0.04-1.3 ppm.

## 5. fp2 window (D39 boosted point, 4 MHz, N1024; GBW 20 / 22.5 MHz, SR 25 / 20.25)
INL ep ppm. PM is HAND: two-pole closed loop s^2 tau2 + s + K = 0, K = beta 2 pi GBW, tau2 = 1/(2 pi fp2), loop PM = 90 deg - atan(y), y^2 = (-1 + sqrt(1 + 4 a^2)) / 2, a = beta/mult, zeta = 0.5 sqrt(mult/beta). Assumed beta1 0.84, beta2 0.497 (REVIEW-S5g) and fp2 = mult x loaded GBW. The deck's own beta may differ slightly (parasitics); the formula reproduces the review's 74.9 deg / zeta 0.945 at mult 3 for OTA1 and the 63 deg of the review's held-pole case (mult 1.5 at beta 0.84 gives the same zeta 0.67).

| fp2 mult | OTA1 INL O1 | OTA1 PM / zeta | OTA2 INL O1 | OTA2 PM / zeta |
|---|---|---|---|---|
| 1 | not run | 55.4 / 0.55 | 5.267 | 65.6 / 0.71 |
| 1.5 | 68.45 | 63.4 / 0.67 | 1.381 (O2: 1.425) | 72.5 / 0.87 |
| 2 | 10.88 | 68.6 / 0.77 | 2.331 | 76.4 / 1.00 |
| 3 | 3.292 (O2: 3.363, both OTAs at 3) | 74.9 / 0.94 | 3.292 | 80.7 / 1.23 |
| 4 | 8.055 | 78.4 / 1.09 | 3.710 | 83.0 / 1.42 |
| 6 | 14.65 | 82.1 / 1.34 | 4.12 | 85.3 / 1.74 |
| 10 | 20.99 | 85.2 / 1.73 | 4.397 | 87.2 / 2.24 |
| 30 | 28.28 (O2: 28.52) | 88.4 / 2.99 | 4.737 (O2: 4.785) | 89.1 / 3.88 |
- OTA1 (OTA2 at 3): minimum at mult 3 on the grid (3.29). A parabola in ln(mult) through 2, 3, 4 puts the minimum at 2.94. The prediction (zeta = 1 at mult = 4 beta1 = 3.36, PM 77 deg) lies between the grid points 3 and 4 and cannot be separated from 2.9 by this grid; the data support a minimum in 2.5-3.5, PM about 72-77 deg, which includes the prediction. The curve is asymmetric: mult 4 is 2.4x the minimum, mult 2 is 3.3x, mult 1.5 is 21x (PM 63 deg).
- OTA2 (OTA1 at 3): the extras change the earlier "monotone" reading. Series 1 -> 1.5 -> 2 -> 3 -> 4 -> 6 -> 10 -> 30 reads 5.27, 1.38, 2.33, 3.29, 3.71, 4.12, 4.40, 4.74. Falling toward low mult down to 1.5, then rising again at 1 (5.27). Minimum is near mult 1.5 (3-point parabola on 1, 1.5, 2: 1.58), HAND zeta 0.87 at beta2 0.497, i.e. slightly underdamped, PM 72 deg, not at the edge. This matches the HAND optimum (zeta = 1 at mult 4 beta2 = 2.0) only to within the grid.
- The OTA2 curve is flatter: 1.38 to 4.74 over 1.5-30 (factor 3.4), against 3.29 to 68.45 for OTA1 over 1.5-3 (factor 21).
- Physical reading (HYPOTHESIS, not tested here): OTA1 is the stage whose settling dominates the error, and its optimum is near critical damping as the textbook closed-loop calc says. OTA2's weaker dependence could come from its smaller step and the fact that its errors are scaled by 1/c1-type factors; this is not shown by these runs. The data show only: (i) OTA1 INL is a sharp function of fp2, (ii) OTA2 INL has an optimum near 1.5 with a shallow rise toward high mult, which is monotone only above the optimum.
- O1 -> O2 on the window: x3 (3.292 -> 3.363), OTA1 x30 (28.28 -> 28.52), OTA2 x30 (4.737 -> 4.785), OTA2 x1.5 (1.381 -> 1.425): +2.2 %, +0.8 %, +1.0 %, +3.2 %. All converged by the rule.
- T3 (s5f x1.5 15 MHz row, fp2 x30, N1024, O2): **137.2 ppm** (bf 126.9). The s5g provisional (default options) was 110.4 (+24 %). No x3 sibling at O2 on this row was run, so the ratio to x3 cannot be formed from this run; REVIEW-S5g's hand estimate was about 30x (10 -> 100 ppm); the s5f x3 value was 9.95 at O0 (13.8x) but the O2 x3 is unknown, so the numerical-vs-physics comparison is only qualitative: the order of magnitude agrees (INL goes to about 100 ppm at x30 regardless of N or GBW2, as s5g found).
- On the D39 boosted point the same x30 move gives only 28.5 ppm, a factor 8.5 (OTA1, vs 3.36 at x3), smaller than the 30x hand number; the hand estimate used the s5f point, where GBW1 is lower (14.2 MHz).

## 6. Numbers that change vs provisional, and open items
| item | provisional | S5h | effect |
|---|---|---|---|
| s5f x1.5 15 MHz N256 | 6.70 (O0) | 18.77 (O2), verdict 20.27 vs gate 20 | converged; fails by 1.4 %; characterisation row |
| D39 control N1024 4 MHz | 3.686 (default) / 3.28 (tight) | 3.292 O1 / 3.363 O2, verdict 3.43 | passes, margin 31 % |
| OTA1 knee 2 MHz | 10.0 (N256) / 9.94 (N1024) | 10.44 / 10.28 | 12.5 gives 20-22 % margin; rule needs 13.05 / 12.85 |
| OTA2 knee N256 (char.) | 12.9 | 12.3 | margin at 13.5: 5 % -> 9 % |
| OTA2 N1024 at 13.5 | 0.60 | 0.253 (O2) | margin >= 12.5 %, not directly at 10.8 |
| V4 / V4m | 0.557 / 0.579 | 0.315 / 0.339 | margin 4.2x / 3.9x |
| A' (c) / (d) | 0.880 / 1.079 (default) | 0.144 / 1.450 | pass |
| xcheck A60_base | deck 3.99 | 3.993, rel_sym 0.064 % | unchanged |
| fp2 OTA1 optimum | prediction about 3.4 | grid min 3, parabola 2.9 | consistent; PM about 75 deg |
| fp2 OTA2 trend | "monotone toward low mult" (O1, 1.5 edge) | min near 1.5, rises to 5.27 at 1 | optimum is interior |
| T3 | 110.4 (default opts) | 137.2 (O2) | no x3 sibling at O2 |

**SPEC row to consider changing:** OTA1 slew 12.5 V/us (SPEC.md line 94, basis "knee about 10.0 ... margin 25 %"): basis becomes "knee 10.3-10.4 at O2", and 25 % rule gives about 13 V/us. Option: move to 13.0, or keep 12.5 and state the 20 % margin. OTA2 13.5 holds. No other row changes; the OTA2 PM window (SPEC OTA2 has none) could cite the interior optimum near fp2 = 1.5-2 x GBW at beta2 0.497 (PM about 72-76 deg).

**Open items**
- T4 101-point cubic residual at O2: pending rerun.
- No direct points at OTA1 12.5-13 V/us, or OTA2 at 10.8 V/us N1024, so the margins above rest on interpolation / extrapolation.
- O2-only rows (r3, r4, r5, r2 N256) have no O1 pair; convergence for them is inferred from the paired rows (steps <= 9 %).
- The r1 shows a +10 ppm jump at O0 -> O1 from either knob; O0 numbers are unconverged (either sign) and are no longer cited; SPEC rows now cite O2 values.
- fp2 O2 coverage: only x3, x30 (both OTAs) and OTA2 x1.5; no O2 point at OTA1 x2/x4 around the OTA1 minimum.
- Resolved (REVIEW-S5h Q5): `rev_model_inl` 3.09 is the hard-coded S5b model value from before the Ck fix (`REV["A60_base"][3]`, tier1_tb.py:390), never gated; the current model gives 3.991.

## Addendum 2026-11-09 (after REVIEW-S5h)
- r2/r4 rows also run OTA2 GBW at 10 MHz (the SPEC floor); not stated above (H-m6).
- OTA1-only direct points (2 MHz, sr2 unset): N1024 12.5 V/us O1/O2 0.098/0.101 (verdict 0.104), 13 V/us 0.082/0.083; N256 O2 12.5 → 0.359, 13 → 0.340. User kept 12.5 V/us (D44).
- Reviewer gap jobs: OTA2 10.8 V/us N1024 O2 0.756 (under 1.333 share, ≥ 25 % margin direct); A′ N256 O1 c 0.403 / d 1.982 (gate 20); trap O1 vs gear O1 at r2 N1024 13.5: 0.253 vs 0.2595 (2.5 %).
