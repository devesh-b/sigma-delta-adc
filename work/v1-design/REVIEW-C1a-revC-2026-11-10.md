# REVIEW C1a rev C: OTA1 + CMFB (WO-23; 289aec7, 61ca6a7), 2026-11-10

Reviewer: sd-adc-design-reviewer. Read-only. Condensed by the coordinator.

## Verdict: PROCEED TO C1b WITH CONDITIONS
- No Critical findings; three Majors, all fixable inside WO-24 steps 0–3.
- **Closed:** RB-M1, RB-M2 (spot level), RB-m3, RB-m4.
- **Carried into C1b:** RB-m1 (tb13), RB-m5 (timing), RB-m6 (tb10), RB-m7 (junction and chopper caps), RB-m8 (real CMFB in the tables).

## Major

### RC-M1: Precision A0 sits on the m_pl soft-saturation edge (PROVEN)
- In run 4, raising K_P base from 7 to 8 moved A0 by +3.0–3.5 dB (fs/125 76.5 → 79.5, ff/−40 76.2 → 79.7, tt 77.8 → 80.9).
- D55 alone at fs/−40 base gives at most 78.4 + 1.16 = 79.56 dB, and less in practice because the degraded ro_pl dominates.
- **Fix:** K_P base 8 → 10. Set vbpc base to I_NC/22.4 and BOOST_SCALE["vbpc"] to 0.7, so boost stays at K 7. Cost is +0.14 µA in base and no area; base span drops about 0.1 V from ≥ 1.8 V.
- Keep D55 alongside: m_plc 15/2 → 30/4 (same W/L), Cc 0.1 → 0.2 pF, and Cr scaled to about 50 fF.
- **Sweep first:** K_P base {8, 9, 10, 11} × m_plc {15/2, 30/4}.
- **Exit:** A0 ≥ 80.3 dB at all 9 PVT in the netlisted deck, plus the A0 MC spread at fs/−40 base.
- **Do not lengthen m_pl to L 6.** At W 80 it costs about 0.04 V of boost span. At W 120 the bp node becomes ≈ 2.4 pF and settling takes about 5.9 µs, which breaks CL-7.

### RC-M2: Single-finger 1:32 references dominate mirror mismatch (REASONED, using A_VT 8 mV·µm)
- **Tail:** σI ≈ 2.9 %. **Sink:** ≈ 1.9 %.
- **3σ effect:**
  - I_fold/I_tail falls from 1.35 to about 1.21, at the edge of the ≥ 1.2 row;
  - SR falls to about 12.1 V/µs (about 11.7 at the trim floor), against 12.5;
  - boost GBW drops about 9 %, to about 24.6 MHz at 1.4 pF.
- The global trim does not see a local mirror error.
- **Fix:** build each reference as a series-parallel composite of identical unit fingers (for example 4 × 4). That gives σ/4 at about +350 µm² gate area and 0 µA. A 1:16 ratio would cost about 1.4 / 2.8 µA instead.
- **Verification:** tb8b must measure the reference-to-mirror ratio of all four 1:32 mirrors in both modes.

### RC-M3: The precision table-INL gate has no broken copy that fails it, and mode is mixed with corner (PROVEN)
- The PMOS-cascode-short copy ran at ss/125 boost (9.86 ppm, rejected) but at tt/27 base (3.37 ppm, blind). These runs differ in both mode and corner.
- A flat gain loss cannot fail an INL gate (WO-22: a flat 60 dB table gives 1.47 ppm). Flat loss is the job of the A0 ≥ 80 dB row.
- **Reword CL-1c per mode:**
  - **Boost INL gate:** PMOS cascode short at ss/125 boost.
  - **Precision INL gate:**
    - (i) A synthetic known-answer table: the S4 droop shape anchored at 76 dB (8.51 / 8.31 ppm) must REJECT at both N. Do not anchor it at 80 dB, because N 4096 then reads 5.25, which passes.
    - (ii) A circuit droop copy at ss/125/3.0 base, for example V_OCM +0.5 V or vbpc ÷ 4 (K_P ≈ 2). Accept it only if it is predicted at ≥ 1.5× the gate.
  - **Precision A0 row:** the PMOS cascode short must REJECT there.
  - Run each mode's broken copy at the same corner, so mode and corner effects separate.

## Minor
- **RC-m1: split K_P is sound.**
  - Physics: in moderate inversion, base needs a larger K.
  - Tracking: one device and ratioed current densities.
  - Settling: about 0.5 µs.
  - But vbpc steps ×1.75 (×1.4 with K_P 10), not ×2 as D43b says. That needs a C6 spec line, coverage in tb12 for both directions and in tb11, and a broken copy: K 8 in boost ⇒ span 1.355 V.
- **RC-m2: D55 lowers f_cm.** About 5.1 MHz base and about 8 MHz boost. tb9 in boost (≤ 10 mV in 22.5 ns) needs ≥ 9.4 MHz, so it likely misses by about 15 %. Options: Cc 0.25–0.3 pF or m_plc L 3. Scale Cr with Cc.
- **RC-m3: β1 0.831 against 0.83 is a margin on a proxy** (estimated routing and PEX). The physics impact is about 1 %. Options: make CL-4 informational with gate B authoritative, or set it at ≥ 0.82. A miss here should not force a revert of D54.
- **RC-m4: span margin 0.01 V is against the ±1.4 V table target.** The signal needs about 1.2 V, so the real headroom is about 0.2 V. Add per-side top and bottom checks with the real SC CMFB V_OCM error.
- **RC-m5: `revc_inl.py` always exits nonzero,** because the sensitivity rows count as must-reject. Tag them `info`.
- **RC-m6: DESIGN.md is stale against rev C:**
  - header;
  - §1.1 and §1.2;
  - §2.9 (1:8 / 1:6 ratios, 196 µA);
  - §3 and §5;
  - the rev C table (it says L 6, the file has L 7);
  - the sizes_draft and revc_inl docstrings.
- **RC-m7: do not size C_FOLD_EXTRA from fp2/GBW at the 1.4 pF lump** (see Q4).

## Q4 (GBW and fp2)
- The real in-loop loads are 0.78 pF (integrate) and 0.90 pF (hold), so the real GBW is about 1.5× the 1.4 pF figure (≈ 40+ MHz). fp2 is independent of C_L.
- So fp2/GBW_real ≈ 0.64 × (3.4–6.1) × 0.7–0.8 (junction caps) ≈ **1.5–3.1**, already at or below the WO-22 window without any extra cap.
- A C_FOLD_EXTRA sized at the 1.4 pF lump could push fp2 onto the sharp low-mult side.
- Gate B likely does not fail on GBW, so the D54 current fallback is unlikely.
- **First measurements, in order:**
  1. Netlisted op/AC with junction caps at the 4 hot corners, boost; GBW at both C_L definitions.
  2. Gate B at fs/125 boost with C_FOLD_EXTRA = 0.
  3. Only if that fails: a 2D GBW × mult scan at the real loads.

## WO-24 order (steps and exits)
| step | work | exit |
|---|---|---|
| 0 | Sync DESIGN.md to rev C; fix the revc_inl info tagging | single source of truth; a nominal run exits 0 |
| 1 | K_P base 8–11 × m_plc sweep | A0 ≥ 80.3 at 9 PVT, base span ≥ 1.6 V |
| 2 | Netlist generator: ad/as/pd/ps, composite references, fold chopper, 3.3 V switches, real SC CMFB, level-shifted clocks | lint clean; tt converges; margins ≥ 50 mV; m_nc-short copy rejects |
| 3 | tb1/tb2 op/AC, 9 PVT × 2, CMFB as a DC equivalent | A0 precision ≥ 80.3; hand A0 within ±1 dB; GBW and fp2 at both C_L definitions |
| 4 | tb9 CMFB transient, boost hot | ≤ 10 mV in 0.2·t_half; start-up from both rails |
| 5 | tb3 tables with real CMFB + table-INL + per-mode broken copies | CL-1b; every broken copy REJECTs |
| 6 | Gate B: fs/125 boost first, then ss/125, ss/−40, tt; C_FOLD_EXTRA 0 | ≤ 5 / ≤ 1.333 ppm, O1/O2 |
| 7 | tb12 (with vbpc ×1.75) and tb11 | 4 µs; ≤ 189 µA |
| 8 | tb8/tb8b MC | 3σ offset ≤ 9 mV; I_fold/I_tail ≥ 1.2 at 3σ |
| 9 | tb7 noise, tb6 slew at −3σ, tb4 step | SPEC rows |
| 10 | tb10 stress, tb13 switches | ≤ 1.98 V; Ron |
| 11 | Full 45-PVT batch | all ACCEPT |

## Questions and coordinator answers
1. How does the tier-1 macro apply C_L? → WO-24 step 3 documents it, by reading gen_tier1.
2. Are the SR and GBW rows nominal per corner or at 3σ? → Nominal per corner, plus the tb8b MC check that I_fold/I_tail stays ≥ 1.2 at 3σ, plus composite references (RC-M2). SR at the −3σ tail is reported, not gated, unless the user chooses otherwise.
3. Does the trim see OTA1's own current? → No, it is a global reference trim (D42).
4. Does the tb9 limit apply at 4 MHz boost? → Yes.
5. Is D55's Cc 0.2 pF still needed if K_P 10 alone reaches ≥ 80.3 dB? → Decide after the step-1 sweep. That is the user's option, since D55 was the user's decision.
