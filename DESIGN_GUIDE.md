# DESIGN_GUIDE — tt-iadc: the whole flow, decisions, trade-offs and verification in one place

Snapshot 2026-11-09 (SPEC through D42). This is a guide, not the spec:
- **SPEC.md** wins on numbers;
- **work/v1-design/DECISIONS.md** wins on history;
- this file explains *why*.

Each decision is tagged with its D-number so you can trace it.

---

## 1. Goal and constraints

| Item | Value | Why it matters |
|---|---|---|
| Goal | Learn by building a better ΣΔ ADC than prior Tiny Tapeout attempts (all 1st order, none with an on-chip decimator). Case-study target: MCP3421 (18-bit, 3.75–240 SPS) | Sets the bar: µV-level noise and ppm-level INL, at low speed |
| Process | sky130A, TT analog **2×2 tile** (334 × 225 µm ≈ 75,000 µm²), VAPWR 3.3 V, VDPWR 1.8 V, met5 forbidden | Area, devices and supply are all fixed |
| Pins | ua0/ua1 VIN±, ua2 VREF+, ua3 VREF− (D24) | Analog pins: €40 each for the first 2, then €100 each, so 4 pins = €280; a 5th (ua4) would be +€100 (none planned, D47) |
| Current | ≤ 200 µA analog in every mode, at every corner (D31, D42) | Couples speed, slew and bias to each other |
| Corners | tt/ss/ff/sf/fs (+ ss_hh, ff_ll) × −40/27/125 °C × 3.0/3.3/3.6 V × VDPWR ±10 % + MC (≥ 200 at tt, ≥ 50 at worst) × fs 0.25/2/4 MHz (D2, D7) | **A spec passes only if it passes at every corner** (D1) |

---

## 2. The flow: gated S → C → V, in Paul Thomas's style (D1)

```
S  system   (model tier 0 + behavioural SPICE tier 1)  -> SPEC v1 frozen
C  component (transistor tier 2, then PEX per block)    -> every block passes all corners
V  verification (top-level tier 2-3, PEX, non-vacuity)  -> tapeout
```

| Stage | Steps | Status (2026-11-09) |
|---|---|---|
| **S** | S0 infra · S1 VREF/swing · S2 chop · S3 error budget → per-block spec · S4 corner model · S5 tier-1 SC modulator in ngspice · S6 golden vectors · S7 SPEC freeze + review | S0–S5 closed (S5 through S5f; S5g running). **Next: S6, then S7** |
| **C** | C1 OTA1+CMFB (critical) · C2 OTA2 · C3 comparator · C4 switches + non-overlap · C5 choppers · C6 bias/bandgap/start-up · C7 level shifters · C8 reference input · C9 digital decimator (RTL) · C10 MIM arrays | not started |
| **V** | V1 assembly · V2 cold start · V3 DC transfer · V4 mode matrix · V5 mixed-signal bit-exact · V6 top PEX · V7 non-vacuity · V8 physical/precheck · V9 system re-proof with PEX parameters | not started |

**Simulation tiers**
- **Tier 0:** Python model (`model/iadc.py`). Fast enough for full corner sweeps and MC.
- **Tier 1:** behavioural SC modulator in ngspice (B-source OTA with gain, GBW, slew, swing; ideal switches). This is the bridge that checks the model against circuit physics.
- **Tier 2:** transistors.
- **Tier 3:** PEX.

**Why the gating:** long top-level transistor transients across 45 PVT points are infeasible in ngspice. So each block is proven at every corner on its own, and the top is checked at 5 extreme points with short windows (D2). The model carries the full corner sweep (V9).

---

## 3. Architecture decisions: what, why, pros, cons

| # | Decision | Why chosen | Pros | Cons / risk | Alternative rejected |
|---|---|---|---|---|---|
| A1 | **Incremental ΣΔ, order 2, CIFB, 1-bit** | Incremental mode gives a Nyquist-like converter with reset per conversion, which suits a multiplexed/DC sensor ADC (MCP3421 class). Order 2 is enough at OSR 1024–4096 | No idle tones across conversions; simple CoI decimator; 1-bit DAC is inherently linear | Needs a reset window and residue handling; the 1-bit quantiser loads the integrators | Order 1 (prior TT; too noisy for µV); order 3 (stability, area) |
| A2 | **c1 0.125, c2 0.5, k 0.5** (D3, D10, D17) | Both integrators at half swing (peak 0.61 V/side at VREF 2.048 V); same bitstream as c1 0.25 / k 1 | INL margin (12.4 vs 22.4 ppm at 1.2 V); OTA swing relaxed | Cint1 8 pF/side originally (area) | VREF 1.2 V / c1 0.25 |
| A3 | **VREF 2.048 V external, ratiometric 1.0–2.048 V** (D17, D24) | Keeps the MCP3421 full scale; ratiometric sensors (RTD) cancel the reference | No on-chip precision reference needed; REF− on ua3 Kelvin to the sensor ground | Board reference needs a buffer + ≥ 100 nF; pin cost | On-chip reference (noise and drift); chip-ground REF− (100 µV–10 mV error) |
| A4 | **Shared Cs (input = DAC cap), no PGA in v1** (D14, D22) | Matching-free gain; anchor application needs no gain | Gain set by ratios, not by absolute caps | No ×8 for thermocouples (stretch goal) | Separate caps + PGA ×2 |
| A5 | **Cs 0.5 pF, Cint1 4 pF** (D22) | Saves ≈ 4,000 µm²; noise still in budget | Area; OTA load | kT/C noise 0.54 → 0.76 µV at 15 SPS | 1 pF |
| A6 | **N 4096 precision, N 1024 for 240 SPS** (D23, D38c) | N 1024 leaves ≈ 33 µV deterministic quantisation error that averaging cannot remove | Precision modes are µV-clean | 240 SPS mode has a higher floor | N 1024 everywhere |
| A7 | **System chop mandatory + OTA chop as a paired config bit** (D4, D18, D19) | System chop cancels offset to µV at 3σ Vos; OTA chop cuts 240 SPS noise 1.2–14× | Offset ≤ 5 µV; 1/f suppressed | Two choppers to verify; chop phase must restart each reset | OTA chop only (leaves lf·Vos/(N−1)) |
| A8 | **D12: CM-rejecting input switching (top-plate shorting)** (D12, D25, D33) | Only differential charge transferred; input CM anywhere in 0…VREF | First-order CM rejection independent of Cs matching | Residual set by Cp,top and ΔCp,top (layout); per-cycle CM step at the OTA input | Matching-based CMRR (needs ε ≤ 0.1 %; MIM gives 0.75 %) |
| A9 | **CMRR gates: sys-off ≥ 60 dB, sys-on ≥ 100 dB (120 goal)** (D30, D32, D36, D37) | User: "the more the merrier" | Metric defined (least-squares slope over Vin_cm {0.2, 1.0, 2.0} V, N 4096) | Sys-off is 61.5 dB, only 1.5 dB margin; the 66 dB target rests on layout (ΔCp,top ≤ 0.15 fF) | 40 dB |
| A10 | **fs 2 MHz precision (0.25–2), 4 MHz fast mode with bias boost** (D13, D31) | Slew-then-settle INL at 4 MHz would force precision current up | Precision mode stays lean | Boost logic, latched at pair boundaries | Always-on 20 MHz GBW (+45 µA) |
| A11 | **Slew: OTA1 ≥ 12.5, OTA2 ≥ 13.5 V/µs (base)** (D39a, D44) | Tier-1 knee at O2: OTA1-only 10.23–10.28 V/µs (N 1024); OTA2 knee < 10.8 | OTA1 12.5 = 22 % over knee but INL 0.104 ppm (12.8× under share); OTA2 ≥ 25 % measured directly (10.8 → 0.756 ppm) | OTA1 under the 25 % rule (user accepted, D44); slew current dominates the OTA budget | 13 V/µs OTA1 (+2.4 µA precision, +5 µA fast, 0.02 ppm gain) |
| A12 | **Fast mode A′: OTA1 tail ×2, OTA2 tail ×2**; gate the *boosted operating point* (OTA1 ≥ 20 MHz / 25 V/µs, OTA2 ≥ 22.5 MHz / 27 V/µs) at every corner (D39b, D41) | gm grows slower than current in moderate inversion (×1.5 current gave ×1.28 gm), so "base × ratio" sizing builds unbuildable pairs | ≈ 172 µA nominal; small OTA2 pair; 33 % SR margin; β2 safe | INL trend vs GBW2 not yet explained (S5g); cold corner runs ≈ 1.5× faster | A (×1.5, needs L 0.5 µm and a large pair); relax N 1024 to 15 ppm |
| A13 | **1.8 V input pairs on 3.3 V** (D40a) | Better gm/Id and matching per area than thick oxide | Smaller pair, less Cgs → β | Device stress: every terminal pair ≤ 1.98 V over all transients (gate with a broken copy) | Thick-oxide pair |
| A14 | **Switched-capacitor CMFB** (D40b) | No static CMFB amplifier current (≈ 2.7·I_tail vs 3.4·I_tail) | ≈ 20 % analog current saved | Its caps load the OTA outputs (inside C_L); phases from the clock generator | Continuous-time CMFB |
| A15 | **Bias: current-mode bandgap + 3-bit trim** (D42) | Slew (∝ I) is the binding spec, so hold current constant. R spread ±15 % (+VBG, TC) ≈ ±20 % breaks 200 µA without trim (≈ 265 µA) | Flat SR over temperature; ≈ 189 µA worst-case after trim; trim sweep is a silicon experiment | +6–11k µm² (tile at 66–89 %); new block with start-up risk; code found on the bench | Constant-gm (SR falls at cold, same R spread); external resistor (pin) |
| A16 | **Island leakage ≤ 90 pA (ff/125), ≤ 20 pA (ff/100); 0.25 MHz/N 4096 rated to 100 °C** (D39c) | Drift = I·N/(fs·C); 0.25 MHz/N 4096 drifts 0.8 V at 100 pA. Junction leakage falls ×9.4 from 125 to 100 °C | Keeps the slow precision mode | Mode not rated at 125 °C | Cap at 85 °C; drop 0.25 MHz |
| A17 | **MIM caps only in the signal path** | MOS caps have percent-level C(V), which destroys INL | Linear, low leakage | No voltage-coefficient or bottom-plate model in the PDK (V9 risk) | MOS / MOM caps |
| A18 | **On-chip decimator (CoI)** | No prior TT ΣΔ had one; testable bit-exact | Self-contained ADC | Digital area 8–15k µm²; substrate coupling | Off-chip decimation |

---

## 4. Budgets (S3, SPEC §3.0)

| Budget | Target | Allocation / status |
|---|---|---|
| Noise | ≤ 2.5 µV @15 SPS, ≤ 5 µV @240 SPS | joint model 0.93 / 3.94 µV |
| INL | ≤ 20 ppm | OTA 8 + input settling 2 + ref settling 2 + comparator 1 + quant 1 + ref current 2 + reserve 4; joint 2.03 ppm |
| Offset | ≤ 5 µV | sys-chop pair −0.015 µV; leakage and reset residue budgeted as non-cancelling |
| Gain | ≤ 0.5 % | A0 300 + settling 500 + k/c1 50 ppm + reserve |
| Current | ≤ 200 µA, every corner after trim | precision ≈ 106–113, fast ≈ 172 nominal / 189 worst (incl. ≈ 6 µA bandgap) |
| Area | 75,000 µm² | 50–67k estimated (66–89 %): MIM 9k, OTAs 6–8k, bandgap 4–7k, digital 8–15k, ×1.4 analog overhead |

**Main trade-off chain:** INL needs speed. Speed needs current, since slew = I/C. Current hits the 200 µA cap. Noise needs Cs, and Cs needs area and slew current. Every row above is a lever on one or more of the others.

---

## 5. Verification strategy

1. **Green is not proof.** Every check has a **broken copy that must REJECT** (non-vacuity), e.g.:
   - S4: 8/8 broken copies (A(v) 60 dB, reset residue, sys chop off, Cs/100, slow input, swapped CM term, Cs mismatch 3 %, ΔCp 2 fF);
   - tier 1: no-D12, OTA1 at 8 V/µs, 10 nA leakage, no-Ck model.
2. **Cross-tier agreement.** The model and tier-1 deck must agree (xcheck ≤ 5 % rel_sym, currently 0.0–0.7 %). A disagreement is a finding, not a tolerance to widen. Example: the Ck loading bug was found when the deck/model ratio was 1.2–1.4.
3. **Theory checks.** Printed values are compared with hand calculations (ε_eff code = hand 8.407e-4; EKV vs gm/Id table within 1 %). Expected codes come from theory, not from the model's own post-processing.
4. **Every corner, MC rule.** Pass = μ ± 3σ inside spec **and** every sample inside spec. Independent random terms are combined RSS, systematic terms linearly (D36, D37).
5. **Frozen-copy acceptance.** Runs happen on a copy of the tree pinned to a commit (`/home/mempool/regr/tt/acc*-<sha>`), never on the working tree. Results are written as `results/ACCEPT-*.md`.
6. **Independent review at every milestone.** sd-adc-design-reviewer (Opus, read-only). Its findings become WOs, and its own wrong estimates are logged too.
7. **Analog false-pass list** (WORKFLOW §11): wrong metric, wrong frame, ideal parasitics (Cp,top = 0 gave a false 132–152 dB CMRR), simulator artefacts (default gmin 1e-12 added a flat 1.65 pA "leakage"), assumed scaling (gm ∝ I).
8. **Later stages:**
   - C: per-block testbenches at all corners + MC + PEX re-sim.
   - V: cold start (ALIVE), DC transfer at 5 extremes, mode matrix, mixed-signal bit-exact against the S6 golden vectors, top PEX acceptance, broken tops, TT precheck.

---

## 6. Corrections log (the thought process, in practice)

| Found | Wrong belief | Truth | Lesson |
|---|---|---|---|
| S5b review | SPICE CMRR 132–152 dB | Deck had Cp,top = 0 and the wrong metric | Parasitic-free decks prove nothing about CMRR |
| WO-10 | D33 linear sum of 3σ terms | Linear sum ≈ 4.2σ; RSS is correct (D36): 59.3 → 61.5 dB | Combine independent terms statistically |
| S5d/S5e | Sys-on "metric floor" (R4) | Sign/frame bug in the residue correction (C1) | When ideal-A error is not ≈ 0, suspect the code, not the physics |
| S5d xcheck | Model OK | Missing Ck load on stage 2 (×1.2–1.4 INL) | Cross-tier agreement catches model omissions |
| Leak sim | Flat 3–5 pA leakage | gmin artefact; real 0.7 pA at 100 °C | Check simulator floors before trusting small currents |
| S5e/S5f | Boost gives gm ∝ I; 5.3 ppm estimate | gm ratio 1.28–1.42; 7.6–12.5 ppm | Get device data (gm/Id tables) before sizing rules |
| S5e | 3 MHz result is a deck bug | OTA1 slew-limited (12.5 V/µs at 3 MHz ≈ 7.9 at 2 MHz) | Scale against known points before calling it a bug |
| S5f | "Raise base GBW" | Unbuildable pairs; gate the boosted operating point | Constrain the quantity that matters, not a bound on it |
| S5g/S5h | Tier-1 numbers at default solver options (O0) are final | O0 is unconverged in either direction (r1 6.7 → 18.8 ppm at O2; V4 0.56 → 0.32); gear damps settling at 10 ns steps | Run a solver ladder (O0 → O1 → O2) on every gated number; quote converged values |
| S5h smoke | Ladder chgtol ÷100 per step | chgtol 1e-16 with reltol ≤ 1e-4 aborts the decks | Smoke-test every new solver setting on 1 job first |
| S5g/S5h | OTA2 optimum at ζ = 1, PM window 75–82° | Optimum near ζ ≈ 0.9 (PM ≈ 72°) for both OTAs | Measure the window before writing it into SPEC |

---

## 7. Design strategy at the least token cost

How this project keeps the cost (agent tokens, sandbox time) low while staying rigorous:

1. **Model first, transistors last.** Tier 0 (Python) answers about 80 % of the questions (noise, INL, chop, budgets, corners) in seconds. SPICE is used only to validate the model (tier 1) or for physics the model can't hold (slew, CM, leakage).
2. **Hand calculation before every run.** Each WO states the expected result. A run that matches is cheap to accept; a mismatch is a finding. This avoids open-ended sweeps.
3. **Tiered agents with hard budgets.**
   - Opus reviews (high value per token).
   - Sonnet codes from a precise WO: file list, items, acceptance table, commit list, call budget, stop rule.
   - The coordinator runs acceptance directly (ssh + nohup) instead of with a polling agent.
   - Fresh agents from a handoff, never a bloated one.
4. **Decisions are written once** (DECISIONS D1–D42, SPEC) and referenced by number. Nothing is re-derived or re-litigated.
5. **Reuse existing data.** Reference TT layouts (bandgap area), PDK model files (R spread, tc1), and Paul Thomas's verification method all come from what is already published, not from new simulation.
6. **Batch and gate sandbox work.** One runner script per acceptance, load-gated (start only at load < 4), at most about 5 processes, logs plus an ALLDONE marker. No poll loops in agents.
7. **Ask the user only at real forks** (fast mode, bias type, temperature cap). Present 2–4 options with numbers and a recommendation; everything else uses logged, reversible defaults.
8. **Where tokens were wasted** (avoid next time):
   - an agent stalled on a tool lock;
   - a 30-minute coder wait on a busy sandbox (check load before dispatch);
   - two parse bugs in unrun code (run a 1-row smoke test inside the WO);
   - reviewer hand estimates later proven wrong (ask for a data point instead of an estimate when a deck run is cheap).

---

## 8. Status and open items

- **SPEC v1 is frozen** and the S → C gate passed on 2026-11-09 (D50, tag `spec-v1`). SPEC changes go through the change log.
- **Stage C order** is by risk:
  - C1 OTA1 + CMFB;
  - then C2 OTA2, C3 comparator, C4 switches/input, C6 bias (bandgap + trim), and the rest per PLAN.
- **C1 key gate:** the transistor OTA1 inside the tier-1 loop.
  - INL ≤ 1.333 ppm at 2 MHz;
  - INL ≤ 5 ppm at 4 MHz boost (D48).
- **Before C9:** golden vectors v3 (boost/trim, status word, read order).
- **Conditional at C6:** the bias-readback oscillator (D49), if area allows.

---

## 9. Where things live

- `SPEC.md` — numbers (§3.0 per-block table, §6 corners)
- `work/v1-design/PLAN.md` — stage gates
- `work/v1-design/DECISIONS.md` — the D-log
- `work/v1-design/results/` — evidence
- `work/v1-design/REVIEW-*.md` — reviews
- `work/v1-design/RESUME.md` — pickup steps
- `CONTEXT.md` — snapshot
- `SIZING.md` — first-cut sizing and area
- `WORKFLOW.md` — working rules
