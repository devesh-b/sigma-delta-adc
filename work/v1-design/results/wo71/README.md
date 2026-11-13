# WO-71 (C9p): CTS_SINK_CLUSTERING_SIZE = 8. EXIT=0, fanout 10 -> 0, physical clean, slew unchanged (43 pins at ss_1v40)

- Single change vs WO-69 (7841d57): `CTS_SINK_CLUSTERING_SIZE` unset -> 8 (commit fe8b8bf). RTL md5 per file identical to WO-69 run copy.
- Variable source (container `/usr/local/lib/python3.12/dist-packages/librelane`, LibreLane 3.1.0.dev3): `steps/openroad.py:2495`
  (Optional[int], no default, "maximum number of sinks per cluster"), passed as `-sink_clustering_size` by `scripts/openroad/cts.tcl:67`.
  Related: CTS_SINK_CLUSTERING_ENABLE (default True, :2488), CTS_SINK_CLUSTERING_MAX_DIAMETER (:2500, unset), CTS_CLK_MAX_WIRE_LENGTH (:2517, 0).
  There is no CTS_MAX_FANOUT variable.
- Why 8, not 10: in WO-69, with the size unset, TritonCTS searched sizes and chose 10 / diameter 50 (CTS-0206, 22 leaves, 11 dummy loads
  CTS-0207), yet 10 leaves ended at 12-13 sinks. An explicit 10 would repeat the auto choice. 8 leaves margin for overflow and dummy loads.
- Log confirms: `clock_tree_synthesis ... -sink_clustering_size 8 -sink_clustering_enable -apply_ndr half`; 30 leaf buffers, 35 clock buffers,
  17 dummy loads, max 3 buffers in the clock path.
- Run `/home/mempool/regr/tt/WO-71/fe8b8bf/` (git archive fe8b8bf). pnr1.log ends EXIT=0. Data: `final/metrics.json`, `*-openroad-stapostpnr/<corner>/checks.rpt`.

| Check | WO-69 | WO-71 |
|---|---|---|
| Setup WS max/nom/min ss_1v40 | +2.702 / 2.826 / 3.002 | +2.777 / 2.908 / 3.065 (Fmax ~55.4 MHz); 0 vio at all 12 corners |
| Setup WS ss_1v60 / tt / ff (max RC) | 7.463 / 8.768 / 9.255 | 7.465 / 8.768 / 9.254 |
| Hold WS (min_ff) | +0.108 | +0.108; 0 vio at all 12 corners |
| Max fanout | 10 (clkbuf_leaf, 12-13 sinks) | **0** at all 12 corners |
| Max slew | 43 nom/max ss_1v40, 11 min ss_1v40 | 43 / 11, same corners; worst 1.720 ns vs 1.5 (net driven by fanout116, buf_1, mux S pins) |
| Max cap | 0 | 0 |
| Magic / KLayout / route DRC | 0 / 0 / 0 | 0 / 0 / 0 (iter0 15) |
| LVS (7 counters), XOR | 0, 0 | 0, 0 |
| Antenna (route, net/pin) | 0, 0/0 | 0, 0/0; 13 port diodes |
| Clock buffers / clock inverters | 29 / 9 | 37 / 15 (more leaves + dummy loads) |
| Repair / hold buffers | 296 / 179 | 299 / 182 |
| Std-cell area, util | 15,276 um2, 0.668 | 15,434 um2, 0.675 |
| Power, IR worst | 1.655 mW, 0.34 mV | 1.705 mW (+3 %), 0.37 mV |
| Skew | 0.26-0.29 ns | 0.26-0.29 ns |
| Unannotated nets (filtered) | 12 (0) | 18 (0); inferred: extra dummy-load outputs, as in WO-69 (clkload*) - not checked per net |
| Route wirelength | 31,338 um | 31,356 um |

- Setup +0.08 ns at ss_1v40 is within run-to-run noise; no mechanism claimed.
- Note: the Max Slew checker only warns (checker.py:626); the flow exits 0 with 43 slew violations. Slew is not gated by EXIT.

## Still open (recoverable)
- Slew at ss_1v40 only, up to 0.22 ns over 1.5 ns, on the buf_1 repair-buffer nets. Cells outside the characterised range make the ss_1v40 timing less trustworthy.

## Proposed next single change (not run)
- `RUN_POST_GRT_DESIGN_REPAIR = true` (flows/classic.py:139, default false; log confirms OpenROAD.RepairDesignPostGRT is skipped now). Re-sizes the
  buf_1 fanout buffers against routed load. Risk: placement perturbation, more buffers, hold recheck. Verify: slew 0 at all 12 corners, all other rows unchanged or explained.
