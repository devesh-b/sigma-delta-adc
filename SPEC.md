# SPEC.md — tt-iadc design specification (incremental ΣΔ ADC, sky130A / Tiny Tapeout)

Status: **SPEC v1 FROZEN 2026-11-09** (S7 passed, user OK, D50; git tag `spec-v1`). Changes after the freeze go only through the change log at the end of this file, each with a reason and a decision ID. Rev 2026-11-09 (S7, WO-19): REVIEW-S7 edits E1-E24 applied, digital I/O table §3.8a added, no PGA in v1 (D14, D45h), CJC off-chip, corner set §6. §3.0 is authoritative; §2 and §3.1-§3.5 are informative history. Scope: the numbers you design each block to. Anchored on the
best-fit application (ratiometric temperature sensing) with secondary modes (DC/ratiometric
monitoring, thermocouple/shunt (needs a PGA: stretch, not v1), analog entropy-source recovery). Pairs with
PUBLICATION_PLAN.md (how it gets characterized) and iadc.py (the model that predicts these numbers).

All targets are v1 (commit) unless marked (stretch). "Confirm in model/PDK" = not yet locked.

---

## 1. System-level specification

| Item | Value | Notes / derivation |
|---|---|---|
| Architecture | Fully-differential, 2nd-order CIFB incremental ΣΔ, 1-bit quantiser | reset every conversion |
| Fallback | 1st-order mode (bypass 2nd integrator) | high-confidence safety net |
| Loop coefficients | **c1 = 0.125, c2 = 0.5, k = 0.5** (user D17, option B) | bit-identical to c1 0.25/k 1 (k/c1 = 4); both integrators at half swing: S1 peak 0.61 V/side at VREF 2.048 V. Note (review M1): B's INL edge over A comes from c1 halving, not VREF; at N 4096/A0 80 dB, B ≈ 3.7 ppm. Area option E1: Cs 0.5 pF/Cint1 4 pF keeps ratios (INL unchanged), saves ≈4000 µm², kT/C 0.54→0.76 µV @15 SPS. c2 stays free for x2 sizing (0.25 halves x2) |
| Clock fs | 0.25–4 MHz, nominal **2 MHz** | SC ⇒ jitter-immune; OTA power ∝ fs·C |
| N (conversion cycles per sub-conversion, plus 2 reset cycles) | 64 / 256 / 1024 / 4096; **precision modes (3.75–60 SPS) use N = 4096** (D23: N 1024 leaves ≈33 µV non-averaging quant error, N 4096 ≈2 µV) | res ≈ 2·log2(N) − 4 (order 2): N=64→~8 b, N=1024→~16 b, N=4096→~20 b. N is a counter value (digital-only cost), so all four stay in v1 |
| Output rate | one frame (sub-conversion) per N + 2 fs cycles (N conversion cycles + 2-cycle reset window, §3.7a k): fs/(N+2), e.g. 2 MHz/1026 ≈ 1.95 kSPS; firmware averages K sub-conversions (pairs) to reach 3.75–240 SPS | slow precision via averaging + system chop. Modes without system chop (and order 1, OTA-only chop) are characterisation-only (§3.6, D4, D21, D45 g) |
| Reference | **External / ratiometric only**, no on-chip voltage reference; bandgap-type bias current only (C6) | VREF choice constrained by swing — see §2.1 |
| VREF nominal | **2.048 V** (user D17, option B, 2026-11-07; ratiometric, range 1.0–2.048 V) | keeps the MCP3421 FSR; swing handled by c1 = 0.125/k = 0.5. S1 (results/s1_vref.md): noise 0.54 µV @15 SPS (lf 5.3), INL 12.4 ppm at A0 75 dB / vlin 2.0 V diff, peak 0.61 V/side. Costs: Cint1 8 pF/side (+4000 µm² total), white-noise gain 9.3 |
| Supply | VAPWR 3.3 V (analog), VDPWR 1.8 V (digital) | uses_3v3 template |
| Sampling cap Cs | **0.5 pF** (MIM `cap_mim_m3_1` only; user D22) | kT/C averages over N; INL set by ratios (unchanged); noise 0.94 µV @15 SPS governs (joint model, §3.0); 0.71 µV is the kT/C-only Cs-row value |
| PGA | **none in v1 (user Q3/D14: shared Cs; the config field is removed, D45h)**; ×2 / ×4 / ×8 stretch via a separate Cs:Cref ratio | ×8 needs 8 pF input Cs per side (area, Zin ≈ 125 kΩ) or a 125 fF ref cap (kT/C). Separate input/ref caps add mismatch gain error (calibratable) |
| Power (analog) | ≤ 200 µA design budget (D46c); ≈ 106–113 µA precision incl. bandgap, ≈ 172 µA fast (boost = 1, resets to 0) | OTA dominates; worst case after trim ≈ 189 µA fast is accepted risk (D46c) |
| Area | 2×2 tile (~334×225 µm, ~75k µm²) | met5 forbidden; power on met4 |
| Analog pins | **ua0 VIN+, ua1 VIN−, ua2 VREF+, ua3 VREF− (Kelvin to sensor ground, user D24)** | pad path <500 Ω, <5 pF, ≤4 mA; both reference pins settle in ~3 ns ⇒ gain error only. Integrator/supply monitor would need ua4 (not in v1) |

---

## 2. Noise, resolution and linearity budget

### 2.1 Full-scale, LSB, and the swing constraint (historical, pre-S3; §1 and §3.0 govern: VREF 2.048 V, c1 0.125, k 0.5)
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
- **Input CM (review F2; closed by D12, user Q1: CM-rejecting input switching):** OTA virtual-ground CM = Vcm_s + Vref_cm − Vin_cm. The input CM range
  must be specified and Vcm_s chosen so the PMOS pair stays in range at all corners (or use CM-rejecting
  input switching). **Usable input range:** ±0.9·VREF (model-verified swing); overload 1.0–1.1·VREF must
  recover on the next conversion (review m3).

### 2.2 Input-referred noise targets (historical: model at Cs = 1 pF, pre-D22; §3.0 budget governs, 0.94 µV @15 SPS at Cs 0.5 pF)
| Case | 240 SPS | 15 SPS | 3.75 SPS |
|---|---|---|---|
| kT/C only | 2.0 µV | 0.5 µV | 0.24 µV |
| + 1/f, no chop | ~10 µV | ~7 µV | ~8 µV |
| + system chop | 3.8 µV | 0.7 µV | 0.3 µV |
| + OTA + system chop | 2.6 µV | 0.5 µV | 0.23 µV |

Targets (superseded by §3.0 / D27: ≤ 2.5 µV @15 SPS, ≤ 5 µV @240 SPS): ~~≤ 50 µV rms @ 15 SPS (v1); ≤ 5 µV (stretch)~~. Model intrinsic floor ~0.5 µV.
Noise-gain note: in a **stray-insensitive SC integrator**, offset and 1/f refer to the input with gain ≈ 1;
the wideband gain (1+Cf/Cs+Cp/Cs ≈ 5.3) applies to **white** noise only. (Bottom-plate sampling is
mandatory too, but for a different reason: it removes signal-dependent charge injection.)
Noise in µV does not depend on VREF; effective bits do (see §1 VREF row).

### 2.3 Linearity vs OTA gain (historical, pre-S3: INL values are the early model; §3.0 gives A0 ≥ 80 dB and INL ≤ 8 ppm for the OTA)
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
Tier-1 (SPICE) evidence numbers in the rows below are converged per D43c: an O1/O2 pair passing the rule, or O2 alone with margin above the largest paired step (9 %). Job names are in `work/v1-design/results/s5h_tier1.md`. Earlier O0 values are unconverged, with error of either sign (REVIEW-S5h H-m1), and are not cited.

| Block | Parameter | Spec | Budget line / verify |
|---|---|---|---|
| OTA1, OTA2 (until separated) | DC gain | A(0) ≥ 80 dB; A ≥ 75 dB for \|Vout,diff\| ≤ 1.4 V (x peak 1.21 V + 15 %). A(v) = **static large-signal** gain vo/vg, not incremental; S4 assumed 70/60 dB at 2.0/3.1 V (verify in C1) | INL 8 ppm; gate: model INL with simulated A(v) table ≤ 8 ppm (S4 worst 5.2 ppm) |
| OTA1 | Sampled thermal noise | ≤ 250 µV rms diff at the virtual ground, integration-phase network, chopper parked (expect ≈ 75–110 µV); en reported only | noise 1.2 µV; `.noise` integrated |
| OTA1 | 1/f, chopper | fc ≤ 631 kHz (info); constant chopper residue ≤ 1 mV; signal-dependent residue ≤ 1 µV over ±0.9 FS | noise 1.0 µV, offset reserve; system-level 1/f through V9 (tier 0 with PEX parameters) |
| OTA1 | GBW / PM | loaded GBW ≥ 10 MHz base (20 MHz design target) at β ≥ 0.83 (CL-4), C_L ≥ 1.4 pF (incl. CMFB caps); **boost=1: loaded GBW ≥ 20 MHz absolute** (D39); **gate = closed-loop step settling** at β1, C_L, worst step ≈ 0.49 V diff (= c1(u_max + 1)·VREF = 0.125·1.9·2.048), base 2 MHz and boost 4 MHz (D43a). **Definitions (S7-M1, S7b):** h = 0.5/fs, g = 0.025/fs, t_half = h − 2g (225 ns at 2 MHz, 112.5 ns at 4 MHz). **(B) In-loop gate, authoritative for INL (D48(1) option 2):** transistor OTA1 in the tier-1 deck (OTA2 behavioural), N 1024, 2 MHz ≤ 1.333 ppm and 4 MHz boost ≤ 5 ppm, O1/O2 converged, at tt/27, ss/−40/3.0, ss/125/3.0 and fs/125/3.0 (boost; hot added by CL-3). Broken copy: tail set for 9.5 V/µs ⇒ REJECT. **(A) Step tb (report-only diagnostic, `design/tier1/step_settle.py`):** steps ±{0.1…1.0} × 0.486 V (= c1(u_max + 1)·VREF) from x1 = 0 and from ±0.72 V; ε_dyn(a) = (vo(t_half + 10τ) − vo(t_half))/a, referenced to the late value so A0 and static gain error drop out; ε_NL = max deviation of a·ε_dyn(a) from its LSQ line, divided by 0.486 V. Health check |ε_dyn| ≤ 1e-4; watch level ε_NL ≤ 3e-7 (≈ 1.333/(1.9·2): the worst-case input-referred INL is 1.9·ε_NL, slot averaging takes off 2–4×; gating it would need ≳ 14 MHz GBW, so it is not a gate). Solver: gear, reltol ≤ 1e-8, vntol ≤ 1e-10, plus a reltol/10 rerun (ε agrees within 10 %). Broken copies: tail ×0.5, GBW ×0.5. An isolated step from rest cannot see the in-loop slew knee (S7b-M2), hence (B). Tier-1 macromodel (OTA 12.5 V/µs / 10 MHz, β 0.84, C_L 1.4 pF at 2 MHz; 25 V/µs / 20 MHz at 4 MHz boost) values, reported only (not gates): ε_dyn 4.3e-9 at both points (the same by construction: gm, ip, fp2 and t_half scale together; the earlier 1.6e-8 included the A0 = 1e8 static term), ε_NL below the solver floor (≈ 1.2e-8); WO-19 broken copies GBW/2 and SR/2 differ from nominal by 1e4× and 14× in ε_dyn (SR/2 ε_NL 2.8e-8 passes any INL-derived limit, which is why (A) is not the gate). **C1 transistor OTA: (B) is the pass/fail; (A) is reported at every corner against the health check and watch level above**; PM informational: at boosted GBW 20 MHz only PM ≈ 72–77° at β1 meets the 5 ppm fast gate (fp2 sweep, S5h, O1 numbers: mult 2 → 10.9, 3 → 3.36, 4 → 8.06 ppm); outside that range GBW must rise, and the step row decides (REVIEW-S5h H-m3) | AC + step tb, every corner |
| OTA1 | Slew | **Floor (CL-9, D65): SR − 3σ (hand Pelgrom, σ of I_tail) ≥ 10.3 V/µs base, ≥ 20.6 V/µs boost at C_L = 1.4 pF** (knee-based; 12.5 / 25 V/µs below are the design point). Design point ≥ 12.5 V/µs diff, slower edge, every corner, gated at C_L = 1.4 pF (conservative sum; the itemised real per-phase load is 0.78 pF integrate / 0.90 pF hold, CL-6), Cs2 samples x1 in OTA1's hold phase (D25); I_fold ≥ 1.2·I_tail; boost=1: ≥ 25 V/µs. Basis (O2, converged): OTA1-only knee 10.23–10.28 V/µs at N 1024 (r3, gated), 10.41–10.44 at N 256 (characterisation), at the slew INL share 1.333 ppm; 12.5 V/µs = 1.22× knee (22 %). **D44: user kept 12.5 V/µs; the 25 % rule is relaxed to 22 % because INL at 12.5 V/µs, N 1024, is 0.098/0.101 ppm at O1/O2 (verdict 0.104, 12.8× under share, r3d); 13 V/µs gains only 0.02 ppm for ≈ +2.4 µA precision / +5 µA fast** | transient at real phase plan |
| OTA2 | GBW / slew | base: loaded GBW ≥ 10 MHz into ≈ 0.7 pF (15 MHz design target), SR ≥ 13.5 V/µs diff (O2, converged: 10.8 V/µs = 13.5/1.25 is still under the share at N 1024, 0.756 ppm (g_OTA2_10.8), so margin ≥ 25 %; 13.5 V/µs gives 0.253 ppm at N 1024; V4m 0.339 ppm at N 4096, 3.9× under share); **boost=1 (tail ×2, A′ D41): loaded GBW ≥ 22.5 MHz absolute, SR ≥ 27 V/µs; Cp_vg2 ≤ 0.262 pF per side incl. Cgs, switches, routing (β2 ≥ 0.497, REVIEW-S5f M3); gate = closed-loop step settling at β2, both modes, same h, g, t_half and the ε_dyn definition (late-value reference, 10τ) as the OTA1 row (A); start states x2 = 0 and ± half the x2 peak (≈ ±0.6 V diff); worst step (loop bound) = c2·|x1|max + (Ck2/Cint2)·VREF = 0.5·1.21 + 0.25·2.048 ≈ 1.12 V diff, slewing since it exceeds SR·τ ≈ 0.43 V; a typical ≈ 0.5 V step is informational only. Tier-1 macromodel (13.5 V/µs / 10 MHz at 2 MHz; 27 V/µs / 22.5 MHz at 4 MHz, β2 0.497, C_L 0.7 pF): ε_dyn 6.8e-4 / 3.0e-4, ε_NL 1.2e-4 / 6.1e-5 (report-only); limits (2 ×) on ε_dyn: ε_macro 1.4e-3 / 6e-4; C1 limit = the same ε_dyn numbers on the 1.12 V step. **Plus (B)** as a V-row: transistor OTA2 in the in-loop tier-1 deck (OTA1 behavioural or transistor), N 1024, as the OTA1 (B) INL limits, with the same pass numbers used as the reference for the transistor OTA2; PM ≈ 70–85° informational (D43a, REVIEW-S5h H-m4: optimum ≈ 72° at fp2 ≈ 1.5·GBW, 1.38/1.43 ppm O1/O2; 65.6° fails; hand PM at β2 0.497, D39 boosted point)** (D39; gm does not scale ∝ I in moderate inversion, REVIEW-S5e C-M1) | AC + transient tb, every corner |
| OTA1/OTA2 | Offset | ≤ 9 mV 3σ (constant, cancels in sys pair). OTA2 u error = 1.5·2·Vos2/(c1(N−1)) = 52.7 µV at N 4096 (1.5 from Ck sharing the OTA2 node) | model; C1/C2 MC ≥ 200 runs tt/27 plus ≥ 50 at the worst PVT (§6): 3σ ≤ 9 mV and every sample inside; broken copy: input-pair mismatch ×3 ⇒ REJECT |
| OTA1, OTA2 | Input CM / CMFB | linear (A ≥ 75 dB) for v_g,cm ∈ [V_icm − 0.13 − ΔV_drift, V_icm + 0.13] V (0.13 = D12 CM step + 10 mV CMFB; the 0.13 V step is an O0 quasi-static number, exempt per D43c); V_icm chosen in C1 for ≥ 0.2 V tail headroom at ss/−40/3.0; upper limit checked at ss/−40/3.0, lower at ss/125/3.0 (and ss/100/3.0 for 0.25 MHz N 4096). CMFB absorbs per-cycle CM charge to ≤ 10 mV at the sampling instants (end of each half-phase, charge transfer complete; D63, CL-10); CM-to-DM: the signal-dependent part ≤ 0.256 µV per sample (CL-11); starts from either rail, CM settled before the first valid conversion (the dummy conversion): ph2 sampling instants within 10 mV of steady state by 4 µs (CL-11); **Cs2 interface (CL-2):** Cs2's x1-side plates are shorted to each other (not tied to a CM bus) in OTA2's integrate phase; the CM step at the OTA1 output when Cs2 connects is ≤ 10 mV (\|V_rest,cm − V_OCM1\| ≤ ≈ 38 mV), checked in the C1 CMFB tb with the real stage-2 switching | C1/C4 tb |
| OTA1, OTA2 | Devices / CMFB type (D40) | input pairs 1.8 V `pfet_01v8`/`nfet_01v8` on 3.3 V: every terminal pair ≤ 1.98 V over all transients (power-up, reset, boost toggle, 1.1·VREF overload) at every corner, via cascode/protection; CMFB switched-capacitor, its caps inside C_L | C1 device-stress tb (broken copy: protection removed ⇒ REJECT) |
| Current | Analog total | ≤ 200 µA in every mode **at every corner after trim (D42; worst ≈ 189 µA fast, ≈ 106–113 µA precision incl. ≈ 6 µA bandgap)**. **200 µA = design budget; 189 µA worst-case fast after trim is accepted risk (D46c).** Boost resets to 0. Untrimmed (reset code 100) worst case ≈ 1.5 × the precision minimum ≈ 160 µA (D47). With SC CMFB (D40, I_tot ≈ 2.7·I_tail, a lower bound if GBW-limited): base ≈ 100 µA (≈ 136 µA if fold/CMFB are sized for boost and do not switch), boost=1 ≈ 172 µA with A′ (REVIEW-S5f Q3) | hand, then C1/C6 sim |
| Bias distribution (C6, D43b) | Boost switching | one switched reference leg; tail, fold/cascode and CMFB mirrors all slaved to it (×2 in boost, except the vbpc cascode-bias leg, which has its own ×1.75 / ×1.4 increment, CL-8): I_fold/I_tail constant ±10 % and ≥ 1.2 in base and boost, every corner; settled to 0.1 % within ≤ 0.25·T_slot,min (≈ 4 µs at N 64 / 4 MHz) after a toggle; the toggle pair is invalid (§3.7a e) (toggle only at a pair boundary, C9; CL-7). tb12 limit 4 µs, broken copy: bias reference ratio 1:256 ⇒ REJECT | C1/C6 transient tb |
| Bias reference (C6, D42) | Type / output | current-mode bandgap current reference (PNP `pnp_05v5` + xhrpoly), mirrored to every block; constant current over temperature: \|ΔI/I\| ≤ 3 % over −40…125 °C at a fixed trim code, every process corner | C6 tb: T sweep per corner |
| Bias reference (C6, D42) | Trim | 3-bit binary, range ≥ ±20 % of nominal, step ≤ 6 %, monotonic (every code step > 0 at every corner and MC sample), residual after best code ≤ ±3 %; reset code 100 (mid), latched only at a pair boundary (C9). **Volatile (D47):** TT has no NVM or fuses, so firmware rewrites the trim after every rst_n; the reset state is trim 100 with boost 0, untrimmed worst case ≈ 160 µA (inside the 200 µA budget). **No dedicated pins:** the trim is a field of the serial config shadow register (§3.8a). **Calibration (indirect, no monitor pin):** bench sweep of the 8 codes in fast mode (4 MHz, boost, N 1024) with inputs at −0.9, 0 and +0.9 FS from an external VREF divider; choose the lowest code whose 3-point bow and gain error are within 10 % of the plateau (high-code value). Basis: the ADC is ratiometric, so the bias shows only through settling; INL rises about 2.2 × per 0.5 V/µs below the knee (s5h) and one trim step ≈ 6 % ≈ 0.75 V/µs, so the knee is resolvable. The chosen code is stored per chip in the RP2040 firmware (flash) and rewritten after every rst_n | C6 tb + MC; broken copy: one trim leg open ⇒ monotonicity REJECT; PLAN V4b (calibration); golden v3 boost/trim vectors |
| Bias reference (C6, D42) | Start-up / PSRR / current / area | starts from VAPWR 0→3.0 V ramps (1 µs–10 ms) at ss/−40 and ff/125, no zero-current state (broken copy without start-up ⇒ REJECT); PSRR ≥ 40 dB DC on the output current; own current ≤ 6 µA; area ≤ 7,000 µm² | C6 tb; layout |
| Comparator | Offset / noise | ≤ 20 mV 3σ; ≤ 5 mV rms | INL 1 ppm, noise 0.3 µV; C3 MC ≥ 200 runs (3σ offset ≤ 20 mV, `.noise` ≤ 5 mV rms), broken copy: pair mismatch ×3 ⇒ REJECT |
| Comparator | Decision time | < 68 ns at 2 MHz (< 34 ns at 4 MHz) for \|Vin\| ≥ 1 mV, worst corner | tb |
| Comparator | Single bit (F8) | one retimed FF output drives DAC switches and decimator; y[0] forced at reset release | construction + test; RTL TB drives the junk `comp_raw0` at cycle 0 and through the reset window (golden README), broken copy y0 pass-through ⇒ REJECT |
| Comparator | Kickback | ≤ 5 mV on x2, recovered before next sample (gain only, 3.8 ppm/mV) | gain reserve; C3 tb with pass number: peak disturbance on x2 ≤ 5 mV and recovered within 0.5·t_half at 4 MHz ss/−40; broken copy: isolation removed ⇒ REJECT |
| Input switches | Settling | (Ron + 500 Ω + R_src)·(5 pF + Cs) ≤ 18.75 ns; Ron max over 0…VREF+ at ss/−40/3.0 **incl. body effect** ≤ 1.5 kΩ | INL 2 ppm; DC Ron sweep |
| Input (user-facing) | Source | no board cap: R_src ≤ 1 kΩ; with board cap (τ_pin ≥ T): sys-on CMRR = 1/(ΔR·fs·Cp,top) ⇒ ΔR (VIN+ vs VIN−) ≤ 250 Ω at 2 MHz at the allowed Cp,top 20 fF (330 Ω only if Cp,top ≤ 15 fF) (∝ 1/fs). Pin CM current ≈ fs·Cp,top·\|ΔVcm\|; offset ΔR·I **not** cancelled by sys chop | datasheet row |
| Reference | On-chip / board | on-chip τ_ref ≤ 10 ns; board decap ≥ 100 nF at ua2/ua3, DC R_ext ≤ 10 Ω per pin (u³ INL ≈ 1.4 ppm) | INL 2 ppm; C8 tb: τ_ref ≤ 10 ns at ss/−40/3.0 with the 500 Ω + 5 pF pad and 10 Ω R_ext, broken copy: reference switch Ron ×3 ⇒ REJECT |
| Reset | Residue / window | r ≤ 1e-4 on x1 and x2; window ≥ 2 clock cycles (≥ 1 µs at 2 MHz). **Settling gate (D46a): r ≤ 1e-4 within 2 fs cycles at 4 MHz boost (500 ns window) and at the slowest corner (0.25 MHz, 100 °C N 4096 / 125 °C N ≤ 1024), C1/C4 tb, every corner; if the margin is below 2 ×, add a reset-length config (2/4 cycles)** | offset 1 µV; inter-conversion memory test at 4 MHz boost and at 0.25 MHz (back-to-back ±0.9 FS; second result independent of the first); broken copy: window 1 cycle ⇒ REJECT |
| Virtual ground | Leakage | per vg node (per side), sign stated (NMOS-only island switches ⇒ drift negative): **≤ 90 pA at ff/125/3.6** (0.25 MHz N 1024 stage-2 drift ≤ 0.2 V) and **≤ 20 pA at ff/100/3.6** (0.25 MHz N 4096, D39); signal-dependent ≤ 0.1 pA. Drift = I·N/(fs·C_side), C_side 4.76 / 2.01 pF | offset 1 µV; island CM rows; C4 PEX leakage tb |
| Capacitors | Matching / CMRR | Cs+/Cs− ≤ 0.75 % 3σ; Cp,top ≤ 20 fF/side; ΔCp,top random ≤ 0.25 fF 3σ, systematic (PEX) ≤ 0.08 fF; ε_inj ≤ 2.8e-4; gate \|sys\| + RSS(random 3σ) + \|ε_inj\| ≤ 1e-3 with ε_eff = ((Cp/Cs)·ε_Cs − ΔCp/Cs)/(1+Cp/Cs) + ε_inj (D36, D37) | S4 MC; C4/C10 PEX + MC |
| Clock | Phases | h = 0.5/fs, g = 0.025/fs, t_half = h − 2g = 0.45/fs (225 ns at 2 MHz, 112.5 ns at 4 MHz, 1.8 µs at 0.25 MHz); **g ≤ 0.025/fs at every corner, generated by the on-chip non-overlap delay generator, not by TT-clock ticks**; bottom-plate early phases | C4/C8 transient at 0.25, 2 and 4 MHz at every corner (g and t_half measured); broken copy: g = 0.05/fs ⇒ REJECT |
| Noise spec | Condition | at u = 0 (shorted input); reference noise is a board requirement | V9 only (system noise is a joint, tier-0-with-PEX result; no single block gate) |

**User decisions after S4/S5 (D27–D30):**
- Noise @15 SPS ≤ 2.5 µV at all corners for fs ≥ 2 MHz; at fs 0.25 MHz ≤ 2.5 µV up to 85 °C and ≤ 3.0 µV at 125 °C (D27). **fs 0.25 MHz with N 4096 is rated −40…100 °C only** (island leakage drift, D39); 0.25 MHz N ≤ 1024 keeps 125 °C.
- **Noise @240 SPS ≤ 5 µV rms** (D29).
- **Bias-boost config bit (D31, form per D39):** boost=0 (precision, fs ≤ 2 MHz, reset value), analog ≈ 106–113 µA incl. bandgap. boost=1 (fast mode,
  fs 4 MHz): OTA1 tail ×2, OTA2 tail ×2 (option A′, user 2026-11-09, D41; was ×1.5), gated on **absolute boosted loaded GBW**
  (OTA1 ≥ 20 MHz, OTA2 ≥ 22.5 MHz) and SR (≥ 25 / ≥ 27 V/µs) at every corner, gated as the boosted operating point (gm/Id at the boosted current density), analog ≈ 172 µA. **Analog current ≤ 200 µA
  in every mode.** The former GBW(boost)/GBW(nom) ≥ 1.9 gate is withdrawn (REVIEW-S5e C-M1: needs gm/Id ≈ 24, infeasible
  at OTA1 size); C1 may meet the absolute rows by input-pair sizing, SC CMFB or a larger OTA2 boost, inside 200 µA.
  Boost latched only at a pair boundary (C9); one switched bias leg (C6).
- Fast mode (4 MHz) INL: N 64 ≤ 200 ppm, N 256 ≤ 20 ppm, N 1024 ≤ 5 ppm (D28; confirmed with option A, D39); **gate: V3 at 4 MHz boost for N 256 and N 1024, repeated on PEX in V6**. Evidence (tier 1, s5h, option A′, O1/O2 converged, D43c; the earlier s5f numbers predate the solver ladder and are not cited): D39 control (option-A point, OTA2 20.25 V/µs ≤ A′ 27, conservative): 3.29 / 3.36 ppm O1 / O2, verdict 3.43 ppm; A′ N 1024 (c) cold / (d) hot 0.144 / 1.450 ppm, O2 only; A′ N 256 cold / hot 0.403 / 1.982 ppm, O1 only (gate 20) (labels per REVIEW-S7b m2; job names in `results/s5h_tier1.md`). C1 gates the **boosted operating point at every corner** (gm/Id at the boosted current density, REVIEW-S5f M1), not base × ratio. Closed: cold-corner over-speed (M2), OTA2 β2 / Cp_vg2 row (M3, row in §3.0), user chose A′ (OTA2 ×2, D41).
- **CMRR ≥ 100 dB DC (120 dB goal)** with sys chop on, **≥ 60 dB with sys chop off** (D30, D32; input CM 0…VREF). Definition: CMRR = \|ΔVin_cm/ΔV_os\|, least-squares slope over Vin_cm {0.2, 1.0, 2.0} V at fixed mismatch, N 4096 (sys off raw offset, sys on pair-demodulated). Evidence: S4 sys off 61.5 dB; sys on cites tier-1 cm2 137–173 dB (O0 numbers, quasi-static: exempt from the O1/O2 convergence rule, D43c; the model's ≈ 205 dB is a symmetric-mean metric, not a silicon figure). Risk: 60 dB sys-off needs CM→diff ≤ 0.1 % — Cs+/Cs− matching alone gives ≈ 0.75 % 3σ at 0.5 pF, so the D12 input-switching topology must reject CM to first order independent of cap matching (C4 owns; broken copy: D12 CM-rejecting input switching removed ⇒ sys-off CMRR below 60 dB REJECT).

Allocation after review: INL 8 (OTA) + 2 (input settling) + 2 (ref settling) + 1 (comparator) + 1 (quant floor) + 2 (ref
current) + 4 (reserve: MIM VCC, charge injection, substrate) = 20 ppm. Gain: A0 300, settling 500, k/c1 50, reserve 4150 ppm.
Noise and offset allocations unchanged from s3_budget.md. MIM total ≈ 9,000 µm² (12 % of 2×2 tile).

### 3.1 OTA (first integrator — the critical path, no TT precedent) (informative; §3.0 governs. SR 10 V/µs, PM 60° minimum and β 0.75/0.61 below are the pre-S3 values; current values: SR 12.5/13.5 V/µs, PM informational, β1 0.84, β2 0.497)
| Parameter | Target | Derivation |
|---|---|---|
| Topology | Fully differential, PMOS input pair, with CMFB | PMOS for lower 1/f |
| DC gain A0 | **≥ 80 dB** (v1, user Q6; 75 dB gave 71 ppm at VREF 2.048/c1 0.25 and failed the 1.5× INL margin); 90 dB (stretch) | §2.3, for ≤100→≤30 ppm INL |
| Output-swing linearity | gain drop ≤ ~90% at max excursion; characterise g_m vs Vout | dominant INL mechanism |
| GBW (OTA) | **≥ 10 MHz required, 20 MHz design target** at fs=2 MHz (scale with fs) | see settling below |
| Phase margin | 60° minimum (pre-S3; superseded: PM informational in §3.0, step settling gates) | SC stability |
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
GBW 10 MHz / SR 10 V/µs. **Closed (user Q2, D28):** 4 MHz = fast/low-resolution mode with its own INL target, or spec the
OTA at fs_max (GBW ≥ 20 MHz, SR so slewing ≤ 20 % of t_half then ≥ 10τ). Tier 1 (S5) gets OTA GBW/SR terms.

Second integrator: same topology, relaxed gain/noise (its noise divides by first-stage gain).

### 3.2 Comparator (1-bit quantiser) (informative; §3.0 governs)
| Parameter | Target | Notes |
|---|---|---|
| Topology | StrongARM latch + SR/retiming FF. **One retimed FF output drives both the DAC switches and the decimator** (review F8: first decision after reset has x2 = 0, so it is metastable every conversion; DAC/decimator disagreement ⇒ ≈4/N FS error, sporadic) | optional: force y[0] digitally |
| Offset | ≤ ~20 mV tolerable | incremental loop + first-integrator gain suppress it to input; design modest, don't over-spend |
| Noise (input-ref) | ≤ few hundred µV | divided by integrator gain at input |
| Decision time | < 0.3·t_half | fits within clock phase |
| Kickback | minimise (preamp or isolation) | corrupts integrator state |

### 3.3 Switches (informative; §3.0 governs)
| Switch | Type | Spec |
|---|---|---|
| Input sampling | **3.3 V TG (complementary)**, sized for τ ≤ t_half/12 at **ss/−40 °C/3.0 V** incl. 500 Ω pad + source (review m4), bootstrapped only if block sims show need | with bottom-plate sampling and full settling, Ron nonlinearity does not matter: TG ~1 kΩ × 1 pF ⇒ τ ≈ 1 ns vs 250 ns t_half. A bootstrap adds 3.3 V device stress risk and sim effort (first-cut rule) |
| Integrator / feedback | TG (complementary) | Ron < ~1 kΩ; bottom-plate with dummy switches |
| Chopping / DAC | TG | matched, charge-injection cancelled |
| Sampling scheme | **Bottom-plate** mandatory, stray-insensitive integrator | bottom-plate: signal-independent charge injection; stray-insensitive topology: offset/1-f gain ≈ 1 |

### 3.4 Capacitors (MIM `cap_mim_m3_1` only; no MOS caps in signal path) (values per §3.0, S7-M4)
| Cap | Value | Note |
|---|---|---|
| Cs1 (sample, int1) | **0.5 pF** (D22) | = DAC cap (1-bit DAC reuses Cs) |
| Cint1 | **4 pF** | c1 = Cs1/Cint1 = 0.125 (option B, Cs 0.5 pF) |
| Cs2 (sample, int2) | **0.5 pF** (§3.0) | C_side2 2.01 pF, β2 0.497 |
| Cint2 | **1 pF** | c2 = Cs2/Cint2 = 0.5 |
| Ck2 (k-DAC cap, int2) | **0.25 pF** (= k·Cs2, on full VREF; shares the OTA2 virtual-ground node, D25) | Ck2/Cint2 = c2·k = 0.25 |
| PGA caps | none in v1 (shared Cs); stretch: binary Cs for ×2/4/8 | matching-limited gain error |
| Density | ~2 fF/µm² (confirm in PDK) | total core caps ×2 (diff) ≈ (0.5+4+Cs2+Cint2)·2; with stage 2 at 0.5/1 pF plus Ck2 0.25 pF ≈ 12 pF (≈ 6,000 µm²; MIM total with all caps ≈ 9,000 µm², §3.0) (~10 % of tile); stage-2 sizing in S3 |
| Layout | common-centroid, guard-ringed | matching + substrate isolation |

### 3.5 Reference / 1-bit DAC (informative; §3.0 governs)
- 1-bit DAC: switch Cs between +VREF / −VREF ⇒ **inherently linear** (mismatch ⇒ gain error only).
- External VREF buffered off-chip; on-chip reference settling τ_ref ≤ 10 ns (§3.0 row; = 0.044·t_half at 2 MHz, 0.089·t_half at 4 MHz; gain error only; C8 tb).
- Reference loading through the 500 Ω pad gives **gain error only** for settled SC (not INL).

### 3.6 Clocking
- 2-phase non-overlapping + delayed phases for bottom-plate sampling.
- fs from programmable divider off the TT clock (0.25–4 MHz).
- Chop clocks: **system chop** toggled at conversion/reset boundaries (digital, 4 switches);
  **OTA chop** at fch = fs/2 (D45 i; 1 MHz at 2 MHz, above the 631 kHz 1/f corner (info), 125 kHz at 0.25 MHz where the 1/f corner is not a gate).
- **Chop decision (user D4 = DECISIONS D18, 2026-11-07): keep OTA chop as a config bit, always paired with system chop**;
  system chop alone is the fallback. S2 (results/s2_chop.md): OTA chop alone leaves lf·Vos/(N−1) (closed form,
  model agrees 54/54), so it is never used alone; sys / ota+sys offset ≤ 0.8 µV at Vos 9 mV; ota+sys cuts
  240 SPS noise 1.2–14× vs sys alone.
- **Sequencing rules (S2, binding on C9):** system-chop swap only at conversion boundaries; integrators and
  sampling caps reset between swapped sub-conversions; **N even**; OTA-chop phase restarts at the same value at
  cycle 0 of every sub-conversion; sub-conversions averaged in pairs (alternating polarity, same N and fs).
  Additional rules from review (REVIEW-S1S2 m2): (7) OTA-chop state during the reset window identical every
  sub-conversion; (8) sys-chop swap on the pin side, ahead of sampling and CM-rejecting switches (only errors
  after the swap cancel); (9) one retimed y drives DAC and decimator, y[0] forced at reset release; (10) config
  changes (N, order, chop enables, fs divider, short, boost, trim) latched only at a pair boundary, first pair after a change tagged
  invalid; (11) decimator accumulators cleared on the same edge that releases the analog reset; frame carries
  the chop sign and frame_ctr (frame_ctr[0] marks slot a/b; there is no separate pair counter); (12) reset window = 2 fs cycles (≥ 1 µs at 2 MHz) and covers ≥ ~15 τ of Cint discharge (1 kΩ × 4 pF = 4 ns, so 15 τ ≈ 60 ns) + post-swap input
  settling + OTA/CMFB recovery (gate: reset residue r ≤ 1e-4, row "Reset", D46a); the +−−+ pair ordering is dropped from v1 (§3.7a b).
  (13) **OTA-chop edge placement (REVIEW-S7 m4):** with fch = fs/2 a chop edge may fall only in a non-overlap interval (g), never in a phase where Cs2 samples x1 while OTA1 is held.
- **OTA chop scope (review E2/M3):** chopper on **OTA1 only** (OTA2 1/f is divided by c1(N−1)/2, its offset
  cancels with sys chop). OTA chop stays in v1 **only if the C1 OTA meets A0 ≥ 80 dB and settling with the
  chopper switches in place, chopping and parked**; otherwise drop it (sys-only meets the ≤ 2.5 µV @15 SPS target even at lf 9.3).
- **Modes without system chop are characterization-only:** they carry lf·Vos1/(N−1) (order 2; lf·Vos1/N order 1)
  plus 2·Vos2/(c1(N−1)) from OTA2 offset (52.7 µV at Vos2 9 mV, c1 0.125, N 4096: 1.5·2·Vos2/(c1(N−1)), the 1.5 from Ck sharing the OTA2 node, §3.0).

### 3.7 Decimator (digital, on-chip — must live in the macro)
- Order-2 **cascade-of-integrators**: 2 accumulators + counter; reset each conversion (incremental).
- Order-1 mode: single accumulator for the result (acc1); acc2 keeps accumulating ΣS (§3.7a f). Structure (REVIEW-S7 m3, model assumption): in order 1 the comparator senses x1 directly and int2 is held in reset; reconstruction u = acc1/N (golden `den` = N).
- Accumulator width: acc2 max = N(N−1)/2; N=4096 ⇒ 8,386,560 < 2²³−1 ⇒ signed 24-bit fits (margin 2047); use 32-bit.
- Accumulator convention bound to the model: **exclusive S** (`acc2 += acc1` before `acc1 += y`). An inclusive
  RTL acts like k/c1 = 5 (≈2/N gain error); golden vectors (S6) pin the convention (review m2).
- Precision reconstruction for verification (review F9): u = (ΣS + (k/c1)·S + x2[N]/(c1·c2)) / (N(N−1)/2) is exact;
  transistor-level INL checks use it with x2[N] read from the sim.
- Output: **raw accumulators** (acc1 = S, acc2 = ΣS; 32 b each) read as 16-bit words over the parallel bus of §3.8a (D46b); firmware forms
  u = (acc2 + (k/c1)·acc1) / (N(N−1)/2), so no on-chip divider. The **raw bitstream**, `valid` (= frame_ready) and bit clock are on the bus in debug mode (§3.8a).
- **Frame tags (review F4):** each frame carries (tag word) chop sign, order, N code and a frame counter, so firmware
  demodulates system chop correctly even if a frame is dropped.
- **System-chop swap only inside the reset window**, never mid-conversion; integrators fully reset between
  swapped sub-conversions (reset residue r ≤ 1e-4 at every N, row "Reset" of §3.0 and D46a; the earlier 2.2e-3 at N 1024 and 1.4e-4 at N 64 are superseded).
- `valid` (= frame_ready) means a complete frame is in the hold register; `invalid` (tag) means do not use it (§3.7a c, e). They are independent.
- 1.8↔3.3 V level shifters between analog macro and digital.

### 3.7a Digital conventions bound to the S6 golden vectors (D45, REVIEW-S6 §5). **(e), (g) and (i) are user-confirmed (D46a)**; (i) is gated by the reset-settling row of §3.0
| # | Item | Rule |
|---|---|---|
| a | Forced y[0] | y[0] = +1 at reset release. The cycle-0 comparator output (and anything it outputs during the reset window) is ignored. The forced bit drives the DAC, the decimator and the raw bitstream pin from one retimed FF (F8) |
| b | Chop-sign order | sub-conversion slot parity: even slot = +1 (direct), odd = −1 (swapped). The +−−+ ordering of rule (12) is dropped from v1 |
| c | Frame layout | per frame: acc1 (32 b, two's complement), acc2 (32 b), then a 16-bit tag word, MSB first: `chop` (1 b: 0 = +1, 1 = −1; **with sys_en = 0 the tag chop bit is 0 in every slot**, as the golden vectors implement it: the swap never happens, so both frames of a pair read 0), `order` (1 b: 0 = order 1), `n_code` (2 b: 0..3 = N 64/256/1024/4096), `sys_en`, `ota_en`, `short` (1 b each), `invalid` (1 b), `frame_ctr` (8 b, +1 per sub-conversion, wraps 255 → 0, never reset by config changes, reset to 0 only by rst_n). No pair_idx: frame_ctr[0] marks slot a/b. `frame_ready` (status[15]; debug uo[2]) marks a complete frame. The `invalid` tag marks frames not to be used. The two are independent |
| d | Config latch | writes go to a shadow register. The shadow is copied to active on the clock edge that starts the reset window of an even slot. A write on or after that edge applies to the next pair. The last write before the edge wins. Latched set: order, N, fs divider, sys_en, ota_en, short, **boost (1 b, reset 0), trim (3 b, reset 100)** (D31, D42; §3.8a register map) |
| e | Invalid scope (user-confirmed, D46a; also applies to a change of boost or trim) | both frames of the first pair after any change of the latched set, **and** the first pair after rst_n release (start-up: CMFB, decap, bias) |
| f | Order-1 acc2 | keeps accumulating ΣS exactly as in order 2 (defined value, not don't-care); firmware ignores it |
| g | OTA-only chop | (ota_en 1, sys_en 0) allowed, characterisation-only like every sys-off mode (D4: never used for data). Direct measurement of the lf·Vos1/(N−1) residue: golden vectors with this mode already exist (`chop_mode` ota); PLAN row V4a runs it at transistor level |
| h | PGA | none in v1; the config field is removed |
| i | Reset window / OTA chop timing | reset window = 2 fs cycles (row "Reset", ≥ 1 µs at 2 MHz), with the sys swap, accumulator clear and y force inside it. Accumulators clear on the edge that releases the analog reset (rule 11). OTA chop runs at fch = fs/2: its phase toggles every fs cycle and is 0 at conversion cycle n = 0 (c = 2) of every sub-conversion, and 0 throughout the reset window (c = 0, 1) (rule 7) |
| j | Output frame | accumulators are emitted in the modulator frame, with no sys sign applied on chip; firmware applies the chop tag and demodulates pairs |
| k | Cycle level (WO-18, golden v2) | a slot is N + 2 fs cycles: the reset window is cycles 0–1, and conversion cycle n = c − 2. `sys_swap` changes on cycle 0 and is held for the slot. `acc_clear` is high on cycle 1, so the clearing edge is the one that releases `rst_analog`. `y_force` is a 1-cycle strobe at n = 0. `raw_pin` = 0 while `bit_valid` = 0. OTA-chop phase = 0 in reset, then n mod 2. Config write timing: a write at offset 0 of an even slot (on the edge) goes to the next pair; a write in the last cycle of the previous slot latches. A write equal to the active config is not a change (no invalid flag). An applied short forces u and the offset to 0 |

### 3.8 Configuration & I/O
- Config register (serial write on ui_in, §3.8a; shadow register, §3.7a d): order (1/2), N, fs divider, OTA-chop en,
  system-chop en, internal short, **boost (1 b, reset 0, D31/D46c), bias trim (3 b, reset 100, D42)** (no PGA field: no PGA in v1, D45h).
- I/O pin map, read bus, buffering and register map: §3.8a.
- **Internal-short input mode** (mux VIN to CM) — required to measure the ADC's own noise floor.
- ua3 is VREF− (D24). An integrator/supply monitor would need ua4, a 5th analog pin at €100 (pins cost €40 each for the first two, then €100 each). Not in v1 (D47); leakage observability comes from the internal-short mode instead.

### 3.8a Digital I/O (WO-19, D46b; proposal for coordinator review, golden v3 items marked G3)
Assumed TT clock **clk = 48 MHz**. TT pins: `ui_in[7:0]` in, `uo_out[7:0]` out, `uio[7:0]` all outputs (uio_oe = 0xFF), `rst_n`, `clk`; analog `ua0-ua3` unchanged (§1).

**Pins**
| Pin | Dir | Function |
|---|---|---|
| `uo_out[7:0]` + `uio[7:0]` | out | 16-bit read bus: bus[15:8] = uo_out, bus[7:0] = uio. Value = word selected by `addr` (normal mode) or the debug signals (below) |
| `ui_in[2:0]` | in | `addr[2:0]`: 0 = acc1 hi (31:16), 1 = acc1 lo (15:0), 2 = acc2 hi, 3 = acc2 lo, 4 = tag word (§3.7a c), 5 = status, 6-7 reserved (read 0). Order = §3.7a(c) |
| `ui_in[3]` | in | `rd` frame-ack: `rd` goes through a 2-FF synchroniser and a rising-edge detect; the edge clears frame_ready and overrun **only if frame_ctr is unchanged since the last status read** (otherwise a load between the status read and the rd edge would clear a new, unread frame; in that case the clear is suppressed and the new frame stays flagged). Word reads need no strobe (`addr` is a combinational select of the hold register) |
| `ui_in[4]` `[5]` `[6]` | in | `cfg_clk`, `cfg_dat`, `cfg_ld`: serial config write (below) |
| `ui_in[7]` | in | `dbg`: 1 = debug bus |
`ui_in` is fully allocated (8 of 8: addr[2:0], rd, cfg_clk, cfg_dat, cfg_ld, dbg). The bias trim has no dedicated pins; it is a field of the config register (D47).

**Debug mode (`dbg` = 1).** uo_out[0] = raw bitstream y (after the forced y[0], §3.7a a; 0 when bit_valid = 0), [1] = bit_valid, [2] = valid (= frame_ready), [3] = fs bit clock, [4] = rst_analog, [5] = sys_swap, [6] = ota_chop_phase, [7] = invalid (of the hold-register frame); uio[7:0] = status[7:0] (frame_ctr). The bus signals are synchronous to clk; y changes on the **falling** edge of the exported bit clock (half an fs period of setup), so a logic analyser samples the bit stream on the rising edge of the fs bit clock.

**Status word (addr 5)**: [15] frame_ready, [14] overrun, [13] cfg_pending (shadow differs from active), [12:9] boost and trim **of the frame in the hold register** (boost = [12], trim = [11:9], latched with the hold register, D48(4)), [8] 0, [7:0] frame_ctr of the frame in the hold register.

**Buffering.** The accumulators and tag are captured into a **hold register at the end of every slot** (the clock edge that ends the last conversion cycle, c = N + 1, which is also the start of the next reset window; the accumulators clear on the reset-release edge of the next slot, c = 1, §3.7a i, k). `frame_ready` is set at the load and cleared by a `rd` edge. If a load happens while frame_ready is still 1 the hold register is overwritten with the newest frame and **overrun** is set (cleared by `rd`); the dropped frame shows as a frame_ctr gap (§3.7a c, golden `seq_drop`). A read that straddles a load is detected by reading the status word last: if overrun is set or frame_ctr differs from the tag word's frame_ctr (word 4), discard the frame.

**Read timing.** Frame = 5 words, plus status = 6 reads. Shortest slot = (N + 2)/fs = 66 cycles / 4 MHz = **16.5 µs** (N 64 at 4 MHz). 6 reads in 16.5 µs = 2.75 µs per word, i.e. the host needs a word rate of **≥ 0.36 Mword/s** (addr write, ≥ 3 clk = 62.5 ns settle, 16-bit read). That is trivial for an RP2040 PIO/DMA or C loop (≈ 1 µs for all six words) and not reachable from MicroPython bit-banging (≈ 10 µs per word): at fs = 4 MHz use N ≥ 256 (64.5 µs slot) with MicroPython, or the raw bitstream (debug mode) with firmware decimation for N 64 (REVIEW-S7 §8). Slot lengths at N 4096: 2.05 ms (2 MHz), 16.4 ms (0.25 MHz). **The host must read every frame** (PIO/DMA, or N ≥ 1024 with MicroPython at 4 MHz): a host whose read takes 1–2 slots can end up reading only even or only odd slots, which gives no complete chop pairs.

**Config write (serial).** 16-bit shift register, MSB first: `cfg_dat` is sampled on the rising edge of `cfg_clk`; a rising edge of `cfg_ld` copies the shift register to the **shadow register** (§3.7a d). `cfg_clk`, `cfg_dat`, `cfg_ld` are synchronised to clk (2 flops) and `cfg_clk` must be ≤ clk/4 = 12 MHz; `cfg_dat` is stable around the edge for ≥ 2 clk. A short shift (fewer than 16 clocks) before cfg_ld loads the last 16 bits received. The write time counts as the write cycle of §3.7a(k).

| Bits | Field | Meaning | Reset |
|---|---|---|---|
| 15:13 | reserved | write 0 | 0 |
| 12 | order | 1 = order 2, 0 = order 1 (tag `order`) | 1 |
| 11:10 | n_code | 0..3 = N 64 / 256 / 1024 / 4096 | 3 |
| 9:7 | fs_div | 0 = clk/12 = 4 MHz, 1 = clk/24 = 2 MHz, 2 = clk/48 = 1 MHz, 3 = clk/96 = 0.5 MHz, 4 = clk/192 = 0.25 MHz, 5-7 reserved (treated as 1) | 1 |
| 6 | sys_en | system chop enable | 1 |
| 5 | ota_en | OTA chop enable | 1 |
| 4 | short | internal short (VIN to CM) | 0 |
| 3 | boost | bias boost (fast mode, fs 4 MHz, D31/D41); reset 0 | 0 |
| 2:0 | trim | bias trim code, binary, 100 = mid (D42) | 100 |
All fields of rows 12:0 are in the latched set of §3.7a(d); a change of any of them makes the first pair invalid (§3.7a e). The fs_div table needs the 48 MHz TT clock: **50 MHz does not divide to 4 / 2 / 1 / 0.5 / 0.25 MHz** (clk/12 = 4.17 MHz, clk/24 = 2.08 MHz, and so on: fs would be 4 % high and the settling and noise gates are not rated there).

**rst_n.** Asynchronous assert, synchronous release. While low: analog reset held (rst_analog = 1), config shadow and active registers at the reset values above, accumulators and hold register cleared, frame_ready = overrun = 0, frame_ctr = 0 (reset to 0 only here, §3.7a c). On release the first slot starts on the next fs edge; the first pair is `invalid` (D45 e: CMFB, decap, bias start-up). **The trim is volatile (no NVM or fuses on TT): firmware rewrites the whole config, including trim, after every rst_n**; until then the chip runs at reset values (trim 100, boost 0).

**Golden v3 items (G3; golden files unchanged in WO-19).**
1. Config set gains boost and trim: vectors and `config` fields, tag unchanged (boost/trim are status-word fields, not tag bits), invalid-after-change scope includes both (S7-M2).
2. Config reset values and the fs_div code table at clk = 48 MHz (golden holds `fs_div` as a code; the table above fixes its meaning).
3. Status word, hold register and overrun semantics: `seq_drop` gains an overrun flag expectation, frame_ready set/clear by `rd`.
4. 16-bit word order of the frame readout (addr 0-4) and the debug-bus signal list: RTL-level tests, golden `wire` is the concatenation of words 0-4.
5. The OTA-only chop mode vectors already exist (`chop_mode` ota); add a transistor-level V4a row (PLAN), no golden change.
6. Status word [12:9] reports the boost/trim of the frame in the hold register (D48(4)): vectors carry the per-frame boost/trim.

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
| Thermocouple (type-K) | 41 µV/°C, ~52 mV span, CJC | needs PGA ×4/×8 (stretch, not v1); **CJC off-chip** (external RTD/thermistor on a second conversion) — no on-chip temp sensor in v1 | good at stretch |
| Shunt / coulomb counting | µV offset critical | system chop <1 µV offset | plausible, floor-limited |
| Entropy-source recovery | fast mode + raw pin + self-noise subtract | N=64–256, raw bitstream, internal-short | secondary result |
| Load cell / bridge | ~50 nV rms | — | out of reach v1 (needs ~×128 LNA) |
| ECG / EEG | ≥500 SPS, ≥2.5 MΩ Zin, <5 µV | rate is fine (~2 kSPS at N=1024); noise at that rate (~2–5 µV floor, more with coupling) and ~1 MΩ Zin are the limits | out of reach |

Input impedance to publish: Zin ≈ 1/(fs·Cs) ≈ 1 MΩ/side at 1 MHz, 1 pF — buffer high-Z sources.

---

## 5. Open items: closure map (REVIEW-S7 E20)
Items 1-8 of the original list are closed or owned elsewhere; none blocks the freeze.
1. VREF vs swing: **closed**, VREF 2.048 V with c1 0.125 / k 0.5 (D17, S1).
2. OTA-chop weighting in incremental mode: **closed**, OTA chop paired with system chop (D18, S2); OTA-only is characterisation-only (D45 g).
3. OTA 1/f re-characterisation: **owned by C1** (row "1/f, chopper"; system level in V9).
4. PGA gain-error budget: **closed (withdrawn)**, no PGA in v1 (D14, D45 h).
5. Accumulator widths and word format: **closed**, §3.7 and §3.7a (c), 2 × 32 b + 16 b tag, read as 16-bit words (§3.8a).
6. OTA-chop-only residual: **closed**, lf·Vos1/(N−1) (S2); measured by V4a.
7. Comparator kickback and offset: **owned by C3** (MC and tb rows of §3.0).
8. §3.1 sim parameters into iadc.py: **closed** (S3/S4 joint model run).
**No ua4 / extra analog pin in v1 (user, D47).**

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
PGA in v1** (PGA ×2 moves to stretch). **Q6 → OTA A0 ≥ 80 dB.** **D17 (user D3) → option B (VREF 2.048 V, c1 0.125, k 0.5). D18 (user D4) → keep OTA chop paired with system chop.** Defaults accepted (D21): Vos 9 mV, order-1 characterization only, overload recovery.
Cs 0.5 pF (D22), N 4096 precision (D23). REF− on ua3 (D24, user OK).

## Change log (post-freeze)
| Date | Section / row | Change | Reason | Decision |
|---|---|---|---|---|
| 2026-11-09 | §3.0 OTA1 A0 / A(v), boost | **CL-1 (P1).** boost=1: A0 ≥ A_floor and A(v) ≥ A_floor − 5 dB at every corner. A_floor comes from a tier-0 INL-vs-A0 scan at N 1024, 4 MHz, with 1.5× margin to 5 ppm (≈ 72 dB expected), **plus** the in-loop gate (B) at the hot corners. Precision mode keeps A0 ≥ 80 dB. The A_floor number goes into the row when the scan lands; until then the row is pending. The §3.6 "OTA chop only if A0 ≥ 80 dB" rule is re-checked for boost | A plain FC cannot reach 80 dB in boost at hot corners (≈ 69–75 dB after the M1 fix, REVIEW-C1a); finite-gain INL ∝ N/A, so N 1024 at 5 ppm needs less gain than N 4096 at 8 ppm. Gain boosters rejected (P2): fast mode would reach ≈ 196–204 µA | D51 |
| 2026-11-09 | §3.0 Input CM / CMFB row | **CL-2 (P4).** Cs2 x1-side plates shorted in OTA2's integrate phase; CM kick ≤ 10 mV (text in the row) | Tying them to V_ICM kicks −79 mV, 4–8× the CMFB tolerance (REVIEW-C1a) | D51 |
| 2026-11-09 | §3.0 OTA1 GBW row, gate (B) corners | **CL-3 (P5).** ss/125/3.0 and fs/125/3.0 (boost) added to the (B) corner list | The lowest loaded GBW is at hot (21.8 MHz ss/125 boost), not ss/−40 (REVIEW-C1a M6) | D51 |
| 2026-11-09 | §3.0 OTA1 GBW row, β1 | **CL-4 (P3).** β1 ≥ 0.83 (Cp_vg ≤ 0.32 pF per side). Rev B design value: Cp_vg ≈ 0.23 pF (pair Cgg 137–189 fF plus ≈ 4 fF of 3.3 V switch), so β1 ≈ 0.846. The wider pair keeps W·L, so Cgg is unchanged | Input gate C 0.18–0.20 pF per side plus chopper switches; −1 % β·GBW is negligible and (B) uses the real Cp | D51 |
| 2026-11-09 | §3.0 OTA1 rows; C4 | **CL-5.** vg chopper and vg island switches are 3.3 V devices (`nfet_g5v0d10v5`, NMOS-only at vg ≈ 1.2 V) on level-shifted 3.3 V clocks, **closed by default while rst_n is low or the bias is invalid**. This bounds vg at power-up and replaces any tail clamp | A `nfet_01v8` at 1.62 V drive is off (Ron 62 MΩ–1e15 Ω); a tail clamp cannot conduct below 3.7 V; the "gates high" fault is reachable through Cint at power-up (REVIEW-C1a M4/M5, WO-21) | D52 |
| 2026-11-09 | §3.0 OTA1 Slew row | **CL-6.** SR is still gated at C_L = 1.4 pF; the row now states the itemised real load (0.78 / 0.90 pF), so SR on the real load is ≥ 20 V/µs | C_L had not been itemised (REVIEW-C1a m1); clarification, no number changed | D52 |
| 2026-11-09 | §3.0 Bias distribution row | **CL-7.** Boost-toggle bias settling relaxed from "within the reset window" (500 ns at 4 MHz) to "0.1 % within ≤ 0.25·T_slot,min (≈ 4 µs)"; the toggle pair is invalid | Boost is in the latched set, so the first pair after a toggle is invalid (≥ 33 µs). Integrators and islands reset every slot, the CMFB settles in under 1 µs, and the thermal effect is negligible (REVIEW-C1a-revB Q3). Saves ≈ 7–9 µA in fast mode (≈ 187–189 µA instead of ≈ 200–206) | D53 |
| 2026-11-09 | §3.0 OTA1 A0 / A(v), boost (restates CL-1) | **CL-1b.**<br>• Boost: gated by model INL using the **measured secant A(v) table** at every PVT point, N 1024 at 4 MHz, ≤ 5/1.5 = 3.33 ppm, plus the in-loop gate (B) at the CL-3 corners. Boost A0 becomes a health row; no fixed A_floor.<br>• Precision: keeps A0 ≥ 80 dB **and** its table-INL gate, now run at N 1024 **and** N 4096.<br>• Table rules:<br>  – range ±1.8 V diff, or until A < 40 dB;<br>  – steps ≤ 0.05 V above 0.8 V;<br>  – both signs, symmetric within 0.5 dB;<br>  – raw curves saved;<br>  – measured with the real SC CMFB.<br>• The model REJECTs on table extrapolation.<br>• Broken copies, per mode and corner (CL-1c/CL-1d):<br>• boost INL gate: PMOS cascode D–S short at ss/125/3.0 boost ⇒ REJECT;<br>• precision INL gate: (i) a synthetic known-answer table, the S4 droop shape anchored at 76 dB (8.51 / 8.31 ppm at N 1024 / 4096), ⇒ REJECT at both N, and (ii) a circuit droop copy at ss/125/3.0 base, predicted at ≥ 1.5× the gate, ⇒ REJECT;<br>• precision A0 row: PMOS cascode short ⇒ REJECT.<br>m_pl L 0.5 is kept as a sensitivity row | The WO-22 A0 scan: with the S4 droop shape, N 1024 reads 5.37 ppm at 80 dB A0, yet flat 60 dB passes. The droop shape sets INL, so a fixed A0 floor can neither pass nor fail correctly (REVIEW-C1a-revB Q4) | D53 |
| 2026-11-10 | CL-1b broken copy | **CL-1c.** The required broken copy for the table-INL gate becomes "PMOS cascode drain–source short" (A0 ≈ 52 dB ⇒ REJECT). m_pl L 0.5 is kept as a sensitivity row | m_pl L 0.5 only moved boost INL from 2.43 to 3.02 ppm against 3.33, so it could not show the gate works (WO-23 run 3) | D55 |
| 2026-11-10 | CL-1c broken copies | **CL-1d.** The broken copies are now set per mode and per corner (text in the row). A flat gain loss cannot fail an INL gate, so the precision INL gate gets a droop-type copy plus a synthetic known-answer table, and the flat-loss copy moves to the precision A0 row | WO-23 run 5: the PMOS short is blind at tt base (3.37 ppm < 5.33). Flat 60 dB gives only 1.47 ppm (WO-22). REVIEW-C1a-revC RC-M3. Makes the check stricter, nothing relaxed | D56 |
| 2026-11-10 | §3.0 Bias distribution row (D43b) | **CL-8.** The vbpc cascode-bias leg has its own boost increment (×1.75, or ×1.4 with K_P base 10) instead of ×2, because K_P differs per mode (base 8–10, boost 7). tb12 covers both toggle directions, tb11 covers current. Broken copy: base K in boost ⇒ ss/125 span 1.355 V ⇒ REJECT | Wide-swing margin needs a larger K in moderate inversion at base current (REVIEW-C1a-revC RC-m1) | D56 |
| 2026-11-11 | §3.0 OTA1 Slew row | **CL-9.** The SR floor is re-based on the knee: SR − 3σ ≥ 10.3 V/µs base and ≥ 20.6 V/µs boost at 1.4 pF. 12.5 / 25 V/µs stay as the design point. Knee per mode: base 10.23–10.28 V/µs (O2, N 1024, 2 MHz, share 1.333 ppm, D44 / r3); boost 20.6 V/µs = 2 × the base knee (the tier-1 boost point scales gm, SR, fp2 and t_half together; taken at the base share, conservative against the boost share 3.33 ppm). Gate B (fs/125 boost): nominal 26.9 V/µs → 2.17 ppm, sr95 → 51 956 ppm; near-knee copy srknee at 0.8 × the boost floor (16.5 V/µs) checks the floor (WO-32). The I_tail ceiling stays a power row; the C6 reference window the rows allow is an info row; the D47 3-bit trim centres the reference | 12.5 V/µs was 1.22 × the knee and, with the ceiling, left an I_REF window of about −2 % / +1.6 % against ±10–20 % untrimmed (REVIEW-C1b-final M1). The knee-based floor opens the low side to about −19 % | D65 |
| 2026-11-11 | §3.0 Input CM / CMFB row (text) | **CL-10.** "≤ 10 mV in 0.2·t_half" → "≤ 10 mV at the sampling instants (end of each half-phase)" | The 0.2·t_half limit was a proxy; D63 judges the CM at the instants Cs2 and the integrator use (REVIEW-C1b-final m4) | D63, D65 |
| 2026-11-11 | §3.0 Input CM / CMFB row | **CL-11.** (a) Start-up: CM settled before the first valid conversion (the dummy conversion); tb9 gate: CM at the ph2 sampling instants within 10 mV of its steady state by 4 µs. The output start-up clamp is a transmission gate (0 µA). (b) CM-to-DM: only the signal-dependent part counts (a constant CM-induced DM offset cancels in endpoint INL); per-sample bound 0.1 × the 5 ppm boost share × 2·c1·VREF = 0.256 µV, checked on a 3σ mismatch copy (Cs, Cint, Cc, Cr p/n, input pair ΔV_T) at DM levels ±0.486 V and 0 (DESIGN.md 2.12) | The old start-up row read the steady ph1/ph2 ripple (m3); the PMOS-only clamp was weak at V_OCM (m7); the CM-to-DM row could not fail on the symmetric netlist (M2) | D65 |
