# WO-07 (S5): tier-1 behavioural SC modulator in ngspice + simulator null test

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer.
**Spec source:** SPEC.md §1, §3.0, §3.6–3.7; PLAN.md S5 and its review additions; REVIEW-spec-plan F3/F9 (simulator null test, residue reconstruction); Paul Thomas's tier-1 (`repos/sd-analog/pthomas-sigma-delta-design/xschem/tier1_sdm.sch`, `sim/snr.py`, `params.py`), used as a pattern only.
Read `work/v1-design/HANDOFF.md` first.

## Goal
An **independent** SPICE implementation of the decided loop that cross-checks the Python model. It must not import iadc.py for expected values. Expected values come from theory: the CoI reconstruction formula, residue reconstruction, and the ideal-quantizer DC transfer.

## Files you may touch (nothing else)
- `design/tier1/` (new): decks, generator script, `tier1_tb.py`, README
- `design/params.py`: only to add tier-1 / simulator option constants
- `design/tests/test_tier1.py` (new)
- `work/v1-design/results/s5_tier1.{md,json}` (new)

Don't touch `model/` (WO-06 owns it) or SPEC.md.

## Items
1. **Deck generator.** `design/tier1/gen_tier1.py` writes the ngspice deck from `design/params.py` (single source of truth):
   - fully differential SC order-2 CIFB at the design point: c1 .125 (Cs 0.5 pF / Cint1 4 pF), c2 .5 (Cs2 0.5 / Cint2 1 pF), k .5 (separate 0.25 pF k-DAC cap on full VREF, D25), shared Cs1 for input and DAC
   - bottom-plate two-phase non-overlapping clock at 2 MHz
   - Cs2 samples x1 in OTA1's hold phase (D25)
   - **behavioural OTA**: B-source / VCVS with finite A0, a single pole for GBW, slew limiting and output-swing clamp. Parameters come from params.
   - ideal switches (`sw` model with Ron/Roff); ideal comparator with a latch on the clock edge
   - reset phase ≥ 2 cycles
   - 500 Ω + 5 pF pad models on VIN± and VREF±
   - digital counting (ΣS, S) in Python post-processing of the sampled comparator output
2. **Simulator null test.** With ideal OTA (A0 1e9, huge GBW/SR) and ideal switches, the deck must reproduce the theory DC transfer to < 1/10 of the INL budget (2 ppm), using residue reconstruction u = (ΣS + (k/c1)S + x2[N]/(c1c2))/(N(N−1)/2) with x2[N] read from the sim.
   - Sweep `reltol` {1e-3, 1e-4, 1e-5}, `chgtol`, and `method` {trap, gear}. Pick the loosest setting that passes. Freeze it in `params.py` as `SPICE_OPTIONS`.
   - Report run time per conversion.
3. **Tier-1 DC transfer.** Behavioural OTA at the spec limits (A(0) 80 dB, GBW 10 MHz, SR 12 V/µs, swing clamp ±1.4 V diff). About 9–15 DC points over ±0.9 FS at N = 256 with residue reconstruction (short windows, F9).
   - Report INL and gain error.
   - Theory expectations: INL ≪ 8 ppm; gain error ≈ −1/(A0·something). The model's S3 joint run gave 3.4 ppm INL; that is listed for comparison only, not as a pass criterion.
4. **OTA requirement sweep** (Paul's `spec_sweep` pattern, REVIEW F3): one at a time A0 {60, 70, 80} dB, GBW {2, 5, 10, 20} MHz, SR {3, 6, 12, 25} V/µs at 2 MHz and at 4 MHz, at a reduced point set (5 DC points, N 256). Find the knee for each.
   - These are the first numbers in the project that include **OTA dynamics**; the model has none.
   - Flag any knee that is above the SPEC §3.0 value.
5. **Non-vacuity:** each must REJECT:
   - a DAC-polarity-flipped deck (loop unstable / codes wrong);
   - c1 doubled (transfer gain wrong vs theory);
   - an OTA with A0 50 dB (INL above budget).

## Acceptance (Haiku, frozen copy, sandbox; ngspice from the IIC image or nix; record which)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest design/tests -q` | pass |
| 2 | `python3 design/tier1/tier1_tb.py --null` | null test ACCEPT at the frozen SPICE_OPTIONS (< 2 ppm vs theory) |
| 3 | `tier1_tb.py --dc` | INL ≤ 8 ppm at spec OTA; ACCEPT |
| 4 | `tier1_tb.py --sweep` | knee table written |
| 5 | `tier1_tb.py --nonvac` | the 3 broken decks REJECT; exit 1 |

Every ngspice run is checked per WORKFLOW §11 analog false-pass list:
- the final sim time equals tstop;
- no `failed` measurement;
- the models/options actually loaded, read from the log;
- the netlist is grepped for the intended ideal parts only.

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `design: tier-1 SC modulator deck generator`
2. `design: tier-1 simulator null test, frozen SPICE options`
3. `design: tier-1 DC transfer, OTA requirement sweep, non-vacuity + results`

## Budget and stop rule
At most 90 tool calls. Use `--bg` for every multi-conversion run; at most 3 parallel ngspice processes, under `nice -n 10` and `timeout`. If one N = 256 conversion takes more than 5 min, report it and reduce the scope (fewer points); don't drop the null test. `rta-tt` is shared: retry on busy, and always cd explicitly. Use scp of specific files for results. Finish by reporting "k of 5 items done, with reasons".
