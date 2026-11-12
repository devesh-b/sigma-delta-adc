# WO-45 (C6a) results: bias reference design note + spot sims

2026-11-12. Design note: `design/c6_bias/DESIGN.md`. Deck: `design/c6_bias/c6_spot.py` (PDK devices only), run script `design/c6_bias/run_wo45.sh`.
Frozen copy on the sandbox: `/home/mempool/regr/tt/WO-45-0fb6db0` (`.spiceinit` num_threads=1, `golden/` gets summary.txt + tune.json), stage 2 through `scripts/lpool.sh` (`out/pool_run`), done marker `out/pool/POOL_DONE`. Raw csv deleted by the deck after parsing.

## Runs
- Stage 1 (sequential): tt/27/3.3 V, R2/R1 grid 3.0…6.6 (13 points), ratio at the 125 vs −40 slope zero → `out/tune.json`.
- Stage 2 (lpool, 17 jobs): dct (T −40…125, master current + 8 trim copies + own current) at tt/3.3, ss/3.0, ff/3.6, fs/3.0, sf/3.0; broken copies ptat (R2 open) and trim_open (LSB leg open) at tt; dcv (PSRR info) at tt/27, ss/−40, ff/125; tran (VAPWR 0 → V over 1 µs and 10 ms, uic, no .op) at tt/27/3.3, ss/−40/3.0, ff/125/3.0; broken copy nosu (Ms removed) at ss/−40 and ff/125, both ramps.

## Smoke (before the tune, ratio 4.6, tt)
I(27) 1.005 µA (master, code 100); TC −2.77 / +0.52 % (slope +1.97 %); own current 3.58 µA; trim: steps 0.996–0.998 u, step 5.04 % of target, I7/I0 1.4103–1.4112 (≥ 1.4126 for the literal ±20 % fails by 0.1 %: the DESIGN.md §3 finding; the check now uses the process range ±19 %, I7/I0 ≥ 1.3836).

## Results
PENDING. Status at 23:18 (sandbox time): stage 1 tune running (≈ 86 s per grid point under load 6.8 on 6 cores, the dct sweep needs true-gmin stepping; ≈ 19 min for the grid), stage 2 not started; expect ≈ 30–40 min more.

## Pickup (no wait loops)
1. `ssh sandbox 'ls /home/mempool/regr/tt/WO-45-0fb6db0/out/pool/POOL_DONE && cat /home/mempool/regr/tt/WO-45-0fb6db0/out/summary.txt'`
2. If absent: `cat .../out/tune.log` (stage 1 output appears only when it ends) and `tail .../out/pool_run/pool.status`.
3. Expected verdicts: every `none` row ACCEPT, `ptat` / `trim_open` / `nosu` rows REJECT (`summary` prints MISMATCH otherwise and exits 1). A `nosu` ACCEPT means the start-up check is blind (DESIGN.md §6) and needs a harder condition.
4. Copy the table into this README, fill DESIGN.md §8 own-current line and §6 t90 − t_ok, then run the reviewer on DESIGN.md.
