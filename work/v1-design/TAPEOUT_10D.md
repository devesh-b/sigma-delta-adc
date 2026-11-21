# 10-day tape-out plan (start 2026-11-21, submit by 2026-12-01)

User decisions, 2026-11-21:
- **Schematics first:** xschem schematics and full-chip schematic verification come first. Small tasks run in the background.
- **OTA2:** analyse reusing the OTA1 cell as OTA2. Report the extra area and current against the spec, and by how much they overshoot.
- **Modes:** verify one at a time, precision first.
- **Layout:** agents attempt all of it.
- **Top verification:** analog top plus ideal digital first; mixed-signal co-simulation if time permits.

## Tracks (parallel)

| Track | WO | What | Day target |
|---|---|---|---|
| A | WO-93 | OTA2 = OTA1-cell reuse: area/current overshoot vs spec, in-loop fit (x2 swing, β2, CM kick) | D1 |
| B | WO-94 | xschem schematics and symbols for C1, C3, C4, C6 (+ OTA2), plus the top-level modulator schematic. xschem-netlist vs Python-netlist equivalence check | D1–D3 |
| C | WO-95 | Full-chip transistor-level top bench (ideal digital loop logic, golden/Ref A decimation), precision mode first: function, start-up, INL spot points, key corners | D2–D5 |
| D | WO-96 | Layout: TT 2×2 analog tile floorplan (pins, power, C9 macro, MIM arrays, block slots), then cells by script (switches, caps, bias, comparator, OTAs), DRC/LVS per cell | D1–D8 |
| E | WO-97 | C9 final PnR (D85/D88 RTL, `bias_ok` pin, LVS, floating nets), GL/SDF sim | D1–D3 |
| bg | — | C6 copy fixes, C4 triage, C1 remaining parts, C3 rev g set | background |
| V | later | Tile DRC/LVS, PEX spot re-sim, TT precheck, submission repo (no Claude traces, user pushes) | D8–D10 |

## Rules
- Sandbox reached by WAN: `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox` (host key verified equal to mempool.lan 2026-11-21).
- lpool v3: fast work runs at `PRIO=high`, sweeps at `PRIO=low`.
- Heavy formal runs alone with `ulimit -v`.
- All other standing rules apply (STATE-2026-11-14 §1).

## Risks
- Agent-generated precision analog layout may not reach DRC/LVS-clean in time. The fallback is decided at D4–D5 from layout progress.
- The tile area is about 62 % committed before analog layout. OTA2 reuse adds area (WO-93 quantifies it).
