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

## Results (coordinator, after hand-off)
- op/AC 9 PVT (opac_058/123/467): **VERDICT ACCEPT** in every group. Nominal rows pass. The maxima of CM peaking 1.87 dB and V_OCM 3σ 64 mV come from the broken copies (mcc4, mvo). Min CM PM 65.9°.
- tb9 (tt, ss125, fs125, sf125 + mut): **VERDICT ACCEPT**.
  - Start-up err over the last period (limit 10 mV): suhi 7.5–9.3, sulo 6.9–9.6, suvb 7.5–9.3. 8 T sulo (info) 7.3–9.1.
  - Broken copy mcr05 (old Cr 0.025 pF): sulo 34.0 mV → REJECTED.
- **Gate B launched** in WO-31-1cf257d: `gb.sh` (fs/125, ss/−40, ss/125, tt/27 + sr95 at fs/125 and sf/−40). Markers `out/gb_status`, `out/gb/*/combine.out`, `GB_DONE`.

## Gate B (WO-31 netlist: D59–D64; boost, N 1024, m 21, O1, 6 parts, combine with the broken-copy rule)
| config | INL ep [ppm] | verdict | endpoint spread [ppm] |
|---|---|---|---|
| fs/125 (c3) | **2.170** | ACCEPT (gate 5, share 3.33) | 0.0026 |
| ss/−40 (c1) | 1.291 | ACCEPT | 0.021 (mixed 8-thread and 1-thread parts) |
| ss/125 (c2) | 1.337 | ACCEPT | 0.0011 |
| tt/27 (c0) | 0.452 | ACCEPT | 0.0008 |
| sr95 fs/125 | 51 956 | broken copy REJECTED | 27 (info) |
| sr95 sf/−40 | 50 231 | broken copy REJECTED | 2.4 (info) |

- All four corners pass. fs/125 improved from 3.31 ppm (WO-26) to 2.17 ppm. That is below gate/2 (2.5), so no O2 run is needed.
- Changing the thread count from 8 to 1 mid-run left the c1 endpoints within 0.021 ppm, so it is harmless.
- Gate B started 00:54 and finished at about 04:20: waves of 3 at first, then 5 single-thread jobs from 02:02.
