# WO-94: xschem schematics and symbols for all analog blocks plus the top-level modulator

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. Plan: `work/v1-design/TAPEOUT_10D.md`, track B.

## Inputs
The Python netlist generators are the source of truth today:
- `design/c1_ota1/netlist.py` + `sizes_draft.py` (WO-52 netlist, sink L 8);
- `design/c3_comp/netlist.py` + `sizes_draft.py` (rev g: keeper 0.84/0.15, precharge R0/R1 1.0/0.3);
- `design/c4_sw/` (rev b: switches, phase generator, level shifters, Sg);
- `design/c6_bias/` (option (c), R1 144.8 µm);
- the system architecture in SPEC §3 and DESIGN_BOOK II.2 / III.0 (block map, ports, Cs 0.5 pF, Cint1 4 pF, c1/c2/k, chop and CM switching).

## Items
1. Create `design/xschem/` with an `xschemrc` that uses the sky130A PDK symbols from IIC-OSIC-TOOLS (`/foss/pdks`).
2. **One schematic and one symbol per block:** `ota1`, `ota2` (an OTA1 instance for now; WO-93 decides), `comp`, `sw_*` / `phasegen` / `ls`, `bias`, and the MIM cap arrays. Device sizes must come **exactly** from the generator outputs. Prefer a script that emits `.sch` from the same size tables, over hand-drawing.
3. **Top schematic `sd_mod_top.sch`:** the full fully-differential modulator. Integrators 1 and 2 with caps, input/DAC/chop switching, comparator, phase generator, bias, and the `bias_ok` output. Use the TT analog port names: ua[…] for inputs and the reference, VAPWR, VDPWR, VGND. The C9 interface pins are comp_out, phase/control inputs, rst_analog and bias_ok.
4. **Equivalence check:** netlist each block from xschem (batch, on the sandbox, IIC-OSIC-TOOLS) and compare it with the Python netlist using netgen LVS. Each block must match, and a broken copy (one size changed) must mismatch.
5. Export the top-level netlist as `design/xschem/sd_mod_top.spice` for WO-95 and the layout LVS (WO-96).
6. Write `results/wo94/README.md`: blocks, the match table, the broken copies, and the port list.

## Rules
- Run xschem and netgen on the sandbox via `scripts/iic`. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`; the container sees `/home/mempool/regr/tt` as `/foss/designs/regr`. Frozen copy `/home/mempool/regr/tt/WO-94-<sha>`.
- No local tool runs and no local python.
- Do not change device sizes. If a generator and the design book disagree, report it.
- Write only `design/xschem/` and `results/wo94/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 20 lines. Target D1–D3.
