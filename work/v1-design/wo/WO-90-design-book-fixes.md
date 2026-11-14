# WO-90: DESIGN_BOOK.md review fixes (REVIEW-BOOK-2026-11-15)

Coordinator-written, 2026-11-15. **Tier: writing (Opus).** Fresh agent.

## Input
`work/v1-design/reviews/REVIEW-BOOK-2026-11-15.md` (1 critical, 12 major, 9 minor, 4 style), plus the book at c1fa950. The sources are cited in the review.

## Items
1. Apply **every** finding: C1, M1–M12, m1–m9 and s1–s4. Use the coordinator answers for Q1–Q3. For each fix, check the source the review cites before you edit.
2. The Proposal summary must contain no overclaim. Every status says exactly what was run, on which netlist, at which solver setting. Every model number is labelled tier-0 model.
3. Make the WO-73/D86 HARDENING.md conflict explicit in Appendix E. Do not edit HARDENING.md.
4. Normal prose. Edit `DESIGN_BOOK.md` only. Commit it alone, explicit path, no trailers, no push.
5. Report in ≤ 15 lines: each finding with fixed / not fixed (and why).

## Rules
- No sandbox runs. No local python. If you need to read a web page, use the URL cited in the review only.

## Budget
At most 35 tool calls.
