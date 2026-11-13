# WO-67 (C9n): DRV trace + one change (ban buf_1). EXIT=0, change is a regression: do not adopt

- Run `/home/mempool/regr/tt/WO-67/9413a36-r60b/` = `git archive 9413a36 design/c9_digital` + WO-66 RTL (7 md5 identical
  local / WO-66 run copy; c9_fsdiv.v `1acea78d...`). Log `pnr1.log` ends `EXIT=0`. Metrics: `ext.sh`, `corners.py`.
- One change (9413a36, `flow/config.json`): `sky130_fd_sc_hd__buf_1` added to `EXTRA_EXCLUDED_CELLS`
  (LibreLane 3.1.0.dev3 `config/flow.py:383`; applied via `steps/openroad.py:339` set_dont_use and `steps/yosys.py:105`).

## Trace of WO-66 (`runs/pnr1/56-openroad-stapostpnr/<corner>/checks.rpt`)
- Slew: worst nets are resizer fanout buffers `buf_1` (fanout116/68/57/70/59/71/60/58/73, 1.72-2.20 ns vs 1.5 at max_ss_1v40);
  plus _1110_ nor3b_2 (2.06) and a few and2/a21o/dfrtp Q nets. Pin counts are inflated: 128 of 302 listed pins are antenna diodes.
- Max-cap (max_ss_1v60): fanout116 buf_1 0.0868 / fanout68 buf_1 0.0848 (limit 0.0815), _1110_/Y 0.0555 (limit 0.0549).
- Fanout: 10 violations before diode insertion (38-stamidpnr-2: clkbuf_leaf_* 12-13 sinks, CTS clustering), 46 after
  (44-stamidpnr-3): heuristic diodes add one diode per sink, e.g. fanout116 = 10 cells + 11 diodes = 21. The GRT antenna
  check before insertion (40-openroad-checkantennas) found 0 net / 0 pin violations.
- Repair scope: RepairDesignPostGPL only (placement estimates, slew_margin 20); RUN_POST_GRT_DESIGN_REPAIR default false
  (`flows/classic.py:139`); mid-PnR STA reports only nom_tt. RUN_HEURISTIC_DIODE_INSERTION default false (`classic.py:166`), set true by us (HARDENING plan, no reason recorded).

## Result WO-66 -> WO-67 (max RC unless noted; 12-corner table from corners.py)
| Check | WO-66 | WO-67 |
|---|---|---|
| Setup WS ss_1v40 max / nom / min | +2.582 / 2.713 / 2.878 | **+0.173** / 0.297 / 0.449 (Fmax 48.0 MHz, was 54.8) |
| Setup WS ss_1v60 / tt / ff | 7.40 / 8.73 / 9.23 | 7.06 / 8.72 / 9.23; 0 setup vio, 0 hold vio all 12 corners |
| Hold WS min (ff) | 0.108 | 0.111 |
| Max slew ss_1v40 max/nom/min | 256 / 240 / 240 | 108 / 86 / 20 (54 of 108 are diode pins); other corners 0 (was 44 at max_ss_1v60) |
| Max cap | 3 | 0 |
| Max fanout | 46 | 51 |
| DRC Magic/KLayout/route, LVS, XOR, antenna, disconnected | 0 | 0 (route iter0 275) |
| Diodes / std-cell area / util | 342 / 16,099 / 0.704 | 372 / 16,561 / 0.724 |
| Power / IR worst | 1.644 mW / 0.34 mV | 1.667 mW / 0.35 mV |
- Mechanism (red flag): with buf_1 banned, repair_design picked `dlygate4sd3_1` for all 70 fanout buffers (0 buf_*
  repair buffers left). They are delay cells: fanout52 dlygate 2.12 ns on the new ss_1v40 critical path _1441_ -> _1280_.
  Remaining slew drivers are 4 dlygate fanout buffers (1.55-1.61 ns) and _1110_ nor3b_2 (2.01 ns). Same failure class as WO-58B clkdlybuf.

## Proposal (not run)
- Revert the buf_1 ban (back to e450ae2 config, WO-66 state). Coordinator decision.
- Next single change: `RUN_HEURISTIC_DIODE_INSERTION: false` (LibreLane default). Expected: fanout 46 -> ~10 (clock leaves),
  slew/cap pin counts and diode cap drop, 342 diodes / ~860 um2 freed. Risk: antenna; RepairAntennas (GRT-based) stays on
  and post-route CheckAntennas must show 0; DIODE_ON_PORTS in stays. Then slew on buf_1 nets (driver-strength) and clock
  leaf fanout (CTS clustering) need their own changes; a buffer-selection lever that does not fall back to dlygate must be
  found in the installed OpenROAD/LibreLane before banning buf_1 again.
