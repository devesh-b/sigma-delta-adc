# WO-58 Part B: first full LibreLane PnR of the C9 macro `sd_adc_c9` (run finished: EXIT=2, setup fails at ss_100C_1v40)

- Inputs: RTL at 346995c (unchanged at HEAD); flow at 3e1e9ea (`design/c9_digital/flow/`, commits a166371 + 3e1e9ea).
- Frozen copy (container-visible via the `scripts/iic` regr mount `/foss/designs/regr` = `/home/mempool/regr/tt`):
  `/home/mempool/regr/tt/WO-58B/3e1e9ea/c9_digital` (rsync of tt-sd/design/c9_digital without runs/; aggregate md5 of
  flow/* + rtl/*.v matches local: 72f01bc4...). The regr/tt mount worked; no copy into tt-sd was needed.
- Tool: LibreLane v3.1.0.dev3, IIC-OSIC-TOOLS 2026.10, TT-pinned sky130A (`/foss/pdks-tt`), 4 CPUs, nice 10.
- Launch: `/home/mempool/regr/tt/WO-58B/3e1e9ea/run.sh` (detached), log `.../pnr1.log` (ends with `EXIT=<rc>`),
  run dir `.../c9_digital/flow/runs/pnr1`. Metric dump: `bash /home/mempool/regr/tt/WO-58B/3e1e9ea/ext.sh`.
- Run a166371 (first launch) was stopped in synthesis: SDC/pin order referenced ports that the macro does not have
  (ena, uio_in, uio_oe; STA-0366). Fixed in 3e1e9ea (input change, clean re-run). No other constraint changed.

## Config changes vs WO-47 draft
- `FP_PDN_MULTILAYER` -> `PDN_MULTILAYER` (false: met4 straps only, no met5); DIE_AREA 190 x 150 um.
- Corners: `LIB` + `STA_CORNERS` = {nom,min,max} x {tt_025C_1v80, ss_100C_1v60, ss_100C_1v40 (D72 stand-in), ff_n40C_1v95}.
  Explicit LIB disables the PDK-compat defaults, so the three default corners are re-listed (same lib files).
- `TIMING_VIOLATION_CORNERS` = ["*"] (PDK default is ["*tt*"], i.e. ss/ff violations would not fail the flow). Tighter, not looser.

## Measured so far (M)
- Synthesis: 860 cells, 11,790 um2, 204 dfrtp_2 + 19 dfstp_2 (223 FF) (`06-yosys-synthesis/reports/stat.rpt`).
- Floorplan: core 22,876 um2, utilisation 0.515 (`13-openroad-floorplan`).
- Post-CTS, nom tt only (mid-PnR STA): setup WS 8.76 ns, hold WS 0.27 ns, skew 0.26 ns (`38-openroad-stamidpnr-2`).
- `RSZ-0020 found 2 floating nets` = VPWR/VGND (special nets, no signal pins) - benign. `STA-1140 library already exists`:
  each lib is read once per RC corner (nom/min/max) - benign.

- Detailed routing converged: DRC 370 / 151 / 152 / 0 over iterations 0-3.

## Final results (M, run `runs/pnr1`, `final/metrics.json`, signoff STA `56-openroad-stapostpnr/<corner>/`)
EXIT=2 = LibreLane deferred error "Setup violations found in: max/min/nom_ss_100C_1v40" (`pnr1.log`). Everything else ran.

| Corner | Setup WS (ns) nom / min / max RC | Setup vio | Hold WS (ns) nom / min / max | Hold vio | Max slew vio (nom/min/max) |
|---|---|---|---|---|---|
| tt_025C_1v80 | 8.499 / 8.536 / 8.464 | 0 | 0.228 / 0.234 / 0.219 | 0 | 0 |
| ss_100C_1v60 | 6.078 / 6.264 / 5.916 | 0 | 0.683 / 0.691 / 0.672 | 0 | 0 |
| **ss_100C_1v40 (D72)** | **-1.404 / -1.193 / -1.599** | **3 / 3 / 13** | 0.637 / 0.648 / 0.623 | 0 | **110 / 66 / 203** |
| ff_n40C_1v95 | 9.062 / 9.088 / 9.037 | 0 | 0.075 / 0.080 / 0.068 | 0 | 0 |

- 48 MHz margin: max_ss_100C_1v40 **-1.60 ns** (Fmax there = 1/(20.833+1.599) = **44.6 MHz**); ss_100C_1v60 +5.92 ns
  (~67 MHz); tt +8.46 ns. TT path = 20.833-8.464 = 12.37 ns > period/2 (10.42 ns): the HARDENING sec. 5 "2x silicon" rule fails.
- Critical path (max_ss_100C_1v40, `max.rpt`): `_1245_` dfstp (act[7], u_cfg) -> or3b -> a221o -> or4 (2.45 ns) ->
  **fanout60/52/51 = clkdlybuf4s25_1** (1.29 / 1.43 / 2.15 ns) -> mux2 -> a22o -> or4b -> or3b -> a22o -> `_1254_` (overrun).
  The resizer used clock-delay cells as fanout buffers (65 clkdlybuf4s25 in the netlist): about 5 ns of the 21.7 ns path.
- Max fanout: **54 violations at every corner** (limit 10 from SDC/MAX_FANOUT_CONSTRAINT, e.g. fanout51/X drives 21). Max cap 0.
- Clock skew 0.26-0.28 ns (setup and hold, all corners); 25 clkbuf + 12 clkinv. Unannotated nets 13 (tie LO / clkload), 0 after filter.
- Physical: Magic DRC 0, KLayout DRC 0, illegal overlap 0, route DRC 0, LVS 0 (all LVS counters 0), XOR 0, antenna 0 nets /
  0 pins (396 antenna diode cells, 991 um2, from heuristic insertion), disconnected pins 0. IR drop worst 0.33 mV.
- met5: no metal5/via4 in `final/mag/sd_adc_c9.mag` (0 hits); DEF mentions met5 only in TRACKS and the CTS_NDR rule (no shapes).
  PDN: met1 rails + met4 straps, VPITCH 153.6 / VOFFSET 16.32 (defaults).
- Area: die 190 x 150 = 28,500 um2, core 22,876 um2, std cells (no fill) 16,268 um2, utilisation 0.711; 1,895 cells
  (223 FF, 284 timing-repair buffers, 140 hold buffers). Power 1.59 mW (tt, default activity: indicative only).
- Waivers: none. Constraint changes in this WO: only removal of non-existent ports (3e1e9ea).

## Files for GL / SDF sim (`/home/mempool/regr/tt/WO-58B/3e1e9ea/c9_digital/flow/runs/pnr1/final/`)
`nl/sd_adc_c9.nl.v`, `pnl/sd_adc_c9.pnl.v` (power pins), `sdf/<corner>/sd_adc_c9__<corner>.sdf` (12 corners),
`spef/`, `gds/`, `lef/`, `lib/`, `mag/`, `spice/`.
