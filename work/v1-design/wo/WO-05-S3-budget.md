# WO-05 (S3): error budget → per-block specs at the decided design point

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer reviews the budget before SPEC §3 is updated.
**Spec source:**
- SPEC.md §1–§3, §6; DECISIONS D13–D24
- PLAN.md S3 (margins ≥ 2× noise, ≥ 1.5× INL)
- REVIEW-spec-plan (E2, F3, F8, m4, reset depth, leakage)
- REVIEW-S1S2 (M2, m3, m4, m6, m7)

Read `work/v1-design/HANDOFF.md` first.

## Decided design point (use exactly this)
| Item | Value |
|---|---|
| Loop | Order 2 CIFB; c1 = 0.125, c2 = 0.5, k = 0.5 |
| Reference | VREF = 2.048 V; VREF+ on ua2, VREF− on ua3, each through 500 Ω + 5 pF pad |
| Capacitors | Cs1 = 0.5 pF, Cint1 = 4 pF, shared Cs (input = DAC) |
| Clock | fs = 2 MHz precision (0.25–2 MHz); 4 MHz is the fast mode |
| Precision mode | N = 4096, K pairs averaged, ota+sys chop |
| Fast modes | N ∈ {64, 256, 1024} |
| OTA | A0 ≥ 80 dB; gain-drop model with vlin in volts |
| Offsets | Vos1 = Vos2 = 9 mV (3σ) |
| Input | Overload 1.0–1.1·VREF must recover |

## Budget targets
The design budget targets the **stretch** specs, so the v1 targets keep large margin:

| Quantity | Design budget (all blocks together) | v1 target | Stretch target |
|---|---|---|---|
| Noise @15 SPS | ≤ 2.5 µV rms (2× under 5 µV) | 50 µV | 5 µV |
| INL | ≤ 20 ppm (1.5× under 30 ppm) | 100 ppm | 30 ppm |
| Offset after sys chop | ≤ 5 µV | — | — |
| Gain error | ≤ 0.5 %, calibratable | — | — |

## Files you may touch (nothing else)
- `design/params.py`
- `design/tests/test_params.py`
- `model/studies/s3_budget.py` (new)
- `model/tests/test_s3_budget.py` (new)
- `work/v1-design/results/s3_budget.{md,json}` (new)

Do **not** edit SPEC.md: the coordinator updates it from your results after review. Do not edit `model/iadc.py`. If you need a model change, stop and report it.

## Items
1. **params.py update.**
   - CS1 0.5 pF, CINT1 4 pF; stage 2: propose Cs2/Cint2 in item 3, initially CS2 0.5 pF, CINT2 1 pF.
   - `N_PRECISION = 4096`, `N_FAST = (64, 256, 1024)`.
   - Pins: ua0 VIN+, ua1 VIN−, ua2 VREF+, ua3 VREF−.
   - `VOS_3SIGMA = 9e-3` for both OTAs. Overload range 1.1.
   - Update tests: c1 == 0.125 from 0.5/4 pF, k/c1 == 4, pin map.
   - Non-vacuity: a CINT1 = 2 pF copy fails.
2. **One-at-a-time sensitivity sweeps** (PLAN S3, Paul's `spec_sweep` pattern) at the design point. Each block parameter is swept alone with the others ideal. Report its contribution to noise @15 and @240 SPS, INL (N 4096), offset (sys pairs) and gain error:

   | Parameter | Sweep values |
   |---|---|
   | A0 | {70, 75, 80, 85, 90} dB × a0_drop {0.5, 0.9} |
   | vlin_diff | {0.8, 1.0, 1.5, 2.0} V |
   | OTA thermal excess (`ktc_excess` OTA part, E2) | equivalent 5 / 7 / 10 / 14 / 20 nV/√Hz — state the mapping |
   | OTA 1/f corner | {100 k, 631 k, 2 M} Hz |
   | lf | {1, 9.3} |
   | vres | {0, 5, 20 µV} |
   | Vos2 | {1, 9, 20 mV} |
   | comp_offset | {5, 20, 50 mV} |
   | comp_noise | {0.1, 1, 5 mV} rms |
   | τ_in | {1, 10, 45} ns |
   | τ_ref | {2.5, 10, 45} ns |
   | Reset residue r on x1 | {1e-2, 1e-3, 1e-4}, by injecting a nonzero initial x1 |
   | Virtual-ground leakage | I_leak {10 pA, 100 pA, 1 nA} → offset I/(fs·Cs) at fs 0.25 and 2 MHz |

   - For reset residue, report the closed-form check 2·r·x1max/(c1(N−1)).
   - For leakage, implement it as an equivalent constant input-referred offset. State that it cancels in sys pairs only if it is signal-independent, and flag that as an assumption.
   - **Expected-value checks (theory, not the model):**
     - offset terms: lf·Vos1/(N−1) and 2·Vos2/(c1(N−1)) with sys off;
     - kT/C noise scaling ∝ 1/√Cs;
     - reset residue formula;
     - leakage I/(fs·Cs).
3. **Stage-2 sizing.** Propose Cs2/Cint2 (c2 = 0.5) from (a) kT/C of stage 2 divided by the stage-1 gain, (b) area, and (c) x2 swing vs comparator offset and noise. Option: c2 = 0.25 halves x2; that is allowed if the comparator budget still holds.
4. **Allocation table.** Split each budget (noise, INL, offset, gain error) across the blocks (OTA1, OTA2, comparator, switches/charge injection, reference path, clock/settling, leakage, reset, quantization floor). From the sweeps, derive the **per-block spec** that meets its share; state the margin.
   - The OTA linearity spec takes the form "A ≥ X dB with ≤ Y % drop at |Vout,diff| ≤ Z V" (review m4).
   - The comparator spec states offset, noise, decision time < 0.3·t_half, and a kickback limit as a fraction of the minimum x2 step.
   - Hand-calc rows from the review that the model can't sweep go in as hand-calc rows, marked as such:
     - GBW/slew at 2 MHz with β = 0.75 (Cs 0.5 pF changes β: recompute)
     - TG Ron at ss/−40/3.0 V
     - reset window ≥ 15 τ
4b. **Area and power estimate** at the design point:
   - MIM area for all caps at 2 fF/µm² ×1.5 overhead
   - OTA currents implied by GBW and slew at the real load
   - against the 2x2 tile budget and ≤ 200 µA
5. **Report** in `results/s3_budget.md`:
   - the design point
   - the sweep tables
   - the theory checks
   - the allocation table with margins
   - the per-block spec table, ready to paste into SPEC §3
   - the area/power estimate
   - open risks (things not modelled: substrate coupling, MIM VCC, chopper charge-injection spikes)

## Acceptance (Haiku, sandbox, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `python3 -m pytest design/tests model/tests -q` | all pass |
| 2 | CINT1 = 2 pF copy | params test fails |
| 3 | `python3 -m model.studies.s3_budget --out <dir>` | md + json; every theory-check line PASS; allocation sums ≤ budgets; prints `ACCEPT` only if every per-block spec meets its share with the stated margin, else `REJECT` with the failing row (exit 1) |
| 4 | `s3_budget --nonvac` | a budget run with A0 70 dB / a0_drop 0.9 / vlin 0.8 V REJECTs on INL |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `design: params at decided point (Cs 0.5 pF, N 4096 precision, ua3 VREF-, Vos 9 mV)`
2. `model: S3 sensitivity sweeps with theory checks`
3. `model: S3 error budget, allocation and per-block specs + results`

## Budget and stop rule
At most 80 tool calls. Use `--bg` for long runs. `rta-tt` is shared: retry on busy, and always `cd /home/mempool/tt-sd`. Finish by reporting "k of 6 items done, with reasons". If a block cannot meet its share at any sensible value, report it as a finding; don't relax the budget.
