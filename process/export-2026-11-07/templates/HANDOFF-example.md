# Verification closing (VC) handoff, 2026-11-07

Branch `verif-close_alfadelta10010`, cut from main `a2f7285` (+ fc6cf0a, agent
notes only). RTL = main a2f7285 = the tree hardened 2026-11-01 as sandbox
project `fin-3x4` and ported to the submission repo. The coordinator (main
session) dispatches; this file is what every VC agent starts from.

## Goal

Close every open verification point of docs/ROADMAP.md (verilator branch copy,
sections 1.6 item 3, 2.2, 2.3) and tb/VPLAN.md's open list, on this tree:

| ID | Item | Owner |
|---|---|---|
| VC-1 | EQY: RTL vs the fin-3x4 netlist; cut points, tie lists, no-match list, NL_MD5, accounting table refitted (tb/eqy, WO-24 method) | planner C |
| VC-2 | scripts/gl parts A-D on the fin-3x4 pnl netlist | RUNNING (coordinator) |
| VC-3 | 8-seed run of the seeded unit benches (seeds 1-8), incl. TB-007 (tb_uart seed-4 floor) | RUNNING; fixes planner A |
| VC-4 | tb/formal harnesses as .sby (sby + bitwuzla/yices), then deeper BMC, cover, liveness where it adds signal | planner A |
| VC-5 | riscv-formal through an RVFI port (`ifdef RISCV_FORMAL`, zero area) | planner B |
| VC-6 | SoC properties: soc_bus (an IO target drops ready only while selected), mem_ctrl (data-first, no starvation, bounded), qspi_ctrl (tCEM, never selects flash for a write) | planner A |
| VC-7 | MD07 / FC02 / FC49 equivalence proofs as tb/formal harnesses (today only a recipe in agent memory vplan.md) | planner A |
| VC-8 | TT01 / pin glitch: tb_tt_um stopped-clock reset on the SDF-annotated fin-3x4 netlist, monitor uo_out/uio_oe for a glitch at the first edge (VPLAN 4.2 open list; recipe memory sdf-gls-icarus, localFiles/setup-timing-2026-10-14/tools/gls-sdf) | planner C |
| VC-9 | SA-008: a watchdog kick in the fire cycle does not stop the fire; no test (VPLAN open list) | planner A |

Not in scope: F1 (accepted), F11 (board question), RTL changes other than
VC-5's ifdef'd RVFI port, area items (FC02/FC49 removal is an area decision).

## Sandbox (USER RULE 2026-11-07: all verification on the server)

"localhost does not have power or space": every simulation, proof, synthesis
and regression runs on the sandbox, coder self-checks included. Local machine
= edit, commit, dispatch only.

* `ssh sandbox` (mempool@mempool.lan), 6 cores, 29 GB RAM, 63 GB disk free
  (93% used: keep outputs small, delete scratch).
* Work dirs under `~/regr/vc/` only. Each agent owns `~/regr/vc/<WO-id>/`.
  Push a working tree: `rsync -a --delete --exclude build/ --exclude localFiles/
  --exclude <confidential-dir>/ --exclude .git/ ./ sandbox:regr/vc/<WO-id>/tree/`.
  Frozen acceptance tree: `git archive <hash> | ssh sandbox "mkdir -p
  regr/vc/<WO-id>/acc-<hash> && tar -x -C regr/vc/<WO-id>/acc-<hash>"`.
* Frozen copy of this branch: `~/regr/vc/repo` (fc6cf0a).
* Tools: iverilog 12 `/usr/bin/iverilog`; iverilog 13 `/home/mempool/tt/iverilog13/usr/bin`;
  RISC-V gcc `/home/mempool/tools/rv64-gcc-elf/bin`; Spike `/home/mempool/tools/rv32-isa-sim/bin`;
  **no yosys on the default PATH**: formal uses OSS CAD Suite 2026-11-01 (yosys 0.70, sby,
  eqy, bitwuzla 0.9.1, yices 2.7.0, z3, boolector) via `source ~/tools/oss-cad-suite/environment`
  in the proof shell ONLY (it puts its own iverilog/verilator first). tb/eqy runs
  inside docker `ghcr.io/librelane/librelane:3.0.14` (yosys/eqy 0.62) as its run.sh does.
  Verilator `~/tools/verilator` (5.031). GitHub is reachable (riscv-formal clone).
* Netlists (fin-3x4, LibreLane 3.0.14): `/home/mempool/tt/projects/fin-3x4/runs/wokwi/final/{nl,pnl}/tt_um_alfadelta10010_alphaone_soc.{nl,pnl}.v`
  (pnl md5 5862cf7620e7a1d8c053154ee426fd1c); SDF/SPEF under `.../final/`.
  PDK `/home/mempool/tt/pdk` (ciel version 8afc8346...).
* Long runs: `setsid nohup` driver writing `driver.sid`, plus
  `M=<dir> setsid nohup bash ~/regr/thermal-watch.sh` (kills the session above
  80 C, writes TRIPPED). Resumable stages (`done.<stage>`): the box reboots
  uncleanly and zeroes recently written files; after a reboot (`uptime -s`
  changed) checksum-rsync the tree before trusting it.
* CPU budget: GL night (VC-2) uses 4 cores until it finishes (est. 5 h from
  01:05 IST 11-07). Until then each agent: one job at a time, `nice -n 10`.

## House rules (every agent)

* Never bare `make clean` (it is `rm -rf build/`): `make BUILD_DIR=build/<own> clean`.
* Stage explicit paths only; never `git add -A`/`-a`, never stage README.md or
  other agents' memory. No attribution trailer of any kind in commits (no
  Claude-Session, no Co-Authored-By). Atomic commits. Never push.
* No `git stash`, no `pkill`/`killall` (exact PIDs), no sleep/poll loops left behind.
* Never name or sync `<confidential-dir>/`.
* Do not edit `src/` (only VC-5's coder, inside `ifdef RISCV_FORMAL`, after review).
* Formal soundness traps already paid for: a yosys hierarchical reference
  `dut.x` in a harness is an implicit UNDRIVEN wire (proof about a free signal)
  and `bind` asserts never reach sat: read internals only via `expose` or the
  sed-added ports that tb/formal/run.sh uses. An EQY/sat PASS counts only at
  induction length 1 (undefined init makes longer inductions vacuous). Every
  new property needs a mutant or broken copy that it FAILS on (non-vacuity),
  and every cover a reached trace.
* Durable results go under `localFiles/verif-close-2026-11-07/` (local) as well as the WO.

## Pipeline (user rule)

Opus specialist plans and reviews (writes work orders, short time-boxed probes
only); Sonnet coder implements one WO, self-checks on the sandbox, commits;
Haiku runs acceptance on a frozen tree on the sandbox and reports PASS/FAIL
per expectation with deviating lines verbatim. One committer at a time.
WO numbering continues at WO-30. WO format: goal + target, spec source,
exact files the coder may touch (file-disjoint between WOs), design with
expected values, sandbox acceptance commands with expected output, commit
plan, tier ("routine" / "review before accept"), dependencies.
WOs go to `build/wo/WO-nn-*.md` and a copy to `localFiles/verif-close-2026-11-07/wo/`.

## Pointers

* tb/VPLAN.md (requirements, mutation verdicts 4.2, open list), tb/formal/run.sh
  header, tb/eqy/run.sh header, scripts/gl/*.sh headers, docs/CLAUDE.md.
* Agent memory `.claude/agent-memory/rtl-verification-engineer/` (vplan.md has
  the MD07/FC02/FC49 proof recipe; env.md; coverage-holes.md).
* EQY history: build/wo/WO-24-eqy-rtl-vs-pnr.md, build/wo/WO-24-handoff-2026-10-27.md;
  last EQY: 157/157 on the PR #12 netlist (sc-3x4, 10-25). The WO-24 planner
  grew to ~800k tokens chasing partition failures: USER RULE, no open-ended digs.
* GL history: ~/regr/gl/night-2026-10-28 (183/184, ma_data known), ~/regr/gl/partD-20261030b.
