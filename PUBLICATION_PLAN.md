# PUBLICATION_PLAN.md — Characterization paper for tt-iadc (incremental ΣΔ ADC, sky130A)

Status: draft plan, pre-silicon. Rev 2026-11-07b: review fixes (custom carrier PCB, die count, PSRR feasibility, thermal EMF, entropy section optional, AN1154 figure unverified). Purpose: design the experiment backward from the paper so that
when silicon returns there is nothing to decide — only data to take. Written to double as a
**reusable characterization template** for analog on an open PDK (sky130A / Tiny Tapeout), with the
incremental ΣΔ ADC as the worked example.

---

## 0. One-line thesis (the claim referees judge)

> An open-source, silicon-characterized incremental ΣΔ ADC on the sky130A PDK, presented with a
> complete, reproducible characterization methodology and open datasets, and validated against a
> pre-silicon behavioural model — demonstrated on its best-fit application (ratiometric temperature
> sensing), with secondary modes (DC/ratiometric monitoring, thermocouple/shunt, and analog
> entropy-source recovery).

Novelty is **open reproducibility + measured-vs-modelled correlation on an open PDK**, not circuit
performance records. Say this plainly; do not claim SOTA specs.

---

## 1. Framing options (pick one as primary)

| Framing | Primary contribution | Best venue | Risk |
|---|---|---|---|
| **A. Characterization methodology/template** (recommended) | A reusable, documented flow to characterize analog ΣΔ on an open PDK; tt-iadc is the vehicle | WOSET, ORConf/FOSSi, IEEE Access, MDPI Electronics | Low — survives even a mediocre chip |
| B. Application paper (temperature) | A sky130 open ratiometric temperature front-end with measured °C resolution | Sensors (MDPI), I2MTC | Needs the temp result to be good |
| C. Entropy-source instrument | ADC as open-silicon entropy-source characteriser (recovery fidelity, SP 800-90B on real data) | WOSET + a security workshop | Needs clean entropy data |

Recommendation: **A as the paper, with B and C as two of its result sections.** A is robust to a
weak chip because the *method and the measured-vs-model correlation* are the product; even null or
modest specs are a valid, publishable outcome in the open-hardware context.

---

## 2. Best-fit application and the spec targets to report

Anchor on **ratiometric temperature sensing** (external/ratiometric VREF, no bandgap). Report the
full spec sheet at the design's data rates; mark v1 (commit) vs stretch.

| Parameter | v1 target | Stretch | Best-fit app meaning | How reported |
|---|---|---|---|---|
| Architecture | 2nd-order CIFB incremental, 1-bit, c1=0.25/c2=0.5 | + 1st-order fallback | — | schematic + sim |
| Resolution (N=1024, order 2) | ~16 bit | 20 bit (N=4096) | temp/DC | noise-free bits |
| Input-referred noise @ 15 SPS | ≤ 50 µV rms | ≤ 5 µV | ~0.5 °C (Pt100) → 0.05 °C | shorted-input histogram |
| INL | ≤ 100 ppm | ≤ 30 ppm | linearity over range | DC transfer sweep |
| Offset (after system chop) | < 1 µV–few µV | — | DC accuracy | shorted-input mean, chop on/off |
| Gain error | calibratable (~−460 ppm sim) | — | ratiometric cal | precision DC sweep |
| Offset/gain drift | report ppm/°C | — | temp stability | thermal chamber |
| PSRR / CMRR | report measured | — | supply/CM immunity | injected tone / CM sweep |
| Power (analog) | ≤ 200 µA | — | — | supply current |
| Data rates | 3.75/15/60/240 SPS + fast (N=64–256) | — | temp slow; TRNG/waveform fast | all tables swept vs rate |
| Area | 2×2 tile (~75k µm²) | — | — | layout |
| Pins | ua0=VIN+, ua1=VIN−, ua2=VREF, (ua3=monitor) | — | — | — |
| Dies characterized | all received dies (report per die + spread) | ≥ 5 | die-to-die claims | per-die tables |

Reference app numbers to cite for context (**AN1154 figure not yet re-verified against the app note — check before citing**): MCP3421 class (18-bit, 10 ppm INL,
2.048 V ref); Microchip AN1154 gives 111.6 µV/°C for Pt100 ratiometric with 2 V ref and 6.8 kΩ bias;
type-K Seebeck ≈ 41 µV/°C.

---

## 3. Characterization methodology (the core of the paper)

This is the reusable template. Every measurement lists: what, why, how, equipment, and the figure it
feeds. Run **all** of it with the **same analysis code** used for the model (single source of truth).

### 3.1 Test setup (report in full for reproducibility)
- **Reference source:** low-noise precision source (AD5791-class) or ratiometric bridge; battery
  power to break ground loops; shielded enclosure.
- **Carrier:** a **custom low-noise carrier PCB** for all µV / INL / PSRR measurements (Wulff tt06-sar: noise much
  better on his own PCB than on the demo board). The ETR dbv3 demo board is for bring-up and functional checks only.
- **Capture:** RP2350 (demo board or carrier); log raw accumulators AND the raw 1-bit bitstream pin.
- **Checks before data:** demo-board pull-downs and errata (a demo-board pull-down has killed analog
  amplitude on prior TT silicon); verify the <500 Ω / <5 pF pad path; confirm clock path (proven to
  62–100 MHz on TT).
- **Conditions:** nominal, then VDD ±10%, and temperature points (0/27/60 °C min) in a chamber.
- **Supply control:** PSRR and VDD ±10 % need control of VAPWR/VDPWR. Confirm the demo board allows an external
  supply; otherwise the carrier PCB provides it.
- **Sample size:** TT returns few chips. Characterize every die received; report per die and the spread; state N.

### 3.2 Static / DC (primary, incremental ADC is a DC machine)
1. **Input-referred noise & noise-free resolution** — use the **internal-short** input mode (external shorts add
   connector thermal EMFs of ~µV/°C); repeat with an external short to show the board's contribution; collect ≥10k conversions per
   data rate; report rms noise, peak-to-peak, noise-free bits (`log2(FSR / (6.6·rms))`), ENOB_DC.
   *Feeds: noise-vs-rate figure; this is the ADC's own floor for all later subtraction.*
2. **DC transfer / INL / DNL** — sweep a precision DC input across full scale (bipolar); fit
   end-point line; report INL/DNL in ppm and LSB. *Feeds: INL curve; the headline linearity number.*
3. **Offset & chop efficacy** — mean of shorted-input, chop OFF vs OTA-chop vs system-chop; show the
   offset collapse. *Feeds: chop bar chart.*
4. **Gain error & calibration** — two-point precision DC; report raw gain error and residual after
   1-point cal. *Feeds: gain/cal table.*
5. **Drift** — repeat 2–4 over temperature; report offset drift (µV/°C) and gain drift (ppm/°C).
6. **PSRR / CMRR** — inject a small tone on VDD / sweep common mode; report dB. *Feeds: immunity table.*
7. **Ratiometric verification** — vary VREF, confirm code tracks VIN/VREF (temperature-sensing claim).

### 3.3 Dynamic (secondary; reviewers still expect it)
8. **SNR/SNDR/SFDR/ENOB** — low-frequency coherent sine + FFT at the fast modes; note incremental
   caveats. *Feeds: FFT spectrum figure.*

### 3.4 Application validations (the "fits the best application" results)
9. **Temperature (primary):** Pt100 ratiometric front end; report measured °C resolution and
   accuracy vs a reference thermometer across range; single-point-cal result (AN1154 method).
10. **Thermocouple:** type-K with cold-junction compensation; measured error curve; note PGA usage.
11. **DC / shunt monitoring:** large-signal accuracy, offset-limited resolution.
12. **Entropy-source recovery (OPTIONAL — keep or drop decided before tapeout; `trng_recovery_study.py` does not
    exist yet; fast mode N=64 gives only ~8 b):** feed a known analog noise source; report
    recovery-ratio vs source bandwidth (vs N, fs), recovered PSD and histogram, per-sample
    min-entropy (SP 800-90B MCV) on captured codes, and the raw-bitstream path decimated off-chip.
    Always subtract the §3.2.1 shorted-input floor. State plainly: the bitstream is a *measurement*
    of entropy, never shipped as random bits.

### 3.5 Measured-vs-model correlation (the novelty glue)
13. Extract block params from transistor sims (OTA gain/swing/noise PSD/fc, settling, comparator
    offset) → feed into `iadc.py` → overlay predicted vs measured noise, INL, offset. Report the
    correlation and where the model was wrong (honest error analysis — this is the scientific core).

---

## 4. Figures & tables (the skeleton to fill with silicon)

Figures: (F1) architecture + chip micrograph/layout; (F2) measured noise vs data rate, model overlay;
(F3) INL/DNL curve; (F4) offset vs chop mode; (F5) drift over temperature; (F6) low-freq FFT/ENOB;
(F7) Pt100 measured °C error; (F8) entropy recovery-ratio & min-entropy vs bandwidth; (F9)
measured-vs-model scatter.
Tables: (T1) target-vs-measured spec summary; (T2) per-application results; (T3) comparison to
MCP3421-class and to prior TT ΣΔ (all 1st-order, none measured) — position as *open & characterized*,
not *faster*.

---

## 5. Paper outline
1. Intro — gap: open analog PDKs exist, but characterized analog ΣΔ silicon and a reusable
   characterization flow are scarce; prior TT ΣΔ are 1st-order and unmeasured.
2. Architecture — incremental 2nd-order, chopping, CoI decimator, config knobs, sky130 constraints.
3. Behavioural model — brief; it is the prediction being tested.
4. **Characterization methodology** — §3, framed as reusable template (the contribution).
5. Measured results — §3.2–3.4.
6. Measured-vs-model — §3.5.
7. Application fit & limits — honest envelope (temp/DC/TC good; load-cell/ECG/EEG out of reach because of
   noise at the needed rate and ~1 MΩ input impedance, not output rate).
8. Reproducibility — open design, datasets, scripts, BOM, procedures.
9. Conclusion + next shuttle.

---

## 6. Reproducibility package (ship with the paper)
- Design: schematics, GDS, LibreLane config, info.yaml.
- Data: raw bitstreams + captured codes per experiment (open dataset, DOI via Zenodo).
- Code: `iadc.py`, (`trng_recovery_study.py` if §3.4.12 is kept), analysis notebooks (same code sim + measurement).
- Docs: measurement procedures, test-bench photos, demo-board errata notes.

---

## 7. Honest risks / pre-registered outcomes
- **No silicon yet.** Next sky130 shuttle ~early–mid 2027; the paper cannot be submitted on sim alone
  for venues that expect measurement (declare sim-only clearly if submitted early to WOSET).
- **Chip underperforms specs.** Fine for framing A: a documented gap between model and silicon is a
  result. Pre-register the targets so a miss is a finding, not a failure.
- **Entropy section goes negative** (bandwidth-limited recovery). Publishable as a stated limitation;
  keep the temperature result as the positive anchor.
- **Scope creep.** Keep the paper to ONE primary app (temperature) + method; the rest are secondary
  result sections, not separate claims.

---

## 8. Immediate next actions (pre-silicon, doable now)
0. Execute the gated design plan in `work/v1-design/PLAN.md` (system → component → verification, all corners).
1. Lock `SPEC.md` v1 around the temperature anchor (external/ratiometric VREF, fast modes, raw pin,
   internal-short input for self-noise, defeatable chop).
2. Extend `iadc.py` with the fast-mode/TRNG study and the internal-short + PGA knobs.
3. Write the measurement procedures now (so the test bench is built before silicon).
4. Produce all F* figures from the *model* as "predicted" plots; silicon later overlays "measured".
5. Pre-register targets (T1) publicly in the repo.
