# WO-41 (C1): OTA1 noise (tb7): thermal at the virtual ground, 1/f corner, chopper residue

Coordinator-written, 2026-11-12. **Tier: design (Opus).** Next C1 step per REVIEW-C1b-final (noise before MC, since it may resize the input pair). Sources:
- SPEC.md rows 92–93 and §2.2 (noise-gain note: white noise × ≈ 5.3, 1/f/offset × 1);
- D4, D45g (chop modes);
- `design/c1_ota1/*`, the WO-31/39 netlist;
- `model/` (tier-0 noise inputs).

## Items
1. **`c1b_tb7.py`:** `.noise` on the netlisted OTA1 in the integration-phase network, at 9 PVT × 2 modes.
   - Integration-phase network: Cs / Cint / Cp_vg / C_L per phase, CMFB included, chopper parked.
   - Report en(f) at the OTA input, the integrated sampled thermal noise at the virtual ground (rms diff, over the bandwidth the SC network actually sees), and the 1/f corner fc.
   - Gates (SPEC rows 92–93):
     - thermal ≤ 250 µV rms diff (expect about 75–110);
     - fc ≤ 631 kHz (info).
   - Report the dominant noise contributors per device: input pair, cascodes, loads, CMFB and integrator path.
2. **Chopper residue:**
   - the constant residue (≤ 1 mV) and the signal-dependent residue (≤ 1 µV over ±0.9 FS), from a transient with system chop;
   - or bound them by hand with evidence if a full transient is too costly. Say which.
3. **Tier-0 feed:** convert the results into the model's noise inputs (white, 1/f) and run the S-model noise at 15 SPS, nominal and worst corner. Report it against the 2.5 µV budget (the block share is 1.2 µV thermal + 1.0 µV 1/f).
4. **Broken copy:** input pair halved (W/2) ⇒ the thermal row must REJECT, or the noise share is exceeded (PLAN C1 broken copy).
5. **If a gate fails:** stop and report options, such as input pair area. Do not change sizes yourself.

## Rules
- Sandbox only.
- Frozen copy `regr/tt/WO-41-<sha>` with golden/.
- Use `scripts/lpool.sh` for the parallel runs (load-adaptive, single-thread).
- No local python. Explicit-path commits, no trailers, no push. Markers, no wait loops.

## Budget
At most 45 tool calls. Report in ≤ 40 lines.
