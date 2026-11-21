# WO-93 (C2): OTA2 as an OTA1-cell reuse, analysis of the area and current overshoot

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. The 10-day tape-out plan is in `work/v1-design/TAPEOUT_10D.md`.

## Ask (user)
"Do an analysis of the extra area and current and see if it can meet our required spec, and by how much it overshoots."

## Items
1. **OTA2 requirements.** Take them from SPEC (C2 rows, II.2, D46 current budget) and DESIGN_BOOK III.2:
   - x2 peak 1.41 V differential;
   - β2 0.497;
   - Cint2 and load;
   - settling or SR at 2 MHz precision and at 4 MHz boost;
   - A0 ≥ 75 dB;
   - CM kick 39–47 mV from the C3 rev f/g comparator;
   - noise share, which is small after integrator 1 gain.
2. **OTA1 cell as-is** (WO-52 netlist, sink L 8). Is it valid as OTA2? Use hand analysis and existing data (results/wo52, wo63, wo91), plus at most a few spot sims through lpool `PRIO=high`.
   - Check the output swing against 1.41 V, using the boost span (1.43 V).
   - Check A0, PM with the OTA2 load, SR, and CMFB with the comparator kick.
3. **A scaled variant**, for example lower current for precision mode with boost for fast mode. Give its numbers.
4. **Totals vs budget.**
   - **Current:** precision and fast-mode totals (OTA1 + OTA2 + C6 + switches/LS; the comparator is on VDPWR) against the 200 µA analog budget. State the overshoot in µA and %, and the margin.
   - **Area:** OTA1 cell area estimate, with the source or a device-area sum ×(2–3) routing factor. Report the tile area totals against 72,071 µm², with C9 28,500, MIM ≈ 9,000 and C6 ≤ 7,000.
5. **Verdict and options.**
   - Does reuse meet the spec? By how much does it miss each row?
   - Give 2–3 options with cost: reuse as-is / scaled reuse / new design. Recommend one.
   - Do not change any SPEC row.
6. Write `results/wo93/README.md`. Commit with explicit paths.

## Rules
- Sandbox only, for any sim. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- No local python.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 30 tool calls. Report in ≤ 20 lines. **Fast:** target within hours.
