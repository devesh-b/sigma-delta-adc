# S3: error budget and per-block specs at the decided design point (WO-05)

Command: `python3 -m model.studies.s3_budget --out /home/mempool/regr/tt/WO-05/run4`

## Design point

Order 2 CIFB, c1 0.125, c2 0.5, k 0.5; VREF 2.048 V (REF+ ua2, REF- ua3, 500 ohm + 5 pF pads); Cs1 0.5 pF, Cint1 4 pF, shared Cs; fs 2 MHz (0.25-2 precision, 4 MHz fast); precision N 4096 with K sys-chop pairs, ota+sys chop; fast N 64/256/1024; A0 >= 80 dB, vlin in volts; Vos1 = Vos2 = 9 mV (3 sigma); overload 1.0-1.1 VREF. Sweeps: one parameter at a time on an otherwise ideal loop (switch kT/C only, shared Cs, chop+sys on). Noise: rms of 64 outputs at 15 SPS (statistical error ~9 %) (N 4096, K 34) and 240 SPS (N 1024, K 8). INL: endpoint, +-0.9 FS, N 4096, residue-corrected, ppm of FSR. Offset: paired difference (offset sources on minus zeroed), noise-free, mean over 512 DC points; `sys` = pair of opposite input polarities. lf = 9.3 is the pessimistic input-referral bound (SPEC 2.2 nominal ~1).

## Theory checks

```
PASS lf*Vos1/(N-1), ota chop, sys off, lf 9.3, N 4096: model 20.49 vs theory 20.44 uV
PASS lf*Vos1, no chop, sys off: model 83699.9 vs theory 83700.0 uV
PASS 2*Vos2/(c1(N-1)), sys off: model 35.17 vs theory 35.16 uV
PASS sys pair cancels vos1: residual 0.000 uV (theory 0, tol 0.5)
PASS sys pair cancels vos2: residual 0.000 uV (theory 0, tol 0.5)
PASS sys pair cancels vres: residual 0.000 uV (theory 0, tol 0.5)
PASS kT/C noise ratio Cs 0.0625/0.25 pF = 1.988 vs sqrt(4) = 2 (10 %)
PASS kT/C per-conversion rms Cs 0.0625 pF: model 9.19 vs 2kT/C-weighted theory 9.29 uV (15 %)
PASS kT/C per-conversion rms Cs 0.125 pF: model 6.49 vs 2kT/C-weighted theory 6.57 uV (15 %)
PASS kT/C per-conversion rms Cs 0.25 pF: model 4.62 vs 2kT/C-weighted theory 4.64 uV (15 %)
PASS reset residue r 0.01, N 4096: x1-init sim 47.65, model x1_offset 47.65 vs 2*r*x1max/(c1(N-1)) = 47.67 uV
PASS reset residue r 0.003, N 4096: x1-init sim 14.18, model x1_offset 14.18 vs 2*r*x1max/(c1(N-1)) = 14.30 uV
PASS leakage 100 pA, fs 0.25 MHz: model 799.9 vs I/(fs*Cs) = 800.0 uV; sys-pair residual 0.000 uV (ASSUMES signal-independent)
PASS leakage 100 pA, fs 2 MHz: model 100.2 vs I/(fs*Cs) = 100.0 uV; sys-pair residual 0.000 uV (ASSUMES signal-independent)
PASS comparison rejects theory x1.5, x0.5 and NaN
```

## Sensitivity sweeps

Base (ideal OTA, switch kT/C only): noise 0.556 uV @15, 2.35 uV @240, INL 1.11e-10 ppm, gain 0 ppm.

| sweep | value | noise@15 uV | noise@240 uV | INL ppm | gain err ppm | offset sys-off uV | offset sys-pair uV |
|---|---|---|---|---|---|---|---|
| A0 x a0_drop (vlin 2 V) | 70, 0.5 | 0.588 | 2.4 | 5.09 | -177 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 75, 0.5 | 0.546 | 2.58 | 2.86 | -99.7 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 80, 0.5 | 0.555 | 2.49 | 1.61 | -56.1 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 85, 0.5 | 0.555 | 2.21 | 0.905 | -31.5 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 90, 0.5 | 0.542 | 2.47 | 0.509 | -17.7 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 70, 0.9 | 0.573 | 2.25 | 10.3 | -196 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 75, 0.9 | 0.563 | 2.41 | 5.78 | -110 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 80, 0.9 | 0.539 | 2.55 | 3.25 | -62 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 85, 0.9 | 0.571 | 2.24 | 1.83 | -34.9 | 0 | 0 |
| A0 x a0_drop (vlin 2 V) | 90, 0.9 | 0.543 | 2.46 | 1.03 | -19.6 | 0 | 0 |
| vlin_diff (A0 80, drop 0.9) | 0.8 | 0.566 | 2.46 | 459 | -1.52e+03 | 0 | 0 |
| vlin_diff (A0 80, drop 0.9) | 1 | 0.578 | 2.23 | 253 | -793 | 0 | 0 |
| vlin_diff (A0 80, drop 0.9) | 1.5 | 0.563 | 2.4 | 7.6 | -77.3 | 0 | 0 |
| vlin_diff (A0 80, drop 0.9) | 2 | 0.539 | 2.55 | 3.25 | -62 | 0 | 0 |
| OTA thermal en | 5 | 0.661 | 2.76 | 1.11e-10 | 0 | 0 | 0 |
| OTA thermal en | 7 | 0.776 | 3.2 | 1.11e-10 | 0 | 0 | 0 |
| OTA thermal en | 10 | 0.927 | 3.9 | 1.11e-10 | 0 | 0 | 0 |
| OTA thermal en | 14 | 1.16 | 4.77 | 1.11e-10 | 0 | 0 | 0 |
| OTA thermal en | 20 | 1.59 | 6.48 | 1.11e-10 | 0 | 0 | 0 |
| OTA 1/f corner (lf 9.3) | 1e+05 | 0.574 | 2.44 | 1.11e-10 | 0 | 0 | 0 |
| OTA 1/f corner (lf 9.3) | 6.31e+05 | 0.599 | 2.64 | 1.11e-10 | 0 | 0 | 0 |
| OTA 1/f corner (lf 9.3) | 2e+06 | 0.635 | 2.9 | 1.11e-10 | 0 | 0 | 0 |
| lf (flicker 631k, Vos1 9 mV, vres 5 uV) | 1 | 0.59 | 2.44 | 1.11e-10 | 0 | 7.31 | 0 |
| lf (flicker 631k, Vos1 9 mV, vres 5 uV) | 9.3 | 0.593 | 2.59 | 1.11e-10 | 0 | 66.9 | 0 |
| vres (lf 9.3) | 0 | 0.556 | 2.35 | 1.11e-10 | 0 | 0 | 0 |
| vres (lf 9.3) | 5e-06 | 0.545 | 2.42 | 1.11e-10 | 0 | 46.4 | 0 |
| vres (lf 9.3) | 2e-05 | 0.549 | 2.33 | 1.11e-10 | 0 | 186 | 0 |
| Vos2 | 0.001 | 0.554 | 2.35 | 1.67e-10 | -1.11e-10 | 3.91 | 0 |
| Vos2 | 0.009 | 0.554 | 2.38 | 1.67e-10 | -1.11e-10 | 35.2 | 0 |
| Vos2 | 0.02 | 0.549 | 2.41 | 2.22e-10 | 2.22e-10 | 78.2 | 0 |
| comp_offset (c2 0.5) | 0.005 | 0.564 | 2.37 | 1.11e-10 | 0 | 0.000954 | 0 |
| comp_offset (c2 0.5) | 0.02 | 0.563 | 2.43 | 2.78e-10 | 2.22e-10 | 0.00668 | 0 |
| comp_offset (c2 0.5) | 0.05 | 0.533 | 2.46 | 2.22e-10 | 2.22e-10 | 0.02 | 0 |
| comp_offset (c2 0.25) | 0.005 | 0.567 | 2.35 | 1.11e-10 | 0 | 0.00382 | 0 |
| comp_offset (c2 0.25) | 0.02 | 0.547 | 2.48 | 2.22e-10 | 2.22e-10 | 0.021 | 0 |
| comp_offset (c2 0.25) | 0.05 | 0.562 | 2.31 | 2.22e-10 | 2.22e-10 | 0.2 | 0 |
| comp_noise rms | 0.0001 | 0.582 | 2.67 | 1.11e-10 | 0 | 0 | 0 |
| comp_noise rms | 0.001 | 0.587 | 2.67 | 1.11e-10 | 0 | 0 | 0 |
| comp_noise rms | 0.005 | 0.592 | 2.72 | 1.11e-10 | 0 | 0 | 0 |
| tau_in | 1e-09 | 0.556 | 2.35 | 1.11e-10 | 0 | 0 | 0 |
| tau_in | 1e-08 | 0.556 | 2.35 | 2.22e-10 | -4.13e-07 | 0 | 0 |
| tau_in | 4.5e-08 | 0.548 | 2.27 | 0.00176 | -16.6 | 0 | 0 |
| tau_ref (cd_ref 5 pF pad) | 2.5e-09 | 0.556 | 2.35 | 1.11e-10 | 0 | 0 | 0 |
| tau_ref (cd_ref 5 pF pad) | 1e-08 | 0.556 | 2.35 | 1.67e-10 | -3e-08 | 0 | 0 |
| tau_ref (cd_ref 5 pF pad) | 4.5e-08 | 0.551 | 2.41 | 0.00517 | -1.19 | 0 | 0 |
| reset residue r on x1 | 0.01 | 0.549 | 2.24 | 2.78e-10 | 2.22e-10 | 47.6 | 0 |
| reset residue r on x1 | 0.001 | 0.565 | 2.32 | 1.11e-10 | 0 | 4.86 | 0 |
| reset residue r on x1 | 0.0001 | 0.553 | 2.39 | 2.78e-10 | 2.22e-10 | 0.485 | 0 |
| leakage at fs 0.25 MHz | 1e-11 | 1.92 | 5.15 | 1.11e-10 | 0 | 80.1 | 0 |
| leakage at fs 0.25 MHz | 1e-10 | 1.82 | 4.81 | 1.11e-10 | 0 | 800 | 0 |
| leakage at fs 0.25 MHz | 1e-09 | 1.9 | 5.23 | 1.11e-10 | 0 | 8e+03 | 0 |
| leakage at fs 2 MHz | 1e-11 | 0.56 | 2.38 | 1.11e-10 | 0 | 10 | 0 |
| leakage at fs 2 MHz | 1e-10 | 0.568 | 2.36 | 1.11e-10 | 0 | 100 | 0 |
| leakage at fs 2 MHz | 1e-09 | 0.55 | 2.15 | 1.11e-10 | 0 | 1e+03 | 0 |

Notes: OTA thermal mapping `ktc_excess = 1 + 0.5 (en/6.9)^2` (calibration comment in iadc.py: 0.5 = OTA at 6.9 nV/rtHz, scaled by noise gain 9.3/5.3). Leakage rows inject the offset I/(fs Cs) as a constant input-referred offset; they cancel in the sys pair only if the leakage is signal-independent (ASSUMPTION; bottom-plate virtual ground sits at a fixed voltage, but junction leakage varies with temperature drift between sub-conversions). Reset-residue rows inject x1[0] = r x1max, equivalent to a constant stage-2 offset (verified against a local x1-init simulation); x1max = 1.22 V differential (S1). Reset residue tracks the previous conversion's final x1, so it is not guaranteed to cancel in a sys pair and is budgeted as non-cancelling.

## Allocation table

Noise: RSS of values and of shares. INL, offset, gain: linear sums. Margin = share / value (>= 1 required).

| block | metric | share | per-block spec | measured/hand value | margin | kind |
|---|---|---|---|---|---|---|
| sampling switches kT/C (Cs 0.5 pF) | noise_uv | 1.2 | Cs 0.5 pF, 2 events | 0.556 | 2.16 | model |
| OTA1 thermal | noise_uv | 1.2 | en <= 10 nV/rtHz | 0.742 | 1.62 | model |
| OTA1 1/f + chopper residue | noise_uv | 1 | fc <= 631 kHz, lf <= 9.3, vres <= 5 uV | 0.155 | 6.47 | model |
| comparator noise | noise_uv | 0.3 | <= 5 mV rms (input-ref) | 1.06e-16 | >1000 | model |
| OTA2 + stage-2 kT/C (hand) | noise_uv | 0.3 | Cs2 0.5 pF, OTA2 same excess | 0.00404 | 74.20 | hand |
| reserve: ref path, substrate, chopper spikes | noise_uv | 1 | unmodelled; measure in C10/V | 0 | inf | reserve |
| OTA1+OTA2 gain and swing linearity | inl_ppm | 8 | A >= 80 dB, <= 90 % drop at |Vout,diff| <= 2 V | 3.25 | 2.46 | model |
| input sampling settling | inl_ppm | 2 | tau_in <= 18.75 ns | 2.08e-06 | >1000 | model |
| reference path settling | inl_ppm | 2 | tau_ref <= 10 ns (500 ohm + 5 pF pad) | 1.67e-10 | >1000 | model |
| comparator offset | inl_ppm | 1 | <= 20 mV | 2.78e-10 | >1000 | model |
| quantization floor (N 4096, raw accumulators) | inl_ppm | 1 | N = 4096 | 0.419 | 2.38 | model |
| reserve: MIM VCC, charge-inj. nonlinearity, substrate | inl_ppm | 6 | unmodelled | 0 | inf | reserve |
| Vos1, Vos2, vres, comp offset (model residual in sys pair) | offset_uv | 1 | Vos 9 mV, vres 5 uV, comp 20 mV | 0 | inf | model |
| reset residue r (worst case, does NOT cancel) | offset_uv | 1 | r <= 0.0001 (window >= 15 tau) | 0.485 | 2.06 | model |
| virtual-ground leakage (hand, rho 0.1 % ASSUMED) | offset_uv | 1 | I_leak <= 100 pA at 125 C, fs 0.25 MHz | 0.8 | 1.25 | hand |
| reserve: pair drift, chopper charge injection | offset_uv | 2 | unmodelled; +--+ ordering helps | 0 | inf | reserve |
| finite A0 and swing (model) | gain_ppm | 300 | A >= 80 dB | 62 | 4.84 | model |
| input + reference settling (model) | gain_ppm | 500 | tau_in, tau_ref as above | 0.015 | >1000 | model |
| cap ratio mismatch Cs/Cint (hand) | gain_ppm | 3e+03 | 3 sigma ratio mismatch <= 0.3 %; verify by MC in C10 | 3e+03 | 1.00 | requirement |
| reserve: pad/bond droop, 5 mV kickback | gain_ppm | 1.2e+03 | calibratable | 19.1 | 62.91 | hand |

| metric | budget | sum of shares | sum of values |
|---|---|---|---|
| noise_uv | 2.5 | 2.25 | 0.94 |
| inl_ppm | 20 | 20 | 3.67 |
| offset_uv | 5 | 5 | 1.28 |
| gain_ppm | 5e+03 | 5e+03 | 3.08e+03 |

Joint run (all blocks at spec together): n15 0.935, n240 3.94, inl 3.41, gain -62, off_nosys 103, off_sys -0.021

## Findings from the sweeps

- OTA linearity: INL 3.25 ppm at 80 dB / 90 % drop / 2 V (share 8 ppm, margin 2.5). 75 dB / 0.9 gives 5.78 ppm (still inside the share), 70 dB / 0.9 gives 10.3 ppm (outside). The linear range matters more than A0: vlin 1.5 V gives 7.6 ppm, 1.0 V gives 253 ppm, 0.8 V gives 459 ppm. Spec the swing in volts (m4): the x1 peak is 1.22 V diff, so 2.0 V keeps the gain-drop region away from the signal.
- OTA thermal noise: total noise @15 SPS 0.661/0.776/0.927/1.16/1.59 uV for 5/7/10/14/20 nV/rtHz (12 % of statistical scatter). Even 20 nV/rtHz stays inside the 2.5 uV budget alone; the limit is set by current (see power table), not by noise.
- Sampling kT/C of the switches at Cs 0.5 pF is the floor (0.56 uV @15 SPS) and not reducible without a larger Cs.
- tau_in and tau_ref (shared Cs): INL stays below 0.01 ppm and gain error below 17 ppm up to 45 ns; the shared-Cs error is a gain error (review F6/m6). The binding limit on the input is the pad/source recharge (hand row), not the model's tau.
- Comparator: noise up to 5 mV rms and offset up to 50 mV produce < 0.2 uV noise and < 0.2 uV offset. The comparator is not budget-limiting; its offset only matters through x2 swing (c2 0.25 makes 50 mV 0.2 uV instead of 0.02 uV).
- The model's constant offsets (Vos1, Vos2, vres, comparator offset, reset residue, leakage) cancel exactly in a sys pair (residual 0.000 uV, numerical). The offset budget is therefore carried by the non-cancelling mechanisms: reset residue (worst case), leakage fraction (assumed) and pair drift (reserve).
- Leakage raw offsets I/(fs Cs): 100 pA gives 800 uV at 0.25 MHz and 100 uV at 2 MHz; 1 nA gives 8 mV at 0.25 MHz (1 mV at 2 MHz). Without cancellation the leakage spec would be ~1 pA.
- Raw (sys-off) offsets at the SPEC values: lf*Vos1/(N-1) 20.4 uV, 2*Vos2/(c1(N-1)) 35.2 uV, vres 5 uV x lf 9.3 = 46 uV: characterization-only modes carry these (SPEC 3.6).
- 4 MHz fast mode (hand): t_half 113 ns needs GBW 8.22-16.4 MHz and SR >= 22.8 V/us; both are met by the noise-set OTA1 design (gm/GBW/SR columns in the power table).

## Stage-2 sizing (item 3)

Stage-2 white sampling error referred to the input is u_err = sqrt(N) sigma / (c1 sum w) (unit weights, because it enters x2 per cycle), with sigma = sqrt(2 events * 2kT/Cs2). (a) kT/C of stage 2 divided by the stage-1 gain is negligible at any plausible Cs2; (b) area is the only cost of larger Cs2; (c) x2 swing and comparator: c2 0.5 gives a feedback step c2 k VREF = 0.512 V (c2 0.25: 0.256 V), see the comp_offset (c2 0.5) and (c2 0.25) sweeps.

| option | stage-2 kT/C at input [uV/conv] | MIM um2 (diff, x1.5) | x2 min step [V] |
|---|---|---|---|
| Cs2 0.25 / Cint2 0.5 pF, c2 0.5 | 0.0157 | 1.12e+03 | 0.512 |
| Cs2 0.5 / Cint2 1 pF, c2 0.5 | 0.0111 | 2.25e+03 | 0.512 |
| Cs2 1 / Cint2 2 pF, c2 0.5 | 0.00786 | 4.5e+03 | 0.512 |
| Cs2 1 / Cint2 4 pF, c2 0.25 | 0.00786 | 7.5e+03 | 0.256 |
| Cs2 0.5 / Cint2 2 pF, c2 0.25 | 0.0111 | 3.75e+03 | 0.256 |

Proposal: **Cs2 0.5 pF, Cint2 1 pF (c2 0.5)**. The kT/C term is orders of magnitude under the stage-1 floor, so the choice is set by area, by keeping Cs2 well above the OTA1 load parasitics (0.25 pF would be dominated by wiring) and by matching. c2 = 0.25 (Cs2 0.5 / Cint2 2 pF) is allowed if the comparator offset sweep for c2 0.25 stays inside its share; it costs 1 pF more MIM per side and halves the x2 swing, so it is an option for OTA2 swing only (review E3: no INL benefit).

## Area and power estimate (item 4b)

All hand estimates, no simulation.

MIM (2 fF/um2, x1.5 overhead, differential): Cs1 750 um2, Cint1 6e+03 um2, Cs2 750 um2, Cint2 1.5e+03 um2; total 9e+03 um2 = 12.0 % of the 2x2 tile (7.52e+04 um2).

| OTA1 en | gm needed [uS] | input tail [uA] | OTA1 total [uA] (fold x2, +10 %) | GBW at gm, CL1 [MHz] | SR [V/us] | chip analog total [uA] | vs 200 uA |
|---|---|---|---|---|---|---|---|
| 7 nV/rtHz | 676 | 90.2 | 198 | 85.5 | 71.6 | 230 | OVER 200 uA |
| 10 nV/rtHz | 331 | 44.2 | 97.2 | 41.9 | 35.1 | 129 | OK |
| 14 nV/rtHz | 169 | 22.5 | 49.6 | 21.4 | 17.9 | 81.1 | OK |

Assumptions: thermal en^2 = 4kT (2 gamma/gm)(1 + gm_load/gm_in), gamma 2/3, gm_load/gm_in 0.5; gm/Id 15 /V; folded cascode doubles the branch current. Other consumers: {'ota2_uA': 5.529203070318037, 'comparator_uA': 6.0, 'bias_cmfb_refs_uA': 20.0}. Noise, not GBW or slew, sets the OTA1 current: GBW needed 4.11 MHz (tau <= 0.2 t_half) to 8.22 MHz (10 tau), slew needed 11.4 V/us diff (max step 0.512 V in 0.2 t_half), beta1 = 0.86, OTA1 load 1.26 pF. The 7 nV/rtHz inherited from the continuous-time spec does not fit the 200 uA budget with this estimate; 10-14 nV/rtHz does (review E2).

## Per-block spec table (paste-ready for SPEC section 3)

All entries are limits at every corner of SPEC section 6. Margin = allocation share / value at the spec.

| block | parameter | spec | budget line |
|---|---|---|---|
| OTA1 (and OTA2 until separated) | DC gain / linearity | A >= 80 dB with <= 90 % gain drop at |Vout,diff| <= 2 V | INL share 8 ppm |
| OTA1 | input white noise | <= 10 nV/rtHz (mapping in sweeps) | noise share 1.2 uV |
| OTA1 | 1/f corner (with chop + sys) | <= 631 kHz, residual chopper offset vres <= 5 uV | noise share 1.0 uV |
| OTA1 | GBW / slew (hand) | >= 10 MHz (needs 4.11-8.22), SR >= 12 V/us diff at beta 0.86, CL 1.26 pF | hand |
| OTA1/OTA2 | input offset | <= 9 mV (3 sigma); cancels with sys chop (constant) | offset |
| Comparator | offset | <= 20 mV (3 sigma) | INL share 1 ppm |
| Comparator | input-referred noise | <= 5 mV rms (1 mV or less has no measurable effect: decisions never flip) | noise share 0.3 uV |
| Comparator | decision time | < 0.3 t_half = 68 ns at 2 MHz (34 ns at 4 MHz) | hand |
| Comparator | kickback on x2 | <= 1 % of the minimum x2 step (5.1 mV of 0.512 V); signal-dependent kickback gives 3.81 ppm gain error per mV | hand |
| Input switches | settling tau_in (Ron + 500 ohm + source) x (5 pF + Cs) | <= 18.75 ns, i.e. source <= 2089 ohm (+ the 500 ohm pad); tau <= 18.8 ns (t_half/12) is the outer limit | INL share 2 ppm |
| TG Ron (hand, ASSUMED device numbers) | ss/-40 C/3.0 V mid-range | Ron ~ 820 ohm at W/L 20/0.5 each; spec Ron <= 1.5 kohm | hand |
| Reference path | tau_ref (500 ohm, 5 pF pad) | <= 10 ns, pad path < 500 ohm and < 5 pF | INL share 2 ppm |
| Reset | residue r on x1 at conversion start | <= 0.0001; window >= 15 tau = 60 ns (1 kohm x 4 pF), residue at 15 tau 3.1e-07 | offset share 1 uV |
| Virtual ground | leakage (125 C) | <= 100 pA total at the integrator input; non-cancelling fraction <= 0.1 % (ASSUMED) | offset share 1 uV |
| Capacitors | ratio mismatch Cs/Cint | <= 0.3 % (3 sigma), gain error only; verify by MC (C10) | gain share 3000 ppm |
| Clock | t_half / non-overlap | t_half 225 ns at 2 MHz, 0.45/fs after non-overlap; jitter-immune (SC) | hand |

## Open risks (not modelled)

- Substrate coupling from the decimator and clock drivers into the integrator virtual ground.
- MIM voltage coefficient and bottom-plate parasitic (the sky130 MIM model has none): Cint VCC INL and Cp appear only in PEX/silicon.
- Chopper charge-injection spikes and OTA settling with the chopper in place, chopping and parked.
- OTA1 and OTA2 gain/linearity are applied together in the model (one `a0_db`); OTA2 cannot be relaxed on evidence until iadc.py has a separate a0_db2.
- Leakage cancellation in sys pairs assumes a signal-independent leakage (rho = 0.1 % non-cancelling is an assumption).
- Reset residue is budgeted as non-cancelling; a +--+ pair order and a >= 15 tau reset window make it negligible.
- Shared-Cs input: the source must settle a 5 pF pad plus Cs every half period; a 10 kohm source is not supported without an external buffer or decap.
- Fast modes (N 64/256/1024, 4 MHz) have their own INL/noise targets and were not swept here.

## Hand calculations (marked hand; not model results)

```
{
 "beta1": 0.8602150537634409,
 "beta2": 0.6060606060606061,
 "cl1_pF": 1.2591397849462367,
 "step_diff_V": 0.512,
 "sr_min_V_per_us": 11.377777777777776,
 "gbw_lin_MHz": 4.1115026965406285,
 "gbw_full_MHz": 8.223005393081257,
 "gm_noise": {
  "7": {
   "gm_uS": 676.2362448979591,
   "i_tail_uA": 90.16483265306123,
   "i_ota1_uA": 198.36263183673472,
   "gbw_MHz": 85.47608642038674,
   "sr_diff_V_per_us": 71.6082787082382,
   "total_uA": 229.89183490705275
  },
  "10": {
   "gm_uS": 331.35576,
   "i_tail_uA": 44.18076799999999,
   "i_ota1_uA": 97.19768959999999,
   "gbw_MHz": 41.8832823459895,
   "sr_diff_V_per_us": 35.08805656703671,
   "total_uA": 128.72689267031802
  },
  "14": {
   "gm_uS": 169.05906122448977,
   "i_tail_uA": 22.541208163265306,
   "i_ota1_uA": 49.59065795918368,
   "gbw_MHz": 21.369021605096684,
   "sr_diff_V_per_us": 17.90206967705955,
   "total_uA": 81.11986102950172
  }
 },
 "power_other": {
  "ota2_uA": 5.529203070318037,
  "comparator_uA": 6.0,
  "bias_cmfb_refs_uA": 20.0
 },
 "ron_ohm": 819.672131147541,
 "vov_V": 0.5,
 "tau_in_ns_rsrc0": 7.258196721311475,
 "rsrc_max_tau10_ohm": 498.50968703427725,
 "rsrc_max_tau45_ohm": 6862.146050670641,
 "rsrc_max_tau18_ohm": 2089.418777943368,
 "fast_4MHz": {
  "t_half_ns": 112.50000000000001,
  "gbw_lin_MHz": 8.223005393081257,
  "gbw_full_MHz": 16.446010786162514,
  "sr_min_V_per_us": 22.755555555555553
 },
 "tau_in_budget_t12_ns": 18.750000000000004,
 "t_reset_15tau_ns": 59.99999999999999,
 "r_after_15tau": 3.059023205018258e-07,
 "tau_needed_for_r1e-4": 9.210340371976184,
 "stage2": {
  "Cs2 0.25 / Cint2 0.5 pF, c2 0.5": {
   "ktc2_in_uV_per_conv": 0.015716229519085474,
   "mim_um2_diff_x1.5": 1125.0,
   "x2_step_V": 0.512
  },
  "Cs2 0.5 / Cint2 1 pF, c2 0.5": {
   "ktc2_in_uV_per_conv": 0.011113052467629532,
   "mim_um2_diff_x1.5": 2250.0,
   "x2_step_V": 0.512
  },
  "Cs2 1 / Cint2 2 pF, c2 0.5": {
   "ktc2_in_uV_per_conv": 0.007858114759542737,
   "mim_um2_diff_x1.5": 4500.0,
   "x2_step_V": 0.512
  },
  "Cs2 1 / Cint2 4 pF, c2 0.25": {
   "ktc2_in_uV_per_conv": 0.007858114759542737,
   "mim_um2_diff_x1.5": 7499.999999999998,
   "x2_step_V": 0.256
  },
  "Cs2 0.5 / Cint2 2 pF, c2 0.25": {
   "ktc2_in_uV_per_conv": 0.011113052467629532,
   "mim_um2_diff_x1.5": 3749.999999999999,
   "x2_step_V": 0.256
  }
 },
 "mim_um2": {
  "Cs1": 749.9999999999999,
  "Cint1": 5999.999999999999,
  "Cs2": 749.9999999999999,
  "Cint2": 1499.9999999999998
 },
 "mim_total_um2": 8999.999999999998,
 "tile_um2": 75150,
 "kick_gain_ppm_per_mV": 3.814697265625,
 "x2_min_step_V": 0.512
}
```

## Verdict

ACCEPT

