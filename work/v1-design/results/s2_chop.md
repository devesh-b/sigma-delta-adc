# S2 chopping study (WO-03)

Command: `python3 model/studies/s2_chop.py --out /home/mempool/regr/tt/WO-03` (sandbox, ~13 min); md regenerated with `--render-only` after notes edits. Non-vacuity: `--nonvac`. Study script git blob of iadc.py used: see hash below.

fs = 2 MHz, Cs = 1 pF, kT/C on, flicker on (noise runs). iadc.py blob hash `c4269ba2152b6c9ef01d17c6ecc7bda8ec22309d`. Offset: 16384 stratified-DC conversions/point, differential vs a zero-offset run with identical random numbers (flicker off: it is zero-mean); noise: m_out = 32, flicker + kT/C on.

## Verdicts: |offset| <= 5 uV at Vos = 9 mV, vres <= 5 uV, all N, lf 1 and 5.3

Targets apply to sys and ota+sys at order 2 (the v1 mode, gates the exit code). Order 1 is informational: its differential estimate is quantisation-limited (see notes).

| mode | order 2 | worst uV | order 1 | worst uV |
|---|---|---|---|---|
| none | REJECT (no target) | 47726.47 | REJECT (no target) | 47714.23 |
| ota | REJECT (no target) | 211.55 | REJECT (no target) | 208.98 |
| sys | ACCEPT | 0.72 | REJECT | 12.70 |
| ota+sys | ACCEPT | 0.77 | REJECT | 11.72 |

## Mean offset, order 2, Vos = 9 mV, vres = 5 uV [uV], model / theory

| mode | lf | N=256 | N=1024 | N=4096 |
|---|---|---|---|---|
| none | 1.0 | 9002.23 / 9005.00 (sem 1.72) | 9004.92 / 9005.00 (sem 0.09) | 9005.00 / 9005.00 (sem 0.00) |
| none | 5.3 | 47720.42 / 47726.50 (sem 1.33) | 47726.19 / 47726.50 (sem 0.08) | 47726.47 / 47726.50 (sem 0.01) |
| ota | 1.0 | 38.44 / 40.29 (sem 1.21) | 13.79 / 13.80 (sem 0.07) | 7.20 / 7.20 (sem 0.00) |
| ota | 5.3 | 211.55 / 213.56 (sem 1.23) | 72.99 / 73.13 (sem 0.07) | 38.14 / 38.15 (sem 0.00) |
| sys | 1.0 | 0.72 / 0.00 (sem 2.22) | -0.01 / 0.00 (sem 0.10) | -0.01 / 0.00 (sem 0.00) |
| sys | 5.3 | 0.61 / 0.00 (sem 1.52) | -0.02 / 0.00 (sem 0.07) | -0.01 / 0.00 (sem 0.01) |
| ota+sys | 1.0 | 0.18 / 0.00 (sem 1.34) | -0.01 / 0.00 (sem 0.07) | -0.01 / 0.00 (sem 0.00) |
| ota+sys | 5.3 | 0.77 / 0.00 (sem 1.36) | -0.03 / 0.00 (sem 0.08) | 0.00 / 0.00 (sem 0.00) |

## Mean offset, order 1, Vos = 9 mV, vres = 5 uV [uV], model / theory

| mode | lf | N=256 | N=1024 | N=4096 |
|---|---|---|---|---|
| none | 1.0 | 8956.05 / 9005.00 (sem 62.05) | 8999.02 / 9005.00 (sem 13.53) | 9003.42 / 9005.00 (sem 0.46) |
| none | 5.3 | 47535.16 / 47726.50 (sem 20.99) | 47678.22 / 47726.50 (sem 8.50) | 47714.23 / 47726.50 (sem 3.53) |
| ota | 1.0 | 34.18 / 5.00 (sem 5.77) | 11.23 / 5.00 (sem 1.65) | 7.81 / 5.00 (sem 0.69) |
| ota | 5.3 | 208.98 / 26.50 (sem 14.19) | 74.22 / 26.50 (sem 4.22) | 38.21 / 26.50 (sem 1.50) |
| sys | 1.0 | 4.88 / 0.00 (sem 82.86) | 2.20 / 0.00 (sem 15.58) | 0.67 / 0.00 (sem 0.33) |
| sys | 5.3 | -12.70 / 0.00 (sem 20.83) | -0.73 / 0.00 (sem 8.79) | -0.92 / 0.00 (sem 4.16) |
| ota+sys | 1.0 | -3.91 / 0.00 (sem 5.35) | 1.22 / 0.00 (sem 1.56) | 0.55 / 0.00 (sem 0.60) |
| ota+sys | 5.3 | 11.72 / 0.00 (sem 14.15) | -2.20 / 0.00 (sem 4.29) | 2.62 / 0.00 (sem 1.52) |

## Model vs theory, OTA chop only, order 2

Theory (s2_theory.py): offset = lf*(Vos*r(N) + vres), r = 1/(N-1) for order 2, 0 for order 1 (N even). 54 of 54 grid points agree (within 20 %, or 4 sem, or 0.5 uV). Worst relative deviation where |theory| >= 10 uV: 9.6 %.

## Model vs theory, OTA chop only, order 1

Theory (s2_theory.py): offset = lf*(Vos*r(N) + vres), r = 1/(N-1) for order 2, 0 for order 1 (N even). 33 of 54 grid points agree (within 20 %, or 4 sem, or 0.5 uV). Worst relative deviation where |theory| >= 10 uV: 688.6 %.
- DISAGREE N 256 lf 1.0 Vos 9.0 mV vres 0.0 uV: model 29.30 theory 0.00 (sem 5.34)
- DISAGREE N 256 lf 1.0 Vos 9.0 mV vres 5.0 uV: model 34.18 theory 5.00 (sem 5.77)
- DISAGREE N 256 lf 1.0 Vos 9.0 mV vres 20.0 uV: model 50.78 theory 20.00 (sem 7.03)
- DISAGREE N 256 lf 5.3 Vos 1.0 mV vres 0.0 uV: model 18.55 theory 0.00 (sem 4.25)
- DISAGREE N 256 lf 5.3 Vos 3.0 mV vres 0.0 uV: model 54.69 theory 0.00 (sem 7.30)
- DISAGREE N 256 lf 5.3 Vos 3.0 mV vres 5.0 uV: model 78.12 theory 26.50 (sem 8.71)
- DISAGREE N 256 lf 5.3 Vos 3.0 mV vres 20.0 uV: model 164.06 theory 106.00 (sem 12.59)
- DISAGREE N 256 lf 5.3 Vos 9.0 mV vres 0.0 uV: model 181.64 theory 0.00 (sem 13.24)

## rms noise [uV], order 2 (Vos 9 mV, vres 5 uV; rms excludes DC offset)

N = 256 rows are quantisation-limited (order 2, ~12 b): values there are not OTA-noise. Order-1 noise is not tabulated: its quantisation error (about 1/N of FS) is deterministic at a fixed DC input, so the sample rms is 0 or dominated by code flips (raw values are in the json).

| mode | lf | N | 240 SPS (actual) | 15 SPS (actual) |
|---|---|---|---|---|
| none | 1.0 | 256 (quant-limited) | 7.99 (244) | 6.53 (15.0) |
| none | 1.0 | 1024 | 12.47 (244) | 12.22 (15.0) |
| none | 1.0 | 4096 | 12.94 (244) | 13.33 (15.3) |
| none | 5.3 | 256 (quant-limited) | 79.94 (244) | 67.20 (15.0) |
| none | 5.3 | 1024 | 67.69 (244) | 64.86 (15.0) |
| none | 5.3 | 4096 | 69.00 (244) | 70.39 (15.3) |
| ota | 1.0 | 256 (quant-limited) | 35.28 (244) | 8.13 (15.0) |
| ota | 1.0 | 1024 | 2.07 (244) | 0.43 (15.0) |
| ota | 1.0 | 4096 | 1.95 (244) | 0.57 (15.3) |
| ota | 5.3 | 256 (quant-limited) | 0.00 (244) | 0.00 (15.0) |
| ota | 5.3 | 1024 | 2.13 (244) | 0.54 (15.0) |
| ota | 5.3 | 4096 | 2.04 (244) | 0.56 (15.3) |
| sys | 1.0 | 256 (quant-limited) | 1.96 (244) | 2.22 (15.0) |
| sys | 1.0 | 1024 | 2.58 (244) | 0.82 (15.0) |
| sys | 1.0 | 4096 | 4.73 (244) | 1.10 (15.3) |
| sys | 5.3 | 256 (quant-limited) | 25.99 (244) | 6.29 (15.0) |
| sys | 5.3 | 1024 | 9.82 (244) | 2.76 (15.0) |
| sys | 5.3 | 4096 | 25.64 (244) | 5.58 (15.3) |
| ota+sys | 1.0 | 256 (quant-limited) | 24.48 (244) | 5.35 (15.0) |
| ota+sys | 1.0 | 1024 | 2.14 (244) | 0.57 (15.0) |
| ota+sys | 1.0 | 4096 | 1.72 (244) | 0.48 (15.3) |
| ota+sys | 5.3 | 256 (quant-limited) | 27.48 (244) | 6.06 (15.0) |
| ota+sys | 5.3 | 1024 | 1.94 (244) | 0.56 (15.0) |
| ota+sys | 5.3 | 4096 | 1.75 (244) | 0.46 (15.3) |

## Reading the results
- Order 2 (the v1 mode): sys and ota+sys ACCEPT (worst 0.7-0.8 uV, inside the measurement resolution, at Vos = 9 mV, lf 1 and 5.3, N = 256..4096). none and ota REJECT as expected: none leaves lf*(Vos+vres) (9.0 mV at lf 1); ota leaves lf*Vos/(N-1)+lf*vres = 7.2 uV (N=4096) to 38 uV (N=256) at lf 1, 38-214 uV at lf 5.3. OTA chop alone does NOT remove offset in incremental mode, as feared in SPEC 3.6.
- Model vs theory (ota only, order 2): 54 of 54 points agree, worst deviation 9.6 % where |theory| >= 10 uV (N=256 points, within their 1-2 uV sem). The 1/(N-1) CoI-weight law is confirmed.
- Order 1: the differential offset estimate is quantisation-limited (sem 0.3 to 83 uV, N=256 worst), so the order-1 sys and ota+sys REJECT rows are a measurement-resolution failure, not evidence of a residual: every sys-mode order-1 value is within about 2 sem of 0. Order-1 ota values sit about Vos/N above the equal-weight theory (7.8 vs 5.0 uV at N=4096, 4 sem); unresolved, probably a last-sample term of the final integrator state. Order 1 is a secondary mode; not pursued within this WO.
- Noise (order 2, N >= 1024, lf 1): none 12-13 uV; sys 2.6/0.8 uV (N=1024, 240/15 SPS), 4.7/1.1 uV (N=4096); ota 2.1/0.4-0.6; ota+sys 2.1/0.6 (N=1024), 1.7/0.5 (N=4096). With the pessimistic lf = 5.3: none 65-70 uV, sys 9.8-25.6 uV at 240 SPS, ota+sys 1.8-1.9 uV. So OTA chop adds a 1.2x (lf 1, N=1024) to 14x (lf 5.3, N=4096) noise gain over sys-only at 240 SPS; sys-only has too few sub-conversions at 240 SPS to average 1/f. Rms values carry about 12 % statistical error (m_out = 32) and N = 256 rows are quantisation-limited.
- Not modelled: the real chopper residual (charge-injection spikes, fs-dependent vres) beyond a constant vres, the SC sampling of OTA noise by the chop phase, and OTA-chop settling cost. The model puts the chopped noise straight at the input with perfect sign inversion; fs/2 = 1 MHz is only 1.6x the 631 kHz 1/f corner.

## Sequencing rules for the digital sequencer (C9), reasoned not modelled
1. System-chop swaps only at conversion boundaries, never mid-conversion. The CoI weights are (N-1-n); changing the input polarity mid-run makes u_hat = sum w_n s_n u / sum w_n, a wrong-gain, input-dependent result. One sub-conversion has one polarity for all N cycles.
2. Integrator reset (both caps, plus input/ref sampling-cap precharge) between swapped sub-conversions. Incremental decoding assumes x1 = x2 = 0 at n = 0; any leftover state adds a term x2[0]-dependent error of the order of the leftover over N(N-1)/2. Reset also removes memory of the other polarity (a swap with no reset puts +-2u of step on the integrators).
3. Input polarity swap and the reset share a settle slot: swap while the integrators are in reset and let the input cap settle before cycle 0 (swap-induced charge goes to the reset, not to the first sample). Mux switches in the first phase only.
4. OTA-chop phase restarts at the same value at cycle 0 of every sub-conversion, and N is even. With N even and the same starting phase the residual lf*Vos/(N-1) is identical in both sub-conversions and sys averaging cancels it. If N is odd or the phase is continued across the reset, the residual flips sign between sub-conversions and sys averaging doubles it (2*lf*Vos/(N-1)): it adds instead of cancelling.
5. Sub-conversions are averaged in pairs: always an even count, strictly alternating polarity, same N, same fs. An odd count leaves a net offset of one sub-conversion; the sequencer must refuse or round up (iadc.measure_noise rounds up).
6. Chop clock (fs/2) is derived from the same divider as the modulator clock and is phase-locked to the non-overlapping phases; changing the chop phase relative to the sampling phase mid-conversion injects a charge step.

## Recommendation (D4: the user and the reviewer decide)
Keep OTA chop in v1 as a config bit, always paired with system chop (even N, chop phase restarted at each reset), with sys-only as the fallback mode. Numbers: the pair costs nothing in offset (0.8 uV worst vs 0.7 uV for sys) and lowers 240 SPS noise from 4.7 to 1.7 uV (lf 1, N=4096) and from 9.8-25.6 to 1.8-1.9 uV (lf 5.3). OTA chop alone is not a way to remove offset: it leaves Vos/(N-1) (7.2 to 38 uV at Vos 9 mV, lf 1-5.3, N=4096), so it must never be the only offset canceller. Drop it if the OTA-chop switches or their charge injection cost more area or residual than the 1/f benefit warrants once the OTA noise is characterised (unchopped OTA noise at lf 1 is already about 12 uV, inside the 50 uV v1 target).
