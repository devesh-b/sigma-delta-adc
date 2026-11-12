# WO-39 results (C1: D69 clamp copies in the tb9 event deck), 2026-11-12

Frozen copy: `/home/mempool/regr/tt/WO-39-993677c` (design/, golden/, `.spiceinit` num_threads=1, jobs.txt, out/tb9, out/logs).
Commit 993677c (tb9 change). Run with `scripts/lpool.sh` (5 jobs: tb9 corner 0, 2, 3, 4, and 0 --mut), 10:40-10:49 IST,
all EXIT=0, POOL_DONE written; csv deleted.

## Change (c1b_tb9.py)
- New gated row on ev copies, **DM diff step**: at the ph2 instants after the diff step (to the CM step),
  | |V_dm(t) - V_dm(pre)| - |lev| x 0.486 V | <= 10 mV.
- mcnr (rst_never) and mcst (clamp_stuck) now ev kind, EXPECT "DM diff step". mclv dropped (evidence: results/wo36, DESIGN.md 2.12).

## Results
| run | verdict | DM diff-step err |
|---|---|---|
| tt 27 (0) | ACCEPT | 0.039 mV (step 486.36 mV) |
| fs 125 (2) | ACCEPT | 0.053 mV |
| ss 125 (3) | ACCEPT | 0.048 mV |
| sf 125 (4) | ACCEPT | 0.048 mV |
| --mut (tt) | ACCEPT (every copy rejected on its row) | |

- mcnr REJECTED: DM step 84.7 mV of 486 mV (err 401.7 mV). mcst REJECTED: 84.7 mV (err 401.7 mV). The held output TG
  collapses the DM response; CM rows stay in band, as expected from WO-36.
- mcc4 REJECTED (reset release 13.3, reset assert 26.4 mV, static ph1 -42.9 mV); masy REJECTED (CM-to-DM u-dep 0.548 uV >
  0.256); mio REJECTED (start-up abs 119.3 mV). Healthy copies show 0.04-0.05 mV on the new row, so it has about 200x margin
  on the good netlist and 40x on the broken ones.
