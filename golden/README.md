# golden/ : S6b golden vectors v2 for the C9 decimator, frame and sequencer

`s6_vectors.json` is produced by `python -m model.golden` (tier 0, ideal-A, seed 20261109) and checked by
`model/tests/test_golden.py`. Canonical JSON (sorted keys, compact), so regenerating gives identical bytes
(sha256 pinned in the test). Do not edit by hand. Conventions: SPEC section 3.7a (D45).

Loop: option B, c1 = 1/8, c2 = 1/2, k = 1/2, so k/c1 = 4 (integer). Every u is a multiple of 2^-20, so the
float model and an integer implementation agree bit for bit.

Top level: `format` (2), `seed`, `model`, `vectors`, `streams`, `sequences`, `traces`.

## RTL-observable fields (what an RTL testbench must reproduce)
| Field | Meaning |
|---|---|
| `ybits` | the retimed bit stream = the raw pin. Hex, y[0] is the MSB of the first nibble, 1 = +1, 0 = -1. y[0] is +1 (forced) |
| `acc1`, `acc2` | the two accumulator words, 32-bit two's complement. `acc1` = S = sum y. `acc2` = sum of S, **exclusive** (`acc2 += acc1` before `acc1 += y`); **order 1 keeps accumulating `acc2` exactly as order 2** (defined value, firmware ignores it) |
| `tags`, `tag_word` | the 16-bit tag word, MSB first: `chop` (bit 15, 0 = +1 direct, 1 = -1 swapped), `order` (14, 0 = order 1), `n_code` (13:12, 0..3 = N 64/256/1024/4096), `sys_en` (11), `ota_en` (10), `short` (9), `invalid` (8), `frame_ctr` (7:0, +1 per sub-conversion, wraps 255 -> 0, never reset by a config change, reset only by rst_n) |
| `wire` | the frame as sent: acc1 (8 hex = 32 b), acc2 (32 b), tag word (16 b), MSB first, 20 hex characters. Accumulators are in the modulator frame, no sys sign applied on chip |
| `traces[].trace.rows` | the control trace (below) |

Slot parity is the pair position: `frame_ctr[0]` = 0 for slot a (even, chop +1), 1 for slot b. No pair_idx.

## Reference-only fields (not decimator outputs; do not compare an RTL to them)
`num`, `den`, `num_signed` (= chop sign x num; `num` = acc2 + 4 acc1, `den` = N(N-1)/2, order 1: `num` = acc1, `den` = N),
`pair`, `pairs` (`pair_num` = sum of `num_signed`, `pair_den` = 2 den; pair-demodulated u = pair_num/pair_den),
`model_ref` (`u_hat_signed`, `u_corr`, `x1_final`, `x2_final`, `u_frame`), `u`, `u_requested`, `off`, `config`,
`note`, `dropped`, `frames_sent`, `valid`, `complete`, `loop_valid`. Firmware forms u from the observable words.

## C9 stimulus rule for the forced y[0] (REVIEW-S6 M1)
Each frame carries `comp_raw0`, the junk bit the comparator presents at cycle 0 (1 = +1): the inverse of `ybits[0]`,
so always 0. An RTL testbench drives the comparator input with the `ybits` stream for cycles 1..N-1 but must
drive **`comp_raw0` at cycle 0 and throughout the reset window**. An RTL that passes it through (no forcing) gets
y[0] = -1 and fails every frame. The checker mutant `y0pass` rejects.

## Mode vector (`kind: "mode"`) and offset vector (`kind: "offset"`)
One pair (2 frames, slots 0 and 1) from reset release; both frames are `invalid` (first pair after rst_n, D45 e).
- `config`: `order`, `N`, `n_code`, `fs_div` (code), `sys_en`, `ota_en`, `short`, `chop_mode` (off / sys / ota+sys / ota).
  `ota` (sys 0, ota 1) is the characterisation-only OTA-chop mode (D45 g); never used for data.
- `u`: applied input (0 with `short`). `off`: offset added after the swap, so the modulator input is `s*u + off`
  (`off` = 0 for mode vectors; offset vectors have off = +-1/8 with sys chop; a pair returns u, a stuck chop tag returns about off, an inverted one about -u).
- 320 mode vectors (2 orders x 4 chop modes x 4 N x 9 u + 32 internal-short vectors) and 48 offset vectors.

## Frame
`slot`, `n`, `tags`, `tag_word`, `wire`, `ybits`, `comp_raw0`, `acc1`, `acc2`, then the reference fields above.

## Stream vectors (`kind: "stream"`, `loop_valid: false`)
Synthetic RTL-only streams at N 4096 that no loop produces: all +1 (acc1 = 4096, needs 14 bits), +1 then all -1
(acc2 near -N^2/2), alternating, and order 1 all +1. They test accumulator width. Do not compare to the loop model.

## Sequences (`kind: "sequence"`)
`config0`, `slots[t] = {writes: [{off, cfg}], u}`: a write at cycle `off` of slot t (0 = first cycle of the slot's
reset window). Slot length = N + 2 fs cycles. The latch copies shadow to active on the clock edge that starts the reset
window of an even slot; every write before that edge counts and the last wins; a write on or after the edge (including
`off` 0 of the even slot itself) applies to the next pair. `invalid` marks both frames of the pair after rst_n and
after a change of the latched set (order, N, fs divider, sys_en, ota_en, short). Fields: `dropped`, `frames_sent`,
`frames`, `pairs`.
`seq_cfgchange`, `seq_drop` (slot 3 lost, `frame_ctr` 0,1,2,4,5,6,7), `seq_short` (short toggled mid-pair is
deferred, M3), `seq_multiwrite` (three writes in one slot, last wins; a write on the edge goes to the next pair),
`seq_edge` (write on the last cycle before the edge latches; write at offset 0 does not), `seq_wrap` (262 slots at
N 64, `frame_ctr` wraps at slot 256, two ybits reused).

## Control trace (`traces[0]`, id `trace_ctl`, REVIEW-S6 M2)
N 64, sys + ota chop, pairs 0 and 1, a config write (order 1) in slot 2 that latches at slot 4, then pair 2.
6 slots x 66 fs cycles = 396 rows. `trace.fields` gives the row order; each row is a string of 9 digits (one per field).
D45 i timing, cycle c = 0..N+1 of a slot, conversion index n = c - 2:
| field | value |
|---|---|
| `rst_analog` | 1 on c = 0, 1 (reset window = 2 fs cycles) |
| `acc_clear` | 1 on c = 1, the cycle whose closing edge releases the analog reset (accumulators clear on that edge) |
| `sys_swap` | swap level (1 on odd slots with sys_en), set from c = 0 of the slot, so it changes inside the reset window, never mid-conversion |
| `ota_chop_phase` | 0 during the reset window, n mod 2 for n >= 0 when ota_en (fch = fs/2), 0 when ota_en = 0 |
| `y_force` | 1 on n = 0 only |
| `bit_valid` | 1 for n = 0..N-1 (accumulate enable) |
| `raw_pin` | the retimed y (y[0] forced +1), 0 when `bit_valid` = 0 |
| `tag_chop` | the chop bit of the frame, from the same flop as `sys_swap` (must equal it every cycle) |
| `cfg_latch` | 1 on c = 0 of every even slot (shadow -> active edge) |
`tag_chop` and `cfg_latch` are added to the seven signals named in REVIEW-S6 M2 so the tag-flop and latch-edge rules are observable.

## Checker and mutants
`model/tests/test_golden.py` has an independent integer checker (no iadc import). Every mutant must REJECT: data
(inclusive S, N-1, N+1, y flipped, acc2 23-bit, acc1 13-bit, no sign, y0 free, y0 pass-through, y0 = -1 loop, swap late,
truncate/extend by 1 with den fixed, accumulators not cleared), sequencer (mid-pair latch, invalid on first frame only,
frame_ctr reset on change, no invalid after rst_n, edge write counted before the edge), control trace (swap one clock
late, acc_clear one clock early / late, OTA phase not restarted, tag from a different flop), tag (stuck / inverted
chop sign in pair demodulation). Accumulators of 24 bit (acc2) and 14 bit (acc1) must ACCEPT.
