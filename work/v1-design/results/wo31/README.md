# WO-31 results (C1b part 2g: D64 Cr x 2, op/AC + tb9 reconfirm, gate B), 2026-11-11

Frozen copy: `/home/mempool/regr/tt/WO-31-1cf257d` (design/, golden/ from WO-30, run.sh, gb.sh).
Commits: 739e3da (Cr 0.05 pF default, cr_x05 token, tb9 2 T start-up gates, mcr05 broken copy, DESIGN.md), 1cf257d (run.sh, gb.sh).

## Item 1: done
- `sizes_draft.C_CMFB_REFRESH` 0.025 -> 0.05 pF (D64). `netlist.py` token `cr_x05` = Cr / 2 (the pre-D64 0.025 pF); `cr_x2` kept (info).
- tb9 NOM: ev, ev0, suhi / sulo / suvb with the 2 T clamp (gates, default Cr); sulo8 (8 T) info. TB9_SET=cr2 removed
  (it would now mean Cr x 4). MUT adds mcr05 = sulo with cr_x05, EXPECT "start-up" (WO-30 sulo2t at 0.025 pF: 14-34 mV).
- c1b_opac hold-phase load picks up the +25 fF Cr through S.C_CMFB_REFRESH (no code change).

## Items 2-3: RUNNING (launched 2026-11-11 00:23 IST, 3 chains)
- chain 1: op/AC 1,2,3 then tb9 0,2; chain 2: op/AC 4,6,7 then tb9 3,4; chain 3: op/AC 0,5,8 then tb9 0 --mut.
- Markers: `out/status_{1,2,3}` (EXIT= per step), `out/DONE_{1,2,3}`. Summary: `python design/c1_ota1/c1b_opac.py --summary out/opac`
  (compare with `/home/mempool/regr/tt/WO-29-9e14bed/out/opac` for the deltas); tb9 VERDICT lines in `out/tb9/*.out`.

## Item 4: gate B NOT launched (items 2-3 pending)
Launch from the frozen copy after items 2-3 pass: `cd /home/mempool/regr/tt/WO-31-1cf257d && setsid nohup bash gb.sh >/dev/null 2>&1 &`.
Markers: out/gb_status, out/gb/*/combine.out (EXIT=), GB_DONE.
