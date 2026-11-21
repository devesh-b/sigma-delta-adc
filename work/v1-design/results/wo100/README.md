# WO-100: D93/D94 floorplan, WO-96 blockers, MIM1 array (pd-expert, 2026-11-21)

Commits a3e721f → 2db06b1 → **0814947 (final run)**. Frozen run: `/home/mempool/regr/tt/WO-100-0814947/out/` (`summary.txt`,
`ver_*.log`, `*.lyrdb`, `lvs_*.out`). Earlier runs: `WO-100-a3e721f`, `WO-100-2db06b1`. Probes: `WO-100-probe/`.
Harness: `design/layout/scripts/run.sh`. Tools as WO-96 (magic 8.3.685, image klayout/netgen, TT-pinned sky130A).
DRC deck: PDK `sky130A_mr.drc` (feol, beol, offgrid; floating_metal off). The TT precheck deck was **not** run (item 5 open).

## Verdict: PARTIAL. Floorplan closes at the low estimate only. Blockers a, c, d fixed; b fixed for extraction, LVS still fails. Comparator not started.

## Floorplan (D93 MIM over circuits, D94 C9 stays 190 × 150)
C9 at (4, 72), mirrored. Digital straps at x 195.5 / 198.5. A p+ tap guard ring (L-shape) runs at x 204.5 and y 64.
The analog column starts at x 209, which is **15 µm** from the macro (WO-96: 10 µm, no ring).

| Slot | µm² | need lo–hi | Status |
|---|---|---|---|
| C9 | 28,500 | 28,500 | placed (GDS; check cell `c9_place`) |
| OTA1 (209–303 × 3–112) | 10,246 | 9,100–13,100 | low estimate only |
| OTA2 (× 114–182) | 6,392 | 5,350–7,450 | low/mid |
| C3 (× 184–222, next to OTA2 out and C9) | 3,572 | 1,500–3,000 | fits |
| SW in/ref (3–39 × 3–62) | 2,124 | 1,000–2,000 | fits |
| C4 (41–101) | 3,540 | 3,400–4,600 (MOS caps) | low only |
| C6 (103–203.5) | 5,930 | 5,800–7,000 (WO-96 estimate; the resistors are now 1,533, so this is likely high) | low only |
| MIM1 over OTA1 (rot90) / MIM2 over OTA2 | 9,471 (106 × 89.35) / 5,213 (75.6 × 69) | — | fit when rotated / fit |
| Circuits total | 60,304 = 83.7 % | 54,650–65,650 = 75.8–91.1 % | short by **5,350 µm² (7.4 % of the tile)** at the high estimate, before routing |

Notes: MIM1 is 106 µm wide against the 94 µm column, so it fits only rotated 90° (89 × 106). Under D93, circuits beneath
the MIM may route only in li/met1, because met2 is the shield. A 175-wide C9 would give the column +15 µm × 219 ≈ 3,300 µm².

## Cells (final run 0814947)
| Cell | bbox | Magic | KLayout | LVS | Broken copies (fail as required) |
|---|---|---|---|---|---|
| tt_um_sd_adc_fp (frame, ring, straps) | 319.24 × 225.76 | 0 | 0 | — | — |
| c9_place (WO-97 GDS, mirrored) | 190 × 150 | **512 (open, see below)** | 0 | — | — |
| mim_s2 (shared-gap router) | 75.6 × 68.95 = 5,213 (was 5,706) | 0 | 0 | PASS | drcbad 1/1, short FAIL, ref −1 unit FAIL |
| mim_s1 36 u CC (Cs1 2 u, Cint1 16 u per side) | 106 × 89.35 = 9,471 | 0 | 0 | PASS | drcbad 1/1, short FAIL, ref −1 unit FAIL |
| c6_res: R1 4 legs × 36.2, R2a/b 10 × 35.475, met1 series | 37.6 × 40.8 = 1,533 (was 4,544) | 0 (was 15) | 0 (was 4) | PASS | drcbad 1/1, open strap FAIL, R1 +10 % ref FAIL |
| c4_sw (LS from GDS) | 100.5 × 39 | 0 | 0 | **FAIL: port errors** | drcbad 1/1 |

## Blockers (item 2)
- (a) rpm.1/urpm.1a: a lone nx=1 0p69 gencell also fails (its marker is 0.69 wide), and so does snake 1. **nx ≥ 2, snake 0,
  guard 0** is clean in both decks (`WO-100-probe/probe2.log`). Legs are joined in met1, and netgen merges the series
  legs (l add). **Design impact:** each leg adds two head contacts, so the absolute R1 and R2 rise compared with one
  long device. The C6 owner (WO-99) must re-simulate with 4 + 10 + 10 segments. The ratio is nearly preserved
  (head count over length: 0.0553 vs 0.0564 per µm).
- (b) c4: the hvl `.mag` view is an abstract, and magic dumped core while extracting it. The library GDS is now read
  first, and extraction completes. LVS still fails: the GDS LS has split rails (VPWR/VPWR_uq0, VGND/VGND_uq0) that
  must be strapped at block level. TG wiring is not done.
- (c) LVS verdict: it now uses `Final result: Circuits match uniquely.` and requires no property, mismatch or
  pin-failure lines. The C6 reference got ports (a portless subckt let netgen merge devices 3→1).
- (d) nwell.4: the source was LEF `OBS nwell` (sd_adc_c9.lef:416) painted as real nwell. The frame no longer
  places the LEF. The macro GDS needs `gds readonly true`. Without it, magic regenerated the hd implants and KLayout
  reported 217 items (hvtp.2 177, psdm.1 29, …) that came from magic's re-write, not from the macro.
  Open: magic reports 512 on `c9_place` and `ver_c9_place.log` also says "No errors found", which is not explained.
  The KLayout control run on the source GDS produced no report (wrong topcell name?), so it is unknown.

## Not done
Item 3: TG wiring. Item 4: comparator (44 devices, rev g, `netlist.py` output checked). Item 5: precheck deck.

## Pickup / next-cell plan
1. C4: strap the LS split rails in c4_sw, add pins, then TG wiring. Gate: LVS PASS plus broken copies.
2. C3 rev g: HV pair M1/M2 as 8 × W5 unit fingers, ABBA ABBA with end dummies; K1/K2 and T in the same row pitch;
   a mirror-symmetric latch row (M3–M6, R0–R3, KPo/KPn 0.84/0.15, RSO 1.0/0.3); then the buffers and the SR latch.
   LVS against `python3 design/c3_comp/netlist.py` (ports inp inn clk q qb vdd vss). Broken copies: pair finger swap
   (must fail), KP W changed in the reference.
3. Root-cause the 512 magic count on c9_place and fix the c9_orig control topcell. Then run the TT precheck deck.
4. C6 re-sim with the segmented resistors (WO-99). OTA1 layout D4.

D4–D5 fallback assessment: the passive arrays (MIM1, MIM2, C6 resistors) are DRC/LVS clean. No active cell is
LVS-clean yet, and no OTA or comparator has been drawn. With 9 days left, the risk is high. One option for the user:
reuse proven layout for the comparator/OTA (ttsky-sigma-delta) as a fallback if C3 is not LVS-clean by D4.
