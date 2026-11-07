# WO-33 — Seeded-bench floors by construction (TB-007, TB-009) and the SA-008 test (VC-3 follow-up, VC-9)

Tier: **review before accept** (Part A changes the random stimulus of two seeded benches and what their floors mean; Part B is routine).
Base: HEAD of `verif-close_alfadelta10010` (fc6cf0a or later). Planner A, 2026-11-07.
Sandbox work dir: `~/regr/vc/WO-33/`. House rules: build/wo/VC-HANDOFF.md (`make BUILD_DIR=build/<own> ...`, never bare `make clean`).
Dependencies: none. File-disjoint from WO-30/31/32 and from planners B/C.

## Files the coder may touch

`tb/tb_uart.v`, `tb/tb_spi.v`, `tb/tb_syscon.v`. Nothing else (the Makefile already defaults
`SEEDS` to 1-8; VPLAN/CLAUDE.md text goes to WO-39).

## Evidence (VC-3 run, `~/regr/vc/seeds/results.txt`, frozen fc6cf0a, seeds 1-8, 12 benches)

At 01:31 IST, 95 of 96 runs done (tb_spi seed 8 still running): **one failure**, `FAIL tb_spi seed=5 ... FAIL coverage floor
missed: bytes B=79-253`. tb_uart seeds 1-5 PASS, including seed 4: TB-007's symptom ("too few
breaks: 8 sent") is gone since 2dde982 (floor 10 -> 5, BI counted on clearing reads), but its
cause is not: the floor still rests on luck (tb_uart.v:1583 "Breaks sent per seed run 8-15, so
the floor is 5" is an observation over a few seeds, not a guarantee). tb_spi has the same defect
(tb_spi.v:781: "seeds 1-4 reach 8, 10, 5, 13" — tuned to seeds 1-4), and seed 5 misses it.
New ID for the coordinator: **TB-009** (tb_spi random-phase floors not guaranteed). The coder
first reads the final results.txt (RUN_DONE) and adds any other floor failure there to Part A.

## Part A — every floor holds for every seed, by construction

Rule: a coverage floor in a seeded bench must be met by every seed. Lowering a floor is not a fix
unless a derivation in the comment shows the stimulus guarantees the new value.
Design: quota steering in the random phase. For each floored bin keep `need = floor - got`; when
the operations left can only just cover the outstanding needs (`ops_left <= sum(need_i * cost_i)`
plus a margin), the next operation is forced to the most-behind bin instead of drawn. Cost = the
operations one bin hit takes (tb_spi: one transfer at that baud; tb_uart: a break **followed by
the LSR read that clears BI before the next break**, so every forced break also gives one
`bi_seen`). Steering affects only the tail of the phase, so seeds that already met the floors see
little change. Print per run `steered <n> of <N> random ops` next to the existing counters.
Floors and their values stay as they are: tb_uart `rx_breaks >= 5 && bi_seen >= 5`
(tb_uart.v:1587), tb_spi every `floor(...)` call (tb_spi.v:865-870 and any other). Note that the
stimulus per seed changes (rd8/idle and the new draws consume `$random`); that is accepted.

Non-vacuity (the benches still catch what they caught): on a frozen tree, before and after,
`python3 tb/mutate/run.py --file uart.v --benches unit --results build/mut/wo33-uart-<tag>.tsv`
and the same for `spi.v` and `gpio.v`; no mutant killed before survives after (compare with
`--report`; the C7 results in `localFiles/c7-mutation-2026-10-31/` are a second baseline).

## Part B — SA-008: a kick or a TORR write in the fire cycle does not stop the fire

Spec: `docs/soc-architecture.md`, watchdog "Accuracy" and the **SA-008** paragraph ("A kick or a
TORR write in the very cycle of the third tick does not stop the fire. The reset still comes within
the bound above"); REQ-SYS-015/016. tb_syscon drives `wdt_tap = tc[15:0]` from a free-running
counter (tb_syscon.v:22-28), so the cycle of each tap rising edge is known in advance.
Directed cases (a new section; each checked against the bench's spec model as well — if the model
and the DUT disagree, report it and triage, do not bend the model):

| case | stimulus | expected |
|---|---|---|
| K1 | EN set; after the second tick, a CRR write of 0x76 (lane 0) on the clock of the third tap rising edge | the fire happens: `rq` on that edge, two-edge reboot, RESET_CAUSE.WDT set after it, watchdog disabled with TOP 15 (REQ-SYS-016) |
| K2 | the same with a TORR write in that clock | the fire happens, same checks |
| K3 | the kick one clock **before** the third tap edge | no fire; the next fire comes after three further tap edges counted from the kick, inside (2Pt, 3Pt+1] (REQ-SYS-015) |
| K4 | CRR write of a value != 0x76 in the fire clock | fire (not a kick) |

Add a counter `kick in fire cycle` (any CRR-0x76 or TORR write on a clock where `fire` would be
predicted by the model) and print it per run with the random phase's count, so the gap the directed
cases close is visible.
Non-vacuity: two broken syscon copies, built with `make SRC_DIR=<copy> BUILD_DIR=build/wo33-nv test-syscon`:
`fire = en & tick & (cnt == 2'd2) & ~rst_soc & ~kick` ("a kick wins") must FAIL (K1), and the same
with `& ~w_torr` must FAIL (K2). Report the FAIL lines.

## Acceptance (Haiku, frozen tree on the sandbox, `nice -n 10`)

1. `make BUILD_DIR=build/acc test-seeds SEEDS="1 2 3 4 5 6 7 8"` -> 96 PASS lines, no FAIL.
2. Fresh seeds for the two changed benches: after building, in `build/acc`, `for s in $(seq 9 32); do
   vvp -n tb_uart +SEED=$s | grep -E '^(PASS|FAIL)'; vvp -n tb_spi +SEED=$s | grep -E '^(PASS|FAIL)'; done`
   -> 48 PASS lines. Paste the `steered` line of seeds 1, 4, 5 for both benches.
3. `vvp -n tb_syscon +SEED=1` in build/acc shows K1-K4 checks passing and the `kick in fire cycle` counter; seeds 1-8 PASS (step 1).
4. The two broken syscon copies: tb_syscon FAILS on each, with a K1 / K2 check named in the FAIL output.
5. Part A non-vacuity tables (before/after kill sets for uart.v, spi.v, gpio.v): no lost kill.

## Commit plan

1. `test(uart): steer breaks so the break and BI floors hold for every seed (TB-007)`
2. `test(spi): steer the random phase so every coverage floor holds for every seed (TB-009)`
3. `test(syscon): a kick or TORR write in the fire cycle does not stop the fire (SA-008)`
No attribution trailer; explicit paths. Seed tables and mutation before/after to `localFiles/verif-close-2026-11-07/WO-33/`.

## Amendment 2026-11-07 — planner A's review of d1dc43b, 6838b61, 4ff7b02

Verdict: **APPROVED subject to one fixup commit and the acceptance rows below.**
Accepted: the uart top-up after the random phase instead of interleaved steering; the spi
widening to stall classes and mid-byte reads; slack 10000; the C7 file as the "before" kill set
(same catalogue, pre-WO-33 benches), with R7 below as the fresh "after" run. nv1.out already ends
`FAIL tb_syscon: 124 failures, 3945498 checks, seed 1`.

**Fixup — `test(uart,spi): exercise the break top-up (+BRK_FLOOR); a steering wait that times out fails`**
1. tb_uart.v: `integer brk_floor = 5;` with `$value$plusargs("BRK_FLOOR=%d", brk_floor)`; use it in
   the top-up `while ((rx_breaks < brk_floor || bi_seen < brk_floor) && n < 2 * brk_floor + 10)` and
   in the final floor check; print it in the `steered` line. Default behaviour unchanged. Reason: the
   top-up never ran in 32 seeds, and its first `wait_cts` can block if the random phase left RBR full
   with RTS# flow control on; a construction that never ran is not evidence.
2. tb_spi.v steer_byte: both `g < 100000` waits call `fail("steer: engine still busy after 100000 clocks")`
   when the cap is hit (today they continue silently; a hang must fail).

## Acceptance rows (Haiku, frozen tree with the fixup, sandbox, `nice -n 10`, one job at a time)

| row | command | expected |
|---|---|---|
| R1 | `make BUILD_DIR=build/acc test-seeds SEEDS="1 2 3 4 5 6 7 8"` | 96 `PASS` lines, no `FAIL`, rc 0 |
| R2 | in build/acc: `for s in $(seq 1 32); do vvp -n tb_uart +SEED=$s > uart_$s.log; vvp -n tb_spi +SEED=$s > spi_$s.log; done` | 64 runs ending `PASS`; tb_uart `steered 0` on all 32; tb_spi `steered` > 0 on exactly seeds 5 7 8 9 13 14 15 16 17 19 26 31 (paste any difference) |
| R3 | from spi_*.log, every `coverage: <name>=<got>/<floor>` line: the minimum `got` per floor over seeds 1-32 | steered floors (8 byte bins, 5 stalled-write classes, mid-byte RXDATA reads): min >= floor. Every other floor: min >= floor + 4*sqrt(floor) (5->14, 20->38, 50->79, 100->140, 200->257, 300->370, 10240->10645). Table of all floors; a floor under its line is a finding (to be steered or derived later), not a FAIL of this WO |
| R4 | `vvp -n tb_uart +SEED=4 +BRK_FLOOR=30` and `+SEED=17 +BRK_FLOOR=30` | `steered k` with k >= 15, breaks >= 30, BI >= 30, final `PASS tb_uart`, no FAIL/TIMEOUT |
| R5 | `vvp -n tb_syscon +SEED=1` (build/acc) | `kick/TORR write in a fire clock: <a> in the run, <b> in the random phase` with a > b > 0; no line starting `FAIL`; `PASS tb_syscon` |
| R6 | two src copies: `fire = ... & ~rst_soc & ~kick` and `... & ~rst_soc & ~w_torr`; `make SRC_DIR=<copy> BUILD_DIR=build/acc-nv<k> test-syscon` | nv1: a `FAIL K1 kick` line and last bench line `FAIL tb_syscon: ...`; nv2: `FAIL K2 torr` and `FAIL tb_syscon: ...`; make rc != 0 both |
| R7 | `python3 tb/mutate/run.py --file <f> --benches unit --results build/mut/acc33-<f>.tsv` for uart.v spi.v gpio.v, then `--report` | killed IDs contain every C7 kill for those files (47 killed, 12 survived); paste any ID that differs |
