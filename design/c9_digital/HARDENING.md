# C9 hardening plan (WO-47, pd-expert, 2026-11-12)

Status: **plan + synthesis/floorplan probe only. No PnR, no GDS.** Probe evidence: `work/v1-design/results/wo47/README.md`
(run `/home/mempool/regr/tt/WO-47-7742be2/c9_digital/flow/runs/probe`, LibreLane v3.1.0.dev3 in IIC-OSIC-TOOLS 2026.10,
TT-pinned sky130A open_pdks d56f8a8e). Measured / inferred / assumed are marked M / I / A.

## 1. How a digital block goes into a TT analog 2x2 tile

TT analog projects are submitted as a finished GDS + LEF (language "Analog"); TT's digital flow does not run on them. A
digital block is therefore hardened **as a separate macro** with OpenLane/LibreLane and instanced in the analog top
(Magic `.mag`), which then gets the template DEF pins and the power stripes. Evidence (M, reference repos, read only):
- `repos/adc-ref/flash-adc/openlane/encoder/config.tcl`: OpenLane macro `encoder`, absolute 80x36 um die, `DESIGN_IS_CORE 0`,
  `RT_MAX_LAYER met4` ("Don't use power rings or met5 layer"), pin order file; instanced as `use encoder encoder_0` in
  `mag/tt_um_htfab_flash_adc.mag`, GDS in `gds/encoder.gds`.
- `repos/adc-ref/tt07-12bit_SAR_ADC`: `state_machine_openlane_generated.spice` included in the top schematic (same pattern).
- `repos/sd-analog/ttsky-sigma-delta/tt_frame/build_frame.tcl` (Paul Thomas): template DEF read with `def read`, design placed
  with `getcell`, full-height met4 VDPWR / VGND / VAPWR stripes with labels spanning the stripe (10 um edge rule).
A top-level single flow (digital PnR over the analog area) is not used by any reference and is rejected: LibreLane cannot
place around MIM arrays and guard rings under our matching rules.

**Choice: separate LibreLane macro, imported as LEF/GDS into the Magic top (C7).**

## 2. Floorplan inside the tile
- Tile 319.24 x 225.76 um = 72,071 um2 (M, `tt_analog_2x2_3v3.def` DIEAREA). TT digital pins (ui_in, uo_out, uio_*, clk,
  rst_n) are on the **top edge** (met4, y 225.26), analog ua[*] on the **bottom edge** (y 0.5) (M, build_frame.tcl comment;
  re-check against the template DEF at C7).
- Macro along the top edge, full width as needed; TT pins enter its north side by short met4 drops. Analog interface pins on
  its south side (`flow/pin_order.cfg`). Below it: C4 (level shifters, phase generator) as a buffer band, then comparator,
  integrator 2, and **integrator 1 + Cs/Cint arrays at the bottom** next to ua0..ua3. This puts the maximum distance between
  the clock tree and OTA1 that the tile allows.
- Isolation (A, to be checked in C7 PEX/layout): p-tap guard ring around the macro tied to a **separate VGND stripe** that
  joins the analog VGND only at the tile power pin; analog in deep n-well / guard rings (SPEC 3.9); no route from the macro
  crosses the integrators; `fs_clk` routed along the C4 band edge, not over caps; the macro's own met4 straps stay inside it.

## 3. Size (probe result, M) and the area decision
- Synthesis (sky130_fd_sc_hd, LibreLane default script): **1111 cells, 15,172 um2 cell area, 276 flops** (257 dfrtp + 19 dfstp,
  6.75k + 0.50k um2). Flops are 48 % of the area. No latches (latch.rpt). The generic yosys count was 1174.
- I: after repair, CTS and hold buffers +10-15 % -> ~17-17.5k um2; at 60 % density + PDN margins the die is about
  **190 x 150 um (~28k um2), 35-45 % of the tile.** SIZING.md budgeted 8-15k um2 for the digital block: **over budget ~2x.**
- Largest lever (SPEC change, not mine): accumulator width. |acc1| <= N = 4096 needs 14 b signed, |acc2| <= N^2/2 needs 24-25 b;
  SPEC 3.7 fixes 2 x 32 b plus a 2 x 32 b hold. 14 + 25 b would save ~50 acc + ~50 hold flops (~2.6k um2) and adder area.
  The 16-bit word read-out (§3.8a) can sign-extend, so firmware is unchanged. Decision for the user (section 9).

## 4. LibreLane config draft (`flow/config.json`, `flow/c9.sdc`, `flow/pin_order.cfg`)
- clk 48 MHz (`CLOCK_PERIOD 20.833`), one clock domain (RTL README), SDC with every port constrained, **no false or
  multicycle paths**. `check_setup -unconstrained_endpoints -no_clock -no_input_delay -loops` is clean in the probe (M).
- PDN: macro style (no core ring), met1 rails + met4 straps, **no met5** (`RT_MAX_LAYER met4`). Probe warning (M):
  `FP_PDN_MULTILAYER` is deprecated in LibreLane 3.1; rename to the current key before PnR (check `librelane` docs in the image).
- `DIE_AREA [0,0,150,80]` in the draft is a **placeholder and is too small** (probe utilisation 1.91, M). Next run: 190 x 150 um
  at `PL_TARGET_DENSITY_PCT` 60, then shrink. Power straps: set pitch/offset so one VDPWR and one VGND strap pair lines up with
  the tile stripes, which C7 extends full height through a met4-free lane.
- Antenna: `RUN_HEURISTIC_DIODE_INSERTION`, `DIODE_ON_PORTS in`; keep LibreLane's antenna check on.
- Macro name: the RTL top is `tt_um_sd_adc_c9`. The shuttle merges all GDS, so the macro cell must not be the project's
  top_module name and should carry the project prefix; renaming is an RTL change (decision 9.3).

## 5. STA corners and the SDF gate-level plan
- LibreLane sky130 corners: tt_025C_1v80, ss_100C_1v60, ff_n40C_1v95 x min/nom/max RC (9 at signoff, M: 3 nom pre-PnR).
- **Gap vs SPEC 6** (VDPWR 1.62-1.98 V, -40..125 C): no hd liberty at 125 C or 1.98 V (M, lib dir). Proposal: add
  `ss_100C_1v40` as a pessimistic proxy for ss/125 C/1.62 V and keep ff_n40C_1v95 for hold, with 125 C and 1.98 V listed
  as **Unknown (no model)**. Pthomas: TT SAR silicon ran ~2x the tt timing (LEARNINGS), so require ss setup slack >= 0 **and**
  tt path <= period/2.
- Probe (pre-PnR, ideal clock, no wires, M): setup WNS 1.75 ns at ss_100C_1v60, 9.07 tt, 9.38 ff; hold WNS -1.06 ns (input
  ports, min delay 0, unrepaired), 559 max-slew / 16 fanout / 5 cap violations. Critical path: `act[8]` (fs_div[1]) -> divider
  compare -> `fs_tick` net with ~10 ns slew (unbuffered fanout into the mux selects) -> datapath. **Not representative**: the
  10 ns slew goes away with buffering. Re-judge only post-route.
- Recoverability: setup is **recoverable** (lower TT clk; fs scales down, the 4 MHz mode is lost). RTL lever if post-route ss
  slack is thin: register `fs_tick`/`s_tick` one clk early (decode `dc == div_m1 - 1`), which removes the decode from the path.
- GL plan (after PnR): (1) formal equivalence RTL vs final netlist (yosys `eqy` if in the image, else yosys equiv); (2) the
  existing `tb/gl_job.sh` golden tests on the final netlist with SDF back-annotation at ss max (setup) and ff min (hold),
  iverilog `-gspecify` with sky130 cell models (not `FUNCTIONAL`); (3) reset/X: outputs and uio_oe not X after rst_n.

## 6. Analog/digital interface (CL-23 port contract)
- Out to C4 (levels, 1.8 V): fs_clk, rst_analog, sys_swap, ota_chop_phase, short_o, order_o, boost_o, trim_o[2:0], y_force,
  bit_valid, y_dac. They must be **direct flop outputs** (no glitch into level shifters): check in the final netlist (Unknown).
- In: comp_in, captured on the clk edge with `s_tick` (bit clock falling, CL-23); not synchronised in RTL. Safe only if the
  comparator output changes **after** that edge (C4 + C3 delay > flop hold) and is latched for the rest of the fs period.
  **F-IF-1:** C3/C4 must guarantee a latched (SR) comparator output and min delay clk->comp_in >= 1 ns (SDC assumes 1.0 ns);
  otherwise metastability on the one bit that feeds both DAC and decimator (fatal: wrong function at random).

## 7. info.yaml implications
`language: Analog`, `tiles: "2x2"`, `analog_pins` = used ua count, **both `uses_3v3: true` and `uses_vapwr: true`** (key rename,
LEARNINGS / pthomas info.yaml), top_module = the Magic top (not the macro). All uo_out, uio_out and uio_oe are driven by the
macro (uio_oe = 0xFF via tie cells); `ena`, `uio_in` unused.

## 8. Precheck traps
- No antenna check for sky130 in precheck (pd notes): run Magic antenna on the full top ourselves (pthomas `tools/antenna.tcl`).
- Power labels must span the full stripe (within 10 um of both edges); macro straps are not tile ports.
- Precheck does not check tied outputs (WO-01): verify by extraction that all 24 outputs reach a driver.
- met5 forbidden: verify the macro GDS has no met5/via4 (KLayout layer check).
- Tools: precheck@ttsky26d uses tt-support-tools `main` (unpinned): pin a commit for our runs; Magic `expand` before DRC.
- Extract the framed top and run netgen LVS with the macro netlist; prove pin connectivity (missing via killed a tt08 RO).

## 9. Decisions for the user
1. Area: accept ~35-45 % of the tile for C9, or narrow acc1/acc2 (SPEC 3.7 change; saves ~15-20 % of C9).
2. Corners: accept ss_100C_1v40 as the 125 C proxy and 125 C / 1.98 V as unmodelled.
3. Macro cell name: rename the RTL wrapper (prefixed, not the top_module) before PnR.
4. Approve the next run: full LibreLane PnR of the macro at 190 x 150 um (one run, sandbox).
