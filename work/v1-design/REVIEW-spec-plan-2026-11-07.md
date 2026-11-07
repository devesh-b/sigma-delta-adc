# REVIEW: SPEC.md rev 2026-11-07b + work/v1-design/PLAN.md (2026-11-07)

**Source.** sd-adc-design-reviewer (Opus). No simulations were run; PDK facts were read-only from the sandbox ciel sky130A. The coordinator saved this review (the reviewer is read-only).
- The full original text is in the session transcript.
- This file keeps every finding, its evidence class and its fix.
- The **Disposition** column shows what the coordinator did.

## Verdict
The direction is sound and the PLAN copies Paul's method well. **Do not freeze SPEC v1 (S7) until F1–F8 are resolved.** None of them makes the chip dead, but several would make gates vacuous or test the wrong design.

**Checked items (14/14):**
- reconstruction formula
- raw-accumulator output
- TG input switch
- CJC off-chip
- the 0.77 b cost of VREF
- noise numbers

## Correctness: Major
| # | Finding | Class | Fix | Disposition |
|---|---|---|---|---|
| F1 | Option B (c1 = 0.125, k = 1) changes the NTF (k/c1 = 8) and does not halve x2. The correct version is **c1 = 0.125, k = 0.5, c2 = 0.5**: bit-identical to A, both integrators at half swing. x2 swing can be set freely through c2. | PROVEN (algebra) | Redefine option B; note that c2 is free | WO-02 amended live; SPEC fixed |
| F2 | OTA input CM = Vcm_s + Vref_cm − Vin_cm. Example: VREF 1.2 V, Vcm_s 1.65 V, Vin_cm 2.5 V gives ≈ −0.25 V at the virtual ground, which forward-biases junctions. The input CM range is not specified. | REASONED | (a) specify the input CM range and choose Vcm_s; (b) use CM-rejecting input switching; (c) add an input-CM sweep to C4 and V3 | **USER Q1**; sweep added to PLAN |
| F3 | β is 0.75 for int1 and 0.61 for int2, not 0.3–0.5. The settling study covers input/reference RC only, not OTA GBW or slew. At 4 MHz with GBW 10 MHz and SR 10 V/µs, the signal-dependent slew-then-settle error is ≈ 6e-3 of a step (thousands of ppm INL). At 2 MHz it is ≈ 3e-5. SPEC t_half 250 ns vs model 225 ns. | PROVEN (hand calc) / REASONED | (a) make 4 MHz a fast, low-resolution mode; or (b) spec the OTA at fs_max: GBW ≥ 20 MHz at the real load and worst corner, slew ≤ 20 % of t_half, then ≥ 10τ. Add OTA GBW/SR to tier 1 and run spec_sweep | **USER Q2**; β and t_half fixed in SPEC |
| F4 | The output frame has no chop-sign, order or N tag. A dropped frame flips the system-chop demodulation, so offset adds instead of cancelling. | REASONED | Add chop-sign, order, N code and a frame counter to the word; include them in the golden vectors | SPEC §3.7 fixed |
| F5 | A0 75 dB gives 71.3 ppm INL, which fails the PLAN's 1.5× margin (≤ 67 ppm). | PROVEN (repo numbers) | Raise A0 to ≈ 78–80 dB, tighten a0_drop, use a smaller swing (correct option B), or the user changes the margin | **USER Q6** (A0 target); SPEC flags it |
| F6 | SPEC says the DAC shares Cs, but the design point ran with separate caps. PGA ×2 needs separate caps. Separate caps are far more settling-sensitive (−1286 vs −26 ppm at τ_in = 0.15·t_half). PGA is not in the model, S6 or V4. | PROVEN (file read) | Pick one architecture; re-run the design point with it and PGA ×2; add PGA to S6, V4 and C10 | **USER Q3**; PLAN updated |
| F7 | One VREF pin means REF− is tile ground, shared with the decimator. Ground bounce enters unshaped and does not cancel ratiometrically. | REASONED | Dedicate ua3 to REF− (+€100) with a Kelvin connection, or document star grounding plus a ground-bounce V-test | **USER Q1b** |
| F8 | The first comparator decision after reset (x2 = 0) is metastable every conversion. If the DAC and decimator see different bits, the error is ≈ 4/N FS ≈ 4000 ppm, and it is sporadic. | REASONED | One retimed FF drives both the DAC and the decimator; optionally force y[0]; add a C3 test at Δ = 0, 4 MHz, ss/−40 | SPEC §3.2 and PLAN C3 fixed |

## Correctness: Minor
| # | Finding | Class | Disposition |
|---|---|---|---|
| m1 | acc2 = N(N−1)/2 (not N(N+1)/2). Signed 24-bit fits: 8,386,560 < 8,388,607 | PROVEN | SPEC fixed |
| m2 | Model uses exclusive S (`sumS += S` before `S += y`). An inclusive RTL behaves like k/c1 = 5, a ≈ 2/N gain error. Bind the convention in the S6 golden vectors | PROVEN | PLAN S6/C9 |
| m3 | Input range unstated. Model swing is measured at \|u\| ≤ 0.9. Add an overload test at 1.0–1.1 with recovery | PROVEN | SPEC + PLAN |
| m4 | TG Ron is worst at ss/−40 °C/3.0 V. Size for τ ≤ t_half/12, including the pad and source | REASONED | SPEC §3.3 |
| m5 | Cap corners: R+C sections ll/hh/hl/lh and combined (ss_hh, ff_ll) plus *_mm exist and are not in the 45 | PROVEN (lib file) | SPEC §6: +ss_hh, +ff_ll |
| m6 | The MC rule "one sample beyond 3σ" is ill-defined | — | PLAN: μ ± 3σ inside spec AND every sample inside spec |
| m7 | VDPWR adds ×3 for digital and level shifters, giving 135 points | — | SPEC §6 |

## Efficiency
| # | Finding | Disposition |
|---|---|---|
| E1 | Set x2 swing through c2 (e.g. 0.25). A simpler OTA2 saves ≈ 20–40 µA | WO-02 amended (option-A c2 = 0.25 variant) |
| E2 | The OTA white-noise spec of ≤ 7 nV/√Hz is inherited from continuous-time. In SC, kT/C dominates. 10–14 nV/√Hz, checked via a ktc_excess sweep, could roughly halve OTA1 current | S3 budget item |
| E3 | Correct option B costs +4000 µm² of MIM (Cint1 8 pF per side) | In the S1 table |
| E4 | Residue reconstruction (F9) allows short top-level windows at ppm accuracy | PLAN V3/V6 |
| E5 | If S2 shows system chop is enough, dropping OTA chop removes 2 choppers and the sequencing | Pending WO-03 / D4 |

## Verification gaps (added to PLAN)
- **F9.** V3 at N = 256 has a ≈ 244 ppm quantization floor, so its INL check is vacuous.
  - Use residue reconstruction: u = (ΣS + (k/c1)·S + x2[N]/(c1·c2)) / (N(N−1)/2), with x2[N] read from the transistor run.
  - The "OTA −20 dB" broken copy must REJECT.
- **Simulator null test in S5.**
  - Build an ideal deck that reproduces the theory to < 1/10 of the INL target.
  - Freeze reltol, chgtol and method in params.spice. Paul's reltol of 1e-4 is a sanity gate, not a precision one.
- **Reset completeness.** Back-to-back conversions at ±0.9·FS. Reset depth r ≤ 2.2e-3 for N = 1024 (≈ 6τ) and 1.4e-4 for N = 64 (≈ 9τ).
- **Reset charge injection.** Offset = 2·x1[0]/(c1(N−1)): 1 mV gives 7.8 µV at N = 1024 and 127 µV at N = 64. It must cancel in the chop pair.
- **Chop sequencing.** The swap may happen only inside the reset window. Assert it in RTL and at transistor level. A broken copy that swaps one cycle late must REJECT.
- **Analog/digital reset alignment.** Add a top-level broken copy that is off by one cycle.
- **CMFB start-up.** Start with `.ic` outputs at 0 V and at VAPWR, at every corner (C1, C2, V2).
- **Comparator kickback.** Numeric gate: disturbance on x2 ≤ a fraction of the minimum x2 step.
- **TT pad model in every top-level testbench.** 500 Ω, 5 pF and ESD on VIN± and VREF. Add a 10 kΩ source case.
- **Input-CM sweep (F2).** Add PGA ×2 (F6) and overload/recovery (m3).
- **Documented blind spots in V9.**
  - The MIM model has no voltage coefficient and no bottom-plate parasitic (tc1 = tc2 = 0).
  - Digital-to-analog substrate coupling is not simulated.
- **D2 / F10: data-driven top-level points.**
  - Use the union of tier-2 worst corners (≈ 6–8 points). It must include ss/−40/3.0 and ff/125/3.6, plus VDPWR 1.62 with VAPWR 3.6.
  - Tier 0 does not model charge injection, kickback, CMFB or input CM, so those are checked only at the top-level points.
- **Leakage.** At 0.25 MHz with N = 1024/4096, a transistor-level run is infeasible. Measure virtual-ground leakage at block level and feed it into tier 0. Offset = I_leak/(fs·Cs): 1 nA gives 4 mV.

## Questions for the user (Q numbers used in DECISIONS)
1. Input CM range? Is REF− chip ground, or does ua3 become REF− (+€100)? (F2, F7)
2. Is fs = 4 MHz a precision mode, or a fast / entropy mode? (F3)
3. Input stage: shared Cs (no PGA) or separate Cin/Cref (PGA ×2)? (F6)
4. Is the chop phase deterministic from global reset, or carried in the frame? Answered by F4: carry it in the frame.
5. Must order-1 mode support every chop and N combination? (Sets the V4 matrix size.)
6. OTA A0 target 78–80 dB, or relax the INL margin? (F5)
