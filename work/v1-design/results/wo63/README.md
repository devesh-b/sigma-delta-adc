# WO-63 results (C1): precision-mode gate B, 2 MHz, base bias. 2026-11-13

SPEC row 94 / D48(1): transistor OTA1 (netlist.py, sc CMFB, WO-52 netlist: sink L 8, D59-D64, D71/D75) in the tier-1 deck,
OTA2 behavioural at its precision point (13.5 V/us, GBW 10 MHz, fp2_mult 3, beta2 0.497 via the default cp_vg),
fs 2 MHz, boost 0, N 1024, m 21, O1, 6 parts per corner (`--part i/6`, endpoints in every part), combined with `combine()`.
Gate: INL(endpoint) <= 1.333 ppm (share 0.889 info). O2 needed only if O1 >= 0.667 ppm.

## Code
`design/c1_ota1/c1b_gateb.py`: new `--mode prec` (default `--mode boost` is unchanged: same deck, same tags `gb_*`, same
gate 5 ppm). Prec tags `gbp_*`. `combine()` takes `gate=`. Broken copy `--copy srknee` in prec: all six bias ports x 0.6234,
base SR at the SPEC basis (I_tail / 1.4 pF) 8.24 V/us = 0.8 x the 10.3 V/us base floor; must REJECT (> 1.333 ppm).
`design/tier1/` not touched.
Commit: NOT made. `git commit` failed, "1Password: agent returned an error" (signing). Uncommitted paths:
`design/c1_ota1/c1b_gateb.py`, `work/v1-design/results/wo63/README.md`.

## Sandbox
Frozen copy `/home/mempool/regr/tt/WO-63-e450ae2` (HEAD e450ae2 + the uncommitted c1b_gateb.py above; design/, golden/,
model/, `.spiceinit` num_threads=1). Smoke: `run_smoke.sh` / `jobs_smoke.txt`, logs `out/logs_smoke`.
Full run: `run.sh` -> lpool on `jobs.txt` (30 jobs: c0 tt/27/3.3, c1 ss/-40/3.0, c2 ss/125/3.0, c3 fs/125/3.0 nom + c3
srknee, 6 parts each), logs `out/logs/job_N.log`, marker `out/logs/POOL_DONE`, then combine -> `out/gb/<cfg>/combine.out`,
csv deleted, `out/ALL_DONE`.

## Smoke (N 64, m 3, tt/27, O1)
This was a run check only. At N 64 with 3 points, INL is quantisation-dominated: the boost and prec values agree.

| job | mode / copy | INL ep [ppm] | runtime | verdict |
|---|---|---|---|---|
| 1 | prec nom | 0.718 | 240 s | ACCEPT, no problems |
| 2 | boost nom (unchanged path) | 0.721 | 146 s | ACCEPT, no problems |
| 3 | prec srknee | still running at 15:45 (`out/logs_smoke/job_3.log`) | | |

Runtime ratio prec/boost 1.64 (not 2×). The WO-52 boost N 1024 parts took 1190-1320 s, so a prec part should take about
2100 s at light load. Deck timeout 10800 s, job timeout 11000 s.

## Results (N 1024, m 21, O1)
Status at hand-off (15:45 IST): RUNNING. lpool started at 15:41. Box load is 6-8 on 6 cores (the WO-61 reruns are also
running), so lpool runs 1 job at a time. Serial worst case: 30 x ~35-45 min, about 18-22 h. It shortens as the load drops.
No N 1024 numbers yet. Do not fill this table from the smoke.

| corner | INL ep (combined) [ppm] | union ep / bf [ppm] | verdict |
|---|---|---|---|
| c0 tt/27/3.3 nom | | | |
| c1 ss/-40/3.0 nom | | | |
| c2 ss/125/3.0 nom | | | |
| c3 fs/125/3.0 nom | | | |
| c3 fs/125/3.0 srknee (must REJECT) | | | |

## Pickup
```
ssh sandbox; R=/home/mempool/regr/tt/WO-63-e450ae2; cd $R; ls out/logs/POOL_DONE out/ALL_DONE; grep -L "EXIT=0" out/logs/job_*.log
grep -h "INL ep" out/gb/*/gbp_*.json >/dev/null; grep -h "INL ep" out/logs/job_*.log
grep -h "VERDICT\|broken copy\|COMBINE" out/gb/*/combine.out; head -c 600 out/gb/*/combine.out
```
If run.sh died before combining (ALL_DONE missing but POOL_DONE present), env as in run.sh, then for each d in
c0_nom c1_nom c2_nom c3_nom c3_srknee: `python design/c1_ota1/c1b_gateb.py out/gb/$d --mode prec --combine 6 --copy ${d#*_}`;
`find out -name '*.csv' -delete`.
