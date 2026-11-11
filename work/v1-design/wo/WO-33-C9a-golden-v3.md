# WO-33 (C9a): golden v3, the C9 entry gate

Coordinator-written, 2026-11-11. **Tier: code (Sonnet).** C9 starts in parallel with C1 (user, 2026-11-11). Sources:
- SPEC.md §3.7a, §3.8, §3.8a, and "Golden v3 items (G3)" items 1–4 and 6 (item 5 needs no golden change);
- D45, D46, D46a/b, D47, D48(4);
- REVIEW-S7 S7-M2 and REVIEW-S7b m10;
- `model/golden.py`, `model/tests/test_golden.py`, `golden/README.md`, `golden/s6_vectors.json` (v2, sha f08faffe…).

**Do not touch** `design/c1_ota1/`, `design/tier1/` or any C1 file. A C1 agent (WO-32) is working there.

**Sandbox:**
- Run on the sandbox only, from a frozen copy `regr/tt/WO-33-<sha>` including `golden/`.
- At most 1 process; nice and timeout. No local python.

## Items
1. **G3-1:** add boost (1 b, reset 0) and trim (3 b, reset 100) to the config set, the vectors and the `config` fields.
   - The tag word is unchanged.
   - The invalid-after-change scope includes both.
   - Both are latched only at a pair boundary (SPEC §3.7a(d)); last write wins.
2. **G3-2:** config reset values, plus the `fs_div` code table at clk 48 MHz (golden holds the code; the table fixes its meaning).
3. **G3-3:** status word, hold register and overrun semantics.
   - `seq_drop` gains an overrun-flag expectation.
   - frame_ready is set when a frame lands and cleared by `rd`.
4. **G3-4:** 16-bit word order of the frame readout (addr 0–4). Golden `wire` = the concatenation of words 0–4.
   - Also the debug-bus signal list (SPEC §3.8a) as reference data for the RTL tests.
5. **G3-6:** status word [12:9] reports the boost/trim of the frame in the hold register. The vectors carry the per-frame boost/trim.
6. **Bump to golden v3:**
   - `format` 3, a new canonical sha pinned in the test, and golden/README updated.
   - v2 rows stay bit-identical where unaffected; prove it with a test comparing v2 vectors to the v3 subset.
7. **Broken copies (tests must fail on each):**
   - boost latched mid-pair;
   - trim reset ≠ 100;
   - word order swapped (addr 1↔2);
   - frame_ready not cleared by rd.

## Git
Atomic commits with explicit paths (`git commit -- <paths>`), no trailers, no push. If signing fails, list the paths.

## Budget
At most 35 tool calls. Report in ≤ 40 lines: new sha, what changed, test counts, and any SPEC ambiguity found (report it; do not edit SPEC).
