# WO-105: full-chip short gates (D95) and tier-1 gate B with transistor OTA1 + OTA2

Status 2026-11-21 16:48: code committed (b7cb88d), frozen copy `/home/mempool/regr/tt/WO-105-b7cb88d`, three pools launched and **waiting for global lpool slots** (all held by other WOs at launch). **No gate results yet.**

- WO-95 orchestrator `run_wo95.sh` (PID / PGID 743866) killed by process group before it launched the N 1024 pool. The WO-95 smoke (PGID 743864, N 16, t_rel 20 µs, 48 µs simulated) is still running and is the source of `sec_per_conv`.
- Stand-ins unchanged and marked: C6.3 port mirrors (bench, uncascoded), ideal V_ICM / V_OCM, bench output-reset TG. Swap to `c6_final` / `c5c7_ref` once WO-104 accepts them, then rerun (a) and (b16).
- OTA2 in every top job = D91 cell (`design/c2_ota2/ota2.spice`, byte-identical to WO-95's `d91.spice`), shared bias (`--ota2-shared`), tag `ota2-ota2`.

## Code changes (b7cb88d)
- `design/top/top_bench.py`
  - Each conversion now records the slot-0 residue `x1s`, `x2s`, read at t0 + 0.4 T (sampling half, after reset release, before the first integration).
  - `bc` takes `--uset=a,b,c` (use the `=` form for negative values) and `--no-dummy`. INL (c) is reported only below N 1024 (D95). `pass_b` is the gate.
  - The `e` run also scores gate **(f)**: max slot-0 residue ≤ `RES_LIM` = 1e-3 VREF (≈ 2 mV diff; a bench choice, not a SPEC number), and every non-overload conversion within `fn_tol`. The json carries `pass_e` and `pass_f` separately. ACCEPT needs both.
- `design/tier1/gen_tier1.py`: new `ota2_xtor` hook, mirroring `ota1_xtor` (it needs `ota1_xtor`).
  - Xota2 sits on OTA1's bias nets and phases, with isl = rst.
  - The vg–o reset short is replaced by an output short `Srst2d`.
  - Stage-2 top plates and bleeders go to V_ICM.
  - `cp_vg_ext` is 35 fF and `c_out_ext` is 20 fF.
  - Generate check: the deck parses and has the expected Xota2 / Srst2d / Rbl2→vicm lines.
- `design/top/gateb_x2.py`: wraps `c1b_gateb.py --mode prec` and injects `ota2_xtor` (prec mode only).

## Gate table (tt/27/3.3, fs 2 MHz, boost 0, t_rel 40 µs, O1; each broken copy must REJECT)
| Gate | Job (out/…) | Rule | Broken copy | Nominal | Broken |
|---|---|---|---|---|---|
| (a) start-up → first valid conv | g/a_nom, g/a_nosu | WO-95 (a) checks at N 16. These include ib within 1 % at t_rel = 40 µs (per-cycle means within ±1 % of ib_final, WO-105c); if that fails, t_rel is too short for every gate | nosu | pending | pending |
| (b) DC fn N 16 | g/b16_nom, g/b16_dacswap | 5 pts ±0.9 (dummy first), \|u_hat−u\| ≤ fn_tol, bits-only vs golden ≤ fn_tol + 2·x2 bound | dacswap | pending | pending |
| (b) DC fn N 64 | g/b64_p0 (−0.9, 0, 0.9), g/b64_p1 (±0.45) | same rule, no dummy (relies on (a)) | covered by b16_dacswap (same check code) | pending | — |
| (d) chop pair N 16 | g/d_nom, g/d_noswap | WO-95 (d) | noswap | pending | pending |
| (e) overload ±1.1 / recovery N 16 | g/ef_nom, g/ef_noreset | recovery ≤ 1 ppm FSR, over ≥ 0.95 / ≤ −0.95 | noreset (check `pass_e` false) | pending | pending |
| (f) reset residue at slot 0 | the same ef runs | res_slot0_max ≤ 1e-3 VREF, non-overload convs within fn_tol | noreset (check `pass_f` false on its own) | pending | pending |
| ss/−40/3.0 | c/a_ss, c/b16_ss, c/d_ss, c/ef_ss (PRIO=low) | same | — | pending | — |
| Tier-1 gate B, OTA1 + OTA2 transistor | t1/ parts 0..5 of 6, O2, N 1024, m 21 | combined endpoint INL ≤ 1.333 ppm | none queued (open item; option: srdeep, which scales the shared bias of both OTAs) | pending | — |

## Runtime sizing
- `sec_per_conv` has not been measured yet: the smoke json is pending. Sizing used the D95 rate of 0.5 µs simulated per 5 min (6 µs/h). One N 16 conversion is 19 T = 9.5 µs ≈ 1.6 h, and one N 64 conversion is 33.5 µs ≈ 5.6 h.
- Estimated job times:
  - a: ~6.5 h
  - b16: ~13 h
  - d: ~11 h
  - ef: ~14 h
  - b64_p0: ~20 h
  - b64_p1: ~15 h
- tt total ≈ 126 slot-hours and ss ≈ 45. With about 3–5 slots, the tt set should finish in about 1.5–2 days, and ss after it.
- If the smoke shows a rate worse than 2× this: drop b64_p1 first, then ef_ss.

## Pickup (sandbox)
```
F=/home/mempool/regr/tt/WO-105-b7cb88d
tail -3 $F/out/{gates,t1,corners}/pool/pool.status; ls $F/out/*/pool/POOL_DONE
grep -h '"sec_per_conv"' /home/mempool/regr/tt/WO-95-b4b44f4/out/smoke/gsmoke_*.json   # measured throughput (smoke, WO-95 copy)
grep -h "VERDICT\|broken copy" $F/out/g/*/run.txt $F/out/c/*/run.txt
grep -h '"pass_e"\|"pass_f"\|res_slot0_max' $F/out/g/ef_*/*.json                       # (f) must fail on its own in noreset
# tier-1 combine after t1 POOL_DONE:
cd $F/out/t1 && . $F/env.sh && python3 $F/design/top/gateb_x2.py $F/out/t1 --mode prec --opt O2 --n 1024 --combine 6
# relaunch a pool after a stop: cd <pooldir>/.. && PRIO=high SKIPDONE=1 setsid nohup bash $F/scripts/lpool.sh jobs.txt pool >/dev/null 2>&1 </dev/null &
```
If the tier-1 combined Δ vs the OTA1-only gate B is large, run the D43c ladder (O1/O2/third point, `--vntol-div`, `--tmax-div`) on the part with the worst endpoint.
