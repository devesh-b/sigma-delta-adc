# WO-55 (C6c) results: robust bias start-up (architecture change)

2026-11-13. Status: **architecture chosen and implemented, full pool running; the 1 µs settle gate (±1 % by ramp end + 10 µs) is not met in smoke.**

- Design note: `design/c6_bias/DESIGN.md` §6.5 (note on the nonphysical WO-50 DC results) and §6.6 (comparison, choice, implementation, smoke).
- Deck: `design/c6_bias/c6_spot.py`; launcher `design/c6_bias/run_wo55.sh`.
- Frozen copies:
  - full pool: `/home/mempool/regr/tt/WO-55-2662364` (`.spiceinit` num_threads=1). It re-tunes R2/R1 first (serial, ≈ 20–30 min), then runs 71 jobs through `scripts/lpool.sh`.
  - smoke: `/home/mempool/regr/tt/WO-55-4ea14b9` (`smoke/`, `smoke2/`, `sm_*`).

## 1. Choice (item 1)
**(c) Banba core with a built-in amp offset.**
- The main amp input pair is skewed 2:1, so the amp balances at V_B − V_A = +Voff ≈ 15 mV (≈ 7σ of the random offset).
- Below ≈ 50 % of I0 the core differential is ≈ 0 < Voff, so the amp always drives the current up. The only non-zero equilibrium left is I0.
- It adds a bounded kick into o1 (≤ the amp sink, off after ok) and bias_ok from a pnp-on comparator on V_R1 = V_B − V_C.

Rejected:
- (a) needs a release threshold accurate to better than ×2 over VDD/T/corner; the gate-0 leaker spreads ×4 (WO-50: 0.39–1.68).
- (b) the constant-gm current has a TC of ≈ +0.8 %/K with xhrpoly, against a row-102 limit of 3 % over 165 K; correcting it needs a VBE/R loop with its own amp.

Table in DESIGN §6.6.

## 2. Smoke evidence (ratio 4.6, before re-tune)

| run | result |
|---|---|
| loop tt/27, sf/27 (skew) | 1 stable equilibrium, 0 mid crossings: ACCEPT |
| loop sf/27 noskew (broken copy) | mid crossing (WO-50: unstable at 0.27 µA): REJECT |
| dci sf/27, from `.ic` 0 / VDD | 1.06845 / 1.06845 µA vs op 1.06844: ACCEPT (WO-50 landed at 0.268 µA from VDD) |
| dct tt/27/3.3, ss/27 | V_R1 70–116 mV over T, ok high over T, phys OK; TC REJECT before the re-tune (±7 %) |
| tran tt/27/3.3, 1 µs (Cc 3 pF, NKK 8) | end error 0.03 %, peak 1.94 ×, t90 19.6 µs, t(±1 %) 32 µs after ramp, 2 ok rises: REJECT on the 10 µs gate |
| Cc 1 pF / NKK 8; Cc 3 pF / NKK 4 | t(±1 %) ≈ 26 µs, 3 rises |
| Cc 1 pF / NKK 4; Cc 0.5 pF / NKK 4 | relaxation, 16–17 rises |
| tran sf/−40 1 µs | settles to 0.03 %, t(±1 %) 40 µs, 3 rises |

WO-50 DC "errors" (12–23 µA, 5.5 mA own current) were nonphysical .dc solutions with V_A ≈ −1400 V. The deck now rejects off-rail DC results.

## 3. Sequencer (item 3), provisional (smoke worst)
- bias_ok asserts when the pnps conduct (I@ok 1.1–1.3 × DC in smoke), then the current settles from an overshoot.
- Proposal: C9 holds rstb for N fs cycles after bias_valid, with N·T_fs ≥ 2 × the worst t(±1 %) − t_ok. Smoke worst: 13.4 µs ⇒ ≥ 27 µs ⇒ **128 cycles at 4 MHz (32 µs)**.
- AND VAPWR-good: VAPWR ≥ 2.7 V from the board/TT supervisor or a C9 counter after power-on.
- Re-derive from the pool's `WORST settle after bias_ok` line.

## 4. Pickup
1. `ssh sandbox 'ls /home/mempool/regr/tt/WO-55-2662364/out/pool/POOL_DONE && cat /home/mempool/regr/tt/WO-55-2662364/out/summary.txt'`
2. If absent: `ssh sandbox 'tail -3 /home/mempool/regr/tt/WO-55-2662364/out/pool_run/pool.status; grep ratio /home/mempool/regr/tt/WO-55-2662364/out/tune.log'`.
3. Expected:
   - ACCEPT: loop / dci / dct `none` rows.
   - REJECT: nosu, early, noskew, ptat, trim_open.
   - INFO: dcv.
   - `tran none` rows are expected to MISMATCH on the 10 µs settle gate and the single-rise row (smoke); read t(±1 %), rises and I@ok per corner.
4. Open options for the 1 µs settle (the gate is not loosened):
   - (i) shorter-L core PMOS units (less VG gate C; costs mismatch and λ);
   - (ii) a larger M5/M6 current (VG slew; costs own current, now ≈ 4.2–5.0 µA at R1 82, ≈ −13 % at 94 µm);
   - (iii) a stronger hysteresis on the comparator (removes the 2–3 extra rises);
   - (iv) the user accepts a ≈ 30–40 µs settle and the C9 hold covers it.
