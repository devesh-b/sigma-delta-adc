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
