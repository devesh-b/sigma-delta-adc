# WO-17 (S6): golden vectors for the C9 decimator, frame and sequencer

Coordinator-written, 2026-11-09. **Tier: routine (Sonnet).** Sources:
- PLAN S6 / C9 / V4 and the PLAN "Review additions" (S6: m2, F4, F6);
- SPEC §3.6 sequencing rules (1)–(12), §3.7 decimator, §3.8 config, comparator row F8;
- REVIEW-S5e (F7/F8 closure);
- REVIEW-S5h §3: cover the order-1 u_corr branch.

Read `work/v1-design/HANDOFF.md` first.

**Sandbox:** direct ssh + nohup, full env (as in WO-16). There is no load gate (user rule); still use at most 2 of your processes, with nice -n 10 and timeout. Never use shell wait loops or pgrep polling: check once, and if the job is not finished, report. Smoke-test on 1 vector first.

## Files you may touch
- `model/golden.py` (new). It is the generator, and it imports `model/iadc.py` read-only.
- `model/tests/test_golden.py` (new).
- `golden/` (new): the vectors as JSON, plus `golden/README.md` describing the format.
- `model/iadc.py`: **only** if the bitstream / accumulators are not exposed. Make the smallest change, add a test, and leave default behaviour unchanged.
- `work/v1-design/results/s6_golden.md` (new).

## Items
1. **Generator** (tier 0, ideal-A: no noise, no leakage, no OTA non-idealities).
   - For each vector, emit:
     - the config: order, N, N code, fs divider, OTA-chop enable, sys-chop enable, internal short, and PGA if SPEC has one (F6; skip if not chosen);
     - the input u;
     - the per-sub-conversion bitstream y[0..N−1], **with y[0] forced at reset release** as SPEC F8 / rule (9) defines it (find the forced value in SPEC or the model and state it);
     - acc1 = S and acc2 = ΣS, using the **exclusive-S** convention (`acc2 += acc1` before `acc1 += y`);
     - the frame tags (F4): chop sign, order, N code, frame counter, pair index, and the invalid flag on the first pair after a config change (rule 10);
     - the decimator output: **bitstream-only u_hat with the sys sign applied**, not u_corr, plus the pair-demodulated value.
2. **Coverage (mode matrix, V4):**
   - order 1/2 × chop {off, sys, ota+sys} × N {64, 256, 1024, 4096} (or the SPEC N set if it differs) × internal short;
   - u at {−0.9, −0.5, −1/N-ish small, 0, +small, +0.5, +0.9} FS, plus 2 random u per mode with a fixed seed;
   - **the order-1 u_corr branch** (REVIEW-S5h);
   - one config-change sequence, showing the invalid tag and the latch-at-pair-boundary behaviour;
   - one dropped-frame sequence, showing the frame counter gap.
3. **Independent check.** Write a second, minimal pure-Python accumulator and frame implementation from the SPEC text (not by calling iadc). It must reproduce every acc1, acc2 and tag from y bit-exact.
4. **Non-vacuity (mutants), each must REJECT** against the golden set:
   - inclusive-S convention;
   - off-by-one N (N−1 and N+1);
   - y sign flipped;
   - accumulator truncated to 23-bit signed (N 4096 must overflow) — SPEC says 24-bit fits, so also show that 24-bit passes;
   - sys sign not applied;
   - y[0] not forced;
   - chop swap one cycle late (C9 mutant), if it can be expressed at this level; else say so.
5. **Determinism.** Regenerating with the same seed gives byte-identical JSON; check this with a hash in the test.

## Acceptance (coordinator, frozen copy)
| # | Row | Expect |
|---|---|---|
| 1 | pytest (model + design) | pass; the new tests are included |
| 2 | independent check | bit-exact on 100 % of vectors |
| 3 | mutants | every listed mutant REJECTs (count reported) |
| 4 | coverage | the matrix in item 2 is complete, or the gaps are listed with reasons |

## Commits (explicit paths, no attribution trailer, no push)
1. `model: golden-vector generator (exclusive-S, forced y[0], frame tags) + independent checker + tests`
2. `golden: S6 vectors + format README`
3. `v1-design: S6 results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget
At most 50 tool calls. Report: vector count, file size, mutant table, coverage gaps, and any SPEC ambiguity you had to resolve (state the choice; don't silently pick one).
