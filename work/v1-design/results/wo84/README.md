# WO-84 (C3i): rev f residuals, supply basis, WO-78/81 pools

Code: d651488 (`c3_tb.py` st_deck `rv`/`sub`, `netlist.py` + `sizes_draft.py` mut `kp2`, `supply_probe.py`),
7e83397 (`supply_probe.py` set 2). Frozen copies: `/home/mempool/regr/tt/WO-84-d651488` (set 1),
`/home/mempool/regr/tt/WO-84-7e83397` (set 2). Both have design/ without c1_ota1, c4_sw, c6_bias; golden, model,
scripts; `.spiceinit` num_threads=1. Load was 10-13 on 6 cores the whole session (3 earlier pools still running),
so every pool runs 1 slot, about 6-10 min per full st deck. Budget ran out before most rows finished: pickup below.

## Item 1: pools (WO-78, WO-81)
Not finished at the end of this session (WO-78: 12 of 13 jobs done, 13th running; WO-81-fe9e787: 6 of 49;
WO-81-600c547: 4 of 19). `results/wo78/summary.txt` and the WO-81 tables are NOT written. Pickup below.

## Item 2: supply basis
- **Ideal / near-ideal pin aborts at the ramp corner, independent of R.** `st_r001_split` (0.01 ohm feed) and
  `st_p10_split` (10 ohm feed + 0 V ammeters on every vdd terminal) both abort at t = 400 ns (start of the vdd PWL
  ramp, vdd still 0 V) with "timestep too small ... v.xc.viob2pb#branch": any ideal source tied straight onto the vdd
  net aborts there (same mechanism as WO-79). The ammeter split was therefore not usable: the device/path that
  carries the reverse current is **not identified** yet. Next step: device terminal currents via `save
  @m.xc.x<dev>.<inst>[is]/[ib]` instead of ammeters (instance name inside the PDK subckt still to be looked up).
- **Stiff pin that runs:** `sup="sw"` in `supply_probe.py`: 10 ohm feed for the power-up ramp only, then a 1 mohm
  switch in parallel closes 100 ns after the ramp ends (order a: 600 ns). `st_sw` (rev f, tt/27, order a) ran to
  tend 2.7 us, **post_vddmax = 1.98000 V** (vdd never above its source; the 1.98194 V rise is gone), judged on raw
  |V| (no subtraction):

  | row | S (sustained) | P (peak) | D (longest > 1.98) | verdict |
  |---|---|---|---|---|
  | st_sw (rev f, stiff) | **1.980344 V** on op/on (M4 gb, Bo1n gs/gb) | **2.2240 V** (same pairs) | **144.3 ns** Sb3 gb, Bn2n ds, Sq3 gb | REJECT sus+cap+dur |
  | WO-81 st_tt27_a (subtracted) | 1.980284 V | 2.2206 V | 143.8 ns Sb3 gb | REJECT |

  The stiff supply and the subtraction **agree in direction and differ by 0.06 mV / 3.4 mV**; the stiff result wins:
  op/on sit 0.34 mV above a 1.98 V pin, sustained. So the residual is **not** a bench drop artefact: something
  injects charge into op/on (and nb2/ob2) above VDPWR. Candidate (not proven): the HV nodes ap/an, kicked to
  2.29-2.39 V by x2 (WO-78), leaking through K1/K2 -> dp/dn -> M3/M4 into op/on. If so it is physical; on the chip the
  shared VDPWR would absorb the reverse current, but the 1.8 V gates on op/on still see > 1.98 V.
- Tighter-setting rows (`st_sw_ron01m` 0.1 mohm switch, `st_sw_rt6` reltol 1e-6) and `st_ideal` (smooth
  raised-cosine ramp, no feed R) are queued in set 2, not run yet. The st_sw numbers are not yet shown invariant.
- Set 1 st rows with rv <= 1 ohm (`st_r01`, `st_r001_rt6`, `st_r1`, `*_r001`) are expected to abort at 400 ns.

## Item 3: Sb3 gb 143.8 ns
Same on the stiff basis (144.3 ns, also Bn2n ds and Sq3 gb), so it is not the drop subtraction. Nodes: nb2 (Sb3
gate, Bn2n drain) and ob2 (Sq3 gate) high, sitting above 1.98 V by less than the op/on excess (their S stays below
1.980344 V; exact µV level not printed), for 144 ns: a sustained sub-mV excess on on-state output nodes, i.e. the
same class of residual as op/on (charge pushed above VDPWR with no path back). Cause not named yet (budget).

## Item 4: precharge-edge peak 2.2206 V, one change
Chosen: stronger keeper `kp2` (KPo/KPn 0.84/0.15, 2x W), not a slower precharge edge: the slower edge moves the
precharge (reset) time and with it T7 memory / T2 at ss; the keeper only acts while op/on are high, and in WO-81 the
keeper alone took the real-edge peak from 2.2797 V (nokeep) to 2.2206 V. On the stiff basis the peak is 2.2240 V.
Rows: `st_kp2_sw`, `st_kp2_ff-40_b_sw` (set 2), `one_kp2_ss-40_162` (T2band tdec, T5 kick, CM kick),
`one_kp2_fs+125_198` (worst T5 kick), `cyc_kp2_ss-40_162` (T2 tdec, T7) in set 1. **Not run yet.** Compare against
rev f rows of WO-81-fe9e787 (`one_ss-40_162`, `one_fs+125_198`, `cyc_ss-40_162`) and rev e (WO-68): T2 one_ss40
2.035 ns, cyc_ss-40_162 2.293 ns; T5 1.82 mV, CM kick 40.1-48.1 mV. kp2 does not address item 2/3 (sustained excess).

## Item 5: checker copies
`st_chk_{sus195,cap20,dur01}_{sw,kp2_sw}` (set 2): judge-only on `st_sw` / `st_kp2_sw`. `st_sw` REJECTs, so its
three copies are trivially REJECT (not live). Live only if `st_kp2_sw` ACCEPTs and the named limb is the only new
reason (it cannot: kp2 leaves the sustained excess). `st_brk_noclamp_sw`, `st_brk_vdd200_sw` queued.

## Pickup
    ssh sandbox; . /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A
    for S in d651488 7e83397; do F=/home/mempool/regr/tt/WO-84-$S; ls $F/run/pool_logs/POOL_DONE && \
      PYTHONPATH=$F python $F/design/c3_comp/c3_tb.py collect $F/run > $F/run/collect.log 2>&1; cat $F/run/collect.log; done
    W=/home/mempool/regr/tt/WO-78-1f18fa6; ls $W/run/pool_logs/POOL_DONE && PYTHONPATH=$W python $W/design/c3_comp/c3_tb.py collect $W/run > $W/run/collect.log 2>&1; cat $W/run/collect.log   # -> results/wo78/summary.txt
    F=/home/mempool/regr/tt/WO-81-fe9e787  # one/mc/cyc rows;  F2=/home/mempool/regr/tt/WO-81-600c547  # st rows (see results/wo81/README.md)
Collect also lists rows without a log (and aborted set-1 st rows) as off-expectation: ignore those.

## Ready for review
- Bench: `sup="sw"` stiff pin (10 ohm ramp, 1 mohm after) as the D87(a) basis, replacing the drop subtraction
  (coordinator decision; then make it the c3_tb default and rerun the gate rows).
- Finding: rev f REJECTs on a stiff 1.98 V pin (S 1.980344 V op/on, D 144 ns nb2/ob2, P 2.224 V). The residual is
  real, not the 10 ohm feed.
- Open: path of the charge into op/on, nb2/ob2 (device currents via `save @m...`), kp2 rows, tighter-setting rows,
  WO-78/81 collection.
