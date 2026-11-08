# S4: corner-aware tier-0 model (WO-06, re-gated in WO-06a)

Command: `python3 -m model.studies.s4_corners --out /home/mempool/regr/tt/WO-06a/s4`

Wall time 463 s on 4 processes (grid 411 s, MC 50 s). No transistor data exists: every mapping is an **assumption** (nominal at tt/27/3.3, the SPEC 3.0 limit at that mechanism's worst corner, linear in a 0..1 stress between). A result here says the budget closes if each block just meets SPEC 3.0; it is not a statement about a circuit.

## Mapping (explicit)

| block | parameter | nominal (tt/27/3.3) | worst | stress | worst at |
|---|---|---|---|---|---|
| OTA1/OTA2 | A(v) table (dB, |Vout,diff| 0/1.4/2.0/3.1 V) | 90/88/85/75 | 80/75/70/60 (80 and 75 = SPEC; 70, 60 assumed) | s_gain | ss/125/3.0 |
| OTA1 | en white (kT/C excess = 1 + 0.5 (en/6.9)^2) | 7 nV/rtHz | 10 nV/rtHz (SPEC: info only, sampled noise <= 250 uV) | s_gain | ss/125/3.0 |
| OTA1 | 1/f corner fc | 400 kHz | 631 kHz (SPEC info) | s_gain | ss/125/3.0 |
| OTA1 | lf_gain (input referral of slow errors) | 9.3 | 9.3 (pessimistic bound, as S3) | const | all |
| OTA1, OTA2 | Vos1, Vos2 | +-9 mV | +-9 mV 3 sigma, 4 sign combinations | const (mismatch) | all |
| Comparator | offset | +-20 mV | +-20 mV 3 sigma, sign combinations with Vos | const (mismatch) | all |
| Comparator | input-referred noise rms | 2 mV | 5 mV | s_gain | ss/125/3.0 |
| Input TG | tau_in = (Ron + 500 ohm + R_src)(5 pF + Cs) | 8 ns | 18.75 ns | s_speed | ss/-40/3.0 |
| Reference | tau_ref (500 ohm, 5 pF pad) | 3 ns | 10 ns | s_speed | ss/-40/3.0 |
| Reset | r on x1 and x2 at conversion start | 1e-5 | 1e-4 | s_speed | ss/-40/3.0 |
| Virtual ground | leakage I (offset I/(fs Cs), non-cancelling fraction rho 0.1 %) | ~0.1 pA (tt/27/3.3) | 100 pA = 100 pA x 2^((T-125)/10) (V/3.6)^2 x proc{ff 1, fs/sf .7, tt/RC .5, ss .3} | formula | ff/125/3.6 |
| Capacitors | Cs (kT/C) | 0.5 pF | ss_hh x1.1, ff_ll x0.9 (ASSUMED +-10 % MIM corner) | corner | ff_ll |
| kT/C | temperature in kT | T + 273.15 K | 398 K at 125 C | T | 125 C |
| Reference pins | R_ext per pin (DC) | 10 ohm | 10 ohm (board spec) | const | all |
| Cs+/Cs- | mismatch (CMRR) | - | 0.75 % 3 sigma (MC only) | MC | MC |

Stress variables: s_gain = (proc{ss 1, sf/fs .5} + max(0,(T-27)/98) + max(0,(3.3-V)/.3))/3; s_speed = (proc{ss 1, sf/fs/ss_hh .5} + max(0,(27-T)/67) + max(0,(3.3-V)/.3))/3. ff, ff_ll, tt and the RC points (MOS typical) carry no proc stress; nothing is better than nominal.

## Limits (pass = every point inside)

| spec | limit | source |
|---|---|---|
| noise @15 SPS (u = 0) | 2.5 uV; 3.0 uV at fs < 2 MHz and T > 85 C | SPEC 3.0 budget; D27 (the applied limit is printed per row in the appendix) |
| noise @240 SPS (u = 0) | 5 uV (gated only where 240 SPS is reachable, fs >= 0.49 MHz) | D29 |
| CMRR, sys chop on / off | >= 100 dB / >= 60 dB at Vin_cm 0.2, 1.0, 2.0 V (VREF_CM 1.0 V assumed), tt/27 and worst MC draws | D30, sys-off 60 dB per D32 |
| INL, N 4096 | 20 ppm | SPEC 3.0 budget (4 ppm of it is unmodelled reserve) |
| sys-pair offset | 5 uV | SPEC 3.0 budget = model residual + reset 2 r x1max/(c1(N-1)) + leakage x rho 0.1 % (2 uV of it unmodelled reserve) |
| gain error | 5000 ppm | SPEC 3.0 |
| inter-conversion memory | 0.5 uV | review S3-5 (+-FS then 0) |

## Corner grid: 126 evaluations = 63 analog PVT points x fs {0.25, 2} MHz

Worst point per spec (over all points and both fs):

| spec | worst value | limit | margin (limit/value) | margin % (limit/value - 1) | worst point | fs [MHz] |
|---|---|---|---|---|---|---|
| n15 | 2.983 uV | 3 | x1.01 | +1 % | ss/125/3 | 0.25 |
| n240 | 3.603 uV | 5 | x1.39 | +39 % | ff_ll/125/3 | 2 |
| inl | 5.234 ppm | 20 | x3.82 | +282 % | ss/125/3 | 0.25 |
| off | 0.8478 uV | 5 | x5.90 | +490 % | ff/125/3.6 | 0.25 |
| gain | 71.6 ppm | 5000 | x69.83 | +6883 % | ss/125/3 | 0.25 |
| mem | 0.3072 uV | 0.5 | x1.63 | +63 % | ss/-40/3 | 2 |


Worst per spec at fs 0.25 MHz:

| spec | worst | limit | margin % (limit/value - 1) | point |
|---|---|---|---|---|
| n15 | 2.983 uV | 3 | +1 % | ss/125/3 |
| n240 (NOT GATED: 240 SPS unreachable below 0.49 MHz) | 9.86 uV | 5 | -49 % | ss/125/3 |
| inl | 5.234 ppm | 20 | +282 % | ss/125/3 |
| off | 0.8478 uV | 5 | +490 % | ff/125/3.6 |
| gain | 71.6 ppm | 5000 | +6883 % | ss/125/3 |
| mem | 0.3042 uV | 0.5 | +64 % | ss/-40/3 |


Worst per spec at fs 2 MHz:

| spec | worst | limit | margin % (limit/value - 1) | point |
|---|---|---|---|---|
| n15 | 0.7784 uV | 2.5 | +221 % | ss/125/3 |
| n240 | 3.603 uV | 5 | +39 % | ff_ll/125/3 |
| inl | 4.177 ppm | 20 | +379 % | ss/125/3 |
| off | 0.4772 uV | 5 | +948 % | ss/-40/3 |
| gain | 64.53 ppm | 5000 | +7649 % | ss/125/3 |
| mem | 0.3072 uV | 0.5 | +63 % | ss/-40/3 |


## Monte Carlo (Vos1, Vos2 3 sigma 9 mV; comparator offset 3 sigma 20 mV; Cs+/Cs- 0.75 % 3 sigma)

INL and gain per draw: 161-point sweep, residue-corrected; offset per draw: sys-pair residual (24 inputs) + reset + leakage x rho. Pass: mu + 3 sigma and every sample inside the limit. Worst-INL point = grid worst INL (ss/125/3, 0.25 MHz); worst-offset point = grid worst offset (ff/125/3.6, 0.25 MHz).

| set | point | draws | INL ppm mu/sigma/max | gain ppm mu/sigma/max | offset uV mu/sigma/max | raw sys-off offset uV mean|.|/max (info) |
|---|---|---|---|---|---|---|
| tt/27 | tt/27/3.3 @ 0.25 MHz | 200 | 0.452 / 0.0038 / 0.469 (lim 20) | 17.4 / 0.00051 / 17.4 (lim 5000) | 0.0481 / 6.4e-05 / 0.0484 (lim 5) | 47.5 / 88.7 |
| tt/27 | tt/27/3.3 @ 2 MHz | 200 | 0.873 / 0.0021 / 0.88 (lim 20) | 10.3 / 0.00048 / 10.3 (lim 5000) | 0.0478 / 6.9e-05 / 0.0481 (lim 5) | 47.2 / 81.6 |
| worst-INL | ss/125/3 @ 0.25 MHz | 50 | 5.11 / 0.023 / 5.16 (lim 20) | 71.6 / 0.0033 / 71.6 (lim 5000) | 0.501 / 0.00084 / 0.504 (lim 5) | 47.6 / 74.7 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 50 | 1.2 / 0.007 / 1.22 (lim 20) | 28.1 / 0.00089 / 28.1 (lim 5000) | 0.848 / 0.00017 / 0.848 (lim 5) | 48.2 / 73.6 |

## CMRR (D30, D33: on the D12 residual eps_eff)

**This models the hypothesis; WO-08 checks it in SPICE.** D33 (REVIEW-S4S5b C-M3): D12 cancels the Cs+/Cs- mismatch term to first order, so the CM->diff coefficient is the D12 residual eps_eff = ((Cp,top/Cs) eps_Cs - dCp,top/Cs) / (1 + Cp,top/Cs) + eps_inj (D36: sign '-' confirmed by WO-09 --cm2, deck vs closed form 0.0 % in 12 cases). MC: signed per-draw sum of the two independent Gaussians, eps_inj at its worst sign against the draw; 3 sigma corner rows: RSS of the two random terms + |eps_inj| linearly. A CM change dVcm = Vin_cm - VREF_CM (VREF_CM = 1 V ASSUMED, SPEC 3.0 does not fix it) gives a differential term eps_eff*dVcm. Allocation (C4): Cp,top 20 fF per side (fixed), dCp,top Gaussian 3 sigma 0.25 fF, eps_Cs Gaussian 3 sigma 0.75 %, eps_inj 0.00028 (fixed, worst sign). Corner points use the 3 sigma values; the worst-draw row uses the largest per-draw |eps_eff| of the MC draws. Hypothesis for the sys-chop behaviour (unchanged): the pin-side swap does not change the pin CM, so the term is fixed in the modulator frame, with the same sign in both halves of a sys pair (like an OTA offset); it is modelled as an additive term e on the sampled input after the swap, u_in = s*u + e, demodulated exactly as the chip does (conversion with sys_sign +1 and -1, residue-corrected, averaged). Sys chop off: the term stays, error = eps_eff*dVcm (tested to 2 %). The --nonvac copy with the term flipping with the input fails the sys-on gate. D38(a): the earlier sys-on 'metric floor' (D37(b)) was a model bug in the S4 reconstruction (residue added in the modulator frame after demodulation, C1); iadc.convert now returns the demodulated residue-corrected u_corr and the sys-on gate is evaluated at every N. The tier-1 cm2 deck (137-173 dB) is independent evidence. CMRR = 20 log10(dVcm / input-referred error). Errors below 1e-12 V are capped (240 dB). Sets: tt/27 (both fs) and the worst-INL / worst-offset points.

### Theory check (hand calculation)

At tt, Cs = 0.5 pF, 1 + Cp,top/Cs = 1.04: dCp,top/Cs/(1+Cp/Cs) = 4.81e-04; (Cp,top/Cs) eps_Cs/(1+Cp/Cs) = 2.88e-04; eps_inj = 2.80e-04. RSS of the two random terms + |inj| = **8.407e-04** = 61.5 dB. Printed 3 sigma eps_eff = 8.407e-04 = 61.5 dB. Agreement within 10 %: **yes**. MC |eps_eff| (signed sum, inj worst sign): mean 429 uV/V, max of draws 831 uV/V (eps_Cs-only mean 2175, max 6209).

**Superseded (D36): D33 linear worst-case sum** = 1.080e-03 = 59.3 dB (REJECT). A linear sum of independent 3 sigma terms is about 4.2 sigma, beyond the MC pass rule; D36 uses RSS of the independent random terms plus |eps_inj|. The result 61.5 dB passes the 60 dB gate (+1.5 dB) and misses the 66 dB design target (-4.5 dB, informational). The target stays a C4/C10 layout goal (dCp,top 3 sigma <= 0.15 fF). The gate is not relaxed.

Worst sys-off CMRR over all rows below: 61.1 dB (gate 60 dB, margin +1.1 dB; against the 66 dB design target -4.9 dB, informational).

| set | point | eps | eps uV/V | Vin_cm V | dVcm V | sys-off err uV | sys-off CMRR dB (gate >= 60) | sys-on err uV | sys-on CMRR dB (gate >= 100, all N) |
|---|---|---|---|---|---|---|---|---|---|
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 841 | 0.2 | -0.8 | 672.5 | 61.5 | 3.1e-05 | 208.2 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 841 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 841 | 2 | +1.0 | 840.7 | 61.5 | 4.76e-05 | 206.4 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 831 | 0.2 | -0.8 | 664.9 | 61.6 | 5.9e-05 | 202.6 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 831 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 831 | 2 | +1.0 | 831.1 | 61.6 | 4.9e-05 | 206.2 |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 841 | 0.2 | -0.8 | 672.5 | 61.5 | 2.74e-05 | 209.3 |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 841 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 841 | 2 | +1.0 | 840.7 | 61.5 | 5.72e-05 | 204.8 |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 883 | 0.2 | -0.8 | 706.6 | 61.1 | 7.47e-05 | 200.6 |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 883 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 883 | 2 | +1.0 | 883.2 | 61.1 | 0.000146 | 196.7 |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 841 | 0.2 | -0.8 | 672.5 | 61.5 | 0.00144 | 174.9 |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 841 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 841 | 2 | +1.0 | 840.6 | 61.5 | 0.000498 | 186.1 |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 796 | 0.2 | -0.8 | 637 | 62.0 | 0.000987 | 178.2 |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 796 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 796 | 2 | +1.0 | 796.3 | 62.0 | 0.00125 | 178.1 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 841 | 0.2 | -0.8 | 672.5 | 61.5 | 4.52e-05 | 205.0 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 841 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 841 | 2 | +1.0 | 840.6 | 61.5 | 5.04e-05 | 205.9 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 789 | 0.2 | -0.8 | 631.3 | 62.1 | 3.58e-05 | 207.0 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 789 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 789 | 2 | +1.0 | 789.1 | 62.1 | 5.78e-05 | 204.8 |


### Superseded (D33): old eps_Cs * dVcm term

Kept for the record, not gated. 3 sigma 7500 uV/V gives 42.5 dB sys-off; it modelled a mechanism that D12 cancels to first order.

| set | point | eps | eps uV/V | Vin_cm V | dVcm V | sys-off err uV | sys-off CMRR dB (gate >= 60) | sys-on err uV | sys-on CMRR dB (gate >= 100, all N) |
|---|---|---|---|---|---|---|---|---|---|
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 8.47e-05 | 199.5 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 5.04e-05 | 206.0 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 6209 | 0.2 | -0.8 | 4967 | 44.1 | 6.71e-05 | 201.5 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 6209 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 6209 | 2 | +1.0 | 6209 | 44.1 | 5.37e-06 | 225.4 |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 6.59e-05 | 201.7 |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 3.18e-06 | 229.9 |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 6667 | 0.2 | -0.8 | 5334 | 43.5 | 5.24e-05 | 203.7 |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 6667 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 6667 | 2 | +1.0 | 6667 | 43.5 | 2.03e-05 | 213.8 |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 0.000683 | 181.4 |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 0.000794 | 182.0 |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 4235 | 0.2 | -0.8 | 3388 | 47.5 | 0.000759 | 180.5 |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 4235 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 4235 | 2 | +1.0 | 4235 | 47.5 | 0.0015 | 176.5 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 0.000259 | 189.8 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 7.16e-05 | 202.9 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 6334 | 0.2 | -0.8 | 5067 | 44.0 | 8.37e-05 | 199.6 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 6334 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 6334 | 2 | +1.0 | 6334 | 44.0 | 0.000209 | 193.6 |


## Fast mode (fs 4 MHz, informational, not gated)

Thermal noise: u = 0, no averaging (k 1, sys-chop pair); at small N it is far below one LSB, so decisions rarely flip and the measured rms can be 0: the quantization column (raw accumulators, rms over a +-0.9 FS sweep) is the real fast-mode resolution limit. INL: ideal-OTA-table model (tables at the corner) with tau_in/tau_ref scaled to the 4 MHz t_half, residue-corrected. `with settle`: hand slew-then-settle penalty lumped as a finite-gain-equivalent pole error (ESTIMATE, not a simulation): eps = exp(-(t_half - dV/SR)/tau_ota), tau_ota = 1/(2 pi beta GBW), OTA1 beta .84, dV .512 V, SR 12 V/us; OTA2 beta .61, dV c2(.6+k)VREF, SR 25 V/us; A_eq = (1+c)/((1+c)/A(1 V) + eps).

| point | N | GBW MHz | thermal noise uV rms (u = 0) | quantization rms uV (raw) | INL ppm (no settle) | INL ppm with settle | gain ppm with settle | eps OTA1 / OTA2 |
|---|---|---|---|---|---|---|---|---|
| tt/27/3.3 | 64 | 10 | 0 | 3.21e+03 | 1.42 | 847 | -19585 | 2.5e-02 / 8.7e-02 |
| tt/27/3.3 | 64 | 20 | 0 | 3.21e+03 | 1.42 | 156 | -1175 | 6.3e-04 / 7.5e-03 |
| tt/27/3.3 | 256 | 10 | 41.5 | 200 | 2.04 | 290 | -13809 | 2.5e-02 / 8.7e-02 |
| tt/27/3.3 | 256 | 20 | 41.5 | 200 | 2.04 | 27.2 | -484 | 6.3e-04 / 7.5e-03 |
| tt/27/3.3 | 1024 | 10 | 7.32 | 18.8 | 2.23 | 113 | -12172 | 2.5e-02 / 8.7e-02 |
| tt/27/3.3 | 1024 | 20 | 7.32 | 18.8 | 2.23 | 4.62 | -333 | 6.3e-04 / 7.5e-03 |
| ss/125/3 | 64 | 10 | 0 | 3.28e+03 | 7.84 | 1.26e+03 | -20177 | 2.5e-02 / 8.7e-02 |
| ss/125/3 | 64 | 20 | 0 | 3.28e+03 | 7.84 | 159 | -1336 | 6.3e-04 / 7.5e-03 |
| ss/125/3 | 256 | 10 | 40.7 | 268 | 3.73 | 296 | -13956 | 2.5e-02 / 8.7e-02 |
| ss/125/3 | 256 | 20 | 40.7 | 268 | 3.73 | 27.1 | -572 | 6.3e-04 / 7.5e-03 |
| ss/125/3 | 1024 | 10 | 9.91 | 71.9 | 3.29 | 138 | -12262 | 2.5e-02 / 8.7e-02 |
| ss/125/3 | 1024 | 20 | 9.91 | 71.9 | 3.29 | 4.64 | -398 | 6.3e-04 / 7.5e-03 |
| ss/-40/3 | 64 | 10 | 0 | 3.54e+03 | 7.2 | 1.11e+03 | -20259 | 2.5e-02 / 8.7e-02 |
| ss/-40/3 | 64 | 20 | 0 | 3.54e+03 | 7.2 | 152 | -1553 | 6.3e-04 / 7.5e-03 |
| ss/-40/3 | 256 | 10 | 39.9 | 310 | 1.23 | 305 | -14011 | 2.5e-02 / 8.7e-02 |
| ss/-40/3 | 256 | 20 | 39.9 | 310 | 1.23 | 26.5 | -613 | 6.3e-04 / 7.5e-03 |
| ss/-40/3 | 1024 | 10 | 7.19 | 68.1 | 0.995 | 141 | -12276 | 2.5e-02 / 8.7e-02 |
| ss/-40/3 | 1024 | 20 | 7.19 | 68.1 | 0.995 | 4.59 | -388 | 6.3e-04 / 7.5e-03 |

Proposed fast-mode INL targets (GBW 20 MHz design target, worst of the three points, 1.5x margin rounded up to 1-2-5): N 64: <= 500 ppm; N 256: <= 50 ppm; N 1024: <= 10 ppm. Proposal only; the SPEC fast-mode target is not set.

## Verdict

ACCEPT

GATE grid specs: ACCEPT
GATE MC INL/gain/offset: ACCEPT
GATE CMRR sys on >= 100 dB: ACCEPT
GATE CMRR sys off >= 60 dB (D32): ACCEPT


## Appendix: all grid evaluations

| point | fs MHz | n15 | n15 limit | n240 | n240 limit | INL | gain | offset | memory |
|---|---|---|---|---|---|---|---|---|---|
| tt/-40/3 | 0.25 | 2.01 | 2.5 | 6.48 | not gated | 1.23 | 28.1 | 0.334 | 0.217 |
| tt/-40/3 | 2 | 0.521 | 2.5 | 2.6 | 5 | 0.468 | 21 | 0.334 | 0.219 |
| tt/-40/3.3 | 0.25 | 1.88 | 2.5 | 6.1 | not gated | 0.466 | 17.4 | 0.191 | 0.126 |
| tt/-40/3.3 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.88 | 10.3 | 0.191 | 0.127 |
| tt/-40/3.6 | 0.25 | 1.88 | 2.5 | 6.1 | not gated | 0.466 | 17.4 | 0.191 | 0.126 |
| tt/-40/3.6 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.88 | 10.3 | 0.191 | 0.127 |
| tt/27/3 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28.1 | 0.191 | 0.126 |
| tt/27/3 | 2 | 0.599 | 2.5 | 2.76 | 5 | 0.469 | 21 | 0.191 | 0.125 |
| tt/27/3.3 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.466 | 17.4 | 0.0482 | 0.0316 |
| tt/27/3.3 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.881 | 10.3 | 0.0478 | 0.0321 |
| tt/27/3.6 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.466 | 17.4 | 0.0482 | 0.0316 |
| tt/27/3.6 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.881 | 10.3 | 0.0478 | 0.0321 |
| tt/125/3 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.66 | 44.9 | 0.469 | 0.122 |
| tt/125/3 | 2 | 0.734 | 2.5 | 3.18 | 5 | 1.74 | 37.9 | 0.226 | 0.124 |
| tt/125/3.3 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28.1 | 0.384 | 0.0311 |
| tt/125/3.3 | 2 | 0.684 | 2.5 | 3.09 | 5 | 0.469 | 21 | 0.09 | 0.0335 |
| tt/125/3.6 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28.1 | 0.448 | 0.0311 |
| tt/125/3.6 | 2 | 0.684 | 2.5 | 3.09 | 5 | 0.469 | 21 | 0.098 | 0.0335 |
| ss/-40/3 | 0.25 | 2.16 | 2.5 | 7.03 | not gated | 2.66 | 45 | 0.477 | 0.304 |
| ss/-40/3 | 2 | 0.563 | 2.5 | 2.86 | 5 | 1.74 | 37.9 | 0.477 | 0.307 |
| ss/-40/3.3 | 0.25 | 2.01 | 2.5 | 6.48 | not gated | 1.23 | 28.1 | 0.334 | 0.217 |
| ss/-40/3.3 | 2 | 0.521 | 2.5 | 2.6 | 5 | 0.468 | 21 | 0.334 | 0.219 |
| ss/-40/3.6 | 0.25 | 2.01 | 2.5 | 6.48 | not gated | 1.23 | 28.1 | 0.334 | 0.217 |
| ss/-40/3.6 | 2 | 0.521 | 2.5 | 2.6 | 5 | 0.468 | 21 | 0.334 | 0.219 |
| ss/27/3 | 0.25 | 2.45 | 2.5 | 7.91 | not gated | 2.66 | 45 | 0.334 | 0.212 |
| ss/27/3 | 2 | 0.633 | 2.5 | 2.92 | 5 | 1.74 | 37.9 | 0.334 | 0.215 |
| ss/27/3.3 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28.1 | 0.191 | 0.126 |
| ss/27/3.3 | 2 | 0.599 | 2.5 | 2.76 | 5 | 0.469 | 21 | 0.191 | 0.125 |
| ss/27/3.6 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28.1 | 0.191 | 0.126 |
| ss/27/3.6 | 2 | 0.599 | 2.5 | 2.76 | 5 | 0.469 | 21 | 0.191 | 0.125 |
| ss/125/3 | 0.25 | 2.98 | 3 | 9.86 | not gated | 5.23 | 71.6 | 0.502 | 0.205 |
| ss/125/3 | 2 | 0.778 | 2.5 | 3.37 | 5 | 4.18 | 64.5 | 0.355 | 0.207 |
| ss/125/3.3 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.66 | 44.9 | 0.393 | 0.122 |
| ss/125/3.3 | 2 | 0.734 | 2.5 | 3.18 | 5 | 1.74 | 37.9 | 0.217 | 0.124 |
| ss/125/3.6 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.66 | 44.9 | 0.432 | 0.122 |
| ss/125/3.6 | 2 | 0.734 | 2.5 | 3.18 | 5 | 1.74 | 37.9 | 0.221 | 0.124 |
| ff/-40/3 | 0.25 | 2.01 | 2.5 | 6.48 | not gated | 1.23 | 28.1 | 0.334 | 0.217 |
| ff/-40/3 | 2 | 0.521 | 2.5 | 2.6 | 5 | 0.468 | 21 | 0.334 | 0.219 |
| ff/-40/3.3 | 0.25 | 1.88 | 2.5 | 6.1 | not gated | 0.466 | 17.4 | 0.191 | 0.126 |
| ff/-40/3.3 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.88 | 10.3 | 0.191 | 0.127 |
| ff/-40/3.6 | 0.25 | 1.88 | 2.5 | 6.1 | not gated | 0.466 | 17.4 | 0.191 | 0.126 |
| ff/-40/3.6 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.88 | 10.3 | 0.191 | 0.127 |
| ff/27/3 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28.1 | 0.192 | 0.126 |
| ff/27/3 | 2 | 0.599 | 2.5 | 2.76 | 5 | 0.469 | 21 | 0.191 | 0.125 |
| ff/27/3.3 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.466 | 17.4 | 0.0486 | 0.0316 |
| ff/27/3.3 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.881 | 10.3 | 0.0479 | 0.0321 |
| ff/27/3.6 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.466 | 17.4 | 0.0487 | 0.0316 |
| ff/27/3.6 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.881 | 10.3 | 0.0479 | 0.0321 |
| ff/125/3 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.66 | 44.9 | 0.747 | 0.122 |
| ff/125/3 | 2 | 0.734 | 2.5 | 3.18 | 5 | 1.74 | 37.9 | 0.261 | 0.124 |
| ff/125/3.3 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28.1 | 0.72 | 0.0311 |
| ff/125/3.3 | 2 | 0.684 | 2.5 | 3.09 | 5 | 0.469 | 21 | 0.132 | 0.0335 |
| ff/125/3.6 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28.1 | 0.848 | 0.0311 |
| ff/125/3.6 | 2 | 0.684 | 2.5 | 3.09 | 5 | 0.469 | 21 | 0.148 | 0.0335 |
| sf/-40/3 | 0.25 | 2.1 | 2.5 | 6.54 | not gated | 1.84 | 35.6 | 0.406 | 0.26 |
| sf/-40/3 | 2 | 0.54 | 2.5 | 2.77 | 5 | 0.99 | 28.5 | 0.406 | 0.264 |
| sf/-40/3.3 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.786 | 22.1 | 0.262 | 0.171 |
| sf/-40/3.3 | 2 | 0.518 | 2.5 | 2.46 | 5 | 0.614 | 15.1 | 0.262 | 0.174 |
| sf/-40/3.6 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.786 | 22.1 | 0.262 | 0.171 |
| sf/-40/3.6 | 2 | 0.518 | 2.5 | 2.46 | 5 | 0.614 | 15.1 | 0.262 | 0.174 |
| sf/27/3 | 0.25 | 2.34 | 2.5 | 7.66 | not gated | 1.84 | 35.6 | 0.263 | 0.17 |
| sf/27/3 | 2 | 0.623 | 2.5 | 2.93 | 5 | 0.991 | 28.5 | 0.263 | 0.171 |
| sf/27/3.3 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.787 | 22.1 | 0.12 | 0.0778 |
| sf/27/3.3 | 2 | 0.573 | 2.5 | 2.81 | 5 | 0.614 | 15.1 | 0.12 | 0.0794 |
| sf/27/3.6 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.787 | 22.1 | 0.12 | 0.0778 |
| sf/27/3.6 | 2 | 0.573 | 2.5 | 2.81 | 5 | 0.614 | 15.1 | 0.12 | 0.0794 |
| sf/125/3 | 0.25 | 2.9 | 3 | 9.35 | not gated | 3.76 | 56.8 | 0.652 | 0.168 |
| sf/125/3 | 2 | 0.757 | 2.5 | 3.33 | 5 | 2.77 | 49.7 | 0.312 | 0.166 |
| sf/125/3.3 | 0.25 | 2.71 | 3 | 8.73 | not gated | 1.84 | 35.6 | 0.59 | 0.0781 |
| sf/125/3.3 | 2 | 0.711 | 2.5 | 3.22 | 5 | 0.99 | 28.5 | 0.178 | 0.0785 |
| sf/125/3.6 | 0.25 | 2.71 | 3 | 8.73 | not gated | 1.84 | 35.6 | 0.68 | 0.0781 |
| sf/125/3.6 | 2 | 0.711 | 2.5 | 3.22 | 5 | 0.99 | 28.5 | 0.189 | 0.0785 |
| fs/-40/3 | 0.25 | 2.1 | 2.5 | 6.54 | not gated | 1.84 | 35.6 | 0.406 | 0.26 |
| fs/-40/3 | 2 | 0.54 | 2.5 | 2.77 | 5 | 0.99 | 28.5 | 0.406 | 0.264 |
| fs/-40/3.3 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.786 | 22.1 | 0.262 | 0.171 |
| fs/-40/3.3 | 2 | 0.518 | 2.5 | 2.46 | 5 | 0.614 | 15.1 | 0.262 | 0.174 |
| fs/-40/3.6 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.786 | 22.1 | 0.262 | 0.171 |
| fs/-40/3.6 | 2 | 0.518 | 2.5 | 2.46 | 5 | 0.614 | 15.1 | 0.262 | 0.174 |
| fs/27/3 | 0.25 | 2.34 | 2.5 | 7.66 | not gated | 1.84 | 35.6 | 0.263 | 0.17 |
| fs/27/3 | 2 | 0.623 | 2.5 | 2.93 | 5 | 0.991 | 28.5 | 0.263 | 0.171 |
| fs/27/3.3 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.787 | 22.1 | 0.12 | 0.0778 |
| fs/27/3.3 | 2 | 0.573 | 2.5 | 2.81 | 5 | 0.614 | 15.1 | 0.12 | 0.0794 |
| fs/27/3.6 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.787 | 22.1 | 0.12 | 0.0778 |
| fs/27/3.6 | 2 | 0.573 | 2.5 | 2.81 | 5 | 0.614 | 15.1 | 0.12 | 0.0794 |
| fs/125/3 | 0.25 | 2.9 | 3 | 9.35 | not gated | 3.76 | 56.8 | 0.652 | 0.168 |
| fs/125/3 | 2 | 0.757 | 2.5 | 3.33 | 5 | 2.77 | 49.7 | 0.312 | 0.166 |
| fs/125/3.3 | 0.25 | 2.71 | 3 | 8.73 | not gated | 1.84 | 35.6 | 0.59 | 0.0781 |
| fs/125/3.3 | 2 | 0.711 | 2.5 | 3.22 | 5 | 0.99 | 28.5 | 0.178 | 0.0785 |
| fs/125/3.6 | 0.25 | 2.71 | 3 | 8.73 | not gated | 1.84 | 35.6 | 0.68 | 0.0781 |
| fs/125/3.6 | 2 | 0.711 | 2.5 | 3.22 | 5 | 0.99 | 28.5 | 0.189 | 0.0785 |
| ss_hh/-40/3 | 0.25 | 1.94 | 2.5 | 6.44 | not gated | 1.22 | 28 | 0.405 | 0.265 |
| ss_hh/-40/3 | 2 | 0.499 | 2.5 | 2.42 | 5 | 0.405 | 20.2 | 0.405 | 0.266 |
| ss_hh/-40/3.3 | 0.25 | 1.81 | 2.5 | 6.1 | not gated | 0.454 | 17.3 | 0.262 | 0.173 |
| ss_hh/-40/3.3 | 2 | 0.468 | 2.5 | 2.38 | 5 | 1.02 | 9.54 | 0.262 | 0.175 |
| ss_hh/-40/3.6 | 0.25 | 1.81 | 2.5 | 6.1 | not gated | 0.454 | 17.3 | 0.262 | 0.173 |
| ss_hh/-40/3.6 | 2 | 0.468 | 2.5 | 2.38 | 5 | 1.02 | 9.54 | 0.262 | 0.175 |
| ss_hh/27/3 | 0.25 | 2.17 | 2.5 | 7.28 | not gated | 1.22 | 28 | 0.263 | 0.171 |
| ss_hh/27/3 | 2 | 0.565 | 2.5 | 2.82 | 5 | 0.404 | 20.2 | 0.262 | 0.174 |
| ss_hh/27/3.3 | 0.25 | 2.04 | 2.5 | 6.75 | not gated | 0.454 | 17.3 | 0.12 | 0.0788 |
| ss_hh/27/3.3 | 2 | 0.528 | 2.5 | 2.64 | 5 | 1.02 | 9.54 | 0.119 | 0.0794 |
| ss_hh/27/3.6 | 0.25 | 2.04 | 2.5 | 6.75 | not gated | 0.454 | 17.3 | 0.12 | 0.0788 |
| ss_hh/27/3.6 | 2 | 0.528 | 2.5 | 2.64 | 5 | 1.02 | 9.54 | 0.119 | 0.0794 |
| ss_hh/125/3 | 0.25 | 2.65 | 3 | 8.62 | not gated | 2.65 | 44.8 | 0.515 | 0.168 |
| ss_hh/125/3 | 2 | 0.693 | 2.5 | 2.99 | 5 | 1.65 | 37.1 | 0.295 | 0.17 |
| ss_hh/125/3.3 | 0.25 | 2.47 | 3 | 8.09 | not gated | 1.22 | 28 | 0.425 | 0.078 |
| ss_hh/125/3.3 | 2 | 0.666 | 2.5 | 3.08 | 5 | 0.404 | 20.2 | 0.158 | 0.0794 |
| ss_hh/125/3.6 | 0.25 | 2.47 | 3 | 8.09 | not gated | 1.22 | 28 | 0.483 | 0.078 |
| ss_hh/125/3.6 | 2 | 0.666 | 2.5 | 3.08 | 5 | 0.404 | 20.2 | 0.165 | 0.0794 |
| ff_ll/-40/3 | 0.25 | 2.14 | 2.5 | 6.78 | not gated | 1.25 | 28.2 | 0.334 | 0.217 |
| ff_ll/-40/3 | 2 | 0.549 | 2.5 | 2.72 | 5 | 0.538 | 21.8 | 0.334 | 0.219 |
| ff_ll/-40/3.3 | 0.25 | 1.97 | 2.5 | 6.66 | not gated | 0.479 | 17.5 | 0.191 | 0.126 |
| ff_ll/-40/3.3 | 2 | 0.521 | 2.5 | 2.51 | 5 | 0.743 | 11.2 | 0.191 | 0.127 |
| ff_ll/-40/3.6 | 0.25 | 1.97 | 2.5 | 6.66 | not gated | 0.479 | 17.5 | 0.191 | 0.126 |
| ff_ll/-40/3.6 | 2 | 0.521 | 2.5 | 2.51 | 5 | 0.743 | 11.2 | 0.191 | 0.127 |
| ff_ll/27/3 | 0.25 | 2.4 | 2.5 | 7.6 | not gated | 1.25 | 28.2 | 0.191 | 0.125 |
| ff_ll/27/3 | 2 | 0.629 | 2.5 | 2.97 | 5 | 0.537 | 21.8 | 0.191 | 0.127 |
| ff_ll/27/3.3 | 0.25 | 2.23 | 2.5 | 7.6 | not gated | 0.479 | 17.5 | 0.0483 | 0.0315 |
| ff_ll/27/3.3 | 2 | 0.592 | 2.5 | 2.8 | 5 | 0.743 | 11.2 | 0.0478 | 0.032 |
| ff_ll/27/3.6 | 0.25 | 2.23 | 2.5 | 7.6 | not gated | 0.479 | 17.5 | 0.0483 | 0.0315 |
| ff_ll/27/3.6 | 2 | 0.592 | 2.5 | 2.8 | 5 | 0.743 | 11.2 | 0.0478 | 0.032 |
| ff_ll/125/3 | 0.25 | 2.95 | 3 | 8.91 | not gated | 2.68 | 45.1 | 0.5 | 0.123 |
| ff_ll/125/3 | 2 | 0.775 | 2.5 | 3.6 | 5 | 1.83 | 38.7 | 0.23 | 0.124 |
| ff_ll/125/3.3 | 0.25 | 2.78 | 3 | 8.82 | not gated | 1.25 | 28.2 | 0.421 | 0.031 |
| ff_ll/125/3.3 | 2 | 0.726 | 2.5 | 3.51 | 5 | 0.536 | 21.8 | 0.0947 | 0.0317 |
| ff_ll/125/3.6 | 0.25 | 2.78 | 3 | 8.82 | not gated | 1.25 | 28.2 | 0.492 | 0.031 |
| ff_ll/125/3.6 | 2 | 0.726 | 2.5 | 3.51 | 5 | 0.536 | 21.8 | 0.104 | 0.0317 |

