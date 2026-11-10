# WO-31 (C1b part 2g): D64 Cr ×2, op/AC + tb9 reconfirm, gate B

Coordinator-written, 2026-11-11. **Tier: design (Opus), narrow scope.** Sources:
- D63, D64;
- `work/v1-design/results/wo30/README.md`;
- `design/c1_ota1/{sizes_draft.py,netlist.py,c1b_opac.py,c1b_tb9.py}`;
- `/home/mempool/regr/tt/WO-30-6ee1e9d/gb.sh`.

**Sandbox:** same rules as WO-30. New frozen copy with golden/, at most 3 own processes, absolute paths, markers, no pgrep/pkill, no wait loops, delete csv files, **no local python**.

## Items
1. Make Cr 0.05 pF the default (sizes_draft + DESIGN.md). Keep a `cr_x05` token (the old 0.025 pF) as the start-up broken copy: it must REJECT the sulo row.
2. Rerun the op/AC at 9 PVT × 2 × 3 C_L.
   - Exit: every WO-29 row passes; CM PM ≥ 45°; peaking ≤ 1 dB; V_OCM sys + 3σ ≤ 10 mV.
   - Report the deltas from WO-29.
3. Rerun tb9 (tt, ss125, fs125, sf125, plus --mut).
   - Exit: every D63 row passes, including suhi/sulo/suvb (2 T) ≤ 10 mV.
   - The cr_x05 copy REJECTs.
4. If items 2–3 pass, launch gate B on this netlist: fs/125, ss/−40, ss/125, tt/27, plus sr95 at fs/125 and sf/−40. Detached, with markers. Report paths and do not wait.

## Git
Explicit-path commits only, no trailers, no push. If signing fails, list the paths.

## Budget
At most 30 tool calls. Report in ≤ 40 lines. If an exit fails, stop and report.
