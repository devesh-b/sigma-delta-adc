# WO-50 (C6b) results: bandgap start-up fix

2026-11-13. Status: **the WO exit is not met.** The diagnosis is done; the slow-ramp start-up is fixed at tt/27; the 1 µs ramp still relaxes. Design note: `design/c6_bias/DESIGN.md` §6 (rewritten, status in §6.5). Deck: `design/c6_bias/c6_spot.py` (commit dde5031; 3caec67 superseded), run script `design/c6_bias/run_wo50.sh`.
Frozen copy on the sandbox: `/home/mempool/regr/tt/WO-50-dde5031` (`.spiceinit` num_threads=1). It runs 63 jobs through `scripts/lpool.sh` (`out/pool_run`), with the done marker at `out/pool/POOL_DONE` and the verdict table at `out/summary.txt` (copied to `golden/`). R2/R1 = 4.1988 comes from the WO-45 golden. There is no re-tune, because the start-up is off in the steady state. The deck deletes the raw csv after parsing.

## 1. Diagnosis (item 1)
Smoke runs (same deck, tt/27/3.3):
- `loop_tt_27_3.3_nosu`: the loop is broken at the M5 gate, the start-up is removed, and the sweep is `.dc Vx 0…2 V`. It finds **one non-zero stable equilibrium, at 1.0748 µA**, plus the zero state. Core differential V_B − V_A vs current:

  | I / I_good | 10 % | 25 % | 50 % | 75 % | 90 % |
  |---|---|---|---|---|---|
  | V_B − V_A (mV) | −0.00003 | −0.0008 | −0.69 | −25.5 | −12.3 |
  | V_A (V) | 0.089 | 0.216 | 0.436 | 0.603 | 0.631 |

  Below about 50–60 % of I0 both pnps are off. Both branches are then just R2, and the differential is in the µV range, far below the amp offset (σ ≈ 2 mV). The loop has no restoring force there.
- WO-45 bad states (from the frozen WO-45 json):
  - At the end of the run, tsu was 0.52–0.79 V, so Ms sat in subthreshold. VG was 1.67–2.24 V.
  - bias_ok asserted at 0.05–0.8 % of I.
  - So the WO-45 start-up (Ms driven by tsu, Mk 1:1, release at about 10 %) acted as a proportional regulator and held the current inside the zero-gain region. **Cause: the start-up release (WO candidate 3) acting on the zero-gain core region.** The amp has no second equilibrium.
- `dci` (DC op from `.nodeset` at 0 V and at VDD), tt/27: the new start-up and the WO-45 start-up both land at 1.0743 µA. The WO-45 DC failure was at sf/27; the full run repeats it as `dci_sf_27_3_su45`.

## 2. Fix (item 2)
The new start-up is in DESIGN.md §6.2:
- thresholded detector: Mk 0.21 ×, release at I_lk / 0.21;
- hysteresis: Mkh 0.105 ×, switched in by ok;
- digital drive (ok, sua);
- injection only by Mpo (one unit PMOS, gate ok) pulling o1 up; no device forces VG;
- full steal-away: the Mpo gate is at VDD after release.

The first version (3caec67) also had a hard VG pull-down Ms. At tt/27 with a 1 µs ramp:
- I peaked at 20 × I0;
- o1 was slammed to 0.04 V;
- bias_ok asserted 41 times.

That pool was stopped by moving its deck aside, without pkill. A `SUPERSEDED` note is in its directory, and its remaining jobs failed fast.

## 3. Runs (item 3), partial

| run | verdict | dev in window | peak | ok rises | I@ok | note |
|---|---|---|---|---|---|---|
| tran tt/27/3.3, 10 ms | REJECT | 0.000 % | 1.06 × | 1 | 0.043 | starts and holds; fails only the bias_ok row (asserted at VAPWR ≈ 1.1 V, DESIGN §6.5) |
| tran tt/27/3.3, 1 µs | REJECT | 201 % | 5.4 × | 15 | 1.52 | relaxation persists (DESIGN §6.5) |

The other 61 jobs (corners, nosu/early/su45 broken copies, dct/dcv/dci, loop) are queued in the same pool. Next-step options are in DESIGN.md §6.5.

lpool note: GNU `nproc` honours `OMP_NUM_THREADS`. run_wo45.sh exported that variable before calling lpool, so the WO-45 pool and the first WO-50 pool both ran with nproc=1 (serial). run_wo50.sh now calls lpool under `env -u OMP_NUM_THREADS`. lpool.sh itself is outside this WO's scope; it should read nproc before it exports the variable.

## 4. Sequencer (item 4)
DESIGN.md §6.3: bias_ok means "running", not "settled". C9 should hold rstb for a fixed count after bias_valid (proposal: 64 fs cycles), set from the worst t(±1 %) − t_ok. It also needs a VAPWR-good condition, because the release threshold scales with VAPWR (§6.5).

## 5. Pickup
1. `ssh sandbox 'ls /home/mempool/regr/tt/WO-50-dde5031/out/pool/POOL_DONE && cat /home/mempool/regr/tt/WO-50-dde5031/out/summary.txt'`
2. If the marker is absent: `ssh sandbox 'tail -3 /home/mempool/regr/tt/WO-50-dde5031/out/pool_run/pool.status'`. Jobs are numbered in `out/jobs.txt`: 1–22 tran none, 23–30 nosu/early, 31–32 su45, then dct, dcv, dci, loop.
3. Expected verdicts: `none` rows ACCEPT; nosu, early, su45, ptat and trim_open rows REJECT; dcv and loop rows INFO. Otherwise `summary` prints MISMATCH. With the current design, the 1 µs and 10 ms `none` rows will mismatch as above.
