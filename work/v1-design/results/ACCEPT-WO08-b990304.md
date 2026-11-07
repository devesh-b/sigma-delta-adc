# WO-08 acceptance (S5b), frozen copy of tree at b990304

- Frozen copy: `/home/mempool/regr/tt/acc08-b990304`. It has no `.git`; its identity comes from the sync at b990304.
- Row 1 was run by the Haiku tester.
- Rows 2–8 were run by the coordinator via `run_rows.sh`, using direct ssh plus nohup with the rt-tt env (venv, nix ngspice).
  - The first launch without the env failed (no ngspice → KeyError). It was relaunched.
- Outputs went to `<copy>/out_rowN`, not to the shared WO-08 directory.
- Run checks (tstop, BAD_LOG scan, netlist audit) are built into `tier1_tb.py`: any problem forces REJECT. Every ACCEPT row therefore passed them.

| # | Command | Expect | Result | Evidence |
|---|---|---|---|---|
| 1 | `pytest design/tests -q` | pass | PASS: 27 passed | tester stdout |
| 2 | `--xcheck` | ACCEPT | PASS: ACCEPT, EXIT 0 | `row2.log` |
| 3 | `--av` | ACCEPT within 30 % | PASS: ACCEPT, EXIT 0 | `row3.log` |
| 4 | `--knees2` | table + flags | PASS: ACCEPT, EXIT 0. Flags do not set the exit code (review m9). | `row4.log`, `out_row4/` |
| 5 | `--cm` | CM log + CMRR table | PASS: ACCEPT, EXIT 0. The metric is flagged by review m1. | `row5.log`, `out_row5/` |
| 6 | `--offsets` | ACCEPT, sys residual ≤ 0.5 µV | PASS: ACCEPT, EXIT 0 | `row6.log` |
| 7 | `--rsrc` | table | PASS: ACCEPT, EXIT 0 | `row7.log` |
| 8 | `--nonvac2` | broken cases REJECT, nonzero exit | PASS: EXIT 1. Each broken case REJECTs:<br>• A(v) vsw 0.8 → 197 %<br>• sys pair one cycle late → −4800 µV<br>• no-D12 at Vin_cm 0.2 → vg CM [1.42, 2.54] leaves range | `row8.log` |

**Verdict.** 8/8 rows pass. The content gaps (C-M1, C-M3, C-M4, m1, m3, m9) are listed in REVIEW-S4S5b-2026-11-08.md.
