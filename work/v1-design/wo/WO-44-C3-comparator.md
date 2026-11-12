# WO-44 (C3a): StrongARM comparator + latch, design note + spot sims

Coordinator-written, 2026-11-12, parallel to C1 (user). **Tier: design (Opus).** Sources:
- SPEC rows 105–108 (offset ≤ 20 mV 3σ, noise ≤ 5 mV rms, decision < 34 ns at 4 MHz for |Vin| ≥ 1 mV worst corner, kickback ≤ 5 mV on x2 recovered within 0.5·t_half, single retimed bit);
- the §3.2 comparator section;
- CL-23 (sampled on the bit-clock falling edge; the DAC flop updates on the rising edge);
- PLAN C3 + review additions (Δ = 0 at 4 MHz ss/−40, DAC/decimator disagreement probability, kickback gate);
-  (one ngspice per decision point, tmax 1 ps through regeneration, 10 Ω series, sub-mV verdicts = solver noise, clock-phase / ELD, NOR-SR hysteresis → inverter buffers + NAND latch);
-  (, read only).

## Items
1. :
   - topology (StrongARM + preamp or not, latch, retime FF interface to C9);
   - supply (1.8 vs 3.3 V) and level shifting;
   - hand calcs for offset, noise, decision time, kickback and metastability MTBF at 4 MHz;
   - device sizes (draft);
   - the testbench plan with gates and broken copies.
2.  and a spot transient (tt, ss/−40, 4 MHz) for decision time and kickback on a behavioural x2 node.
3. MC plan: the PDK's 1.8 V devices do have Vth mismatch; check that first and state it.

**Rules:** sandbox only (scripts/sync-to-sandbox.sh; frozen copy `regr/tt/WO-NN-<sha>` with golden/ and single-thread `.spiceinit`; parallel runs via `scripts/lpool.sh`, wait on POOL_DONE); no local python; never touch `/home/mempool/tt`; explicit-path commits, no trailers, no push; every check gets a broken copy that REJECTs. Stage 1 of the block recipe (PLAN.md Stage C) = **design note first**; the reviewer checks it before the netlist. Stop after the design note plus hand calcs and spot sims; the netlist and full testbench come in the next WO, after the review.

## Budget
At most 40 tool calls. Report in ≤ 35 lines.
