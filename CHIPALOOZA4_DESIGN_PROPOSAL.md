# Chipalooza Challenge #4 proposal: second-order incremental ΣΔ ADC with on-block decimation (sky130)

This proposal follows the contents list of rule 6. The equipment list (6.6) and the designers' CVs (6.7) are sent separately.

## 1. Type of IP block

**Precision DC analog-to-digital converter.** A fully differential, second-order, 1-bit, discrete-time switched-capacitor **incremental** ΣΔ ADC, with the decimating accumulators inside the block.

It is meant as the measurement front end of an SoC for slow, accurate signals:
- sensors, bridges, RTDs and thermistors, read ratiometrically;
- battery and supply monitoring;
- housekeeping.

The design point follows the class of the Microchip MCP3421 (18-bit ΔΣ, 2.048 V full scale). Parity with that part is not claimed.

The open-source sky130 analog ΣΔ designs we found are all first order and have no on-chip decimation. This block adds:
- second-order noise shaping;
- incremental (resettable, multiplexing-friendly) conversion;
- on-block decimation;
- chopping for µV-level offset;
- a standard SPI read port.

## 2. List of I/O, including test ports

The block's own port list is the IP interface. The slot mapping uses the resources in rule 7. The organisers expect a slot of about 1200 × 400 µm (not final).

**Supplies.**

| Port | Dir | Description |
|---|---|---|
| VAPWR / VSSA | supply | 3.3 V analog supply (3.0–3.6 V) |
| VDPWR / VSSD | supply | 1.8 V digital supply (1.62–1.98 V) |

**Analog ports.**

| Port | Dir | Description | Slot resource |
|---|---|---|---|
| VIN+, VIN− | in | Differential input, sampled at fs | 2 dedicated analog pads |
| VREF+ | in | External reference, 1.0–2.048 V (nominal 2.048 V) | 1 dedicated analog pad |
| VREF− | in | Reference return, Kelvin to the sensor ground | 1 shared analog line (agreed with the organisers); fallback: tied to VSSA in the slot |
| BIAS_EXT | in | Bandgap-referenced bias current. With bias_sel = 1 it replaces the internal bias reference, and all bias currents follow it. Range 2.5–10 µA, nominal 5.25 or 5.5 µA (harness fine-mode steps of 250 nA) | Harness current source 1 |
| AMON[1:0] | out (test) | Buffered DC monitors: bias-reference voltage and CM reference | 2 shared analog lines |

**Digital ports.**

| Port | Dir | Description | Slot resource |
|---|---|---|---|
| clk | in | Clock, 48 MHz nominal; fs = clk / divider | Control input |
| rst_n | in | Asynchronous reset, synchronous release | Control input |
| cfg_clk, cfg_dat, cfg_ld | in | Serial configuration write | 3 control inputs |
| bias_sel | in | 0 = internal bias reference, 1 = BIAS_EXT; change only during reset | Control input |
| addr[2:0], bsel | in | Read word select (acc1 hi/lo, acc2 hi/lo, tag, status) and byte select | 4 control inputs |
| rd | in | Frame acknowledge | Control input |
| dbg | in | Debug bus select | Control input |
| spi_en | in | 1 = SPI read mode | Control input |
| spi_sck, spi_cs_n | in | SPI clock and chip select | 2 control inputs |
| data[7:0] | out | Read bus byte. Debug mode: bitstream, bit clock, valid, analog reset, chop phase, invalid. SPI mode: data[0] = MISO | 8 test outputs |
| frame_ready, overrun | out | Frame status; frame_ready is the data-ready (DRDY) signal | 2 test outputs |
| bias_ok | out (test) | Bias-good from the bias reference | Test output |
| y_raw | out (test) | Raw modulator bitstream | Test output |

**Resource use:** 3 of 3 dedicated pads, 3 of 4 shared analog lines, 1 of 2 bias currents, 16 of 24 control inputs, 12 of 12 test outputs.

## 3. Functional description

**Signal path.**
- VIN+ and VIN− are sampled differentially onto 0.5 pF MIM capacitors with bottom-plate sampling.
- CM-rejecting input switching lets the converter accept any input common mode from 0 to VREF.
- Two switched-capacitor integrators form a CIFB loop (c1 = 0.125, c2 = 0.5, k = 0.5).
- A latched comparator closes the loop as a 1-bit quantiser.
- The feedback DAC switches between VREF+ and VREF−. The result is therefore VIN/VREF, so reference drift cancels in ratiometric measurements.

**Analog blocks:**
- OTA1: folded cascode with switched-capacitor CMFB and a slow integrating CMFB path;
- OTA2: a scaled copy of the OTA1 cell;
- latched comparator;
- non-overlapping phase generator, switches and 1.8 V ↔ 3.3 V level shifters;
- trimmable constant-current bias reference with a bias-good signal, selectable against the external BIAS_EXT;
- common-mode reference.

**Incremental operation.**
- Each conversion resets both integrators, then runs N = 64, 256, 1024 or 4096 clock cycles. A frame is N + 2 cycles.
- The loop starts from a known state, so the input follows exactly from the two accumulator values.
- The remaining quantisation error falls as 1/N².
- Conversions are independent, so an external multiplexer can switch channels between them with no settling penalty.

**Chopping.**
- System chop swaps the input polarity between the two halves of a conversion pair. This cancels offset and 1/f noise.
- OTA1 chop is optional.

**Digital section** (a hardened standard-cell macro inside the block):
- second-order cascade-of-integrators decimator (two 32-bit accumulators);
- sequencer for reset, conversion, chop phase and frame counting;
- serial configuration register for order, N, fs divider, chop modes, bias boost and bias trim;
- hold register with frame-ready and overrun flags;
- power-good hold, so conversions start only once the supplies and bias are good.

The host does the final scaling and chop demodulation, which is two adds and a shift per frame. A reference decoder in C and Python is provided.

**Read-out.** There are two ways to read a frame.
- **Parallel byte bus.** Select a word with addr and a byte with bsel, then acknowledge with rd. Suits an FPGA or logic analyser; in an SoC the native 16-bit port is used directly.
- **SPI** (target, mode 0, MSB first, read-only), for direct connection to a microcontroller:
  - When CS_n falls, the block takes a consistent 96-bit snapshot of the frame (status, acc1, acc2, tag) and shifts it out on MISO.
  - SCLK runs up to 12 MHz and need not be related to clk. A frame takes 8 µs to read.
  - frame_ready serves as DRDY.
  - A lost frame shows as a gap in the frame counter.

I²C, as on the MCP3421, can be added later if the harness provides a bidirectional pad.

**Modes.**

| Mode | fs | N | Output |
|---|---|---|---|
| Precision | 0.25–2 MHz | 4096 | Frames averaged to 3.75–240 SPS |
| Fast | 4 MHz, bias boost on | 64 / 256 / 1024 | Up to about 60 kSPS |
| First-order | — | — | Second integrator bypassed; for comparison and as a fallback |

## 4. Target specification

Conditions unless stated: VAPWR 3.3 V, VDPWR 1.8 V, VREF 2.048 V, 27 °C, precision mode, fs 2 MHz, N 4096, system chop on.

The design is checked across process corners (tt, ss, ff, sf, fs), −40 to 125 °C and supplies ±10 %.

**Accuracy.**

| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| Input range (differential) | −0.9·VREF | | +0.9·VREF | ±1.84 V at VREF 2.048 V; overload to 1.1·VREF recovers on the next conversion |
| Input common mode | 0 | | VREF | |
| Output word | | 32-bit accumulators | | Effective resolution set by noise |
| Input-referred noise, 15 SPS | | 1 µV rms | 2.5 µV rms | |
| Input-referred noise, 240 SPS | | | 5 µV rms | |
| INL, precision modes | | 3.4 ppm FSR | 20 ppm FSR | |
| INL, fast mode | | | 200 / 20 / 5 ppm FSR | At N 64 / 256 / 1024 |
| Offset | | | 5 µV | System chop on |
| Gain error | | | 0.5 % | Ratiometric, so the reference is excluded |
| CMRR | 100 dB | | | 60 dB minimum with system chop off |

**Timing.**

| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| Frame rate | | fs/(N+2) | | 1.95 kSPS at 2 MHz, N 1024; 60 kSPS at 4 MHz, N 64 |
| Start-up | | 2^16 fs cycles + 256 | | Power-good hold |
| SPI SCLK | | | 12 MHz | |

**Supplies and ambient.**

| Parameter | Min | Typ | Max | Notes |
|---|---|---|---|---|
| VAPWR | 3.0 V | 3.3 V | 3.6 V | |
| VDPWR | 1.62 V | 1.8 V | 1.98 V | |
| VREF | 1.0 V | 2.048 V | 2.048 V | |
| Analog current, precision | | 110 µA | 200 µA | Includes the bias reference |
| Analog current, fast (boost) | | 185 µA | 200 µA | |
| Digital power | | 1.7 mW | | Estimate at clk 48 MHz |
| BIAS_EXT | 2.5 µA | 5.25–5.5 µA | 10 µA | When bias_sel = 1 |
| Operating temperature | −40 °C | | 125 °C | The 0.25 MHz, N 4096 mode is derated to 100 °C |

**Absolute limits** (to be confirmed against the pad library):
- VAPWR: 3.63 V maximum.
- VDPWR: 1.98 V maximum.
- VIN±, VREF±: VSSA − 0.3 V to VAPWR + 0.3 V.
- Current into any analog pad: 4 mA maximum.

## 5. Outline of the test plan

**Setup:**
- a low-noise board with an external 2.048 V reference;
- a precision DC source;
- a microcontroller host on SPI.

**Measurements:**
1. Functional: configuration, frame read over SPI and over the byte bus, start-up.
2. Noise against conversion rate (shorted input).
3. INL and gain error (stepped DC input, ratiometric).
4. Offset, with chop on and off.
5. CMRR.
6. Supply current and supply sensitivity.
7. Internal bias reference against the harness BIAS_EXT.
8. Temperature.

---

The design is released under Apache 2.0. Every design file and check runs on open-source tools.
