# WO-44 (C3a): StrongARM comparator + latch, design note + spot sims

Coordinator-written, 2026-11-12, in parallel with C1 (user request). **Tier: design (Opus).** Sources:
- SPEC rows 105–108: offset ≤ 20 mV 3σ; noise ≤ 5 mV rms; decision < 34 ns at 4 MHz for |Vin| ≥ 1 mV at the worst corner; kickback ≤ 5 mV on x2, recovered within 0.5·t_half; single retimed bit.
- SPEC §3.2 (comparator section).
- CL-23: sampled on the bit-clock falling edge; the DAC flop updates on the rising edge.
- PLAN C3 plus the review additions:
  - Δ = 0 at 4 MHz, ss/−40;
  - probability that the DAC and the decimator disagree;
  - kickback gate.
- `work/v1-design/LEARNINGS-pthomas-2026-11-10.md`:
  - one ngspice process per decision point;
  - tmax 1 ps through regeneration;
  - 10 Ω in series with sources;
  - sub-mV verdicts are solver noise;
  - clock phase and excess loop delay;
  - a NOR SR latch causes hysteresis; use inverter buffers and a NAND latch.
- `repos/sd-analog/ttsky-sigma-delta` (its `comp_mc.py`), read only.

## Items
1. Write `design/c3_comp/DESIGN.md`:
   - topology: StrongARM with or without a preamp, latch, and the retime-FF interface to C9;
   - supply (1.8 V vs 3.3 V) and level shifting;
   - hand calculations: offset, noise, decision time, kickback, metastability MTBF at 4 MHz;
   - draft device sizes;
   - testbench plan, with a gate and a broken copy for each row.
2. Write `design/c3_comp/sizes_draft.py` and run a spot transient (tt and ss/−40, 4 MHz): decision time, and kickback on a behavioural x2 node.
3. MC plan. The PDK's 1.8 V devices do have Vth mismatch; check that first and state it.

## Rules
- Run everything on the sandbox:
  - sync with `scripts/sync-to-sandbox.sh`;
  - frozen copy `regr/tt/WO-44-<sha>` with `golden/` and a `.spiceinit` containing `set num_threads=1`;
  - parallel runs through `scripts/lpool.sh`; wait on its POOL_DONE marker.
- No local python. Never touch `/home/mempool/tt`.
- Commits: explicit paths, no trailers, no push.
- Every check needs a broken copy that REJECTs.
- This is stage 1 of the block recipe (PLAN.md Stage C): the design note comes first, and the reviewer checks it before any netlist. Stop after the design note, hand calculations and spot sims. The netlist and the full testbench come in the next WO, after the review.

## Budget
At most 40 tool calls. Report in ≤ 35 lines.
