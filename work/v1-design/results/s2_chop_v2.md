# S2 v2: OTA2 offset, order-1 residue, noise at the D17 point (WO-04)

Command: `python3 model/studies/s2_chop.py --v2 --out /home/mempool/regr/tt/WO-04/s2v2 --offset-pairs 8192 --o1-pairs 65536 --m-out 32`

```
PASS e2 model-vs-theory vos2 c1 0.25 N 256: model 284.22 (sem 1.59) vs theory 282.35 uV (10 %)
PASS e2 sys-chop cancels vos2 c1 0.25 N 256: pair-averaged 0.86 uV (sem 1.11), single 284.2
PASS e2 non-vacuity (sign-flipped model rejected) vos2 c1 0.25 N 256
PASS e2 model-vs-theory x1_offset c1 0.25 N 256: model 284.22 (sem 1.59) vs theory 282.35 uV (10 %)
PASS e2 sys-chop cancels x1_offset c1 0.25 N 256: pair-averaged 0.86 uV (sem 1.11), single 284.2
PASS e2 non-vacuity (sign-flipped model rejected) x1_offset c1 0.25 N 256
PASS e2 model-vs-theory vos2 c1 0.25 N 1024: model 70.41 (sem 0.03) vs theory 70.38 uV (10 %)
PASS e2 sys-chop cancels vos2 c1 0.25 N 1024: pair-averaged -0.01 uV (sem 0.02), single 70.4
PASS e2 non-vacuity (sign-flipped model rejected) vos2 c1 0.25 N 1024
PASS e2 model-vs-theory x1_offset c1 0.25 N 1024: model 70.41 (sem 0.03) vs theory 70.38 uV (10 %)
PASS e2 sys-chop cancels x1_offset c1 0.25 N 1024: pair-averaged -0.01 uV (sem 0.02), single 70.4
PASS e2 non-vacuity (sign-flipped model rejected) x1_offset c1 0.25 N 1024
PASS e2 model-vs-theory vos2 c1 0.25 N 4096: model 17.58 (sem 0.00) vs theory 17.58 uV (10 %)
PASS e2 sys-chop cancels vos2 c1 0.25 N 4096: pair-averaged -0.00 uV (sem 0.00), single 17.6
PASS e2 non-vacuity (sign-flipped model rejected) vos2 c1 0.25 N 4096
PASS e2 model-vs-theory x1_offset c1 0.25 N 4096: model 17.58 (sem 0.00) vs theory 17.58 uV (10 %)
PASS e2 sys-chop cancels x1_offset c1 0.25 N 4096: pair-averaged -0.00 uV (sem 0.00), single 17.6
PASS e2 non-vacuity (sign-flipped model rejected) x1_offset c1 0.25 N 4096
PASS e2 model-vs-theory vos2 c1 0.125 N 256: model 564.31 (sem 1.81) vs theory 564.71 uV (10 %)
PASS e2 sys-chop cancels vos2 c1 0.125 N 256: pair-averaged -0.32 uV (sem 1.60), single 564.3
PASS e2 non-vacuity (sign-flipped model rejected) vos2 c1 0.125 N 256
PASS e2 model-vs-theory x1_offset c1 0.125 N 256: model 564.31 (sem 1.81) vs theory 564.71 uV (10 %)
PASS e2 sys-chop cancels x1_offset c1 0.125 N 256: pair-averaged -0.32 uV (sem 1.60), single 564.3
PASS e2 non-vacuity (sign-flipped model rejected) x1_offset c1 0.125 N 256
PASS e2 model-vs-theory vos2 c1 0.125 N 1024: model 140.74 (sem 0.05) vs theory 140.76 uV (10 %)
PASS e2 sys-chop cancels vos2 c1 0.125 N 1024: pair-averaged -0.04 uV (sem 0.03), single 140.7
PASS e2 non-vacuity (sign-flipped model rejected) vos2 c1 0.125 N 1024
PASS e2 model-vs-theory x1_offset c1 0.125 N 1024: model 140.74 (sem 0.05) vs theory 140.76 uV (10 %)
PASS e2 sys-chop cancels x1_offset c1 0.125 N 1024: pair-averaged -0.04 uV (sem 0.03), single 140.7
PASS e2 non-vacuity (sign-flipped model rejected) x1_offset c1 0.125 N 1024
PASS e2 model-vs-theory vos2 c1 0.125 N 4096: model 35.16 (sem 0.00) vs theory 35.16 uV (10 %)
PASS e2 sys-chop cancels vos2 c1 0.125 N 4096: pair-averaged -0.00 uV (sem 0.00), single 35.2
PASS e2 non-vacuity (sign-flipped model rejected) vos2 c1 0.125 N 4096
PASS e2 model-vs-theory x1_offset c1 0.125 N 4096: model 35.16 (sem 0.00) vs theory 35.16 uV (10 %)
PASS e2 sys-chop cancels x1_offset c1 0.125 N 4096: pair-averaged -0.00 uV (sem 0.00), single 35.2
PASS e2 non-vacuity (sign-flipped model rejected) x1_offset c1 0.125 N 4096
PASS order-1 OTA-chop residue N 256: model 34.06 (sem 2.04) vs theory lf*Vos/N = 35.16 uV
PASS order-1 OTA-chop residue N 512: model 18.92 (sem 1.07) vs theory lf*Vos/N = 17.58 uV
PASS order-1 OTA-chop residue N 255: model 0.00 (sem 0.00) vs theory lf*Vos/N = 0.00 uV
PASS order-1 OTA-chop residue N 511: model 0.00 (sem 0.00) vs theory lf*Vos/N = 0.00 uV
PASS order-1 sys-chop cancels residue N 256: 0.49 uV (sem 41.44)
PASS order-1 sys-chop cancels residue N 512: -0.98 uV (sem 10.94)
PASS order-1 non-vacuity: old kernel (0) rejected at N 512 (model 18.92 vs 0.00)
PASS noise: all measurements finite
PASS noise <= 50 uV @15 SPS, lf 9.3, N 4096, ota+sys, Cs 1.0 pF: 0.50 uV
PASS noise <= 50 uV @15 SPS, lf 9.3, N 4096, ota+sys, Cs 0.5 pF: 0.71 uV
PASS noise <= 50 uV @15 SPS, lf 9.3, N 4096, sys, Cs 1.0 pF: 9.82 uV
PASS noise <= 50 uV @15 SPS, lf 9.3, N 4096, sys, Cs 0.5 pF: 9.79 uV
```

## OTA2 offset / x1 output offset, 9 mV, no sys chop [uV], model (sem) / theory 2*e2/(c1(N-1))

| c1 | injected at | N=256 | N=1024 | N=4096 |
|---|---|---|---|---|
| 0.25 | vos2 | 284.22 (1.59) / 282.35 | 70.41 (0.03) / 70.38 | 17.58 (0.00) / 17.58 |
| 0.25 | x1_offset | 284.22 (1.59) / 282.35 | 70.41 (0.03) / 70.38 | 17.58 (0.00) / 17.58 |
| 0.125 | vos2 | 564.31 (1.81) / 564.71 | 140.74 (0.05) / 140.76 | 35.16 (0.00) / 35.16 |
| 0.125 | x1_offset | 564.31 (1.81) / 564.71 | 140.74 (0.05) / 140.76 | 35.16 (0.00) / 35.16 |

## Order-1 OTA-chop-only residue, Vos 9 mV, lf 1 [uV]

| N | model (sem) | theory lf*Vos/N (even) / 0 (odd) |
|---|---|---|
| 256 | 34.06 (2.04) | 35.16 |
| 512 | 18.92 (1.07) | 17.58 |
| 255 | 0.00 (0.00) | 0.00 |
| 511 | 0.00 (0.00) | 0.00 |

## rms noise at the D17 point [uV]

B (VREF 2.048, c1 .125, c2 .5, k .5), shared Cs, A0 80 dB, a0_drop 0.9 at vlin 2.0 V, flicker + kT/C on, Vos 9 mV, vres 5 uV. m_out 32 (about 12 % statistical error). Actual rates in brackets.

| N | mode | lf | Cs pF | 240 SPS | 60 SPS | 15 SPS | 3.75 SPS |
|---|---|---|---|---|---|---|---|
| 1024 | ota+sys | 1 | 1 | 2.35 (244.1) | 1.22 (61.0) | 0.69 (15.0) | 0.29 (3.8) |
| 1024 | ota+sys | 1 | 0.5 | 3.15 (244.1) | 1.74 (61.0) | 0.91 (15.0) | 0.46 (3.8) |
| 1024 | ota+sys | 9.3 | 1 | 2.37 (244.1) | 1.26 (61.0) | 0.68 (15.0) | 0.32 (3.8) |
| 1024 | ota+sys | 9.3 | 0.5 | 3.46 (244.1) | 1.78 (61.0) | 0.93 (15.0) | 0.43 (3.8) |
| 1024 | sys | 1 | 1 | 2.66 (244.1) | 1.46 (61.0) | 0.87 (15.0) | 0.47 (3.8) |
| 1024 | sys | 1 | 0.5 | 3.62 (244.1) | 1.84 (61.0) | 0.99 (15.0) | 0.53 (3.8) |
| 1024 | sys | 9.3 | 1 | 17.34 (244.1) | 8.76 (61.0) | 4.82 (15.0) | 2.80 (3.8) |
| 1024 | sys | 9.3 | 0.5 | 17.23 (244.1) | 8.74 (61.0) | 4.84 (15.0) | 2.85 (3.8) |
| 4096 | ota+sys | 1 | 1 | 2.07 (244.1) | 1.12 (61.0) | 0.50 (15.3) | 0.30 (3.8) |
| 4096 | ota+sys | 1 | 0.5 | 2.81 (244.1) | 1.66 (61.0) | 0.72 (15.3) | 0.41 (3.8) |
| 4096 | ota+sys | 9.3 | 1 | 1.87 (244.1) | 1.25 (61.0) | 0.50 (15.3) | 0.28 (3.8) |
| 4096 | ota+sys | 9.3 | 0.5 | 2.82 (244.1) | 1.67 (61.0) | 0.71 (15.3) | 0.42 (3.8) |
| 4096 | sys | 1 | 1 | 4.71 (244.1) | 2.58 (61.0) | 1.13 (15.3) | 0.53 (3.8) |
| 4096 | sys | 1 | 0.5 | 4.97 (244.1) | 2.94 (61.0) | 1.21 (15.3) | 0.58 (3.8) |
| 4096 | sys | 9.3 | 1 | 45.25 (244.1) | 19.37 (61.0) | 9.82 (15.3) | 4.52 (3.8) |
| 4096 | sys | 9.3 | 0.5 | 45.08 (244.1) | 19.49 (61.0) | 9.79 (15.3) | 4.51 (3.8) |

