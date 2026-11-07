# v1-design work orders

| WO | Stage | Title | Owner files | Tier | State |
|---|---|---|---|---|---|
| WO-01 | S0 | infra: params.py, toolchain record, TT analog template precheck | design/, scripts/s0_*.sh, results/s0_* | review (pd-expert) | accepted as plumbing (11/11 with WO-02); gate closes after WO-01a |
| WO-02 | S1 | VREF / swing study; model: vlin in volts, white-noise gain split | model/iadc.py, model/studies/s1_*, model/tests/, results/s1_* | review (sd-adc-design-reviewer) | acceptance PASS; design review pending |
| WO-01a | S0 | fixes from pd-expert review + no hard-coded paths | design/params.py, design/tests/, scripts/s0_*.sh, results/s0_* | routine | dispatched 2026-11-07 |
| WO-03 | S2 | chop study (OTA vs system chop, incremental residual) | model/studies/s2_*, results/s2_* | review (sd-adc-design-reviewer) | dispatched 2026-11-07 |

| WO-04 | S1/S2→S3 | model ext + S1 v2 at D17 point | model/iadc.py, model/tests/, model/studies/s1_vref.py, s2_*.py, results/*_v2 | review | dispatched 2026-11-07 |

WO-01..03 were file-disjoint: WO-02 alone owns `iadc.py` and creates `model/studies/__init__.py`.
