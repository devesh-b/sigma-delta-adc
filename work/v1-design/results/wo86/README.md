# WO-86 (C3j): all C3 pools collected, stiff-supply robustness, over-supply path, kp2 verdict

Code: 7d9e174 (`supply_probe.py` set 3: `gen3` / `dpost`, device terminal currents via `save @m.xc.x<dev>.msky130_fd_pr__<model>[id/is/ib]`).
New frozen copy `/home/mempool/regr/tt/WO-86-7d9e174` (2 decks: `st_sw_icur`, `st_kp2_sw_icur`; design/ without c1_ota1,
c4_sw, c6_bias; `.spiceinit` num_threads=1; scripts/lpool.sh). No limit changed.

## Item 1: collection (all five pools POOL_DONE)
Collect logs copied here: `results/wo78/summary.txt`, `results/wo81/summary_{fe9e787,600c547}.txt`,
`results/wo84/summary_{d651488,7e83397}.txt`. Full reason lists from each `run/c3_tb.json` (the collect line prints
only `why[:3]`, so a third limb, usually `over:dur`, is hidden in the text logs: read the json for checker work).

Data checks: every row used below has `sanity=ok` (tend reached, temp, vdd) and n = all pairs. Rows with `tend`
failures are only the expected ones: ideal / ammeter-split st decks (`st_sw_split`, `st_ideal`, `st_p10_split`,
`st_r001_split` + its 3 chk copies: abort at the 400 ns ramp corner), and in WO-81-fe9e787 the cyc_* rows, which were
**never run** (not in `jobs_wo81.txt`; deck dirs hold only deck.sp). So there is **no rev f cyc row**; the only cyc
row on rev f+ is `cyc_kp2_ss-40_162` (WO-84).

Rev f vs rev e (rev e = WO-68 numbers quoted in wo81/README):

| test | rev e | rev f (WO-81-fe9e787) | rev f + kp2 (WO-84-d651488) |
|---|---|---|---|
| T3 MC tt, abs(mu)+3s (sigma) | 49.59 mV (16.32) | 45.07 mV (14.81), n=200 | not run |
| T3 MC ss/-40, abs(mu)+3s (sigma) | 49.26 mV (15.17) | 42.74 mV (14.21), n=50 | not run |
| T2 one_ss-40_162 tdec | 2.035 ns | 1.354 ns | 1.291 ns |
| T2 cyc_ss-40_162 tdec max | 2.293 ns | not run | 1.343 ns (T1/T2/T7/T10 ACCEPT) |
| T5 diff kick, ss-40 / worst (fs+125) | - / 1.82 mV | 0.617 / 2.524 mV | 1.142 / 3.399 mV |
| T5 CM kick range (all one_ corners) | 40.1-48.1 mV | 38.96-47.41 mV | 38.92 (ss-40), 46.82 (fs+125) |

T3 rows REJECT only on `plaus` (sens/pdk decks not in this pool, sigma_est NaN), as in earlier pools; the count/mu3s
limbs pass. The rev f T2 gain over rev e is not explained here (the D87 x2 stimulus range changed between WO-68 and
WO-81, so this is not a pure keeper effect). All one_* p-rows ACCEPT T5; broken copies (one_brk_starve, one_chk_kick1,
one_chk_rec02, mc_brk_x6) REJECT for their own reasons.

T8 (st) rows, raw |V| on the stiff pin (WO-84-7e83397, d651488) and on the subtraction basis (WO-81-600c547):

| row | S | P | D (node) | reasons |
|---|---|---|---|---|
| st_sw (rev f, tt27 a) | 1.980344 V (op/on) | 2.2240 V | 144.3 ns (nb2: Sb3 gb) | sus, cap, dur |
| st_sw_ron01m (0.1 mohm switch) | 1.980344 V | 2.2240 V | 144.3 ns | sus, cap, dur |
| st_sw_rt6 (reltol 1e-6) | 1.980344 V | 2.2241 V | 144.3 ns | sus, cap, dur |
| st_r001_rt6 / st_r01 / st_r1 (fixed feed 0.01/0.1/1 ohm) | 1.980344 / .980343 / .980338 V | 2.2241 / 2.2240 / 2.2237 V | 144.2 / 144.2 / 210.8 ns | sus, cap, dur |
| st_ff-40_b_sw | 1.980272 V | 2.2511 V | 144.4 ns | sus, cap, dur |
| st_kp2_sw | 1.980150 V | **2.1792 V** | 144.3 ns | sus, dur |
| st_kp2_ff-40_b_sw | 1.980131 V | **2.2062 V** | 144.4 ns | sus, cap, dur |
| st_tt27_a (WO-81, subtraction) | 1.980284 V | 2.2206 V | 143.8 ns | sus, cap, dur |
| st_ff-40_a/b (WO-81) | 1.980227 V | 2.2466 V | 144.0 ns | sus, cap, dur |
| st_tt27_a (WO-78, rev e, old basis) | 2.045957 V | 2.2796 V | - | sus, cap, dur |

## Item 2: stiff-supply robustness
S = 1.980344 V holds to the µV with a 10x stiffer switch (0.1 mohm), with reltol 1e-6, and with a fixed 0.01 ohm feed
(`st_r001_rt6`, which did not abort, unlike the WO-84 expectation). vddmax = 1.98000 V in all of them. A 2.00 V pin
(`st_brk_vdd200_sw`) gives S = 2.000343 V: **the excess is +0.344 mV above whatever the pin is**, i.e. a fixed offset
riding on vdd, not a bench drop. P moves by <= 0.1 mV and D by <= 0.1 ns across these settings (st_r1 is the only
outlier, D 210.8 ns, its 1 ohm feed lets vdd itself rise 60 µV).

## Item 3: path (NOT named; probe failed)
`st_sw_icur` ran to tend 2.7 µs, but its `write` aborted: "Error during 'write': no writable vector found" (deck.log
line 58), so no raw, no dpost table. The `@m.xc.x<dev>.msky130_fd_pr__<model>[id]` names written into `save all` /
`write` do not match what ngspice stores (all-or-nothing write). `st_kp2_sw_icur` (still running at hand-off) will fail
the same way. Fix for the pickup: a 10 ns smoke of the same deck with `display` after tran to read the real vector
names, then rerun one deck (~12 min at 1 slot).
What the existing data does say (inference, not proof):
- The op/on excess is a **fixed +0.344 mV above the pin** (1.98 V and 2.00 V pins give the same offset) and is
  insensitive to switch R, feed R and reltol, so it is not numerical noise on the bench.
- Doubling the op/on keeper (kp2) cuts it from 0.344 to 0.150 mV (x0.44): the excess scales like a DC current
  pushed into op/on times the pull-up resistance to vdd, i.e. a **steady injection of order tens of nA** (M5/M6 +
  keeper ~ kohms). Candidate sources: HV ap/an (kicked to 2.29-2.39 V) leaking through K1/K2 -> dp/dn -> M3/M4, or
  the 1.8 V devices' junction/GIDL currents. Physical in kind; which device is not shown.
- nb2/ob2 (D 144 ns on Sb3/Sq3 gb, Bn2n ds) sit above vdd by less than op/on (their S is below 1.980344 V; WO-81
  st_fast rows show ob2 at +10-11 µV). D counts any excess > 0 V, so D is long while the level is µV.

## Item 4: kp2 verdict
**Not under 2.2 V at all corners:** P 2.1792 V at tt/27 a (pass cap), **2.2062 V at ff/-40 b** (cap fails by 6 mV;
rev f there 2.2511 V). Costs vs rev f: T2 one_ss-40 tdec 1.354 -> 1.291 ns (no penalty); cyc_kp2_ss-40_162 max
1.343 ns, all cyc limbs ACCEPT (no rev f cyc row to compare); T5 diff kick ss-40 0.617 -> 1.142 mV, fs+125 2.524 ->
3.399 mV (limit 5 mV, margin 1.6 mV); CM kick 39.56 -> 38.92 / 47.41 -> 46.82 mV (no change). S 0.344 -> 0.150 mV
(still over), D unchanged. kp2 alone does not reach T8.

## Item 5: checker copies
**No base row passes** (st_sw: sus+cap+dur; st_kp2_sw: sus+dur), so no copy can be judged as rejecting for its own
reason. Partial: `st_chk_cap20_kp2_sw` adds `over:cap` to its base's {sus, dur}: the cap limb is shown live.
sus195 / dur01 copies add nothing (their limb already trips in every base). `st_brk_noclamp_sw` (S 2.3107 V sq3/sb3
ds) and `st_brk_vdd200_sw` (S 2.000343 V, D 1311 ns) REJECT with the same reason set as the base; they differ only by
magnitude. Collect text truncates reasons to 3 (`why[:3]`, c3_tb.py line 757): use c3_tb.json.

## Item 6: decision input (conditional: the path is not yet named)
S exceeds 1.98 V by 0.15-0.34 mV on a steady (keeper-dependent) injection. The sus limb (S <= 1.98 V) fails on any
nonzero DC injection into a node held to vdd, however small.
1. **Circuit fix, after the path is named** (e.g. clamp ap/an to vdd while the strobe is high, or cut the
   K1/K2 -> dp/dn leak). Cost: one probe deck + a rev g + full T2/T3/T5/T8 rerun (~1 day of pools). Risk: a new
   device on the HV nodes moves T5 kick / T2; may only shrink the excess, never to exactly 0.
2. **Stated sub-mV tolerance in the D83 sus rule** (e.g. S <= 1.98 V + 1 mV, judged on the pin). Cost: a rule
   decision by the user, no sim. Risk: masks a later regression below 1 mV; justified only if the path is shown to be
   a static leakage (10% over-voltage on 1.8 V oxide is already the rated maximum; 0.3 mV adds ~0.02%).
3. **Other: judge sus relative to the actual pin** (S - vdd(t) <= tolerance), which is what the vdd200 copy shows
   the excess tracks. Same rule-change cost as 2, cleaner on any bench.
Recommendation: name the path first (1 smoke + 1 deck); if it is static leakage, option 2 with a 1 mV tolerance and
a broken copy at +2 mV; if it is the HV ap/an kick, option 1. Separately, cap still fails at ff/-40 (2.206 V with
kp2), which needs its own fix (slower precharge edge or a stronger keeper still).

## Ready for review
- Collection of all five pools (tables above; summaries in results/wo78, wo81, wo84). rev f has no cyc row.
- Stiff-supply result invariant: S 1.980344 V, a fixed +0.344 mV offset above the pin.
- kp2: tt passes cap (2.179 V), ff/-40 b fails (2.206 V); T5 kick +0.9 mV worst; T2 unchanged or better.
- Checker copies: no passing base; only cap limb shown live (cap20 on kp2). why[:3] truncation in collect text.
- Open: device-current probe (vector names), path naming, then the item 6 decision.
