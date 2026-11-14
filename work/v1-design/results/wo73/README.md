# WO-73 (C9r): GRT_DESIGN_REPAIR_MAX_SLEW_PCT 10 -> 40. EXIT=0, slew 43 -> 32 (max ss_1v40), worst unchanged 1.728 ns; DRV not 0

- Item 1 (diag_slew.tcl / diag_run.sh, logs /home/mempool/regr/tt/WO-73/diag/): WO-72 final ODB, ss_100C_1v40, worst slew per net (ns):
  | net (driver) | placement est | GRT est | RCX nom | RCX max | max/GRT |
  |---|---|---|---|---|---|
  | net116 (fanout116/X) | 1.184 | 1.257 | 1.643 | 1.720 | 1.37 |
  | net68 (fanout68/X) | 1.064 | 1.104 | 1.586 | 1.650 | 1.49 |
  | net57 (fanout57/X) | 1.012 | 1.072 | 1.502 | 1.589 | 1.48 |
  | _0181_ (_1110_/Y) | 1.147 | 1.171 | 1.527 | 1.605 | 1.37 |
  Estimates use set_wire_rc met2/met3, not LibreLane set_rc per-layer values (approximation). 0 estimated violators; 43 with RCX max.
  Sizing: 30 % (1.05 ns) x 1.49 = 1.56 ns fails, so 40 % (0.9 ns) chosen. Source: steps/openroad.py:2711 (default 10), repair_design_postgrt.tcl:37.
- Item 3 run /home/mempool/regr/tt/WO-73/b8898159-c9def89a/ = git archive 8898159 + config.json from 9def89a (cmp: only config differs).
  The first copy /home/mempool/regr/tt/WO-73/9def89a/ failed EXIT=2 (HEAD already had the WO-74 RTL with bias_ok; pin_order.cfg has no bias_ok). Not used.
  Step 41: `repair_design -slew_margin 40.0`, final row: 1 resized, 5 buffers, 33 nets repaired (WO-72: 0).
  | Check | WO-72 | WO-73 |
  |---|---|---|
  | Max slew max/nom/min ss_1v40 | 43 / 43 / 11 (1.720) | 32 / 21 / 11 (worst 1.728, _1128_/A2 _1117_/B1 _1152_/A2) |
  | Setup WS ss_1v40 max/nom/min | 2.777/2.908/3.065 | 2.961/3.073/3.190; 0 vio |
  | Hold WS, vio | +0.108, 0 | +0.108, 0 |
  | Cap / fanout | 0 / 0 | 0 / 0 |
  | Magic/KLayout/route DRC, XOR | 0/0/0, 0 | 0/0/0, 0 |
  | Route antenna | 0 | 0 |
  | LVS | 0 | not extracted (unknown) |
  | Util, route WL, power, IR | 0.675, 31,356, 1.705 mW, 0.371 mV | 0.676, 31,427, 1.705 mW, 0.37 mV |
- Item 4: timing__drv__floating__nets = 2 comes from RSZ-0020 at step 32 (repairdesignpostgpl). Names not obtained (scp dropped). Open.
- Exit: DRV is not 0, so this is not a signoff candidate. Recoverable (ss_1v40 stand-in only, +2.96 ns setup).
  Next: rerun the diag on the WO-73 ODB for the new worst net (est vs RCX, likely ratio > 1.67). Then choose between a higher post-GPL DESIGN_REPAIR_MAX_SLEW_PCT (openroad.py:2649)
  and the diag using LibreLane set_rc. Final PnR is redone anyway for the D85 RTL; pin_order.cfg must gain bias_ok.
