# WO-78 (C3g): T8 per D83 — checker done, full rerun RUNNING, rows still REJECT under D83 (questions open)

Code: commits 1f18fa6 + b1a7e63 (`design/c3_comp/c3_tb.py`). Frozen copy: `/home/mempool/regr/tt/WO-78-1f18fa6`
(dir named after the first commit; `c3_tb.py` updated to b1a7e63 before launch, see `SOURCE_SHA`). Design = rev e,
unchanged (no rev f run).

## Item 1: D83 in the T8 checker (CL-35 wording)
- Each st deck writes the node waveforms (`st.raw`, binary); the job then runs `c3_tb.py post DIR`, which appends RES
  lines to `deck.log` and deletes the raw file.
- Per 1.8 V oxide-class pair (gs, dg, gb, ds): **P** peak |V| (native points, cross-checked against ngspice's own
  vecmax, mismatch > 0.1 mV ⇒ REJECT), **S** sustained level = max over t of min |V| over [t, t+1 ns] (5 ps grid),
  **D** longest continuous time above 1.98 V (interpolated edges), plus times tP / tD and `post_vddmax`.
- Limbs: `sus` S ≤ 1.98 V; `cap` P ≤ 2.2 V; `dur` D < 1 ns. Junctions (D80, 4.95 V) and HV (5.5 V) single peak as
  before. Missing post data ⇒ REJECT (`no_post`, seen live in the first smoke attempt).
- Per-device table (S/P/D, worst pair) goes to `run/t8_devices.txt` and `c3_tb.json` (`dev`).

## Item 2: copies that must REJECT
- `st_brk_noclamp` (rev d latch, design broken copy, was info): sq/sb −0.345 V ⇒ Vds 2.32 V for 105 ns (sus+dur+cap).
- Checker copies on the st_tt27_a data (judge-only, `judge_from`, no extra sim): `st_chk_sus195` (sustained limit
  1.95 V), `st_chk_cap20` (cap 2.0 V), `st_chk_dur01` (duration cap 0.1 ns). `st_chk_jn20` and `st_brk_in18` kept.

## Item 3: the 4 off-expectation rows (st_tt27_a/b, st_ff-40_a/b, all `over:18` in WO-68)
Under the single-peak rule they fail by construction (checker rule, fixed by D83). **Under D83 they still REJECT**
(smoke: st_tt27_b, first 500 ns, `smoke/`), for three separate reasons:
1. `sus` by 3–8 µV: S = 1.980003–1.980008 V on every on-state rail-to-rail pair. Cause: the bench supply node rises
   to 1.98198 V (diode current into `VDDS` through `RVDD` 10 Ω). **Bench/rule question, not design** (Q1).
2. `cap`: on/op (M3/M4 gb, R1 dg, Bn1 inverter pairs) peak 2.264 V at 494.12 ns, above 2.2 V for 92 ps (above 2.0 V
   for ≈ 130 ps), at the strobe falling edge (precharge start) with x2p = x2n ≈ 2.06 V (CM ramp after power-up,
   order b). WO-68 data: 2.26–2.32 V on st_m3/m4_gb at all four rows. **Design issue** (precharge-edge overshoot, the
   HV ap/an + dn/dp nodes reach 2.29–2.39 V and drag op/on), possibly helped by the bench's 0.1 ns ideal strobe edge (Q2).
3. Expected from WO-68 probe2 (to be confirmed by the pool): R1/M6/R3 Vds 2.025–2.033 V for 61–75 ns, i.e. on/dn
   at −47…−56 mV after the x2 = −0.5 V step pulls tl to −0.52 V. Sustained 45–55 mV over ⇒ **design/stimulus issue** (Q3).

**Full st_tt27_a (pool job 1, partial collect in `$F/partial`):** S = 2.0460 V on M3/M4 gb, Bo1/Bn1 (nodes op/on), above 1.98 V for 126 ns; P 2.280 V at 2494 ns; 12 pairs > 2.2 V. op/on sit ≈ 66 mV above VDPWR for a whole strobe phase: after the strobe edge no device pulls them down when the pair is off (x2 at −0.5 V). **This is a real sustained violation (design issue), the main one; the µV supply rise (1.98194 V) is secondary.** M5/M6 Vds 2.025 V for 61 ns confirmed (reason 3). Checker copies currently all show `over:sus, over:cap` (trivially REJECT, see caveat).

## Item 4: rev f — not run (budget). Smallest single-change candidates for the coordinator to choose:
- for (2): slower precharge edge (R0–R3 / P1–P2 smaller W) or a realistic strobe edge from C4 (bench change, Q2);
- for (3): clamp of tl to vss (NMOS diode) so the −0.5 V x2 step cannot pull the 1.8 V stack below ground.

## Pickup (pool started 14:54, 13 jobs, load ≈ 7 ⇒ 1–2 slots, ≈ 15–55 min per deck ⇒ hours)
    ssh sandbox; F=/home/mempool/regr/tt/WO-78-1f18fa6
    ls $F/run/pool_logs/POOL_DONE && cat $F/run/collect.log $F/run/t8_devices.txt   # COLLECT_EXIT line at the end
Expect: st_brk_noclamp, st_brk_in18, st_chk_* REJECT, each `why` containing its named limb (chk_sus195 `over:sus`,
chk_cap20 `over:cap`, chk_dur01 `over:dur`); gate rows REJECT as above until Q1–Q3 are decided. **Caveat (green is
not proof):** while st_tt27_a itself REJECTs, the chk copies' REJECT is trivially met; they only prove a limb live
once the base row passes, so recheck them then (look for the named limb being the only new reason). Copy
`collect.log` here as `summary.txt` (no raw or csv).

## Questions (not decided here; no limit was changed)
- Q1: is the 1.98 V sustained limit judged including the bench supply rise (vdd 1.98198 V, 10 Ω numerical rule)?
- Q2: is the 0.1 ns ideal strobe edge the stress basis, or C4's real phiC edge?
- Q3: is the −0.5 V x2 step a required stress state for the 1.8 V stack (it causes the sustained undershoot)?
