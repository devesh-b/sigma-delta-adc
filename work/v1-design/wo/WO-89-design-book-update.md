# WO-89: DESIGN_BOOK.md update to 2026-11-15, plus a proposal-ready summary

Coordinator-written, 2026-11-15. **Tier: design/writing (Opus).** Fresh agent. The user will use the book to write a design proposal (Chipalooza), so accuracy and traceability matter more than polish.

## Inputs (read, do not run anything)
- `DESIGN_BOOK.md` (adad138, current to 2026-11-13).
- `work/v1-design/DECISIONS.md` D80–D90.
- `SPEC.md` change log CL-33 to CL-39.
- `work/v1-design/RESUME.md` (entries from 2026-11-14 on), `wo/INDEX.md`, `STATE-2026-11-14.md`.
- Results READMEs: `results/wo63, wo68, wo70–wo88/` (all that exist).
- `C9_VERIF_PLAN.md` §14–15 and `design/c9_digital/flow/HARDENING.md`.

## Items
1. **Bring every stale section up to date.** Keep the existing structure and style.
   - III.1 C1: precision gate B (WO-63), the ss/−40 O1 fail, the bias-sweep finding (it moves rather than fixes), and the O2 parts (p0 0.142, p2 0.160 ppm). The **final verdict is pending** the O2 combine. Also the tb7 bench fixes (WO-77).
   - III.3 C3: rev e (latch clamp), rev f (op/on keeper), D83/D87/D90, the stiff switched supply basis, the +0.344 mV result, the precharge-edge cap and its mechanism, and the rev g candidates (pending).
   - III.4 C4: the WO-79/85 bench root causes, D82 rating, and the open 20 pA ff/100 row.
   - III.5 C6: R1 144.8 numbers, bias_ok pulse findings, D89, and the WO-87 bench changes (pending rerun).
   - III.6 C9: D84/D86 PnR closure, D85 counter, D88, WO-75/83 verification results, formal width limits, and the pending final PnR.
   - IV.7: the lpool global cap and the overload lessons.
   - Part V: status, pending values, open decisions and risks, as of 2026-11-15.
   - Appendix B (D80–D90) and Appendix C (CL-33 to CL-39).
2. **Mark every number that is not final** as pending, with the WO that will settle it. Never fill in a pending value. Every number must cite its source (WO / results file / D / CL).
3. **New section: "Proposal summary".** Put it near the front, after "How to read this book". It is factual and calm, with no marketing language:
   - what the design is;
   - target specs vs MCP3421 vs prior TT ΣΔ designs (NOTES.md, ACHIEVABILITY.md);
   - what is new on TT: order 2, incremental, on-chip decimator, chopping;
   - the verification approach;
   - status per block;
   - top risks and open items;
   - area/power budget;
   - what silicon would measure.

   Use a table where it helps. Every claim must trace to a section of the book.
4. Update "Gaps in this book's sourcing" (Appendix E).
5. Write in normal prose (not caveman). Markdown only. Do not edit any other file.
6. Commit `DESIGN_BOOK.md` only, with explicit path, no trailers, no push. Report in ≤ 20 lines: sections changed, word count, and every pending item.

## Rules
- No sandbox runs are needed. No local python.
- If two sources conflict, use the newer decision and note the conflict in Appendix E.

## Budget
At most 45 tool calls.
