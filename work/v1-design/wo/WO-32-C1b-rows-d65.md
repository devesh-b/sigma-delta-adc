# WO-32 (C1b part 3a): D65 row fixes, SPEC change-log entries, TG clamp, CM-to-DM bound + mismatch copy, near-knee copy

Coordinator-written, 2026-11-11. **Tier: design (Opus).** Sources:
- `work/v1-design/REVIEW-C1b-final-2026-11-11.md`;
- D47, D57–D65;
- results/wo29–wo31;
- `design/c1_ota1/*`, `design/tier1/*`, `model/iadc.py`;
- SPEC.md rows 94–98 and its change log.

**Sandbox:** same rules as WO-31.
- New frozen copy per commit run, with golden/.
- **Single-threaded ngspice:** put a `.spiceinit` with `set num_threads=1` in the frozen copy root.
- At most 5 own processes. Absolute paths, markers, no pgrep/pkill, no wait loops, delete csv files.
- **No local python.**

## Items
1. **SPEC change log (D65).** Add CL entries with reason and decision ID:
   - SR floor re-based on the gate-B knee + 3σ (state the knee per mode from the D44/WO-22 data and gate B, and the resulting floor);
   - SPEC row 98 text → D63 sampling-instant wording;
   - start-up: CM settled before the first valid conversion.
   - Edit only rows 94–98 and the change log. SPEC stays FROZEN otherwise.
2. **Rows in c1b_opac.py.**
   - New SR floor: SR − 3σ ≥ new floor.
   - The ceiling stays a power row.
   - Add a C6 reference-accuracy info row: the I_REF window the rows allow, per corner.
   - Update the bkt copy so its role matches.
3. **Start-up (D65).**
   - tb9 start-up row: CM at the ph2 sampling instants within 10 mV of steady state by 4 µs.
   - Output clamp → transmission gate (size it; 0 µA).
   - Broken copies: mcr05 must still REJECT; a weak-clamp copy (PMOS only, W/4) must REJECT.
4. **CM-to-DM (D65).**
   - Derive the signal-dependent CM-to-DM bound from the S-model. Constant CM-induced DM offsets cancel in endpoint INL, so only the u-dependent part counts. Write the derivation in DESIGN.md.
   - Then add a 3σ mismatch copy in tb9: Cs, Cint, Cc, Cr p/n at 3σ of the sky130 MIM matching (state the source), plus the input-pair ΔVt at A_VT 12 (pfet_01v8: use PDK MC or hand delvto). Run it against the bound at tt and fs/125.
   - Keep masy as the broken copy.
5. **Near-knee gate-B broken copy:** boost bias at about 0.8 × the new floor (`--copy srknee`) at fs/125. It must REJECT, or report the measured knee if it passes.
6. Rerun op/AC 9 PVT and tb9 (4 corners + mut). Gate B: run only srknee, plus a nominal fs/125 if the TG clamp changed the netlist. Use 5 parallel single-thread jobs and `combine()`.

## Git
Explicit-path commits only, no trailers, no push. If signing fails, list the paths.

## Budget
At most 55 tool calls. Report in ≤ 60 lines. Stop on a failed exit and report.
