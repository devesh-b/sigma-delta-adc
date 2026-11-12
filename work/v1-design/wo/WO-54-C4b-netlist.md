# WO-54 (C4b): revise the C4 note per REVIEW-C4a + D76, netlist + full testbench

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Sources:
- `work/v1-design/REVIEW-C4a-2026-11-13.md`
- D74, D76
- `design/c4_sw/*`
- `work/v1-design/results/wo46/`
- SPEC (switch rows, CL-5, CL-25, CL-28)
- `design/c3_comp/DESIGN.md` (strobe)
- `design/c1_ota1/netlist.py` (switch ports)

## Items
1. **Revise DESIGN.md:**
   - M2: early fully off (10 %, T and C) before late; K_E 1–2 ns.
   - M3: differential injection sweep at fixed CM; report INL in ppm.
   - M4: VDPWR detector plus PDK isolation LS cells (SLEEP_B) (D76). The ramp tb checks no crowbar and no 1.8 V overstress, both orders.
   - m1: controls change inside the reset window (rule), or a 3.3 V gap latch.
   - m2: g measured on gated nets plus cross terms.
   - m3: Sg NMOS W 4–6 µm, plus the leak sweep vs Vin_cm with the sign (D76).
   - m4: strobe hv2lv LS in the C7 count.
   - m6: S2cm on φIl, Sk0 on φSl.
   - m7: DAC 4/12; VREF− NMOS-only.
   - Q5: edge_max derived from dead time / injection timing (D76), edge rate as info, inv_8 drivers.
   - Order 1: leave a placeholder pending WO-53 (model study). Do not finalise the order-1 switch plan.
2. **`design/c4_sw/netlist.py`** (switch banks plus generator plus LS) and **`c4_tb.py`** with the C4b plan rows plus the review additions:
   - injection diff sweep;
   - early-before-late at thresholds;
   - gated-control glitch;
   - strobe LS;
   - edge broken copy (inv_1);
   - every row with a broken copy.
3. **Run through lpool:** the §6 corners that matter (state the subset and why), at 0.25 / 2 / 4 MHz, plus the VDPWR axis for the LS (worst case sf/−40/3.6/1.62).

## Rules
- Sandbox only. Frozen copy with a single-thread `.spiceinit`; ngspice runs in a cwd that has it, or OMP_NUM_THREADS=1.
- Run through lpool, waiting on POOL_DONE.
- No local python. Write files with the Write tool.
- Do not touch other blocks.
- Explicit-path commits, no trailers, no push.

## Budget
At most 50 tool calls. Report in ≤ 35 lines.
