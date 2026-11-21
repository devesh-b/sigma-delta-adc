# WO-102: xschem top update from the WO-99 review, then re-run the equivalence check

Coordinator-written, 2026-11-21. **Tier: code (Sonnet).** Fresh agent. Inputs: `results/wo94/README.md`, `results/wo99/README.md` item 5, commits a9a416f and 69c59b9.

## Items
1. **Update `design/xschem/gen/refnets.py` and `sch_gen.py`:**
   - (a) the internal-short node → `vscm`;
   - (b) **swap the Ck2 khi/klo**, because Cint is crossed in the top;
   - (c) add `SW['sr2']` and connect OTA2 `isl` to `r2_t`;
   - (d) the C6 final instance from `design/c6_bias/c6_final.py` and the reference instance from `design/c5c7_ref/c5c7_ref.py`;
   - (e) top ports `boost`, `trim0..2`;
   - (f) OTA2 from `design/c2_ota2/ota2.spice`, D91 sizes; remove the "PENDING D91" flag.
2. **Regenerate and re-run the netgen equivalence** for every cell plus the top. Add **one wiring broken copy per cell** (one net swapped), alongside the existing size copies; each must fail.
3. Export `design/xschem/sd_mod_top.spice`. Write `results/wo102/README.md` with the match table and the port list.

## Rules
- Sandbox only, via `scripts/iic`. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-102-<sha>`.
- No local python, not even an empty `python3 -`. Check every command before running it.
- Write only `design/xschem/` and `results/wo102/`. No size changes.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 30 tool calls. Report in ≤ 15 lines.
