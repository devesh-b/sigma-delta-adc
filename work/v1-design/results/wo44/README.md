# WO-44 (C3a) results: comparator spot sims and PDK mismatch probe

Frozen copy: `/home/mempool/regr/tt/WO-44-5bfb065` (`c3_comp/` at commit 5bfb065, `golden/`, `.spiceinit` `num_threads=1`; each deck dir also has its own `.spiceinit` with the PDK flags and `num_threads=1`).
Decks: `spot/<point>/deck.sp`, logs `spot/<point>/deck.log`, pool `spot/pool_logs/` (lpool.sh, launched 23:10:56, detached).
Design note: `design/c3_comp/DESIGN.md`. Sizes: set A of DESIGN.md §5.

## State at hand-off (2026-11-12 ~23:20)
Box load ≈ 5–6 on 6 cores, so lpool runs one job at a time. 1 of 13 decks finished (≈ 85 s); `tt27_m1` was still running after > 3 min. **Pending:** when `spot/pool_logs/POOL_DONE` exists, run on the sandbox:

    cd /home/mempool/regr/tt/WO-44-5bfb065 && python c3_comp/spot_tran.py collect spot

It writes `spot/spot.json` and prints one ACCEPT/REJECT row per point plus `SUMMARY` (exit 1 if a nominal point REJECTs or a broken copy ACCEPTs). Expected REJECTs: `brk_starve` (t_dec), `brk_qswap` (polarity), `brk_cl10` (kickback), `brk_mm_off` (PDK MC off → σ ≈ 0). If `brk_starve` does not reject, the starve copy is too mild (record it, do not tune the gate).

## Finished point: tt27_p1 (tt, 27 °C, VDPWR 1.80 V, Δ = +1 mV, x2 CM 1.5 V, 4 MHz timing)
| Quantity | Value | Limit |
|---|---|---|
| sim end | 195 ns (= TSTOP) | §11.2 |
| decision time (clk 50 % → q 50 %) | 0.345 ns | < 33.75 ns |
| polarity | q 1.80 V, qb ≈ 1 µV (q = 1 for x2p > x2n) | correct |
| kickback diff peak, fire / reset edge | 0.64 mV / 1.86 mV | ≤ 5 mV |
| diff residue at +0.5·t_half, fire / reset | 0.6 µV / 0.6 µV | ≤ 0.5 mV |
| kickback CM peak | 45 mV | report (C2 CMFB interface; hand estimate 25–30 mV was low) |
| supply charge per cycle | 0.175 pC ⇒ 0.70 µA at 4 MHz from VDPWR | report |

`tqbz` "out of interval" in this log is expected (qb does not rise for Δ > 0); it is an info measurement and not in the required set.

## PDK mismatch (item 3, from the model files)
- `nfet_01v8` / `pfet_01v8`: vth0 mismatch present (`MC_MM_SWITCH·AGAUSS·slope/sqrt(l·w·mult)`, nfet 3.356 / 7.356 mV·µm, pfet 4.356–7.356 mV·µm), active in the `*_mm` lib sections.
- **`nfet_g5v0d10v5`: `vth0_slope = 0.000` for all devices; only toxe mismatch (0.8e-2; pfet_g5v0d10v5 1.2–2.3e-2).** A `tt_mm` MC therefore under-reports any HV input pair offset. The `mm_tt` / `brk_mm_off` decks measure σ(Vgs) of 60 instances per type (pending, same pool).
