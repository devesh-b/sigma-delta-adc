# WO-48 (C3b) results: D74 revision, netlist, full testbench

Commit: 37ca242 (`design/c3_comp/{DESIGN.md,sizes_draft.py,netlist.py,c3_tb.py}`).
Frozen copy: `/home/mempool/regr/tt/WO-48-37ca242` (`c3_comp/`, `.spiceinit` `num_threads=1`; each deck dir has its own `.spiceinit`, MC decks add `rndseed`).
Full run: `run/` (47 decks: 13 one, 5 st, 12 mc × 25 instances, 17 cyc), lpool launched detached 2026-11-13 00:02:39, logs `run/pool_logs/`.

## State at hand-off
Box load ≈ 6.6 on 6 cores, so lpool runs one job at a time. Expected wall time at one slot: ≈ 6–9 h (cyc decks ≈ 18 min each at tmax 1 ps, 2 MHz deck ≈ 2×; MC decks not yet timed at full size).
**Pending:** when `run/pool_logs/POOL_DONE` exists, run on the sandbox:

    cd /home/mempool/regr/tt/WO-48-37ca242 && . /home/mempool/tt-sd/.venv-sbx/bin/activate && python c3_comp/c3_tb.py collect run

It writes `run/c3_tb.json` and `run/summary.txt` (one line per deck / MC group, ACCEPT/REJECT per row with the expectation, SUMMARY; exit 1 if any nominal row REJECTs or any broken copy ACCEPTs its target row). Copy `run/summary.txt` here as `summary.txt`. No raw/csv files are written.

## Smoke run (`smoke/`, C3_SMOKE=1: 2 cycles, 2 MC instances, 2 bisection steps; syntax check only)
| Deck | Result |
|---|---|
| one_ss-40_162 (set A′, 100 fF q load, output buffer) | sanity ok; **t_dec(1 mV) 2.00 ns** (T2band ACCEPT, band 0.56–3.36 ns); diff kick 0.34 / 2.73 mV fire / reset, residue 1 µV; CM peak 40.8 mV, CM residue at 0.5·t_half 0.92 / 1.04 mV |
| st_tt27_a (order a, VDPWR 1.98) | sanity ok, 181/181 pair measurements; **T8 REJECT: max 1.8 V pair 2.36 V (M3 source–body = dp to vss)**; HV max 3.72 V (M1 Vgs) |
| mc_tt_0 (2 instances, 2 steps) | bisection loop works (trips ±10 mV after 2 steps, as expected); injected rms 3.57 mV vs σ_inj 3.39 |
| cyc_ss-40_162 (2 cycles) | timed out at 250 s (smoke limit) at ≈ 511 of 560 ns: deck runs, measurements untested until the full run |

## Finding to carry (T8, nominal REJECT in smoke)
dp (internal drain of the HV input pair, source of the 1.8 V latch NMOS M3) reaches ≈ 2.36 V with VDPWR = 1.98 V, i.e. ≈ 0.38 V above the supply. Likely cause (not yet confirmed from the waveform): the overload part of the stimulus swings x2 by 4.1 V in 20 ns through 10 Ω (≈ 200 V/µs, no R_X2/C_X2), and the gate–drain overlap of the 20 µm HV pair kicks the floating losing-side dp/dn up until the precharge PMOS drain–body diode clamps. Options (not applied; the gate was not changed): (a) drive the stress deck through the behavioural x2 node (R_X2 / C_X2) or at the OTA2 slew rate once C2 has it, which is a stimulus correction to be agreed by the reviewer; (b) if the kick is real at OTA2 slew, a small clamp/keeper on dp/dn or a cascode. The full run repeats it at tt/27 and ff/−40, orders a and b.
