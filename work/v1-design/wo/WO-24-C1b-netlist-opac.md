# WO-24 (C1b part 1): sync, precision sweep, netlist generator, op/AC at 9 PVT × 2, first gate B point

Coordinator-written, 2026-11-10. **Tier: design (Opus).** Sources:
- `work/v1-design/REVIEW-C1a-revC-2026-11-10.md` (RC-M1, RC-M2, RC-M3, RC-m1 to RC-m7, Q4, and the WO-24 order steps 0–3 and 6-first);
- D54, D55, D56;
- SPEC change log CL-1b/1c/1d, CL-3, CL-4, CL-7, CL-8;
- `design/c1_ota1/*`;
- `design/tier1/gen_tier1.py` and `tier1_tb.py` for gate B;
- `work/v1-design/results/c1_macro_scans.md`.

**Sandbox:**
- Run from a frozen copy `regr/tt/WO-24-<sha>`.
- At most 2 processes, nice, timeout ≤ 600 s for spot runs and ≤ 7200 s for the gate B deck.
- Keep small json and **delete raw csv** files.
- Launch long runs with `setsid nohup` and a `DONE`/`EXIT=` marker. Do not use pgrep wait loops; if a job is still running when you check, report and stop.

## Items
0. **Single source of truth.**
   - Sync `DESIGN.md` to rev C (RC-m6: header, §1.1, §1.2, §2.9, §3, §5, the Rev C table, docstrings).
   - Fix the `revc_inl.py` info tagging (RC-m5): a nominal run must exit 0, and a real REJECT must still exit nonzero.
1. **Precision A0 sweep (RC-M1).**
   - Sweep K_P base ∈ {8, 9, 10, 11} × m_plc ∈ {15/2, 30/4 with Cc 0.2 pF and Cr scaled} on the spot deck, at 9 PVT in base mode.
   - Read A0, m_pl and m_pc margins, base span, and f_cm (hand or AC of the CM loop).
   - Pick the cheapest point with A0 ≥ 80.3 dB at all 9 PVT and base span ≥ 1.6 V. Boost stays at K 7.
   - **Report whether K_P 10 alone reaches it without D55's Cc 0.2 pF.** That is a user option; do not drop D55 yourself.
2. **Netlist generator** (`design/c1_ota1/netlist.py`, reading `sizes_draft.py`):
   - ad/as/pd/ps on every device;
   - **composite 1:32 references** (RC-M2): series-parallel unit fingers, for example 4 × 4, with the same finger W/L as the mirror;
   - fold chopper `nfet_01v8` 4/0.15;
   - 3.3 V input chopper and island switches (CL-5);
   - **real SC CMFB** (Cc, Cr, phases);
   - level-shifted clock ports;
   - the vbpc per-mode increment (CL-8).

   Exit: lint clean, tt op converges, every device margin ≥ 50 mV, and the m_nc-short broken copy REJECTs. Add a unit test that checks the device count and composite-reference structure, and that FAILs on a single-finger reference.
3. **tb1/tb2 op and AC on the netlisted OTA,** 9 PVT × 2 modes.
   - CMFB as a DC equivalent (Cr → R = 1/(f·Cr)). Say how the C_L in the tier-1 macro is defined (review Q1).
   - Exit:
     - precision A0 ≥ 80.3 dB;
     - hand A0 within ±1 dB of AC;
     - GBW and absolute fp2 reported at **both** the 1.4 pF lump and the real per-phase loads (0.78 / 0.90 pF);
     - β1 recomputed with the real gate routing estimate (CL-4).
4. **First gate B point (review Q4).** Run the tier-1 deck with the transistor OTA1 (OTA2 behavioural) at **fs/125 boost**, N 1024, 4 MHz, with **C_FOLD_EXTRA = 0**, at O1, and O2 if O1 is within 2× of the gate.
   - Gate: ≤ 5 ppm at 4 MHz boost (and report it against 3.33).
   - Broken copy: tail current set for 9.5 V/µs ⇒ REJECT.
   - If gate B fails, stop and report. Do not add current (D54 needs the user).

## Commits (explicit paths, no attribution trailer, no push)
1. `design: C1 DESIGN sync to rev C + revc_inl info tagging`
2. `design: C1 precision A0 sweep`
3. `design: C1 netlist generator (composite refs, real SC CMFB, junction caps) + test`
4. `design: C1b op/AC 9 PVT x 2 + first gate B point`

## Budget
At most 50 tool calls. Report:
- the chosen K_P and m_plc, and whether K_P 10 alone suffices;
- per-corner A0, GBW and fp2 at both load definitions;
- β1;
- the gate B result and its broken copy;
- current;
- risks.
