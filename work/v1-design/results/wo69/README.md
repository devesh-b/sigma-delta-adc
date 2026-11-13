# WO-69 (C9o): RUN_HEURISTIC_DIODE_INSERTION = false. EXIT=0, physical clean, DRV down to 10 fanout + 4 slew drivers

- Single change vs WO-66 (flow e450ae2): `RUN_HEURISTIC_DIODE_INSERTION` true -> false (commit 7841d57). The base is the
  config with the buf_1 ban reverted (8ddea05; frozen config has no buf_1 in EXTRA_EXCLUDED_CELLS).
  RTL = committed d971935, md5 of all 7 rtl/*.v identical to the WO-66 run copy.
- Variable source (container `/usr/local/lib/python3.12/dist-packages/librelane`, LibreLane 3.1.0.dev3):
  `flows/classic.py:166` (default False, "for compatibility with OL1"). It gates `Odb.HeuristicDiodeInsertion` at classic.py:277.
  The log confirms "Gating variable for step 'Odb.HeuristicDiodeInsertion' set to 'False'- the step will be skipped."
  Still active: RUN_ANTENNA_REPAIR (default True, classic.py:171) and DIODE_ON_PORTS "in" (Odb.PortDiodePlacement, steps/odb.py:740).
- Run: `/home/mempool/regr/tt/WO-69/7841d57/` (git archive 7841d57). Log pnr1.log ends EXIT=0. Metrics come from `final/metrics.json`
  and `*-openroad-stapostpnr/<corner>/checks.rpt`.

## WO-66 -> WO-69 (all 12 corners)
| Check | WO-66 | WO-69 |
|---|---|---|
| Setup WS max_ss_1v40 / nom / min | +2.582 / 2.713 / 2.878 | **+2.702** / 2.826 / 3.002 (Fmax 55.2 MHz) |
| Setup WS ss_1v60 / tt / ff (max RC) | 7.399 / 8.734 / 9.235 | 7.463 / 8.768 / 9.255; 0 vio at all 12 corners |
| Hold WS min (min_ff) | +0.108 | +0.108; 0 vio at all 12 corners |
| Max fanout (all corners) | 46 | **10** (all are clkbuf_leaf_*: 12-13 sinks vs 10) |
| Max slew | 256 max_ss_1v40, 44 max_ss_1v60 | **43 pins at nom/max_ss_1v40, 11 at min_ss_1v40, 0 elsewhere** |
| Max cap | 3 (max_ss_1v60) | **0** at all corners |
| Magic / KLayout / route DRC | 0 / 0 / 0 | 0 / 0 / 0 (iter0 23, was 265) |
| LVS (7 counters), XOR | 0, 0 | 0, 0 |
| Antenna: CheckAntennas pre / post repair, route antenna | 0 / 0, 0 | 0 net / 0 pin (40- and 46-openroad-checkantennas), route 0 |
| Diode cells | 342 (856 um2) | 13 (32.5 um2; input-port diodes) |
| Std-cell area, util | 16,099 um2, 0.704 | 15,276 um2, 0.668 (die 190x150 unchanged) |
| Repair / hold buffers | 296 / 179 | 296 / 179 |
| Power, IR worst | 1.644 mW, 0.34 mV | 1.655 mW, 0.34 mV |
| Skew, unannotated nets | 0.26-0.30 ns, 12 | 0.26-0.29 ns, 12 (filtered 0) |
| Wirelength (route) | n/a | 31,338 um |

- Critical path at ss_1v40 is unchanged: `_1437_` (u_seq.c[5]) -> `_1280_` (cfg_pending), arrival 18.51 ns.
- The remaining max slew at ss_1v40 comes from 4 drivers: `fanout116`, `fanout68` and `fanout57` (sky130_fd_sc_hd__buf_1, 1.75/1.63/1.62 ns)
  and `_1110_` (nor3b_2, 1.58 ns), against a 1.5 ns limit. The same buf_1 repair buffers were flagged in WO-66.
- Inference (not measured): the +0.12 ns at ss_1v40 and the lower slew come from the diode loads that were removed. The deltas are small
  and could be run-to-run noise.

## Still open (recoverable: frequency-independent only in the constraint sense; no functional or physical failure)
- Fanout: 10 CTS leaf buffers with 12-13 sinks against the SDC `set_max_fanout 10`. This sits on the clock tree, and skew and timing are met.
- Slew: 4 drivers at ss_1v40 only, up to 0.25 ns over the limit. Cells outside their characterised range make the ss_1v40 numbers less trustworthy.

## Proposed next single change (not run)
1. Clock-leaf fanout: cap CTS sink clustering at 10 or fewer. First confirm the variable name and default in the container
   (`grep -n CTS_ steps/openroad.py`, e.g. a CTS sink-clustering size or max-diameter variable). Expected effect: fanout 10 -> 0, a few more
   clkbuf leaves, a small rise in skew and power. Hold must be rechecked.
2. After that, for slew: `RUN_POST_GRT_DESIGN_REPAIR = true` (classic.py:139, default false). It re-sizes the buf_1 fanout buffers
   against routed load. Risk: placement perturbation and runtime. Use it instead of a cell ban, because of the WO-67 lesson.
