# WO-51 (C3c): comparator fixes after the WO-48 full run

Coordinator-written, 2026-11-13. **Tier: design (Opus).**

## Sources
- `work/v1-design/results/wo48/{README.md,summary.txt}`
- D74, D75
- `REVIEW-C3a-2026-11-12.md`
- `design/c3_comp/*`
- SPEC rows 105–108 and the change log

## Items
1. **T3 offset row (D75).**
   - Derive the comparator offset limit from its loop impact, not a fixed mV number. Cover both:
     - x2 headroom: the offset shifts the x2 switching level, which uses up OTA2 swing;
     - chop residue: system chop removes the constant offset, so state the residue at N 1024 and N 4096.
   - Write the derivation in DESIGN.md.
   - Add a SPEC change-log entry citing D75.
   - Re-judge the existing MC result against the new limit: σ 14.4 mV at tt, |μ|+3σ 44.8 mV.
   - Also find the dominant mismatch device. A per-device sensitivity is enough.
   - Broken copy: mismatch ×3. It must still REJECT.
2. **T8 stress, dp 2.36–2.44 V vs 1.98 V.**
   - First decide whether the stimulus is realistic: x2 slewing at ~200 V/µs through 10 Ω is about 7× faster than OTA2's 27 V/µs boost slew.
   - Re-run T8 with x2 driven at OTA2's slew rate through R_X2/C_X2, and add a fast-edge info copy.
   - If the stress still fails, add a dp/dn clamp or a cascode and show the fix.
   - Do not loosen the 1.98 V limit.
3. **T5 asymmetric kickback, 7.7–8.2 mV vs 5 mV.**
   - Find the mechanism.
   - Fix it with sizing or isolation, or bound it as gain-only with evidence. The ±10 % R/C asymmetry may be unrealistic: compare it with the real OTA2 output impedance mismatch.
   - Propose a fix and state the cost.
4. Re-run the full C3 suite through lpool. Exit: every nominal row ACCEPTs and every broken copy REJECTs.

## Rules
- Sandbox only. Frozen copy with a single-thread `.spiceinit`. Parallel runs through lpool, waiting on POOL_DONE.
- No local python. Write files with the Write tool.
- Do not touch other blocks.
- Explicit-path commits, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 35 lines.
