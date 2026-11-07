# Sigma-delta ADC on Tiny Tapeout — research notes

Survey date: 2026-11-07. Source: https://index.tinytapeout.com (29 shuttles, ~4,900 projects). I searched titles and descriptions by keyword, so a project with an unusual name could be missing.

## 1. Prior work (all cloned under repos/)

### Analog sigma-delta modulators on sky130 (main references)
| Shuttle | Repo dir | What | Key specs |
|---|---|---|---|
| ttsky26c | sd-analog/ttsky-sigma-delta (+ `pthomas-sigma-delta-design`, the full GitLab design repo) | Paul Thomas, 1st-order **continuous-time** ΣΔ | 3.3 V analog rail; folded-cascode OTA, active-RC integrator, 132k input R; StrongARM comparator + retimer; RZ resistive DAC; **50 MHz** clock; off-chip decimation with a fast path (~1 MHz BW, ≥6 ENOB) and a precision path (~100 kHz BW, 10+ ENOB, target). 2x2, ua[0]=VIN, ua[1]=integrator monitor. Most thorough methodology: DESIGN.md, STATUS.md, xschem, params.py, CI. README says the GDS was work in progress. |
| ttsky26c | sd-analog/tt_um_tilesos_dual_adc | Tyler McClure, 1st-order **switched-cap** ΣΔ + VCO ADC | 1.8 V only; SC OTA integrator, Cin/Cf/Cdac = 0.2566/1.466/0.1466 pF (7:40:4 units of M1/M2 VPP caps); StrongARM; 1-bit DAC (0/1.8 V); **500 kHz** clk; on-chip non-overlap clock gen; VCM 0.9 V; input range 0.75–1.2 V; buffered loop monitor on ua[1]. 2x2. |
| ttsky26a | sd-analog/tt_sky26a_analog_prj | shimomi, ΣΔ ADC + bandgap | Docs say "TBD"; read design/ and src/. 1x2, 1 analog pin. |
| ttsky26c | sd-analog/ttsky26c_ns_sar_adc | Silicon Edge, 8-bit differential SAR core for a future NS-SAR | 96 kHz clk, 8 kS/s, CM 0.9 V, 5 µA bias; noise shaping not in this tapeout yet. |

### Digital-only / external RC (comparator = digital input pin, integrator = off-chip RC)
- sd-digital/tt02-adc-dac: Adam Greig, tt02/tt03
- sd-digital/tt06_jv_sigdel_v: Joerg Vollrath, tt06, external R1, R2, C2
- sd-digital/tt09-sigma-delta: Martin Schoeberl, tt09 / ttihp25a
- sd-digital/TTSKY26A-ADC-8BIT: William Anthony, ttsky26b. Decimator only: counts ones over 256 cycles, i.e. a sinc1 "boxcar", 8-bit, with gain and offset trim. Very basic.
- sd-digital/ttsky25b-noise-shaping-ds-dac: Toivo Henningsson, 16-bit noise-shaping ΣΔ **DAC** (useful for noise-shaping theory and the DAC direction)

### Decimation
- decimation/tt09-decimation_filter: bmurmann group (Stanford). Handles incremental and regular ΣΔ. **Best back-end reference.**
- decimation/tt09-delta-sigma-decimation-filter: Sheldon
- decimation/lime_cic_filter: CIC filter

### Other analog sky130 ADCs (references for pads, comparator, flow)
- adc-ref/tt06-sar: Carsten Wulff, 8-bit SAR. Mature flow; Wulff also teaches analog IC design at NTNU.
- adc-ref/tt07-12bit_SAR_ADC: Ricardo Nunes, 12-bit differential SAR
- adc-ref/flash-adc: htfab, 4-bit flash

### IHP SG13G2
- sd-ihp/analog-trial: SoilZ, CT-ΣΔ inside an IQ lock-in impedance analyzer (ttihp26a)
- sd-ihp/Delta-Sigma-Comparator-Based-ADC: Kozlowski, switched-cap lines (ttihp25b)

### Gaps no one has filled on sky130 yet (learning targets)
1. ΣΔ modulator of **2nd order or higher** (all three prior analog ones are 1st order)
2. **On-chip decimator** (CIC/sinc³ + optional FIR/halfband) giving multi-bit words, i.e. a complete ADC
3. **Fully differential** switched-cap modulator (better PSRR and even-order rejection)
4. **Multi-bit quantizer** with DEM (dynamic element matching)
5. Incremental ΣΔ (good for DC/sensor use, pairs with the bmurmann filter)
6. Silicon-measured SNDR/ENOB results published (no measured results found)

## 2. Making specs better: the levers
- SQNR (ideal, L = loop order, N = quantizer bits, OSR = oversampling ratio): `SQNR ≈ 6.02N + 1.76 − 10log10(π^(2L)/(2L+1)) + (2L+1)·10log10(OSR)`
  - Each OSR doubling gains 3(2L+1) dB: 1st order +9 dB (1.5 bit), **2nd order +15 dB (2.5 bit)**, 3rd order +21 dB.
  - Example: 2nd order, 1-bit, OSR 128 → ~85 dB SQNR → in practice limited by thermal noise, kT/C, and op-amp gain.
- In practice on sky130, the limits are kT/C (larger Cs → more area; tile is only ~334x225 µm for 2x2), OTA gain and swing, comparator metastability, clock jitter (critical for CT designs), and the pad/analog-switch path (<500 Ω, <5 pF, through tt_asw_3v3).
- A 2nd-order **CIFF or CIFB SC** modulator is the classic, robust next step (Boser-Wooley / Schreier toolbox). Tools: python-deltasigma (port of Schreier's DSToolbox) for NTF synthesis, then a behavioral sim, then xschem/ngspice.
- On-chip CIC (sinc³ for 2nd order: CIC order ≥ L+1) is cheap in digital tiles and makes the ADC complete.

## 2b. Clock / bandwidth achieved by prior designs (from repo docs, 2026-11-07)
| Design | Clock / fs | Signal BW | Result | Status |
|---|---|---|---|---|
| pthomas CT-ΣΔ (ttsky26c) | 50 MHz | fast ~1 MHz / precision ~100 kHz | extracted sim: fast 38.3–40.7 dB SNDR (~6 ENOB), precision ~57 dB (~9.2 ENOB) | sim only, no silicon yet |
| TilesOS SC-ΣΔ (ttsky26c) | 500 kHz | not stated (off-chip decim) | — | sim only |
| Schoeberl tt09 (digital + ext RC) | 50 MHz clk | — | — | digital |
| tt06-sar Wulff (silicon!) | 4 MHz (sim 44 ns, silicon <83 ns per conversion) | tested at 100 kHz sine | **~7 ENOB measured**, 7.63 ENOB_FS sim | **silicon measured** (`adc-ref/tt06-sar/meas/`) |
| tt07 12-bit SAR Nunes | ≤20 MHz clk, fs = clk/16 → ≤1.25 MS/s | — | ENOB table blank | limited by 500 Ω pad R |
| NS-SAR core (ttsky26c) | 96 kHz clk | 8 kS/s | — | — |
| Platform: TT clk path | **62–100 MHz proven on silicon** (urish charge pump, cited in pthomas DESIGN.md) | | | silicon |
| Platform: RP2040 demo board | clock gen ≤ ~50 MHz (and jittery → use external clean clock for CT-ΣΔ) | | | |
- Analog pad path is the BW limit: <500 Ω + <5 pF (+ analog switch). The tt07 SAR datasheet blames its clock limit on that 500 Ω.
- Digital output pad toggle rate: pthomas set a fallback if it measures <25 MHz. Unverified in silicon at 50 MHz bitstream rates.

## 3. Typical applications of sigma-delta ADCs
High resolution, low-to-moderate bandwidth, little or no anti-alias filter needed (oversampling relaxes it), and a tolerance of latency.
- **Audio**: codecs, mics, DAC/ADC in phones and laptops (16–24 bit, 20 kHz BW). PDM MEMS microphones are ΣΔ modulators that output a 1-bit stream.
- **Precision measurement / instrumentation**: weigh scales (load cells, bridge sensors), DMMs, thermocouples, RTDs, pressure (24-bit, low rate). Usually incremental ΣΔ.
- **Industrial**: PLC analog inputs, 4–20 mA loops, process control.
- **Motor control and power**: isolated ΣΔ modulators for shunt current sensing (e.g. AMC1306/AD7403-type parts). The 1-bit stream crosses the isolation barrier and an FPGA/MCU applies sinc³ filters (a fast "trip" path plus a precise control path). Paul Thomas's dual-path idea copies this.
- **Energy / smart metering**: voltage/current metering ICs.
- **Biomedical**: ECG, EEG, EMG, bioimpedance (low BW, high dynamic range); the SoilZ project is a similar impedance use.
- **Sensor interfaces**: MEMS accelerometers/gyros, temperature sensors (often an on-chip ΣΔ + BJT front end), capacitive sensing (CDC = ΣΔ capacitance-to-digital).
- **Communications / RF**: wideband CT ΣΔ in radio receivers, bandpass ΣΔ (MHz–GHz BW, lower resolution).
- **Seismic / geophysical**: 24–32-bit ultra-low-noise.

## 4. Tiny Tapeout analog constraints and PCB

### Analog spec (https://tinytapeout.com/specs/analog/)
- ua[0..5] usable (6 max). Pins must be used in order from 0. Only pins you paid for connect to pads.
- Path: through the `tt_asw_3v3` analog switch, **<500 Ω, <5 pF, ≤4 mA**. No bandwidth figure given.
- Supplies: VDPWR 1.8 V; **VAPWR 3.3 V** optional (needs the `_3v3` template and `uses_3v3: true`). ~0.1 V drop at 20 mA. IHP templates offer no VAPWR.
- Metal 5 is forbidden (power grid). Power stripes are vertical met4, ≥1.2 µm wide.
- Tile sizes: analog must be 1x2 (~160x225 µm) or 2x2 (~334x225 µm).
- Cost: €70 per tile (min €140); analog pins €40 each for the first 2, then €100 each. A 1x2 with 2 pins costs €220.

### PCBs (cloned under pcb/)
- **tt-demo-pcb** (TT04 onward): carries the breakout board. RP2040 (newer boards: RP2350) runs MicroPython with the TT SDK. It selects the project through a mux, generates the project **clock up to ~50 MHz**, drives ui/uio, and reads uo/uio. Also: DIP switches, 7-segment display, USB-C, PMOD headers (in/bidir/out), and a 1x24 top header (power + mux control). The TT06 demoboard had very-low-value resistors that **must be removed or replaced for analog projects** (errata on the tt06 tag).
- **breakout-pcb**: QFN chip carrier. Analog I/O access:
  - TT06/TT07 boards: ipex/u.fl connectors (hard to use, higher capacitance)
  - **TT08 board onward: 100-mil headers per analog bank**, also routed to demoboard headers for custom host boards and pull-downs
  - Other variants: IHP/GF/sky QFN, sockets, dip-dock, ASIC-simulator
- **ETR / current board** (RP2350): removable breakout, PMODs (audio, VGA, 7-seg, QSPI flash/PSRAM, gamepad), hardware-in-the-loop testing with microcotb. GF dies are wire-bonded and not removable.
- **Current demoboard = tt-demo-pcb main branch, "ETR dbv3"** (RP2350, schematic at `pcb/tt-demo-pcb/doc/tt-etr-dbv3.pdf`). Since TT06, analog signals come out on a **100-mil header directly on the demoboard** (photo: `pcb/tt-demo-pcb/doc/img/tt-etr-dbv3-analog.jpg`). Older boards are documented in `doc/historic/`.
- **tt-micropython-firmware**: SDK for driving the chip from the MCU.
- The demo board has **no precision ADC or DAC for analog test**. For an ADC test you bring your own: a low-noise source (an audio DAC or precision signal generator), a low-jitter clock (important for CT ΣΔ; the RP2040 PLL clock is jittery), and bitstream capture by FPGA, logic analyzer, or RP2040 PIO, then decimate in software or FPGA.
- Links: https://github.com/TinyTapeout/tt-demo-pcb · https://github.com/TinyTapeout/breakout-pcb · https://github.com/TinyTapeout/pcb-files · https://tinytapeout.com/specs/pcb/ · https://tinytapeout.com/specs/pcb-etr/
