# WO-46 (C4a): switches, bottom-plate sampling, non-overlap phase generator (+ C7 level shifters), design note + spot sims

Coordinator-written, 2026-11-12, parallel to C1 (user). **Tier: design (Opus).** Sources:
- PLAN C4/C7 + review additions (input-CM sweep F2; TG sized at ss/−40/3.0);
- SPEC §3.0 switch / settling rows, §3.6 rule 13 (OTA-chop edge placement);
- CL-5 (3.3 V input chopper and island switches), CL-23/CL-25 (phase generator in C4, fed by C9's fs clock + active-high controls), D66/D67;
-  (existing switch models, clock ports ph1/ph1b/ph2/ph2b, level-shifted clocks);
- pthomas learning (a 545 ps clock edge cost 1.3 dB: check edges in-chip).

## Items
1. :
   - the switch list for both integrators (input, DAC/VREF, Cs2, island/reset, chopper);
   - TG / NMOS-only choice and sizing vs Ron and settling τ ≤ 0.2·t_half at 4 MHz;
   - charge injection and clock feedthrough (bottom-plate sampling, early phases);
   - the non-overlap generator (delay-based, dead time vs t_half at 4 MHz);
   - early/late phases;
   - level shifters 1.8 → 3.3 V (delay, duty, VDPWR/VAPWR ramp order);
   - testbench plan and broken copies (overlapping phases, one-sided injection).
2. Spot sims:
   - TG Ron vs signal at ss/−40/3.0 and ff/125;
   - non-overlap dead time at the corners;
   - the level-shifter edge rate.

**Rules:** sandbox only (scripts/sync-to-sandbox.sh; frozen copy `regr/tt/WO-NN-<sha>` with golden/ and single-thread `.spiceinit`; parallel runs via `scripts/lpool.sh`, wait on POOL_DONE); no local python; never touch `/home/mempool/tt`; explicit-path commits, no trailers, no push; every check gets a broken copy that REJECTs. Stage 1 of the block recipe (PLAN.md Stage C) = **design note first**; the reviewer checks it before the netlist. Stop after the design note plus hand calcs and spot sims; the netlist and full testbench come in the next WO, after the review.

## Budget
At most 45 tool calls. Report in ≤ 35 lines.
