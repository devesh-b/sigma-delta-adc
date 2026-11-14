# Proposal draft: a second-order incremental ΣΔ ADC with on-tile decimation for sky130

*Draft, 2026-11-15. A starting point to edit. Every number comes from `DESIGN_BOOK.md` (section references in brackets). Items marked PENDING are not final and should stay worded as in-progress.*

**Author / team:** _[fill in]_  **Target:** sky130A, Tiny Tapeout 2×2 analog tile  **License:** _[fill in]_

## 1. Summary

We propose an open-source precision ADC block for sky130: a second-order, 1-bit, discrete-time **incremental** ΣΔ modulator with its decimating accumulators hardened in the same analog tile. It targets DC measurement, such as sensors, bridges and thermocouples, using the Microchip MCP3421 as the reference point for specifications. It is designed for an external ratiometric 2.048 V reference [II.1, II.2].

Earlier analog ΣΔ designs on Tiny Tapeout sky130 that we found are all first-order and have no on-chip decimation. This design moves the open-silicon state of the art up one loop order and adds conversion-ready digital output on the tile [Proposal summary].

## 2. Architecture

- **Loop:** a fully differential switched-capacitor CIFB loop. Coefficients c1 0.125, c2 0.5 and k 0.5; Cs 0.5 pF, Cint1 4 pF; 1-bit quantiser [II.2.3, II.2.5].
- **Incremental operation:** the loop is reset for every conversion. N = 64 / 256 / 1024 / 4096 cycles trades rate for resolution. The reconstruction formula from the two accumulators is exact, and the residual quantisation error falls as 1/N² [I.5].
- **Clocking:** fs 0.25–2 MHz in precision mode and 4 MHz in fast mode with bias boost [II.2.6, II.2.7].
- **Accuracy features:** system chopping (polarity-swapped sub-conversion pairs) with optional OTA1 chopping, and common-mode-rejecting input switching by top-plate shorting [II.2.8, II.2.10].
- **Blocks:**
  - folded-cascode OTA1 with switched-capacitor CMFB plus a slow integrating CMFB path;
  - OTA2;
  - latched comparator;
  - switches, non-overlapping phase generator and level shifters;
  - trimmable bias reference with a bias-good signal;
  - a hardened digital macro holding the 2nd-order cascade-of-integrators accumulators, sequencer, configuration register, a VAPWR-good reset hold and a 16-bit read bus [III].
- **Firmware:** final scaling and chop demodulation run in firmware [SPEC §3.7].

## 3. Target specifications

| Parameter | Target | MCP3421 (reference) |
|---|---|---|
| Noise | ≤ 2.5 µV rms @ 15 SPS; ≤ 5 µV @ 240 SPS | 1.5 µV rms @ 3.75 SPS |
| INL (precision modes) | ≤ 20 ppm FSR | 10 ppm typ |
| Offset / gain error | ≤ 5 µV / ≤ 0.5 % (ratiometric) | 15 µV / 0.05 % (internal reference included) |
| CMRR | ≥ 100 dB with system chop | 105–110 dB |
| Analog supply current | ≤ 200 µA budget (analog only) | 145 µA whole chip |
| Digital power | ≈ 1.7 mW estimate (not comparable as a total) | included above |

Our behavioural model gives an intrinsic floor of 0.94 µV and 3.4 ppm. These are model numbers that exclude reference, board, coupling and layout effects, not silicon predictions. We do not claim parity with the MCP3421 [Proposal summary; V.4].

## 4. What is new

From a keyword survey of 29 Tiny Tapeout shuttles up to ttsky26c (2026-11-07):
- **Second order.** All three analog ΣΔ modulators found on TT sky130 (Paul Thomas, tilesos, shimomi) are first order.
- **Incremental conversion**, with independent conversions and a selectable N.
- **Decimating accumulators in the same analog tile.** To our knowledge this is the first analog ΣΔ modulator on TT sky130 with its CoI accumulators hardened in the same analog tile. TT does have digital-only decimators.
- **Chopping and CM-rejecting switching** aimed at µV-level DC accuracy [Proposal summary].

## 5. Design and verification method

The flow is gated: system → block → top. Each stage has written gates taken from a frozen specification, evaluated at all PVT corners plus Monte Carlo as the plan [IV.1, D2]. Every gate prints ACCEPT/REJECT and fails on missing data. Each gate is meant to have a deliberately **broken copy** that must REJECT, so that a passing check is shown to be able to fail [IV.3].

Tiers:
- a Python behavioural model;
- behavioural SPICE;
- transistor blocks inside the loop, where the authoritative OTA check is in-loop INL;
- later, post-layout extraction.

The digital macro has an independent bench with:
- its own reference model;
- golden vectors;
- mutation testing;
- formal properties;
- multi-corner static timing after LibreLane place-and-route [III.6].

All design decisions and specification changes are logged with reasons (D1–D90, CL-1–CL-39).

## 6. Status (2026-11-15)

- **Specification:** frozen, with a controlled change log.
- **OTA1:** at transistor level. Boost-mode in-loop INL passes at the corners run so far, at the first solver level. Precision mode at ss/−40 is **PENDING** a solver-convergence check [III.1.8a].
- **Comparator:** rev f. One device-stress overshoot item is open (rev g PENDING) [III.3].
- **Switches/phases:** reruns PENDING. **Bias reference:** DC rows pass at 5 corners; transient rows PENDING [III.4, III.5].
- **Digital macro:** RTL verified on the bench. A pre-final place-and-route meets setup and hold at 12 corners. The final place-and-route with LVS is **PENDING** [III.6].
- **Not started:** OTA2, top-level integration, analog layout and extraction.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Tile area: about 62 % of the tile is committed before most analog layout | Early floorplan; digital macro die-shrink option; capacitor sizing review |
| Digital-to-analog coupling in a shared tile | Separation by placement, guard rings, quiet sampling instants; measure on silicon |
| Fast-mode current margin about 1 % to budget | Bias-boost trim; mode-dependent biasing; confirm once OTA2 exists |
| Solver-accuracy uncertainty in in-loop INL | Convergence ladder per a written rule before any verdict |
| Device stress at fast edges | Project stress rules (stricter than a single peak value) with checker copies. Note: sky130 1.8 V model validity is documented to 1.95 V |

## 8. Deliverables and silicon characterisation

**Deliverables:**
- open-source schematics, netlists and layout;
- the hardened digital macro;
- all benches and checker scripts;
- the behavioural model;
- the design book;
- a firmware reference decoder.

**Silicon measurements:**
- noise versus N and fs;
- INL against a precision source;
- offset and gain with chop on and off;
- CMRR;
- supply current per mode;
- trim and calibration;
- start-up behaviour;
- the high-temperature derating of the slowest mode.

Measuring at µV level needs an external low-noise source and reference board, and a host that is fast enough for fast mode [Proposal summary].

## 9. Requested support

_[Fill in: e.g. silicon slot, measurement equipment, review time, mentoring.]_
