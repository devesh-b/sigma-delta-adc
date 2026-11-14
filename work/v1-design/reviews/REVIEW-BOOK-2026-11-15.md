# REVIEW-BOOK-2026-11-15: sd-adc-design-reviewer accuracy review of DESIGN_BOOK.md c1fa950

Condensed by the coordinator from the reviewer report (read-only review, no simulations).

**Verdict.** The body is mostly correct and the PENDING marking is consistent. The Proposal summary has 1 critical and several major issues. One C1 rule interpretation contradicts D43c, and the C3 mechanism text has a circuit error.

## Critical
- **C1.** Proposal, "What is new", bullet 3, "no earlier TT ΣΔ has an on-chip decimator": **false** per NOTES.md §1.
  - TTSKY26A-ADC-8BIT has an on-chip sinc1 counter.
  - Standalone TT decimation-filter projects exist (tt09-decimation_filter, tt09-delta-sigma-decimation-filter).
  - On this chip the decimator is the two CoI accumulators only. The weighting acc2 + 4·acc1, the normalisation and the chop demodulation run in firmware (SPEC §3.7, I.5.3).
  - Fix: "first analog ΣΔ modulator on TT sky130 with its decimating accumulators (2nd-order CoI) in the same analog tile, found in our keyword survey of 29 shuttles up to ttsky26c (2026-11-07); final scaling and chop demodulation in firmware". The table cell "Prior analog ΣΔ … no on-chip decimator" can stay.

## Major
- **M1. C1 boost gate B** (Proposal status, V.1, III.1.8 "All recorded boost gate B runs pass").
  - On the current WO-52 netlist it was run only at fs/125 (3.14 ppm) and ss/−40 (0.71 ppm), both at O1. tt/27 and ss/125 exist only on older netlists (WO-31).
  - 3.14 against 5 is < 3× margin, so D43c requires O2 at fs/125. It is not scheduled.
  - Fix the wording to exactly that, and add both items to V.2.
- **M2. C3 status** (Proposal, V.1, III.3 rev f row).
  - T3: the `plaus` limb REJECTs because the sens decks were not run; only the count and |μ|+3σ limbs pass (42.7–45.1 mV ≤ 60).
  - T2: only the single-shot rows pass; no rev f cyc rows were run (they are PENDING in WO-88).
  - T5: margin by construction (D81).
  - T8: rev f cap is 2.251 V at ff/−40; 2.206 V is the kp2 candidate.
  - Fix the wording to these facts.
- **M3. Power row.** MCP3421 145 µA is the whole chip; our 200 µA is analog only. **User decision 2026-11-15: show both.**
  - Analog row: ≤ 200 µA budget; fast-mode ≈ 180 µA REASONED, not proven (needs C2).
  - Digital row: C9 1.705 mW, LibreLane default-activity estimate (WO-73), ≈ 0.95 mA at 1.8 V.
  - Add a plain note that the total is not comparable to the MCP3421's 145 µA.
- **M4. Proposal "Verification approach".** D2 (all PVT + MC) is the plan, not the current state. State the coverage to date:
  - gate B at 4 corners, only 2 on the current netlist;
  - C6 DC rows at 5 corners;
  - C3 at 9 PVT;
  - MC only for C3 T3; C1 tb8 and C6 MC not run.

  Also list the weak or absent broken copies:
  - C1 srknee, 3 % over the gate;
  - C6 early/hy1 under D89;
  - C3 T8 copies, which cannot be judged without a passing base;
  - T5, checker copies only (D81).
- **M5. Proposal "Top risks".** Add the risks that are in V.4 but missing here:
  - area closure: C9 28,500 µm² (40 %) + MIM ≈ 9,000 (12 %) + C6 ≤ 7,000 (≤ 10 %) ≈ 62 % of 72,071 µm² before OTA1/OTA2/comparator/switches/guard rings/routing; V.4 says 66–89 % full by estimate;
  - digital-to-analog coupling: a 48 MHz macro in the same tile as a µV front end, not simulated;
  - sys-off CMRR margin of only 1.1–1.5 dB over 60 dB.
- **M6. C9 status.** WO-75 bench passes. WO-83 is 106/107 so far. Pre-D85 PnR meets setup/hold at 12 corners, with slew waived at the stand-in (D86). WO-73 says DRV is not 0 ("not a signoff candidate"), LVS was not extracted, and 2 floating nets are open.
- **M7. C1 O2 interpretation** (III.1.8a, V.3 item 1, Appendix E). "D48 requires O2 … and O2 is then the converged result" is wrong under D43c:
  - D43c accepts a pair only if |O2−O1| ≤ max(10 %·INL, 0.1·(gate−INL)). O1 1.706 against O2 0.160 is about a 10× step, so it fails.
  - The D43c verdict formula INL(O2)·(1+|Δ|/INL) gives about 1.7 ppm.
  - WO-76 §2's own rule (`--tight` vs O2 the same) is unmet: the O2 tight run aborted and the O1 tight run timed out.
  - The ladder never tightens vntol (1e-6 V ≈ 0.25 ppm), and O2 values of 0.14–0.16 ppm sit below that.
  - Fix: "O2 becomes the result only if a further tightening confirms it (D43c; WO-76 §2); a 10× O1→O2 step does not meet D43c as written."
  - Note the counter-evidence: the O1 endpoints agree to 0.005 ppm across parts.
  - State the consequence: every O1-only INL in the book (boost gate B; precision tt/ss125/fs125; earlier s5 rows) carries the same uncertainty.
  - Keep the PENDING / "strong sign" framing.
- **M8. Proposal noise/INL rows.**
  - Label "model at spec 0.94 µV / 3.4 ppm" as "tier-0 model, intrinsic floor (V.4)"; it excludes reference, board, coupling and PEX.
  - Qualify the targets:
    - noise target at 2 MHz across corners, with 3.0 µV at 125 °C for 0.25 MHz (D27);
    - INL target for the precision modes; fast mode N 64 is ≤ 200 ppm;
    - MCP3421's gain error includes its reference; this design is ratiometric.
- **M9. Rule misattributed.** There is no "gate/2" trigger in D48 or SPEC; that was WO practice. D43c applies the O1/O2 ladder to every gated INL with < 3× margin: gate/3, i.e. 0.444 ppm in precision and 1.667 ppm in boost.
  - Fix III.1.8a, III.1.10, V.2 row 3 and Appendix E.
  - Note that WO-31's "2.17 < gate/2, so no O2" fell below the D43c standard.
- **M10.** III.1.8a: slew is "unlikely" (WO-76 §3), not "ruled out".
- **M11. C3 precharge-edge mechanism.**
  - R0 (pfet 1.0/0.15, drain op, gate clk, source vdd; RSO) restores op during precharge. It is 2.4× wider than the keeper.
  - Correct wording: R0 and R1 share the clk gate, so while R1 pulls on up, R0 is still turning on, and the already-on keeper is the main return path during the edge. That explains the kp2 effect; once R0 is fully on, it restores op too.
  - Consequence: a narrower R0/R1 slows the aggressor but also weakens op's restore path, so the net effect is not obvious.
  - Mark the mechanism as "interim (WO-88), probe PENDING".
- **M12. Stress rules vs PDK.** The SkyWater device-details page gives nfet/pfet_01v8 model validity of Vds/Vgs 0–1.95 V and nfet Vbs +0.3 to −1.95 V. The project's 1.98 V sustained, 2.2 V < 1 ns, the 4.95 V junction and the C3 Vsb 2.37–2.39 V are **project stress rules (D80/D83/D90), not PDK ratings**, and they lie outside the model-validity range.
  - Add one line saying so in III.3, Appendix C and the Proposal.
  - Never write "within PDK ratings".
  - Source: https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html

## Minor
- **m1.** "Every earlier analog ΣΔ on sky130 TT is 1st order": qualify it with the survey date and method (keyword survey, 2026-11-07), and list all three: pthomas, tilesos, shimomi (ttsky26a, "first-order 1-bit continuous-time DSM"). Add shimomi to the table.
- **m2.** "Exact reconstruction" → "exact reconstruction formula; residual quantisation error ∝ 1/N²" (≈ 33 µV at N 1024, ≈ 2 µV at N 4096, I.5.4).
- **m3.** Risk 3 / V.2: 180 µA nominal against the 172 µA SPEC basis scales the accepted 189 µA worst case to about 198 µA, which is about 1 % to the 200 µA budget. State it.
- **m4.** Comparator current 0.50–0.76 µA is the rev a value; mark it "not re-measured on rev f".
- **m5.** C4: 23.4 pA gives 0.19 V drift, which is under the 0.2 V criterion. The 20 pA limit carries margin (0.2 V at N 4096 with 2.01 pF allows about 24.5 pA). Say so, so the two numbers don't read as contradictory.
- **m6.** III.2 table: CM kick 41–45 mV is rev a. Use the rev f range 38.96–47.41 mV (kp2 38.92–46.82).
- **m7.** Tile size: 319.24 × 225.76 µm (current TT tools `tt_analog_2x2_3v3.def`), against 334.88 µm in the ttsky-sigma-delta frame and ~334 in SPEC. Name the template source and version in II.1.2.
- **m8.** Keep "5 corners" wherever the C6 DC rows are quoted.
- **m9.** IV.7: the "broken cap 9 → 3" test was limited by load, so it could not fail. Describe it as non-discriminating.

## Style
- **s1.** The Paul Thomas SNDR (dB, 100 kHz) is a different metric from µV rms at DC. Say so.
- **s2.** "A reviewer checks every design change" → "is required for every design change" (the C3 final review is open).
- **s3.** Put PENDING in the III.1.8a gate-mechanics bullet.
- **s4.** Cite the WO-76 per-part numbers as unfiled interim data (the coordinator note).

## Coordinator answers to the reviewer's questions
- **Q1** (origin of the 20 pA row): left open. Log it in Appendix E as "the 20 pA limit sits below the 24.5 pA that the 0.2 V criterion allows; origin to be traced".
- **Q2:** show both (user decision 2026-11-15).
- **Q3:** no amendment to D43c. A third solver point is to be scheduled; until then the C1 precision verdict stays PENDING.
