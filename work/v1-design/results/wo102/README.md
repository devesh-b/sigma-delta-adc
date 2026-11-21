# WO-102 results: xschem top update from the WO-99 review

Run 2026-11-21 on the sandbox (IIC-OSIC-TOOLS 2026.10, TT-pinned sky130A). Frozen copy
`/home/mempool/regr/tt/WO-102-a3cd977` (HEAD a3cd977 plus the uncommitted xschem edits committed after this run); outputs in `out/`.
Re-run: `scripts/iic "bash design/xschem/run_wo94.sh OUT"`. Exported: `design/xschem/sd_mod_top.spice`.

## Changes (gen/refnets.py, gen/sch_gen.py, run_wo94.sh)
- (a) `ssh{p,n}` short CM node vicm -> **vscm**.
- (b) Ck2 `khi/klo` swapped for both sides (side p: ua2 on `kl`, ua3 on `kh`).
- (c) `sw("sr2","x2p","x2n","r2","sr2")` added (SW['sr2'] = 8/24 from c4_sw/netlist.py); OTA2 `isl` = `r2_t` (rstb stays C4's).
- (d) `c6_bias` from `c6_final.py netlist` (ports `vdd vss vdl boost trim0..2 ibtp ibn ibp ivbl0 ok`); `c5c7_ref` from `c5c7_ref.py netlist`;
  top: `Xbias VAPWR VGND VDPWR boost trim0 trim1 trim2 o1_ibtp o1_ibn o1_ibp o1_ivbl0 ok`, `Xref ua2 VGND vocm vicm vscm`.
- (e) top ports `boost trim0 trim1 trim2` added.
- (f) OTA2 read from `design/c2_ota2/ota2.spice` (D91 sizes); PENDING flag gone. The file has four 0 V wire sources
  (Vwi1/2, Vwf1/2); `refnets.ota2()` merges them (same as the old C6 ammeters) because the schematic does not draw V sources.
- New wiring broken copies (`sch_gen --break CELL/INST:pinI=NET`, one pin moved to an existing net). The ota2 size copy used a
  non-existent instance `mtr` in the first run and so was not broken (it showed MATCH); fixed to `mt` W 3.75 -> 4.

## Match table (`summary.txt`)
| cell | elements | good | size copy | size | wiring copy | wiring | row |
|---|---|---|---|---|---|---|---|
| ota1 | 76 | MATCH | mtr W=4 | MISMATCH | min1 gate gp->gm | MISMATCH | ACCEPT |
| ota2 | 51 | MATCH | mt W=4 | MISMATCH | min1 gate gp->gm | MISMATCH | ACCEPT |
| c3_comp | 43 | MATCH | M1 W=4.5 | MISMATCH | M1 gate inp->inn | MISMATCH | ACCEPT |
| c4_gen | 166 | MATCH | mdp W=0.5 | MISMATCH | mdn gate vdl->vss | MISMATCH | ACCEPT |
| c6_bias | 99 | MATCH | m1 mult=16 | MISMATCH | m1 gate vg->a | MISMATCH | ACCEPT |
| c5c7_ref | 47 | MATCH | r1 L=5 | MISMATCH | r1 pin0 n2->n3 | MISMATCH | ACCEPT |
| mim_cs/cint1/cint2/ck2 | 1 each | MATCH | MF/W | MISMATCH | top->bot | MISMATCH | ACCEPT |
| sd_mod_top | 60 | MATCH | sinpn W=11 | MISMATCH | Xota1 inp vg1p->vg1n | MISMATCH | ACCEPT |

The top is compared hierarchically (sub-cells are instances); the cells are each checked on their own.
Gap: `run_wo94.sh` does not stop if a break target is missing (it only logs `--break target not found` in `brk_*.log`); I checked
the logs by hand for the second run. A guard was attempted but its sed did not apply.

## Top port list
`ua0 ua1 ua2 ua3 VAPWR VDPWR VGND fs y swap short chop rst_analog order boost trim0 trim1 trim2 comp_out bias_ok`
(ua0/ua1 VIN+/-, ua2/ua3 VREF+/-; fs..order, boost, trim0..2 are 1.8 V inputs from C9; comp_out, bias_ok are 1.8 V outputs).

## Still open
- `o1_ivbnc`, `o1_ivbpc` (OTA cascode biases) have no source: C6 final has no such port. OTA1/OTA2 take them as top-level nets.
- `r2_c` is only the complement phase for the sr2 TG; OTA2 `isl` takes `r2_t` only.
- WO-99 item 6 (WO-95 deck `so1` on r2) and item 7 (OTA `boost` static) are not xschem items; not touched.
- `design/c4_sw/netlist.py` shows as modified in the work tree from another WO; not staged here.
