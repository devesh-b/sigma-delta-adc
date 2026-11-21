# WO-98 (C2): OTA2 as the 9/16-scaled OTA1 cell (D91), generator and C2 bench

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. Plan: `TAPEOUT_10D.md`. Inputs: `results/wo93/README.md` (option B), D91, SPEC C2 rows, DESIGN_BOOK III.1 and III.2.

## Items
1. **Generator.** Add an OTA2 variant to `design/c1_ota1/netlist.py` + `sizes_draft.py` (or `design/c2_ota2/`, importing C1). Use 9/16 scaling per D91. Bias is shared with OTA1's nets; the CMFB is its own. Emit a standalone SPICE subckt `ota2`, and tell WO-94/WO-95 the file path.
2. **C2 bench at all 9 PVT corners** (base and boost), with every gate printing ACCEPT/REJECT, plus broken copies:
   - op/AC: A0, GBW, PM with the real Cint2/comparator load;
   - step settling and SR at 2 MHz and 4 MHz;
   - output swing against x2 1.41 V, the boost span, and A(v)min at hot boost;
   - CMFB under the 39–47 mV comparator kick;
   - offset Monte Carlo;
   - the boost-toggle settling of the shared bias (≤ 4 µs);
   - the OTA1↔OTA2 coupling through the shared bias.
3. **Totals:** precision and fast current against the 200 µA budget.
4. **In-loop spot check:** one gate B run with transistor OTA1 + OTA2 at tt/27 precision, O2, a few parts.
5. Write `results/wo98/README.md` and a "ready for review" list.

## Rules
- Sandbox only. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-98-<sha>`. Use the repo lpool v3 with `PRIO=high`. Source the venv and nix PATH. Use absolute paths. Wait on markers only.
- No local python. Do not change OTA1 sizes.
- Write only the OTA2 generator files, the C2 bench and `results/wo98/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 20 lines. Time-critical: target D2–D3.
