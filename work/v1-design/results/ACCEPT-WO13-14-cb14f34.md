# Acceptance: WO-13 (model fixes) and WO-14 (S5e follow-ups), frozen copies

Run by the coordinator by direct ssh + nohup, 2026-11-09, on frozen copies of the tree:
- `acc14-cb14f34`: the main runner, which waits for load before each step.
- `acc14b-925b983`: the gm/Id decks, after the CSV naming fix.
- `acc14c-05cbab2`: `--gmid` and `--fast3`, after the column fix.

The pytest, s4 and tier-1 rows were not rerun on 925b983 / 05cbab2 because those two commits touch only the gm/Id decks and the gm/Id reader.

| # | Row | Copy | Exit | Verdict |
|---|---|---|---|---|
| 1 | pytest model + design | cb14f34 | 0 | **103 passed** (includes WO-14 order-1 residue frame, bstgm bit-identity, β2 ≈ 0.497) |
| 2 | s4_corners | cb14f34 | 0 | **ACCEPT**, all 4 gates. Sys-off 61.5 dB; ε_eff code = hand, 8.407e-4 |
| 3 | s4_corners --nonvac | cb14f34 | 1 | **REJECT, 8/8** broken copies, each named |
| 4 | s3_budget | cb14f34 | 0 | **ACCEPT** (joint: n15 0.93 µV, n240 3.94 µV, INL 2.03 ppm) |
| 5 | tier1 --xcheck | cb14f34 | 0 | **ACCEPT**: deck vs model rel_sym 0.0–0.7 % in all 6 gated rows (gate 5 %) |
| 6 | tier1 --nonvac5 | cb14f34 | 1 | **REJECT as required**: the no-Ck model fails all 6 rows; the control passes |
| 7 | gm/Id decks (9) | 925b983 | 0 | 36 CSVs. The first run (cb14f34) wrote one file per deck: ngspice `$t.csv` needed `{$t}`. Fixed in 925b983 |
| 8 | tier1 --gmid | 05cbab2 | 0 | **ACCEPT**. Peak gm/Id is below 1/UT in every row. The first run (925b983) failed: the reader assumed paired x/y columns, but `wr_singlescale` writes (V, Id1, Id2). Fixed in 05cbab2 |
| 9 | tier1 --fast3 | 05cbab2 | running | see `s5f_tier1.md` when done |
| 10 | S3 A/B (iadc a3ea4eb^ vs a3ea4eb, current script) | cb14f34 | 0/0 | see `s3_ab.md` |

Process note: in `acc14b` the coordinator ran the 9 short gm/Id decks in parallel (about 1 min each) at load ≈ 2, which was over the 5-process cap. No harm was seen; later runs are capped again.
