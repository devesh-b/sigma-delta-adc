# S4: corner-aware tier-0 model (WO-06, re-gated in WO-06a)

Command: `python3 -m model.studies.s4_corners --out /home/mempool/regr/tt/WO-06a/s4`

Wall time 246 s on 4 processes (grid 217 s, MC 29 s). No transistor data exists: every mapping is an **assumption** (nominal at tt/27/3.3, the SPEC 3.0 limit at that mechanism's worst corner, linear in a 0..1 stress between). A result here says the budget closes if each block just meets SPEC 3.0; it is not a statement about a circuit.

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

| spec | worst value | limit | margin (limit/value) | worst point | fs [MHz] |
|---|---|---|---|---|---|
| n15 | 2.98 uV | 3 | x1.01 | ss/125/3 | 0.25 |
| n240 | 3.603 uV | 5 | x1.39 | ff_ll/125/3 | 2 |
| inl | 5.222 ppm | 20 | x3.83 | ss/125/3 | 0.25 |
| off | 0.9739 uV | 5 | x5.13 | ff/125/3.6 | 0.25 |
| gain | 71.49 ppm | 5000 | x69.94 | ss/125/3 | 0.25 |
| mem | 0.3073 uV | 0.5 | x1.63 | ss/-40/3 | 2 |


Worst per spec at fs 0.25 MHz:

| spec | worst | limit | point |
|---|---|---|---|
| n15 | 2.98 uV | 3 | ss/125/3 |
| n240 (NOT GATED: 240 SPS unreachable below 0.49 MHz) | 9.86 uV | 5 | ss/125/3 |
| inl | 5.222 ppm | 20 | ss/125/3 |
| off | 0.9739 uV | 5 | ff/125/3.6 |
| gain | 71.49 ppm | 5000 | ss/125/3 |
| mem | 0.3039 uV | 0.5 | ss/-40/3 |


Worst per spec at fs 2 MHz:

| spec | worst | limit | point |
|---|---|---|---|
| n15 | 0.7791 uV | 2.5 | ss/125/3 |
| n240 | 3.603 uV | 5 | ff_ll/125/3 |
| inl | 4.168 ppm | 20 | ss/125/3 |
| off | 0.6108 uV | 5 | ss/-40/3 |
| gain | 64.41 ppm | 5000 | ss/125/3 |
| mem | 0.3073 uV | 0.5 | ss/-40/3 |


## Monte Carlo (Vos1, Vos2 3 sigma 9 mV; comparator offset 3 sigma 20 mV; Cs+/Cs- 0.75 % 3 sigma)

INL and gain per draw: 161-point sweep, residue-corrected; offset per draw: sys-pair residual (24 inputs) + reset + leakage x rho. Pass: mu + 3 sigma and every sample inside the limit. Worst-INL point = grid worst INL (ss/125/3, 0.25 MHz); worst-offset point = grid worst offset (ff/125/3.6, 0.25 MHz).

| set | point | draws | INL ppm mu/sigma/max | gain ppm mu/sigma/max | offset uV mu/sigma/max | raw sys-off offset uV mean|.|/max (info) |
|---|---|---|---|---|---|---|
| tt/27 | tt/27/3.3 @ 0.25 MHz | 200 | 0.45 / 0.0038 / 0.467 (lim 20) | 17.4 / 0.0004 / 17.4 (lim 5000) | 0.108 / 0.044 / 0.231 (lim 5) | 47.5 / 88.7 |
| tt/27 | tt/27/3.3 @ 2 MHz | 200 | 0.877 / 0.0021 / 0.884 (lim 20) | 10.3 / 0.00037 / 10.3 (lim 5000) | 0.107 / 0.046 / 0.26 (lim 5) | 47.2 / 81.6 |
| worst-INL | ss/125/3 @ 0.25 MHz | 50 | 5.1 / 0.023 / 5.15 (lim 20) | 71.5 / 0.0031 / 71.5 (lim 5000) | 0.58 / 0.047 / 0.687 (lim 5) | 47.6 / 74.7 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 50 | 1.2 / 0.0071 / 1.22 (lim 20) | 28 / 0.00075 / 28 (lim 5000) | 0.902 / 0.039 / 0.983 (lim 5) | 48.2 / 73.6 |

## CMRR (D30)

**This models the hypothesis; WO-08 checks it in SPICE.** The Cs+/Cs- mismatch (|dCs/Cs| 2175 uV/V mean, max of draws 6209 uV/V, 3 sigma 7500 uV/V) turns an input common-mode change dVcm = Vin_cm - VREF_CM (VREF_CM = 1 V ASSUMED, SPEC 3.0 does not fix it) into a differential term eps*dVcm. Hypothesis: the pin-side sys-chop swap does not change the pin CM, so the mismatch term is fixed in the modulator frame, with the same sign in both halves of a sys pair (like an OTA offset); the demodulation flips it between the halves and the pair average cancels it. It is modelled as an additive term e on the sampled input after the swap, u_in = s*u + e, demodulated exactly as the chip does (conversion with sys_sign +1 and -1, residue-corrected, averaged). Sys chop off: the term stays, error = eps*dVcm (theory check, tested to 2 %). The S4 coder claim that sys chop does not cancel it is the opposite hypothesis (term flips with the input); the --nonvac copy models that and fails the sys-on gate. CMRR = 20 log10(dVcm / input-referred error). Errors below 1e-12 V are capped (240 dB). Sets: tt/27 (both fs) and the worst-INL / worst-offset points; eps = 3 sigma 7500 uV/V and the largest MC draw.

| set | point | eps | eps uV/V | Vin_cm V | dVcm V | sys-off err uV | sys-off CMRR dB (gate >= 60) | sys-on err uV | sys-on CMRR dB (gate >= 100) |
|---|---|---|---|---|---|---|---|---|---|
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 0.0395 | 146.1 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 0.25 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 0.0388 | 148.2 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 6209 | 0.2 | -0.8 | 4967 | 44.1 | 0.0346 | 147.3 |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 6209 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 0.25 MHz | worst_draw | 6209 | 2 | +1.0 | 6209 | 44.1 | 0.0151 | 156.4 |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 0.00413 | 165.7 |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 2 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 0.00599 | 164.5 |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 6667 | 0.2 | -0.8 | 5334 | 43.5 | 0.00912 | 158.9 |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 6667 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| tt/27 | tt/27/3.3 @ 2 MHz | worst_draw | 6667 | 2 | +1.0 | 6667 | 43.5 | 0.0369 | 148.7 |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 0.0536 | 143.5 |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-INL | ss/125/3 @ 0.25 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 0.018 | 154.9 |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 4235 | 0.2 | -0.8 | 3388 | 47.5 | 0.0421 | 145.6 |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 4235 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-INL | ss/125/3 @ 0.25 MHz | worst_draw | 4235 | 2 | +1.0 | 4235 | 47.5 | 0.0374 | 148.5 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 7500 | 0.2 | -0.8 | 6000 | 42.5 | 0.0355 | 147.0 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 7500 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-offset | ff/125/3.6 @ 0.25 MHz | 3sigma | 7500 | 2 | +1.0 | 7500 | 42.5 | 0.06 | 144.4 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 6334 | 0.2 | -0.8 | 5067 | 44.0 | 0.0545 | 143.3 |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 6334 | 1 | +0.0 | 0 | n/a (dVcm 0) | 0 | n/a (dVcm 0) |
| worst-offset | ff/125/3.6 @ 0.25 MHz | worst_draw | 6334 | 2 | +1.0 | 6334 | 44.0 | 0.0299 | 150.5 |


## Fast mode (fs 4 MHz, informational, not gated)

Thermal noise: u = 0, no averaging (k 1, sys-chop pair); at small N it is far below one LSB, so decisions rarely flip and the measured rms can be 0: the quantization column (raw accumulators, rms over a +-0.9 FS sweep) is the real fast-mode resolution limit. INL: ideal-OTA-table model (tables at the corner) with tau_in/tau_ref scaled to the 4 MHz t_half, residue-corrected. `with settle`: hand slew-then-settle penalty lumped as a finite-gain-equivalent pole error (ESTIMATE, not a simulation): eps = exp(-(t_half - dV/SR)/tau_ota), tau_ota = 1/(2 pi beta GBW), OTA1 beta .84, dV .512 V, SR 12 V/us; OTA2 beta .61, dV c2(.6+k)VREF, SR 25 V/us; A_eq = (1+c)/((1+c)/A(1 V) + eps).

| point | N | GBW MHz | thermal noise uV rms (u = 0) | quantization rms uV (raw) | INL ppm (no settle) | INL ppm with settle | gain ppm with settle | eps OTA1 / OTA2 |
|---|---|---|---|---|---|---|---|---|
| tt/27/3.3 | 64 | 10 | 0 | 3.21e+03 | 1.56 | 703 | -17358 | 2.5e-02 / 7.5e-02 |
| tt/27/3.3 | 64 | 20 | 0 | 3.21e+03 | 1.56 | 80.8 | -760 | 6.3e-04 / 5.7e-03 |
| tt/27/3.3 | 256 | 10 | 40.6 | 200 | 2.09 | 190 | -12955 | 2.5e-02 / 7.5e-02 |
| tt/27/3.3 | 256 | 20 | 40.6 | 200 | 2.09 | 12.2 | -392 | 6.3e-04 / 5.7e-03 |
| tt/27/3.3 | 1024 | 10 | 7.39 | 18.7 | 2.24 | 77 | -11785 | 2.5e-02 / 7.5e-02 |
| tt/27/3.3 | 1024 | 20 | 7.39 | 18.7 | 2.24 | 1.5 | -310 | 6.3e-04 / 5.7e-03 |
| ss/125/3 | 64 | 10 | 0 | 3.28e+03 | 6.54 | 780 | -17703 | 2.5e-02 / 7.5e-02 |
| ss/125/3 | 64 | 20 | 0 | 3.28e+03 | 6.54 | 79.9 | -922 | 6.3e-04 / 5.7e-03 |
| ss/125/3 | 256 | 10 | 40.7 | 269 | 3.55 | 205 | -13070 | 2.5e-02 / 7.5e-02 |
| ss/125/3 | 256 | 20 | 40.7 | 269 | 3.55 | 12.5 | -479 | 6.3e-04 / 5.7e-03 |
| ss/125/3 | 1024 | 10 | 9.82 | 71.5 | 3.26 | 75.3 | -11856 | 2.5e-02 / 7.5e-02 |
| ss/125/3 | 1024 | 20 | 9.82 | 71.5 | 3.26 | 1.73 | -374 | 6.3e-04 / 5.7e-03 |
| ss/-40/3 | 64 | 10 | 0 | 3.54e+03 | 7.19 | 661 | -17823 | 2.5e-02 / 7.5e-02 |
| ss/-40/3 | 64 | 20 | 0 | 3.54e+03 | 7.19 | 89.4 | -1193 | 6.3e-04 / 5.7e-03 |
| ss/-40/3 | 256 | 10 | 39.9 | 308 | 1.15 | 198 | -13105 | 2.5e-02 / 7.5e-02 |
| ss/-40/3 | 256 | 20 | 39.9 | 308 | 1.15 | 12.8 | -524 | 6.3e-04 / 5.7e-03 |
| ss/-40/3 | 1024 | 10 | 7.19 | 67.9 | 0.976 | 78.7 | -11869 | 2.5e-02 / 7.5e-02 |
| ss/-40/3 | 1024 | 20 | 7.19 | 67.9 | 0.976 | 1.66 | -365 | 6.3e-04 / 5.7e-03 |

Proposed fast-mode INL targets (GBW 20 MHz design target, worst of the three points, 1.5x margin rounded up to 1-2-5): N 64: <= 200 ppm; N 256: <= 20 ppm; N 1024: <= 5 ppm. Proposal only; the SPEC fast-mode target is not set.

## Verdict

REJECT

GATE grid specs: ACCEPT
GATE MC INL/gain/offset: ACCEPT
GATE CMRR sys on >= 100 dB: ACCEPT
GATE CMRR sys off >= 60 dB (D32): REJECT (16)

- CMRR tt/27 tt/27/3.3 fs 0.25 MHz 3sigma eps 7500 uV/V Vin_cm 0.2 V: sys off = 42.5 dB < 60
- CMRR tt/27 tt/27/3.3 fs 0.25 MHz 3sigma eps 7500 uV/V Vin_cm 2 V: sys off = 42.5 dB < 60
- CMRR tt/27 tt/27/3.3 fs 0.25 MHz worst_draw eps 6209 uV/V Vin_cm 0.2 V: sys off = 44.1 dB < 60
- CMRR tt/27 tt/27/3.3 fs 0.25 MHz worst_draw eps 6209 uV/V Vin_cm 2 V: sys off = 44.1 dB < 60
- CMRR tt/27 tt/27/3.3 fs 2 MHz 3sigma eps 7500 uV/V Vin_cm 0.2 V: sys off = 42.5 dB < 60
- CMRR tt/27 tt/27/3.3 fs 2 MHz 3sigma eps 7500 uV/V Vin_cm 2 V: sys off = 42.5 dB < 60
- CMRR tt/27 tt/27/3.3 fs 2 MHz worst_draw eps 6667 uV/V Vin_cm 0.2 V: sys off = 43.5 dB < 60
- CMRR tt/27 tt/27/3.3 fs 2 MHz worst_draw eps 6667 uV/V Vin_cm 2 V: sys off = 43.5 dB < 60
- CMRR worst-INL ss/125/3 fs 0.25 MHz 3sigma eps 7500 uV/V Vin_cm 0.2 V: sys off = 42.5 dB < 60
- CMRR worst-INL ss/125/3 fs 0.25 MHz 3sigma eps 7500 uV/V Vin_cm 2 V: sys off = 42.5 dB < 60
- CMRR worst-INL ss/125/3 fs 0.25 MHz worst_draw eps 4235 uV/V Vin_cm 0.2 V: sys off = 47.5 dB < 60
- CMRR worst-INL ss/125/3 fs 0.25 MHz worst_draw eps 4235 uV/V Vin_cm 2 V: sys off = 47.5 dB < 60
- CMRR worst-offset ff/125/3.6 fs 0.25 MHz 3sigma eps 7500 uV/V Vin_cm 0.2 V: sys off = 42.5 dB < 60
- CMRR worst-offset ff/125/3.6 fs 0.25 MHz 3sigma eps 7500 uV/V Vin_cm 2 V: sys off = 42.5 dB < 60
- CMRR worst-offset ff/125/3.6 fs 0.25 MHz worst_draw eps 6334 uV/V Vin_cm 0.2 V: sys off = 44.0 dB < 60
- CMRR worst-offset ff/125/3.6 fs 0.25 MHz worst_draw eps 6334 uV/V Vin_cm 2 V: sys off = 44.0 dB < 60

## Appendix: all grid evaluations

| point | fs MHz | n15 | n15 limit | n240 | n240 limit | INL | gain | offset | memory |
|---|---|---|---|---|---|---|---|---|---|
| tt/-40/3 | 0.25 | 2 | 2.5 | 6.51 | not gated | 1.23 | 28 | 0.384 | 0.218 |
| tt/-40/3 | 2 | 0.522 | 2.5 | 2.6 | 5 | 0.465 | 21 | 0.435 | 0.219 |
| tt/-40/3.3 | 0.25 | 1.89 | 2.5 | 6.1 | not gated | 0.464 | 17.4 | 0.325 | 0.126 |
| tt/-40/3.3 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.884 | 10.3 | 0.288 | 0.127 |
| tt/-40/3.6 | 0.25 | 1.89 | 2.5 | 6.1 | not gated | 0.464 | 17.4 | 0.325 | 0.126 |
| tt/-40/3.6 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.884 | 10.3 | 0.288 | 0.127 |
| tt/27/3 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28 | 0.266 | 0.124 |
| tt/27/3 | 2 | 0.599 | 2.5 | 2.78 | 5 | 0.467 | 21 | 0.255 | 0.125 |
| tt/27/3.3 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.464 | 17.4 | 0.129 | 0.0316 |
| tt/27/3.3 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.884 | 10.3 | 0.13 | 0.0318 |
| tt/27/3.6 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.464 | 17.4 | 0.129 | 0.0316 |
| tt/27/3.6 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.884 | 10.3 | 0.13 | 0.0318 |
| tt/125/3 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.65 | 44.9 | 0.538 | 0.122 |
| tt/125/3 | 2 | 0.733 | 2.5 | 3.18 | 5 | 1.73 | 37.8 | 0.343 | 0.124 |
| tt/125/3.3 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28 | 0.51 | 0.0309 |
| tt/125/3.3 | 2 | 0.681 | 2.5 | 3.11 | 5 | 0.466 | 21 | 0.171 | 0.0317 |
| tt/125/3.6 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28 | 0.574 | 0.0309 |
| tt/125/3.6 | 2 | 0.681 | 2.5 | 3.11 | 5 | 0.466 | 21 | 0.179 | 0.0317 |
| ss/-40/3 | 0.25 | 2.17 | 2.5 | 7.03 | not gated | 2.65 | 44.9 | 0.581 | 0.304 |
| ss/-40/3 | 2 | 0.562 | 2.5 | 2.85 | 5 | 1.73 | 37.8 | 0.611 | 0.307 |
| ss/-40/3.3 | 0.25 | 2 | 2.5 | 6.51 | not gated | 1.23 | 28 | 0.384 | 0.218 |
| ss/-40/3.3 | 2 | 0.522 | 2.5 | 2.6 | 5 | 0.465 | 21 | 0.435 | 0.219 |
| ss/-40/3.6 | 0.25 | 2 | 2.5 | 6.51 | not gated | 1.23 | 28 | 0.384 | 0.218 |
| ss/-40/3.6 | 2 | 0.522 | 2.5 | 2.6 | 5 | 0.465 | 21 | 0.435 | 0.219 |
| ss/27/3 | 0.25 | 2.45 | 2.5 | 7.91 | not gated | 2.65 | 44.9 | 0.388 | 0.212 |
| ss/27/3 | 2 | 0.632 | 2.5 | 2.93 | 5 | 1.74 | 37.8 | 0.406 | 0.214 |
| ss/27/3.3 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28 | 0.266 | 0.124 |
| ss/27/3.3 | 2 | 0.599 | 2.5 | 2.78 | 5 | 0.467 | 21 | 0.255 | 0.125 |
| ss/27/3.6 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28 | 0.266 | 0.124 |
| ss/27/3.6 | 2 | 0.599 | 2.5 | 2.78 | 5 | 0.467 | 21 | 0.255 | 0.125 |
| ss/125/3 | 0.25 | 2.98 | 3 | 9.86 | not gated | 5.22 | 71.5 | 0.563 | 0.204 |
| ss/125/3 | 2 | 0.779 | 2.5 | 3.37 | 5 | 4.17 | 64.4 | 0.442 | 0.207 |
| ss/125/3.3 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.65 | 44.9 | 0.462 | 0.122 |
| ss/125/3.3 | 2 | 0.733 | 2.5 | 3.18 | 5 | 1.73 | 37.8 | 0.334 | 0.124 |
| ss/125/3.6 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.65 | 44.9 | 0.501 | 0.122 |
| ss/125/3.6 | 2 | 0.733 | 2.5 | 3.18 | 5 | 1.73 | 37.8 | 0.338 | 0.124 |
| ff/-40/3 | 0.25 | 2 | 2.5 | 6.51 | not gated | 1.23 | 28 | 0.384 | 0.218 |
| ff/-40/3 | 2 | 0.522 | 2.5 | 2.6 | 5 | 0.465 | 21 | 0.435 | 0.219 |
| ff/-40/3.3 | 0.25 | 1.89 | 2.5 | 6.1 | not gated | 0.464 | 17.4 | 0.325 | 0.126 |
| ff/-40/3.3 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.884 | 10.3 | 0.288 | 0.127 |
| ff/-40/3.6 | 0.25 | 1.89 | 2.5 | 6.1 | not gated | 0.464 | 17.4 | 0.325 | 0.126 |
| ff/-40/3.6 | 2 | 0.493 | 2.5 | 2.43 | 5 | 0.884 | 10.3 | 0.288 | 0.127 |
| ff/27/3 | 0.25 | 2.29 | 2.5 | 7.54 | not gated | 1.23 | 28 | 0.266 | 0.124 |
| ff/27/3 | 2 | 0.599 | 2.5 | 2.78 | 5 | 0.467 | 21 | 0.255 | 0.125 |
| ff/27/3.3 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.464 | 17.4 | 0.129 | 0.0316 |
| ff/27/3.3 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.884 | 10.3 | 0.13 | 0.0318 |
| ff/27/3.6 | 0.25 | 2.13 | 2.5 | 6.96 | not gated | 0.464 | 17.4 | 0.129 | 0.0316 |
| ff/27/3.6 | 2 | 0.561 | 2.5 | 2.67 | 5 | 0.884 | 10.3 | 0.13 | 0.0318 |
| ff/125/3 | 0.25 | 2.8 | 3 | 8.73 | not gated | 2.65 | 44.9 | 0.816 | 0.122 |
| ff/125/3 | 2 | 0.733 | 2.5 | 3.18 | 5 | 1.73 | 37.8 | 0.378 | 0.124 |
| ff/125/3.3 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28 | 0.846 | 0.0309 |
| ff/125/3.3 | 2 | 0.681 | 2.5 | 3.11 | 5 | 0.466 | 21 | 0.213 | 0.0317 |
| ff/125/3.6 | 0.25 | 2.62 | 3 | 8.55 | not gated | 1.23 | 28 | 0.974 | 0.0309 |
| ff/125/3.6 | 2 | 0.681 | 2.5 | 3.11 | 5 | 0.466 | 21 | 0.229 | 0.0317 |
| sf/-40/3 | 0.25 | 2.09 | 2.5 | 6.54 | not gated | 1.83 | 35.5 | 0.477 | 0.261 |
| sf/-40/3 | 2 | 0.541 | 2.5 | 2.77 | 5 | 0.987 | 28.4 | 0.502 | 0.264 |
| sf/-40/3.3 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.783 | 22.1 | 0.282 | 0.172 |
| sf/-40/3.3 | 2 | 0.517 | 2.5 | 2.44 | 5 | 0.619 | 15 | 0.361 | 0.174 |
| sf/-40/3.6 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.783 | 22.1 | 0.282 | 0.172 |
| sf/-40/3.6 | 2 | 0.517 | 2.5 | 2.44 | 5 | 0.619 | 15 | 0.361 | 0.174 |
| sf/27/3 | 0.25 | 2.34 | 2.5 | 7.66 | not gated | 1.84 | 35.5 | 0.348 | 0.169 |
| sf/27/3 | 2 | 0.623 | 2.5 | 2.93 | 5 | 0.987 | 28.4 | 0.347 | 0.171 |
| sf/27/3.3 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.784 | 22.1 | 0.235 | 0.0778 |
| sf/27/3.3 | 2 | 0.574 | 2.5 | 2.81 | 5 | 0.618 | 15 | 0.209 | 0.079 |
| sf/27/3.6 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.784 | 22.1 | 0.235 | 0.0778 |
| sf/27/3.6 | 2 | 0.574 | 2.5 | 2.81 | 5 | 0.618 | 15 | 0.209 | 0.079 |
| sf/125/3 | 0.25 | 2.9 | 3 | 9.18 | not gated | 3.76 | 56.7 | 0.744 | 0.165 |
| sf/125/3 | 2 | 0.757 | 2.5 | 3.3 | 5 | 2.76 | 49.6 | 0.416 | 0.167 |
| sf/125/3.3 | 0.25 | 2.71 | 3 | 8.58 | not gated | 1.83 | 35.5 | 0.677 | 0.078 |
| sf/125/3.3 | 2 | 0.71 | 2.5 | 3.21 | 5 | 0.986 | 28.4 | 0.231 | 0.0775 |
| sf/125/3.6 | 0.25 | 2.71 | 3 | 8.58 | not gated | 1.83 | 35.5 | 0.766 | 0.078 |
| sf/125/3.6 | 2 | 0.71 | 2.5 | 3.21 | 5 | 0.986 | 28.4 | 0.242 | 0.0775 |
| fs/-40/3 | 0.25 | 2.09 | 2.5 | 6.54 | not gated | 1.83 | 35.5 | 0.477 | 0.261 |
| fs/-40/3 | 2 | 0.541 | 2.5 | 2.77 | 5 | 0.987 | 28.4 | 0.502 | 0.264 |
| fs/-40/3.3 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.783 | 22.1 | 0.282 | 0.172 |
| fs/-40/3.3 | 2 | 0.517 | 2.5 | 2.44 | 5 | 0.619 | 15 | 0.361 | 0.174 |
| fs/-40/3.6 | 0.25 | 1.96 | 2.5 | 6.51 | not gated | 0.783 | 22.1 | 0.282 | 0.172 |
| fs/-40/3.6 | 2 | 0.517 | 2.5 | 2.44 | 5 | 0.619 | 15 | 0.361 | 0.174 |
| fs/27/3 | 0.25 | 2.34 | 2.5 | 7.66 | not gated | 1.84 | 35.5 | 0.348 | 0.169 |
| fs/27/3 | 2 | 0.623 | 2.5 | 2.93 | 5 | 0.987 | 28.4 | 0.347 | 0.171 |
| fs/27/3.3 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.784 | 22.1 | 0.235 | 0.0778 |
| fs/27/3.3 | 2 | 0.574 | 2.5 | 2.81 | 5 | 0.618 | 15 | 0.209 | 0.079 |
| fs/27/3.6 | 0.25 | 2.19 | 2.5 | 7.12 | not gated | 0.784 | 22.1 | 0.235 | 0.0778 |
| fs/27/3.6 | 2 | 0.574 | 2.5 | 2.81 | 5 | 0.618 | 15 | 0.209 | 0.079 |
| fs/125/3 | 0.25 | 2.9 | 3 | 9.18 | not gated | 3.76 | 56.7 | 0.744 | 0.165 |
| fs/125/3 | 2 | 0.757 | 2.5 | 3.3 | 5 | 2.76 | 49.6 | 0.416 | 0.167 |
| fs/125/3.3 | 0.25 | 2.71 | 3 | 8.58 | not gated | 1.83 | 35.5 | 0.677 | 0.078 |
| fs/125/3.3 | 2 | 0.71 | 2.5 | 3.21 | 5 | 0.986 | 28.4 | 0.231 | 0.0775 |
| fs/125/3.6 | 0.25 | 2.71 | 3 | 8.58 | not gated | 1.83 | 35.5 | 0.766 | 0.078 |
| fs/125/3.6 | 2 | 0.71 | 2.5 | 3.21 | 5 | 0.986 | 28.4 | 0.242 | 0.0775 |
| ss_hh/-40/3 | 0.25 | 1.94 | 2.5 | 6.44 | not gated | 1.21 | 27.9 | 0.471 | 0.264 |
| ss_hh/-40/3 | 2 | 0.5 | 2.5 | 2.43 | 5 | 0.41 | 20.2 | 0.525 | 0.266 |
| ss_hh/-40/3.3 | 0.25 | 1.81 | 2.5 | 6.1 | not gated | 0.452 | 17.3 | 0.322 | 0.173 |
| ss_hh/-40/3.3 | 2 | 0.468 | 2.5 | 2.38 | 5 | 1.02 | 9.51 | 0.322 | 0.174 |
| ss_hh/-40/3.6 | 0.25 | 1.81 | 2.5 | 6.1 | not gated | 0.452 | 17.3 | 0.322 | 0.173 |
| ss_hh/-40/3.6 | 2 | 0.468 | 2.5 | 2.38 | 5 | 1.02 | 9.51 | 0.322 | 0.174 |
| ss_hh/27/3 | 0.25 | 2.17 | 2.5 | 7.19 | not gated | 1.21 | 27.9 | 0.394 | 0.171 |
| ss_hh/27/3 | 2 | 0.562 | 2.5 | 2.82 | 5 | 0.41 | 20.2 | 0.344 | 0.173 |
| ss_hh/27/3.3 | 0.25 | 2.04 | 2.5 | 6.75 | not gated | 0.452 | 17.3 | 0.192 | 0.0787 |
| ss_hh/27/3.3 | 2 | 0.528 | 2.5 | 2.64 | 5 | 1.02 | 9.51 | 0.175 | 0.0793 |
| ss_hh/27/3.6 | 0.25 | 2.04 | 2.5 | 6.75 | not gated | 0.452 | 17.3 | 0.192 | 0.0787 |
| ss_hh/27/3.6 | 2 | 0.528 | 2.5 | 2.64 | 5 | 1.02 | 9.51 | 0.175 | 0.0793 |
| ss_hh/125/3 | 0.25 | 2.65 | 3 | 8.62 | not gated | 2.64 | 44.8 | 0.586 | 0.167 |
| ss_hh/125/3 | 2 | 0.69 | 2.5 | 2.99 | 5 | 1.65 | 37 | 0.358 | 0.169 |
| ss_hh/125/3.3 | 0.25 | 2.47 | 3 | 8.09 | not gated | 1.21 | 27.9 | 0.492 | 0.0785 |
| ss_hh/125/3.3 | 2 | 0.663 | 2.5 | 3.08 | 5 | 0.41 | 20.2 | 0.237 | 0.0788 |
| ss_hh/125/3.6 | 0.25 | 2.47 | 3 | 8.09 | not gated | 1.21 | 27.9 | 0.55 | 0.0785 |
| ss_hh/125/3.6 | 2 | 0.663 | 2.5 | 3.08 | 5 | 0.41 | 20.2 | 0.244 | 0.0788 |
| ff_ll/-40/3 | 0.25 | 2.14 | 2.5 | 6.78 | not gated | 1.24 | 28.1 | 0.384 | 0.217 |
| ff_ll/-40/3 | 2 | 0.55 | 2.5 | 2.72 | 5 | 0.535 | 21.8 | 0.446 | 0.219 |
| ff_ll/-40/3.3 | 0.25 | 1.97 | 2.5 | 6.66 | not gated | 0.477 | 17.5 | 0.315 | 0.126 |
| ff_ll/-40/3.3 | 2 | 0.52 | 2.5 | 2.51 | 5 | 0.746 | 11.1 | 0.248 | 0.127 |
| ff_ll/-40/3.6 | 0.25 | 1.97 | 2.5 | 6.66 | not gated | 0.477 | 17.5 | 0.315 | 0.126 |
| ff_ll/-40/3.6 | 2 | 0.52 | 2.5 | 2.51 | 5 | 0.746 | 11.1 | 0.248 | 0.127 |
| ff_ll/27/3 | 0.25 | 2.4 | 2.5 | 7.6 | not gated | 1.24 | 28.1 | 0.266 | 0.125 |
| ff_ll/27/3 | 2 | 0.629 | 2.5 | 2.97 | 5 | 0.535 | 21.8 | 0.27 | 0.126 |
| ff_ll/27/3.3 | 0.25 | 2.24 | 2.5 | 7.6 | not gated | 0.477 | 17.5 | 0.17 | 0.0316 |
| ff_ll/27/3.3 | 2 | 0.594 | 2.5 | 2.8 | 5 | 0.746 | 11.1 | 0.111 | 0.0316 |
| ff_ll/27/3.6 | 0.25 | 2.24 | 2.5 | 7.6 | not gated | 0.477 | 17.5 | 0.17 | 0.0316 |
| ff_ll/27/3.6 | 2 | 0.594 | 2.5 | 2.8 | 5 | 0.746 | 11.1 | 0.111 | 0.0316 |
| ff_ll/125/3 | 0.25 | 2.95 | 3 | 8.91 | not gated | 2.67 | 45 | 0.574 | 0.122 |
| ff_ll/125/3 | 2 | 0.775 | 2.5 | 3.6 | 5 | 1.82 | 38.6 | 0.307 | 0.123 |
| ff_ll/125/3.3 | 0.25 | 2.78 | 3 | 8.82 | not gated | 1.24 | 28.1 | 0.563 | 0.031 |
| ff_ll/125/3.3 | 2 | 0.724 | 2.5 | 3.51 | 5 | 0.534 | 21.8 | 0.173 | 0.0312 |
| ff_ll/125/3.6 | 0.25 | 2.78 | 3 | 8.82 | not gated | 1.24 | 28.1 | 0.634 | 0.031 |
| ff_ll/125/3.6 | 2 | 0.724 | 2.5 | 3.51 | 5 | 0.534 | 21.8 | 0.182 | 0.0312 |


## Findings (WO-06a, read first)

Commands: `python3 -m model.studies.s4_corners --out /home/mempool/regr/tt/WO-06a/s4` (exit 1) and `... --out /home/mempool/regr/tt/WO-06a/nv --nonvac` (REJECT, exit 1; all 7 broken copies rejected, including the CM-term-flips-with-input copy at sys-on 42.5 dB and the 3 % mismatch copy at sys-off 30.5 dB).

1. Gates: grid specs ACCEPT (n15 worst 2.98 uV vs the applied 3.0 uV limit at ss/125/3, 0.25 MHz; x1.01; at fs 2 MHz worst 0.78 uV vs 2.5; n240 worst 3.60 uV vs 5, gated at fs 2 MHz only); MC INL/gain/offset ACCEPT; CMRR sys-on ACCEPT (143-166 dB); **CMRR sys-off REJECT (D32, 60 dB)**: 42.5 dB at the 3 sigma mismatch 0.75 % (44 dB at the largest MC draws), 16 failing rows. Not relaxed.
2. Sys-off CMRR = 1/eps in this model (theory check, tested to 2 %). The mismatch needed for 60 dB is eps = 0.1 % (1000 uV/V); the spec mismatch is 7.5x larger.
3. Sys-on residual is 0.004-0.06 uV (>= 143 dB): the hypothesis (term fixed in the modulator frame, cancels in the pair) is only modelled here; WO-08 checks it in SPICE. VREF_CM = 1.0 V is an assumption; Vin_cm = 1.0 V has dVcm = 0 and shows n/a.
