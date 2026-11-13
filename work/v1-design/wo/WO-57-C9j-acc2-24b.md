# WO-57 (C9j): D77 acc2 at 24 bits + CL-29 wording

Coordinator-written, 2026-11-13. **Tier: code (Sonnet).** Fresh agent.

## Items
1. In `design/c9_digital/rtl/c9_dec.v`, change acc2 and its hold register from 25 bits to 24. Sign-extend to 32 bits on readout, as now.
2. In SPEC.md, add a change-log entry (D77) correcting CL-29. acc2 is 24 bits, which is exact because max |acc2| = N(N−1)/2 < 2^23. The width mutant that must REJECT is acc2 at 23 bits; 24 bits is equivalent.
3. Update `design/c9_digital/README.md`.
4. Run lint (verilator -Wall) and yosys synth on the sandbox inside IIC-OSIC-TOOLS. Report the cell and FF counts.
5. Do not touch `tb/`. The verification agent re-runs separately.

## Rules
- Use a frozen copy at `regr/tt/WO-57-<sha>`.
- No local runs and no local python.
- Commit with explicit paths only, no trailers, no push.

## Budget
At most 15 tool calls. Report in ≤ 15 lines.
