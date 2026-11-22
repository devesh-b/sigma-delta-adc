# Chipalooza Challenge #4 proposal: second-order incremental ΣΔ ADC with on-block decimation (sky130)

*Draft 2026-11-21 for the author to edit before the 23 November 2026 proposal deadline. It follows the content list in rules item 6 (block type, I/O, functional description, target specification, test plan). Equipment list and CVs are sent separately, as the rules ask. No personal or institutional details appear in this document because it becomes part of the block's repository documentation. Numbers come from `SPEC.md` and `DESIGN_BOOK.md`. Values marked PENDING are not yet verified.*

## 1. Type of IP block

**Precision DC analog-to-digital converter.** It is a fully differential, second-order, 1-bit, discrete-time switched-capacitor **incremental** ΣΔ ADC. The decimating accumulators are part of the block. It is meant as the measurement front end of an SoC for slow, accurate signals: sensors, bridges, RTDs and thermistors read ratiometrically, battery and supply monitoring, and housekeeping. The design point follows the class of the Microchip MCP3421 (18-bit ΔΣ, 2.048 V full scale). Parity with that part is not claimed.

The sky130 analog ΣΔ designs found in an open-source survey are all first order and have no on-chip decimation. This block adds:
- the second order;
- incremental (resettable, multiplexing-friendly) conversion;
- on-block decimation;
- chopping for µV-level offset.

## 2. Functional description

**Signal path.** VIN+ and VIN− are sampled differentially onto 0.5 pF MIM capacitors with bottom-plate sampling. CM-rejecting input switching shorts the top plates, so the converter accepts any input common mode between 0 and VREF.
- Two SC integrators (Cint1 = 4 pF) form a CIFB loop with c1 = 0.125, c2 = 0.5 and k = 0.5.
- A latched comparator closes the loop as a 1-bit quantiser.
- The 1-bit feedback DAC switches between VREF+ and VREF−, so the conversion is **ratiometric**: the result is VIN/VREF, and reference drift cancels in bridge and divider measurements.

**Analog blocks:**
- OTA1: folded cascode with switched-capacitor CMFB plus a slow integrating CMFB path;
- OTA2: a 9/16-scaled copy of the OTA1 cell;
- latched comparator;
- non-overlapping phase generator, switches and 1.8 V ↔ 3.3 V level shifters;
- trimmable constant-current bias reference with a bias-good signal;
- common-mode reference string.

**Incremental operation.** Each conversion resets both integrators and runs N = 64, 256, 1024 or 4096 clock cycles. Each frame takes N + 2 cycles, which includes a 2-cycle reset window. Because the loop starts from a known state, the input follows exactly from the two accumulator values. The leftover quantisation error falls as 1/N²: about 33 µV at N = 1024 and 2 µV at N = 4096. Each conversion is independent, so an external multiplexer can switch channels between conversions without settling or latency penalty.

**Chopping.**
- **System chop** swaps the input polarity between the two sub-conversions of a pair, which cancels offset and 1/f noise.
- **OTA1 chop** is optional and always paired with system chop.

**Digital section** (hardened standard-cell macro inside the block):
- a second-order cascade-of-integrators decimator (two 32-bit accumulators);
- a sequencer for reset, conversion, chop phase and frame counting;
- a serial configuration register for order, N, fs divider, chop modes, bias boost and the 3-bit bias trim;
- a hold register with frame-ready and overrun flags;
- a power-good hold, which starts conversions only after 2^16 cycles and once bias-good has been high for 256 consecutive cycles.

The final scaling (acc2 + 4·acc1, then normalisation) and chop demodulation are two adds and a shift per frame, done by the host processor. A reference decoder in C and Python is part of the deliverables.

**Modes.**

| Mode | fs | N | Output |
|---|---|---|---|
| Precision | 0.25–2 MHz | 4096 | Frames averaged to 3.75–240 SPS |
| Fast | 4 MHz, bias boost on | 64 / 256 / 1024 | Up to about 60 kSPS frame rate |
| First-order fallback | — | — | Second integrator bypassed; for characterisation and as a safety net |

## 3. Interface and I/O (including test ports)

The block's own port list is the IP interface. The mapping to the Chipalooza slot follows the resources in rules item 12 and is a proposal: slot size and I/O configuration are still TBD in the harness.

**Supplies.**

| Port | Dir | Description |
|---|---|---|
| VAPWR / VSSA | supply | 3.3 V analog supply (3.0–3.6 V) |
| VDPWR / VSSD | supply | 1.8 V digital supply (1.62–1.98 V) |

**Analog ports.**

| Port | Dir | Description | Slot mapping |
|---|---|---|---|
| VIN+, VIN− | in | Differential input, sampled at fs (charge kicks at fs) | 2 dedicated analog pads |
| VREF+ | in | External reference, 1.0–2.048 V (nominal 2.048 V) | 1 dedicated analog pad |
| VREF− | in | Reference return (Kelvin to the sensor ground) | Tied to VSSA inside the slot (see note) |
| BIAS_EXT | in | Bandgap-referenced current from the harness. When `bias_sel` = 1 it replaces the internal bias-reference master current, and all bias currents follow it ratiometrically. Fallback if the on-chip reference misbehaves on silicon | Harness current source 1 |
| AMON[1:0] | out (test) | Buffered DC monitors: bias-reference voltage and CM reference, switch-selected (proposed, not yet designed) | 2 of the 4 shared analog lines |

**Digital ports.**

| Port | Dir | Description | Slot mapping |
|---|---|---|---|
| clk | in | Digital clock (48 MHz nominal); fs = clk / divider | Control input |
| rst_n | in | Asynchronous reset, synchronous release | Control input |
| cfg_clk, cfg_dat, cfg_ld | in | Serial configuration write | 3 control inputs |
| bias_sel | in | 0 = internal bias reference, 1 = BIAS_EXT. Static; change only while rst_n is low | Control input |
| addr[2:0], bsel | in | Read word select (acc1 hi/lo, acc2 hi/lo, tag, status) and byte select | 4 control inputs |
| rd | in | Frame acknowledge | Control input |
| dbg | in | Debug bus select | Control input |
| data[7:0] | out | Read bus byte; in debug mode: bitstream y, bit clock, valid, rst_analog, chop phase, invalid | 8 test outputs |
| frame_ready, overrun | out | Frame status | 2 test outputs |
| bias_ok | out (test) | Bias-good from the analog bias reference | Test output |
| y_raw | out (test) | Raw modulator bitstream | Test output |

That uses 13 of 24 control inputs and 12 of 12 test outputs.

**Byte-select read bus.** The digital macro keeps its native registered 16-bit read port. A small wrapper cell (`cz_bus8`) outputs bus[7:0] when bsel = 0 and bus[15:8] when bsel = 1. Each 16-bit word is read as two bytes, and a byte is valid one mux delay after bsel changes. In an SoC the 16-bit port can be used directly.

**VREF− (request to the organisers).** The design has a Kelvin VREF− input. **Baseline:** with three dedicated pads, VREF− is tied to VSSA inside the slot. The block is designed to meet its specification in this configuration; ground drop in the slot appears as a small, calibratable gain error. **Request:** if the harness allows, we would like either of the following for a true Kelvin reference return. Either is optional, and the design does not depend on it:
- a fourth dedicated pad for VREF−;
- VREF− on one of the shared analog lines (DC only, but it carries the DAC charge kicks at fs).

## 4. Target specification

Conditions, unless stated otherwise:
- VAPWR 3.3 V, VDPWR 1.8 V, VREF 2.048 V, 27 °C;
- precision mode, fs 2 MHz, N 4096, system chop on.

Verification covers process corners tt, ss, ff, sf and fs plus two R+C points, temperatures −40, 27 and 125 °C, both supplies ±10 %, and Monte Carlo. Post-layout verification is planned at the same corners. The 125 °C range is wider than the 110 °C the rules accept.

**Accuracy.**

| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| Input range (differential) | −0.9·VREF | | +0.9·VREF | ±1.84 V at VREF 2.048 V; overload up to 1.1·VREF recovers on the next conversion |
| Input common mode | 0 | | VREF | CM-rejecting switching |
| Resolution (accumulator output) | | 32-bit words | | Effective resolution set by noise |
| Input-referred noise @ 15 SPS | | 0.94 µV (model floor) | 2.5 µV rms | At fs ≥ 2 MHz; at 0.25 MHz, 3.0 µV is allowed at 125 °C |
| Input-referred noise @ 240 SPS | | | 5 µV rms | |
| INL, precision modes | | 3.4 ppm (model floor) | 20 ppm FSR | Transistor-level in-loop OTA1 gate: ≤ 0.74 ppm at the corners run |
| INL, fast mode | | | 200 / 20 / 5 ppm | At N 64 / 256 / 1024 |
| Offset | | | 5 µV | System chop on |
| Gain error | | | 0.5 % | Ratiometric, so it excludes the reference |
| CMRR | 100 dB | | | 60 dB minimum with system chop off |

**Timing.**

| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| Frame rate | | fs/(N+2) | | 1.95 kSPS at 2 MHz, N 1024; 60 kSPS at 4 MHz, N 64 |
| Start-up | | 2^16 fs cycles + 256 | | Power-good hold; the first chop pair is flagged invalid |

**Supplies and ambient.**

| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| Analog current, precision | | 106–113 µA | 200 µA | Includes the bias reference |
| Analog current, fast (boost) | | 172–193 µA | 200 µA | PENDING: full-chip simulation |
| Digital power | | 1.7 mW (estimate) | | Place-and-route estimate at default activity, clk 48 MHz |
| VAPWR | 3.0 V | 3.3 V | 3.6 V | |
| VDPWR | 1.62 V | 1.8 V | 1.98 V | |
| VREF | 1.0 V | 2.048 V | 2.048 V | |
| Temperature (verified) | −40 °C | | 125 °C | 0.25 MHz / N 4096 mode is derated to 100 °C (leakage) |

**Absolute limits.** These are to be confirmed against the pad library.
- VAPWR: 3.63 V maximum (sky130 3.3 V device rating, 3.3 V + 10 %).
- VIN±, VREF±: VSSA − 0.3 V to VAPWR + 0.3 V (pad ESD diodes).
- Pad current: ≤ 4 mA per analog pad.
- VDPWR: 1.98 V maximum.
- Internal 1.8 V devices on the 3.3 V supply are held to project stress rules:
  - gate-oxide and Vds ≤ 1.98 V sustained;
  - ≤ 2.2 V for < 1 ns;
  - junctions ≤ 4.95 V.

## 5. Design and verification method

All design files are open and run on open-source tools: ngspice, xschem, magic, netgen, KLayout, Yosys, LibreLane and Icarus or Verilator, on the IIC-OSIC-TOOLS image.

The flow is gated, from system to block to top level. Every gate:
- takes its limit from a frozen, change-logged specification;
- prints ACCEPT or REJECT;
- fails on missing data;
- has a deliberately broken circuit copy that must REJECT, so that a passing check is shown to be able to fail.

Model tiers:
1. a Python behavioural model;
2. behavioural SPICE;
3. transistor-level blocks inside the loop (the OTA is judged by in-loop INL);
4. post-layout extraction.

The digital macro has its own reference model, golden vectors, mutation testing, formal properties and multi-corner static timing.

AI tools assisted the design work. Nothing in the repository needs AI to use, verify or modify the block: every check is a script plus open-source tools.

## 6. Test plan for silicon validation

Board:
- a low-noise, low-thermal-EMF board with an external 2.048 V reference;
- a precision DC source or calibrator, with a reversing switch for thermal-EMF cancellation;
- a host reading the slot's digital outputs (logic analyser or MCU).

Measurements:
1. **Functional check.** Configuration write and read back; frame counter; bitstream on y_raw; power-good hold timing; bias_ok.
2. **Noise.** Shorted input, versus N and fs, chop on and off: µV rms at 3.75, 15, 60 and 240 SPS.
3. **INL and gain.** Stepped precision DC source over ±0.9·VREF, ratiometric (source and VREF from the same reference). Best-fit-line INL in ppm FSR at N 4096 and in fast mode at N 64, 256 and 1024.
4. **Offset.** With system chop on and off, and with OTA chop.
5. **CMRR.** Input common mode swept from 0.2 to 2.0 V, chop on and off.
6. **Supply.** Analog and digital current per mode and boost setting; supply sensitivity over 3.0–3.6 V.
7. **Bias.** Trim range and the trim calibration rule; internal against harness bias current (if BIAS_EXT is accepted); AMON monitors.
8. **Temperature.** Chamber or hot plate, 0–85 °C at least, plus the derating of the 0.25 MHz mode.
9. **First-order fallback mode** as a comparison.

Results will be published with the measurement scripts in the repository.

## 7. Deliverables

- Public repository under Apache 2.0, following the Chipalooza repository template. It holds:
  - xschem schematics;
  - SPICE netlists;
  - magic and GDS layout, both standalone and in the slot wrapper;
  - RTL;
  - LibreLane configuration and the hardened macro;
  - all testbenches and gate scripts with their broken copies;
  - the behavioural model;
  - DRC, LVS and PEX sign-off results with summary plots;
  - a full behavioural description;
  - the reference decoder.
- Standalone layout sized to the block, not expanded to fill the slot.

## 8. Status (2026-11-21)

- **Specification:** frozen, with a change log. Full behavioural model and golden vectors exist.
- **Schematics:** done for all blocks. xschem schematics match the generator netlists (11 of 11 cells) and each match has a broken copy.
- **OTA1:** the precision-mode in-loop INL gate passes at transistor level (worst corner 0.165 ppm, solver-converged).
- **OTA2:** precision rows pass. The fast-mode output swing at hot corners is open.
- **Comparator:** final revision selected.
- **Bias reference:** DC and start-up rows pass. Trim and boost rows are being fixed.
- **Digital macro:** hardened, DRC, LVS and antenna clean, gate-level simulation in progress.
- **Layout:** MIM capacitor arrays and the bias resistor are DRC/LVS clean. The active cells and the top-level assembly are in progress.
- **Not started:** full post-layout verification.

The Chipalooza schedule fits this state:
- schematic review, week of 28 Dec 2026;
- layout and post-layout review, week of 1 Feb 2027;
- final integration, week of 22 Feb 2027.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Digital-to-analog coupling in one block | Placement separation, guard rings, quiet sampling instants; measured on silicon |
| Fast-mode current close to the 200 µA budget | Bias-boost trim; fast mode can be dropped to precision-only without other changes |
| Precision-layout parasitics (MIM bottom plate and voltage coefficient are not in the model) | Fully differential, bottom-plate sampling; PEX at all corners; silicon INL |
| Slot I/O limits (VREF− Kelvin, 12 outputs) | Byte-wide read bus; VREF− options for organiser decision |

---
## Notes for the author (delete before sending)

- **Fill in:**
  - the title and a block name for the repository;
  - the equipment list and CVs, sent separately;
  - confirm Apache 2.0.
- **Questions for the organisers** (chipalooza@opencircuitdesign.com or fossi-chat #chipalooza):
  - the slot area (the full block is likely more than 100,000 µm² as sized; OTA1 layout alone is about 27,000 µm²);
  - whether a 48 MHz clock is available on a control input;
  - the VREF− request (4th pad or shared line; optional);
  - the BIAS_EXT current value and range;
  - whether the 12 test outputs can be driven at frame rate.
- **Chipalooza-variant changes (D99, WO-108; the TT design is unchanged):**
  - applied: the byte-select read bus (`cz_bus8` wrapper) and BIAS_EXT with bias_sel (a wrapper around the bias reference);
  - still an option: AMON monitor taps;
  - VREF− is a request, not a dependency (baseline is tied to VSSA).
- **BIAS_EXT current range:** nominal 5.35 µA; the gated range is 2.5–10 µA (0.5× to 2× the OTA bias), with 1 µA and 20 µA reported as info. Confirm the value with the harness.
- **Tiny Tapeout:** dropped as a target (D101); the design does not fit the TT 2×2 tile as sized. Slot area matters: OTA1 alone is about 27,000 µm² in layout today.
- **Overvoltage protection:** the rules ask for it on 1.8 V blocks that face the pad frame. Here only the 3.3 V analog front end faces pads, and the 1.8 V digital section talks to harness logic. Confirm this with the harness.
