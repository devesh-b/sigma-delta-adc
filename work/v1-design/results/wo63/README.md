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
Filled by WO-76 (2026-11-14) from `out/gb/*/combine.out` in `/home/mempool/regr/tt/WO-63-e450ae2`. pool finished, ALL_DONE present.
All 30 part logs end with EXIT; the 7 EXIT=1 logs are srknee parts p1-p5 (each passes on its own) and
ss/-40 parts p2 and p4 (each REJECTs on its own). Every combine is healthy (no problems, endpoint spread <= 0.017 ppm).

| corner | INL ep (combined) [ppm] | union ep / bf [ppm] | verdict |
|---|---|---|---|
| c0 tt/27/3.3 nom | 0.692 | 0.686 / 0.589 | ACCEPT (>= gate/2, O2 needed) |
| c1 ss/-40/3.0 nom | **1.706** | 1.706 / 1.378 | **REJECT** |
| c2 ss/125/3.0 nom | 0.698 | 0.697 / 0.594 | ACCEPT (>= gate/2, O2 needed) |
| c3 fs/125/3.0 nom | 0.967 | 0.968 / 0.763 | ACCEPT (>= gate/2, O2 needed) |
| c3 fs/125/3.0 srknee (must REJECT) | 1.375 | 1.374 / 1.203 | REJECTED (good), margin only 3 % over the gate |

Per-part srknee INL p0..p5: 1.375, 1.180, 1.135, 0.044 (p3: points -0.54, 0, 0.54 sit on zero crossings of its residual), 1.153, 1.179 ppm;
only p0 and the combine reject. Gate rule: O1 >= gate/2 (0.667) needs O2 at tt (0.692), ss/125 (0.698) and fs/125 too;
WO-76 runs O2 at ss/-40 and fs/125 only. Per-point residuals and the WO-76 follow-up: `results/wo76/README.md`.

## Pickup
```
ssh sandbox; R=/home/mempool/regr/tt/WO-63-e450ae2; cd $R; ls out/logs/POOL_DONE out/ALL_DONE; grep -L "EXIT=0" out/logs/job_*.log
grep -h "INL ep" out/gb/*/gbp_*.json >/dev/null; grep -h "INL ep" out/logs/job_*.log
grep -h "VERDICT\|broken copy\|COMBINE" out/gb/*/combine.out; head -c 600 out/gb/*/combine.out
```
If run.sh died before combining (ALL_DONE missing but POOL_DONE present), env as in run.sh, then for each d in
c0_nom c1_nom c2_nom c3_nom c3_srknee: `python design/c1_ota1/c1b_gateb.py out/gb/$d --mode prec --combine 6 --copy ${d#*_}`;
`find out -name '*.csv' -delete`.
