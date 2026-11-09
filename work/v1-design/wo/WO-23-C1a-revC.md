# WO-23 (C1a rev C): A(v) tables through the model INL, bias diode fix, swing fix

Coordinator-written, 2026-11-09. **Tier: design (Opus).** Sources:
- `work/v1-design/REVIEW-C1a-revB-2026-11-09.md` (RB-M1, RB-M2, RB-m2, RB-m3, Q2–Q4, WO-23 priorities 1–4);
- SPEC change log CL-1b and CL-7, D53;
- `design/c1_ota1/*`;
- `model/iadc.py` (`_leaky` A(v) table).

**Sandbox:**
- No load gate, at most 2 processes, nice and timeout ≤ 600 s.
- At most 3 corners per process; one deck takes about 3 min.
- Keep the A(v) DC curves as small json (not raw csv); delete raw csv files.
- No shell wait loops. If a job is still running when you check, report and stop.
- Work under `regr/tt/WO-23`.

**Do not touch** `design/tier1/` or `design/tests/test_tier1.py` (WO-22 is active).

## Items
1. **Model guard.** In `model/iadc.py`, add an opt-in strict mode that REJECTs (raises) when |x| exceeds the A(v) table range (no silent `np.interp` clamp), and that reports max |x1| and max |x2| per run. Default behaviour stays unchanged.
   - Test in `model/tests/`: strict mode raises on extrapolation; the default is unchanged.
2. **RB-M1 bias diodes.**
   - Make the cascode-bias diode geometry consistent with K at about 0.5 µA. Examples: m_bnc W 0.625 / L 16 (K_N 8), m_bpc W 1.25 / L 10 (K_P 5), or the narrow-width equivalent.
   - Redo the K sweep at hot boost (ss/125, fs/125, sf/125) and ff/−40 base.
   - Update the bias budget, including the V_BL0 replica and the V_ICM/V_OCM sources, and the CL-7 relaxed toggle ratios (about 1:32).
   - Report the fast-mode total.
3. **Swing fix (Q2).**
   - Widen m_pc from 40/2 to 80/2, and add K_P 4 if still needed.
   - Target: span ≥ 1.40 V (with the 50 mV margins) at all three hot-boost corners.
   - Check f_cm against the m_plc variant: keep L 2, or use L 4 with Cc 0.2 pF only if precision A0 at fs/125 still needs it.
4. **A(v) tables (CL-1b).** Rerun the spot for the final rev C sizes at 9 PVT × 2 modes:
   - sweep ±1.8 V diff (or until A < 40 dB), 0.05 V steps above 0.8 V, both signs;
   - secant gain against vod(0), with the offset removed;
   - assert symmetry ≤ 0.5 dB;
   - **save each table.**
   - Ideal CMFB is acceptable at this stage; mark it as such. The real SC CMFB comes in C1b.
5. **Table-INL.** Push each table through the model in strict mode:
   - boost: N 1024 at 4 MHz, ≤ 3.33 ppm;
   - precision: N 1024 and N 4096, each against its share (OTA A(v) share 8 ppm, gate ≤ share/1.5);
   - print max |x1| and confirm it lies inside the table.
   - Broken copy: m_pl L 0.5 ⇒ REJECT on INL.
6. **RB-m3.** Make `sizes_draft.py` agree with DESIGN.md:
   - chopper W 4 / L 0.5, CMFB split, diode currents, docstrings;
   - RB-m4: island switch as a shunt to V_ICM, with its own reset-residue row.
7. Update DESIGN.md: a "Rev C changes" section, results tables, and fast-mode current.

## Commits (explicit paths, no attribution trailer, no push)
1. `model: strict A(v) table range check + max |x| report + test`
2. `design: C1a rev C (bias diodes, swing fix, A(v) tables, table-INL)`

## Budget
At most 45 tool calls. Report:
- table-INL per corner and mode (pass/fail);
- span at hot boost;
- fast-mode current;
- remaining risks.
