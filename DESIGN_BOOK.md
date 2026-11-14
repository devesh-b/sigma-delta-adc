# DESIGN BOOK: tt-iadc, a second-order incremental ΣΔ ADC on Tiny Tapeout (sky130A)

Snapshot: 2026-11-15. Covers SPEC v1 (frozen 2026-11-09) through change-log entry CL-39 and decisions D1 to D90, with results up to WO-88 (2026-11-15 early morning).

## How to read this book

This book explains the design from first principles to the current transistor-level state. It covers the values chosen, the reasons for them, and the evidence behind each one. It is a companion to the governing documents and does not replace them:

| Document | Role | Wins on |
|---|---|---|
| `SPEC.md` | frozen specification + change log (CL-1 … CL-39) | numbers and limits |
| `work/v1-design/DECISIONS.md` | decision log (D1 … D90) | history and who decided |
| `work/v1-design/PLAN.md` | gated plan (S → C → V) | stage gates |
| `design/<block>/DESIGN.md` | per-block design notes | block sizes and hand calculations |
| `work/v1-design/results/*/README.md` | per-work-order evidence (WO-23 … WO-88) | measured (simulated) values |
| `work/v1-design/RESUME.md`, `STATE-2026-11-14.md` | coordinator log and state snapshot | values collected but not yet written into a results file |

**Citation convention.** Every number carries an inline source:
- `SPEC §x` is a SPEC section; `SPEC row` means the per-block table of SPEC §3.0.
- `Dnn` is a decision and `CL-nn` is a SPEC change-log entry.
- `WO-nn` points to `work/v1-design/results/woNN/README.md`, unless a file is named.
- `C1 §x`, `C3 §x`, `C4 §x`, `C6 §x` are sections of `design/c1_ota1/DESIGN.md`, `design/c3_comp/DESIGN.md`, `design/c4_sw/DESIGN.md` and `design/c6_bias/DESIGN.md`.
- `S1` … `S6` are the system-study results in `work/v1-design/results/s*_*.md`.
- `HARD` is `design/c9_digital/HARDENING.md`, `VPLAN` is `work/v1-design/C9_VERIF_PLAN.md`, and `GOLD` is `golden/README.md`.
- `GUIDE`, `CTX`, `ROAD`, `NOTES`, `MCP` and `MODEL` are `DESIGN_GUIDE.md`, `CONTEXT.md`, `ROADMAP.md`, `NOTES.md`, `MCP3421_TARGET.md` and `model/README.md`.

**Status words.** "SIM" means a simulated value, "HAND" a hand calculation and "MODEL" a tier-0 Python result. **PENDING** marks a value whose run had not been collected as of 2026-11-15; the WO that will settle it is named next to it. "Coordinator note 2026-11-15" marks a value the coordinator collected from a sandbox pool that is not yet in a results file (see Appendix E).

## Proposal summary

Status 2026-11-15. This section only summarises; every row points to the section of the book that holds the numbers and their sources. Values that are not final are marked PENDING.

**What the design is.** A second-order, 1-bit, discrete-time incremental ΣΔ ADC for a 2×2 analog tile on sky130A Tiny Tapeout (II.1.2; II.2.1–II.2.3). The modulator is a fully differential switched-capacitor CIFB loop with c1 0.125, c2 0.5, k 0.5 (II.2.3), Cs 0.5 pF and Cint1 4 pF (II.2.5). The reference is external and ratiometric, VREF 2.048 V on ua2 with a Kelvin REF− on ua3 (II.1.2; II.2.4). Each conversion resets the loop and runs N = 64 / 256 / 1024 / 4096 cycles at fs 0.25–2 MHz (precision) or 4 MHz with bias boost (fast) (II.2.6; II.2.7). A cascade-of-integrators decimator, sequencer, configuration register and 16-bit read bus live in a hardened digital macro inside the analog tile (III.6).

**Targets against the case-study part and prior TT designs.**

| | This design (SPEC targets) | MCP3421 (datasheet) | Prior analog ΣΔ on TT sky130 |
|---|---|---|---|
| Architecture | 2nd-order DT SC incremental, fully differential, 1-bit; the two CoI decimating accumulators are on chip, the final scaling (acc2 + 4·acc1, normalisation) and chop demodulation run in firmware | ΔΣ + PGA + internal reference + oscillator + I²C | 1st order (CT: Paul Thomas ttsky26c, single-ended; SC: tilesos dual ADC, ttsky26c; CT: shimomi ttsky26a, "first-order 1-bit continuous-time DSM"); no on-chip decimator |
| Noise | ≤ 2.5 µV rms @ 15 SPS at fs ≥ 2 MHz across corners (0.25 MHz: ≤ 2.5 µV to 85 °C, ≤ 3.0 µV at 125 °C, D27); ≤ 5 µV @ 240 SPS. Tier-0 model, intrinsic floor: 0.94 µV (V.4) | 1.5 µV rms @ 3.75 SPS | Paul Thomas: ≈ 57 dB SNDR precision (≈ 100 kHz band), ≈ 40 dB fast (≈ 1 MHz band), simulated. SNDR over a band is a different metric from µV rms at DC and is not directly comparable |
| INL | ≤ 20 ppm FSR in the precision modes; fast mode N 64 ≤ 200 ppm, N 256 ≤ 20 ppm, N 1024 ≤ 5 ppm (SPEC §1). Tier-0 model, intrinsic floor: 3.4 ppm (V.4) | 10 ppm typ, 35 max | not reported |
| Offset / gain error | ≤ 5 µV / ≤ 0.5 %; ratiometric, so the gain error excludes the reference | 15 µV typ / 0.05 % typ; the gain error includes the internal reference | not reported |
| CMRR | ≥ 100 dB with system chop; ≥ 60 dB without | 105–110 dB | not reported |
| Reference | external, ratiometric 2.048 V | internal 2.048 V | — |
| Supply current, analog (VAPWR) | ≤ 200 µA design budget; fast mode ≈ 180 µA nominal by reasoning, not simulated (needs C2) | 145 µA @ 3 V, whole chip | — |
| Digital power (VDPWR) | C9 macro 1.705 mW at LibreLane default switching activity (WO-73), ≈ 0.95 mA at 1.8 V; an estimate, not a measurement | included in the 145 µA | — |
| Silicon data | none yet | product | none measured; the only measured analog ADC among the references is Wulff's tt06 SAR (≈ 7 ENOB) |

Sources: II.1.1 (MCP3421 and prior art); II.1.3 (budgets); `NOTES.md` (survey table, prior-design rows); SPEC §1 (targets). The "tier-0 model" numbers are the intrinsic floor of the Python model: they exclude reference noise, board noise, digital coupling and PEX (V.4). The design aims at DC precision and resolution, not bandwidth (II.1.1). MCP3421 parity is not claimed: the on-chip reference and 10 ppm INL are out of reach on a first chip (II.1.1). The current rows are not comparable as totals: the MCP3421's 145 µA covers the whole chip, while this design's 200 µA is an analog-only budget and its digital macro alone is estimated at ≈ 0.95 mA.

**What is new on TT.** The prior-art statements below come from a keyword survey of titles and descriptions over 29 shuttles up to ttsky26c (index.tinytapeout.com, 2026-11-07; NOTES §1). A project with an unusual name could be missing.
- **Order 2.** The three analog ΣΔ modulators found on TT sky130 (Paul Thomas, tilesos, shimomi) are all 1st order (II.1.1; NOTES).
- **Incremental operation** with an exact reconstruction formula from the two accumulators; the residual quantisation error falls as 1/N² (≈ 33 µV at N 1024, ≈ 2 µV at N 4096, I.5.4). Each conversion is independent and N trades rate for resolution (I.5; II.2.1).
- **Decimating accumulators in the analog tile.** To our knowledge from that survey, this is the first analog ΣΔ modulator on TT sky130 with its decimating accumulators (2nd-order CoI) in the same analog tile, hardened as a separate LibreLane macro (III.6). The final scaling and the chop demodulation run in firmware (SPEC §3.7; I.5.3). Digital-only decimators exist on TT: TTSKY26A-ADC-8BIT has an on-chip sinc1 counter, and tt09-decimation_filter and tt09-delta-sigma-decimation-filter are standalone filter projects (NOTES §1).
- **Chopping:** system chopping (input polarity swap between the two sub-conversions of a pair) and optional OTA1 chopping, always paired with system chop (II.2.8; D18).
- **CM-rejecting input switching** by top-plate shorting (II.2.10; D12).

**Verification approach.** A gated flow from system to block to top (IV.1): a Python model (tier 0), behavioural SPICE (tier 1), transistor-level blocks in the loop (tier 2) and, later, PEX (tier 3). Every gate row takes its limit from SPEC, prints ACCEPT/REJECT, fails on missing data, and is meant to have a broken copy that must REJECT (III.0; IV.3). The plan is all PVT corners plus Monte Carlo for every block (D2); that is the plan, not the current coverage. The authoritative OTA1 check is an in-loop INL gate with the transistor OTA (gate B, D48; III.1.8). The digital macro has an independent bench with its own reference model, mutation testing and formal properties (III.6.3). A read-only design review is required for every design change (IV.8); the C3 final review is still open. False passes found on the way are logged as lessons (IV.4).

Coverage to date (2026-11-15):
- C1 gate B: boost at 4 corners, of which only fs/125 and ss/−40 are on the current WO-52 netlist, both at solver level O1 only; precision at 4 corners at O1, with O2 on 2 of 6 parts at ss/−40 (III.1.8, III.1.8a).
- C6: DC, loop and start-up-from-rest rows at 5 corners (III.5).
- C3: function rows at 9 PVT corners (III.3).
- Monte Carlo: only C3 T3 (offset). C1 tb8 offset MC and C6 MC have not been run.

Broken copies that are weak or absent:
- C1 precision `srknee` rejects at only 3 % over the gate (III.1.8a).
- C6 `early` and `hy1` are expected to ACCEPT under D89 (V.3 item 4).
- C3 T8 copies cannot be judged until a base revision passes T8 (III.3).
- C3 T5 has no physical copy that REJECTs; it is accepted by margin by construction, with checker copies only (D81).

**Status per block (2026-11-15; details in V.1).**

| Block | State | Open |
|---|---|---|
| C1 OTA1 + CMFB | transistor schematic, sink L 8 (WO-52 netlist). Boost gate B (≤ 5 ppm) on this netlist was run only at fs/125 (3.14 ppm) and ss/−40 (0.71 ppm), both at solver level O1; tt/27 and ss/125 exist only on older netlists (WO-31) | boost fs/125 needs O2 under D43c (3.14 ppm is less than 3× under 5 ppm), not scheduled; precision gate B ss/−40: O1 1.706 ppm vs 1.333, O2 on two parts 0.142 / 0.160 ppm (unfiled interim data); a ≈ 10× O1→O2 step does not meet D43c as written, so the verdict stays PENDING until a further solver point confirms it (WO-76); tb7/op-AC rerun PENDING (WO-77) |
| C2 OTA2 | not started | inputs gathered (III.2) |
| C3 comparator | rev f. T2: the single-shot rows pass; the rev f cyc rows were not run. T3: the count and \|μ\| + 3σ limbs pass (42.7–45.1 mV ≤ 60 mV), the `plaus` limb REJECTs because the sensitivity decks were not run. T5: accepted by margin by construction (D81) | T8 precharge-edge cap: rev f 2.251 V at ff/−40 against 2.2 V (2.206 V with the kp2 candidate); rev g and the cyc rows PENDING (WO-88) |
| C4 switches / phases / level shifters | rev b; bench numerics fixed | gate pools PENDING (WO-79, WO-85); ff/100 20 pA row open |
| C6 bias | architecture (c); DC rows pass at 5 corners | transient rows under D89 PENDING (WO-87) |
| C9 digital | RTL with D85/D88. WO-75 bench (D85) passes; WO-83 bench (D88) 106 of 107 jobs so far. PnR on the pre-D85 RTL meets setup and hold at 12 corners, with max slew waived at the stand-in corner (D86); DRV is not 0, LVS was not extracted and 2 floating nets are open, so WO-73 calls it "not a signoff candidate" | final PnR PENDING; formal at real widths open |
| C5, C7, C8, C10, top level, PEX | inside C1/C4 or not started | — |

**Top risks and open items** (V.3; V.4):
1. The C1 precision INL verdict at ss/−40 is PENDING: O1 fails (1.706 ppm), two O2 parts read 0.142 / 0.160 ppm, but a ≈ 10× O1→O2 step does not meet the D43c convergence rule, so a further solver point is needed (WO-76; III.1.8a). Every O1-only INL in the book (boost gate B, precision tt/27, ss/125 and fs/125) carries the same solver uncertainty.
2. C3 T8 overshoot at the precharge edge is above the 2.2 V cap at ff/−40 (WO-86, WO-88).
3. Fast-mode current: ≈ 180 µA nominal by reasoning, against the 172 µA SPEC basis. Scaling the accepted 189 µA worst case by the same ratio gives ≈ 198 µA, about 1 % under the 200 µA budget, before OTA2 exists (V.2).
4. OTA2 must swing ≈ 1.41 V differential at A ≥ 75 dB (III.2).
5. Area closure: C9 28,500 µm² (40 %) + MIM ≈ 9,000 µm² (12 %) + C6 ≤ 7,000 µm² (≤ 10 %) ≈ 62 % of the 72,071 µm² tile before OTA1, OTA2, the comparator, switches, guard rings and routing; the earlier estimate put the tile 66–89 % full (V.4).
6. Digital-to-analog coupling: a 48 MHz digital macro shares the tile with a µV-level front end; not simulated (V.4).
7. Sys-off CMRR margin is only 1.1–1.5 dB over 60 dB, from the model with allocations (V.4).
8. Virtual-ground leakage forces a temperature derating of the slowest mode (D82); the 20 pA ff/100 row is open.
9. No PEX and no analog layout yet; every margin is schematic-level.
10. C9 counter properties are formally proven only at reduced widths (WO-75, WO-83).

**Device stress limits.** The 1.98 V sustained, 2.2 V for < 1 ns and 4.95 V junction limits, and the C3 source-to-bulk 2.37–2.39 V, are project stress rules (D80, D83, D90), not PDK ratings. The SkyWater device-details page gives a model-validity range of 0–1.95 V for Vds and Vgs of nfet/pfet_01v8 and +0.3 to −1.95 V for nfet Vbs (https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html); these project limits lie outside that range (III.3).

**Area and power budget.**

| Item | Value | Status | Source |
|---|---|---|---|
| Tile | 319.24 × 225.76 µm = 72,071 µm² (template) | fixed | II.1.2 |
| MIM capacitors | ≈ 9,000 µm² (≈ 12 % of the tile) | estimate | II.2.5; SPEC §3.0 |
| C6 bias | ≤ 7,000 µm² (row); resistor length 854 µm at R1 144.8 µm | row / SIM | III.5; WO-80 |
| C9 digital macro | die 190 × 150 µm = 28,500 µm² (≈ 40 % of the tile), std-cell utilisation 0.676 | PnR on pre-D85 RTL; final PENDING | III.6.4; WO-73 |
| C1, C2, C3, C4 layout area | — | PENDING (no layout) | V.4 |
| Analog current budget | ≤ 200 µA in every mode (design budget) | SPEC | II.1.3; D46 |
| OTA1 current (netlist) | base 60.1–61.6 µA; boost 121.8–123.9 µA | SIM | III.1.9; WO-28 |
| C6 own current | 4.34–4.96 µA (≤ 6 µA row) | SIM | III.5; WO-80 |
| Comparator | 0.50–0.76 µA dynamic, on VDPWR (outside the 200 µA analog budget) | SIM (rev a; not re-measured on rev f) | III.3; WO-44 |
| Fast-mode system total | ≈ 180 µA nominal (REASONED, not simulated) against the 172 µA SPEC estimate; the accepted 189 µA worst case scales to ≈ 198 µA, about 1 % under 200 µA | needs C2 | V.2 |
| C9 power | 1.705 mW at default switching activity (LibreLane estimate, 1.8 V domain), ≈ 0.95 mA at 1.8 V | PnR estimate on pre-D85 RTL | WO-72; WO-73 |

**What silicon would measure.** The SPEC rows give the measurement list (II.1.3; SPEC §3.0): noise versus N and fs with a shorted input; INL against a precision DC source with the ratiometric reference; offset and gain error with system chop on and off; CMRR with chop on and off; supply current per mode and boost setting; the trim range and the "lowest passing code + 2" calibration rule (D73); start-up through the VAPWR-good hold (D85); order-1 mode as characterisation only (II.2.9; D21); fast-mode INL at N 64 / 256 / 1024 (II.1.3); and the 125 °C derating of the 0.25 MHz mode (D82). Two practical limits apply: the TT demo board has no precision source or ADC, so a low-noise source and reference must be brought in (NOTES, PCB section), and at 4 MHz / N 64 the host must read ≥ 0.36 Mword/s, which MicroPython cannot do (V.4). The model sets an intrinsic floor only; the one measured TT analog ADC came in ≈ 0.6 b below simulation (V.4).

## Contents

- Proposal summary
- Part I: Fundamentals
- Part II: System design (Stage S)
- Part III: Block designs (Stage C)
- Part IV: Verification methodology
- Part V: Status, open items and risks
- Appendices: glossary, decision index, change-log index, symbol table

---

# Part I: Fundamentals

This part builds the theory the design rests on. Equations are standard; every numeric example is taken from this project's sources.

## I.1 Sampling, quantisation and quantisation noise

An ADC maps a continuous input $u$ to a code. Two operations are involved:
- **Sampling** discretises time. A sampled-data system at rate $f_s$ represents bandwidths up to $f_s/2$ without aliasing.
- **Quantisation** discretises amplitude. A uniform quantiser with step $\Delta$ (one LSB) adds an error $e = Q(u) - u$ bounded by $\pm\Delta/2$.

When the input is busy enough that $e$ is uncorrelated with $u$ and uniformly distributed over $[-\Delta/2, \Delta/2]$, the error behaves like additive white noise:

$$\sigma_e^2 = \frac{1}{\Delta}\int_{-\Delta/2}^{\Delta/2} e^2\,de = \frac{\Delta^2}{12}.$$

For an $N$-bit quantiser with full-scale range $\mathrm{FSR} = 2^N\Delta$ and a full-scale sine of amplitude $\mathrm{FSR}/2$ (power $\mathrm{FSR}^2/8$):

$$\mathrm{SQNR} = 10\log_{10}\frac{\mathrm{FSR}^2/8}{\Delta^2/12} = 10\log_{10}\left(\tfrac{3}{2}\,2^{2N}\right) = 6.02\,N + 1.76\ \text{dB}.$$

This is the Nyquist-rate limit. Each extra bit buys 6 dB and halves $\Delta$.

**This design's full scale.** The input is differential and the reference is $V_\mathrm{REF} = 2.048$ V (D17), so $\mathrm{FSR} = 2V_\mathrm{REF} = 4.096$ V differential (SPEC §2.1). Effective resolution is quoted against that FSR as $\mathrm{ENOB} = \log_2\!\big(\mathrm{FSR}/(\sqrt{12}\,v_\mathrm{rms})\big) = (\mathrm{SNR} - 1.76)/6.02$, where SNR is the full-scale sine power over the noise power. For example, 1.5 µV rms ≈ 19.6 b, 5 µV ≈ 17.9 b and 50 µV ≈ 14.5 b (CTX §6).

## I.2 Oversampling and noise shaping

### I.2.1 Oversampling alone

Sample at $f_s \gg 2B$, where $B$ is the signal bandwidth. Then $\mathrm{OSR} = f_s/(2B)$ (ROAD §1). The white quantisation noise spreads over $[0, f_s/2]$, and only the fraction $1/\mathrm{OSR}$ falls in band. Each doubling of OSR therefore gains 3 dB, or half a bit. That is too slow to reach 18–20 bits from a 1-bit quantiser.

### I.2.2 The ΣΔ loop, STF and NTF

A ΣΔ modulator puts the quantiser inside a feedback loop with a filter $H(z)$ ahead of it. With the quantiser modelled as a gain plus additive error $E(z)$:

$$Y(z) = \mathrm{STF}(z)\,U(z) + \mathrm{NTF}(z)\,E(z),\qquad \mathrm{STF} = \frac{H}{1+H},\quad \mathrm{NTF} = \frac{1}{1+H}.$$

A large $|H|$ in band makes $|\mathrm{NTF}|$ small in band. The quantisation noise is pushed ("shaped") to high frequencies, where a digital filter removes it.

**First order.** One delaying integrator, $H = z^{-1}/(1-z^{-1})$, gives $\mathrm{STF} = z^{-1}$ and $\mathrm{NTF} = 1 - z^{-1}$.

**Second order.** Two integrators in a stable topology give $\mathrm{NTF} = (1-z^{-1})^2$. On the unit circle, $|1 - e^{-j\omega}| = 2\sin(\omega/2) \approx \omega$ for small $\omega$, so an order-$L$ NTF suppresses low-frequency noise as $\omega^{L}$.

### I.2.3 In-band noise versus OSR

Integrate $|\mathrm{NTF}|^2 \approx \omega^{2L}$ over the band. This gives the ideal SQNR of an order-$L$ modulator with an $N$-bit quantiser (NOTES §SQNR):

$$\mathrm{SQNR} \approx 6.02N + 1.76 - 10\log_{10}\frac{\pi^{2L}}{2L+1} + (2L+1)\,10\log_{10}\mathrm{OSR}.$$

Each doubling of OSR gains $3(2L+1)$ dB: +9 dB for first order and +15 dB for second (ROAD §1). NOTES gives the example of a 2nd-order, 1-bit modulator at OSR 128, which reaches ≈ 100 dB ideal SQNR by the formula above (lower in practice, limited by thermal noise, kT/C and op-amp gain).

### I.2.4 Why a 1-bit quantiser is inherently linear

A 1-bit DAC has exactly two output levels. Any two points define a straight line, so DAC level errors produce only an offset and a gain error, never INL. Multi-bit DACs need element matching or dynamic element matching to reach ppm linearity; a 1-bit DAC needs neither.

In this design, the 1-bit DAC switches the sampling capacitor between $+V_\mathrm{REF}$ and $-V_\mathrm{REF}$. Capacitor mismatch therefore causes gain error only (SPEC §3.5). The price is that the quantiser error is large ($\pm V_\mathrm{REF}$ class), so the loop filter must be stable for a 1-bit quantiser and the integrator states must be scaled; see I.3.

## I.3 Loop stability, overload and state swing

### I.3.1 The CIFB topology and its state equations

This design uses a cascade of integrators with distributed feedback (CIFB). Both integrators are delaying, there is one comparator, and the DAC feeds back to both stages. With all voltages normalised to $V_\mathrm{REF}$ and $y[n] \in \{\pm1\}$:

$$x_1[n+1] = x_1[n] + c_1\,(u - y[n]),$$
$$x_2[n+1] = x_2[n] + c_2\,(x_1[n] - k\,y[n]),$$
$$y[n] = \operatorname{sign}(x_2[n]).$$

The capacitor ratios set the coefficients (SPEC §3.4):
- $c_1 = C_{s1}/C_{int1} = 0.5/4 = 0.125$;
- $c_2 = C_{s2}/C_{int2} = 0.5/1 = 0.5$;
- $c_2 k = C_{k2}/C_{int2} = 0.25/1 = 0.25$, so $k = 0.5$.

These equations are consistent with the exact reconstruction formula of SPEC §3.7, derived in I.5.3.

### I.3.2 Overload and input range

A 1-bit loop can only cancel an input that its feedback can balance on average, so $|u| < 1$ (in units of $V_\mathrm{REF}$). Near full scale the integrator states grow and a second-order loop can lose stability. The project limits the usable range to $\pm 0.9\,V_\mathrm{REF}$ (the model-verified swing). Overload at $1.0$–$1.1\,V_\mathrm{REF}$ must recover on the next conversion (SPEC §2.1; D21). In an incremental converter every conversion starts from reset (I.5), so an overload cannot persist past one conversion.

### I.3.3 Coefficient scaling and integrator swing

Scaling is a design choice, not a free parameter. The textbook 0.5/0.5 coefficients drive integrator 1 to $\pm1.85\,V_\mathrm{REF}$ and integrator 2 to $\pm4.75\,V_\mathrm{REF}$. That clips the states and collapses the resolution to ≈ 4.7 b (CTX §6). With $c_1 = 0.25, c_2 = 0.5, k = 1$ both states stay within $\pm1.2\,V_\mathrm{REF}$ (CTX §6; MODEL).

**Bit-identical rescaling.** Halve $c_1$ and $k$ together. Then $x_1$ halves, the term $(x_1 - k y)$ halves, and $x_2$ halves. $\operatorname{sign}(x_2)$ is unchanged, so the bitstream is identical and only the analog swing changes. S1 verified this to $\max|\Delta\hat u| = 0$ (S1 theory checks; D10). The same holds for $c_2$, because $y = \operatorname{sign}(x_2)$: $c_2 = 0.25$ halves $x_2$ with an identical bitstream (SPEC §2.1).

**Swing at the chosen point.** At $c_1 = 0.125, k = 0.5$ and $V_\mathrm{REF} = 2.048$ V, the peak state is 0.61 V per side (SPEC §1; S1 option B: $x_1$ 0.602, $x_2$ 0.607 V/side). The comparator offset raises the realistic $x_2$ peak to ≈ 1.41 V differential (C3 §3.1b; WO-51). Part III takes this up.

### I.3.4 Loop delay, and why an extra delay matters

The equations above assume the decision $y[n]$ made at the end of cycle $n$ is applied to the DAC in cycle $n$'s integration, with no extra delay. An extra cycle of delay, $y[n+1] = \operatorname{sign}(x[n])$, adds a $z^{-1}$ in the loop:
- **First order.** The loop's linearised poles move onto the unit circle (REVIEW-C4a M1, recorded in D76).
- **Second order.** The NTF is no longer $(1-z^{-1})^2$, so the coefficients, the golden vectors and the reconstruction all change.

The project hit this twice.
1. **Capture edge (D74, CL-28).** Under CL-23 the C9 RTL captured the comparator on the falling edge of the bit clock, but the comparator strobe fired after that edge. This cost a full extra cycle of loop delay (REVIEW-C3a). D74 moves the strobe into the sample phase φS and captures `comp_in` straight into the DAC flop on the next fs-cycle start edge. The order-2 loop delay is then equal to the tier-1 deck again (C4 §1).
2. **Order-1 mode (D76, WO-53).** The comparator always reads $x_2$, and integrator 2 acts as a per-cycle follower in order 1 (D74). The order-1 loop therefore has an extra delay. WO-53 modelled it as $y[n+1] = \operatorname{sign}(x_1[n])$:
   - The loop is stable. $|x_1|$ peaks at 0.475 $V_\mathrm{REF}$ = 0.486 V/side at every N, because the comparator, not the linear NTF, bounds the state.
   - It costs about 1 bit. At N 4096, error $4.5\times10^{-4} \to 8.6\times10^{-4}$, i.e. 11.1 → 10.2 b; endpoint INL 174 → 308 ppm.
   - Order 1 is characterisation-only (D21), so this was accepted (D76; WO-53).

## I.4 Discrete-time versus continuous-time ΣΔ

| Aspect | Continuous-time (CT) | Discrete-time switched-capacitor (DT/SC) | Source |
|---|---|---|---|
| Clock jitter | the DAC pulse width modulates charge: $\mathrm{SNR}_\mathrm{jitter} \propto 1/(f_s\sigma)^2\cdot\mathrm{OSR}$, very sensitive | charge is transferred to completion each phase; nearly jitter-immune | ROAD §1 |
| Excess loop delay | the comparator and DAC delay add to the loop and must be compensated | the delay is set by the phase plan; only one decision per cycle is needed | (theory; see I.3.4 for the SC case) |
| Coefficient accuracy | set by RC products, which spread ±15–20 % over process | set by capacitor **ratios**: matching-limited, typically < 1 % | SPEC §3.4; D42 for the R spread |
| Anti-aliasing | inherent | none; needs an external RC (as the MCP3421 does) | MCP |
| Power at a given speed | lower (no full settling) | OTA must settle within $T/2$, so $\mathrm{GBW}\propto f_s$ and power $\propto f_s C$ | ROAD §1 |

**Reasons for DT/SC here.**
- **Precision DC operation.** The target is a precision DC converter (MCP3421 class, 3.75–240 SPS). Bandwidth is not the constraint; offset, 1/f noise, gain and INL are (ROAD §1).
- **Clock.** SC at ≈ 1–2 MHz is nearly jitter-immune, so the demo-board RP2040/RP2350 clock is adequate. The comparable TT design by Paul Thomas is 1st-order CT at 50 MHz and needs a low-jitter FPGA clock (CTX §4; ROAD §2).
- **Coefficients from ratios.** A CT design takes its coefficients from RC products, which follow the ±15 % xhrpoly spread (D42). An SC design takes them from capacitor ratios.
- **Reference loading.** A settled SC loop turns reference loading through the 500 Ω pad into gain error only (SPEC §3.5; CTX §8 correction 2). The IR-drop INL mechanism belongs to CT resistive DACs.

**Current-mode versus voltage-mode.** Two discussions in the sources use this distinction.
1. **The modulator.** Paul Thomas's CT design uses an RZ resistive (current) DAC (CTX §4). As above, its reference current flows through the pad resistance, and its pulse timing carries jitter (ROAD §1). This design's charge-mode (SC) DAC avoids both.
2. **The bias.** The user chose a **constant-current** (current-mode bandgap) reference over a constant-gm one (D41(b), D42). Slew rate ($\propto I$) is the binding spec, so holding $I$ constant over temperature keeps SR flat. Constant-gm would let SR fall at cold and has the same R-spread dependence (`results/bias_bgr_area.md`; GUIDE A15).

## I.5 Incremental ΣΔ

### I.5.1 Reset and finite N

A free-running ΣΔ never resets. Its decimation filter has memory across conversions, and idle tones can appear. An **incremental** ΣΔ resets the integrators (and the decimator) before every conversion and then runs exactly $N$ cycles. The result is a Nyquist-rate converter with one output per $N$ cycles: no memory between conversions, no idle tones across conversions, and simple multiplexing (GUIDE A1).

In this design a slot is $N + 2$ fs cycles: a 2-cycle reset window, then $N$ conversion cycles (SPEC §1; §3.7a k). The frame rate is $f_s/(N+2)$, for example 2 MHz/1026 ≈ 1.95 kSPS at N 1024 (SPEC §1).

### I.5.2 The cascade-of-integrators (CoI) decimator

The matched decimator for an order-$L$ incremental loop is a cascade of $L$ accumulators that is reset with the loop. For order 2 it is two accumulators and a counter (SPEC §3.7):

$$\mathrm{acc}_1 = S = \sum_{n=0}^{N-1} y[n],\qquad \mathrm{acc}_2 = \sum_{n=0}^{N-1} S_n,\quad S_n = \sum_{j<n} y[j]\ \ \text{(exclusive)}.$$

The update order is **exclusive**: `acc2 += acc1` before `acc1 += y`. An inclusive implementation acts like $k/c_1 = 5$ and gives a ≈ 2/N gain error. The golden vectors pin the convention (SPEC §3.7; GOLD).

### I.5.3 Exact reconstruction of u from the accumulators

Iterate the state equations of I.3.1 from $x_1[0] = x_2[0] = 0$ with constant $u$:

$$x_1[n] = c_1\,(n\,u - S_n),$$
$$x_2[N] = c_2\sum_{n=0}^{N-1}\bigl(x_1[n] - k\,y[n]\bigr) = c_2\Bigl[c_1\Bigl(u\tfrac{N(N-1)}{2} - \textstyle\sum_n S_n\Bigr) - k\,S_N\Bigr].$$

Solving for $u$:

$$\boxed{\,u = \frac{\sum S + (k/c_1)\,S + x_2[N]/(c_1 c_2)}{N(N-1)/2}\,}$$

This is exact (SPEC §3.7, review F9). The chip outputs only the accumulators. Firmware forms

$$\hat u = \frac{\mathrm{acc}_2 + (k/c_1)\,\mathrm{acc}_1}{N(N-1)/2},\qquad k/c_1 = 4,$$

so there is no on-chip divider (SPEC §3.7). The integer $k/c_1 = 4$ is one reason for the coefficient choice: the float model and an integer implementation agree bit for bit (GOLD). The dropped term $x_2[N]/(c_1c_2)$ is the quantisation error. Transistor-level INL checks add it back using $x_2[N]$ read from the simulation (SPEC §3.7).

For order 1, $x_1[N] = c_1(Nu - S)$, so $u = S/N + x_1[N]/(c_1 N)$ (WO-53). The golden denominator is $N$ (SPEC §3.7).

### I.5.4 Resolution and INL versus N

Because $|x_2|$ is bounded, the error in $\hat u$ falls as $1/N^2$ for order 2, compared with $1/N$ for order 1:
- Order 1: ≈ $\log_2 N - 1$ bits (the MCP3421 pattern, MODEL finding 1).
- Order 2: ≈ $2\log_2 N - 4$ bits with the scaled coefficients. N 64 → ≈ 8 b, N 1024 → ≈ 16 b, N 4096 → ≈ 20 b (SPEC §1; MODEL). The ideal "$2\log_2 N - 1$" of an early hand table was too optimistic (CTX §8 correction 6).

The quantisation error is deterministic for a given input, so averaging repeated conversions does not remove it. At N 1024 it is ≈ 33 µV; at N 4096 it is ≈ 2 µV. That is why the precision modes use N 4096 (D23). The S3 budget gives the N 4096 quantisation floor as 0.419 ppm INL against a 1 ppm share (`s3_budget.md` allocation table).

**Finite OTA gain and N.** A finite gain makes each integrator leaky. In incremental mode the leak accumulates over N cycles, so the gain needed grows with N: "A0 ≳ N" (ROAD §1). CL-1 states the corollary: finite-gain INL ∝ N/A. N 1024 at 5 ppm therefore needs less gain than N 4096 at 8 ppm.

### I.5.5 Why the forced y[0] exists

At the first decision after reset, $x_2 = 0$ exactly. The comparator sees zero input and is metastable every conversion. Suppose the DAC and the decimator read that bit through different paths and disagree. The DAC then applies one value and the decimator accumulates the other, which is a ≈ 4/N error in u units (u is ±1, so 2/N of FSR) that appears sporadically (SPEC §3.2, review F8). The rules (SPEC §3.7a a):
- $y[0] = +1$ is forced at reset release.
- The cycle-0 comparator output is ignored.
- **One** retimed flop drives the DAC, the decimator and the raw bitstream pin.

The golden vectors carry the junk bit `comp_raw0`, which a testbench must drive at cycle 0. An RTL that passes it through fails every frame (GOLD; mutant `y0pass`).

## I.6 Switched-capacitor circuits

### I.6.1 Charge transfer

An SC integrator moves a charge packet $C_s V_{in}$ onto $C_{int}$ every cycle. The output step is $\Delta V_o = (C_s/C_{int})V_{in}$, so the gain is a capacitor ratio. The two phases are named in C4 §1:
- **φS (sample):** $C_{s1}$ samples VIN.
- **φI (integrate):** $C_{s1}$ dumps its charge into $C_{int1}$, and the DAC connects the bottom plate to $\pm V_\mathrm{REF}$.

### I.6.2 The stray-insensitive integrator

The parasitic $C_p$ at the virtual ground is always held at the same potential, the virtual ground. It therefore never exchanges signal charge. The parasitic at the bottom plate is driven by a low-impedance source and does not enter the transfer either. The integrator gain is then $C_s/C_{int}$, independent of strays.

**Referral of slow errors.** In a stray-insensitive SC integrator, OTA offset and 1/f noise refer to the input with gain ≈ 1. The wideband noise gain $(1 + C_f/C_s + C_p/C_s)$ applies to **white** noise only (SPEC §2.2). It is ≈ 5.3 for the legacy point and up to 9.3 for option B (SPEC §1; S1). An early project error applied the wideband gain to offset and 1/f. That overstated unchopped noise as ≈ 30 µV instead of ≈ 7–12 µV (CTX §8 correction 1).

### I.6.3 Bottom-plate sampling

A switch that opens injects part of its channel charge into the nodes it connects. If the injection is signal-dependent, it adds INL. Bottom-plate sampling opens a switch on the **top-plate** side first: here, the D12 top-plate short in φSe. The top plate is then floating, so by charge conservation the differential charge on $C_s$ is frozen. The later opening of the input switch on the bottom plate injects into a driven node and cannot change the stored charge (C4 §4 item 1). SPEC §3.3 makes bottom-plate sampling mandatory for exactly this reason: it removes signal-dependent charge injection.

### I.6.4 kT/C noise

A resistor charging a capacitor leaves a sampled noise of variance $kT/C$, independent of the resistor. Each sampling event therefore adds $\sqrt{kT/C}$ rms. For a differential pair of $C_{s1} = 0.5$ pF, the per-sample differential charge noise referred to voltage is $\sqrt{4kT/C_{s1}} = 182.0$ µV at 300 K (C1 §2.7a; CL-31). That 182 µV counts 2 sides × 2 phases; one differential sampling event is 129 µV (182.0/√2).

The noise averages over the conversion, $\bar v^2 \approx kT/(C N)$, so small caps are enough (CTX §6). At $C_s = 0.5$ pF the kT/C-only noise is 0.556 µV at 15 SPS (`s3_budget.md:31`). The 0.71 µV figure is the WO-04 ota+sys model value (D22), not kT/C-only; SPEC §1 text at lines 18 and 25 disagrees on this (see Appendix E). The joint model, which includes OTA thermal excess, gives 0.94 µV, and that is the governing number (D22; D48(3)). Halving $C_s$ from 1 pF to 0.5 pF raised the kT/C term from 0.54 to 0.76 µV at 15 SPS (SPEC §1, area option E1).

### I.6.5 Charge injection and clock feedthrough

When an MOS switch turns off, its channel charge $Q_{ch} \approx WLC_{ox}(V_{GS} - V_t)$ splits between its terminals, and its overlap capacitance couples the clock edge (feedthrough). Mitigations used here:
- **Bottom-plate order**, as in I.6.3.
- **A differential top-plate short.** One switch between $tp_p$ and $tp_n$ splits its charge into two equal capacitors. The injected charge is then common-mode, which D12 rejects to first order. The residue is the split asymmetry, $\Delta V_{dm} \approx (q/2C_s)(\Delta C_s/C_s)$ (C4 §4 item 2).
- **Size limits from injection, not settling.** For the top-plate short, the Vin_cm-dependent residue is $6.8\times10^{-5}$ CM→DM at 2/4 µm against the $\varepsilon_{inj} \le 2.8\times10^{-4}$ budget. An 8/24 switch would give $3.6\times10^{-4}$ and fail. Rule: ≤ 2/4 (C4 §4).
- **Virtual-ground switches inject into a constant node.** The charge is then constant (an offset), which chopping cancels. The signal-dependent part comes only from $x_1/A_0$ at the virtual ground, ≈ 60 µV per side (C4 §4 item 3).

### I.6.6 Non-overlapping clocks

If φS and φI overlap, a charge path shorts the input to the reference or the integrator. The phase generator therefore inserts a dead time $g$ between them, and it produces early and late versions of each phase for bottom-plate sampling (C4 §5–§6). The SPEC limits (SPEC "Clock" row):
- $h = 0.5/f_s$, $g = 0.025/f_s$;
- usable half-period $t_\mathrm{half} = h - 2g = 0.45/f_s$, i.e. 225 ns at 2 MHz, 112.5 ns at 4 MHz and 1.8 µs at 0.25 MHz;
- $g \le 0.025/f_s$ at every corner, from an on-chip delay generator, not from TT-clock ticks.

## I.7 Offset, 1/f noise and chopping

**Offset** is a static input-referred error, typically mV-level for MOS pairs. The project budgets OTA offset at 9 mV 3σ (D21; SPEC OTA offset row).

**1/f noise** has a PSD $\propto 1/f$. It does not average down with more samples, and it is unchanged by $f_s$ (ROAD §1). The reference data comes from Paul Thomas's sky130 PMOS pair (250 µm wide): 6.9 nV/√Hz white and a 631 kHz 1/f corner (CTX §6; MODEL). This project's own OTA1 measured a 17–61 kHz corner (WO-41).

**OTA chopping** modulates the input to $f_{ch}$ ahead of the OTA and demodulates it after, so the offset and 1/f noise move to $f_{ch}$. Here $f_{ch} = f_s/2$ (SPEC §3.6). In an **incremental** loop, OTA chop alone leaves a residue $lf\cdot V_{os}/(N-1)$, because the chop phases do not weight equally over a finite conversion. S2 confirmed the closed form against the model at 54/54 points (SPEC §3.6; D18). S2's order-2 numbers at $V_{os}$ 9 mV and lf 1 are 13.79 µV at N 1024 and 7.20 µV at N 4096 (`s2_chop.md`). These include the 5 µV vres term; the closed form $lf\cdot V_{os}/(N-1)$ at lf 1 alone gives 8.80 µV and 2.20 µV.

**System chopping** swaps the input polarity on the pin side between sub-conversions and averages the pair with alternating sign. Every error that enters after the swap and does not depend on the swap state cancels. S2 numbers (`s2_chop.md`; D18):

| Mode at $V_{os}$ 9 mV | Offset, order 2 |
|---|---|
| no chop | 9005 µV |
| sys | ≤ 0.72 µV |
| ota + sys | ≤ 0.77 µV |

Adding OTA chop to system chop cuts the 240 SPS noise 1.2–14× (SPEC §3.6).

**Rules that make system chop exact** (SPEC §3.6, binding on C9):
- swap only at conversion boundaries, inside the reset window;
- integrators reset between swapped sub-conversions;
- N even;
- OTA-chop phase restarted at the same value every sub-conversion;
- swap on the pin side, ahead of the sampling and CM-rejecting switches;
- one retimed y;
- config changes only at pair boundaries.

**Residues that do not cancel:** reset residue, virtual-ground leakage, and anything that depends on the swap state. Examples are the D12 CM path and source-resistance mismatch ΔR·I (SPEC "Input (user-facing)" row). The S3 budget lists them as non-cancelling offset lines (`s3_budget.md`).

**Decision (D18).** OTA chop is a configuration bit, always paired with system chop. OTA-only chop is characterisation-only (D45 g).

## I.8 Fully differential circuits and CMFB

**Why fully differential.**
- Even-order distortion and common-mode (supply, substrate, clock) coupling cancel to first order.
- The swing doubles for the same supply. At $V_\mathrm{REF} = 2.048$ V the differential FSR is 4.096 V on a 3.3 V supply (SPEC §2.1).
- The system-chop swap is a simple crossover.

**CMFB.** A differential pair with high-impedance loads has an undefined output CM. A common-mode feedback loop senses the output CM and corrects a load current. Two families exist:
- **Continuous-time CMFB** uses a resistive or differential-pair sense and costs static current.
- **SC CMFB** senses with capacitors $C_c$ from the outputs to a control node `ctl`. A refresh capacitor $C_r$ alternates between the reference pair $(V_\mathrm{OCM}, V_\mathrm{BL0})$ and the sense node. It costs no static current, but its caps load the outputs (D40b). This design chose SC CMFB for current: $I_{tot} \approx 2.7\,I_\mathrm{tail}$ versus $3.4\,I_\mathrm{tail}$ (GUIDE A14).

**Static error with no in-loop gain.** A passive SC CMFB has unity gain from the sensed CM to `ctl`. Every mismatch and every fold-node current error passes 1:1 into the output CM error $V_\mathrm{OCM}$. On the WO-26 netlist this was 30.8 mV systematic at ff/125 base, against a ≈ 38 mV CL-2 bound (C1 §1.3a; D60).

**The dual-path idea (D61).**
- Keep the fast passive SC path for the CM loop bandwidth $f_{cm}$.
- Add a slow, high-gain gm-C integrator from `ctl` into the CMFB reference node `bli`.

At DC, $V_{out,cm} - V_\mathrm{OCM} = V_{os,int} + (V_{need} - V_{dio})/A_{int}$, so the mismatch terms the passive loop passed 1:1 are divided by $A_{int}$ (C1 §1.3b). The integrator forms a PI zero at $f_z = g_{m,ia}/(2\pi C_\mathrm{INT})$ (C1 §1.3b). Part III gives the history and the numbers.

## I.9 OTA fundamentals

**gm/Id.** The transconductance efficiency $g_m/I_D$ rises from strong inversion (≈ $2/V_{ov}$) toward weak inversion, where it saturates at ≈ $1/(nU_T)$. Two consequences shaped this design:
1. **Halve L at equal W·L.** W/L goes up 4×, and the device moves toward weak inversion. For the C1 pair at ss/125 boost, 40/1 → 80/0.5 gave +26 % gm at −11 % $C_{gg}$, with Pelgrom σ and 1/f area unchanged (C1 §2.2).
2. **gm does not scale with I in moderate inversion.** ×1.5 tail current gave only ×1.28–1.31 gm (D39; GUIDE A12; REVIEW-S5e C-M1). This is why the fast mode is gated on the absolute boosted operating point, not on a ratio.

**Folded cascode.** Per side: tail → PMOS input pair → protection cascode → fold node → NMOS cascode → output, with a PMOS cascode and load from above (C1 §1.1). One stage gives a dominant pole at the output and needs no Miller compensation. The output swing is set by the cascode stacks.

**DC gain.**

$$A_0 = g_{m1}\,(R_{dn}\parallel R_{up}),\quad R_{dn} = (g_{m,nc}+g_{mbs,nc})\,r_{o,nc}\,r_{o,n},\quad R_{up} = g_{m,pc}\,r_{o,pc}\,(r_{o,pl}\parallel r_{o,plc}).$$

This hand formula agreed with AC simulation within 0.2 dB at all 18 rev B points (C1 §2.3). On the WO-24 netlist the agreement was +0.3 to +0.55 dB (WO-24).

**GBW, feedback factor and phase margin.** In an SC integrator the OTA sees the feedback factor

$$\beta = \frac{C_{int}}{C_{int} + C_s + C_p},$$

and the closed-loop bandwidth is $\beta\cdot\mathrm{GBW}$. For OTA1, $\beta_1 = 4/(4.5 + 0.23) = 0.846$ with $C_{p,vg} \approx 0.23$ pF per side (C1 §2.2). The spec floor is $\beta_1 \ge 0.83$, i.e. $C_{p,vg} \le 0.32$ pF (CL-4). A second pole $f_{p2}$ sets the phase margin at the crossover $\beta\cdot\mathrm{GBW}$. The tier-1 study found the INL optimum near PM ≈ 72° ($\zeta \approx 0.9$, $f_{p2} \approx 1.5$–3·GBW), not at $\zeta = 1$ (GUIDE §6; SPEC OTA1 GBW row).

**Linear settling versus slew.** Linear settling with time constant $\tau = 1/(2\pi\beta\,\mathrm{GBW})$ leaves an error $e^{-t/\tau}$ that is proportional to the step. That is a gain error, which is calibratable, provided $\tau \le 0.2\,t_\mathrm{half}$ (SPEC §3.1). **Slewing** is signal-dependent: a step larger than $\mathrm{SR}\cdot\tau$ spends a step-dependent time slewing, which is INL. $\mathrm{SR} = I_\mathrm{tail}/C_L$. For example, 18.5 µA / 1.4 pF = 13.2 V/µs (C1 §2.1). The tier-1 study found a sharp INL **knee** in SR. For OTA1 at N 1024 and 2 MHz the knee is 10.23–10.28 V/µs at O2 (D44). This is why the slew floor is set from the knee plus a 3σ mismatch margin: SR − 3σ ≥ 10.3 V/µs base and ≥ 20.6 V/µs boost (CL-9).

**Why gain that droops with signal causes INL.** A constant finite gain $A$ makes each integrator leak $x/(\beta A)$ per cycle, uniformly in the signal. The result is a gain error ≈ $1/A_0$, which is calibratable, not INL (CTX §6; MODEL finding 2). If $A$ falls as $|v_{out}|$ grows (output-stage compression), the leak depends on the signal. That produces INL that grows with N/A. Examples:
- MODEL finding 2, at 90 % gain loss at full swing: $A_0$ 70 dB → ≈ 120 ppm, 80 dB → ≈ 45 ppm, 90 dB → ≈ 19 ppm.
- S3 sweep: $A_0$ 80 dB with a 90 % drop at vlin 2 V gives 3.27 ppm. A 1.0 V linear range gives 254 ppm (`s3_budget.md`).

The droop **shape**, not $A_0$ alone, sets the INL. At N 1024 the S4 droop shape reads 5.37 ppm at 80 dB, while a flat 60 dB passes (CL-1b reason). So a fixed $A_0$ floor can neither pass nor fail correctly.

**The A(v) table method (CL-1b).**
1. Measure the **static, large-signal secant gain** $A(v) = v_o/v_g$ of the transistor OTA with a DC servo, using the real SC CMFB. The range is ±1.8 V differential (or until A < 40 dB), in steps ≤ 0.05 V above 0.8 V, both signs, symmetric within 0.5 dB.
2. Feed the table into the tier-0 model.
3. Compute the endpoint INL.

The model rejects any extrapolation beyond the table, and the raw curves are saved. Gates (CL-1b):
- Boost: ≤ 3.33 ppm at N 1024.
- Precision: ≤ 5.33 ppm at N 1024 and N 4096, together with $A_0 \ge 80$ dB.

## I.10 Noise in SC loops

**Sampled thermal noise.** The OTA's thermal noise at the virtual ground is sampled once per phase. Its sampled variance is approximately $2kT\gamma(1+\alpha)\beta/C_L$, with $\alpha = (g_{m,n} + g_{m,pl})/g_{m1}$, the extra noise of the current sources relative to the pair (C1 §2.7). The measured thermal noise at the virtual ground on the C1 netlist was 160–241.5 µV rms differential (WO-41). The NMOS sinks contributed 53.8 % of the thermal power at tt base (WO-41).

**Noise gain.** Referring that noise to the input through the conventional noise-gain path (S3 scaling) overstates it, because the sampled virtual-ground noise is not an independent input noise each cycle. The project compared two tier-0 paths (WO-41; D71):

| Path | OTA1 thermal at 15 SPS | Joint |
|---|---|---|
| conventional (noise-gain scaling) | 1.45–2.65 µV, over the 1.2 µV share | 1.54–2.70 µV |
| **direct** (simulated sampled $v_{vg}$ into the kT/C excess) | 0.52–0.71 µV | 0.75–0.92 µV |

**D71** made the direct path the gate and the conventional path information. V9 (tier 0 with PEX) validates it.

**From the system share to a block row (CL-31).** Charge error at sampling is $C_{s1}v_{vg}$ against the switch noise $4kT/C_{s1}$, so the model's excess factor is $1 + v_{vg}^2/(4kT/C_{s1})$. The OTA1 share at the output is then (C1 §2.7a)

$$th_{direct} = n_{ktc}\cdot\frac{v_{vg}}{\sqrt{4kT/C_{s1}}},\quad n_{ktc} = 0.559\ \mu\mathrm{V},\ \sqrt{4kT/C_{s1}} = 182.0\ \mu\mathrm{V}.$$

The 1.2 µV share gives $v_{vg} \le 391$ µV. The row limit is 390 µV, rounded down (CL-31; D75).

## I.11 Mismatch

**Pelgrom's law.** For two nominally identical devices,

$$\sigma(\Delta V_T) = A_{VT}\sqrt{\tfrac{1}{(WL)_a} + \tfrac{1}{(WL)_b}},\qquad \sigma\!\left(\tfrac{\Delta I}{I}\right) = \sqrt{\left(\tfrac{g_m}{I}\sigma(\Delta V_T)\right)^2 + \left(A_\beta\sqrt{\tfrac{1}{(WL)_a}+\tfrac{1}{(WL)_b}}\right)^2}.$$

These are the C1 allotment formulas, with $A_{VT}$ = 12 mV·µm gating (8 mV·µm as information) and $A_\beta$ = 1 %·µm (C1 §2.11). Convention: $A_{VT}$ here is per device; the pair-difference $A_{VT}$ of Pelgrom is √2 larger, so 12 per device ≈ 17 per pair.

**PDK limitation for 5 V devices.** In the sky130 models, `nfet_g5v0d10v5` has `vth0_slope = 0`; it carries only toxe mismatch (WO-44; C3 §7). The PDK Monte Carlo therefore under-reports any HV-pair offset. The probe measured an HV nfet σ of 5.87 mV, equivalent to $A_{VT}$ ≈ 9.29 mV·µm, from toxe alone (WO-44). By contrast, `nfet_01v8` / `pfet_01v8` carry vth0 mismatch in the `*_mm` sections (WO-44).

The project's rules:
- Every HV-dependent row carries a hand-Pelgrom allotment (C1 §2.11; REVIEW-WO26 M1).
- For the comparator, MC injects $\sqrt{12^2 - 9.3^2} \approx 7.6$ mV·µm per device on top of `tt_mm`, so the HV pair totals 12 mV·µm and is not double counted (D74; C3 §3.1).
- MIM local mismatch is not modelled in the PDK either. C1 uses a hand $A_C$ = 1 %·µm (C1 §2.12).

## I.12 Comparators

**StrongARM latch.**
- In precharge, both output nodes are pulled to the supply.
- On the strobe, the input pair discharges the internal nodes at rates set by the input difference.
- A cross-coupled inverter pair then regenerates the difference to full logic levels.

It draws no static current, which matters inside a 200 µA budget (C3 §1).

**Offset.** Input-pair ΔVT dominates; latch mismatch is divided by the pre-latch gain (C3 §3.1):

$$\sigma_{os}^2 \approx \sigma_{\Delta VT,in}^2 + \left(\tfrac{V_{ov,in}}{2}\tfrac{\sigma_{\Delta\beta}}{\beta}\right)^2 + \left(\tfrac{\sigma_{\Delta VT,LN}}{A_n}\right)^2 + \left(\tfrac{\sigma_{\Delta VT,LP}}{A_p}\right)^2.$$

Inside a ΣΔ loop, comparator offset is divided by the integrator gains and, with system chop, cancels as a constant. Its real limit is loop headroom (I.3.3; CL-30).

**Noise.** The integration-phase noise is $\sigma_n^2 \approx 2(4kT\gamma/g_m)/(2t_{int})$. For C3 this is ≈ 0.3–0.6 mV rms, against a 5 mV row (C3 §3.2).

**Decision time and metastability.** The decision time (C3 §3.3) is

$$t_{dec} \approx t_{int} + \tau_{reg}\ln\frac{V_{DD}/2}{A_n\Delta} + t_{buf}.$$

An input smaller than $\Delta_{crit} = (V_{DD}/2/A_n)\,e^{-(t - t_{int})/\tau_{reg}}$ is unresolved at time $t$. With ≈ 75 ns available at 4 MHz, even a pessimistic $\tau_{reg}$ of 1 ns gives P ≈ 2e-17 per decision (C3 §3.5).

**Kickback.** The strobe edge couples through the input-pair $C_{gs}$ back onto $x_2$. The CM part was 32–49 mV (WO-44). Asymmetric $x_2$ impedances convert part of it to differential: ≈ $2\delta_c V_{cm,kick}$, i.e. 8.2 mV at ±10 % (C3 §3.4b).

## I.13 Bias references

**PTAT and CTAT.**
- $V_{BE}$ of a bipolar falls ≈ 2 mV/K (CTAT). C6 §2.1 computes −2.1 mV/K from the model parameters.
- $\Delta V_{BE} = V_T\ln n$ between two junctions at a current-density ratio $n$ is PTAT.

**Banba current-mode bandgap.** Two PMOS legs feed (node A) Q1 ∥ R2a and (node B) R1 → Q2 (8 units) ∥ R2b. An amplifier forces $V_A = V_B$, so each branch carries (C6 §2)

$$I_0 = \frac{V_T\ln 8}{R_1} + \frac{V_{EB1}}{R_2}.$$

Because the output is a current, the voltage part must also cancel the resistor's own TC ($tc_1$ = −1470 ppm/K for xhrpoly). This sets $R_2/R_1 \approx 4.6$ by hand (C6 §2.1). The residual curvature is ≈ 2–3 % over −40…125 °C (C6 §2.1).

**Trim.** The current is V/R, so it follows the ±15 % R spread, plus ±4 % from $V_{BG}$ and ±3 % TC residual: ±20 % in total (D42). A 3-bit binary trim on the master leg ($G_0 + k$ units, $G_0 = 17$) covers ±19 % of process error with a ≤ 6 % step and a ±3 % adjacent-code residual (D73; C6 §3).

**Start-up and multiple equilibria.** A self-biased reference always has a zero-current equilibrium. A start-up circuit must remove it, then release and get out of the way. C6 found something subtler, a **zero-gain region**: below ≈ 50–60 % of $I_0$ both pnps are off. Both branches are then plain R2 and $V_B - V_A$ is in the µV range, far below the ≈ 2 mV amp offset, so the loop has no restoring force. At sf/27 and ff/125 the loop-break sweep found a real unstable equilibrium at 0.27 µA and 0.06 µA (C6 §6.1, §6.6; WO-50). The fix gave the amplifier a built-in offset (a 2:1 skewed input pair, ≈ 15 mV). In the low-current region the amp then always drives the current up, and the only non-zero equilibrium is $I_0$ (D78 basis; C6 §6.6; WO-55). Part III gives the full history.

## I.14 PVT corners, Monte Carlo, and "green is not proof"

**Corners (SPEC §6; D7).**

| Axis | Values |
|---|---|
| Process | tt, ss, ff, sf, fs, plus R+C points ss_hh and ff_ll |
| Temperature | −40, 27, 125 °C (and 100 °C for 0.25 MHz / N 4096) |
| VAPWR | 3.0 / 3.3 / 3.6 V |
| VDPWR | 1.62 / 1.8 / 1.98 V |
| fs | 0.25 / 2 / 4 MHz |
| Layout | schematic and PEX |

**Monte Carlo.** ≥ 200 runs at tt/27 and ≥ 50 at the worst PVT. Pass = estimated μ ± 3σ inside spec **and** every sample inside spec (SPEC §6). Independent random terms combine RSS and systematic terms linearly. A linear sum of n independent equal 3σ terms is 3n·σ_term = 3√n σ in RSS-equivalent terms (for two equal terms ≈ 4.2σ), so it exceeds the RSS pass rule (D36). **A spec passes only if it passes at every corner** (D1; SPEC §6).

**Green is not proof.** A check that cannot fail proves nothing. Every gate in this project has a **broken copy**, a deliberately damaged circuit or model that must REJECT. A gate whose broken copy passes is reported as blind and fixed; the limit is never relaxed to suit the copy (GUIDE §5; WORKFLOW §11). Examples from the record:
- S4 had 8/8 broken copies (GUIDE §5).
- The precision INL gate was blind to a PMOS-cascode short (3.37 ppm ≤ 5.33). That led to the droop-type copy and the synthetic known-answer table of CL-1d (C1 §2.10).
- The C3 decision-time row could not see a 5× slower comparator (WO-44: `brk_starve` at 6.4 ns ≪ 33.75 ns). That led to the T2band row (C3 §3.3).

Part IV lists the false-pass lessons in full.


---

# Part II: System design (Stage S)

## II.1 The target and the constraints

### II.1.1 Case study: the MCP3421

The user picked the Microchip MCP3421 as the case-study target (CTX §1; MCP):

| Parameter | MCP3421 | Source |
|---|---|---|
| Architecture | ΔΣ + PGA + 2.048 V ref + oscillator + I²C | MCP |
| Resolution / rate | 12 b @ 240 SPS … 18 b @ 3.75 SPS | MCP |
| Noise | 1.5 µV rms @ 3.75 SPS | MCP |
| INL | 10 ppm FSR typ, 35 max | MCP |
| Offset | 15 µV typ, 40 max | MCP |
| Gain error | 0.05 % typ | MCP |
| CMRR / PSRR | 105–110 / 100 dB | MCP |
| Input | ±2.048 V differential, PGA ×1–×8, 3.2 pF sampling cap | MCP |
| Power | 145 µA @ 3 V | MCP |

$2^{bits}\times\mathrm{rate}$ is constant at ≈ 983 kHz. That fits a 1st-order incremental converter near 1 MHz, though this is an inference, not a datasheet statement (MCP).

The feasibility verdict was "partially delulu": the architecture fits TT well, but MCP3421 precision parity is not realistic on a first chip (CTX §1). In particular:
- 1.5 µV needs chopping against sky130 1/f noise.
- 10 ppm INL needs ≥ 80–90 dB of OTA gain.
- A ±0.05 % on-chip reference is impossible without trim, and TT has no fuses (MCP feasibility table).

These findings led to an external, ratiometric reference (D17, D24) and to chopping (D18).

**Prior art on TT** (CTX §4; ROAD §2):
- Scope: a keyword survey of titles and descriptions over 29 shuttles up to ttsky26c (index.tinytapeout.com, 2026-11-07; NOTES §1). A project with an unusual name could be missing.
- The three analog ΣΔ modulators found on sky130 TT are 1st order: Paul Thomas (ttsky26c, CT), tilesos dual ADC (ttsky26c, SC) and shimomi (ttsky26a, "first-order 1-bit continuous-time DSM" converting a PTAT voltage; its README).
- None of these analog modulators has its decimator on chip, and none has measured silicon. Digital decimators do exist on TT: TTSKY26A-ADC-8BIT has an on-chip sinc1 counter, and tt09-decimation_filter and tt09-delta-sigma-decimation-filter are standalone filter projects (NOTES §1). On this chip the decimator is the two CoI accumulators; the final scaling and chop demodulation run in firmware (SPEC §3.7).
- Paul Thomas's ttsky26c design is 1st-order CT, single-ended, at 50 MHz, simulated at ≈ 40 dB (fast, ≈ 1 MHz band) / ≈ 57 dB SNDR (precision, ≈ 100 kHz band). SNDR over a band is a different metric from this design's µV rms at DC.
- Wulff's tt06 SAR is the only measured analog ADC among the references: ≈ 7 ENOB measured against 7.63 simulated.

This design aims at resolution and DC precision, not bandwidth (ROAD §2).

### II.1.2 Tiny Tapeout constraints

| Constraint | Value | Source |
|---|---|---|
| Process | sky130A, TT analog template `tt_analog_2x2_3v3.def`, `uses_3v3` | SPEC §3.9 |
| Tile | 2×2, ≈ 334 × 225 µm ≈ 75,000 µm² (SPEC); DIEAREA of the TT analog template `tt_analog_2x2_3v3.def` as measured in HARD §2: 319.24 × 225.76 µm = 72,071 µm². Paul Thomas's ttsky-sigma-delta frame uses a 334.88 µm width. The TT tools version of the measured template is not recorded; re-check against the template at C7 (Appendix E) | SPEC §1; HARD §2 |
| Supplies | VAPWR 3.3 V analog, VDPWR 1.8 V digital, each ±10 % at the corners | SPEC §1, §6 |
| Metal | met5 forbidden; power stripes on met4 | SPEC §3.9 |
| Analog pins | via `tt_asw_3v3`: < 500 Ω, < 5 pF, ≤ 4 mA | CTX §5 |
| Pin pricing | €40 each for the first two analog pins, then €100 each: 4 pins = €280; plus 4 tiles × €70 = €280; total ≈ €560; a 5th pin would add €100 | CTX §5; D47 |
| Mux | TT selects one project at a time, so the decimator must live inside the analog macro (LibreLane hardening, 1.8↔3.3 V level shifters) | CTX §5; HARD §1 |
| Clock | TT clk assumed 48 MHz (50 MHz does not divide to the fs set) | SPEC §3.8a |
| NVM | none: any trim is volatile and is rewritten by firmware after every rst_n | D47 |

**Pin map (D24).** ua0 VIN+, ua1 VIN−, ua2 VREF+, ua3 VREF− (Kelvin to the sensor ground). Taking REF− from chip ground instead would give an error ≈ u·δ, where δ is the on-chip-to-board ground difference (estimated at 0.1–10 mV and unmeasured). That is ≈ 100 µV–10 mV at full scale, far above the noise floor and not separable on silicon (D24). A 5th pin (ua4, an integrator/supply monitor) was declined (D47).

### II.1.3 Budget top line (SPEC §3.0)

| Budget | Target | Source |
|---|---|---|
| Noise | ≤ 2.5 µV rms @ 15 SPS (all corners for fs ≥ 2 MHz); ≤ 5 µV @ 240 SPS | D27, D29 |
| INL | ≤ 20 ppm FSR | SPEC §3.0 |
| Offset | ≤ 5 µV | SPEC §3.0 |
| Gain error | ≤ 0.5 % | SPEC §3.0 |
| CMRR | ≥ 100 dB DC with sys chop (120 dB goal); ≥ 60 dB with sys chop off | D30, D32 |
| Analog current | ≤ 200 µA design budget in every mode; 189 µA worst-case fast after trim accepted as risk | D46c, D42 |
| Fast mode INL (4 MHz) | N 64 ≤ 200, N 256 ≤ 20, N 1024 ≤ 5 ppm | D28, D39 |

The **joint model run at spec** gives 0.94 µV @ 15 SPS, 3.9 µV @ 240 SPS and 3.4 ppm INL (SPEC §3.0). The 0.94 µV figure governs (D48(3)).

**Main trade-off chain** (GUIDE §4):
- INL needs speed.
- Speed needs current, since SR = I/C.
- Current hits the 200 µA budget.
- Noise needs $C_s$, which needs area and slew current.

## II.2 System choices: what, why, alternatives, numbers

### II.2.1 Incremental versus free-running (GUIDE A1)

| Option | For | Against |
|---|---|---|
| **Incremental, reset every conversion (chosen)** | Nyquist-like converter for DC / multiplexed sensors; no idle tones across conversions; tiny CoI decimator (2 accumulators + counter); exact reconstruction with a measurable residue; each conversion independent, so system chop can swap at boundaries | needs a reset window and residue handling; finite-gain leak accumulates over N |
| Free-running ΣΔ + sinc filter | standard, higher SQNR per cycle | filter memory across conversions, idle tones, no clean per-conversion boundary for system chop |

### II.2.2 Order 2, CIFB, 1-bit (GUIDE A1)

- **Order 1** (all prior TT designs) gives ≈ $\log_2 N - 1$ bits. 18 b would need $N \approx 2^{19}$ cycles: too slow and too noisy for µV work. It is kept as a characterisation fallback (SPEC §1; D21).
- **Order 2** gives ≈ $2\log_2 N - 4$ bits. N 4096 → ≈ 20 b. That is enough at OSR 1024–4096 (SPEC §1; MODEL finding 1).
- **Order 3** was rejected for stability and area (GUIDE A1).
- **CIFB with delaying integrators.** Its state equations give the exact reconstruction of I.5.3 with integer $k/c_1$.
- **1-bit.** It is inherently linear (I.2.4).

### II.2.3 Coefficients: c1 0.125, c2 0.5, k 0.5 (D10, D17, D19)

S1 compared four points at fs 2 MHz, N 1024, A0 75 dB and a 2 V differential linear range (`s1_vref.md`):

Table from `s1_vref.md` v1 (`s1_vref_v2.md` also exists).\n\n| Option | VREF | c1 / c2 / k | peak x1 / x2 (V/side) | INL ppm (vlin 2 V) | noise @15 SPS (lf 5.3) | Cint1 per side | Verdict |
|---|---|---|---|---|---|---|---|
| A | 1.2 | 0.25 / 0.5 / 1 | 0.705 / 0.711 | 22.4 | 0.52 µV | 4 pF | ACCEPT |
| A2 | 1.2 | 0.25 / 0.25 / 1 | 0.705 / 0.356 | 21.1 | 0.51 µV | 4 pF | ACCEPT |
| **B** | **2.048** | **0.125 / 0.5 / 0.5** | **0.602 / 0.607** | **12.4** | **0.54 µV** | 8 pF (at Cs 1 pF) | ACCEPT |
| C | 2.048 | 0.25 / 0.5 / 1 | 1.203 / 1.213 | 942.3 | 0.48 µV | 4 pF | REJECT (INL, swing) |

**Choice: option B** (user, D17).
- It has the most INL margin (12.4 vs 22.4 ppm), keeps the MCP3421 FSR, and has the lowest swing (0.61 V/side).
- B's INL edge over A comes from halving $c_1$, not from VREF (REVIEW-S1S2 M1; D19).
- B is bit-identical to A ($k/c_1 = 4$ in both).
- An earlier "option B" with $c_1 = 0.125, k = 1$ was a different NTF and was corrected live (D10; S1 theory check "wrong-B ≠ A").
- Costs: white-noise gain up to 9.3 and, at $C_s$ = 1 pF, $C_{int1}$ = 8 pF/side (+4000 µm²). D22 halved this to $C_s$ 0.5 / $C_{int1}$ 4 pF.
- $c_2$ stays a free knob for $x_2$ sizing, because 0.25 would halve $x_2$ (SPEC §1).

### II.2.4 VREF 2.048 V, external and ratiometric (D17, D24; GUIDE A3)

- **Value.** 2.048 V keeps the MCP3421 FSR (4.096 V differential). The ratiometric range is 1.0–2.048 V (SPEC §1).
- **No on-chip voltage reference.** For the anchor application (ratiometric RTD/thermistor) the reference cancels, and an untrimmed sky130 bandgap would be ±1–2 % / 20–50 ppm/°C (MCP).
- **Board requirement.** A buffer plus ≥ 100 nF at ua2/ua3 and ≤ 10 Ω DC per pin (D25). The u³ INL from reference current through that R is ≈ 1.4 ppm against a 2 ppm share (SPEC "Reference" row; `s3_budget.md`).
- **Alternative rejected.** VREF 1.2 V (option A) was the provisional choice (D3) before S1 showed B's margin.

### II.2.5 Cs 0.5 pF, Cint1 4 pF, stage 2 (D14, D22, D25; GUIDE A4, A5)

| Cap | Value | Ratio | Source |
|---|---|---|---|
| Cs1 (sample = 1-bit DAC cap, shared) | 0.5 pF | — | D14, D22 |
| Cint1 | 4 pF | c1 = 0.125 | SPEC §3.4 |
| Cs2 | 0.5 pF | — | SPEC §3.4 |
| Cint2 | 1 pF | c2 = 0.5 | SPEC §3.4 |
| Ck2 (k-DAC cap, full VREF, on the OTA2 node) | 0.25 pF | Ck2/Cint2 = c2·k = 0.25 | D25; SPEC §3.4 |
| MIM total | ≈ 9,000 µm² (≈ 12 % of the tile) | — | SPEC §3.0 |

**Shared Cs (D14).** The input cap is also the DAC cap. Gain is then set by ratios, not by absolute caps, and the anchor application needs no PGA. Separate input/reference caps were far more settling-sensitive. A PGA (×2/×4/×8) moved to stretch; the config field was removed (D45 h).

**Cs 0.5 pF (D22).**
- INL is unchanged, because it is set by ratios (WO-04: 3.63 ppm).
- Noise is 0.556 µV kT/C-only @ 15 SPS (`s3_budget.md:31`), 0.71 µV in the WO-04 ota+sys model (D22), and 0.94 µV in the joint run (D48(3)). SPEC §1 (lines 18, 25) labels 0.71 as kT/C-only; see Appendix E.
- It saves ≈ 4,000 µm² against 1 pF.

**Stage-2 choices (D25, coordinator defaults).**
- Cs2 samples $x_1$ in OTA1's hold phase. This keeps OTA1's slew need at ≈ 12 V/µs.
- The k-DAC is a separate 0.25 pF cap on full VREF, so no VREF/2 node is needed.
- Cs2's $x_1$-side plates are shorted to each other in OTA2's integrate phase, not tied to a CM bus. Tying them to V_ICM kicked −79 mV, 4–8× the CMFB tolerance (CL-2).

**MIM only.** No MOS caps in the signal path. MOS caps have percent-level C(V), and `cap_mim_m3_2` uses met5, which TT forbids (CTX §2; GUIDE A17). Known gap: the sky130 MIM model has no voltage coefficient and no bottom-plate parasitic, so MIM VCC appears only in PEX or silicon (SPEC §6; V9).

### II.2.6 fs: 2 MHz precision, 4 MHz fast with bias boost (D13, D28, D31, D39, D41)

**Why ≈ 1–2 MHz** (ROAD §1):
- Nearly jitter-immune.
- GBW of 10–20 MHz is µA-level.
- Input impedance ≈ $1/(f_s C_s)$.
- Leakage droop sets the lower end.

2 MHz gives ≈ 1.4× lower noise than 1 MHz at the same output rate (CTX §6).

**fs set.** At clk = 48 MHz the divider codes 0…4 give 4 / 2 / 1 / 0.5 / 0.25 MHz. Codes 5–7 are normalised to 1 (SPEC §3.8a; CL-16).

**The 4 MHz problem.** Slew-then-settle error is ≈ 3e-5 of a step at 2 MHz but ≈ 6e-3 at 4 MHz with GBW 10 MHz / SR 10 V/µs: thousands of ppm (SPEC §3.1 F3). Options and the decision path:
- D28: always-on 20 MHz GBW, +≈ 45 µA.
- D13: 4 MHz is a fast / low-resolution mode with its own INL target. Precision is gated at 0.25–2 MHz.
- D31: a **bias-boost config bit** doubles the OTA tails only in fast mode.
- D39: OTA2 ×1.5.
- D41 (option A′): OTA2 tail ×2. The gates are absolute: boosted loaded GBW OTA1 ≥ 20 MHz, OTA2 ≥ 22.5 MHz; SR ≥ 25 / 27 V/µs.

**Why absolute gates.** gm grows slower than I in moderate inversion. The ratio gate GBW(boost)/GBW(nom) ≥ 1.9 needed gm/Id ≈ 24, which is infeasible at OTA1 size, so it was withdrawn (SPEC §3.0 D31 text; REVIEW-S5e C-M1).

**Current.** ≈ 106–113 µA precision (including ≈ 6 µA bandgap), ≈ 172 µA fast nominal, ≈ 189 µA fast worst after trim (SPEC §1, §3.0).

**Fast-mode evidence (tier 1, S5h, converged).**
- D39 control point (OTA2 20.25 V/µs, conservative): 3.29 / 3.36 ppm O1/O2, verdict 3.43 ppm.
- A′ at N 1024: 0.144 (cold) / 1.450 ppm (hot).
- A′ at N 256: 0.403 / 1.982 ppm against a gate of 20 (SPEC §3.0).

**0.25 MHz / N 4096 is rated −40…100 °C only.** Island leakage drift $= I\cdot N/(f_s C)$. Junction leakage falls ×9.4 from 125 to 100 °C. 100 pA at 125 °C becomes ≈ 11 pA at 100 °C, a drift of 37 / 86 mV (stage 1/2), inside 0.2 V (D39(c); `results/leak_temp.md`). Leakage rows: ≤ 20 pA at ff/100/3.6 and ≤ 90 pA at ff/125/3.6 (SPEC "Virtual ground" row).

### II.2.7 N: 64 / 256 / 1024 / 4096 (D23, D38c)

N is a counter value, so every N is a digital-only cost and all four stay in v1 (SPEC §1).
- **Precision modes (3.75–60 SPS) use N 4096.** N 1024 leaves ≈ 33 µV of deterministic quantisation error that averaging does not remove; N 4096 leaves ≈ 2 µV (D23).
- **240 SPS** = N 1024 sys pairs at 2 MHz (D38c).
- **N 256 and N 64 at 2 MHz** are characterisation-only, with no INL spec (D38c, D43d).
- **Output rate.** A frame is N + 2 fs cycles. Firmware averages K sub-conversion pairs to reach 3.75–240 SPS (SPEC §1). Slot length at N 4096 is 2.05 ms at 2 MHz and 16.4 ms at 0.25 MHz; the shortest slot is 16.5 µs (N 64 at 4 MHz) (SPEC §3.8a).

### II.2.8 Chop modes (D4, D18, D19, D45 g; GUIDE A7)

| Mode (sys_en, ota_en) | Use | Offset residue | Source |
|---|---|---|---|
| ota + sys (1, 1), reset default | data | cancels; −0.015 µV sys-pair in the budget | SPEC §3.8a; GUIDE §4 |
| sys only (1, 0) | data, fallback if OTA chop costs A0/settling | cancels | SPEC §3.6 |
| ota only (0, 1) | characterisation only | lf·Vos1/(N−1), measured by V4a | D45 g; SPEC §3.7a g |
| none (0, 0) | characterisation only | lf·Vos1/(N−1) plus 2·Vos2/(c1(N−1))·1.5 = 52.7 µV at Vos2 9 mV, N 4096 | SPEC §3.6 |

Further rules:
- OTA chop is on **OTA1 only**. OTA2's 1/f is divided by $c_1(N-1)/2$, and its offset cancels with sys chop (SPEC §3.6, review E2/M3).
- OTA chop stays in v1 only if C1 meets A0 ≥ 80 dB and settling with the chopper in place (SPEC §3.6). C1 placed the input chopper at the gates (3.3 V NMOS) and the output chopper at the fold node (C1 §1.4).
- OTA chop runs at $f_{ch} = f_s/2$. Its phase is 0 in the reset window and $n \bmod 2$ afterwards (SPEC §3.7a i).
- A chop edge may fall only in a non-overlap interval (SPEC §3.6 rule 13).

### II.2.9 Order-1 mode (D21, D74, D76)

Order 1 is a characterisation-only fallback (D21). In order 1:
- the comparator still reads $x_2$, with no input mux (D74);
- integrator 2 is reset every cycle late in φS, gated by the comparator's decision-done signal, so $x_2 = (C_{s2}/C_{int2})\cdot x_1 = c_2\cdot x_1$, not $k\cdot x_1$ (C4 §2, D76);
- the Ck2 DAC is held in its rest short.

This adds one loop delay. WO-53 showed it stable with ≈ 10 b at N 4096 (I.3.4). acc2 keeps accumulating ΣS (a defined value that firmware ignores; SPEC §3.7a f). Reconstruction is $u = \mathrm{acc}_1/N$ (golden `den` = N).

### II.2.10 CM-rejecting input switching (D12, D25, D33, D36; GUIDE A8)

The input CM can sit anywhere in 0…VREF (user Q1). The virtual-ground CM is $V_{cm,s} + V_{ref,cm} - V_{in,cm}$, so without CM rejection the OTA input range would have to absorb it (SPEC §2.1 F2).

**D12: top-plate shorting.** During sampling, the two top plates are shorted together, so only differential charge is transferred.

**CMRR budget.** Matching alone cannot give 60 dB with sys chop off: that needs $\varepsilon \le 0.1$ % 3σ, while MIM gives ≈ 0.75 % at 0.5 pF (D32). The D12 residual is

$$\varepsilon_{eff} = \frac{(C_p/C_s)\,\varepsilon_{Cs} - \Delta C_p/C_s}{1 + C_p/C_s} + \varepsilon_{inj}.$$

The minus sign was confirmed in SPICE: deck versus closed form 0.0 % in 12 cases (D36). Allocations: $C_{p,top}$ ≤ 20 fF/side; random $\Delta C_{p,top}$ ≤ 0.25 fF 3σ; systematic ≤ 0.08 fF; $\varepsilon_{inj}$ ≤ 2.8e-4. Gate: |sys| + RSS(random 3σ) + |ε_inj| ≤ 1e-3 (SPEC "Capacitors" row; D37).

**Result.** RSS gives 8.407e-4 = 61.5 dB, passing 60 dB by +1.5 dB. The worst row is 61.1 dB. It misses the 66 dB design target (`s4_corners.md`; D36). The 66 dB target is a layout goal ($\Delta C_{p,top}$ ≤ 0.15 fF). Sys-on CMRR cites tier-1 cm2 at 137–173 dB (O0, quasi-static, exempt from the convergence rule; SPEC §3.0 CMRR text; D39(d)).

**False pass on the way.** An earlier SPICE CMRR of 132–152 dB was withdrawn: the deck had $C_{p,top} = 0$ and the metric was wrong (D33).

## II.3 Budget allocation (S3, as corrected by REVIEW-S3)

S3 swept one parameter at a time on an otherwise ideal loop and set per-block shares. Noise combines RSS; INL, offset and gain combine linearly (`s3_budget.md` allocation table; SPEC §3.0 allocation sentence).

| Metric | Line | Share | S3 value | Per-block spec it became |
|---|---|---|---|---|
| noise µV @15 | sampling kT/C (Cs 0.5 pF) | 1.2 | 0.556 | Cs 0.5 pF |
| noise | OTA1 thermal | 1.2 | 0.742 | en ≤ 10 nV/√Hz (S3); later the 390 µV v_vg row (CL-31) |
| noise | OTA1 1/f + chopper residue | 1.0 | 0.155 | fc ≤ 631 kHz (info), residue rows |
| noise | comparator | 0.3 | ≈ 0 | ≤ 5 mV rms |
| noise | OTA2 + stage-2 kT/C | 0.3 | 0.004 | Cs2 0.5 pF |
| noise | reserve | 1.0 | — | — |
| INL ppm | OTA gain + swing linearity | 8 | 3.27 | A0 ≥ 80 dB, A ≥ 75 dB to 1.4 V; table-INL gate |
| INL | input settling | 2 | ≈ 0 | τ_in ≤ 18.75 ns |
| INL | reference settling | 2 | ≈ 0 | τ_ref ≤ 10 ns |
| INL | comparator | 1 | ≈ 0 | offset row (CL-30) |
| INL | quantisation floor (N 4096) | 1 | 0.419 | N 4096 |
| INL | reference current × R_ext (u³) | 2 | 1.4 | R_ext ≤ 10 Ω, ≥ 100 nF |
| INL | reserve (MIM VCC, injection, substrate) | 4 | — | — |
| offset µV | sys-pair residual | 1 | 0 | Vos 9 mV, vres 5 µV |
| offset | reset residue (non-cancelling) | 1 | 0.485 | r ≤ 1e-4, window ≥ 2 cycles |
| offset | vg leakage (non-cancelling, hand) | 1 | 0.8 | ≤ 100 pA (later 90 / 20 pA) |
| offset | reserve | 2 | — | — |
| gain ppm | finite A0 and swing | 300 | 62.1 | A ≥ 80 dB |
| gain | settling | 500 | 0.015 | τ_in, τ_ref |
| gain | k/c1 mismatch | 50 | 10.9 | ≤ 0.56 % 3σ |
| gain | reserve (calibratable) | 4150 | 19.1 | — |

The S3 theory checks matched closed forms (`s3_budget.md`):
- $lf\cdot V_{os1}/(N-1)$: 20.49 vs 20.44 µV.
- $2V_{os2}/(c_1(N-1))$: 35.17 vs 35.16 µV.
- Reset residue $2r\,x_{1max}/(c_1(N-1))$: 47.65 vs 47.67 µV.
- Leakage $I/(f_sC_s)$: 799.9 vs 800.0 µV (the 47.65 µV check is at r = 0.01).

**Why a per-block INL share of 8 ppm for the OTA leaves the in-loop gate at 1.333 / 3.33 / 5 ppm.** The OTA's 8 ppm splits across mechanisms:
- the in-loop slew/settling gate B: 1.333 ppm at 2 MHz (the slew share), 5 ppm at 4 MHz boost (SPEC OTA1 GBW row);
- the static table-INL gate: 5.33 ppm precision and 3.33 ppm boost, i.e. 5/1.5 for a 1.5× margin (CL-1b).

## II.4 Stage-S evidence: S1 … S7

| Study | Question | Result | Source |
|---|---|---|---|
| S0 | infrastructure, precheck flow | tools and precheck broken copies accepted (drcfeol fails both Magic and KLayout FEOL, accepted per D20) | D20; `results/s0_precheck.md` |
| S1 | VREF and swing | option B: 12.4 ppm, 0.61 V/side, bit-identical to A | II.2.3; D17 |
| S2 | chopping | sys / ota+sys offset ≤ 0.8 µV at Vos 9 mV; OTA-only residue lf·Vos/(N−1) | I.7; D18 |
| S3 | error budget → per-block specs | allocation table above; joint 0.94 µV / 3.9 µV / 3.4 ppm | II.3; D26 |
| S4 | budget at every corner + MC (assumed block mappings, not circuits) | worst n15 2.983 µV (limit 3.0 at ss/125, 0.25 MHz, per D27), n240 3.603 µV, INL 5.234 ppm, offset 0.848 µV, gain 71.6 ppm, sys-off CMRR 61.1–61.5 dB | `s4_corners.md`; D27, D36 |
| S5 (a–h) | tier-1 behavioural SC modulator in ngspice | slew knees, fast-mode options, Ck loading bug, convergence ladder; OTA1 knee 10.23–10.28 V/µs (O2, N 1024) | `s5*_tier1.md`; D38, D43, D44 |
| S6 | golden vectors for C9 | 500/500 frames bit-exact against an independent integer checker; every mutant REJECTs | `s6_golden.md`; II.5 |
| S7 | SPEC freeze + review | REVIEW-S7 E1–E24 applied, I/O table §3.8a added; frozen 2026-11-09, tag `spec-v1`; 152 tests passing | D46, D50 |

### II.4.1 Tier 0, tier 1 and gate B

**Tier 0** is `model/iadc.py` (MODEL): a vectorised Python model of the order-1/2 CIFB incremental loop. It models:
- finite and swing-dependent gain, and clipping;
- kT/C with OTA excess;
- OTA white and 1/f noise;
- offset and chopper residue;
- OTA and system chop;
- input/reference settling;
- comparator offset and noise.

It is fast enough for full corner sweeps and MC (GUIDE §2).

**Tier 1** is a behavioural SC modulator in ngspice. It uses a B-source OTA with gain, GBW, slew and swing, plus ideal switches. It is the bridge that checks the model against circuit physics. The model and the tier-1 deck must agree within ≤ 5 % rel_sym; they agreed at 0.0–0.7 % (GUIDE §5). A disagreement is treated as a finding. Two examples:
- **The Ck loading bug.** The deck/model INL ratio of 1.2–1.4 traced to a missing $C_{k2}$ load on the stage-2 node: the model had $(1 + c_2)$ where the deck had $1 + c_2(1+k)$ (RESUME 2026-11-08; D38(b)).
- **The S4 sys-on "metric floor".** It was a model bug: the residue correction was applied in the modulator frame after demodulation (D38(a)).

**The convergence ladder (D43c).** Every gated tier-1 INL with < 3× margin is run at O0 → O1 → O2:
- each step divides reltol by 10, halves tmax and divides chgtol by 10 (floored);
- trtol is 1 at O2;
- tmax ≤ τ_cl/10.

Accept if |INL(O2) − INL(O1)| ≤ max(10 %·INL, 0.1·(gate − INL)). The verdict is INL(O2)·(1 + |Δ|/INL). O0 numbers are unconverged with either sign. One row moved 6.69 → 18.77 ppm from O0 to O2 (`s5h_tier1.md`), so O0 numbers are not cited.

**Gate B** is the in-loop gate (D48(1)): the transistor OTA1 in the tier-1 deck with OTA2 behavioural, N 1024. Limits:
- ≤ 1.333 ppm at 2 MHz;
- ≤ 5 ppm at 4 MHz boost.

It runs O1/O2 converged at tt/27, ss/−40/3.0, ss/125/3.0 and fs/125/3.0 (boost; CL-3). Its broken copy is a tail set for 9.5 V/µs. The isolated step test (A) is report-only: health $|\varepsilon_{dyn}| \le 10^{-4}$, watch $\varepsilon_{NL} \le 3\times10^{-7}$. A step from rest cannot see the in-loop slew knee, and gating it would force GBW ≳ 14 MHz (D48; S7b-M2).

## II.5 Golden vectors (v2 → v3.2) and the digital conventions (§3.7a)

### II.5.1 Golden vectors

`golden/s6_vectors.json` is generated by `python -m model.golden` (tier 0, ideal-A, seed 20261109). The JSON is canonical, so regeneration is byte-identical, and the sha256 is pinned in the test (GOLD).
- The loop uses option B with $k/c_1 = 4$.
- Every $u$ is a multiple of $2^{-20}$, so float and integer implementations agree bit for bit.
- The bitstreams come from an ideal-A loop, so they do not depend on the OTA model (D38(d)).

| Revision | What it added | Source |
|---|---|---|
| v2 (WO-17/18, S6) | 240 mode vectors + 2 sequences = 500 frames; cycle-level control trace (§3.7a k) | `s6_golden.md`; SPEC §3.7a k |
| v3 (WO-33) | boost/trim config fields, reset values, fs_div table, status word, hold/overrun semantics, word order, debug bus; 320 mode + 48 offset vectors | GOLD; SPEC §3.8a G3 items |
| v3.1 (WO-35, D66) | `hold_reset` (tag 0x0100, status 0x0800), effective-change rule, rd before/on/after load, `cfg_shift`; D70 rising-edge debug y | GOLD; CL-12…CL-27 |
| v3.2 (WO-53, D76) | `o1d_vectors`: 72 order-1 vectors with the extra loop delay; v3.1 rows unchanged; sha 6ae28d76… | GOLD; WO-53 |

**Independent checker.** `model/tests/test_golden.py` is an integer loop and sequencer written from SPEC with no `iadc` import. It reproduces all 500 v2 frames bit-exactly (`s6_golden.md`). Every mutant must REJECT:
- inclusive S;
- N±1;
- y flipped;
- acc2 23-bit, acc1 13-bit;
- no sign;
- y0 free, y0 pass-through;
- swap late;
- acc_clear early/late;
- OTA phase not restarted;
- mid-pair latch;
- frame_ctr reset on change;
- tag from another flop;
- and others.

24-bit acc2 and 14-bit acc1 must ACCEPT (GOLD).

### II.5.2 Digital conventions (SPEC §3.7a; D45, D46a)

| # | Rule |
|---|---|
| a | $y[0] = +1$ forced at reset release; the cycle-0 comparator output is ignored; one retimed FF drives DAC, decimator and raw pin |
| b | slot parity sets the chop sign: even slot +1 (direct), odd −1 (swapped); the +−−+ ordering is dropped |
| c | frame = acc1 (32 b), acc2 (32 b), 16-bit tag: chop, order, n_code (2 b), sys_en, ota_en, short, invalid, frame_ctr (8 b, wraps, reset only by rst_n) |
| d | writes go to a shadow; shadow → active on the edge that starts an even slot's reset window; last write wins; only effective changes count (CL-14, CL-15, CL-16) |
| e | invalid = both frames of the first pair after any latched change (including boost or trim) and after rst_n |
| f | order-1 acc2 keeps accumulating ΣS |
| g | OTA-only chop allowed, characterisation only |
| h | no PGA field |
| i | reset window 2 fs cycles; sys swap, accumulator clear and y force inside it; OTA chop phase 0 in reset, then $n \bmod 2$ |
| j | accumulators emitted in the modulator frame (no sys sign on chip) |
| k | a slot is N + 2 cycles: c = 0, 1 reset; n = c − 2; `acc_clear` on c = 1 (the edge that releases `rst_analog`); `y_force` strobe at n = 0 |

**The I/O map** (SPEC §3.8a; D46b; D47):
- **Read bus.** A 16-bit parallel bus on uo_out + uio. ui_in[2:0] selects one of 6 words: acc1 hi/lo, acc2 hi/lo, tag, status.
- **rd.** Frame acknowledge with a guard: clear only if no new frame loaded since the rd edge (CL-12, CL-13).
- **Config.** A 16-bit serial write: order, n_code, fs_div, sys_en, ota_en, short, boost, trim.
- **Debug mode** (ui_in[7]) puts the raw bitstream, bit_valid, frame_ready, bit clock, rst_analog, sys_swap, chop phase and invalid on uo.
- **Host rate.** The host must read every frame. A frame is 6 reads in 16.5 µs at N 64 / 4 MHz, i.e. ≥ 0.36 Mword/s. That is trivial for RP2040 PIO/DMA but out of reach of MicroPython bit-banging (SPEC §3.8a).


---

# Part III: Block designs (Stage C)

## III.0 Block map and the Stage-C recipe

```
            ua0 VIN+ ─┐                      ┌─ ua2 VREF+   ua3 VREF− (Kelvin)
            ua1 VIN− ─┤                      │
                      ▼                      ▼
   ┌──────────────── C4 switches + D12 top-plate short + DAC switches ──────────────┐
   │   Cs1 0.5p ──► [vg1]──► C1 OTA1 + CMFB (Cint1 4p) ──x1──► Cs2 0.5p ──► [vg2]   │
   │                                                          Ck2 0.25p ──►  │      │
   │                                         C2 OTA2 (Cint2 1p) ◄────────────┘      │
   │                                                │x2                              │
   │                                         C3 StrongARM ──q──► (1.8 V)             │
   └──────────────┬──────────────────────────────────────────────┬────────────────┘
                  │ C6 bias (Banba BGR + 3-bit trim, boost leg)   │ C7 level shifters
                  ▼                                               ▼
           C9 digital macro: fs divider, sequencer, DAC flop (one FF), CoI acc1/acc2,
           hold/frame/overrun, serial config, 16-bit read bus  ──►  ui/uo/uio (TT pins)
```

The block numbering follows the PLAN:
- C1 OTA1 + CMFB;
- C2 OTA2;
- C3 comparator;
- C4 switches and non-overlap generator;
- C5 choppers;
- C6 bias / bandgap / start-up;
- C7 level shifters;
- C8 reference input;
- C9 digital;
- C10 MIM arrays.

C1 came first because it is the critical path with no TT precedent (GUIDE §2, §8).

**Stage-C recipe** (PLAN; GUIDE §5): each block goes through a design note → `sd-adc-design-reviewer` → netlist and gate testbench → full PVT + MC → reviewer → PEX re-simulation. Every testbench row:
- prints ACCEPT/REJECT;
- exits non-zero on REJECT;
- fails on NaN or a missing measurement;
- takes its expected values from SPEC, never from the DUT;
- has a broken copy that must REJECT (C1 §4 rules).

## III.1 C1: OTA1 + CMFB

### III.1.1 Purpose and interface

OTA1 is the first integrator's amplifier, so it sets most of the INL, noise and slew budget.
- **Load per side, itemised** (C1 §2.1): 0.78 pF integrate / 0.90 pF hold. The SPEC conservative sum is 1.30 pF and the tier-1 lump 1.4 pF.
- **Feedback factor:** $\beta_1 \ge 0.83$ (CL-4).
- **Virtual-ground CM:** V_ICM = 1.20 V.
- **Output CM:** V_OCM = 1.50 V (C1 §2.4–2.5).
- **Ports:** inputs vg1p/n; outputs o1p/n; clock ports for the input chopper, fold chopper, CMFB phases and island shunts; bias ports from C6 (`ibtp`, `ibn`, `ibp`, `ivbl0`) (C1 §1; C6 §1).

### III.1.2 Topology and alternatives

| Option | Verdict | Reason |
|---|---|---|
| **Fully differential folded cascode, PMOS input (chosen)** | chosen | one stage (no Miller compensation), good swing with Vdsat-tracking cascodes, PMOS for lower 1/f (SPEC §3.1) |
| Telescopic cascode | rejected | output swing (C1 §1.6) |
| Two-stage Miller | rejected | current and PM window (C1 §1.6) |
| Gain boosters | rejected (P2, D51) | fast mode would reach ≈ 196–204 µA (CL-1 reason) |

**Devices (D40a).** The input pair uses 1.8 V `pfet_01v8` on the 3.3 V supply, with bulk tied to the tail. This gives better gm/Id and matching per area than thick oxide. The cost is a device-stress proof: every terminal pair stays ≤ 1.98 V over all transients. Everything else is a 3.3 V (`g5v0d10v5`) device, so only `m_in` needs the stress proof (C1 §1.1).

### III.1.3 Revision history (rev A → B → C)

**Rev A (WO-20)** had:
- m_pl / m_n 40/4 with fixed cascode biases;
- input pair 40/1 (gm/Id 11.05 at ss/125 boost, GBW 21.8 MHz);
- a protection-cascode replica that was infeasible at ss/−40;
- a 3.3 V tail clamp that never conducts;
- 1.8 V vg switches driven at 1.62 V, which are off (C1 rev B table).

REVIEW-C1a raised M1–M8.

**Rev B (WO-21)** answered them (C1 rev B table):

| Item | Rev A | Rev B | Evidence |
|---|---|---|---|
| M1 headroom | fixed V_FOLD/V_SDL 0.45 V | m_pl 80/4 + 15/2 CMFB section, m_n 72/4, m_nc 20/2, m_pc 40/2; **Vdsat-tracking** diode biases (K_N 8, K_P 5) | SIM: every device ≥ 0.09 V above Vdsat at 18 points; A0 ≥ 79.6 dB |
| D51(2) gm first | 40/1 | **80/0.5** (same W·L 40 µm²: same Cgg and Pelgrom σ) | SIM boost GBW ≥ 26.5 MHz at the same current |
| M3 protection cascode | replica V_DIN 1.10 V | m_pp gate tied to 0 V | lower input-CM limit 0.10–0.39 V vs 0.87 V needed |
| M4 tail clamp | PMOS clamp | dropped; vg bounded by island/reset switches **closed by default** while rst_n is low or the bias is invalid (CL-5) | design rule + tb10 broken copy |
| M5 chopper / island | nfet_01v8 1/0.15 at 1.62 V | nfet_g5v0d10v5 (chopper 4/0.5, island 2/0.5) on 3.3 V level-shifted clocks | SIM: 1.8 V switch Ron 62 MΩ–1.5e15 Ω (off); 3.3 V NMOS 0.82–2.5 kΩ |

**Rev B op/AC results** (C1 §2.3; spot deck, ideal CMFB, no junction caps, C_L 1.4 pF):

| corner | A0 base | A(v)min base | A0 boost | A(v)min boost | GBW base/boost (MHz) | PM base/boost |
|---|---|---|---|---|---|---|
| tt/27/3.3 | 81.5 | 80.3 | 83.6 | 81.4 | 16.9 / 33.0 | 80.1 / 79.5 |
| ss/−40/3.0 | 81.7 | 80.8 | 84.0 | 82.3 | 21.5 / 41.3 | 78.4 / 77.2 |
| ss/125/3.0 | 80.5 | 78.6 | 81.2 | 73.6 | 14.5 / 27.7 | 81.0 / 80.7 |
| fs/125/3.0 | **79.6** | 77.9 | 80.8 | 74.7 | 13.5 / 26.5 | 82.0 / 81.6 |
| sf/125/3.0 | 80.8 | 79.0 | 81.4 | 74.4 | 15.1 / 28.3 | 80.3 / 80.3 |
| ff/−40/3.6 | 82.3 | 81.5 | 85.0 | 83.7 | 21.3 / 41.4 | 78.7 / 77.5 |
| ff/125/3.6 | 81.2 | 79.7 | 82.8 | 78.4 | 14.4 / 27.6 | 81.3 / 81.2 |

- Precision A0 failed only at fs/125 base (−0.4 dB).
- A(v) fell at hot boost because the output-swing top end was 0.04–0.10 V short (C1 §2.4).
- The broken copy (m_nc D–S short) gave A0 41.3 dB, REJECTED (C1 status note).

**Rev C (WO-23)** made these changes:
- **Unit-finger 1:32 mirrors.** The first narrow single-finger references shifted I_fold/I_tail to 1.7–2.6, a narrow-width Vth effect. Unit fingers restored 1.27–1.36 at all 18 points (C1 rev C lesson).
- **m_pc 80/2** for swing.
- **Pair 120/0.5 (D54).** This was the free route: same current, worst boost GBW 26.9–27.0 MHz, $\beta_1$ 0.831–0.846. A 160/0.5 pair broke $\beta_1 \ge 0.83$ (C1 §2.10 GBW table).

Rev C run 5 used K_P 8 base / 7 boost, because one K_P could not serve both modes (C1 §2.10):
- K_P 7 left m_pl at 0.043 V at fs/−40 base.
- K_P 8 cut the ss/125 boost span to 1.355 V.

| corner | A0 base | boost span (V) | INL boost N1024 (≤ 3.33) | INL prec N1024 / N4096 (≤ 5.33) |
|---|---|---|---|---|
| tt/27 | 80.8 | 2.06 | 0.68 | 0.44 / 0.42 |
| ss/125 | 81.3 | 1.41 | 2.20 | 0.74 / 0.73 |
| fs/125 | **79.3** | 1.48 | **2.31** | 0.81 / 0.79 |
| ff/−40 | **79.5** | 2.61 | 0.38 | 0.33 / 0.31 |
| fs/−40 | **78.4** | 1.95 | 0.52 | 0.40 / 0.39 |

Outcome (C1 §2.10):
- Table-INL passed at all 9 PVT in both modes.
- Precision $A_0 \ge 80$ dB failed at 3 of 9 corners.
- The PMOS-cascode-short broken copy REJECTED in boost (9.86 ppm) but **passed** the precision gate (3.37 ppm). The precision gate was blind to it, and that finding led to CL-1d (II.4; I.14).

### III.1.4 Precision A0: the reference saga (D55 → D58 → D59 → D60)

| Step | Decision | What happened | Source |
|---|---|---|---|
| 1 | D55: m_plc L 2 → 4 with Cc 0.2 pF (≈ +1.2 dB) | WO-24 spot sweep showed **K_P 10 alone** reaches ≥ 82.0 dB; D55 adds only 0.5–0.7 dB and lowers f_cm ≈ 25 % | WO-24 step 1; D58 |
| 2 | composite 4∥×4-series 1:32 references (RC-M2, for matching) | netlisted A0 79.47 dB at fs/−40, 80.23 at ff/−40: **composites with bulk at the rail mirror ≈ +20 % current** (I_tail 21–23 µA vs 18.5), diluting K_P 10 → ≈ 8.8 at cold. Single-finger references: 83.66 / 83.80 dB | WO-24 diagnosis; D58 |
| 3 | D58: scale I_REF by the measured ratio + **replica-fed cascode bias** (K_P/K_N track the real folded branch); D55 reverted | precision A0 met at all 9 (min 80.43); but I_tail ±3 % failed at 5 of 9 (−4.0…+4.2 %), because the composite ratio moves 1.14–1.25 over PVT; the replica ran ≈ +5–9 % high | WO-25; D58 |
| 4 | D59: **parallel-only unit-finger references at 1:8**, K_P 12.5 base, replica fix | op/AC all exits met: precision A0 min 83.79 dB (≥ 3.5 dB margin), I_fold/I_tail ≥ 1.277, β1 ≥ 0.832, boost hot span ≥ 1.414 V; the mirror-ratio row failed (0.944–1.031, systematic CLM/DIBL from diode-vs-mirror Vds) | WO-26; D59 |
| 5 | D60: ratio row → info (systematic, covered by PVT); I_REF_btp recentred +1.9 %; mismatch allotments added | — | D60; C1 §2.11 |

**K_P / K_N and the replica.** Each cascode gate comes from a diode-connected copy of one cascode finger, run at K times its current density. The main device then sees $V_{DS} = V_{GS}(KJ) - V_{GS}(J)$, which scales with overdrive and tracks Vdsat over PVT and boost (C1 §1.2).

The replica (D58/D59) makes the diode current a copy of the actual folded-branch current, $(2I_\mathrm{SINK} - I_\mathrm{TAIL})/8$. A fixed current would break the tracking when the mirrors err. Results:
- K_P tracking under ibn × 1.05 was −0.34 % to −0.64 % (WO-26).
- The broken copy `kp_fixed + ibn105` gave −7.24 %, REJECT (WO-26).

The boost step of the vbpc leg is a gate-path bank switch, ×1.4 / ×1.75 rather than ×2, because K_P differs per mode (CL-8).

### III.1.5 CMFB evolution

| Stage | Design | Result | Decision |
|---|---|---|---|
| a | passive SC CMFB: Cc 0.1 pF, Cr 25 fF, onto m_plc (25 % of I_LOAD) | V_OCM 30.8 mV systematic at ff/125 base against a ≈ 38 mV bound; f_cm ≈ 8 MHz against the 9.4 MHz tb9 proxy | WO-26; D60 |
| b | add a CT CM error amp (A_cm ≈ 3–4) | A_cm 2.74–3.14 within 4/8 µA: V_OCM \|err\| + 3σ 63.3 / 20.7 mV against 10 mV; reaching it needed ≳ 150 MHz amp GBW | WO-27; D61 |
| c | **dual path** (C1 §1.3b): fast passive SC path + slow 5T gm-C integrator from `ctl` into `bli` (m_ia W 5 L 14, m_il W 6 L 16, tail 1 m_n finger, C_INT 2 pF); amp removed (−3.85 / −7.66 µA), +0.78 / 1.56 µA | op/AC 9 PVT: V_OCM sys + 3σ ≤ 7.84 mV, CM PM ≥ 78°, peaking ≤ 0.40 dB; boost f_cm 4.71–6.97 MHz < 9.4 at every corner | WO-28 run 2; D61 |
| d | tb9 transient (CM events): first results looked like a +129…+167 mV CM offset | **testbench bug**: Cint wired outp → inp gave positive differential feedback, latching the outputs (V_diff 3.107 V). Fixed; broken copy `TB9_POL_OLD=1` REJECTs | WO-29 item 2 |
| e | D62 (f_cm ≥ 9.4 → info, tb9 authoritative), corrected by D63: tb9 limits judged at the **sampling instants** (end of each half-phase) plus a CM-to-DM row; gate B is the final arbiter | on the fixed bench: events 1.8–5.9 mV, static ph2 1.3–2.3 mV, CM-to-DM 0.006–0.024 µV vs 0.256 µV; start-up with the 2 T clamp failed (sulo 14–34 mV) | WO-30; D62, D63 |
| f | D64: **Cr 25 → 50 fF** per side. The Cc charge error decays only through the Cr refresh (factor Cc/(Cc + Cr) per cycle: 0.79 → 0.67, τ ≈ 1.1 → 0.6 µs at 4 MHz) | op/AC 9 PVT ACCEPT (min CM PM 65.9°); tb9 ACCEPT at 4 corners (start-up 6.9–9.6 mV); broken copy mcr05 (old Cr) 34.0 mV → REJECT | WO-31; D64 |
| g | D65: output start-up clamp → **transmission gate** (n W 2 / p W 4, L 0.5; 0 µA); start-up row = ph2 instants within 10 mV of steady state by 4 µs | tb9 ACCEPT; start-up 0.03–0.21 mV; but broken copies mio, mcr05, mclw **passed**: the relative-only row was blind | WO-32; D65 |
| h | D68: add the absolute term \|steady state − V_OCM\| ≤ 10 mV; D69: "clamp never released" and "clamp stuck on" judged on a new DM diff-step row in the event deck | mio REJECTED (119.2 mV off); mcnr / mcst REJECTED (DM step 84.7 of 486 mV); healthy copies 0.039–0.053 mV (≈ 200× margin) | WO-36, WO-39; D68, D69 |

**The CM-to-DM bound (D65 M2; C1 §2.12).** An error $d_k$ (V differential) on $x_1$ at the instant Cs2 samples it enters the estimate as $d_k/(c_1V_\mathrm{REF})$. Split $d_k = a + b\,x_{1,k} + r_k(u)$:
- The constant $a$ cancels in endpoint INL and in the chop.
- $b\,x_1$ is a finite-gain-like leak, covered by the table gate.
- The worst-case remainder gives INL $= r/(2c_1V_\mathrm{REF})$. Allotting 0.1 × the 5 ppm boost share gives $|r| \le 0.256$ µV.

On a 3σ mismatch copy (Cs, Cint, Cc, Cr and input-pair ΔVT), the u-dependent part was 0.012 / 0.031 µV, an 8–21× margin. The broken copy `masy` gave 0.549 µV, REJECT (WO-32).

### III.1.6 Mismatch allotments, reference area and the SR floor

The HV MC has no Vth term (I.11), so every mirror-dependent row carries a hand-Pelgrom 3σ (C1 §2.11; D60). WO-27 found σ(I_tail) 3.43 % base / 2.42 % boost at A_VT 12, which failed SR − 3σ and ceiling + 3σ (WO-27). D61 grew the reference area at the same current density: the tail unit went from 1.25/2 to 3.75/6 (×9 area). The hand estimate was σ ÷ 3 (WO-28).

On the WO-28 netlist (WO-28 run 2):
- SR − 3σ was ≥ 12.76 / 25.83 V/µs.
- The ceiling held (I_tail + 3σ ≤ 19.67 / 38.81 µA against 1.08 × design).

**Knee-based floor (D65, CL-9).** 12.5 V/µs was 1.22 × the knee. Together with the ceiling, it left the C6 reference a window of only about −2 % / +1.6 %, against ±10–20 % untrimmed (REVIEW-C1b-final M1). The floor is now SR − 3σ ≥ 10.3 V/µs base and ≥ 20.6 V/µs boost; 12.5 / 25 V/µs stay as the design point. On the WO-32 netlist:
- SR − 3σ was 12.76–13.22 base and 25.83–26.55 boost.
- The C6 window (info) allows I_REF_btp to drop 19.3–22.4 % but rise only +1.58 % at ff/125 base (WO-32).
- That window drove the calibration rule "lowest passing code + 2" (D73; III.5).

**Near-knee broken copy (WO-32).** `srknee`, all six bias ports × 0.624 (16.5 V/µs at 1.4 pF, 0.8 × the boost floor), gave gate B 17.37 ppm > 5, REJECT. So the floor sits where the loop actually breaks.

### III.1.7 Noise work (WO-41 → D71 → WO-43 → D75 → WO-52)

| Step | Finding | Source |
|---|---|---|
| WO-41 tb7 (9 PVT × 2 modes) | thermal at vg 160–241.5 µV against 250 (fs/125 base, 3.4 % margin); sinks 53.8 % of thermal power; 1/f corner 17–61 kHz; chopper residue 0.20 mV constant / 0.25 µV signal-dependent (≤ 1 mV / ≤ 1 µV); VERDICT REJECT from tool and hand-row issues, not the thermal gate | WO-41 |
| D71 | the direct tier-0 path counts (I.10); reduce sink gm/I for ≥ 20 % margin (200 µV design target); the broken copy becomes sink noise × 2; recalibrate the hand γ | D71 |
| WO-43 sweep | no candidate reached 200 µV. Worst thermal: c0 baseline 257, **c1 L 8: 242 (boost span 1.43 V kept)**, c2 240, c3 RS 2.5 kΩ 221, c4 224; c2–c4 cut the boost span to 1.265–1.29 V (< 1.40). Measured γ: pfet_01v8 0.58, nfet_g5v0d10v5 1.31 (the 2/3 hand value explains most of the WO-41 hand-row gap) | WO-43; RESUME 2026-11-13 |
| D75 / CL-31 | take sink L 8; drop the 200 µV target; row v_vg ≤ 390 µV (I.10); system direct path 0.75–0.92 µV against 2.5 | D75; CL-31 |
| WO-52 | sink L 4 → 8 (W 72 kept; m_nr / m_rn / m_it derive from it, 0 µA); tb7 op fix (noiseless 1 GΩ instead of 1 MH inductors; op and noise decks split; fallback accepted only if gm matches the op within 0.1 %); gate B reruns done (III.1.8) | WO-52; RESUME 2026-11-13 |
| WO-61 | the WO-52 tb7 and op/AC jobs held **no data**: the scripts passed a relative output dir while ngspice ran in another cwd, so every tb7 value was NaN and op/AC found no `ac.csv`. Fixed with absolute paths. Gate B and tb9 were not affected | WO-52 README (WO-61 update) |
| WO-77 | the rerun then failed every tb7 row on the `noise op != op` lint: the `.noise` deck repeated the op from scratch and fell back to a transient op 0.6 % off in gm_in. Fix: the converged `op` node voltages become the noise deck's `.nodeset`; the 0.1 % match tolerance is kept. The mrg/msink copies looked blind only because the same lint invalidated their op. op/AC mutants now run one deck each (a merged deck fell to transient op). Rerun **PENDING**; jobs 3–5 timed out under the 2026-11-14 overload | WO-77; RESUME 2026-11-14 18:45 |

### III.1.8 Gate B history (in-loop, transistor OTA1, boost, N 1024, 4 MHz)

| Netlist | fs/125 | ss/−40 | ss/125 | tt/27 | Broken copy | Source |
|---|---|---|---|---|---|---|
| WO-24 | 2.29 ppm (6 parts) | — | — | — | — | WO-25 item 0 |
| WO-26 (D59) | 3.314 (at the 3.33 share) | 0.797 | 1.686 | 0.454 | sr95: 43,600–54,600 ppm (combine INVALID: endpoint memory → combine rule fixed in WO-29) | WO-26 |
| WO-31 (D59–D64) | **2.170** | 1.291 | 1.337 | 0.452 | sr95 fs/125 51,956, sf/−40 50,231: REJECTED | WO-31 |
| WO-32 (TG clamp) | 2.171 | — | — | — | srknee 17.37: REJECTED | WO-32 |
| WO-52 (sink L 8) | **3.14** (under the 3.33 share) | 0.71 | — | — | — | RESUME 2026-11-14 (WO-52 reruns) |

Every recorded boost gate B run passes the 5 ppm gate, but coverage on the current netlist is partial. On the WO-52 netlist (sink L 8) only fs/125 (3.14 ppm) and ss/−40 (0.71 ppm) were run, both at solver level O1; the tt/27 and ss/125 values exist only on older netlists (WO-31). Sink L 8 raised fs/125 from 2.17 to 3.14 ppm (RESUME 2026-11-14). D43c applies the O1/O2 ladder to every gated INL with less than 3× margin, i.e. INL above gate/3 = 1.667 ppm in boost. 3.14 ppm is therefore owed an O2 run at fs/125, which is not scheduled (V.2). WO-31 skipped O2 at 2.17 ppm on a "below gate/2" argument, which fell below the D43c standard.

### III.1.8a Precision gate B at 2 MHz (WO-63, WO-76)

The 2 MHz precision gate B (≤ 1.333 ppm; D48(1), SPEC row 94) had never been run before WO-63. Setup (WO-63): the WO-52 transistor OTA1 (sink L 8) in the tier-1 deck, OTA2 behavioural at its precision point (13.5 V/µs, GBW 10 MHz, β2 0.497), fs 2 MHz, boost 0, N 1024, 21 points in 6 parts, solver level O1. The convergence rule is D43c: every gated INL with less than 3× margin (here INL above gate/3 = 0.444 ppm) needs the O0→O1→O2 ladder, and an O1/O2 pair is accepted only if |O2 − O1| ≤ max(10 % · INL, 0.1 · (gate − INL)), with the verdict taken on INL(O2) · (1 + |Δ|/INL). WO-63 applied a "gate/2" trigger instead; that trigger is not in D48 or SPEC and is weaker than D43c. The broken copy `srknee` scales all six bias ports by 0.6234, i.e. a base SR of 0.8 × the 10.3 V/µs floor.

| Corner | O1 combined INL (ppm) | Verdict | Note | Source |
|---|---|---|---|---|
| tt/27/3.3 | 0.692 | ACCEPT at O1 | above gate/3: O2 needed under D43c, not yet scheduled | WO-63 |
| ss/−40/3.0 | **1.706** | **REJECT at O1** | jagged, pattern-dependent residual; O2 PENDING | WO-63; WO-76 |
| ss/125/3.0 | 0.698 | ACCEPT at O1 | above gate/3: O2 needed under D43c, not yet scheduled | WO-63 |
| fs/125/3.0 | 0.967 | ACCEPT | O2 PENDING (WO-76) | WO-63 |
| fs/125 `srknee` (must REJECT) | 1.375 | REJECTED | only 3 % over the gate; only part 0 rejects on its own | WO-63 |

**Diagnosis so far (WO-76).** Every combine is healthy (endpoint spread ≤ 0.017 ppm). The residual shapes differ:
- tt/27, ss/125 and fs/125 show a smooth odd "S", the signature of a GBW/settling nonlinearity, plus ≤ 0.3 ppm of jitter.
- ss/−40 is jagged: neighbouring points jump by up to 1.3 ppm, which points to a step-history (bit-pattern) dependent error, not a static A(v) (WO-76 §1).
- Static gain is ruled out (A0 is highest at ss/−40, 85.9 dB) and so is the CMFB (best f_cm and PM_cm at ss/−40). Slew alone is judged unlikely, not ruled out: SR is 13.2–13.5 V/µs at every corner, yet only ss/−40 fails (WO-76 §3). The first hypothesis was integrate-phase phase margin: 49.9° at ss/−40, fp2/GBW 1.02, the lowest of all corners (WO-76 §3).

**Bias sweep: the error moves, it is not fixed.** Per-part O1 INL at ss/−40 with all OTA1 bias ports scaled. These are unfiled interim data: diagnostic decks only, taken from the coordinator note of 2026-11-15 and RESUME 2026-11-14 22:55 and 23:40, not from `results/wo76/README.md`:

| Part | nominal | bias × 0.8 | bias × 1.3 |
|---|---|---|---|
| p0 | 1.330 | **1.830** | — |
| p1 | 1.263 | 1.349 | — |
| p2 | 1.706 | 1.281 | 1.494 |
| p3 | 0.368 | 0.114 | — |
| p4 | 1.671 | 1.226 | 1.421 |
| p5 | 1.259 | 1.302 | — |

Both directions lower p2 and p4, but × 0.8 raises p0 from 1.330 to 1.830 ppm. The coordinator's reading: the error shifts between parts, which points away from a simple PM or SR cause and toward a pattern-dependent term, possibly numerical at O1; bias options are not supported by these data (RESUME 2026-11-14 23:40).

**O2 parts.** At ss/−40, O2 gives p0 **0.142 ppm** (O1 1.330) and p2 **0.160 ppm** (O1 1.706) (RESUME 2026-11-15 00:45 and 01:40; coordinator note 2026-11-15; unfiled interim data). That is a strong sign that the ss/−40 O1 failure is a numerical artefact of the O1 solver settings, but it is not yet a converged result:
- D43c accepts an O1/O2 pair only if |O2 − O1| ≤ max(10 % · INL, 0.1 · (gate − INL)). A step from 1.706 to 0.160 ppm (≈ 10×) fails that test, and the D43c verdict formula INL(O2) · (1 + |Δ|/INL) gives ≈ 1.7 ppm.
- WO-76 §2's own rule (`--tight` against O2, same test) is unmet: the `--tight` O2 deck (reltol 1e-6, vntol 1e-8) aborted with "timestep too small", past the solver floor, and the O1 `--tight` deck timed out.
- The ladder never tightens vntol (1e-6 V ≈ 0.25 ppm of the span), and the O2 values of 0.14–0.16 ppm sit below that.
- Counter-evidence for the O1 values being well formed: the O1 endpoints agree to 0.005 ppm across parts.

O2 becomes the result only if a further tightening confirms it (D43c; WO-76 §2). No amendment to D43c is made; a third solver point is to be scheduled, and until then the C1 precision verdict stays **PENDING**. The other O2 parts and the fs/125 O2 parts are still running (`WO-76-f00f9bf/out/logs_o2`). The same solver uncertainty applies to every O1-only INL in this book: boost gate B, precision tt/27, ss/125 and fs/125, and the earlier s5 rows.

**Gate rule gap.** tt/27 (0.692) and ss/125 (0.698) are above gate/3 (0.444 ppm), so D43c asks for O2 there; those runs are not in the WO-76 job list (WO-63). Listed in V.2.

**Gate B mechanics.**
- N 1024, 21 input points, split into 6 parts. Convergence follows D43c; the precision verdict is **PENDING** (above).
- `combine()` asserts a complete part set, the same endpoints in every part, and $\hat u$ agreement ≤ 0.05 ppm at shared points. The gate value is the max per-part endpoint INL (WO-25).
- Broken-copy rule (WO-29): when every part is healthy and above the gate, the copy reports REJECTED even if its endpoints disagree. A slew-limited copy carries memory between conversions, so its endpoints are sequence-dependent.

### III.1.9 Current sizes (file of record `design/c1_ota1/sizes_draft.py`)

| Device / element | Value | Decision / source |
|---|---|---|
| m_in input pair | pfet_01v8 120/0.5 (12 × 10), bulk = tail | D54 |
| m_t tail | I_TAIL 18.5 µA base, ×2 boost; unit finger 3.75/6 | C1 §2.1; WO-28 |
| m_n fold sinks | 72 µm, unit L 8; I_SINK = 1.35·I_TAIL | D75; C1 §1.5 |
| m_nc / m_pc cascodes | 20/2 / 80/2 | C1 §1.1 |
| m_pl load (fixed 75 %) | 80/4 (32 × 2.5/4) | C1 §1.1 |
| m_plc CMFB section (25 %) | 15/2 as 8 × 1.875/2 | D58, D59 |
| m_pp protection cascode | 10/0.5, gate = 0 V | rev B M3 |
| References | parallel unit fingers, 1:8 | D59 |
| Cascode bias | K_P 12.5 base / 7.14 boost; K_N 8; replica-fed | D59; CL-8 |
| CMFB | Cc 0.1 pF, Cr 50 fF per side; dual path C_INT 2 pF | D58, D61, D64 |
| Output start-up clamp | TG n 2 / p 4, L 0.5 | D65 |
| Input chopper / island | nfet_g5v0d10v5 4/0.5 and 2/0.5, closed by default | CL-5 |
| Fold-node chopper | nfet_01v8 4/0.15 | C1 §1.4 |
| C_FOLD_EXTRA | 0 pF (gate B decides) | D56 |
| Current, netlist I_vdd | base 60.1–61.6 µA, boost 121.8–123.9 µA (WO-28 run 2) | WO-28 |

### III.1.10 Open items for C1

- Precision gate B verdict: the 6-part O2 combine at ss/−40, the fs/125 O2 parts, and a further solver point to confirm O2 under D43c. **PENDING** (WO-76).
- O2 runs at tt/27 and ss/125, which D43c asks for (O1 above gate/3 = 0.444 ppm). No WO yet.
- Boost gate B on the WO-52 netlist: O2 at fs/125 (3.14 ppm is above gate/3 = 1.667 ppm), and tt/27 and ss/125 on this netlist. No WO yet.
- A stronger precision broken copy: `srknee` rejects by only 3 % (WO-63; WO-76 §4).
- tb7 noise on the sink-L 8 netlist and the op/AC mutants. **PENDING** (WO-77 rerun).
- MC of the 1:8 ratios and the replica is open (C1 §1.1 layout intent).
- tb8 offset MC, tb8b 3.3 V mirror MC, tb10 device stress, tb12 boost toggle and tb13 vg switches are in the C1b plan (C1 §4). Their results are not in the result files read here.
- PEX re-simulation (C7/C10) is not started.

## III.2 C2: OTA2 (not started)

C2 has no design note yet. Inputs gathered so far:

| Input | Value | Source |
|---|---|---|
| Spec rows | base loaded GBW ≥ 10 MHz into ≈ 0.7 pF (15 MHz target), SR ≥ 13.5 V/µs; boost GBW ≥ 22.5 MHz, SR ≥ 27 V/µs; β2 ≥ 0.497 (Cp_vg2 ≤ 0.262 pF per side); worst loop step ≈ 1.12 V diff | SPEC OTA2 row; D41 |
| Realistic x2 peak | ≈ 1.41 V diff for any comparator offset 0 < \|Vos\| ≤ 90 mV (not 1.21 V), at the edge of the 1.4 V A ≥ 75 dB range | C3 §3.1b; WO-51 |
| Comparator CM kickback | 38.96–47.41 mV per fire edge on x2 on rev f (38.92–46.82 mV with kp2); OTA2 output headroom must absorb it | C3 §3.4, §3.4b; WO-86 |
| Order-1 duty | per-cycle reset of Cint2 (`rst2_o1`), gated by the comparator's decision-done signal, ≥ 15 ns; x2 = (Cs2/Cint2)·x1 = c2·x1 follower | C4 §2; D76 |
| Offset | ≤ 9 mV 3σ; 52.7 µV input-referred at N 4096 without sys chop (cancels with it) | SPEC OTA offset row |
| Leak / Cs2 interface | Cs2 plates shorted in OTA2 integrate; CM kick ≤ 10 mV | CL-2 |

## III.3 C3: comparator (rev a → f; rev g pending)

**Purpose and interface.**
- Decides the sign of $x_2$ once per fs cycle.
- Its output `q`/`qb` (1.8 V) goes to the C9 DAC flop, captured on `fs_tick` (D74).
- The input is always $x_2$ (D74).
- The strobe φC fires inside φS, derived by C4 from the φSe rising edge (C3 §2).

**Topology choice (C3 §1).**

| Option | Verdict |
|---|---|
| **A: NMOS-input StrongARM on VDPWR, HV input pair, no static preamp** | chosen (D74): output in the 1.8 V domain, so no level shifter in the bit path; ≈ 0.7 µA dynamic, outside the 200 µA analog budget; HV gates survive x2 at VAPWR; the HV pair is an accepted exception to D40(a) |
| B: all-HV StrongARM on VAPWR | down- and up-shifters, slower, current counts against 200 µA |
| C: 1.8 V input pair | the gate sees x2 up to VAPWR, violating D40 (broken copy `in18`) |
| static preamp | 10–30 µA against the 189/200 µA worst case |

**Revision history.**

| Rev | WO | Change | Result |
|---|---|---|---|
| a | WO-44 | set A spot sims, PDK MC probe | t_dec 0.35 (tt)–1.39 ns (ss/−40) vs 33.75; diff kickback ≤ 0.73 / 1.86 mV; CM kick 32–49 mV; 0.50–0.76 µA; HV nfet σ(Vgs) 5.87 mV (A_VT ≈ 9.29 eq., toxe only); **brk_starve passed** (6.4 ns): decision-time row blind |
| — | REVIEW-C3a → D74 | strobe in φS + capture on fs_tick (removes one cycle of loop delay); A_VT 12 total (inject 7.6 mV·µm on tt_mm); set A′ (pair ×4, latch 4/0.5); 1.8 V tail; order 1 via int2 follower | D74 |
| b | WO-48 | netlist + full tb (47 decks): T1/T2/T7/T10/T10nz/T5 ACCEPT at 9 PVT, every broken copy REJECTs | **fails:** T3 offset σ 14.4 mV, \|μ\| + 3σ 44.8 mV against 20 (hand 17.7); T8 stress dp 2.36–2.44 V > 1.98 V; T5 asymmetric kick 7.7–8.2 mV > 5 |
| c | WO-51 | offset row re-based (D75, CL-30); HV cascode K1/K2 for T8; T5 gate at R ±5 % / C ±1 % | offset ACCEPT (44.8 / 45.0 mV ≤ 60); **cascode broke function**: T2/T7/T10 REJECT at every corner (decision memory) and T8 moved to the tail (2.38–2.55 V) |
| d | WO-56, WO-65 | HV PMOS precharge of the cascode nodes ap/an (gate = strobe) + HV tail (5/0.5 ×4) | function restored; under the D80 split the junctions pass (2.38–2.39 V vs 4.95 V), but the oxide class still fails: SR-latch Sq3/Sb3 Vds 2.32–2.33 V (also present in rev b/c, hidden under the junction number); T5 has no physical copy that REJECTs → D81 |
| e | WO-68 | latch clamp NMOS `S{q,b}5` 0.42/0.15 from each NAND stack node to vss, gate on the complement of that NAND's set input | the stack node sq/sb had floated to −0.345 V for 105 ns on every latch flip; with the clamp, Sq3/Sb3 Vds 2.32 → 2.047 V for ≤ 0.65 ns. The remaining fails are edge overshoots of 2.02–2.06 V on 1.8 V nodes → D83 |
| — | WO-78 | T8 checker per D83 (sustained S over 1 ns windows, peak P ≤ 2.2 V, duration D < 1 ns) | rev e still REJECTs: op/on sit ≈ 66 mV above VDPWR for a whole strobe phase (S 2.046 V for 126 ns) because nothing drives them while the pair is off: a real design issue → D87 |
| f | WO-81, WO-84, WO-86 | op/on keeper `KPo/KPn` pfet_01v8 0.42/0.15, gate on the first buffer inverter of the same node; D87 bench basis | S 2.046 → 1.980344 V; P 2.224 V (tt/27), 2.251 V (ff/−40); T2/T3/T5 pass (below). T8 still REJECTs on sus, cap and dur → D90 |
| g | WO-88 | candidates: slower op/on precharge (R0/R1 0.5/0.15, 1.0/0.3, 1.0/0.5, each with the 2× keeper kp2); kp3 as info | **PENDING** (WO-88 pool A) |

**Offset limit from loop impact (D75, CL-30).** Model `offset_loop.py`, ±0.9 FS, 4001 points (C3 §3.1b):

| Vos (mV) | 0 | ±15 | ±45 | 90 | 135 | 200 |
|---|---|---|---|---|---|---|
| peak \|x2\| diff, N 1024, ideal (V) | 1.237 | 1.408 | 1.408 | 1.408 | 1.435 | 1.664 |

- The x2 peak is flat to 90 mV. The limit is 2/3 of that: $|\mu| + 3\sigma \le 60$ mV, with every MC sample ≤ 60 mV.
- The chop residue is ≤ 0.74 ppm at N 1024 and ≤ 0.055 ppm at N 4096 for any Vos ≤ 200 mV, under the 1 ppm share.
- The gating broken copy is pair A_VT × 6. ×3 (≈ 62 mV) sits at the limit and is kept as information.

**The rev c memory fault (C3 §4b; WO-56).** The cascode nodes ap/an had no precharge. They charged only through K1/K2 toward VDPWR − VT,HV, ending in subthreshold. After a ±0.3 V decision, one node was left low, and the next strobe favoured the previous decision. The small cycles that followed read the wrong sign, which showed up as t_dec ≈ 500 / 250 ns. Rev d precharges ap/an and makes the tail HV, so tl, ap and an touch only HV devices.

**The 1.8 V stress rule and the T8 bench (D80, D83, D87, D90).** The T8 row checks that no 1.8 V device in the comparator sees more than its rating. The row was refined four times, each by a user decision, because the original wording was stricter than the physics (STATE-2026-11-14 §2, lesson 4). All of these limits (1.98 V sustained, 2.2 V for < 1 ns, the 4.95 V junction limit, and the rev d source-to-bulk 2.37–2.39 V) are **project stress rules (D80, D83, D90), not PDK ratings**. The SkyWater device-details page gives a model-validity range of 0–1.95 V for Vds and Vgs of nfet/pfet_01v8 and +0.3 to −1.95 V for nfet Vbs (https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html); the project limits lie outside that range, so passing them does not show operation within the models' validated range.

| Step | Rule | Why | Source |
|---|---|---|---|
| D80 / CL-33 | oxide pairs (Vgs, Vgd, Vgb) and Vds ≤ 1.98 V; junction reverse bias ≤ 4.95 V (PDK `_05v5` diode rating 5.5 V − 10 %) | rev d's 2.38 V was source-to-bulk on a reverse-biased junction, with no oxide stress | D80; WO-65 |
| D83 / CL-35 | 1.98 V applies **sustained** (> ~1 ns); short switching overshoot allowed up to 2.2 V for < 1 ns; a checker copy must prove the rule is live | after the rev e clamp, the remaining fails were 2.02–2.06 V edges lasting < 1 ns against a limit equal to the maximum supply | D83; WO-68 |
| D87 | stress judged against an ideal 1.98 V pin (the bench's 10 Ω feed drop is not device stress); strobe overshoot judged on C4's real phiC edge per corner (0.1 ns ideal edge → info); x2 stimulus bounded by OTA2's range plus margin (0.3–2.7 V per side; the −0.5 V step → info); rev f keeper | the WO-78 numbers mixed a real fault (op/on at 2.046 V) with bench artefacts (supply rise to 1.98194 V, 0.1 ns edge, −0.5 V x2 step) | D87; WO-78; WO-81 |
| D90 / CL-39 | sustained level judged ≤ 1.981 V (1 mV numerical/leakage tolerance), also the threshold of the duration limb; checker copy at 1.985 V must REJECT | on a stiff pin, op/on sit a fixed +0.344 mV above the pin | D90; WO-86; WO-88 |

**The stiff switched supply basis (WO-84, WO-86).** An ideal source tied straight onto vdd aborts at the start of the power-up ramp ("timestep too small"), the same mechanism as the C4 bench aborts (III.4). WO-84 therefore uses a 10 Ω feed for the ramp only, then closes a 1 mΩ switch in parallel 100 ns after the ramp ends; vdd then never exceeds its source (vddmax 1.98000 V). The coordinator adopted this as the D87(a) basis (wo/INDEX). On it, rev f gives S = 1.980344 V on op/on, P 2.2240 V and D 144.3 ns (WO-84).

**The +0.344 mV result (WO-86).** S stays at 1.980344 V to the µV with a 10× stiffer switch, with reltol 1e-6 and with a fixed 0.01 Ω feed. A 2.00 V pin gives 2.000343 V. So the excess is a fixed +0.344 mV above whatever the pin is, not a bench drop and not solver noise. Doubling the keeper (kp2) cuts it to 0.150 mV (× 0.44), which behaves like a steady injection of tens of nA into a supply-held node through the pull-up resistance. The injecting device is not named yet: the WO-86 probe failed on vector names, and WO-88 fixed the probe (save `[id]` only) and re-launched it (**PENDING**). The candidate is the HV nodes ap/an, kicked to 2.29–2.39 V by x2, leaking through K1/K2 into dp/dn and M3/M4 (WO-84, inference). nb2/ob2 sit above vdd by less (≈ 10 µV), but D counted any excess > 1.98 V, hence 144 ns. Because the stress equals the supply itself plus 0.3 mV, the user set the 1 mV tolerance (D90). Under D90 the sustained limb and the duration threshold move to 1.981 V; the re-judged rows are **PENDING** (WO-88).

**The precharge-edge cap (WO-86, WO-88).** The peak P is on M4 gb, node op, at the strobe **falling** (precharge) edge. The losing node (on) is pulled from 0 to vdd by R1 in about 0.2 ns. Through the Cgd of M5 and M3 (gate on, drain op), that edge couples the held-high op upward. R0 (pfet_01v8 1.0/0.15, drain op, gate clk, source vdd; size RSO in `sizes_draft.py`) also restores op during precharge and is 2.4× wider than the keeper. R0 and R1 share the clk gate, so while R1 pulls on up, R0 is still turning on, and the already-on keeper is the main return path for op during the edge; once R0 is fully on, it restores op too (`netlist.py`; WO-88 item 3). That explains why kp2 lowers P. It also means a narrower R0/R1 slows the aggressor but weakens op's restore path, so the net effect of the rev g candidates is not obvious. This mechanism is an interim reading (WO-88); the probe that would confirm it is **PENDING**.

| Variant | P tt/27 | P ff/−40 | Against 2.2 V | Source |
|---|---|---|---|---|
| rev f | 2.2240 V | 2.2511 V | fails | WO-86 |
| rev f + kp2 (KPo/KPn 0.84/0.15) | 2.1792 V | **2.2062 V** | fails by 6 mV at ff/−40 | WO-86 |
| rev g candidates (slower R0/R1 precharge: 0.5/0.15, 1.0/0.3, 1.0/0.5, each with kp2; kp3 info) | — | — | **PENDING** (WO-88) | WO-88 |

Narrower R0/R1 also halves their Cgd overlap, which should reduce the strobe-rise kick on op/on; longer L lowers mismatch but adds channel charge; the precharge time has ≈ 100 ns of margin (WO-88).

**Rev f against rev e on the other rows (WO-86).**

| Row | rev e | rev f | rev f + kp2 |
|---|---|---|---|
| T3 MC tt, \|μ\| + 3σ (σ) | 49.59 mV (16.32) | 45.07 mV (14.81), n 200 | not run |
| T3 MC ss/−40, \|μ\| + 3σ (σ) | 49.26 mV (15.17) | 42.74 mV (14.21), n 50 | not run |
| T2 one_ss-40_162 t_dec | 2.035 ns | 1.354 ns | 1.291 ns |
| T5 diff kick, ss/−40 / worst (fs/125) | — / 1.82 mV | 0.617 / 2.524 mV | 1.142 / 3.399 mV (limit 5 mV) |
| T5 CM kick, all one_ corners | 40.1–48.1 mV | 38.96–47.41 mV | 38.92–46.82 mV |

The T3 rows are flagged only on the `plaus` limb (sensitivity decks not in the pool), as in earlier pools; the count and |μ| + 3σ limbs pass. The rev f cyc rows were never run in WO-81; they are in the WO-88 pool (**PENDING**). The T2 gain from rev e to rev f is not explained, because the D87 x2 stimulus changed between the two runs (WO-86).

**T5 under D81.** The worst differential kick is 2.7 mV even with the cascode and precharge removed (WO-65: nohvc 2.67 mV), so no realistic physical copy can fail the 5 mV row. D81 accepts margin by construction; checker copies judge real data at tight limits (`one_chk_kick1` at 1 mV, `one_chk_rec02` at 0.2 mV recovery) and REJECT (WO-68; WO-86). The CM kick stays a reported number for C2.

**Sizes, rev f (C3 §5; WO-68; WO-81).**

| Device | Size |
|---|---|
| M1/M2 input pair | nfet_g5v0d10v5 5/0.5 × 4 |
| Tail T | HV 5/0.5 × 4 |
| K1/K2 cascode | HV 5/0.5 × 4, gate VDPWR |
| P1/P2 precharge | HV PMOS 2/0.5 |
| Latch | 01v8 4/0.5 |
| Latch stack clamps Sq5/Sb5 (rev e) | NMOS 0.42/0.15 |
| op/on keepers KPo/KPn (rev f) | pfet_01v8 0.42/0.15 (kp2 candidate 0.84/0.15) |
| Output buffer | drives 100 fF routed |

**Testbench rows (C3 §6).** Each row has its own broken copy:

| Row | Checks | Broken copy |
|---|---|---|
| T1 | polarity | `qswap` |
| T2 | decision time < 0.3·t_half | weak strobe |
| T2band | t_dec within [0.5, 3] × 1.12 ns | `starve` |
| T3 | MC offset | A_VT × 6 |
| T5 | kickback | C_X2/10 |
| T7 | memory | `nobuf` |
| T8 | stress, both power-up orders, OTA2-slew stimulus | `in18` |
| T10 / T10nz | capture window, near-zero inputs | wrong-phase strobe, `nolatch` |

Numerical rules: gear, reltol 1e-5, tmax 1 ps.

**Open items (C3 §8; WO-86; WO-88).**
- Rev g: pick a precharge-edge candidate from the WO-88 sweep, then the full T2/T3/T5/T8 set. **PENDING.**
- Name the device that injects into op/on (WO-88 probe `runI`). **PENDING.**
- T8 re-judged at 1.981 V (D90); T3 MC on the final revision; the rev f cyc rows. **PENDING** (WO-88 and after).
- Reviewer pass on the final revision.
- Kickback fixes are listed, not applied: halve the pair, or add a neutralisation pair.
- Layout: routed q load (100 fF assumed) and common-centroid HV pair.

## III.4 C4: switches, phase generator and level shifters (rev a → b)

**Purpose.** All signal switches, the D12 top-plate shorts, the DAC switches, the non-overlap phase generator with early/late phases, comparator strobe placement, OTA-chop edge placement (rule 13) and the C7 level shifters (C4 §1–§7). Phase naming: φI (integrate) is high when the C9 bit clock is high; φS (sample) when it is low (C4 §1).

**Switch list and sizing (C4 §2–§3, §9).**

| # | Switch | Type / size | Basis |
|---|---|---|---|
| 1 | input / sys-swap / short, merged | 3.3 V TG **12/36** | Ron_max 1247 Ω at ss/−40/3.0 against ≤ 1.5 kΩ (10/30 = 1490 Ω, 0.7 % margin; 8/24 fails at 1784 Ω) |
| 2, 10 | DAC VREF+ / Ck2 DAC | 3.3 V TG ≈ 6/18 (4/12 read 3.6 kΩ) | τ_ref ≤ 10 ns behind 500 Ω + 5 pF |
| 2 | DAC VREF− | NMOS 4/0.5 | VREF− ≈ 0 V |
| 3, 8 | D12 top-plate shorts | TG ≤ 2/4 | injection rule (I.6.5), not settling |
| 4, 9 | vg connect | NMOS only, W 5 / L 0.5 (D76) | PMOS useless at 1.2 V; leakage row |
| 6, 7, 11 | Cs2 sample, Cs2 short (φIl), Ck2 rest short | TG | CL-2 |
| 12 | int2 reset, order-1 per-cycle reset | C2-owned, C4-driven | D74, D76 |

**Why a TG for the input.** VIN spans 0–2.25 V on a 3.0 V minimum supply, and an NMOS-only switch stops conducting above ≈ 1.8–2.0 V. The broken copy `nonly8` reads 2.2e11 Ω at 2.25 V (WO-46). A bootstrapped switch is not needed and stays rejected (D5).

**Input settling budget (SPEC "Input switches" row).** $(R_{on} + 500\,\Omega + R_{src})(5\,\mathrm{pF} + C_s) \le 18.75$ ns, with τ = 16.5 ns at the 1.5 kΩ cap (C4 §3).

**Phase generator (C4 §5).**
- **Domain.** The fs clock crosses to 3.3 V once, and all phases are generated in the VAPWR domain from hvl cells. Generating them at 1.8 V and shifting each one would put level-shifter delay mismatch into the dead time.
- **Structure.** Cross-coupled NANDs with delay chains. Feedback is taken from the **late** phase.
- **Spot results (WO-46).** Dead time 1.82 ns (thresholds, ff/−40) to 5.50 ns (50 %, ss/125), inside [1.0, 6.25] ns; t_half ≥ 118.1 ns; LS edges ≤ 0.25 ns; duty error ≤ 0.48 %. One fail: a phase edge of 1.22 ns at ss/125 against a 1 ns spot limit. The fix is inv_8 drivers. All 9 broken copies REJECT.

**Rev b (WO-54) changes after REVIEW-C4a and D76.**
- **Edge rate becomes information.** Edges matter only through dead time and injection order, both now measured at the switch thresholds: g at the 10 %/90 % points including gated nets and cross terms; eb ≥ 0 for early-before-late.
- **Gated controls.** pas / swp / sho are gated with the rule that C9 changes them only on the rising edge.
- **The y race** is covered by the gap.
- **Strobe placement row**, with broken copy `wrongstrobe`.
- **Order-1 reset** gated by the decision-done signal (`o1early` broken copy).
- **Power-up.** A VDPWR-present detector, `pwrok`, gates the generator and closes the islands.

**Rev b smoke findings (WO-54).**
- The PDK SPICE models of `lsbuflv2hv_clkiso_hlkg_3` (output stuck) and `lsbuflv2hv_isosrchvaon_1` (no devices on its rails) are unusable. D78 therefore isolates in logic with normal `lsbuflv2hv_1` cells.
- The Sg leakage share fails: 68 pA at ff/125 against a proposed 45 pA share of the 90 pA row. D78 re-splits the row using C1's measured share; the fallbacks are W 4 or a T-switch.
- Ron at tt/27 is inside every limit: sin 382 Ω, DAC 1.15 kΩ, VREF− 519 Ω, stp 3.45 kΩ, Sg 816 Ω.

**C4b gate rows** (C4 §11): ron, g_min, g50_max, t_half_min, eb_min, ls_edge_max, glitch_s, glitch_d, rule13, strobe, order1, injdm, injcm, settle, leak, rampa/rampb, and since D82 a `rating` row. Each has a broken copy.

**Bench root causes (WO-70, WO-79, WO-85).** No C4 run so far has produced a design verdict, because three bench problems hid it in turn. None is a design finding, and no tolerance or limit was changed to fix them:

| WO | Symptom | Root cause | Fix |
|---|---|---|---|
| WO-70 | ≈ 40 WO-54 jobs reported "incomplete or empty netlist" | ngspice's batch-mode follow-on message after a "timestep too small" abort; the error capture was case-sensitive and missed the real line. The inj integrators also started from an undefined DC point (13.2 V) | Ron/Roff 10 Ω / 1e12 on ideal switches, integrators held in reset until T0 − 5 ns, digital inputs through 100 Ω + 5 fF, gear on inj/settle/ramp, case-insensitive capture |
| WO-79 | 28 of 89 WO-70 jobs still aborted (inj at 20 ns on `vinn#branch`, settle, ramp) | an ideal source tied straight to pF of device capacitance: its branch current C·dV/dt is numerical noise at the 1e-22 s steps after a breakpoint and cannot meet abstol, so the step collapses; adding a source R moves the abort to the next ideal source on the node | `soften()`: a series R on every grounded independent source (10 Ω signals, 1 Ω vdd/vdl); `C4TB_TIGHT=1` copies show the results do not move with tighter tolerances |
| WO-85 | tim decks then aborted on HV body-junction nodes (`nfet_g5v0d10v5#dbody`) | the 1 Ω in series with an undecoupled vdd/vdl leaves only device capacitance on the supply node (sub-ps time constant); crowbar current moves it every edge. Gear does not help; ideal supplies run clean | tim decks keep ideal supplies (`supplies=False`), as in WO-70; tim therefore sees no supply bounce. A bond-R + decap supply model is an option for later |

**Leakage and D82.** WO-70 measured C1's own vg-node devices on the same node: 81.2 pA at ff/125, about 90 % of the 90 pA row, with Sg adding 68.5 pA, so ≈ 150 pA per node. Shrinking Sg (W 4) or a T-switch cannot close that. D82 / CL-34 derates instead: 0.25 MHz N 1024 is rated to ≤ 100 °C, and at 125 °C the 0.25 MHz mode is limited to N ≤ 256; faster modes are unaffected because drift scales with 1/fs. The new `rating` row checks drift = I_tot·N_rated/(0.25 MHz · 2.01 pF) ≤ 0.2 V, with broken copies `noderate` (N 1024 at 125 °C, expected ≈ 0.31 V) and `sgx6` (WO-79). Expected from the WO-70 numbers: ff/125 ≈ 0.076 V and ff/100 N 1024 0.048 V pass, but the **20 pA ff/100 row (N 4096) fails at 23.4 pA**. The two numbers do not contradict each other: 23.4 pA gives 0.19 V of drift, under the 0.2 V criterion, because at N 4096 with 2.01 pF the 0.2 V criterion allows about 24.5 pA. The 20 pA row therefore carries margin below the drift criterion; its origin is to be traced (Appendix E). That row is still open and goes to the user after the rerun confirms it (WO-79; wo/INDEX).

**Pools.** The non-tim rows run in `WO-79-139a29d/run/pool2` (relaunched under the global cap after the 2026-11-14 overload) and the tim rows in WO-85 (54 jobs; the WO-79 tim rows are void). Both are **PENDING**; WO-85 job 1 (tim ss/−40 2 MHz) timed out at 5400 s under the overload and must be rerun (RESUME 2026-11-14 18:05, 18:45).

**Phase edge used by C3.** WO-81 measured C4's phiC edge from the WO-70 tim waveforms for the C3 T8 bench (D87): 10–90 % rise 0.40–1.35 ns and fall 0.18–0.32 ns over five corners (WO-81).

**Level shifters (C7) (C4 §7).** Up-shifters (`lsbuflv2hv_1`): fs, y, swap, short, chop, rst, order, dec, plus the C6 static lines boost and trim. Down-shifters (`lsbufhv2lv_1`): chlp, chln and the comparator strobe φC.

## III.5 C6: bias reference (WO-45 → WO-87)

**Purpose.**
- A constant-current reference (D42) with a 3-bit trim.
- Distribution mirrors, with boost as one switched reference leg: one of two master-diode halves is switched out, which doubles every port ratio at once with zero added current (C6 §5; D43b).
- Start-up and a `bias_ok` flag.

Own current ≤ 6 µA; area ≤ 7,000 µm² (SPEC rows 102–104). OTA1 port currents (base): ibtp 2.357, ibn 3.122, ibp 1.475, ivbl0 0.492 µA, 7.45 µA in total, charged to the OTA budgets (C6 §1).

**Core (C6 §2).** Banba core with these elements:
- PMOS legs: 17 units of 0.42/20 each.
- Q1: 1 × pnp_05v5. Q2: 8 units, 3 × 3 common-centroid.
- Resistors: xhrpoly 2 kΩ/sq. R1 82 µm ≈ 258 kΩ, later 94 µm (WO-55), now **144.8 µm** (WO-64 tune, verified in WO-80); total resistor length 854 µm (WO-80).
- R2/R1: ≈ 4.6 by hand; 4.1988 from the WO-45 tune; **2.45** after the 2:1 amp skew of architecture (c), whose n·VT·ln 2 PTAT term moves the zero-TC ratio down (WO-64 estimate ≈ 2.2; tuned value 2.45) (WO-64 §1; WO-80).
- Two-stage amplifier: Cc 3 pF, Cvg 1 pF.

**Trim (C6 §3; D73).** $G_0 = 17$ plus binary legs of 1, 2 and 4 units; the reset code 100 is 21 units. Three linear bits cannot meet ±20 % range, ≤ 6 % step and ±3 % residual at once; they miss by 0.04 %. So the trim covers the process part, ±19 % ($I_7/I_0 \ge 1.3836$). The TC part cannot be trimmed at room temperature anyway (D73). Calibration rule: firmware uses the lowest passing code + 2, landing at ≈ 0.85–0.97 × nominal. That keeps ≥ 4.6 % margin under the +1.6 % OTA1 ceiling at ff/125 and stays above the SR knee with TC margin (D73; C6 §4).

**History.**

| WO | Design | Result | Source |
|---|---|---|---|
| WO-45 | Banba + proportional start-up (Ms driven by tsu, Mk 1:1) | DC, trim (step 5.04 %), TC (−2.4/+0.25 %) and PSRR (69–73 dB) OK; nosu, ptat, trim_open REJECT; **start-up fails**: transients settle at 13–48 % of the DC current, sf/27 DC at 0.106 µA | RESUME 2026-11-13; WO-45 smoke |
| WO-50 | diagnosis: a zero-gain region below ≈ 50–60 % I0 (V_B − V_A −0.00003 mV at 10 %, −0.69 mV at 50 %); thresholded start-up with hysteresis, Mpo injection into o1 | 10 ms ramp at tt holds within ±1 % but bias_ok asserts at VAPWR ≈ 1.1 V (4 % of I); 1 µs ramp relaxes (15 assertions, peak 5.4 × I0); the WO-50 DC "errors" were later shown to be nonphysical .dc solutions (V_A ≈ −1400 V) | WO-50; C6 §6.5 |
| WO-55 | **architecture (c)**: amp input pair skewed 2:1 (balances at V_B − V_A ≈ +15 mV, ≈ 7σ); bounded kick into o1; bias_ok from a pnp-on comparator on V_R1 (core-derived, not VAPWR-derived); R1 → 94 µm | smoke: one stable equilibrium at tt/27 and sf/27 (noskew broken copy REJECTs); dci from 0 and VDD 1.06845 / 1.06845 µA vs op 1.06844; 1 µs ramp settles to 0.03 % but ±1 % only 26–40 µs after the ramp (gate 10 µs) | WO-55; C6 §6.6 |
| D78 | accept a ≈ 40 µs settle; row → settled ±1 % before rstb release; C9 holds rstb after bias_ok for a count set from the measured worst (e.g. 256 fs cycles ≈ 64 µs at 4 MHz); one bias_ok rise required | — | D78 |
| WO-64 | diagnosis: I0 1.45 µA and TC −3.7…−4.2 % had one cause, a tune grid (R2/R1 3.0–6.6) that never bracketed zero TC; two-stage tune (R1 165 µm, then rescaled to 1.07 µA); sf/27 "third state" was a solver artefact (nodeset now from a transient); 125 °C SIMFAIL traced to the bench; D78 rows implemented | pool collected 2026-11-14: MISMATCH 18 (125 °C SIMFAIL, fast-ramp metric) → WO-80 | WO-64; RESUME 2026-11-14 14:50 |
| D85 | VAPWR-good is a C9 counter, not a C6 detector: rstb held 2^16 fs cycles after rst_n release AND bias_ok high 256 cycles; board asserts rst_n only after VAPWR is up | bias_ok fired at VAPWR 1.4–1.7 V; an analog detector would need a 2.3–2.85 V threshold over temperature | D85; CL-36 |
| WO-80 | R1 144.8 / R2/R1 2.45, no re-tune; 125 °C SIMFAIL root cause = deck gmin 1e-15 (tran decks now gmin 1e-12, abstol 1e-12, error ≈ 3 pA per node); `dev` relabelled info; bias_ok pulses measured | DC/loop/dci rows all ACCEPT (table below); tran rows REJECT on `rises == 1`; final summary MISMATCH 16; worst settle after the final rise 1.68 ms | WO-80; `results/wo80/summary.txt` |
| D89 | start-up row redefined (CL-38): from the final bias_ok rise, settle to ±1 % within 0.25 × the 2^16-cycle hold (4.1 ms at 4 MHz) and stay there from release; earlier pulses reported, not gated; broken copy must settle too slowly | — | D89; CL-38 |
| WO-87 | D89 gate in `tran_eval`; a current never inside ±1 % at the last sample now counts as "never settled" (was read as settled); new copies `slow` (τ 1.2 ms master leg) and `earlyx`; `oldhint` retired to info (no longer breaks at the new operating point), replaced by `zhint`/`zhintnk`; 125 °C 1 µs ramps get gmin 1e-11 (≈ 30 pA per junction) | rerun pool (42 jobs) **PENDING** | WO-87; wo/INDEX |

**R1 144.8 µm, DC results (WO-80, five dct corners).**

| Row | Result | Limit |
|---|---|---|
| TC over −40…125 °C | −2.56/+0.08 % (ff, worst) … −2.12/+0.15 % (fs) | ±3 % |
| I0 at tt/27 | 1.0677 µA (−0.21 %) | 1.07 µA ± 2 % |
| Own current | 4.34–4.96 µA | ≤ 6 µA |
| Trim cover / step | 1.410–1.411 / ≤ 5.06 % | ≥ 1.3836 / ≤ 6 % |
| Start-up from rest (dci from 0 and from VDD, 15 points) and loop rows | one stable point, no mid crossing, all ACCEPT | — |
| PSRR (dcv, info) | 70.5–72.5 dB | ≥ 40 dB |

**bias_ok pulse findings (WO-80; RESUME 2026-11-15 00:10).** At low VDD nothing holds the bias_ok output q low: the default-low device is gated by tsu, which is still below the NMOS threshold, so q follows the supply through the inverters. Measured pulses:
- fast (1 µs) ramps: early pulses of 0.1–1.0 µs at VDD ≈ 1.01 V with near-zero current; ff/−40 adds a 4.2 µs pulse at full VDD;
- slow (10 ms) ramp at sf/−40: a **104 µs pulse at VDD 1.02 V with I ≈ 0**, longer than the 64 µs C9 bias filter;
- fs/125 10 ms: the final rise comes at VDD 1.08 V with 2 % of the current.

The worst settle after the final rise is 1.68 ms, well inside the ≈ 16 ms C9 hold. The user chose to redefine the row (D89) rather than change the circuit, relying on the board rule (D85) and on the bias-run restart (D88). Two old broken copies, `early` and `hy1`, were rejected only by the removed `rises` rule and are expected to ACCEPT under D89; whether to retire them to info or add a separate hysteresis row is an open decision (WO-87 §1).

**Alternatives rejected at WO-55 (C6 §6.6).**
- (a) Banba with a current-sensing start-up: it needs a release threshold accurate to better than ×2 over VDD/T/corner, and the leaker spreads ×4.
- (b) Beta-multiplier (constant-gm): $I \propto 1/(\mu R^2)$ gives ≈ +0.8 %/K with xhrpoly, ≈ +130 % over −40…125 °C, against the 3 % row.

**Open items.**
- WO-87 transient rerun under D89 (42 jobs). **PENDING.**
- `early` / `hy1` copies: retire or add a hysteresis row (user's call; WO-87 §1).
- The ivbl0 clamp current from C1 tb9 (C6 §5).
- VAPWR-good for the sequencer: answered by the C9 counter (D85, CL-36, CL-37).
- The bias-readback oscillator (D49), conditional on area.

## III.6 C9: digital (RTL, verification, hardening)

### III.6.1 RTL architecture

Verilog-2005, one clock domain at clk 48 MHz. The macro top is `sd_adc_c9` (D72); `tt_um_sd_adc_c9` is a simulation-only wrapper (README C9). Hierarchy:

```
sd_adc_c9
 ├─ c9_fsdiv  divider, fs_tick (1-clk enable), bit clock
 ├─ c9_cfg    serial shift register, shadow, active, cfg_pending
 ├─ c9_seq    slot counter, reset window, chop, forced y[0] / DAC flop, control outputs
 ├─ c9_dec    acc1 (14 b), acc2 (24 b), hold, frame_ready / overrun, rd guard
 └─ c9_rdbus  addr sync, registered 16-bit word, debug mux
```

Accumulator widths:
- acc1 is 14 b ($|acc_1| \le 4096$).
- acc2 is 24 b, because $\max|acc_2| = N(N-1)/2 = 8{,}386{,}560 < 2^{23}$ for N ≤ 4096.
- Both are sign-extended to 32 b on readout, so frame words and firmware are unchanged (CL-29, CL-32; D72, D77).

Firmware-visible facts: the acc LSBs are always 0 for even N, and status[8] is tied to 0 (README C9, WO-42).

**RTL revisions since D77** (wo/INDEX; CL-36, CL-37):
- D79 retime (WO-60B; PnR in WO-66): fs_tick / s_tick registered one clk early and the divider terminal constants registered, which removed the fs_div compare → overrun path from the critical path.
- D85 (WO-74, RTL df9bded): new input `bias_ok` (2-FF synchronised) and the VAPWR-good hold, parameterised by PW_BITS / BIAS_BITS (16 / 8 on chip). FF 231 → 259, cells 966 → 1068.
- D88 (WO-82, RTL baa0706): the bias run clears on any low sample until release, saturates at done and freezes after release. One RTL line; 259 FF, cells 1068 → 1077 (generic count; CL-37).

### III.6.2 Port contract and contract decisions

| Decision | Content |
|---|---|
| D66 (CL-12 … CL-26) | 16 ambiguities from the independent verification plan resolved: rd guard (snapshot at the rd edge, post-load compare), hold reset invalid = 1 / trim 100, write time = synchronised shadow update, fs_div restart without a runt period, effective-change rule, shift register cleared at rst_n and after cfg_ld, divider held in reset, registered read bus (≤ 3 clk), `ena` ignored, free-running ≈ 50 % bit clock, phase generator in analog C4, sequencer on a 1-clk `fs_tick` enable (design for formal) |
| D67 | debug y = the DAC flop, changes on the rising bit-clock edge; all C9 → analog controls active-high at the C9 port |
| D70 (CL-27) | rst_n release synchronised by 2 FF; the first fs_tick comes exactly `div` clk after the synchronised release |
| D72 (CL-29) | narrow accumulators, macro renamed, STA proxy corner ss_100C_1v40 (125 °C / 1.98 V unchecked), one PnR run |
| D74 (CL-28) | comp_in captured straight into the DAC flop on fs_tick; comp_s removed (one cycle less loop delay) |
| D77 (CL-32) | acc2 24 b, not 25; the 23 b mutant must REJECT, 24 b is equivalent |
| D79 | PnR fixes one change per run: clock-delay cells banned from the resizer, then the fs_tick retime |
| D85 (CL-36) | `bias_ok` input and VAPWR-good hold: no slot and rst_analog = 1 until 2^16 fs cycles after the synchronised release AND bias_ok high for 256 cycles; the board asserts rst_n only after VAPWR is up |
| D88 (CL-37) | AMB-30: bias_ok must be high for the last 256 consecutive fs cycles before release (the count restarts on a drop; sticky only after release); AMB-31: fs_clk keeps toggling during the hold |

**Control signals to analog** (SPEC §3.8a): `rst_analog`, `sys_swap`, `ota_chop_phase`, `short`, `order`, `boost`, `trim[2:0]`, `y_force`, `bit_valid`, plus the fs bit clock. All are active-high direct flop outputs. **F-IF-1:** the comparator output must be latched, with a minimum delay clk → comp_in ≥ 1 ns (HARD §6). C3's SR latch holds q through precharge (C3 §2).

### III.6.3 Verification (VPLAN; WO-38 … WO-58)

- **Independent bench.** A separate verification agent derives intent from SPEC, never from the RTL author. cocotb + Verilator/iverilog, with always-on checkers (VPLAN §2).
- **Ref A.** A cycle-level Python reference at clk resolution, written from SPEC §3.7a/§3.8a with no import of `model/golden.py` or `iadc.py`. It must reproduce every golden frame, sequence and trace row before it is used on random stimulus. A disagreement is triaged as a SPEC ambiguity (VPLAN §2.4).
- **Hostile comparator BFM.** `comp_in` carries the correct bit only on the capture clk and the inverted bit on every other clk. A DUT that captures one clk early or late fails (VPLAN §12).
- **Coverage.** Functional bins 250/250 after WO-49B (RESUME 2026-11-13). Unreachable bins are documented, e.g. multi-write within 3 clk of the latch edge (VPLAN §11.2).
- **Mutation.** 64/65 killed on the D72/D74 RTL. The survivor W2 (acc2 24 b) was provably equivalent, which led to D77 (RESUME; D77). WO-58 re-anchored the width mutants: W2 = 23 b, M01 = 22 b (git log 80bb23e).
- **Formal.** SVA properties F-01…F-17 on `c9_core` via sby (yices / abc pdr). Each property must fail on at least one mutant, otherwise it is reported as vacuous (VPLAN §5). F-01 was strengthened to fail on M07, M07b and M19 (VPLAN §11.2).
- **CDC.** A static review (VPLAN §11.1): rst_n async assert / sync release; 2-FF synchronisers on cfg_clk, cfg_dat, cfg_ld and rd. Multi-bit `addr` may show a wrong word for 1 clk, inside the 3-clk settle.
- **WO-75, bench for D85** (RTL df9bded; VPLAN §14). Golden v3.2 stays the arbiter from slot 0 on, because the hold only adds a prefix before slot 0. Ref A models the hold from the SPEC text, and an independent observer in the bench checks the slot-0 tick. Ref A agreement, lint, suite seeds 1–3 (27/27 each, including the new hold tests d_hold01–04), C9_FULL, R-01 seeds 1–20, GL quick (27/27) and d_hold01 at the real 16/8 widths all PASS. Formal F01–F18 PASS at reduced widths (F18 at 3/2), and F18 FAILs on hold mutants, so it is live. Every mutant is killed except M64, the known equivalent; M45 first survived because the bench top bypassed the tt_um wrapper, which was then fixed. No RTL bug was found; the bench raised AMB-30/31, which became D88 (WO-75).
- **WO-83, bench for D88** (RTL baa0706; VPLAN §15). `defparam` was removed so Verilator builds the bench top again (X-01 s1 7/7 PASS). Ref A and `exp_slot0()` are written from the CL-37 text; a new test d_hold05_d88 has six hand-derived slot-0 cases; new mutants M71–M74 and re-derived M66/M68; F18 follows CL-37 and a new F19 checks that slot 0 is not late. Smoke: F18 and F19 PASS at 3/2. Full regression: **106 of 107 jobs EXIT=0 so far**, the rest PENDING (coordinator note 2026-11-15).
- **Formal width limit.** The counter properties are proven only at reduced widths. At the real 16/8 widths F18 timed out at 8673 s with no proof, and F19 was killed at more than 5 GB of memory during the 2026-11-14 overload. The real widths are covered by RTL simulation (d_hold01 and d_hold05 at 16/8). The formal reruns are to go alone under `ulimit -v` (WO-83; RESUME 2026-11-14 18:45). A width ladder (4/2 … 12/6) in the WO-83 pool shows the widest width proven.
- **Remaining risks** (RESUME 2026-11-13; WO-83): SOAK only 3000 slots; no gate-level / SDF simulation of the final layout yet; the `c9_seq.v` comment on the bias bit is stale after D88.

### III.6.4 Hardening (HARD; WO-47, WO-58B)

- **Flow.** A separate LibreLane macro, imported as LEF/GDS into the Magic top. Every reference TT analog design that contains digital logic does this (HARD §1).
- **Placement.** The macro sits along the top edge near the TT digital pins, with C4 as a buffer band and OTA1 plus the cap arrays at the bottom next to ua0–ua3 (HARD §2).
- **Probe (WO-47).** 1111 cells, 15,172 µm², 276 FF. Pre-PnR setup WNS 1.753 ns at ss_100C_1v60. The die was estimated at ≈ 190 × 150 µm (35–45 % of the tile), ≈ 2× the SIZING digital budget (WO-47; HARD §3).
- **After narrowing.**
  - D72: 936 cells / 225 FF.
  - D77: 929 cells / 223 FF (RESUME 2026-11-13; generic yosys count). LibreLane sky130 synthesis in WO-58B gives 860 cells / 223 FF; the two counts use different bases.
- **PnR config (WO-58B, commit a166371).** PDN_MULTILAYER rename, 190 × 150 die, ss_100C_1v40 corner, all-corner timing checks. first PnR (WO-58B, `results/wo58b/README.md`) finished with EXIT=2: setup fails at ss_100C_1v40 (WS −1.599 ns max RC, Fmax 44.6 MHz), 54 max-fanout violations at every corner, slew violations (203 at ss_1v40 max RC); physical checks clean (Magic/KLayout DRC 0, LVS 0, antenna 0). WO-60A (`results/wo60a/README.md`, clkdlybuf/dlymetal6s banned, D79) improved setup WS to −1.181 ns (Fmax 45.4 MHz) with 2 violating paths per RC corner, but slew violations rose to 336 and fanout stays at 54; physical checks still clean. D79 then started a sequence of single-change PnR runs, each with every check re-run (STATE-2026-11-14 §2, lesson 5):

| Run | Single change | Result | Source |
|---|---|---|---|
| WO-60A | clkdlybuf/dlymetal6s banned (D79) | setup WS −1.599 → −1.181 ns at ss_1v40; slew 203 → 336 | WO-60A |
| WO-66 | fs_tick retime RTL (D79) | **setup and hold met at all 12 corners** (ss_1v40 +2.582 ns, Fmax 54.8 MHz); tt reg-to-reg 6.66 ns < T/2; physical clean; fanout 46, slew 256 (ss_1v40), cap 3 | WO-66 |
| WO-67 | buf_1 banned | worse: the resizer used delay cells as fanout buffers (ss_1v40 +0.17 ns); reverted (8ddea05) | wo/INDEX; HARD (WO-67) |
| WO-69 | heuristic diode insertion off | fanout 46 → 10, slew 43 pins (ss_1v40 only), cap 0, diodes 342 → 13; utilisation 0.668 | WO-69 |
| WO-71 | CTS sink clustering size 8 | fanout 0 at 12 corners; setup +2.777 ns; slew unchanged | WO-71 |
| WO-72 | post-GRT design repair on | no effect: the resizer's parasitic estimate shows no slew violator, while routed slew is 1.37–1.49 × the GRT estimate | WO-72; WO-73 |
| WO-73 | GRT slew margin 10 → 40 % (D84) | slew 43 → 32 pins at ss_1v40, worst 1.728 vs 1.5 ns; setup +2.961 ns; hold +0.108 ns; DRC and antenna 0; LVS not extracted; 2 floating nets (RSZ-0020) unnamed | WO-73 |

D86 waives max slew at the ss_100C_1v40 stand-in corner only: it occurs only at the pessimistic 1.40 V stand-in for 125 °C, setup slack there is +2.96 ns, and ss_1v60 and every other corner are clean. The **final PnR** on the D85/D88 RTL carries the WO-73 flow settings with `bias_ok` added to `pin_order.cfg`, then re-checks slew, LVS and the 2 floating nets; it is **PENDING** (D86; STATE-2026-11-14 §6). WO-73's first copy failed for exactly that reason: HEAD already had the `bias_ok` RTL but `pin_order.cfg` did not list the pin (WO-73).
- **STA gap.** sky130_fd_sc_hd has no 125 °C or 1.98 V liberty, so 125 °C / 1.98 V stays unchecked (D72).
- **Precheck traps** (HARD §8):
  - run the Magic antenna check ourselves;
  - power labels must span the stripe;
  - verify by extraction that all 24 outputs reach a driver;
  - no met5 or via4 in the macro;
  - pin the precheck tool commit.

## III.7 C5, C7, C8, C10: status

| Block | Status (2026-11-15) | Source |
|---|---|---|
| C5 choppers | the OTA1 choppers are inside C1 (input chopper at the gates, 3.3 V NMOS 4/0.5; fold-node chopper 1.8 V 4/0.15); the system-chop swap is merged into the C4 input switch (#1); no separate C5 design note | C1 §1.4; C4 §2 |
| C7 level shifters / layout | cell choice and count in C4 rev b; isolation done in logic (D78); layout rules carried by pd-expert (common-centroid references with edge dummies, D59); top-level assembly not started | C4 §7; D59; D78 |
| C8 reference input | spec row τ_ref ≤ 10 ns at ss/−40/3.0 with the 500 Ω + 5 pF pad and R_ext 10 Ω; DAC switch sizes from C4; the C8 tb is not started | SPEC "Reference" row; C4 §3 |
| C10 MIM arrays | spec rows: Cs+/Cs− ≤ 0.75 % 3σ, Cp,top ≤ 20 fF/side, ΔCp,top random ≤ 0.25 fF / systematic ≤ 0.08 fF; 66 dB CMRR target needs ΔCp,top ≤ 0.15 fF; not started | SPEC "Capacitors" row; D36, D37 |


---

# Part IV: Verification methodology

## IV.1 The gated flow and its tiers (D1, D2)

The user rule (D1): a gated flow system → component → verification suite. Proceed only if every check passes at every corner. The method follows Paul Thomas's: a single parameter source, tiered simulation, per-block tb + cross-check + MC + PEX re-simulation, ACCEPT/REJECT gates and top-level PEX acceptance.

| Tier | What | Used for | Source |
|---|---|---|---|
| 0 | Python model `model/iadc.py` | full corner sweeps, MC, budgets, golden vectors, A(v)-table INL, CM-to-DM bounds | GUIDE §2; MODEL |
| 1 | behavioural SC modulator in ngspice (B-source OTA, ideal switches) | slew/settling knees, fast-mode options, the gate-B harness | GUIDE §2; `design/tier1/` |
| 2 | transistor-level blocks | per-block gates at every corner + MC | PLAN Stage C |
| 3 | PEX | block re-sim, top acceptance | PLAN Stage V |

**Why not full transistor top-level runs at every corner.** Long top-level transistor transients at 45 PVT points are infeasible in ngspice. TilesOS could not complete an 8192-bit transient (VPP cap timestep failures). So:
- each block is proven at every corner on its own;
- the top is checked at 5 extreme points with ≤ 2048-cycle windows;
- the model carries the full corner sweep (D2; CTX §4).

**Stage V plan** (GUIDE §2):
- V1 assembly;
- V2 cold start;
- V3 DC transfer;
- V4 mode matrix (V4a: the OTA-only chop residue);
- V5 mixed-signal bit-exact against the golden vectors;
- V6 top PEX;
- V7 non-vacuity;
- V8 physical / precheck;
- V9 system re-proof with PEX parameters.

## IV.2 Spot runs versus full runs

- **Spot runs** support a design note at stage 1 of the recipe. They are labelled "not a gate", and their optimism is listed. The C1 spot deck, for example, had no junction caps, ideal references and an ideal CMFB (C1 status notes).
- **Full runs** are the gate. They run on a **frozen copy** of the tree pinned to a commit (`/home/mempool/regr/tt/WO-NN-<sha>`), never on the working tree. They cover every corner in the row's corner set, include every broken copy, and print one VERDICT line with a non-zero exit on any mismatch (GUIDE §5).

## IV.3 Gates and broken copies

**Rules applied in every testbench** (C1 §4; C3 §6; C4 §11; C6 §9):
- ACCEPT/REJECT per row;
- NaN or a missing measurement fails;
- tstop must be reached;
- expected values come from SPEC or hand calculation, never from the DUT;
- every row has a broken copy that must REJECT.

**A broken copy that passes makes the row blind.** The fix is a better copy or a stricter row; the gate is never relaxed to suit the copy. Recorded blind spots and their fixes:

| Blind spot | Fix | Source |
|---|---|---|
| m_pl L 0.5 moved boost INL only 2.43 → 3.02 ppm | PMOS cascode D–S short becomes the INL-gate copy | CL-1c |
| PMOS short passed the precision INL gate (3.37 ≤ 5.33 ppm) | per-mode copies: droop copy + known-answer table (S4 shape at 76 dB: 8.51 / 8.31 ppm) | CL-1d; C1 §2.10 |
| `brk_starve` comparator passed the decision-time row (6.4 ns ≪ 33.75 ns) | T2band row [0.5, 3] × the spot value | WO-44; C3 §3.3 |
| start-up row relative-only: mio 119 mV off V_OCM passed | absolute term \|steady − V_OCM\| ≤ 10 mV | WO-32; D68 |
| clamp held at V_OCM is a CM source, invisible to CM rows | DM diff-step row in the event deck | WO-36; D69 |
| masy on the output side was blind (0.01 µV) | inject on the island side: 0.550 µV REJECT | WO-30 |
| K_P row blind to `kp_fixed` once REF_TRIM was in | perturbation copy `kp_fixed + ibn105` | WO-25, WO-26 |
| mhalf (pair W/2) barely changed thermal noise (sinks dominate) | msink sensitivity row | WO-41; WO-52 |
| combine() returned INVALID for a healthy slew-limited copy | rule: all parts healthy and > gate ⇒ REJECTED | WO-26; WO-29 |
| decision memory in rev c hid behind passing CM 1.8 V rows | `ap_an_pre_fire_mV` probe, rev c info copies | WO-56 |

## IV.4 False-pass lessons

| Lesson | What happened | Guard now in place | Source |
|---|---|---|---|
| Ideal parasitics | SPICE CMRR 132–152 dB with Cp,top = 0 and the wrong metric | parasitic allocations in decks; metric defined in SPEC | D33; GUIDE §6 |
| Latched tb9 bench | Cint wired outp → inp: positive differential feedback latched the outputs (V_diff 3.107 V); the CMFB wound up; D62 had been decided on this bench | polarity fixed; broken copy `TB9_POL_OLD=1` REJECTs; D63 corrected D62 | WO-29; D63 |
| Transient-op fallback | ngspice fell back silently to "Transient op" in a non-converging deck; huge caps kept their initial charge (V_OCM error +1.76 V on a helper) | "transient op" is lint that fails every row; one closed copy + its open twin per deck; helper op = closed op within 1 mV; WO-52: noise-deck fallback accepted only if gm matches the op deck within 0.1 % | WO-28 bug 1; WO-29; WO-52 |
| Solver convergence | O0 results unconverged with either sign (6.69 → 18.77 ppm); chgtol 1e-16 with reltol ≤ 1e-4 aborts decks | O0 → O1 → O2 ladder on every gated number with < 3× margin; smoke-test each new setting | D43c; S5h; GUIDE §6 |
| Simulator floors | default gmin 1e-12 added a flat ≈ 1.65 pA "leakage"; the real value was 0.7 pA at 100 °C | check simulator floors before trusting small currents | GUIDE §5–§6 |
| DC-sweep tool errors | a single −1.8 → +1.8 V A(v) sweep started clipped and stayed at the rail; vntol 1 µV quantised the gains; vntol 1e-10 broke DC convergence | two sweeps outward from 0 V; servo node scaled ×1000 | C1 §2.10 |
| Nonphysical DC solutions | C6 .dc "errors" (12–23 µA, 5.5 mA own current) had V_A ≈ −1400 V | DC hint near the operating point; reject off-rail results (`phys`) | C6 §6.5; WO-55 |
| PDK MC blind spot | HV devices have `vth0_slope = 0` | hand-Pelgrom allotments; injected ΔVT in MC; σ plausibility vs a per-device sensitivity estimate | WO-44; C3 §3.1, §6 |
| Assumed scaling | gm ∝ I assumed for boost; real gm ratio 1.28–1.42 | gm/Id tables before sizing rules; gate absolute boosted points | GUIDE §6; D39 |
| Wrong metric frame | S4 sys-on residue added in the modulator frame after demodulation | `convert` returns the demodulated residue-corrected estimate | D38(a) |
| Unusable PDK cell models | clkiso / isosrc level-shifter models do not simulate | logic isolation with simulable cells | WO-54; D78 |

## IV.5 Cross-tier agreement and theory checks

**Model ↔ tier 1.** Agreement within ≤ 5 % rel_sym; achieved 0.0–0.7 % (GUIDE §5). A disagreement is a finding, as in the Ck loading case (II.4.1).

**Theory ↔ code.** Every study prints PASS/FAIL theory checks against closed forms, as in S1 and S3 (`s1_vref.md`; `s3_budget.md`). Each check must reject a perturbed theory (×1.5, ×0.5 and NaN in S3).

**Hand ↔ SIM.**
- The A0 hand formula is within ±1 dB of AC (achieved +0.24…+0.55 dB) (WO-24; WO-25).
- The noise hand row is held to ±30 % with measured γ (D71; WO-43).
- The CMRR closed form: ε_eff code = hand 8.407e-4 (GUIDE §5).

## IV.6 Determinism

- **Golden vectors.** Canonical JSON, byte-identical regeneration, sha pinned in the test. Every revision proves the previous revision's rows are a subset (GOLD).
- **Frozen copies.** Every gate runs from `/home/mempool/regr/tt/WO-NN-<sha>` with a recorded commit (GUIDE §5).
- **Thread count.** `.spiceinit` sets `num_threads=1` for the decks. Changing from 8 threads to 1 mid-run left gate-B endpoints within 0.021 ppm (WO-31).
- **Seeds.** MC decks carry their own `rndseed`. Python injections use `random.Random(seed)` (C3 §7).
- **Raw CSV** is deleted after parsing. Results are stored as JSON lines plus a README per WO (WO-45; WO-48).

## IV.7 The sandbox and lpool process

**Everything runs on the sandbox, nothing locally** (CLAUDE.md working rules):
- `scripts/sync-to-sandbox.sh` pushes the tree.
- `~/bin/rta-tt` runs commands.
- EDA runs in IIC-OSIC-TOOLS through `scripts/iic`.
- The project tree lives in `/home/mempool/tt-sd`.

The sandbox has 6 cores and 15 GB. Keep about 5 processes in total (RESUME 2026-11-08 17:22).

**lpool** (`scripts/lpool.sh`) is a load-adaptive job pool:
- Single-threaded ngspice jobs.
- Parallelism sized from the box load; it throttles to 1 job at load ≈ 6 (RESUME).
- `POOL_DONE` and per-job `EXIT=` markers. No poll loops in agents.

Two bugs were found and fixed (WO-50 §3; RESUME 2026-11-13):
1. GNU `nproc` honours `OMP_NUM_THREADS`, so callers that exported it got nproc = 1 and ran serially. Callers now use `env -u`.
2. The running-job count miscounted inside `$(...)`, and a restart over-launched 10 gate-B parts at load ≈ 6. lpool now keeps a PID list, checks with `kill -0`, and waits 30 s between launches.

**Environment pitfalls.**
- A relaunch without the environment failed fast, because ngspice was not on PATH (WO-52 relaunch, RESUME).
- The IIC container cannot mount `/home/mempool/regr` (RESUME, final note).

**The 2026-11-14 overload and the global cap** (RESUME 2026-11-14 18:05, 18:45; coordinator note 2026-11-15). About 15 of the project's own pools ran at once, each sizing itself to the load independently. Load reached 44–53 on 6 cores and memory 15/15 GB when a 10.6 GB yosys-abc PDR (WO-83 F18 at real widths) ran beside them, and ssh hung. Several decks timed out and must be rerun (WO-76 diagnostics, WO-77 jobs 3–5, WO-85 job 1), and the real-width formal runs gave no result. The user decided:
- lpool has a **global cap of GMAX = 5 slots** shared by all pools, implemented with flock slot locks in `/home/mempool/regr/tt/.lpool_slots` (commit 2f2e0a0). Tested: a cap of 2 gave at most 2 concurrent jobs. The broken copy (cap 9) gave only 3 concurrent jobs because the box load limited it, so that test was non-discriminating: it could not have failed. Frozen copies must take lpool from the repo or tt-sd to pick up the cap; older pools drained uncapped.
- Heavy formal or PDR runs go alone, under a memory limit (`ulimit -v`).

Lessons: per-pool load sizing does not bound the total when many pools start together; long decks need timeouts sized for a loaded box (30,000–40,000 s for C1 gate B parts); a timed-out deck is a missing result, neither a pass nor a fail, and no decision is taken until the data exists (RESUME 2026-11-14 20:45).

## IV.8 Review gates

**Reviewer.** A review by `sd-adc-design-reviewer` (read-only) is required for every design change: a design note before the netlist, and again after results land (CLAUDE.md working rules; GUIDE §5 item 6). The C3 final review is still open. Reviews on record:

| Stage | Reviews |
|---|---|
| Spec and plan | REVIEW-spec-plan |
| S1–S7 | S1S2, S3, S4S5b, S5, S5c-S4close, S5d, S5e, S5f, S5g, S5h, S6, S7, S7b |
| C1 | C1a, C1a-revB, C1a-revC, C1b-code, C1b-final, WO25, WO26 |
| Other blocks | C3a, C4a, WO01-pd |

These are the `work/v1-design/REVIEW-*.md` files.

**How findings flow.**
- Findings become work orders, and a reviewer's own wrong estimates are logged as well (GUIDE §5).
- The user decides only at real forks, with 2–4 options and numbers. Everything else uses logged, reversible defaults (GUIDE §7). D-numbers record both kinds.

**Tiered agents.** Opus plans and reviews, Sonnet codes from a precise WO, and the coordinator runs acceptance directly. A rate-limited agent is resumed; a new WO gets a fresh agent (CLAUDE.md; RESUME 2026-11-13).


---

# Part V: Status, open items and risks (as of 2026-11-15)

## V.1 Stage status

| Stage / block | Status | Last evidence |
|---|---|---|
| S0–S7 | closed; SPEC v1 frozen 2026-11-09 (D50); post-freeze change log now runs to CL-39 | D50; SPEC change log |
| C1 OTA1 + CMFB | sink L 8 netlist (D75). Boost gate B on this netlist: fs/125 3.14 ppm and ss/−40 0.71 ppm against 5 ppm, both at O1 only; fs/125 needs O2 under D43c (not scheduled); tt/27 and ss/125 only on older netlists (WO-31). Precision gate B (2 MHz, ≤ 1.333 ppm): tt/27 0.692, ss/125 0.698 and fs/125 0.967 ppm pass at O1; ss/−40 fails at O1 (1.706 ppm). The first two O2 parts at ss/−40 read 0.142 and 0.160 ppm (unfiled interim data); the ≈ 10× O1→O2 step does not meet D43c, so **verdict PENDING** the 6-part O2 combine and a further solver point (WO-76). tb7 noise and op/AC mutant benches are fixed; rerun **PENDING** (WO-77) | RESUME 2026-11-14 (WO-52 reruns); WO-63; WO-76; WO-77 |
| C2 OTA2 | not started | III.2 |
| C3 comparator | rev f (op/on keeper) on the D87 bench basis. T2: the single-shot rows pass; the rev f cyc rows were not run (WO-88). T3: the count and \|μ\| + 3σ limbs pass (42.7–45.1 mV ≤ 60 mV); the `plaus` limb REJECTs because the sensitivity decks were not run. T5: accepted by margin by construction (D81). T8 still fails: the sustained excess (+0.344 mV over the pin) is now inside the D90 tolerance (≤ 1.981 V), but the re-judged run is **PENDING**; the precharge-edge peak is 2.224 V (tt/27) and 2.251 V (ff/−40) against the 2.2 V cap (2.179 / 2.206 V with the 2× keeper kp2). Rev g candidates **PENDING** (WO-88) | WO-86; WO-88; D90 |
| C4 switches / generator | rev b. Every WO-54/WO-70 error was traced to bench numerics and fixed (WO-70, WO-79, WO-85); D82 rating rows added. Gate pools **PENDING** (WO-79 `pool2` for the non-tim rows, WO-85 for the tim rows). The ff/100 20 pA row read 23.4 pA in WO-70: **open** | WO-70; WO-79; WO-85 |
| C5 choppers | inside C1 / C4 | III.7 |
| C6 bias | architecture (c), R2/R1 2.45, R1 144.8 µm. All DC, loop and start-up-from-rest rows pass at the 5 corners (TC −2.56/+0.08 % worst, I0 1.0677 µA at tt/27, own current 4.34–4.96 µA, trim cover 1.410). The bias_ok start-up row was redefined (D89, CL-38); transient rerun **PENDING** (WO-87, 42 jobs) | WO-80; WO-87 |
| C7 / C8 / C10 | not started (rules and spec rows only) | III.7 |
| C9 digital | RTL baa0706 (D72, D74, D77, D79, D85, D88): 259 FF, 1077 cells (generic count). WO-75 bench on D85: every row passes, mutants all killed except the known equivalent M64. WO-83 bench on D88: 106 of 107 regression jobs EXIT=0 so far; formal proofs only at small counter widths. PnR on the pre-D85 RTL (WO-73) meets setup and hold at 12 corners with DRC and antenna clean; max slew is waived at the ss_100C_1v40 stand-in (D86). DRV is not 0, LVS was not extracted and 2 floating nets are open, so WO-73 calls it "not a signoff candidate". Final PnR on the D85/D88 RTL **PENDING** | WO-75; WO-83; WO-73; D86; coordinator note 2026-11-15 |
| Stage V | not started | GUIDE §2 |

## V.2 Values still pending a run

| Item | Pending run | Source |
|---|---|---|
| C1 precision gate B, ss/−40: 6-part O2 combine (O1 1.706 ppm; O2 so far p0 0.142, p2 0.160 ppm) | WO-76 `out/logs_o2` | WO-76; coordinator note 2026-11-15 |
| C1 precision gate B, fs/125 at O2 | WO-76 `out/logs_o2` | WO-76 |
| C1 precision gate B at O2 for tt/27 (O1 0.692) and ss/125 (O1 0.698). D43c asks for O2 whenever a gated INL has less than 3× margin (O1 above gate/3 = 0.444 ppm); these two corners are not in the WO-76 job list | no WO yet | WO-63; D43c |
| C1 precision gate B: a third solver point to confirm O2 at ss/−40 (the ≈ 10× O1→O2 step does not meet D43c; no amendment to D43c) | to be scheduled | D43c; REVIEW-BOOK-2026-11-15 Q3 |
| C1 boost gate B on the WO-52 netlist: O2 at fs/125 (O1 3.14 ppm, above gate/3 = 1.667 ppm), and tt/27 and ss/125, which exist only on older netlists (WO-31) | no WO yet | RESUME 2026-11-14; WO-31; D43c |
| C1 tb7: thermal v_vg ≤ 390 µV and the tier-0 direct path with sink L 8, all PVT; mrg and msink copies must REJECT; op/AC mutants per deck | WO-77 rerun; jobs 3–5 timed out under the overload and must be rerun | WO-77; RESUME 2026-11-14 18:45 |
| C1 tb8 / tb8b MC, tb10 stress, tb12 boost toggle, tb13 vg switches | not found in the results read | C1 §4 |
| C3 rev g: precharge-edge cap candidates (R0/R1 0.5/0.15, 1.0/0.3, 1.0/0.5 with kp2; kp3 as info), the rev f cyc rows that were never run, and the leak-path probe | WO-88 pool A and `runI` | WO-88 |
| C3 T8 re-judged at the D90 tolerance (1.981 V), with the `sus1985` checker copy | WO-88 and after | D90; CL-39; WO-88 |
| C3 T3 offset MC on rev f + kp2 or on rev g | not run | WO-86 |
| C4 inj, settle, ramp, leak and rating rows on the softened bench | WO-79 `run/pool2` | WO-79; RESUME 2026-11-14 18:05 |
| C4 tim rows (dead time, strobe placement, order-1 reset) with ideal supplies in tim | WO-85 (54 jobs; job 1 timed out at 5400 s and must be rerun) | WO-85; RESUME 2026-11-14 18:45 |
| C4 ff/100 20 pA leakage row (23.4 pA in WO-70) | WO-79 / WO-85 reruns, then a user decision | WO-79; D82 |
| C6 transient rows under D89: settle ≤ 4.1 ms after the final bias_ok rise, broken copies `slow` and `earlyx`, 125 °C fast ramps at gmin 1e-11 | WO-87 | WO-87; CL-38 |
| C9 F18 / F19 at the real 16/8 widths | rerun alone with `ulimit -v` ≈ 8 GB | WO-83; RESUME 2026-11-14 18:45 |
| C9 WO-83 regression: the last of 107 jobs | WO-83 pool | coordinator note 2026-11-15 |
| C9 final PnR (D85/D88 RTL, slew margin 40 %, `bias_ok` in `pin_order.cfg`), LVS re-extraction, the 2 unnamed floating nets, then the gate-level / SDF sim | next C9 PnR WO | D86; WO-73; STATE-2026-11-14 §6 |
| System current in fast mode with real blocks | needs C2 and C6 numbers. OTA1 alone draws 121.8–123.9 µA in boost on the WO-28 netlist. Reviewer estimate (REASONED, not simulated): OTA1 ≈ 122 + OTA2 ≈ 51 + bias ≈ 6 µA ≈ 180 µA nominal, against the 172 µA SPEC estimate and the 200 µA budget. Scaling the accepted 189 µA worst case by 180/172 gives ≈ 198 µA, about 1 % under the budget | WO-28; SPEC §1; WO-62 reviewer |
| Reset residue r ≤ 1e-4 in 2 cycles at 4 MHz boost and 0.25 MHz | C1/C2 integration (needs C2) | C4 §11; D46a |
| System noise / INL with PEX parameters (V9) | Stage V | SPEC §3.0 noise row |

## V.3 Open decisions and items

1. **C1 precision gate B.** A passing 6-part O2 combine is not enough on its own: the ≈ 10× O1→O2 step does not meet D43c as written, so O2 becomes the result only if a further tightening confirms it (D43c; WO-76 §2). D43c is not amended; a third solver point is to be scheduled, and the verdict stays PENDING until then (coordinator answer to REVIEW-BOOK-2026-11-15 Q3). If it then passes, no design change follows (RESUME 2026-11-15 00:45). If it fails, options go to the user with data. Bias scaling is not supported by the data so far: it moves the error between parts instead of removing it (RESUME 2026-11-14 23:40).
2. **C1 precision broken copy.** `srknee` rejects at 1.375 ppm, only 3 % over the 1.333 ppm gate, and only part 0 rejects on its own. It is a weak discriminator (WO-63; WO-76 §4).
3. **C3 T8 precharge-edge cap.** Choose a rev g candidate from the WO-88 sweep, then run the full C3 set; name the leak path that lifts op/on (WO-88).
4. **C6 broken copies `early` and `hy1`.** Under D89 they are expected to ACCEPT. Retire them to INFO, or keep a separate hysteresis row with a noise-injected bias_ok bench (WO-87 §1). User's call.
5. **C4 ff/100 20 pA row.** 23.4 pA in WO-70; a user decision follows once the rerun confirms it (WO-79; wo/INDEX).
6. **C6 ivbl0 clamp current** from C1 tb9 (C6 §5).
7. **C3 kickback options.** Halve the pair, or add a neutralisation pair; not applied (C3 §3.4b). The CM kick stays ≈ 39–47 mV on rev f and kp2 (WO-86).
8. **C2 swing.** OTA2 must hold A ≥ 75 dB to ≈ 1.41 V differential plus the CM kick (C3 §3.1b; WO-86).
9. **D49 bias-readback oscillator.** Conditional on C6 floorplan area.
10. **SPEC-AMB-24** (cfg_ld / rd minimum width) is open from WO-42 (RESUME).
11. **C9 STA.** 125 °C / 1.98 V is not modelled by the liberty set (D72); max slew is waived at the ss_100C_1v40 stand-in (D86).
12. **To raise when relevant** (STATE-2026-11-14 §5): the fast-mode current budget when C2 starts; a C9 die shrink (utilisation ≈ 0.68); the SOAK scale (10⁶ slots is not reachable at the current simulation speed).

## V.4 Risks

| Risk | Basis | Source |
|---|---|---|
| C1 precision INL depends on solver settings at ss/−40: O1 1.706 ppm against O2 0.142–0.160 ppm on the parts run so far | the gate verdict rests on the O2 combine; a pattern-dependent error that moves between parts under bias scaling | WO-76; RESUME 2026-11-14/15 |
| C3 T8: precharge-edge overshoot on 1.8 V oxide pairs above the 2.2 V / < 1 ns cap (2.206 V at ff/−40 even with kp2) | rev g not chosen yet; any extra device on the HV nodes may move T5 kick and T2 | WO-86; WO-88 |
| C3 sustained sub-mV excess above VDPWR on op/on and nb2/ob2 | accepted by the D90 tolerance; the injection path is not yet named | D90; WO-86 |
| Virtual-ground leakage ≈ 150 pA per node at ff/125 (C1 81 pA + Sg 68.5 pA) against the 90 pA row | handled by derating (D82): 0.25 MHz N 1024 rated to ≤ 100 °C, N ≤ 256 at 125 °C; the ff/100 20 pA row is open (23.4 pA) | WO-70; D82; CL-34 |
| Sys-off CMRR margin 1.1–1.5 dB over 60 dB; the 66 dB target depends on layout (ΔCp,top ≤ 0.15 fF) | model with allocations, not PEX | `s4_corners.md`; D36 |
| MIM voltage coefficient and bottom-plate parasitic not in the PDK model | appears only in PEX/silicon; covered by the 4 ppm INL reserve | SPEC §6 |
| Digital → analog substrate coupling inside the tile not simulated | isolation by placement and guard rings only | SPEC §6; HARD §2 |
| HV-device mismatch from hand Pelgrom (A_VT 12 assumed) | PDK MC has no vth0 term | C1 §2.11; WO-44 |
| Fast-mode current against the 200 µA budget | 189 µA worst after trim is accepted risk; OTA1 alone ≈ 124 µA boost on the netlist; reviewer reasoned estimate ≈ 180 µA nominal vs 172 µA SPEC | D46c; WO-28 |
| C6 reference window: only +1.6 % above nominal at ff/125 base before the OTA1 ceiling | calibration "+2" rule lands at 0.85–0.97 × | WO-32; D73 |
| bias_ok can pulse high before the bias is valid (0.1–1 µs at ≈ 1 V on fast ramps; 104 µs at 1.02 V on a slow sf/−40 ramp) | covered at system level by the board rule (rst_n only after VAPWR is up, D85), the bias-run restart (D88) and the 2^16-cycle hold; no brown-out detection | WO-80; D85; D88; D89 |
| C9 counter-width proofs: F18/F19 proven only at small widths; real 16/8 runs timed out (8673 s) or ran out of memory (> 5 GB) | real widths covered only by RTL simulation (H-01, H-05 at 16/8) | WO-75; WO-83; coordinator note 2026-11-15 |
| C9 timing at 48 MHz | met at 12 corners on the pre-D85 RTL (ss_1v40 stand-in +2.96 ns); slew waived at the stand-in (D86); the final PnR on the D85/D88 RTL (≈ +9 cells) is not run | WO-73; D86 |
| C9 area: die 190 × 150 µm = 28,500 µm², ≈ 40 % of the 72,071 µm² tile | the analog blocks have no layout yet; the tile was 66–89 % full by estimate | WO-60A; HARD §2–3; D42 |
| Untested 48 MHz assumption for the TT clock | fs_div table valid only at 48 MHz | SPEC §3.8a |
| Host read rate | at 4 MHz / N 64 the host needs ≥ 0.36 Mword/s; MicroPython cannot keep up | SPEC §3.8a |
| Sandbox capacity | overload on 2026-11-14 (load 44–53, 15/15 GB) delayed C1, C4 and C9 runs; several decks timed out and must be rerun | RESUME 2026-11-14 18:05; IV.7 |
| No PEX anywhere yet | every block margin is schematic-level | PLAN; GUIDE §5 |
| Model gap to silicon | the model is the intrinsic floor: no reference noise, coupling or board noise; Wulff's SAR came in ≈ 0.6 b below sim | MODEL caveats; CTX §4 |


---

# Appendices

## A. Glossary

| Term | Meaning |
|---|---|
| A(v) | static large-signal secant gain $v_o/v_g$ at differential output $v$ (CL-1b) |
| A′ | fast-mode option: OTA1 and OTA2 tails ×2 in boost (D41) |
| AMB-nn | SPEC ambiguity found by the C9 verification plan (VPLAN §8) |
| β (beta) | feedback factor $C_{int}/(C_{int}+C_s+C_p)$ |
| boost | config bit that doubles the OTA bias for 4 MHz fast mode (D31) |
| broken copy | a deliberately damaged circuit/model that a gate must REJECT |
| CIFB | cascade of integrators with distributed feedback |
| CMFB | common-mode feedback |
| CoI | cascade-of-integrators decimator (acc1, acc2) |
| combine() | gate-B merge of 6 parallel parts with endpoint agreement checks (WO-25, WO-29) |
| D12 | CM-rejecting input switching by top-plate shorting |
| direct path | tier-0 noise path that injects the simulated sampled v_vg into the kT/C term (D71) |
| dual-path CMFB | fast passive SC path plus a slow gm-C integrator (D61) |
| frozen copy | tree copy pinned to a commit on the sandbox, `regr/tt/WO-NN-<sha>` |
| gate A / gate B | step-settling diagnostic (report only) / in-loop transistor OTA1 INL gate (D48) |
| golden vectors | tier-0 reference frames for the C9 RTL (`golden/s6_vectors.json`) |
| HV | 5 V `g5v0d10v5` devices used on the 3.3 V supply |
| island | the virtual-ground node region between the vg switches and the OTA input |
| K_P, K_N | current-density ratio of the Vdsat-tracking cascode-bias diodes |
| knee | SR below which in-loop INL rises sharply (OTA1 10.23–10.28 V/µs, D44) |
| lf (lf_gain) | input-referral gain of slow errors (≈ 1 for bottom-plate SC; 9.3 pessimistic bound) |
| lpool | load-adaptive job pool on the sandbox |
| O0 / O1 / O2 | solver-tolerance ladder levels (D43c) |
| pair / slot | a sub-conversion is a slot (N + 2 cycles); two slots with opposite chop sign form a pair |
| Ref A | independent cycle-level reference model of C9 (VPLAN §2.4) |
| spot run | design-note simulation, not a gate |
| sys chop | system chopping: input polarity swap between sub-conversions |
| tb7 / tb9 | C1 noise testbench / C1 CMFB transient testbench |
| tier 0/1/2/3 | Python model / behavioural SPICE / transistor / PEX |
| WO | work order (`work/v1-design/wo/`) |

## B. Decision index (D-number → one line; full text in `work/v1-design/DECISIONS.md`)

| D | One line |
|---|---|
| D1 | gated S → C → V flow, every check at every corner, Paul-Thomas method |
| D2 | "all corners" = 45 PVT + MC for tier 0 and every block; top at 5 extreme points, ≤ 2048-cycle windows |
| D3 | (superseded by D17) VREF 1.2 V provisional |
| D4 | (superseded by D18) OTA chop pending S2; system chop mandatory |
| D5 | input switch 3.3 V TG, bootstrap only if needed |
| D6 | (superseded by D14) PGA ×1/×2 in v1 |
| D7 | corner set of SPEC §6 |
| D8 | git init of the project |
| D9 | parallel file-disjoint WOs, path-limited commits |
| D10 | option B = c1 0.125, k 0.5, c2 0.5 (bit-identical to A) |
| D11 | non-decision review fixes applied to SPEC/PLAN |
| D12 | CM-rejecting input switching |
| D13 | 4 MHz is a fast / low-resolution mode; precision gated at 0.25–2 MHz |
| D14 | shared Cs, no PGA in v1 |
| D15 | OTA A0 ≥ 80 dB |
| D16 | S1 ran with separate caps; rerun with shared caps in S3 |
| D17 | VREF 2.048 V, c1 0.125, c2 0.5, k 0.5 (option B) |
| D18 | OTA chop kept as a config bit, always paired with system chop |
| D19 | review S1/S2 rules applied (C9 rules 7–12, OTA chop on OTA1 only) |
| D20 | drcfeol broken copy failing both Magic and KLayout FEOL accepted |
| D21 | Vos 9 mV budget; order 1 characterisation only; overload recovery |
| D22 | Cs 0.5 pF (Cint1 4 pF) |
| D23 | N 4096 for precision modes |
| D24 | ua3 = REF− Kelvin to sensor ground |
| D25 | Cs2 samples x1 in OTA1 hold; separate Ck2 on full VREF; board reference rules |
| D26 | S3 per-block table = review-corrected WO-05 |
| D27 | 0.25 MHz / 125 °C noise ≤ 3.0 µV accepted |
| D28 | (superseded) fast-mode GBW 20 MHz always on; fast INL targets |
| D29 | noise @ 240 SPS ≤ 5 µV |
| D30 | CMRR ≥ 100 dB sys-on |
| D31 | bias-boost config bit for fast mode |
| D32 | CMRR sys-off ≥ 60 dB, sys-on 120 dB goal |
| D33 | S4 CMRR term replaced by the D12 residual ε_eff; 132–152 dB withdrawn |
| D34 | do not freeze SR / CM / CMRR rows before WO-09 |
| D35 | provisional calls from WO-09 (ε_eff sign, pin CMRR form, per-side leakage) |
| D36 | ε_eff sign "−" confirmed; RSS combination; 61.5 dB |
| D37 | systematic ΔCp added linearly; leakage per vg node; fast INL provisional |
| D38 | sys-on metric floor was a model bug; Ck loading default; 240 SPS = N 1024 |
| D39 | SR rows 12.5 / 13.5 V/µs; fast option A gated on absolute boosted points; 0.25 MHz/N 4096 rated to 100 °C |
| D40 | 1.8 V input pairs with stress proof; SC CMFB |
| D41 | fast mode A′ (OTA2 ×2); constant-current bias requested |
| D42 | current-mode bandgap reference with 3-bit trim |
| D43 | step-settling gate; one switched bias leg; tier-1 convergence ladder |
| D44 | OTA1 SR stays 12.5 V/µs (22 % over knee) |
| D45 | digital conventions §3.7a (a)–(j) |
| D46 | (e)(g)(i) confirmed; 16-bit parallel readout; 200 µA = design budget; full freeze |
| D47 | no extra analog pin; volatile trim via config register; manual calibration |
| D48 | gate B authoritative, step tb report-only; 0.94 µV governs; status reports frame boost/trim |
| D49 | bias-readback oscillator conditional on area |
| D50 | SPEC v1 frozen; S → C gate passed |
| D51 | boost A0 floor from model scan; no gain boosters; gm first; P3–P5 accepted |
| D52 | CL-4 β1 ≥ 0.83; CL-5 3.3 V vg switches closed by default |
| D53 | CL-7 boost-toggle settling relaxed; CL-1b table-INL gate |
| D54 | OTA1 pair 120/0.5 (free GBW route) |
| D55 | (reverted by D58) m_plc L 4 with Cc 0.2 pF |
| D56 | per-mode broken copies (CL-1d); vbpc boost ×1.75/×1.4 (CL-8) |
| D57 | CMFB clamp start-up only; gate B load basis; OTA-chop mode characterisation only |
| D58 | references scaled + replica-fed cascode bias; D55 reverted |
| D59 | parallel unit-finger 1:8 references; K_P 12.5 base |
| D60 | ratio row info; I_REF_btp +1.9 %; CM amp (later replaced) |
| D61 | dual-path CMFB; larger reference area |
| D62 | (corrected by D63) tb9 authoritative, f_cm info |
| D63 | tb9 judged at sampling instants + CM-to-DM row |
| D64 | Cr 25 → 50 fF per side |
| D65 | knee-based SR floor (CL-9); CM-to-DM bound; TG start-up clamp |
| D66 | C9 contract: AMB-01…15 resolved (CL-12…CL-26) |
| D67 | debug y = DAC flop; controls active-high |
| D68 | start-up row relative + absolute |
| D69 | clamp broken copies on the DM diff-step row |
| D70 | rst_n release latency fixed (CL-27) |
| D71 | direct tier-0 noise path; reduce sink gm/I; tb7 fixes |
| D72 | acc1 14 b / acc2 25 b (later 24 b); STA proxy corner; macro rename; PnR run |
| D73 | trim ±19 % process-only; calibration lowest passing code + 2 |
| D74 | strobe in φS, capture on fs_tick; A_VT 12 total; set A′; HV pair; order 1 via int2 follower |
| D75 | C1 sink L 8 + noise row 390 µV; C3 offset from loop impact (60 mV) |
| D76 | model order-1 delay first; edge rate info; small Sg; power-up detector |
| D77 | acc2 24 b; 23 b mutant must REJECT |
| D78 | C4 logic isolation; Sg re-split; C6 ≈ 40 µs settle covered by the C9 hold |
| D79 | C9 first-PnR fixes, one change per run: ban clkdlybuf* from the resizer; register fs_tick one clk early (RTL, re-verified before PnR) |
| D80 | 1.8 V stress rule split: oxide pairs and Vds ≤ 1.98 V; junction reverse bias judged against the PDK junction rating with margin (CL-33) |
| D81 | C3 T5 kickback has margin by construction (2.7 mV worst without isolation vs 5 mV); a checker copy proves the row is live |
| D82 | vg leakage: derate the slowest mode at 125 °C (0.25 MHz N 1024 to ≤ 100 °C, N ≤ 256 at 125 °C); 20 pA ff/100 row still checked (CL-34) |
| D83 | 1.8 V stress limit 1.98 V applies sustained (> ~1 ns); short overshoot allowed up to 2.2 V for < 1 ns; checker copy required (CL-35) |
| D84 | C9: one more single-change PnR run, GRT_DESIGN_REPAIR_MAX_SLEW_PCT 10 → 30 after measuring estimated vs routed slew |
| D85 | VAPWR-good is a C9 counter: hold rstb 2^16 fs cycles after rst_n release AND bias_ok for 256 cycles; board asserts rst_n only after VAPWR is up (CL-36) |
| D86 | C9: max slew waived at the ss_100C_1v40 stand-in corner; slew margin 40 % and `bias_ok` in pin_order carried into the final PnR |
| D87 | C3 T8 bench basis: stress judged against an ideal 1.98 V pin (no bench-drop counting), on C4's real phiC edge, with x2 bounded by OTA2's range; rev f op/on keeper |
| D88 | C9 AMB-30: the bias count restarts on any low bias_ok sample until release (last 256 consecutive cycles); AMB-31: fs_clk toggles during the hold (CL-37) |
| D89 | C6 bias_ok start-up row redefined: settle to ±1 % after the final bias_ok rise, well inside the C9 hold; earlier pulses reported, not gated (CL-38) |
| D90 | D83 sustained limit gets a stated 1 mV numerical/leakage tolerance (judged ≤ 1.981 V); checker at 1.985 V must REJECT (CL-39) |

## C. Change-log index (SPEC post-freeze)

| CL | Row | Change (one line) | D |
|---|---|---|---|
| CL-1 | OTA1 A0 boost | boost A0 floor from model scan + gate B hot | D51 |
| CL-1b | OTA1 A0 / A(v) | boost gated by measured A(v)-table INL ≤ 3.33 ppm; precision A0 ≥ 80 dB + table gate at N 1024 and 4096 | D53 |
| CL-1c | broken copy | PMOS cascode D–S short for the INL gate | D55 |
| CL-1d | broken copies | per mode and corner; droop copy + known-answer table | D56 |
| CL-2 | Input CM / CMFB | Cs2 x1-side plates shorted; CM kick ≤ 10 mV | D51 |
| CL-3 | gate B corners | ss/125 and fs/125 boost added | D51 |
| CL-4 | β1 | ≥ 0.83 (Cp_vg ≤ 0.32 pF) | D51, D52 |
| CL-5 | OTA1 / C4 | 3.3 V vg chopper/island switches, closed by default | D52 |
| CL-6 | slew row | itemised real load stated (0.78 / 0.90 pF) | D52 |
| CL-7 | bias distribution | boost-toggle settling 0.1 % within ≈ 4 µs, toggle pair invalid | D53 |
| CL-8 | bias distribution | vbpc leg ×1.75 / ×1.4 | D56 |
| CL-9 | slew row | SR − 3σ ≥ 10.3 / 20.6 V/µs (knee-based) | D65 |
| CL-10 | CMFB row | ≤ 10 mV at the sampling instants | D63, D65 |
| CL-11 | CMFB row | start-up by 4 µs; CM-to-DM ≤ 0.256 µV | D65 |
| CL-12 | rd | clear guard on new-frame load | D66 |
| CL-13 | rd | post-load frame_ctr compare | D66 |
| CL-14 | config | write time = synchronised shadow update | D66 |
| CL-15 | config | fs_div change restarts the divider, no runt | D66 |
| CL-16 | config | fs_div 5–7 → 1; reserved bits ignored; effective changes only | D66 |
| CL-17 | rst_n | hold tag invalid = 1, status shows trim 100 | D66 |
| CL-18 | config | shift register cleared at rst_n and after cfg_ld | D66 |
| CL-19 | rst_n | divider held in reset, deterministic latency | D66 |
| CL-20 | pins | `ena` ignored | D66 |
| CL-21 | read | registered bus, ≤ 3 clk after addr | D66 |
| CL-22 | debug | free-running ≈ 50 % bit clock + qualifier | D66 |
| CL-23 | port contract | (replaced by CL-28) comparator sampled on the bit-clock fall | D66 |
| CL-24 | status | cfg_pending sampled post-latch | D66 |
| CL-25 | port contract | phase generator and chop edge placement in analog C4 | D66 |
| CL-26 | port contract | sequencer on a 1-clk fs_tick enable | D66 |
| CL-27 | rst_n / debug | release latency `div` clk after 2-FF sync; debug y rising edge | D70 |
| CL-28 | port contract | comp_in captured into the DAC flop on fs_tick; comp_s removed | D74 |
| CL-29 | accumulators | acc1 14 b, acc2 25 b (corrected by CL-32); macro rename | D72 |
| CL-30 | comparator offset | \|μ\| + 3σ ≤ 60 mV from loop impact | D75 |
| CL-31 | OTA1 thermal | v_vg ≤ 390 µV from the 1.2 µV direct-path share | D75 |
| CL-32 | accumulators | acc2 24 b; 23 b mutant REJECT | D77 |
| CL-33 | OTA1/OTA2 devices (row 99), every 1.8 V stress row | oxide pairs and Vds ≤ 1.98 V; junctions ≤ 4.95 V (PDK `_05v5` diodes, 5.5 V − 10 %) | D80 |
| CL-34 | virtual ground (row 113) | 0.25 MHz N 1024 rated to ≤ 100 °C; N ≤ 256 at 125 °C in 0.25 MHz mode; 20 pA ff/100 row kept | D82 |
| CL-35 | every 1.8 V stress row | 1.98 V applies sustained (> ~1 ns); overshoot cap 2.2 V for < 1 ns; live-rule checker copy | D83 |
| CL-36 | §3.8a rst_n, new input `bias_ok` | VAPWR-good hold: 2^16 fs cycles after release AND bias_ok high 256 cycles; slot-0 timing updated | D85 |
| CL-37 | §3.8a rst_n | bias_ok must be high for the last 256 consecutive cycles before release (count restarts on a drop); fs_clk toggles in the hold; slot-0 formula replaced | D88 |
| CL-38 | bias reference start-up row | from the final bias_ok rise, settle to ±1 % within 4.1 ms (0.25 × the 2^16-cycle hold at 4 MHz); earlier pulses reported only | D89 |
| CL-39 | every 1.8 V stress row | sustained level judged ≤ 1.981 V (1 mV tolerance), also the duration-limb threshold; checker at ~1.985 V must REJECT | D90 |

The stress limits in CL-33, CL-35 and CL-39 are project stress rules, not PDK ratings. They lie outside the SkyWater model-validity range (nfet/pfet_01v8 Vds and Vgs 0–1.95 V, nfet Vbs +0.3 to −1.95 V; III.3).

## D. Symbol table

| Symbol | Meaning | Value (where fixed) | Source |
|---|---|---|---|
| $u$ | normalised input, $V_{in}/V_\mathrm{REF}$ | usable ±0.9 | SPEC §2.1 |
| $y[n]$ | comparator / DAC bit | ±1 | — |
| $x_1, x_2$ | integrator states | peak 0.61 V/side (ideal); x2 ≈ 1.41 V diff with offset | S1; C3 §3.1b |
| $c_1, c_2, k$ | loop coefficients | 0.125, 0.5, 0.5 | D17 |
| $N$ | conversion cycles per slot | 64 / 256 / 1024 / 4096 | SPEC §1 |
| $f_s$ | modulator clock | 0.25–4 MHz, nominal 2 | SPEC §1 |
| $h, g, t_\mathrm{half}$ | half period, dead time, usable half | $0.5/f_s$, $0.025/f_s$, $0.45/f_s$ | SPEC "Clock" row |
| $V_\mathrm{REF}$ | reference | 2.048 V (ratiometric 1.0–2.048) | D17 |
| FSR | full-scale range (differential) | $2V_\mathrm{REF}$ = 4.096 V | SPEC §2.1 |
| $C_{s1}, C_{int1}$ | stage-1 caps | 0.5 pF, 4 pF | SPEC §3.4 |
| $C_{s2}, C_{int2}, C_{k2}$ | stage-2 caps | 0.5, 1, 0.25 pF | SPEC §3.4 |
| $\beta_1, \beta_2$ | feedback factors | ≥ 0.83 (0.846 design); ≥ 0.497 | CL-4; SPEC OTA2 row |
| $C_{p,vg}$ | virtual-ground parasitic per side | ≈ 0.23 pF (≤ 0.32) | C1 §2.2 |
| $C_L$ | OTA1 load basis | 1.4 pF (lump), 0.78 / 0.90 pF real | CL-6 |
| $A_0$ | OTA DC gain | ≥ 80 dB precision | D15 |
| SR | slew rate | design 12.5 / 25 V/µs; floor SR − 3σ ≥ 10.3 / 20.6 | CL-9 |
| $I_\mathrm{TAIL}$ | OTA1 tail current | 18.5 µA base, ×2 boost | C1 §2.1 |
| $I_\mathrm{SINK}/I_\mathrm{TAIL}$ | fold ratio | 1.35 | C1 §1.5 |
| $K_P, K_N$ | cascode-bias density ratios | 12.5 base / 7.14 boost; 8 | D59; CL-8 |
| $V_\mathrm{ICM}, V_\mathrm{OCM}$ | input / output CM | 1.20 V, 1.50 V | C1 §2.4–2.5 |
| $C_c, C_r, C_\mathrm{INT}$ | CMFB sense, refresh, slow-path caps | 0.1 pF, 50 fF, 2 pF | D58, D64, D61 |
| $f_{cm}, f_z$ | CM loop bandwidth, slow-path zero | info rows | D62, D63 |
| $v_{vg}$ | sampled OTA1 thermal noise at vg | ≤ 390 µV rms diff | CL-31 |
| $n_{ktc}$ | model kT/C output noise at 15 SPS, N 4096 | 0.559 µV (worst) | C1 §2.7a |
| $\varepsilon_{eff}$ | D12 CM→DM residual | 8.407e-4 (61.5 dB) | D36 |
| $\varepsilon_{dyn}, \varepsilon_{NL}$ | step-tb settling error, its nonlinear part | health 1e-4, watch 3e-7 | SPEC OTA1 GBW row |
| $A_{VT}, A_\beta$ | Pelgrom coefficients | 12 mV·µm (gating), 1 %·µm | C1 §2.11; D74 |
| $r$ | reset residue | ≤ 1e-4 | SPEC "Reset" row |
| $G_0$ | trim master units | 17 (code 100 = 21) | D73; C6 §3 |
| $I_0$ | bandgap branch current | $V_T\ln 8/R_1 + V_{EB1}/R_2$, ≈ 1.07 µA (1.0677 µA at tt/27 with R1 144.8 µm) | C6 §2; WO-55; WO-80 |
| acc1, acc2 | CoI accumulators | 14 b, 24 b on chip; 32 b on readout | CL-29, CL-32 |

## E. Gaps in this book's sourcing

These values are marked PENDING or "not found" above because no source read for this book (as of 2026-11-15) contained them:
- **C1:** the precision gate B O2 combines at ss/−40 and fs/125 (WO-76), and O2 at tt/27 and ss/125, which D43c asks for (O1 above gate/3) but no WO runs yet; a third solver point for the precision verdict; boost O2 at fs/125 and boost tt/27 and ss/125 on the WO-52 netlist; the WO-77 tb7 and op/AC mutant rerun; tb8/8b/10/12/13 results. The WO-76 per-part O1/O2 numbers quoted here for parts not in `results/wo76/README.md` come from the coordinator's note of 2026-11-15 and RESUME, not from a results file.
- **C3:** rev g (WO-88), the leak-path probe, T8 re-judged at D90, and T3 on rev f + kp2.
- **C4:** the gate verdicts from the WO-79 `pool2` and WO-85 pools; the ff/100 20 pA row.
- **C6:** the WO-87 transient rows under D89.
- **C9:** the last WO-83 job, F18/F19 at real widths, the final PnR on the D85/D88 RTL, LVS on that layout, the gate-level / SDF sim.
- **C2, C7, C8, C10:** any design numbers.
- **Any PEX number, and any layout area for the analog blocks.**

The book does not estimate them.

**Conflicts and stale text found in the sources** (the newer decision is used in the book):
- SPEC.md:18 and SPEC.md:25 give different labels for the 0.71 µV figure: it is the WO-04 ota+sys model value (D22), while kT/C-only at Cs 0.5 pF and 15 SPS is 0.556 µV (`s3_budget.md:31`). SPEC was not edited.
- `results/wo52/README.md` calls the 390 µV noise row "SPEC CL-30"; the SPEC change log has it as CL-31 (CL-30 is the comparator offset row). The book uses CL-31.
- WO-89 names `design/c9_digital/flow/HARDENING.md`; the file is `design/c9_digital/HARDENING.md`. Its WO-log section ends at WO-72: WO-73 and the D86 slew waiver (which D86 says is "recorded in HARDENING.md with the net list") are not there yet. This is an open conflict: D86 says the waiver is recorded in HARDENING.md, and HARDENING.md does not contain it. HARDENING.md was not edited for this book. The book takes WO-73 and D86 from `results/wo73/README.md` and DECISIONS.md.
- `STATE-2026-11-14.md` lists SPEC as "CL-1…CL-36" and DECISIONS as "D1–D86"; SPEC and DECISIONS now run to CL-39 and D90.
- C6 rstb hold: WO-55 proposed 128 fs cycles, D78 proposed 256 cycles (64 µs) after bias_ok; D85 / CL-36 / CL-37 replaced both with the 2^16-cycle VAPWR-good hold plus a 256-cycle bias run, and D89 / CL-38 gates the settle at 0.25 × the 2^16-cycle hold (4.1 ms at 4 MHz).
- The WO-86 T3 table labels its rev f numbers "abs(mu)+3s" 45.07 / 42.74 mV, while STATE-2026-11-14 quotes 44.9 mV for rev e; WO-86 gives 49.59 / 49.26 mV for rev e. The book uses WO-86.
- C9 cell counts use different bases: generic yosys (1068 → 1077 after D88, CL-37) versus LibreLane sky130 synthesis (860 in WO-58B). Only the generic count is quoted for the current RTL.
- `c9_seq.v` line 29 still calls the bias bit a sticky done flag; after D88 it clears on a low sample until release (WO-83 open item; RTL comment not edited by verification).
- **O2 trigger: gate/2 versus D43c.** WO-63 (and WO-31 before it) used a "gate/2" O2 trigger that is not in D48 or SPEC. D43c applies the O1/O2 ladder to every gated INL with less than 3× margin (gate/3: 0.444 ppm in precision, 1.667 ppm in boost). The book uses D43c. Under D43c the ss/−40 step from O1 1.706 to O2 0.160 ppm fails the convergence test; D43c is not amended and a third solver point is to be scheduled (coordinator answer Q3).
- **C4 20 pA row.** The 20 pA ff/100 limit sits below the 24.5 pA that the 0.2 V criterion allows (N 4096, 2.01 pF); origin to be traced (coordinator answer Q1).
- **Tile width.** HARD §2 measures 319.24 × 225.76 µm from the DIEAREA of `tt_analog_2x2_3v3.def` (TT tools version not recorded); the ttsky-sigma-delta frame (Paul Thomas) uses 334.88 µm and SPEC says about 334 µm. The book uses 319.24 µm; re-check against the template at C7.
- **Stress limits versus PDK.** The project stress rules (D80, D83, D90) are not PDK ratings and lie outside the SkyWater model-validity range; see III.3.
