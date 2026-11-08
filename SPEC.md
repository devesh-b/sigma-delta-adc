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
| Loop coefficients | **c1 = 0.125, c2 = 0.5, k = 0.5** (user D3, option B) | bit-identical to c1 0.25/k 1 (k/c1 = 4); both integrators at half swing: S1 peak 0.61 V/side at VREF 2.048 V. Note (review M1): B's INL edge over A comes from c1 halving, not VREF; at N 4096/A0 80 dB, B ≈ 3.7 ppm. Area option E1: Cs 0.5 pF/Cint1 4 pF keeps ratios (INL unchanged), saves ≈4000 µm², kT/C 0.54→0.76 µV @15 SPS. c2 stays free for x2 sizing (0.25 halves x2) |
| Clock fs | 0.25–4 MHz, nominal **2 MHz** | SC ⇒ jitter-immune; OTA power ∝ fs·C |
| N (cycles/conversion) | 64 / 256 / 1024 / 4096; **precision modes (3.75–60 SPS) use N = 4096** (D23: N 1024 leaves ≈33 µV non-averaging quant error, N 4096 ≈2 µV) | res ≈ 2·log2(N) − 4 (order 2): N=64→~8 b, N=1024→~16 b, N=4096→~20 b. N is a counter value (digital-only cost), so all four stay in v1 |
| Output rate | fs/N: e.g. 2 MHz/1024 ≈ 1.95 kSPS; firmware averages K sub-conversions to reach 3.75–240 SPS | slow precision via averaging + system chop |
| Reference | **External / ratiometric only**, no bandgap in v1 | VREF choice constrained by swing — see §2.1 |
| VREF nominal | **2.048 V** (user D3, option B, 2026-11-07; ratiometric, range 1.0–2.048 V) | keeps the MCP3421 FSR; swing handled by c1 = 0.125/k = 0.5. S1 (results/s1_vref.md): noise 0.54 µV @15 SPS (lf 5.3), INL 12.4 ppm at A0 75 dB / vlin 2.0 V diff, peak 0.61 V/side. Costs: Cint1 8 pF/side (+4000 µm² total), white-noise gain 9.3 |
| Supply | VAPWR 3.3 V (analog), VDPWR 1.8 V (digital) | uses_3v3 template |
| Sampling cap Cs | **0.5 pF** (MIM `cap_mim_m3_1` only; user D22) | kT/C averages over N; INL set by ratios (unchanged); noise ota+sys 0.71 µV @15 SPS |
| PGA | **none in v1 (user Q3: shared Cs)**; ×2 / ×4 / ×8 stretch via a separate Cs:Cref ratio | ×8 needs 8 pF input Cs per side (area, Zin ≈ 125 kΩ) or a 125 fF ref cap (kT/C). Separate input/ref caps add mismatch gain error (calibratable) |
| Power (analog) | ≤ 200 µA | OTA dominates |
| Area | 2×2 tile (~334×225 µm, ~75k µm²) | met5 forbidden; power on met4 |
| Analog pins | **ua0 VIN+, ua1 VIN−, ua2 VREF+, ua3 VREF− (Kelvin to sensor ground, user D24)** | pad path <500 Ω, <5 pF, ≤4 mA; both reference pins settle in ~3 ns ⇒ gain error only. Integrator/supply monitor would need ua4 (not in v1) |

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

### 3.0 Per-block specs (S3 result, v1) — authoritative for Stage C

Source: `work/v1-design/results/s3_budget.md` (WO-05) as corrected by `work/v1-design/REVIEW-S3-2026-11-07.md`.
Limits hold at every §6 corner, precision mode 0.25–2 MHz. Where §3.1–3.9 below disagree, **this table wins**.
Design point: order-2 CIFB c1 0.125 / c2 0.5 / k 0.5, VREF 2.048 V (ua2 VREF+, ua3 VREF−), Cs1 0.5 pF / Cint1 4 pF,
Cs2 0.5 pF / Cint2 1 pF, fs 2 MHz, N 4096 precision (ota+sys chop), Vos 9 mV.
Budget (all blocks): noise ≤ 2.5 µV @15 SPS, INL ≤ 20 ppm, offset ≤ 5 µV, gain ≤ 0.5 %. Joint model run at spec:
0.94 µV @15 SPS, 3.9 µV @240 SPS, 3.4 ppm INL.

| Block | Parameter | Spec | Budget line / verify |
|---|---|---|---|
| OTA1, OTA2 (until separated) | DC gain | A(0) ≥ 80 dB; A ≥ 75 dB for \|Vout,diff\| ≤ 1.4 V (x peak 1.21 V + 15 %). A(v) = **static large-signal** gain vo/vg, not incremental; S4 assumed 70/60 dB at 2.0/3.1 V (verify in C1) | INL 8 ppm; gate: model INL with simulated A(v) table ≤ 8 ppm (S4 worst 5.2 ppm) |
| OTA1 | Sampled thermal noise | ≤ 250 µV rms diff at the virtual ground, integration-phase network, chopper parked (expect ≈ 75–110 µV); en reported only | noise 1.2 µV; `.noise` integrated |
| OTA1 | 1/f, chopper | fc ≤ 631 kHz (info); constant chopper residue ≤ 1 mV; signal-dependent residue ≤ 1 µV over ±0.9 FS | noise 1.0 µV, offset reserve |
| OTA1 | GBW / PM | loaded GBW ≥ 10 MHz base (20 MHz design target) at β ≥ 0.84, C_L ≥ 1.4 pF (incl. CMFB caps); **boost=1: loaded GBW ≥ 20 MHz absolute** (D39); PM ≥ 60° both | AC + step tb, every corner |
| OTA1 | Slew | ≥ 12.5 V/µs diff, slower edge, every corner, C_L ≥ 1.4 pF, Cs2 samples x1 in OTA1's hold phase (D25); I_fold ≥ 1.2·I_tail; boost=1: ≥ 25 V/µs. Basis: tier-1 knee ≈ 10.0 V/µs at the slew INL share 1.333 ppm (s5d R1), margin 25 % (D39) | transient at real phase plan |
| OTA2 | GBW / slew | base: loaded GBW ≥ 10 MHz into ≈ 0.7 pF (15 MHz design target), SR ≥ 13.5 V/µs diff (margin 37 % at N 1024, INL 3.4× under share at N 4096); **boost=1 (tail ×2, A′ D41): loaded GBW ≥ 22.5 MHz absolute, SR ≥ 27 V/µs; Cp_vg2 ≤ 0.262 pF per side incl. Cgs, switches, routing (β2 ≥ 0.497, REVIEW-S5f M3)** (D39; gm does not scale ∝ I in moderate inversion, REVIEW-S5e C-M1) | AC + transient tb, every corner |
| OTA1/OTA2 | Offset | ≤ 9 mV 3σ (constant, cancels in sys pair). OTA2 u error = 1.5·2·Vos2/(c1(N−1)) = 52.7 µV at N 4096 (1.5 from Ck sharing the OTA2 node) | model |
| OTA1, OTA2 | Input CM / CMFB | linear (A ≥ 75 dB) for v_g,cm ∈ [V_icm − 0.13 − ΔV_drift, V_icm + 0.13] V (0.13 = D12 CM step + 10 mV CMFB); V_icm chosen in C1 for ≥ 0.2 V tail headroom at ss/−40/3.0; upper limit checked at ss/−40/3.0, lower at ss/125/3.0 (and ss/100/3.0 for 0.25 MHz N 4096). CMFB absorbs per-cycle CM charge to ≤ 10 mV in 0.2·t_half; starts from either rail | C1/C4 tb |
| OTA1, OTA2 | Devices / CMFB type (D40) | input pairs 1.8 V `pfet_01v8`/`nfet_01v8` on 3.3 V: every terminal pair ≤ 1.98 V over all transients (power-up, reset, boost toggle, 1.1·VREF overload) at every corner, via cascode/protection; CMFB switched-capacitor, its caps inside C_L | C1 device-stress tb (broken copy: protection removed ⇒ REJECT) |
| Current | Analog total | ≤ 200 µA in every mode **at every corner after trim (D42; worst ≈ 189 µA fast, ≈ 113 µA precision incl. ≈ 6 µA bandgap)**. With SC CMFB (D40, I_tot ≈ 2.7·I_tail, a lower bound if GBW-limited): base ≈ 100 µA (≈ 136 µA if fold/CMFB are sized for boost and do not switch), boost=1 ≈ 172 µA with A′ (REVIEW-S5f Q3) | hand, then C1/C6 sim |
| Bias reference (C6, D42) | Type / output | current-mode bandgap current reference (PNP `pnp_05v5` + xhrpoly), mirrored to every block; constant current over temperature: \|ΔI/I\| ≤ 3 % over −40…125 °C at a fixed trim code, every process corner | C6 tb: T sweep per corner |
| Bias reference (C6, D42) | Trim | 3-bit binary, range ≥ ±20 % of nominal, step ≤ 6 %, monotonic (every code step > 0 at every corner and MC sample), residual after best code ≤ ±3 %; reset code 100 (mid), latched only at a pair boundary (C9) | C6 tb + MC; broken copy: one trim leg open ⇒ monotonicity REJECT |
| Bias reference (C6, D42) | Start-up / PSRR / current / area | starts from VAPWR 0→3.0 V ramps (1 µs–10 ms) at ss/−40 and ff/125, no zero-current state (broken copy without start-up ⇒ REJECT); PSRR ≥ 40 dB DC on the output current; own current ≤ 6 µA; area ≤ 7,000 µm² | C6 tb; layout |
| Comparator | Offset / noise | ≤ 20 mV 3σ; ≤ 5 mV rms | INL 1 ppm, noise 0.3 µV |
| Comparator | Decision time | < 68 ns at 2 MHz (< 34 ns at 4 MHz) for \|Vin\| ≥ 1 mV, worst corner | tb |
| Comparator | Single bit (F8) | one retimed FF output drives DAC switches and decimator; y[0] forced at reset release | construction + test |
| Comparator | Kickback | ≤ 5 mV on x2, recovered before next sample (gain only, 3.8 ppm/mV) | gain reserve |
| Input switches | Settling | (Ron + 500 Ω + R_src)·(5 pF + Cs) ≤ 18.75 ns; Ron max over 0…VREF+ at ss/−40/3.0 **incl. body effect** ≤ 1.5 kΩ | INL 2 ppm; DC Ron sweep |
| Input (user-facing) | Source | no board cap: R_src ≤ 1 kΩ; with board cap (τ_pin ≥ T): sys-on CMRR = 1/(ΔR·fs·Cp,top) ⇒ ΔR (VIN+ vs VIN−) ≤ 330 Ω at 2 MHz (∝ 1/fs). Pin CM current ≈ fs·Cp,top·\|ΔVcm\|; offset ΔR·I **not** cancelled by sys chop | datasheet row |
| Reference | On-chip / board | on-chip τ_ref ≤ 10 ns; board decap ≥ 100 nF at ua2/ua3, DC R_ext ≤ 10 Ω per pin (u³ INL ≈ 1.4 ppm) | INL 2 ppm |
| Reset | Residue / window | r ≤ 1e-4 on x1 and x2; window ≥ 2 clock cycles (≥ 1 µs at 2 MHz) | offset 1 µV; inter-conversion memory test |
| Virtual ground | Leakage | per vg node (per side), sign stated (NMOS-only island switches ⇒ drift negative): **≤ 90 pA at ff/125/3.6** (0.25 MHz N 1024 stage-2 drift ≤ 0.2 V) and **≤ 20 pA at ff/100/3.6** (0.25 MHz N 4096, D39); signal-dependent ≤ 0.1 pA. Drift = I·N/(fs·C_side), C_side 4.76 / 2.01 pF | offset 1 µV; island CM rows; C4 PEX leakage tb |
| Capacitors | Matching / CMRR | Cs+/Cs− ≤ 0.75 % 3σ; Cp,top ≤ 20 fF/side; ΔCp,top random ≤ 0.25 fF 3σ, systematic (PEX) ≤ 0.08 fF; ε_inj ≤ 2.8e-4; gate \|sys\| + RSS(random 3σ) + \|ε_inj\| ≤ 1e-3 with ε_eff = ((Cp/Cs)·ε_Cs − ΔCp/Cs)/(1+Cp/Cs) + ε_inj (D36, D37) | S4 MC; C4/C10 PEX + MC |
| Clock | Phases | t_half ≥ 225 ns at 2 MHz after non-overlap; bottom-plate early phases | hand |
| Noise spec | Condition | at u = 0 (shorted input); reference noise is a board requirement | — |

**User decisions after S4/S5 (D27–D30):**
- Noise @15 SPS ≤ 2.5 µV at all corners for fs ≥ 2 MHz; at fs 0.25 MHz ≤ 2.5 µV up to 85 °C and ≤ 3.0 µV at 125 °C (D27). **fs 0.25 MHz with N 4096 is rated −40…100 °C only** (island leakage drift, D39); 0.25 MHz N ≤ 1024 keeps 125 °C.
- **Noise @240 SPS ≤ 5 µV rms** (D29).
- **Bias-boost config bit (D31, form per D39):** boost=0 (precision, fs ≤ 2 MHz), analog ≈ 118 µA. boost=1 (fast mode,
  fs 4 MHz): OTA1 tail ×2, OTA2 tail ×2 (option A′, user 2026-11-09, D41; was ×1.5), gated on **absolute boosted loaded GBW**
  (OTA1 ≥ 20 MHz, OTA2 ≥ 22.5 MHz) and SR (≥ 25 / ≥ 27 V/µs) at every corner, gated as the boosted operating point (gm/Id at the boosted current density), analog ≈ 172 µA. **Analog current ≤ 200 µA
  in every mode.** The former GBW(boost)/GBW(nom) ≥ 1.9 gate is withdrawn (REVIEW-S5e C-M1: needs gm/Id ≈ 24, infeasible
  at OTA1 size); C1 may meet the absolute rows by input-pair sizing, SC CMFB or a larger OTA2 boost, inside 200 µA.
  Boost latched only at a pair boundary (C9); one switched bias leg (C6).
- Fast mode (4 MHz) INL: N 64 ≤ 200 ppm, N 256 ≤ 20 ppm, N 1024 ≤ 5 ppm (D28; confirmed with option A, D39). Evidence (s5f): at the D39 boosted operating point (OTA1 20 MHz / 25 V/µs, OTA2 22.5 MHz / 20.25 V/µs) 3.7 ppm at N 1024; built from the minimum base GBWs with real gm/Id boost ratios 7.6–12.5 ppm (FAIL). C1 gates the **boosted operating point at every corner** (gm/Id at the boosted current density, REVIEW-S5f M1), not base × ratio. Open before S7: cold-corner over-speed run (M2), OTA2 β2 / Cp_vg2 row (M3), user chose A′ (OTA2 ×2, D41).
- **CMRR ≥ 100 dB DC (120 dB goal)** with sys chop on, **≥ 60 dB with sys chop off** (D30, D32; input CM 0…VREF). Definition: CMRR = \|ΔVin_cm/ΔV_os\|, least-squares slope over Vin_cm {0.2, 1.0, 2.0} V at fixed mismatch, N 4096 (sys off raw offset, sys on pair-demodulated). Evidence: S4 sys off 61.5 dB; sys on cites tier-1 cm2 137–173 dB (the model's ≈ 205 dB is a symmetric-mean metric, not a silicon figure). Risk: 60 dB sys-off needs CM→diff ≤ 0.1 % — Cs+/Cs− matching alone gives ≈ 0.75 % 3σ at 0.5 pF, so the D12 input-switching topology must reject CM to first order independent of cap matching (C4 owns).

Allocation after review: INL 8 (OTA) + 2 (input settling) + 2 (ref settling) + 1 (comparator) + 1 (quant floor) + 2 (ref
current) + 4 (reserve: MIM VCC, charge injection, substrate) = 20 ppm. Gain: A0 300, settling 500, k/c1 50, reserve 4150 ppm.
Noise and offset allocations unchanged from s3_budget.md. MIM total ≈ 9,000 µm² (12 % of 2×2 tile).

### 3.1 OTA (first integrator — the critical path, no TT precedent)
| Parameter | Target | Derivation |
|---|---|---|
| Topology | Fully differential, PMOS input pair, with CMFB | PMOS for lower 1/f |
| DC gain A0 | **≥ 80 dB** (v1, user Q6; 75 dB gave 71 ppm at VREF 2.048/c1 0.25 and failed the 1.5× INL margin); 90 dB (stretch) | §2.3, for ≤100→≤30 ppm INL |
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
| Cs1 (sample, int1) | **0.5 pF** (D22) | = DAC cap (1-bit DAC reuses Cs) |
| Cint1 | **4 pF** | c1 = Cs1/Cint1 = 0.125 (option B, Cs 0.5 pF) |
| Cs2 (sample, int2) | 1 pF | |
| Cint2 | 2 pF | c2 = Cs2/Cint2 = 0.5 |
| PGA caps | none in v1 (shared Cs); stretch: binary Cs for ×2/4/8 | matching-limited gain error |
| Density | ~2 fF/µm² (confirm in PDK) | total core caps ×2 (diff) ≈ (0.5+4+Cs2+Cint2)·2; with stage 2 at 1/2 pF ≈ 15 pF ≈ 7,500 µm² (~10 % of tile); stage-2 sizing in S3 |
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
- **Chop decision (user D4, 2026-11-07): keep OTA chop as a config bit, always paired with system chop**;
  system chop alone is the fallback. S2 (results/s2_chop.md): OTA chop alone leaves lf·Vos/(N−1) (closed form,
  model agrees 54/54), so it is never used alone; sys / ota+sys offset ≤ 0.8 µV at Vos 9 mV; ota+sys cuts
  240 SPS noise 1.2–14× vs sys alone.
- **Sequencing rules (S2, binding on C9):** system-chop swap only at conversion boundaries; integrators and
  sampling caps reset between swapped sub-conversions; **N even**; OTA-chop phase restarts at the same value at
  cycle 0 of every sub-conversion; sub-conversions averaged in pairs (alternating polarity, same N and fs).
  Additional rules from review (REVIEW-S1S2 m2): (7) OTA-chop state during the reset window identical every
  sub-conversion; (8) sys-chop swap on the pin side, ahead of sampling and CM-rejecting switches (only errors
  after the swap cancel); (9) one retimed y drives DAC and decimator, y[0] forced at reset release; (10) config
  changes (N, order, chop enables, fs divider) latched only at a pair boundary, first pair after a change tagged
  invalid; (11) decimator accumulators cleared on the same edge that releases the analog reset; frame carries
  chop sign and pair index; (12) reset window ≥ ~15 τ of Cint discharge (1 kΩ × 8 pF ≈ 120 ns) + post-swap input
  settling + OTA/CMFB recovery; optional +−−+ pair ordering cancels linear offset drift.
- **OTA chop scope (review E2/M3):** chopper on **OTA1 only** (OTA2 1/f is divided by c1(N−1)/2, its offset
  cancels with sys chop). OTA chop stays in v1 **only if the C1 OTA meets A0 ≥ 80 dB and settling with the
  chopper switches in place, chopping and parked**; otherwise drop it (sys-only meets 50 µV even at lf 9.3).
- **Modes without system chop are characterization-only:** they carry lf·Vos1/(N−1) (order 2; lf·Vos1/N order 1)
  plus 2·Vos2/(c1(N−1)) from OTA2 offset (35 µV at Vos2 9 mV, c1 0.125, N 4096).

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
- ua3 is VREF− (D24). An integrator/supply monitor would need ua4 (not in v1; leakage observability via the internal-short mode instead).

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
| Temperature | −40, 27, 125 °C; **plus 100 °C for fs 0.25 MHz / N 4096** (that mode is not gated at 125 °C, D39) | bench test covers 0–60 °C; wider sim range is margin |
| VAPWR | 3.0, 3.3, 3.6 V | ±10 % |
| VDPWR | 1.62, 1.8, 1.98 V | ±10 %; ×3 axis for level shifters and digital ⇒ 135 points for C7/C9 (review m7) |
| Mismatch | Monte Carlo ≥ 200 runs at tt/27 °C, ≥ 50 at worst PVT corner (`*_mm` sections) | pass = estimated μ ± 3σ inside spec **and** every sample inside spec (review m6) |
| fs | 0.25, 2, 4 MHz (nominal 2) | settling at 4 MHz, leakage at 0.25 MHz |
| Layout | schematic first, then PEX (C+CC) at the same corners | PEX within margin of schematic (§ PLAN gates) |

Pass rule: **a spec passes only if it passes at every corner above.** One corner failing = gate closed.

Known un-simulated risks (listed in V9, not gated): the sky130 MIM model has **no voltage coefficient and no
bottom-plate parasitic** (tc1 = tc2 = 0, c0–c1 only), so Cint VCC INL and Cp appear only in PEX/silicon;
digital→analog substrate coupling inside the tile is not simulated.

User decisions 2026-11-07 (review questions): **Q1 → CM-rejecting input switching** (only differential charge
transferred; input CM anywhere in 0…VREF); REF− = ua3 (D24). **Q2 → 4 MHz is a
fast / low-resolution mode** with its own INL target; precision specs gated at 0.25–2 MHz. **Q3 → shared Cs, no
PGA in v1** (PGA ×2 moves to stretch). **Q6 → OTA A0 ≥ 80 dB.** **D3 → option B (VREF 2.048 V, c1 0.125, k 0.5). D4 → keep OTA chop paired with system chop.** Defaults accepted (D21): Vos 9 mV, order-1 characterization only, overload recovery.
Cs 0.5 pF (D22), N 4096 precision (D23). REF− on ua3 (D24, user OK).
