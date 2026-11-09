# golden/ : S6 golden vectors for the C9 decimator, frame and sequencer

`s6_vectors.json` is produced by `python -m model.golden` (tier 0, ideal-A, seed 20261109) and checked by
`model/tests/test_golden.py`. Canonical JSON (sorted keys, compact), so regenerating gives identical bytes
(sha256 pinned in the test). Do not edit by hand.

Loop: option B, c1 = 1/8, c2 = 1/2, k = 1/2, so k/c1 = 4 (integer). Every u is a multiple of 2^-20, so the
float model and an integer implementation agree bit for bit.

Top level: `format`, `seed`, `model`, `vectors` (240 mode vectors), `sequences` (2).

## Mode vector (`kind: "mode"`)
One sub-conversion pair (2 frames, slots 0 and 1), run from reset release with the initial config (not a "change").
- `config`: `order` (1/2), `N`, `n_code` (0..3 = 64/256/1024/4096), `fs_div` (code, no tier-0 effect), `ota_chop`,
  `sys_chop`, `short` (internal short), `chop_mode` (off / sys / ota+sys), `pga` (null: no PGA in v1).
- `u_requested`, `u`: input in FS units; with `short` the applied `u` is 0.
- `frames[2]` and `pair`.

## Frame
- `slot`, `n`, `tags` = {`chop_sign` (+1/-1, sys chop sign of this sub-conversion; -1 only on odd slots with sys chop),
  `order`, `n_code`, `frame_ctr` (8-bit, +1 per sub-conversion), `pair_idx` (pairs since the last config latch),
  `invalid` (true on both frames of the first pair after a config change)}.
- `ybits`: hex string, y[0] is the MSB of the first nibble; bit 1 = y +1, bit 0 = y -1. y[0] is forced to +1 at reset release.
- `acc1` = S = sum y; `acc2` = sum of S, **exclusive** (`acc2 += acc1` before `acc1 += y`); `acc2` is null for order 1.
- `num` = acc2 + 4*acc1 (order 2, `den` = N(N-1)/2) or acc1 (order 1, `den` = N). `num_signed` = chop_sign * num.
  Bitstream-only u_hat = num_signed/den (no residue correction).
- `model_ref` (model-side reference, not a decimator output): `u_hat_signed`, `u_corr` (residue-corrected, input frame),
  `x1_final`, `x2_final`. `u_corr` covers the order-1 branch (x1/(c1 N)) and equals u to rounding.

## Pair
`pair_num = num_signed(a) + num_signed(b)`, `pair_den = 2*den`: pair-demodulated u = pair_num/pair_den (exact integers).

## Sequence (`kind: "sequence"`)
`config0`, `slots[t] = {request, u}` (a request written during slot t latches at the next even slot > t),
`dropped` (slots lost on the link), `frames` (all slots), `frames_sent` (slots delivered), `pairs`
({`slots`, `complete`, `valid`, `pair_num`, `pair_den` when complete}). `seq_cfgchange`: two requests, invalid pairs,
latch only at pair boundary. `seq_drop`: slot 3 dropped, `frame_ctr` 0,1,2,4,5,6,7, pair 1 incomplete.
