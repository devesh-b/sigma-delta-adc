# WO-92 (C3l): rev g chosen, pool B (full C3 set) in flight, pickup below

Status 2026-11-15 05:53 IST. Items 1-5 are done. Item 1 is partial because pool A is still running. Items 6-7 are
waiting on pool B. Design commit: 1323676. Frozen copy: `/home/mempool/regr/tt/WO-92-1323676`.

## Item 1: pool A (`/home/mempool/regr/tt/WO-88-2a923df/runA`), partial collect at 05:50
- Pool A is **not done**: 18 of 33 jobs had launched. Jobs 17-33 are the rev f `cyc_*_revf` rows; each can take up
  to 6 h at 1 slot. No POOL_DONE yet. Partial collect: `runA/collect_partial.log`.
- The 16 sweep jobs all finished. Only one failed: **`st_kp3_ff-40_b_sw`** (launched 03:38, next job 05:38). It ran
  into the 7200 s st timeout, so it has no post (`no_post`, n=0/223). It is a kp3 info row, not a candidate.
  Not rerun.

| candidate | P tt27 a | P ff-40 b | S ff-40 b | T5 kick (ss-40 / fs+125) | CM peak (ss-40 / fs+125) | T2band |
|---|---|---|---|---|---|---|
| kp2_rsoW05 | 2.1761 | **2.2140 REJECT (over:cap)** | 1.980131 | 1.142 / 3.399 mV | 38.93 / 46.84 mV | pass |
| **kp2_rsoL03** | 2.1651 | **2.1966** | 1.980131 | 1.143 / 3.398 mV | 38.92 / 46.83 mV | pass |
| kp2_rsoL05 | 2.1584 | 2.1984 | 1.980131 | 1.143 / 3.398 mV | 38.92 / 46.83 mV | pass |
| kp3 (info) | 2.1441 | timeout | - | 1.51 / 3.893 mV | 38.98 / 41.97 mV | pass |

## Item 2: leak device
**It cannot be named yet.** In `WO-88-bfc8611/runI/st_sw_icur/dpost.txt`, every "into-terminal mean currents" list
is empty, so dpost found none of the `[id]` vectors. The pins parse correctly (the X lines are d g s b), so the
lookup by exact display name must have missed in the raw. `st.raw` was deleted by post, so the names cannot be
checked now.
- Fix in 1323676: `supply_probe._iget` matches on the instance path plus `[i<term>]`, and dpost now prints every
  current vector it finds in the raw ("NONE" if there are none).
- The probe reruns on rev g as `runB/st_sw_icur` (info row).
- If its list is still empty, the `write` line does not carry the `@` vectors into the binary raw. Next step then:
  check the raw header with `head -c 40000 st.raw | strings | grep '\['` before post deletes it.

## Item 3: rev g = kp2_rsoL03 (KP 0.84/0.15, R0/R1 1.0/0.3)
- It meets every gate:
  - P at ff/−40 b is 2.1966 V ≤ 2.2 V.
  - T5 diff kick at fs+125 is 3.398 mV ≤ 5 mV.
  - T2band passes.
  - S is 1.980131 V ≤ 1.981 V.
- It has the larger P margin of the two that pass (rsoL05 is 2.1984 V) and the smaller L change.
- **The margin is thin: 3.4 mV (0.15 %).** This is a corner number on one seed and one phase, and pool B rechecks it
  at 5 corners. W05 fails, so lowering the R0/R1 Cgd does not do it; the slower edge (longer L) does.
- CM kick into OTA2: 38.92 mV peak at ss/−40 and 46.83 mV at fs+125. CM recovery: 0.92/1.06 and 1.14/1.31 mV.
  These are the same as the other candidates, because RSO does not move the CM kick.
- The diff kick's first element (3.398 mV) is also the same for every RSO value. Only the second kick sample
  changes: 0.68 mV for L03, 0.26 mV for W05, 1.40 mV for L05.
- M11 (R0 shares the clk gate with R1): RSO sizes R0 and R1 together, and dp/dn R2/R3 stay on RS 1.0/0.15. The change
  is symmetric, so the ambiguity does not apply.

## Item 4: default and the revf mutation
- `sizes_draft.py`: KP is now 0.84/0.15 and RSO is 1.0/0.3. `revf` was added to MUTS.
- `netlist.py`: mut `revf` sets KP back to 0.42/0.15 and RSO to RS.
- Checked in the generated decks: `st_tt27_a_sw` has XR0/XR1 at L=0.3 and XKP at W=0.84, and `st_revf_ff-40_b_sw`
  has L=0.15 and W=0.42.

## Item 5: pool B, 65 decks, launched 05:52:51 (1 slot at load ~6)
`/home/mempool/regr/tt/WO-92-1323676/runB` holds the full deck_list4 set:
- 19 cyc
- 21 one
- 12 mc, plus sens_tt and pdk_tt (the M2 gap)
- 12 st on the stiff pin, plus the st_sw_icur probe

The judged-from checkers (sus195, cap20, dur01, jn20) are rows, not decks. At 1 slot this is expected to take
**many hours, likely more than a day**: the mc decks time out at 4 h and the cyc decks at 6 h.

## Pickup (sandbox; env: `. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$F`, `F=/home/mempool/regr/tt/WO-92-1323676`)
1. Wait for `$F/runB/pool_logs/POOL_DONE` and `/home/mempool/regr/tt/WO-88-2a923df/runA/pool_logs/POOL_DONE`.
2. `cd $F && python3 design/c3_comp/c3_tb.py collect $F/runB > $F/runB/collect.log 2>&1`.
3. Pool A: `cd /home/mempool/regr/tt/WO-88-2a923df && PYTHONPATH=$PWD python3 design/c3_comp/c3_tb.py collect $PWD/runA > runA/collect.log 2>&1`.
   Read the `cyc_*_revf` rows into the rev f info column.
4. Read `$F/runB/st_sw_icur/dpost.txt` and name the leak device (see item 2).
5. Fill the table below. Every checker must REJECT **for its own reason** (the full reason lists are printed):
   - sus195: over:sus
   - sus1985: over:sus, with S ≈ 1.985 V
   - cap20: over:cap
   - dur01: over:dur
   - jn20: over:jn
   - noclamp and vdd200: their own reasons, not no_post or a sanity fail

   Recheck that rev g P at `st_ff-40_b_sw` ≤ 2.2 V, and that sens/pdk give a finite sigma_est and `plaus` passes.
6. Hand the "ready for review" list to sd-adc-design-reviewer.

## Verdict table (to fill)
| row | rev g result | expect | verdict |
|---|---|---|---|
| T8 st_* tt27 a/b, ff-40 a/b, ff125 b (sw) | | pass | |
| T8 chk sus195 / sus1985 / cap20 / dur01 / jn20 | | reject (own reason) | |
| T8 brk noclamp / vdd200 / in18 | | reject | |
| T8 info revf ff-40 b, edge01, st_sw_icur | | info | |
| T2 / T7 / T10 cyc (12 rows + 5 brk) | | pass / reject | |
| T5 one_* (9 PVT + 2 MHz + asym) + chk kick1 / rec02, brk starve | | pass / reject | |
| T3 MC tt (n=200) / ss40 / brk_x6, sens + plaus | | pass / reject | |
| rev f cyc rows (pool A) | | info | |

## Ready for review (sd-adc-design-reviewer, once filled)
- The rev g change (KP 2x, R0/R1 L 0.15 to 0.3): the 3.4 mV P margin, and any cost to T2, T5 and T3.
- D90 implementation (WO-88: limits, the sus1985 copy, the full reason lists).
- The leak-path name, or the reason it is still open.
- The full C3 verdict table, including the M2 gap (sens/pdk, plaus).
- The rev f cyc rows (pool A) as the baseline.
- That every checker copy rejects for its own reason against the passing rev g base.
