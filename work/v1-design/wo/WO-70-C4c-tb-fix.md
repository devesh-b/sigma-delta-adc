# WO-70 (C4c): fix the C4 testbench netlist bug, rerun the gate pool

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Context
- WO-54 run: `/home/mempool/regr/tt/WO-54-e6022d3/run`, read-only. Report: `run/report.txt`.
- About 40 jobs failed with `ngspice rc=1 bad=['Error: incomplete or empty netlist']`. That covers almost all of:
  - tim, injdm, injcm, settle, rampa, rampb;
  - their broken copies.
- So the report has no design verdict.
- The smoke2 run in `/home/mempool/regr/tt/WO-54-smoke2` may help locate the cause.

## Items
1. Find out why the deck is empty or incomplete. Candidates:
   - the netlist generator (`design/c4_sw/netlist.py`);
   - the `c4_tb.py` deck writer: paths, cwd, includes;
   - concurrency, e.g. a shared filename between parallel jobs.

   Fix it. Back the fix with evidence: an empty deck before and a full deck after.
2. Rerun the full C4 rev b pool (89 jobs) through `scripts/lpool.sh`.
   - Source the venv and the nix PATH in the launcher.
   - Do not export OMP_NUM_THREADS.
   - Use absolute paths.
3. Report every row, with a verdict and numbers. Every broken copy must REJECT.
4. Also implement D78 (Sg leak re-split using C1's measured island-leak share) and record it.
5. Then request the reviewer pass on C4 rev b.

## Rules
- Sandbox only. Use a frozen copy with a single-thread `.spiceinit`.
- No local python. Write files with the Write tool.
- Write only under `design/c4_sw/` and `results/wo70/`.
- Explicit-path commits, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines.
