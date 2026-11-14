# WO-70 (C4c) results: C4 testbench fix, D78 leak re-split, gate pool rerun

Script: `design/c4_sw/c4_tb.py` (commit 01fc505). Frozen copy: `/home/mempool/regr/tt/WO-70-01fc505`
(`c4_sw/` scripts, `run/` outputs, `run/pool/` pool logs, `run/.spiceinit` single-thread, `launch.sh`).

## 1. Cause of the WO-54 "incomplete or empty netlist" errors

The decks were complete (WO-54 `run/injdm_tt_27_4M_none.sp`: 268 lines, `.tran` and `.control` present).
The message is ngspice's batch-mode follow-on after an aborted transient. The real first error, from the WO-54 logs:

| deck | WO-54 log line |
|---|---|
| injdm / injcm (all corners) | `Timestep too small; time = 2e-08 ... trouble with node "vinn#branch"` (first fs edge) |
| settle ss_m40 | `Timestep too small; time = 2.846e-08 ... node "vord#branch"` |
| rampa / rampb | `Timestep too small; time = 1.22..1.34e-05 ... node "brs#branch"` (VDPWR ramp, LS input snap) |

`spice()` matched `"timestep too small"` case-sensitively, so only the follow-on `Error:` line was reported.
In the inj decks the 1e5-gain E-source integrators also started at an undefined DC point (`oxp` = 13.2 V at t = 0).

Fixes (testbench only, no gate limit changed):
- ideal `sw` models: ron 1 / roff 1e13 (ratio 1e13, above ngspice's ~1e12) -> ron 10 / roff 1e12, same on the real
  and ideal copies so the roff leakage cancels in the difference;
- both integrators of each copy held in reset until T0 - 5 ns (`Sr0*`, `Vrst0`);
- every digital pad input driven through 100 ohm + 5 fF (`drv()`), not a bare ideal source / B-source;
- `method=gear` on inj / settle / ramp; tolerances unchanged (inj/settle reltol 1e-6, ramp 1e-4);
- error capture case-insensitive and also catches "aborted".

## 2. D78: Sg leak re-split with C1's measured share

The leak deck now measures C1's devices on the same vg node on their own ammeter (C1 DESIGN.md M5: island
nfet_g5v0d10v5 2/0.5 off to V_ICM; input chopper 4/0.5, one on to the pair gate, one off). Sg limit = row - C1 share.

| corner | row | C1 share (sign) | Sg limit | Sg max abs (sign) | verdict |
|---|---|---|---|---|---|
| ff/125/3.6 | 90 pA | 81.2 pA (-) | 8.8 pA | 68.5 pA (-) | FAIL |
| ff/125 `tg` copy | | | 8.8 pA | 64.8 pA | REJECT |

Finding: C1's junction share alone is ~90 % of the 90 pA row, so W 4 (~55 pA) or a T-switch (vg-side junction
remains) does not close it. C1 + Sg = ~150 pA per node at ff/125. This needs a user decision (row / temperature
allocation, junction area of the vg-side devices). Caveat: `tg` REJECTs only because the limit is now small; the
added PMOS junction (n-well) has the opposite sign and lowers |I| (68.5 -> 64.8 pA). A copy that raises the leak
(e.g. Sg W x3) would be a stronger broken copy for this row.

## 3. Gate pool (89 jobs)

Launched 2026-11-13 20:45 IST, `lpool.sh` with `run/jobs2.txt` (same 89 jobs, inj / settle / ramp / leak first).
Box load ~14 on 6 cores, so the pool runs one job at a time.

**Status 20:52 IST: the inj fix is not sufficient.** `injdm_tt_27_4M_none` still stops at t = 20 ns (first fs edge),
`Timestep too small ... node "vinn#branch"`, now reported correctly. The pool was left running for the settle / ramp
/ tim / ron / leak rows (inj jobs fail fast). Next suspects for inj, in order: (1) the ideal `sw` copy (vh 10 mV,
gates on the live generator nets) chattering at the first edge: drive the ideal switches from `B`-source logic
copies of the gate nets or replace them with smooth `B`/`R` conductances; (2) the 1e5 E-source integrators with
no output limit: add a finite output R or a tanh-limited B source; (3) a short 2-cycle debug deck first.

## Pickup
- When `run/pool/POOL_DONE` exists: `ssh sandbox '. /home/mempool/tt-sd/.venv-sbx/bin/activate; cd
  /home/mempool/regr/tt/WO-70-01fc505/run; python ../c4_sw/c4_tb.py report .'` and copy `summary.md` here.
- Fix inj in `c4_tb.py`, new frozen copy, rerun only `injdm|injcm` jobs (`c4_tb.py jobs OUT injdm` style filter).
- Reviewer pass on C4 rev b not requested yet (no inj verdict).

## 4. WO-79 collection and triage (2026-11-14)

`POOL_DONE` present; 61 jobs EXIT=0, 28 EXIT=1. `c4_tb.py report .` exits 2 (errored jobs); `run/summary.md` (131 lines)
written. **All 28 EXIT=1 jobs are one cause: a transient timestep abort, i.e. a bench / simulator artefact. None is a
design verdict.** Every abort names the branch current of an ideal voltage source (`Timestep too small ... node "vX#branch"`):

| group | jobs | node | when |
|---|---|---|---|
| injdm / injcm, all corners + `order_inv` / `top8` copies | 10 | vinn#branch | t = 20 ns exactly (first fs edge, a breakpoint) |
| tim (ss_m40 2M, ff_125 4M, ss_m40_ls 4M/2M, sf_m40_ls 4M/2M/0M25) | 7 | vord#branch (vrs once) | 36 ns .. 4 us, LS edges |
| tim broken copies (overlap tt_27, wrongstrobe / ylate / ctlmid / o1early ff_m40, ylate tt_27) | 6 | vord#branch | 0.4 .. 0.8 us |
| settle ss_m40, ss_125; settle ss_m40 `ronx3` | 3 | vtpb#branch, vdl#branch | 38 ns .. 1.1 us |
| rampa ff_m40, sf_m40_ls | 2 | vadn#branch | 12.4 / 13.3 us (VDPWR ramp, LS snap) |

So: 0 expected REJECTs among the EXIT=1 jobs (a broken copy that aborts has no verdict; those copies are rerun),
0 real design failures among them. The real design findings are in the EXIT=0 rows: `leak_ff_125` and `leak_ff_100`
FAIL (section 2; ff/100: Sg 14.8 pA + C1 8.6 pA = 23.4 pA against the 20 pA row). Root cause and fix: `results/wo79/`.
