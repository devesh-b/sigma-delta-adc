# WO-106: C9 die 175x150 trial (D96), KEPT

Input: commit 9650241, which changes only `DIE_AREA` [0,0,190,150] -> [0,0,175,150]. Pins (pin_order.cfg), density 60 and the SDC are as in WO-97.
Frozen copy: /home/mempool/regr/tt/WO-106-9650241 (git archive of design/c9_digital). Run: `/home/mempool/regr/tt/WO-106-9650241/design/c9_digital/flow/runs/pnr1`, EXIT=0 (launch.sh).

## Results (final/metrics.json). Base WO-97 (190) and WO-101 (165) in brackets
| Check | 175x150 | WO-97 190 | WO-101 165 |
|---|---|---|---|
| Setup ss_100C_1v40 max/nom/min (ns) | +0.937 / +1.060 / +1.207 | +0.753 max | -0.095 / +0.078 / +0.222 |
| Setup ss_1v60 / tt / ff worst (ns) | +7.544 / +8.812 / +9.284 | +7.50 / +8.78 / +9.27 | +7.07 |
| Hold worst (ns) | +0.110 (ff min) | +0.079 | +0.108 |
| Max slew viols (ss_1v40 max/nom; other corners 0) | 19 / 8, worst 1.655 ns vs 1.5 (_0927_/A2) | 43/11, 1.634 | 11, 1.749 |
| Max cap / fanout | 0 / 0 | 0 / 0 | 0 / 0 |
| Magic / KLayout / route DRC, XOR | 0 / 0 / 0, 0 | 0 | 0 |
| LVS | 0 errors, "Circuits match uniquely." | match | match |
| Antenna nets/pins | 0 / 0 | 0 | 0 |
| Utilization, power, IR worst | 0.806, 1.774 mW, 1.19 mV | 0.739, 1.787 mW | 0.857, 1.05 mV |
| Floating nets | 2 (VPWR/VGND, as WO-97) | 2 | 2 |

Exit rule (ss_1v40 setup >= 0 at every RC corner, real corners clean, DRC/LVS/antenna 0): **met, config kept at 175x150.**
The stand-in slack is higher than at 190 (+0.94 vs +0.75), but no mechanism is identified. Treat it as placement noise. The robust result is setup >= 0 with ~0.9 ns margin.
The ss_1v40 slew violations are the same known class as WO-97 (stand-in corner only, D86 waiver record). They are not new.

## Hand-off (layout)
GDS `/home/mempool/regr/tt/WO-106-9650241/design/c9_digital/flow/runs/pnr1/final/gds/sd_adc_c9.gds`, LEF `/home/mempool/regr/tt/WO-106-9650241/design/c9_digital/flow/runs/pnr1/final/lef/sd_adc_c9.lef`, pins from design/c9_digital/flow/pin_order.cfg (unchanged from WO-97). The macro is 15 um narrower than the WO-96/WO-100 floorplan assumed.

## GL/SDF (WO-97 job set)
gl_jobs.txt = the WO-97/WO-101 5 jobs re-pathed to this run, in lpool PRIO=high, logs /home/mempool/regr/tt/WO-106-9650241/gl/job_*.log (POOL_DONE at the end).
The first launch was stopped by PID because gl_routed.sh lives only in results/wo97 and not in design/c9_digital/tb. It was copied in (identical to the WO-101 copy) and the pool relaunched.
**Status at hand-off: running, results UNKNOWN.** The function-only caveat from WO-97 applies (icarus, no TIMINGCHECK).
