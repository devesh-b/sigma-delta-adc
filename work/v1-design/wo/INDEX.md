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

WO-06 and WO-07 are file-disjoint (model/ vs design/). WO-01..03 were file-disjoint: WO-02 alone owns `iadc.py` and creates `model/studies/__init__.py`.
