# Bias reference: bandgap current reference with 3-bit trim, area and current check (2026-11-09)

Coordinator analysis, written for the user's call on D41(b). The only number here measured from a layout is the reference bandgap. Everything else is an estimate.

## 1. Evidence
- **Reference bandgap on TT sky130.** `repos/sd-analog/tt_sky26a_analog_prj`, cell `bgr3v3_v2` (submitted to TTSKY26a; no silicon data seen).
  - Layout bounding box, from `design/layout/bgr3v3_v2.mag` (magscale 1/2) with subcell boxes: **66.9 × 94.2 µm ≈ 6,300 µm²**.
  - Contents: 12 `pnp_05v5_W3p40L3p40` (including dummies), 39 xhrpoly 0.35 µm resistors, about 30 thick-oxide MOS (amplifier and start-up), 1 MIM compensation cap.
  - Its own spec: VREF 1.116–1.217 V over corners (±4.4 %); TC between −80 and +440 µV/°C.
- **sky130 xhrpoly (`res_xhigh_po`), from PDK model files:**
  - 2000 Ω/sq;
  - corners ±15 % (`var_mult` ±0.15 in `r+c/res_{high,low}*`);
  - mismatch σ 2.5 %;
  - tc1 −1470 ppm/K, tc2 +2.7 ppm/K².
  - Relative to 27 °C, R is about −12 % at 125 °C and +11 % at −40 °C.

## 2. Why the trim is needed (current budget)
The bias current is V/R, so it follows R's ±15 % process spread. The bandgap voltage adds about ±4 %. Temperature drift can be nulled to first order by the PTAT/CTAT mix in a current-mode bandgap; a residual of about ±3 % is assumed. That gives about ±20 % total (worst-case linear sum).

The figures below scale the whole fast-mode estimate (172 µA, REVIEW-S5f A′) plus about 6 µA for the bandgap's own current:

| Scheme | Design rule | Fast mode, worst corner |
|---|---|---|
| No trim | nominal = min/0.8 so the low corner meets SR; high corner = 1.5 × min | ≈ 1.5 × 178 ≈ **265 µA, over 200 µA** |
| **3-bit trim over ±20 %** | step ≈ 5.7 %, residual ±2.9 % | ≈ 178 × 1.06 ≈ **189 µA, under 200 µA** (≈ 5 % headroom) |
| Precision mode, with trim | | ≈ 106–113 µA |

Without trim the 200 µA cap only holds by dropping or shrinking the fast-mode boost. Constant-gm has the same R dependence, so it doesn't avoid this.

## 3. Area roll-up for the 2×2 tile (334 × 225 µm ≈ 75,000 µm²)
"Analog raw" is the device-level estimate. Guard rings and routing are taken as ×1.4 on analog. The digital figures already include routing.

| Block | Raw low–high (µm²) | Source |
|---|---|---|
| MIM signal caps (Cs, Cint, Ck, both stages, diff) | 9,000 | SPEC §3.4 |
| SC CMFB caps (≈ 0.8 pF total) | 800 | estimate, 2 fF/µm² + overhead |
| 2 OTAs, 1.8 V pairs + protection cascodes (OTA1 W ≈ 30 µm, OTA2 ≈ 20 µm at L 1) | 6,000–8,000 | SIZING §4, REVIEW-S5f Q2 |
| Comparator, switches, non-overlap clock, choppers, level shifters | 3,000–4,000 | SIZING §4 |
| Bias distribution (mirrors, boost legs) | 1,500–2,000 | estimate |
| **Bandgap current reference** | **4,000–7,000** | reference cell 6,300 |
| **3-bit trim** (3 binary mirror legs + switches, 3 config FFs + 3 level shifters) | **500–1,000** | estimate |
| Decaps (MOS, partly under MIM) | 5,000 | SIZING §4 |
| Analog subtotal × 1.4 | 41,700–51,500 | |
| Digital (CoI accumulators, counter, config, shift-out) | 8,000–15,000 | SIZING §4 |
| **Total with bandgap + trim** | **≈ 50,000–67,000 (66–89 % of tile)** | |
| Total without them (simple bias) | ≈ 43,000–56,000 (58–75 %) | |

The increment is about **+6,000 to +11,000 µm² including overhead (8–15 % of the tile)**. It fits.

At the high end the tile is about 89 % full, which is tight for hand-made analog layout. Mitigations, if needed:
- MOS decaps under the MIM arrays (≈ −3,000 to −5,000);
- a smaller bandgap than the reference, without an internal amplifier (a current-mode cell with mirrors, ≈ 4,000);
- on-chip averaging kept off-chip (SIZING §9).

No extra pin is needed.

## 4. Risks and checks
- **New block (C6).** It needs its own corner and mismatch checks, a start-up check (power-up from 0 V at ss/−40/3.0 must always start; a broken copy without start-up must hang), PSRR, and a trim-monotonicity check (every code step > 0, range covers ±20 %).
- **Finding the trim code on silicon** without a bias-monitor pin:
  - sweep the code and pick the lowest one that meets the SR knee / INL test; or
  - measure the analog supply current per code, if the board allows it.
  - A monitor pin would be the 5th analog pin, at €100 (the first two cost €40 each, then €100 each). Not planned: the user ruled out extra analog pins (D47).
- **Code default at reset:** mid-scale (100), latched only at a pair boundary, like the boost bit (C9).
- The reference bandgap has no silicon data here. Treat its area as an order-of-magnitude anchor, not a proven cell.

## 5. Reading
A bandgap current reference with a 3-bit trim costs about 8–15 % of the tile and keeps fast mode inside 200 µA at every corner (≈ 189 µA worst). The total stays at 66–89 % of the 2×2 area. Without trim, the 200 µA cap fails by about 65 µA at the high-current corner.
