# Sizing, trade-offs, and challenges: precision incremental ΣΔ (MCP3421-class) on TT sky130

Draft analysis, 2026-11-07. Hand calculations only; Phase 1 Python model must confirm.

## 0. The capacitor question: MIM, not MOS, and caps stay small
- **sky130 MIM (`sky130_fd_pr__cap_mim_m3_1`, met3–met4)**: ~2 fF/µm² (Paul: 60 pF ≈ 30,000 µm²). Linear (low voltage coefficient), low leakage. Use it for **all signal-path caps** (sampling, integrating, DAC). `cap_mim_m3_2` uses met5, which is **forbidden on TT**.
- **MOS caps** (thin-ox ~8 fF/µm², thick-ox 3.3/5 V ~3 fF/µm²): strongly **voltage-dependent** (percent-level C(V)), which destroys INL in the signal path, plus modelling/sim effort. Use them **only for decoupling and bias filtering**, where nonlinearity doesn't matter. MIM can sit **above** MOS decaps or circuitry (met3/4 vs FEOL) for stacked density.
- MOM/VPP finger caps (TilesOS used M1/M2): lower density; only for tiny matched unit caps.
- **Why caps stay small: oversampling averages kT/C away.** We don't need large caps for noise, so no MOS caps are needed in the signal path.

## 1. Noise vs Cs vs N (fully differential, 4kT/Cs per sample, CoI 2nd-order weighting 4/(3N), ×√2 for OTA excess)
| Cs (each side) | per-sample | N=256 | N=1024 | N=4096 | N=16384 | N=65536 |
|---|---|---|---|---|---|---|
| 0.25 pF | 257 µV | 26 µV | 13 | 6.6 | 3.3 | 1.6 |
| 0.5 pF | 182 µV | 19 | 9.3 | 4.6 | 2.3 | 1.2 |
| **1 pF** | 129 µV | 13 | 6.6 | **3.3** | 1.6 | **0.8** |
| 2 pF | 91 µV | 9.3 | 4.6 | 2.3 | 1.2 | 0.6 |

Noise to "ENOB" over a 4.096 V FSR: 1.5 µV ≈ 19.6 b · 5 µV ≈ 17.9 b · 20 µV ≈ 15.9 b · 50 µV ≈ 14.5 b.
→ **Cs ≈ 0.5–1 pF already beats the MCP3421's 1.5 µV in thermal noise** at its rates. Thermal noise is **not** the limiter; 1/f, offset, OTA gain, reference, and coupling are.

## 2. Quantization vs N vs order (ideal; scaled coefficients lose ~2–4 bits)
| N (cycles/conversion) | rate @ fs=1 MHz | 1st-order bits ≈ log2 N | 2nd-order bits ≈ 2·log2 N − 1 |
|---|---|---|---|
| 256 | 3.9 kSPS | 8 | ~15 |
| 1024 | 977 SPS | 10 | ~19 |
| 4096 | 244 SPS | 12 | ~23 |
| 16384 | 61 SPS | 14 | ~27 |
| 262144 | 3.75 SPS | **18 (= MCP3421 pattern)** | — |

**The MCP3421 rate/resolution table fits 1st order exactly.** With 2nd order, N ~ 1–4k already gives ≥18-bit quantization, so the extra time is spent averaging noise.
**Plan:** 2nd-order incremental with N ≈ 1024–4096 per *sub-conversion*. To reach MCP3421-like low rates, average K sub-conversions digitally, alternating input polarity between them (system-level chopping). This keeps N small, which matters for the OTA gain requirement (§3).

## 3. OTA requirements (fs = 1 MHz)
- Settling to 20 b in ~T/2 (450 ns minus non-overlap) → τ ≤ ~32 ns. With β ≈ 0.5 → **GBW ≥ ~10 MHz**, gm ≈ 125 µS at 2 pF → **~6 µA/side** at gm/Id≈20. Cheap.
- Slew: Vref·Cs/Cf steps of ~0.5–1 V in ≤100 ns → ~10 V/µs on 2 pF → ~20 µA. Still cheap.
- **DC gain is the hard one:** a leaky first integrator in an incremental converter causes errors ∝ N/A0. With N ≈ 4096 we need **A0 ≳ 80–90 dB** fully differential with CMFB at 3.3 V. Options: two-stage Miller (stability, CMFB×2), gain-boosted folded cascode (complex), or N ≈ 1024 (fewer quantization bits, relaxed gain ~70 dB). **Trade: N ↔ OTA gain ↔ averaging K.**
- 1/f noise: large PMOS input pair (W·L in the 100s of µm²) plus chopping or CDS. **This is where area goes, not the caps.**

## 4. Area budget for a 2x2 tile (~334×225 ≈ 75,000 µm²)
| Block | Estimate (µm²) | Note |
|---|---|---|
| Stage-1 caps: Cs 1 pF + Cf 2–4 pF, ×2 sides | ~5,000–7,500 | MIM + 1.5× overhead |
| Stage-2 caps (smaller: noise suppressed by stage-1 gain) | ~2,000 | |
| PGA: x1/x2 only (one extra Cs bank) | ~1,500 | x8 = 8× Cs → ~8k more. Defer, or scale Cs base down |
| 2 fully-diff OTAs + CMFB, big input pair | ~6,000 | |
| Comparator, switches, non-overlap clock, choppers, level shifters | ~3,000 | |
| Bias + reference buffer/divider | ~3,000 | |
| Ref/supply decap (MOS, MIM stacked over) | ~5,000 | |
| **Digital**: CoI (2 accumulators ~24 b), counter, config, shift-out (averaging K off-chip or on-chip ~+30 b acc) | ~8,000–15,000 | sky130 hd cells ~40 µm²/cell incl. routing |
| Guard rings, routing, met4 power stripes | ×1.5–2 | |
| **Total** | **~45,000–65,000** | fits a 2x2; **a 1x2 (36k) is too small** |

## 5. Speed vs everything (similar speed to the MCP3421)
| Knob | ↑ improves | ↓ costs |
|---|---|---|
| fs ↑ | more N per conversion → lower noise/quant at the same rate; higher max rate | OTA power ∝ fs; charge-injection input current/offset ∝ fs; lower input impedance (1/(fs·Cs): 1 MHz·1 pF → 1 MΩ/side) |
| fs ↓ | power, input impedance | cap leakage (hot), fewer cycles |
| Cs ↑ | kT/C noise | area, OTA power (CL), lower input impedance, slower settling |
| N ↑ (per sub-conversion) | quantization bits | OTA gain requirement, integrator swing |
| K ↑ (averaging) | noise √K, enables system chopping | rate |
| Order 2 vs 1 | massively fewer cycles per bit | 2nd OTA, scaling, more sim |
| Chopping/CDS | offset and 1/f (the real precision limiters) | residual spikes, charge injection, design complexity |

**Recommended operating point:** fs = 1 MHz (programmable), Cs = 0.5–1 pF, Cf ≈ 2–4×Cs, 2nd order, N = 1024/4096, K = 1…64.
→ Rates 3.75–244+ SPS like the MCP3421. **Thermal-limited noise of a few µV even at 244 SPS**, where the MCP3421 gives only 12 bits. That is the potential "better than MCP3421 at speed" research claim, if 1/f and offset are handled.
→ Analog power ≈ 50–100 µA at 3.3 V (MCP3421: 145 µA).

## 6. Challenges (ranked)
1. **1/f noise and offset (#1).** At DC, sky130's 1/f noise dominates, and it doesn't average down. Needs OTA chopping/CDS at ≥ the 1/f corner (likely 10s of kHz–MHz) **plus** system-level input-swap chopping to kill residual offset (charge-injection mismatch). Hard to predict: ngspice has **no PSS/pnoise**, so only analytic estimates + slow transient-noise sims. **Silicon is the real answer, and that is the research data.**
2. **OTA DC gain vs N.** 80–90 dB fully diff at 3.3 V with CMFB and enough swing. Stability/corner sims.
3. **Reference.** An untrimmed on-chip bandgap is ±1–2 %. Go **ratiometric / external VREF**. *Correction (model, 2026-11-07): when the reference node settles each phase (τ ≲ 0.2·t_half), loading through the ≤500 Ω pad gives only gain error, not INL. The IR-drop INL mechanism applies to continuous-time resistive DACs such as Paul's.* Keep an on-chip ref decap; reference noise passes straight through unless the measurement is ratiometric.
4. **Linearity (INL).** 1-bit DAC is inherently linear and **cap mismatch only causes gain error** (sharing one Cs for input and reference cancels even that). Remaining INL sources: OTA gain variation with swing, signal-dependent switch charge injection / Ron (use bottom-plate sampling, fully differential, 3.3 V TGs), incomplete settling through the TT pad path (needs an external RC like the MCP3421 recommends).
5. **TT input path.** tt_asw_3v3 analog switch (≤500 Ω, ~5 pF, leakage, nonlinear Ron) sits in front of our sampling caps: SC kickback and settling. Test board needs an RC filter at the pin.
6. **Mixed-signal integration.** Decimator must live inside the analog macro (the TT mux selects one project), so it needs hardening (LibreLane) + placement + 1.8↔3.3 V level shifters. Digital switching noise coupling into a µV-level front end: guard rings, separate wells, quiet clock edges (decimator updates in the non-sampling phase).
7. **Simulation cost.** Transistor sims of 4096+ cycles × corners are slow. Use a **tiered** approach (Paul's method): behavioural model → block sims → short transistor-level runs → PEX spot checks.
8. **Verification and measurement.** Proving 10 ppm INL / µV noise needs a 20-bit-class source (e.g. AD5791) or a ratiometric resistor bridge, battery power, and shielding. The bench is a project of its own. Start it in parallel.
9. **Area.** Fits a 2x2 but tight with x8 PGA + on-chip averaging. Defer x8 PGA; keep averaging off-chip in v1 if needed.
10. Temperature drift / supply range: not controllable on TT. Document only.

## 7. First-cut simplifications (to pass first silicon)
- MIM only, no MOS caps in the signal path. Unit-cap arrays, common-centroid.
- 1st-order mode selectable (fallback) + raw bitstream pin.
- Chopping switchable (on/off) so silicon shows both.
- PGA x1/x2 only. External VREF (ratiometric). No on-chip bandgap in v1, or one as an optional experiment.
- On-chip CoI decimator only; averaging/calibration in MCU firmware.
