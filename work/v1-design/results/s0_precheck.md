# S0 part C: TT analog template through TT precheck

Date 2026-11-07. Driver: `scripts/s0_precheck.sh {ok|met5|all}` (sandbox only).

## Sources (cloned fresh under `/home/mempool/regr/tt/WO-01/tt/`, never `/home/mempool/tt`)
- Template: https://github.com/TinyTapeout/ttsky-analog-template.git @ `301590bc02ffeabc2bb176489de9db0818a4b958` (workflows use tt-gds-action `ttsky26d`)
- Tools: https://github.com/TinyTapeout/tt-support-tools.git @ `9d13ff3e3e6202090740110438c6a10c1d62ca0f` (main; no `ttsky26d` tag exists in the clone, so "matching ref" = main at clone time)
- Precheck run with nix magic 8.3.693 and klayout python module 0.30.x in a venv (TT pins magic 8.3.568 / klayout 0.30.4 in `precheck/tool-versions.json`; versions differ, noted), PDK = TT-pinned open_pdks d56f8a8e.

## Dummy project
2x2 analog tile, `uses_vapwr: true` (the template's name for the 3v3 option; `uses_3v3` is the legacy alias), `analog_pins: 3` (ua0 VIN+, ua1 VIN-, ua2 VREF), DEF `tt_analog_2x2_3v3.def`. Magic builds it from the DEF: met4 power stripes VDPWR/VGND/VAPWR (2 um wide) and one met4 stub on each of ua0..ua2. Verilog ties uo_out, uio_out, uio_oe to 0. No met5.
**Deviation from WO:** no poly resistor to VGND; the structure is met4 stubs only (the pin check needs only metal on the pin). Not a loss for the S0 purpose; the resistor can be added when real structures exist.

## Results (logs: `/home/mempool/regr/tt/WO-01/tt/proj_{ok,met5}/precheck.log`, `results.md`)
| Variant | Result |
|---|---|
| ok (dummy) | PASS, all 15 checks green, rc=0 |
| met5 (one met5 rectangle added) | FAIL: `KLayout Checks: Forbidden layer met5.drawing found`; every other check still green, rc=1 |

`scripts/s0_precheck.sh all` prints `ACCEPT` only if ok passes AND the met5 copy fails with the "Forbidden layer" message (a failure for another reason does not count).

## What TT precheck does (sky130A, analog)
Magic DRC, KLayout FEOL/BEOL/offgrid DRC, pin-label/drawing overlap, zero-area, top-cell name + forbidden layers (met5) + prBoundary, pin check against the DEF, boundary check, power-pin presence (VGND, VDPWR, VAPWR iff `uses_vapwr`), valid-layer list, cell-name characters, urpm/nwell spacing, analog pin connected-iff-declared, Yosys syntax check of the Verilog.

## What it does NOT check (become V8 items)
- Antenna: the antenna check in precheck runs only for gf180mcuD, not sky130A.
- LVS (layout vs schematic) and any netlist equivalence; the Verilog is only syntax-checked.
- Parasitic extraction, pad-path R/C (<500 ohm, <5 pF) and the 4 mA pin current limit.
- Electromigration / metal current density on rails and ua stubs; power-stripe width beyond the tool's minimum.
- Metal density / fill (added after precheck by TT).
- Substrate noise, latch-up, guard rings, ESD behavior of the analog pins.
- Whether 3v3 devices sit on the right supply, and that VAPWR is not used by thin-oxide devices.
- Dummy-fill / matching quality (common-centroid) and cap density.
- Magic and KLayout DRC are the same decks used by TT, but with newer tool versions here than TT pins.

## Gotchas found
- Precheck's `magic -noconsole -dnull` hangs forever if stdin is a terminal; run with `</dev/null` (same family as the netgen stdin gotcha).
- `save /abs/path` in magic renames the top cell to the path, tripping the top-name, pin and cell-name checks; save with a relative name from the project dir.
- Precheck must run from `tools/precheck` (relative `../tech`, `magic_drc.tcl`); `yowasp-yosys` must be on PATH (venv bin).
- Magic DRC is fast here (seconds) on a near-empty layout; expect minutes on real layout.
