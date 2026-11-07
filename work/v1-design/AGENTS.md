# v1-design agents ledger

| Agent | Role | State | Next |
|---|---|---|---|
| reviewer (Opus) | sd-adc-design-reviewer: SPEC rev b + PLAN | DONE → REVIEW-spec-plan-2026-11-07.md; fixes a3db5b9; user decisions d6a86b2 | Q5, D3 (VREF), REF− pin open |
| coder WO-01 (Sonnet) | S0 infra | DONE: 684bb9c, fe4d46f, bcccf61; 6/6 self-checks; precheck 15/15 on dummy, met5 copy fails | Haiku acceptance + pd-expert review (running) |
| coder WO-02 (Sonnet) | S1 VREF/swing (F1 amendment applied) | DONE: 1b12a68, a602190; A, A2, B ACCEPT, C REJECT | Haiku acceptance (running); design review batched with WO-03 |
| coder WO-03 (Sonnet) | S2 chop study | RUNNING (5de2ee1 theory committed) | Haiku acceptance + design review |
| Haiku tester | acceptance WO-01 + WO-02 on frozen copy | RUNNING | coordinator reads verdicts |
| pd-expert (Opus) | review of WO-01 precheck flow | RUNNING | coordinator applies fixes |
