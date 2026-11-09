# WO-21 (C1a rev B): OTA1 design note revision per REVIEW-C1a

Coordinator-written, 2026-11-09. **Tier: design (Opus).** Sources: `work/v1-design/REVIEW-C1a-2026-11-09.md` (M1–M8, m1–m7), D51, SPEC change log CL-1 to CL-4, `design/c1_ota1/DESIGN.md`, `sizes_draft.py`, sandbox `regr/tt/WO-20/run3.log`.

**Sandbox:** small `.op`/`.ac` checks only (no MC, no full PVT; that is WO-23), at most 2 processes, nice and timeout, no wait loops, delete raw csv.

## Items (revise DESIGN.md in place, keeping a "Rev B changes" section at the top)
1. **M1 headroom fix:**
   - resize m_pl (W ≈ 100–120 µm at L 4) and m_n (W ≈ 56–80 µm) for Vdsat ≤ ≈ 0.30 V at ss/125 and fs/125 boost, at 3.0 V;
   - replace the fixed 0.45 V V_SDL / V_FOLD with a **Vdsat-tracking** wide-swing replica bias (Vds = Vdsat + ≈ 0.1 V);
   - cascodes m_nc / m_pc at L ≈ 2 with W ×2.
   - Show the stack budget per corner, and confirm the hand A0 from op numbers: precision ≥ 80 dB at ff/125 base; boost hot ≈ value, for comparison against the CL-1 floor (≈ 72 dB, set by WO-22).
2. **D51(2) gm first for fast mode:**
   - Size the input pair for the GBW that WO-22 says is needed. If WO-22 has not landed, design for 26 MHz worst-corner loaded GBW in boost at the same current, by widening the pair (gm/Id ↑).
   - Report the Cgg / β1 cost (CL-4) and the offset gain. Keep fp2 controllable: leave a fold-node MIM placeholder `C_FOLD_EXTRA` that is set later from WO-22.
3. **M3:** the m_pp gate tied to a fixed low voltage, with V_DIN floating. Recompute the lower input-CM limit with the **measured** Vsg (0.86–1.24 V), and redo the stress numbers.
4. **M4:** drop the tail clamp. Bound vg by construction: the reset and vg island switches are closed by default whenever rst_n is low or the bias is invalid. Update tb10 and its broken copy ("reset default open at power-up ⇒ REJECT").
5. **M5:** the input chopper and the vg island switches become a 3.3 V device or TG with level-shifted 3.3 V clocks (D51 Q1/Q4). Ron over the vg CM range at ss/−40/3.0, injection, and Cp_vg, which feeds the CL-4 β1 number.
6. **m1:** itemise C_L (Cs2-in-hold, Cc, the Cdb of m_pc/m_nc, routing, PEX allowance). Re-derive I_TAIL against that sum, then the SR margin.
7. **m2:** CMFB section range, its ro cost to A0, and Cr refresh phase ≠ Cs2 sample phase.
8. **m3:** boost-toggle bias settling ≤ 500 ns.
9. **m4:** keep I_sink/I_tail at 1.35.
10. **m5:** include the sf/fs corners.
11. **m6:** add a 3.3 V mirror-pair MC to the test plan.
12. **m7:** a Vdsat-per-device-per-corner table.
13. **§4 test plan:**
    - M8 mutants: C_L ÷ 6; series gate R ≈ 65 kΩ; the ±30 % expected-value check;
    - gate (B) at tt/27, ss/−40, ss/125 and fs/125 in boost (CL-3);
    - every tb fails on NaN or a missing measurement.
14. Update `sizes_draft.py`.

## Commit (explicit paths, no attribution trailer, no push)
`design: C1a rev B (headroom resize, tracking bias, gm-first pair, 3.3 V chopper, vg bound by reset)`

## Budget
At most 40 tool calls. Report the new sizes, the hand A0, GBW, SR and current per corner and mode, β1 and Cp_vg, and the open risks.
