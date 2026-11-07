# WO-01a (S0 fixes): make the S0 gate prove it catches real failures

Coordinator-written, 2026-11-07. **Tier: routine.** The Haiku tester re-runs the acceptance table below.
**Spec source:** `work/v1-design/REVIEW-WO01-pd-2026-11-07.md` (B-1, S-1…S-6, N-2); SPEC.md §1, §3.1, §6; DECISIONS D14, D15.
Read `work/v1-design/HANDOFF.md` first.

## Files you may touch (nothing else)
- `design/params.py`
- `design/tests/test_params.py`
- `scripts/s0_precheck.sh`
- `scripts/s0_toolcheck.sh`
- the dummy layout build script that `s0_precheck.sh` uses: under `scripts/`, or generated into `/home/mempool/regr/tt/WO-01/`. If it lives in the repo, it is in scope.
- `work/v1-design/results/s0_precheck.md`
- `work/v1-design/results/s0_tools.json`

## Items
1. **B-1, params.py:**
   - Set `OTA_A0_DB_MIN = 80.0` (SPEC §3.1, user Q6).
   - PGA: none in v1 (D14). Remove v1 PGA gains or mark them stretch.
   - `VREF_OPTIONS`: A = {vref 1.2, c1 0.25, c2 0.5, k 1.0}, A2 = {vref 1.2, c1 0.25, c2 0.25, k 1.0}, B = {vref 2.048, c1 0.125, c2 0.5, k 0.5}.
   - Add `FS_PRECISION = (0.25e6, 2e6)` and `FS_FAST = 4e6` (fast / low-resolution mode, D13).
2. **S-6, corner set:**
   - `CORNERS_RC = ("ss_hh", "ff_ll")`.
   - `PVT_LIST_ANALOG`: (5 MOS corners + 2 RC) × 3 temperatures × 3 VAPWR = **63** points.
   - `PVT_LIST_DIGITAL`: 5 × 3 × 3 VAPWR × 3 VDPWR = **135** points.
   - `MC_RUNS = {"tt_mm": 200, "<worst>_mm": 50}`. Worst = a placeholder key, documented.
   - Tests:
     - exact counts 63 and 135, all points distinct;
     - k/c1 == 4 for options A and B;
     - A0 ≥ 80;
     - **every corner and MC section name exists**. Parse the `.lib` names from `$PDK_ROOT/sky130A/libs.tech/combined/sky130.lib.spice`. Skip with a clear message if PDK_ROOT is unset; the sandbox has it.
   - **Non-vacuity:** a copy with a typo section name (`ss_hhh`) must fail.
3. **S-1, DRC non-vacuity:** add broken dummy variants to `s0_precheck.sh`. Each must fail **on its own named precheck check**, and the others must stay green:
   - `drcbeol`: a met4 wire 0.2 µm wide. Must fail Magic DRC and KLayout BEOL.
   - `drcfeol`: a poly or li1 sliver below minimum width. Must fail KLayout FEOL.
   - `apin`: ua2 stub removed, or an extra stub on ua3. Must fail the analog pin check.
   - `met5`: as today.

   `all` prints ACCEPT only if `ok` passes and every broken variant fails on its expected check name.
4. **S-2, digital tie in GDS:** in the `ok` dummy, tie uo_out[7:0], uio_out[7:0] and uio_oe[7:0] to VGND in the layout (met3/met4), matching `project.v`. Note in `s0_precheck.md` that precheck does not check this; the V8 tie check covers it.
5. **S-3, tool versions:**
   - Run precheck inside TT's own `nix-shell <tt-support-tools>/precheck/default.nix --run "python precheck.py …"`, with the venv python for pip modules. Expect magic 8.3.568 and klayout 0.30.8.
   - Record the versions actually printed in `s0_precheck.md`.
   - **Do not** use the IIC image for precheck.
   - Build tools (layout generation) may stay newer.
6. **S-4, PDK:** CI uses open_pdks 0536d02 and the sandbox has d56f8a8 (1 commit ahead, metadata + gf180 only).
   - Correct the wording in `s0_precheck.md`.
   - If `ciel` can enable 0536d02 into a **separate** PDK_ROOT under `/home/mempool/regr/tt/WO-01/pdk-ci` within 5 tool calls, run precheck against it. Otherwise record the diff as accepted.
   - Never modify `/home/mempool/.ciel`.
7. **N-2, toolcheck:** take the open_pdks hash from `readlink -f /home/mempool/.ciel/sky130A`. Remove the `cat` on a directory and the `ls | head -1`.

## Acceptance (sandbox)
| # | Command | Expect |
|---|---|---|
| 1 | `python3 -m pytest design/tests -q` | all pass (63 / 135 / names / A0 / k/c1) |
| 2 | tests on the `ss_hhh` typo copy | fail on the section-name test |
| 3 | `scripts/s0_precheck.sh ok` | ACCEPT; log shows magic 8.3.568 and klayout 0.30.8 |
| 4 | `scripts/s0_precheck.sh all` | ACCEPT; each of met5 / drcbeol / drcfeol / apin fails on its named check |
| 5 | `scripts/s0_toolcheck.sh` | ACCEPT; open_pdks hash from readlink |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `design: params A0 80 dB, VREF options with k, R+C and digital corner lists, PDK section-name test`
2. `scripts: S0 precheck under TT's nix-shell tools, DRC/pin broken copies, GDS digital tie`
3. `scripts: toolcheck PDK hash via readlink`

## Budget and stop rule
At most 60 tool calls. `rta-tt` is one shared tmux session: on "another rt call is in flight", retry later, and always `cd` explicitly inside the command. Finish by reporting "k of 7 items done, with reasons".
