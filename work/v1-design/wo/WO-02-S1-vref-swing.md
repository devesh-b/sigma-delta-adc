# WO-02 (S1): VREF / integrator-swing study (option A 1.2 V vs option B 2.048 V with c1 = 0.125)

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer reviews it before accept.
**Spec source:** SPEC.md §1 VREF row, §2.1, §2.3, §5 item 1; PLAN.md S1; DECISIONS D3.
Read `work/v1-design/HANDOFF.md` first.

## Why
The model ran at VREF = 2.048 V. SPEC proposes 1.2 V so the OTA output swing stays comfortable on 3.3 V. Option B keeps 2.048 V and halves the swing with c1 = 0.125. This WO decides which options meet the v1 targets.

**The key flaw to fix first:** today's swing-dependent gain uses `xswing` in units of VREF. Real OTA linearity is set in **volts** per side. Comparing VREF options needs the gain drop expressed in volts.

## Files you may touch (nothing else)
- `model/iadc.py` (edit)
- `model/studies/__init__.py` (new)
- `model/studies/s1_vref.py` (new)
- `model/tests/test_iadc_regress.py` (new)
- `work/v1-design/results/s1_vref.md` (new)
- `work/v1-design/results/s1_vref.json` (new)

WO-03 runs in parallel and does **not** touch `iadc.py`. You own `iadc.py` for this WO.

## Model changes (`iadc.py`), backward compatible
1. **Linear range in volts.** Add an optional `vlin_diff` (volts, differential output at which gain has dropped by `a0_drop`). If `vlin_diff` is set, the gain drop uses `(x·vref)/vlin_diff`. If it is unset, behaviour is identical to today (`xswing`).
2. **White-noise split.** Split OTA noise so that:
   - offset and flicker use `lf_gain`, as today;
   - **OTA white noise** uses `noise_gain = 1 + 1/c1 + cp_ratio`, which depends on c1. That is 5.3 at c1 = 0.25 and 9.3 at c1 = 0.125.

   This matters because option B raises the white noise gain.
   - Document in a comment how sampled white noise is counted today: `ktc_excess` plus the white floor in `flicker_series`. Don't double count.
   - If you change the accounting, state the old and new numbers.
3. **Peak swing output.** `convert(..., return_state=True)` must expose the max |x1| and |x2| (units of VREF) so swing can be reported in volts per side: `0.5·|x|·vref`.
4. **Regression test** `model/tests/test_iadc_regress.py`: with the new fields unset, `report_design.md` design-point numbers are reproduced within seed noise:
   - noise 2.51 / 1.31 / 0.51 / 0.26 µV ±10 %
   - INL 71 ppm ±10 %
   - gain error −459 ppm ±10 %

   Expected values come from `model/out/report_design.md` (pre-change).

   **Non-vacuity:** the test must fail if `a0_drop` is set to 0.

## Study (`model/studies/s1_vref.py`, CLI, writes md + json)
**Options:**
- **A:** VREF 1.2 V, c1 = 0.25, c2 = 0.5, k = 1.
- **B:** VREF 2.048 V, c1 = 0.125. Re-tune c2 and k: sweep c2 ∈ {0.25, 0.5, 1.0} and k ∈ {0.5, 1, 2}. Keep the combination that has both integrators within ±1.2 (in units of VREF·c-scaling) **and** keeps resolution ≥ 2·log2(N) − 4 at N = 1024.
- **C** (reference): VREF 2.048 V, c1 = 0.25 (today's model).

**For each option** (fs = 2 MHz, Cs = 1 pF, OTA + system chop, vos = 3 mV, vres = 5 µV, A0 = 75 dB, a0_drop = 0.9):
- Noise at 240/60/15/3.75 SPS (lf_gain 1 and 5.3).
- Effective bits over FSR = 2·VREF.
- Quantization bits at N = 1024 and 4096.
- Peak |x1|, |x2| in **volts per side**.
- INL in ppm for `vlin_diff` ∈ {1.5, 2.0, 2.5, 3.0} V differential.
- Integrator-cap area: Cint1 = Cs/c1, so 8 pF per side for B. Use 2 fF/µm² MIM and report µm².

**Theory checks** (expected values from theory, not from the model):
- Effective-bit difference between A and C = log2(2.048/1.2) = 0.77 b ±0.05.
- Peak swing per side for C ≈ 0.6·2.048 ≈ 1.23 V (SPEC §2.1). Report the measured value next to it.

**Pass criterion for an option:**
- noise ≤ 50 µV @ 15 SPS (lf_gain 5.3, pessimistic)
- INL ≤ 100 ppm at `vlin_diff` = 2.0 V
- peak swing per side ≤ 0.9 V around CM = 1.65 V (output stays within 0.75–2.55 V)

Print `ACCEPT`/`REJECT` per option. The study **does not choose**: it reports which options pass, then a recommendation with reasons. The user picks (D3).

**Non-vacuity:** with `vlin_diff` = 0.5 V, option A's INL criterion must REJECT. Show it.

## Acceptance (Haiku, sandbox, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `python3 -m pytest model/tests -q` | pass |
| 2 | regress test with `a0_drop` = 0 | fail |
| 3 | `python3 -m model.studies.s1_vref --out /home/mempool/regr/tt/WO-02` | md + json, one ACCEPT/REJECT line per option, theory-check lines PASS |
| 4 | same with `--vlin 0.5` | option A REJECT on INL |
| 5 | `python3 model/run_studies.py design` | numbers match `report_design.md` ±10 % |

Run time is about minutes, so use `--bg`.

## Commits (explicit paths, no attribution trailer, no push)
1. `model: OTA linear range in volts, white-noise gain split, peak-swing output (backward compatible) + regression test`
2. `model: S1 VREF/swing study + results`

## Budget and stop rule
At most 60 tool calls. Finish by reporting "k of 2 commits done, with reasons". If the option-B retune finds no stable c2/k, report that as a result. Don't widen the search.
