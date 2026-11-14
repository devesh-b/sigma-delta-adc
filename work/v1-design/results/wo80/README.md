# WO-80 (C6e) results: WO-64 MISMATCH 18, R1 144.8 check, bias_ok behaviour

2026-11-14. Status: **root causes found; deck fixed (commit 1153e82); full pool running, no verdicts yet.** The sandbox is at load 50–60 from other users, so lpool runs 1 job at a time and the 77-job pool will take hours.

- Deck `design/c6_bias/c6_spot.py`, launcher `design/c6_bias/run_wo80.sh` (no re-tune: R2/R1 2.45, R1 144.8 µm from the WO-64 tune.json), diagnostic `design/c6_bias/okpulses.py`.
- Frozen copy `/home/mempool/regr/tt/WO-80-1153e82` (`.spiceinit` num_threads=1). Experiments: `/home/mempool/regr/tt/WO-80-587e6ecw/exp/` (`res.txt`, decks, logs, `s1_B.csv`).

## 1. SIMFAIL at 125 °C: simulator numerics, root cause is the deck gmin
- WO-64 logs: two modes. (a) "Timestep too small … vsm#branch" at VAPWR ≈ 50–60 mV (ss/125 1e-06 at 11.2 ns, ff/125 0.01 at 19.7 µs, ff/125 early at 11.9 ns). (b) tt/125 0.01 and ss/125 0.01 were killed by the 5400 s `sim()` timeout (no .json, Python traceback in `pool_run/job_6.log`, `job_10.log`).
- The deck sets `gmin=1e-15`, 1000x below the ngspice default. At 125 °C and near-zero bias the matrix is ill-conditioned.
- Experiments on the three failing decks (exp/res.txt):

| Variant | s1 ss/125 1 µs | f2 ff/125 10 ms | t3 tt/125 10 ms |
|---|---|---|---|
| base (WO-64) | fail 11.2 ns | fail 19.7 µs | > 5400 s |
| A abstol 1e-12 | fail 11.2 ns | > 1500 s | > 1500 s |
| C A + trap | fail 11.2 ns | ok, 901 s | > 1500 s |
| E reltol 1e-4 + abstol 1e-12 | fail 11.2 ns | > 1500 s | — |
| **B gmin 1e-12 + abstol 1e-12** | **ok, 123 s** | **ok, 173 s** | **ok, 254 s** |

- Fix: tran decks only get `.option gmin=1e-12 abstol=1e-12`. Error ≈ 1e-12 S × 3 V = 3 pA per node, against 1 µA (3 ppm). The dct/dcv/dci/loop decks are unchanged (they all ran and their results stand). The 125 °C broken copies (ff/125 nosu, early) rerun under the same options and must still REJECT.

## 2./3. Fast-ramp "dev ≈ 100 %" and sf/−40 rises 2: metric reading, then real behaviour
- `dev` is the WO-55 window (ramp end + 10 µs), **reported only, not gated**. On a 1 µs ramp the current is still rising at 11 µs (t1% = 30–44 µs), hence ≈ 100 %. Relabelled `dev10us(info)` in the summary. The gated metric `dev@rel` (after final ok + hold) is 0.005–0.02 %, and settled-before-release is True.
- **The fast-ramp rows REJECT on the `rises == 1` gate (rises 2–3), not on dev.** Waveform (s1_B, ss/125 1 µs): bias_ok pulse 1 rises at 0.34 µs (VDD 1.01 V, I = 0.7 % of final), width 0.77 µs; final rise at 37.5 µs (I 96 %). While 0.3 V < VDD ≤ 1 V, ok/VDD reaches 0.74 (at 0.54 V).
- Cause: at low VDD nothing holds q low. The default-low device `mqd` is gated by tsu, which is 0.16–0.2 V at that time (below the NMOS threshold), so ok follows the supply through the inverters. **This is real circuit behaviour, a glitch-high before the bias is valid.** sf/−40 0.01 rises 2 is very likely the same mechanism on the slow ramp; the pool reports every pulse (rise time, width, VDD, I/Idc; `pre-covered` = every non-final pulse narrower than H_HOLD 64 µs).
- The gate is **not** loosened. Options (coordinator/user):
  - (a) Keep "one rise" and fix the circuit. One change: a power-up default-low on q that does not depend on tsu (e.g. q pulled low by a leaker-biased NMOS, or gate mqd from a node that is high while VG is not yet regulating). Needs a design pass and review.
  - (b) Redefine the D78 row as "one final rise; every earlier high pulse narrower than the C9 256-cycle filter, with margin". C9 already clears its counter on a low sample. Note the slow-ramp pulse width scales with the ramp, so it must be measured on the 10 ms rows before (b) is safe.
  - Recommendation: wait for the slow-ramp pulse widths. If they exceed about 32 µs, (a).

## 4. R1 144.8 (WO-64 pool, which already ran at 144.8)
- dct, 5 corners: TC −2.56/+0.08 % (ff, worst) … −2.12/+0.15 % (fs), within ±3 % over −40…125 °C. tt/27 I0 1.0677 µA (−0.21 % vs 1.07, ±2 % gate). Own current 4.34–4.96 µA (≤ 6 µA). Trim cover 1.410–1.411 (≥ 1.3836 for ±19 %), step ≤ 5.06 %. Rlen 854 µm.
- Start-up: every dci (from 0 and from VDD, 15 corner/T points) and every loop row ACCEPTs (one stable point, no mid crossing). The 125 °C tran rows are in the running pool.
- `dct sf 27 oldhint` MISMATCH: at the new operating point the WO-55 static nodeset converges to the physical point, so the copy is not broken any more. The gate is unchanged. Question: retire the copy (INFO), or build a broken hint that does land elsewhere.

## 5. D78 / D85: bias_ok
- Polarity: active high (ok = q through two inverters), as CL-36 expects. Final level: ok ≈ VDD after the final rise.
- At the VAPWR ramp: not cleanly low. See item 2 (glitch-high at VDD 0.5–1.1 V, I ≈ 0). The C9 256-cycle filter rejects a 0.77 µs pulse; the D85 2^16 count also covers slow ramps.
- CL-36 wording to confirm with C9: "J = tick at which (b) completes". If a long early glitch completes (b) and bias_ok later drops before the 2^16 count ends, does (b) re-arm? This affects option (b) above.
- Sg logic gating (D78) lives in C4 (VDPWR-good closes the islands), not in C6. Nothing to do here.

## Pickup
1. `ssh sandbox 'ls /home/mempool/regr/tt/WO-80-1153e82/out/pool/POOL_DONE && cat /home/mempool/regr/tt/WO-80-1153e82/out/summary.txt'`. If it is absent: `tail -2 /home/mempool/regr/tt/WO-80-1153e82/out/pool_run/pool.status`.
2. Expected: no SIMFAIL. 125 °C none rows: dev@rel ≤ 1 %. 125 °C nosu/early: REJECT. The fast-ramp none rows will still REJECT on rises (item 2, open question). Read the `pulses` field on the 0.01 rows for the slow-ramp glitch width.
3. Copy `summary.txt` here as `results/wo80/summary.txt`.

## Ready for review
- `design/c6_bias/c6_spot.py`: tran gmin/abstol change (item 1), pulse report (items 2/5).
- Decision for the coordinator: the rises gate (a) vs (b); the oldhint copy; CL-36 (b) re-arm semantics.
- WO-80 pool summary once POOL_DONE exists.
