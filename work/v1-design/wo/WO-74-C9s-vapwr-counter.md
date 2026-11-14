# WO-74 (C9s): D85 VAPWR-good counter in the C9 RTL, plus SPEC entries for D82, D83, D85

Coordinator-written, 2026-11-14. **Tier: code (Sonnet).** Fresh agent.

## Items
1. **RTL** (`design/c9_digital/rtl/`).
   - Hold `rst_analog` (rstb) asserted until both conditions hold:
     - (a) 2^16 fs cycles have elapsed since the synchronised rst_n release;
     - (b) the `bias_ok` input from C6 has been high for 256 fs cycles (64 µs at 4 MHz).
   - `bias_ok` is a new top-level input (analog → digital, active high). Synchronise it with 2 FF.
   - Keep the D70 reset-release latency behaviour for the sequencer.
     - The first slot must not start until rstb releases.
     - State exactly how the first-slot timing changes, because D70 / CL-19 / CL-27 need an update.
   - Mark the first pair after the release invalid, as now.
   - Run lint and synth on the sandbox (IIC-OSIC-TOOLS). Report the FF and cell delta.
2. **SPEC change-log entries:**
   - D82: virtual-ground leakage derating. Add the 0.25 MHz N 1024 ≤ 100 °C rating and update the SPEC row 113 wording.
   - D83: sustained limit plus overshoot cap; clarifies D40/D80 and the row 99 wording.
   - D85: the VAPWR-good counter and the new `bias_ok` port in the §3.8a port contract. Update the rst_n paragraph, and state the board assumption that rst_n is asserted after VAPWR is up.
3. **Golden model.** If the reset/first-slot timing changes what golden v3.2 encodes (`hold_reset`, the sequences), say so. Do not edit golden; the verification agent will handle it.

Do not touch `tb/`.

## Rules
- Sandbox only.
- No local tool runs and no local python.
- Commit with explicit paths, no trailers, no push. If signing blocks, leave the changes and list the paths.

## Budget
At most 25 tool calls. Report in ≤ 20 lines.
