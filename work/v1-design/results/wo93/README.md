# WO-93 (C2): OTA2 as an OTA1-cell reuse, area and current overshoot. 2026-11-21

Hand analysis only, built on existing C1 data. No sims were run, so there is no frozen copy.
Sources:
- C1 `DESIGN.md` §2.1–2.9 and §2.7a: the OTA1 SIM tables (A0, GBW, PM, fp2 and Vdsat over 9 corners × 2 modes) and the WO-43 boost span of 1.43 V.
- `design/c1_ota1/sizes_draft.py`: the WO-52 netlist sizes.
- DESIGN_BOOK III.1.9 and III.2, and the Proposal-summary area/power table.
- SPEC §3.0: the OTA2, offset, CMFB, current and comparator kickback rows.

No SPEC row or device size was changed. Labels: HAND = derived here; SIM = taken from an existing run.

## 1. OTA2 requirements (SPEC §3.0, III.2)
| item | value |
|---|---|
| x2 peak | ≈ 1.41 V diff for any \|Vos\| ≤ 90 mV (C3 §3.1b). Needs A ≥ 75 dB up to 1.4 V (row 91); the boost span is checked against 1.41 V |
| β2 / Cp_vg2 | β2 ≥ 0.497 ⇔ Cp_vg2 ≤ 0.262 pF per side. Feedback network: Cs2 0.5 pF, Ck2 0.25 pF, Cint2 1 pF |
| load | C_L ≈ 0.7 pF per side. HAND itemisation: feedback series 1·1.012/2.012 = 0.50 pF, Cc/Cr 0.125 pF, junctions/routing/comparator input ≈ 0.07 pF |
| speed, 2 MHz | loaded GBW ≥ 10 MHz (15 MHz target), SR ≥ 13.5 V/µs. Step gate: ε_dyn on the 1.12 V worst step ≤ 1.4e-3 |
| speed, 4 MHz boost | GBW ≥ 22.5 MHz, SR ≥ 27 V/µs (tail ×2, A′ D41). ε_dyn ≤ 6e-4 |
| A0 | ≥ 75 dB (WO-93 item list); A(v) ≥ 75 dB for \|v\| ≤ 1.4 V |
| CM | comparator kick 38.9–47.4 mV per fire edge (C3 rev f/g). CMFB must bring CM within 10 mV by the sampling instant |
| offset | ≤ 9 mV 3σ |
| noise | OTA2 noise is divided by integrator-1 gain (c1(N−1)/2 ≈ 256 at N 4096): negligible against the 2.5 µV row |

## 2. OTA1 cell as-is in the OTA2 slot (HAND on OTA1 SIM data)
The rows below use three rules:
- The fold pole (fp2), A0 and swing do not depend on the load.
- GBW scales with 1.4/0.7 = 2×, because the OTA1 SIM C_L is 1.4 pF.
- SR = I_TAIL/C_L, the SPEC tier-1 definition.

The closed-loop crossover is β·GBW. β2/C_L2 = 0.71 against β1/C_L1 = 0.60, so the crossover is 1.18× the one in the OTA1 slot.

| row | requirement | as-is (worst corner) | margin |
|---|---|---|---|
| swing, base | 1.41 V diff | ≥ 1.8 V span (C1 run 4) | +0.39 V |
| **swing, boost** | 1.41 V diff | **1.43 V span** (WO-43, ss/125 boost) | **+0.02 V (1.4 %)** |
| A0 / A(v)min | ≥ 75 dB | A0 79.6–85.0 dB; A(v)min 73.6 dB at ss/125 boost (old K_P 5 table; the WO-43 span fix should lift it, re-check) | A0 +4.6 dB; A(v) to be re-checked hot boost |
| GBW base / boost | ≥ 10 / 22.5 MHz | 27–43 / 53–83 MHz | 2.7× / 2.4× |
| SR base / boost | ≥ 13.5 / 27 V/µs | 26.4 / 52.9 (trim floor −3 %: 25.6 / 51.3) | 1.9× |
| PM | 70–85° (info) | 90° − atan(1.18·tan(90° − PM1)), with PM1 77–82° ⇒ **≈ 75–81°** | inside the window |
| ε_dyn, 1.12 V step | 1.4e-3 / 6e-4 | slew 42 / 21 ns, then ≥ 15 τ linear ⇒ < 1e-6 | > 1000× |
| β2 | Cp_vg2 ≤ 0.262 pF | pair Cgg ≤ 189 fF + switches/routing/PEX ≈ 0.23 pF | 12 % |
| CM kick | ≤ 10 mV at the sample | f_cm ≈ 2 × 7 MHz (C_L halved); 47 mV·e^(−112.5 ns/11 ns) ≈ 0 mV | OK. Residual: during the kick, the low output dips ≈ 40 mV below the 0.79 V hot-boost bottom limit, which costs transient A until it recovers (C2 tb) |
| offset | ≤ 9 mV 3σ | 4.8 mV (C1 hand) | OK |

**Verdict:** every OTA2 performance row passes, most of them by about 2×. The OTA1 cell is oversized for this slot, with GBW and SR about twice what the rows need. The tight row is the boost swing, +0.02 V; it is the same cell and the same corner as OTA1.

## 3. Scaled variant B: "9/16 cell", bias nets shared with OTA1 (HAND)
**Scaling:**
- Tail, sinks and fixed loads go to 18 of 32 fingers; m_pc to 9; m_nc to 2 × 5.625; m_plc to 4 × 2.1; the pair to 70/0.5 (WF 10, M 7).
- The current density and L are unchanged. Vdsat, swing, K_P/K_N tracking, A0 and fp2 therefore stay as in OTA1.
- I_TAIL2 = 10.4 µA base and 20.8 µA boost.

**Shared bias:** the mirror gates tie to OTA1's btp/bn/bp/vbpc/vbnc/vbl0 nets, so OTA2 has no reference, replica or cascode-bias legs of its own. It keeps its own dual-path CMFB.

An exact ½ scale would give SR 13.2 V/µs, which is under the 13.5 V/µs row. The scale is 9/16 for that reason.

| row | B (worst corner) | vs row |
|---|---|---|
| SR base / boost | 14.9 / 29.7 V/µs (trim floor 14.4 / 28.9) | +7 % / +7 % |
| GBW base / boost | 0.5625 × 2 × OTA1 = 15.2–24.2 / 29.8–46.6 MHz | 1.5× / 1.3× |
| β2 | pair Cgg ≈ 0.11 pF ⇒ Cp ≈ 0.14 pF, β2 ≈ 0.53 | OK |
| ε_dyn | base: τ 19.8 ns, slew 55 ns, 8.6 τ ⇒ 4.8e-5. Boost: τ 10 ns, slew 28 ns, 8.5 τ ⇒ 5.5e-5 | 29× / 11× under |
| PM | fp2 unchanged and crossover lower ⇒ ≈ 80–85° | inside the window |
| A0, swing | as OTA1 (boost span 1.43 V) | +0.02 V |
| offset | pair term × 4/3 ⇒ ≈ 6.4 mV 3σ | OK |

The hand ε method is conservative. On the SPEC macromodel it gives 1.7e-3 against the 6.8e-4 the SPEC row reports.

## 4. Totals against the budgets
**Current, µA.** Assumptions:
- OTA1 = SIM netlist worst: 61.6 base, 123.9 boost.
- C6 = 4.96 (SIM).
- V_ICM/V_OCM source allowance = 2 per OTA (I_VCM_SRC, open). HAND.
- Switches/LS (CV·f) ≈ 2.5 at 2 MHz and ≈ 5 at 4 MHz. HAND.
- The comparator is on VDPWR and is not counted.

| mode | A: as-is (OTA2 = 61.6 / 123.9) | B: 9/16 shared bias (OTA2 ≈ 28.5 / 57, core 27.4/55.3 + CMFB integrator) |
|---|---|---|
| precision 2 MHz | 134.7: margin 65.3 (33 %) | 101.6: margin 98.4 (49 %) |
| fast 4 MHz boost | **261.8: over by 61.8 µA (+30.9 %)**. OTAs + C6 alone: 252.8, +26.4 % | **194.9: margin 5.1 µA (2.6 %)**. 5.9 µA over the D46c 189 µA risk figure. A +3 % trim residual takes it to ≈ 200.7 |

**Area, µm².**
- OTA1 cell gate-area sum (sizes_draft): core 3,102 + references 206 + replica/cascode bias 318 + CMFB integrator 350 ≈ 4,000.
- With a 2–3× routing factor: 8,000–12,000, plus CMFB MIM (C_INT 2 pF + Cc/Cr 0.3 pF) ≈ 1,150 ⇒ **9,100–13,100 per OTA1 cell**.
- Variant B: core × 0.5625 + integrator, no bias legs ≈ 2,100 ⇒ 4,200–6,300, plus MIM 1,150 ⇒ **5,350–7,450**.
- Committed area: C9 28,500 + MIM 9,000 + C6 7,000 = 44,500 (61.7 %).
- Comparator, switches and LS: SIZING estimate ≈ 3,000. Guard rings and top routing are not counted.

| | A: OTA1 + OTA1 copy | B: OTA1 + 9/16 OTA2 |
|---|---|---|
| tile total before guard rings | 65,700–73,700 = **91–102 %** (OTA2 adds 9,100–13,100 = 12.6–18.2 %) | 61,950–68,050 = **86–94 %** (OTA2 adds 5,350–7,450 = 7.4–10.3 %) |

Area lever, not applied: C_INT is a CMFB integrator cap, not in the signal path. It may be a MOS cap under MIM, as SIZING §1 allows for bias filtering, which saves ≈ 1,000 µm² per OTA.

## 5. Verdict and options (recommendation is an option, not applied)
| option | meets OTA2 rows | current (fast) | area | cost / risk |
|---|---|---|---|---|
| A. reuse as-is | yes, ~2× margins; boost swing +1.4 % | **misses by +61.8 µA (+31 %)** | +9.1–13.1k; tile 91–102 % | zero design work; fails the 200 µA budget and likely the area |
| **B. 9/16 cell, shared bias (recommended)** | yes; SR +7 %, ε ≥ 11× under, boost swing +1.4 % | 194.9 µA, under by 5.1 (2.6 %); over 189 by 5.9 | +5.4–7.5k; tile 86–94 % | sizes_draft/netlist.py parameter (finger counts, bias ports as inputs); C2 tb: op/AC, step, swing/A(v), CMFB + kick, MC offset; reviewer pass. About 1–2 days |
| C. new OTA2 design | open | could reach ≈ 40–45 µA boost | smaller | a full C1-style campaign; does not fit 10 days |

Risks for B, all to be checked in the C2 bench (not run here):
- Shared bias nets couple OTA1 and OTA2 through mirror-gate kickback. The bias-node C grows ≈ 1.56×, which moves boost-toggle settling from about 370 to 580 ns (the D53 limit is ≤ 4 µs).
- The fast-mode current margin is 2.6 %. It is gone at a +3 % trim residual.
- The boost swing margin is 0.02 V. Add to that the 40 mV transient dip from the kick at hot boost.
- C3 has no measured comparator input cap inside the 0.7 pF.
