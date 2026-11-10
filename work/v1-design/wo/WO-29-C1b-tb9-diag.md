# WO-29 (C1b part 2e): tb9 switched-cap CM offset, cold-corner op, then gate B on the WO-28 netlist

Coordinator-written, 2026-11-10. **Tier: design (Opus).** Sources:
- D57–D62;
- `work/v1-design/results/wo28/README.md` (run 2);
- `design/c1_ota1/{netlist.py,c1b_opac.py,c1b_tb9.py,c1b_gateb.py}`;
- `work/v1-design/results/wo26/README.md` (gate B, combine() note).

**Sandbox:** same rules as WO-28.
- New frozen copy per commit you run; include `golden/`.
- At most 3 of your own processes. Absolute paths, markers, no pgrep/pkill, no wait loops, delete csv files.
- **Run no python locally, not even a text edit script; use the Edit tool.**

## Items
1. **D62:** make f_cm ≥ 9.4 and f_z ≤ f_cm/10 info rows. CM PM ≥ 45° and peaking ≤ 1 dB stay gates.
2. **tb9 SC CM offset diagnosis** (the main item). In the switched-cap transient the CM sits +129–167 mV (tt) / +34–42 mV (hot) above V_OCM, against +0.3–0.6 mV in the averaged op.
   - Run tt boost for 10–20 µs and log the CM and `bli` vs time, to tell an unconverged slow loop from a real offset.
   - If it is real, find the mechanism and fix it, citing the circuit evidence. Candidates:
     - Cr refresh/share phasing or polarity;
     - charge injection and clock feedthrough of the CMFB switches;
     - the averaged-model B-source not matching the SC network;
     - the start-up clamp release;
     - reset-phase island shunt interaction.
   - Exit: SC transient CM within 10 mV of the averaged op and of V_OCM at the end of each half-phase, at tt and the hot boost corners.
   - Make the tb9 event rows discriminate: the Cc ÷ 4 copy must fail a row that nominal passes.
   - Fix the sulo start-up (14–34 mV) within the CL-7 4 µs.
3. **Cold-corner op convergence:**
   - Make ff/−40 and sf/−40 converge without transient op, using one closed copy plus its open twin per deck, or a DC-exact loop break.
   - Do not break the tt mutant deck.
   - The transient-op lint stays.
4. **combine() broken-copy rule:** for a broken copy, all parts healthy and > gate ⇒ REJECTED, even if the endpoints disagree. Report the endpoint disagreement as info. A nominal run still needs endpoint agreement.
   - Test it on WO-26's c3_sr95 parts: read `/home/mempool/regr/tt/WO-26-b177d23/out/gb/c3_sr95/*.json`, read-only.
5. If items 2–3 pass: rerun op/AC at 9 PVT and tb9. Then **launch gate B** (`results/wo28/gb.sh`, adapted) with fs/125, ss/−40, ss/125, tt/27 + sr95 at fs/125 and sf/−40, detached with markers. Do not wait for it.

## Git
Explicit-path commits only, no trailers, no stash, no push. If signing fails, list the paths and do not bypass.

## Budget
At most 55 tool calls. Report in ≤ 60 lines. If an exit cannot be met without adding current or changing a D61/D62 decision, stop and report options.
