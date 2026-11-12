# C3 comparator: design note (WO-44, stage 1 of the block recipe)

Status: draft for `sd-adc-design-reviewer`, before any golden netlist. Spot-sim numbers: `work/v1-design/results/wo44/README.md`.
Sources: SPEC §3.0 rows 105–108, §3.2, §3.7a(a), §3.8a port contract (CL-23, CL-25), PLAN Stage C row C3 and the C3 review addition, LEARNINGS-pthomas-2026-11-10, `repos/sd-analog/ttsky-sigma-delta/sim/comp_{tb,mc}.py` (read only).

## 0. Targets (SPEC §3.0 governs)
| Row | Limit | Where it bites |
|---|---|---|
| 105 offset / noise | ≤ 20 mV 3σ; ≤ 5 mV rms | input-pair + latch area |
| 106 decision time | < 34 ns at 4 MHz (0.3·t_half, t_half 112.5 ns), < 68 ns at 2 MHz, \|Vin\| ≥ 1 mV, worst corner | latch gm/C at ss/−40/VDPWR 1.62 V |
| 107 single bit | one retimed FF (C9) drives DAC and decimator; y[0] forced | interface only (C9 owns the FF and the force) |
| 108 kickback | ≤ 5 mV on x2, recovered within 0.5·t_half at 4 MHz ss/−40 | input-pair Cgs/Cgd vs x2 node impedance |
| PLAN C3 add. | Δ = 0 at 4 MHz ss/−40; P(DAC ≠ decimator); numeric kickback gate | metastability, phase plan |

The comparator input is x2 (order 2) or x1 (order 1, int2 in reset), differential, CM = V_OCM = 1.50 V on VAPWR 3.0–3.6 V; normal swing ≈ ±0.3 V per side (x2 peak ≈ 1.2 V diff), overload / power-up up to the rails.

## 1. Topology
**Choice (recommended): NMOS-input StrongARM on VDPWR (1.8 V), no static preamp, HV input pair and tail, 1.8 V core latch, two inverter buffers per side, cross-coupled NAND SR latch.**

```
x2p ─ M1 (HV)   M2 (HV) ─ x2n        clk high = evaluate, clk low = precharge (4 PMOS to VDPWR: op, on, dp, dn)
        dp ───────── dn
        M3/M4 NMOS cross-coupled (src on dp/dn), M5/M6 PMOS cross-coupled → op / on
        tail T (HV) gate = clk
op → inv → inv → ob2 ┐ NAND SR  → q  (q = 1 ⇔ x2p > x2n)          q / qb → C9 retime FF (falling bit-clock edge, CL-23)
on → inv → inv → nb2 ┘ latch    → qb
```

| Option | For | Against |
|---|---|---|
| **A. StrongARM on VDPWR, HV input pair + tail (recommended)** | output and clock already in the 1.8 V domain: no level shifter on the bit path (one less delay, one less failure point); dynamic current only (≈ µA, from VDPWR, outside the 200 µA analog budget); HV gates survive x2 at VAPWR (D40) | the HV pair has **no Vth mismatch in the PDK** (§3.6), so MC needs injected offsets; HV pair is larger (Cgs, kickback); comparator ground shared with the noisy 1.8 V supply (harmless: noise/offset rows are loose, x2 is the integrated signal) |
| B. All-HV StrongARM on VAPWR (pthomas style) | single domain with the analog core | 3.3→1.8 V down-shifter on q and 1.8→3.3 V up-shifter on clk (two edges in the bit path, his 545 ps edge lesson); slower, larger; its current counts against 200 µA |
| C. 1.8 V input pair | PDK MC covers it; smaller | gate sees x2 up to VAPWR on overload/power-up: violates D40 (1.98 V); would need clamps that add leakage/kickback on x2 |
| Static preamp (any) | kickback isolation, lower offset | 10–30 µA static against a budget already at 189/200 µA fast-mode worst case (D46c); rows 105/106 do not need the gain |

Why HV tail too: with clk low the tail is off and node `tl` follows x2 − Vth; with x2 at VAPWR that is ≈ 2.6 V on a 1.8 V tail drain. The input-pair drains dp/dn are bounded by VDPWR (precharge PMOS), so M3–M6 and the buffers stay 1.8 V devices.

Latch: buffers (not the latch gates) load op/on, and both buffer outputs are high during precharge whatever the held state, so the loading is symmetric (pthomas: NAND latch directly on the regeneration nodes gave ≈ 10 mV-equivalent hysteresis). NAND with both inputs high = hold, so q/qb keep the last decision through precharge, which is what the C9 FF samples.

## 2. Timing and the C9 interface (CL-23, CL-25)
- C9 samples q on the **falling** bit-clock edge (end of ph1); the DAC flop (the one F8 FF) updates on the next rising edge. C3 needs only that q is settled before that edge: t_fire + t_dec + t_SR + t_su ≤ t_sample.
- The comparator clock is a C4 phase (C4 owns the phase generator, CL-25), taken on the 1.8 V side before any up-shifter. Proposal for C4: clk_cmp rises when x2 is final and held (OTA2 not integrating) and stays high until the next OTA2 integration starts; the fire edge sits ≥ 0.4·t_half before the C9 sample edge. **Open item for C4/C2:** confirm in which phase OTA2 holds x2 (D25 puts the Cs2 sample of x1 in OTA1's hold phase); the kickback recovery row assumes x2 is not being sampled by anything else in the 0.5·t_half after the fire and reset edges.
- **Capture-window guarantee (coordinator note, C9 probe: C9 captures `comp_in` on the s_tick = bit-clock falling edge with no synchroniser).** Timing, at every corner: clk_cmp rises at t_fire = t_capture − Δt_fc with **Δt_fc ≥ 0.4·t_half (≥ 45 ns at 4 MHz, ≥ 90 ns at 2 MHz)**; q is final by t_fire + t_dec,max (≤ 3 ns hand, gate < 33.75 ns), i.e. **setup margin ≥ Δt_fc − t_dec,max − t_su ≥ 10 ns**. The NAND SR latch then holds q through the precharge edge (both buffer outputs high = hold) until the next decision, which starts no earlier than the next t_fire = t_capture + T − Δt_fc, so **hold margin ≥ T − Δt_fc ≥ 0.5·T (≥ 125 ns) ≫ 1 ns**. The clk_cmp falling (precharge) edge may fall on either side of t_capture; q does not move on it. C4 must keep Δt_fc within [0.4·t_half, T − 1 ns − t_hold] at every corner (its phase-generator spread).
- No retiming FF inside C3. q also feeds nothing else (single bit, row 107); y[0] force and the cycle-0 junk are C9's (§3.7a a).

## 3. Hand calculations (draft sizes of §5; V_ov,in ≈ 0.5 V at x2 CM 1.5 V)
### 3.1 Offset (row 105: 3σ ≤ 20 mV ⇒ σ ≤ 6.7 mV)
σ_os² ≈ σ_ΔVT,in² + (V_ov,in/2 · σ_Δβ/β)² + (σ_ΔVT,LN/A_n)² + (σ_ΔVT,LP/A_p)², A_n ≈ 2·V_th,n/V_ov,in ≈ 2 (integration gain at latch onset), A_p ≈ 4.

| Term | Basis | Size set A (spot sims: IN 5/0.5 ×4, LN/LP 2/0.3) | Set B (offset margin: IN ×6, LN/LP 4/0.5) |
|---|---|---|---|
| in pair ΔVT | A_VT,HV 12 mV·µm (C1 gating value; 8 optimistic) | 5.4 mV (3.6) | 4.4 mV (2.9) |
| in pair Δβ | 1 %·µm, V_ov/2 = 0.25 V | 1.1 mV | 0.9 mV |
| LN ΔVT / A_n | PDK nfet_01v8 vth0 slope 3.36 (7.36 some bins) mV·µm | 3.1 (6.7) mV | 1.7 (3.7) mV |
| LP ΔVT / A_p | PDK pfet_01v8 5.86–7.36 mV·µm | 2.7–3.4 mV | 1.5–1.8 mV |
| **σ total / 3σ** | | **6.9 mV / 20.5 mV (8.4 / 25 with slope1)** | **5.1 mV / 15 mV (6.1 / 18)** |

Set A is marginal on offset; **recommend set B** for the netlist WO (cost: ≈ 1.5× input Cgs, so ≈ 1.5× kickback CM charge; latch L 0.5 slows regeneration ≈ 2×, still far inside row 106, §3.3). A_n, A_p are rough; MC decides.

### 3.2 Noise (row 105: ≤ 5 mV rms)
Input-pair integration noise: σ_n² ≈ 2·(4kTγ/g_m)·1/(2 t_int); g_m ≈ 1 mS per side at the eval current, t_int ≈ C_d·V_th,n/(I_tail/2) ≈ 0.1–0.3 ns ⇒ **σ_n ≈ 0.3–0.6 mV rms**, ≈ 10× under the row. Latch noise divides by A_n. In-loop it divides by the integrator gains (budget 0.3 µV, SPEC row 105 col 4).

### 3.3 Decision time (row 106)
t_dec ≈ t_int + τ_reg·ln((V_DD/2)/(A_n·Δ)) + t_buf+SR. τ_reg = C_op/g_m,latch ≈ 12 fF / 0.4 mS ≈ 30 ps (tt), ≈ 75 ps at ss/−40/1.62 V. At Δ = 1 mV: ln(450) ≈ 6 ⇒ ≈ 0.2 + 0.2 + 0.2 ≈ 0.6 ns (tt), ≈ 1.5–3 ns (ss/−40/1.62). Margin ≈ 10× to 33.75 ns; set B ≈ 2× slower, still ≈ 5×.

### 3.4 Kickback (row 108)
Per side, the gate charge moved at the fire edge ≈ C_gs·V_ov + C_gd,ov·ΔV_d ≈ (2/3·C_ox·W·L·m)·0.5 V + (W·m·0.25 fF/µm)·1.8 V. Set A (C_ox,HV ≈ 3 fF/µm², 10 µm²): ≈ 10 fC + 9 fC ≈ 19 fC ⇒ **≈ 25–30 mV common mode** on C_X2 = 0.7 pF, both sides alike. The **differential** part comes only from the asymmetric trajectory during regeneration (both dp and dn end at 0 V, so final states match): expected a few mV peak at most. Recovery through the OTA2 closed-loop output resistance R ≈ 1/(β2·g_m2) ≈ 1/(0.497·99 µS) ≈ 20 kΩ (g_m2 = 2π·22.5 MHz·0.7 pF, 4 MHz boost) ⇒ τ ≈ 14 ns, 0.5·t_half = 56 ns = 4τ ⇒ 1.8 % of the peak remains. At 2 MHz base (g_m2 ≈ 44 µS) τ ≈ 32 ns against 0.5·t_half = 112 ns (3.5τ).
- Gate on the differential disturbance (it is what changes the sampled state); CM is reported and handed to C2 (OTA2 CMFB must absorb ≈ 30 mV CM per fire edge to ≤ 10 mV at its sampling instants, CL-10). Recommendation pending the spot numbers: no isolation unless the differential peak is > 2.5 mV (half the limit); if needed, cross-coupled neutralisation (HV dummy pair, gate on the opposite input, S/D on dp/dn) is the cheapest, and then "isolation removed" is the row-108 broken copy as the SPEC words it.

### 3.5 Metastability, Δ = 0, P(DAC ≠ decimator) (PLAN C3, F8)
Unresolved at time t if |Δ| < Δ_crit = (V_DD/2/A_n)·exp(−(t − t_int)/τ_reg). Available t ≥ 0.4·t_half = 45 ns at 4 MHz. Per-decision failure P = 2·Δ_crit·p(0), worst case p(0) = 1/(√(2π)·σ_n) ≈ 800 V⁻¹ (x2 ≈ 0 every cycle, as at cycle 0 after reset).
| τ_reg | Δ_crit | P per decision | MTBF at 4 MHz |
|---|---|---|---|
| 75 ps (hand ss) | ≈ 1e-261 V | ≈ 1e-258 | unbounded |
| 1 ns (13× pessimistic) | ≈ 1e-20 V | ≈ 2e-17 | ≈ 1e10 s (≈ 400 years, every cycle at x2 = 0) |

**P(DAC ≠ decimator):** by construction (F8, row 107) one FF drives both, so they can disagree only if that FF goes metastable, which needs q to change inside its setup/hold window, i.e. the same P as above (≪ 1e-15). The cycle-0 decision (x2 = 0 after reset, the systematic Δ = 0 case) is overridden by the forced y[0] (§3.7a a). Gate proposal (row "meta"): fit t_dec(Δ) at Δ = 1 mV, 100 µV, 10 µV, 1 µV (one process each) at 4 MHz ss/−40/1.62 → τ_reg, t_int; P from the formula ≤ 1e-15 per decision. Δ = 0 exactly is run but reported only: in a symmetric deck the outcome is set by solver noise (LEARNINGS-pthomas: sub-mV verdicts are solver noise).

## 4. Supply, levels, current
- VDPWR 1.62–1.98 V; clk from C4's 1.8 V side; q/qb straight into C9 (no shifter). Input gates on the 3.3 V-domain x2 via HV devices. All 1.8 V terminal pairs ≤ 1.98 V by construction (dp/dn ≤ VDPWR); to be proven in the stress row.
- Current: dynamic only, ≈ C_sw·V_DD·f ≈ (100–200 fF)·1.8 V·4 MHz ≈ 1–2 µA from VDPWR (spot sim reports it).

## 5. Draft sizes (`sizes_draft.py`, set A as simulated in WO-44)
| Device | Type | W/L (µm) × m | Note |
|---|---|---|---|
| M1/M2 input pair | nfet_g5v0d10v5 | 5/0.5 × 4 (set B: × 6) | 5 µm unit fingers (HV width bins) |
| T tail | nfet_g5v0d10v5 | 5/0.5 × 4 | gate = 1.8 V clk |
| M3/M4 latch N | nfet_01v8 | 2/0.3 (B: 4/0.5) | sources on dp/dn |
| M5/M6 latch P | pfet_01v8 | 2/0.3 (B: 4/0.5) | |
| R0–R3 precharge | pfet_01v8 | 1/0.15 | op, on, dp, dn |
| buffers (2/side) | 01v8 | N 0.5/0.15, P 1/0.15 | |
| NAND SR | 01v8 | 1/0.15 | load 5 fF per output (C9 D pin + wire) |

## 6. Testbench plan (next WO, `sim/c3_tb.py`; every row ACCEPT/REJECT, exits nonzero, broken copy must REJECT)
| Row | Stimulus / corners | Gate | Broken copy ⇒ REJECT |
|---|---|---|---|
| T1 polarity (output sense, pthomas Q/QB) | Δ = ±1 mV, CM 1.2/1.5/1.8 V, 45 PVT × VDPWR | q = 1 ⇔ x2p > x2n, q/qb complementary at the C9 sample instant | `qswap` |
| T2 decision time | as T1, 4 MHz and 2 MHz timing | t_dec < 0.3·t_half (33.75 / 67.5 ns) | `starve` (tail 5/8 ×1) |
| T3 offset MC | ≥ 200 tt/27 + ≥ 50 at the worst T2 point; bisection to 0.2 mV, one process per decision point, own `.spiceinit` `rndseed` per sample (comp_mc.py style); **PDK `*_mm` for the 1.8 V devices + injected Gaussian ΔVT on M1/M2 from A_VT,HV 12 mV·µm** (PDK has vth0_slope = 0 for g5v0d10v5) | 3σ ≤ 20 mV and no sample outside ±20 mV·(1+…) reported; spread non-zero and within 0.5–2× of §3.1 (§11.7) | input-pair ΔVT ×3 |
| T4 noise | `.noise` on the frozen integration-phase linearisation (tail at its eval current, latch removed, output dp−dn), integrated over ENBW = 1/(2 t_int) with t_int from T2 | ≤ 5 mV rms | 10 mV rms trnoise injected at inp (chain check); row is ≈ 10× under the limit, reviewer may make it report-only |
| T5 kickback | behavioural x2 per side (R 20 kΩ, 0.7 pF at 4 MHz boost; 46 kΩ at 2 MHz), fire and reset edges, 45 PVT, gate at 4 MHz ss/−40 | diff peak ≤ 5 mV, ≤ 0.5 mV at 0.5·t_half after each edge; CM reported to C2 | isolation removed (if §3.4 adds one), else C_X2/10 |
| T6 metastability | Δ ladder 1 mV…1 µV at 4 MHz ss/−40/1.62, fit τ_reg; Δ = 0 run reported | P(unresolved at the C9 sample) ≤ 1e-15 per decision | `starve` |
| T7 hysteresis / memory | previous decision at ∓0.3 V, then Δ = ±0.5 mV | correct sign every corner | latch gates directly on op/on (buffers removed) |
| T8 device stress | x2 per side 0…VAPWR 3.6 V, both power-up orders | every 1.8 V terminal pair ≤ 1.98 V, HV ≤ 5.5 V | input pair as nfet_01v8 |
| T10 capture window (C9 contract) | full cycles at 4 / 2 MHz, alternating ±1 mV and ±0.3 V decisions, capture edge at t_fire + Δt_fc, 45 PVT | q valid (≥ 0.9·VDD or ≤ 0.1·VDD, correct sign) from t_capture − (t_su + 1 ns) to t_capture + 1 ns, and no glitch > 0.1·VDD on q/qb from t_fire + t_dec to the next t_fire (spans the precharge edge) | latch removed (q = buffered op, transparent: returns to the precharge level at the clk fall) |
| T9 current | 4 MHz, 45 PVT | report (from VDPWR) | — |

Numerical rules for all rows: gear, reltol 1e-5, tmax 1 ps through regeneration, 10 Ω in series with ideal sources, check tstop reached and every `.meas` present (§11.1–2), corner/temperature read back from the log (§11.3), no ideal parts except labelled probes and the behavioural x2 node (§11.6).

## 7. MC plan (WO item 3)
- **PDK check (done, WO-44):** `nfet_01v8` / `pfet_01v8` carry `vth0 = … + MC_MM_SWITCH·AGAUSS(0,1,1)·slope/sqrt(l·w·mult)` (nfet slope 3.356e-3, slope1 7.356e-3; pfet 5.856e-3 / 7.356e-3 / 4.356e-3 V·µm), enabled by the `*_mm` lib sections (`mc_mm_switch=1`). **`nfet_g5v0d10v5` has `vth0_slope = 0.000` ("All devices")**; only toxe mismatch is present (nfet 0.8e-2, pfet 1.2–2.3e-2). The spot probe measures σ(Vgs) per type (results README).
- Consequence: a plain `tt_mm` MC would under-report the input-pair offset (§11.7 "MC that isn't"). T3 adds per-sample ΔVT sources on M1/M2 from A_VT,HV (12 mV·µm, C1's gating value) and keeps the PDK draws for the 1.8 V latch. The same caveat applies to every HV pair in C1/C2 (C1 already uses hand A_VT,HV allotments).
- Sample count / seeds: per sample its own dir and `.spiceinit` (`set rndseed=N`, `num_threads=1`), bisection steps share the seed; parallel through `scripts/lpool.sh`.

## 8. Open items for the reviewer
1. Set A vs B (offset margin vs kickback CM); 2. OTA2 hold phase vs comparator fire/reset edges (C4/C2); 3. whether a kickback isolation element is needed (spot numbers) and so which broken copy row 108 uses; 4. noise row method (`.noise` linearisation proxy); 5. ≈ 30 mV CM kick per fire edge into OTA2's CMFB (C2 interface).
