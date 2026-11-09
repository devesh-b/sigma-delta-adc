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
