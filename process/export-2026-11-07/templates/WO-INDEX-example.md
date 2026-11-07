# Planner A work orders (VC-3 follow-up, VC-4, VC-6, VC-7, VC-9) — index, order, decisions

2026-11-07, planner A. Base `verif-close_alfadelta10010` fc6cf0a. Copies in
`localFiles/verif-close-2026-11-07/wo/`. Probes: `~/regr/vc/plannerA/p1` (run.sh under yosys 0.70),
`~/regr/vc/plannerA/p2` (sby smtbmc/pdr on syscon_gate, WD16, spi_core). 2 of 4 probes used.

## Order

| WO | goal | files | tier | depends on |
|---|---|---|---|---|
| WO-30 | run.sh: sidecars, FORMAL_BIN, sby engine (smtbmc/pdr), `--nonvac`, `--cover`; deeper csr / syscon_comb / spi_bb(1) / core_req (VC-4) | tb/formal/run.sh, tb/formal/*.nonvac, cover/invariant additions in existing *_props.sv | review | — |
| WO-31 | SoC properties: bus ready rule + decode; flash backstop, tCEM, tCPH, data-first, split, latency bounds; strap miter (QS06); core data-per-fetch bound (VC-6) | new tb/formal/{bus,mem*,qspi_strap,core_df}_props.sv + .conf + .nonvac | review | WO-30 commits 1-3 |
| WO-32 | MD07 / FC02 / FC49 equivalence proofs committed (VC-7) | new tb/formal/{md07,md07_miter,core_inv}_props.sv + .conf + .nonvac | review | WO-30 commits 1-3 |
| WO-33 | seeded floors by construction (TB-007 tb_uart, new TB-009 tb_spi seed 5) + SA-008 directed test (VC-3, VC-9) | tb/tb_uart.v, tb/tb_spi.v, tb/tb_syscon.v | review | — |
| WO-39 | run.py FORMAL map + formal-only mutation campaign + final-tree formal run; VPLAN + CLAUDE.md (shared: B's and C's text too) | tb/mutate/run.py, tb/VPLAN.md, docs/CLAUDE.md | review | WO-30..33 + planners B, C committed |

WO-30 and WO-33 can run in parallel from the start; WO-31 and WO-32 in parallel once WO-30's
commits 1-3 are accepted. One committer at a time.

## Decisions

1. **run.sh coexistence (D1).** run.sh stays the only runner and keeps run.py's contract
   (PROVED/BOUNDED/COVERED/FAILED/ERROR, exit 0/1/2); default engine stays yosys `sat`;
   `FORMAL_ENGINE=sby` generates the .sby from run.sh's own tables (one source of the
   expose/PRE recipe); new harnesses register through `tb/formal/<n>.conf` sidecars so WOs stay
   file-disjoint. Rejected: committed .sby files + a second runner (two sources of file lists and
   white-box scripts, a second contract for run.py).
2. **yosys (D2).** OSS CAD yosys 0.70+286 for both engines, reached through `FORMAL_BIN`
   (prepended to PATH inside run.sh only, so campaign simulators stay iverilog 12). Probe p1: all 14
   harnesses give the recorded verdict words under 0.70 in ~3.5 min. Finding: **csr is PROVED only
   at induction length 8** (not counted under the length-1 rule; WO-30 D1 fixes or reports it).
3. **PROVED rule (D3).** Counted: sat or sby-smtbmc k-induction at length 1, or sby `abc pdr`
   PASS (complete engine). smtbmc UNKNOWN at depth 1 = FAILED "did not close" (as sat's "Reached
   maximum"); pdr UNKNOWN/TIMEOUT = ERROR. Probe p2: pdr PASS syscon_gate / FAIL WD16; smtbmc d1
   PASS syscon_gate and spi_core (4 s) but UNKNOWN on WD16; pdr timed out on spi_core (280 s), so
   pdr is opt-in per harness and WO-31 plans a split-by-define fallback.
4. **Properties, spec, mode, non-vacuity.** Per property in WO-31 / WO-32 tables. Every harness has
   a committed `.nonvac` (catalogue mutant, hand-made sed, or a define) that must FAIL it, and
   antecedent covers that must be reached. Kills planned: SB01-03, QS01, MC01-04, MC07-08, QS06
   (a current survivor of every bench), QS02 (stretch).
5. **Liveness (decision 4).** No `mode live`. The QSPI Pmod has no device-side handshake (the engine
   is self-timed by clk), so no fairness assumption on the Pmod is needed; "no starvation" is proven
   as a bounded response by pdr (stronger). The one environment assumption is the core's
   data-per-fetch bound (M-A4, DF_N = 2); it is load-bearing (`def -DNO_DF_ASSUME` must FAIL) and
   is discharged on the core by `core_df`, **bounded** (BMC 24), since the core is not inductive
   without internal invariants.
6. **SA-008** is specified in docs/soc-architecture.md ("A kick or a TORR write in the very cycle of
   the third tick does not stop the fire"): WO-33 tests that text; no user decision needed.

## Findings to carry

* VC-3 run (95/96 at 01:31 IST, only tb_spi seed 8 still running): only `tb_spi seed=5` fails, "coverage floor missed: bytes
  B=79-253" -> **TB-009** (same class as TB-007). tb_uart seed 4 now passes (2dde982), but its floor
  is still luck, so TB-007 is closed by construction in WO-33, not by the green run.
* Docs gap: docs/soc-architecture.md "Arbitration" says one data request per fetch; mem_ctrl's
  header says two (fetch-word reuse). WO-31 uses 2; core_df measures the truth; WO-39 fixes the doc.
* Cross-planner: core_fetch's sed anchors on `output wire        dbg_trap$` in src/fyracore.v; if
  planner B's RVFI ifdef adds ports after it, core_fetch prints ERROR (loud, not silent). WO-32 uses
  `expose` by wire name to avoid this; WO-39 re-runs all core_* on the final tree.

## Question for the user

* Decision 3 extends the "PROVED only at induction length 1" rule to also count an `abc pdr` PASS
  (unbounded, complete; it finds an inductive invariant or a counterexample). The VC-6 latency and
  tCEM bounds need it (counters to ~250 do not close at length 1 without white-box invariants).
  Accept pdr PASS as PROVED?
