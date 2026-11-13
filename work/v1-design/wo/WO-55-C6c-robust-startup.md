# WO-55 (C6c): robust bias reference start-up, possibly a re-architecture

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Sources
- `work/v1-design/results/wo45/` and `results/wo50/README.md`
- WO-50 run summary: `/home/mempool/regr/tt/WO-50-dde5031/out/summary.txt` (read only)
- `design/c6_bias/{DESIGN.md,c6_spot.py,run_wo50.sh}`
- D42, D47, D73
- SPEC rows 100–104
- LEARNINGS-pthomas (bias section: beta-multiplier K=4, start-up stolen away once running, PMOS start-up bulk to VDD, PWL ramps)

## Status after WO-50: worse than WO-45
- **DC errors** (supposed to be ~1.07 µA):
  - ss/27 DC reads 12.35 µA, with 5.5 mA of own current.
  - tt/−40 DC reads 18.8 µA.
  - fs/27 own current reaches 21 µA.
  - The WO-50 detector/hysteresis start-up creates new equilibria or a large-current state.
- **Start-up transients:** fail at nearly every corner and ramp, with oscillation (up to 223 bias_ok rises) or a wrong final state.
- **Still fine:** trim and PSRR (69–73 dB); the broken copies REJECT.
- **Loop-break diagnosis (WO-50):** the core has a low-gain region below about 50 % of I0 (both pnps off), with an amp-offset-dominated differential.

## Items
1. **Step back, compare and choose.** Compare 2–3 architectures against SPEC rows 102–104 (ΔI/I ≤ 3 % over T, own current ≤ 6 µA, area ≤ 7000 µm², start-up from 1 µs to 10 ms ramps with no zero-current state):
   - (a) the current Banba core with a proven start-up: a current-sensing start-up that is fully off in steady state and has no feedback into the amp output beyond a clamp;
   - (b) a self-biased beta-multiplier (constant-gm) reference with a classic start-up plus a PTAT/CTAT correction or trim, as pthomas did;
   - (c) the Banba core with a chopper-free amp that has a guaranteed input-common-mode / offset margin in the low-gain region (for example, an offset-injected or level-shifted amp).

   Use hand analysis plus loop-break DC sweeps: count the equilibria and their stability at all corners. A DC "find all equilibria" sweep is the key evidence. Pick one and justify it in DESIGN.md.
2. **Implement it.** Then:
   - DC initial-state test (`.ic` from 0 and from VDD) at 5 corners × 3 temperatures: a single equilibrium everywhere.
   - Start-up ramps, 1 µs and 10 ms, at 5 corners × −40/125: settled within ±1 % by ramp end + 10 µs, with a single final bias_ok assertion at I ≥ 50 % of DC.
   - TC and trim as before.
   - Broken copies: nosu and early-release.
   - Run everything through lpool. Do not export OMP_NUM_THREADS before calling lpool; it sets it itself.
3. **bias_ok / rstb interface for C9:** a fixed hold count plus a VAPWR-good condition. Propose numbers from the measured worst settling.

## Rules
- Sandbox only. Frozen copy with a single-thread `.spiceinit`; source the venv and nix PATH in the launcher. Run through lpool and wait on POOL_DONE.
- No local python. Write files with the Write tool.
- Write only under `design/c6_bias/` and `results/wo55/`.
- Commit by explicit path; no trailers, no push.

## Budget
At most 55 tool calls. Report in ≤ 35 lines. If no architecture meets row 104, stop and report the options.
