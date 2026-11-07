# Tapeout roadmap: precision incremental ΣΔ ADC on TT sky130

Working title: **"tt-iadc"**, an open, silicon-characterized, MCP3421-class incremental ΣΔ ADC.
Status: DRAFT direction (2026-11-07). The user has not locked it yet.

---

## 1. How sampling speed (fs) affects everything else

For a fixed signal bandwidth BW: OSR = fs / (2·BW). For an incremental ADC, conversion time = N/fs, where N is the cycle count per conversion.

| Parameter | Effect of raising fs | Note for our design |
|---|---|---|
| Quantization noise (SQNR) | improves +3(2L+1) dB per doubling (1st order +9, 2nd +15 dB) | Incremental: 1st order needs N ≈ 2^n cycles for n bits, 2nd order (CoI filter) needs only N ≈ 2^((n+1)/2). **2nd order at 1 MHz reaches 18-bit quantization in <1 ms.** |
| kT/C thermal noise | averaged over N samples: v² ≈ kT/(C·N). A faster fs lets C shrink for the same noise. | 1 pF → 64 µV/sample; N = 2^16 → ~0.25 µV. Not the bottleneck at low output rates. |
| OTA settling and power (SC) | must settle within T/2 → GBW ∝ fs → **power ∝ fs·C** | ~1 MHz needs GBW ~10–20 MHz: µA-level, easy |
| Op-amp gain needed | independent of fs. Incremental resolution needs A0 ≳ N (leaky integrator) | 2nd order, N ~ 1000 → ≥ 70–80 dB, which needs gain boosting or 2-stage |
| Clock jitter | **CT ΣΔ: SNR_jitter ∝ 1/(fs·σ)²·OSR**, very sensitive. SC: nearly immune (charge-based). | This is why Paul needs a PolarFire clock. SC at 1 MHz is fine with the RP2040/RP2350 clock. |
| 1/f noise | does not average away. Unchanged by fs. | Fix with **chopping** at f_chop ≤ fs/2, above the 1/f corner |
| Input impedance (SC) | Z_in ≈ 1/(fs·Cs) **drops** | 1 MHz × 2 pF → 500 kΩ; MCP3421 has 2.25 MΩ. Matters for high-impedance bridges. |
| Charge-injection / chopper spikes | residual offset and input current ∝ fs (and f_chop) | slower chopping reduces residual offset |
| Comparator metastability | probability ∝ fs·e^(−T/τ) | negligible at 1 MHz |
| Leakage on caps | **slower** fs → more droop (worse when hot) | sets the minimum fs at ~10s of kHz |
| Digital power / substrate noise | ∝ fs | decimator at 1 MHz is negligible |
| Pad / output limits | bitstream output at fs must pass the pads (unverified >25–50 MHz) | on-chip decimation reduces this to words; the raw bit pin stays for debug |
| Conversion rate / latency | rate = fs/N | trade fs against N |

**Choice: fs ≈ 1 MHz (programmable 250 kHz–4 MHz), switched-capacitor, chopped.** In that region precision is limited by analog effects (1/f, offset, gain, INL), not by speed. This sits in the opposite corner from Paul Thomas (50 MHz CT, jitter-limited).

---

## 2. vs Paul Thomas: where we can be better (honestly)
| Axis | Paul Thomas ttsky26c | Our target |
|---|---|---|
| Use case | wideband protection/measurement (100 kHz–1 MHz BW) | DC/low-frequency precision (sensors, bridges) |
| Loop | 1st-order CT, single-ended, RZ resistive DAC | **2nd-order SC incremental, fully differential**, 1-bit |
| Clock | 50 MHz, needs a low-jitter FPGA clock | ~1 MHz from the demo board |
| Decimation | off-chip (FPGA) | **on-chip** (CoI/sinc) + raw bit pin |
| Offset/1/f handling | none (not needed at his BW) | **chopping**, switchable on/off |
| Resolution (sim) | fast ~40 dB / precision ~57 dB SNDR (~9 ENOB) | **≥ 84 dB DR (~14 ENOB) at 15 SPS**, stretch 16+ |
| Silicon | not yet measured | first measured incremental ΣΔ on TT (if it works) |

We will NOT beat him on bandwidth, and shouldn't claim to. We can beat him on **resolution, completeness, DC precision, and published silicon characterization**. Compare honestly with **Schreier FoM_DR = DR + 10·log10(BW/P)** and the Walden FoM.

His methodology (DESIGN.md decision log, tiered sim, PEX gates in CI, silicon test plan) is the standard to copy. Reuse his flow ideas and cite him.

---

## 3. Research angle: an "experiment chip" (open-source contribution)
Make the die **configurable** so one chip runs controlled experiments. Everything below is selected by digital config bits (ui/uio pins or a shift register):

1. **Loop order 1 vs 2** on the same die (bypass the 2nd integrator), giving measured resolution vs N for both. Validates incremental ΣΔ theory on silicon.
2. **Chopping ON/OFF + f_chop select**: measures the sky130 1/f corner and offset, and shows how much chopping buys. Nobody has published this on open TT silicon.
3. **OSR / N select** (12/14/16/18-bit modes like the MCP3421): measured noise vs N, showing where thermal and 1/f dominate.
4. **fs sweep** (external clock): measured settling, leakage, and charge-injection limits, i.e. section 1 measured.
5. **Raw bitstream + on-chip result** both out, to cross-check the decimator. Gives an open dataset.
6. **Platform characterization**: TT analog-switch distortion/leakage and supply noise from neighbouring designs. Useful to the whole TT community.

Deliverables (the "research" part):
- Open repo: Python model → xschem → ngspice → magic/klayout PEX → CI gates (sim vs extracted)
- Silicon test notebooks + **raw captured datasets** (published)
- Writeup: **measured vs simulated correlation** for a sky130 incremental ΣΔ; incremental ΣΔ order/chopping study
- Venues to consider: FSiC (Free Silicon Conference), ORConf, Latch-Up, IEEE SSCS open-source / PICO / Chipathon programs, arXiv. Check current CFPs.

---

## 4. Proposed v1 spec (to be locked after the Phase 1 model)

> **Superseded by `SPEC.md`** (2026-11-07b): fs 2 MHz nominal, VREF 1.2 V provisional (study S1), N 64–4096, raw-accumulator output, TG input switch, corner set SPEC §6. The table below is the original draft. Execution plan: `work/v1-design/PLAN.md`.
| Item | v1 target | Stretch |
|---|---|---|
| Architecture | fully differential SC incremental ΣΔ, 2nd order (1st-order mode), 1-bit, chopped | multi-bit / DEM |
| fs | 1 MHz typ (0.25–4 MHz) | |
| Modes | N for 12/14/16/18 bit; rates ≥ MCP3421's | |
| Noise | ≤ 50 µV rms @ 15 SPS (≥ 14 ENOB DR) | ≤ 5 µV |
| INL | ≤ 100 ppm FSR | ≤ 30 ppm |
| Input | differential, ±VREF; PGA x1/x2 (cap ratio) | x4/x8 |
| Reference | **ratiometric**: VREF = external pin or VAPWR-derived; bridge sensors don't need an absolute reference | on-chip bandgap + digital trim |
| Supply | VAPWR 3.3 V analog, VDPWR 1.8 V digital | |
| Power | ≤ 200 µA analog | |
| Output | 16–24-bit word via shift-register/SPI-like on uo, + raw bit + data-ready | I²C slave |
| Area / pins | 2x2 tile, ua0 VIN+, ua1 VIN−, ua2 VREF (3 pins: 40+40+100 €) | ua3 integrator monitor (debug) |
| Est. cost | 4 tiles × 70 + 180 = **~460 €** (+ PCB/instruments) | |

The decimator must live **inside** the analog macro (the TT mux selects one project at a time, so an off-chip digital helper project can't be wired to it). Harden the RTL with LibreLane/OpenLane as a sub-macro, or with hand-placed std cells. CoI decimation for an incremental design is just 2 accumulators + a counter, so it's tiny.

---

## 5. Phases: start → submission
Shuttle: check https://tinytapeout.com/runs for the next sky130 shuttle (ttsky26c closed 2026-09-07; the next is probably early–mid 2027). Plan **~20 weeks part-time**; work backwards from the deadline and keep 3+ weeks buffer for precheck/LVS pain.

| # | Phase | Weeks | Output | Gate (must pass to move on) |
|---|---|---|---|---|
| 0 | **Foundations** | 2–3 | Read Schreier & Temes *Understanding ΔΣ Data Converters* (ch. 1–4, incremental chapter); Markus/Silva/Temes, "Theory and applications of incremental ΔΣ converters" (2004); Wulff tt06-sar + pthomas repos. Install: ciel (PDK), xschem, ngspice, magic, netgen, klayout, LibreLane, cocotb, iverilog, python-deltasigma. Run the TT analog template end to end (dummy inverter → GDS → precheck). | template passes precheck locally |
| 1 | **System model** | 2–3 | Python behavioural model: 1st/2nd-order incremental, CoI decimator, nonidealities (finite gain, swing, kT/C, offset, 1/f, chop, cap mismatch, jitter). **Noise budget + spec table locked.** Coefficient choice, N per mode. | model meets v1 spec with margin; spec frozen in SPEC.md |
| 2 | **Block schematics** | 5–6 | Fully-diff OTA + CMFB, StrongARM comparator + latch, TG switches (3.3 V), non-overlap clock gen, chopper, bias, ref buffer/divider. Each block: testbench, corners (tt/ss/ff, −40/27/125 °C, ±10 % V), Monte Carlo. | every block meets the budgeted spec at all corners |
| 3 | **Top + digital** | 2–3 | Top-level schematic; decimator + config + output RTL; cocotb TB; mixed-signal sim (ngspice d_cosim / bitstream export → RTL). | full chain ENOB in transistor sim ≈ model |
| 4 | **Layout** | 5–6 | common-centroid MIM/MOM caps, guard rings, symmetric diff routing, decimator hardened macro, TT power stripes (met4, no met5). DRC/LVS clean, **PEX re-sim gates** (copy Paul's CI). | extracted SNDR within ~2–3 dB of schematic |
| 5 | **Integration + submit** | 1–2 | TT analog template, info.yaml, docs/info.md (datasheet + test plan), GDS/LEF, GH Actions precheck, submit. | precheck green, submitted |
| ∥ | **Test bench prep** (parallel) | — | Test plan (Paul's 4-phase style), battery-powered setup, low-noise source (precision DAC e.g. AD5541A/AD5791 class, or a bridge/resistor divider), RP2350 MicroPython/PIO capture, analysis notebooks reused from sim (same FFT/noise code). | bench ready when chips arrive (~6–9 months later) |

### Risks and mitigations
- **Too ambitious for a first tapeout** → keep 1st-order mode + raw bitstream pin as the "something works" fallback.
- **Decimator integration inside the analog macro** → prototype hardening flow in Phase 0/3 early.
- **Area (2x2 ≈ 75k µm²)** → budget caps in Phase 1 (MIM ~2 fF/µm²: 20 pF ≈ 10k µm²).
- **1/f / offset worse than sim** → chopping switchable + digital offset cal (shorted-input conversion).
- **Demo-board passives on analog pins** (pull-downs, errata) → check the current board before measuring.
- **Shuttle slip/cancel** (ChipFoundry needs ≥ 50 % fill) → keep the design portable (IHP has no 3.3 V rail; note it).
