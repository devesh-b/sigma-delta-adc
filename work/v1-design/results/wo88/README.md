# WO-88 (C3k): D90, leak-path probe, precharge-edge cap candidates (IN PROGRESS, pickup below)

Status 2026-11-15 01:25 IST: the code and SPEC items are done. The runs are in flight; the sandbox load is about 8 on
6 cores, so lpool gives 1 slot and the decks run one at a time. Items 2, 3, 4 and 6 are waiting on data. Nothing
below is a verdict yet.

## Done
- **Item 1 (D90) in `c3_tb.py`** (commit 2a923df):
  - New constants `V18_TOL = 1 mV` and `V18_SUS = 1.981 V`.
  - The sustained limb's default `sus_lim` and the duration threshold in `st_post` (`_longest_above(..., V18_SUS)`)
    both use 1.981 V.
  - The `why[:3]` and `detail[:4]` truncations are removed, so collect now prints every reason.
  - Checker copy `st_chk_sus1985_sw` is a real deck: the pin is at 1.985 V on the stiff switched basis, so S is about
    1.98515 V and the row must REJECT on `over:sus`.
  - In `supply_probe.py deck_list4`, `sus195`, `cap20`, `dur01` and `jn20` are judged from `st_tt27_a_sw`.
- **Item 5:** SPEC row 99 (the D83 wording) now states the 1 mV tolerance. A CL-39 change-log entry was added.
- **Item 2 (smoke):** run in `/home/mempool/regr/tt/WO-88-smoke`, 10 ns with `display`.
  - The vector names in `supply_probe._ivec` are correct (`@m.xc.x<dev>.msky130_fd_pr__<model>[id]`).
  - In tran, `[is]` and `[ib]` come back **0-long**, and that is what makes WO-86's `write` abort.
  - Fix (bfc8611): save `[id]` only. Each node's KCL is then over the drain currents of the devices whose drain is
    on that node. For op, that is M3, M5, R0 and KPo; the M4/M6/Bo1 gates carry only gate leakage.
  - `dpost` skips the terms that are missing.
- **Item 3 candidates** (commit 2a923df):
  - Mechanism: P is on `M4 gb`, which is node op, at t = 2494.1 ns. That is the strobe **falling** (precharge) edge,
    n = 9.
  - The losing node (on) is pulled 0 to vdd by R1 in about 0.2 ns. Through the Cgd of M5 and M3 (both have gate on
    and drain op), that couples the held-high op upward. The keeper is the only thing returning op, which is why kp2
    lowered P from 2.251 V to 2.206 V.
  - The candidate fix is a slower op/on precharge. It changes R0/R1 only; the dp/dn devices R2/R3 stay at 1.0/0.15.
    The new size key `RSO` is applied through these mutations:

    | mutation | R0/R1 W/L |
    |---|---|
    | `kp2_rsoW05` | 0.5/0.15 |
    | `kp2_rsoL03` | 1.0/0.3 |
    | `kp2_rsoL05` | 1.0/0.5 |

  - `kp3` (a 3x keeper, info) is the "something else" comparison.
  - Expected trade-offs:
    - Narrower W also halves the R0/R1 Cgd overlap, so the strobe-rise kick on op/on should drop.
    - Longer L lowers mismatch, but it adds channel charge at the rising edge.
    - Precharge time has a margin of about 100 ns.

## Runs in flight
- Pool A: `/home/mempool/regr/tt/WO-88-2a923df/runA` has 33 jobs, launched 01:09.
  - Jobs 1-16 are the sweep. For each candidate: `st_<c>_sw` (tt/27 a), `st_<c>_ff-40_b_sw`,
    `one_<c>_ss-40_162` (T5, T2band) and `one_<c>_fs+125_198` (T5).
  - Jobs 17-33 are the **rev f cyc rows that were never run**, as `cyc_*_revf` (9 PVT, cm12, cm18, 2 MHz and the
    5 brk copies).
- Probe: `/home/mempool/regr/tt/WO-88-bfc8611/runI/st_sw_icur` (1 job). It writes `dpost.txt`, the per-node
  drain-current table that names the leak path.

## Pickup (sandbox; env: `. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=<frozen>`)
1. Wait for `runA/pool_logs/POOL_DONE` and `runI/pool_logs/POOL_DONE`.
2. Collect pool A:
   `cd /home/mempool/regr/tt/WO-88-2a923df && PYTHONPATH=$PWD python3 design/c3_comp/c3_tb.py collect $PWD/runA > runA/collect.log`
3. Read `runI/st_sw_icur/dpost.txt` and name the device on op/on and on nb2/ob2: the largest negative mean current
   ("device pushes current into the node").
4. Choose the candidate:
   - P ≤ 2.2 V at ff/−40 b, with margin.
   - T5 kick ≤ 5 mV at fs+125.
   - T2band passes.
   - Prefer the smallest change.

   Then make it the default in `sizes_draft.py`: `KP = 0.84/0.15`, `RSO = <chosen>`. Add mut `revf` (`KP 0.42`,
   `RSO = RS`) to MUTS and netlist. `deck_list4` already uses `revf` for an info row. Commit `design/c3_comp/`.
5. Freeze a new copy `/home/mempool/regr/tt/WO-88-<sha>` (rsync design/ (without c1_ota1, c4_sw, c6_bias), golden/,
   model/, scripts/, plus `.spiceinit` `set num_threads=1`).
6. Generate and launch pool B (setsid nohup):
   `python3 design/c3_comp/supply_probe.py gen4 $F/runB`, then `scripts/lpool.sh $F/runB/jobs.txt`.

   This is the full set: one, cyc, MC T3 (n = 200 tt + 50 ss/−40), sens/pdk, and the st rows on the stiff pin
   (tt27 a/b, ff-40 a/b, ff125 b) plus brk, chk and info. Expect many hours at 1 slot.
7. Collect pool B. Fill in the verdict table below: T2, T3, T5, T8 and the info rows. Every copy must REJECT for its
   own reason; the full reason lists are now printed.

## Verdict table (to fill)
| row | rev g result | expect | verdict |
|---|---|---|---|
| T8 st_* (5 corners, sw basis) | | pass | |
| T8 copies sus195 / cap20 / dur01 / jn20 / sus1985 / brk_noclamp / brk_vdd200 / brk_in18 | | reject | |
| T2 / T7 / T10 cyc (12 rows + 5 brk) | | pass / reject | |
| T5 one_* (9 PVT + 2 MHz + asym) + chk copies | | pass / reject | |
| T3 MC tt / ss40 / brk_x6 | | pass / reject | |

## Ready for review (once filled)
- D90 implementation (limits, the sus1985 copy, the full reason lists).
- The leak-path name.
- The cap fix choice and its T2/T5/T3 cost.
- The full C3 verdict table.
- The rev f cyc rows.
