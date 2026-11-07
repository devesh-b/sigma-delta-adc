# S4: corner-aware tier-0 model (WO-06)

Command: `python3 -m model.studies.s4_corners --out /home/mempool/regr/tt/WO-06/s4`

Wall time 364 s on 4 processes (grid 339 s, MC 24 s). No transistor data exists: every mapping is an **assumption** (nominal at tt/27/3.3, the SPEC 3.0 limit at that mechanism's worst corner, linear in a 0..1 stress between). A result here says the budget closes if each block just meets SPEC 3.0; it is not a statement about a circuit.

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
| noise @15 SPS (u = 0) | 2.5 uV | SPEC 3.0 budget |
| noise @240 SPS | 5 uV | ASSUMED (SPEC has no 240 SPS limit; joint run at spec 3.9 uV) |
| INL, N 4096 | 20 ppm | SPEC 3.0 budget (4 ppm of it is unmodelled reserve) |
| sys-pair offset | 5 uV | SPEC 3.0 budget = model residual + reset 2 r x1max/(c1(N-1)) + leakage x rho 0.1 % (2 uV of it unmodelled reserve) |
| gain error | 5000 ppm | SPEC 3.0 |
| inter-conversion memory | 0.5 uV | review S3-5 (+-FS then 0) |

## Corner grid: 126 evaluations = 63 analog PVT points x fs {0.25, 2} MHz

Worst point per spec (over all points and both fs):

| spec | worst value | limit | margin (limit/value) | worst point | fs [MHz] |
|---|---|---|---|---|---|
| n15 | 2.98 uV | 2.5 | x0.84 | ss/125/3 | 0.25 |
| n240 | 3.603 uV | 5 | x1.39 | ff_ll/125/3 | 2 |
| inl | 5.222 ppm | 20 | x3.83 | ss/125/3 | 0.25 |
| off | 0.9739 uV | 5 | x5.13 | ff/125/3.6 | 0.25 |
| gain | 71.49 ppm | 5000 | x69.94 | ss/125/3 | 0.25 |
| mem | 0.3073 uV | 0.5 | x1.63 | ss/-40/3 | 2 |


Worst per spec at fs 0.25 MHz:

| spec | worst | limit | point |
|---|---|---|---|
| n15 | 2.98 uV | 2.5 | ss/125/3 |
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

CMRR term (Cs+/Cs- mismatch, D12 switching): CM-to-differential gain |dCs/Cs| = 2175 uV/V mean, 3 sigma point 6696 uV/V (7500 uV/V = 0.75 %), max of draws 6209 uV/V. This is a constant offset for a given input common-mode error dVcm that sys chop does NOT cancel: the 5 uV offset budget is used up by dVcm = 0.67 mV at the 3 sigma mismatch. SPEC 3.0 has no CM-dependent offset limit; this is a spec gap, not gated.

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

- tt/125/3 fs 0.25 MHz: n15 = 2.798 uV > 2.5
- tt/125/3.3 fs 0.25 MHz: n15 = 2.616 uV > 2.5
- tt/125/3.6 fs 0.25 MHz: n15 = 2.616 uV > 2.5
- ss/125/3 fs 0.25 MHz: n15 = 2.98 uV > 2.5
- ss/125/3.3 fs 0.25 MHz: n15 = 2.798 uV > 2.5
- ss/125/3.6 fs 0.25 MHz: n15 = 2.798 uV > 2.5
- ff/125/3 fs 0.25 MHz: n15 = 2.798 uV > 2.5
- ff/125/3.3 fs 0.25 MHz: n15 = 2.616 uV > 2.5
- ff/125/3.6 fs 0.25 MHz: n15 = 2.616 uV > 2.5
- sf/125/3 fs 0.25 MHz: n15 = 2.903 uV > 2.5
- sf/125/3.3 fs 0.25 MHz: n15 = 2.706 uV > 2.5
- sf/125/3.6 fs 0.25 MHz: n15 = 2.706 uV > 2.5
- fs/125/3 fs 0.25 MHz: n15 = 2.903 uV > 2.5
- fs/125/3.3 fs 0.25 MHz: n15 = 2.706 uV > 2.5
- fs/125/3.6 fs 0.25 MHz: n15 = 2.706 uV > 2.5
- ss_hh/125/3 fs 0.25 MHz: n15 = 2.645 uV > 2.5
- ff_ll/125/3 fs 0.25 MHz: n15 = 2.946 uV > 2.5
- ff_ll/125/3.3 fs 0.25 MHz: n15 = 2.776 uV > 2.5
- ff_ll/125/3.6 fs 0.25 MHz: n15 = 2.776 uV > 2.5

## Appendix: all grid evaluations

| point | fs MHz | n15 | n240 | INL | gain | offset | memory |
|---|---|---|---|---|---|---|---|
| tt/-40/3 | 0.25 | 2 | 6.51 | 1.23 | 28 | 0.384 | 0.218 |
| tt/-40/3 | 2 | 0.522 | 2.6 | 0.465 | 21 | 0.435 | 0.219 |
| tt/-40/3.3 | 0.25 | 1.89 | 6.1 | 0.464 | 17.4 | 0.325 | 0.126 |
| tt/-40/3.3 | 2 | 0.493 | 2.43 | 0.884 | 10.3 | 0.288 | 0.127 |
| tt/-40/3.6 | 0.25 | 1.89 | 6.1 | 0.464 | 17.4 | 0.325 | 0.126 |
| tt/-40/3.6 | 2 | 0.493 | 2.43 | 0.884 | 10.3 | 0.288 | 0.127 |
| tt/27/3 | 0.25 | 2.29 | 7.54 | 1.23 | 28 | 0.266 | 0.124 |
| tt/27/3 | 2 | 0.599 | 2.78 | 0.467 | 21 | 0.255 | 0.125 |
| tt/27/3.3 | 0.25 | 2.13 | 6.96 | 0.464 | 17.4 | 0.129 | 0.0316 |
| tt/27/3.3 | 2 | 0.561 | 2.67 | 0.884 | 10.3 | 0.13 | 0.0318 |
| tt/27/3.6 | 0.25 | 2.13 | 6.96 | 0.464 | 17.4 | 0.129 | 0.0316 |
| tt/27/3.6 | 2 | 0.561 | 2.67 | 0.884 | 10.3 | 0.13 | 0.0318 |
| tt/125/3 | 0.25 | 2.8 | 8.73 | 2.65 | 44.9 | 0.538 | 0.122 |
| tt/125/3 | 2 | 0.733 | 3.18 | 1.73 | 37.8 | 0.343 | 0.124 |
| tt/125/3.3 | 0.25 | 2.62 | 8.55 | 1.23 | 28 | 0.51 | 0.0309 |
| tt/125/3.3 | 2 | 0.681 | 3.11 | 0.466 | 21 | 0.171 | 0.0317 |
| tt/125/3.6 | 0.25 | 2.62 | 8.55 | 1.23 | 28 | 0.574 | 0.0309 |
| tt/125/3.6 | 2 | 0.681 | 3.11 | 0.466 | 21 | 0.179 | 0.0317 |
| ss/-40/3 | 0.25 | 2.17 | 7.03 | 2.65 | 44.9 | 0.581 | 0.304 |
| ss/-40/3 | 2 | 0.562 | 2.85 | 1.73 | 37.8 | 0.611 | 0.307 |
| ss/-40/3.3 | 0.25 | 2 | 6.51 | 1.23 | 28 | 0.384 | 0.218 |
| ss/-40/3.3 | 2 | 0.522 | 2.6 | 0.465 | 21 | 0.435 | 0.219 |
| ss/-40/3.6 | 0.25 | 2 | 6.51 | 1.23 | 28 | 0.384 | 0.218 |
| ss/-40/3.6 | 2 | 0.522 | 2.6 | 0.465 | 21 | 0.435 | 0.219 |
| ss/27/3 | 0.25 | 2.45 | 7.91 | 2.65 | 44.9 | 0.388 | 0.212 |
| ss/27/3 | 2 | 0.632 | 2.93 | 1.74 | 37.8 | 0.406 | 0.214 |
| ss/27/3.3 | 0.25 | 2.29 | 7.54 | 1.23 | 28 | 0.266 | 0.124 |
| ss/27/3.3 | 2 | 0.599 | 2.78 | 0.467 | 21 | 0.255 | 0.125 |
| ss/27/3.6 | 0.25 | 2.29 | 7.54 | 1.23 | 28 | 0.266 | 0.124 |
| ss/27/3.6 | 2 | 0.599 | 2.78 | 0.467 | 21 | 0.255 | 0.125 |
| ss/125/3 | 0.25 | 2.98 | 9.86 | 5.22 | 71.5 | 0.563 | 0.204 |
| ss/125/3 | 2 | 0.779 | 3.37 | 4.17 | 64.4 | 0.442 | 0.207 |
| ss/125/3.3 | 0.25 | 2.8 | 8.73 | 2.65 | 44.9 | 0.462 | 0.122 |
| ss/125/3.3 | 2 | 0.733 | 3.18 | 1.73 | 37.8 | 0.334 | 0.124 |
| ss/125/3.6 | 0.25 | 2.8 | 8.73 | 2.65 | 44.9 | 0.501 | 0.122 |
| ss/125/3.6 | 2 | 0.733 | 3.18 | 1.73 | 37.8 | 0.338 | 0.124 |
| ff/-40/3 | 0.25 | 2 | 6.51 | 1.23 | 28 | 0.384 | 0.218 |
| ff/-40/3 | 2 | 0.522 | 2.6 | 0.465 | 21 | 0.435 | 0.219 |
| ff/-40/3.3 | 0.25 | 1.89 | 6.1 | 0.464 | 17.4 | 0.325 | 0.126 |
| ff/-40/3.3 | 2 | 0.493 | 2.43 | 0.884 | 10.3 | 0.288 | 0.127 |
| ff/-40/3.6 | 0.25 | 1.89 | 6.1 | 0.464 | 17.4 | 0.325 | 0.126 |
| ff/-40/3.6 | 2 | 0.493 | 2.43 | 0.884 | 10.3 | 0.288 | 0.127 |
| ff/27/3 | 0.25 | 2.29 | 7.54 | 1.23 | 28 | 0.266 | 0.124 |
| ff/27/3 | 2 | 0.599 | 2.78 | 0.467 | 21 | 0.255 | 0.125 |
| ff/27/3.3 | 0.25 | 2.13 | 6.96 | 0.464 | 17.4 | 0.129 | 0.0316 |
| ff/27/3.3 | 2 | 0.561 | 2.67 | 0.884 | 10.3 | 0.13 | 0.0318 |
| ff/27/3.6 | 0.25 | 2.13 | 6.96 | 0.464 | 17.4 | 0.129 | 0.0316 |
| ff/27/3.6 | 2 | 0.561 | 2.67 | 0.884 | 10.3 | 0.13 | 0.0318 |
| ff/125/3 | 0.25 | 2.8 | 8.73 | 2.65 | 44.9 | 0.816 | 0.122 |
| ff/125/3 | 2 | 0.733 | 3.18 | 1.73 | 37.8 | 0.378 | 0.124 |
| ff/125/3.3 | 0.25 | 2.62 | 8.55 | 1.23 | 28 | 0.846 | 0.0309 |
| ff/125/3.3 | 2 | 0.681 | 3.11 | 0.466 | 21 | 0.213 | 0.0317 |
| ff/125/3.6 | 0.25 | 2.62 | 8.55 | 1.23 | 28 | 0.974 | 0.0309 |
| ff/125/3.6 | 2 | 0.681 | 3.11 | 0.466 | 21 | 0.229 | 0.0317 |
| sf/-40/3 | 0.25 | 2.09 | 6.54 | 1.83 | 35.5 | 0.477 | 0.261 |
| sf/-40/3 | 2 | 0.541 | 2.77 | 0.987 | 28.4 | 0.502 | 0.264 |
| sf/-40/3.3 | 0.25 | 1.96 | 6.51 | 0.783 | 22.1 | 0.282 | 0.172 |
| sf/-40/3.3 | 2 | 0.517 | 2.44 | 0.619 | 15 | 0.361 | 0.174 |
| sf/-40/3.6 | 0.25 | 1.96 | 6.51 | 0.783 | 22.1 | 0.282 | 0.172 |
| sf/-40/3.6 | 2 | 0.517 | 2.44 | 0.619 | 15 | 0.361 | 0.174 |
| sf/27/3 | 0.25 | 2.34 | 7.66 | 1.84 | 35.5 | 0.348 | 0.169 |
| sf/27/3 | 2 | 0.623 | 2.93 | 0.987 | 28.4 | 0.347 | 0.171 |
| sf/27/3.3 | 0.25 | 2.19 | 7.12 | 0.784 | 22.1 | 0.235 | 0.0778 |
| sf/27/3.3 | 2 | 0.574 | 2.81 | 0.618 | 15 | 0.209 | 0.079 |
| sf/27/3.6 | 0.25 | 2.19 | 7.12 | 0.784 | 22.1 | 0.235 | 0.0778 |
| sf/27/3.6 | 2 | 0.574 | 2.81 | 0.618 | 15 | 0.209 | 0.079 |
| sf/125/3 | 0.25 | 2.9 | 9.18 | 3.76 | 56.7 | 0.744 | 0.165 |
| sf/125/3 | 2 | 0.757 | 3.3 | 2.76 | 49.6 | 0.416 | 0.167 |
| sf/125/3.3 | 0.25 | 2.71 | 8.58 | 1.83 | 35.5 | 0.677 | 0.078 |
| sf/125/3.3 | 2 | 0.71 | 3.21 | 0.986 | 28.4 | 0.231 | 0.0775 |
| sf/125/3.6 | 0.25 | 2.71 | 8.58 | 1.83 | 35.5 | 0.766 | 0.078 |
| sf/125/3.6 | 2 | 0.71 | 3.21 | 0.986 | 28.4 | 0.242 | 0.0775 |
| fs/-40/3 | 0.25 | 2.09 | 6.54 | 1.83 | 35.5 | 0.477 | 0.261 |
| fs/-40/3 | 2 | 0.541 | 2.77 | 0.987 | 28.4 | 0.502 | 0.264 |
| fs/-40/3.3 | 0.25 | 1.96 | 6.51 | 0.783 | 22.1 | 0.282 | 0.172 |
| fs/-40/3.3 | 2 | 0.517 | 2.44 | 0.619 | 15 | 0.361 | 0.174 |
| fs/-40/3.6 | 0.25 | 1.96 | 6.51 | 0.783 | 22.1 | 0.282 | 0.172 |
| fs/-40/3.6 | 2 | 0.517 | 2.44 | 0.619 | 15 | 0.361 | 0.174 |
| fs/27/3 | 0.25 | 2.34 | 7.66 | 1.84 | 35.5 | 0.348 | 0.169 |
| fs/27/3 | 2 | 0.623 | 2.93 | 0.987 | 28.4 | 0.347 | 0.171 |
| fs/27/3.3 | 0.25 | 2.19 | 7.12 | 0.784 | 22.1 | 0.235 | 0.0778 |
| fs/27/3.3 | 2 | 0.574 | 2.81 | 0.618 | 15 | 0.209 | 0.079 |
| fs/27/3.6 | 0.25 | 2.19 | 7.12 | 0.784 | 22.1 | 0.235 | 0.0778 |
| fs/27/3.6 | 2 | 0.574 | 2.81 | 0.618 | 15 | 0.209 | 0.079 |
| fs/125/3 | 0.25 | 2.9 | 9.18 | 3.76 | 56.7 | 0.744 | 0.165 |
| fs/125/3 | 2 | 0.757 | 3.3 | 2.76 | 49.6 | 0.416 | 0.167 |
| fs/125/3.3 | 0.25 | 2.71 | 8.58 | 1.83 | 35.5 | 0.677 | 0.078 |
| fs/125/3.3 | 2 | 0.71 | 3.21 | 0.986 | 28.4 | 0.231 | 0.0775 |
| fs/125/3.6 | 0.25 | 2.71 | 8.58 | 1.83 | 35.5 | 0.766 | 0.078 |
| fs/125/3.6 | 2 | 0.71 | 3.21 | 0.986 | 28.4 | 0.242 | 0.0775 |
| ss_hh/-40/3 | 0.25 | 1.94 | 6.44 | 1.21 | 27.9 | 0.471 | 0.264 |
| ss_hh/-40/3 | 2 | 0.5 | 2.43 | 0.41 | 20.2 | 0.525 | 0.266 |
| ss_hh/-40/3.3 | 0.25 | 1.81 | 6.1 | 0.452 | 17.3 | 0.322 | 0.173 |
| ss_hh/-40/3.3 | 2 | 0.468 | 2.38 | 1.02 | 9.51 | 0.322 | 0.174 |
| ss_hh/-40/3.6 | 0.25 | 1.81 | 6.1 | 0.452 | 17.3 | 0.322 | 0.173 |
| ss_hh/-40/3.6 | 2 | 0.468 | 2.38 | 1.02 | 9.51 | 0.322 | 0.174 |
| ss_hh/27/3 | 0.25 | 2.17 | 7.19 | 1.21 | 27.9 | 0.394 | 0.171 |
| ss_hh/27/3 | 2 | 0.562 | 2.82 | 0.41 | 20.2 | 0.344 | 0.173 |
| ss_hh/27/3.3 | 0.25 | 2.04 | 6.75 | 0.452 | 17.3 | 0.192 | 0.0787 |
| ss_hh/27/3.3 | 2 | 0.528 | 2.64 | 1.02 | 9.51 | 0.175 | 0.0793 |
| ss_hh/27/3.6 | 0.25 | 2.04 | 6.75 | 0.452 | 17.3 | 0.192 | 0.0787 |
| ss_hh/27/3.6 | 2 | 0.528 | 2.64 | 1.02 | 9.51 | 0.175 | 0.0793 |
| ss_hh/125/3 | 0.25 | 2.65 | 8.62 | 2.64 | 44.8 | 0.586 | 0.167 |
| ss_hh/125/3 | 2 | 0.69 | 2.99 | 1.65 | 37 | 0.358 | 0.169 |
| ss_hh/125/3.3 | 0.25 | 2.47 | 8.09 | 1.21 | 27.9 | 0.492 | 0.0785 |
| ss_hh/125/3.3 | 2 | 0.663 | 3.08 | 0.41 | 20.2 | 0.237 | 0.0788 |
| ss_hh/125/3.6 | 0.25 | 2.47 | 8.09 | 1.21 | 27.9 | 0.55 | 0.0785 |
| ss_hh/125/3.6 | 2 | 0.663 | 3.08 | 0.41 | 20.2 | 0.244 | 0.0788 |
| ff_ll/-40/3 | 0.25 | 2.14 | 6.78 | 1.24 | 28.1 | 0.384 | 0.217 |
| ff_ll/-40/3 | 2 | 0.55 | 2.72 | 0.535 | 21.8 | 0.446 | 0.219 |
| ff_ll/-40/3.3 | 0.25 | 1.97 | 6.66 | 0.477 | 17.5 | 0.315 | 0.126 |
| ff_ll/-40/3.3 | 2 | 0.52 | 2.51 | 0.746 | 11.1 | 0.248 | 0.127 |
| ff_ll/-40/3.6 | 0.25 | 1.97 | 6.66 | 0.477 | 17.5 | 0.315 | 0.126 |
| ff_ll/-40/3.6 | 2 | 0.52 | 2.51 | 0.746 | 11.1 | 0.248 | 0.127 |
| ff_ll/27/3 | 0.25 | 2.4 | 7.6 | 1.24 | 28.1 | 0.266 | 0.125 |
| ff_ll/27/3 | 2 | 0.629 | 2.97 | 0.535 | 21.8 | 0.27 | 0.126 |
| ff_ll/27/3.3 | 0.25 | 2.24 | 7.6 | 0.477 | 17.5 | 0.17 | 0.0316 |
| ff_ll/27/3.3 | 2 | 0.594 | 2.8 | 0.746 | 11.1 | 0.111 | 0.0316 |
| ff_ll/27/3.6 | 0.25 | 2.24 | 7.6 | 0.477 | 17.5 | 0.17 | 0.0316 |
| ff_ll/27/3.6 | 2 | 0.594 | 2.8 | 0.746 | 11.1 | 0.111 | 0.0316 |
| ff_ll/125/3 | 0.25 | 2.95 | 8.91 | 2.67 | 45 | 0.574 | 0.122 |
| ff_ll/125/3 | 2 | 0.775 | 3.6 | 1.82 | 38.6 | 0.307 | 0.123 |
| ff_ll/125/3.3 | 0.25 | 2.78 | 8.82 | 1.24 | 28.1 | 0.563 | 0.031 |
| ff_ll/125/3.3 | 2 | 0.724 | 3.51 | 0.534 | 21.8 | 0.173 | 0.0312 |
| ff_ll/125/3.6 | 0.25 | 2.78 | 8.82 | 1.24 | 28.1 | 0.634 | 0.031 |
| ff_ll/125/3.6 | 2 | 0.724 | 3.51 | 0.534 | 21.8 | 0.182 | 0.0312 |


## Findings (read first)

1. **FAIL, noise @15 SPS at fs 0.25 MHz, at 125 C** (19 of the 21 points at 125 C; none below 125 C; worst 2.98 uV at ss/125/3.0, 2.62 uV at ff/125/3.6 and tt/125/3.3 and 3.6; limit 2.5 uV). Passes at all points at 2 MHz (worst 0.78 uV) and at 0.25 MHz below 125 C. Cause: at a fixed output rate the sample count falls with fs (4 conversions per output at 0.25 MHz vs 33 at 2 MHz) and kT and en rise at 125 C. Not relaxed. Options for the coordinator: (a) state the 2.5 uV noise limit for fs >= 2 MHz and a looser limit (>= 3.0 uV with margin, e.g. 3.5 uV) at 0.25 MHz; (b) raise the lowest precision fs; (c) reduce 0.25 MHz noise with larger Cs (area). The scaling with fs lies between 1/sqrt(fs) and 1/fs (0.78 -> 2.98 uV is x3.8 for fs /8), so the fs at which 2.5 uV is met is not extrapolated here.
2. noise @240 SPS: SPEC has no limit; 5 uV is an ASSUMPTION (worst 3.60 uV at ff_ll/125/3.0, 2 MHz). At fs 0.25 MHz 240 SPS cannot be reached with a sys-chop pair of N 1024 (needs fs >= 0.49 MHz): not gated there, values reported (6-10 uV).
3. Everything else passes at all 126 evaluations: INL worst 5.2 ppm (limit 20; 3.8x), offset worst 0.97 uV (limit 5), gain worst 71 ppm (limit 5000), memory worst 0.307 uV (limit 0.5, 1.6x, at the SPEC limit r = 1e-4; r = 1e-2 gives 30.6 uV).
4. MC: all four sets pass (mu + 3 sigma and every sample). Vos1/Vos2/comparator offset/Cs mismatch move INL and gain by <0.03 ppm and the sys-pair offset by <0.05 uV: INL and offset are set by the A(v) table, R_ext, reset and leakage terms, not by these mismatches. The raw (sys chop off) offset is 48 uV mean, up to 89 uV: characterization-only modes carry it.
5. SPEC gap: the Cs+/Cs- mismatch makes a CM-to-differential offset of up to 7.5 mV/V (0.75 % 3 sigma) that sys chop does not cancel; 5 uV is used by 0.67 mV of input common-mode error. SPEC 3.0 has no CM-dependent offset limit and the model has no input-CM axis. Not gated.
6. Fast mode (informational): the model needs OTA GBW 20 MHz at 4 MHz; with GBW 10 MHz the hand slew-then-settle estimate gives about 1.2 % gain error and 75-780 ppm INL. Proposed INL targets with GBW 20 MHz: N 64 <= 200, N 256 <= 20, N 1024 <= 5 ppm (the thermal noise at N 64 is below one LSB; quantization sets resolution).
7. Method notes: the memory and offset measures use the residue-corrected reconstruction (quantization error removed exactly), so they are deterministic; the memory measurement floor is 0.002 uV (comparator-noise draw differences). The mapping is an assumption table; the transistor-level corner values replace it in Stage C.

## Non-vacuity (separate command, `--nonvac`): broken copies must REJECT at the named point

Command: `python3 -m model.studies.s4_corners --out DIR --nonvac`

Unbroken copies at the same points (all must pass):

| point | n15 | n240 | inl | off | gain | mem |
|---|---|---|---|---|---|---|
| ss/125/3 | 0.779 | 3.37 | 4.17 | 0.442 | 64.4 | 0.207 |
| ss/-40/3 | 0.562 | 2.85 | 1.73 | 0.611 | 37.8 | 0.307 |
| tt/27/3.3 | 0.561 | 2.67 | 0.884 | 0.13 | 10.3 | 0.0318 |

Broken copies:

| broken copy | spec | value | limit | result |
|---|---|---|---|---|
| A(1.4 V) = 60 dB at ss/125/3.0 | inl | 43.76 ppm | 20 | REJECT |
| reset r = 1e-2 at ss/-40/3.0 | mem | 30.61 uV | 0.5 | REJECT |
| sys chop off (model offset not cancelled) at tt/27/3.3 | off | 102.5 uV | 5 | REJECT |
| Cs / 100 (noise) at tt/27/3.3 | n15 | 5.657 uV | 2.5 | REJECT |
| tau_in 2 us (gain) at ss/-40/3.0 | gain | 2.06e+04 ppm | 5000 | REJECT |

REJECT

- ss/125/3 fs 2 MHz [A(1.4 V) = 60 dB at ss/125/3.0]: inl = 43.76 ppm > 20
- ss/-40/3 fs 2 MHz [reset r = 1e-2 at ss/-40/3.0]: mem = 30.61 uV > 0.5
- tt/27/3.3 fs 2 MHz [sys chop off (model offset not cancelled) at tt/27/3.3]: off = 102.5 uV > 5
- tt/27/3.3 fs 2 MHz [Cs / 100 (noise) at tt/27/3.3]: n15 = 5.657 uV > 2.5
- ss/-40/3 fs 2 MHz [tau_in 2 us (gain) at ss/-40/3.0]: gain = 2.06e+04 ppm > 5000
