# WO-25 (C1b part 2a): D58 reference fix, D55 revert, close out gate B

Coordinator-written, 2026-11-10. **Tier: design (Opus).** Sources:
- D58, D57, D55;
- `work/v1-design/results/wo24/README.md` (diagnosis + confirmation run `ref1_diag.log`);
- `work/v1-design/REVIEW-C1b-code-2026-11-10.md` (items 11–15 still open);
- `design/c1_ota1/{netlist.py,sizes_draft.py,c1b_opac.py,c1b_gateb.py,revc_check.py}`.

**Sandbox:**
- Run from a frozen copy `regr/tt/WO-25-<sha>`.
- At most 3 processes, nice, timeout ≤ 600 s for spot runs and ≤ 11000 s per gate B part.
- Delete raw csv files.
- Launch long runs with `setsid nohup` and `EXIT=`/`DONE` markers. No pgrep wait loops.
- **Use absolute output paths** (ngspice runs from another cwd).

## Items
0. **Close out WO-24 gate B** (WO-24-8ef9a7e, composite-ref netlist):
   - Check endpoint agreement across the 6 parts: identical endpoint codes/residues in every part json. Then combine = max INL. Implement `combine()` with that assert (REVIEW-C1b m6).
   - Run `--copy sr95` in 6 parts. Exit: healthy and INL > 5 ppm ⇒ REJECTED. Blind or invalid ⇒ stop and report.
1. **D58 reference fix** (`sizes_draft.py`, `netlist.py`):
   - (a) Measure the composite-to-mirror ratio for all four 1:32 mirrors (m_tr, m_nr, m_plr, and the V_BL0 replica stack) at 9 PVT × 2 modes on the netlisted OTA. This is tb8b's ratio row (RC-M2 verification).
   - (b) Scale the I_REF ports by the inverse of the tt ratio, so tail and fold currents sit on the design values at tt.
   - (c) Feed the vbpc and vbnc diodes (m_bpc, m_bnc) from a replica of the real folded branch: a composite reference identical to the mirror reference, scaled down. K_P and K_N then track the actual I_NC over PVT. Keep the CL-8 boost increment (base K_P 10 / boost K 7).
   - (d) Fix the V_BL0 replica the same way if (a) shows it off (V_OCM error was −31 to +23 mV).
   - Exit: I_tail within ±3 % of 18.5 µA (×2 boost) at all 9 PVT; effective K_P within ±10 % of target at all 9 PVT; I_vdd base ≈ 50 µA.
   - Broken copy: the replica fed from fixed I_REF (the old wiring) ⇒ effective K_P at ff/−40 drops below 9 ⇒ REJECT on the K_P row.
2. **D55 revert:** m_plc 30/4 → 15/2, Cc 0.1 pF, Cr scaled back. Keep the f_cm hand row; f_cm gets its own lever in tb9 (next WO).
3. **op/AC rerun** (`c1b_opac.py`), 9 PVT × 2 modes × 3 C_L.
   - Exit: precision A0 ≥ 80.3 dB at all 9; I_fold/I_tail ≥ 1.2; margins ≥ 50 mV (boost m_plc included); hand A0 within ±1 dB; β1 ≥ 0.83.
   - Report boost fp2/GBW at the integrate load and the PM, per corner.
   - Wire the `ref_single` mutant into a testbench (reviewer note: it exists in `netlist.py` but nothing uses it).
4. **Gate B rerun on the D58 netlist:** fs/125 boost N 1024 m 21 O1 in 6 parts, plus sr95. Then ss/−40 boost (worst PM, fp2/GBW 1.08 on the old netlist), same gate. Run O2 on any point whose O1 result is ≥ gate/2.
   - If gate B fails, stop and report. Do not add current (D54 needs the user).

## Commits (explicit paths, no attribution trailer, no push)
1. `design: C1b gate B combine() with endpoint check + sr95 result`
2. `design: C1 D58 reference scale + replica cascode bias, D55 revert`
3. `design: C1b op/AC + gate B rerun on the D58 netlist`

## Budget
At most 50 tool calls. Report:
- the four mirror ratios over PVT;
- I_tail, K_P, K_N and A0 per corner;
- I_vdd;
- the gate B results (fs/125 and ss/−40) and the sr95 copy;
- risks.

Then: sd-adc-design-reviewer pass on the diff and the results.
