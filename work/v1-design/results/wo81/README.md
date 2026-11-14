# WO-81 (C3h): D87 bench basis + rev f op/on keeper

Code: commit fe9e787 (`design/c3_comp/c3_tb.py`, `netlist.py`, `sizes_draft.py`). Frozen copy:
`/home/mempool/regr/tt/WO-81-fe9e787` (design/ without c1_ota1, c6_bias; golden, model, scripts; `.spiceinit`
num_threads=1). Pool: 49 of the 72 generated decks (`run/jobs_wo81.txt`), started 15:13 at load ~9 (1 slot,
WO-78 pool still running beside it).

## WO-78 pool (input)
Not finished at 15:10 (5 of 13 jobs started, `POOL_DONE` absent), so `results/wo78/summary.txt` is not written yet.
Pickup below.

## Item 1: bench basis per D87 (`c3_tb.py` st_deck, constants V_ST / EDGE_C4 / X2_LO, X2_HI)
- **(a) Supply:** first try (fe9e787) put an ideal source straight on vdd: every st deck aborts at the 400 ns ramp corner ("timestep too small ... vrdd#branch", the WO-79 root cause; green-is-not-proof: caught by tend). Implemented instead (600c547): 10 ohm feed kept for numerics, and its drop is not counted: each 1.8 V oxide pair is judged on |V| - max(0, vdd(t) - 1.98 V) (`st_post`; raw peak `_Pr` still cross-checked against vecmax). Coordinator: confirm this reading of D87(a).
  Broken copy `st_brk_vdd200` (ideal 2.00 V) must REJECT (`over:sus` on the on-state rail-to-rail pairs). Info:
  `st_info_rvdd_tt27_a` (old 10 ohm feed).
- **(b) Strobe edge:** C4 phiC 10-90 % rise / fall per corner, measured here from the WO-70 C4 tim waveforms
  (`/home/mempool/regr/tt/WO-70-01fc505/run/tim_<corner>_*.csv`, net `phc` = se -> 2 hvl inverters ->
  `lsbufhv2lv_1`, 50 fF load; C4 `netlist.py` lines 182-184, tb `Clphc 50f`):

  | corner (C4 deck) | rise 10-90 | fall 10-90 |
  |---|---|---|
  | tt/27/1.80 V | 0.626 ns | 0.252 ns |
  | ff/-40/1.98 V | 0.448 ns | 0.177 ns |
  | ff/125/1.98 V | 0.403 ns | 0.238 ns |
  | ss/-40/1.62 V | 1.337 ns | 0.320 ns |
  | sf/-40/1.62 V (ls) | 1.354 ns | 0.220 ns |

  Deck ramp = 1.25 x (0-100 %). The T8 rows use tt and ff. Caveat: the tt number is at VDPWR 1.80 V, the T8 deck
  runs at 1.98 V, so the tt ramp is slightly slow; ff/-40 at 1.98 V is the fast bound. Info row
  `st_info_edge01_tt27_a` keeps the 0.1 ns ideal edge. Broken copies on the real edge: `st_brk_noclamp`,
  `st_brk_nokeep`, `st_brk_nokeep_ff-40_b`.
- **(c) x2 stimulus:** assumed OTA2 range (C2 not designed): CM 1.2..1.8 V (the cyc cm12 / cm18 rows) +-0.705 V
  (x2 peak 1.41 V diff, `DESIGN.md` 3.1b; SPEC row 91 A >= 75 dB for |Vout,diff| <= 1.4 V) = 0.495..2.505 V per
  side, + 0.2 V margin = **0.3..2.7 V**. Power-up still holds both sides at the 3.6 V VAPWR rail (OTA2 output before
  its CMFB settles). Info row `st_info_x2m05_tt27_a` keeps the old -0.5 / 3.6 V steps. Broken copies on the bounded
  stimulus: `st_brk_noclamp`, `st_brk_nokeep*`.

## Item 2: rev f, one change: op/on keeper
`KPo`/`KPn`: pfet_01v8 **0.42/0.15** (minimum device), drain op/on, source + body vdd, gate ob1/nb1 (the first
buffer inverter of the same node). Reasoning: in rev e, with the pair off (x2 low), nothing drives op/on in the
strobe-high phase; the strobe rising edge couples through the precharge PMOS R0/R1 Cgd and leaves op/on ~66 mV
above VDPWR for the whole phase (WO-78: S 2.046 V, 126 ns). While op/on are high, ob1/nb1 are low, so the keeper is
on and returns the node to VDPWR; after a decision it is off (no static current). The sus limb (S <= 1.98 V over
1 ns windows) needs the kick to decay to VDPWR inside 1 ns: 66 mV down to the leakage floor (tens of uV) is ~8
time constants, so tau must be <~ 0.1 ns. Minimum size: linear Ron ~5 kohm at Vgs 1.98 V, op/on ~15 fF -> tau ~75 ps.
A weaker keeper needs a longer L (more area and cap, slower decay), so the minimum device is both the smallest and
the only size class that meets the 1 ns window. Cost: ~0.13 mA saturated keeper current against the CM discharge
at the start of evaluation (both sides, matched) -> watch T2 decision time and T3 offset. "nokeep" = rev e.

## Item 3: results (rev f vs rev e)
First rows (st, 15:26, WO-81-600c547):

| row | S (sustained) | P (peak) | D (longest > 1.98) | verdict |
|---|---|---|---|---|
| st_tt27_a (rev f) | 1.980284 V, M4 gb (op) | 2.2206 V M4 gb @2494 ns | 143.8 ns, Sb3 gb | REJECT sus+cap |
| st_brk_nokeep (rev e, D87 basis) | 2.013767 V, M4 gb | 2.2797 V | 143.8 ns | REJECT sus+cap (expected) |

The keeper cuts the op/on sustained excess from 34 mV (rev e on the same basis; 66 mV in WO-78) to 0.28 mV, but
**rev f still REJECTs**: (1) a residual 0.28 mV sustained on op/on vs vdd-set, and a 143.8 ns > 1.98 V stretch on
Sb3 gb (gate nb2 = an on-state rail node: likely the same sub-mV residual, i.e. the drop-subtraction or an on-state
node sitting above vdd(t); not diagnosed, budget); (2) cap: 2.2206 V at 2494 ns (precharge edge, real C4 edge),
20 mV over 2.2 V (was 2.28 V at the 0.1 ns edge). Not a pass; no limit changed. Remaining rows (ff-40, order b,
broken / info copies, one/mc/cyc) still running. Rev e reference (WO-68, `WO-68-764fd1c/run/collect.log`): T3 mc_tt |mu|+3s 49.59 mV
(sigma 16.32), mc_ss40 49.26 mV (sigma 15.17); T5 worst diff kick 1.82 mV (fs/125), CM kick 40.1-48.1 mV;
T2 one_ss40 tdec 2.035 ns, cyc_ss-40_162 tdec max 2.293 ns, cyc_tt 1.506 ns.

## Item 4: checker copies
Still trivial: st_chk_sus195 / cap20 / dur01 all REJECT with `over:sus, over:cap` because the base row st_tt27_a REJECTs; not re-judged as live. st_brk_noclamp pending.

## Pickup
    ssh sandbox; F=/home/mempool/regr/tt/WO-81-fe9e787
    ls $F/run/pool_logs/POOL_DONE && cat $F/run/collect.log $F/run/t8_devices.txt   # COLLECT_EXIT at the end
    W=/home/mempool/regr/tt/WO-78-1f18fa6; ls $W/run/pool_logs/POOL_DONE && cat $W/run/collect.log
Collect judges all 72 deck dirs; the 23 not in `jobs_wo81.txt` (cyc_info_revc_*, sens_tt, pdk_tt, mc_info_x3_*,
cyc rows other than ss-40_162 / tt+27_180 / brk_weak) have no log and show as off-expectation: ignore those rows.
    F2=/home/mempool/regr/tt/WO-81-600c547; ls $F2/run/pool_logs/POOL_DONE && cat $F2/run/collect.log $F2/run/t8_devices.txt
Use one_*/mc_*/cyc_* rows from $F and st_* rows from $F2 only.
