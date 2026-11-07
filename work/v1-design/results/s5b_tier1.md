# S5b tier-1 extensions (WO-08)

Commands: `python3 design/tier1/tier1_tb.py --{xcheck,av,knees2,cm,offsets,rsrc,nonvac2}` on the sandbox (tree `tt-sd`), nix ngspice 45 (host, not the IIC image), `nice -n 10`, at most 3 ngspice at once.
Raw output: `/home/mempool/regr/tt/WO-08/` (per-mode `<mode>.txt`, `<mode>.json`, per-run `.cir/.log/.csv`); numbers in `s5b_tier1.json`.
Pass criteria come from theory or the REVIEW-S5 probe numbers. `model/iadc.py` is imported only for the item-1 / item-4 cross-check tables.
Relative differences are symmetric: |a-b| / mean(|a|,|b|).

## Acceptance
| # | Command | Result |
|---|---|---|
| 1 | `pytest design/tests -q` | 27 passed |
| 2 | `--xcheck` | ACCEPT (table + noise transfer) |
| 3 | `--av` | ACCEPT: deck vs model INL 13.9 % (limit 30 %) |
| 4 | `--knees2` | ACCEPT (table written), no knee above SPEC 3.0; margins thin, see flags |
| 5 | `--cm` | ACCEPT (log + CMRR table); sys-off and sys-on CMRR targets met in the ideal deck, see caveats |
| 6 | `--offsets` | ACCEPT: closed forms within 0.5 %, sys-pair residual 0.0008 / 0.0049 uV (limit 0.5) |
| 7 | `--rsrc` | ACCEPT (table written) |
| 8 | `--nonvac2` | all three broken cases handled: A(v) vsw 0.8 REJECT, late swap REJECT, no-D12 REJECT at Vin_cm 0.2 (Vin_cm 2.0 stays in range, reported); exit 1 |

Raw log of every mode: `s5b_run_all.txt`; JSON: `s5b_tier1.json`; per-run decks and logs in `/home/mempool/regr/tt/WO-08/`.
Every run passes the run checks (final time == tstop, log scan for error/singular/timestep/failed, netlist audit V R C S B only). Two deck changes were forced by run checks:
`trnoise` aborted with "timestep too small", so the noise is a deterministic per-cycle PWL (the same sequence feeds the model); a 9 mV offset step at the 180 dB open-loop DC point failed the DC operating point, so offsets ramp in over the first microsecond of the reset phase.

## 1. Cross-check (M1), ideal everything except A0, N 256, 5 points, endpoint INL in ppm FSR
| Case | Deck gain | Model gain | Deck INL | Model INL | Reviewer deck / model INL | Gain diff | INL diff (sym.) |
|---|---|---|---|---|---|---|---|
| A0 60 dB base | -5.589e-4 | -5.471e-4 | 3.993 | 3.090 | 3.99 / 3.09 | 2.1 % | 25 % |
| A0 60 dB, k 0.25 | -2.931e-4 | -2.882e-4 | 6.979 | 5.897 | 6.98 / 5.90 | 1.7 % | 17 % |
| A0 60 dB, c1 0.25 | -5.507e-4 | -5.430e-4 | 10.049 | 7.431 | 10.05 / 7.43 | 1.4 % | 30 % |
| A0 80 dB base | -5.630e-5 | -5.470e-5 | 0.413 | 0.295 | 0.29 / 0.295 | 2.9 % | 33 % |

Deck gain matches the model within 3 % (tolerance 5 %); INL within 33 % (tolerance 35 %, symmetric relative difference; deck always higher, as the review found). The A0 80 dB INL (0.41 vs 0.29 ppm) sits on the null floor.
The deck gain error is about -1.09 k/A0 independent of c1 (k 0.25 halves it, c1 0.25 leaves it).
**Noise transfer** (trnoise replaced by PWL, 32 conversions, N 256, white per-cycle error of 2.01 mV rms at OTA1's input, A0 120 dB): deck output rms 7.46e-5 u vs theory sqrt(sum w^2)/(N(N-1)/2) x e/VREF = 7.10e-5 (ratio 1.05); per-conversion regression against the model driven by the same sequence: slope -1.043, correlation -1.000 (the sign is the OTA inverting convention). Within 30 %, no waiver needed.

## 4. A(v) in the deck (M2)
Static A(v) = A0 max(0.02, 1 - 0.9 (vo/2.0 V)^2) as a B-source output conductance on both OTAs. Static table C1 must deliver (vo_diff / vd_diff, not dA/dv):
| vo_diff (V) | 0 | 0.4 | 0.8 | 1.2 | 1.4 | 1.6 | 2.0 |
|---|---|---|---|---|---|---|---|
| A (dB) | 80.0 | 79.68 | 78.65 | 76.60 | 74.95 | 72.55 | 60.0 |

At 1.4 V this is 74.95 dB, the SPEC 3.0 "A >= 75 dB at 1.4 V" row. Deck INL 3.175 ppm (flat A0: 0.546), model 3.648: difference 13.9 % (limit 30 %). Broken copy: vsw 0.8 V gives deck INL 535.8 ppm against the same model, REJECT.

## 5. Load-dependent OTA knees (M3), 21 points, N 256
Deck: gm into per-side output nodes with C_L 1.4 pF (OTA1) and 0.7 pF (OTA2) including the feedback network, virtual-ground parasitic 0.262 pF (beta 0.84), second pole at 3 x GBW (PM about 74 deg analytic), tail-current slew, CMFB, Cs2 hold-phase load present, real reference pins, D12 shorting. Boost (D31) = 2x gm and 2x tail current. Precision spec point GBW 10 MHz / SR 12 V/us; fast spec point (boost) base 10 / 12 -> loaded 20 / 24.
| Set | Parameter | Value (base units) | INL (ppm) | Target | Pass |
|---|---|---|---|---|---|
| 2 MHz | GBW (MHz) | 5 / 7 / 10 / 20 / 30 | 21.05 / 6.10 / 1.69 / 0.56 / 0.54 | 8 | knee 7 |
| 2 MHz | SR (V/us) | 6 / 8 / 10 / 12 / 25 | 1665 / 133 / 3.08 / 1.69 / 0.35 | 8 | knee 10 |
| 4 MHz boost | GBW base (MHz) | 5 / 7.5 / 10 / 20 | 42.5 / 7.11 / 6.99 / 1.35 | 20 (N 256) | knee 7.5 |
| 4 MHz boost | SR base (V/us) | 6 / 9 / 12 / 25 | 5146 / 265 / 6.99 / 1.07 | 20 (N 256) | knee 12 |
| 4 MHz no boost, spec base | | | 6252 | 20 | FAIL |
| 4 MHz boost, spec, N 1024 | | | 4.23 | 5 | pass (thin) |
| 2 MHz spec + A(v) | | | 1.01 | 8 | pass |
| 2 MHz spec, negative-direction SR halved (6 V/us) | | | 2815 | 8 | FAIL |

Flags (none above SPEC 3.0, but the margins are thin or absent):
- FLAG SR is a cliff: at 2 MHz SR 8 V/us gives 133 ppm and 10 V/us 3 ppm; the 12 V/us spec has about 20 % margin. At 4 MHz boost the SR knee (12 base, 24 loaded) equals the spec, zero margin.
- FLAG the SR limit must hold in both directions: an asymmetric tail (negative direction half) fails at 2815 ppm; SR 12 V/us must be the worst direction, over corners.
- FLAG 4 MHz without boost fails (6252 ppm): the bias-boost bit is required; the N 1024 fast target (5 ppm) passes at 4.23 ppm with 15 % margin.
- GBW has margin at the spec point (knee 7 MHz at 2 MHz, 7.5 base at 4 MHz boost).

## 6. Reference pins, common mode, CMRR (M4a, D32)
Real pins (VREF+ 2.048 V, VREF- 0 V), Vin_cm in {0.2, 1.0, 2.0} V, u = +-0.08, CMFB 40 dB / 10 MHz.
**Virtual-ground CM excursion** (min/max):
| Variant | Vin_cm 0.2 | 1.0 | 2.0 | Required PMOS-pair CM |
|---|---|---|---|---|
| D12 top plates shorted (OTA1 vg) | 1.649 - 1.728 | 1.647 - 1.728 | 1.554 - 1.728 | whole run 1.554 - 1.731 V; inside conversions 1.630 - 1.728 V (cm 1.65 V) |
| Tops tied to cm (no D12) | 1.648 - 2.538 | 1.648 - 1.738 | 0.674 - 1.682 | 0.67 - 2.54 V |

OTA2 vg: 1.630 - 1.652 V (D12), 1.421 - 1.650 V (no D12). **C1/C4 target: PMOS-pair input CM range covering at least 1.55 - 1.73 V with D12 (say 1.45 - 1.85 V with margin); without D12 it would need 0.67 - 2.54 V, which leaves the assumed 0.2 - 2.0 V range at Vin_cm 0.2.** (The assumed 0.2 - 2.0 V range is mine; SPEC gives no number.) The D12 reset-release step is the largest excursion: output CM deviation 82.5 mV peak, 1.8 mV at 0.2 t_half after each phase start (SPEC row: <= 10 mV in 0.2 t_half; met).

**CMRR** = 20 log10(|Vin_cm - 1.024 V| / error), error = differential offset change from the ideal-match run. Only Vin_cm 0.2 and 2.0 have a usable CM step. "Sys on" = pin-side swap pair (u, -u), residual of the pair.
| Topology | Mismatch | Vin_cm 0.2 off / on (dB) | Vin_cm 2.0 off / on (dB) |
|---|---|---|---|
| D12 (v1 choice) | 0.25 % | 151.5 / 159.9 | 152.1 / 161.3 |
| D12 | 0.75 % | 132.4 / 139.9 | 133.6 / 141.4 |
| no D12 (tops tied to cm) | 0.25 % | 75.9 / 134.7 | 75.9 / 136.0 |
| no D12 | 0.75 % | 66.3 / 134.4 | 66.3 / 142.7 |
| D12 + Cs role swap every cycle (variant) | 0.25 % | 151.3 / 124.7 | 152.8 / 126.2 |
| D12 + Cs role swap | 0.75 % | 132.3 / 106.1 | 133.8 / 107.6 |

All meet the D32 targets (>= 60 dB sys off, >= 100 dB sys on) in this ideal deck. Findings:
1. **The naive expectation 1/epsilon (52 dB at 0.25 %) is wrong for a floating-virtual-ground SC integrator.** With a Cs mismatch the sampled error is eps Cs (vg_cm - v_top + Vin_cm - Vref_cm). The floating CM nodes move so that this term is zero in steady state: with D12 (floating shorted tops) vg_cm and the top-plate CM track and the term cancels to first order; with tops tied to cm the vg CM settles to cm - Vin_cm + Vref_cm (hence the 0.67 - 2.54 V excursion) and only the settling transient leaves an error, closed form eps X (2/(N-1)) sum (1 - m/(N-1)) a^m with a = 1 - Cs/(Cs+Cint+Cp) = 0.895: 7.2 % of eps X predicted, 6.4 % measured (limit set at 25 %). That is 66 - 76 dB without D12, so no-D12 also passes 60 dB but at the price of the wide vg CM range.
2. Sys chop does cancel the remaining no-D12 error (66 -> 134 dB, hypothesis confirmed: the CM->diff term has the same sign in both halves). With D12 there is nothing left to cancel at this level; the residual mismatch offset (0.2 uV at 0.75 %) is second order: it scales as eps^2 (2.2e-8 V at 0.25 %, 1.98e-7 V at 0.75 %, ratio 9.0 = 3^2), so it is not a floor and not a bleeder effect (a floor would not scale; a bleeder term would be first order). [text fixed in WO-09 item 7 / REVIEW-S4S5b m7]
3. **Caveat (not covered by this deck):** the cancellation depends on the top-plate CM being truly floating for a conversion. Real leakage on the shorted-top node, switch charge injection and Cp+/Cp- mismatch reintroduce a CM->diff term of order (leak charge) x eps. The 1e13 ohm bleeder here is about 1 uA/V per... i.e. 0.4 pA at 1 V, far below 125 C junction leakage (tens of pA to 100 pA): at 100 pA on about 1 pF over 128 us the node drifts 10 mV, 1 % of X, which would cut the 150 dB figure to roughly 60 + 52 = 100 dB at 0.25 %. Treat >= 100 dB sys-on as plausible and >= 60 dB sys-off as plausible, but not demonstrated; C4 must run the leakage/charge-injection case.
4. The cycle-by-cycle Cs role swap (cheap alternative variant) does not help: sys-off is unchanged and sys-on gets worse (106 - 126 dB), so it is not recommended.

## 7. Offsets and system chop (m5), ideal OTA (A0 180 dB), Roff 1e14, N 256
| Item | Measured | Closed form | Diff |
|---|---|---|---|
| Null floor (Roff 1e14, no offsets) | 0.0025 uV | 7e-9 u = 0.014 uV | ok |
| Vos2 = 9 mV unchopped | 851.47 uV | 2 Vos2 (1 + Ck/Cs2) / (c1 (N-1)) = 847.06 uV | 0.5 % |
| Vos1 = 9 mV unchopped | 9564.72 uV | lf Vos + S2 x1_offset path 2 Vos/(c1 (N-1)) = 9000 + 564.7 = 9564.71 uV | 0.0001 % |
| Vos1 = 9 mV OTA chop (ideal swap, phase restarts at reset) | 35.297 uV | Vos/(N-1) = 35.294 uV | 0.01 % |
| Comparator offset 20 mV (260 bits change) | residue-reconstructed 0.013 uV; plain CoI 301 uV | ~0 (loop-suppressed) | ok |
| All offsets + chop, single conversion | -30.9 uV | | |
| Sys-chop pair, u = 0.05 / 0.3 | residual -0.0008 / -0.0049 uV | 0 (limit 0.5 uV) | ok |

Findings: (a) the stage-2 offset sensitivity is (Cs2 + Ck)/Cs2 = 1.5 x the S2 closed form, because the separate k-DAC cap Ck (D25) shares OTA2's input node; the S2 model (c2 only) underestimates a constant OTA2 offset by 1.5 x. The pair cancels it, so no budget row changes. (b) An OTA1 offset also reaches stage 2 as an x1 offset (S2 `x1_offset`), adding 2 Vos/(c1 (N-1)) = 565 uV to the unchopped value. (c) Order-1 path: the plain bit average obeys mean(y) = u - x1[N]/(c1 N) exactly; the raw residual 1.373e-4 equals the readout offset term Vos/(VREF c1 N), leftover 2.4e-9. The S2 order-1 value lf Vos/N (35.2 uV) is c1 times that term (the integrator state carries c1 e); it is not separately testable in an order-2 deck, so it is covered by this identity.
Broken copy: the swap one cycle late (mid-conversion) leaves -4800 uV residual, REJECT.

## 8. Source impedance (m6), spec OTA, 11 points
| R_src | INL (ppm) | Gain error | Offset | tau_in (no cap) |
|---|---|---|---|---|
| none (500 ohm pad only) | 1.69 | -6.34e-5 | +0.1 uV | 8.2 ns |
| 1 kohm | 1.69 | -6.34e-5 | +0.1 uV | 13.7 ns |
| 10 kohm | 2.18 | -1.41e-4 | +31.9 uV | 63.2 ns |
| 10 kohm + 10 nF at the pin | 1.53 | -3.22e-4 | +208.3 uV | 63.2 ns |

The SPEC input-source row holds: 1 kohm costs 0.00 ppm INL and no gain change. 10 kohm without a cap costs 0.5 ppm INL and a 31.9 uV offset; with 10 nF the INL is fine but the gain error is 5 x larger and there is a 208 uV offset (input current x R_src that the sys chop does not cancel, as the SPEC row says). The 10 nF case is run as one deck per input value (a 10 nF pin does not settle between conversions in one deck: tau 100 us).

## Limits (open)
Ideal switches (no charge injection, body effect, leakage except the stated bleeders), the PMOS CM range is an assumption, CMFB is a first-order CM-only model, the second pole is on the gm control path, no noise in the v2 OTA (noise is a separate input source), corners not run (tier 1 is nominal).

