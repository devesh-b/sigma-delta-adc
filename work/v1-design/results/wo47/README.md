# WO-47 results: C9 LibreLane feasibility probe (synthesis + floorplan)

- Frozen copy: `/home/mempool/regr/tt/WO-47-7742be2/c9_digital` (local HEAD 7742be2; RTL unchanged since 25be205; flow/
  = the WO-47 drafts committed with this README). Other local uncommitted changes (design/c1_ota1) are not in this copy.
- Tool: LibreLane v3.1.0.dev3 (IIC-OSIC-TOOLS 2026.10), sky130A = TT-pinned open_pdks d56f8a8e (`/foss/pdks-tt`).
- Command (in `flow/`): `librelane --manual-pdk --pdk-root /foss/pdks-tt --pdk sky130A --scl sky130_fd_sc_hd --run-tag probe
  --overwrite --to OpenROAD.Floorplan config.json` -> `EXIT=0` (`flow/probe.log`). Run dir `flow/runs/probe`.
- Steps run: Verilator.Lint (errors / warnings / timing constructs clear), Yosys.Synthesis, unmapped-cell / synth / assign
  checks, CheckSDCFiles, CheckMacroInstances, STAPrePNR (3 nom corners), Floorplan.

| Item | Value | Source |
|---|---|---|
| Cells | 1111 | `06-yosys-synthesis/reports/stat.rpt` |
| Cell area | 15,172.05 um2 | same |
| Flops | 257 dfrtp_2 (6.75k um2) + 19 dfstp_2 (0.50k um2) | same |
| Latches | none ("No latch inferred") | `latch.rpt` |
| Setup WNS (pre-PnR, ideal clk) | ss_100C_1v60 1.753 ns, tt_025C_1v80 9.067, ff_n40C_1v95 9.378; TNS 0 | `12-openroad-staprepnr/summary.rpt`, `final/metrics.json` |
| Hold WNS (pre-repair) | -1.063 ns (ss), 39 violations, 9 reg-to-reg at ff (-0.0018 ns) | same |
| DRV (pre-repair) | max slew 559, max fanout 16, max cap 5 | `final/metrics.json` |
| check_setup (unconstrained, no clock, no input delay, loops) | no entries | `nom_ss_100C_1v60/checks.rpt` |
| Floorplan | die 150 x 80 (placeholder), core 7,935 um2, utilisation **1.91** (too small, expected) | `13-openroad-floorplan` log |

Critical path (ss): `u_core.act[8]` (fs_div[1]) -> or3/xnor2/or4 compare chain -> nor4b `_0814_` (slew 10.1 ns, drives the
mux selects) -> a22o -> dfrtp D, arrival 18.58 ns. Slew-dominated, unbuffered: pre-PnR only.

Warnings: `FP_PDN_MULTILAYER` deprecated (rename before PnR); `[ORD-0032] Invalid thread number specification: None`
(OpenROAD threads, harmless for the probe). Everything here is pre-placement, ideal clock, no parasitics: no timing claim.
Interpretation and plan: `design/c9_digital/HARDENING.md`.
