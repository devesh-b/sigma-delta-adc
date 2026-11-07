# S1 v2: INL at the D17 point (WO-04)

Command: `python3 -m model.studies.s1_vref --v2 --out /home/mempool/regr/tt/WO-04/s1v2`

Setup: fs 2 MHz, A0 80 dB (D15), a0_drop 0.9 with vlin 2.0 V, ref_mode shared (D14), tau_in 20 ns, tau_ref 10 ns / cd_ref 20 pF (items 3, 5), no noise/offset in the INL sweep, 401 points in +-0.9. INL is the endpoint-fit INL in ppm of FSR (2 normalised). Residue column: u = (sum S + (k/c1) S + x2[N]/(c1 c2)) / (N(N-1)/2) from the final x2 state. Floor: the same sweep with an ideal OTA, ideal references.

```
PASS INL N 4096 A0 80 shared A: 9.29 ppm vs expected 9.3 (+-20 %)
PASS INL N 4096 A0 80 shared A_half: 1.38 ppm vs expected 1.4 (+-20 %)
PASS INL N 4096 A0 80 shared B: 3.63 ppm vs expected 3.7 (+-20 %)
PASS INL N 4096 A0 80 shared C: 541.32 ppm vs expected 541.0 (+-20 %)
PASS ideal-OTA quantization floor N 4096 A: 0.42 ppm vs expected 0.5 (+-20 %)
PASS ideal-OTA quantization floor N 4096 A_half: 0.42 ppm vs expected 0.5 (+-20 %)
PASS ideal-OTA quantization floor N 4096 B: 0.42 ppm vs expected 0.5 (+-20 %)
PASS ideal-OTA quantization floor N 4096 B_half-Cs: 0.42 ppm vs expected 0.5 (+-20 %)
PASS ideal-OTA quantization floor N 4096 C: 0.42 ppm vs expected 0.5 (+-20 %)
PASS B_half-Cs INL (3.63) ~ unchanged vs B (3.63) (review E1)
PASS residue reconstruction lowers N 1024 INL (except C where OTA nonlinearity dominates)
PASS non-vacuity: comparator rejects expected values doctored by x1.5 / x0.5
PASS non-vacuity: A at A0 40 dB rejects (869 ppm)
PASS ref recovery: all measurements finite
PASS ref recovery: some decap in the grid keeps INL <= 100/3 ppm (smallest 0 pF = 0 um2)
PASS non-vacuity: ref-recovery sweep reacts to a slow reference (tau 100 ns / 2 pF: gain err -82 vs settled -63 ppm)
PASS quant floor N 1024: finite (noise-free max|err| 33.3 uV)
PASS quant floor N 4096: finite (noise-free max|err| 2.1 uV)
PASS quant floor scales down with N: 33.3 uV (1024) vs 2.1 (4096)
```

## INL (ppm FSR) and quantization floor

| option | VREF | c1 | k | Cs pF | Cint1 pF | INL N4096 | floor N4096 | INL N1024 residue | INL N1024 plain | floor N1024 | gain err N4096 ppm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 1.2 | 0.25 | 1.0 | 1 | 4.0 | 9.29 | 0.42 | 9.06 | 15.26 | 7.18 | -140 |
| A_half | 1.2 | 0.125 | 0.5 | 1 | 8.0 | 1.38 | 0.42 | 1.03 | 6.76 | 7.18 | -55 |
| B | 2.048 | 0.125 | 0.5 | 1 | 8.0 | 3.63 | 0.42 | 3.34 | 9.35 | 7.18 | -63 |
| B_half-Cs | 2.048 | 0.125 | 0.5 | 0.5 | 4.0 | 3.63 | 0.42 | 3.34 | 9.35 | 7.18 | -63 |
| C | 2.048 | 0.25 | 1.0 | 1 | 4.0 | 541.32 | 0.42 | 539.79 | 543.13 | 7.18 | -1735 |

Expected (review probes, N 4096, A0 80): A 9.3, A_half 1.4, B 3.7, C 541.0, floor 0.5 ppm.

## Reference recovery at the B point (shared Cs, N 4096)

R = 500 ohm, node C = 5 pF pad + on-chip decap; tau_ref = R C. Model: cd_ref = C, share = Cs/(Cs+C).

| decap pF | tau_ref ns | INL ppm | gain err ppm | decap MIM um2 (2 fF/um2) |
|---|---|---|---|---|
| 0 | 2.5 | 3.63 | -63 | 0 |
| 2 | 3.5 | 3.63 | -63 | 1000 |
| 5 | 5.0 | 3.63 | -63 | 2500 |
| 10 | 7.5 | 3.63 | -63 | 5000 |
| 20 | 12.5 | 3.63 | -63 | 10000 |

smallest decap with INL <= 33.3 ppm: 0 pF (tau_ref 2.5 ns, 0 um2 MIM at 2 fF/um2).

At R = 500 ohm the reference node settles to e^-18 within a half period (t_half 225 ns), so INL and gain error do not depend on the decap in this model; decap sizing is then set by other effects (pad/bond droop between cycles, noise), not modelled here. Where recovery starts to matter (B point, shared Cs, N 4096):

| tau_ref ns | cd_ref pF | INL ppm | gain err ppm |
|---|---|---|---|
| 12.5 | 2 | 3.63 | -63 |
| 12.5 | 10 | 3.63 | -63 |
| 30 | 2 | 3.67 | -64 |
| 30 | 10 | 3.69 | -63 |
| 60 | 2 | 4.23 | -78 |
| 60 | 10 | 3.90 | -67 |
| 100 | 2 | 58.41 | -82 |
| 100 | 10 | 23.42 | -63 |
| 200 | 2 | 1857.20 | 1521 |
| 200 | 10 | 652.14 | 521 |

## Quantization floor of averaged modes (B point, ideal OTA, sys-chop pairs)

Noise-free max|error| over 4001 DC values in +-0.9 is identical for every K (averaging identical conversions removes nothing). With kT/C dither (white, Cs 1 pF; flicker not included, which is conservative) the per-DC bias is estimated from 8 repeats at 65 DC values; its resolution is std/sqrt(8), shown as 'res'. Rates are fs/(N K).

N = 1024: noise-free max|err| = 33.26 uV

| K pairs | rate SPS | max abs bias uV | res uV | rms scatter uV |
|---|---|---|---|---|
| 2 | 976.56 | 34.52 | 1.99 | 5.64 |
| 4 | 488.28 | 31.34 | 1.36 | 3.84 |
| 8 | 244.14 | 32.56 | 0.97 | 2.74 |
| 16 | 122.07 | 33.11 | 0.69 | 1.95 |
| 32 | 61.04 | 31.98 | 0.48 | 1.35 |
| 64 | 30.52 | 32.26 | 0.33 | 0.95 |

N = 4096: noise-free max|err| = 2.08 uV

| K pairs | rate SPS | max abs bias uV | res uV | rms scatter uV |
|---|---|---|---|---|
| 2 | 244.14 | 3.15 | 0.79 | 2.23 |
| 4 | 122.07 | 2.16 | 0.55 | 1.57 |
| 8 | 61.04 | 1.81 | 0.43 | 1.21 |
| 16 | 30.52 | 1.53 | 0.28 | 0.81 |
| 32 | 15.26 | 1.72 | 0.19 | 0.54 |
| 64 | 7.63 | 1.87 | 0.14 | 0.39 |

