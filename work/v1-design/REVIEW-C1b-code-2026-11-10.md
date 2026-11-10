# REVIEW-C1b-code-2026-11-10: static review of the WO-24 code (nothing run)

Reviewer: sd-adc-design-reviewer. The sandbox was unreachable, so this is a read-only review. Condensed by the coordinator.

## Verdict
**Hold the first run until must-fixes 1–10 are in.** The netlist core is wired correctly: connectivity, polarity, bulks, chopper pairing, SC CMFB polarity and bias arithmetic were all traced. The problems are in the testbenches and in the broken-copy logic.

## Major
- **M1: gate B drives `rstb` from the per-conversion reset**, so the CMFB clamp is open in every 750 ns reset.
  - The operating point at t=0 has no CM regulation, and CM drifts about 0.27 V per reset.
  - The first block (the u = −0.9 endpoint) starts inside a CM transient.
  - Fix: start-up-only `rstb`, one dummy first conversion, and CM-at-release reporting.
- **M2: the sr95 broken copy is rated at 1.4 pF.** The real integrate-phase load is about 0.84 pF, so the copy slews at about 16 V/µs and is probably blind.
  - Scaling only the tail current also distorts the operating point.
  - It is fail-open: a crash counts as "REJECTED (good)".
  - Fix: scale ≈ 0.22 from the real load (or a measured SR), scale all six bias ports, and count it as rejected only if the run is healthy and INL > gate.
- **M3: the kp sweep's p15 builds the same 30/4 device as p30** (`sz({})` copies the D55 sizes). So "does K_P 10 alone suffice" cannot be answered.
  - Fix: p15 = WF 5, M 3, L 2; assert the two differ.
- **M4: the c1b_opac per-phase loads predate D55.** With D55 they are 0.84 / 0.99 pF, not 0.78 / 0.90, so GBW at the real loads reads 8–12 % high.
  - Fix: derive the loads from the sizes.
- **M5: the opac mutant counts as REJECTED on any failure**, including lint lines and NaN. It also shares a deck with the tt corner.
  - Fix: count it as rejected only when A0 is finite and below the minimum; run it in its own deck.
- **M6: revc_inl exits 0 on an empty directory or a missing mutpcb2.**
  - Fix: require the expected row count and at least one evaluated must-reject mutant; treat a missing table as bad.
- **M7: gate B is fail-open** (part of M2).

## Minor
- **m1: the composite-reference test is blind to wiring.** Add chain, diode and rail assertions, a core connectivity table, and chopper pairing.
- **m2: β1 undercounts Cp_vg by about 45 fF** (β1 ≈ 0.838). Measure the island admittance with AC.
- **m3: the gate B audit filter masks everything.** Whitelist {X, I} and the specific tokens.
- **m4: no servo-lost row in opac.**
- **m5: a stale AC csv can be reused.** Delete it before each run.
- **m6: `combine()` in gate B is not implemented.** Add an endpoint-agreement assert.
- **m7: the 1.8 V fold chopper can be overstressed at bias start-up**, and the 1.62 V lv corner is never simulated.
- **m8: OTA-chop mode leaves load offset (≈ 0.1 mV) and 1/f noise unchopped.** System chop cancels both.
- **m9: c_out_ext of 0.02 pF is probably low.** Add a spec-basis 1.4 pF gate B copy.
- **m10: ota1_xtor silently ignores noise1 and the offset settings.**

## The author's flagged choices
- CM-only DC CMFB: sound.
  - Cr is a linear settling load, so it causes gain error, not INL.
  - A per-side averaged R would read about 15 dB of false A0 loss.
- 1.4 pF cl1: sound for the macro, but the transistor-deck numbers must be re-based to the real load.
- Composite references with bulk at the rail: sound and the right choice. A series-parallel association is equivalent to a single device; the error is < 1 % for L 2–4.
- Margin exclusions: sound. Add a fold-switch Vds row.
- ota1_xtor: loop sign and differential reset are preserved. CM regulation during reset is not (M1).

## Fix list
| # | Where | Change | When |
|---|---|---|---|
| 1 | revc_check PLC | p15 = WF 5 / M 3 / L 2; assert p15 and p30 differ | before step 1 |
| 2 | c1b_gateb:76 | rejected only if healthy and INL > gate | before gate B |
| 3 | c1b_gateb:24 | SR95 scale from the real load (≈ 0.22) or a measured SR; scale all six ports or report the op | before gate B |
| 4 | gen_tier1 xtor Brstb | start-up-only rstb, dummy first conversion, CM-at-release saves | before gate B |
| 5 | c1b_opac:31 | loads derived from sizes (≈ 0.84 / 0.99 pF) | before op/AC |
| 6 | c1b_opac:202 | mutant rejected only if A0 finite and below the minimum; separate deck | before op/AC |
| 7 | revc_inl main | expected row count, ≥ 1 evaluated mutant, missing table = bad, empty directory = REJECT | before the next INL run |
| 8 | c1b_opac:188 | remove the csv before running | before op/AC |
| 9 | c1b_opac analyse | servo-lost row | before op/AC |
| 10 | c1b_gateb:25,62 | audit whitelist | before gate B |
| 11–15 | tests, β1 by AC, combine(), xtor guards, start-up tb | later |

## Questions, with the coordinator's answers (D57)
- **Q1: is the ctl clamp tied to rst_n / bias-invalid, or to the per-conversion reset?**
  → **Start-up only (global rst_n / bias-invalid).** The CMFB runs through every conversion reset on silicon. DESIGN.md §1.3 wording to be made explicit.
- **Q2: gate B load basis?**
  → **The real netlist load plus a PEX estimate is authoritative.** A spec-basis copy (integrate-phase load 1.4 pF) runs as information (m9).
- **Q3: is OTA-chop mode still planned?**
  → **Yes, as characterisation only** (D4, D45g). The unchopped load offset (≈ 0.1 mV) and 1/f noise are recorded as an info row. System chop, the data mode, cancels both.
