# v1-design work orders

| WO | Stage | Title | Owner files | Tier | State |
|---|---|---|---|---|---|
| WO-01 | S0 | infra: params.py, toolchain record, TT analog template precheck | design/, scripts/s0_*.sh, results/s0_* | review (pd-expert) | ACCEPTED; S0 closed with WO-01a |
| WO-02 | S1 | VREF / swing study; model: vlin in volts, white-noise gain split | model/iadc.py, model/studies/s1_*, model/tests/, results/s1_* | review (sd-adc-design-reviewer) | ACCEPTED, reviewed |
| WO-01a | S0 | fixes from pd-expert review + no hard-coded paths | design/params.py, design/tests/, scripts/s0_*.sh, results/s0_* | routine | ACCEPTED 6/6 (acc1a-cd6ff13) |
| WO-03 | S2 | chop study (OTA vs system chop, incremental residual) | model/studies/s2_*, results/s2_* | review (sd-adc-design-reviewer) | ACCEPTED 3/3 (acc3-c75aa91), reviewed |

| WO-04 | S1/S2→S3 | model ext + S1 v2 at D17 point | model/iadc.py, model/tests/, model/studies/s1_vref.py, s2_*.py, results/*_v2 | review | ACCEPTED 4/4 (acc4-a8b3c1e) |
| WO-05 | S3 | error budget → per-block specs; params at decided point | design/params.py, design/tests/, model/studies/s3_budget.py, model/tests/test_s3_budget.py, results/s3_budget.* | review | ACCEPTED 4/4 (acc5-446cc9c), reviewed — S3 closed |
| WO-06 | S4 | corner-aware tier 0 + iadc hooks (OTA2 gain, A(v) table, ref R_ext, reset memory) + s3_budget fixes | model/ | review | dispatched 2026-11-07 |
| WO-07 | S5 | tier-1 ngspice SC modulator, simulator null test, OTA requirement sweep | design/tier1/, design/params.py (SPICE options), design/tests/test_tier1.py | review | dispatched 2026-11-07 |
| WO-08 | S5b | tier-1 extensions from S5 review | design/tier1/, design/params.py, design/tests/test_tier1.py, results/s5* | review | dispatched 2026-11-07 |
| WO-06a | S4 | re-gate with user limits D27–D30, CMRR axis | model/studies/s4_corners.py, model/tests/test_s4_corners.py, results/s4_corners.* | routine | dispatched 2026-11-07 |

WO-06 and WO-07 are file-disjoint (model/ vs design/). WO-01..03 were file-disjoint: WO-02 alone owns `iadc.py` and creates `model/studies/__init__.py`.
| WO-09 | S5c tier-1 follow-ups (C-M1 separated knees, C-M3 Cp,top, C-M4 drift, m1/m3/m6/m7/m9) | review | dispatched 2026-11-08 |
| WO-10 | S4 close: ε_eff CMRR term (D33), margin columns | routine | dispatched 2026-11-08 |
| WO-11 | S5c write-up + S4 D36 RSS | routine | dispatched 2026-11-08 |
| WO-12 | S5d verification gaps (R1 R2 R4 R6 R7 R9) | review | dispatched 2026-11-08 |
| WO-13 | model residue-frame + Ck topology fixes, S3/S4 reruns, fast-mode option runs | review | dispatched 2026-11-08 |
- WO-14 S5e follow-ups (gm-boost realism, V4 margin point, S3 A\/B, small fixes): dispatched 2026-11-08
- WO-15 S5g boosted-point runs, INL-vs-GBW2 trend, gm/Id tooling: dispatched 2026-11-09
- WO-16 S5h convergence rule + margin-critical reruns + fp2 window + W/L fix: done 2026-11-09 (S5h results, REVIEW-S5h, D44)
- WO-17 S6 golden vectors (generator, independent checker, mutants, frame tags, order-1 u_corr): dispatched 2026-11-09
- WO-18 S6b golden v2 (D45 conventions, control trace, edge streams, REVIEW-S6 mutants): dispatched 2026-11-09
- WO-19 S7 SPEC freeze edits (E1-E24, digital I/O 16-bit bus, step-gate threshold): dispatched 2026-11-09
- WO-20 C1a OTA1 + CMFB design note (block recipe step 1; reviewed before schematic): dispatched 2026-11-09
- WO-21 C1a rev B (OTA1 note revision per REVIEW-C1a): dispatched 2026-11-09
- WO-22 macro/model scans (single-pole GBW, pole order, boost A0 floor): dispatched 2026-11-09
- WO-23 C1a rev C (A(v) tables through model INL, bias-diode fix, swing fix): dispatched 2026-11-09
- WO-24 C1b part 1 (sync, precision A0 sweep, netlist generator, op/AC 9 PVT x 2, first gate B point): dispatched 2026-11-10; done 2026-11-10 (results/wo24, D58)
- WO-25 C1b part 2a (D58 ref scale + replica cascode bias, D55 revert, gate B close-out + rerun): written 2026-11-10, waiting on sandbox access
- WO-26 C1b part 2b (D59 parallel 1:8 refs, K_P 12.5, replica fix, SR/K_P/V_OCM rows, gate B 4 corners): dispatched 2026-11-10
- WO-27 C1b part 2c (D60 recentre, CM error amp, tb9, mismatch allotments, review minors): dispatched 2026-11-10
- WO-28 C1b part 2d (D61 dual-path CMFB, larger refs, tb9 start-up fix, WO-27 leftovers): dispatched 2026-11-10
- WO-29 C1b part 2e (D62 rows, tb9 SC CM offset diagnosis, cold-corner op, combine() broken-copy rule, gate B on WO-28 netlist): dispatched 2026-11-10
- WO-30 C1b part 2f (D63 tb9 rows, CM-to-DM leakage, open tb9 items, gate B): dispatched 2026-11-11
- WO-31 C1b part 2g (D64 Cr x2, op/AC + tb9 reconfirm, gate B): dispatched 2026-11-11
- WO-32 C1b part 3a (D65: SPEC CL entries, SR floor re-base, TG clamp, CM-to-DM bound + mismatch copy, near-knee copy): dispatched 2026-11-11
- WO-33 C9a golden v3 (G3 items 1-4, 6): dispatched 2026-11-11 (parallel to C1)
- WO-34 C9b independent verification plan (rtl-verification-engineer): dispatched 2026-11-11
- WO-35 C9c (D66 contract → SPEC CL + golden v3.1): dispatched 2026-11-11
- WO-36 C1 start-up row (D68) + close WO-32 gate B: dispatched 2026-11-11
- WO-37 C9d RTL (Sonnet): dispatched 2026-11-11
- WO-38 C9e cocotb TB + Ref A + formal (rtl-verification-engineer, independent of RTL): dispatched 2026-11-11
- WO-39 C1 clamp copies in the tb9 event deck (D69): dispatched 2026-11-12
- WO-40 C9f D70 alignment + RTL mutation + coverage (rtl-verification-engineer): dispatched 2026-11-12
- WO-41 C1 noise (tb7: thermal, 1/f, chopper residue, tier-0 feed): dispatched 2026-11-12
- WO-42 C9g verification closure (F01, functional bins, 200 seeds, soak, X-init, full golden, CDC note): dispatched 2026-11-12
- WO-43 C1 sink-noise reduction (D71) + tb7 fixes + reruns: dispatched 2026-11-12
- WO-44 C3a comparator design note + spot sims: dispatched 2026-11-12 (parallel)
- WO-45 C6a bias/trim/start-up design note + spot sims: dispatched 2026-11-12 (parallel)
- WO-46 C4a switches + phase gen (+C7 level shifters) design note + spot sims: dispatched 2026-11-12 (parallel)
- WO-47 C9h hardening plan + synth probe (pd-expert): dispatched 2026-11-12 (parallel)
- WO-48 C3b revise per D74 + netlist + full tb (9 PVT + MC): dispatched 2026-11-12
- WO-49 C9i RTL D72+D74 (Sonnet) then bench + WO-42 leftovers (verif): dispatched 2026-11-13
- WO-50 C6b bandgap start-up fix: dispatched 2026-11-13
- WO-51 C3c offset re-base (D75), stress stimulus, asym kick: dispatched 2026-11-13
- WO-52 C1 L8 + noise row re-base (D75) + tb7 op fix + test fixes + reruns: dispatched 2026-11-13
- WO-53 S-model order-1 delay study (D76): dispatched 2026-11-13
- WO-54 C4b revise + netlist + tb (REVIEW-C4a, D76): dispatched 2026-11-13
- WO-55 C6c robust bias start-up / re-architecture (fresh agent): dispatched 2026-11-13
- WO-56 C3d stress fix without breaking function (fresh agent): dispatched 2026-11-13
- WO-57 C9 acc2 24 b (D77): done 346995c (CL-32)
- WO-58 C9 re-verify (A) + first full PnR (B, pd-expert): dispatched 2026-11-13
- WO-59 design book (DESIGN_BOOK.md, writer agent; reviewer accuracy pass after): dispatched 2026-11-13
- WO-60 C9 timing fixes (D79): A flow-only PnR dispatched 2026-11-13; B RTL after WO-58A
- WO-61 C1 finish the WO-52 reruns (op/AC path bug, tb7 summary crash): dispatched 2026-11-13
- WO-62 design book fixes: done (uncommitted, signing)
- WO-63 C1 precision gate B: running
- WO-64 C6d close option (c): dispatched 2026-11-13
- WO-65 C3e close rev d (D80 stress row, T5 copy): dispatched 2026-11-13
- WO-66 C9 PnR on the retimed RTL: dispatched 2026-11-13
- WO-67 C9 DRV closure (fanout/slew/cap) on the retimed macro: dispatched 2026-11-13
- WO-68 C3f latch Vds + T5 per D81 + close: dispatched 2026-11-13
- WO-67 done (9413a36, 80bb74d): the buf_1 ban made things worse; reverted in 8ddea05
- WO-69 C9 heuristic diode insertion off (single change): dispatched 2026-11-13
- WO-70 C4c tb netlist bug fix + rerun + D78 Sg re-split: dispatched 2026-11-13
- WO-69 done (7841d57): heuristic diodes off
- WO-71 C9 CTS sink clustering <= 10 (single change): dispatched 2026-11-13
- WO-71 done (fe8b8bf, 401fb33): CTS clustering 8, fanout 0
- WO-72 C9 post-GRT design repair (single change): dispatched 2026-11-13
- WO-72 done (8898159): post-GRT repair no effect
- WO-73 C9 slew margin PnR run (D84): dispatched 2026-11-14
- WO-74 C9 VAPWR counter RTL (D85) + SPEC CL for D82/D83/D85: dispatched 2026-11-14
- WO-74 done (76fe624, df9bded): lint/synth clean, 259 FF (+28), 1068 cells (+102)
- WO-75 C9 bench for D85 + full regression: dispatched 2026-11-14
- WO-73 done (9def89a, f58d6eb): slew 43 to 32, waived (D86)
- WO-63/61/68/70/64 collected 2026-11-14: C1 prec gate B ss/-40 1.71 ppm REJECT (others pass); tb7 all REJECT on 'noise op != op' lint + blind broken copies; C3 T8 single-peak rule still in checker; C4 28/89 EXIT=1; C6 MISMATCH 18 (125 C SIMFAIL, fast-ramp dev metric)
- WO-76 C1 precision gate B diagnosis + options (Opus): dispatched 2026-11-14
- WO-77 C1 tb7/op-AC mutant bench fix (Sonnet): dispatched 2026-11-14
- WO-78 C3g T8 per D83 + off-expectation rows (Opus): dispatched 2026-11-14
- WO-79 C4d triage + inj abort + D82 (Opus): dispatched 2026-11-14
- WO-80 C6e MISMATCH 18 + R1 144.8 verify (Opus): dispatched 2026-11-14
- WO-75 resumed after network drop (pool done, collecting)
- WO-77 handed off (0328c57): tb7 noise deck nodeset from op, mutants split per deck; pool /home/mempool/regr/tt/WO-77-87a05a2/out/logs/POOL_DONE, pickup in results/wo77/README.md (coordinator collects)
- WO-76 handed off (f00f9bf): diag interim, lead hypothesis integrate-phase PM 49.9 deg at ss/-40; O2 + bias-scale 0.8/1.3 + tight pools in /home/mempool/regr/tt/WO-76-f00f9bf (out/ALL_DONE, B_DONE, C_DONE), ~1 day; options A-E, provisional C; user decision after dx results. Rule slip: one empty local python3 - (no effect)
- D87 (C3 T8 basis + rev f clamp) logged; WO-81 C3h dispatched 2026-11-14
- WO-79 handed off (139a29d, a228a8f): 28 fails all timestep aborts (ideal sources on pF; soften() fix); tim second abort (HV model dbody, gear exp pending); D82 rating row + copies; ff/100 leak 23.4 pA vs 20 pA row FAIL -> user decision after rerun confirms. Pool /home/mempool/regr/tt/WO-79-139a29d/run/pool; next: fresh agent from results/wo79/README.md Pickup
- WO-75 done (2e0a43c..196f122): golden v3.2 kept via defparam bench, d_hold01-04 PASS, mutants 76/77 killed (M64 equiv), F18 proven small widths, suite/C9_FULL/R-01/GL quick PASS; open: X-01 + Verilator (defparam of parameter rejected), F18 real widths. AMB-30/31 -> D88. WO-82 C9u (D88 RTL+CL-37) dispatched
- WO-82 done (baa0706): D88 RTL one line, 259 FF, 1077 cells, CL-37. WO-83 C9v bench for D88 dispatched
- WO-81 handed off (fe9e787, 600c547, 0bf4d4c): rev f keeper pfet 0.42/0.15; st_tt27_a S 1.980284 (subtracted basis), P 2.2206 on real edge, Sb3 143.8 ns; pools pending. WO-84 C3i (residuals, stiff-supply basis check) dispatched
- WO-79 rerun: tim jobs 1-4 abort at HV dbody/sbody (6.25e-23 timestep). WO-85 C4e (tim abort fix + collect) dispatched
- WO-84 handed off (d651488, 7e83397, e03e927): stiff switched pin (10 ohm ramp then 1 mOhm switch, sup=sw) adopted by coordinator as D87(a) basis; rev f st_tt27_a on stiff pin: S 1.980344 V (op/on), P 2.2240 V, D 144.3 ns (nb2/ob2) -> real residual, injection path unnamed; kp2 + tight + copies queued. Pools: WO-78-1f18fa6, WO-81-fe9e787, WO-81-600c547, WO-84-d651488, WO-84-7e83397. Next: fresh agent after pools (collect, name the path, kp2 verdict); sub-mV sustained excess may become a user rule question (lesson 4) once confirmed
- WO-85 handed off (6aab377, d6510fd): tim abort = 1 ohm undecoupled supply (soften), fix supplies=False in deck_tim; tim rerun 54 jobs /home/mempool/regr/tt/WO-85-6aab377 (~9 h); WO-79 pool's ~55 tim jobs will abort (ignore); collect + SPEC rows + 20 pA pending
- WO-80 handed off (1153e82, c4f73c2): 125 C SIMFAIL = gmin 1e-15 (fix gmin 1e-12 tran only); fast-ramp rows REJECT on rises==1 (real: bias_ok 0.77 us pulse at VDD ~1 V, q not held low); R1 144.8 TC -2.56/+0.08 %, I0 1.0677 uA, own 4.34-4.96 uA, trim OK; pool /home/mempool/regr/tt/WO-80-1153e82 (77 jobs). Coordinator: CL-36(b) re-arm answered by D88 (drop before release restarts count); oldhint copy -> must be replaced by a hint that really breaks (not INFO); rises gate (a) vs (b) -> user after slow-ramp pulse widths. 2026-11-14 user: global lpool cap GMAX 5 + stop WO-79 tim jobs; sandbox unreachable (banner timeout) at ~17:40
