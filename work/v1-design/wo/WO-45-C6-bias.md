# WO-45 (C6a): bias reference + trim + start-up + boost bank control, design note + spot sims

Coordinator-written, 2026-11-12, parallel to C1 (user). **Tier: design (Opus).** Sources:
- SPEC rows 100–104;
- D42, D43b, D47, D57, D58–D61, D65 (C6 reference window: −19 … +1.6 % at ff/125; D47 trim centres it);
- REVIEW-C1b-final C6/SPEC items:
  - start-up sequencer: rstb ≥ 2 T after bias-valid;
  - boost bank control: 3.3 V level shift, break-before-make, toggle at a pair boundary;
  - ivbl0 absorbs the clamp currents;
- CL-8, CL-9, CL-22, CL-23;
-  port list (the six bias ports + bank control);
- pthomas learnings (start-up leaker steal-away, PMOS start-up bulk to VDD, cascoded mirrors, res_high_po model R = 256.2 + 230.06·L, PWL ramp start-up proof);
- .

## Items
1. :
   - current-mode bandgap reference (pnp_05v5 + xhrpoly);
   - 3-bit trim (range ≥ ±20 %, step ≤ 6 %, monotonic);
   - mirroring to the OTA1/OTA2/comparator ports;
   - start-up circuit and its sequencer interface (bias-valid → C9/rstb);
   - boost bank switch drive (level shifter, break-before-make);
   - own current ≤ 6 µA, area ≤ 7000 µm²;
   - hand calcs: TC, PSRR, trim, start-up, mismatch;
   - testbench plan and broken copies (no start-up, one trim leg open, ratio 1:256).
2. Spot sims (tt, ss/−40, ff/125): the reference current vs T, and start-up from a 0 V VAPWR ramp (1 µs and 10 ms).
3. **Flag:** the +1.6 % high-side window at ff/125. Propose how the trim calibration lands low.

**Rules:** sandbox only (scripts/sync-to-sandbox.sh; frozen copy `regr/tt/WO-NN-<sha>` with golden/ and single-thread `.spiceinit`; parallel runs via `scripts/lpool.sh`, wait on POOL_DONE); no local python; never touch `/home/mempool/tt`; explicit-path commits, no trailers, no push; every check gets a broken copy that REJECTs. Stage 1 of the block recipe (PLAN.md Stage C) = **design note first**; the reviewer checks it before the netlist. Stop after the design note plus hand calcs and spot sims; the netlist and full testbench come in the next WO, after the review.

## Budget
At most 45 tool calls. Report in ≤ 35 lines.
