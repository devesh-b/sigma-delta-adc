# C1 macro and model scans (WO-22)

Frozen copy `/home/mempool/regr/tt/WO-22-b4fb3d2/` (tree at commit b4fb3d2; runner `run.sh`, jobs `jobs.txt`, `jobs2.txt`; json in `out/<name>/point.json`). Each deck: `tier1_tb.py --point '<k=v,...>' --n 1024 --m 21 --opt O1|O2 --deck-timeout 7000`, fs 4 MHz, bst1 = bst2 = 1. INL = endpoint-fit ppm. pt.csv deleted after each json. Full pytest on the sandbox: 153 passed.

## (a) Single-pole GBW sweep (A' hot point)
Point: GBW2 22.5 MHz, SR1 25, SR2 27 V/us, fp2_mult2 = 3, N 1024, m 21. INL ppm vs OTA1 GBW.

| GBW1 MHz | mult 10, O1 | mult 30, O1 |
|---|---|---|
| 20 | 18.91 | 26.17 |
| 22 | 11.03 | 15.21 |
| 24 | 6.56 | 9.21 |
| 26 | 4.02 (O2 4.09) | 5.66 |
| 28 | 2.58 (O2 2.63) | 3.60 (O2 3.64) |
| 30 | 1.76 | 2.39 (O2 2.41) |

Crossing of 3.33 ppm (5/1.5), log-linear interpolation between the O2 points: **GBW_needed = 26.9 MHz at mult 10, 28.4 MHz at mult 30** (O1 gives 27.0 / 28.5). O2 differs from O1 by 0.2 to 1.8 %. The 5 ppm line (O1) is at about 25.4 / 27 MHz. Interpolated, not simulated at the crossing; a 1 MHz margin (28 / 30 MHz) is covered by the table.

## (b) Pole after tanh (OTA1 only, D39 point GBW 20 / 22.5 MHz, SR 25 / 20.25, mult2 = 3), O1

| mult1 | pole after tanh | S5h pole before |
|---|---|---|
| 2 | 9.50 | 10.88 |
| 2.5 | 1.20 | not run |
| 3 | 3.58 | 3.29 |
| 3.5 | 6.74 | not run |
| 4 | 9.38 | 8.06 |
| 10 | 22.01 | 20.99 |

- **Transfer verdict: the low-mult optimum transfers.** The curve is a narrow well around mult 2.5 to 3 in both pole orders; at 2, 3, 4 and 10 the two orders agree within 10 to 16 %. Pole-before has no 2.5 point, so the depth of its minimum is unknown; pole-after reaches 1.20 at 2.5.
- Optimum at about **mult 2.5 (between 2.2 and 3.0)**. Window with INL <= 3.33 ppm (log-log interpolation between grid points, rough): **about 2.2 to 3.0, i.e. a factor 1.3 in fp2 (+/- 15 %)**. The real OTA at mult 10 to 12 is 6x worse (22 vs 3.6 ppm at mult 3).
- The sharpness (2 -> 2.5 -> 3 goes 9.5 -> 1.2 -> 3.6) is a cancellation of the signed settling error against the pole, so the window is narrow in fp2; the design target is fp2 about 2.5 to 3x GBW with a tolerance of +/- 15 % over PVT, which is tight. This is a model reading on a behavioural macro, not an OTA result.

## (c) Tier-0 A0 scan (reference only; CL-1b/D53 gate on the measured table)
`model/studies/c1_a0_scan.py` (run on the sandbox). Table anchored at A0: A0, A0-5, A0-10, A0-20 dB at |Vout| 0 / 1.4 / 2.0 / 3.1 V (S4 worst-corner shape; both OTAs); flat A0 and flat A0-5 for comparison.

| A0 dB | N1024 S4 shape | N1024 flat A0 | N1024 flat A0-5 | N4096 S4 shape | N4096 flat A0 | N4096 flat A0-5 |
|---|---|---|---|---|---|---|
| 60 | 53.69 | 1.47 | 2.65 | 52.49 | 0.41 | 0.82 |
| 64 | 33.90 | 0.87 | 1.70 | 33.11 | 0.25 | 0.49 |
| 68 | 21.36 | 0.60 | 1.04 | 20.89 | 0.15 | 0.28 |
| 72 | 13.49 | 0.38 | 0.64 | 13.17 | 0.09 | 0.16 |
| 76 | 8.51 | 0.22 | 0.42 | 8.31 | 0.06 | 0.10 |
| 80 | 5.37 | 0.14 | 0.25 | 5.25 | 0.04 | 0.06 |
| 84 | 3.39 | 0.09 | 0.16 | 3.31 | 0.02 | 0.04 |
| 88 | 2.13 | 0.06 | 0.10 | 2.09 | 0.01 | 0.03 |
| 92 | 1.35 | 0.04 | 0.06 | 1.32 | 0.01 | 0.02 |

- Cross-check: N 4096, 80 dB, S4 shape = 5.245 ppm (expected about 5.2).
- With the S4 shape, N 1024 needs **A0 about 84.1 dB** for 3.33 ppm; flat shapes pass at 60 dB. The droop shape, not A0, sets INL, and N 1024 vs N 4096 are nearly equal (INL does not scale with N/A here). A fixed A_floor is therefore not meaningful, consistent with CL-1b / D53.
