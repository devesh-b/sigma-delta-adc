# C1a: OTA1 + CMFB design note, rev B (WO-21)

Status: rev B for `sd-adc-design-reviewer`, before any schematic. Rev A was WO-20; this revision answers REVIEW-C1a-2026-11-09 (M1–M8, m1–m7) under D51 and SPEC CL-1 to CL-4. SPEC v1 is frozen and is not edited here; proposed change-log entries are in §6.

**Evidence tags.** HAND = hand calculation (formula and inputs given). SIM = WO-21 spot run on the sandbox, **not a C1b gate**:
- `python design/c1_ota1/op_ac_check.py OUT <corner indexes>`; logs `/home/mempool/regr/tt/WO-21/r1{a,b,c,d}.log`, json `r1/op_ac_revb_*.json`. 9 PVT points (tt/27/3.3, ss/−40/3.0, ss/125/3.0, fs/125/3.0, sf/125/3.0, ff/−40/3.6, ff/125/3.6, fs/−40/3.0, sf/−40/3.0) × base and boost. Rev B sizes, Vdsat-tracking cascode biases, m_pp gate at 0 V, CMFB = ideal B-source on the CMFB load section only, C_L = 1.4 pF per side.
- `python design/c1_ota1/revb_unit_checks.py OUT`; log `/home/mempool/regr/tt/WO-21/u1.log`. Device-level .op (pair candidates, bias density factor K, vg switches). It hit the 600 s limit on the loaded box after tt/27, ss/−40 and ss/125; those three corners are complete.

**Script fixes (M7).** A(v) now uses the measured V(op,om). A lost servo (> 1 mV), a dead OTA (|H| < 1 at 1 Hz), a missing unity crossing, NaN or a missing value prints REJECT. Each device's Vds − Vdsat ≥ 50 mV is asserted. The servo correction is clamped to ±0.3 V, because in the first run the tt base copy converged to a run-away servo state (tail 1.11 V, pair off). The script reported REJECT for that point, so the check was not blind. One broken copy runs every time: m_nc drain–source shorted at tt base. It gives A0 41.3 dB ⇒ **REJECTED (good)**. MC and `.noise` are not in this script; they move to WO-23 / C1b.

**Known optimism of the spot deck (WORKFLOW §11).**
- The devices have no ad/as/pd/ps, so **drain/source junction caps are zero**. fp2 and GBW are optimistic. HAND: about +50 fF at each fold node, which lowers fp2 by ≈ 20–30 %.
- Bias reference currents are ideal.
- CMFB is ideal.
- C1b must add the junction geometry, or use PEX.

## Rev B changes (summary)

| item | rev A | rev B | evidence |
|---|---|---|---|
| M1 headroom | m_pl 40/4, m_n 40/4, cascodes L 1; fixed V_FOLD = V_SDL = 0.45 V | m_pl 80/4 fixed half + 15/2 CMFB section (≈ 107 µm at L 4 equivalent), m_n 72/4, m_nc 20/2, m_pc 40/2; **Vdsat-tracking** diode biases (K_N 8, K_P 5) | SIM: every device ≥ 0.09 V above Vdsat at all 18 points; A0 ≥ 79.6 dB everywhere |
| D51(2) gm first | m_in 40/1, gm/Id 11.05 at ss/125 boost, GBW 21.8 MHz | **m_in 80/0.5** (same W·L 40 µm², so the same Cgg and Pelgrom σ); gm/Id 13.2–14.0 at hot boost | SIM: boost GBW ≥ **26.5 MHz** at every corner, at the same current |
| M3 protection cascode | V_PC from a replica holding V_DIN 1.10 (infeasible at ss/−40) | m_pp gate tied to **0 V**; V_DIN floats at Vsg_pp = 0.77–1.31 V; one bias leg removed | SIM: lower input-CM limit 0.10–0.39 V vs 0.87 V needed |
| M4 tail clamp | 3.3 V PMOS clamp (never conducts) | **dropped**; vg bounded by reset / island switches **closed by default** while rst_n low or bias invalid | design rule + tb 10 broken copy |
| M5 input chopper / island switches | nfet_01v8 1/0.15, 1.62 V drive | **nfet_g5v0d10v5**, chopper W 4/L 0.5, island W 2/L 0.5, gates from level-shifted 3.3 V clocks (C8) | SIM: nfet_01v8 Ron 62 MΩ–1.5e15 Ω (off); 3.3 V NMOS 4/0.5 Ron 0.82–2.5 kΩ |
| m1 C_L | 1.4 pF lump | itemised per phase (§2.1); I_TAIL stays **18.5 µA** | HAND |
| m2 CMFB | load gate, k 0.2 | 25 % short-ish (L 2) PMOS section on ctl; Cr refresh in OTA1 integrate (≠ Cs2 sample phase) | SIM ctl range; HAND ro cost −1.2 dB |
| m3 boost toggle | — | bias-node settle ≤ 500 ns with the mirror ratios in §2.9 | HAND |
| m4 | I_SINK/I_TAIL 1.35, option (c) to 1.2 | 1.35 kept, option (c) dropped | — |
| m5 corners | 5 | 9 incl. sf/fs at both temperatures | SIM |
| m6 | — | 3.3 V mirror-pair MC added (tb 8b) | plan |
| m7 | — | Vdsat per device per corner (§2.4 table) | SIM |
| M8 / M6 | noise mutants: sinks W÷4, 4 kΩ | C_L ÷ 6 and series gate R 65 kΩ, plus the ±30 % expected-value check; gate (B) at tt/27, ss/−40, ss/125, fs/125 boost (CL-3) | plan |

## 1. Topology

### 1.1 Core: fully differential folded cascode, PMOS input (D40a)

Per side: tail → input → protection cascode → fold node → NMOS cascode → output ← PMOS cascode ← PMOS load (fixed half ∥ CMFB section).

| device | type | W/L (µm) | role |
|---|---|---|---|
| m_t | pfet_g5v0d10v5 | 40/2 | tail, I_TAIL 18.5 µA (37 boost) |
| m_in | **pfet_01v8**, bulk = tail | **80/0.5** (8 × 10) | input pair |
| m_pp | pfet_g5v0d10v5 | 10/0.5 | protection cascode, **gate = VSS (V_PC 0 V)** |
| m_n | nfet_g5v0d10v5 | **72/4** | fold sinks, I_SINK = 1.35·I_TAIL |
| m_nc | nfet_g5v0d10v5 | **20/2** | NMOS cascode |
| m_pc | pfet_g5v0d10v5 | **40/2** | PMOS cascode |
| m_pl | pfet_g5v0d10v5 | **80/4** | load, fixed mirror half, 75 % of I_LOAD |
| m_plc | pfet_g5v0d10v5 | **15/2** | load, CMFB section, 25 % of I_LOAD, gate = ctl |
| m_bnc | nfet_g5v0d10v5 | 5/16 diode | m_nc gate bias (K_N 8) |
| m_bpc | pfet_g5v0d10v5 | 5/10 diode | m_pc gate bias (K_P 5) |

Everything except m_in is a 3.3 V device, so only m_in needs the D40 stress proof.

### 1.2 Vdsat-tracking cascode bias (M1)

- Each cascode gate comes from a diode-connected copy of **one finger** of that cascode, at L × K. This is a wide-swing bias: the diode runs at K times the cascode's current density, and the main sink/load sees Vds = Vgs(K·J) − Vgs(J).
- That difference scales with the overdrive of the cascode device, so it follows Vdsat over process, temperature and boost.
- Unit run (tt / ss/−40 / ss/125), m_n margin Vds − Vdsat by K:
  - K 3: −0.03…−0.02 V
  - K 4: 0.00…0.01 V
  - K 6: 0.05…0.12 V
- m_pl margin by K:
  - K 4: 0.07…0.15 V
  - K 6: 0.16…0.34 V
- Chosen **K_N 8, K_P 5**. In-OTA SIM gives m_n 0.09–0.22 V and m_pl 0.11–0.25 V above Vdsat at every point (§2.4 table).
- Diode currents: I_nc/4 (NMOS) and I_nc/8 (PMOS) in the spot deck. Final ratios are in §2.9.

### 1.3 SC CMFB (D40b, m2)

- **Sense caps:** C_c = 0.1 pF per side, from the output to `ctl`.
- **Refresh caps:** C_r = 25 fF per side.
- **CMFB device:** `ctl` drives only m_plc, a 15/2 PMOS section carrying 25 % of I_LOAD. The fixed 80/4 half takes its gate from a mirror diode.
  - The section's Cgg is ≈ 30 fF, so k = C_c/(C_c + C_g) ≈ 0.77.
  - HAND f_cm = gm_plc·k/(2π·C_L,int) with gm_plc ≈ 45 µS base gives ≈ 7 MHz base (C_L,int 0.77 pF, §2.1) and ≈ 11 MHz boost.
- **Phases (m2):** C_r is switched onto (V_OCM, V_BL0) in OTA1's **integrate** phase and onto (out, ctl) in OTA1's **hold** phase. So Cr refresh ≠ Cs2 sample phase, as the review asks. Cs2 samples x1 in hold (D25), and that hold-phase kick is covered by CL-2 (shorted Cs2 plates, ≤ 10 mV).
- **Range (SIM):** ctl = VAPWR − (0.93…1.42) V over all points, i.e. Vsg,plc 0.92–1.42 V. V_BL0 must come from a replica of m_plc at 25 % of I_LOAD, not from a fixed voltage, so that the SC loop only corrects mirror error.
  - Mirror error budget: sink ±5 % and fixed load ±5 % move the section current from 3.9 µA to 2.1–5.8 µA (54–147 %). It stays positive, so the loop does not run out of range.
- **ro cost (HAND):** ro ∝ L/I. Load ro (80/4 at 75 %) ∥ section ro (15/2 at 25 %) = 0.80 × a full 107/4 load, so R_up −1.9 dB. With R_dn/R_up ≈ 1.6–1.8 (SIM), this costs **A0 ≈ −1.2 dB**. This is included in the SIM A0.
- **Start-up:** `ctl` is clamped to V_BL0 by the reset switch while rst_n is low (same default-closed rule as §2.8).

### 1.4 OTA chopper (D4/D18, E2) and vg island switches (M5, D51 Q1/Q4)

- **Input chopper:** at the gates (vg side), **nfet_g5v0d10v5 W 4/L 0.5**, gates driven 0/VAPWR from C8 level shifters.
- **vg island / reset switches:** nfet_g5v0d10v5 W 2/L 0.5, also on 3.3 V clocks, **closed by default** (§2.8).
- **Output chopper:** stays at the fold node (low impedance), nfet_01v8 4/0.15 at 1.8 V clocks. This is the review's "fold-node chopper is fine".
- **Placement rule:** chop edges fall only in g (SPEC §3.6 rule 13).
- **Device choice (SIM, Ron at 1 mV, vg CM 1.07 / 1.20 / 1.33 V):**

| switch | tt/27/3.3 | ss/−40/3.0 | ss/125/3.0 |
|---|---|---|---|
| nfet_01v8 1/0.15, gate 1.62 V (rev A) | 62 MΩ / 4.3 GΩ / 318 GΩ (**off**) | 18 GΩ … 1.5e15 Ω | — |
| nfet_g5v0d10v5 4/0.5, gate VAPWR | 0.82 / 0.91 / 1.03 kΩ | 0.98 / 1.19 / **1.58 kΩ** | 1.74 / 2.05 / **2.54 kΩ** |
| TG n 2/0.5 + p 4/0.5 | 1.69 / 1.88 / 2.09 kΩ | 2.08 / 2.56 / 3.43 kΩ | 4.8 kΩ at 1.33 V |

- The PMOS half of a TG contributes almost nothing at vg ≈ 1.1–1.3 V: Ron,p ≥ 95 kΩ, and GΩ cold. So a TG is not worth its capacitance, and **NMOS-only 3.3 V** is chosen.
- **Series-R pole:** worst Ron 2.5 kΩ in series with the gate Cgg (≤ 0.19 pF) gives 330 MHz. That adds ≈ 4° of phase at the boost loop crossover (≈ 23 MHz). It is in the PM/fp2 picture that gate (B) sees, because (B) uses the real switches.
- **Injection (HAND):**
  - Q_ch = W·L·Cox·(VAPWR − vg − Vt,n) ≈ 4·0.5·3.0 fF·(3.0 − 1.2 − 1.0) ≈ 4.8 fC, half to each side.
  - 10 % mismatch into Cint 4 pF gives ≈ 60 µV constant residue, against ≤ 1 mV ✓.
  - Signal dependence: dQ/dvg = W·L·Cox ≈ 6 fF/V times the vg excursion (≤ x/A0 ≈ 0.1 mV) gives ≪ 1 µV ✓.
- **Noise:** 4kT·2.5 kΩ is 6.4 nV/√Hz per gate, i.e. ≈ 9 nV/√Hz diff against the OTA's ≈ 28 nV/√Hz. That adds ≈ +5 % in power.
- **Cp_vg contribution (SIM):**
  - closed switch: Cgg ≈ 4.2 fF, half on each terminal;
  - open switch: Cbd ≈ 1.2 fF;
  - island: ≈ 1 fF.
  - Per side ≈ 4 fF. See §2.2.

### 1.5 Boost (D43b)

One switched reference leg in C6 feeds the tail, sink, load-reference and cascode-bias mirrors, so every current scales by 2. I_SINK/I_TAIL = 1.35 by geometry in both modes (m4: kept; option (c) dropped).

### 1.6 Alternatives rejected

These are as in rev A (telescopic: swing; two-stage Miller: current and PM window).

**Gain boosters are no longer the fallback.** P2 was rejected (D51), and rev B meets A0 without them (§2.3).

## 2. Hand calculations and spot results

### 2.1 C_L itemised (m1) and I_TAIL / SR

Per side, Cp_vg = 0.23 pF (§2.2). Feedback series cap in integrate: Cint·(Cs + Cp)/(Cint + Cs + Cp) = 4·0.73/4.73 = 0.617 pF. In hold, Cs1 is off: 4·0.23/4.23 = 0.217 pF.

| item | integrate | hold | SPEC sum (conservative, §3.0 "Cs2 + series(Cs+Cp, Cint) + CMFB") |
|---|---|---|---|
| feedback network | 0.617 | 0.217 | 0.617 |
| Cs2 (samples x1 in OTA1 hold, D25) | — | 0.500 | 0.500 |
| C_c (CMFB sense) | 0.100 | 0.100 | 0.100 |
| C_r (on out in hold, m2) | — | 0.025 | 0.025 |
| Cdb m_nc 20/2 + m_pc 40/2 (HAND ≈ 0.5 fF/µm width) | 0.030 | 0.030 | 0.030 |
| Cs2 / Cint switch junctions, routing | 0.020 | 0.020 | 0.020 |
| PEX allowance (+20 % of parasitic rows) | 0.010 | 0.010 | 0.010 |
| **total** | **0.78 pF** | **0.90 pF** | **1.30 pF** |

- **I_TAIL = 18.5 µA kept** (no current change, D51). SR at the tier-1 definition is 18.5/1.4 = 13.2 V/µs, 12.8 at the −3 % trim floor ✓ (≥ 12.5).
- At the conservative SPEC sum (1.30 pF): 14.2 V/µs (13.8 at trim floor).
- At the real per-phase loads (≤ 0.90 pF): ≥ 20.5 V/µs. Boost doubles each figure.
- **Review m1 case:** C_c 0.2 pF would make the SPEC sum 1.40 pF, still 13.2 V/µs nominal.
- **The binding item is the trim floor at 1.4 pF**, not the real C_L.

### 2.2 GBW, gm first (D51(2)), Cp_vg and β1 (CL-4)

- WO-22 had not landed when this was written, so the target is the WO default: **26 MHz worst-corner loaded GBW in boost at the same current**. That needs gm1 ≥ 2π·26 MHz·1.4 pF = 229 µS, i.e. gm/Id ≥ 12.4 at 18.5 µA.
- **Pair candidates (unit SIM, ss/125/3.0 boost, 18.5 µA per device):**

| W/L | gm/Id | gm1 | Cgg/side | note |
|---|---|---|---|---|
| 40/1 (rev A) | 11.0 | 204 µS | 180 fF | 22.9 MHz |
| 80/1 | 12.8 | 237 µS | 336 fF | Cgg ×1.9 (β1 0.81) |
| **80/0.5** | **13.95** | **258 µS** | **160 fF** | **chosen**: same W·L as rev A |
| 120/0.5 | 14.4 | 266 µS | 229 fF | +3 % gm for +43 % Cgg |
| 160/0.5 | — | — | 306 fF (tt) | diminishing (weak inversion) |

- **Why 80/0.5:**
  - At equal W·L, halving L quadruples W/L. The pair moves deeper into moderate/weak inversion, which gives **+26 % gm** at **−11 % Cgg**.
  - Pelgrom σ (∝ 1/√(W·L)) and the 1/f area are unchanged.
  - Beyond W/L 160 the gain is ≤ 3 %, because weak inversion saturates gm/Id at ≈ 1/(n·U_T).
- **Offset (HAND):**
  - pair √2·5.856/√40 = 1.31 mV (unchanged);
  - sinks √2·8/√288 = 0.67 mV × gm_n/gm1 ≈ 1.2, giving 0.80 mV;
  - loads √2·8/√320 = 0.63 mV × gm_pl/gm1 ≈ 0.65, giving 0.41 mV.
  - σ = 1.59 mV, so **3σ ≈ 4.8 mV** ≤ 9 mV (rev A 5.9). A_VT 8 mV·µm for 3.3 V devices is still an assumption, which tb 8b checks (m6).
- **SIM (in-OTA, C_L 1.4 pF):** loaded GBW **base 13.5–21.5 MHz** (worst fs/125) and **boost 26.5–41.4 MHz** (worst fs/125 26.5, ss/125 27.7, ff/125 27.6, sf/125 28.3). The boost gm/Id is 13.2–14.0 hot.
- **Cp_vg per side:**
  - pair Cgg 137–189 fF (SIM, max ss/−40 boost);
  - chopper + island ≈ 4 fF (SIM);
  - Cs1 top-plate ≈ 5 fF (HAND);
  - routing 20 fF;
  - PEX allowance 6 fF.
  - **Cp_vg ≈ 0.22–0.23 pF**, so **β1 = 4/(4.5 + 0.23) = 0.846** ≥ 0.84.
- **The CL-4 number (proposal):** **β1 ≥ 0.83 (Cp_vg ≤ 0.32 pF per side)**, with rev B at 0.846. The "β1 ≈ 0.80 for a wider pair" fallback is not needed.

### 2.3 A0 and A(v) (hand from op numbers vs SIM)

- **HAND:** A0 = gm1·(R_dn ∥ R_up), with R_dn = (gm_nc + gmbs_nc)·ro_nc·ro_n and R_up = gm_pc·ro_pc·(ro_pl ∥ ro_plc). The gm and ro values are the op-point values of each corner.
- **The hand value agrees with the AC A0 within 0.2 dB at all 18 points** (example: ss/125 boost, R_dn 128 MΩ, R_up 71 MΩ, gm1 256 µS, giving 81.3 vs 81.2 dB).

| corner | A0 base | A(v)min base | A0 boost | A(v)min boost | GBW base / boost (MHz) | PM base / boost | fp2_eq base / boost (MHz) |
|---|---|---|---|---|---|---|---|
| tt/27/3.3 | 81.5 | 80.3 | 83.6 | 81.4 | 16.9 / 33.0 | 80.1 / 79.5 | 82 / 150 |
| ss/−40/3.0 | 81.7 | 80.8 | 84.0 | 82.3 | 21.5 / 41.3 | 78.4 / 77.2 | 88 / 153 |
| ss/125/3.0 | 80.5 | 78.6 | 81.2 | **73.6** | 14.5 / 27.7 | 81.0 / 80.7 | 77 / 142 |
| fs/125/3.0 | **79.6** ✗ | 77.9 | **80.8** | 74.7 | **13.5 / 26.5** | 82.0 / 81.6 | 81 / 151 |
| sf/125/3.0 | 80.8 | 79.0 | 81.4 | 74.4 | 15.1 / 28.3 | 80.3 / 80.3 | 74 / 140 |
| ff/−40/3.6 | 82.3 | 81.5 | 85.0 | 83.7 | 21.3 / 41.4 | 78.7 / 77.5 | 90 / 158 |
| ff/125/3.6 | **81.2** | 79.7 | 82.8 | 78.4 | 14.4 / 27.6 | 81.3 / 81.2 | 79 / 150 |
| fs/−40/3.0 | 81.0 | 80.1 | 83.6 | 81.9 | 20.7 / 40.6 | 79.3 / 78.0 | 92 / 162 |
| sf/−40/3.0 | 81.2 | 80.2 | 83.5 | 81.9 | 20.3 / 39.1 | 78.7 / 77.4 | 85 / 147 |

**Against the targets:**
- **Precision (≥ 80 dB A0, ≥ 75 dB A(v)):**
  - A(v) passes everywhere (≥ 77.9).
  - A0 passes everywhere except **fs/125 base, 79.6 dB (−0.4 dB)**.
  - ff/125 base, the review's "≈ 80 marginal" point, is at 81.2 ✓.
  - R_up is the smaller branch everywhere. Fix candidate (not yet simulated): **m_plc L 2 → 4** (W 30), which recovers most of the 1.2 dB section ro cost; C1b re-checks f_cm.
- **Boost (CL-1 floor, ≈ 72 dB expected, from WO-22):** A0 hot is **80.8–82.8 dB**, well above the review's 69–75 dB estimate. A(v)min hot is **73.6–78.4 dB**, above A_floor − 5 ≈ 67 dB.
- **Why A(v) falls at hot boost:** the drop is set by the output-swing top end (§2.4), not by A0.

### 2.4 Stack budget and Vdsat per device per corner (M1, m7)

- **Output swing need:** ±0.7 V per side around V_OCM 1.50 V, i.e. 0.80–2.20 V.
- **Swing limits:**
  - bottom = V_fold + Vdsat_nc + 50 mV;
  - top = V_sa − Vdsat_pc − 50 mV (V_sa = load-drain node).

| corner, mode | V_fold | V_sa | bottom | top | Vdsat m_in / m_pp / m_t / m_n / m_nc / m_pc / m_pl / m_plc (V) | min margin (device) |
|---|---|---|---|---|---|---|
| tt/27/3.3 base | 0.258 | 2.994 | 0.45 | 2.77 | 0.062 / 0.123 / 0.195 / 0.147 / 0.146 / 0.175 / 0.168 / 0.146 | 0.111 (m_n) |
| tt/27/3.3 boost | 0.366 | 2.867 | 0.62 | 2.57 | 0.074 / 0.165 / 0.268 / 0.200 / 0.201 / 0.244 / 0.230 / 0.205 | 0.166 (m_n) |
| ss/−40/3.0 boost | 0.306 | 2.625 | 0.52 | 2.36 | 0.064 / 0.138 / 0.233 / 0.166 / 0.165 / 0.214 / 0.197 / 0.182 | 0.140 (m_n) |
| ss/125/3.0 base | 0.329 | 2.626 | 0.57 | 2.35 | 0.078 / 0.162 / 0.245 / 0.190 / 0.193 / 0.223 / 0.209 / 0.188 | 0.139 (m_n) |
| **ss/125/3.0 boost** | 0.474 | 2.466 | **0.79** | **2.11** ✗ | 0.091 / 0.219 / 0.337 / 0.258 / 0.269 / 0.311 / 0.284 / 0.261 | 0.216 (m_n) |
| **fs/125/3.0 boost** | 0.473 | 2.503 | 0.79 | **2.16** ✗ | 0.088 / 0.202 / 0.315 / 0.258 / 0.268 / 0.289 / 0.270 / 0.241 | 0.178 (m_pp) |
| sf/125/3.0 boost | 0.452 | 2.464 | 0.76 | **2.10** ✗ | 0.093 / 0.218 / 0.337 / 0.247 / 0.256 / 0.312 / 0.284 / 0.262 | 0.205 (m_n) |
| ff/125/3.6 boost | 0.453 | 3.096 | 0.76 | 2.76 | 0.088 / 0.203 / 0.315 / 0.247 / 0.254 / 0.285 / 0.270 / 0.236 | 0.206 (m_n) |
| ff/−40/3.6 base | 0.211 | 3.346 | 0.37 | 3.16 | 0.051 / 0.095 / 0.158 / 0.117 / 0.113 / 0.139 / 0.137 / 0.116 | 0.093 (m_n) |

- **All Vdsat ≤ 0.34 V.** m_n and m_pl are ≤ 0.26 / 0.28 V at ss/125 and fs/125 boost, inside the ≤ 0.30 V target.
- **No device is within 0.09 V of triode at any of the 18 points.** Rev A had m_pl in triode at ss/125 boost.
- **The 3.0 V hot boost points are 0.04–0.10 V short at the top.** This is why A(v)min there is 73.6–74.7 dB rather than ≈ 80. The PMOS bias is generous: m_pl sits 0.23–0.25 V above Vdsat.
  - Fix for C1b: **K_P 5 → 4**. The unit run shows the m_pl margin falls to ≈ 0.15 V at ss/125 boost and V_sa rises by ≈ 0.1 V, so the top end comes to ≥ 2.2 V. This is not simulated in-OTA yet.
  - Alternative: V_OCM 1.45 V.
- **The bottom end is ≥ 0.79 V** (≤ 0.80 needed; 0.01 V margin at ss/fs/125 boost).
- **The base-mode stack has ≥ 0.15 V margin at both ends at every corner.**

### 2.5 Input CM (M3) and protection cascode

- **m_pp gate = 0 V.** V_DIN = Vsg,pp(I_TAIL/2) floats at **0.77 V** (fs/125 base) … **1.31 V** (sf/−40 boost).
- **Lower limit (SPEC: linear down to V_ICM − 0.13 − 0.2 = 0.87 V, checked at ss/125/3.0):**
  - With the measured Vsg,in (0.69–1.14 V), vg_min = V_DIN − Vsg,in + Vdsat,in + 50 mV is **0.10–0.39 V** (ss/125 boost 0.37 V).
  - **Margin ≥ 0.48 V.** Rev A had ≈ 0 V at V_DIN 1.25 (review M3).
  - The wider pair lowers Vsg,in by ≈ 0.12 V, which this absorbs.
- **Upper limit / tail headroom (SPEC ≥ 0.2 V at ss/−40/3.0, vg = V_ICM + 0.13):**
  - VAPWR − tail − 0.13 = **0.54 V boost / 0.57 V base** at ss/−40.
  - Less Vdsat,t (0.23 V), this leaves 0.31 V.
  - sf/−40 is the same (0.53 V). Rev A had 0.23 V.
  - V_ICM 1.20 V stays.

### 2.6 Second pole and PM (R2, D51(2))

- **SIM:** fp2_eq 74–92 MHz base and 140–162 MHz boost, i.e. **fp2/GBW ≈ 3.8–6.0**. PM at β1 is **77–82°**.
- Rev A had fp2/GBW 10–12 and PM 85–86°. The larger fold node (m_n 72/4, m_nc L 2) moved the pole down.
- With the junction caps the deck omits (+≈ 50 fF per fold node, HAND), fp2/GBW is expected near **3–4.5**, close to the S5h window (mult ≈ 3, PM 72–77°) **without** an extra cap.
- **C_FOLD_EXTRA** stays a MIM placeholder at 0 pF in `sizes_draft.py`. Its value is set from WO-22 (GBW needed at mult 10/30, pole-after-tanh verdict) and then from gate (B) with real junctions.
- gm_nc/gm1 spread sets fp2/GBW spread: SIM boost fp2/GBW is 3.8 (ff/−40) … 5.7 (fs/125), ±20 %. That is wider than the rev A estimate (±6 %) and comparable to the S5h window (±17 %).
- **The robust lever stays gm1** (review M2). It is already used, and GBW boost hot is now 26.5–28.3 MHz instead of 21.8.

### 2.7 Noise

Not re-simulated (WO-23). HAND:
- Sampled noise 2kT·γ·(1+α)·β/C_L.
- α = (gm_n + gm_pl)/gm1 falls from 2.16 to ≈ 1.8, because gm1 rises 12 % at tt base while gm_n and gm_pl are unchanged.
- That gives ≈ 100 µV rms at tt, plus ≈ 5 % from the 3.3 V chopper Ron (§1.4). SPEC ≤ 250 µV ✓.
- 1/f: the pair W·L is unchanged; the loads (not chopped) have larger W·L. Expected ≤ rev A's 50–100 kHz corner.

### 2.8 Device stress (D40a) and the vg bound (M4)

**Rule (M4):**
- The vg island switches and the Cint reset switches are nfet_g5v0d10v5 whose 3.3 V gate signal is **high by default**. The C8 level-shifter output has a pull-up to VAPWR and is forced high while rst_n is low **or** while the C6 bias-valid flag is low.
- At power-up, then, vg is tied to the V_ICM source (or follows it up from 0), and Cint is shorted, so output transients cannot couple to the gates.
- This replaces the tail clamp, which never conducted (tail > 3.7 V).
- The "gates high" fault is now unreachable by construction. tb 10 proves this, with the broken copy "reset default open at power-up ⇒ REJECT".

**SIM nominal m_in:**
- Vsd = tail − V_DIN ≤ 1.18 V (fs/−40 boost); Vsg ≤ 1.14 V (sf/−40 boost).
- Vgb = Vsg, since bulk = tail.
- Vgd = vg − V_DIN = −0.11…+0.43 V.

| event | worst (HAND on SIM nominal) | limit |
|---|---|---|
| nominal | Vsd 1.18 V, Vsg 1.14 V | 1.98 ✓ (0.80 V margin) |
| 1.1·VREF overload (one gate +0.12 V) | Vsd 1.30 V, Vsg,off 1.38 V | ✓ |
| power-up / bias invalid | vg ≤ V_ICM; tail ≤ vg + Vsg (sub-threshold), V_DIN ≥ 0 → Vsd ≤ ≈ 1.2 + 1.2 = 2.4 V **only if** V_DIN sits at 0 with the tail high. That needs m_pp off with current flowing, which is a contradiction, so the bias-off case is bounded by leakage | tb 10 measures it (ramp 1 µs–10 ms) |
| boost toggle | tail +0.04 V | ✓ |

### 2.9 Current, bias legs and boost-toggle settling (m3)

- **Core OTA1 (SIM i(VDD) device sum):** 47.7–48.7 µA base, 96.9–98.4 µA boost. This is unchanged from rev A, because the currents are unchanged.
- **Bias legs:** the spot deck uses 1:4 references (19.7 / 39.4 µA). That is far too much, and is only for convenience.
- **m3 sets the minimum ratio.** Each bias node must settle to 0.1 % (7τ) within 500 ns after the boost toggle, from both directions. The base-mode gm is the slow case.

| node | C on node (HAND/SIM) | ratio | ref I base | gm diode base | 7τ |
|---|---|---|---|---|---|
| bn (m_n gates) | 2 × 0.70 pF + diode ≈ 1.6 pF | 1:8 | 3.12 µA | ≈ 30 µS | 370 ns ✓ |
| bp (m_pl fixed gates) | 2 × 0.52 pF + diode ≈ 1.1 pF | 1:6 | 1.97 µA | ≈ 20 µS | 390 ns ✓ |
| btp (tail) | ≈ 0.25 pF | 1:16 | 1.16 µA | ≈ 13 µS | 135 ns ✓ |
| vbnc / vbpc | ≈ 0.32 / 0.42 pF | I_nc/32 | 0.49 µA each | ≈ 8 µS | 280 / 370 ns ✓ |

- **Bias legs ≈ 7.2 µA base / 14.5 µA boost**, against rev A's ≈ 3 / 6 µA estimate.
- **OTA1 ≈ 56 µA base, ≈ 113 µA boost.**
- Fast-mode system ≈ 188 + 8.5 ≈ **196 µA** after trim. That is inside the 200 µA design budget but over the D46c 189 µA risk figure. **This is an open item for the user** (§6, R5).
- **Option with the same settling:** bn and bp at 1:16, plus a reset-window pre-charge switch that shorts each bias node to its new-mode replica for the first 100 ns. Bias ≈ 4.4 / 8.9 µA, fast ≈ 191 µA.
- The CMFB loop re-settles in ≈ 5τ_cm ≈ 110 ns (f_cm ≈ 7 MHz) ✓.

## 3. Expected values (rev B)

| SPEC row | spec | value | margin | binding corner |
|---|---|---|---|---|
| A0 precision | ≥ 80 dB | SIM 79.6–82.3 | **−0.4 dB** | fs/125/3.0 base (m_plc L 4 proposed) |
| A(v) precision | ≥ 75 dB | SIM 77.9–81.5 | +2.9 dB | fs/125 base |
| A0 boost (CL-1) | ≥ A_floor (≈ 72, WO-22) | SIM 80.8–85.0 | ≈ +9 dB | fs/125 boost |
| A(v) boost (CL-1) | ≥ A_floor − 5 (≈ 67) | SIM 73.6–83.7 | ≈ +6.6 dB | ss/125 boost (top swing) |
| GBW base | ≥ 10 MHz | SIM 13.5–21.5 | +35 % | fs/125 |
| GBW boost | ≥ 20 (SPEC) / 26 (D51 target) | SIM 26.5–41.4 | +2 % on 26 | fs/125 |
| PM / fp2 (info) | ≈ 72–77°, mult ≈ 3 | SIM 77–82°, mult 3.8–6.0 (no junction caps) | toward window | C_FOLD_EXTRA from WO-22 / (B) |
| SR | ≥ 12.5 / 25 V/µs at 1.4 pF | HAND 13.2 / 26.4 (12.8 / 25.6 at −3 % trim) | +2.4 % | trim floor |
| I_fold/I_tail | ≥ 1.2, ±10 % | 1.35 by geometry | 12.5 % | mirror error |
| Offset 3σ | ≤ 9 mV | HAND 4.8 mV | 1.9× | A_VT(3.3 V) assumption, tb 8b |
| Input CM lower | 0.87 V | SIM vg_min 0.10–0.39 V | ≥ 0.48 V | ss/125 boost |
| Tail headroom | ≥ 0.2 V at ss/−40 | SIM 0.54 V (0.31 V above Vdsat) | +0.34 V | ss/−40 / sf/−40 boost |
| Stress m_in | ≤ 1.98 V | SIM ≤ 1.18 V nominal, ≤ 1.38 V overload | ≥ 0.6 V | fs/−40 boost |
| β1 / Cp_vg | ≥ 0.84 (CL-4: ≥ 0.83, ≤ 0.32 pF) | 0.846 / 0.23 pF | ✓ | ss/−40 boost |
| Current OTA1 | budget share | SIM core 48.7 / 98.4 + HAND bias 7.2 / 14.5 | fast ≈ 196 µA | boost, high trim |

## 4. Testbench plan (C1b)

**Rules:**
- Every tb prints ACCEPT/REJECT and exits nonzero on REJECT.
- **Every tb fails on NaN or on a missing measurement.**
- Every tb runs at all §6 corners, with sf/fs included (m5).
- Expected values come from SPEC and §3, never from the DUT.
- Device geometry includes ad/as/pd/ps (or PEX).

| # | tb | measures | pass limit | broken copy that must REJECT |
|---|---|---|---|---|
| 0 | tier-1 pre-check (WO-22) | GBW needed at mult 10/30; pole-after-tanh; A_floor | — | — (sets C_FOLD_EXTRA, CL-1 number) |
| 1 | op dump | every device Vds − Vdsat ≥ 50 mV, I_fold/I_tail, §2.4 table | table | sink m 16 → 8 (ratio 0.68) |
| 2 | AC open loop (real SC CMFB averaged) | A0, GBW, fp2_eq, PM; hand A0 from op within ±1 dB | §3 | m_nc D–S short (A0 41 dB, shown in the WO-21 spot) |
| 3 | static A(v) (measured Vod; servo-lock assert) | secant gain ±1.4 V diff, table into model INL | precision ≥ 75 dB; boost ≥ A_floor − 5 | m_pl L 4 → 0.5 |
| 4 | step diagnostic (A) | ε_dyn, ε_NL | report, health ≤ 1e-4 | tail ×0.5; GBW ×0.5 |
| 5 | **in-loop gate (B)** | transistor OTA1 with the 3.3 V chopper/island switches and SC CMFB, OTA2 behavioural, N 1024, 2 MHz ≤ 1.333 ppm and 4 MHz boost ≤ 5 ppm, O1/O2; **corners tt/27, ss/−40/3.0, ss/125/3.0, fs/125/3.0 (boost; CL-3)** | SPEC | I_TAIL for 9.5 V/µs (13.3 µA) |
| 6 | slew | ±0.49 V and full-scale, slower edge, C_L per §2.1 | ≥ 12.5 / 25 V/µs | I_TAIL ×0.75 |
| 7 | noise | integrated `.noise` at vg, closed-loop network; plus the ±30 % expected-value check vs §2.7 | ≤ 250 µV | **C_L ÷ 6 (≈ 318 µV ⇒ REJECT on the row)** and **65 kΩ series gate R** (⇒ REJECT); both must also fail the ±30 % check (M8) |
| 8 | MC offset | real per-seed MC (agauss redrawn per run, not a `repeat/reset` loop, M7), ≥ 200 tt/27 + ≥ 50 worst PVT, plus the hand A_VT(3.3 V) add-in | 3σ ≤ 9 mV, every sample | input-pair mismatch ×3 |
| 8b | **3.3 V mirror-pair MC (m6)** | ΔI/I of an m_n pair and an m_pl pair, both modes, ≥ 200 seeds; compares against the A_VT 8 mV·µm assumption | report; offset add-in uses max(measured, assumption) | mismatch disabled (`mc_mm` off) ⇒ σ = 0 ⇒ REJECT ("MC blind") |
| 9 | CMFB loop | CM step 30 mV, start-up from 0 and VAPWR, Cs2 hold-phase kick (CL-2), Cr phase per §1.3, ctl range per §1.3 | ≤ 10 mV in 0.2·t_half | C_r removed |
| 10 | device stress | max \|Vgs\|, \|Vds\|, \|Vgb\|, \|Vdb\| of m_in over power-up ramps (1 µs–10 ms), bias-off, reset, boost toggle, 1.1·VREF overload | ≤ 1.98 V | m_pp removed ⇒ REJECT; **reset/island switches default-open at power-up ⇒ REJECT** (M4; the Cint-coupled gate rise) |
| 11 | current | I(VAPWR) incl. bias legs, both modes, trim 000/100/111 | §2.9 ±10 % | — |
| 12 | boost toggle | I_fold/I_tail both modes; every bias node within 0.1 % in ≤ 500 ns, both directions (m3) | ≥ 1.2, ±10 %; 500 ns | sink mirror not slaved (ratio 0.68); bp reference 1:32 (settle > 500 ns) |
| 13 | vg switches | Ron over vg CM 1.07–1.33 V at ss/−40/3.0 and ss/125/3.0, injection residue, Cp_vg | Ron ≤ 3 kΩ; ≤ 1 mV / ≤ 1 µV residue | gate driven at 1.62 V (rev A device) ⇒ Ron > 1 MΩ |

## 5. SIZES

`design/c1_ota1/sizes_draft.py`: `SIZES` (rev B, `src` op = WO-21 spot), `REV_A` for comparison.

**Open:**
- C_FOLD_EXTRA (WO-22 / B);
- K_P 5 → 4 and m_plc L 4 (C1b);
- bias ratios (§2.9, user);
- CMFB caps (tb 9).

## 6. Risks and open questions, with proposed change-log entries

1. **R1, A0 precision at fs/125 base, 79.6 dB (−0.4 dB).** Candidate: m_plc L 4. This is a C1b op/AC re-check.
2. **R2, hot boost output swing top end 0.04–0.10 V short** (A(v)min 73.6 dB, above the CL-1 floor). Candidate: K_P 4 or V_OCM 1.45 V. C1b sweeps both.
3. **R3, fp2/GBW spread ±20 % over corners** (3.8–6.0), against the S5h window ±17 %.
   - The spot deck lacks junction caps.
   - Decide C_FOLD_EXTRA after WO-22 and gate (B) at the four CL-3 corners.
   - If (B) fails at a window edge, the next lever is gm1 again, i.e. current; that is a user decision under D51.
4. **R4, boost GBW margin 2 % on the 26 MHz target** at fs/125 (26.5 MHz). The real per-phase C_L (≤ 0.90 pF) gives ≥ 40 MHz. (B) uses the real load, so the margin question moves to (B).
5. **R5, bias-leg current.** m3 settling needs ≈ 7.2 / 14.5 µA of bias legs, so fast ≈ 196 µA, over the 189 µA D46c risk figure.
   - Options:
     - (a) accept, at ≤ 200 µA;
     - (b) 1:16 references plus a reset-window pre-charge switch (≈ 191 µA);
     - (c) relax m3 to the actual reset-window length, if longer than 500 ns.
   - User decision.
6. **R6, 3.3 V mismatch** (PDK vth0_slope 0). The offset is assumption-dependent; tb 8b measures it.
7. **R7, spot-deck optimism:** no junction caps, ideal references, ideal CMFB.
8. **Tooling:** at the current sandbox load one ngspice deck (two OTA copies) takes ≈ 3 min. Run ≤ 3 corners per process to stay inside the 600 s limit.

**Proposed SPEC change-log entries (user OK needed; SPEC frozen):**
- **CL-4 number:** "β1 ≥ 0.83 (Cp_vg ≤ 0.32 pF per side); rev B design value 0.846 (Cp_vg 0.23 pF incl. 3.3 V chopper and island switches)." Reason: the gm-first pair (80/0.5) keeps Cgg at the rev A level, so β1 ≈ 0.80 is not needed.
- **CL-5 (new, OTA1 devices row):** "vg-side chopper and island switches are 3.3 V devices on level-shifted VAPWR clocks; island and reset switches are closed by default while rst_n is low or the bias is invalid (bounds vg; replaces any tail clamp)." Reason: REVIEW-C1a M4/M5, SIM Ron of nfet_01v8 at 1.62 V > 60 MΩ.
- **CL-6 (new, OTA1 slew row, wording only):** "C_L ≥ 1.4 pF is the tier-1 lump; the itemised real load is 0.78 pF (integrate) / 0.90 pF (hold), and the conservative sum is 1.30 pF (§2.1). SR is gated at 1.4 pF." Reason: review m1.
