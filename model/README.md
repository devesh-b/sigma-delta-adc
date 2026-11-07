# Phase-1 behavioural model: incremental ΣΔ ADC

`iadc.py` is the model library and `run_studies.py` holds the studies. Reports and plots go to `out/`.

```sh
cd ~/projects/tt/model
../.venv/bin/python run_studies.py            # all studies (~1 min)
../.venv/bin/python run_studies.py noise      # one study: quant | gain | noise | settle | design
```

## What it models
A discrete-time, 1-bit, CIFB, **order 1 or 2** incremental ΣΔ, reset every conversion, with cascade-of-integrators reconstruction. It is vectorised over a batch of conversions. Voltages are normalised to VREF (±1 = ±2.048 V differential, MCP3421-style).

| Non-ideality | Parameter(s) | Source of default |
|---|---|---|
| Finite OTA gain (leaky integrator), swing-dependent gain | `a0_db`, `a0_drop`, `xswing` | — |
| Integrator swing clipping | `xmax` | — |
| kT/C (input + ref sampling, OTA thermal excess) | `cs`, `ktc_events`, `ktc_excess` | textbook |
| OTA 1/f + white density | `ota_white`, `ota_fc` | **pthomas sky130 PMOS pair: 6.9 nV/√Hz, corner 631 kHz** |
| OTA offset, chopper residual | `vos`, `vres` | assumption: 3 mV, 5 µV |
| OTA chopping at fs/2; system (input-swap) chopping | `chop`, `sys_chop` | — |
| Slow-error input referral | `lf_gain` | 1 (bottom-plate SC); `noise_gain` = pessimistic bound |
| Input / reference incomplete settling, shared vs separate caps | `tau_in`, `tau_ref`, `ref_mode`, `cd_ref` | — |
| Comparator offset / noise | `comp_offset`, `comp_noise` | — |

Loop coefficients: **c1 = 0.25, c2 = 0.5, k = 1**. The textbook 0.5/0.5 drives integrator 1 to ±1.85·VREF and integrator 2 to ±4.75·VREF; 0.25/0.5 keeps both within ±1.2·VREF (≈ ±2.5 V differential, OK for a 3.3 V fully-differential OTA).

## Findings (2026-11-07)
1. **Quantisation** (`report_quant.md`): order 1 gives log2(N) − 1 bits (the MCP3421 pattern). **Order 2 gives ≈ 2·log2(N) − 4 bits: N=1024 → 16 b, N=4096 → 20 b.** Order 2 is clearly worth it.
2. **OTA gain** (`report_gain.md`): a *constant* finite gain produces mostly **gain error ≈ 1/A0** (calibratable), not INL. **INL comes from gain that varies with swing.** With 90 % gain loss at full swing: **A0 ≈ 70 dB → ~120 ppm, 80 dB → ~45 ppm, 90 dB → ~19 ppm.** INL ≤ 100 ppm needs ~72 dB; ≤ 10–20 ppm needs ≥ 90 dB **or a more linear OTA output stage / smaller swing**.
3. **Settling** (`report_settle.md`): linear RC settling of the input or reference up to τ ≈ 0.2·t_half produces **gain error only**, no INL, in this model. `shared` caps are more tolerant of input settling than `separate`. *Not modelled: signal-dependent switch Ron/charge injection, which is the real INL risk → transistor sims.* This corrects my earlier claim in ACHIEVABILITY.md that the 500 Ω pad would cause INL through reference loading. That mechanism belongs to Paul's continuous-time resistive DAC, not to a settled SC design.
4. **Noise** (`report_noise.md`, lf_gain = 1, Cs = 1 pF):
   | case | 240 SPS | 15 SPS | 3.75 SPS |
   |---|---|---|---|
   | kT/C only (fs = 2 MHz) | 2.0 µV | 0.5 µV | 0.24 µV |
   | + 1/f, **no chopping** | ~10 µV | ~7 µV | ~8 µV (1/f doesn't average) |
   | + system chop only | 3.8 µV | 0.7 µV | 0.3 µV |
   | + OTA chop + system chop | 2.6 µV | 0.5 µV | 0.23 µV |
   - **Unchopped ≈ 7–12 µV (~18.5–19 b effective resolution)**, already better than the v1 target of 50 µV. My earlier ~30 µV estimate used the wrong (wideband) noise gain.
   - **System chopping alone** (just swapping input polarity each sub-conversion, digital + 4 switches) removes offset (3 mV → < 1 µV) and most 1/f. **Cheapest big win → do it in v1.**
   - The pessimistic bound (lf_gain = 5.3) gives ~40–60 µV unchopped and ~1–13 µV with system chop. Still within v1.
   - fs = 2 MHz vs 1 MHz: ~1.4× lower noise at the same rate (more samples averaged).
5. **Candidate v1 point** (`report_design.md`): fs = 2 MHz, order 2, N = 1024, Cs = 1 pF, A0 = 75 dB with 90 % swing drop, OTA + system chop. **Noise 2.5 µV @ 244 SPS, 0.5 µV @ 15 SPS, 0.26 µV @ 3.75 SPS; INL ≈ 71 ppm (OTA linearity limited); gain error −460 ppm (calibrate).**

## Caveats (what this model does NOT include, so silicon will be worse)
- Comparator noise / metastability; **reference noise** (cancels only if ratiometric); supply/substrate/clock coupling from TT neighbours and the on-chip decimator; board noise. **The model is the intrinsic circuit floor.** Wulff's SAR measured ~0.6 bit below sim, and nobody knows the ΣΔ gap yet. That gap is the research question.
- 1/f data is from Paul's specific PMOS pair (250 µm wide). Flicker ∝ 1/(W·L); our OTA sizing must be re-characterised with `ngspice .noise`.
- The flicker generator is ~15 % low in variance (finite low-frequency bins).
- Chopper residual offset (5 µV) and its spikes are assumptions. Real residuals scale with fs and charge-injection mismatch.
- Signal-dependent switch Ron, charge injection, clock feedthrough: not modelled. They need transistor sims.

## Next model steps
- Calibrate `ota_white`, `ota_fc`, `a0_db`, `a0_drop` from our own OTA transistor sims (Phase 2) and re-run.
- Add comparator noise + reference noise + supply-coupling terms. Add a PGA (Cs scaling) study and an area/power estimator.
- Export golden bitstreams/results for the cocotb decimator testbench.
