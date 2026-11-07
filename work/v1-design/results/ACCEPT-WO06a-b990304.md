# WO-06a acceptance (S4 re-gate), frozen copy of tree at b990304

- Frozen copy: `/home/mempool/regr/tt/acc06a-b990304`.
- Row 1 was run by the Haiku tester.
- Rows 2–3 were completed by the coordinator using direct ssh plus nohup. The tester was blocked by the rta-tt lock.

| # | Command | Expect | Result | Evidence |
|---|---|---|---|---|
| 1 | `pytest model/tests -q` | pass | PASS: 54 passed | tester stdout |
| 2 | `s4_corners --out <copy>/out` | ACCEPT, exit 0 | **EXIT 1, known finding.** Gates: grid (n15, n240, INL, gain, offset, memory) ACCEPT; MC INL/gain/offset ACCEPT; CMRR sys-on ≥ 100 dB ACCEPT; **CMRR sys-off ≥ 60 dB REJECT at 16 points** (worst 44.0 dB at ff/125/3.6, fs 0.25 MHz, ε 6334 µV/V). | `row2.log` |
| 3 | `s4_corners --nonvac` | REJECT including the CM-after-swap copy, exit 1 | PASS: REJECT, EXIT 1. The 7 broken copies all fail and are named:<br>• A(1.4 V) 60 dB → INL 43.8 ppm<br>• reset r 1e-2 → mem 30.6 µV<br>• sys chop off → off 102.5 µV<br>• Cs/100 → n15 5.66 µV<br>• τ_in 2 µs → gain 2.06e4 ppm<br>• **CM after swap → sys-on 42.5 dB**<br>• Cs mismatch 3 % → sys-off 30.5 dB | `row3.log` |

**Verdict.** The gate behaves as designed. The only REJECT is the sys-off CMRR line. REVIEW-S4S5b C-M3 dispositions it:
- the S4 term ε·ΔVcm models a mechanism that D12 cancels;
- it is to be replaced by the D12 residual ε_eff (ΔCp,top), expected about 65 dB;
- the 60 dB gate moves to C4, on post-layout extraction plus MC.

S4 closes once that correction lands.
