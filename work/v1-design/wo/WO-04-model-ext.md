# WO-04 (S1/S2 follow-up, S3 prerequisite): model extensions + S1 INL re-run at the D17 point

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer reviews it before accept.
**Spec source:** `work/v1-design/REVIEW-S1S2-2026-11-07.md` (M1, M2, m1, m6, m7); SPEC.md §1, §3.6; DECISIONS D14, D15, D17–D19.
Read `work/v1-design/HANDOFF.md` first.

## Files you may touch (nothing else)
- `model/iadc.py`
- `model/tests/` (new tests only)
- `model/studies/s1_vref.py`
- `model/studies/s2_theory.py`
- `model/studies/s2_chop.py`
- `work/v1-design/results/s1_vref_v2.{md,json}` (new)
- `work/v1-design/results/s2_chop_v2.{md,json}` (new)

Leave the old s1/s2 result files unchanged; they are the record. Do not touch `design/` (WO-01a owns it).

## Items
1. **OTA2 offset and x1 output-offset injection (M2).** Add `vos2` (OTA2 input offset, V) and `x1_offset` (constant offset on x1, V) to `iadc.convert`. Both default to 0, which must reproduce today's behaviour bit-for-bit.
   - Theory, in `s2_theory.py` and independent of iadc: u_err = 2·e2/(c1(N−1)) for each, where e2 = vos2/vref or x1_offset/vref.
   - Test: model matches theory within 10 % at N ∈ {256, 1024, 4096} for c1 ∈ {0.25, 0.125}. The test must fail on a copy that injects e2 with the wrong sign or scale.
2. **Order-1 residue term (m1).** Add to `s2_theory`: OTA-chop-only order 1 gives lf·Vos/N for N even.
   - Verify with paired differences at M ≥ 65536 for N even and odd. Expected for N = 512: about 17.6 µV per 9 mV.
   - Do **not** change the order-1 output reconstruction.
3. **S1 INL re-run at the decided point (M1).**
   - Settings: N = 4096 **and** residue-reconstructed INL at N = 1024, u = (ΣS + (k/c1)S + x2[N]/(c1c2))/(N(N−1)/2), using x2 from return_state.
   - A0 = 80 dB (D15), `ref_mode="shared"` (D14), vlin 2.0 V.
   - Options: A, A_half (1.2 V, c1 .125, k .5), B, B_half-Cs (B with Cs 0.5 pF, Cint1 4 pF), C.
   - Report the ideal-OTA quantization floor next to each value. Expected values come from the review probes:

     | Option | Expected INL, N 4096 / A0 80 dB |
     |---|---|
     | A | 9.3 ppm |
     | A_half | 1.4 ppm |
     | B | 3.7 ppm |
     | C | 541 ppm |
     | floor | 0.5 ppm |

     Agreement ±20 %, or explain.
4. **Reference recovery sweep (m6),** at the B point with shared Cs. Pin R = 500 Ω. On-chip decap ∈ {0, 2, 5, 10, 20} pF plus the 5 pF pad, so τ_ref = 500 Ω × (5 pF + decap).
   - Report INL and gain error.
   - Report the smallest decap that keeps INL ≤ 1/3 of the 100 ppm budget, plus its MIM area at 2 fF/µm².
5. **Quantization floor at fixed DC (m7).** For the averaged modes (K = 2…64 pairs) at N = 1024 and 4096, report the deterministic error that averaging does not remove (max |error| over a fine DC grid), alongside the rms noise.
6. **Noise at the D17 point.** Re-run noise (ota+sys and sys-only) at the B point, with lf ∈ {1, 9.3} (B's own noise gain) and Cs ∈ {1, 0.5} pF. Rates are 240/60/15/3.75 SPS.

## Acceptance (Haiku, sandbox, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `python3 -m pytest model/tests -q` | all pass, including the old regression test (bit-identical with new fields at 0) |
| 2 | e2 wrong-sign broken copy | the e2 theory test fails |
| 3 | `python3 -m model.studies.s1_vref --v2 --out <dir>` | INL table with floor; A, A_half, B, C within ±20 % of the item-3 expected values |
| 4 | `python3 model/studies/s2_chop.py --v2 --out <dir>` | OTA2/x1-offset model-vs-theory lines PASS; order-1 residue line PASS |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `model: OTA2 offset and x1 offset injection (default off, bit-identical) + theory tests`
2. `model: order-1 OTA-chop residue theory`
3. `model: S1 v2 INL at D17 point (N 4096, residue, A0 80, shared Cs), ref-recovery and quant-floor studies`
4. `model: S2 v2 noise at D17 point`

## Budget and stop rule
At most 70 tool calls. `rta-tt` is shared: on "busy", retry, and always `cd /home/mempool/tt-sd` explicitly. Use `--bg` for runs longer than 2 min. Finish by reporting "k of 6 items done, with reasons".
