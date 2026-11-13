# WO-59: DESIGN_BOOK.md, a complete technical design book (user request, 2026-11-13)

Coordinator-written. **Tier: writer (Opus).** Fresh agent. A document only: no design changes, no simulations.

## What the user asked for
"A very detailed document on the design and its values, and details on how the values were achieved. Explain all the fundamentals leading to this, even the basics of sigma-delta ADC, and how we chose each topology and its reason, with great technical detail and depth."

## Output
- `DESIGN_BOOK.md` at the repo root, in Markdown (user rule: "doc" = Markdown).
- For figures, use ASCII/Markdown diagrams and LaTeX-style math in `$...$` / `$$...$$` (GitHub renders it).
- Write it section by section with Write/Edit, appending part by part. Do not try to write it in one call.
- Target length: thorough, around 15–25k words.

## Sources (read them; every number must come from a source, with the source cited inline)
- `SPEC.md` (frozen spec plus the change log CL-1…CL-32)
- `work/v1-design/DECISIONS.md` (D1…D78)
- `DESIGN_GUIDE.md`, `CONTEXT.md`, `ROADMAP.md`, `SIZING.md`, `ACHIEVABILITY.md`, `MCP3421_TARGET.md`, `NOTES.md`
- `work/v1-design/PLAN.md`, `work/v1-design/RESUME.md`
- All `work/v1-design/REVIEW-*.md`, `work/v1-design/LEARNINGS-pthomas-2026-11-10.md`, `work/v1-design/C9_VERIF_PLAN.md`
- `model/` (`iadc.py`, studies, README) and `golden/README.md`
- `design/*/DESIGN.md` (c1_ota1, c3_comp, c4_sw, c6_bias, c9_digital, plus `c9_digital/HARDENING.md`)
- `work/v1-design/results/*/README.md` (WO-23 … WO-57)

## Required structure
### Part I: Fundamentals (from first principles, with equations)
1. Sampling, quantisation, quantisation noise; SNR = 6.02N + 1.76.
2. Oversampling and noise shaping:
   - NTF and STF;
   - first- and second-order modulators;
   - the in-band noise formula vs OSR;
   - why a 1-bit quantiser is inherently linear.
3. Loop stability:
   - overload, the input range;
   - integrator state swing;
   - loop delay, and why the extra delay matters (link to D76 / WO-53).
4. Discrete-time vs continuous-time ΣΔ:
   - jitter, excess loop delay, RC spread;
   - why DT/SC for a precision DC ADC (cite the current-vs-voltage-mode discussion and its reasons).
5. **Incremental ΣΔ:**
   - reset;
   - finite N;
   - the cascade-of-integrators (CoI) decimator;
   - exact reconstruction of u from the accumulators;
   - INL and resolution vs N;
   - order-2 numerator/denominator, and why the forced y[0] exists.
6. Switched-capacitor circuits:
   - charge transfer;
   - the stray-insensitive integrator;
   - bottom-plate sampling;
   - kT/C noise;
   - charge injection and clock feedthrough;
   - non-overlapping clocks.
7. Offset and 1/f noise; chopping (OTA chop vs system chop, residues).
8. Fully differential circuits and CMFB:
   - why fully differential;
   - SC CMFB;
   - static error with no in-loop gain;
   - the dual-path idea.
9. OTA fundamentals:
   - gm/Id;
   - the folded cascode;
   - DC gain;
   - GBW and phase margin with feedback factor β;
   - slew vs linear settling;
   - why finite gain with signal-dependent droop causes INL;
   - the A(v) table method.
10. Noise in SC loops: sampled thermal noise, noise gain, the direct vs conventional path (D71).
11. Mismatch: Pelgrom A_VT; the PDK MC limitations for 5 V devices (vth0_slope = 0).
12. Comparators: StrongARM; offset, noise, kickback, metastability.
13. Bias references: bandgap/Banba, PTAT/CTAT, trim, start-up and multiple equilibria (the C6 story).
14. PVT corners, Monte Carlo, and why "green is not proof" (broken copies).

### Part II: System design (Stage S)
- The target (MCP3421 case study) and the Tiny Tapeout constraints:
  - sky130A;
  - the analog 2×2 tile;
  - pin pricing €40/€40/€100/€100;
  - supplies;
  - area.
- Every system choice with its alternatives, reason and numbers:
  - incremental vs free-running;
  - order 2 CIFB;
  - coefficients c1 0.125 / c2 0.5 / k 0.5;
  - VREF 2.048;
  - Cs 0.5 pF and Cint;
  - fs 2/4 MHz and boost;
  - N 64…4096;
  - the chop modes;
  - order-1 mode;
  - the noise / INL / offset / gain budgets (SPEC §2–§3.0) and how each was allotted;
  - S-model results (S1…S7), tier-0 / tier-1 / gate B.
- Golden vectors (v2 → v3.2) and the digital conventions (§3.7a).

### Part III: Block designs (Stage C)
For each block: purpose, interface, topology alternatives and the choice with its reason, hand calculations, sizes, the decision history (cite D-numbers and CL-numbers), simulated results per corner (tables), the broken copies, and open items.
- **C1 OTA1 + CMFB.** The full history:
  - rev A/B/C;
  - precision A0, composite refs (and their failure), parallel 1:8 refs;
  - K_P/K_N, replica bias;
  - CMFB evolution: passive SC → CM amp → dual path; Cr ×2; TG clamp;
  - the noise work (sinks, L 8, the 390 µV row);
  - gate B results.
- **C2 OTA2:** not started; list the inputs found so far (the 45 mV CM kick, the x2 peak of 1.41 V).
- **C3 comparator:** rev a–d.
- **C4 switches / phase generator / level shifters:** rev a–b.
- **C6 bias:** WO-45 → WO-55.
- **C9 digital:**
  - RTL architecture;
  - port contract;
  - the D66/D70/D72/D74/D77 contract decisions;
  - verification (independent bench, Ref A, golden, mutation 64/65, coverage, formal);
  - hardening.
- **C5, C7, C8, C10:** status.

### Part IV: Verification methodology
- tier-0 / tier-1 / transistor;
- spot vs full runs;
- gates and broken copies;
- the false-pass lessons: latched tb9 bench, transient-op fallback, solver convergence ladder;
- determinism;
- the sandbox / lpool process;
- review gates.

### Part V: Status, open items and risks (as of 2026-11-13)
Mark every value that is still pending a run.

### Appendices
- glossary;
- the decision index (D-number → one line);
- the change-log index;
- the symbol table.

## Rules
- Technical depth over prose. State units.
- Every numeric value carries a source reference (a file plus D/CL/WO).
- Never invent a number. If something is unknown or pending, say so.
- Calm, factual tone.
- Do not run anything on the sandbox and do not edit any other file.
- Commit only `DESIGN_BOOK.md`, with explicit paths, no trailers and no push.

## Budget
At most 70 tool calls. Report in ≤ 20 lines: the outline, the word count, and any gaps you could not source.
