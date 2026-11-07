# S1: VREF / integrator-swing study

Command: `python3 -m model.studies.s1_vref --out /home/mempool/regr/tt/WO-02 --vlin 2`

Setup: fs 2 MHz, N 1024, Cs 1 pF, OTA+system chop, vos 3 mV, vres 5 uV, A0 75 dB, a0_drop 0.9, linear range `vlin_diff` in volts (differential). White noise: OTA part of ktc_excess scaled by noise_gain/5.3 (identical to legacy at c1=0.25; B: noise gain 9.3, excess 1.88 vs 1.5).

## Verdicts

```
ACCEPT option A: noise ok (0.52 uV <= 50 @15 SPS lf 5.3); inl ok (22.4 ppm <= 100 @ vlin 2 V); swing ok (0.711 V/side <= 0.9)
ACCEPT option A2: noise ok (0.51 uV <= 50 @15 SPS lf 5.3); inl ok (21.1 ppm <= 100 @ vlin 2 V); swing ok (0.705 V/side <= 0.9)
ACCEPT option B: noise ok (0.54 uV <= 50 @15 SPS lf 5.3); inl ok (12.4 ppm <= 100 @ vlin 2 V); swing ok (0.607 V/side <= 0.9)
REJECT option C: noise ok (0.48 uV <= 50 @15 SPS lf 5.3); inl FAIL (942.3 ppm <= 100 @ vlin 2 V); swing FAIL (1.213 V/side <= 0.9)
PASS theory-check bitstream B(c1 .125,k .5) == A: max|du_hat| 0.00e+00
PASS theory-check bitstream A2(c2 .25) == A: max|du_hat| 0.00e+00
PASS theory-check bitstream wrong-B(c1 .125,k 1) != A: max|du_hat| 2.29e-05
PASS theory-check B swing = A swing x (2.048/1.2) x 0.5 (algebra): B x1 0.602 x2 0.607; A x1 0.705 x2 0.711
PASS theory-check A2 x2 swing = A x2 / 2, x1 unchanged: A2 x1 0.705 x2 0.356
PASS theory-check eff-bit difference C-A: A-C = -0.797 b, theory -0.771 +-0.05
PASS theory-check C peak swing/side ~ 1.23 V (SPEC 2.1): measured 1.213 V (x1 1.203, x2 1.213), expected 1.23 +-15 %
PASS theory-check non-vacuity: A INL at vlin 0.5 V rejects: INL 2246 ppm > 100
PASS theory-check C at legacy xswing-equivalent vlin 2.46 V ~ 71 ppm (report_design.md): 71.3 ppm
PASS theory-check non-vacuity: noise criterion rejects 60 uV: 60.00 uV <= 50 @15 SPS lf 5.3
PASS theory-check non-vacuity: swing criterion rejects 1.0 V/side: 1.000 V/side <= 0.9
```

## Option B definition

B = c1 0.125, c2 0.5, k 0.5 (coordinator amendment F1: x1, x2 halve, bitstream identical to A, k/c1 = 4). A2 = A with c2 0.25 (x2 halved, same bitstream; sizes OTA2).

## Per option

| opt | VREF | c1 | c2 | k | peak x1 / x2 (V/side) | bits N=1024 / 4096 | Cint1 pF/side | Cint1 um2 (side / both) |
|---|---|---|---|---|---|---|---|---|
| A | 1.2 | 0.25 | 0.5 | 1.0 | 0.705 / 0.711 | 16.0 / 19.9 | 4.0 | 2000 / 4000 |
| A2 | 1.2 | 0.25 | 0.25 | 1.0 | 0.705 / 0.356 | 16.0 / 19.9 | 4.0 | 2000 / 4000 |
| B | 2.048 | 0.125 | 0.5 | 0.5 | 0.602 / 0.607 | 16.0 / 19.9 | 8.0 | 4000 / 8000 |
| C | 2.048 | 0.25 | 0.5 | 1.0 | 1.203 / 1.213 | 16.0 / 19.9 | 4.0 | 2000 / 4000 |

## Noise (uV rms) and effective bits over FSR = 2 VREF

| opt | lf_gain | 240 SPS uV (bits) | 60 SPS uV (bits) | 15 SPS uV (bits) | 3.75 SPS uV (bits) |
|---|---|---|---|---|---|
| A | 1 | 2.38 (19.9) | 1.16 (21.0) | 0.52 (22.1) | 0.24 (23.2) |
| A | 5.3 | 2.42 (19.9) | 1.12 (21.0) | 0.52 (22.1) | 0.24 (23.3) |
| A2 | 1 | 2.38 (19.9) | 1.17 (21.0) | 0.51 (22.2) | 0.24 (23.2) |
| A2 | 5.3 | 2.42 (19.9) | 1.13 (21.0) | 0.51 (22.2) | 0.24 (23.3) |
| B | 1 | 2.53 (20.6) | 1.26 (21.6) | 0.59 (22.7) | 0.27 (23.9) |
| B | 5.3 | 2.79 (20.5) | 1.30 (21.6) | 0.54 (22.8) | 0.28 (23.8) |
| C | 1 | 2.51 (20.6) | 1.31 (21.6) | 0.51 (22.9) | 0.26 (23.9) |
| C | 5.3 | 2.29 (20.8) | 1.14 (21.8) | 0.48 (23.0) | 0.25 (24.0) |

## INL (ppm FSR) vs OTA linear range vlin_diff (V differential)

| opt | 1.5 V | 2 V | 2.5 V | 3 V |
|---|---|---|---|---|
| A | 56.0 | 22.4 | 14.2 | 11.2 |
| A2 | 56.3 | 21.1 | 14.3 | 11.2 |
| B | 19.1 | 12.4 | 10.1 | 9.4 |
| C | 1662.0 | 942.3 | 63.5 | 30.5 |

## Recommendation

Options passing the criteria: A, A2, B. A has the smallest Cint1 (4 pF/side) and the lowest white noise gain (5.3) but gives up 0.77 b of effective bits vs 2.048 V (same uV noise). B keeps the 2.048 V FSR and has the least swing; it needs Cint1 = 8 pF/side (4000 um2/side) and raises white noise gain to 9.3. The study does not choose; D3 is the user's call.
