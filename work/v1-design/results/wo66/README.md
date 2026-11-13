# WO-66 (C9m): PnR on the retimed RTL (WO-60B), flow e450ae2. EXIT=0, setup met at all 12 corners

- One change vs WO-60A: RTL `c9_fsdiv.v` retime (fs_tick/s_tick registered one clk early, terminal constants registered).
  RTL is uncommitted (working tree = sandbox `/home/mempool/regr/tt/WO-60B-e450ae2-dirty/*.v`, flat dir, not `design/c9_digital/rtl`).
  md5 of all 7 `rtl/*.v` identical local / WO-60B freeze / WO-66 run copy (c9_fsdiv.v `1acea78dd2dc22d5e70a6501c8e5e7e8`).
- Run copy: `/home/mempool/regr/tt/WO-66/e450ae2-r60b/` = `git archive e450ae2 design/c9_digital` + WO-60B RTL overlaid.
  `launch.sh` -> `run.sh`, log `pnr1.log` (ends `EXIT=0`), metrics `bash ext.sh`, `python3 corners.py <metrics.json>` (in container).

## Results (M, `c9_digital/flow/runs/pnr1/final/metrics.json`, `56-openroad-stapostpnr/<corner>/max.rpt`)
| Corner (max RC) | Setup WS ns WO-60A -> WO-66 | Setup vio | Hold WS | Max slew vio | Max fanout | Max cap |
|---|---|---|---|---|---|---|
| tt_025C_1v80 | 8.583 -> 8.734 | 0 | 0.313 | 0 | 46 (was 54) | 0 |
| ss_100C_1v60 | 6.239 -> 7.399 | 0 | 0.475 | 44 (nom 22, min 0) | 46 | 3 (nom 1) |
| ss_100C_1v40 | -1.181 -> **+2.582** (nom 2.713, min 2.878) | 0 | 0.358 | 256 (nom/min 240; was 336) | 46 | 0 |
| ff_n40C_1v95 | 9.122 -> 9.235 | 0 | 0.112 (min corner 0.108) | 0 | 46 | 0 |

- Setup 0 vio / hold 0 vio at all 12 corners. Fmax at max_ss_100C_1v40 = 1/(20.833-2.582) = 54.8 MHz (was 45.4).
- TT period/2 rule: **passes**. Worst tt reg-to-reg arrival 6.66 ns (`_1348_`->`_1422_`, slack 14.30) < 10.42 ns. The tt
  WS of 8.734 is an output-port path (trim_o[2], 0.30*P output delay), not reg-to-reg. Note: WO-58B/60A computed the
  rule as P - WS; that mixes in I/O paths and was conservative (not rechecked for those runs).
- New ss_1v40 critical path: `_1437_` (u_seq.c[5]) -> or3 -> or3 -> or4 (2.92 ns, fo 11) -> a21o -> fanout56 buf_1 -> nor2 ->
  fanout40 buf_1 (slew 1.37 ns, 1.28 ns) -> mux2 (1.63) -> xor2 -> a221o -> 3x a2111o -> `_1280_` (cfg_pending); arrival 18.65 ns.
  fs_div compare -> overrun path is gone from the top. No hold buffer on this path; no clkdlybuf/dlymetal in netlist.
- Physical: Magic DRC 0, KLayout DRC 0, route DRC 0 (iter0 265), LVS 0 (all 7 counters), XOR 0, antenna 0 vio
  (342 diode cells, 856 um2; was 399), disconnected pins 0, illegal overlap 0. Skew 0.26-0.30 ns. Unannotated nets 12, filtered 0.
- Area: die 28,500 / core 22,876 um2 unchanged; std cells 16,099 um2 (was 15,914), util 0.704 (was 0.696), 231 flops,
  296 timing-repair buffers (2,313 um2), 179 hold buffers (dlygate4sd3_1). Power 1.644 mW (was 1.566, default activity).
  IR drop worst 0.34 mV, avg 0.11 mV (VPWR 1.8 V).
- Flow gating: EXIT=0 although metrics show slew 256, fanout 46, max-cap 3: the slew/cap/fanout checkers do not fail
  the flow (same as WO-60A; checker corner scope unverified). Not a pass for DRV.

## Open (not fixed by this run)
- DRV: 46 max-fanout (limit 10, SDC `set_max_fanout`), 256 slew at ss_1v40, 3 max-cap at max_ss_1v60. Cells outside
  characterised slew make ss_1v40 timing less trustworthy (recoverable: lower clock). Root cause not yet traced (which nets).
- Proposed next single change (not run): first read `checks.rpt` per corner to name the violating nets; if they are the
  `fanout*` buf_1 repair buffers (e.g. fanout40 slew 1.37 ns at ss_1v40), add `sky130_fd_sc_hd__buf_1` to
  `EXTRA_EXCLUDED_CELLS` so the resizer must use buf_2+. Note LibreLane uses `RSZ_CORNERS or STA_CORNERS` for repair
  (`steps/openroad.py:2439`), so ss_1v40 should already be in the repair corner set: why repair left them is unknown.

## GL/SDF sim inputs (container paths `/foss/designs/regr/...` = `/home/mempool/regr/tt/...`)
- Netlist: `WO-66/e450ae2-r60b/c9_digital/flow/runs/pnr1/final/nl/sd_adc_c9.nl.v` (power-pin variant `final/pnl/sd_adc_c9.pnl.v`).
- SDF: `.../final/sdf/<corner>/sd_adc_c9__<corner>.sdf` for all 12 corners (nom/min/max x tt, ss_1v60, ss_1v40, ff).
