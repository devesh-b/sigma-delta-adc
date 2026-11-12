# WO-46 (C4a): switches, bottom-plate sampling, non-overlap phase generator (+ C7 level shifters), design note + spot sims

Coordinator-written, 2026-11-12. Runs in parallel with C1 (user request). **Tier: design (Opus).**

## Sources
- PLAN rows C4 and C7, plus the review additions: input-CM sweep (F2); TG sized at ss/−40/3.0.
- SPEC §3.0 switch and settling rows, and §3.6 rule 13 (OTA-chop edge placement).
- CL-5: 3.3 V input chopper and island switches.
- CL-23 and CL-25: the phase generator sits in C4, fed by C9's fs clock and active-high controls.
- D66, D67.
- `design/c1_ota1/netlist.py`: existing switch models, clock ports ph1/ph1b/ph2/ph2b, level-shifted clocks.
- pthomas learning: a 545 ps clock edge cost 1.3 dB, so check edges in-chip.

## Items
1. Write `design/c4_sw/DESIGN.md`, covering:
   - the switch list for both integrators: input, DAC/VREF, Cs2, island/reset, chopper;
   - TG vs NMOS-only choice, and sizing for Ron and settling τ ≤ 0.2·t_half at 4 MHz;
   - charge injection and clock feedthrough: bottom-plate sampling, early phases;
   - the non-overlap generator: delay-based, dead time vs t_half at 4 MHz;
   - early and late phases;
   - 1.8 → 3.3 V level shifters: delay, duty, VDPWR/VAPWR ramp order;
   - a testbench plan with broken copies: overlapping phases, one-sided injection.
2. Spot sims:
   - TG Ron vs signal at ss/−40/3.0 and ff/125;
   - non-overlap dead time across the corners;
   - level-shifter edge rate.

## Rules
- Sandbox only:
  - sync with `scripts/sync-to-sandbox.sh`;
  - frozen copy `regr/tt/WO-46-<sha>`, with golden/ and a single-thread `.spiceinit`;
  - run parallel jobs through `scripts/lpool.sh` and wait on POOL_DONE.
- No local python. Never touch `/home/mempool/tt`.
- Commits: explicit paths, no trailers, no push.
- Every check gets a broken copy that REJECTs.
- This is stage 1 of the block recipe (PLAN.md Stage C): the design note comes first, and the reviewer checks it before the netlist. Stop after the design note, hand calculations and spot sims. The netlist and full testbench come in the next WO, after the review.

## Budget
At most 45 tool calls. Report in ≤ 35 lines.
