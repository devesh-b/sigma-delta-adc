# WO-18 (S6b): golden vectors v2: D45 conventions plus REVIEW-S6 gaps

Coordinator-written, 2026-11-09. **Tier: routine (Sonnet).** Sources: SPEC §3.7a (D45), REVIEW-S6-2026-11-09.md (M1–M3, m1, m3, m7–m11, the gap list), WO-17.

**Sandbox:**
- No load gate. Use at most 2 processes, with nice -n 10 and timeout. No shell wait loops.
- **The disk is nearly full** (the user is freeing it). Write nothing large; the target is a golden file under 1 MB.
- Before every sync, make sure `golden/` exists locally, because the rsync --delete would remove it.

## Files you may touch
- `model/golden.py`
- `model/tests/test_golden.py`
- `golden/*`
- `work/v1-design/results/s6_golden.md` (add a v2 section)
- `model/iadc.py`: do not touch.

## Items
1. **Apply D45 to the generator and the independent checker:**
   - tag word layout (c): chop bit, order, n_code, sys_en, ota_en, short, invalid, 8-bit frame_ctr; no pair_idx;
   - order-1 acc2 keeps ΣS (f);
   - invalid on the first pair after rst_n (e);
   - latch on the even-slot reset edge, last write wins, with short in the latched set (d);
   - OTA-only mode vectors (g);
   - no PGA field (h).

   Emit each frame both as fields and as the packed wire words (acc1 32 b, acc2 32 b, tag 16 b, MSB first).
2. **M1 (forced y[0]):** add a per-frame `comp_raw0` junk bit, equal to the inverse of ybits[0], that RTL testbenches must drive at cycle 0. Document the stimulus rule in the README. Add a mutant: an RTL that passes comp_raw0 through must REJECT.
3. **M2 (control trace):** add one cycle-level sequence: N = 64, sys + ota chop, two pairs, then one config change, then one more pair. Per fs clock it lists `rst_analog`, `acc_clear`, `sys_swap`, `ota_chop_phase`, `y_force`, `bit_valid`, `raw_pin`, using the D45(i) timing (reset window 2 fs cycles, fch = fs/2, phase 0 at cycle 0 and held in reset). The independent checker builds the trace from the SPEC text. Mutants, each must REJECT:
   - swap one clock late;
   - acc_clear one clock early;
   - acc_clear one clock late;
   - OTA-chop phase not restarted;
   - chop tag taken from a different flop (tag inverted relative to the swap).
4. **M3:** add a sequence that toggles short only, mid-pair, and shows that the latch defers it and the invalid flag is set.
5. **Edge cases:**
   - **m8:** synthetic RTL-only streams at N 4096: all +1, +1 then all −1, and alternating. Mark them `loop_valid: false`. Add an acc1 13-bit mutant (must REJECT) and an RTL-shaped truncate/extend-by-1 mutant with den fixed.
   - **m9:** a ≥ 258-frame N 64 sequence that reuses one frame's ybits, to cover the frame_ctr wrap.
   - **m10:** dyadic-offset vectors with u_eff = s·u + off. The pair returns u; a misaligned tag returns ±off.
   - **m3:** a multi-write-per-pair vector, and a write landing on the latch edge.
6. **Sequencer mutants (must REJECT):**
   - immediate (mid-pair) latch;
   - invalid on the first frame only;
   - frame_ctr reset on config change;
   - no invalid after rst_n;
   - accumulators not cleared between sub-conversions.
7. **Assertions and README:** add an assertion for `u_hat_signed·den == num_signed`. The README (m11) must mark the RTL-observable fields (acc words, tag word, raw pin, control trace) separately from the reference-only fields.
8. Keep the determinism hash test (with the new hash). Keep the v1 tests that still apply, and update the rest.

## Acceptance
| # | Row | Expect |
|---|---|---|
| 1 | pytest (model + design) | pass |
| 2 | independent checker | bit-exact on 100 % of frames and trace cycles |
| 3 | mutants | every listed mutant REJECTs (table) |
| 4 | file size | < 1 MB |

## Commits (explicit paths, no attribution trailer, no push)
1. `model: golden v2 (D45 tags/latch/invalid, control trace, edge streams) + checker + mutants`
2. `golden: S6b vectors v2 + README`
3. `v1-design: S6b results`

## Budget
At most 50 tool calls. Report the vector, frame and trace counts, the size, the mutant table, and any D45 point that was ambiguous at cycle level (state the choice).
