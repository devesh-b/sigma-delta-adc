# WO-84 (C3i): rev f residuals, check the supply basis, collect the WO-78/81 pools

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent.

## Inputs
- WO-81 README `results/wo81/README.md`; commits fe9e787, 600c547, 0bf4d4c.
- WO-78 README.
- Pools:
  - `/home/mempool/regr/tt/WO-78-1f18fa6`
  - `/home/mempool/regr/tt/WO-81-fe9e787`: one, mc and cyc rows valid; st rows invalid (aborted)
  - `/home/mempool/regr/tt/WO-81-600c547`: st rows

  Pickup commands are in the WO-81 README.
- D80, D83, D87.

## Where WO-81 left it
Rev f adds an op/on keeper, pfet 0.42/0.15, gate ob1/nb1. The st_tt27_a row still REJECTs:
- S = 1.980284 V on op (M4 gb), 0.28 mV over the limit;
- Sb3 gb is above 1.98 V for 143.8 ns, not diagnosed;
- P = 2.2206 V at the precharge edge on the real phiC edge, against the 2.2 V cap.

The supply basis used is |V| − max(0, vdd(t) − 1.98). The vdd node sits at 1.98194 V, **above** its source, which means reverse current flows into the supply. Removing the 10 Ω made the decks abort.

## Coordinator reading of D87(a)
The intent is a **stiff 1.98 V supply pin**. The drop subtraction is only acceptable if it is shown equivalent to that. Sub-mV results on a subtracted basis are not trusted until it is.

## Items
1. **Collect** the WO-78 and WO-81 pools. Write `results/wo78/summary.txt` and the WO-81 tables, including offset, kick, CM kick and decision time against rev e. Check each data file is non-empty.
2. **Supply basis.**
   - Find what drives vdd above its source: which device or path carries the reverse current, and whether it is physical (e.g. the HV x2 side through a clamp or the input pair).
   - Then make the supply stiff without the abort. Options include a small R (e.g. 0.1 Ω) plus on-die decap with a PWL ramp, or method=gear as in WO-79.
   - Show that the result does not move under a tighter setting.
   - Re-judge st_tt27_a without the subtraction. If the stiff-supply result and the subtraction disagree, the stiff supply wins.
   - If reverse current into VDPWR is physical, report it as a finding: on the real chip, VDPWR is shared.
3. **Sb3 143.8 ns:** say whether it is the same residual or a real sustained excess, and name the node and its cause.
4. **The 2.2206 V precharge-edge peak:** one change only, either a slower precharge edge or a slightly stronger keeper. Show its effect on decision time, kick and CM kick.
5. **Checker copies:** sus195, cap20 and dur01 must be shown live against a base row that passes. Also run st_brk_noclamp and st_brk_vdd200.
6. End with a "ready for review" list.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-84-<sha>`.
- Use lpool. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers.
- Do not change limits. Make design changes one at a time.
- Write only `design/c3_comp/`, `results/wo78/`, `results/wo81/` and `results/wo84/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
