# WO-56 (C3d): comparator stress fix without breaking function

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Sources
- `work/v1-design/results/wo51/` (README) and the WO-51 run summary `/home/mempool/regr/tt/WO-51-c88268b/run/summary.txt` (read only)
- `design/c3_comp/*`
- D40, D74, D75
- `REVIEW-C3a-2026-11-12.md`
- SPEC rows 105–108

## Status after WO-51 (the HV cascode on dp/dn)
- **Function broke at every corner.** T2, T7 and T10 now REJECT: decision cycle 1 shows tdec ≈ 500 ns, i.e. a missed or very late decision every other cycle.
- **The stress fix did not land.** T8 still fails at 2.38–2.55 V; the worst terminal moved to the tail (st_t_ds) instead of dp/dn.
- **What works:**
  - the offset row (60 mV) and its ×6 broken copy (REJECTs);
  - the sensitivity data: M1 dominates at 7.9 mV;
  - T5 gate at ±5 %/±1 %;
  - every functional broken copy REJECTs.

## Items
1. **Diagnose the missed decision.** Find why decisions fail or stall every other cycle with the cascode in: it may be the precharge of the cascode internal node, the cascode gate at VDPWR during reset, or the strobe phase. Back the cause with waveforms.
2. **Fix the T8 stress without breaking function.** Compare at least these options and pick one:
   - fix the cascode, e.g. a precharged or self-biased cascode gate;
   - input-side protection: a series R plus a clamp at the comparator inputs, if that is compatible with the kickback limit;
   - a fully HV StrongARM core, sized for t_dec;
   - stress-aware sequencing.

   The 1.98 V limit stays. Show every 1.8 V terminal pair stays within it under the realistic stimulus, at both power-up orders, tt and ff/−40.
3. **Re-run the full C3 suite through lpool.** Exit:
   - every nominal row ACCEPTs;
   - every broken copy REJECTs;
   - the offset MC is recomputed if the core changed.

   Do not export OMP_NUM_THREADS before calling lpool.

## Rules
- Run everything on the sandbox. Use a frozen copy with a single-thread `.spiceinit`, and source the venv and nix PATH in the launcher.
- No local python. Write files with the Write tool.
- Write only under `design/c3_comp/` and `results/wo56/`.
- Commit by explicit path, with no trailers and no push.

## Budget
At most 50 tool calls. Report in ≤ 35 lines.
