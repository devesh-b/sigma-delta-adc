# WO-87 (C6f) results: D89 gate, 125 °C fast-ramp SIMFAIL, oldhint copy, CL-38

2026-11-15. Status: **bench and SPEC changes committed; the rerun pool is running (load ~8 on 6 cores, 1 slot), no verdicts yet.** Pickup at the end.

- Commits: 4086317 (D89 gate, new copies, oldhint retired, SPEC CL-38), 41aa132 (fast-ramp gmin fix, `run_wo87.sh`).
- Frozen copy `/home/mempool/regr/tt/WO-87-41aa132` (`git archive` of design/ golden/ model/ scripts/, `.spiceinit` num_threads=1, repo `scripts/lpool.sh`).
- Experiments: `/home/mempool/regr/tt/WO-87-exp2/` (27 one-change variants, ff/fs/tt 125 °C; still running at hand-off), `/home/mempool/regr/tt/WO-87-exp3/` (tt/125, 5 variants, done). `WO-87-exp/` is a dead first attempt (`/usr/bin/time` missing, every job EXIT=127); ignore it.

## 1. D89 gate (`c6_spot.py tran_eval`)
- Removed: `rises == 1` and `I@ok >= 50 %` (the two D78-row terms D89 replaces; fs/125 10 ms failed only on the second, at 2 % current). Both stay in the summary as info, with every pulse (rise, width, VDD, I/Idc).
- Added: settle (±1 %) after the **final** bias_ok rise ≤ `LIM_D89` = 0.25 × 2^16 / 4 MHz = **4.1 ms**. Why 25 %: the hold that must cover the settle is the C9 count (2^16 fs cycles after rst_n, D85; 16.4 ms at the fastest fs, longer at slower fs). A quarter leaves 4x for count/fs uncertainty and model error. WO-80 worst: 1.68 ms (sf/−40 10 ms), 41 % of the limit.
- Unchanged: dev@rel ≤ 1 %, settled before release (release = final rise + 64 µs; slow ramps also wait for the 2^16 count), ≥ 20 µs window, ok > 0.9 VDD after release, Idc ≥ 0.75 µA.
- Blind spot fixed (tightening): a current still outside ±1 % at the last sample used to give `t1 = None`, read as "settled". It is now "never settled" (REJECT).

### Broken copies under the new gate (predictions written before the run)
| Copy | Old reject reason (WO-80) | Reason under D89 | Prediction |
|---|---|---|---|
| nosu (ss/−40, ff/125; 1 µs, 10 ms) | no current | no current, no final rise | REJECT |
| nocnt (tt/27, ss/−40, 10 ms) | not settled before release | same (release at final rise + 64 µs, settle 1.6 ms) | REJECT |
| hold0 (tt/27 1 µs) | not settled before release | same | REJECT |
| **slow** (new; tt/27, sf/−40, 10 ms): master-leg gate RC τ 1.2 ms | — | settle after final rise ≈ 5.5 ms > 4.1 ms, while still settled before the 16.4 ms release (only the D89 term fails) | REJECT |
| **earlyx** (new; ss/−40, ff/125, 1 µs): ok from the core-off flag, Mk x1000 | — | ok high near 1 V with I ≈ 0 turns the kick off before the core starts: zero-current state (as nosu) | REJECT |
| early (Mk x16) | **rises 2** | ok rises at I ≈ 52 %, settles 13.6 µs later: harmless under D89 | **ACCEPT expected → MISMATCH, needs a decision** |
| hy1 (tt/27, sf/−40, 1 µs) | **rises 3** | chatter ends 24 µs after the ramp; settle after the final rise 8–11 µs | **ACCEPT expected → MISMATCH, needs a decision** |

- early and hy1 were rejected only by the rises rule. In a noiseless bench, an early or chattering bias_ok does no harm under D89 and D88 (the C9 run restarts on any drop), so no valid D89 reason exists for them. **Not retired here; their EXPECT stays REJECT.** Options: (a) retire both to INFO, with earlyx and slow as the copies that keep the start-up and D89 terms honest; (b) keep a hysteresis row outside the start-up gate (e.g. a noise-injected bias_ok bench). This is the coordinator's/user's call.

## 2. SIMFAIL at 125 °C, 1 µs ramp
- Abort: "Timestep too small … vsm#branch" at t = 35 ns (tt), 128 ns (ff), i.e. VAPWR 0.12–0.41 V on the ramp, with step 6.25e-21. The 10 ms ramps (tmax 2 µs) ran with the WO-80 gmin 1e-12.
- One change at a time from the WO-80 deck (gmin 1e-12, abstol 1e-12, gear, tmax 5 ns):

| Variant | tt/125 | ff/125 |
|---|---|---|
| v0 baseline | — (WO-80: abort 35 ns) | abort 128 ns (930 s) |
| v1 method=trap | abort 35 ns | abort 37 ns |
| **v2 gmin 1e-11** | **ok, 268 s** | **ok, 339 s** |
| v3 abstol 1e-11 | abort 35 ns | abort 128 ns |
| v4 reltol 1e-4 | — | abort 128 ns |
| v5 tmax 1 ns | abort 35 ns | abort 37 ns |
| v6 rshunt 1e10 | abort 10 ns | (exp2, pending) |

- Fix: `gmin=1e-11` on the fast-ramp tran decks only (slow ramps keep 1e-12). Error ~1e-11 S × 3 V = 30 pA per junction against 1 µA (30 ppm).
- Tighter check: every 1 µs row that completed in WO-80 at gmin 1e-12 (ss/±125/−40, tt/−40, tt/27, ff/−40, fs/−40, sf/−40, the hold0/hy1/early/nosu copies) reruns here at 1e-11. Compare idc, t1%, tok, settle-after-ok and dev@rel with `results/wo80/summary.txt` (WO-80 values, e.g. ss/125: t1% 47.275 µs, tok 36.467 µs, settle 10.807 µs, dev@rel 0.022 %). Pass: changes ≤ 1 % of each settle time and ≤ 0.01 % in dev@rel.

## 3. oldhint
- The WO-55 static nodeset now converges to the physical point (WO-80: 1.0699 µA, agree 0.000 %), so it is blind. **Retired to INFO** (still run, still printed).
- Replacement, two rows on the same dct gate (first sweep point vs the transient-from-0 state, `hagree ≤ 0.5 %`):
  - **zhint** (sf/27, ff/27, ss/27; real circuit, nodeset on the zero-current state: a=b=c=0, VG=VDD, ok=0): predicted ACCEPT. If a wrong DC equilibrium existed, .dc from that nodeset is where it would land; the kick (on while ok is low) leaves no zero-current solution, and the loop rows already show no crossing between 0.02 µA and 0.9 I_good.
  - **zhintnk** (sf/27; kick removed + zero nodeset): a real wrong equilibrium exists; predicted REJECT on hagree. This shows the gate can fail.
- If zhint REJECTs, that is a real finding (a DC zero state with the kick present), not a bench issue.

## 4. SPEC
- Row 104 (C6 start-up) and **CL-38**, in commit 4086317. CL-39 (WO-88) was added afterwards by another agent; CL-38 sits above it.

## 5. Verdict table
Pending: `out/summary.txt`. The non-tran rows (15 dci + nosu, 17 loop, 3 dcv, 5 dct, ptat, trim_open) are copied from WO-80, because their decks did not change (the c6_spot.py diff from 1153e82 touches only tran, the new copies, and a /0 guard in dct thr).

## Pickup
1. `ssh sandbox 'ls /home/mempool/regr/tt/WO-87-41aa132/out/pool/POOL_DONE && cat /home/mempool/regr/tt/WO-87-41aa132/out/summary.txt'`. If it is absent: `tail -2 /home/mempool/regr/tt/WO-87-41aa132/out/pool_run/pool.status`.
2. Copy `summary.txt` here. Check the predictions in §1/§3, the expected MISMATCH on early/hy1 (and nothing else), and the gmin comparison in §2.
3. Optional: `/home/mempool/regr/tt/WO-87-exp2/` v6–v8 and fs/125 rows, for the variant table.

## Ready for review
- `design/c6_bias/c6_spot.py` (D89 gate, t1 blind spot, slow/earlyx/zhint/zhintnk copies, fast-ramp gmin 1e-11), `design/c6_bias/run_wo87.sh`, SPEC row 104 + CL-38.
- Numbers: LIM_D89 4.1 ms against a 1.68 ms worst case; gmin 1e-11 error 30 ppm.
- Open: early/hy1 retire-or-rebench decision; the rerun verdicts; reviewer sign-off on the oldhint retirement.
