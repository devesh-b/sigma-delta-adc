# SPEC.md — tt-iadc design specification (incremental ΣΔ ADC, sky130A / Tiny Tapeout)

Status: draft for design, pre-silicon. Rev 2026-11-07b: review fixes applied (VREF/model mismatch, TG input switch, PGA x1/x2 in v1, GBW/slew derivations, raw accumulator output, CJC off-chip, corner set §6). Scope: the numbers you design each block to. Anchored on the
best-fit application (ratiometric temperature sensing) with secondary modes (DC/ratiometric
monitoring, thermocouple/shunt with PGA, analog entropy-source recovery). Pairs with
PUBLICATION_PLAN.md (how it gets characterized) and iadc.py (the model that predicts these numbers).

All targets are v1 (commit) unless marked (stretch). "Confirm in model/PDK" = not yet locked.

---

## 1. System-level specification

| Item | Value | Notes / derivation |
|---|---|---|
| Architecture | Fully-differential, 2nd-order CIFB incremental ΣΔ, 1-bit quantiser | reset every conversion |
| Fallback | 1st-order mode (bypass 2nd integrator) | high-confidence safety net |
| Loop coefficients | c1 = 0.25, c2 = 0.5, k = 1 | keeps both integrators within ±1.2·VREF (0.5/0.5 clips) |
| Clock fs | 0.25–4 MHz, nominal **2 MHz** | SC ⇒ jitter-immune; OTA power ∝ fs·C |
| N (cycles/conversion) | 64 / 256 / 1024 / 4096 | res ≈ 2·log2(N) − 4 (order 2): N=64→~8 b, N=1024→~16 b, N=4096→~20 b. N is a counter value (digital-only cost), so all four stay in v1 |
| Output rate | fs/N: e.g. 2 MHz/1024 ≈ 1.95 kSPS; firmware averages K sub-conversions to reach 3.75–240 SPS | slow precision via averaging + system chop |
| Reference | **External / ratiometric only**, no bandgap in v1 | VREF choice constrained by swing — see §2.1 |
| VREF nominal | **1.2 V provisional** (range 1.0–2.048 V, ratiometric) | 2.048 V keeps the MCP3421 FSR but stresses OTA output swing on 3.3 V. **All model numbers in §2 were run at 2.048 V**: µV noise and ppm INL carry over, effective resolution drops by log2(2.048/1.2) ≈ 0.77 b at 1.2 V. Alternative (option B, corrected per review F1): keep 2.048 V and halve swing with **c1 = 0.125, k = 0.5** (k/c1 stays 4, bitstream identical to c1 = 0.25/k = 1). Decided by study S1 (work/v1-design/PLAN.md) |
| Supply | VAPWR 3.3 V (analog), VDPWR 1.8 V (digital) | uses_3v3 template |
| Sampling cap Cs | 1 pF (MIM `cap_mim_m3_1` only) | kT/C averages over N ⇒ 1 pF ample |
| PGA | **×1 / ×2 (v1)**; ×4 / ×8 (stretch) via Cs:Cref ratio | ×8 needs 8 pF input Cs per side (area, Zin ≈ 125 kΩ) or a 125 fF ref cap (kT/C). Separate input/ref caps add mismatch gain error (calibratable) |
| Power (analog) | ≤ 200 µA | OTA dominates |
| Area | 2×2 tile (~334×225 µm, ~75k µm²) | met5 forbidden; power on met4 |
| Analog pins | ua0 VIN+, ua1 VIN−, ua2 VREF, (ua3 integrator/supply monitor, optional) | pad path <500 Ω, <5 pF, ≤4 mA |

---

## 2. Noise, resolution and linearity budget

### 2.1 Full-scale, LSB, and the swing constraint
- FSR (differential) = 2·VREF. At VREF=1.2 V ⇒ 2.4 Vpp; at 2.048 V ⇒ 4.096 Vpp.
- **Design tension to resolve in the model (study S1):** peak integrator excursion ≈ ±1.2·VREF (volts). Fully
  differential, that is ±0.6·VREF per side around the CMFB common mode. On a 3.3 V analog supply with
  CM ≈ 1.65 V, VREF=2.048 V ⇒ per-side swing ≈ ±1.23 V (0.42–2.88 V) — hard for a cascoded OTA output.
  VREF≈1.2 V ⇒ per-side ≈ ±0.72 V (0.93–2.37 V) — comfortable. **Provisional: design to VREF≈1.2 V,
  verify the folded-cascode output swing in sim, raise VREF only if swing allows.** Option B: VREF 2.048 V
  with c1 = 0.125 **and k = 0.5** (both integrators at half swing, bitstream identical, white noise gain
  up to 9.3, Cint1 = 8 pF/side ≈ +4000 µm²) — compare both in S1 before locking. (c1 = 0.125 with k = 1 is a
  different NTF — review F1.) **x2 swing is a free choice via c2** (y = sign(x2)): c2 = 0.25 halves it with an
  identical bitstream; limited only by comparator offset/noise/kickback (eases OTA2, review E1).
- **Input CM (review F2, OPEN — user Q1):** OTA virtual-ground CM = Vcm_s + Vref_cm − Vin_cm. The input CM range
  must be specified and Vcm_s chosen so the PMOS pair stays in range at all corners (or use CM-rejecting
  input switching). **Usable input range:** ±0.9·VREF (model-verified swing); overload 1.0–1.1·VREF must
  recover on the next conversion (review m3).

### 2.2 Input-referred noise targets (model, Cs=1 pF, fs=2 MHz)
| Case | 240 SPS | 15 SPS | 3.75 SPS |
|---|---|---|---|
| kT/C only | 2.0 µV | 0.5 µV | 0.24 µV |
| + 1/f, no chop | ~10 µV | ~7 µV | ~8 µV |
| + system chop | 3.8 µV | 0.7 µV | 0.3 µV |
| + OTA + system chop | 2.6 µV | 0.5 µV | 0.23 µV |

Targets: **≤ 50 µV rms @ 15 SPS (v1); ≤ 5 µV (stretch).** Model intrinsic floor ~0.5 µV.
Noise-gain note: in a **stray-insensitive SC integrator**, offset and 1/f refer to the input with gain ≈ 1;
the wideband gain (1+Cf/Cs+Cp/Cs ≈ 5.3) applies to **white** noise only. (Bottom-plate sampling is
mandatory too, but for a different reason: it removes signal-dependent charge injection.)
Noise in µV does not depend on VREF; effective bits do (see §1 VREF row).

### 2.3 Linearity vs OTA gain (swing-dependent gain, 90% loss at full swing)
| OTA DC gain A0 | INL |
|---|---|
| 70 dB | ~120 ppm |
| 80 dB | ~45 ppm |
| 90 dB | ~19 ppm |

⇒ **≤100 ppm needs A0 ≳ 72 dB.** Constant finite gain gives gain error (≈1/A0, calibratable), not
INL; INL comes from gain that **varies with swing** ⇒ OTA output-stage linearity is a key spec.

---

## 3. Block specifications

### 3.1 OTA (first integrator — the critical path, no TT precedent)
| Parameter | Target | Derivation |
|---|---|---|
| Topology | Fully differential, PMOS input pair, with CMFB | PMOS for lower 1/f |
| DC gain A0 | **≥ 75 dB** (v1, **OPEN — review F5 / user Q6**: 75 dB gives 71 ppm, failing the PLAN's 1.5× INL margin; candidates 78–80 dB, tighter a0_drop, or half swing); 80–90 dB (stretch) | §2.3, for ≤100→≤30 ppm INL |
| Output-swing linearity | gain drop ≤ ~90% at max excursion; characterise g_m vs Vout | dominant INL mechanism |
| GBW (OTA) | **≥ 10 MHz required, 20 MHz design target** at fs=2 MHz (scale with fs) | see settling below |
| Phase margin | ≥ 60° | SC stability |
| Slew rate | **≥ 10 V/µs** (diff) | per-cycle output step ≤ c1·2·VREF = 0.5·VREF diff (0.6 V at 1.2 V, 1.0 V at 2.048 V), slewed in ≤ ~0.4·t_half (100 ns) ⇒ ≥ 6–10 V/µs; full integrator excursion builds over many cycles, not one step |
| Input-referred noise | white ≤ 7 nV/√Hz; re-characterise 1/f corner (Paul: 6.9 nV/√Hz, fc≈631 kHz) | .noise sim, not .tran |
| Output swing | accommodate ±1.2·VREF excursion (see §2.1) within linear range | sets VREF |
| Current | budget within ≤200 µA total (OTA1 dominant; OTA2 relaxed) | ∝ fs·C |

Settling derivation (corrected per review F3): at fs=2 MHz, t_half = 0.45/fs ≈ 225 ns (model value, after non-overlap). The model shows **linear** incomplete settling gives
**gain error only** (calibratable) as long as τ ≤ 0.2·t_half ≈ 50 ns ⇒ closed-loop BW ≥ 3.2 MHz ⇒ OTA
GBW = BW/β with β = Cint/(Cint+Cs+Cp) = 4/5.3 = **0.75 (int1)**, 2/3.3 = 0.61 (int2) ⇒ GBW ≥ ~4.3 MHz at 2 MHz;
**required ≥ 10 MHz at the real load** (Cs2 + series(Cs+Cp, Cint) + comparator) and worst corner. The old
16-bit full-settling rule (11τ ⇒ τ ≤ 23 ns ⇒ 14–23 MHz) is kept as the **design target (20 MHz)** for
margin, because the real INL risk is the nonlinear part (slew, swing-dependent gm), not linear τ.
**Caveat (F3):** the model's settling study covers input/reference RC only, not OTA GBW/slew. Slew-then-settle
error is signal-dependent: ≈3e-5 of a step at 2 MHz (OK) but ≈6e-3 at **4 MHz** (thousands of ppm INL) with
GBW 10 MHz / SR 10 V/µs. **OPEN — user Q2:** 4 MHz = fast/low-resolution mode with its own INL target, or spec the
OTA at fs_max (GBW ≥ 20 MHz, SR so slewing ≤ 20 % of t_half then ≥ 10τ). Tier 1 (S5) gets OTA GBW/SR terms.

Second integrator: same topology, relaxed gain/noise (its noise divides by first-stage gain).

### 3.2 Comparator (1-bit quantiser)
| Parameter | Target | Notes |
|---|---|---|
| Topology | StrongARM latch + SR/retiming FF. **One retimed FF output drives both the DAC switches and the decimator** (review F8: first decision after reset has x2 = 0, so it is metastable every conversion; DAC/decimator disagreement ⇒ ≈4/N FS error, sporadic) | optional: force y[0] digitally |
| Offset | ≤ ~20 mV tolerable | incremental loop + first-integrator gain suppress it to input; design modest, don't over-spend |
| Noise (input-ref) | ≤ few hundred µV | divided by integrator gain at input |
| Decision time | < 0.3·t_half | fits within clock phase |
| Kickback | minimise (preamp or isolation) | corrupts integrator state |

### 3.3 Switches
| Switch | Type | Spec |
|---|---|---|
| Input sampling | **3.3 V TG (complementary)**, sized for τ ≤ t_half/12 at **ss/−40 °C/3.0 V** incl. 500 Ω pad + source (review m4), bootstrapped only if block sims show need | with bottom-plate sampling and full settling, Ron nonlinearity does not matter: TG ~1 kΩ × 1 pF ⇒ τ ≈ 1 ns vs 250 ns t_half. A bootstrap adds 3.3 V device stress risk and sim effort (first-cut rule) |
| Integrator / feedback | TG (complementary) | Ron < ~1 kΩ; bottom-plate with dummy switches |
| Chopping / DAC | TG | matched, charge-injection cancelled |
| Sampling scheme | **Bottom-plate** mandatory, stray-insensitive integrator | bottom-plate: signal-independent charge injection; stray-insensitive topology: offset/1-f gain ≈ 1 |

### 3.4 Capacitors (MIM `cap_mim_m3_1` only; no MOS caps in signal path)
| Cap | Value | Note |
|---|---|---|
| Cs1 (sample, int1) | 1 pF | = DAC cap (1-bit DAC reuses Cs) |
| Cint1 | 4 pF | c1 = Cs1/Cint1 = 0.25 |
| Cs2 (sample, int2) | 1 pF | |
| Cint2 | 2 pF | c2 = Cs2/Cint2 = 0.5 |
| PGA caps | binary Cs for ×1/2/4/8 | matching-limited gain error |
| Density | ~2 fF/µm² (confirm in PDK) | total core caps ×2 (diff) ≈ 16 pF ≈ 8000 µm² (~10% of tile) |
| Layout | common-centroid, guard-ringed | matching + substrate isolation |

### 3.5 Reference / 1-bit DAC
- 1-bit DAC: switch Cs between +VREF / −VREF ⇒ **inherently linear** (mismatch ⇒ gain error only).
- External VREF buffered off-chip; on-chip reference settling τ_ref ≤ 0.2·t_half (gain error only).
- Reference loading through the 500 Ω pad gives **gain error only** for settled SC (not INL).

### 3.6 Clocking
- 2-phase non-overlapping + delayed phases for bottom-plate sampling.
- fs from programmable divider off the TT clock (0.25–4 MHz).
- Chop clocks: **system chop** toggled at conversion/reset boundaries (digital, 4 switches);
  **OTA chop** at fch above the 1/f corner (>~631 kHz, re-characterise).
- ⚠ Verify in model: OTA-chop residual is weighted by the CoI kernel in incremental mode and may not
  cancel as in free-running ΣΔ (Ulm result). System chop between sub-conversions is the robust path.

### 3.7 Decimator (digital, on-chip — must live in the macro)
- Order-2 **cascade-of-integrators**: 2 accumulators + counter; reset each conversion (incremental).
- Order-1 mode: single accumulator.
- Accumulator width: acc2 max = N(N−1)/2; N=4096 ⇒ 8,386,560 < 2²³−1 ⇒ signed 24-bit fits (margin 2047); use 32-bit.
- Accumulator convention bound to the model: **exclusive S** (`acc2 += acc1` before `acc1 += y`). An inclusive
  RTL acts like k/c1 = 5 (≈2/N gain error); golden vectors (S6) pin the convention (review m2).
- Precision reconstruction for verification (review F9): u = (ΣS + (k/c1)·S + x2[N]/(c1·c2)) / (N(N−1)/2) is exact;
  transistor-level INL checks use it with x2[N] read from the sim.
- Output: **raw accumulators** (acc1 = S, acc2 = ΣS; up to 32 b) via shift register on uo; firmware forms
  u = (acc2 + (k/c1)·acc1) / (N(N−1)/2), so no on-chip divider. Plus **raw bitstream pin**, data-ready, valid.
- **Frame tags (review F4):** each word carries chop sign, order, N code and a frame counter, so firmware
  demodulates system chop correctly even if a frame is dropped.
- **System-chop swap only inside the reset window**, never mid-conversion; integrators fully reset between
  swapped sub-conversions (reset depth r ≤ 2.2e-3 at N=1024, ≤ 1.4e-4 at N=64).
- 1.8↔3.3 V level shifters between analog macro and digital.

### 3.8 Configuration & I/O
- Config register (via ui pins or simple SPI): order (1/2), N, fs divider, PGA gain, OTA-chop en,
  system-chop en, mode.
- **Internal-short input mode** (mux VIN to CM) — required to measure the ADC's own noise floor.
- ua3 optional monitor: integrator output or supply-sense (for the leakage-observability experiment).

### 3.9 Physical
- Template: `tt_analog_2x2_3v3.def`; uses_3v3: true.
- met5 forbidden; power stripes on met4.
- Common-centroid MIM arrays; guard rings around OTA and caps; separate analog/digital grounds where
  possible; keep the digital decimator away from the first integrator.
- DRC/LVS/PEX as CI gates (Phase 4).

---

## 4. Per-application spec mapping (what to validate post-silicon)

| App | Needs | This design | Verdict |
|---|---|---|---|
| RTD/thermistor (ratiometric) | ~100 µV/°C, ref cancels | external/ratiometric VREF; 5–50 µV ⇒ 0.05–0.5 °C | **primary / best fit** |
| DC & battery monitoring | 14–16 b, V-level | native | strong |
| Thermocouple (type-K) | 41 µV/°C, ~52 mV span, CJC | PGA ×4/×8 (stretch); **CJC off-chip** (external RTD/thermistor on a second conversion) — no on-chip temp sensor in v1 | good at stretch |
| Shunt / coulomb counting | µV offset critical | system chop <1 µV offset | plausible, floor-limited |
| Entropy-source recovery | fast mode + raw pin + self-noise subtract | N=64–256, raw bitstream, internal-short | secondary result |
| Load cell / bridge | ~50 nV rms | — | out of reach v1 (needs ~×128 LNA) |
| ECG / EEG | ≥500 SPS, ≥2.5 MΩ Zin, <5 µV | rate is fine (~2 kSPS at N=1024); noise at that rate (~2–5 µV floor, more with coupling) and ~1 MΩ Zin are the limits | out of reach |

Input impedance to publish: Zin ≈ 1/(fs·Cs) ≈ 1 MΩ/side at 1 MHz, 1 pF — buffer high-Z sources.

---

## 5. Open items to lock before tapeout
1. **VREF vs swing** (§2.1) — settle VREF in the model against measured/sim OTA output swing.
2. **OTA-chop weighting in incremental mode** (§3.6) — confirm cancellation or drop OTA chop, keep
   system chop.
3. **Re-characterise OTA 1/f** for the actual input pair (Paul's numbers are a placeholder).
4. **PGA gain-error budget** — pick cap matching / layout for target calibratable error.
5. **Accumulator widths & output word format** — fix for N_max=4096.
6. **OTA-chop-only residual** in incremental mode (≈ Vos/N ≈ 3 µV for 3 mV, N=1024): quantify in S2.
7. **Comparator kickback** and offset at corners: confirm the ≤20 mV budget is ≥3σ.
8. Feed §3.1 OTA sim params (A0, a0_drop, GBW, ota_white, ota_fc) back into iadc.py and re-run the
   design point; update §2 tables with the real numbers.

---

## 6. Corner and sign-off conditions (every block and the top must pass ALL of these)

| Axis | Set | Note |
|---|---|---|
| Process | tt, ss, ff, sf, fs (sky130 MOS corners) **+ 2 combined R+C points: ss_hh (settling), ff_ll (kT/C, noise)** | R+C sections ll/hh/hl/lh and *_mm exist in sky130.lib.spice (review m5) |
| Temperature | −40, 27, 125 °C | bench test covers 0–60 °C; wider sim range is margin |
| VAPWR | 3.0, 3.3, 3.6 V | ±10 % |
| VDPWR | 1.62, 1.8, 1.98 V | ±10 %; ×3 axis for level shifters and digital ⇒ 135 points for C7/C9 (review m7) |
| Mismatch | Monte Carlo ≥ 200 runs at tt/27 °C, ≥ 50 at worst PVT corner (`*_mm` sections) | pass = estimated μ ± 3σ inside spec **and** every sample inside spec (review m6) |
| fs | 0.25, 2, 4 MHz (nominal 2) | settling at 4 MHz, leakage at 0.25 MHz |
| Layout | schematic first, then PEX (C+CC) at the same corners | PEX within margin of schematic (§ PLAN gates) |

Pass rule: **a spec passes only if it passes at every corner above.** One corner failing = gate closed.

Known un-simulated risks (listed in V9, not gated): the sky130 MIM model has **no voltage coefficient and no
bottom-plate parasitic** (tc1 = tc2 = 0, c0–c1 only), so Cint VCC INL and Cp appear only in PEX/silicon;
digital→analog substrate coupling inside the tile is not simulated.

Open user decisions from review: Q1 input CM range + REF− (chip ground vs ua3 as Kelvin REF−, +€100), Q2 4 MHz
mode, Q3 shared Cs (no PGA) vs separate Cin/Cref (PGA ×2), Q5 order-1 mode coverage, Q6 A0 target vs INL margin.
