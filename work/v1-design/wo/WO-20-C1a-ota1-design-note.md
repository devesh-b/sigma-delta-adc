# WO-20 (C1a): OTA1 + CMFB design note (block recipe step 1)

Coordinator-written, 2026-11-09. **Tier: design (Opus), because this is planning and sizing, not coding.**

The note is the first block-recipe step (PLAN Stage C): topology, hand calculations, expected values. `sd-adc-design-reviewer` checks it **before** any schematic or netlist. The SPEC is frozen (`spec-v1`), so if a SPEC row looks unbuildable, report it as a proposed change-log entry. Do not edit SPEC.

**Read first:**
- SPEC.md §3.0: the OTA1 rows (GBW/PM, slew, noise, 1/f/chopper, A0/A(v), CM/CMFB, devices D40, current, bias D43b), the Clock row, §3.6 chopper rules, §6 corners;
- DECISIONS D25, D39–D44, D48;
- `work/v1-design/results/gmid_table.md`;
- SIZING.md;
- ACHIEVABILITY.md, OTA sections;
- Paul Thomas's folded-cascode OTA in `repos/sd-analog/pthomas-sigma-delta-design` (or `ttsky-sigma-delta`): read its sizing and methodology, and note what you reuse;
- PLAN C1 row.

**Sandbox:**
- Small ngspice `.op` / `.ac` checks are allowed to confirm hand numbers, using the sky130 models via the existing tier-1 env, at tt, plus ss/−40 for gm/Id.
- At most 2 processes, nice and timeout, no shell wait loops.
- Delete any raw csv after reading it.

## Deliverable: `design/c1_ota1/DESIGN.md` (new) plus `design/c1_ota1/sizes_draft.py` (a SIZES dict draft)

The note has these sections:

1. **Topology choice, with alternatives rejected:**
   - Folded cascode with a PMOS `pfet_01v8` input pair on 3.3 V (D40a), with protection cascodes so every terminal pair stays ≤ 1.98 V.
   - Switched-capacitor CMFB (D40b), with its caps inside C_L.
   - OTA chopper on OTA1 (config bit, D4/E2).
   - Boost through the one switched reference leg with every mirror slaved to it (D43b): I_fold/I_tail ≥ 1.2 and constant ±10 % in both modes.
   - Compare at least one alternative (for example telescopic, or a two-stage Miller) on swing, gain, power and stress.
2. **Hand calculations at the worst corner** (ss/−40/3.0 for gm and slew; ff/125 for leakage and stress where relevant), base and boost:
   - **Current from slew:** I_tail from SR 12.5 V/µs (25 boost) into C_L 1.4 pF diff (D44/D39). Show it per side.
   - **GBW:** gm from loaded GBW ≥ 10 MHz base / ≥ 20 MHz boost at β1 0.84 and C_L 1.4 pF.
   - **Sizing from gm/Id:** the gm/Id needed and the W/L, from gmid_table per device (I_tail/2, G-M2), with L choice and justification.
   - **A0 ≥ 80 dB and A ≥ 75 dB for |Vout,diff| ≤ 1.4 V:** the cascode gm·ro budget per stage and the headroom stack at 3.0 V. State the static large-signal A(v) definition used.
   - **Output swing** and input CM range (D34/§3.0 row), with V_icm proposed for ≥ 0.2 V tail headroom at ss/−40/3.0.
   - **Noise:** sampled thermal noise at the virtual ground (≤ 250 µV rms diff; expect 75–110 µV) and the 1/f corner estimate; chopper residue.
   - **Second pole:** fold-node pole, fp2/GBW, and hand PM. Compare against the S5h finding that the optimum is ζ ≈ 0.9 (PM ≈ 72–77° at 20 MHz). Say how fp2 is set by sizing.
   - **CMFB loop:** SC CMFB cap values, its loop GBW/PM, and absorbing the per-cycle CM charge to ≤ 10 mV in 0.2·t_half. Start-up from either rail.
   - **Device stress:** list every node at power-up, reset, boost toggle and 1.1·VREF overload; give the protection-cascode bias.
   - **Current:** OTA1 share against the D41/D42 budget (precision ≈ 106–113 µA total, fast ≈ 189 µA worst after trim), base and boost.
   - **Offset 3σ:** Pelgrom estimate from sky130 mismatch, against ≤ 9 mV 3σ.
3. **Expected-values table:** every SPEC OTA1 row, with the hand value, the margin, and the corner where it binds.
4. **Testbench plan** (C1b), per SPEC row:
   - list each tb: op dump, AC, step diagnostic (D48 A definitions), slew, noise, MC offset, CMFB loop, device stress, and current;
   - **the in-loop gate (B):** how the transistor OTA1 goes into the tier-1 deck (OTA2 behavioural), N 1024 at 2 MHz and 4 MHz boost, converged at O1/O2;
   - for each check, the **broken copy that must REJECT**: input pair halved for noise, cascode removed for gain, tail current set for 9.5 V/µs for the in-loop gate, protection cascode removed for stress, and so on.
5. **SIZES dict draft:** every device W/L/mult, bias currents and voltages, caps. Mark which values are hand-derived and which still need sim confirmation.
6. **Risks and open questions**, ranked. Include anything in SPEC that the hand calculations say is marginal, as a proposed change-log entry.

## Commits (explicit paths, no attribution trailer, no push)
`design: C1a OTA1 design note + SIZES draft`

## Budget
At most 45 tool calls. Report: topology, the key hand numbers (I_tail, gm/Id, W/L, A0, fp2/PM, noise, current), the binding corner per row, and the top 3 risks.
