# WO-98 (C2): OTA2 = 9/16-scaled OTA1 cell (D91), generator and C2 bench. 2026-11-21

Status (updated after run 1): run 1 pool `WO-98-692f8b5` finished (59 jobs). **Rerun of the 21 tran jobs plus 3 fixed copies is running on `WO-98-c0bbaff`** (1 slot, load ~34), launched with PRIO=high and SKIPDONE=1. The opac, toggle and MC results of run 1 are final and were copied into its `out/`.

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

## 4. Run 1 verdicts (frozen copy `WO-98-692f8b5`, summary in `out/summary.txt`)
| row | base (2 MHz) worst | boost (4 MHz) worst | verdict |
|---|---|---|---|
| A0 ≥ 75 dB | 82.0 dB, sf/125 | 80.0 dB, fs/125 | ACCEPT 9/9 in both modes |
| GBW ≥ 10 / 22.5 MHz | 15.3 MHz, fs/125 | 30.1 MHz, fs/125 | ACCEPT 9/9 in both modes |
| PM at β2 0.53 (info) | 74.8°, sf/−40 | 73.0°, sf/−40 | inside the 70–85° window |
| SR = I_tail/0.7 pF ≥ 13.5 / 27 V/µs | 14.9, sf/−40 | 29.8, sf/−40 | ACCEPT (+10 %) |
| Vds − Vdsat ≥ 50 mV | 72 mV | 80 mV | ACCEPT |
| **span ≥ 1.41 V** (static A ≥ 75 dB) | 1.72 V, fs/125 | **1.22 V, fs/125**. ss/125 1.29, ff/125 1.38, sf/125 1.38 | base ACCEPT; **boost REJECT at 4 hot corners** |
| **A(v) ≥ 75 dB, \|v\| ≤ 1.41 V** | 79.6 dB | **70.2 dB, fs/125** | **boost REJECT at 4 hot corners** |
| boost toggle, 0.1 % ≤ 4 µs | 2.38 µs, ss/125 (the HAND estimate was 0.58 µs) | — | ACCEPT 9/9 |
| **offset MC, 3σ and every sample ≤ 9 mV** | tt pooled n 200: **3σ 9.93 mV**, max 8.19 mV, mean −0.25 mV. ss/125 boost: 10.7 mV. ff/−40: ≤ 10.9 mV | — | **REJECT**. The HAND pair alone is 8.6 mV, and the sinks and loads add the rest |
| total current ≤ 200 µA | 98.0 µA, fs/125 (OTA1 58.3 + OTA2 28.2 + 11.46 HAND) | 188.4 µA, fs/125 (117.5 + 56.9 + 13.96): margin 11.6 µA | ACCEPT |
| tran rows (ε, kick, coupling) | — | — | run 1 aborted in all 21 decks ("timestep too small" at a ph2 edge, gear reltol 1e-6 / vntol 1e-9). Rerun: reltol 1e-5, vntol 1e-8, chgtol 1e-16, tmax 0.5 ns, and an abort check that marks the deck INVALID |

Broken copies, run 1:
- **Live:** nc_short (A0 41 dB), C_L ×4 (GBW 11 MHz), tail_half (SR 7.6 V/µs), pair ×3 (27 mV).
- **Blind in run 1, fixed in the rerun:**
  - vocm +0.3 V widened the span at tt base, because the bottom side is the limit. The replacement vocm −0.3 V REJECTs span (1.36 V) and A(v) (73.5 dB), so the swing gate is live.
  - Cbig 300 pF gave 2.98 µs, under the 4 µs limit. It is now 3 nF.
- The 3 tran broken copies are in the rerun.

Findings, as options for the coordinator and the reviewer. No sizes were changed.
1. **Hot-boost swing.** Under the SPEC definition (static A ≥ 75 dB) the boost span is 1.22–1.38 V at the hot corners, against 1.41 V. WO-93 assumed OTA2 inherits OTA1's WO-43 span of 1.43 V. That number may use a different definition (device margins). Run-2 job `opac 3 1 ota1cell` puts the unscaled OTA1 cell in the same slot. Its result separates two causes: the 9/16 scaling, or the definition, in which case OTA1 is affected too.
   - Options: run OTA2 at a lower boost current (it has SR headroom of +10 %); trim V_OCM; or ask for a SPEC ruling on the A(v) definition for OTA2. OTA2's error is divided by the integrator-1 gain, which may justify a relaxed OTA2 A(v) row; that would be a model check.
2. **Offset.** 3σ is 9.93 mV against 9 mV.
   - Options: a larger pair, which costs β2 and Cp (pair 140/0.5 gives about 6.5 mV for the pair term); longer sink/load L; or review the 9 mV row for OTA2. The u error is 1.5·2·Vos2/(c1(N−1)) = 58 µV at 9.9 mV, and the error cancels in the sys pair.
3. The **fast-mode current margin** is 11.6 µA (5.8 %) at worst, better than the HAND 5.1 µA.

## Pickup (run 2)
1. Wait for `/home/mempool/regr/tt/WO-98-c0bbaff/pool/POOL_DONE`. Then run `. env.sh; python design/c2_ota2/c2_bench.py $PWD/out summary`. The out dir already holds the run-1 opac, toggle and MC JSONs.
2. Check:
   - the tran rows (eps, kick_cm, coup1, coup2) and the D-copy floor (`coup1_floor` must be ≪ 1e-5);
   - that the 3 tran broken copies and toggle cbig3n REJECT;
   - the `opac_fs125_b1_ota1cell` span.
3. If tran still aborts, relax further (reltol 1e-4, the tb9 setting). Then rerun with SKIPDONE=1 after deleting the INVALID JSONs.
