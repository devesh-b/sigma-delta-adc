# Case study target: Microchip MCP3421

Datasheet: `datasheets/mcp3421.pdf` (DS22003E, 2009). Text extract: `datasheets/mcp3421.txt`.

## Key specs (VDD 5 V, PGA 1, 25 °C unless noted)
| Parameter | MCP3421 | Notes |
|---|---|---|
| Architecture | ΔΣ ADC + PGA + 2.048 V ref + oscillator + I²C | internals not published |
| Resolution / rate | 12 b @ 240 SPS, 14 b @ 60, 16 b @ 15, **18 b @ 3.75 SPS** | no missing codes (by design) |
| Input | differential ±2.048 V / PGA (FSR 4.096 V / PGA) | CM range VSS−0.3 … VDD+0.3 |
| PGA | x1, x2, x4, x8 | |
| Output noise | **1.5 µV rms** @ 3.75 SPS | ≈ 20 bit rms over the 4.096 V FSR |
| INL | **10 ppm FSR typ**, 35 max | ≈ 41 µV |
| Offset | 15 µV typ, 40 max; drift 50 nV/°C | self-calibrated every conversion |
| Gain error | 0.05 % typ, 0.35 max; drift 15 ppm/°C | includes VREF |
| Reference | 2.048 V ± 0.05 %, 15 ppm/°C | |
| CMRR / PSRR (DC) | 105–110 dB / 100 dB | |
| Input impedance | 2.25 MΩ / PGA diff (3.2 pF sampling cap), 25 MΩ CM | switched-cap input |
| Power | 155 µA @ 5 V, 145 µA @ 3 V; standby 0.1 µA | one-shot mode |
| Supply / temp | 2.7–5.5 V; −40 … +125 °C | |
| Anti-alias filter | "internal first order sinc filter" (§4.7) | external RC recommended |
| Applications | weigh scales, RTD/thermocouple/thermistor, bridge sensors, portable instruments, fuel gauges | |

### Architecture hints (my inference, not stated in the datasheet)
- (2^bits) × rate is constant: 4096×240 = 16384×60 = 65536×15 = 262144×3.75 = **983 kHz**. Rate drops 4× for every 2 bits gained, which fits a **1st-order incremental ΣΔ** clocked near 1 MHz with a counter/sinc1 decimator.
- On the other hand, 2.25 MΩ from 3.2 pF gives f = 1/(Z·C) ≈ 139 kHz sampling, so the modulator might run slower and use a higher order or include calibration phases. Unknown. Either way it is a slow, DC-precision, incremental converter.

## Feasibility on Tiny Tapeout sky130
| Spec | Doable on TT? | Why |
|---|---|---|
| 12–18 bit **resolution**, 3.75–240 SPS | **Yes** | a 1-bit ΣΔ is inherently linear; the decimator is digital and tiny. Quantization noise at OSR ≥ 4096 is not the problem. |
| Differential input, PGA x1–8 | Yes | SC cap ratios; needs 2 analog pins (€80) |
| ±2.048 V input range | Partly | needs the 3.3 V VAPWR rail (`uses_3v3`); 1.8 V domain cannot swing 4 V differential |
| 1.5 µV rms noise | **Very hard** | kT/C is fine with heavy averaging (1 pF → 64 µV/sample → ~0.1 µV after 262k samples), but sky130 **1/f noise** and on-chip digital noise from neighbours dominate at DC → requires **chopping / auto-zero** (MCP3421 self-calibrates each conversion). Realistic first-chip target: 10–50 µV rms. |
| 10 ppm INL | Hard | needs high OTA gain (≥ 80–90 dB for a leaky-integrator-free incremental loop) and a linear input sampling path; the TT analog switch (tt_asw_3v3, <500 Ω) adds some error. ~100 ppm is realistic. |
| 15 µV offset | Medium | achievable with chopping + digital offset calibration (convert a shorted input, subtract) |
| 2.048 V ±0.05 %, 15 ppm/°C ref | **No (untrimmed)** | there are no fuses/OTP on TT; a sky130 bandgap is ±1–2 % / 20–50 ppm/°C untrimmed. Workarounds: external reference pin, or software calibration using digital trim bits loaded over I²C/pins. |
| CMRR/PSRR 100 dB | Hard | fully differential + chopping help; TT supply has ~0.1 V IR drop and shared-rail noise |
| 145 µA | Yes | low-speed OTA |
| I²C interface | Yes | digital Verilog; fits in the mixed-signal tile or uses ui/uo pins |
| 2.7–5.5 V, −40…125 °C | No / untestable | TT rails are fixed at 1.8 / 3.3 V |

## Verdict: partially delulu. The architecture is fine; the precision numbers are not achievable on a first chip.
The MCP3421 class (slow, DC, incremental ΣΔ) is actually the **best fit for TT**. It needs low bandwidth, a low clock (~1 MHz, easy for the RP2040, so jitter doesn't matter), a small digital back end, and few pins. The hard part is analog precision (noise, INL, reference), not speed.

### Proposed spec tiers
| Tier | Goal |
|---|---|
| **v1 (realistic)** | fully differential SC **incremental ΣΔ** (1st → 2nd order), 1-bit, chopped input, ~1 MHz clock, on-chip sinc/counter decimator, 12/14/16-bit modes at 240/60/15 SPS, **≥14 ENOB-ish (≤ 50 µV rms) at 15 SPS**, INL ≤ 100 ppm, PGA x1/x2, external VREF pin + on-chip bandgap option, digital readout (shift register/SPI first, I²C as a stretch) |
| v2 (stretch) | 2nd-order CIFF, CDS/chopper OTA, 18-bit mode, ≤ 5 µV rms, INL ≤ 30 ppm, trimmable bandgap with digital trim + per-die calibration |
| MCP3421 parity | 1.5 µV, 10 ppm, 0.05 % ref: commercial-grade, needs trimming, a quiet process/package, and iteration |

The gaps from section 2 of NOTES.md line up with v1: no prior TT sky130 ΣΔ is incremental, differential, chopped, or has an on-chip decimator.
