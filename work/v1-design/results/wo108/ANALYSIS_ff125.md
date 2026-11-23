# WO-108 BIAS_EXT: ff/125 failure analysis (2026-11-24)

The analysis was done by an Opus analyst, read-only. No new simulations were run.
- Results read: run `WO-108-796658b`, `/home/mempool/regr/tt/WO-108-796658b/out/cz`.
- Code read: `design/cz/c6_cz.py` at 796658b.

## Summary

| Item | Root cause | Class | Fix |
|---|---|---|---|
| G3 lost current at ff/125, 25.6–28.7 nA (limit 20 nA) | The 10 pF pin discharges through the ext diode in subthreshold, so I ∝ 1/t. The tail scales with kT and with pin capacitance, which includes board capacitance and is unknown. | Design | D1 |
| G4 leakage with ext on at ff/125, 4.8–5.8e-3 (limit 1e-3) | In sel 0 the live ext mirror pulls the e-nodes to 0 V. The off ext-TG then sees the full Vds and leaks about 2.3–2.7 nA into each port. | Design | D1 |
| 11 ff/125 s0/lk aborts | s0: the bare c6_bias reference deck (`_b`) aborts; the wrapper decks complete. lk: the 125 °C ramp start at t = 10 ns aborts. | Bench (numerical) | B1 |
| s1z stress, −0.66 V (tt) / −0.81 V (ff) vs −0.6 V | The 1 Ω × 10 pF pin short (about 10 ps edge) couples through the sense-cascode Cgd into the high-impedance node esn. The SPEC pair rule is met. | Mostly bench, small design margin | D2, B2 |

**Harness bias:** keep K = 5 (5.35 µA design point). Use 5.25 µA as the default harness setting (−1.9 %) and 5.5 µA as the second point. Not 5.0 µA.

## 1. G3 lost current
- The gate is the 4 µs mean of i_lost at 326–330 µs, which is 56–60 µs after removal at 270 µs (`c6_cz.py:300`). The limit is 20 nA (`:67`, `:304`).
- i_lost by corner:

  | Corner | i_lost |
  |---|---|
  | tt | 19.88 nA |
  | ss/−40/3.0 | 15.6 nA |
  | ss/−40/3.6 | 16.3 nA |
  | fs/−40 | 16.2 nA |
  | ff/125/3.0 | 25.6 nA |
  | ff/125/3.6 | 26.4 nA |
  | ff_ll | 26.4 nA |

- The ibn tail at tt: 225 nA (+5 µs), 108 (+10), 54 (+20), 36.6 (+30), 27.9 (+40), 22.7 (+50), 19.3 (+60). I × t ≈ 1.1–1.2 pA·s is nearly constant, so the current falls as 1/t.
- The pin decays logarithmically: 0.119 V per e-fold at tt and 0.161 V at ff. The ratio 1.35 matches 398 K/300 K = 1.33, and the i_lost ratio ff/tt is also 1.33.
- With a hard 0 V off state (s1z), i_lost is 3.1 nA (tt) and 5.1 nA (ff). The DC floor from the 5 nA pin leakage is ≤ 2.9 nA, so the failure is the transient tail.
- **Root cause:** the ext diode is the only discharge path for the pin capacitance, and the output mirrors follow it. ok falls within 5 µs, but the ports keep a decaying bias for hundreds of µs. On the board, at 50–100 pF, the tail would be 100–250 nA at 60 µs at every corner.
- Relaxing the limit or moving the window is not proposed: it would make the result depend on an unknown board.

## 2. G4 leakage with ext present

| Case | ibtp | ibp | ivbl0 | ibn | worst |
|---|---|---|---|---|---|
| lke5 ff/125/3.0 | +2.25 nA | +2.25 | +2.24 | −0.01 | 4.77e-3 |
| lke20 ff/125/3.0 | +2.25 | — | +2.25 | — | 4.79e-3 |
| lke5 ff/125/3.6 | +2.72 | — | +2.70 | — | 5.75e-3 |
| lke20 ff/125/3.6 | +2.72 | +2.72 | +2.71 | +0.03 | 5.78e-3 |
| lke20 tt/27/3.3 | +0.004 | +0.004 | +0.004 | −0.12 | 5.6e-5 |
| lk tt/27/3.3 (ext 0 V) | −0.0006 | — | −0.00002 | — | 5.6e-5 |

- The extra current is the same absolute value on every sink and in base and boost. It does not depend on the ext current. It rises with VDD through DIBL, and it is about 600× smaller at tt.
- **Root cause:** in sel 0 the ext replica stays biased.
  - Its sink outputs (`emc*`, `:111-112`) pull `e_<port>` to about 0 V.
  - The off ext-TG NMOS (2/0.5, Vgs = 0, `:101`) then has Vds = VDD − 0.3 V and leaks about 2.3–2.7 nA at ff/125.
  - With ext at 0 V the e-nodes float to the port voltage, so Vds ≈ 0. That is why lk, tt and ss are clean.
- The mirror case in sel 1: the off c-path TG leaks about 2.6–3.0 nA. That is 0.6 % of ivbl0, inside the G2 limbs, and is reported only.
- The 0.1 % limit is the definition of "sel 0 equals verified C6", so it stays.

## 3. ff/125 aborts (11 cases)
- **s0 family:** only the `_b` deck aborts.
  - "Timestep too small" at 14.7 µs (vbmn#branch, 3.6 V) and at 20.5 µs (vbmbl#branch, 3.0 V).
  - The `_b` deck is bare c6_bias plus the OTA1 diodes, with no wrapper device. `run()` then writes REJECT "no data" (`:220-241`).
- **lk family:** the combined deck aborts at t = 10 ns (the ramp start) on `vzfx_ibn#branch`. The fixed port sources are DC at their final value while VDD sits at 0.05 V until 10 ns, so the PMOS TG drain–nwell junctions are forward-biased. That state does not occur on silicon.
- The current options are gmin 1e-11, reltol 1e-5, abstol 1e-14 (`:167`), with no rshunt. Precedents in `c6_spot.py:201-215` (WO-55/64/80/87): rshunt 1e12 with itl4 200, and abstol 1e-12.
- **Class:** bench. G1/G4 at ff/125 is unverified until these run.

## 4. s1z stress undershoot
- Minima:
  - tt: esn −0.661 V, vn2e −0.586 V;
  - ff/3.6: esn −0.807 V, vn2e −0.578 V;
  - all at 270.001 µs, when Sz closes (ron 1 Ω, `:178-179`). Boost also turns off at 270 µs (`T_BOOST = (210, 270)`, `:72`).
- esn is the drain of the 16-unit sense cascode (`:118`), loaded only by the 0.87 MΩ pull-up and the schmitt input, so it is high-impedance.
- SPEC row 99 (D80) is a pair rule: the worst pair is 4.48 V (ff/3.6) and 4.09 V (tt), both ≤ 4.95 V. The ±0.6 V bound is a bench proxy.

## 5. Nominal current against the harness steps
- 5.35 µA = 5 × 0.535 µA, with K an integer number of unit fingers. An exact harness step would need K = 9.81, 10.28 or 9.35, none of them integer.
- With K = 5: 5.25 µA gives −1.87 %, 5.5 µA gives +2.80 %, 5.0 µA gives −6.54 %.
- In ext mode the C6 trim is bypassed. The 250 nA step (4.7 %) plays the role of the trim step (5.5 %), and −1.9 % is inside the ±3 % residual of SPEC row 103.
- **Recommendation:** keep K = 5. Default harness setting 5.25 µA; 5.5 µA as the second characterisation point.
- Exact-match option, not recommended: K = 7 gives 3.745 µA, which matches the 3.75 µA step (+0.13 %). The costs are a coarser step and a full G2/G3 re-verification.

## 6. Ranked fixes

**D1 (design, rank 1): output enable on the ext mirrors.** It fixes G3 and G4.
- Split the cascode-gate net of the ext outputs (`emc<p><i>`, `emfc`, `:112-113`) into `ecg`. Feed it from bias_ext through a 3.3 V TG (N 2/0.5, P 4/0.5) enabled by en = sel_i AND ok_e (hvl nand2_1 + inv_1), plus an NMOS pull-down ecg → vss on en_b.
- Add a PMOS pull-up vpe → vdd when disabled. Without it the ibn PMOS mirror keeps a tail: 22.6 nA at +10 µs at tt.
- The diode stack and the sense leg stay on bias_ext, so the detect keeps working and there is no lock-up.
- Expected: G4 at ff/125 back to about 5e-5. Lost current drops to the c-path floor (≈ 3 nA at ff) within the ~5 µs detect delay, independent of board capacitance.
- Cost: 6 devices plus 2 hvl cells.
- Risks:
  - In sel 1 the bias depends on the detect. Near the 0.9–1.7 µA threshold the ports switch fully on or off, so the 1 µA info row at ff reads 0.
  - About 10 ns of gate settling.
  - The off pull-down leaks about nA at 125 °C, ≤ 0.1 % at 2.5 µA.

**D2 (design, rank 2): esn capacitor.** About 100–200 fF from esn to vss. The undershoot should roughly halve, and the detect slows by about 0.2 µs. Adopt it only if B2 alone leaves esn below −0.6 V.

**B1 (bench, rank 1): ff/125 convergence.** A one-change ladder on `cz_s0_ff_125_3_none_b` and `cz_lk_ff_125_3.6_none`:
1. rshunt 1e12 with itl4 200 at 125 °C;
2. abstol 1e-12;
3. lk only: ramp the fixed port sources with VDD.

Apply the result to `_b` and `_z` alike.

**B2 (bench, rank 2): s1z timing.** Move the boost-off edge away from the pin event, for example `T_BOOST = (210, 265)`.

**Not proposed:** widening ±0.6 V, raising the 20 nA or 1e-3 limits, or moving the lost window.

## 7. Gate limits

| Gate | Change | Justification |
|---|---|---|
| G1 | none | 0.1 % = "equals verified c6_final" |
| G2 | Absolute limb expectation = PORT_I × I/5.35 µA, also at 5.25 and 5.5 µA (new STEPS windows). Limits stay ±3 % / ±4 %. | The harness value is a known input; kwrong still rejects |
| G3 | Add an early window, 276–280 µs, at 20 nA. Keep +60 µs. Add kind s1c (pin 100 pF). | Tightening: fail-safe must not depend on board capacitance |
| G4 | none (1e-3) | Same as G1 |
| stress | Keep ±0.6 V. Add a SPEC row 99 limb: max − min ≤ 4.95 V. | Adds the real SPEC rule |

## 8. Runs needed later (each broken copy must REJECT)
1. **B1 ladder** on the two decks. Then an option-neutrality check on s0/lk at tt and ss/−40/3.6: every port within 1e-5 of 796658b.
2. **G1** s0/s0e5/s0e20 at all 5 corners with D1, D2 and B1. swapsel (s0) and noiso (s0e5) at tt and ff.
3. **G4** lk/lke5/lke20 at all 5 corners. Broken copies: `noen` (the 796658b topology) on lke20 ff/125/3.6; `leaky` (lk) and `noiso` (lke20) at tt and ff.
4. **G3** s1/s1z at all corners plus the extras, and s1c at tt, ss/−40/3.0 and ff. Broken copies: `noen` on s1c at tt and ff; `nopu` on s1z tt (+10 µs window); `nodetect` and `rupq`.
5. **G2** with the 5.25 and 5.5 µA windows. `kwrong` and `efinger` at tt and ff. D1 must leave tracking within 1e-3 of 796658b.
6. **Stress** after D2 and B2: s1z at tt, ss and ff, and s1 at all corners. `overv` must reject both limbs. `nocap` on s1z ff must reject ±0.6 V.
7. **Variant `nosu`** at tt and ff must ACCEPT. It now REJECTs only on G3 at ff/125/3.6.
8. **Detect corners with D1:** s1 at ff_ll, ss_hh and fs. Ports on at 2.5 µA; `rupq` must REJECT.

D1 and D2 are design changes, so sd-adc-design-reviewer reviews them before item 2 and again after the results.
