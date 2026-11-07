# WO-44: one resumable "verify everything" driver for after an RTL change

Coordinator-written, 2026-11-07 13:20. Tier: routine. Runs last, after WO-39 and WO-43, so it wraps the final state of every suite.

## Why
User, 2026-11-07: "lets close verif fully, we might need to make rtl updates based on other submissions". After any RTL change, the whole closure (VC-1..VC-10) must be re-runnable without a day of hand dispatch. Today it is spread over make targets, tests/directed/run.sh, tb/formal/run.sh, tb/rvfi/run.sh, tb/eqy/run.sh, scripts/gl/night.sh, tb/gls_sdf/run_glitch.sh and the river_core sandbox drivers.

## Deliverable (files: scripts/verify-all.sh and docs/verification-runbook.md, both new; nothing else)
`scripts/verify-all.sh OUT=<dir> [STAGES="..."] [NETLIST=<nl.v> PNL=<pnl.v> SDFDIR=<dir>] [JOBS=4]`, run ON THE SANDBOX from a frozen tree.
* Stages, each resumable via `done.<stage>` and each writing `<stage>.verdict` (one line: PASS / FAIL / BOUNDED-OK / ERROR plus counts):
  1. unit: `make BUILD_DIR=<OUT>/unit test-all`, then `test-seeds SEEDS="1..8"`.
  2. directed: `tests/directed/run.sh` (plain and `+RF_X +RF_COLLIDE_X`), `run.sh soc`.
  3. formal: `tb/formal/run.sh` default list on both engines, plus `--nonvac` on every harness. Its verdicts are compared against a checked-in expected table (scripts/verify-all.expected, written from today's results). A changed verdict word fails the stage.
  4. rvfi: `tb/rvfi/run.sh` with the WO-38 solver families, plus the fault matrix (tb/rvfi/mutants.sh).
  5. mutation: `tb/mutate/run.py` on the files changed since a given base (`BASE=<git rev>`, default main). Reports lost kills against the last results.
  6. (only with NETLIST/PNL/SDFDIR) eqy: `tb/eqy/run.sh` with all stages and mutants. gl: `scripts/gl/night.sh` with PARTS "A B C D" and refs built. sdf: `tb/gls_sdf/run_glitch.sh`, all variants and corners.
  - river_core is NOT re-implemented here. The runbook points to the existing sandbox driver (~/regr/run-multi.sh via launch-multi.sh) with the exact command.
* Under the thermal watchdog (the script writes driver.sid; the runbook gives the launch line). No `tail -f`, no sleep loops. The last file written is `<OUT>/SUMMARY`, with one line per stage plus total wall time.
* docs/verification-runbook.md:
  - what each stage proves;
  - the verdict words (PROVED / BOUNDED / COVERED / NONVAC; BMC is never "proved");
  - the stated residuals (from WO-39's VPLAN text);
  - wall times from today's runs;
  - the post-harden order (harden -> STA -> EQY -> GL -> SDF);
  - what to update when the netlist changes (NL_MD5, the accounting table, the partition count, the GL refs).

## Addition (coordinator, 2026-11-07 13:30): EQY refit helper
The one manual step after every RTL change is EQY's refit (NL_MD5, accounting table, partition count; tie lists or FSM cut tables only when flops or FSMs were added). Add `scripts/eqy-refit.sh NETLIST=<nl.v>`. It:
* prints the new md5;
* derives the flop accounting (gold/gate/direct/rename/recode/removed) with tb/eqy/accounting.py;
* runs the read+lemma+fsminv stages;
* prints the partition count from the setup;
* emits a patch for NL_MD5, the EXPECT table and verdict.py's count.
It must refuse to auto-apply when the accounting shows new unmatched flops or a new recoded FSM: those need a person. Document it in the runbook.
Also put a table of "what to rerun after an RTL change, by file touched" in the runbook (each formal harness's FILES, riscv-formal on fyracore.v, mutation per file, netlist-side checks after any harden).

## Addition (coordinator, 13:35): QSPI-change checklist in the runbook
The next RTL change (user, 2026-11-07) is in src/qspi_ctrl.v (and possibly mem_ctrl.v): streaming flash reads as the default and an optional DDR/DTR mode. The runbook gets a section "After a QSPI change" listing:
* tb/qspi_pmod_model.v must model streaming reads and DTR, with the setup/hold check extended to DTR edges (the -DTR datasheet rows);
* test-qspi plus its QSPI_RUNS sweep, and the SoC directed suite at the rd_late/QSPI_DELAY corners;
* formal mem_flash (CS0 command set), mem_arb (a stream yields to data), mem_ld/mem_li (re-measure LD/LI with bounds_tb.v), mem_tcem (if PSRAM streams), qspi_strap;
* EQY refit (expect new FSM states: manual);
* GL A-D and SDF with the Pmod checks at all corners;
* the tb_sw benchmarks on the verilator branch for the CPI gain.

## Acceptance (sandbox)
* `STAGES="unit formal"` on a frozen tree of the branch head: both PASS, and formal matches the expected table.
* A broken copy (one catalogue mutant applied to src/ in the frozen tree) makes at least the formal or unit stage FAIL, and SUMMARY says which.
* Relaunching after deleting one done marker reruns only that stage.

## Commits (path-limited, no attribution trailer, no push)
1. `test: verify-all.sh, one resumable driver for the whole verification closure`
1b. `test(eqy): eqy-refit.sh derives the netlist md5, accounting and partition count for a new harden`
2. `docs: verification runbook (stages, verdict words, residuals, after an RTL change)`

Budget: 50 tool calls. Sandbox only (~/regr/vc/WO-44/), nice -n 10.
