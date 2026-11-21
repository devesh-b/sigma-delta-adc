# WO-95: full-chip transistor-level top bench (precision mode first)

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. Plan: `work/v1-design/TAPEOUT_10D.md`, track C.

## Approach (user)
Run the analog top at transistor level with **ideal digital**: the loop logic (comparator capture into the DAC flop on fs_tick, phases, chop sequence, reset) is behavioural in the deck. The bitstream is decimated offline by the existing golden model / Ref A (`model/`, `design/c9_digital/tb/ref_a.py`). Mixed-signal co-simulation with the real C9 netlist (XSPICE/d_cosim) is a later stretch item.

## Inputs
- The block netlists from the Python generators now (C1 WO-52; C3 rev g; C4 rev b; C6 option (c)). Switch to `design/xschem/sd_mod_top.spice` once WO-94 delivers it; the netlist-equivalence check makes the two equal.
- OTA2: the OTA1 cell for now (WO-93 decides).
- The existing tier-1 deck and gate B machinery (`design/tier1/`, `design/c1_ota1/c1b_gateb.py`) for the loop and INL extraction.

## Items
1. **Build the top deck** with every analog block at transistor level: OTA1, OTA2, comparator, switches/phase generator/level shifters, and C6 bias, with the real `bias_ok` driving an ideal reset hold. Use the D85/D88 behaviour, but with a shortened hold for simulation; state the scaling.
2. **Gates, precision mode first** (fs 2 MHz, boost 0, N 1024 unless stated). Modes are verified one at a time.
   - (a) start-up from VAPWR ramp to the first valid conversion: bias_ok, CMFB settle, no stuck state;
   - (b) DC function: code against Vin at ~5 points from −FS to +FS, with the output against the golden model within the SPEC tolerance;
   - (c) INL spot points (m 5–7, N 1024) at tt/27 and ss/−40;
   - (d) chop pair offset cancellation;
   - (e) overload / recovery.

   Each gate needs a broken copy that REJECTs, for example a swapped DAC polarity or a dead OTA2 bias.
3. **Runtime:** measure it per conversion, and plan the corner set to fit about 3 days on a 5-slot box. Use lpool v3 with `PRIO=high` for the gates and `PRIO=low` for sweeps.
4. **Then the next mode** (boost / 4 MHz, N 64/256), as time allows. Report each mode separately.
5. Write `results/wo95/README.md`: deck description, gate table, runtimes, and the next-mode plan.

## Rules
- Sandbox only. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-95-<sha>`.
- Use the repo `scripts/lpool.sh` (v3: PRIO, SKIPDONE). Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- No local python. No device-size changes.
- Write only `design/top/` and `results/wo95/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 25 lines. Write the pickup commands into the README.
