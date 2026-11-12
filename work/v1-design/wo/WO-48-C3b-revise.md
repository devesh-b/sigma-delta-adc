# WO-48 (C3b): revise the comparator note per D74 + REVIEW-C3a, then a netlist and spot rerun

Coordinator-written, 2026-11-12. **Tier: design (Opus).**

**Sources:**
- `work/v1-design/REVIEW-C3a-2026-11-12.md`
- DECISIONS D74
- `design/c3_comp/*`
- `work/v1-design/results/wo44/`
- SPEC rows 105–108

## Items
1. Update `design/c3_comp/DESIGN.md` and `sizes_draft.py` for D74:
   - strobe in φS, captured by C9 on fs_tick;
   - offset basis A_VT 12 mV·µm in total;
   - set A′ sizing;
   - HV input pair with a 1.8 V tail;
   - order 1 reads x2, with integrator 2 as a follower.
2. Change the test rows:
   - **T2:** keep it as the requirement row. Add a band row: t_dec at 1 mV, ss/−40/1.62 V, must fall within [0.5, 3]× the spot value.
     - Broken copies: brk_starve must REJECT on the band; a physical weak-strobe copy must REJECT on T2.
   - **T10:** timing window referenced to the C9 48 MHz clk edge. Add a near-zero-Δ check that q and qb are never both high at capture. Use the routed q load, or add a buffer.
     - Broken copy: strobe on the wrong phase ⇒ REJECT.
   - **T5:** add a ±10 % R/C asymmetric x2 variant. Report CM recovery.
   - **T4:** report-only, plus the hand calculation.
   - **T3 (offset MC):** at the D74 basis, ≥ 200 runs at tt and ≥ 50 at the worst corner. Broken copy: mismatch ×3 ⇒ REJECT.
   - **T8:** stress across both power-up orders, plus x2 below ground.
3. Write the netlist generator `design/c3_comp/netlist.py` and the full testbench (`c3_tb.py`). Run 9 PVT plus MC through lpool. Every row and every broken copy as specified.

## Rules
- Sandbox only. Frozen copy with a single-thread `.spiceinit`. Parallel runs through lpool, waiting on POOL_DONE.
- No local python. Write files with the Write tool, not shell heredocs.
- Never touch `/home/mempool/tt`, `design/c1_ota1/`, `design/c9_digital/`, or `design/c4_sw/`.
- Commits: explicit paths, no trailers, no push.

## Budget
At most 50 tool calls. Report in ≤ 40 lines.
