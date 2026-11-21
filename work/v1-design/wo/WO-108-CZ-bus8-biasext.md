# WO-108: Chipalooza variant, byte-select bus (cz_bus8) and BIAS_EXT (D99)

Tier: Sonnet codes. sd-adc-design-reviewer reviews the BIAS_EXT design before sim and after results. rtl-verification-engineer writes the cz_bus8 bench independently of the author.
Budget: about 4 h agent time. Stop rule: hand off when one sim pool is running or on any blocker. No open-ended digs.

## Scope (CZ variant only; TT design unchanged)
1. **cz_bus8** (`design/cz/rtl/cz_bus8.v`):
   - Inputs: bus[15:0] (the registered C9 read bus), bsel.
   - Output: data[7:0] = bsel ? bus[15:8] : bus[7:0].
   - Pure combinational; document that a valid byte appears one mux delay after a bsel change.
   - Debug mode passes through unchanged (bus carries the debug signals).
   - No change to `design/c9_digital/**`.
2. **cz_bus8 bench** (rtl-verification-engineer, from this spec only):
   - exhaustive or random checks with iverilog;
   - two mutants (swapped halves, stuck bsel) must REJECT.
3. **BIAS_EXT** (`design/cz/c6_cz.py`, wraps `c6_bias` from `design/c6_bias/c6_final.py`; do NOT edit c6_final.py, WO-104 owns it):
   - Ports: c6_bias ports + `bias_ext` (current in, harness bandgap-referenced source, range TBD: design for 1–20 µA nominal 5 µA, scaled to the C6 master unit by a selectable or fixed mirror ratio, state the assumption) + `bias_sel` (3.3 V domain after a level shifter; static).
   - bias_sel = 0: C6 behaviour must equal c6_final (port currents within 0.1 %; prove with a diff run).
   - bias_sel = 1: port currents track bias_ext ratiometrically. The C6 core is off or isolated and must not fight. bias_ok must be defined (ext-current-present detect or forced high, state it).
   - Stress: SPEC device-stress rules (D80/D83/D90).
   - Gates at tt/27 plus ss/−40 and ff/125, VAPWR 3.0/3.6:
     - G1: sel 0 equals the baseline;
     - G2: sel 1 port-current ratio error ≤ 2 % over the 1–20 µA range;
     - G3: bias_ext open with sel 1 → bias_ok low or a stated safe state;
     - G4: switch leakage effect on sel 0 ≤ 0.1 %.
   - Each gate has a broken copy that must REJECT (for example, a missing isolation switch, or a wrong mirror ratio).
   - Runs use lpool with PRIO=high on the sandbox only.
4. Update `PROPOSAL_CHIPALOOZA4.md` I/O only if port names change.

## Rules
- Sandbox only; no local python.
- Atomic explicit-path commits, no attribution trailers, no push.
- Never write in /home/mempool/tt.
- No pkill -f.

Commits: `WO-108: ...`.
