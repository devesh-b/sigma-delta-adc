# WO-91 (C1): gate B solver convergence under D43c (precision and boost). 2026-11-15

Status: RUNNING (launched 05:52 IST; 41 jobs in 4 pools under the global 5-slot cap, ~45-60 min per O2 part at load ~7).
No OTA, netlist or current change. Code: `design/c1_ota1/c1b_gateb.py` (commit 1419218):
- `--vntol-div D` (tag `_V<D>`), `--tmax-div D` (tag `_S<D>`), `--method trap|gear` (tag `_M<m>`): one-axis third solver
  points on top of `--opt`. The WO-76 `--tight` set (reltol 1e-6 with vntol 1e-8) aborted (timestep too small), and O1
  `--tight` timed out at 20000 s, so the third point moves one axis only.
- `--copy srdeep` (prec only): all six bias ports scaled so the base SR is 0.6 x the 10.3 V/us floor = 6.18 V/us at 1.4 pF.
  The combine prints the broken-copy strength INL/gate and STRONG if >= 1.5 x gate (2.0 ppm).

## Why the third point is tighter
O2 = gear, reltol 1e-5, chgtol 1e-15, trtol 1, vntol 1e-6 V, abstol 1e-12, tmax min(2.5 ns, tau_cl/10) = 1.895 ns (deck).
- **V10** (primary): vntol 1e-7 V. 1e-6 V is ~0.24 ppm of the 4.096 V differential span, the same size as the O2 INL
  (0.12-0.165 ppm) being judged, and the ladder never tightens it (REVIEW-BOOK M7). 1e-7 V is ~0.024 ppm, 10x below the
  0.1 ppm resolution the gate needs. Confirmed in the deck: `.options ... vntol=1e-07`, `.tran ... 1.894702e-09`.
- **S2** (hedge, p2 only): tmax 1.25 ns (1.5x finer than the effective O2 step), all else O2.

## Frozen copy and pools
`/home/mempool/regr/tt/WO-91-1419218` (design/, golden/, model/, scripts/ at 1419218; `.spiceinit` num_threads=1).
| pool | jobs (in order) | out dirs (`out/`) |
|---|---|---|
| p1 | ss/-40 prec O2+V10 p2, p0, p4; fs/125 O2+V10 p0; ss/-40 O2+S2 p2; then waits for WO-76 `out/O2_DONE` and combines fs/125 O2 | c1_nom_O2V, c3_nom_O2V, c1_nom_O2S, wo76_c3_O2_combine.out |
| p2 | tt/27 prec O2 p0-5; tt/27 boost O1 p0-5; combines | c0_nom_O2, gb_c0_nom_O1 |
| p3 | ss/125 prec O2 p0-5; ss/125 boost O1 p0-5; combines | c2_nom_O2, gb_c2_nom_O1 |
| p4 | ss/-40 prec srdeep O2 p2, p4, p0, p1, p3, p5; fs/125 boost O2 p0-5; combines | c1_srdeep_O2, gb_c3_nom_O2 |
Boost runs use the current netlist, which equals the WO-52 netlist (no netlist.py / sizes_draft.py / params.py change since
bf4a565), with the WO-52 settings (mode boost, N 1024, m 21, 6 parts).

## D43c rules used
Accept a pair (A, B) if |A - B| <= tol = max(10 % INL, 0.1 (gate - INL)), INL = the tighter value. If not met, the D43c
verdict value is INL(B) (1 + |Delta| / INL(B)). Precision gate 1.333 ppm (3x margin 0.444); boost gate 5 ppm (3x margin 1.667).
ss/-40 O2 0.165: tol = max(0.017, 0.117) = 0.117 ppm, so V10 must lie in 0.048-0.282 ppm per part (O2 parts p0-p5: 0.142, 0.160, 0.160, 0.120, 0.164, 0.165;
`WO-76-f00f9bf/out/gb/c1_nom_O2/*.json`). Per-part tol uses each part's O2 value.

## Verdict table (fill from the pickup)
| corner / mode | O1 | O2 | third point | Delta | D43c | copies |
|---|---|---|---|---|---|---|
| ss/-40 prec | 1.706 | 0.165 (comb.) | V10 p2/p0/p4: PENDING; S2 p2: PENDING | O1->O2 1.54 | O1/O2 fails; O2/V10 PENDING | srdeep PENDING |
| fs/125 prec | 0.967 | p0 0.472, p1 0.463, p2-p5 PENDING (WO-76) | V10 p0 PENDING | ~0.5 | O1/O2 fails (tol 0.097) | srknee 1.375 (1.03x, weak) |
| tt/27 prec | 0.692 | PENDING | - | | | |
| ss/125 prec | 0.698 | PENDING | - | | | |
| tt/27 boost | WO-31 only (old netlist) | O1 PENDING | - | | | |
| ss/125 boost | WO-31 only | O1 PENDING | - | | | |
| fs/125 boost | 3.14 (WO-52) | PENDING | - | | | |
| ss/-40 boost | 0.71 (WO-52) | - (>3x margin) | - | | | |

## Pickup
```
ssh sandbox; R=/home/mempool/regr/tt/WO-91-1419218; cd $R; ls out/P*_DONE /home/mempool/regr/tt/WO-76-f00f9bf/out/O2_DONE
tail -n 2 out/logs_p*/pool.status; grep -h "INL ep\|EXIT" out/logs_p*/job_*.log | cut -c1-160
cat out/*/combine.out out/wo76_c3_O2_combine.out
grep -h '"inl_ep_ppm"' /home/mempool/regr/tt/WO-76-f00f9bf/out/gb/c1_nom_O2/gbp_nom_O2_N1024_p[024]o6.json   # O2 per part
```
If a run_pN.sh died after its lpool: env as in `run_pN.sh`, then the combine lines at the end of that file.
srdeep: `broken copy REJECTED (good)` and `STRONG` needed; part logs also say REJECTED per part.
