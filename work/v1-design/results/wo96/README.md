# WO-96: tile floorplan and first layout cells (pd-expert, 2026-11-21)

Inputs: commits f25358d → 17ed32a → 5d9aac5 → **e9fa31f (final run)**. Frozen run: `/home/mempool/regr/tt/WO-96-e9fa31f/`
(`out/summary.txt`, per-cell `ver_*.log`, `kl_*.log`, `*.lyrdb`, `lvs_*.out`). Harness: `design/layout/scripts/run.sh`.
Tools: IIC-OSIC-TOOLS 2026.10, magic 8.3.685, klayout (image), netgen (image), TT-pinned sky130A (`/foss/pdks-tt`).
KLayout deck = PDK `sky130A_mr.drc` (feol, beol, offgrid); the TT precheck uses its own copy of the decks (not run here).

## Verdict: NOT DONE. One cell (MIM) is DRC- and LVS-clean. The floorplan does not close: OTA2 has no slot.

## Floorplan (`design/layout/frame/floorplan.tcl`, Magic, from the template DEF; the macro is placed from the WO-97 LEF)
C9 sits at the top left at (4, 72), mirrored. Mirroring turns its north pin order (clk … uio_out) into the TT pad order
(uio_out … clk), so no crossing channel is needed. The south-edge analog pins face the bottom strip.
Straps are met4 and run the full height: VDPWR x 196.5, VGND x 200.5 and 305.5, VAPWR x 311.
Analog areas: the right column x 205–303 (OTA1 at the bottom, MIM1 and MIM2 above it) and the bottom strip
y 3–69 (C6, input switches next to ua0–ua3, C3, C4).

| Slot | slot µm² | need µm² | Status |
|---|---|---|---|
| C9 macro | 28,500 | 28,500 | placed (LEF) |
| OTA1 | 10,388 | 9,100–13,100 (WO-93) | fits only at the low estimate |
| MIM1 Cs1/Cint1 | 6,762 | 5,700–8,800 (MIM2-style routing: about 12,800) | fits only at the low estimate |
| MIM2 Cs2/Cint2/Ck2 | 3,920 | measured cell 5,706 | **does not fit** at the current routing density |
| C6 bias | 4,620 | 5,800–7,000 | **does not fit** |
| SW in/ref, C3, C4 | 1,750 / 2,730 / 3,102 | 1–2k / 1.5–3k / 2–4k | fit only at the low estimate |
| OTA2 (D91, 9/16 OTA1) | 0 | 5,350–7,450 (WO-93) | **no slot** |
| Total | 61,772 (85.7 %) | 60,750–79,150 = 84–110 % of the tile | before routing and guard rings |

Options for the user (not decided here): (1) put the MIM over active circuits (OTA and C6), which costs met3/met4
routing over those blocks; (2) a smaller Cint1 (a spec change); (3) a smaller C9 die (utilisation is already about
0.70); (4) an OTA2 below 9/16 of OTA1 (revisits D91). Digital-to-analog distance: the OTA1 slot is 10 µm from the
macro's east edge, with the straps in between. That spacing is weak isolation.

## Cells (final run e9fa31f)
| Cell | Area (bbox) | Magic DRC | KLayout DRC | LVS (netgen, sky130A_setup) | Broken copies |
|---|---|---|---|---|---|
| `mim_u250` 0.25 pF unit (11×11 capm) | 135 µm² | 0 | 0 | — | — |
| `mim_s2` 4×4 common centroid (Cs2±, Cint2±, Ck2±, 2 dummies) | 82.75×68.95 = 5,706 µm² | 0 | 0 | **PASS** (match uniquely, no property errors) | sliver: DRC 1/1 ✓; short cs2p_t–cs2n_t: LVS fail ✓; reference with one unit missing: fail ✓ |
| `c6_res` R1 144.8, R2a/R2b 354.76 µm, 0p69 xhrpoly (unwired) | 4,544 µm² (loose) | **15 (rpm.1)** | **4 (urpm.1a)** | netlists match (1 symmetry), no property errors; harness verdict mis-reads it as FAIL (regex, open) | R1 +10 % reference: property error ✓; sliver: DRC +1 ✓ |
| `c4_sw` sg 5/0.5, sin 12/36 HV FETs + lsbuflv2hv_clkiso_hlkg_3 (unwired) | 3,921 µm² (loose) | 0 | 0 | **NOT RUN**: magic stops after extracting the LS cell; there is no c4_sw.ext | sliver: DRC 1/1 ✓ |

C6 extracted lengths are 144.81 / 355.04 µm (+0.007 / +0.078 %). Netgen's l/w tolerance is 1 % (setup.tcl:54), so
LVS cannot catch errors below 1 %; the R2/R1 ratio is fixed by drawing, not by LVS. The netgen sky130A setup merges
parallel MIM units, so a missing unit shows up only as a property error. The harness gate therefore requires
"no property errors".

## Findings
- Fatal until fixed: the C6 xhrpoly snake from the gencell fails rpm.1/urpm.1a in both decks. Fix: per-segment
  nx=1 resistors joined in met1, or gencell end/marker params. Check against the 1p41 path that Paul used.
- MIM2 routing overhead is 2.9× the capm area (one gap per column, 13 nets). It needs shared gaps and narrower track
  pitch before stage 1 (36 units) can fit 6.8k.
- C4 delay caps (14 caps, 0.92 pF total, in the netlist) and the hvl logic (3,258 µm² incl. ×1.3) need a layout form.
  The project rule bars MOS caps only in the signal path. Whether MOS caps are allowed here is a user decision.
- Area estimator: the C3 netlist parse found 0 devices, so that row is unknown. The OTA1 footprint is 9,091 µm²
  (K 2–3 gives 18–27k, above WO-93's 9.1–13.1k; WO-93 is the reference).
- The floorplan has 2 Magic nwell.4 errors after the LEF macro is placed. The source is not root-caused (likely the
  abstract). There is no floorplan GDS yet, because the LEF abstract has no GDS.
- Path correction: the WO-97 LEF is at `WO-97-6b474df/design/c9_digital/flow/runs/pnr1/61-magic-writelef/`, not `runs/pnr1/final/`.

## Pickup / next-cell plan
D2 (11-22): C6 rpm fix; C4 extraction crash (try `extract all` without the hvl subcell, or flatten);
LVS regex (`run.sh` lvs(): accept "match with N symmetries"); TG wiring; denser MIM routing, then the MIM1 array.
D3: C3 StrongARM (common-centroid HV input pair, dummies). D4: OTA1 (decide the fallback at D4–D5).
D5: OTA2. D6: C6 complete (pnp 3×3 + ring). D7: top assembly, power, tie-offs for unused outputs.
D8: tile DRC/LVS. D9: PEX spot. D10: TT precheck.
Risks: the area does not close (see the options above); agent-drawn analog layout in 8 days; the reference decks
differ from the precheck decks; LVS of unwired cells checks device parameters only.
