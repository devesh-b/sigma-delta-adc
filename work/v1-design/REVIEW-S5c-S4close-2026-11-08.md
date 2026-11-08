# REVIEW S5c (WO-09) + S4 close (WO-10/11), sd-adc-design-reviewer, 2026-11-08

Saved by the coordinator. The reviewer is read-only.
- Nothing was run.
- One ssh grep of `/home/mempool/regr/tt/WO-09/cm2.log`.

## Verdict
- **S5 closable with conditions:**
  - re-state the SR knee against an allocation (R1);
  - gate the island CM range (R7);
  - log the m4 bias (R9).
- **S4 closable with conditions:**
  - restore the sys-on test at N 4096 (R4);
  - split the C4 CMRR gate into systematic and random ΔCp (R5);
  - apply the SPEC rows in §10.
- WO-09 genuinely closed C-M1, C-M3 (within its scope), m1, m3, m7 and m9.
  - m6 closed in a better form than proposed.
  - m2 is only partly closed.
- No critical defect.

| Area | Status | Note |
|---|---|---|
| Separated knees (C-M1) | closed | knee threshold uses the whole INL budget (R1) |
| D12 residual + sign (C-M3) | closed for the linear lumped mechanism | ε_inj has no SPICE evidence yet |
| CMRR metric (m1) | closed (deck) | |
| CMRR gate non-vacuity (m2) | partial | removing D12 still passes every gate (R7) |
| Island drift (C-M4) | measured | stage 2 not gated (R6) |
| Pin path (m6) | closed | user-facing ΔR limit missing from SPEC (R8) |
| Xcheck (m3) | closed | m4 bias unexplained (R9) |
| S4 sys-on gate | trustworthy only as a floor | weakened test (R4) |
| D36 statistics | sound for the random terms | ΔCp,top is mostly systematic (R5) |

## 1. Correctness

### Major

**R1. The OTA1 SR knee is measured against the whole INL budget, not a slew allocation.** REASONED.
- **Problem.** The knee is defined as INL ≤ 13.3 ppm (20/1.5). The SPEC INL allocation has no slew line:

  | Line | ppm |
  |---|---|
  | OTA | 8 |
  | input settling | 2 |
  | ref settling | 2 |
  | comparator | 1 |
  | quantisation floor | 1 |
  | ref current | 2 |
  | reserve | 4 |

  The OTA line is already used by A(v): the S4 worst is 5.2 ppm at ss/125/3.0. That leaves ≈ 2.8 ppm, or ≈ 1.9 ppm after the 1.5× margin.
- **Knee at that share.** Log interpolation between grid points:
  - 2 MHz N256: 10.4 ppm at 9 V/µs, 1.33 ppm at 10 V/µs → ≈ 9.8 V/µs.
  - 2 MHz N1024: 8.79 ppm at 9 V/µs, 1.18 ppm at 10 V/µs → ≈ 9.8 V/µs.
  - The margin of 12 V/µs is therefore ≈ 22 %, not 35 %, and below the 25 % flag.
- **Not a failure.** 12 V/µs is the worst-corner minimum, and the tanh macromodel has a soft knee. The frozen row should still rest on the right basis.
- **Direction.**
  - Give slew its own INL line, e.g. 2 ppm from the reserve.
  - OTA1 SR ≥ 12.5 V/µs (≈ 27 % margin, ≈ +2 µA).
  - Confirm in C1 with A(v) and SR together, since INL is not additive (m5).

**R2. The OTA1-only-boost floor ≈ 12.9 ppm (4 MHz, N1024) comes from OTA2 small-signal settling (GBW), not OTA2 slew.** PROVEN from two deck rows; hand number REASONED.
- **Evidence.**

  | OTA2 config | INL |
  |---|---|
  | base SR 12 V/µs, boosted (24 V/µs, 20 MHz, fp2 scaled) | 4.23 ppm |
  | unboosted (25 V/µs, 10 MHz), OTA1-only boost | 11.8 / 12.9 / 13.2 / 12.9 ppm, flat across OTA1 SR 11–15 |

  The slew rates are the same, so the 3× difference is GBW (and fp2). `gen_tier1.py:245-252` scales gm, I and fp2 together with `bst`.
- **Hand check.**
  - τ2 = 1/(2π·0.61·10 MHz) = 26 ns.
  - At 4 MHz, after ≈ 45 ns of slew, ≈ 70 ns remain ≈ 2.7τ, so ε ≈ 7 %.
  - This matches the S4 fast table (OTA2 ε 7.5e-2 at GBW 10).
- **Direction.** In fast mode OTA2 needs loaded GBW ≈ 20 MHz. It does not need more SR. See §5.

**R5. D36 RSS treats ΔCp,top as zero-mean random, but in a real layout it is mostly systematic.** REASONED.
- **Problem.**
  - RSS of independent Gaussian 3σ terms is correct statistics. D36 is not a disguised relaxation for ε_Cs, nor for the random part of ΔCp.
  - A deterministic ΔCp,top seen in PEX must be added linearly.
  - If the full 0.25 fF is systematic: 4.81e-4 + 2.88e-4 + 2.8e-4 = 1.05e-3, i.e. 59.6 dB, which fails.
- **Bound.** (1e-3 − 8.41e-4)·Cs·(1+r) = 1.59e-4 × 0.52 pF, so **ΔCp,top,sys ≤ 0.08 fF** (0.4 % of 20 fF). That needs a mirrored layout.
- **The sign.** The confirmed "−" sign means the area-proportional part of Cp (ΔCp = Cp·ε_Cs) cancels exactly, which is favourable. For independent draws the sign is irrelevant to the RSS: independence, not the sign, is what justifies D36.
- **Direction.** C4/C10 gate:

  |ΔCp,sys(PEX)|/(Cs(1+Cp/Cs)) + RSS(3σ random terms) + |ε_inj| ≤ 1e-3 (60 dB), design target ≤ 5e-4.

**R6. Stage-2 island drift is reported but not gated; it is 2.37× stage 1.** PROVEN from the drift table.
- C_side2 = 0.5 + 0.25 + 1 + 0.26 = 2.01 pF.
- Stage-2 drift:

  | Case | Drift |
  |---|---|
  | 2 MHz, N4096 | 102 mV |
  | 0.25 MHz, N1024 | 204 mV (already > 0.2 V) |
  | 0.25 MHz, N4096 | 814 mV |

- So the "N ≤ 1024 at 0.25 MHz" mitigation does not fix stage 2.
- **Direction.** Gate both stages. Add an OTA2 input-pair CM row with its own drift term.

### Minor

**R4. The weakened S4 test (sys-on 99.4 dB at ΔCp 0.05 fF) is a metric floor, not physics.** REASONED mechanism; scaling PROVEN by arithmetic.
- **Where.** `model/tests/test_s4_corners.py` at d3ab346: two asserts reduced to sys-off only.
- **Mechanism.**
  - `cm_err_v` adds e = ε·dVcm in the modulator frame. The ±1 sys pair cancels it exactly to first order, by construction.
  - What remains is the change in residue-corrected reconstruction error when every input shifts by e. `_corr` (`s4_corners.py:160`) uses the ideal-loop residue formula, but the OTA has finite A(v), so a pattern-dependent error remains: ≈ 2.1 ppm FS ≈ 8.6 µV at N256 (S4 fast table, INL 2.09 ppm at N256).
  - At dVcm 0.8 V, 8.6 µV gives 99.4 dB. This matches the failing test.
- **Scaling.**
  - The floor scales as 1/N²: 8.6 µV × (256/4096)² = 0.034 µV, which matches the full-run sys-on errors of 0.002–0.07 µV.
  - The non-monotonic behaviour is the signature of a bit-pattern floor.
  - A real second-order term exists, e·d(g_even)/du ≈ e·1e-5 (sys-on ≈ sys-off + 100 dB). The symmetric-u mean cancels it, so the metric can't see it. It is harmless (≈ 160 dB).
- **Trust.**
  - The full-run sys-on ACCEPT (143–174 dB) is trustworthy only as "the model metric floor is ≥ 100 dB at N 4096". It is circular: it does not test the hypothesis.
  - The real evidence is tier-1 cm2 sys-on, 137–173 dB.
  - The flip broken copy still rejects sys-on, so the gate is not vacuous.
- **Direction.**
  - Restore the sys-on asserts at N 4096.
  - At N256, assert only an ε-independent bound (sys-on error ≤ 20 µV).
  - Label the S4 sys-on column "metric floor (hypothesis)".
  - SPEC states that sys-on CMRR is specified at N 4096.
- **Probe** (sandbox, ≈ 1 min):
  ```
  python3 -c "import model.studies.s4_corners as s;p=s.point('tt',27,3.3,2e6,N=256)[0];[print(e,s.cm_err_v(p,e*0.8,True)) for e in (0,1e-4,2e-4,4e-4,5.84e-4,8e-4)]"
  ```
  Repeat with N=1024 and with an ideal A(v). Expect ≈ 1/N² scaling, and ≈ 0 with ideal A.

**R7. m2 residue: no check fails when D12 is removed.** PROVEN from cm2.log.
- `nod12_ref` at 0.75 % mismatch gives sys-off 66.3 dB, which passes 60 dB.
- What D12 buys is CM range: vg1 CM [1.554, 1.728] V with D12 vs [0.673, 2.538] V without it. Nothing gates this.
- **Direction.** Add a cm2 check that vg1,cm stays within V_icm ± 0.15 V over Vin_cm 0.2–2.0 V. The nod12 copy must REJECT on it.

**R8. Pin path: the user-facing limit is missing.** PROVEN arithmetic on a form the deck confirmed within 2 %.
- With board cap (τ ≥ T), sys-on CMRR = 1/(ΔR·fs·Cp,top).
- 100 dB needs **ΔR ≤ 333 Ω** at 2 MHz, 15 fF (250 Ω at 20 fF).
- SPEC row 104 allows R_src ≤ 1 kΩ with a board RC ≥ 10 nF, which gives ≈ 90 dB at ΔR 1 kΩ.
- Row 104 still carries the pre-D12 pin current fs·Cs·(Vin_cm − Vref_cm). Post-D12 it is ≈ fs·Cp,top·ΔVcm (tens of nA).

**R9. m4 bias still open.**
- Deck INL is 26–39 % above the model (rel_sym 30–33 % against the 35 % tolerance, one-sided).
- Deck gain is 2–3 % more negative in every row.
- Roff 1e14 rules out the null floor.
- Suspect β: the deck has Cp,vg 0.26 pF, which the model β may lack (≈ 6 % on β). Check before relaxing or freezing the 35 % tolerance.

**R10. The D28 fast-mode INL targets were derived from the model under test.** That is a WORKFLOW "expected value from code" issue: S4 proposed N1024 ≤ 5 ppm as 1.5× the model's GBW-20 result. For reference, fast-mode N1024 resolution is 7.4 µV thermal + 18.7 µV quantisation rms. Treat the target as a user decision.

**R11.** SPEC requires GBW(boost)/GBW(nom) ≥ 1.9; the deck uses 2.0. The effect is negligible; state it.

## 2. WO-09 closure
- **C-M1: closed.** Threshold basis per R1.
- **C-M3: closed for the linear lumped model.**
  - The 0.0 % agreement is not suspicious. The deck is linear (ideal switches with Ron/Roff, linear caps, VCVS OTA), and the closed form is the exact charge-conservation solution of the same lumped circuit.
  - It is computed independently from parameters (`tier1_tb.py:874-878`, called at :906), not from deck outputs. The small residuals come from finite A0/Roff.
  - The sign test discriminates: in 8 cases the "+" form is off by 125–200 %.
  - Scope: it validates the algebra and the wiring. It does not cover TG injection (ε_inj, a third of the budget, no SPICE evidence), Cj(V) or routing. That belongs to tier-2/C4.
- **m1: closed** (slope metric, deck).
- **m3: closed.**
- **m6: closed** (settling-aware form; SPEC pad 179.6 dB at the floor; case B within 2 %).
- **m7: closed.**
- **m9: closed.**
- **m2: partial** (R7).
- **Drift:** the 0.0 % agreement is expected (ideal source into an isolated linear island). The implied C_side 4.76 pF and 2.01 pF match the parameters. The anchored contrast (85.9 mV) shows that the bleeders anchor nothing at 100 pA.

## 3. D36
- Sound statistics for independent random terms. Linear |ε_inj| is conservative.
- The rows are analytic, so the MC draw count does not matter. The worst draw (883 µV/V, ≈ 3.2σ) passes.
- The weakness is R5: classify ΔCp,top as systematic or random. With the R5 C4 gate, D36 is not a relaxation.
- Margin to the gate is +1.1 to +1.5 dB, so the 66 dB target depends entirely on C4 layout.

## 4. Drift mitigations, ranked
1. **Leakage spec with sign and node, plus a corner-aware CM row.** Recommended, cheap.
   - Leakage ≤ 100 pA per vg node (per side). SPEC.md:107 is ambiguous today.
   - NMOS-only switches on the island nodes are feasible at V_icm ≈ 1.2 V with 3.3 V gate drive. Leakage is then n+/psub only, so drift goes **down**, away from the PMOS tail-headroom limit.
   - Hot drift and cold headroom do not coincide: leakage is negligible at −40 °C, and V_SG is lower at 125 °C.
   - C1 impact: asymmetric linear range, checked at two corners:
     - upper limit at ss/−40/3.0, V_icm + 0.13 V, no drift;
     - lower limit at ss/125/3.0, V_icm − 0.13 − drift. This is easy for a PMOS pair.
2. **N cap at 0.25 MHz on the hot side.** It loses the 0.25 MHz/N4096 low-noise mode, and stage 2 still drifts 204 mV at N1024. Use it only if C1 can't absorb the downward drift.
3. **Accept the hot-corner drift, documented.** Equivalent to option 1 once C1 shows the pair stays linear; accepted risk without that evidence.
4. **Island CM refresh inside a conversion.** Not for v1.
   - A refresh injects CM charge, and mismatch makes it differential, which breaks the incremental state.
   - A per-cycle refresh undoes D12 (vg CM [0.67, 2.54] V without it).

## 5. SR / GBW / current
**Precision rows**
- OTA1 SR ≥ 12.5 V/µs diff, slower edge, every corner, C_L ≥ 1.4 pF, I_fold ≥ 1.2·I_tail.
- OTA2 SR ≥ 13.5 V/µs, reduced from 25.
  - knees3 gives 1.69 / 0.78 ppm at 12 V/µs (N256/N1024) and an 8 ppm knee at 8.1 V/µs, so 25 is over-specified at 2 MHz.
  - 13.5 also covers 4 MHz boost (2.18 ppm).
- OTA2 GBW ≥ 10 MHz into 0.7 pF.

**Current** (I_tot ≈ 3.4·SR·C_L)

| Mode | OTA1 | OTA2 | Comparator | Bias/CMFB | Total |
|---|---|---|---|---|---|
| Base | ≈ 60 µA (or the noise-set value if larger) | ≈ 32 µA | 6 µA | 20 µA | ≈ 118 µA |
| Boost OTA1 only | ≈ 120 µA | ≈ 32 µA | 6 µA | 20 µA | ≈ 178 µA |
| Boost both | ≈ 120 µA | ≈ 64 µA | 6 µA | 20 µA | ≈ 210 µA (over the cap) |

**Fast-mode options**
- (a) OTA1-only boost plus OTA2 loaded GBW ≥ 20 MHz at base bias (gm/Id ≈ 18, ≈ 4.7 µA per device; PM ≥ 60° in C1). ≈ 180 µA, inside the cap. Preferred. Needs one deck run: OTA2 unboosted, GBW 20 MHz, OTA1 boosted, N1024.
- (b) Fast mode at 3 MHz.
- (c) User raises the D28 N1024 target to ≈ 20 ppm. The current OTA1-only floor of 12.9 ppm passes.
- (d) Boost both and lift the cap.
- The 4 MHz OTA1 margins (19 % and 10 %) are fast-mode only and acceptable as informational.

## 6. Efficiency
- OTA2 SR 25 → 13.5 V/µs saves ≈ 28 µA in base mode (≈ 60 → 32 µA), ≈ 25 % of analog power. Evidence: knees3 OTA2 rows.
- Option (a) avoids boosting OTA2, saving ≈ 32 µA in fast mode against "boost both".
- NMOS-only island switches have smaller diffusion Cp than a TG, which helps both Cp,top and leakage.

## 7. Verification gaps (tasks)
- [ ] Restore the S4 sys-on asserts at N 4096. At N256, assert an ε-independent bound. Label the sys-on column as a floor (R4).
- [ ] Gate the vg1,cm range in cm2; the nod12 copy must REJECT (R7).
- [ ] Gate stage-2 drift; add the OTA2 CM row (R6).
- [ ] Re-derive the knees against a slew INL line (R1).
- [ ] Deck run: OTA2 GBW 20 MHz unboosted, OTA1-only boost, 4 MHz N1024 (R2).
- [ ] Explain the m4 bias (β/Cp,vg in the model) before freezing the 35 % xcheck tolerance (R9).
- [ ] Tier-2/C4:
  - ε_inj in SPICE with transistor TGs;
  - leakage split by sign (n+/p+ junctions) at ff/125/3.6;
  - PEX ΔCp,top split into systematic and random (R5).
- [ ] S4 n15 margin is +1 % at ss/125/3.0, 0.25 MHz (m8): log it as accepted risk or fix it.

## 8. What held up
- The D12 residual algebra and the "−" sign; the area-correlated part of Cp cancels.
- The drift closed form with the per-side leakage correction (D35c). The earlier 21/170 mV used 100 pA for the whole island.
- The settling-aware pin form. 1/(ΔR·fs·Cp) is correct only for τ ≥ T.
- RSS for independent terms. ε_Cs 3σ 0.75 % is consistent with the MIM mismatch model.
- Non-vacuity copies all reject:
  - ΔCp 2 fF: 48.3 dB;
  - SR 6 V/µs: 1623 ppm;
  - 10 nA leakage: −2.15 V.
- Island CM excursion −0.10/+0.08 V across Vin_cm 0.2–2.0 V, which confirms that D12 works for CM range.

## 9. Questions
1. What is the "50 mV row" in the drift table? It is not in SPEC.
2. Is ΔCp,top 0.25 fF meant as the random 3σ or the total? (R5)
3. Fast mode: which of options (a)–(d)?
4. Is the 0.25 MHz/N4096 mode needed at 125 °C, or only at room temperature?

## 10. SPEC §3.0 row text to apply
- **OTA1 Slew:** ≥ 12.5 V/µs diff, slower edge, every corner, C_L ≥ 1.4 pF, Cs2 sampling x1 in OTA1's hold phase (D25); I_fold ≥ 1.2·I_tail. Basis: tier-1 knees3 OTA1-only knee ≈ 9.8 V/µs at the slew INL share, margin ≥ 25 %. Boost: ≥ 2× base.
- **OTA2 GBW/slew:** GBW ≥ 10 MHz into 0.7 pF (base); SR ≥ 13.5 V/µs diff (knees3 knee 8.1 V/µs at 2 MHz). Fast mode 4 MHz: loaded GBW ≥ 20 MHz. The OTA1-only-boost floor of 12.9 ppm at N1024 is OTA2 small-signal settling.
- **OTA1 Input CM:** linear (A ≥ 75 dB) for v_g,cm ∈ [V_icm − 0.13 − ΔV_drift1, V_icm + 0.13] V.
  - 0.13 V = D12 CM step (cm2: −0.10/+0.08 V at Vin_cm 0.2–2.0, ±0.12 V at 0–VREF) + 10 mV CMFB.
  - V_icm is chosen in C1 for ≥ 0.2 V tail headroom at ss/−40/3.0.
  - Upper limit checked at ss/−40/3.0, lower limit at ss/125/3.0.
  - Same row for OTA2 with ΔV_drift2.
- **Leakage / drift:** island leakage ≤ 100 pA per vg node (per side) at ff/125/3.6, sign stated (NMOS-only island switches ⇒ drift negative); signal-dependent ≤ 0.1 pA.
  - Drift = I·N/(fs·C_side), with C_side 4.76 pF (stage 1) and 2.01 pF (stage 2).

    | Case | Stage 1 | Stage 2 |
    |---|---|---|
    | 2 MHz, N4096 | 43 mV | 102 mV |
    | 0.25 MHz, N1024 | 86 mV | 204 mV |
    | 0.25 MHz, N4096 | 344 mV | 814 mV |

  - The input-pair CM rows must cover it at the hot corner.
- **CMRR:**
  - Definition: CMRR = |ΔVin_cm/ΔV_os|, the least-squares slope over Vin_cm {0.2, 1.0, 2.0} V at fixed mismatch, N 4096. Sys off uses the raw offset; sys on uses the pair-demodulated offset.
  - Limits: sys off ≥ 60 dB (66 dB design), sys on ≥ 100 dB (120 goal).
  - ε_eff = ((Cp/Cs)·ε_Cs − ΔCp/Cs)/(1+Cp/Cs) + ε_inj.
  - Allocation:
    - Cp,top ≤ 20 fF/side;
    - ε_Cs ≤ 0.75 % 3σ;
    - ΔCp,top random ≤ 0.25 fF 3σ;
    - ΔCp,top systematic (PEX) ≤ 0.08 fF;
    - ε_inj ≤ 2.8e-4.
  - Combination: |systematic| + RSS(random 3σ) + |ε_inj| ≤ 1e-3.
- **Input source / pin path:**
  - No board cap: R_src ≤ 1 kΩ (SPEC pad, sys-on ≥ 179 dB, deck floor).
  - With board cap (τ_pin ≥ T): sys-on CMRR = 1/(ΔR·fs·Cp,top), so ΔR (VIN+ vs VIN−) ≤ 330 Ω at 2 MHz, scaling with 1/fs.
  - Pin CM current ≈ fs·Cp,top·|ΔVcm|, replacing fs·Cs·(Vin_cm − Vref_cm).
- **A(v) table:** static large-signal gain vo/vg (S5-3), not incremental.
  - Gating: ≥ 80/75 dB at |Vout,diff| 0/1.4 V.
  - S4 assumptions, to verify in C1: 70/60 dB at 2.0/3.1 V.
  - Gate: model INL with the simulated table ≤ 8 ppm (S4 worst 5.2 ppm).
- **OTA2 offset:** ≤ 9 mV 3σ. u error = 1.5·2·Vos2/(c1(N−1)) = 52.7 µV at 9 mV, c1 0.125, N 4096. The 1.5 comes from Ck sharing the OTA2 node (S5b). Constant; cancels in the sys pair.
- **Current:** ≤ 200 µA in every mode.
  - Base ≈ 118 µA: OTA1 ≈ 60 µA (= max(noise, 3.4·SR·C_L)), OTA2 ≈ 32, comparator 6, bias/CMFB 20.
  - Fast mode per the chosen option: OTA1-only boost ≈ 178 µA; boost both ≈ 210 µA (over the cap).

## 11. Evidence
- `work/v1-design/results/s5c_tier1.md`, `work/v1-design/results/s4_corners.md`
- `model/tests/test_s4_corners.py` (d3ab346)
- `model/studies/s4_corners.py`: lines 160, 340–398, 366–369
- `design/tier1/tier1_tb.py`: lines 874–878, 968–972, 346
- `design/tier1/gen_tier1.py`: lines 245–252
- `/home/mempool/regr/tt/WO-09/cm2.log`
- `SPEC.md`: lines 93–107, 122–123
