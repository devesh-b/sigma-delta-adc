# S6 golden vectors (WO-17)

Generator: `python -m model.golden --out golden/s6_vectors.json` (sandbox, seed 20261109). Test: `python -m pytest -q model/tests design/tests` -> 129 passed, 2 skipped (sandbox, 79 s).
Mutant table: `python model/tests/test_golden.py` (sandbox).

- 242 records: 240 mode vectors (2 frames each) + 2 sequences (12 and 8 frames) = 500 frames. File `golden/s6_vectors.json` 376,471 bytes, sha256 b8bd7a93b82b999556cc7a2f07fd1644af82d2881daa03ff961b374ecef9053b (pinned in the test; regeneration is byte-identical).
- Independent check (integer loop + accumulators + sequencer written from SPEC, no iadc import): 500/500 frames bit-exact on acc1, acc2, num, den, signed num, tags, pair values; it also regenerates every stored bitstream.

| Mutant | Frames differing (of 500) | Result |
|---|---|---|
| inclusive S | 210 | REJECT |
| N-1 | 500 | REJECT |
| N+1 | 500 | REJECT |
| y sign flipped | 402 | REJECT |
| acc2 truncated to 23-bit signed | 18 (all N 4096) | REJECT |
| acc2 24-bit signed | 0 | ACCEPT (as required) |
| sys sign not applied | 137 | REJECT |
| y[0] not forced (decimator sees opposite first decision, loop used +1; F8 disagreement) | 500 | REJECT |
| y[0] = -1 through the whole loop (alternative valid stream) | accumulators agree on some frames; bitstream compare rejects 500 | REJECT (bit level) |
| sys-chop swap one cycle late (input sign changes at cycle 1) | 275 | REJECT |
| OTA-chop phase restart (rule 7) | not expressible: tier 0 is ideal, OTA chop has no effect on the bitstream | gap |

Also: the checker rejects a corrupted copy (acc2 +1, invalid tag flipped).

## SPEC ambiguities and the choice made
1. Forced y[0] value: SPEC (3.2, 3.6 rule 9) gives none. Chosen +1 (model tie x = 0 -> +1). Note: an alternative loop with y[0] = -1 reaches nearly the same accumulators (the loop absorbs it), so only the bitstream compare, or a decimator/DAC disagreement, shows it.
2. Frame tag widths and encodings: not in SPEC. Chosen: chop_sign +-1, n_code 0..3 = 64/256/1024/4096, frame_ctr 8-bit per sub-conversion, pair_idx = pairs since last config latch, invalid = both frames of the first pair after a change (initial config load is not a change).
3. "Pair index" meaning: taken as the pair count since the last latch (lets firmware pair frames across a drop).
4. Config request timing: a request written during slot t latches at the next even slot > t.
5. Order-1 acc2: SPEC says single accumulator; acc2 recorded null (don't care).
6. Without sys chop a "pair" is still emitted (two same-sign frames) so the pair counter path is exercised.
7. Loop coefficients: option B (c1 1/8, c2 1/2, k 1/2, k/c1 = 4) per D3; u quantised to 2^-20 so integer and float loops agree exactly.

## Coverage gaps
- Internal short: one vector per mode (u forced to 0), so no 7 + 2 u sweep.
- fs divider: carried in the config and varied in the config-change sequence only; no tier-0 effect.
- PGA: not in v1 (none), field is null.
- OTA-chop-phase mutant (above). Analog effects (noise, leakage) are out of scope at tier 0.
- Random u: 2 per (order, chop, N) from the fixed seed.

## Model change
`model/iadc.py`: `convert(..., return_state=True)` now also returns `y` (N, B) decisions; default outputs unchanged (all existing tests pass; `test_iadc_y_exposed`).

## v2 (WO-18, S6b): D45 conventions plus REVIEW-S6 gaps

Generator: `python -m model.golden --out golden/s6_vectors.json` (sandbox). Mutant table: `python model/tests/test_golden.py`. Pytest (`model/tests design/tests`, sandbox): 147 passed, 2 skipped, 56 s.
File `golden/s6_vectors.json`: 776,948 bytes (< 1 MB), sha256 f08faffe17ceea91f31920f66bf3d4ac263c62e4b575432b5154aea7b90c938f (pinned; regeneration is byte-identical).

Counts: 368 vectors (320 mode incl. OTA-only and 32 short, 48 offset), 4 RTL-only streams (N 4096, `loop_valid: false`), 6 sequences (cfgchange, drop, short, multiwrite, edge, wrap 262 slots), 1 control trace (396 cycles); 1054 frames. Independent checker: 1054/1054 frames and 396/396 trace cycles bit-exact (acc words, 32-bit wire word, 16-bit tag word, comp_raw0, tags, pairs), plus `u_hat_signed*den == num_signed` on every loop frame.

| Mutant | Result (differences) |
|---|---|
| inclusive S / N-1 / N+1 / y flipped / acc2 23-bit / no sign | REJECT (919 / 1050 / 1050 / 986 / 47 / 330 of 1054) |
| y0 free (F8) / y0 pass-through of comp_raw0 (M1) / y0 = -1 loop / swap late (loop) | REJECT (1054 / 1054 / 1050 / 661) |
| RTL truncate by 1 / extend by 1, den fixed | REJECT (1054 / 1054) |
| acc1 13-bit | REJECT (2 frames, the N 4096 all-+1 streams only) |
| accumulators not cleared between sub-conversions | REJECT (643) |
| acc2 24-bit, acc1 14-bit | ACCEPT (0), as required |
| immediate (mid-pair) latch / invalid on first frame only / frame_ctr reset on change / no invalid after rst_n / edge write counted before the edge | REJECT (19 / 384 / 31 / 761 / 8 mismatches) |
| trace: swap one clock late / acc_clear early / acc_clear late / OTA phase free-running (not held at 0 in reset) / tag inverted vs swap | REJECT (5 / 12 / 12 / 6 / 396 rows) |
| offset pairs: chop sign stuck / inverted | REJECT (return about off / about -u, 48/48 vectors) |

D45 points that were ambiguous at cycle level, with the choice made:
1. acc_clear timing: asserted on cycle 1 (the last reset-window cycle), so the clearing edge is the one that releases rst_analog. Window = cycles 0-1; conversion cycle n = c - 2.
2. sys_swap changes on cycle 0 of the slot (first cycle of the reset window), the earliest instant inside the window.
3. raw_pin outside bit_valid is 0 (idle low); y_force is a single-cycle strobe on n = 0.
4. Two columns were added to the trace (`tag_chop`, `cfg_latch`) so the tag-flop and latch-edge rules are observable.
5. OTA phase mutant: a phase flop that is not held in reset toggles on cycle 1. A mutant that merely free-runs over N+2 (even) cycles would be indistinguishable at the slot start, so reset-window hold is what the trace tests.
6. A write that equals the active config is not a "change", so it would give a valid pair. No vector covers this case; if C9 flags any write, SPEC should say so.
7. Writes carry a cycle offset in the slot; only the slot of the write and its order matter (earlier slot = before the edge, even slot itself = on/after it). The last cycle of the previous slot is offset N+1.
8. Order-1 acc2 = sum S, so the unused word is defined; `num` for order 1 stays acc1, den N.
