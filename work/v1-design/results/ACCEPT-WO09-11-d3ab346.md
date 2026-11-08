# Acceptance WO-09 / WO-10 / WO-11, frozen copy of tree at d3ab346

- Frozen copy: `/home/mempool/regr/tt/acc0911-d3ab346`, made with `cp -a` of `tt-sd` after the sync at d3ab346.
- Runner: `acc.sh`, using the full env (venv, nix ngspice, PDK_ROOT `.ciel`). Two queues:
  - tier-1 modes, run serially;
  - s4 with `--procs 2`.
- The coordinator launched and evaluated it. The Haiku testers had stalled on the rta-tt lock in the previous round.
- Finished 2026-11-08 18:35 IST.

| # | Command | Expect | Result | Evidence |
|---|---|---|---|---|
| 1 | `pytest design/tests model/tests -q` | pass | PASS: 90 passed, EXIT 0 | `pytest.log` |
| 2 | `tier1_tb.py --knees3` | separated knees; run-health ACCEPT | PASS: run-health ACCEPT, EXIT 0. 2 MHz OTA1 knee 8.9 V/µs (13.3 ppm), matching WO-09 | `knees3.log` |
| 3 | `--cm2` | closed form within 25 %; ACCEPT | PASS: ACCEPT, EXIT 0. Checks: runs_ok, closed_form_25pct, sign_discriminates, sys_off_60_at_alloc, sys_on_100 all True | `cm2.log` |
| 4 | `--drift` | vs closed form within 25 %; ACCEPT | PASS: ACCEPT, EXIT 0 | `drift.log` |
| 5 | `--rsrc2` | vs closed form within 30 %; ACCEPT | PASS: ACCEPT, EXIT 0 | `rsrc2.log` |
| 6 | `--xcheck` | A0 80 row at Roff 1e14; ACCEPT | PASS: ACCEPT, EXIT 0 | `xcheck.log` |
| 7 | `--nonvac3` | 3 broken cases REJECT; nonzero exit | PASS: EXIT 1. Each broken case REJECTs and its control passes:<br>• ΔCp 2 fF: 48.3 dB<br>• SR 6 V/µs: 1623 ppm<br>• 10 nA: −2.15 V | `nonvac3.log` |
| 8 | `s4_corners --out` | ACCEPT, exit 0 | PASS: all 4 gates ACCEPT, including sys-off CMRR on ε_eff per D36; EXIT 0 | `s4.log` |
| 9 | `s4_corners --nonvac` | REJECT, naming the ΔCp 2 fF copy; exit 1 | PASS: EXIT 1. 8/8 broken copies REJECT, including ΔCp 2 fF at 47.7 dB, Cs 3 % at 56.3 dB, and flip-after-swap sys-on at 61.5 dB | `s4nv.log` |

**Verdict:** 9/9 pass. The open content items are in REVIEW-S5c-S4close-2026-11-08.md and WO-12. Note that the S4 sys-on gate is a model metric floor (D37b).
