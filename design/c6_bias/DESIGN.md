# C6a — bias reference, trim, start-up and boost bank control (design note, stage 1)

WO-45, 2026-11-12. Stage 1 of the block recipe (PLAN.md Stage C): design note, hand calculations and spot sims. The netlist and the full testbench come in the next WO, after the `sd-adc-design-reviewer` pass on this note.

Sources: SPEC §3.0 rows 100–104, §3.8a (C9 port contract), CL-8, CL-9, CL-22, CL-23; DECISIONS D42, D43b, D47, D57–D65; REVIEW-C1b-final (C6 items, m8); results/wo32/README.md (C6 window); results/bias_bgr_area.md; LEARNINGS-pthomas-2026-11-10.md; `design/c1_ota1/netlist.py` (ports, bank switch).

Spot-sim deck: `design/c6_bias/c6_spot.py` (behavioural-free: PDK devices only), run script `run_wo45.sh`, results `work/v1-design/results/wo45/README.md`.

## 1. Block list and interfaces

| Sub-block | Function | Interface |
|---|---|---|
| C6.1 BGR core | current-mode bandgap (Banba): I0 = ΔVBE/R1 + VBE/R2 per branch | VG (PMOS gate line), VAPWR 3.3 V domain |
| C6.2 Trim + master | trimmed PMOS master leg from VG into the NMOS master diode VN | trim[2:0] from the C9 config shadow (1.8 V) → level-shifted |
| C6.3 Distribution | port mirrors slaved to VN (sinks) and to one PMOS slave diode VP (sources); boost = one switched leg (the VN half-diode switch) | OTA1 ports `ibtp ibn ibp ivbl0` (ivbnc / ivbpc are replica-fed in C1, 0 A from C6); OTA2 and comparator ports TBD by C2/C3 |
| C6.4 Start-up + bias_ok | zero-state detector, VG pull-down, bias_ok flag | `bias_ok` (3.3 V) → 1.8 V → C9 2-FF sync → `bias_valid` |
| C6.5 Boost bank drive | 3.3 V level shift + break-before-make for the C1 bank switch (TG Sbk, pull-up mbku) and the VN half-diode switch | `boost` (1.8 V, C9, latched at a pair boundary) |

OTA1 port currents (base; ×2 in boost; `sizes_draft.I_REF`): ibtp 2.357 µA (C6 sinks), ibn 3.122 µA (C6 sources), ibp 1.475 µA (C6 sinks), ivbl0 0.492 µA (C6 sinks). Total 7.45 µA base, 14.9 µA boost; these are charged to the OTA budgets, not to C6's own current.

## 2. C6.1 Current-mode bandgap core

Topology (Banba): two PMOS legs M1 = M2 (17 units each, unit `pfet_g5v0d10v5` W 0.42 / L 20) from VG. Node A: Q1 (1 × `pnp_05v5_W3p40L3p40`) ∥ R2a. Node B: R1 → Q2 (8 × pnp, 3×3 common-centroid with Q1 in the centre plus a dummy ring) ∥ R2b. An amplifier forces V_A = V_B, so each branch carries

I0 = VT·ln 8 / R1 + V_EB1 / R2.

Amplifier: stage 1 = PMOS pair (W 4 / L 4, gate A on the mirror-diode side, gate B on the output side), NMOS mirror load (W 1 / L 8), tail = 8 units from VG (self-biased), Cc 3 pF on o1. Stage 2 = NMOS M5 (W 2 / L 8, same current density as the load, so no systematic offset) into the PMOS diode M6 (8 units) on VG. VG is therefore a low-impedance node (1/gm6) and Cvg = 1 pF from VG to VDD sits on it (PSRR, and the worst case for start-up: VG follows VDD on a ramp). Loop sign: B has the larger impedance (R1 + 1/gm_Q2 ∥ R2 vs 1/gm_Q1 ∥ R2), so the net loop through B must be negative: VB ↑ ⇒ o1 ↓ ⇒ VG ↑ ⇒ I ↓.

Headroom at ss/−40/3.0 (worst): source of the input pair ≈ V_EB(0.75) + V_SG(≈1.3) ≈ 2.05 V; tail V_SD ≈ 0.95 V ≥ V_dsat ≈ 0.2 V. All devices are 5 V (`g5v0d10v5`), so no 1.98 V stress rule applies.

Resistors: `res_xhigh_po_0p69` (2 kΩ/sq, w_eff 0.634 µm). R1 = 82 µm ≈ 258 kΩ; R2 = ratio × R1 (ratio tuned by sim, §6; start 4.6 → 377 µm ≈ 1.19 MΩ). Size from the model inverse (LEARNINGS: Magic extraction misses the head term).

### 2.1 Hand calculation: temperature coefficient
The output current is V/R, so the voltage part must cancel R's own TC (tc1 −1470 ppm/K, tc2 +2.7 ppm/K², bias_bgr_area.md).
- V_EB1 at ≈ 0.2 µA in Q1 ≈ 0.62 V; dV_EB/dT ≈ (V_EB − Eg − XTI·VT)/T = (0.62 − 1.125 − 5·0.0259)/300 ≈ −2.1 mV/K (model: eg 1.125, xti 5).
- Let x = (R2/R1)·VT·ln 8 (PTAT part). Flat current needs d(V_EB + x)/dT = tc1·(V_EB + x): −2.1e-3 + x/300 = −1.47e-3·(0.62 + x) ⇒ x ≈ 0.246 V, V_eff ≈ 0.87 V, R2/R1 ≈ 0.246 / 0.0538 ≈ 4.6.
- Residual after the linear term is nulled: R curvature tc2·(ΔT)² ≈ 2.7e-6·(82 K)² ≈ 1.8 % peak over −40…125 °C, plus V_EB curvature (≈ 3–4 mV over the range, ≈ 0.4 %). Expect a concave I(T) with ≈ 2–3 % between the middle and the ends; the row limit is 3 % (§6 gives the measured number).
- Process: the R corners (±15 %) scale I but not its TC to first order; the pnp IS/BF corners move V_EB by ≈ ±10 mV (≈ ±1.2 % of V_eff, and a small TC change). Check per corner (§6).

### 2.2 Hand calculation: PSRR (DC, on the output current)
Definition used here (flag for the reviewer, the SPEC row does not define it): PSRR = 20·log10[(ΔV_DD/V_DD) / (ΔI/I)] over 3.0 → 3.6 V. 40 dB ⇔ ΔI/I ≤ 0.18 % over 0.6 V (0.3 %/V).
- The loop holds V_A = V_B, so M1/M2 see equal V_SD; the error comes from (i) the master leg's V_SD tracking VDD 1:1 (drain at V_GS,VN ≈ 0.9 V) and (ii) loop gain. With L 20 the unit λ is small (≈ 0.005/V estimated) ⇒ ≈ 0.5 %/V from (i) alone ⇒ ≈ 36 dB. If the spot sim confirms < 40 dB, cascode the master/trim legs and the port mirrors (LEARNINGS: uncascoded 5 V mirrors ran 43 % hot and tracked VDD). The cascode needs a VPC bias from a self-biased leg (≈ +0.2 µA).

### 2.3 Hand calculation: mismatch (per chip, untrimmed; σ)
Unit PMOS 0.42 × 20 = 8.4 µm², A_VT ≈ 6 mV·µm (5 V pfet, assumed) ⇒ σ_VT ≈ 2.1 mV; at ≈ 48 nA/unit (I/(W/L) ≈ 2.3 µA/sq, V_ov ≈ 0.39 V) gm/I ≈ 5/V ⇒ σ(I)/I ≈ 1.1 % per unit, σ/√n for n units.

| Source | σ on I_out | Note |
|---|---|---|
| Amp offset (pair W4L4: 1.5 mV; load W1L8: ≈ 1.3 mV referred) ≈ 2.0 mV | 2.0 mV / R1 / I0 ≈ 1.0 % | dominant; static, trimmed out; adds ≈ 0.25 % TC (Vos/R1 follows R's TC) |
| M1/M2 (17 units each) | ΔV_EB ≈ VT·0.4 % ≈ 0.1 mV ⇒ 0.05 % | negligible |
| Q1/Q2 (1:8 common centroid) | ≈ 0.3 mV ⇒ 0.15 % | |
| R1 / R2 (body Pelgrom 0.0347/√(w·l)) | 0.46 % / 0.21 % | the ratio error tilts the TC by ≈ 0.1–0.2 % |
| Master leg 21 units vs core 17 | 0.35 % | |
| **Total untrimmed** | **≈ 1.2 % σ (3.6 % 3σ)** | small next to R ±15 % and V_BG ±4 % |
| **Trim DNL**, worst transition 011 → 100: σ(4u − 3u) = 1.1 %·u·√7 | **2.9 % of one step** | the step is 34 σ from zero: monotonic by construction |

## 3. C6.2 Trim (3-bit, D42 / D47)

Master leg = G0 + k units, k = trim code (binary legs 1, 2, 4 units, each through a 5 V PMOS series switch W 1 / L 0.5; gate low = on, driven by a 1.8 → 3.3 V level shifter from the C9 config field). G0 = 17. Code 100 (reset, D47) = 21 units.

**Requirement set and what 3 bits can do.** SPEC row 103: range ≥ ±20 %, step ≤ 6 %, residual after the best code ≤ ±3 %. For a linear code (G0 + k) these three are at the edge:
- residual ≤ ±3 % needs adjacent codes within (1.03/0.97) ⇒ 1/G0 ≤ 6.19 % ⇒ G0 ≥ 16.2;
- covering a reference error of ±ε at ±3 % residual needs (G0 + 7)/G0 ≥ (1+ε)/(1−ε)·0.97/1.03. For ε = 20 % this is 1.4126; G0 = 17 gives 1.4118 (ε ≈ ±19.96 %), G0 = 16 gives 1.4375 but a residual of ±3.03 %.
- **Choice: G0 = 17 and the trim covers the process part of the error, ±19 %** (R ±15 % + V_BG ±4 %, bias_bgr_area.md). The ±3 % TC part of the ±20 % budget cannot be trimmed by a room-temperature calibration anyway. The spot check uses ±19 % (I7/I0 ≥ 1.3836) plus the adjacent-code residual. Options if the reviewer wants the literal ±20 %: accept ±3.03 % residual (G0 16), or a 4th trim bit (one more config bit + one leg; register bits 15:13 are reserved).
- Trim target (the value the calibration aims for, in units): GT = 19.8 (centre of [G0·1.19/1.03, (G0+7)·0.81/0.97]). The step is u/(GT·u) = 5.05 % of the target (≤ 6 %). Code 100 is +6.1 % above the target; codes 000 / 111 are −19.0 % / +14.3 % from code 100.
- **Untrimmed current** at reset (code 100) = 1.061·target·(1 + ε): with the §4 landing (target ≈ 0.91·I_REF,C1) that is ≈ 0.97·I_REF,C1·(1 ± 0.19), worst ≈ 1.15·I_REF,C1, inside the D47 untrimmed ≈ 1.5 × precision-min bound (≈ 160 µA).
- Code changes take effect at a pair boundary only (C9 latch); the transition glitch (011 → 100 swaps all legs) lands in the invalid toggle pair.

## 4. The +1.6 % high-side window at ff/125 and where the calibration lands (WO item 3)

**Flag.** WO-32 (C6 window, info): the OTA1 rows allow I_REF_btp to drop 19.3–22.4 % (SR − 3σ floor, CL-9) but rise only **+1.6 %** at ff/125 base (+1.62 % ff/−40; ceiling row). The trimmed current therefore has a 20.6 %-wide window, almost all of it on the low side. Landing on the design value (0 %) leaves 1.6 % against ±3 % trim residual + ±3 % TC (+ calibration temperature): **a trim aimed at 0 % fails the ceiling on part of the chips.**

**Where the calibration lands by itself.** SPEC row 103: lowest code whose 3-point bow and gain error are within 10 % of the plateau. That code sits at, or one step above, the SR knee: ≈ 10.25 V/µs vs 12.5–13.2 nominal ⇒ ≈ 0.80·I_REF (knee) to ≈ 0.85·I_REF. That is the bottom of the window: a −3 % TC excursion (cold or hot, relative to the bench temperature) puts the OTA below its knee.

**Proposal (options; the user decides):**
- **A (recommended): "lowest passing code + 2".** Lands at knee × (1.10 … 1.18) ≈ 0.88–0.94·I_REF. With residual inside that range and TC ±3 %: 0.85–0.97·I_REF. High-side margin to +1.6 %: ≥ 4.6 %; low side ≥ 5 % above the knee-current. Clip at code 111 (then flag the chip: the reference is > 14 % low and the SR margin is reduced).
- **B: "lowest passing code + 1".** Lands ≈ 0.84–0.90·I_REF; high-side margin ≥ 10 %, but only ≈ 1 % above the knee-current after a −3 % TC excursion. Lowest power.
- **C: aim by supply current instead of INL** (if the board can measure analog supply current per code, bias_bgr_area §4): target 0.91·I_REF directly. Needs a bench ammeter step; independent of the INL knee resolution.

In all three the C6 design target in hardware is unchanged; the window is met by where the firmware puts the code. The C6 tt/27 nominal (code 100) is set so that the target code (GT = 19.8 units) corresponds to 0.91·I_REF,C1, so the median chip lands at code 011/100 under option A.

## 5. C6.3 Distribution and boost (D43b, CL-8)

- VN = NMOS master diode (2 halves, each W 2 / L 4 × m). Sink ports (ibtp, ibp, ivbl0, and OTA2 / comparator sinks) = cascoded NMOS mirrors from VN, ratio = port current / master current (non-integer ratios by unit count + one trimmed-width unit; the ratio row is info-only per D60). The source port ibn = PMOS mirror from one slave diode VP, fed by an NMOS sink from VN at 0.5 × master (≈ 0.5 µA base, 1.0 µA boost).
- **Boost = one switched reference leg:** in boost, one of the two VN diode halves is switched out (NMOS series switch in its drain). The same master current through half the diode doubles every port mirror ratio at once (tail, fold, CMFB, ivbl0, OTA2, comparator), so I_fold/I_tail stays constant by construction. **Zero added current** for the ×2 (only the VP slave branch doubles, +0.5 µA). The vbpc leg's own ×1.75 increment (CL-8) is the C1 m_bpd bank switch, driven by C6.5.
- Settling after a toggle (tb12, ≤ 4 µs to 0.1 %): τ_VN = C_VN / gm_VN. C_VN ≈ 1–2 pF (all sink gates; OTA2/comparator TBD), gm_VN ≈ 10–15 µS at ≈ 1 µA ⇒ τ ≈ 0.1–0.2 µs ⇒ 0.1 % (6.9 τ) ≈ 0.7–1.4 µs; the C1-internal nodes (vbpc replica) add their own τ (tb12 in C1). Broken copy: master/diode ratio 1:256 ⇒ gm/256 ⇒ τ ≈ 26–51 µs ⇒ REJECT.
- **ivbl0 must absorb the clamp currents (REVIEW-C1b-final).** While rstb is low, mrst / mrsb tie ctl and bli to ivbl0, so whatever the CMFB amp output and the integrator push into those nodes flows into the m_bl0 diode against C6's 0.492 µA sink. If the injected current reaches the sink current, m_bl0 turns off and V_BL0 runs to VDD. Requirement: I_clamp,max ≤ 0.25·I_vbl0 (ΔV_BL0 ≲ 0.13·V_ov), or C6 raises the ivbl0 sink while rstb is low (×4, the C1 `vbl0x4` token; ≈ +1.5 µA only during start-up). **Needs from C1:** the maximum clamp current (tb9 start-up). Open item.

## 6. C6.4 Start-up, bias_ok and the sequencer interface

- **Zero state:** VG = VDD, I = 0, V_A = V_B = 0 is a valid DC solution of the Banba loop (and of the self-biased amp).
- **Detector:** node tsu pulled up by a leaker (8 × unit PMOS L 20 in series, gate 0, ≈ 0.1–0.2 µA) and pulled down by Mk (NMOS W 2 / L 4, gate VN, a mirror of the master diode, ≈ 1 µA capability). Master off ⇒ tsu = VDD; master on ⇒ Mk wins ≈ 5–10 × ⇒ tsu ≈ 0.
- **Kick:** Ms (NMOS W 1 / L 1, gate tsu) pulls VG down while tsu is high. Once the master runs, tsu ≈ 0 and **Ms is fully off** (V_GS ≈ 0): the start-up current is stolen away, no leaker current reaches the core (LEARNINGS: his weak always-on leaker injected 17 % error). The leaker current flows only VDD → tsu → Mk → VSS (own-current overhead, not an error term). PMOS bulks to VDD (LEARNINGS).
- **bias_ok** = NOT tsu (3.3 V CMOS inverter), level-down to 1.8 V, 2-FF synchroniser in C9 ⇒ `bias_valid`. It asserts when the master current crosses the Mk/leaker balance (≈ 10–20 % of final), so it says "running", not "settled". **Sequencer requirement (to C9):** rstb (C1 clamps) held low ≥ 2 T after bias_valid (REVIEW-C1b-final), and in addition ≥ t_settle,bias after bias_valid; the spot sim gives t90 − t_ok (§7). If 2 T at the fastest fs (0.5 µs at 4 MHz) is shorter, C9 holds rstb for a fixed count instead (e.g. 64 fs cycles). Then the clamps release and the dummy conversion runs (D65 m3).
- **Broken copy:** Ms removed ⇒ the 1 µs and 10 ms ramps must end at I ≈ 0 (Cvg keeps VG at VDD). If the copy starts anyway, the check is blind and needs a harder condition.

## 7. C6.5 Boost bank switch drive (REVIEW-C1b-final m8)

- C1 bank switch: TG `Sbk` (gbk ↔ ivbpc; closed in boost) and pull-up `mbku` (gbk → vdd; on in base). Both on at once shorts ivbpc to VDD.
- Drive: `boost` (1.8 V, from C9, latched only at a pair boundary, CL-7) → 3.3 V level shifter (cross-coupled 5 V PMOS, 5 V NMOS pull-downs from boost / boost_b) → non-overlap generator (two NOR/NAND gates with a delay chain, t_d ≈ 10–20 ns) → `bk_n` / `bk_p` (TG gates) and `pu_b` (mbku gate, high = off).
- **Order:** base → boost: pu_b high (pull-up off) first, then TG closes and the VN half-diode opens. Boost → base: TG opens and the VN half-diode closes first, then the pull-up turns on. Static current 0.
- The toggle pair is invalid (§3.7a e); bias settles ≤ 4 µs (§5).

## 8. Budgets (hand + spot sim)

| Item | Base | Boost | Limit |
|---|---|---|---|
| Core 2 × I0 (≈ 0.81 µA each) | 1.62 | 1.62 | |
| Amp (tail 0.38 + M6 0.38) | 0.76 | 0.76 | |
| Master leg (code 100) | 1.0 | 1.0 | |
| Start-up leaker | ≈ 0.2 | ≈ 0.2 | |
| VP slave branch (ibn source) | 0.5 | 1.0 | |
| **Own current** | **≈ 4.1** (spot sim w/o VP: §7 of README) | **≈ 4.6** | **≤ 6 µA** |

Area (estimate, pre-layout): pnp array 3×3 + dummy ring ≈ 1,300 µm²; xhrpoly 836 µm of 0p69 in ≈ 42 × 20 µm segments + dummies ≈ 2,300; MOS (≈ 90 units incl. leaker + amp + switches) ≈ 1,900 with overhead; level shifters, BBM, trim switches ≈ 300. Cc 3 pF + Cvg 1 pF MIM ≈ 2,000 µm² placed over the MOS/resistor area (MIM on met3/met4). **≈ 5,800 µm² of 7,000** (distribution mirrors counted under "bias distribution" in bias_bgr_area.md). If tight: Cc 3 → 1.5 pF after the stability check, or MOS caps.

## 9. Testbench plan (next WO), each with its broken copy

| tb | Check | Pass | Broken copy ⇒ expected |
|---|---|---|---|
| tbB1 T-sweep | I_out vs T, −40…125, 5 corners (+ fs, sf), fixed code | \|ΔI/I27\| ≤ 3 % | R2 open (PTAT-only core) ⇒ REJECT |
| tbB2 trim | 8 codes at −40 / 27 / 125, every corner + MC (≥ 200 tt, ≥ 50 worst) | every step ≥ 0.5 u (> 0), step ≤ 6 % of target, I7/I0 ≥ 1.3836, adjacent ≤ 1.0619 | **one trim leg open ⇒ REJECT** |
| tbB3 start-up | VAPWR PWL 0 → 3.0 V, 1 µs and 10 ms, ss/−40 and ff/125 (+ tt), uic, no .op; both orders vs the 1.8 V rail | I_end within 2 % of DC, settled (p2p ≤ 0.5 %), bias_ok high; t90 − t_ok reported | **start-up removed ⇒ REJECT** |
| tbB4 leaker-off | after start-up: Ms V_GS and I_D, tsu level | Ms I_D ≤ 0.1 % of I0 at ff/125 | Ms gate tied to a weak always-on bias ⇒ REJECT (error > 1 %) |
| tbB5 PSRR | DC 3.0 → 3.6 V, every corner | ≥ 40 dB (definition §2.2) | cascode removed (if added) ⇒ REJECT |
| tbB6 MC | 200 tt + 50 worst: untrimmed σ, TC spread, monotonicity | matches §2.3 within 2 × | pair mismatch × 3 ⇒ σ row REJECT |
| tb12 (C1/C6) | boost toggle both directions: I_fold/I_tail, settle ≤ 4 µs to 0.1 % | SPEC row 101 | **reference ratio 1:256 ⇒ REJECT** |
| tb11 (C1/C6) | currents base/boost per port | SPEC rows 100–101 | base K in boost ⇒ REJECT (CL-8) |
| tbB7 BBM | level shifter + non-overlap: TG and pull-up never both on (≥ 5 ns gap), every corner | overlap 0 | delay chain removed ⇒ overlap ⇒ REJECT |
| tbB8 clamp | rstb low: max clamp current into ivbl0, V_BL0 shift | ΔV_BL0 within the C1 bound | ivbl0 sink / 4 ⇒ REJECT |

## 10. Open items for the reviewer
1. Trim triplet (±20 %, ≤ 6 %, ±3 %) is infeasible by 0.04 % with 3 linear bits; this note trims ±19 % (process only). Accept, or G0 16 (±3.03 %), or a 4th bit.
2. PSRR definition (§2.2) and whether cascodes are needed (spot sim).
3. Calibration landing (§4): option A/B/C.
4. Clamp current into ivbl0 (§5): number from C1 tb9.
5. bias_ok → rstb hold: 2 T may be shorter than the bias settling (§6, spot sim).
