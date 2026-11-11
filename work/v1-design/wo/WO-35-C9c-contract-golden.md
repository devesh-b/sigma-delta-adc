# WO-35 (C9c): D66 contract into SPEC change log + golden v3.1

Coordinator-written, 2026-11-11. **Tier: code (Sonnet).** Sources:
- D66;
- `work/v1-design/C9_VERIF_PLAN.md` §8;
- SPEC.md §3.7a, §3.8, §3.8a and the change log;
- `model/golden.py`, `model/tests/test_golden.py`, `golden/`.

**Do not touch** C1 files (`design/c1_ota1/`, `design/tier1/`). WO-32 is running there.

**Sandbox:** frozen copy `regr/tt/WO-35-<sha>`, at most 1 process, no local python.

## Items
1. **SPEC change log:** one CL entry per D66 bullet (reason + D66), plus the matching wording edits in §3.7a/§3.8/§3.8a only. SPEC stays FROZEN otherwise. Add a short "C9 digital ↔ analog port contract" subsection in §3.8a:
   - comparator sample edge;
   - DAC flop edge;
   - control-signal list with polarities;
   - fs clock + bit_valid;
   - phase generator in C4.
2. **Golden v3.1:**
   - hold tag invalid = 1 after rst_n, with status trim 100;
   - cfg_pending post-latch value on the coincident clk (no mask);
   - `hold[t]` / status semantics under the new rd rule (snapshot on the rd edge; post-load suppression), with sequences covering rd before, on and after a load;
   - fs_div normalisation for codes 5–7;
   - reserved bits ignored.
   New canonical sha; v3 rows that are unaffected stay identical, proved by a subset test against a frozen v3 copy.
3. **Broken copies:**
   - hold invalid = 0 after reset;
   - rd on the load clk clears;
   - fs_div 5 counted as a change;
   - shift register not cleared at ld.
   Each must fail.

## Git
Explicit-path commits, no trailers, no push.

## Budget
At most 35 tool calls. Report in ≤ 40 lines.
