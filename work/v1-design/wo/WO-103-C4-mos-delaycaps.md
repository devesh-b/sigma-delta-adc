# WO-103 (C4): delay caps MIM→MOS (D93), dead-time check at corners

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. Inputs: D93; `design/c4_sw/` (rev b, 14 delay caps, 0.92 pF); `results/wo79/`, `wo85/` (tim bench, `soften`/`drv`, supplies ideal in tim).

## Items
1. Replace the 14 phase-generator delay caps with MOS caps (sky130 nfet/pfet as caps, or varactor-free MOS) sized to give the same delays at tt. Justify the bias region: each must stay in inversion over the swing, or the non-linearity must be accounted for.
2. **Dead-time / non-overlap table** at 9 PVT corners: all phases, MOS caps against the old MIM caps. Every gate row is against the C4 non-overlap rows. Broken copy: one cap removed, which must REJECT.
3. Write `results/wo103/README.md`. Give the area saving and a "ready for review" list.

## Rules
- Sandbox only. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-103-<sha>`. Use lpool v3 with `PRIO=high`. Wait on markers only.
- No local python.
- Write only `design/c4_sw/` (delay caps only) and `results/wo103/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 30 tool calls. Report in ≤ 15 lines.
