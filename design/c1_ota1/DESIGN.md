# C1a: OTA1 + CMFB design note (WO-20, block recipe step 1)

Status: draft for `sd-adc-design-reviewer`, before any schematic. SPEC v1 is frozen and is not edited here; proposed changes are in §6 as change-log entries.

**Evidence tags.** HAND = hand calculation (formula and inputs given). SIM = WO-20 spot run, `design/c1_ota1/op_ac_check.py` on the sandbox: `python design/c1_ota1/op_ac_check.py /home/mempool/regr/tt/WO-20/run3`, log `/home/mempool/regr/tt/WO-20/run3.log`. That run uses ideal bias currents, replica-diode cascode biases, an ideal B-source CMFB, and C_L = 1.4 pF per side. It is **not** a C1b gate: it has no broken copies, and 5 corners × 2 modes instead of §6.

**Spot-run defects (stated, not hidden).**
- The Monte Carlo section timed out (EXIT 124 at 1500 s, `repeat`/`reset` loop), so there is no MC number. Offset is HAND only.
- `ss/125/3.0 base` failed in post-processing (empty interpolation array), so that point has no numbers.
- The `.noise` result is invalid at ss/−40, ss/125 and ff/125 for the long variant (en ≈ 2–3 µV/√Hz, which is not physical). The short variant and long tt/ff−40 are consistent with each other. The cause is suspected to be the 1e9 F servo capacitor in `.noise`, not yet fixed.
- The static A(v) sweep gives a negative dB value at ff/125/3.6 (both variants) and at short ss/125 boost. So at those points the output does not reach ±0.7 V per side, or the servo lost lock. **This is an open item, not a pass.**

## 1. Topology

### 1.1 Core (chosen): fully differential folded cascode, PMOS input (D40a)

Per side: tail → input → protection cascode → fold node → NMOS cascode → output ← PMOS cascode ← PMOS load.

| device | type | role |
|---|---|---|
| m_t (×1) | pfet_g5v0d10v5, 1:4 mirror | tail, I_TAIL |
| m_in | **pfet_01v8**, bulk = tail (own n-well) | input pair |
| m_pp | pfet_g5v0d10v5, gate V_PC | protection cascode: holds the input drain at V_DIN ≈ 1.1 V |
| m_n | nfet_g5v0d10v5, 1:4 mirror | fold sinks, I_SINK = 1.35·I_TAIL |
| m_nc / m_pc | g5v0d10v5 | output cascodes |
| m_pl | pfet_g5v0d10v5 | loads; gates driven (fully or split) by the SC CMFB control node |

Everything except the input pair is a 3.3 V device, so only m_in needs the D40 stress proof.

The CMFB acts on the PMOS loads, so the sink current, and with it I_fold/I_tail, is set by mirror geometry only. This meets D43b without a second loop.

### 1.2 SC CMFB (D40b)

A Castello-type SC CMFB:
- **Sense caps:** C_c = 0.1 pF per side, from each output to the control node `ctl`. Counted in C_L.
- **Refresh caps:** C_r = 25 fF per side, switched between (V_OCM, V_BL0) and (out, ctl) on the two non-overlap phases from C8.

### 1.3 OTA chopper (D4/D18, E2)

- **Input chopper:** at the gates (vg side).
- **Output chopper:** between the fold node and the NMOS cascode source. This is a low-impedance node, the switch Ron only adds cascode source degeneration, and the swap sits **after** the sinks, so input-pair and sink offset and 1/f are chopped.
- **Not chopped:** the PMOS loads and cascodes. Their 1/f refers to the input as (gm_pl/gm_in)² ≈ 0.5 (SIM tt: gm_pl 102 µS / gm_in 142 µS). They are sized long (L 4) for that reason.
- **Placement rule:** chop edges fall only in g (SPEC §3.6 rule 13).

### 1.4 Boost (D43b)

There is one switched reference leg in C6. The tail, sink and CMFB-reference mirrors all hang off it, so every current scales by BOOST = 2. Then:
- I_SINK/I_TAIL = 1.35 by geometry in both modes;
- the ±10 % rule is met by construction, and only mirror mismatch and λ error are left (m_n Vds 0.45 V vs diode ≈ 0.9 V, ≈ 2–4 %, HAND). C1b checks this.

### 1.5 Alternatives rejected (HAND)

| option | swing / gain | power | stress | verdict |
|---|---|---|---|---|
| **Folded cascode (chosen)** | ±0.7 V/side at 3.0 V with ≈ 0.1 V margin (§2.5); A0 = gm·(gm·ro·ro) one stage, **75–83 dB base, 58–79 dB boost (SIM)** | 2·I_SINK = 2.7·I_TAIL | only m_in is 1.8 V; protection cascode | chosen; gain needs §2.4 fix |
| Telescopic | more gain per µA (no fold), but the output range shrinks by one Vdsat stack plus the input CM coupling: ≈ ±0.45 V/side at 3.0 V | ≈ 1.0·I_TAIL·(1+CMFB) | the 1.8 V pair sits in the main stack, so stress follows the output | rejected: fails |Vout,diff| 1.4 V |
| Two-stage Miller (FC or 5T first stage + CS second) | rail-to-rail-ish output; A0 > 90 dB easy | second stage needs its own slew current: SR·(C_L + Cc)·… ≈ +20–30 µA base; two CMFBs | 1.8 V pair fine | rejected on current (D42 budget 106–113 µA total) and on the PM window (Miller zero, C_L-dependent), which the S5h data shows is narrow |
| Gain-boosted FC (FC + 4 small aux amps on m_nc/m_pc) | +20–30 dB | +≈ 4×1–2 µA | aux amps 3.3 V | **kept as the fallback to fix A0** (§2.4, §6) |

## 2. Hand calculations (worst corner per row)

Inputs:
- C_L = 1.4 pF per side (tier-1 `TIER1_CL1`, SPEC);
- β1 = 0.84;
- t_half = 225 ns at 2 MHz, 112.5 ns at 4 MHz;
- gm per input device = gm1. With these, loaded GBW = gm1/(2π C_L) and diff SR = I_TAIL/C_L, which matches `gen_tier1.py` lines 259–260.

### 2.1 Current from slew

- Base: I_TAIL,min = SR·C_L = 12.5 V/µs × 1.4 pF = **17.5 µA**, i.e. **8.75 µA per input device** at balance and up to 17.5 µA in one device when fully steered.
- Boost: 25 V/µs × 1.4 pF = **35 µA**.
- Nominal choice: **I_TAIL = 18.5 µA** (boost 37 µA). The +5.7 % covers the D42 trim residual (±3 %) and mirror error (≈ 2 %).
- SR at nominal = 18.5/1.4 = **13.2 V/µs** (26.4 boost). At the trim floor: 0.97 × 13.2 = **12.8 V/µs ≥ 12.5** ✓ (margin 2.4 %).
- Untrimmed −20 %: 10.6 V/µs. That is above the D44 knee (10.23–10.28) but below the row, which is consistent with the D47 rule that the trim is always rewritten.
- **Binding corner:** the corner where the trimmed reference sits lowest, together with the largest real C_L. SR does not depend on gm.
- Sinks: I_SINK = 1.35·I_TAIL = **25.0 µA** per side (SPEC ≥ 1.2; 1.35 keeps ≥ 1.2 with 10 % mirror error).
- Loads: I_LOAD = I_SINK − I_TAIL/2 = **15.7 µA** per side.

### 2.2 GBW and gm/Id

- Requirement:
  - base: gm1 ≥ 2π·10 MHz·1.4 pF = **88 µS** (gm/Id ≥ 88/9.25 = 9.5);
  - boost: gm1 ≥ 2π·20 MHz·1.4 pF = **176 µS** at 18.5 µA, i.e. **gm/Id ≥ 9.5**. With 15 % margin, target 202 µS (gm/Id 10.9).
- **Binding corner for gm is hot (ss/125), not ss/−40.** In gmid_table, the pfet_01v8 gm/Id at fixed J is highest at −40 °C (L 1, 3e-7 A: 17.4 at ss/−40 vs 12.1 at ss/125). The WO's "ss/−40 for gm" is corrected here: ss/−40 binds slew-related headroom (§2.5), not gm.
- **Sizing (HAND).** gmid_table, ss/125, L 1: gm/Id 10.9 by log-interpolation between J = 3e-7 (12.1) and 1e-6 (8.6), giving J = 4.5e-7 A/□. So W/L = 18.5 µA / 0.45 µA = 41, hence **W 40 µm, L 1 µm** (4 × 10 µm fingers). This is above the table's minimum W/L of 28.2.
- **Why L = 1 µm:**
  - Offset needs W·L ≈ 40 µm² (§2.10).
  - 1/f falls with W·L.
  - L 0.5 would give the same gm at W·L 10, but with pair 3σ ≈ 7.9 mV, leaving no room for the sink and load terms.
  - L 2 would quadruple Cgs and break the Cp_vg budget (below).
- **SIM results:**

| point | gm/Id | gm1 | loaded GBW |
|---|---|---|---|
| tt/27 base | 15.5 | 142 µS | **15.9 MHz** (HAND 16.5) |
| tt/27 boost | 13.5 | 246 µS | 27.4 MHz |
| ss/125 boost | **11.05** | 201 µS | **21.8 MHz** ≥ 20 ✓ (margin 9 %; HAND 10.9 / 23 MHz) |
| ff/125 base | — | — | 13.2 MHz ≥ 10 ✓ (lowest base seen; ss/125 base missing) |
| ff/−40 boost | — | — | 34.4 MHz (highest) |

- **Input-pair gate capacitance (SIM):** Cgg = **0.178–0.201 pF** per side. That is 70–77 % of the Cp_vg budget (0.262 pF per side, `TIER1_CP_VG`, which gives β1 0.84). With switches, Cs top-plate and routing (≈ 0.08 pF, HAND), Cp_vg ≈ 0.27–0.28 pF, so β1 = 4/(4 + 0.5 + 0.28) = **0.837** (−0.4 %). The effect is negligible, but the row says β ≥ 0.84; see §6 (P3).

### 2.3 A0 and A(v)

**Definition used.** Static large-signal A(v) = Vod/(vid(Vod) − vid(0)), the secant from the offset point (SPEC §3.0 DC-gain row), not the incremental slope. The tb forces Vod = Vt with a DC servo and sweeps Vt over ±1.4 V diff (±0.7 V per side).

**HAND budget:**
- R_dn = gm_nc·ro_nc·ro_n (the input branch is cascoded by m_pp, so it adds only a high-impedance branch);
- R_up = gm_pc·ro_pc·ro_pl;
- A0 = gm1·(R_dn ∥ R_up).

With 3.3 V devices at λ ≈ 0.1/L [1/V], L in µm, rough:
- gm·ro of a cascode at L 1 is ≈ 60–100;
- ro of a sink or load at L 4 and 15–25 µA is ≈ 1.5–2.5 MΩ;
- so R_out ≈ 50–100 MΩ, and gm1 = 142 µS gives **≈ 77–83 dB** at tt base.

Gain ∝ 1/I (gm·ro of the cascodes ∝ 1/√I in moderate inversion, ro ∝ 1/I), so **boost costs ≈ 6–10 dB**. Hot corners lose ro.

**SIM (long variant = proposal; short = L_c 0.5, L_s/L_l 2):**

| point | A0 long | A_static min (\|Vod\| ≤ 1.4) long | A0 short |
|---|---|---|---|
| tt/27/3.3 base | **80.3 dB** | **78.6 dB** ✓ | 66.7 |
| tt/27/3.3 boost | 71.0 | 68.9 ✗ | 63.6 |
| ss/−40/3.0 base | 82.7 | 80.7 ✓ | 68.8 |
| ss/−40/3.0 boost | 74.7 | 72.2 ✗ | 65.9 |
| ss/125/3.0 boost | **58.3** | **55.0** ✗ | 58.8 |
| ff/125/3.6 base | 75.3 ✗ | invalid (see header) | — |
| ff/125/3.6 boost | 64.5 | invalid | — |

**Result:**
- The plain folded cascode meets A0 ≥ 80 dB / A ≥ 75 dB **only at cold and typical, base mode**.
- Hot and boost corners fall 5–25 dB short.
- Lengthening L (short → long) bought ≈ 13 dB at tt but almost nothing at ss/125 boost (58.8 → 58.3). This suggests that at hot boost the limit is a device leaving saturation or junction leakage, not λ. The op dump shows the fold node at 0.45 V and the load node at VDD − 0.45; this needs the C1b op-dump tb with Vds − Vdsat per device.

**Fix options (ranked):**
- **(a) Gain-boost amplifiers on m_nc and m_pc** (classic regulated cascode; +20–30 dB, ≈ 4–8 µA base total).
  - Risk: a slow pole–zero doublet. The aux-amp UGB must sit between β·GBW and fp2, i.e. ≈ 40–150 MHz.
  - The S5h result shows OTA1 INL is very sensitive to the settling shape, so the in-loop gate (B) must include the boosters.
- **(b) Run the in-loop gate (B) with the transistor A(v) table to see whether the hot/boost gain loss actually costs INL.**
  - The SPEC gain row's budget line is "model INL with simulated A(v) table ≤ 8 ppm".
  - Fast mode is N 1024 with a 5 ppm gate.
  - If (B) passes, the fast-mode A0 can be exempted by change log (P1).
- **(c)** Reduce I_SINK/I_TAIL toward 1.2 (raises ro_n and ro_pl by ≈ 12 %, worth ≈ 1 dB). Not enough on its own.

### 2.4 Output swing and input CM (D34)

**Output stack at VAPWR 3.0 V:**
- bottom = V_FOLD (0.45) + Vds_nc,min (≈ 0.25) = 0.70 V;
- top = 3.0 − V_SDL (0.45) − Vsd_pc,min (≈ 0.25) = 2.30 V;
- V_OCM = **1.50 V**, swing ±0.7 V per side needs 0.80–2.20 V, so **margin ≈ 0.10 V each end**.
- Vdsat from SIM (tt base): m_n 0.19, m_nc 0.14, m_pc 0.17, m_pl 0.26 V. **m_pl leaves 0.19 V** (0.45 − 0.26); at boost its Vdsat rises ≈ √2.
- So at boost and 3.0 V the load sits close to the triode edge. This is a likely contributor to the boost A(v) loss.
- Option: V_SDL 0.55 V with V_OCM 1.45 V. C1b sweeps it.

**Input CM. Proposal: V_ICM = 1.20 V.**
- **Upper limit** (ss/−40/3.0, v_g,cm = V_ICM + 0.13):
  - SIM tail at V_ICM is 2.395 V at ss/−40 base (2.435 V boost), so at +0.13 V the tail is ≈ 2.53/2.57 V.
  - Tail device Vsd = 3.0 − 2.57 = 0.43 V; with Vdsat ≈ 0.2 V (HAND, L 2), **headroom ≈ 0.23 V ≥ 0.2 ✓** (margin 0.03 V, boost).
  - **This is the tightest row in the note.** V_ICM 1.15 V would buy 0.05 V.
- **Lower limit** (ss/125/3.0, v_g,cm = 1.20 − 0.13 − ΔV_drift; ΔV_drift ≤ 0.2 V gives 0.87 V):
  - the input pair stays saturated while V_DIN ≤ v_g + |Vt| − margin;
  - with |Vt| ≈ 0.45 V hot (HAND), 0.87 + 0.45 − 0.1 = 1.22 V ≥ V_DIN 1.10 ✓.
- **Protection-cascode gate (SIM finding):**
  - the replica that holds V_DIN = 1.10 V needs V_PC = +0.07 V at tt, but **−0.12 V (base) / −0.18 V (boost) at ss/−40**. A ground-referenced gate cannot reach that.
  - **Proposal: V_DIN = 1.25 V**, which keeps V_PC ≥ −0.03 + 0.15 ≈ 0.1 V at ss/−40, with the lower-CM margin re-checked at ss/125 (1.22 V limit above → about 0). Or use a lower-|Vt| PMOS for m_pp: `pfet_g5v0d10v5` is the only 3.3 V option, and the 1.8 V lvt devices are excluded by stress.
  - **Open: V_DIN between 1.15 and 1.25 V; C1b sweeps it across ss/−40 and ss/125.** This is risk R3.

### 2.5 Noise

**Sampled thermal noise at vg** (integration phase, chopper parked):
- Formula: v² = S_in,white·(π/2)·β·GBW = 2kT·γ·(1+α)·β/C_L, with α = (gm_n + gm_pl)/gm1.
- HAND (tt): α = (206 + 102)/142 = 2.16, γ = 0.75, giving v² = 2·4.14e-21·0.75·3.16·0.84/1.4e-12 = 1.18e-8 V², so **108 µV rms**.
- SIM: en (3 MHz) 28.3 nV/√Hz diff and loaded GBW 15.9 MHz give **130 µV** at tt base (121 µV boost). The short variant gives 125–157 µV over all corners.
- SPEC ≤ 250 µV ✓ (margin ≥ 1.6×). The SPEC "expect 75–110 µV" is exceeded by ≈ 20–40 %, because the sinks at gm/Id ≈ 8 contribute more than the input pair (α > 2), a price of the low-Vdsat headroom choice in §2.4.
- **Note for the check design:** sampled noise is almost independent of gm1 (bandwidth ∝ gm1). So the WO broken copy "input pair halved" (W/2 at the same current) changes gm1 by only ≈ +5–10 % in moderate inversion and does **not** move this row out of 250 µV. See §4.

**1/f** (SIM, tt, long): en(1 kHz) 170 nV/√Hz, **fc ≈ 50 kHz** base / 79 kHz boost (short: 141–282 kHz). This is ≤ 631 kHz (info) ✓, and fch = fs/2 = 1 MHz sits well above. The PMOS loads are not chopped (§1.3); their share of the 1/f is what the system chop removes.

**Chopper residue:** the constant residue ≤ 1 mV and the signal-dependent residue ≤ 1 µV are set by switch charge-injection mismatch at the gates. HAND: a 1×0.15 µm nfet_01v8 gives Q_inj ≈ W·L·Cox·Vov/2 ≈ 0.15·8.2 fF·1 V/2 ≈ 0.6 fC, and 10 % mismatch into Cint 4 pF is ≈ 15 µV. ✓ Open for C1b transient.

### 2.6 Second pole and PM

- **Fold-node pole:** fp2 ≈ gm_nc/(2π·C_fold), with C_fold = Cdb,n + Cgd,n + Cdb,pp + Cgs,nc + chopper switch.
- HAND: m_n 40/4 → ≈ 60 fF, m_nc → ≈ 15 fF, m_pp/chopper ≈ 20 fF, so ≈ 95 fF. With gm_nc 178 µS this gives **fp2 ≈ 300 MHz**.
- SIM (two-pole fit from the excess phase at the β1 crossover): fp2_eq **166–344 MHz** long (240–460 short), i.e. **fp2/GBW ≈ 10–12**, and **PM 85–86°** at β1 in every corner.
- **This is outside the S5h window** (PM ≈ 72–77°, fp2 ≈ 3×GBW). The S5h tier-1 data at the boosted 20 MHz point:
  - fp2 ×3 gives 3.36 ppm;
  - fp2 ×4 gives 8.06 ppm;
  - **fp2 ×30 gives 28.5 ppm**, against the 5 ppm fast gate.
- A natural folded cascode is therefore close to the single-pole case that fails. Our boosted GBW (21.8–34 MHz) is above 20 MHz, which helps (HAND: the linear-settling exponent 2πβ·GBW·t_half rises from 11.9 to 13.0–20.4), but whether that is enough is **unknown**.
- **How fp2 is set by sizing:** add C_FOLD_EXTRA (MIM, ≈ 0.3–0.6 pF per side) at the fold nodes. fp2 then tracks gm_nc, which scales with boost like gm1 (both ×1.4–1.6 in SIM), so fp2/GBW is roughly mode-independent. Over corners, though, gm_nc/gm1 spans 1.18–1.33 in SIM (≈ ±6 %).
- The S5h window (mult 2.5–3.5, i.e. ±17 %) is narrow but wider than that spread. The extra cap adds no noise and costs ≈ 300 µm² MIM per side.
- **Resolution path:** tier-1 run of the D39 boosted point with GBW 21.8 MHz and fp2 mult {3, 4, 10} (C1b item 0, §4). This is risk R2.

### 2.7 CMFB loop

- **DC accuracy:** the SC CMFB has no static error beyond charge injection (≈ 1–5 mV, HAND).
- **Loop UGB:** f_cm = gm_pl,ctl·k/(2π·C_L), with k = C_c/(C_c + C_g,pl,ctl).
  - m_pl 40/4 Cgg ≈ 0.4 pF (HAND, 3.3 V Cox ≈ 3 fF/µm² × 160 µm² × 2/3 + overlap).
  - **If the whole load is CMFB-driven:** k = 0.1/(0.1 + 0.4) = 0.2, so f_cm = 102 µS·0.2/(2π·1.4 pF) = **2.3 MHz**, which is too slow.
  - **Proposal (sizes_draft CMFB_SPLIT 0.5):** split each load into a fixed mirror half and a CMFB-driven half (Cg 0.2 pF), and raise C_c to 0.2 pF per side. Then k = 0.5 and f_cm = 51 µS·0.5/(2π·1.4 pF) ≈ **2.9 MHz**. Still slow.
  - **Better:** drive the CMFB through a small NMOS sink section instead. m_n is longer and wider, so it is worse. **Alternative: make the CMFB-controlled device a short-L (L 1) PMOS section, 25 % of the load current**, with gm ≈ 40 µS at Cg ≈ 25 fF, so k = 0.2/0.225 = 0.89 and f_cm ≈ **4 MHz** base, ≈ 6 MHz boost.
- **Per-cycle CM requirement:** absorb the per-cycle CM charge to ≤ 10 mV in 0.2·t_half (45 ns at 2 MHz, 22.5 ns at 4 MHz).
  - With a 4–6 MHz CM loop (τ ≈ 27–40 ns), the requirement holds only if the initial CM kick is ≤ 10 mV·e^(0.2·t_half/τ) ≈ 18–30 mV (2 MHz) or 15–18 mV (4 MHz).
  - The kick sources (HAND): chopper and island-switch injection (≈ 1–5 mV), plus Cs2 connecting in OTA1's hold phase. The latter gives ΔV_cm = (V_cs2,rest − V_OCM)·Cs2/(Cs2 + C_L). It is **zero only if Cs2's bottom plate rests at V_OCM1 = 1.5 V** before it samples x1. This is an interface requirement on C4/C9 (stated in §6, R4).
- **Start-up from either rail:**
  - SC CMFB has no DC path at power-up. The SC refresh caps converge in ≈ (C_c/C_r)·few = 8–30 cycles.
  - The ctl node needs a reset clamp to V_BL0 during the reset window, otherwise the outputs latch at a rail when ctl starts far off.
  - C1b tb: `.ic` outputs at 0 and VAPWR at every corner (PLAN line 172).

### 2.8 Device stress (D40a), 1.8 V devices = m_in only

Nominal (SIM): tail 2.06–2.44 V, V_DIN 1.10 V, so Vsd_in = 0.96–1.34 V. Vsg ≈ 0.86–1.2 V. Vgb = Vsg (bulk = tail); Vdb = Vsd. **Max ≈ 1.34 V, 0.64 V below 1.98** (ss/−40 boost).

| event | mechanism | worst HAND | protection |
|---|---|---|---|
| power-up (VAPWR 0 → 3.6) | bias not started: tail floats; gates driven by island switches to ≈ V_ICM | Vgs ≤ V_ICM + overshoot ≈ 1.3–1.5 V | none needed if vg ≤ 1.98 V w.r.t. tail; weak tail-to-V_ICM keeper (≈ 10 nA) proposed; tb: bias-off state |
| bias on, both gates high (fault, vg > V_ICM + 0.6) | tail follows max(vg) + Vsg toward VDD; off device drain held only by m_pp at V_PC + Vt ≈ 1.0–1.25 V | Vsd → 3.6 − 1.0 = **2.6 V ✗** | m_pp alone is **insufficient** when vg ≳ V_DIN + 1.98 − Vsg ≈ 2.0 V. Needs (a) vg bounded (NMOS-only island switches pass ≤ VDD − Vt; Cs coupling ≤ 0.25 V, below) **or** (b) tail clamp: 3.3 V PMOS diode from tail to a 2.9 V node, limiting the tail to ≈ V_DIN + 1.9 |
| reset | Cint shorted; vg and out to their CMs | ≤ nominal | — |
| boost toggle | currents ×2 within the reset window; tail +0.04 V (SIM) | ≤ 1.38 V | — |
| 1.1·VREF overload | worst vg step = 2.25 V·Cs/(Cs + Cint + Cp) = 2.25·0.5/4.78 = 0.24 V diff; one gate +0.12 V | tail +0.12, Vsd ≈ 1.46 V, Vsg_off ≈ Vsg + 0.24 ≈ 1.4 V | ✓ |
| differential gate split | off device Vsg = Vsg_on + \|vid\| | needs \|vid\| ≤ 1.98 − 1.2 = 0.78 V | ✓ in normal operation (≤ 0.24 V) |

**Protection-cascode bias:**
- V_PC = V_DIN − Vsg,pp(I_TAIL/2), from a replica diode carrying I_TAIL/2 with its source at V_DIN (as in the spot run).
- SIM V_PC at V_DIN 1.10 V: −0.18…+0.31 V, which is infeasible at ss/−40 (§2.4).
- Recommendation: V_DIN ≈ 1.25 V plus tail clamp (b). Broken copy for the stress tb: remove m_pp (the input drain falls to the fold node 0.45 V, so Vsd ≈ 2.0 V at ss/−40 boost: REJECT expected, HAND) **and** remove the clamp in the "gates high" fault.

### 2.9 Current (D41/D42)

- Core OTA1 (SIM i(VDD), excludes bias replicas): **49.4 µA base, 98.4 µA boost** (HAND 2·I_SINK = 50.0 / 99.9 µA).
- Add the local bias legs (cascode, protection and CMFB-reference replicas scaled 1:8, ≈ 4 legs × 2–2.3 µA): **≈ 3 µA base, 6 µA boost** (HAND).
- **OTA1 ≈ 52 µA base, ≈ 105 µA boost.**
- Against the SPEC 2.7·I_TAIL model (47 / 94.5 µA at I_TAIL 17.5 µA): **+5 µA base, +10 µA boost.**
- System (HAND, SPEC inputs): OTA2 25.5/51 + bandgap 6 + comparator/clock ≈ 10.
  - **Precision ≈ 94 µA nominal**, which lies in the 106–113 µA envelope once the ±3 % trim and 10 % untrimmed spread are included.
  - **Fast ≈ 172 + 10 = 182 µA nominal; ×1.03 after trim gives ≈ 188 µA, inside the D46c 189 µA risk figure with ≈ 1 µA to spare.**
- Gain boosters (§2.3a) would add 4–8 µA base and 8–16 µA boost, giving **fast ≈ 196–204 µA**. That is at or over the 200 µA design budget (P2).

### 2.10 Offset 3σ (HAND; the MC run failed, see header)

- Pelgrom from the PDK model: pfet_01v8 `vth0_slope` = 5.856 mV·µm per device (`sky130_fd_pr__pfet_01v8__mismatch.corner.spice`; vth0 += AGAUSS·slope/√(W·L·m)).
- Input pair, W·L = 40 µm²: σ_ΔVt = √2·5.856/√40 = **1.31 mV**.
- The **3.3 V devices have vth0_slope = 0** in the PDK, which models their mismatch through toxe/voff/nfactor only. **An MC will under-report the sink and load terms (a false-pass risk, WORKFLOW §11).**
- HAND, assuming A_VT = 8 mV·µm for g5v0d10v5 (assumption, to be checked against the voff/nfactor-induced σ in C1b):
  - sinks: W·L 160 gives σ 0.63 mV per device, referred ×gm_n/gm1 = 1.45, so **1.30 mV**;
  - loads: ×gm_pl/gm1 = 0.71, so **0.64 mV**.
- Total σ = √(1.31² + 1.30² + 0.64²) = **1.95 mV**, so **3σ ≈ 5.9 mV ≤ 9 mV** (1.5× margin, assumption-dependent).
- The binding corner is hot (gm1 smallest): ss/125 boost gm_n/gm1 = 218/201 = 1.08, which is lower, so tt base is the worst ratio seen.

## 3. Expected values (HAND / SIM, 5 corners × 2 modes, ideal bias)

| SPEC row | spec | hand / sim value | margin | binding corner |
|---|---|---|---|---|
| A0 | ≥ 80 dB | SIM 80.3 tt base … **58.3 ss/125 boost** | **−21.7 dB ✗** | ss/125 boost (also ff/125 base 75.3 ✗) |
| A(v), \|Vod\| ≤ 1.4 V | ≥ 75 dB | SIM 78.6 tt base … 55.0 ss/125 boost | **✗** | ss/125 boost; ff/125 invalid |
| Loaded GBW base | ≥ 10 MHz | SIM min 13.2 MHz (ff/125) | +32 % | ff/125 (ss/125 base missing) |
| Loaded GBW boost | ≥ 20 MHz | SIM min 21.8 MHz | +9 % | ss/125 |
| PM (info) | ≈ 72–77° | SIM 85–86° | outside window | all; fp2/GBW 10–12 |
| SR base / boost | ≥ 12.5 / 25 V/µs | HAND 13.2 / 26.4 (12.8 / 25.6 at −3 % trim) | +2.4 % | trim floor, largest C_L |
| I_fold/I_tail | ≥ 1.2, ±10 % | HAND 1.35 by geometry | 12.5 % | mirror λ error |
| Sampled noise | ≤ 250 µV | SIM 121–157 µV (valid points); HAND 108 µV tt | ≥ 1.6× | hot (∝ T) |
| 1/f corner (info) | ≤ 631 kHz | SIM 50–100 kHz long | 6× | boost |
| Offset 3σ | ≤ 9 mV | HAND 5.9 mV | 1.5× | tt base (largest gm_n/gm1) |
| Input CM upper (tail headroom) | ≥ 0.2 V at ss/−40/3.0 | HAND/SIM 0.23 V | 0.03 V | ss/−40/3.0 boost |
| Input CM lower | linear at V_ICM − 0.33 | HAND V_DIN ≤ 1.22 V at ss/125 | 0.12 V at V_DIN 1.10; ≈ 0 at 1.25 | ss/125/3.0 |
| Stress, 1.8 V | ≤ 1.98 V | nominal 1.34 V; **fault "gates high" 2.6 V ✗ without clamp** | 0.64 V nominal | ss/−40 boost; fault case |
| CMFB 10 mV in 0.2·t_half | — | HAND f_cm 4–6 MHz, holds for kick ≤ 15–30 mV | conditional | 4 MHz boost |
| Current OTA1 | budget share | SIM core 49.4 / 98.4; HAND +3/+6 bias | fast ≈ 188 of 189 | boost, high trim corner |
| Cp_vg (β1) | ≤ 0.262 pF | SIM Cgg 0.18–0.20 + HAND 0.08 | ≈ −0.02 pF | ff/−40 boost |

## 4. Testbench plan (C1b)

Every tb prints ACCEPT/REJECT, exits nonzero on REJECT, fails on NaN or a missing measurement, and runs at all §6 corners. Expected values come from SPEC and §3, never from the DUT.

| # | tb | measures | pass limit | broken copy that must REJECT |
|---|---|---|---|---|
| 0 | **tier-1 pre-check (before schematic freeze)** | D39 boosted point with GBW 21.8 MHz, fp2 mult {3, 4, 10}, N 1024, O1/O2 | ≤ 5 ppm | — (decides C_FOLD_EXTRA, R2) |
| 1 | op dump | every device Vds − Vdsat ≥ 50 mV, region, I_fold/I_tail, node voltages vs §2.4 | table | sink m=4 instead of 8 (I_fold/I_tail 0.68) ⇒ REJECT |
| 2 | AC open loop (servo, real SC CMFB averaged) | A0, loaded GBW base/boost, fp2_eq, PM | §3 rows | cascode m_nc shorted (D–S) ⇒ A0 ≈ 40 dB ⇒ REJECT |
| 3 | static A(v) (D48 / SPEC definition) | secant gain over ±1.4 V diff, also into the model INL table | ≥ 75 dB, model INL ≤ 8 ppm | m_pl L 4 → 0.5 ⇒ REJECT |
| 4 | step diagnostic (A), `step_settle.py` | ε_dyn, ε_NL | report, health \|ε_dyn\| ≤ 1e-4 | tail ×0.5; GBW ×0.5 (m_in W/4) |
| 5 | **in-loop gate (B)** | transistor OTA1 (with chopper switches and SC CMFB) replacing the `ota="v2"` block for stage 1 in `gen_tier1.py`; OTA2 stays behavioural; N 1024 at 2 MHz (≤ 1.333 ppm) and 4 MHz boost (≤ 5 ppm); tt/27 and ss/−40/3.0; O1/O2 ladder per D43c | SPEC | I_TAIL set for 9.5 V/µs (13.3 µA) ⇒ REJECT |
| 6 | slew | ±0.49 V and full-scale steps, slower edge, C_L 1.4 pF | ≥ 12.5 / 25 V/µs | I_TAIL ×0.75 ⇒ REJECT |
| 7 | noise | `.noise` integrated at vg, closed-loop integration network | ≤ 250 µV; plus expected-value check ±30 % of §2.5 | **WO's "input pair halved" does not discriminate (§2.5).** Use instead: sinks W ÷ 4 at the same current (gm/Id ↑, α ≈ 4, ≈ +40 % noise ⇒ expected-value REJECT) and an added 4 kΩ series resistor at each gate (the 250 µV row ⇒ REJECT) |
| 8 | MC offset | ≥ 200 tt/27 + ≥ 50 worst PVT; **plus a hand add-in for the 3.3 V vth term the PDK omits** | 3σ ≤ 9 mV, every sample | input-pair mismatch ×3 (SPEC) ⇒ REJECT |
| 9 | CMFB loop | CM step 30 mV at the output, start-up from 0 and from VAPWR, Cs2 hold-phase kick | ≤ 10 mV in 0.2·t_half; converge ≤ reset window | C_r removed ⇒ no convergence ⇒ REJECT |
| 10 | device stress | max \|Vgs\|, \|Vds\|, \|Vgb\|, \|Vdb\| of m_in over power-up ramps (1 µs–10 ms), bias-off state, reset, boost toggle, 1.1·VREF overload, gates-high fault | ≤ 1.98 V | m_pp removed ⇒ REJECT; tail clamp removed in the fault case ⇒ REJECT |
| 11 | current | I(VAPWR) of OTA1 incl. bias legs, base/boost, trim codes 000/100/111 | §2.9 share | — (expected-value check ±10 %) |
| 12 | boost toggle | I_fold/I_tail in both modes, settle within the reset window | ≥ 1.2, ±10 % | sink mirror not slaved (fixed in boost) ⇒ ratio 0.68 ⇒ REJECT |

## 5. SIZES draft

`design/c1_ota1/sizes_draft.py`. Every value carries `src`:
- `op` = in the WO-20 spot run;
- `hand` = this note;
- `open` = later tb.

The proposal is `SIZES` (long variant); `SIZES_SHORT` is the comparison point. **Not settled:** V_DIN (1.10 → ≈ 1.25), C_FOLD_EXTRA, the CMFB split/device, chopper switches, and gain boosters if adopted.

## 6. Risks and open questions (ranked), with proposed SPEC change-log entries

1. **R1: A0 / A(v) fail at hot and boost corners** (SIM 58–75 dB vs 80/75).
   - Plain FC is not enough; lengthening L does not help at ss/125 boost.
   - Next steps:
     - (i) C1b op dump to find which device leaves saturation;
     - (ii) gain boosters (+4–8 µA base);
     - (iii) run gate (B) with the transistor A(v) table.
   - **P1 (proposed change-log entry):** "OTA1 DC-gain row applies to boost=0. In boost=1 the gain is gated only by the in-loop gate (B) at 4 MHz with the transistor A(v) table (≤ 5 ppm, N 1024)." Reason: N 1024 needs less A0 than N 4096 (S4: A0 effect ∝ N). Proposed only if (iii) passes without boosters.
2. **R2: PM 85–86° (fp2 ≈ 10–12× GBW)**, against the S5h evidence that fp2 ×30 gives 28.5 ppm vs the 5 ppm fast gate.
   - Needs C1b tb 0. The fix is a fold-node MIM cap for fp2 ≈ 3×GBW, and its window is narrow (±17 %) against a corner spread of ±6 %.
3. **R3: protection-cascode bias infeasible at ss/−40** with V_DIN 1.10 (SIM V_PC −0.18 V).
   - V_DIN ≈ 1.25 V removes the lower input-CM margin at ss/125.
   - Also, the "gates high" fault exceeds 1.98 V without a tail clamp.
4. **R4: CMFB speed.** A load-gate CMFB with a large L 4 load gives ≈ 2–3 MHz CM UGB.
   - Needs a short-L CMFB section (≈ 4–6 MHz) **and** an interface rule: Cs2 bottom plate rests at V_OCM1 before the hold-phase sample.
   - **P4 (interface, not a SPEC row change):** add to the §3.0 OTA1 CM row: "Cs2 bottom plate rest voltage = V_OCM1 (C4/C9)".
5. **R5: current.** OTA1 at ≈ 52/105 µA puts fast mode at ≈ 188 µA after trim; boosters would take it to ≈ 196–204 µA.
   - **P2:** if boosters are needed, either accept up to ≈ 205 µA as a D46c-type accepted risk (user decision) or cut I_SINK/I_TAIL to 1.25 (−2 µA base / −4 µA boost).
6. **R6: noise 121–157 µV vs the SPEC "expect 75–110 µV".** Within the 250 µV limit; the expectation line is informational. No change proposed.
7. **R7: MC under-reports 3.3 V mismatch** (PDK vth0_slope = 0 for g5v0d10v5); the offset is assumption-dependent (A_VT 8 mV·µm). C1b adds a hand term.
8. **R8: β1 = 0.837** (Cgg 0.18–0.20 pF).
   - **P3:** restate the OTA1 row as "β1 ≥ 0.83 (Cp_vg ≤ 0.32 pF per side)". GBW·β changes by −1 %.
9. **Tooling (WO-20 spot run):**
   - MC loop timeout;
   - invalid `.noise` at 3 long-variant corners (servo cap);
   - ss/125 base post-processing crash;
   - ff/125 A(v) invalid.
   - Fix in the C1b tb rather than in the spot script.
