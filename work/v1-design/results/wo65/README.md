# WO-65 (C3e): comparator close on rev d — NOT closed

Frozen copy `/home/mempool/regr/tt/WO-65-e450ae2-wt` (HEAD e450ae2 + uncommitted c3_comp changes; commit signing blocked), launcher `/home/mempool/regr/tt/wo65_launch.sh`. 63 decks generated; 61 reuse the WO-56 `deck.log` because their `deck.sp` (title line excluded) and `.spiceinit` are byte-identical (`run/reuse.txt`). Only 2 decks ran (one_brk_nohvc, one_info_nopa). Collect: `run/collect.log`, exit 1, 5 rows off expectation. No csv files.

## Item 1: D80 T8 split (done in the tb, SPEC CL-33, row 99)
- 1.8 V: oxide pairs (Vgs, Vgd, Vgb) and Vds ≤ 1.98 V (unchanged). Junctions (Vsb, Vdb) ≤ 4.95 V.
- Rating source (PDK at `/home/mempool/.ciel/sky130A`, ciel d56f8a8): the nfet_01v8 S/D junction is `diode_pw2nd_05v5`, the pfet_01v8 one is `diode_pd2nw_05v5`. Both carry the `_05v5` 5.5 V rating suffix. Model breakdown: bv 11.7 V and 12.69 V (`libs.ref/sky130_fd_pr/spice/*.model.spice` line 38). The nfet_01v8 BSIM4 cards give bvs 11.7 V. Limit = 5.5 V − 10 %. No rating table ships in the PDK docs (only the xschem README suffix list).
- HV devices are unchanged: every pair ≤ 5.5 V.
- Re-judged WO-56 data: the junctions pass (max 2.38–2.39 V on the M3/M4 sb, against 4.95 V). **New finding: the gated decks still REJECT on the oxide class.** Vds is 2.32–2.33 V on the SR-latch NMOS Sq3/Sb3 (drain ql/qlb, source sq/sb) in st_tt27_a/b and st_ff-40_a/b. The 2.38 V junction value hid this until now. It also shows in rev b/c and the fast/async copies, so it is not new in rev d. It is not diagnosed yet: within a 1.98 V supply, it needs a node outside 0…VDPWR (likely during the ramp or the x2 −0.5 V step).
- Broken copies: st_brk_in18 REJECTs on oxide (M2 gb 3.78 V). st_chk_jn20 (the same deck as st_tt27_a judged at a 2.0 V junction limit) REJECTs with `over:jn`, so the junction limb is live. No physical broken copy can exceed 4.95 V: the largest node span in the system is ≈ 4.1 V (3.6 V to −0.5 V).

## Item 2: T5 broken copy — still blind
- one_brk_nohvc (cascode + ap/an precharge removed, pair drains on dp/dn, HV tail) **ACCEPTs**: kick 0.34 / 2.67 mV, limit 5 mV. one_info_nopa: 0.32 / 0.46 mV. one_info_cl10: 2.20 / 1.49 mV.
- So the diff kick on x2 stays under 5 mV even with no isolation. At C_x2 0.7 pF with R_X2 20 kΩ, the T5 row has no physical isolation-removed copy that REJECTs. Options: (a) combine nohvc with C_x2/10; (b) have the row gate the CM kick as well (cm_peak 40 mV nominal vs 236 mV for cl10); (c) accept that T5 has margin by construction and keep a checker copy.

## Item 3 (info)
- asym10 (±10 % R/C): kick 7.46 / 5.30 mV, REJECT (info).
- The realistic gate asym (±5 % R, ±1 % C) passes: 1.56 / 1.38 mV, recovery 0.40 mV. Left as is.

## Exit
Not met: st_tt27_a/b and st_ff-40_a/b REJECT (Vds on Sq3/Sb3), and one_brk_nohvc ACCEPTs. The reviewer pass should wait.
