# WO-43 (C1): D71 sink-noise reduction + tb7 fixes

Coordinator-written, 2026-11-12. **Tier: design (Opus).** Sources:
- D71, D57–D70;
- `work/v1-design/results/wo41/` (summary, contributors);
- `design/c1_ota1/{sizes_draft.py,netlist.py,c1b_tb7.py,c1b_opac.py,c1b_tb9.py,c1b_gateb.py,DESIGN.md}`.

## Items
1. **Sink redesign (m_n):**
   - Option A: longer L at the same current and W/L class. Option B: source degeneration.
   - Sweep 2–3 candidates on tb7 at the worst corners (fs/125 b/f, ss/125, tt).
   - Pick the cheapest that gives thermal ≤ 200 µV (≥ 20 % margin) at all 9 PVT × 2.
   - Check the side effects: base/boost span, A0, the fold-node pole and fp2/GBW, mirror ratios, and SR/ceiling 3σ rows.
   - Keep the replica / K_N tracking consistent (m_rn derives from m_n).
2. **tb7 fixes (D71):**
   - broken copy msink (sink noise ×2, e.g. W×4) must REJECT on thermal;
   - hand γ for 5 V devices from the PDK; hand row ±30 %;
   - nodesets from the open-loop op so the int copy has op_ok;
   - direct tier-0 path as the gate, conventional as info.
3. **Reruns, all through `scripts/lpool.sh`:**
   - tb7 at 9 PVT × 2;
   - op/AC at 9 PVT;
   - tb9 at 4 corners + mut;
   - gate B at fs/125 + ss/−40 (nominal).
   Exit: every row ACCEPTs and every broken copy REJECTs.
4. **If no candidate meets the target without breaking another row,** stop and report the options.

## Rules
- Sandbox only, frozen copy with golden/ and a single-thread `.spiceinit`.
- No local python. Explicit-path commits, no trailers, no push. Markers via POOL_DONE; no wait loops.

## Budget
At most 55 tool calls. Report in ≤ 40 lines.
