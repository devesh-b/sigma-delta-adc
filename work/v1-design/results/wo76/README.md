# WO-76 (C1): precision gate B fails at ss/-40, diagnosis. 2026-11-14

Input: WO-63, `/home/mempool/regr/tt/WO-63-e450ae2` (2 MHz, N 1024, m 21, O1, 6 parts, endpoint INL, gate 1.333 ppm).
No OTA, netlist or current change was made. Code: `design/c1_ota1/c1b_gateb.py` got two diagnostic flags (commit f00f9bf):
`--tight` (after the `--opt` ladder: reltol/10, vntol/100, abstol/100, tmax/2; tag `_T`) and `--bias-scale S`
(all six OTA1 bias ports x S, diagnostic deck only; tag `_dxS`).

## 1. WO-63 tables
Filled in `results/wo63/README.md`. ss/-40 1.706 ppm REJECT; tt 0.692, ss/125 0.698, fs/125 0.967 ACCEPT; srknee 1.375 REJECTED.
Every combine is healthy, endpoint spread <= 0.017 ppm. tt and ss/125 are also >= gate/2, so the O2 rule applies to them too.

## Per-point residual (endpoint line removed), ppm of FSR, u = -0.9 ... 0.9 step 0.09 (combined 21 points)
```
tt/27   0 -.05 -.11 -.14 -.20 -.30 -.54 -.66 -.37 -.30  .05  .33  .40  .68  .56  .32  .23  .16  .14  .07 0   gain -3.6e-5
ss/-40  0 -.62  .09  .17 -.32 -1.67 -1.26 -1.30 -.43 -.02 .05 .04  .44 1.33 1.27 1.71  .37 -.15 -.09  .66 0   gain -2.9e-5
ss/125  0 -.27 -.45 -.62 -.68 -.55 -.51 -.45 -.64 -.35  .26  .36  .65  .44  .52  .55  .70  .62  .45  .28 0   gain -4.4e-5
fs/125  0 -.30 -.46 -.56 -.78 -.77 -.80 -.97 -.55 -.50 -.04  .45  .51  .95  .76  .72  .75  .52  .42  .27 0   gain -4.4e-5
srknee  0 1.36 1.18  .47  .01 -.27 -.67 -.50 -.41 -1.14 -.04 1.15 .39  .50  .65  .26 -.01 -.48 -1.18 -1.37 0  gain -5.0e-5
boost ss/-40 (WO-52, 4 MHz):  0 -.22 -.27 .25 .48 .51 .38 .57 -.26 -.29 -.05 .19 .17 -.69 -.46 -.62 -.59 -.31 .22 .13 0
```
All shapes are odd (fully differential, as expected). tt/ss125/fs125 are a smooth S (a transfer nonlinearity of the GBW/
settling kind) plus <= 0.3 ppm of jitter. ss/-40 is not smooth: neighbours jump by up to 1.3 ppm (0.45 -> 0.54). That is
a step-history (bit-pattern) dependent error, not a static A(v) or a smooth settling error.

## 2. Numerical cause: PENDING (runs launched, see Pickup)
Frozen copy `/home/mempool/regr/tt/WO-76-f00f9bf` (HEAD f00f9bf; design/, golden/, model/, scripts/, `.spiceinit`).
Pool A (`jobs.txt`, `out/logs`, 16 jobs): 1-2 ss/-40 O2 `--tight` p2, p4 (the two parts holding the 1.71/1.67 ppm points);
3-4 ss/-40 O1 `--bias-scale 1.3` p2, p4; 5-10 ss/-40 O2 p0-p5; 11-16 fs/125 O2 p0-p5; then O2 combines into
`out/gb/c{1,3}_nom_O2/combine.out` and `out/ALL_DONE`. Pool B (`jobs_b.txt`, `out/logs_b`, MAXJOBS 1): ss/-40 O1
`--bias-scale 0.8` p2, p4, then `out/B_DONE`. Started 14:49-14:52 IST at box load ~7 (other users), so 1 slot each:
serial estimate O1 ~20-35 min, O2 ~1-2 h, tight 2-5 h per job, about 1 day in total; it shortens as the load drops.
Evidence so far against a numerical cause (not a substitute for O2): the endpoints are simulated independently in all
6 parts, with different neighbours and time steps, and agree to 0.005 ppm at ss/-40.
**Update 14:54:** job 1 (O2 `--tight`, p2) aborted after 288 s: "Timestep too small" at 0.76 us on `bph2#branch`
(reltol 1e-6, vntol 1e-8 is past the solver floor, as D43c found for reltol 1e-5 with chgtol 1e-15). Its INL 0.000 is
not a result (the log lists the problems). Job 2 (p4) will likely do the same. Replacement, pool C (`jobs_c.txt`,
`out/logs_c`, `out/C_DONE`): ss/-40 `--opt O1 --tight` p2 (reltol 1e-5, vntol 1e-8, abstol 1e-14, tmax 2.5 ns), which
tests the vntol axis that the O0-O2 ladder never tightens (vntol stays 1e-6 V, about 0.25 ppm of the 2 x 2.048 V span).
Decision rule (D43c): accept O1 if |O2 - O1| <= max(10 % INL, 0.1 (gate - INL)); `--tight` vs O2 the same.

## 3. Mechanism (interim, from WO-52 op/AC data, `/home/mempool/regr/tt/WO-52-bf4a565/out/opac/opac_*.json`, base mode)
| corner | A0 dB | GBW MHz lump / integ | PM deg lump / integ | fp2/GBW integ | SR V/us | f_cm MHz / PM_cm | gate B INL |
|---|---|---|---|---|---|---|---|
| tt/27/3.3 | 84.2 | 16.8 / 29.4 | 71.0 / 56.6 | 1.30 | 13.4 | 2.18 / 84 | 0.69 |
| **ss/-40/3.0** | **85.9** | 21.6 / **37.2** | 66.7 / **49.9** | **1.02** | 13.2 | 2.40 / 84 | **1.71** |
| ss/125/3.0 | 82.8 | 14.5 / 25.4 | 70.7 / 55.7 | 1.26 | 13.4 | 1.80 / 83 | 0.70 |
| fs/125/3.0 | 82.7 | 13.6 / 24.3 | 74.0 / 61.0 | 1.55 | 13.5 | 1.98 / 85 | 0.97 |
(lump = 1.4 pF SPEC basis; integ = real integrate-phase load ~0.85 pF; bias currents are ideal sources in the deck.)
- **A0 / gain nonlinearity: ruled out.** A0 is highest at ss/-40, and the in-loop gain error is smallest there (-2.9e-5 vs
  -3.6...-4.4e-5). A static A(v) gives a smooth cubic, as at 125 C, not the jagged ss/-40 shape.
- **Slew alone: unlikely.** Tail current and SR are the same at every corner (13.2-13.5 V/us), yet only ss/-40 fails.
- **CMFB: no sign.** f_cm and PM_cm are the best at ss/-40; f_z 0.43 MHz is info-only (D62), similar at all corners.
- **Leading hypothesis: phase margin in the integrate phase.** Cold raises input-pair gm (GBW 37 MHz) more than the fold-node
  pole, so fp2/GBW falls to 1.02 and PM to 49.9 deg, the lowest of all corners. Underdamped settling that re-enters slewing
  gives a pattern-dependent error, which matches the jagged shape. Not proven: a purely linear ring (fu.beta 32 MHz,
  zeta ~0.45) decays far below 1e-6 within t_half 225 ns, so the error needs a nonlinear step (slew re-entry, a cascode
  near the edge: m_n margin 0.095 V at ss/-40). The bias-scale pair tests it: dx0.8 lowers gm (PM up) and SR (10.6 V/us);
  dx1.3 raises both. dx0.8 better than nominal => PM; dx1.3 better => current/slew limited; both ~nominal => neither.
- **Why fine elsewhere:** 125 C has lower gm (PM 56-61 deg) and shows the smooth GBW-settling S; tt has PM 56.6 deg.
  Boost doubles every current (fold pole moves with gm) at a 5 ppm gate: the same jagged ~0.7 ppm term is there (row above)
  and is 7x under its gate, but half of 1.333.

## 4. Broken copy strength
srknee (fs/125, base SR 0.8 x floor) gives 1.375 ppm: 3 % over the gate, 1.42x the nominal 0.967, and only p0 and the
combine reject. A 5 % solver or model shift flips it, so it does not discriminate well. It is also a hot slew copy, while
the failure is cold and pattern-dependent. Proposals (not run): (a) `srdeep`, base SR 0.6 x floor (scale
0.6*10.3e6*1.4e-12/I_tail) at fs/125, with a rule that a broken copy must exceed the gate by >= 1.5x to count;
(b) a cold PM copy at ss/-40: an extra fold-node cap that pulls integrate-phase fp2/GBW to ~0.7 (PM ~40 deg); needs a
netlist hook. Both stay diagnostic copies, the nominal netlist is untouched.

## 5. Options (no change made). OTA1 base I_vdd 60.5 uA, tail 18.6 uA (ss/-40); fast-mode budget ~180 uA REASONED, 200 uA
| option | current | area | schedule | risk | expected ss/-40 INL |
|---|---|---|---|---|---|
| A. precision-only bias up (x1.3) | +~18 uA precision; fast: +~36 uA (~216 uA, over 200) unless the boost leg is held absolute (ratio 2/1.3), then 0 uA | mirror fingers | C6 ref + 4-corner gate B, ~1 day sandbox | wrong if PM-limited (raises gm) | from the dx1.3 run |
| B. constant-gm / PTAT share for OTA1 | 0 uA at 27 C, less at cold, +up to 33 % at 125 C on the PTAT share: fast at hot needs the share capped to stay <= 200 uA | ~1-2k um2 bias core + start-up | C6 redesign + C1 re-gates, several days | new bias block | ~tt level 0.7 ppm if PM (ASSUMED) |
| C. raise the fold-node pole by sizing (cascode W/L, fold share) | 0 uA | ~0 | OTA re-size + all C1 gates, 2-3 days | noise and fast-mode 5 ppm rows move | ~0.7 ppm if PM (ASSUMED) |
| D. more compensation (Rz/Cc) | 0 uA | small cap | 1-2 days | lowers GBW at fs/125, already the slow corner at 0.97 | fs/125 may exceed 1.333 |
| E. gate/basis change (USER decision): e.g. precision gate at ss/-40 judged at N 4096, or a cold-corner gate of 2 ppm | 0 | 0 | 0 | weaker spec | 1.71 ppm passes a 2 ppm gate |
Recommendation (provisional, pending O2 and the bias-scale pair): **C**, raise fp2 by sizing at 0 uA; it targets the only
property that separates ss/-40 and costs no budget. If dx1.3 helps and dx0.8 hurts, switch to A with the boost leg held
absolute. If O2/tight moves the result by > 10 %, it is numerical: rerun the gate at O2 and change nothing.

## Pickup
```
ssh sandbox; R=/home/mempool/regr/tt/WO-76-f00f9bf; cd $R; ls out/ALL_DONE out/B_DONE out/C_DONE out/logs/POOL_DONE out/logs_b/POOL_DONE
tail -n 3 out/logs/pool.status out/logs_b/pool.status; grep -h "INL ep\|EXIT" out/logs/job_*.log out/logs_b/job_*.log out/logs_c/job_*.log
cat out/gb/c1_nom_O2/combine.out out/gb/c3_nom_O2/combine.out
```
Compare per part: O2 p2/p4 vs O1 1.706/1.671 (WO-63 jobs 13, 23); `_T` vs O2; dx0.8 and dx1.3 vs O1 nominal.
If run.sh died after POOL_DONE: env as in `run.sh`, then
`python design/c1_ota1/c1b_gateb.py $R/out/gb/c1_nom_O2 --mode prec --opt O2 --n 1024 --combine 6 --copy nom` (and c3_nom_O2).
Residual shapes: `/tmp/wo76_shape.py DIR...` on the sandbox (prints per-point residuals; copy it into $R if /tmp is cleared).
