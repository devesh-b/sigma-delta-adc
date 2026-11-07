# S0 part C: TT analog template through TT precheck

Date 2026-11-07. Driver: `scripts/s0_precheck.sh` (sandbox only; W and RUN_TAG from env, default never the shared WO-01 dir).

## Sources (cloned fresh under `$W/` = `/home/mempool/regr/tt/runs/<repo>/precheck` by default, or `W=...`; never `/home/mempool/tt`)
- Template: https://github.com/TinyTapeout/ttsky-analog-template.git @ `301590bc02ffeabc2bb176489de9db0818a4b958` (workflows use tt-gds-action `ttsky26d`)
- Tools: https://github.com/TinyTapeout/tt-support-tools.git @ `9d13ff3e3e6202090740110438c6a10c1d62ca0f` (main at clone time; CI uses main at run time, so re-run on main just before submission and record the hash, review N-1).
- **Precheck runs inside TT's own `nix-shell tools/precheck/default.nix`**: magic 8.3.568 and klayout 0.30.8 (printed per run as the `TOOLS` line in each `proj_*/precheck.log`, and checked by the script). `tool-versions.json` in tt-support-tools (klayout 0.30.4) is stale. venv python supplies the pip modules (gdstk, yaml, klayout.db, yowasp-yosys). The IIC image is not used for precheck (IIC has magic 8.3.685). The dummy layout is built with the newer nix-profile magic (8.3.693); build tools may be newer.
- PDK: CI precheck@ttsky26d uses open_pdks `0536d02`; the sandbox `~/.ciel` has `d56f8a8e`, one commit ahead (metadata + gf180 only, per review S-4). Default runs use the sandbox PDK; see "PDK check" below for a run against 0536d02.

## Dummy project
2x2 analog tile, `uses_vapwr: true`, `analog_pins: 3` (ua0 VIN+, ua1 VIN-, ua2 VREF), DEF `tt_analog_2x2_3v3.def`. Magic builds it from the DEF: met4 power stripes VDPWR/VGND/VAPWR (2 um wide), one met4 stub on each of ua0..ua2, and (S-2) uo_out[7:0], uio_out[7:0], uio_oe[7:0] tied to VGND in the GDS: 24 met4 stubs on the top-edge pins joined by a met4 bar that links to the VGND stripe. Verilog ties the same outputs to 0. No met5.
**Precheck does not check the digital tie in the GDS** (it passed before the tie existed); the V8 GDS-vs-Verilog tie check covers it.
Deviation from the original WO: no poly resistor; met4 stubs only (the pin check needs only metal).

## Results (driver: `scripts/s0_precheck.sh {ok|met5|drcbeol|drcfeol|apin|apinx|all}`; logs under `$W/proj_<variant>/`)
Each broken variant must fail exactly the listed rows; every other row must stay green. `all` checks this, and also that the pinned tool versions were used.
| Variant | Defect | Expected failing rows | Result |
|---|---|---|---|
| ok | none | none | all 15 checks green, magic 8.3.568 / klayout 0.30.8 |
| met5 | one met5 rect | `KLayout Checks` (Forbidden layer met5) | as expected |
| drcbeol | met4 wire 0.2 um wide (min 0.3) | `Magic DRC`, `KLayout BEOL` | as expected |
| drcfeol | poly sliver 0.1 um wide (min 0.15) | `Magic DRC`, `KLayout FEOL` (poly width is in both decks) | as expected |
| apin | ua[2] stub removed | `Analog pin check` naming ua[2] | as expected |
| apinx | extra stub on ua[3] | `Analog pin check` naming ua[3] | as expected |
A first `all` run flagged drcfeol because Magic DRC also fails on the poly sliver; the expectation was corrected to include it. That is a rule overlap, not a tool problem.

## PDK check (S-4)
`ciel enable` of `0536d02d875c8f67dd7cca3902ac457e62f20005` into a separate root `/home/mempool/regr/tt/WO-01/pdk-ci` worked (3 calls; `/home/mempool/.ciel` untouched). Precheck `ok` run against it with `PDK_ROOT=/home/mempool/regr/tt/WO-01/pdk-ci`: **ACCEPT**, all 15 checks green (log `/home/mempool/regr/tt/WO-01/a/pdkci/proj_ok/precheck.log`). The d56f8a8 vs 0536d02 difference is therefore moot for S0.

## Reproduce
`W=<dir under /home/mempool/regr/tt> scripts/s0_precheck.sh all` and `OUT=<dir> scripts/s0_toolcheck.sh` from the tree under test. Acceptance from a frozen copy (`/home/mempool/regr/tt/acc-test`, outputs in `acc-out`): toolcheck ACCEPT (SMOKE_CORNER=ff: REJECT), precheck ok ACCEPT, and the `find -printf "%p %T@"` listing of `/home/mempool/regr/tt/WO-01` was identical before and after.

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
- N-4: CI's custom_gds path (strm2oas, klayout 0.29.12) is not exercised here; low risk.
- V8 additions from review WO-01: GDS-vs-Verilog tie, LVS with device parameters, magic antennacheck, overvoltage/SOA ERC, latch-up/guard rings, floating nets, fill near matched MIM, ESD on ua pins, PEX and IR drop.

## Gotchas found
- Precheck's `magic -noconsole -dnull` hangs forever if stdin is a terminal; run with `</dev/null` (same family as the netgen stdin gotcha).
- `save /abs/path` in magic renames the top cell to the path, tripping the top-name, pin and cell-name checks; save with a relative name from the project dir.
- Precheck must run from `tools/precheck` (relative `../tech`, `magic_drc.tcl`); `yowasp-yosys` must be on PATH (venv bin).
- Magic DRC is fast here (seconds) on a near-empty layout; expect minutes on real layout.
