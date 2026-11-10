# WO-26 (C1b part 2b): D59 parallel 1:8 references, K_P 12.5, replica fix, gate B at 4 corners

Coordinator-written, 2026-11-10. **Tier: design (Opus).** Sources:
- D57, D58, D59;
- `work/v1-design/REVIEW-WO25-2026-11-10.md` (Majors 1–5, minors);
- `work/v1-design/results/wo25/README.md`;
- `design/c1_ota1/*`;
- SPEC rows 94, 95, 98.

**Sandbox rules:** same as WO-25.
- Frozen copy `regr/tt/WO-26-<sha>`, and include `golden/`.
- Absolute paths, at most 3 processes, nice and timeout, `setsid nohup` with markers, no pgrep loops, delete csv files.

## Items
1. **D59 references:**
   - m_tr, m_nr, m_plr and the V_BL0 replica become parallel-only unit fingers at ratio 1:8. Remove REF_TRIM.
   - Update the bias currents so the mirror currents stay on the design values.
   - Record the layout intent in DESIGN.md: common-centroid with dummies at the array edges (C7).
   - Exit: the four mirror ratios are within ±2 % of nominal at 9 PVT × 2 modes, and their spread over temperature is ≤ 2 %.
2. **K_P 12.5 and replica fix:**
   - KP_BANK base 5 → 4.
   - Cascode m_rn, or match its drain voltage to m_n's.
   - Use 2–4× replica fingers.
   - Derive m_rt/m_rn from m_t/m_n in code and test for equality (review minor).
   - Put the bank switch in the gate path (review minor).
3. **Rows, with a broken copy for each:**
   - **SR row:** boost SR ≥ 25 V/µs and base SR ≥ 12.5 V/µs at 1.4 pF, at every corner (from I_tail). Add a current ceiling row. These replace I_tail ±3 %.
   - **K_P tracking row:** a copy with ibn ×1.05, requiring |ΔK_P/K_P| ≤ 2 %. The old fixed-current wiring must REJECT.
   - **V_OCM row:** |V_OCM error| ≤ 38 mV (CL-2) at all corners and modes.
4. **op/AC rerun** at 9 PVT × 2 × 3 C_L.
   - Exit: precision A0 ≥ 80.3 dB with ≥ 1 dB margin at all 9 PVT; margins ≥ 50 mV; I_fold/I_tail ≥ 1.2; β1 ≥ 0.83; base span ≥ 1.6 V; boost hot-corner span ≥ 1.40 V.
   - Report I_vdd and boost fp2/GBW and PM at the integrate load.
   - Explain the WO-24 → WO-25 A0 gap of about 2.6 dB, or show that it is gone.
5. **Gate B** at SPEC row 94 corners in boost: fs/125, ss/−40, ss/125, tt/27. N 1024, m 21, O1, 6 parts each, combine(). Add sr95 at fs/125.
   - Launch detached with markers. Do not wait.
   - If op/AC exits fail, stop before gate B and report.
   - Never add OTA current beyond D59 (D54 needs the user).

## Commits (explicit paths, no trailers, no push)
1. `design: C1 D59 parallel 1:8 references, K_P 12.5, replica fix`
2. `design: C1b SR / K_P tracking / V_OCM rows + broken copies`
3. `design: C1b op/AC on the D59 netlist (WO-26)`

## Budget
At most 55 tool calls. Report in ≤ 60 lines.
