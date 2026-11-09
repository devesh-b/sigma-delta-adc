# v1-design: gated design plan (system → component → verification)

Status: plan, 2026-11-07. RESUME HERE.

- **Spec source:** `SPEC.md` (block targets, §6 corner set).
- **Model:** `model/iadc.py`.
- **Verification method:** copied from Paul Thomas (`repos/sd-analog/pthomas-sigma-delta-design`) and extended to every corner.

## User rule (2026-11-07)
> System-level design, then component-level design, then a verification test suite. **Proceed to the next stage only if all results pass across all corners.** Verification follows Paul Thomas's approach.

- **Gate:** each stage ends in a gate.
  - A gate opens only when every check in it prints `ACCEPT` at every corner in SPEC §6.
  - Every check must also print `REJECT` on its broken copy (non-vacuity, WORKFLOW §11).
- **One failure keeps the gate closed:**
  - One corner, an MC result whose estimated μ ± 3σ leaves the spec or any single sample outside spec, or one vacuous check is enough.
  - The response is to fix and re-run. Specs are never relaxed silently.
  - Relaxing a spec is a **user decision**, logged in `DECISIONS.md`.

---

## 0. Paul Thomas's verification method: what we copy and what we add

| Paul's element (file in his repo) | What it does | Our version |
|---|---|---|
| `params.py` single source of truth → `spice/params.spice` | Every tier reads the same numbers | `design/params.py` derived from SPEC.md. It generates `params.spice` and feeds `iadc.py` |
| Tier 0 Python (`sim/tier0.py`, `snr.py`) | System behaviour, budgets | `model/iadc.py` (exists) plus corner-aware runs |
| Tier 1 behavioural ngspice (`xschem/tier1_sdm.sch`) | Loop with ideal-ish blocks in SPICE | SC incremental modulator with B-source OTA, ideal switches. Cross-checked against tier 0 |
| Tier 2 per-block `sim/<b>_tb.py`, sizes in a `SIZES` dict | One testbench per block, prints numbers | Same, **plus** the full §6 corner matrix and MC, ending in `ACCEPT`/`REJECT` and a nonzero exit |
| `spec_sweep.py` (OTA requirements sweep) | Finds the knee for each block parameter | `design/sim/spec_sweep.py` on tier 1 and tier 0 (A0, GBW, slew, swing, comparator offset) |
| `comp_mc.py` (seeded per-sample mismatch MC) | Deterministic, reproducible Monte Carlo | Same pattern for OTA offset, comparator offset, cap ratio |
| `gen_golden.py` + `gen_sch.py` + `xcheck_blocks.py` | Generated schematic vs golden netlist, **device for device** | Same: no hand-drawn drift between what was simulated and what is laid out |
| `ota_xcheck.py` | xschem netlist re-simulated, compared with the inline testbench | Same for every analog block |
| `pex_ota.py` / `pex_top.py` (fresh magic process, `cthresh 0`) | Extracted re-simulation | Same; block testbenches re-run on PEX at the full corner set |
| `top_tb.py` (PEX top acceptance, documented gate rationale, cold-start "ALIVE" mode, diagnostic `--ideal*` flags) | Catches broken loop, wrong DAC polarity, dead reference | Same, with incremental-specific checks (see §V) |
| `gen_rtl_vectors.py` / `gen_top_golden.py` | Golden vectors from the model | Bitstreams and accumulators from `iadc.py` → cocotb decimator testbench |
| `layout-report` (fails if DRC ≠ 0 or LVS mismatch; fresh-process DRC) | Avoids magic's false-clean DRC | Same, including the `select top cell; expand` and `writeall force` gotchas |
| `framecheck`, `antenna` (sky130 TT precheck has no antenna check) | TT-frame correctness | Same, plus the TT precheck in CI |
| `reports/results/*.json` + DESIGN.md decision log + STATUS.md handoff | Every result is machine-readable and dated | `work/v1-design/results/*.json`, `DECISIONS.md`, `STATE-<date>.md` |

**Added beyond Paul** (his design was one corner-light, 1st-order CT design; ours is precision SC):
1. **The full corner matrix is a gate condition, not a spot check.**
2. **Non-vacuity for every analog check.** Each check has a broken copy that must `REJECT`, for example:
   - OTA gain −20 dB → INL check fails
   - chop off → offset check fails
   - DAC polarity flipped → alive check fails
   - clock phases overlapping → settling check fails
3. **Operating-point dump** (Vds − Vdsat per device) in every block testbench, checked before trusting gain or noise.
4. **Model ↔ circuit independence** (WORKFLOW §11.8). Expected values come from SPEC.md or theory, never from the script that post-processes the circuit.
5. **Noise via `.noise` (AC), not `.tran`.** `.tran` has zero device noise, a lesson from Paul's DESIGN.md.

---

## 1. Corner coverage rule (SPEC §6) and what is feasible

**Full matrix:** 5 process × 3 temperature × 3 VAPWR = **45 PVT points**. On top of that:
- MC: ≥200 runs at tt/27 °C, ≥50 at the worst PVT point.
- fs: 0.25 / 2 / 4 MHz where the check depends on timing.

| Level | Corner coverage | Why |
|---|---|---|
| Tier 0 model | Full 45 PVT + MC, using **per-corner block parameters extracted from tier 2** | cheap; this is where system specs (noise, INL, offset) are proven at every corner |
| Tier 1 behavioural | Nominal + parameter extremes from tier 2 | checks tier 0 against an independent implementation |
| Tier 2 blocks (schematic, then PEX) | **Full 45 PVT + MC + fs set** | blocks are small, so this is feasible on the sandbox |
| Top level, transistor (schematic, then PEX) | **Data-driven points (review F10):** the union of tier-2 worst corners per spec (≈6–8), always including tt/27/3.3, ss/−40/3.0, ss/125/3.0, ff/125/3.6, ff/−40/3.6 and VDPWR 1.62 with VAPWR 3.6. Short windows (≤ 2048 cycles), as Paul did | long full-matrix top transients are infeasible in ngspice: TilesOS's 8192-bit run failed, and Paul gated on 2048-bit windows |

The top-level row is the user-approved interpretation of "all corners" (decision **D2**), with point selection refined per review F10. Caveat: tier 0 does not model switch charge injection, kickback, CMFB or input CM, so those mechanisms are checked only at the top-level points. System-level specs are still proven at every corner, but in tier 0 fed with tier-2 per-corner numbers. Transistor top-level runs prove the chip is alive and correct at the extremes.

---

## Stage S: system-level design

**Goal:** lock SPEC.md v1, derive per-block specs with margin, and build the tier-0/tier-1 verification base.

| ID | Work | Output | Pass criterion |
|---|---|---|---|
| S0 | Infrastructure: `design/` tree, `params.py` (from SPEC), sandbox toolchain check (ngspice ≥ 42, xschem, magic 8.3.6xx source-built, netgen, klayout, ciel-pinned sky130A, LibreLane, cocotb, iverilog), TT analog template through precheck with a dummy cell | `work/v1-design/results/s0_tools.json`, precheck log | template passes TT precheck on the sandbox; tool versions recorded |
| S1 | VREF / swing study: VREF 1.2 V (c1 = 0.25) vs 2.048 V (c1 = 0.125) | noise, effective bits, INL, peak integrator swing per option | an option exists that meets the v1 noise and INL targets with swing ≤ the OTA linear range assumed in S4. User picks if both pass (D3) |
| S2 | Chop study: OTA chop only, system chop only, both; residual vs Vos, N, vres | table of offset and noise per mode | system chop gives offset ≤ few µV at 3σ Vos; decide whether OTA chop stays in v1 (D4) |
| S3 | Error budget: allocate noise, INL, offset and gain error to blocks (OTA1, OTA2, comparator, switches, reference, clock); output **per-block spec with margin** | `SPEC.md` §3 tables updated with min/typ and the budget share | sum of allocations meets the v1 targets with ≥ 2× noise margin and ≥ 1.5× INL margin |
| S4 | Corner-aware tier 0: run the model at bounding block parameters (A0 range, a0_drop, ota_fc, Vos 3σ, comparator offset 3σ, settling at 4 MHz, leakage droop at 0.25 MHz) | `results/s4_corner_model.json` | all v1 system specs pass at every bounding set |
| S5 | Tier-1 behavioural SC modulator in ngspice: B-source OTA (finite gain, GBW, slew, swing), ideal switches, ideal comparator | tier-1 deck + `tier1_tb.py` | codes match the theory-based expected values (not the model's post-processing) within quantization over a DC sweep; INL and noise agree with tier 0 within stated tolerance; broken copies (DAC polarity, coefficient ×2) `REJECT` |
| S6 | Golden vectors: bitstreams and accumulators from tier 0 for every mode (order 1/2, N set, chop modes, internal short) | `golden/*.json` | used by C9 and V3 |
| S7 | SPEC v1 freeze + `sd-adc-design-reviewer` review | review file; SPEC marked v1-frozen | no open correctness findings |

**GATE S → C:** S0–S7 all pass, the review shows no blocking findings, and the user OKs the frozen SPEC.

---

## Stage C: component-level design (tier 2, then PEX per block)

Blocks are ordered by risk. Each one follows the same **block recipe**:
1. A design note: topology, hand calculations, expected values. The reviewer checks it **before** the schematic.
2. `SIZES` dict → golden netlist → generated xschem schematic → `xcheck` device-for-device equivalence.
3. `sim/<b>_tb.py`:
   - operating-point dump
   - every SPEC metric at **45 PVT**
   - MC (≥200 runs at tt, ≥50 at the worst point)
   - fs set where relevant
4. Results go to `results/<b>.json`. The testbench prints `ACCEPT` / `REJECT` and exits nonzero on fail.
5. Broken copy → `REJECT` (non-vacuity).
6. Layout → fresh-process DRC = 0, LVS clean → PEX → re-run step 3 on PEX. **PEX must also `ACCEPT` at 45 PVT.**
7. Feed the extracted per-corner parameters back into tier 0 and re-run S4. System specs must still pass.

| ID | Block | Key gated metrics (SPEC §3) | Broken copy that must REJECT |
|---|---|---|---|
| C1 | **OTA1 + CMFB (critical)** | A0 ≥ 80 dB (≥ 75 dB for |Vout,diff| ≤ 1.4 V), gain vs output swing (a0_drop), loaded GBW ≥ 10 MHz (20 target; boost 20 MHz), PM informational (the in-loop gate (B), transistor OTA1 in the tier-1 deck, is authoritative for INL, SPEC §3.0, D48(1); the step tb is a report-only diagnostic: health check |ε_dyn| ≤ 1e-4, watch level ε_NL ≤ 3e-7), slew ≥ 12.5 V/µs (boost 25), `.noise` white and 1/f corner, offset MC, CMFB loop PM and CM accuracy, current | input pair halved (noise), cascode removed (gain) |
| C2 | OTA2 + CMFB | relaxed A0 and noise per S3 | — same recipe |
| C3 | StrongARM comparator + latch | offset 3σ ≤ budget (Paul `comp_mc.py`), decision time < 0.3·t_half, kickback onto the integrator node, metastability at 4 MHz | latch tail starved |
| C4 | Switches, bottom-plate sampling, non-overlap clock generator | TG Ron vs signal at corners, settling τ ≤ 0.2·t_half, charge-injection offset, non-overlap ≥ min at all corners and 4 MHz | phases overlapping |
| C5 | Choppers (OTA and system) | residual offset, charge-injection mismatch MC | one chopper switch mismatched ×2 |
| C6 | Bias / startup | currents across PVT, startup from 0 V ramp (Paul's cold-start ALIVE) | startup device removed |
| C7 | Level shifters 1.8 ↔ 3.3 V | delay, duty, VDPWR/VAPWR ramp order | — |
| C8 | Reference input and decap, internal-short mux | settling τ_ref, short-mode leakage | — |
| C9 | Digital: CoI decimator, config, chop sequencer, 16-bit parallel read bus (D46b) (RTL) | cocotb bit-exact against S6 golden vectors for every mode; `rtl-verification-engineer` plan; mutation testing; LibreLane hardened, STA clean at all digital corners | mutants (acc width, off-by-one N, sign) caught. **Entry gate: golden v3 (G3 items 1-4 + D48(4): status reports the frame's boost/trim)** |
| C10 | Caps (MIM unit arrays) | ratio accuracy (c1, c2) and parasitic Cp/Cs from PEX vs S3 budget | — |

**GATE C → V:** every block `ACCEPT` at 45 PVT + MC on **schematic and PEX**. The tier-0 re-run with extracted worst-corner parameters passes every system spec, and every broken copy `REJECT`s. Reviewer sign-off per block.

---

## Stage V: verification test suite (top level, tiers 2–3)

| ID | Test | Corners | Pass |
|---|---|---|---|
| V1 | Top-schematic assembly + `xcheck` (top golden netlist vs schematic) | — | device-for-device equivalent |
| V2 | **ALIVE / cold start:** VAPWR/VDPWR ramp, reset, first conversion completes; integrators inside the linear range | extremes per §6 (6–8 points, D2/F10) | ones density in range, data-ready toggles, no rail lock |
| V3 | **DC transfer at transistor level:** ~9 DC points, order 2, N = 256 (short window) | extremes per §6 (6–8 points, D2/F10) | codes within budgeted error of the theory value; gain-error sign and size match S3 |
| V4 | **Mode matrix:** order 1/2 × chop off/OTA/system × N ∈ {64, 256} × internal short, nominal only | tt/27/3.3 | each mode produces the S6-expected code within tolerance |
| V4a | **OTA-only chop (D45 g, D46a):** (ota_en 1, sys_en 0) transistor-level at N 256, nominal; reads lf·Vos1/(N−1) directly. Also the reset-settling gate: r ≤ 1e-4 within 2 fs cycles at 4 MHz boost and at the slowest corner | tt/27/3.3 + ss/−40, ss/100 | residue measured and inside the SPEC bound; broken copy: reset window 1 cycle ⇒ REJECT |
| V4b | **Bias-trim calibration (D47, indirect):** sweep trim 0–7 in fast mode (4 MHz, boost, N 1024), inputs −0.9 / 0 / +0.9 FS; pick the lowest code with 3-point bow and gain error within 10 % of the plateau | tt, ss, ff at 27 | knee resolvable (INL falls monotonically with code to a plateau); broken copy: one trim leg open ⇒ non-monotone ⇒ REJECT |
| V3b | **Fast-mode INL (D28)** (OTA-only chop is V4a): V3 at 4 MHz boost for N 256 and N 1024 | extremes per §6 | INL ≤ 20 / 5 ppm |
| V3c | **In-loop transistor OTA gate (B) (D48(1)):** transistor OTA1 (OTA2 behavioural), then transistor OTA2 (OTA1 behavioural) in the tier-1 deck, N 1024, 2 MHz and 4 MHz boost | tt/27/3.3 and ss/−40/3.0 | OTA1: INL ≤ 1.333 ppm (2 MHz) / ≤ 5 ppm (boost), O1/O2 converged; OTA2: same limits (reference); broken copy: OTA1 tail set for 9.5 V/µs ⇒ REJECT |
| V5 | **Mixed-signal:** transistor-top bitstream → RTL decimator (cocotb / d_cosim) → same result as Python reconstruction | tt + 1 extreme | bit-exact |
| V6 | **Top PEX acceptance** (Paul's `top_tb.py` pattern): V2 + V3 on the extracted top | extremes per §6 (6–8 points, D2/F10) | same pass criteria; documented gate rationale (measured min − margin, far from failure signatures) |
| V7 | **Non-vacuity suite:** broken tops (DAC polarity flipped, OTA gain −20 dB, chop sequencer stuck, clock overlap, VREF pin open) | tt | every one `REJECT` |
| V8 | Physical: layout-report (DRC 0, LVS clean), antenna, framecheck (tied outputs, no met5, info.yaml), TT precheck in CI | — | all clean |
| V9 | **System re-proof:** tier 0 with PEX per-corner parameters, 45 PVT + MC → final predicted spec sheet (feeds PUBLICATION_PLAN F2/F9 "predicted") | 45 + MC | every v1 spec passes |

**GATE V → submission:** V1–V9 all pass, `sd-adc-design-reviewer` and `pd-expert` sign off, and the user OKs. Then Phase 5 (TT template, docs, submit). That step is outward-facing, so the user does it.

**Runner:** one resumable sandbox driver, `design/verify-all.sh`, runs every stage's checks and prints a summary table. It is re-run after any design change, and its output is copied to `work/v1-design/results/`.

---

## Schedule (part-time, rough)
| Stage | Weeks |
|---|---|
| S | 3–4 (S0 toolchain dominates) |
| C | 8–10 (C1 OTA alone ~3) |
| V | 4–5 |
| Integration + buffer | 3 |

Total ≈ 18–22 weeks. Check the next sky130 shuttle date at tinytapeout.com/runs and work backwards from it.

## Agents (WORKFLOW §6)
- **Planning and review:** Opus planners and reviewers (`sd-adc-design-reviewer`, `rtl-verification-engineer`, `pd-expert`).
- **Work orders:** Sonnet coders, one each.
- **Acceptance runs:** Haiku runs them on frozen copies on the sandbox.
- **Ledger and decisions:** `AGENTS.md`, `DECISIONS.md`.
- **Work orders:** `wo/`. The first batch is S0–S2.

---

## Review additions (REVIEW-spec-plan-2026-11-07.md), binding on the stages above
- **S1:** option B = c1 0.125 / k 0.5 (bit-identical to A); option-A c2 = 0.25 variant (E1).
- **S3:** OTA white-noise spec from a ktc_excess sweep (E2); A0 vs INL margin (F5, user Q6).
- **S5:** **simulator null test.** An ideal deck must reproduce the theory to < 1/10 of the INL target. Freeze reltol, chgtol and method in params.spice. The B-source OTA gets GBW and slew terms; run spec_sweep on them (F3).
- **S6:** golden vectors pin the exclusive-S convention (m2). They include frame tags (F4); no PGA in v1 (D14, D45 h).
- **C1/C2:** CMFB start-up with `.ic` outputs at 0 V and at VAPWR, every corner. Virtual-ground leakage measured for tier 0 (offset = I_leak/(fs·Cs)).
- **C3:** test at Δ = 0, 4 MHz, ss/−40; gate on the probability that the DAC and decimator disagree (F8). Numeric kickback gate: disturbance on x2 ≤ a fraction of the minimum x2 step.
- **C4:** input-CM sweep (F2); TG sized at ss/−40/3.0 (m4).
- **C9:** assert the chop swap happens only in the reset window, plus a "swap one cycle late" mutant. Frame tags.
- **C10:** c1/c2 ratio and Cp/Cs checks (no PGA in v1, D14).
- **V2/V3/V6:** every top-level testbench includes the TT pad model (500 Ω, 5 pF, ESD) on VIN± and VREF, plus a 10 kΩ source case.
- **V3/V6:** INL uses residue reconstruction with x2[N] (F9). Plain N = 256 codes have a ≈ 244 ppm floor, which would make the check vacuous. The OTA −20 dB copy must REJECT.
- **New V-tests:**
  - reset completeness (back-to-back ±0.9·FS; the second result is independent of the first)
  - reset charge injection (cancels in the chop pair)
  - analog/digital reset alignment (off-by-one broken copy)
  - overload 1.0–1.1·FS with recovery (m3)
  - input-CM sweep
  - ground-bounce injection if REF− is chip ground (F7)
  - boost/trim vectors (golden v3) and OTA-only chop (V4a), trim calibration (V4b)
- **V9:** lists the un-simulated risks: MIM VCC and bottom-plate parasitic, substrate coupling.
- **V8 additions (pd-expert, REVIEW-WO01-pd-2026-11-07.md):** GDS digital tie + Verilog-vs-GDS consistency; LVS with device-parameter matching; antenna via magic antennacheck (TT precheck antenna is gf180-only); 3.3 V SOA ERC (CVC); latch-up tap/guard rules; floating well/gate ERC; fill vs matched MIM (ask TT); ESD clamp + series R on ua pins; IR drop on the met4 VAPWR stripe. Precheck runs under TT's own `tools/precheck/default.nix` nix-shell (magic 8.3.568, klayout 0.30.8) and is re-run on tt-support-tools main before submission.
