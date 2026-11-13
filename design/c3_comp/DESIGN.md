# C3 comparator: design note (rev b, WO-48; D74 applied)

Status: revised after REVIEW-C3a (verdict REVISE, then netlist) and user decision D74. Netlist generator `netlist.py` (golden subckt), sizes `sizes_draft.py` (set A′), testbench `c3_tb.py`. Results: `work/v1-design/results/wo48/`. WO-44 spot numbers (set A): `work/v1-design/results/wo44/`.
Sources: SPEC §3.0 rows 105–108, §3.2, §3.8a (CL-23, CL-25), D40, D66, D67, D74, REVIEW-C3a, `design/c9_digital/HARDENING.md` §6, `design/c4_sw/DESIGN.md` §1, LEARNINGS-pthomas-2026-11-10.

## 0. Targets (SPEC §3.0 governs)
| Row | Limit | Where it bites |
|---|---|---|
| 105 offset / noise | ≤ 20 mV 3σ; ≤ 5 mV rms | input-pair + latch area. **Soft**: system chop removes the constant offset (REVIEW-C3a 2) |
| 106 decision time | < 34 ns at 4 MHz (0.3·t_half, t_half 112.5 ns), < 68 ns at 2 MHz, \|Vin\| ≥ 1 mV, worst corner | latch gm/C at ss/−40/VDPWR 1.62 V |
| 107 single bit | one FF (C9) drives DAC and decimator; y[0] forced | interface only (C9 owns the FF and the force) |
| 108 kickback | ≤ 5 mV on x2, recovered within 0.5·t_half at 4 MHz ss/−40 | input-pair Cgs/Cgd vs x2 node impedance |
| PLAN C3 add. | Δ ≈ 0 at 4 MHz ss/−40; P(DAC ≠ decimator); numeric kickback gate | metastability, phase plan |

Comparator input: **always x2** (D74, both orders, no mux), differential, CM = V_OCM = 1.50 V on VAPWR 3.0–3.6 V; normal swing ≈ ±0.3 V per side, overload / power-up from below ground (−0.5 V) to VAPWR. In order 1, integrator 2 works as a follower / per-cycle reset (x2 = k·x1 each cycle, C4 `rst2_o1` late in φS after the decision, C2 owns it); C3 sees no difference.

## 1. Topology
**NMOS-input StrongARM on VDPWR (1.8 V), no static preamp; HV (g5v0d10v5) input pair, 1.8 V tail, 1.8 V latch, two inverter buffers per side, cross-coupled NAND SR latch, two-inverter output buffer per side.**

```
x2p ─ M1 (HV)   M2 (HV) ─ x2n        clk = φC strobe: high = evaluate, low = precharge (4 PMOS to VDPWR: op, on, dp, dn)
        dp ───────── dn
        M3/M4 NMOS cross-coupled (src on dp/dn), M5/M6 PMOS cross-coupled → op / on
        tail T (1.8 V nfet_01v8) gate = clk, drain tl
op → inv → inv → ob2 ┐ NAND SR → ql → inv → inv → q   (q = 1 ⇔ x2p > x2n)   q / qb → C9 DAC flop D, captured on fs_tick (D74)
on → inv → inv → nb2 ┘ latch   → qlb → inv → inv → qb
```

| Option | For | Against |
|---|---|---|
| **A. StrongARM on VDPWR, HV input pair, 1.8 V tail (chosen, D74)** | output and strobe in the 1.8 V domain: no level shifter in the bit path; dynamic current only (≈ 0.7 µA from VDPWR, outside the 200 µA analog budget); HV gates survive x2 at VAPWR | HV pair has no Vth mismatch in the PDK (§7), so MC injects it; larger pair (Cgs, kickback); **exception to D40(a)** (user OK, D74) |
| B. All-HV StrongARM on VAPWR (pthomas style) | single domain with the analog core | down- and up-shifters on q and clk; slower; its current counts against 200 µA |
| C. 1.8 V input pair | PDK MC covers it | gate sees x2 up to VAPWR: violates D40 (T8 broken copy `in18`) |
| Static preamp | kickback isolation, lower offset | 10–30 µA static against a 189/200 µA worst case (D46c); rows 105/106 do not need it |

**Rev d (WO-56) supersedes this paragraph:** with the cascode the pair drains no longer sit at VDPWR, so the tail is HV and the cascode nodes are precharged (§4b). Original rev b reasoning, kept for the record. **Why the tail is 1.8 V (D74, REVIEW-C3a 4):** with clk low, dp/dn are precharged to VDPWR and M1/M2 act as source followers onto `tl` from drains at VDPWR, so tl ≤ VDPWR whatever x2 does; the tail sees ≤ VDPWR on every terminal pair. A 1.8 V gate on a 1.8 V strobe gives more overdrive than the HV tail of rev a. The pair gates still need HV (Vgs up to VAPWR + 0.5 V at overload). T8 proves both.

**Latch / buffers:** buffers (not the latch gates) load op/on, and both buffer outputs are high in precharge whatever the held state, so the loading is symmetric (pthomas: NAND latch directly on op/on gave ≈ 10 mV-equivalent hysteresis; T7 broken copy `nobuf`). NAND with both inputs high = hold, so q/qb keep the decision through precharge until the next strobe. **Output buffer (REVIEW-C3a 7):** 0.5/1 then 2/4 inverters per side drive the routed q net; the tb load is 100 fF (≈ 300 µm met2 + D pin, rounded up) instead of the optimistic 5 fF of rev a, and the latch no longer sees the routed load.

## 2. Timing and the C9 interface (D74, supersedes CL-23 / D66 AMB-01 for the comparator)
- Clock: TT clk 48 MHz; fs = clk/12 (4 MHz, T = 250 ns) or clk/24 (2 MHz). The bit-clock rising edge (C9 `fs_tick`) starts φI; t_half = 0.45·T, I↔S gaps g = 0.05·T (C4 §1).
- **Strobe φC in φS:** C4 derives it from the φSe rising edge, i.e. t_fire = t_n + T/2 + g + ≈ 1 ns (x2 final and held: OTA2 in hold through φS). It falls (precharge) at the end of φS, before the next fs edge; q is held by the SR latch.
- **Capture:** C9 latches comp_in straight into the DAC flop on the next `fs_tick` (clk edge at t_n + T); comp_s (falling-edge flop) is removed; one flop drives DAC and decimator (F8, row 107). C4 applies y in that cycle's φI: loop delay = the tier-1 deck.
- **Margins (every corner):** setup = t_cap − (t_fire + t_dec) ≈ T/2 − g − 1 ns − t_dec ≈ 110 ns − t_dec at 4 MHz (≈ 220 ns at 2 MHz); with t_dec < 34 ns, ≥ 75 ns. Hold = next t_fire + t_dec,min − t_cap ≈ T/2 + g ≫ 1 ns (F-IF-1 min delay clk→comp_in ≥ 1 ns holds by construction: q never moves within T/2 of a capture edge).
- **T10** checks this on the C9 clock grid: q, qb valid and correct from t_cap − (t_su + 1 ns) to t_cap + t_h + 1 ns (t_su = t_h = 1 ns), no glitch > 0.1·VDD from t_fire + 0.3·t_half to the next t_fire (spans the precharge edge), and at near-zero Δ (±1 µV) q and qb never both high at capture. Broken copies: strobe in φI (wrong phase; reads the previous x2), latch removed (transparent: q = qb = 1 in precharge).
- No retiming FF inside C3; q feeds nothing else; y[0] force and the cycle-0 junk belong to C9 (§3.7a a).

## 3. Hand calculations (set A′; V_ov,in ≈ 0.5 V at x2 CM 1.5 V)
### 3.1 Offset (row 105: 3σ ≤ 20 mV ⇒ σ ≤ 6.7 mV); basis D74: A_VT,HV = 12 mV·µm **in total**
σ_os² ≈ σ_ΔVT,in² + (V_ov,in/2·σ_Δβ/β)² + (σ_ΔVT,LN/A_n)² + (σ_ΔVT,LP/A_p)², A_n ≈ 2, A_p ≈ 4.

| Term | Basis | Set A′ (IN 5/0.5 ×4, LN/LP 4/0.5) |
|---|---|---|
| in pair ΔVT | 12 mV·µm total (D74), 10 µm² per side | 5.4 mV |
| in pair Δβ | 1 %·µm, V_ov/2 = 0.25 V | 1.1 mV |
| LN ΔVT / A_n | nfet_01v8 3.36 (7.36) mV·µm, 2 µm² | 1.2 (2.6) mV |
| LP ΔVT / A_p | pfet_01v8 5.86 (7.36) mV·µm | 1.0 (1.3) mV |
| **σ / 3σ** | | **≈ 5.9 mV / 17.7 mV (20.5 with slope1)**, REVIEW-C3a 2 |

The rev-a MC plan double counted: the PDK `tt_mm` already gives the HV pair ≈ 9.3 mV·µm equivalent (toxe, WO-44 probe), and adding 12 RSS gave ≈ 15.2. **T3 now injects √(12² − 9.3²) ≈ 7.6 mV·µm** per device on top of `tt_mm` / `ss_mm` (differential σ_inj = √2·7.6/√10 ≈ 3.4 mV), so the pair totals 12.

### 3.1b Offset limit from loop impact (D75, WO-51; replaces the fixed 20 mV 3σ)
Script `offset_loop.py` (model/iadc.py, v1 loop: order 2, c1 0.125, c2 0.5, k 0.5, VREF 2.048 V; `comp_offset` adds to x2 at the decision; u over ±0.9 FS, 4001 points; OTAs ideal and A0 80 dB falling to 75 dB at 1.4 V diff). Results `work/v1-design/results/wo51/offset_loop.json`.

**(a) x2 headroom.** The offset moves the x2 level at which the loop switches, so x2 swings around −Vos instead of 0.

| Vos (mV) | 0 | ±15 | ±45 | 90 | 135 | 200 |
|---|---|---|---|---|---|---|
| peak \|x2\| diff, N 1024, ideal (V) | 1.237 | 1.408 | 1.408 | 1.408 | 1.435 | 1.664 |
| same, A 80→75 dB | 1.219 | 1.405 | 1.405 | 1.404 | 1.431 | 1.659 |

- The peak is flat at ≈ 1.41 V for every non-zero |Vos| ≤ 90 mV; 1.24 V at exactly 0 is a grid artefact of the tie-break (dec ≥ 0 ⇒ +1), which any offset or noise removes. It starts to grow between 90 and 135 mV (+27 mV at 135, +256 mV at 200).
- **Limit (a): |μ| + 3σ ≤ 60 mV** = 2/3 of the last verified-flat point (90 mV); the 90–135 mV interval is not resolved, hence the margin.
- **Finding for C2 (not a C3 limit):** the realistic x2 peak is ≈ 1.41 V diff, not 1.21 V. That is at the edge of the 1.4 V A ≥ 75 dB range (OTA DC-gain row), independent of the comparator offset. OTA2 swing is to be rechecked against 1.41 V.

**(b) Chop residue.** The constant part cancels in the system-chop pair; what is left is the change in the quantisation pattern.

| | N 1024 | N 4096 |
|---|---|---|
| unchopped mean shift at 45 mV (removed by chop) | 1.32 µV (1.53 with A 80→75) | 0.09 µV (0.13) |
| chopped mean shift, any Vos ≤ 200 mV | 0 (≤ 0.001 µV) | 0 |
| max smoothed residue (101-point window), Vos 15–200 mV, ideal | 0.89–1.39 µV (≤ 0.34 ppm FS) | 0.04–0.11 µV (≤ 0.027 ppm) |
| same, A 80→75 dB | 1.39–3.02 µV (≤ 0.74 ppm, at 45 mV) | 0.08–0.22 µV (≤ 0.055 ppm) |

- The residue does not grow with Vos (15 mV gives the same order as 200 mV). It is the floor of the metric: two ±1-LSB sawtooth patterns (55–62 µV p-p at N 1024) that differ only in phase, averaged over a finite window. So it is an upper bound, not an offset effect. On silicon, thermal noise dithers the pattern.
- **Limit (b):** residue ≤ 1 ppm FS, the INL share of this row. It holds at any Vos up to 200 mV (worst 0.74 ppm at N 1024, 0.055 ppm at N 4096), so (a) sets the limit.

**New row 105 (offset): |μ| + 3σ ≤ 60 mV and every MC sample ≤ 60 mV, at tt/27 (≥ 200) and ss/−40 (≥ 50)**, plausibility σ within [0.5, 2]× the sensitivity estimate (§3.1c). Broken copy: HV-pair A_VT ×6 (72 mV·µm total) ⇒ REJECT. ×3 (≈ 62 mV in WO-48) sits at the limit, so it is kept as an info copy only. Re-judged WO-48 MC against 60 mV: tt σ 14.4 mV, |μ| + 3σ 44.8 mV ⇒ ACCEPT (ss/−40: 45.0 ⇒ ACCEPT). Max |x| was clipped at the ±40 mV bisection range, which is why the range is now ±200 mV at 0.1 mV.

### 3.2 Noise (row 105: ≤ 5 mV rms) — T4 is report-only (REVIEW-C3a 6)
Input-pair integration noise: σ_n² ≈ 2·(4kTγ/g_m)·1/(2 t_int); g_m ≈ 1 mS per side, t_int ≈ C_d·V_th,n/(I_tail/2) ≈ 0.1–0.3 ns ⇒ **σ_n ≈ 0.3–0.6 mV rms, ≈ 10× under the row**; latch noise divides by A_n; in-loop it divides by the integrator gains. `.noise` on a frozen linearisation is a poor proxy for a regenerative comparator, so no sim gate.

### 3.3 Decision time (row 106)
t_dec ≈ t_int + τ_reg·ln((V_DD/2)/(A_n·Δ)) + t_buf+SR+outbuf. Set A spot (WO-44): 0.35 ns tt, 1.12 ns ss/−40/1.62 at 1 mV. Set A′ latch L 0.5 (≈ 2× τ_reg) plus the output buffer on 100 fF: expect ≈ 2–3 ns at ss/−40. Requirement row T2 (< 33.75 ns) has ≈ 10× margin and cannot see a starved comparator (REVIEW-C3a 3), so **T2band** gates t_dec(1 mV, ss/−40/1.62, 4 MHz) within [0.5, 3]× the WO-44 spot value (0.56–3.36 ns); broken copies: tail starved 64× (band), strobe level 0.6 V (requirement row).

### 3.4 Kickback (row 108)
CM kick per fire edge ≈ 45 mV (WO-44, set A pair; A′ keeps the pair, so unchanged); differential ≤ 1.9 mV (reset edge). Recovery through R ≈ 1/(β2·g_m2) ≈ 20 kΩ with 0.7 pF (τ ≈ 14 ns; 46 kΩ at 2 MHz). No isolation element; row-108 broken copy = C_X2/10. **Asymmetric x2 (REVIEW-C3a 5):** ±10 % R/C per side converts part of the CM kick to differential; T5 runs it and reports CM recovery. The 45 mV CM kick causes no state error in order 2; open C2 items: OTA2 output headroom (45 mV) and comparator input CM range at the fire instant (T1 covers CM 1.2 / 1.8 V).

### 3.4b Asymmetric kickback (WO-51 item 3)
**Mechanism.** The fire edge pulls both pair sources (tl) down; Cgs of the 20 µm HV pair kicks both x2 sides by the same charge Q. The CM kick is ≈ 41–45 mV. With per-side C_X2 = (1 ± δc)·C, the differential kick is ≈ 2δc·V_cm,kick; ±10 % gives 0.2 × 41 mV ≈ 8.2 mV, as measured (7.7 / 8.2 mV). Recovery: τ_p ≠ τ_n when R differs, so at 0.5·t_half (≈ 4τ) the two CM tails no longer cancel: 41 mV × (e^{−56/16.9} − e^{−56/11.3}) ≈ 1.2 mV, as measured (1.18 / 1.10 mV). The symmetric case shows 0.001 mV. It is CM-to-DM conversion through the x2 node impedance, not a comparator asymmetry.
**Is ±10 % realistic?** No. Per side, x2 is the OTA2 output in closed loop. Its C is the MIM Cint2/load plus routing: MIM matching is ≲ 0.5 % and routing is symmetric by layout, so take ±1 %. Its R ≈ 1/(β2·gm) per side, where the gm mismatch of the OTA2 input/output devices is a few % 3σ, so take ±5 %. The gate deck uses R ±5 %, C ±1 %; ±10 % stays as an info copy. Expected under that gate: diff peak ≈ 2.7 mV (symmetric reset-edge diff) + 0.02 × 41 ≈ 0.8 mV, recovery ≈ 0.1 × 4 × 41 × e^{−4} ≈ 0.3 mV.
**Gain-only?** The kick charge is the same each cycle (CM, set by tl and the pair), and OTA2 is in hold, so x2 recovers to the held value: no state change once recovered (the recovery row checks this). What does not recover by 0.5·t_half is a constant per-cycle error at the decision instant: a fixed comparator-offset-like term, which the chop removes (§3.1b).
**Fix options (not applied, cost stated):** (1) halve the HV pair (5/0.5 ×2): CM kick ≈ ½, so the ±10 % diff ≈ 4 mV; pair offset term √2× larger (5.4 → 7.6 mV σ hand), allowed by the 60 mV row; ≈ 0 area/current cost. (2) A neutralisation pair (cross-coupled dummy HV devices, drains on the opposite tl node) cancels the CM kick to first order: 2 HV devices per side, ≈ +20 µm² and some extra Cgs on x2. (3) A static preamp isolates fully: 10–30 µA against the 189/200 µA budget (D46c); rejected. A cascode does not help: the kick is through Cgs, not Cgd.

### 3.5 Metastability, Δ ≈ 0, P(DAC ≠ decimator)
Unresolved at t if |Δ| < Δ_crit = (V_DD/2/A_n)·exp(−(t − t_int)/τ_reg). Available time ≈ 75 ns (§2) at 4 MHz. Even with τ_reg 1 ns (13× pessimistic), P per decision ≈ 2e-17 at p(0) = 800 V⁻¹. One FF drives DAC and decimator, so they disagree only if that FF goes metastable; q never moves within T/2 of the capture edge. Cycle 0 (x2 = 0) is overridden by the forced y[0]. T10nz runs ±1 µV cycles and checks valid, complementary q/qb at capture (Δ = 0 exactly is solver noise, LEARNINGS-pthomas).

## 4. Supply, levels, current
VDPWR 1.62–1.98 V; strobe from C4's 1.8 V side; q/qb straight into C9 (no shifter). All 1.8 V terminal pairs ≤ 1.98 V by construction (dp/dn, tl ≤ VDPWR), proven by T8 over both power-up orders and x2 from −0.5 V to 3.6 V. Current: dynamic only, ≈ 0.5–0.8 µA from VDPWR at 4 MHz (WO-44), T9 reports it.

### 4b. Rev d (WO-56): cascode-node precharge and HV tail
**Rev c (WO-51)** put an HV cascode K1/K2 (gate = VDPWR) between the pair drains ap/an and dp/dn. Two faults followed:
1. **Memory (T2/T7/T10 REJECT at every corner).** ap/an had no precharge. In reset they charged only through K1/K2 towards VDPWR − VT,HV, and the last part of that runs in subthreshold, so it does not settle within a 250 ns period. After a ±0.3 V decision one node was pulled to ≈ tl and the other was not, so the next strobe started with ap ≠ an. The lower node turns its cascode on first, which favours the previous decision. The −0.5 mV and +0.5 mV cycles that follow a big one (c1, c4) then read the wrong sign, and q only moves on the next big cycle, which is why t_dec shows ≈ 500 / 250 ns. CM 1.8 V passed because with more pair overdrive both nodes are pulled to tl in every decision. Evidence: the `cyc` probe `ap_an_pre_fire_mV` (ap − an 0.2 ns before each fire) on `cyc_info_revc_*` vs rev d (results/wo56).
2. **T8 moved to the tail (2.38–2.55 V, `st_t_ds`).** tl is the common source of the pair. In rev b it followed dp/dn, which the precharge PMOS drain diode clamps at ≈ VDPWR + 0.4 V. In rev c the pair drains are the floating cascode nodes, so with x2 high tl followed ap/an up and the 1.8 V tail saw it.

**Options compared (item 2):**
| Option | For | Against | Verdict |
|---|---|---|---|
| **Fix the cascode: HV PMOS precharge of ap/an (gate = strobe) + HV tail (chosen)** | ap/an start each strobe equal and at VDPWR (no memory); tl, ap, an touch only HV devices, so no 1.8 V terminal can see x2; dp/dn stay behind the cascode | 2 HV PMOS (2/0.5) + tail HV 5/0.5 ×4 (≈ 10 µm² more); the HV tail has a higher VT, so W/L goes 16 → 40 to keep t_dec in the T2band | chosen |
| Self-biased / precharged cascode gate only | no new devices on ap/an | leaves ap/an floating → memory stays; does not bound tl → T8 stays | rejected |
| Input series R + clamp | protects any core | x2 is a 3.3 V-domain node that normally sits at 1.5 ± 0.7 V; a clamp to VDPWR would clip the normal swing, a clamp to VAPWR does not protect 1.8 V devices; series R adds τ to the kick recovery (row 108) | rejected |
| Fully HV StrongARM | no 1.8 V device near x2 | HV latch at 1.62 V: VT,HV ≈ 0.7–1 V leaves little overdrive, t_dec and T2band at risk at ss/−40; needs a 1.8 V output stage anyway | not needed |
| Stress-aware sequencing | no circuit change | TT supplies are external, power-up order is not ours; overload (x2 at VAPWR) also happens in operation | rejected |

T8 then needs every 1.8 V terminal pair ≤ 1.98 V with the gate stimulus (OTA2 slew, φI only), both orders, tt/27 and ff/−40; `in18` stays the broken copy; `nocas` (rev b) and `revc` (rev c) are info copies.

## 5. Sizes (`sizes_draft.py`, set A′, D74)
| Device | Type | W/L (µm) × m | Note |
|---|---|---|---|
| M1/M2 input pair | nfet_g5v0d10v5 | 5/0.5 × 4 | set A pair (CM kick ≈ 45 mV) |
| T tail | nfet_g5v0d10v5 | 5/0.5 × 4 | HV since rev d (WO-56, §4b); rev b/c: nfet_01v8 4/0.5 × 2 |
| K1/K2 cascode | nfet_g5v0d10v5 | 5/0.5 × 4 | gate = VDPWR (WO-51) |
| P1/P2 ap/an precharge | pfet_g5v0d10v5 | 2/0.5 | gate = strobe (WO-56) |
| M3/M4 latch N | nfet_01v8 | 4/0.5 | set B latch |
| M5/M6 latch P | pfet_01v8 | 4/0.5 | set B latch |
| R0–R3 precharge | pfet_01v8 | 1/0.15 | op, on, dp, dn |
| op/on buffers (2/side) | 01v8 | N 0.5/0.15, P 1/0.15 | |
| NAND SR | 01v8 | 1/0.15 | |
| output buffer (2/side) | 01v8 | N 0.5/0.15, P 1/0.15; then N 2/0.15, P 4/0.15 | drives ≈ 100 fF routed q |

## 6. Testbench (`c3_tb.py`; every row ACCEPT/REJECT, exit nonzero; every row has a broken copy that must REJECT)
| Row | Deck / stimulus / corners | Gate | Broken copy ⇒ REJECT |
|---|---|---|---|
| T1 polarity | `cyc`: 8 full fs cycles on the 48 MHz grid, x2 steps at φI start through R_X2/C_X2, sequence +0.3 V, −0.5 mV, +1 mV, −0.3 V, +0.5 mV, −1 mV, ±1 µV; 9 PVT at 4 MHz CM 1.5; ss/−40 CM 1.2, 1.8 and 2 MHz | q = 1 ⇔ x2 > 0 at capture (rails 0.9/0.1·VDD) | `qswap` |
| T2 decision time (requirement) | `cyc`, every non-zero cycle | 0 < t_dec < 0.3·t_half | strobe level 0.6 V (weak strobe, physical) |
| T2band | `one`: single fire at 1 mV, ss/−40/1.62, 4 MHz (WO-44 spot conditions) | t_dec ∈ [0.5, 3]× 1.12 ns | `starve` (tail 1/4, 64× less W/L) |
| T3 offset MC | `mc`: 25 instances per deck, bisection in ngspice (12 steps, ±200 mV, 0.1 mV), own rndseed; 200 at tt_mm/27/1.8, 50 at ss_mm/−40/1.62; + injected 7.6 mV·µm per HV device. `sens` (per-device dVT sensitivity, tt) + `pdk` (σ(Vgs) per device type, tt_mm, 60 each) give σ_est (§3.1c) | \|μ\| + 3σ ≤ 60 mV (D75, §3.1b), every sample ≤ 60 mV, no clipped sample, σ within [0.5, 2]× σ_est (§11.7) | pair A_VT ×6 (72 total); ×3 info |
| T4 noise | hand calc §3.2 | report only (REVIEW-C3a 6) | — |
| T5 kickback | `one`: constant x2, fire + reset edges, 9 PVT at 4 MHz, ss/−40 at 2 MHz, ss/−40 asymmetric R ±5 % / C ±1 % (§3.4b; ±10 % R/C info) | diff peak ≤ 5 mV, ≤ 0.5 mV at 0.5·t_half after each edge; CM peak and recovery reported (C2) | C_X2/10 |
| T7 memory | `cyc` cycles −0.5 mV after +0.3 V and +0.5 mV after −0.3 V | correct sign at capture | `nobuf` (latch gates on op/on) |
| T8 device stress | `st`: VDPWR 1.98 V, order a (x2 to 3.6 V before VDPWR) and b (VDPWR first), then overload both ways, x2 −0.5 V, back to CM; tt/27 and ff/−40. **Gate stimulus (WO-51, §4b):** x2 at the OTA2 slew (27 V/µs per side) through R_X2/C_X2, moving only in φI, strobe on the 4 MHz phase plan. Info: `fast` (WO-48: 4.1 V in 20 ns through 10 Ω, free-running strobe), `async` (OTA2 slew, x2 also moves while the strobe is high) | every terminal pair: 1.8 V devices ≤ 1.98 V, HV ≤ 5.5 V | `in18` |
| T9 current | `cyc` | report (from VDPWR) | — |
| T10 capture window | `cyc`, capture = next fs_tick (clk edge) | §2 window + glitch | strobe in φI (`phase`) |
| T10nz near-zero | `cyc` ±1 µV cycles | q/qb valid, complementary, never both high in the capture window | `nolatch` |

Numerical rules: gear, reltol 1e-5, tmax 1 ps on every decision deck (stress 5 ps), 10 Ω on ideal sources, tstop reached and every measurement present (§11.1–2), temperature (B-source `temper`) and VDPWR read back from the run (§11.3), ideal parts only for stimulus, the behavioural x2 R/C and labelled probes (§11.6).

## 7. MC basis
- PDK (WO-44 probe): `nfet_01v8` / `pfet_01v8` carry vth0 mismatch in the `*_mm` sections; **`nfet_g5v0d10v5` has `vth0_slope = 0`**, only toxe mismatch (≈ 9.3 mV·µm equivalent in σ(Vgs)).
- D74 basis: HV pair 12 mV·µm in total = PDK `*_mm` draw + injected 7.6 mV·µm per device (an ideal series source on the inp gate, labelled). The same caveat applies to every HV pair in C1/C2.
- Seeds: per deck `.spiceinit` `rndseed`, python `random.Random(seed)` for the injection; bisection steps share the draw (no re-parse).

## 8. Open items
1. C4: strobe φC from φSe rising + ≈ 1 ns, falling at φS end (C4 §1); C9 RTL change: capture comp_in on fs_tick, drop comp_s (D74).
2. C2: OTA2 output headroom for the 45 mV CM kick; order-1 follower/reset (`rst2_o1`).
3. Layout: routed q load (100 fF assumed) and HV pair matching (common centroid).
