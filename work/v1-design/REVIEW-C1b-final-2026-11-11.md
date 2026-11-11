# REVIEW-C1b-final-2026-11-11: OTA1 + CMFB milestone (WO-27..31, D59–D64)

Reviewer: sd-adc-design-reviewer. Read-only. Condensed by the coordinator.

## Verdict
**PROCEED. No Critical finding.** C1b cannot close yet: M1, M2 and the verification order below remain.

Confirmed from the logs:
- Dual-path topology and signs are correct.
- Nominal CM PM ≥ 77.4°, peaking ≤ 0.58 dB. The 65.9° / 1.87 dB in the README come from the mcc4 broken copy.
- Start-up clamps have no zero-current state.
- The hand Pelgrom rows reproduce (σ I_tail 1.11 %, V_OCM 3σ 6.9–7.8 mV) and survive A_VT 15.
- D64 is benign: ph2 static CM 0.8–1.5 mV; gate B fs/125 3.31 → 2.17 ppm.
- D63 is the right basis.
- The broken copies mcc4, masy, mio and mcr05 all REJECT.

## Major
- **M1: the C6 reference accuracy the rows need cannot be built untrimmed.**
  - The SR floor and the ceiling leave an I_REF_btp window of about −2 % / +1.6 %; untrimmed sky130 is about ±10–20 %.
  - The SR floor of 12.5 V/µs is itself about 1.22 × the gate-B knee (≈ 10.2 V/µs base).
  - Locations: `c1b_opac.py:65,67,316–323`.
- **M2: the CM-to-DM row cannot fail on the symmetric netlist.** ev − ev0 is only the numerical floor.
  - masy at 1e-4 gives 0.55 µV. At realistic 1e-3 mismatch that is about 5 µV, roughly 20× the 0.256 µV bound.
  - Untested mechanism: Cc/Cr p/n mismatch turns DM swing into CM (δ·Vd/2), which is signal-dependent.
  - Need: a 3σ mismatch copy, and a bound restated for the signal-dependent part only.

## Minor
- m3: the start-up row measures steady CM ripple (sulo8, settled long before, reads 9.06 vs sulo 9.56 mV). The 4 µs comes from CL-7, not from a power-up need.
- m4: SPEC.md:98 still says "≤ 10 mV in 0.2·t_half" (pre-D63).
- m5: sr95 at 9.5 V/µs (38 % of the floor) only proves the gate catches a gross fault. Add a near-knee (≈ 0.8 × floor) boost copy.
- m6: gate B does not run sf/−40 or ff/−40 nominal (worst CM PM and SR/ceiling).
- m7: the output clamp is a weak PMOS pulling to 1.5 V. A transmission gate would add margin at 0 µA.
- m8: bank switch Sbk/mbku need a 3.3 V level shift and break-before-make (ivbpc shorts to vdd if both are on).

## C6 / SPEC items
- SPEC row 98 text.
- C6 reference accuracy relative to the knee.
- Start-up sequencer: rstb ≥ 2 T after bias-valid, clamps, then the dummy conversion.
- Boost bank control: level shift, break-before-make, toggle at a pair boundary.
- ivbl0 must absorb the clamp currents.

## Questions → user (2026-11-11)
- Q1: start-up criterion.
- Q2: SR floor vs C6 reference.
- Q3: CM-to-DM row.
- Q4: output clamp as a transmission gate.

## Recommended next-WO order
1. Row fixes + near-knee copy.
2. Noise (OTA1 + CMFB, thermal and 1/f vs chop).
3. tb12/tb11, which freeze the C6 interface.
4. Hand MC with delvto injection, A_VT 12, ≥ 200 tt + ≥ 50 worst PVT, plus a ×3 broken copy.
5. Stress/SOA at start-up.
6. 45 PVT for op/AC and tb9, plus gate B at sf/−40 and ff/−40. PEX comes at layout.
