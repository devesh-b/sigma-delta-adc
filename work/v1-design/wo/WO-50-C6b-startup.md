# WO-50 (C6b): fix the bandgap start-up (second stable state)

Coordinator-written, 2026-11-13. **Tier: design (Opus).**

Sources:
- `work/v1-design/results/wo45/{README.md,spot_summary.txt}`
- D73
- `design/c6_bias/{DESIGN.md,c6_spot.py,run_wo45.sh}`
- LEARNINGS-pthomas (start-up leaker steal-away, PMOS bulk to VDD, PWL ramp proof)

## Finding (WO-45 spot)
- DC, trim, TC (−2.4/+0.25 %) and PSRR (69–73 dB) are all OK.
- **The transient start-up settles at 13–48 % of the DC current.** Affected: tt and ss/−40, at both the 1 µs and the 10 ms ramp.
- At sf/27 the DC op itself lands in a low state (0.106 µA).
- So the core, the amp or the start-up circuit has a second stable operating point that the start-up circuit does not leave.

## Items
1. Diagnose which loop has the extra state:
   - the core;
   - the two-stage amp (amp output at a rail);
   - the start-up release threshold (bias_ok at 10–20 % releases too early).

   Back it with evidence: node voltages in the bad state, and a DC sweep or `.nodeset` from both states.
2. Fix it. Candidate approaches:
   - a start-up that keeps injecting until the core current is above about 80 %, then steals itself away;
   - amp output pre-bias;
   - a different start-up sense node.

   Own current ≤ 6 µA. Keep the trim, TC and PSRR results.
3. Re-run the spot set through lpool. Also add:
   - the sf/ff/fs DC initial-state test (op from 0 V `.ic` and from VDD `.ic`);
   - VAPWR ramps of 1 µs and 10 ms at all 5 process corners × −40/125.

   Exit:
   - every nominal start-up within ±1 % of DC by the end of the ramp + 10 µs;
   - the nosu copy REJECTs;
   - a new "start-up released early" broken copy REJECTs.
4. Update DESIGN.md (start-up section, bias_ok threshold vs rstb hold) and the results README.

## Rules
- Sandbox only; frozen copy with a single-thread `.spiceinit`; lpool; POOL_DONE.
- No local python; write files with the Write tool.
- Never touch `/home/mempool/tt` or other blocks' directories.
- Commits by explicit path, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 35 lines.
