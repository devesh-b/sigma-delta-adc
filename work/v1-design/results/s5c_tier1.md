# S5c tier-1 results (WO-09): separated knees, D12 residual, drift, pin path

Source: `/home/mempool/regr/tt/WO-09/{knees3,cm2,drift,rsrc2,xcheck,nonvac3}.log` and the output directories next to them. Written by WO-11 from the logs; nothing was rerun. All six runs ended `EXIT=0` except nonvac3 (`EXIT=1`, which is the required result: every broken deck rejected). Spec flags are listed below; the exit code reflects run health only.

## Commands (from `/home/mempool/regr/tt/run_wo0910.sh`, queue `qa`)

Environment: `. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A; cd /home/mempool/tt-sd`, then for each `m` in `knees3 cm2 drift rsrc2 xcheck nonvac3`:

```
nice -n 10 timeout 7200 python3 design/tier1/tier1_tb.py --$m --out /home/mempool/regr/tt/WO-09/$m > /home/mempool/regr/tt/WO-09/$m.log 2>&1
```

## 1. Separated knees (`--knees3`)

INL (ppm, deck) against an imposed per-OTA slew rate, OTA1 and OTA2 swept separately. Knee = lowest SR with INL below the threshold at it and at every higher grid point. SPEC SR is 12 V/us (OTA1).

| case | INL at SR 8 / 9 / 10 / 11 / 12 / 13.5 / 15 V/us (ppm) | knee, interpolated | margin of 12 V/us over the knee |
|---|---|---|---|
| 2 MHz OTA1 N256 | 143.1 / 10.4 / 1.33 / 0.56 / 0.29 / 0.23 / 0.28 | 8.9 (13.3 ppm), 9.1 (8 ppm) | 35 % |
| 2 MHz OTA2 N256 | 8.34 / 5.04 / 3.34 / 2.33 / 1.69 / 1.16 / 0.85 | 8.1 (8 ppm) | 212 % (vs 25 V/us) |
| 2 MHz OTA1 N1024 | 117.6 / 8.79 / 1.18 / 0.53 / 0.31 / 0.12 / 0.04 | 8.8 (13.3 ppm), 9.0 (8 ppm) | 36 % |
| 2 MHz OTA2 N1024 | 2.88 / 1.80 / 1.27 / 0.98 / 0.78 / 0.60 / 0.51 | below grid | 212 % (vs 25 V/us) |
| 4 MHz boost OTA1 N256 | - / 198.8 / 25.3 / 4.17 / 0.72 / 0.68 / 1.02 | 10.1 (20 ppm), 10.3 (13.3 ppm) | 19 % |
| 4 MHz boost OTA2 N256 | - / 20.0 / 13.9 / 9.41 / 6.99 / 4.21 / 1.46 | 9.0 (20 ppm), 10.1 (13.3 ppm) | 178 % (vs 25 V/us) |
| 4 MHz boost OTA1 N1024 | - / 162.9 / 22.6 / 4.44 / 1.42 / 0.40 / 0.49 | 10.9 (5 ppm), 11.2 (3.3 ppm) | 10 % |
| 4 MHz boost OTA2 N1024 | - / 8.27 / 6.43 / 4.99 / 4.23 / 2.18 / 1.72 | 11.0 (5 ppm), 12.5 (3.3 ppm) | 127 % (vs 25 V/us) |
| 4 MHz boost, OTA1-only boost, N1024 | - / 243.5 / 52.4 / 11.8 / 12.9 / 13.2 / 12.9 | none above the SPEC 12 V/us | n/a |

Reading:
- **Margin of 12 V/us over the OTA1 knee.** At 2 MHz the margin is 35 % (N256) and 36 % (N1024); at 4 MHz boost it is 19 % (N256) and 10 % (N1024). The 2 MHz figures are above the 25 % flag level; the 4 MHz ones are below it. FLAG: 4 MHz boost OTA1 margin 19 % and 10 % < 25 %.
- **OTA1-only boost.** With only OTA1 boosted at 4 MHz (OTA2 left unboosted) the INL floors at about 12-13 ppm and no SR on the grid gets below 5 ppm: FLAG, knee not found above the SPEC 12 V/us. OTA2 needs the boost too at 4 MHz.
- OTA2 is not the limiting stage in any case (margin at least 127 % of the 25 V/us OTA2 figure).
- Spec FLAG count 3 (all three above). `run-health ACCEPT`.

## 2. D12 residual, slope metric (`--cm2`)

Metric: slope of the input-referred error against dVcm (the error between Vin_cm points), not the single-point error used in S5b. Closed form for the D12 residual: ((Cp/Cs) eps_Cs - dCp/Cs) / (1 + Cp/Cs) with Cs 0.5 pF.

**Sign confirmed as "-".** Deck against the "-" closed form is within 0.0 % in all 10 cases with a nonzero closed form (D36 quotes "12 cases"; the log lists 10 such rows plus the zero-residual references). The "+" form is off by 125-200 % in the 8 sign-discriminating cases (those where it differs from the "-" form).

| case (Cp,top fF / dCp,top fF / Cs mismatch %) | deck slope | closed "-" | "+" form | sys-off CMRR | sys-on CMRR |
|---|---|---|---|---|---|
| 10 / 0 / 0.75 | +1.470e-4 | +1.471e-4 | +1.471e-4 | 76.7 dB | 153.4 dB |
| 10 / 0.25 / 0 | -4.901e-4 | -4.902e-4 | +4.902e-4 | 66.2 dB | 172.6 dB |
| 10 / 0.25 / 0.75 | -3.430e-4 | -3.431e-4 | +6.373e-4 | 69.3 dB | 157.4 dB |
| 10 / 1 / 0 | -1.961e-3 | -1.961e-3 | +1.961e-3 | 54.2 dB (FLAG) | 151.2 dB |
| 10 / 1 / 0.75 | -1.814e-3 | -1.814e-3 | +2.108e-3 | 54.8 dB (FLAG) | 146.6 dB |
| 20 / 0 / 0.75 | +2.885e-4 | +2.885e-4 | +2.885e-4 | 70.8 dB | 147.1 dB |
| 20 / 0.25 / 0 | -4.808e-4 | -4.808e-4 | +4.808e-4 | 66.4 dB | 164.5 dB |
| 20 / 0.25 / 0.75 | -1.922e-4 | -1.923e-4 | +7.692e-4 | 74.3 dB | 137.1 dB |
| 20 / 1 / 0 | -1.923e-3 | -1.923e-3 | +1.923e-3 | 54.3 dB (FLAG) | 164.0 dB |
| 20 / 1 / 0.75 | -1.635e-3 | -1.635e-3 | +2.212e-3 | 55.7 dB (FLAG) | 160.6 dB |
| zero-residual references (Cp 0 or dCp 0 and mismatch 0) | at the 1e-9 floor | 0 | 0 | 168.8-180 dB | 169-180 dB |
| `nod12_ref` (no D12 swap) | +4.828e-4 | 0 | 0 | 66.3 dB | 148.8 dB |

- At the C4 allocation (dCp,top <= 0.25 fF) the deck sys-off CMRR is at least 66.2 dB for each single point (66.2-66.4 dB at 0.25 fF with zero mismatch, 69.3-74.3 dB with mismatch); the S4 gate is sys-off >= 60 dB and sys-on >= 100 dB. Sys-on is 137-173 dB at every row.
- FLAG: sys-off CMRR is 54.2-55.7 dB < 60 dB at dCp,top = 1 fF (four rows). This is expected: 1 fF is 4x the allocation. These rows are the SPICE support for the dCp,top <= 0.25 fF requirement in C4.
- The combined 3-sigma value (D36) is in `s4_corners.md`, not here.
- **Superseded (m1):** the S5b CMRR numbers (132-152 dB, single-point metric, Cp,top = 0 in the deck) are withdrawn. They are not comparable to the table above.
- Checks: `runs_ok`, `closed_form_25pct`, `sign_discriminates`, `sys_off_60_at_alloc_dcp_le_0p25fF`, `sys_on_100` all True. ACCEPT.

## 3. Leakage drift (`--drift`)

I is the leakage of EACH island side (100 pA per side = 200 pA island total). The REVIEW's 21 mV / 170 mV figures count 100 pA for the whole island.

| case | stage 1 drift | closed form | stage 2 drift | vs stage-1 limit 0.2 V | vs 50 mV row |
|---|---|---|---|---|---|
| 2 MHz, N 4096 | -43.0 mV | -43.0 mV (0.0 %) | -101.8 mV | ok | ok |
| 0.25 MHz, N 4096 | **-344.1 mV** | -344.1 mV (0.0 %) | -814.4 mV | **FLAG exceeded** | FLAG exceeded |
| 0.25 MHz, N 1024 | -86.0 mV | -86.0 mV (0.0 %) | -203.6 mV | ok | FLAG exceeded |
| 0.25 MHz, N 1024, anchored (bleeders 1e12/1e13 + Roff 1e12 kept; contrast, not gated) | -85.9 mV | -86.0 mV (0.1 %) | -203.2 mV | ok | FLAG exceeded |

**FLAG: 0.25 MHz / N 4096 stage-1 drift is 344 mV, above the 0.2 V limit.** The deck matches the closed form to 0.0 %, so the number is a property of the leakage allocation and the conversion time, not of the deck. The leakage-drift row of the SPEC input-CM range (D34, C-M4) is to be set from this result; options are limiting N or fs at the slow end, or lowering the island leakage allocation. `ACCEPT` (run health).

## 4. Pin path (`--rsrc2`)

| case | dR | pair error at Vin_cm 0.2 / 2.0 V | sys-on CMRR | review form 1/(dR fs Cp,top) | settling-aware closed form |
|---|---|---|---|---|---|
| A: SPEC pad 5 pF, Cp,top 15 fF | 0 ohm | -9396.8 / -9399.0 nV | 178.4 dB | inf | 0 |
| A: SPEC pad 5 pF | 50 ohm | -9396.9 / -9398.8 nV | **179.6 dB** | 116.5 dB (1.5e-6) | 8.5e-39 |
| B: board-cap pad 2 nF | 0 ohm | 89600.7 / 89601.1 nV | 180.0 dB | inf | 0 |
| B: pad 2 nF | 50 ohm | 88210 / 90808 nV | 116.8 dB | 116.5 dB | 1.470e-6 (deck within 2 %) |

**Finding.** With the SPEC pad (tau 2.5 ns << t_half) the pin node settles inside the phase, so the deck CMRR is 179.6 dB, no worse than the review bound of 116.5 dB. The review form 1/(dR fs Cp,top) is valid only for tau_pin >~ T (board capacitance behind dR); case B (pad 2 nF, tau ~ T) lies in that regime and agrees with the settling-aware form within 2 %. The SPEC pad figure is therefore 179.6 dB (deck, at the noise/offset floor), not the review bound. D35(b) form confirmed. ACCEPT.

## 5. Cross-check of the model against the deck (`--xcheck`)

| case | deck gain / INL | model gain / INL | reviewer figures | result |
|---|---|---|---|---|
| A60 base | -5.589e-4 / 3.99 ppm | -5.471e-4 / 3.09 | -5.59e-4 / 3.99; model -5.47e-4 / 3.09 | ok |
| A60 k025 | -2.931e-4 / 6.98 | -2.882e-4 / 5.90 | match | ok |
| A60 c1_025 | -5.507e-4 / 10.05 | -5.430e-4 / 7.43 | match | ok |
| A80 base | -5.630e-5 / 0.413 | -5.470e-5 / 0.295 | INL 0.29 / 0.295 | ok |
| A80 Roff 1e14 | -5.580e-5 / **0.410** | -5.470e-5 / 0.295 | INL 0.29 / 0.295 | ok |
| noise | deck rms 7.46e-5 u vs theory 7.10e-5 (ratio 1.052), sigma_in 2.011 mV, 32 conv | model 7.15e-5 | slope -1.043, corr -1.000 | ok |

**Roff 1e14 row: no change** (0.410 ppm against 0.413 ppm at the base Roff). m4's suspicion that the bias came from the Roff model is not supported: the model-versus-deck gap (0.295 vs 0.41 ppm INL) is not the null floor and does not move with Roff. ACCEPT.

## 6. Non-vacuity (`--nonvac3`)

All broken decks reject (exit 1, as required):

| broken copy | value | limit | control (must pass) |
|---|---|---|---|
| dCp,top 2 fF (Cp 20 fF, eps_Cs 0) | sys-off CMRR 48.3 dB | 60.0 dB: REJECT | dCp 0.25 fF: 66.4 dB passes |
| OTA1 SR 6 V/us (2 MHz, N256) | INL 1623.3 ppm | 13.33: REJECT | SR 12 V/us: 0.29 ppm passes |
| leakage 10 nA (0.25 MHz, N256) | stage-1 drift -2.150 V | 0.2 V: REJECT | 100 pA: -21.5 mV passes |

## Items for the coordinator

- FLAG 3 (knees): 4 MHz boost OTA1 margin 19 % / 10 %; OTA1-only boost has no knee above 12 V/us.
- FLAG (drift): 0.25 MHz / N 4096 stage-1 drift 344 mV > 0.2 V.
- FLAG (cm2): sys-off CMRR 54-56 dB at dCp,top 1 fF (4x the allocation).
- D34: the OTA1 SR, input-CM range and CMRR rows can now be frozen with these numbers; the leakage-drift row needs a decision on the 0.25 MHz / N 4096 case.
