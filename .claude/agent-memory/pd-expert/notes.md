# pd-expert notes (tt sigma-delta)

## Flow / tool versions (verified 2026-11-07, WO-01 review)
- Template ttsky-analog-template @301590b uses tt-gds-action/*@ttsky26d (action commit 395eedb, 2026-09-18).
- precheck@ttsky26d: tools-ref default `main` (tt-support-tools has no ttsky26d branch/tag; latest shuttle branch ttsky25a).
  sky130A PDK in CI = open_pdks 0536d02d875c...; sandbox ciel = d56f8a8e (1 commit ahead; diff = VERSION + reference
  hashes in sky130.json + gf180 magic tech only -> sky130 decks identical, reasoned).
- CI tools come from tools/precheck/default.nix: nix-instantiate says klayout-0.30.8, magic-vlsi-8.3.568.
  precheck/tool-versions.json (klayout 0.30.4) is STALE. pip klayout module in CI is ">=0.30.8,<0.31" (unpinned in range).
- Sandbox: nix magic 8.3.693 / klayout 0.30.13; IIC image magic 8.3.685 / klayout 0.30.12. nixpkgs tarballs for
  default.nix are now in the sandbox nix git cache -> `nix-shell tools/precheck/default.nix` reproduces CI tools.
- sky130 precheck checks: Magic DRC (drc full), KLayout FEOL/BEOL/offgrid/pin-label/zero-area, KLayout checks (top name,
  forbidden met5, prBoundary), pin, boundary, power pin, layer, cell name, urpm/nwell, analog pin, yosys syntax.
  Antenna check is gf180mcuD only (techs list in precheck.py). No LVS, no GDS-vs-Verilog tie check.
- sky130.lib.spice sections: tt sf ff ss fs, ll hh hl lh (R+C only with tt MOS), ss_{ll,hl,lh,hh}, sf_{ll,hl,hh}
  (no sf_lh), fs_{ll,hl,lh,hh}, ff_{ll,hl,lh,hh}, all *_mm variants, mc. hh = res_high + cap_high (MIM scales globally).

## Past findings
- WO-01: dummy GDS left uo_out/uio_* untied (Verilog-only tie) and precheck still passed -> precheck does not check it.
- WO-01: DRC non-vacuity only via met5 forbidden-layer (python check), DRC decks never shown to fail.
- params.py (WO-01): OTA_A0_DB_MIN 75 vs SPEC 80 dB (Q6); VREF option B missing k=0.5; corner set lacks ss_hh/ff_ll,
  VDPWR not independent axis (SPEC 135-pt), MC sections not named.

## Open risks / unverified
- Whether TT fill is applied over analog tiles and which blockage it honours (matching near MIM). Unknown.
- sky130 cap_mim_m3_1 mismatch model presence under *_mm. Unverified.
- Latch-up tap-distance coverage in TT KLayout FEOL deck. Unknown.

## C9 digital (WO-47, 2026-11-12)
- IIC image 2026.10 has LibreLane v3.1.0.dev3 (`/foss/tools/bin/librelane`); run with `--manual-pdk --pdk-root /foss/pdks-tt`.
  `FP_PDN_MULTILAYER` is deprecated there (rename). Default STA corners: tt_025C_1v80, ss_100C_1v60, ff_n40C_1v95.
- rta-tt lock blocks when other agents hold it; launch long jobs with `ssh sandbox 'cd tt-sd && nohup nice scripts/iic ... &'`.
  Avoid `grep -v` pipes in rta-tt (output buffered, call hung >120 s).
- Probe: 1111 cells, 15,172 um2, 276 flops; pre-PnR ss setup WNS 1.75 ns (fs_tick fanout slew 10 ns, unbuffered).
  Est. die ~190x150 um = 35-45 % of 2x2 tile (72,071 um2); SIZING budget 8-15k um2 -> over ~2x. Lever: acc widths 32->14/25 b.
- Pattern for digital in analog tile: separate OpenLane macro in Magic top (flash-adc encoder, tt07 SAR state_machine).
- Open: comp_in unsynchronised (F-IF-1, needs latched comparator + clk->comp_in min delay); no hd lib at 125 C / 1.98 V;
  macro name tt_um_sd_adc_c9 clashes with top-module naming; analog outputs flop-driven unverified.

## C9 PnR (WO-58B, 2026-11-13)
- Flow inputs at 3e1e9ea; frozen copy /home/mempool/regr/tt/WO-58B/3e1e9ea/c9_digital (regr/tt mount = /foss/designs/regr works).
- LibreLane 3.1: `PDN_MULTILAYER` (FP_ name deprecated). Setting `LIB` disables pdk_compat defaults for STA_CORNERS,
  DEFAULT_CORNER, TIMING_VIOLATION_CORNERS -> list them all. PDK default TIMING_VIOLATION_CORNERS = ["*tt*"] (ss/ff
  violations would NOT fail the flow) -> set ["*"]. Checkers raise DeferredStepError (flow completes, then fails).
- `pdk_dir::` prefix works in config. hd libs present incl. ss_100C_1v40, ss_n40C_1v40/1v28, ff_100C_1v95; none at 125 C.
- Macro sd_adc_c9 has no ena/uio_in/uio_oe ports (wrapper ties them); SDC/pin order fixed (STA-0366 seen in first launch).
- Synth 860 cells / 11,790 um2 / 223 FF; 190x150 die -> util 0.515 (room to shrink to ~150x130 later).
- Benign: RSZ-0020 2 floating nets = VPWR/VGND; STA-1140 lib "already exists" (read per RC corner).
- Gotchas: `pkill -f <pattern>` over ssh kills the ssh's own shell if the pattern is in the command line (exit 255).
  `ssh sandbox '... setsid nohup ... &'` keeps the ssh channel open (docker -i); returns only when the job ends.
  Detailed-routing log is buffered; progress is visible in pnr1.log (stdout).
- Result pnr1 (EXIT=2): setup FAILS only at ss_100C_1v40 (max RC -1.60 ns, Fmax 44.6 MHz); ss_1v60 +5.92, tt +8.46, ff +9.04.
  Hold min +0.068 (max_ff). Magic/KLayout DRC 0, LVS 0, antenna 0, XOR 0. Util 0.711 at 190x150. 54 max-fanout (all
  corners), 203 max-slew (ss_1v40 only). Critical path act[7] -> fs_div compare -> resizer fanout buffers = clkdlybuf4s25_1
  (65 in netlist, ~5 ns of path) -> overrun. Red flag: delay cells as repair buffers; check dont-use for clkdlybuf* next run.
- ext.sh must use container paths (/foss/designs/regr/...) when run via scripts/iic.

## C9 WO-60A (2026-11-13): delay-cell ban
- LibreLane 3.1.0.dev3 don't-use = `EXTRA_EXCLUDED_CELLS` (config/flow.py; old RSZ_DONT_USE_CELLS/DONT_USE_CELLS), unioned
  with PDK PNR_EXCLUDED_CELL_FILE (openlane/sky130_fd_sc_hd/drc_exclude.cells has only clkdlybuf4s15_1/s18_1), set_dont_use in
  every OpenROAD step (io.tcl). Keys starting "//" are ignored by the config loader (config.py:1057).
- Full PnR of C9 takes ~4-5 min. Frozen via `git archive <sha> design/c9_digital | ssh sandbox tar -x` (clean, reproducible).
  No jq on sandbox host; put python in a script file under the run dir and run it via scripts/iic (inline quoting breaks).
- Result: fanout buffers become buf_1; ss_100C_1v40 max -1.181 ns (was -1.599), Fmax 45.4 MHz; tt path 12.25 ns > P/2.
  Slew vio at ss_1v40 rose 203->336; new max-cap 1 at nom/max ss_1v60; fanout 54 unchanged. A dlygate hold buffer
  (hold153, 1.67 ns) sits on the setup-critical endpoint _1254_ at ss_1v40. RTL fix (WO-60 Part B) is the real lever.
- Max-cap/slew checkers did not fail the flow despite nonzero metrics: checker corner scope unverified (open).
- Git commit signing (1Password) can fail intermittently ("failed to fill whole buffer"); leave staged and report.

## C9 WO-66 (2026-11-13): retimed RTL PnR
- Run /home/mempool/regr/tt/WO-66/e450ae2-r60b (e450ae2 flow + WO-60B RTL; WO-60B freeze is a FLAT dir of *.v, not design/...).
- EXIT=0. Setup met all 12 corners: ss_1v40 max +2.582 (Fmax 54.8 MHz), ss_1v60 +7.40, tt +8.73, ff +9.23; hold min +0.108 (ff).
  New ss_1v40 crit path u_seq.c[5] -> or-chain -> buf_1 fanout bufs -> a2111o chain -> cfg_pending (18.65 ns arrival).
- P/2 rule must use worst reg-to-reg arrival (tt 6.66 ns), NOT P - WS: tt WS is an output-port path (0.3P output delay).
- DRV open: fanout 46, slew 256 (ss_1v40), max-cap 3 (max_ss_1v60); flow EXIT=0 anyway. Repair uses RSZ_CORNERS or
  STA_CORNERS (steps/openroad.py:2439) so ss_1v40 should be in repair scope; why repair leaves them unknown -> read checks.rpt.
- Physical clean (DRC/LVS/XOR/antenna 0), util 0.704, 342 diodes, IR worst 0.34 mV, power 1.644 mW.
- Background ssh launch: `setsid nohup bash launch.sh </dev/null >/dev/null 2>&1 &` still holds the channel (docker -i) until done;
  run it via Bash run_in_background and wait for the notification.

## C9 WO-67 (2026-11-13): buf_1 ban = regression
- Run /home/mempool/regr/tt/WO-67/9413a36-r60b (config 9413a36). EXIT=0. Banning buf_1 -> repair_design uses dlygate4sd3_1
  for ALL fanout buffers (70); ss_1v40 WS +2.58 -> +0.17; slew 256->108, cap 3->0, fanout 46->51. Lesson: the resizer's
  smallest-buffer pick falls to delay cells when weak bufs are banned; need buffer-list control, not dont_use.
- WO-66 fanout 46 = 10 CTS leaf (12-13 sinks) + 36 from heuristic diodes (one per sink; diodes count as fanout and cap).
  GRT antenna check before heuristic insertion: 0 vio. RUN_HEURISTIC_DIODE_INSERTION default false (classic.py:166).
- Mid-PnR STA steps report nom_tt only; only RepairDesignPostGPL runs (RUN_POST_GRT_DESIGN_REPAIR default false, classic.py:139).
- checks.rpt "max slew" pin lists include ANTENNA_*_DIODE pins (~40-50%); count nets/drivers, not pins. If no max-cap section,
  an awk range /max slew/,/max cap/ runs into the fanout list.

## C9 WO-69 (2026-11-13): heuristic diodes off
- Run /home/mempool/regr/tt/WO-69/7841d57 (config 7841d57 = e450ae2 + RUN_HEURISTIC_DIODE_INSERTION false). EXIT=0.
- Fanout 46->10 (clkbuf_leaf only, 12-13 sinks), slew 256->43 pins (drivers fanout116/68/57 buf_1 + _1110_ nor3b_2, ss_1v40 only),
  cap 3->0, diodes 342->13, CheckAntennas 0/0, DRC/LVS/XOR 0. ss_1v40 max setup +2.702 (Fmax 55.2 MHz), hold min +0.108.
- Coordinator "revert done" claims need a git diff check: the first revert had not landed (HEAD still had buf_1 ban).
- Next (unrun): CTS sink clustering <=10 (variable name unverified), then RUN_POST_GRT_DESIGN_REPAIR true.

## C9 WO-71 (2026-11-13): CTS clustering size 8
- Run /home/mempool/regr/tt/WO-71/fe8b8bf (config fe8b8bf). EXIT=0. CTS var = CTS_SINK_CLUSTERING_SIZE (steps/openroad.py:2495, no default,
  cts.tcl:67). Unset -> TritonCTS auto-picks 10/50um (CTS-0206) but leaves overflow to 12-13 + dummy loads; 8 -> 30 leaves, fanout 0.
  No CTS_MAX_FANOUT var exists. Slew 43/11 at ss_1v40 unchanged (fanout116 buf_1 net, 1.72 ns). Power 1.655->1.705 mW. Setup ss_1v40 +2.777.
- Max Slew checker only WARNS (checker.py:626), EXIT=0 despite violations.
- ~/bin/rta-tt does not exist on the sandbox host; run `cd /home/mempool/tt-sd && scripts/iic "bash <script>"` directly. Complex
  quoting: write script locally (scratchpad), scp to run dir, run via iic.
- Next (unrun): RUN_POST_GRT_DESIGN_REPAIR true.

## C9 WO-72 (2026-11-13): post-GRT repair = no-op
- Run /home/mempool/regr/tt/WO-72/8898159 (config 8898159). EXIT=0. RUN_POST_GRT_DESIGN_REPAIR (classic.py:139) ran step 41 with 12 corners,
  repair_design slew_margin 10 -> 0 resized/0 buffers. All metrics identical to WO-71 (slew 43/11 ss_1v40 1.72 ns).
- Estimated parasitics (placement, set_wire_rc met2) show 0 slew violators at ss_1v40 => estimate-vs-RCX gap; resizer never sees it.
  Lever: GRT_DESIGN_REPAIR_MAX_SLEW_PCT (openroad.py:2711, default 10) / _MAX_CAP_PCT. Unrun.
- Standalone openroad on a step ODB: set ::env(SCRIPTS_DIR) and source step _env.tcl is not enough for set_rc.tcl (needs lln:: procs);
  use set_wire_rc. report_net needs a name, not get_nets -of_objects (STA-0232).
- timing__drv__floating__nets = 2 in WO-71 and WO-72: not root-caused (open).

## C9 WO-73 (2026-11-14): BLOCKED, sandbox ssh refused
- ssh sandbox failed 3x: 1Password agent "refused operation"/"communication with agent failed" (IdentityAgent 1Password sock; needs user unlock).
  Nothing ran. Drafted untested work/v1-design/results/wo73/diag_slew.tcl (MODE placement|grt|spef, report_net by name, slew_max per sink).
- Config left at GRT_DESIGN_REPAIR_MAX_SLEW_PCT default 10 (not edited: WO says measure first, then size).
- UPDATE: ssh recovered. Diag measured RCX-max/GRT-est slew ratio 1.37-1.49 -> set 40 % (commit 9def89a). Run WO-73/b8898159-c9def89a EXIT=0:
  step 41 repaired 33 nets/5 bufs; slew 43->32 max ss_1v40 but worst still 1.728 (other sinks). Setup ss_1v40 +2.96. Floating 2 = RSZ-0020 step 32, unnamed.
  Trap: HEAD moved (WO-74 RTL bias_ok) -> archive the WO base commit + only the changed file; check git log base..HEAD before freezing.
  get_property on ports needs -object_type; use odb getITerms/getBTerms for net driver/load scans.
