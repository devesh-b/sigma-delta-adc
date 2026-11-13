# WO-62: DESIGN_BOOK.md accuracy fixes (from the reviewer pass, 2026-11-13)

Coordinator-written. **Tier: writer (Sonnet).** Fresh agent. Documents only.

## Fix in DESIGN_BOOK.md
Line numbers refer to the reviewed version.
1. **L59 (critical):** the resolution formula should be ENOB = log2(FSR/(√12·v_rms)) = (SNR − 1.76)/6.02. Keep the numbers 19.6 / 17.9 / 14.5 b. Also fix the same formula in `CONTEXT.md:119`, where it came from.
2. **L85:** the ideal second-order 1-bit SQNR at OSR 128 is ≈ 100 dB by the L83 formula. Say "lower in practice". Fix `NOTES.md:47` too.
3. **L231 / L566:**
   - kT/C-only = 0.556 µV @15 SPS (s3_budget.md:31).
   - 0.71 µV = the WO-04 ota+sys model value (D22).
   - Note that SPEC.md:18 and SPEC.md:25 disagree. Do not edit SPEC; add a "SPEC text inconsistency" note in the book's gaps appendix.
4. **L254:** S2 13.79 / 7.20 µV include the vres 5 µV term (s2_chop.md). The closed form at lf 1 alone gives 8.80 / 2.20 µV. Say so.
5. **C9 status (L1241, L1414, L1429, V.4 risks):** update from `results/wo58b/README.md` (first PnR) and `results/wo60a/README.md`:
   - setup fails at ss_100C_1v40;
   - Fmax 44.6 → 45.4 MHz;
   - slew and fanout violations;
   - physical checks clean;
   - D79 / WO-60 fixes in progress (the fs_tick retime in WO-60B pending verification).
6. Minor fixes:
   - **L229:** state that 182 µV counts 2 sides × 2 phases; one differential sampling event = 129 µV.
   - **L358–366:** state the A_VT convention (per-device here; Pelgrom's pair-difference A_VT is √2 larger, so 12 ≈ 17).
   - **L633, L1034:** order-1 follower: x2 = (Cs2/Cint2)·x1 = c2·x1, not k·x1. Fix C4 `DESIGN.md:67,251` as well.
   - **L225:** bottom-plate sampling works by charge conservation on the floating top plate.
   - **L202:** 4/N is in u units (±1), i.e. 2/N of FSR.
   - **L686:** the 47.65 µV check is at r = 0.01.
   - **L423:** "a sum of 3σ terms ≈ 4.2σ" only for two equal terms; generalise it.
   - **L529–534:** label the S1 table as s1_vref.md v1 (s1_vref_v2.md exists).
   - **L1240:** 929 cells (generic yosys) vs 860 cells (LibreLane sky130 synth); different counting basis.
7. **Precision gate B:** call it a missing authoritative gate run (D48(1), SPEC:94), not "not found". Point to the new WO-63.
8. **Fast-mode current:** add the reviewer's reasoned estimate. OTA1 boost is ~122 µA. OTA2 is ~51 µA (REASONED, ~19 µA tail × 2.7). Bias is ~6 µA. That gives ≈ 180 µA nominal against the 172 µA SPEC estimate and the 200 µA budget. Mark it as an open risk.

## Rules
- Edit only DESIGN_BOOK.md, CONTEXT.md, NOTES.md and design/c4_sw/DESIGN.md, at the listed lines.
- No sandbox runs. No local python.
- Commit with explicit paths, no trailers, no push. Signing may block; if it does, leave the changes and list the paths.

## Budget
At most 25 tool calls. Report in ≤ 15 lines.
