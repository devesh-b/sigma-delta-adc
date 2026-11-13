# WO-72 (C9q): RUN_POST_GRT_DESIGN_REPAIR = true. EXIT=0, no effect: post-GRT repair_design changed 0 cells; slew 43/11 at ss_1v40 unchanged

- Single change vs WO-71 (fe8b8bf): `RUN_POST_GRT_DESIGN_REPAIR` false -> true (commit 8898159). RTL and c9.sdc identical to the WO-71 run copy (per-file md5).
- Variable source (container LibreLane 3.1.0.dev3, `/usr/local/lib/python3.12/dist-packages/librelane`): `flows/classic.py:139` (bool, default False,
  "experimental"), gates `OpenROAD.RepairDesignPostGRT` (classic.py:271; class at steps/openroad.py:2687; script scripts/openroad/repair_design_postgrt.tcl).
  Related vars kept at defaults (openroad.py:2697-2724): GRT_DESIGN_REPAIR_RUN_GRT true, _MAX_WIRE_LENGTH 0, _MAX_SLEW_PCT 10, _MAX_CAP_PCT 10.
- Run `/home/mempool/regr/tt/WO-72/8898159/` (git archive 8898159). pnr1.log ends EXIT=0. Step `41-openroad-repairdesignpostgrt` ran with all 12 corners loaded:
  `repair_design -verbose -max_wire_length 0.0 -slew_margin 10.0 -cap_margin 10.0`, every iteration row `+0.0% | 0 resized | 0 buffers | 0 nets repaired`.

| Check | WO-71 | WO-72 |
|---|---|---|
| Setup WS max/nom/min ss_1v40 | +2.777 / 2.908 / 3.065 | +2.777 / 2.908 / 3.065; 0 vio at all 12 corners |
| Setup WS ss_1v60 / tt / ff (max RC) | 7.465 / 8.768 / 9.254 | 7.465 / 8.768 / 9.254 |
| Hold WS (min_ff) | +0.108 | +0.108; 0 vio at all 12 corners |
| Max fanout / cap | 0 / 0 | 0 / 0 at all 12 corners |
| Max slew | 43 nom/max, 11 min ss_1v40 | 43 / 11, worst 1.7199 ns vs 1.5 (_0713_/S etc., fanout116 buf_1 net) |
| Magic / KLayout / route DRC | 0 / 0 / 0 | 0 / 0 / 0 (iter0 15) |
| LVS (7 counters), XOR | 0, 0 | 0, 0 |
| Antenna (route, net/pin) | 0, 0/0 | 0, 0/0 |
| Repair / hold buffers, std-cell area, util | 299 / 182, 15,434 um2, 0.675 | 299 / 182, 15,433.6 um2, 0.675 |
| Power, IR worst | 1.705 mW, 0.37 mV | 1.705 mW, 0.371 mV |
| Skew, route WL, unannotated (filtered) | 0.26-0.29 ns, 31,356 um, 18 (0) | same |
| timing__drv__floating__nets | 2 | 2 (present in WO-71 too; not root-caused, open) |

- Result is identical because the step was a no-op; the remaining PnR is then deterministic.

## Root cause (measured + inferred)
- Measured: scratch OpenROAD check on the step-41 ODB (`diag.tcl`/`diag.log` in run dir; ss_100C_1v40 lib, c9.sdc, `estimate_parasitics -placement`,
  met2/met3 wire RC): `report_check_types -max_slew -corner ss14 -violators` lists 0 violators. The script then stopped on a report_net bug, so the repair dry-run did not execute.
- Inferred: with estimated (placement/GRT) parasitics these nets sit below the 1.35 ns repair target (1.5 ns less 10 %), so neither post-GPL nor post-GRT repair acts.
  The 0.22 ns overrun appears only with post-route RCX SPEF. The estimate-vs-RCX slew gap on the fanout116 net was not measured.

## Proposed next single change (not run)
- `GRT_DESIGN_REPAIR_MAX_SLEW_PCT` 10 -> 30 (openroad.py:2711; repair target 1.05 ns). This is a stricter internal repair target. Signoff limits are unchanged, so no check is weakened.
  Keep RUN_POST_GRT_DESIGN_REPAIR true. Before running: fix diag.tcl (report_net by name) to measure the estimated slew on the fanout116 net and size the margin.
  Risk: more and larger buffers, placement perturbation, hold recheck. Verify: slew 0 at all 12 corners, other rows unchanged or explained.
- Fallback (Fail is recoverable): ss_1v40 setup has +2.78 ns, and the slews are 15 % over the characterised limit, so the ss_1v40 timing numbers carry extra uncertainty.
