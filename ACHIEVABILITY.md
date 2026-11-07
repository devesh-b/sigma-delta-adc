# Achievability analysis: evidence from the cloned repos

Draft, 2026-11-07. Every claim cites a file under `repos/`. All repos are Apache-2.0, so blocks and tools can be reused with attribution.

## 1. Block-by-block: prior art vs our need
| Block | Best prior evidence | Their numbers | Our need (2nd-order SC incremental, fs≈1 MHz, 3.3 V) | Gap / risk |
|---|---|---|---|---|
| **OTA (integrator)** | pthomas folded cascode (`sd-analog/ttsky-sigma-delta/STATUS.md`); shimomi 3.3 V two-stage opamp (`sd-analog/tt_sky26a_analog_prj/README.md`); TilesOS 5T OTA (`magic/dsm_ota5*.mag`) | Paul: A0 **65 dB**, GBW 209→119 MHz post-layout, 1.37 mA (built for 50 MHz). Shimomi: **65 min / 75 typ dB**, 2 MHz GBW @10 pF, 18 µA ref, single-ended | **fully differential + CMFB**, A0 ≥ 70 dB (N=1024) or ≥ 80–90 dB (N=4096), GBW ~10 MHz @ 2 pF, tens of µA | **HIGH.** Nobody on TT has done a fully-diff OTA with CMFB. 80 dB not demonstrated. → design at N≈1024 + 75 dB two-stage (shimomi-class is proven in sim), treat 80+ dB as a stretch |
| **Comparator** | pthomas StrongARM (`DESIGN.md` 2026-07-19); TilesOS StrongARM + held latch; shimomi 3.3 V comp | Paul: τ 77 ps, offset σ 13.6 mV (MC), 71 µW. Shimomi: 13 ns delay | anything resolving in <100 ns at 1 MHz; offset irrelevant (after 2 integrators) | **LOW.** Reuse the StrongARM topology. Lesson: Paul found a hysteresis bug in the SR latch and a half-cycle excess delay from clocking on the wrong edge |
| **Switches (TG)** | TilesOS `dsm_tg_switch` qualified over PVT | Ron 2.0–44 kΩ (1.8 V devices) | Ron ≤ ~30 kΩ for 1 pF settling to 20 b at 1 MHz; 3.3 V devices → lower Ron | **LOW** |
| **Non-overlap clock gen** | TilesOS on-chip from external clk | 500 kHz OK; **"do not use 1 MHz as unconditional PVT point"** (lost timing margin at HH, SS_HH) | ~1 MHz, plus chopper phases | **LOW–MED.** Their delay cells were sized for 500 kHz; design ours with margin at 2 MHz |
| **Caps** | Paul and shimomi: MIM `cap_mim_m3_1`; TilesOS: M1/M2 VPP | Paul: 60 pF ≈ 30k µm² (2 fF/µm²). **TilesOS: VPP model caused ngspice timestep failures in long runs** | Cs 0.5–1 pF, Cf 2–4 pF (MIM) | **LOW.** Use MIM (also avoids TilesOS's sim failures) |
| **Reference** | shimomi 3.3 V bandgap (BGR) + PTAT; TilesOS supply-tracking ladder | Shimomi: start-up may oscillate at VDD≈1 V; no MC/post-layout | v1: external ratiometric VREF pin + on-chip decap/buffer | **LOW** (external). An on-chip BGR is an optional experiment |
| **Level shifters 1.8↔3.3** | shimomi LVSHFTL2H; pthomas `lvl` | 9 ns, 10 MHz max | 1 MHz control + bit out | **LOW.** Paul: a slow clk33 rise cost him SNDR; size the edges |
| **Digital decimator inside analog macro** | **shimomi did it**: 1.8 V std-cell ripple-counter decimator inside 1x2 analog + 3.3 V DSM | **"functional bug reported"**, "timing verification not executed", "std-cell netlists not fully LVS-matched" | CoI (2 accumulators ~24 b) + counter + config + shift-out at 1 MHz | **MED.** Precedent exists, but done carelessly. Do it with a proper hardened macro (LibreLane) + STA + cocotb. Size check: the bmurmann/Sheldon filters each fit a 1x1 tile at 50 MHz |
| **Decimator RTL** | bmurmann `tt09-decimation_filter` (incremental + regular mode, 147 lines); Sheldon CIC (338 lines); lime CIC | functional RTL, 16-bit out | CoI for 2nd-order incremental, 18–24 b | **LOW.** Small RTL; learn from bmurmann's incremental mode |

## 2. Noise and offset: the decisive number from Paul's repo

> **Correction (2026-11-07, Phase-1 model):** the ×2.5 noise gain below was wrong for slow errors. In a bottom-plate SC integrator, offset and 1/f refer to the input with gain ≈1, so unchopped DC noise is **~7–12 µV**, not ~30 µV. With system chopping it is ~0.3–4 µV. See `model/README.md`. The table below is kept as the original hand estimate.
`DESIGN.md` 2026-07-26 (`ngspice .noise`, sky130 BSIM4 flicker, PMOS pair 250 µm wide):
**white 6.9 nV/√Hz, 1/f corner 631 kHz.** Also: `.tran` simulates **zero** device noise, so 1/f is invisible to transient sims.

Applied to our DC band (unchopped OTA input, ×~2.5 noise gain to the ADC input):
| Band | at OTA | input-referred | ≈ bits over 4.096 V FSR |
|---|---|---|---|
| 0.1–10 Hz | 11.8 µV | **~30 µV** | ~15.3 |
| 0.1–100 Hz | 14.4 µV | ~36 µV | ~15.0 |

**Consequences:**
- **v1 target ≤ 50 µV (~14.5 b) is reachable WITHOUT chopping** (est. ~30 µV + kT/C 3–7 µV + board noise).
- **MCP3421's 1.5 µV is ~20× below the unchopped 1/f floor → chopping is mandatory** for anything < ~10 µV.
- Chopping only works if f_chop ≳ the 1/f corner (~600 kHz). With chop at fs/2, fs ≥ ~1.2–2 MHz. This feeds back into the fs choice (→ fs = 2 MHz programmable).
- Offset: Paul's comparator σ 13.6 mV implies a sky130 OTA offset in the **mV** range → input offset of mV unchopped. MCP3421's 15 µV only via system-level chop/calibration. A digital offset cal (shorted input) is cheap.

## 3. Simulation feasibility (evidence)
- TilesOS: **an 8,192-bit ngspice transient could not complete** (VPP cap model timestep failures after 3,344 bits; Gear rerun also limited). The SS_HH run needed solver changes.
- Paul: acceptance on 2,048-bit windows (512-bit windows scatter ±3 dB). Tiered flow: tier-0 Python → tier-1 behavioural xschem → tier-2 transistor blocks → tier-3 PEX. Long runs were only feasible at behavioural level.
- Ours: one 18-bit conversion is N = 1024–4096 cycles, and noise/INL need many conversions. **Full transistor-level characterization of noise/INL is infeasible in ngspice** → same tiered approach: transistor-level for *parameters* (gain, settling, swing, offset, noise PSD), Python model for *system* (noise, INL, N, K).
- Paul's magic gotchas (fake DRC from `writeall force`, false-clean DRC without `select top cell; expand`) apply to us; copy his checks.

## 4. Silicon reality checks
- **Wulff tt06-sar** (`adc-ref/tt06-sar/meas/`): the only measured analog ADC here. Alive; **~7 ENOB measured vs 7.63 sim**; conversion **<83 ns vs 44 ns sim (≈2× slower)**; "funky harmonics" attributed to interference; noise improved a lot on his own PCB (STD 0.34 LSB) vs the demo board. Lesson: expect a sim→silicon gap and plan your own test PCB.
- Paul's silicon survey (`DESIGN.md`, harvested from other TT projects): an oscillator **dead from a missing via**; a **demo-board pull-down** killed analog amplitude; TT clk path proven to 62–100 MHz; the 1/f in one measured project came in slightly *below* sky130 sim.
- **No sigma-delta ADC on TT has measured silicon results yet** (ttsky26a/c pending). The first measured incremental ΣΔ is a genuine open contribution, but there is no precedent to lean on.

## 5. Effort calibration
- Paul: 2026-07-05 → 09-07 (~9 weeks), very intensive, heavy automation (CI, generated schematics/layout, PEX gates). Single-ended 1st order, 1x2.
- TilesOS: similarly extensive PVT/extracted verification, 2x2, 1st order SC.
- Ours is more complex (fully diff, CMFB, 2nd order, chopper, on-chip decimator). **~20 weeks part-time is realistic only with the scope cuts below**, reusing Paul's tooling patterns.

## 6. Achievability scorecard (my judgment)
| Spec | v1 target | Confidence | Basis |
|---|---|---|---|
| Working 2nd-order incremental modulator + on-chip CoI | yes | **Med-High** | all blocks have TT precedents except fully-diff OTA/CMFB |
| 1st-order fallback + raw bitstream | yes | **High** | TilesOS/Paul/shimomi-class designs |
| 16–18-bit codes (no missing codes) | yes | **High** | 1-bit loop + digital |
| Noise ≤ 50 µV rms @ 15 SPS (unchopped) | ~7–12 µV (model) | **High** | Paul's 1/f data + model |
| Noise ≤ 5 µV (system chop) | model 0.3–4 µV | **Medium** | chopper residuals, f_chop vs 631 kHz corner, no pnoise in ngspice |
| 1.5 µV (MCP3421) | — | **Low** | 20× below unchopped floor; needs a mature chopper |
| INL ≤ 100 ppm | yes | **Med** | depends on OTA gain/swing + ref loading through the pad |
| INL 10 ppm | — | **Low** | |
| Offset ≤ 50 µV after digital cal / system chop | yes | **Med** | |
| Power ≤ 200 µA analog | yes | **High** | shimomi opamp 18 µA ref; TilesOS ~150 µA total |
| Fits 2x2 | yes | **Med-High** | TilesOS 2x2 incl. VCO; budget in SIZING.md |

## 7. What needs to be done (work breakdown, mapped to reference repos)
**A. Learning / reproduction (Phase 0)**
1. Install the toolchain exactly like Paul (`STATUS.md` Toolchain): ngspice ≥ 42, xschem, **source-built magic 8.3.6xx** + netgen, ciel PDK pinned. Note: these docs are Linux-based; on macOS consider Docker / the IIC-OSIC-TOOLS image.
2. Reproduce Paul's `sim/ota_tb.py` and `sim/noise_tb.py` (a 1/f corner of our own), and shimomi's `opamp3V3_v2` testbench at 3.3 V.
3. Run TT's analog template through precheck with a trivial cell.

**B. System model (Phase 1)**: Python model (pattern: Paul `sim/tier0.py`, `sim/snr.py`)
4. 1st/2nd-order incremental + CoI; inject finite A0, swing clipping, kT/C, OTA 1/f PSD (Paul's numbers), offset, chopping, ref droop through 500 Ω, cap mismatch.
5. Output: lock fs (1 vs 2 MHz), N, K, Cs/Cf, A0 requirement, f_chop → SPEC.md.

**C. Blocks (Phase 2)**: generated-schematic + testbench-per-block pattern (Paul `tools/gen_*_sch.py`, `sim/*_tb.py`)
6. Fully-diff two-stage OTA + SC CMFB (new; textbook: Johns & Martin, Razavi). Corners + MC. **Critical path.**
7. Chopper switches + CDS option (new).
8. StrongARM + latch (adapt Paul/TilesOS).
9. TG switches, bottom-plate sampling, non-overlap clock gen at 2 MHz margin (adapt TilesOS).
10. Ref input buffer/decap; bias (adapt shimomi BGR/bias).
11. Level shifters (adapt shimomi/Paul).

**D. Digital (Phase 3)**
12. CoI decimator + N/order/chop/K config + shift-out + data-ready (learn from bmurmann incremental mode). cocotb tests with golden vectors from the Python model (Paul `tools/gen_golden.py` pattern).
13. Harden as a macro with LibreLane; STA. **Avoid shimomi's untested-timing bug.**

**E. Layout (Phase 4)**
14. MIM unit-cap common-centroid arrays; matched OTA input pair; guard rings; analog/digital separation.
15. DRC/LVS/PEX automation + CI gates (Paul `tools/pex_*.py`, `layout_report.py`, `frame_check.py`).

**F. Integration and test (Phase 5 and in parallel)**
16. TT frame: tie unused outputs (Paul's 22-floating-outputs fix), antenna checks, precheck.
17. Test plan in Paul's 4-phase style; test PCB (Wulff lesson); capture firmware; same FFT/noise estimator for sim and silicon (Paul `sim/snr.py --bits`).

## 8. Recommended scope cuts for first silicon
- fs programmable around 1–2 MHz; N ∈ {256, 1024}; K averaging in firmware.
- OTA target 75 dB (proven class), not 90.
- Chopper switchable on/off (silicon tells us). Unchopped noise already meets v1.
- External VREF (ratiometric); no PGA beyond x1/x2.
- Keep the 1st-order mode + raw bitstream + integrator monitor pin for debug.
