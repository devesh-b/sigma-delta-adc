# WO-24 results (C1b part 1), 2026-11-10

Frozen copies: `regr/tt/WO-24-84aca8c` (step 0, kp sweep, op/AC), `regr/tt/WO-24-8ef9a7e` (gate B). Raw logs here (JSON lines).

## Step 0: tests and revc_inl
- pytest design+model: 163 passed.
- revc_inl on the r5 tables: exit 0. 27 nominal rows ACCEPT; mutpcb2 (ss/125 boost) REJECTED at 9.855 ppm (gate 3.33).
- Broken copies: mutpcb2 table swapped to nominal → mutant PASSED (2.198 ppm), exit 1. Empty dir → exit 1. Review fix 7 verified.

## Step 1: K_P × m_plc sweep (spot deck, base mode, ideal CMFB) — `kp_a.log`, `kp_b.log`
- Op failed (timestep too small, many copies in one deck) at tt/27, ss/−40, ff/125, sf/−40. fs/−40 ran, but its margins came back NaN. The netlisted op/AC below covers all 9 corners.
- Precision A0 [dB], 5 corners that converged:

| corner | K8 p15 | K8 p30 | K9 p15 | K9 p30 | K10 p15 | K10 p30 | K11 p15 | K11 p30 |
|---|---|---|---|---|---|---|---|---|
| ss/125 | 81.32 | 81.75 | 82.64 | 83.17 | 83.46 | 84.06 | 84.01 | 84.65 |
| fs/125 | 79.28 | 79.63 | 80.98 | 81.44 | 82.06 | 82.61 | 82.78 | 83.39 |
| sf/125 | 80.96 | 81.35 | 82.10 | 82.57 | 82.81 | 83.32 | 83.27 | 83.82 |
| ff/−40 | 79.55 | 79.92 | 81.77 | 82.27 | 83.23 | 83.82 | 84.20 | 84.85 |
| fs/−40 | 78.43 | 78.80 | 81.15 | 81.71 | 83.00 | 83.71 | 84.26 | 85.09 |

- Base span at K10: 1.75–2.81 V (≥ 1.6). Boost K7 span at hot corners: 1.414 / 1.482 / 1.496 V.
- **On the spot deck, K_P 10 alone (p15) reaches ≥ 82.0 dB.** D55 (p30) adds +0.5–0.7 dB.
- **D55 lowers f_cm (hand estimate):** base 3.5–4.5 MHz against 4.5–5.9 MHz at p15; boost 5.4–5.6 against 6.9–7.4 MHz. Both miss the ≥ 9.4 MHz tb9 need (RC-m2); p15 is closer.
- vbpc current: K10 0.70 µA base; boost B7 0.98 µA.

## Step 3: netlisted OTA1 op/AC, 9 PVT × 2 modes × 3 C_L (K_P 10 + D55, DC-equivalent CMFB) — `opac_a.log`, `opac_b.log`
Precision exit A0 ≥ 80.3 dB: **fails at fs/−40 (79.47) and ff/−40 (80.23)**. The netlisted A0 is 3.5–4 dB below the spot deck at the cold corners.
- At −40 °C, mplc1/mpl1 margins are 75–95 mV in base and 40–60 mV in boost, and Rdn/Rup is 2.6–5.4. The PMOS load side limits the gain.

| corner | A0 base | A0 boost | hand Δ | GBW base lump/integ/hold [MHz] | GBW boost lump/integ/hold | fp2/GBW boost integ | PM boost integ | I base/boost [µA] | fails |
|---|---|---|---|---|---|---|---|---|---|
| tt/27/3.3 | 82.17 | 80.10 | +0.4 | 20.0/32.2/27.8 | 38.8/62.1/53.6 | 1.42 | 59.2 | 60.1/120.0 | — |
| ss/−40/3.0 | 82.04 | 79.15 | +0.4 | 25.5/40.7/35.2 | 48.3/76.1/66.1 | 1.08 | 52.0 | 61.8/122.1 | — |
| ss/125/3.0 | 83.21 | 80.56 | +0.3 | 17.5/28.2/24.3 | 32.9/52.3/45.3 | 1.24 | 55.5 | 59.2/118.6 | — |
| fs/125/3.0 | 81.50 | 78.62 | +0.3 | 16.3/26.4/22.6 | 31.6/50.6/43.7 | 1.41 | 58.8 | 59.3/118.7 | — |
| sf/125/3.0 | 82.60 | 80.50 | +0.4 | 18.2/29.1/25.2 | 33.8/53.9/46.6 | 1.32 | 57.3 | 58.2/117.6 | — |
| ff/−40/3.6 | **80.23** | 77.97 | +0.5 | 24.5/39.4/34.0 | 48.1/76.5/66.2 | 1.35 | 57.9 | 60.8/121.1 | A0 < 80.3 |
| ff/125/3.6 | 82.24 | 80.53 | +0.4 | 17.2/27.8/23.9 | 33.2/53.5/46.1 | 1.61 | 62.2 | 58.2/117.5 | I_fold/I_tail 1.192 |
| fs/−40/3.0 | **79.47** | 75.92 | +0.4 | 24.4/39.3/33.9 | 47.5/75.4/65.3 | 1.20 | 54.7 | 62.0/122.2 | A0 < 80.3; boost mplc1 margin 40 mV |
| sf/−40/3.0 | 80.44 | 78.40 | +0.5 | 23.5/37.6/32.5 | 45.2/71.6/62.1 | 1.23 | 55.4 | 60.8/121.2 | — |

- Hand A0 lies within +0.3 to +0.55 dB of AC at every corner (exit ±1 dB met).
- **Boost fp2/GBW at the real integrate-phase load is 1.08–1.61, below the WO-22 window of 2.2–3.0.** At the 1.4 pF lump it is 1.89–2.75. Gate B decides.
- β1 0.831–0.845 across corners (CL-4 ≥ 0.83 met; Cp_vg 231–314 fF).
- V_OCM error (DC-equivalent CMFB): −31 to +23 mV.
- Broken copy: m_nc short at tt drops A0 to 69.3 dB (finite) → REJECTED (good).
- Boost A0 is 75.9–80.6 dB. The boost gate is table-INL (CL-1b), not A0. The A(v) tables need a rerun on the netlisted OTA (step 5).

## Step 4: gate B (fs/125 boost, N 1024, 4 MHz, C_FOLD_EXTRA 0)
- Smoke run (N 64, m 3, O0) first failed on control-mode `meas ... par()`. Fixed in 8ef9a7e. The rerun is clean.
  - Out CM at reset release: 1.538 / 1.553 / 1.551 V against V_OCM 1.50 V. Island CM 1.19–1.20 V.
  - Dummy-conversion out CM is 2.61 V (start-up).
- Full run: N 1024, m 21, O1, in 6 parts. Pending.
