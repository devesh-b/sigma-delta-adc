# v1-design agents ledger

| Agent | Role | State | Next |
|---|---|---|---|
| reviewer (Opus) | sd-adc-design-reviewer: SPEC rev b + PLAN | DONE → REVIEW-spec-plan-2026-11-07.md; fixes a3db5b9; user decisions d6a86b2 | Q5, D3 (VREF), REF− pin open |
| coder WO-01 (Sonnet) | S0 infra | DONE: 684bb9c, fe4d46f, bcccf61; 6/6 self-checks; precheck 15/15 on dummy, met5 copy fails | Haiku acceptance + pd-expert review (running) |
| coder WO-02 (Sonnet) | S1 VREF/swing (F1 amendment applied) | DONE: 1b12a68, a602190; A, A2, B ACCEPT, C REJECT | Haiku acceptance (running); design review batched with WO-03 |
| coder WO-03 (Sonnet) | S2 chop study | DONE: 5de2ee1, d06b2f1; order 2 sys / ota+sys ACCEPT (≤0.8 µV @ 9 mV Vos); OTA-chop-only residual lf·Vos/(N−1), model = theory 54/54; order-1 verdict unresolved (quantisation-limited) | Haiku acceptance + design review (running) |
| Haiku tester 2 | acceptance WO-03 on frozen copy | RUNNING | — |
| reviewer (Opus) | design review of S1 + S2 results; D3/D4 recommendations | RUNNING | coordinator → user |
| Haiku tester | acceptance WO-01 + WO-02 @ d6a86b2 | DONE 11/11 PASS → results/ACCEPT-WO01-WO02-d6a86b2.md; found hard-coded paths | — |
| pd-expert (Opus) | review of WO-01 precheck flow | DONE → REVIEW-WO01-pd-2026-11-07.md (B-1, S-1..S-6) | WO-01a |
| coder WO-01a (Sonnet) | S0 fixes (A0 80, corners 63/135, DRC/pin broken copies, TT nix-shell precheck, GDS tie, no hard-coded paths) | RUNNING, budget 70 | Haiku re-acceptance → S0 closes |
