# WO-06a (S4 re-gate): apply user decisions D27–D30 to the S4 corner gate

Coordinator-written, 2026-11-07. **Tier: routine.**
**Spec source:** SPEC.md §3.0 ("User decisions after S4/S5"), DECISIONS D27–D30.
Read `work/v1-design/HANDOFF.md` first.

## Files you may touch (nothing else)
- `model/studies/s4_corners.py`
- `model/tests/test_s4_corners.py`
- `work/v1-design/results/s4_corners.{md,json}`

## Items
1. **Noise @15 SPS limit.**
   - ≤ 2.5 µV at fs 2 MHz, all corners.
   - At fs 0.25 MHz: ≤ 2.5 µV up to 85 °C, and ≤ 3.0 µV at 125 °C (D27).
   - Print the applied limit per row.
2. **Noise @240 SPS.** The limit is 5 µV (D29), now gated and no longer assumed. Rows where 240 SPS is unreachable stay reported but not gated, and are labelled as such.
3. **CMRR (D30).**
   - Add the input-CM axis: Vin_cm ∈ {0.2, 1.0, 2.0} V, with Cs+/Cs− mismatch from the MC draws (0.75 % 3σ).
   - Model it as a CM→diff term ε·(Vin_cm − Vref_cm) referred to the input **before the pin-side swap**. That means it is the same for both halves of a sys pair. Demodulate exactly as the chip does.
   - **Gate:** CMRR ≥ 100 dB with sys chop on, ≥ 40 dB with sys chop off, at tt/27 and at the worst MC draws.
   - **Theory check:** sys-off error = ε·ΔVcm; the sys-on residual is ≈ 0.
   - **Non-vacuity:** a copy that applies the CM term *after* the swap, so it flips with the input, must fail the sys-on gate.
   - Note in the md that this models the hypothesis; WO-08 checks it in SPICE.
4. **Re-run the full S4.** Expect ACCEPT, exit 0. If anything still fails, report it as a finding.

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest model/tests -q` | pass |
| 2 | `s4_corners --out <dir>` | ACCEPT, exit 0; per-row limits printed; CMRR table |
| 3 | `s4_corners --nonvac` | REJECT, including the CM-after-swap copy; exit 1 |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `model: S4 gate limits per D27/D29, CMRR axis per D30 + results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget and stop rule
At most 40 tool calls. `rta-tt` is shared: always `cd /home/mempool/tt-sd`, and retry on busy. Use `--bg` for the full run, which takes about 6 min. Finish by reporting "k of 4 items done".
