# S5 tier-1 behavioural SC modulator in ngspice (WO-07)

Command: `python3 design/tier1/tier1_tb.py --{null,options,dc,sweep,nonvac}` on the sandbox (tree `tt-sd`), nix ngspice 45 (not the IIC image), `nice -n 10`.
Raw outputs: `/home/mempool/regr/tt/WO-07/` (`run_all.txt`, per-run `.cir/.log/.csv`); numbers in `s5_tier1.json`.
Expected values are theory: ideal quantizer transfer u_hat = u_in with residue reconstruction (SPEC 3.7), x2[N] read from the sim. No model/iadc.py.
INL = endpoint, ppm of FSR (FSR = 2 in u). Deck: SPEC 3.0 design point, 2 MHz, N = 256, reset 3 cycles, Ron 1 kohm (null: 1 ohm), pads 500 ohm + 5 pF.

## Frozen SPICE_OPTIONS (design/params.py)
`method=gear reltol=1e-3 chgtol=1e-14 vntol=1e-6 abstol=1e-12 trtol=7 tmax=10 ns`.
Rule: loosest of 18 (reltol {1e-3,1e-4,1e-5} x chgtol {1e-14,1e-15,1e-16} x method {trap,gear}) that passes the null test (5 points, N 256) and runs the spec deck cleanly. 9 of 18 pass.
- Null error at the frozen options: **4.64e-7 in u (tol 2e-6)**, the same floor (4.6e-7) at every passing setting, so it is not option noise. Cause (REVIEW-S5 m2, proven by probe): the reset-switch Roff = 1e12 ohm across Cint1, hand value k/(Roff*fs*Cs1) = 5e-7; with Roff 1e14 it drops to about 7e-9 (shown again in WO-08 `--offsets`, baseline 0.0025 uV). It is not the 1e13 plate bleeders. Real reset-switch leakage at 125 C (50 pA, about 6 Gohm) would give about 80 ppm gain and is nonlinear, so C needs a leakage row.
- trap fails at reltol 1e-3 (null error 1.8e-5 to 6.5e-5); trap 1e-4 passes (cross-check: spec INL 0.174 vs 0.176 ppm at gear 1e-3). trap at 1e-5 and several tight settings stop with "timestep too small" or a singular-matrix warning on the floating k-DAC plate (nodes bkp/bkn); the run checks catch these (final time != tstop).
- First attempt with trap 1e-4 on an earlier deck died at t = 68.5 us (timestep too small): kept as the broken-copy case for the truncation check (`test_truncated_run_is_caught`).

## Acceptance
| # | Check | Result |
|---|---|---|
| 1 | `pytest design/tests -q` | 20 passed |
| 2 | `--null` | ACCEPT, 4.64e-7 (tol 2e-6) |
| 3 | `--dc` | ACCEPT: INL 0.29 ppm (endpoint), 0.18 ppm (best fit), gain error -5.70e-5, offset +3.8e-8 |
| 4 | `--sweep` | knee table below, 36 runs, all clean |
| 5 | `--nonvac` | dac_flip err 2.06, c1x2 err 1.4e-2, A0 50 dB INL 14.05 ppm (> 8): all REJECT; plus no-residue reconstruction err 1.8e-4 REJECT; exit 1 |

## DC transfer at the spec OTA (A0 80 dB, GBW 10 MHz, SR 12 V/us, clamp +-1.4 V diff), 11 points over +-0.9 FS
Error u_hat - u_in = -5.7e-5 * u (51.6 ppm at u = -0.9 ... -51.6 ppm at +0.9, +0.35 ppm at 0): a pure gain error, so INL is only 0.29 ppm.
Gain error -5.7e-5 is about -1.09*k/A0 = -5.5e-5 (virtual-ground error times the mean x1, which equals k*u; independent of c1; REVIEW-S5 m1; the earlier '(1+c1)/(2 A0)' was a coincidence of numbers and is withdrawn). It scales 10x per 20 dB in the sweep. Comparison only: the S3 model joint run gave 3.4 ppm INL; tier-1 has constant A0 (no A(v) swing dependence), so it measures dynamic (settling, slew) INL and not the OTA output-stage nonlinearity.
Run time: 0.9 s per N = 256 conversion (11 conversions 10 s; null 5 conversions 5.7 s, 1.1 s each; sandbox load average 5-9, so expect ~2x faster on a quiet box). 22k data points per 1.4 ms, final time == tstop.

## OTA knee table (INL <= 8 ppm, one parameter at a time, N 256, 5 points, other parameters at the base)
INL in ppm FSR (gain error in brackets only where useful).

| Param | value | 2 MHz (base 80 dB / 10 MHz / 12 V/us) | 4 MHz, spec base (80 / 10 / 12) | 4 MHz, GBW 20 MHz base (80 / 20 / 12) |
|---|---|---|---|---|
| A0 (dB) | 50 | 14.05 | 51.6 | 15.97 |
| | 60 | 3.71 | 60.4 | 6.72 |
| | 70 | 1.02 | 62.6 | 3.82 |
| | 80 | 0.18 | 63.4 | 2.95 |
| GBW (MHz) | 2 | 18.99 | 70.6 | 70.6 |
| | 5 | 6.54 | 157.4 | 157.4 |
| | 10 | 0.18 | 63.4 | 63.4 |
| | 20 | 0.41 | 2.95 | 2.95 |
| SR (V/us) | 3 | 59.11 | 4393 | 4501 |
| | 6 | 1.65 | 426.9 | 153.7 |
| | 12 | 0.18 | 63.4 | 2.95 |
| | 25 | 0.36 | 10.99 | 0.61 |

Knees (lowest swept value with INL <= 8 ppm): 2 MHz: A0 <= 60 dB (50 dB fails at 14 ppm), GBW 5 MHz, SR 6 V/us; all at or below SPEC 3.0. 4 MHz, spec base: no A0 or SR value passes because GBW 10 MHz is the limiter (63 ppm); GBW knee 20 MHz. 4 MHz, GBW 20 MHz base: A0 70 dB, GBW 20 MHz, SR 12 V/us.

## Flags against SPEC 3.0
- **4 MHz fast mode needs GBW >= 20 MHz** (the 20 MHz design target; the 10 MHz minimum gives 63 ppm INL there). SPEC 3.0 already states the 20 MHz target covers 4 MHz; this confirms it, and says the 10 MHz minimum does not. The fast mode has its own INL target (D13), so the 8 ppm line may not apply to it.
- **4 MHz needs SR >= 25 V/us for < 8 ppm at GBW 10 MHz base; at GBW 20 MHz, 12 V/us is enough (2.95 ppm).** With the spec base 12 V/us gives 63 ppm (GBW-limited), 25 V/us 11 ppm.
- No knee at 2 MHz exceeds SPEC 3.0. The A0 knee (<= 60 dB) is not a gain requirement: tier-1 has constant A0, so the A(v) swing dependence (SPEC 2.3, 75 dB at 1.4 V) is not exercised here.

## Run checks (WORKFLOW 11, analog false-pass list)
Per run: final time == tstop; log scanned for error/singular/timestep/failed/no-convergence; options and `.model SWM SW` read back from the log listing; comparator bits all +-1; netlist audit (V R C B S only; 28 SWM switches + 1 latch switch; no subckt, .lib, .include or transistor models). Ideal parts in the deck are listed in README and are the intended ones (sw switches, B-source OTA/comparator).
Non-vacuity shown in `--nonvac`: dac_flip, c1 doubled, A0 50 dB, residue dropped; `test_tier1.py` also checks the reconstruction fails with wrong k/c1, wrong c1, a foreign part in the deck, and a truncated run.

## Limits (open)
Constant A0, one pole (no PM, no second pole), no offset/noise/charge injection/clock feedthrough, ideal CMFB, switch Ron constant (no body effect), single-bit comparator without hysteresis or metastability, pads ideal. x2[N] is read at 5 ns before the conversion end (x2 held, OTA settled).
