# WO-65 (C3e): close the comparator on rev d

Coordinator-written, 2026-11-13. **Tier: design (Opus).** Fresh agent.

## Sources
- `work/v1-design/results/wo56/{README.md,summary.txt}`
- WO-56 run `/home/mempool/regr/tt/WO-56-2e55372` (read only)
- `design/c3_comp/*`
- D40, D74, D75, D80
- SPEC rows 99, 105–108

## Items
1. **D80: rewrite the T8 stress row.**
   - Oxide pairs (Vgs, Vgd, Vgb) and Vds stay ≤ 1.98 V.
   - Junction reverse bias (Vsb, Vdb) is judged against the PDK 1.8 V device junction rating. Find that rating in the PDK docs or models inside the IIC container, state the source, and apply a margin.
   - Add a SPEC change-log entry clarifying D40 (cite D80) and update row 99's wording.
   - Re-judge the WO-56 T8 data against the new row: Vsb is 2.37–2.39 V on the latch NMOS.
   - Keep the in18 broken copy. It must still REJECT because of oxide stress on the 1.8 V input.
2. **The T5 kickback broken copy is blind.** one_brk_cl10 now ACCEPTs at kick 2.2 mV.
   - Design a broken copy that matters for rev d, for example the precharge removed, or the HV cascode removed so dp/dn couple straight to x2.
   - It must REJECT on T5.
3. **T5 asymmetric copy (info).** The ±10 % kick is 7.5 mV. Report it. If the realistic ±5 %/±1 % gate passes, leave it there.
4. **Rerun the affected decks.** The st decks are judged in collect, so only re-collect is needed if the data suffices. Also run the new T5 broken copy and anything the row change needs, through lpool. Do not export OMP_NUM_THREADS.
5. **Exit:** every nominal row ACCEPTs and every broken copy REJECTs. Then the sd-adc-design-reviewer pass on rev d. You may request it in your report rather than running it.

## Rules
- Sandbox only.
- No local python.
- Write only under `design/c3_comp/`, `results/wo65/` and SPEC.md (one CL entry plus the row 99 text).
- Commit by explicit path, no trailers, no push. If signing blocks, leave the changes and list the paths.

## Budget
At most 35 tool calls. Report in ≤ 25 lines.
