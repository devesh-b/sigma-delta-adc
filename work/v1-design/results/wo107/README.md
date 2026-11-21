# WO-107: C4 TG + LS, C3 rev g comparator, c9 DRC root cause, D98 frame (pd-expert, 2026-11-21/22)

Commits 49d46b9 -> dcb620b -> **ac7498c (final run)**. Frozen run `/home/mempool/regr/tt/WO-107-ac7498c/out/summary.txt`
(EXIT=0; `ver_*.log`, `*.lyrdb`, `lvs_*.out`). Probe: `WO-107-probe/` (gencell geometry, `probe.log`). Harness
`design/layout/scripts/run.sh <dir> [all|new]`. New: `cells/route.tcl` (row placer + channel router: via1 -> met2 stub ->
one met3 track per net per row -> met4 spine per multi-row net or port), `cells/c3_comp.tcl`, `cells/c4_setup.tcl`.
D100 (2026-11-22): C3 and C4 are on hold (schematics not verified). The cells stay in the tree as they are, and are not extended.

| Cell | bbox um (um2) | Magic hier / flat | KLayout | LVS | Broken copies |
|---|---|---|---|---|---|
| c4_sw (Msg 5/0.5, sin TG 12/36, lsbuflv2hv_1) | 13.46 x 63.92 (860) | 0 / 0 | 0 | PASS | drcbad 1/1/1; nostrap FAIL (pin matching); ref Msg W 6 FAIL (property) |
| c3_comp rev g (44 dev + 2 dummies) | 52.11 x 110.22 (5,743) | 72 / 0 | 0 | PASS | drcbad 73/1/1; finger swap FAIL (property: M1 3 / M2 5); ref KP W 0.42 FAIL (property) |
| c9_place (WO-106 175 x 150 GDS) | 175 x 150 | 512 / 0 | 0 | - | KL control on the source GDS: 0 items (now produces a report) |
| frame, mim_s1/s2, c6_res | unchanged | 0 / 0 | 0 | PASS | all broken copies still fail |

- C4: the LS is lsbuflv2hv_1 (the netlist.py `ls_up` default, D78), not clkiso. Its GDS has two VPWR rails and two VGND
  rails that are not connected inside the cell. VPWR, VPB and VPWR_uq0 are joined by a met1 block on the east side, and the
  two VGND rails by a strap on the west side. The library spice has no _uq0 pins, so `c4_setup.tcl` flattens the LS on
  both sides and netgen compares it transistor by transistor. Not in the cell: the WO-103 delay caps and the rest of `c4_gen`.
- C3: there are 8 x 5/0.5 pair fingers in the order D ABBA ABBA D, and the gate escapes are mirrored about the centre. The
  K/T row is ABBA ABBA with T x4 in the centre. Latch rows D/E are mirror-symmetric (o side on the left, n side on the right).
  Each finger is its own gencell with its own ring, so the matching is environment-symmetric but the diffusion is not shared.
  The dummies are separate devices with all terminals on vss; they were added to the reference as `XDUM m=2`.
  **Area 5,743 against the 4,142 slot**. The cause is one gencell, ring and track set per finger. Compaction needs nf>1
  shared-diffusion rows.
- Magic hier vs flat: `drc listall count total` also counts subcells checked on their own. On c9_place, that is 57 hd
  std cells (DRCCELL lines). On c3, it is the LV gencell gate-contact met1 (0.067 um2 < met1.6), which the parent escape
  covers. The flat check (verify.tcl `MAGICDRCFLAT`, the same geometry the precheck sees) is 0 in both. That explains
  "512 plus No errors found" (why = top cell only).
- KLayout control: the deck resolves a relative `report=` against the input GDS directory. WO-100 therefore wrote a stray
  `c9_orig.lyrdb` into `WO-97-6b474df/.../final/gds/`, which was left there. The report path is now absolute.
- Frame (D98, C9 175): C9 east edge 179, guard ring at 189.5, analog column from 194. OTA1 is 205.5-303 x 3-112 = 10,628;
  OTA2 7,412; C3 4,142; C6 keeps 5,930 (bottom row east end 203.5); the total is 60,025 = 83.3 % (need 72.7-88.0 %).
- **TT precheck: NOT run (unknown).** `precheck_frame.sh` reached precheck.py under the pinned tools (magic 8.3.568,
  klayout 0.30.8), but it stopped with `PrecheckFailure: info.yaml not found`, and nix also printed "nixpkgs not found in
  search path". It needs a project dir (info.yaml, gds/, lef/) built the way `scripts/s0_precheck.sh build()` does.
- Grep artefacts in summary.txt: `KLCAT ... 256 <category>` (the category definitions, not items) and `MISSING` lines. The
  verdicts use `items=`.

## Open
1. Precheck project dir for the frame (info.yaml + LEF), then precheck with broken copies (as s0_precheck).
2. OTA1 (D100 layout-ready) is not started. It has 71 instances and about 280 fingers (2 x 32 pfet 2.5/4, 2 x 32 + 2 x 4 nfet
   2.25/8, pair 2 x 12 x 10/0.5, ...) plus Cc/Cr/Cint MIM (Cint 2 pF, about 1,000 um2). The per-finger route.tcl is not
   area-feasible in 10,628 um2, so it needs multi-finger interdigitated rows (nf>1, shared diffusion, common-centroid
   gate/drain wiring). That is new router work.
