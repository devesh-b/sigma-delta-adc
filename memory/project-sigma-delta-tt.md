---
name: project-sigma-delta-tt
description: User's project goal — learn by designing a sigma-delta ADC with better specs on Tiny Tapeout sky130
metadata:
  type: project
---

The user wants to design a sigma-delta ADC on Tiny Tapeout (sky130A PDK). This is **a learning project, not a competition**. Don't frame prior TT projects as "competition".

The focus is sigma-delta ADCs with **better specs** than prior TT designs. As of 2026-11-07, every prior analog ΣΔ modulator on sky130 is 1st order and none has an on-chip decimator. The candidate improvements are 2nd order or higher, on-chip CIC/sinc³, fully differential SC, multi-bit with DEM, and incremental ΣΔ.

**Case study target: Microchip MCP3421** (18-bit incremental-style ΔΣ, 3.75–240 SPS, 1.5 µV rms, 10 ppm INL, 2.048 V ref, PGA x1–8, I²C). Analysis and spec tiers are in `MCP3421_TARGET.md`. The proposed realistic v1 (not yet confirmed by the user) is a differential chopped SC incremental ΣΔ with an on-chip decimator, aiming for ~14 ENOB at 15 SPS.

The draft direction (2026-11-07) is in `ROADMAP.md`. It is a configurable "experiment chip": a ~1 MHz SC, fully differential, chopped incremental ΣΔ with 1st/2nd-order and chop on/off selectable, an on-chip CoI decimator, and a raw bitstream pin. The aim is open research publishing measured-vs-sim correlation and datasets. It differentiates from Paul Thomas on resolution and DC precision, not bandwidth. Phases 0–5, ~20 weeks. The next sky130 shuttle deadline is unknown; check tinytapeout.com/runs.

The user prioritises **first-cut silicon success** over heroics: no MOS caps in the signal path (they're too much sim effort and nonlinear); use MIM (cap_mim_m3_1; met5 MIM is forbidden). Target speed is MCP3421-like (3.75–240 SPS) with the best possible precision. Sizing analysis is in `SIZING.md`: Cs 0.5–1 pF is enough because oversampling averages kT/C; 2x2 tile; the main challenges are 1/f/offset and OTA gain, not cap area.

Key evidence (`ACHIEVABILITY.md`): Paul measured sky130 OTA 1/f corner at ~631 kHz (6.9 nV/√Hz white). The Phase-1 model (`model/`, 2026-11-07) puts unchopped DC noise at ~7–12 µV (slow errors refer with gain ≈1 in bottom-plate SC). System chopping (input swap per sub-conversion) gives ~0.3–4 µV; intrinsic floor only. Model choices: c1=0.25 c2=0.5 k=1; order 2 gives ≈2·log2(N)−4 bits; INL is set by swing-dependent OTA gain (≈72 dB for ≤100 ppm, ≥90 dB for ~20 ppm); settling gives only gain error. The candidate v1 point is fs=2 MHz, N=1024, Cs=1 pF. The critical path is a fully-diff OTA with CMFB (no TT precedent). ngspice long transients failed for TilesOS. No TT ΣΔ has silicon results yet.

**Update 2026-11-07b:** `SPEC.md` (authoritative design spec, corner set §6) and `PUBLICATION_PLAN.md` (framing A: method + measured-vs-model) exist and were reviewed/fixed (VREF 1.2 V provisional pending study S1 since the model ran at 2.048 V; PGA x1/x2 v1; TG input switch; GBW ≥10 MHz req / 20 target; raw accumulator output; CJC off-chip; entropy section optional). The user chose a **gated flow like Paul Thomas**: system → component → verification suite, and proceed to the next stage **only if every spec passes at every corner**. Plan: `work/v1-design/PLAN.md` (RESUME HERE).

**Why:** It's a learning exercise in mixed-signal design on an open PDK.
**How to apply:** Frame suggestions as learning steps (theory → behavioral sim → schematic → layout). Point to the reference repos under `repos/` and the survey in `NOTES.md`. See [[reference-tt-workspace]].
