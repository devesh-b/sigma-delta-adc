# WO-58 Part B: first full LibreLane PnR of the C9 macro `sd_adc_c9` (state: RUNNING at hand-off)

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
- Detailed routing in progress at hand-off (iteration 0: 222 violations at 90 %, normal for iteration 0).

## Pending (Unknown until the run ends)
Signoff STA per corner (12), max slew/cap/fanout, Magic + KLayout DRC, Netgen LVS, antenna, IR drop, GL netlist + SDF.
Expected artifact paths: `runs/pnr1/final/{nl,pnl,spef,sdf,gds,lef}/`, `final/metrics.json`.
