# WO-30 (C1b part 2f): tb9 rows on the D63 basis, open tb9 items, then gate B

Coordinator-written, 2026-11-11. **Tier: design (Opus).** Sources:
- D57–D63;
- `work/v1-design/results/wo29/README.md` (fixed-bench tb9 table; op/AC 9 PVT ACCEPT);
- `design/c1_ota1/{c1b_tb9.py,netlist.py,c1b_gateb.py}`;
- `/home/mempool/regr/tt/WO-29-9e14bed/gb.sh` (ready).

**Sandbox:** same rules as WO-29.
- New frozen copy per commit run, with golden/.
- At most 3 of your own processes. Absolute paths, markers, no pgrep/pkill, no wait loops, delete csv files.
- **No local python at all.**

## Items
1. **D63 tb9 rows:**
   - Judge each CM event (reset release, CM step, reset assert, reset release 2) at the sampling instant, i.e. the end of the half-phase where the integrator charge is taken, with the limit ≤ 10 mV. Keep the 22.5 ns value as info.
   - Add a CM-to-DM leakage row: differential output error caused by the CM event at the sampling instant, against an LSB-scale bound you derive from the S-model (state the derivation; for example ≤ 0.1 × the per-sample INL budget).
   - Redefine the diff-step row to measure settling after slewing ends, or use the real worst per-cycle step from the tier-1 waveforms. State which, and why.
   - The Cc ÷ 4 copy must still fail a row the nominal passes; if it no longer does, add a row that discriminates (for example the CM-to-DM row).
2. **Diagnose and fix (or bound, with evidence) the open tb9 items, without adding current or changing D61–D63:**
   - reset-assert error of 25 mV at the hot corners (ss/125, fs/125);
   - sulo start-up 14–34 mV, not within 10 mV at 4 µs (CL-7);
   - end-ph1 ripple of about 12 mV.
   If an item needs a design change beyond the caps, stop and report options.
3. **Gate B on this netlist,** once items 1–2 pass. Launch detached:
   - fs/125, ss/−40, ss/125, tt/27, plus sr95 at fs/125 and sf/−40;
   - N 1024, m 21, O1, 6 parts each, combine() with the broken-copy rule;
   - waves of 3, with markers.
   Report the paths. Do not wait.

## Git
Explicit-path commits only, no trailers, no stash, no push. If signing fails, list the paths and do not bypass.

## Budget
At most 55 tool calls. Report in ≤ 60 lines.
