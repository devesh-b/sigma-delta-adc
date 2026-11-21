# WO-98 (C2): OTA2 = 9/16-scaled OTA1 cell (D91), generator and C2 bench. 2026-11-21

Status: **the generator is done. The bench is written and queued, but not run yet except for one smoke point.** The full pool (59 jobs) is queued on the sandbox. It is waiting for a global lpool slot: all 5 GMAX slots are held by the WO-77, WO-85 and WO-91 pools, each launched about 42 min before this one, with timeouts of up to 40000 s.

## 1. Generator (item 1)
- **OTA2 subckt for WO-94 / WO-95:** `design/c2_ota2/ota2.spice`, `.subckt ota2` with cmfb="sc". It has the same 24 ports in the same order as `ota1`.
  - The bias ports `ibtp ibn ibp ivbnc ivbpc ivbl0` are INPUTS. Tie them to OTA1's nets of the same names; they are gate-only loads.
  - `chp chn chlp chln` are unused, because OTA2 is not chopped (SPEC). Tie them to a rail.
  - `isl ph1 ph1b ph2 ph2b rstb` work as in ota1: OTA2 has its own SC CMFB phases and start-up clamps.
- Sizes: `design/c2_ota2/sizes_ota2.py`.
  - m_t, m_n and m_pl use 18 of 32 unit fingers; m_pc uses 9 of 16.
  - m_nc is 2 × 5.625/2, m_plc is 4 × 2.1/2, the pair is 10 × 7 / 0.5, and m_pp is 5.625/0.5.
  - The CMFB (Cc, Cr, integrator, C_INT) is as in OTA1.
  - The OTA2 gate-area sum is about 2,100 µm² (HAND).
- Generator: `design/c2_ota2/netlist_ota2.py`. It calls `c1_ota1/netlist.py` with the scaled sizes and drops the 17 bias-leg instances. It asserts that every one of them was found. The chopper positions are wired with 0 V sources.
- OTA1 sizes and code are unchanged.

## 2. Bench (items 2–3): `design/c2_ota2/c2_bench.py`
Every row prints ACCEPT/REJECT. Each OTA2 runs on the bias of a transistor OTA1, with ideal C6 currents into OTA1's references.

| test | what | gate |
|---|---|---|
| opac | A0 and GBW into 0.7 pF; PM at the β2 = 0.53 crossing (info); SR = I_tail(op)/0.7 pF; static A(v) = vo/vid from a DC sweep; span (A ≥ 75 dB); Vds−Vdsat margins; currents | 75 dB; 10 / 22.5 MHz; 13.5 / 27 V/µs; span ≥ 1.41 V; A(v) ≥ 75 dB for \|v\| ≤ 1.41 V; margin ≥ 50 mV |
| tran (sc, clocks at fs) | ε_dyn on the 1.12 V step from ∓0.56 V; SR_tran (info); 10 comparator kicks of 47.4 mV, one per cycle; coupling: systems A (OTA1 steps), B (both step), C (OTA2 steps), plus D, a copy of A at tt, as the numerical floor | ε ≤ 1.4e-3 / 6e-4; CM ≤ 10 mV at the sample; OTA1 Δ ≤ 1e-5 × 0.49 V; OTA2 Δ ≤ 1.4e-4 × 1.12 V |
| toggle | OTA1 references ×2 plus the bank switch (bk/bkb ports added in the bench copy), up and down | OTA2 supply current within 0.1 % in ≤ 4 µs |
| mc | hand-Pelgrom ΔVT on 12 core devices (A_VT 12 mV·µm); 200 samples at tt/27, 50 at ss/125 boost, 50 at ff/−40 | 3σ and every sample ≤ 9 mV |
| summary | worst corner per row; worst total current = OTA1 + OTA2 + 11.46 / 13.96 µA other (HAND, WO-93 §4), against 200 µA; broken-copy verdicts | — |

Broken copies (the `BROKEN` dict, each in its own deck), each against the row it must REJECT:

| broken copy | must REJECT |
|---|---|
| nc_short | A0 and A(v) |
| vocm +0.3 V | span |
| C_L ×4 | boost GBW |
| tail_half | SR and ε |
| cm_open | kick |
| 1 pF from o2p to ibn | coupling |
| Cbig 300 pF on ibtp | toggle |
| pair σ ×3 | offset |

## 3. Results so far
Smoke point, opac at tt/27 base (`opac_tt27_b0.json`), all rows ACCEPT. It ran outside lpool, under nice and timeout.

| row | value |
|---|---|
| A0 | 84.4 dB |
| GBW | 18.8 MHz |
| PM | 77.7° (info) |
| SR (I_tail 10.60 µA / 0.7 pF) | 15.1 V/µs |
| span | 2.03 V |
| A(v) min | 82.8 dB |
| min margin | 0.105 V (mn1) |
| OTA1 current | 57.7 µA |
| OTA2 current | 27.9 µA |
| precision total at tt | ≈ 97.1 µA (HAND others included) |

The other 8 corners, boost, tran, toggle and MC are pending.

Expected risk from the HAND numbers in the project's Pelgrom convention (σ per device = A/√(WL)): the pair alone is 3·12 mV·µm·√(2/35) = 8.6 mV 3σ, against the 9 mV limit. WO-93's 6.4 mV figure used a different base. The offset row may fail. At A_VT 8 mV·µm it scales to about 5.7 mV.

Item 4 (in-loop gate B with transistor OTA1 + OTA2) is **not done**. `design/tier1/gen_tier1.py` has only an `ota1_xtor` hook, and that file is outside the WO-98 write scope. It needs an `ota2_xtor` hook, either in a separate WO or with coordinator OK.

## Pickup
1. Frozen copy: `/home/mempool/regr/tt/WO-98-692f8b5`. Source the env with `. env.sh`. The pool logs are in `pool/` and the outputs in `out/`. The marker is `pool/POOL_DONE`.
2. If the pool never started or was killed, relaunch it in that directory:
   ```
   PRIO=high SKIPDONE=1 setsid nohup bash scripts/lpool.sh jobs.txt pool > pool.log 2>&1 < /dev/null &
   ```
3. Read the first 9 jobs first (the broken copies): `grep -h 'ACCEPT\|REJECT\|INVALID\|Traceback' pool/job_{1..9}.log`. The tran, toggle and mc paths have not been executed yet, so check them for script errors. If a fix is needed, commit it, make a new frozen copy and rerun only the failed jobs.
4. Run `python design/c2_ota2/c2_bench.py $PWD/out summary`. Copy `summary.txt` and the JSONs here, and fill in §3.

## Ready for review (`sd-adc-design-reviewer`)
- The sizes and the dropped bias legs; the ivbl0 replica density match (OTA1 V_BL0 finger vs OTA2 m_plc, 0.4 %).
- The CT bench model of the OTA2 slot (Cs2/Ck2/Cint2 + 0.07 pF) versus the real SC phases.
- The coupling metric and its limits (1e-5 / 1.4e-4, set as 10 % of the OTA1 health and OTA2 ε rows).
- The toggle bench: the DC-CMFB R stays at the 2 MHz value through the boost edge.
- The offset row against the 9 mV limit (HAND pair 8.6 mV 3σ).
- Item 4 hook scope.
