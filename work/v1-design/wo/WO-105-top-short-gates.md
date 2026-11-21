# WO-105: full-chip short gates (D95), plus a tier-1 in-loop run with transistor OTA2

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. This continues WO-95 (README `results/wo95`; commits b4b44f4…373f66c), whose budget ran out.

## State
- Frozen copy `/home/mempool/regr/tt/WO-95-b4b44f4`. The smoke was relaunched at 16:28 (PRIO=high, 48 µs simulated). The smoke fix (smoothed B-sources, Ron 200 Ω capture) is 373f66c.
- `run_wo95.sh` is the orchestrator: it starts the **N 1024** gate pool after SMOKE_OK. **That is now out of scope (D95). Stop it before it launches**: kill the orchestrator by its exact PID, not `pkill -f`, and leave the smoke running.

## Items
1. **Re-define the top gates under D95.** Each gets a broken copy that must REJECT (reuse WO-95's copies: nosu, dacswap, ota2dead, noswap, noreset):
   - (a) start-up through the first valid conversion (the smoke covers part of this);
   - (b) DC function at N 16 and N 64: ~5 Vin points against golden within the N-dependent quantisation bound;
   - (d) the chop pair at N 16;
   - (e) overload ±1.1 VREF and recovery at N 16;
   - (f) the stage-1/stage-2 reset behaviour (residue at slot 0).

   All at tt/27 first, then ss/−40 if time allows. Use D91 OTA2, and the real C6 final / c5c7_ref once WO-104 accepts them; stand-ins until then, marked as such.
2. Measure `sec_per_conv` from the smoke. Size the job list to finish within about 2 days at the current throughput. Use PRIO=high for tt and PRIO=low for ss/−40.
3. **Tier-1 in-loop with transistor OTA2.** Add an OTA2 transistor hook to `design/tier1/gen_tier1.py`, mirroring the existing OTA1 hook, and run gate B at tt/27 precision (2 MHz, N 1024, m 21, O2) with OTA1 + OTA2 at transistor level, 6 parts, combined. Gate 1.333 ppm. Use the D43c convergence ladder if Δ is large.
4. Write `results/wo105/README.md`: the gate table, runtimes and pickup.

## Rules
- Sandbox only. Connect with `S=(ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox)` (a zsh array).
- Frozen copy `/home/mempool/regr/tt/WO-105-<sha>`, or reuse WO-95's.
- Use lpool v3. Wait on markers only. No local python.
- No size changes.
- Write only `design/top/`, `design/tier1/` (the OTA2 hook only) and `results/wo105/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 20 lines.
