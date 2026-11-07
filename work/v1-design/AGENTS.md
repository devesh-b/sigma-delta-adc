# v1-design agents ledger

| Agent | Role | State | Next |
|---|---|---|---|
| reviewer (Opus) | sd-adc-design-reviewer: SPEC rev b + PLAN | DONE → REVIEW-spec-plan-2026-11-07.md; fixes a3db5b9; user decisions d6a86b2 | Q5, D3 (VREF), REF− pin open |
| coder WO-01 (Sonnet) | S0 infra | DONE: 684bb9c, fe4d46f, bcccf61; 6/6 self-checks; precheck 15/15 on dummy, met5 copy fails | Haiku acceptance + pd-expert review (running) |
| coder WO-02 (Sonnet) | S1 VREF/swing (F1 amendment applied) | DONE: 1b12a68, a602190; A, A2, B ACCEPT, C REJECT | Haiku acceptance (running); design review batched with WO-03 |
| coder WO-03 (Sonnet) | S2 chop study | DONE: 5de2ee1, d06b2f1; order 2 sys / ota+sys ACCEPT (≤0.8 µV @ 9 mV Vos); OTA-chop-only residual lf·Vos/(N−1), model = theory 54/54; order-1 verdict unresolved (quantisation-limited) | Haiku acceptance + design review (running) |
| Haiku tester 2 | acceptance WO-03 on frozen copy | RUNNING | — |
| reviewer (Opus) | design review of S1 + S2 results | DONE → REVIEW-S1S2-2026-11-07.md (M1–M3, m1–m7, E1–E5); applied to SPEC (D19) | WO-04 |
| coder WO-04 (Sonnet) | model ext + S1/S2 v2 at D17 | DONE: fec83da, a3fdf06, b05619f; INL B 3.63 ppm (N 4096, 80 dB, shared Cs); ref decap not needed if τ_ref ≪ t_half (100 ns/2 pF → 58 ppm); N 1024 floor ≈33 µV not removed by averaging, N 4096 ≈2 µV; noise ota+sys 1.9–3.5 µV @240 SPS | Haiku acceptance (running) |
| Haiku tester | acceptance WO-01 + WO-02 @ d6a86b2 | DONE 11/11 PASS → results/ACCEPT-WO01-WO02-d6a86b2.md; found hard-coded paths | — |
| pd-expert (Opus) | review of WO-01 precheck flow | DONE → REVIEW-WO01-pd-2026-11-07.md (B-1, S-1..S-6) | WO-01a |
| coder WO-01a (Sonnet) | S0 fixes + option B nominal + chop config | DONE: c682804, d0d5d3e, cd6ff13; 9 tests; precheck under TT nix-shell (magic 8.3.568, klayout 0.30.8); 5 broken variants each fail own rows; CI PDK 0536d02 also 15/15 | Haiku re-acceptance (running) → S0 closes |
