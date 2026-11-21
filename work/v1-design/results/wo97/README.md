# WO-97 (C9): final PnR, D85/D88 RTL (baa0706) + bias_ok pin. EXIT=0. Physical and LVS clean; routed GL/SDF 5/5 PASS

Inputs: commit 6b474df. The only flow change from config 9def89a is that `pin_order.cfg` gains `bias_ok` (#S, x = 20.47 um). The RTL has not changed since baa0706.
Frozen copy: /home/mempool/regr/tt/WO-97-6b474df (git archive). Run: `.../design/c9_digital/flow/runs/pnr1` (LibreLane 3.1.0.dev3, IIC 2026.10).

| Check | WO-73 (old RTL) | WO-97 |
|---|---|---|
| Setup WS, 12 corners | ss_1v40 max +2.961 | ss_1v40 max/nom/min +0.753/+0.891/+1.041; ss_1v60 +7.50; tt +8.78; ff +9.27; 0 vio |
| Hold WS | +0.108 | +0.079 (max_ff); 0 vio; 187 hold buffers |
| Max slew (D86) | 32/21/11, worst 1.728 | 43/11/0 at ss_1v40 max/nom/min, worst 1.634; 0 at every other corner |
| Max cap / fanout | 0 / 0 | 0 / 0 at all 12 corners |
| Magic / KLayout / route DRC, XOR | 0/0/0, 0 | 0/0/0, 0 |
| LVS | not extracted | netgen "Circuits match uniquely", all lvs counts 0 (71-netgen-lvs/reports/lvs.netgen.rpt) |
| Antenna (route / CheckAntennas) | 0 | 0 / 0 nets 0 pins |
| Util, stdcell area, power, IR | 0.676, -, 1.705 mW, 0.37 mV | 0.739, 16,895 um2 (190x150 die), 1.787 mW, 0.30 mV |

- Worst ss_1v40 path: _1586_ (dfrtp) -> or3/or4/or4b reduction chain -> and4 -> fanout45 buf_1 (1.42 ns) -> mux2/xor2/a221o/a211o/or4/or3
  -> _1430_, arrival 20.43 ns, required 21.18 ns. Inferred, not traced by name: the new D85/D88 counter-done logic adds depth (setup +2.96 -> +0.75).
- Floating nets (RSZ-0020, step 32): there are 2, VPWR and VGND, which are special supply nets with no signal driver. This is expected and benign (same as WO-58B). Odb scan: fl.tcl.
- D86 waiver: recorded in design/c9_digital/HARDENING.md with the 4 nets: net56, net66, net122, net124, all on buf_1 fanout buffers.
- Bench clock: test_c9.py drives clk at 20 ns, while the SDC period is 20.833 ns. At ss_1v40, 20 ns would leave about -0.08 ns of setup (inferred). The SDF sims
  therefore use ss_100C_1v60, not ss_1v40.
- GL/SDF: `gl_routed.sh` runs the routed nl.v with the sky130 hd specify models, `-gspecify -ginterconnect` and `$sdf_annotate` on u_core.
  The widths are fixed at 16/8 in the routed netlist, so small-width quick tests are not possible on it. Jobs (gl_jobs.txt): d_hold01_len at tt nom / ss_1v60 max / ff min,
  and d_hold05_d88 at tt nom / ss_1v60 max. They ran in lpool PRIO=high (results below).
  Compile smoke (cc.sh): iverilog rc 0, SDF annotates. 8 "could not insert intermodpath" errors remain, not root-caused. Icarus ignores TIMINGCHECK, so these sims prove function with delays, not timing.
- GL/SDF results (pool POOL_DONE, 5/5 EXIT=0, /home/mempool/regr/tt/WO-97-6b474df/pool/job_1..5.log), routed nl.v (3610 cell refs), 16/8:
  | job | SDF | test | result | sim time | wall |
  |---|---|---|---|---|---|
  | tt_h01 | nom_tt_025C_1v80 | d_hold01_len | PASS | 31,463,030 ns | 418 s |
  | ss60_h01 | max_ss_100C_1v60 | d_hold01_len | PASS | 31,463,030 ns | 422 s |
  | ff_h01 | min_ff_n40C_1v95 | d_hold01_len | PASS | 31,463,030 ns | 413 s |
  | tt_h05 | nom_tt_025C_1v80 | d_hold05_d88 | PASS | 189,002,570 ns | 2439 s |
  | ss60_h05 | max_ss_100C_1v60 | d_hold05_d88 | PASS | 189,002,570 ns | 2570 s |
  Not vacuous: each run executed its 1 selected test for the full sim time, the same as the WO-83 yosys GL at 16/8 (31,463,030 / 189,002,570 ns). The h05 log shows the
  hand-derived case checks running (e.g. "drop_on_slot0_tick: slot-0 tick 65537, rst_analog fall at rise 65539").
  SDF: 0 "could not find net". 8 of 3203 INTERCONNECT entries were not applied ("Could not find intermodpath", SDF lines 26-40, at the file head; probably the
  port-to-pin interconnects, inferred). There are 2 header "Chosen value not defined" lines (9, 11), and TIMINGCHECK is ignored.
  Limits: function with back-annotated delays only, with no setup/hold checks in icarus. These two tests were not shown to fail on a broken routed copy in this WO.
  The ss_1v40 SDF was not run (bench clock 20 ns). The quick suite was not run on the routed netlist (fixed widths).
- WO-96 hand-off: GDS `final/gds/sd_adc_c9.gds`, LEF `final/lef/sd_adc_c9.lef` (190x150 um, 43 pins), pins in /home/mempool/regr/tt/WO-97-6b474df/pins.txt.
  North edge (y = 149.86, met2): clk 8.51, rst_n 15.41, ui_in 22.31..70.61, uo_out 77.51..125.81, uio_out 132.71..181.01.
  South edge (y = 0.14, met2): comp_in 8.05, bias_ok 20.47, fs_clk 32.89, y_dac 45.31, y_force 57.73, bit_valid 70.15, rst_analog 82.57, sys_swap 94.99,
  ota_chop_phase 107.41, short_o 119.83, order_o 132.25, boost_o 144.67, trim_o[0..2] 157.09/169.51/181.93. VPWR/VGND are met4 straps (x 21.84/25.14 first strap).
- Status: NOT yet a signoff candidate. Remaining: (1) [done: GL/SDF 5/5 PASS]; (2) the user re-confirms D86 at the +0.75 ns ss_1v40 margin;
  (3) formal equivalence RTL vs nl.v (HARDENING 5, not run); (4) gl_job.sh prints "GL cell instances: 0" because write_verilog writes expressions; tell the rtl-verification owner.
