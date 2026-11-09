# REVIEW C1a rev B: OTA1 + CMFB (WO-21, ca8a6f8), 2026-11-09

Reviewer: sd-adc-design-reviewer (read-only). Condensed by the coordinator.

## Verdict: PROCEED TO C1b WITH CONDITIONS
- No Critical finding. Two new Majors, both cheap, to fix before the netlist is frozen.
- **Closed:** M1, M3, M5, M6, M7 (op/AC), m1, m4, m5, m7. M4 is closed by rule; tb10 is still pending.
- **Open:** M2 (needs WO-22 + gate B), M8 (tb7 not run), m2 (f_cm against m_plc), m6 (tb8b).

## Majors

### RB-M1: cascode-bias diode current inconsistent with K (PROVEN)
- §2.9 drives the diodes at I_nc/32 = 0.49 µA but keeps the 5/16 and 5/10 geometry. That gives K_N = 1.0 and K_P = 1.25, which puts m_n/m_pl back in triode.
- The spot deck ran the diodes at I_nc/4 and I_nc/8. Keeping that geometry costs about +10 µA, so fast mode lands near **206 µA**.
- Fix: narrow the diodes (W 0.625/L 16 and W 1.25/L 10 at ≈ 0.5 µA), redo the K sweep including hot boost and ff/−40 base, and add MC on the margins. Also count the V_BL0 replica and the V_ICM/V_OCM sources in the bias budget.

### RB-M2: hot-boost A(v) droop likely fails fast-mode N 1024 ≤ 5 ppm (REASONED)
- The model `_leaky` uses the secant A(|x|), the same definition the spot script uses.
- Edge Δ(1/A) at ss/125 boost (81.2 → 73.6 dB) is 1.22e-4. That is 1.6× the S4-shape value (0.78e-4), which gave 5.37 ppm. fs/125 and sf/125 are also above the S4 shape.
- Precision fs/125 base (79.6 / 77.9 dB) is mild: 0.29× the S4 shape.
- The deciding check is the measured tables run through the model INL.

## Minors
- **RB-m1 — chopper injection.** The injection repeats every fs/2 cycle; it is not a single event. Worst case ≈ 0.96 mV offset in OTA-only chop mode, realistic case 10–20 µV. System chop removes it. Measure it in tb13.
- **RB-m2 — m_plc L 4.** This slows f_cm to ≈ 4.1 MHz, below the 4.7 MHz needed. Pair it with Cc 0.2 pF (f_cm ≈ 5.7 MHz, C_L sum 1.40 pF), or skip it if the table-INL passes.
- **RB-m3 — sizes_draft.py disagrees with the note.** CHOP_SW input W 2.0 vs the note's 4; CMFB_SPLIT 0.5 vs LOAD_FIXED 0.75; stale docstrings; diode currents not recorded. Fix it before C1b; the netlist generator reads this file.
- **RB-m4 — island switch 2/0.5.** It has ≈ 2× the tabulated Ron (≈ 5 kΩ). As a shunt switch it still meets reset settling in 216 ns. Give it its own row (reset residue ≤ 1e-4).
- **RB-m5 — clock-edge skew.** The 3.3 V vs 1.8 V chopper edges must both land inside g (6.25 ns at 4 MHz). Add this to the C8/C5 timing tb.
- **RB-m6 — vg bound.** The vg bound needs a bounded V_ICM and a defined level-shifter state with VDPWR off. Add VDPWR off/late and a floating-V_ICM case to tb10.
- **RB-m7 — fp2 optimistic.** The spot deck omits the fold-chopper caps and junction caps, so fp2/GBW may fall to ≈ 4 at hot.
- **RB-m8 — CMFB in tb3.** A(v) was measured with an ideal CMFB; tb3 needs the real (or averaged) SC CMFB.

## Answers

**Q2 (fixes):**
- m_plc L 4 gives +1.16 dB, but needs Cc 0.2 pF alongside; it is unnecessary if the table-INL passes.
- On swing, neither V_OCM 1.45 nor K_P 4 is enough alone. The hot-boost span is 1.32–1.37 V against 1.40 V needed.
- Recommended swing fix: widen m_pc from 40/2 to 80/2. This adds about +0.09 V of Vdsat headroom and +0.05–0.08 V of V_sa, and also raises A0. Add K_P 4 if still needed.

**Q3 (boost-toggle settling):**
- 500 ns is not needed. The toggle pair is already invalid (§3.7a e), which leaves ≥ 33 µs. Integrators and islands reset every slot, CMFB settles in under 1 µs, and the thermal effect is negligible.
- Proposed text: "settled to 0.1 % within ≤ 0.25·T_slot,min (≈ 4 µs at N 64 / 4 MHz) after a toggle; the toggle pair is invalid". tb12 limit 4 µs; broken copy 1:256.
- This brings fast mode to ≈ 187–189 µA, but only with RB-M1's narrow diodes.

**Q4 (gain gate):**
- Gate both modes on model INL with the measured secant A(v) table, at every PVT point, at ≤ share/1.5. Boost: N 1024, ≤ 3.33 ppm. Precision: N 1024 and N 4096. A0 becomes a health row.
- Table requirements:
  - range to ±1.8 V diff or until A < 40 dB;
  - steps ≤ 0.05 V above 0.8 V;
  - both signs, symmetry ≤ 0.5 dB;
  - raw curves saved;
  - real SC CMFB.
- Add a REJECT-on-extrapolation assert to the model; `np.interp` clamps silently. Broken copy: m_pl L 0.5 ⇒ REJECT on INL.

**Q5:** ready for netlisting once RB-M1 and RB-m3 are fixed.

## WO-23 priority
1. Rerun the spot with the DC csv kept, ±1.8 V at 0.05 V steps, and push the 18 tables through the model INL; add the extrapolation assert.
2. Fix the RB-M1 diode geometry, redo the K sweep, update the bias budget.
3. Swing fix sweep: m_pc 80/2, K_P 4; f_cm with the m_plc variants.
4. User decision on Q3, then set the bias ratios.
5. Finish WO-22 and set C_FOLD_EXTRA.
6. Netlist with ad/as/pd/ps, fold chopper, real 3.3 V switches and SC CMFB; tb1/2/3 at 45 PVT × 2.
7. Gate B at 4 corners.
8. tb9, tb10, tb13, tb12.
9. tb7 with the M8 mutants; tb8/8b real per-seed MC.

## Reviewer questions, with the coordinator's answers
1. Is the island switch in series or a shunt? → To be stated in the netlist. The intent is a shunt to V_ICM; RB-m4 then applies.
2. Is fast mode a must? → **Yes (D51).**
3. Where does V_ICM come from when the bias is invalid? → C6/C8 item, covered in tb10 (RB-m6).
4. Does precision INL run at N 4096 too? → **Yes.**
