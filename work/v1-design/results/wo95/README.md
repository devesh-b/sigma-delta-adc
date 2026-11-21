# WO-95: full-chip transistor-level top bench, precision mode (fs 2 MHz, boost 0, N 1024)

Status 2026-11-21: the bench has been built and the runs are queued on the sandbox. **No gate results yet.** A generate-only check passed (474-line deck, 355 X instances, `out/smoke/gen_check.cir`); ngspice has not run it yet. All five global lpool slots were taken by WO-91, WO-77 and WO-97, so the smoke run had not started when this was written. The numbers below get filled in from `out/*/run.txt` and `*.json`.

Frozen copy: `/home/mempool/regr/tt/WO-95-b4b44f4` (design/top/top_bench.py at b4b44f4; the orchestrator script from f698d26 is copied in).
OTA2 used in every result: **`ota2-ota1cell`** (the OTA1 cell with its own bench mirrors). D91 (a 9/16-scaled cell on shared bias nets) plugs in through `--ota2-sub <WO-98 file> --ota2-name <subckt> --ota2-shared`. The OTA2 used is part of each tag and of the json field `ota2`.

## Deck (`design/top/top_bench.py`)
- **Transistor level:**
  - OTA1 and OTA2: C1 `ota1` cell, cmfb sc, base geometry.
  - C3 comparator: rev g default sizes, strobe = C4 `phc`, vdd = VDPWR.
  - Every SC switch at the C4 `SW` sizes, on the C4 phases from the DESIGN.md §2 table. This includes the D12 top-plate shorts, the stage-2 plate short, and the Ck2 rest short.
  - C4 `c4_gen` (HVL cells, level shifters, VDPWR detector, chopper latch, strobe).
  - C6 option (c) core: the `c6_spot.deck()` devices wrapped as a subckt, code 100, tune R2/R1 2.45 and R1 144.8 µm from WO-64. Its real `bias_ok` drives the reset hold.
- **Bench stand-ins (not chip netlist):**
  - C6.3 port mirrors, uncascoded. Sinks are NMOS from VN with W = 2 µm × I_port/1.07 µA at L 4. Sources are 0.42/20 PMOS units from VG. The port current error shows in the json `ports` and `startup.ib_*`.
  - Ideal V_ICM 1.20 V and V_OCM 1.50 V.
  - Per-OTA output reset short: TG 4/12 on C4 `r2`, the same as the ideal short in gate B.
  - 35 fF of vg routing and 20 fF of output routing per side (the gate B values).
- **Ideal C9 loop logic:**
  - fs bit clock, 1.8 V: low = φS, high = φI.
  - DAC flop: q is captured just before the fs rising edge. It is forced to +1 in reset and in slot 0.
  - The rst_analog schedule (nrst 3), swap pin, and dec = NAND(q, qb).
  - The reset is forced high whenever `bias_ok` is low.
  - VAPWR is a 1 µs ramp from 50 mV. VDPWR is an ideal 1.8 V.
  - VIN and VREF (2.048 / 0 V) sit behind the 500 Ω + 5 pF pads.
- **Hold scaling (D85/D88):** the reset releases at t_rel = 100 µs = 200 fs cycles. The silicon hold is 2^16 + 256 = 65 792 cycles, so this is 1/329 of it. The shortened hold is valid only if gate (a) shows that bias_ok is up and the bias is within ±1 % at t_rel.
- **Decimation:**
  - INL uses u_hat = the SPEC 3.7 residue reconstruction with x2[N] from the simulation (as gate B).
  - The DC-function row compares the bits-only code (the C9 accumulation) with the bits-only code of the ideal discrete loop (`tier1_tb.ideal_loop`).
  - Ref A was not driven pin-level. Its accumulators are the same formula, so the next step is a Ref A replay of the saved bitstreams.
- **Lint:** BAD_LOG, the transient-op/stepping fallback, the reltol echo, an empty or missing data file, final time = tstop, NaN, and bits that are not ±1 all make a run unhealthy. Unhealthy is neither ACCEPT nor REJECT.
- **Solver:** O1 ladder (tmax ≤ τ/10 ≈ 1.9 ns). An O2 rerun of bc_nom_tt is the convergence check (next).

## Gates (tt/27/3.3 unless stated; each broken copy must REJECT)
| Gate | Pass rule | Broken copy | Nominal | Broken |
|---|---|---|---|---|
| (a) start-up | bias_ok up at t_rel and no drop after it; bias within ±1 % at t_rel and steady (≤ 1 %) afterwards; OTA1/OTA2 output CM within ±50 mV of V_OCM at each conversion start; the first two conversions (u 0.5, −0.3) within the function tolerance | `nosu` (C6 kick removed) | pending | pending |
| (b) DC function | 7 points, ±0.9 FS: \|u_hat − u\| ≤ 0.5 %·\|u\| + 5 µV/VREF + 40e-6 (the 20 ppm FSR INL budget); bits-only code vs golden within that + 2 × the x2 term bound | `dacswap` (stage-1 DAC polarity) | pending | pending |
| (c) INL spot points | the same run: endpoint INL ≤ 1.333 ppm, at tt/27 and ss/−40/3.0 | `ota2dead` (OTA2 bias × 0.1) | pending | pending |
| (d) chop pair | pairs (A,B) without and (C,D) with a +2 mV bench offset at OTA1's input, B and D swapped: the pair shift is ≤ 5 µV, the offset is visible (≥ 50 µV), and pair(A,B) is within the function tolerance of u 0.3 | `noswap` (swap pin held low) | pending | pending |
| (e) overload / recovery | ±1.1 VREF conversions read ≥ 0.95 / ≤ −0.95; the conversions after them agree with the references before them (0.5 and −0.5) within 1 ppm FSR | `noreset` (no per-conversion reset) | pending | pending |

The (d) gate cancels a bench offset only. The transistor deck has no mismatch, so the OTA's own offset is about 0.

## Runtime and corner plan
The runtime per conversion is still to be measured (smoke: `gsmoke_*.json` field `sec_per_conv`, N 16).
- Planned gate pool, 10 jobs at PRIO=high: one 2-conversion job; two 8-conversion jobs (bc m 7); two 4-conversion jobs; two 5-conversion jobs (d); and two 7-conversion jobs (e). A conversion takes 513.5 µs of simulated time.
- Corner pool at PRIO=low: a, d, e at ss/−40/3.0.
- Fitting about 3 days on 5 slots: once `sec_per_conv` is known, the budget is ≈ 3 × 86 400 × 5 / sec_per_conv conversions in total. Rank the corners as follows:
  1. ss/−40 bc (queued);
  2. ff/−40/3.6 bc;
  3. ss/125 bc (needs the C6 gmin 1e-11 rule from WO-87 for the 125 °C ramp);
  4. fs/125 and sf/125 bc at m 5.
- If one conversion takes more than about 2 h, split the bc decks with the gate-B `--part` scheme (endpoints in every slice).

## Next mode (after precision passes)
- boost / 4 MHz needs the boost geometry (`NL.build(boost=True)`, `bias_currents(True)`, the C6 boost leg). These are not in the bench yet; the WO-99 C6 subckt is meant to provide them.
- Then N 64 and N 256 at 4 MHz against the SPEC 200 / 20 ppm gates.
- Switch the deck to `design/xschem/sd_mod_top.spice` (WO-94, a9a416f) once WO-99 adds the C6 mirrors, trim, boost and the Cint2 reset. The netlist-equivalence check covers the switch.

## Pickup (sandbox)
```
ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox
F=/home/mempool/regr/tt/WO-95-b4b44f4
ls $F/out/SMOKE_OK $F/out/SMOKE_FAIL; tail $F/out/smoke/smoke.txt        # smoke verdict + sec_per_conv
cat $F/out/gates/pool/pool.status; ls $F/out/gates/pool/POOL_DONE         # gate pool (started by run_wo95.sh after SMOKE_OK)
grep -h "VERDICT\|broken copy" $F/out/*/*/run.txt $F/out/*/run.txt 2>/dev/null
# relaunch after a stop (skips finished jobs):
cd $F/out/gates && PRIO=high SKIPDONE=1 setsid nohup bash $F/scripts/lpool.sh $F/out/gates/jobs.txt $F/out/gates/pool >/dev/null 2>&1 </dev/null &
# if SMOKE_FAIL: read $F/out/smoke/*.log, fix top_bench.py, refreeze at the new sha, rerun the smoke, then run_wo95.sh
```
