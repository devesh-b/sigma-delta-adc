# WO-60 Part A: ban clock-delay cells from resizer buffering, C9 PnR rerun (EXIT=2, setup still fails at ss_100C_1v40)

- One change vs WO-58B (3e1e9ea): `EXTRA_EXCLUDED_CELLS` = `sky130_fd_sc_hd__clkdlybuf4s*`, `sky130_fd_sc_hd__dlymetal6s*`
  (flow commit e450ae2). RTL 346995c, md5 of rtl/*.v identical to the WO-58B frozen copy (366f25bd...).
- Variable source (LibreLane v3.1.0.dev3 in IIC-OSIC-TOOLS 2026.10): `/usr/local/lib/python3.12/dist-packages/librelane/config/flow.py`
  `EXTRA_EXCLUDED_CELLS` "Wildcards matching additional cells to exclude from both synthesis and PnR", deprecated names
  `RSZ_DONT_USE_CELLS`, `DONT_USE_CELLS`; merged with `PNR_EXCLUDED_CELL_FILE` in `steps/openroad.py:339` and applied by
  `set_dont_use $::env(_PNR_EXCLUDED_CELLS)` in `scripts/openroad/common/io.tcl:391`. Resolved value confirmed in `runs/pnr1/resolved.json`.
- Frozen copy: `/home/mempool/regr/tt/WO-60A/e450ae2/c9_digital` (git archive of e450ae2). Launch `launch.sh` -> `run.sh`,
  log `pnr1.log` (ends `EXIT=2`), metrics `bash ext.sh` / `python3 corners.py <metrics.json>` (in container).

## Results (M, `runs/pnr1/final/metrics.json`, `56-openroad-stapostpnr/max_ss_100C_1v40/max.rpt`)
| Corner (worst RC) | Setup WS ns: WO-58B -> WO-60A | Setup vio | Hold WS | Max slew vio | Max fanout | Max cap |
|---|---|---|---|---|---|---|
| tt_025C_1v80 (max) | 8.464 -> 8.583 | 0 | 0.221 | 0 | 54 (54) | 0 |
| ss_100C_1v60 (max) | 5.916 -> 6.239 | 0 | 0.679 | 22 (was 0) | 54 | 1 at nom/max (was 0) |
| ss_100C_1v40 (max) | -1.599 -> -1.181 (nom -0.963, min -0.778) | 2/2/2 (was 3/3/13) | 0.633 | 336 (was 203) | 54 | 0 |
| ff_n40C_1v95 (max) | 9.037 -> 9.122 | 0 | 0.070 | 0 | 54 | 0 |

- Fmax at max_ss_100C_1v40: 1/(20.833+1.181) = 45.4 MHz (was 44.6). TT period/2 rule: 20.833-8.583 = 12.25 ns > 10.42 ns: still fails.
- Ban effective: 0 clkdlybuf/dlymetal in netlist; the 65 `fanout*` buffers are now `buf_1` (weak), 180 `hold*` = dlygate4sd3_1.
- Critical path unchanged in structure: `_1245_` (act[7]) -> or3b -> a221o -> or4 (2.43 ns) -> fanout60 buf_1 -> or3 (1.86 ns) ->
  fanout52/51 buf_1 -> mux2 -> a22o -> or4b (2.26) -> or3b (1.91) -> a22o -> **hold153 dlygate4sd3_1 (1.67 ns)** -> `_1254_`.
  A hold buffer sits on the setup-critical endpoint at ss_1v40.
- Physical: Magic DRC 0, KLayout DRC 0, route DRC 0 (iter0 282, was 370), LVS 0 (all counters), XOR 0, antenna 0 nets/pins
  (399 diodes, 998 um2), disconnected pins 0, illegal overlap 0. Skew 0.258 ns.
- Area: die 28,500 / core 22,876 um2 unchanged; std cells 15,914 um2 (was 16,268), util 0.696 (was 0.711),
  timing-repair buffers 2,281 um2. Power 1.566 mW (was 1.59, default activity). IR drop not re-read.
- Flow gating: deferred error only for setup. Slew (336) and the new ss_1v60 max-cap 1 did not fail the flow
  ("No max cap violations found" in the log while metrics show 1): checker corner scope unverified.
