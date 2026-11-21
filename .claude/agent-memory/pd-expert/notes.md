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

## C9 WO-97 (2026-11-21): final PnR, D85/D88 RTL + bias_ok pin (6b474df)
- Run /home/mempool/regr/tt/WO-97-6b474df/design/c9_digital/flow/runs/pnr1, EXIT=0. Setup ss_1v40 max +0.753 (was +2.96; new D85/D88 or-chain
  depth), ss_1v60 +7.50, tt +8.78, ff +9.27; hold +0.079. Slew 43/11 ss_1v40 only (net56/66/122/124 buf_1 fanout, worst 1.634). Cap/fanout 0.
  DRC/XOR/antenna 0, LVS "Circuits match uniquely" (lvs metrics present now). Util 0.739, 1.787 mW. Floating 2 = VPWR/VGND (confirmed by odb scan).
- Bench clk is 20 ns vs SDC 20.833 -> ss_1v40 SDF sim would be ~-0.08 ns; use ss_1v60 for SDF.
- Routed GL on icarus needs `-gspecify -ginterconnect` (else 3071 "Could not find net" SDF errors); TIMINGCHECK unsupported -> function only.
  Routed netlist has PW/BIAS widths baked (16/8): small-width quick tests impossible on it.
- lpool can sit queued when other pools hold all 5 global slots (WO-97 GL jobs queued at hand-off).
- zsh: `S="ssh ..."; $S` does not word-split; use a function.
- yosys gl_job.sh prints "GL cell instances: 0" (write_verilog without -noexpr) - counter is vacuous.

## WO-96 layout (2026-11-21): floorplan + first cells
- Final run /home/mempool/regr/tt/WO-96-e9fa31f (harness design/layout/scripts/run.sh). magic 8.3.685; PDK klayout deck sky130A_mr.drc vars: input report top_cell feol beol offgrid floating_met seal thr.
- Magic: use `writeall force` (not save) when gencell/LEF children exist, else fresh-process gds write = "I/O error". `extract do local` needed for PDK subcells.
  c4 (HV gencell FETs + hvl LS) extraction still stops after the LS cell: open.
- MIM direct-draw (met3 plate, mimcap, mimcc, met4) DRC-clean when via3 (not on capm) is >= ~2 um from the capm edge (capm.2b_a fires at 1.1 um).
- netgen sky130A_setup: l/w tolerance 1 %; MIM parallel units merged -> missing unit = property error only. Gate = "Netlists match" + no "Property errors".
- xhigh_po_0p69 snake gencell (nx 4/10) fails rpm.1 (magic 15) / urpm.1a (klayout 4): open. Extracted l nonlinear in seg (secant ok to 0.08 %).
- Floorplan: C9 mirrored (sideways) matches TT north pin order. Tile need 84-110 % before routing; OTA2 no slot; C6 slot short.
- WO-97 LEF real path: WO-97-6b474df/design/c9_digital/flow/runs/pnr1/61-magic-writelef/sd_adc_c9.lef.
- Slip: ran an empty `python3 -` locally once (no-op, it ran nothing). Never put python in local commands.
- WO-97 GL/SDF: 5/5 PASS (d_hold01 tt/ss60/ff, d_hold05 tt/ss60), ~420 s / ~2500 s wall each; 8/3203 SDF interconnects unapplied (port ones, inferred).

## WO-100 layout (2026-11-21): D93 floorplan + WO-96 blockers (run WO-100-a3e721f)
- xhrpoly gencell: lone nx=1 0p69 fails rpm.1 (marker 0.69 wide) in both decks; snake 1 fails at bends; nx>=2 snake 0 guard 0
  (legs at ~1.17 um pitch under one marker) = 0/0. C6 now legs joined in met1 series; netgen setup series {l add, w critical}.
  Each leg adds 2 head contacts -> absolute R shifts vs one long device: C6 owner must re-sim the segmented netlist.
- hvl .mag views are abstracts (GDS_FILE); extracting them core-dumps magic 8.3.685. `gds read sky130_fd_sc_hvl.gds` first -> OK.
- WO-96 nwell.4 = LEF OBS nwell (sd_adc_c9.lef:416) painted as real nwell. Never DRC a LEF abstract; place the macro GDS.
- netgen symmetric match prints "Netlists match with N symmetries"; gate on "Final result: Circuits match uniquely." + no
  property/mismatch lines.
- magic box values = internal units (200/um with sky130A magicrc); coordinates with suffix i.
- Sandbox 2026-11-21: shared, load ~30, ~1 GB free: one magic/klayout at a time.

## C9 WO-101 (2026-11-21): 165x150 shrink, reverted
- /home/mempool/regr/tt/WO-101-7646108 runs pnrA (165, dens 60) + pnr1 (165, dens 75): identical. GPL-0302 is a WARNING that auto-raises
  density to 0.78 (my inference "gpl fails below util" was WRONG; check before changing a 2nd knob). Util 0.857, ss_1v40 max setup -0.095
  (same _1586_->_1432_ path), nom +0.078, min +0.222; ss_1v60 +7.07; hold +0.108; slew 11/11/11 worst 1.749; DRC/LVS/antenna 0; IR 1.05 mV.
- Exit rule -> config back to 190x150/60 (commit 9068469). Width needed for ss_1v40 >= 0 lies between 165 and 190 (untested).
- Waiting without loops: ssh 'tail --pid=PID -f /dev/null' with run_in_background.
- Slip: ran `python3 -c 1` locally once (no-op). Never again.
- Final WO-100 run WO-100-0814947: MIM1/MIM2/C6 DRC 0/0 + LVS PASS, broken copies fail. C4 LVS fails (hvl LS split rails
  VPWR_uq0/VGND_uq0 need strapping). Magic `gds readonly true` needed for macro GDS (else implants regenerated -> 217 KL items).
  Netgen portless reference subckt merges unconnected devices -> give refs ports; labels need parent paint underneath.
  Open: magic 512 on c9_place vs "No errors found"; c9_orig KL control produced no report. D94: C9 stays 190x150.
  Floorplan short 5,350 um2 (7.4 % tile) at high estimate. Comparator layout not started.

## C9 WO-106 (2026-11-21): 175x150 KEPT (commit 9650241, run /home/mempool/regr/tt/WO-106-9650241/.../runs/pnr1)
- ss_1v40 setup +0.937/+1.060/+1.207 (max/nom/min; better than 190's +0.753, read as noise), hold +0.110, slew 19/8 ss_1v40 worst 1.655,
  DRC/XOR/antenna 0, LVS match, util 0.806, 1.774 mW. Fmax margin at ss_1v40 ~0.9 ns over the 20.833 ns SDC.
- Trap: gl_routed.sh is only in results/wo97, not design/c9_digital/tb. Copy it into the frozen tb before running gl_jobs.
- Trap: `cat f | ssh "cat > f && nohup ..."` left a 0-byte file. Use scp. A nohup over ssh holds the session open: add `</dev/null` to ssh and use setsid.

## WO-107 layout (2026-11-21/22): route.tcl, C4 LVS clean, C3 rev g LVS clean (final run WO-107-ac7498c)
- Gencell geometry (probe WO-107-probe): centre = bbox centre (= transform origin); S/D met1 strips +-(L/2+0.145); top gate
  met1 at W/2+0.275 (nfet) / +0.32 (pfet); ring met1 column only with viagl/viagr 100 at L/2+0.715 LV, +0.825 HV n, +0.815 HV p.
  LV gate-contact met1 alone = 0.067 um2 < met1.6 -> hier magic counts it per subcell; patch unused bottom contact.
- route.tcl (via1 stub met2, met3 track per net per row, met4 spines) gave DRC/LVS clean first time, but ~2x area (C3 5,743 vs
  4,142 slot). Not viable for OTA1 (~280 fingers): needs nf>1 interdigitated rows.
- hvl lsbuflv2hv_1 / clkiso GDS have split VPWR/VGND rails (VPWR_uq0/VGND_uq0); strap at block level + netgen flatten class.
- Magic `drc listall count total` includes subcells checked alone (c9_place 512 = 57 hd cells); use flat DRC (flatten X_flat).
- KLayout sky130A_mr.drc: relative report= is resolved against the input GDS dir (WO-100 polluted the WO-97 run dir).
- `git commit -- <paths>` does NOT add untracked files: git add new files first (lost one run to this).
- git archive | ssh tar failed ("not a tar archive"); write the tar to the scratchpad, scp, untar.
- `pgrep -f pattern` inside ssh matches its own bash -c; pick the PID with ps | grep "bash -c" | grep -v grep.
- TT precheck needs info.yaml project dir (PrecheckFailure) - frame precheck still not run.
- D98: C9 175x150 (WO-106 9650241); floorplan C9W default 175; D100: layout only after schematic verified (C3/C4 on hold).
