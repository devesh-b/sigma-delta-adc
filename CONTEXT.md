# CONTEXT: full project context and learnings (snapshot 2026-11-07)

This is a single-file handoff. It records everything decided, learned and corrected so far, so a new session or person can pick up from here. Details live in the linked docs; this file is the map plus the conclusions.

---

## 1. Goal and framing
- **Project:** a sigma-delta ADC on **Tiny Tapeout, sky130A**. It is a **learning project, not a competition**.
- **Aim:** better specs than prior TT ΣΔ designs. Every prior design is 1st order, none is incremental, differential or chopped, and none has an on-chip decimator.
- **Case-study target: Microchip MCP3421** (18-bit ΔΣ, 3.75–240 SPS, 1.5 µV rms, 10 ppm INL, 2.048 V ref, PGA x1–8, I²C).
  - Verdict: "partially delulu". The architecture fits TT well. MCP3421 precision parity is not realistic on a first chip.
- **Working title:** "tt-iadc", an open, silicon-characterized, MCP3421-class incremental ΣΔ ADC.
- **Research angle:** an "experiment chip".
  - It is configurable: order 1/2, chop on/off, N, fs and a raw bitstream are all selectable.
  - It publishes measured-vs-sim correlation and open datasets.
  - It differentiates from Paul Thomas on resolution and DC precision, not bandwidth.

## 2. User preferences and working rules
- **First-cut silicon success over heroics.**
  - **No MOS caps in the signal path**: they are nonlinear and need too much simulation. Use MIM `cap_mim_m3_1` only. `m3_2` uses met5, which TT forbids.
  - MOS caps are fine for decoupling.
- Speed should be MCP3421-like (3.75–240 SPS) with the best precision possible.
- Scratchpad is `~/projects/tt`. Memory lives in `~/projects/tt/memory/`, and the index is also mirrored in `~/.claude/projects/-Users-alfadelta10010-projects-tt/memory/`.
- Added later (see `WORKFLOW.md`, `CLAUDE.md`):
  - **Run everything on the sandbox** (`ssh sandbox`, `scripts/sync-to-sandbox.sh`, `~/bin/rta-tt`); nothing runs locally.
  - "Doc" means Markdown and "report" means HTML.
  - Tiered lean agents.
  - Atomic git commits with no attribution trailers.
  - Green is not proof.
  - No Claude traces in the public TT submission repo.
  - Calm, factual framing.

## 3. Workspace map
| Path | What |
|---|---|
| `NOTES.md` | Prior-shuttle survey, gaps, SQNR formula, applications, max-frequency table (§2b), TT analog/PCB constraints |
| `MCP3421_TARGET.md` | Spec table, feasibility, verdict, spec tiers (v1 / v2 / parity) |
| `ROADMAP.md` | fs trade-off table, Paul comparison, research angle, v1 spec, Phases 0–5, risks |
| `SPEC.md` | **Design spec (source of truth for block targets)**: system, noise/INL budget, block specs, app mapping, open items, corner set §6 |
| `PUBLICATION_PLAN.md` | Characterization paper plan (framing A: method + measured-vs-model), measurements, figures, reproducibility |
| `work/v1-design/` | Gated design campaign: `PLAN.md` (system → component → verification, all corners), ledger, decisions |
| `SIZING.md` | Noise vs Cs vs N, quantization, OTA requirements, area budget, knobs, ranked challenges, first-cut simplifications |
| `ACHIEVABILITY.md` | Block-by-block evidence from cloned repos, Paul's 1/f data, sim feasibility, silicon lessons, scorecard, work breakdown, scope cuts |
| `model/` | Phase-1 Python behavioural model (`iadc.py`, `run_studies.py`, `README.md`, `out/` reports and plots) |
| `datasheets/` | `mcp3421.pdf` and `.txt` (DS22003E) |
| `data/` | TT shuttle index JSONs (`idx_*.json`, `root.json`) and `hits.txt` (ADC keyword matches) |
| `repos/sd-analog/` | ttsky-sigma-delta, **pthomas-sigma-delta-design**, **tt_um_tilesos_dual_adc**, tt_sky26a_analog_prj, ttsky26c_ns_sar_adc |
| `repos/sd-digital/` | TTSKY26A-ADC-8BIT (Sigma-Delta Bitstream ADC 8-bit), tt09-sigma-delta, tt06_jv_sigdel_v, tt02-adc-dac, ttsky25b-noise-shaping-ds-dac |
| `repos/decimation/` | tt09-decimation_filter (bmurmann, has an incremental mode), tt09-delta-sigma-decimation-filter, lime_cic_filter |
| `repos/adc-ref/` | **tt06-sar (Wulff, measured silicon)**, tt07-12bit_SAR_ADC, flash-adc |
| `repos/sd-ihp/` | analog-trial, Delta-Sigma-Comparator-Based-ADC (IHP SG13G2) |
| `pcb/` | tt-demo-pcb, breakout-pcb, tt-micropython-firmware |
| `WORKFLOW.md`, `.claude/agents/`, `scripts/`, `work/` | Process: rules, agents (`sd-adc-design-reviewer`, `rtl-verification-engineer`, `pd-expert`), sandbox sync, campaign state |

All repos are Apache-2.0 shallow clones (`--depth 1`).

## 4. Prior art: what exists
- **Analog ΣΔ on sky130 TT:**
  - All of them are 1st order.
  - None has on-chip decimation.
  - **None has measured silicon yet** (ttsky26a/c pending).
- **Paul Thomas (ttsky26c):**
  - 1st-order CT, single-ended, RZ resistive DAC, 50 MHz clock (needs a low-jitter FPGA clock), off-chip decimation.
  - Sim results: fast ~40 dB, precision ~57 dB SNDR (~9 ENOB).
  - Excellent methodology: DESIGN.md decision log, tiered sims, PEX gates in CI, test plan. **Copy the method and cite him.**
- **TilesOS:** 1st-order SC in a 2x2 tile, ~150 µA. **An 8192-bit ngspice transient could not complete** (VPP cap timestep failures).
- **Wulff tt06-sar:** the only measured analog ADC among the references.
  - **~7 ENOB measured vs 7.63 sim.**
  - Conversion was ~2× slower than sim.
  - Noise was much better on his own PCB than on the demo board.
- **Silicon lessons from Paul's survey:**
  - A design was dead from a missing via.
  - A demo-board pull-down killed analog amplitude.
  - The TT clock path is proven to 62–100 MHz.
  - Measured 1/f came in slightly below the sky130 sim.

## 5. Tiny Tapeout constraints (learned)
- **Analog pins:** `ua[0..5]` via `tt_asw_3v3`. The path is **<500 Ω, <5 pF, ≤4 mA**, with leakage and nonlinear Ron.
- **Supply:** VAPWR 3.3 V via `uses_3v3`; VDPWR 1.8 V.
- **met5 is forbidden**; power stripes go on met4.
- **Tiles:**
  - 1x2 is ~160×225 µm (36k µm²), **too small**.
  - 2x2 is ~334×225 µm (~75k µm²), the target.
- **Cost:**
  - €70 per tile.
  - Analog pins cost €40 each for the first two, then €100 each.
  - v1 uses 3 pins (VIN+, VIN−, VREF), about **€460** in total.
- **The TT mux selects one project at a time**, so the **decimator must live inside the analog macro**. That means LibreLane hardening and 1.8↔3.3 V level shifters.
- **Demo board:** currently ETR dbv3 with an RP2350; analog signals are on a 100-mil header. Check pull-downs and errata before measuring.
- **Shuttle:** ttsky26c closed 2026-09-07. The next sky130 run is probably early–mid 2027; check https://tinytapeout.com/runs.

## 6. Key technical learnings
### Architecture
- **Incremental ΣΔ:** reset every conversion, CIFB loop with delaying integrators, 1-bit quantizer, cascade-of-integrators (CoI) reconstruction. The CoI decimator is just 2 accumulators plus a counter, so it is tiny.
- **MCP3421 pattern:** 2^bits × rate ≈ 983 kHz, consistent with a 1st-order incremental converter (my inference).
- **Quantization:**
  - Order 1 gives ≈ log2(N) − 1 bits.
  - Order 2 gives ≈ 2·log2(N) − 4 bits, with scaled coefficients: **N=1024 → 16 b, N=4096 → 20 b.**
- **Loop coefficients:** use **c1=0.25, c2=0.5, k=1**.
  - The textbook 0.5/0.5 drives integrator 1 to ±1.85·VREF and integrator 2 to ±4.75·VREF, which clips and collapses resolution to ~4.7 b.
  - 0.25/0.5 keeps both integrators within ±1.2·VREF.
- **Plan:** 2nd order with N ≈ 1024 per *sub-conversion*. Average K sub-conversions digitally, with **system chopping** (input polarity swapped between sub-conversions). This reaches MCP3421-like low rates while keeping N small, which relaxes the OTA gain requirement.

### Speed (fs) trade-offs
- **SC switched at ~1–2 MHz is nearly jitter-immune**, so the RP2350 clock is fine. A CT design like Paul's is jitter-limited.
- **OTA power ∝ fs·C.** GBW of ~10–20 MHz is µA-level.
- **Input impedance ≈ 1/(fs·Cs):** 1 MHz with 1 pF gives about 1 MΩ per side.
- **Lower fs** means more cap leakage droop, which sets the minimum fs at ~10s of kHz.
- **1/f does not average with fs.** Chopping is the fix, and it must sit above the corner.
- **Chosen:** fs ≈ 1–2 MHz, programmable. 2 MHz gives ~1.4× lower noise at the same output rate.

### Caps and noise
- **sky130 MIM** is ~2 fF/µm².
- **kT/C averages over N:** v² ≈ kT/(C·N). **Cs 0.5–1 pF is enough**, so caps are small and thermal noise is not the limiter.
- **Paul's sky130 OTA noise** (PMOS pair 250 µm wide, `ngspice .noise`): **6.9 nV/√Hz white, 1/f corner 631 kHz.** `.tran` simulates zero device noise, so 1/f is invisible in transient sims.
- **Referral of slow errors:**
  - **Offset and 1/f refer to the input with gain ≈ 1** in a bottom-plate SC integrator.
  - The wideband noise gain (1 + Cf/Cs + Cp/Cs ≈ 5.3) applies only to white noise. *I got this wrong at first; see §8.*
- **Effective resolution** = log2(FSR/rms) with FSR = 4.096 V. For reference: 1.5 µV ≈ 19.6 b, 5 µV ≈ 17.9 b, 50 µV ≈ 14.5 b.

### Linearity and gain
- **Constant finite OTA gain** gives **gain error ≈ 1/A0**, which can be calibrated out. It does not give INL.
- **INL comes from gain that varies with swing.** With 90 % gain loss at full swing:

  | OTA gain | INL |
  |---|---|
  | 70 dB | ~120 ppm |
  | 80 dB | ~45 ppm |
  | 90 dB | ~19 ppm |

  So **≤100 ppm needs ~72 dB**, and **OTA output-stage linearity is a key spec**.
- **1-bit DAC:** inherently linear. Cap mismatch causes gain error only.
- **Settled SC (τ ≤ 0.2·t_half):**
  - Input/reference settling gives gain error only.
  - Reference loading through the 500 Ω pad gives gain error only. The IR-drop INL mechanism belongs to continuous-time resistive DACs.
- **Real INL risks not yet modelled:** signal-dependent switch Ron, charge injection, OTA swing nonlinearity.

### Simulation reality
- ngspice has **no PSS/pnoise**, and long transients fail (TilesOS).
- Full transistor-level noise/INL characterization is infeasible.
- **Tiered approach (Paul's):**
  1. Python model for the system.
  2. Transistor sims for block *parameters*: gain, swing, settling, offset, noise PSD.
  3. Short top-level runs.
  4. PEX spot checks.

## 7. Phase-1 model results (`model/`, run on the sandbox)
**Run:** `../.venv/bin/python run_studies.py [quant|gain|noise|settle|design|all]` from `model/`, about 1 min. Per the current rules, run it on the sandbox via `rta-tt`.

**Modelled:**
- order 1/2
- finite and swing-dependent gain, clipping
- kT/C
- OTA white + 1/f noise (Paul's numbers)
- offset, OTA chop, system chop, chopper residual
- `lf_gain`
- input/reference settling (shared or separate caps)
- comparator offset and noise

**Noise** (Cs = 1 pF, lf_gain = 1, fs = 2 MHz):
| Case | 240 SPS | 15 SPS | 3.75 SPS |
|---|---|---|---|
| kT/C only | 2.0 µV | 0.5 µV | 0.24 µV |
| + 1/f, no chop | ~10 µV | ~7 µV | ~8 µV |
| + system chop only | 3.8 µV | 0.7 µV | 0.3 µV |
| + OTA chop + system chop | 2.6 µV | 0.5 µV | 0.23 µV |

- System chop alone takes a **3 mV offset to below 1 µV**. It needs only digital logic and 4 switches, so **put it in v1**.
- The pessimistic bound (lf_gain = 5.3) gives ~40–60 µV unchopped and ~1–13 µV with system chop. That still meets v1.

**Candidate v1 design point:** fs = 2 MHz, order 2, N = 1024, Cs = 1 pF, A0 = 75 dB with 90 % swing drop, OTA + system chop, separate caps, τ_in = 20 ns, τ_ref = 10 ns, vos = 3 mV, vres = 5 µV.
- **Noise:** 2.51 / 1.31 / 0.51 / 0.26 µV at 244 / 57 / 15 / 3.74 SPS.
- **INL:** 71 ppm.
- **Gain error:** −459 ppm (calibrate).

**Model caveat: intrinsic floor only.** Not included:
- comparator/reference noise
- supply, substrate and clock coupling (TT neighbours, on-chip decimator)
- board noise
- switch charge injection and Ron

Also:
- The 1/f data is from Paul's specific input pair; re-characterise it for our OTA.
- The flicker generator is ~15 % low in variance.

## 8. Corrections made (mistakes I learned from)
1. **Noise gain:** I had applied the wideband noise gain (×5.3, or ×2.5 by hand) to offset and 1/f noise. The correct factor is ≈1 for a bottom-plate SC integrator, so **unchopped noise is ~7–12 µV, not ~30 µV.** Fixed in ACHIEVABILITY.md (note and scorecard), SIZING.md and memory.
2. **Reference INL:** I had claimed that the 500 Ω pad causes INL through reference loading. That is wrong for settled SC; it gives gain error only.
3. **Coefficients:** the textbook 0.5/0.5 clipped the 2nd-order loop; the fix is 0.25/0.5/k=1.
4. **Constant-gain model:** it was too optimistic for INL, so I added the swing-dependent gain model (`a0_drop`, `xswing`).
5. **Report label:** the design report's "offset" column was really the error at 0.1·VREF, gain error included. It is relabelled.
6. **Earlier hand quantization table** (SIZING §2, "2·log2N − 1"): ideal only. The model with scaled coefficients gives 2·log2N − 4.

**Environment gotchas:**
- `gh` is not installed; use the GitHub REST API via curl.
- zsh `--include` globs fail; use `find | xargs grep`.
- There is no pdftotext; use pypdf in `.venv`.
- Long clones need `run_in_background`.

## 9. v1 spec (draft, not yet locked; **`SPEC.md` is now authoritative**, this is a summary)
- **Architecture:** fully differential SC incremental ΣΔ, 2nd order with a 1st-order fallback mode, 1-bit.
  - Chopping switchable: OTA chop plus system chop.
  - Raw bitstream pin.
- **fs:** 2 MHz nominal (0.25–4 MHz). N ∈ {64, 256, 1024, 4096} (counter value, digital-only cost). K averaging in firmware.
- **VREF:** 1.2 V provisional vs 2.048 V with c1 = 0.125; decided by study S1. Model numbers were run at 2.048 V (µV noise and ppm INL carry over; −0.77 b effective at 1.2 V).
- **Targets:**
  - Noise: ≤50 µV @ 15 SPS (v1); ≤5 µV stretch. The model says ~0.5 µV intrinsic.
  - INL: ≤100 ppm; ≤30 ppm stretch.
  - Power: ≤200 µA analog.
- **Input and reference:** PGA x1/x2 (x4/x8 stretch). Input switch: 3.3 V TG (bootstrap only if sims demand). **External / ratiometric VREF.** No on-chip bandgap in v1, or one only as an optional experiment.
- **Output:** raw accumulators (up to 32 b) via shift register on `uo`, firmware divides; plus raw bit and data-ready. I²C is a stretch. CJC off-chip.
- **OTA GBW:** ≥10 MHz required, 20 MHz design target; slew ≥10 V/µs.
- **Sign-off:** every spec must pass at every corner in SPEC §6 (5 process corners, −40/27/125 °C, ±10 % supplies, MC ±3σ, fs 0.25/2/4 MHz), Paul-Thomas-style gates.
- **Physical:** 2x2 tile; `ua0` VIN+, `ua1` VIN−, `ua2` VREF; optionally `ua3` as an integrator monitor.
- **OTA:** 75 dB fully differential with CMFB. **This is the critical path, with no TT precedent.**

## 10. Achievability (scorecard summary)
| Item | Confidence |
|---|---|
| Working 2nd-order modulator with on-chip CoI | Med-High |
| 1st-order fallback | High |
| ≤50 µV | High |
| ≤5 µV with system chop | Medium |
| 1.5 µV (MCP3421) | Low |
| INL ≤100 ppm | Medium |
| INL 10 ppm | Low |
| Power | High |
| Fits a 2x2 tile | Med-High |

**Effort:** ~20 weeks part-time, and only with the scope cuts. For comparison, Paul spent ~9 intensive weeks on a simpler 1st-order design.

## 11. Phases and next steps
| Phase | Work | Duration | Gate |
|---|---|---|---|
| 0 | Foundations: reading (Schreier & Temes; Markus/Silva/Temes 2004), toolchain (IIC-OSIC-TOOLS Docker likely easiest on macOS; ciel, xschem, ngspice, magic 8.3.6xx, netgen, klayout, LibreLane, cocotb), TT analog template | 2–3 wk | template passes precheck |
| 1 | **System model** | — | **Done in first form**; still needs `SPEC.md` locked |
| 2 | Blocks: fully-diff OTA + CMFB (**critical**), chopper, StrongARM comparator, TG switches, non-overlap clock, bias/ref, level shifters. Corners + Monte Carlo | 5–6 wk | — |
| 3 | Top level + digital: CoI decimator, config, shift-out; cocotb with golden vectors from the model; hardened macro | 2–3 wk | — |
| 4 | Layout: common-centroid MIM, guard rings, DRC/LVS/PEX CI gates | 5–6 wk | — |
| 5 | Integration and submit (precheck) | 1–2 wk | — |
| ∥ | Test bench in parallel: own test PCB, low-noise source (AD5791 class or ratiometric bridge), battery power, RP2350 capture, same analysis code as sim | — | — |

**Immediate next options** (the user had not chosen yet):
1. **OTA spec sheet, then the first fully-diff OTA + CMFB in xschem/ngspice.**
   - Specs to fix: gain, swing linearity, GBW ≥ ~10 MHz, noise vs input-pair W·L.
   - Then feed `ota_white`, `ota_fc`, `a0_db` and `a0_drop` back into the model.
2. **Extend the model:**
   - Add reference noise, supply coupling, a PGA study and an area/power estimator.
   - Export golden vectors for the cocotb decimator.
3. **Phase 0 toolchain setup** on the sandbox.

## 12. Conversation log (user requests, in order)
(10. Review of SPEC.md and PUBLICATION_PLAN.md → fixes applied 2026-11-07b. 11. Gated plan: system → component → verification test suite, proceed only if all corners pass, like Paul Thomas → `work/v1-design/PLAN.md`.)
1. Survey prior TT shuttles for sigma-delta ADCs.
2. Clone the reference repos, including the Sigma-Delta Bitstream ADC 8-bit, into `~/projects/tt`, and save memory there. Also asked for typical applications and tt-pcb info.
3. Max frequency achieved by previous designs.
4. MCP3421 as the case-study target: "am I delulu?"
5. How sampling speed affects other parameters; beating Paul Thomas plus an open-research angle; direction from start to submission.
6. Sizing without MOS caps for first-cut pass; trade-offs and challenges.
7. Deeper achievability analysis based on the cloned repos.
8. Start the Python model.
9. Save all context and learnings to a Markdown file (this file).
