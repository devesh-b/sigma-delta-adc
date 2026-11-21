# WO-94 results: xschem schematics, symbols and the generator-equivalence check

Run 2026-11-21 on the sandbox, IIC-OSIC-TOOLS 2026.10 (TT-pinned sky130A), frozen copy
`/home/mempool/regr/tt/WO-94-6b474df` (outputs in `out/`: `ref/` generator netlists, `good/` and `brk_<cell>/`
xschem netlists + netgen reports). Re-run: `scripts/iic "bash design/xschem/run_wo94.sh OUT"`.

## Flow
- `design/xschem/gen/refnets.py` takes the reference netlists from the Python generators: C1 `netlist.py`
  (`build()`, cmfb sc), C3 `netlist.py`, C4 `netlist.py` (`gen()`, switch sizes `SW`), and the C6 `c6_spot.py`
  tran-deck core. It also composes the top `sd_mod_top` from them.
- `design/xschem/gen/sch_gen.py` turns each `.subckt` into `sch/<cell>.sch` and `sch/<cell>.sym`. Devices use the
  PDK symbols (`sky130_fd_pr/*`); ideal R/C use `devices/res`, `capa`; the hvl/hd standard cells get primitive
  symbols in `sch/cells/`. Sizes are copied verbatim. Placement is a grid with a net label on every pin. The
  schematics are readable, not drawn.
- xschem (batch, `xschemrc`, `top_is_subckt 1`) netlists each `.sch`. netgen `lvs` with `sky130A_setup.tcl`
  compares that netlist with the generator netlist. A cell passes only if it gives "Circuits match uniquely"
  with no property errors **and** its broken copy (one size changed in the `.sch`) does not.

## Match table (`summary.txt`)
| cell | elements | good | broken copy | broken | row |
|---|---|---|---|---|---|
| ota1 | 76 | MATCH | Xmtr W 3.75 → 4 | MISMATCH (property) | ACCEPT |
| ota2 | 76 | MATCH | Xmtr W → 4 | MISMATCH | ACCEPT |
| c3_comp (rev g) | 43 | MATCH | XM1 W 5 → 4.5 | MISMATCH | ACCEPT |
| c4_gen (rev b) | 152 | MATCH | Xmdp W 0.42 → 0.5 | MISMATCH | ACCEPT |
| c6_bias | 48 | MATCH | Xm1 mult 17 → 16 | MISMATCH | ACCEPT |
| mim_cs / cint1 / cint2 / ck2 | 1 each | MATCH | MF 2→3 / 16→15 / 4→5, Ck2 W 11→12 | MISMATCH | ACCEPT |
| sd_mod_top (hierarchical) | 57 | MATCH | Xsinpn W 12 → 11 | MISMATCH | ACCEPT |

The broken copies test the property comparison (W, mult, MF). Topology is netgen's normal graph match and is not
tested with its own broken copy. Standard cells are black boxes on both sides: their pin order comes from the PDK
spice library and is the same in both netlists.

## Top schematic `sd_mod_top` (exported as `design/xschem/sd_mod_top.spice` for WO-95 / WO-96)
Ports: `ua0` VIN+, `ua1` VIN−, `ua2` VREF+, `ua3` VREF− (these are TT ua[0..3]; plain names avoid bus syntax),
`VAPWR VDPWR VGND`, C9 inputs (1.8 V) `fs y swap short chop rst_analog order`, outputs to C9 `comp_out` (C3 q)
and `bias_ok` (C6 ok through `lsbufhv2lv_1`).

Per side: #1 merged input/swap/short TGs → Cs1 (MIM, bottom plate driven) → #4 Sg → vg1. The #2 DAC: side p goes
to VREF+ on `dh`, side n on `dl`. Cint1 runs vg1p→x1n and vg1n→x1p. Stage 2: #6 Cs2 sample, #7 plate short,
#8 top short, #9 Sg2, Ck2 on vg2 with #10/#11, Cint2, then OTA2 → x2 → C3 → `dec` = hd nand2(q, qb) → C4.
The CMFB phases are ph1 = il and ph2 = sl. Both OTAs use one set of chopper, island and clamp signals from C4.

## Open items and gaps (for the coordinator)
1. **C6 has no final subckt.** `c6_bias` is the c6_spot tran core at R1 144.8 µm, R2/R1 2.45 (WO-80). Note that
   the c6_spot defaults are R1_L 94 and ratio 4.6, and the tuned values come from tune.json. The C6.3 port mirrors,
   boost and trim are not generated, so in the top the OTA bias nets `o1_*` and `vicm`/`vocm` are **unsourced**.
2. **OTA2 (D91)** comes from the same generator: `build(name='ota2', sizes=sizes_draft.SIZES_OTA2)`. Until WO-98
   adds `SIZES_OTA2` it uses the OTA1 sizes, and the netlist is flagged `* PENDING D91 sizes`. OTA2 shares OTA1's
   bias nets and has its own CMFB.
3. Choices made in the top, not in any generator; they need review:
   - the `short` CM node is `vicm`;
   - the per-side DAC and Ck2 polarity (k phases mirror stage 1);
   - the hd nand2 for `dec`;
   - the bias_ok down-shifter;
   - the Cint2 reset (#12, C2) is absent: `r2_t/r2_c` are unconnected and OTA2's `isl` takes C4 `isl`.
4. MIM unit is W = L = 11 µm (≈ 0.25 pF nominal), counts Cs 2, Cint1 16, Cint2 4, Ck2 1. The value is not
   simulated yet (WO-95/96).
