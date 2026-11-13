# WO-54 (C4b) results: netlist + gate testbench

Scripts: `design/c4_sw/netlist.py`, `design/c4_sw/c4_tb.py` (rows and broken copies in DESIGN.md §11).
Design note: `design/c4_sw/DESIGN.md` rev b.

## Status

- Netlist and testbench written and committed (abe620c and later). The full gate run is **not finished**:
  see "Pickup" below. No gate verdict yet beyond the smoke runs listed here.

## Smoke findings (sandbox, `/home/mempool/regr/tt/WO-54-smoke`, `WO-54-smoke2`, `WO-54-probe`)

1. **`lsbuflv2hv_clkiso_hlkg_3` does not work in the PDK spice** (probe deck, tt/27, VAPWR 3.3, VDPWR 1.8, A = 1.8 V
   pulse): X = 3.31 / 3.29 V with SLEEP_B = 0 (isolated high, as expected), but X stays at 3.30 V for both input
   levels with SLEEP_B = 3.3 V, and the transient is very slow. `lsbuflv2hv_1` in the same deck passes the pulse
   (3.30 V / 10 µV). With clkiso in the generator every tim job had no phase edges at all, and the inj / settle
   decks stopped on "timestep too small". `lsbuflv2hv_isosrchvaon_1` has no device on VPWR / VGND in the spice
   (virtual rails), so it cannot be simulated either.
   **Consequence (deviation from D76, needs a user decision):** the default netlist uses `lsbuflv2hv_1` and does
   the isolation in logic: pwrok gates fs / not fs into the generator NANDs and forces isl, so every switch phase is
   off while VDPWR is missing, whatever the LS outputs are. Token `isols` keeps the clkiso variant. Options:
   (a) keep the logic gating (simulable, proven by the ramp rows); (b) use the clkiso cell in layout and verify it
   with an extracted / corrected model; (c) both.
2. **Sg leakage share fails:** Sg NMOS 5/0.5 off, vg 1.2 V, tp 0.18–2.22 V, ff/125/3.6: |I| max 68 pA into the vg
   node, against the proposed 45 pA share (50 % of the 90 pA row). Alone it is inside the 90 pA row, but it leaves
   22 pA for the C1 island shunt and the input chopper. Options: W 4 (m3 lower bound), a T-switch (D76 fallback),
   or re-split the row with C1's measured share. Sign and Vin_cm dependence: in the full-run table.
3. Ron (tt/27): every switch inside its limit (sin 382 Ω, DAC 1.15 kΩ, VREF− NMOS 519 Ω, stp 3.45 kΩ, Sg 816 Ω).

## Pickup

See the report from the WO-54 agent for the exact pool command and directory.
