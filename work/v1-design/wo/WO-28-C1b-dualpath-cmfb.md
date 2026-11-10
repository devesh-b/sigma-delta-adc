# WO-28 (C1b part 2d): D61 dual-path CMFB, larger references, tb9 start-up fix

Coordinator-written, 2026-11-10. **Tier: design (Opus).** Builds on the uncommitted WO-27 working tree; read `work/v1-design/results/wo27/README.md` first. Sources:
- D57–D61;
- `REVIEW-WO26-2026-11-10.md`;
- `design/c1_ota1/*` (including the new `c1b_tb9.py`);
- SPEC rows 94, 95, 98, CL-2, CL-7.

**Sandbox:**
- Frozen copy `regr/tt/WO-28-<sha-or-dirty-tag>` with `golden/`. If commits are blocked, tag it with `git stash create`-free means, e.g. `WO-28-<date>-<n>`, and record `git diff --stat` in the README.
- At most 2 of your own processes. The WO-26 gate B (`/home/mempool/regr/tt/WO-26-b177d23`) keeps running; never touch it.
- Absolute paths, markers, no pgrep/pkill, no wait loops, delete csv files.

## Items
1. **Dual-path CMFB (D61):**
   - Keep the passive SC path (Cc 0.1 pF / Cr 25 fF onto m_plc) as the fast path. Remove or repurpose the WO-27 CT amp.
   - Add a slow integrating CM path: the SC-sensed CM against V_OCM drives a small gm-C integrator, whose output trims the m_plc control (for example a separate m_plc subsection, or the V_BL0 node).
   - Targets at 9 PVT × 2 modes:
     - systematic + 3σ V_OCM error ≤ 10 mV, with the integrator pair offset as the main σ;
     - f_cm ≥ 9.4 MHz in boost with CM PM ≥ 45°;
     - the slow-path zero/pole kept a decade or more below f_cm, with no CM peaking above 1 dB;
     - total added current ≤ 3 µA base / 3 µA boost (the slow path does not need to scale with mode).
   - Fix the nominal CM return-ratio measurement first (WO-27 found no clean unity crossing), and validate it on a hand-solvable broken copy.
   - Broken copies: integrator gain off ⇒ V_OCM row REJECTs at ff/125; Cc ÷ 4 ⇒ f_cm REJECTs.
2. **Larger references (D61):**
   - Grow the m_tr, m_nr, m_plr and m_bl0 reference area (and the matched mirror unit, if needed) so that SR − 3σ ≥ 12.5 / 25 V/µs and ceiling + 3σ ≤ the limit at every corner, with A_VT 12 mV·µm. The D60 +1.9 % recentre stays.
   - Report the area added and the σ per mirror.
   - Keep common-centroid/dummies layout intent.
3. **tb9 start-up fix:**
   - Make the start-up state consistent: clamp the outputs and the sense node to V_OCM together during the start-up window, or otherwise fix the wrong stored charge on the sense node.
   - Start the CM-step and reset events only after convergence.
   - Exit:
     - from both rails, V_OCM ± 10 mV within the CL-7 4 µs;
     - CM step and reset settle ≤ 10 mV by 0.2·t_half at 4 MHz boost, at tt and the boost hot corners.
   - Broken copies: Cc ÷ 4 and integrator-off ⇒ REJECT.
4. **WO-27 leftovers:** the replica-drain row (V_rnd vs V_fa) and margin rows for m_rn, m_rnc, m_rcb; the cm_unity copy at ff/125.
5. **op/AC** at 9 PVT × 2 × 3 C_L with all rows.
   - Report I_vdd, f_cm, CM PM, V_OCM (systematic and 3σ) and SR (nominal and −3σ) per corner, plus boost fp2/GBW and PM.
   - Update `results/wo27/gb.sh` → `results/wo28/gb.sh`. Do not launch it.

## Git
- Atomic commits with explicit paths, no trailers, no push. If signing fails (1Password locked), do NOT bypass it. Leave the work in the working tree and list exactly which paths belong to which planned commit.
- Do not touch the coordinator's staged files: DECISIONS.md, RESUME.md, wo/INDEX.md, wo/WO-27, wo/WO-28.

## Budget
At most 60 tool calls. Report in ≤ 60 lines. Stop at the first failed exit you cannot fix within D61, and report.
