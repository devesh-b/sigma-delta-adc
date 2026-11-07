# WO-01 (S0): design infrastructure, params.py, toolchain record, TT analog template precheck

Coordinator-written, 2026-11-07. **Tier: review.** pd-expert reviews the precheck flow before accept.
**Spec source:** SPEC.md §1, §3.9, §6; PLAN.md Stage S0; WORKFLOW.md §4.
Read `work/v1-design/HANDOFF.md` first.

## Goal
Lay the base every later stage builds on. This WO does not start circuit design. There are three parts:
- **A.** one parameter file
- **B.** a recorded toolchain
- **C.** proof that a TT analog 2x2 3v3 project passes TT's own precheck on the sandbox

## Files you may create or touch (nothing else)
- `design/params.py` (new)
- `design/README.md` (new)
- `design/tests/test_params.py` (new)
- `scripts/s0_toolcheck.sh` (new)
- `scripts/s0_precheck.sh` (new)
- `work/v1-design/results/s0_tools.json` (new)
- `work/v1-design/results/s0_precheck.md` (new)

Do not touch `model/`, SPEC.md, `repos/`, or `/home/mempool/tt`.

## A. `design/params.py`: single source of truth (Paul Thomas pattern, `repos/sd-analog/pthomas-sigma-delta-design/params.py`)
1. Write `design/params.py` with all SPEC §1/§3 numbers:
   - fs nominal and range, N set, c1/c2/k, Cs1/Cint1/Cs2/Cint2
   - VREF options: 1.2 V provisional, plus 2.048 V with c1 = 0.125 as `VREF_OPTIONS`
   - VAPWR/VDPWR, CM = VAPWR/2
   - OTA targets (A0 ≥ 75 dB, GBW ≥ 10 MHz required and 20 MHz target, PM ≥ 60°, SR ≥ 10 V/µs)
   - comparator offset budget, τ ≤ 0.2·t_half
   - the corner set from SPEC §6 as data: `CORNERS_PROCESS`, `TEMPS`, `VAPWR_SET`, `VDPWR_SET`, `MC_RUNS`, `FS_SET`
2. Add derived values with the equation as a comment: t_half, c1 = Cs1/Cint1, c2 = Cs2/Cint2, Zin ≈ 1/(fs·Cs), the 45-point PVT list.
3. Running `python3 design/params.py` writes `design/spice/params.spice` as `.param` lines. Generated output: do not commit it, but do commit the generator.
4. Add `design/tests/test_params.py` (pytest):
   - c1 == Cs1/Cint1 == 0.25 and c2 == 0.5. Expected values come from SPEC §3.4.
   - Exactly 45 PVT points, all distinct.
   - `params.spice` contains every scalar.
   - Agreement with `model/iadc.py` `Params()` defaults for order, c1, c2, k and cs.
     - **Expected mismatches** (record, don't "fix"): fs (model default 1 MHz vs SPEC 2 MHz) and vref (2.048 vs 1.2). The test lists them explicitly as known differences and fails on any *other* mismatch.
   - **Non-vacuity:** run the tests on a copy with Cint1 = 2 pF. They must fail. Show the output.

## B. Toolchain record: `scripts/s0_toolcheck.sh`
On the sandbox, inside the IIC image (`scripts/iic`) **and** with the nix fallback, record the versions of:
- ngspice, xschem, magic, netgen, klayout, yosys, iverilog, verilator, cocotb, LibreLane (docker image tags on the box)
- python and numpy
- PDK_ROOT and the open_pdks hash

Write them to `results/s0_tools.json`. Also re-run the nfet `.op` smoke test from WORKFLOW §4. **Expected Id = 46.8 µA ±1 %.** REJECT otherwise.

**Non-vacuity:** run the smoke test with the wrong corner section (`ff`). It must REJECT, because Id differs by more than 1 %.

Use `timeout` on every tool. Remember the netgen stdin gotcha from WORKFLOW §4.

## C. TT analog template through TT precheck: `scripts/s0_precheck.sh`
1. Work only in `/home/mempool/regr/tt/WO-01/`. **Never use `/home/mempool/tt`**.
   - Clone the current TT sky130 analog template (TinyTapeout `ttsky-analog-template`, or the template the current sky130 shuttle names; record the URL and commit).
   - Clone `tt-support-tools` at the matching ref.
   - If the sandbox has no outbound network, stop and report. Don't work around it.
2. Make the minimum dummy project:
   - 2x2 tile, `uses_3v3: true`
   - the analog pins used by SPEC §1 (ua0..ua2) connected to a trivial structure, for example a metal route from `ua[0]` to a poly resistor to VGND
   - all digital outputs tied, as Paul's framecheck requires
   - no met5
   - GDS/LEF made with magic, using fresh-process DRC per Paul's gotchas: `select top cell; expand`, never `writeall force`
3. Run TT's precheck on it. Record the full log path and the verdict in `results/s0_precheck.md`.
4. **Non-vacuity:** run the precheck on a broken copy with one met5 rectangle added. It **must fail**. Record that.
5. Note in `s0_precheck.md` every check TT precheck does **not** do for sky130 analog. For example, Paul found there is no antenna check. Those become V8 items.

## Acceptance (Haiku re-runs on a frozen copy; expected outputs)
| # | Command (on sandbox) | Expect |
|---|---|---|
| 1 | `python3 -m pytest design/tests -q` | all pass |
| 2 | same on the Cint1 = 2 pF broken copy | ≥ 1 fail |
| 3 | `scripts/s0_toolcheck.sh` | `ACCEPT`, Id within 46.8 µA ±1 %, json written |
| 4 | toolcheck with the ff section | `REJECT` |
| 5 | `scripts/s0_precheck.sh` | TT precheck PASS on the dummy |
| 6 | precheck on the met5 copy | precheck FAIL |

## Commits (explicit paths, no attribution trailer, no push)
1. `design: params.py single source of truth + params tests`
2. `scripts: S0 toolchain record and smoke test`
3. `scripts: S0 TT analog template precheck driver + results`

## Budget and stop rule
At most 70 tool calls. If precheck setup eats more than 35 calls, stop C and report what blocks it. Finish by reporting "k of 3 parts done, with reasons".
