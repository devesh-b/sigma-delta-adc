# WO-45 (C6a): bias reference + trim + start-up + boost bank control, design note + spot sims

Coordinator-written, 2026-11-12. Runs in parallel with C1 (user request). **Tier: design (Opus).**

## Sources
- SPEC rows 100–104.
- D42, D43b, D47, D57, D58–D61 and D65. Per D65 the C6 reference window is −19 % … +1.6 % at ff/125, and the D47 trim centres it.
- REVIEW-C1b-final, C6 and SPEC items:
  - start-up sequencer: rstb held ≥ 2 T after bias-valid;
  - boost bank control: 3.3 V level shift, break-before-make, toggle at a pair boundary;
  - ivbl0 must absorb the clamp currents.
- Change log: CL-8, CL-9, CL-22, CL-23.
- `design/c1_ota1/netlist.py`, port list only: the six bias ports and the bank control.
- `work/v1-design/LEARNINGS-pthomas-2026-11-10.md`:
  - a start-up leaker must be stolen away once the core runs;
  - the PMOS start-up bulk goes to VDD;
  - cascoded mirrors;
  - res_high_po model R = 256.2 + 230.06·L Ω;
  - prove start-up with a PWL supply ramp.
- `bias_bgr_area.md`.

## Items
1. Write `design/c6_bias/DESIGN.md`:
   - **Blocks:**
     - current-mode bandgap reference (`pnp_05v5` + xhrpoly);
     - 3-bit trim: range ≥ ±20 %, step ≤ 6 %, monotonic;
     - mirroring to the OTA1, OTA2 and comparator ports;
     - start-up circuit and its sequencer interface (bias-valid to C9 and rstb);
     - boost bank switch drive: level shifter, break-before-make.
   - **Limits:** own current ≤ 6 µA; area ≤ 7,000 µm².
   - **Hand calculations:** TC, PSRR, trim, start-up, mismatch.
   - **Testbench plan, with these broken copies:**
     - start-up circuit removed;
     - one trim leg open;
     - reference ratio 1:256.
2. Spot sims at tt, ss/−40 and ff/125:
   - reference current vs temperature;
   - start-up from a 0 V VAPWR ramp, at 1 µs and at 10 ms ramp times.
3. Flag the +1.6 % high-side window at ff/125, and propose how the trim calibration lands on the low side.

## Rules
- Sandbox only:
  - sync with `scripts/sync-to-sandbox.sh`;
  - frozen copy `regr/tt/WO-45-<sha>`, with golden/ and a `.spiceinit` containing `set num_threads=1`;
  - parallel runs through `scripts/lpool.sh`; wait on POOL_DONE.
- No local python. Never touch `/home/mempool/tt`.
- Commits: explicit paths, no trailers, no push.
- Every check gets a broken copy that REJECTs.
- This is stage 1 of the block recipe (PLAN.md Stage C): the design note comes first, and the reviewer checks it before the netlist. Stop after the design note, the hand calculations and the spot sims. The netlist and the full testbench come in the next WO, after the review.

## Budget
At most 45 tool calls. Report in ≤ 35 lines.
