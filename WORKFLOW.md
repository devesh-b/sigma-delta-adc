# WORKFLOW — how work is done in tt

Working rules for this project, adapted on 2026-11-07 from the AlphaOneSoC
export (`process/export-2026-11-07/PRINCIPLES.md`, kept unchanged as the
source). That export came from digital RISC-V work. This file keeps what
transfers to an analog/mixed-signal ΣΔ ADC, and marks what is new for analog.

"User rule" = the user stated it explicitly. The rest are lessons that cost
time when ignored. Each rule carries its reason so it can be bent sensibly.

Placeholders: `<sandbox>` = remote sim/build box (not set up for tt yet,
see §4), `<campaign>` = a named batch of work (e.g. `ota-v1`).

---

## 1. Talking to the user

- **"doc" = a Markdown file. "report" = an HTML report page.** (User rule.)
  Docs go in the tt root (top-level design docs) or `work/<campaign>/`.
  Do not use the Claude Docs connector unless asked by name: other agents and
  tools cannot read it.
- **Calm framing.** (User rule.) State gaps and risks as facts; rate severity
  by technical impact, not alarm words. Ask before assuming what a milestone
  word means (freeze, done, signoff). Recommendations stay options; the user
  owns the plan. Learning project, not a competition.
- **Fixed vs settable.** Say which things are set in silicon (cap ratios,
  integrator coefficients, OTA sizing) and which are settable after fab
  (OSR/N via digital control, chop on/off, order select, clock frequency).
- **Units the user thinks in.** Area: whole TT tiles (analog tile count,
  currently 2x2) + headroom. Performance: ENOB, µV rms input-referred noise,
  INL in ppm, SPS, power in µW/mW. Not raw µm² or raw dB without the bits.
- **Reviews: silent until done, then one document**: verdict + per-area
  scorecard; severity-ranked findings (where / PROVEN or REASONED / fix);
  claim -> verdict table; verification gaps as a task list; what held up;
  evidence paths.

## 2. Files, state, memory

- `~/projects/tt` is the workspace (user rule, see `memory/`). `work/<campaign>/`
  holds campaign state: `AGENTS.md` ledger, `DECISIONS.md`, `wo/` work
  orders, `STATE-<date>.md`, and durable results.
- **Valuable results never live only in a tool output dir** (ngspice raw
  files, OpenLane `runs/`, `model/out/` reruns). Copy the numbers + the exact
  command into `work/<campaign>/`.
- **State doc at each milestone** (`work/STATE-<date>.md`): what exists, what
  was measured, decisions, next work, rerun commands, gotchas, evidence paths.
- **Memory** (`memory/`, symlinked as Claude's project memory): one fact per
  file, frontmatter `name`/`description`/`metadata.type`, pointer line in
  `MEMORY.md`, feedback memories carry **Why** / **How to apply**, absolute
  dates, mark the current entry point `RESUME HERE`. Update, don't duplicate.
- **Agent memory**: `.claude/agent-memory/<agent>/` per specialist (recipes,
  tool quirks, open findings). Agents write there by absolute path.

## 3. Git (applies once tt or a design repo is under git)

tt itself is not a git repo today. When a design repo exists:

- Branch per topic off `main`: `<topic>_<github-user>`.
- **Atomic commits, made as you go, without being asked.** (User rule.)
  Smallest functional change = one commit; split independent hunks; order
  change -> test -> docs. No uncommitted work at the end of a task.
- **Untested commits are fine** when the verify loop is slow. (User rule.)
  Batching waiting on a suite kills bisection.
- Commit body says **why, with evidence** (error text, file:line,
  before/after numbers).
- **No attribution trailers.** (User rule.) No `Co-Authored-By`, session
  links, "Generated with". tt's `.claude/settings.json` blanks attribution;
  repeat "no attribution trailer" in every agent brief.
- **Push, PR, merge, force-push only on explicit OK.** Local commits on the
  working branch are standing permission.
- Rebases keep dates (`--committer-date-is-author-date`), backup ref first,
  `--force-with-lease` only with an OK.
- **Staging by explicit path only.** No `git add -A` / `-a`, no `git stash`,
  never stage the user's in-progress files. Coordinator commits with
  `git commit -- <paths>`.
- `gh` is not installed here; use the GitHub REST API via curl.

## 4. Machines: local edits, sandbox runs

- **User rule (2026-11-07): run everything on the sandbox, nothing on the
  local system.** That covers every sim, model run, sweep, synthesis,
  layout/DRC/LVS/PEX and agent self-check, including the Python model in
  `model/` and small ngspice `.op`/`.ac` checks. The local Mac (8 GB RAM, no
  EDA tools) only edits files, reads results, and dispatches.
- **Sandbox = the AlphaOneSoC box** (`mempool@mempool.lan`, ssh alias
  `sandbox`, user decision 2026-11-07). Auth: the 1Password key "Abhiram
  Dasika" (pinned in `~/.ssh/config` via `~/.ssh/sandbox_abhiram.pub`).
  Host key stored 2026-11-07 (ED25519
  `SHA256:Fw2Woh/ne6drf+6cXZnABKmUuzbfEtLBmkDWkBfAZ+w`).
- **Bridge installed on the Mac (2026-11-07):** `~/bin/rt`, `~/bin/rta-tt`
  (tmux session `tt`, workdir `/home/mempool/tt-sd`, init
  `~/.config/rt/init-tt.sh`: cd, `.venv-sbx`, PDK_ROOT), `~/bin/rmount`
  (macFUSE + sshfs installed, but mounts hang until macFUSE is approved in
  macOS System Settings; use the sync script meanwhile), `flock` via brew.
  `~/bin` on PATH via `~/.config/rt/env` sourced from `~/.zshrc`; agents still call `~/bin/rta-tt` by full path.
- **`/home/mempool/tt` is NOT ours.** It is AlphaOneSoC's TT tooling dir
  (`tt-support-tools`, `projects/`, `venv*`). Never write, sync or delete
  there. **Incident 2026-11-07:** the first sync pushed into it with
  `rsync --delete` and deleted files from all of those (evidence:
  `/home/mempool/regr/tt/incident-2026-11-07/`). Repair is the user's call.
  The sync script now refuses any non-empty remote dir without a
  `.tt-sd-root` marker.
- **Layout on the box:** `/home/mempool/tt-sd` = synced tree
  (`scripts/sync-to-sandbox.sh`, rsync `--delete`); `/home/mempool/regr/tt`
  = drivers, sim outputs, STATUS files (outside the synced tree, so a push
  never wipes them); `--pull` copies it into local `sandbox-out/`. The box's
  own venv is `.venv-sbx` (never synced). Other sessions on the box
  (`alpha`, `rt`/MemPool) are not ours: never touch them.
- Record the local source state in each run's STATUS file. Check `df` and
  `tmux ls` before a run; one heavy job at a time.
- **Verified working 2026-11-07:** key login, first sync (2137 files),
  `rta-tt` foreground + `--bg`/`--logs`, `.venv-sbx` (numpy 2.5.4,
  matplotlib 3.11.2), `model/iadc.py` imports. Mac fixes needed: Homebrew
  `bash` (rt fails under macOS bash 3.2), `flock`, `--stats` instead of
  `--info=stats2` (macOS rsync).
- **Box facts (2026-11-07):** Debian 13, 6 cores, 29 GB RAM, Python 3.13,
  iverilog, tmux, docker (LibreLane 3.0.14 / 3.0.5 images). **Disk 95% full
  (52 GB free)**, shared with AlphaOneSoC; the user handles cleanup.
- **EDA tools (installed + smoke-tested 2026-11-07, user approved):** nix user profile
  from plain nixpkgs (prebuilt, no sudo): ngspice 45, xschem 3.4.7,
  magic 8.3.693, netgen-vlsi 1.5.325, klayout 0.30.13, yosys 0.70,
  verilator 5.052. Nix needs
  `--extra-experimental-features "nix-command flakes"` on this box.
  `init-tt.sh` puts `~/.nix-profile/bin` on PATH. Smoke test: ngspice
  `.op` of `sky130_fd_pr__nfet_01v8` W=1 L=0.15, Vgs 0.9, Vds 1.8, tt →
  Id = 46.8 µA (`/home/mempool/regr/tt/smoke/nfet_op.spice`). magic loads
  the sky130A magicrc. xschem untested (needs a display). Gotcha: bare
  `netgen -batch quit` hangs; feed it stdin (`echo quit | netgen
  -noconsole`) and wrap every tool call in `timeout`.
- AlphaOneSoC runs formal jobs on this box (oss-cad-suite smtbmc, other
  sessions). Use `nice -n 10` and never kill a PID you did not start.
- **PDK:** sky130 via `ciel` (in `.venv-sbx`) at
  `PDK_ROOT=/home/mempool/.ciel`, open_pdks
  `d56f8a8ea0f9171cbdc5273035907b93f3f3bed7` = the version TT's
  tt-support-tools sky130 precheck pins. No PDK existed on the box before.
- **IIC-OSIC-TOOLS (primary toolset, user request 2026-11-07):** docker image
  `hpretl/iic-osic-tools:2026.10` (12.5 GB; start scripts + docs cloned at
  the same tag in `/home/mempool/iic-osic-tools`). Run batch jobs with
  `~/bin/rta-tt 'scripts/iic "<cmd>"'` (`--bg NAME` for long ones).
  `scripts/iic` mounts `tt-sd` at `/foss/designs/tt-sd` and `regr/tt` at
  `/foss/designs/regr` (write outputs there), caps at 4 CPUs / 16 GB, and
  refuses to run off the sandbox. PDK default = the TT-pinned `~/.ciel`
  (mounted read-only at `/foss/pdks-tt`); `IIC_PDK=image` uses the image's
  own PDKs (open_pdks `1689ac3f…`, plus gf180mcuD, ihp-sg13g2).
  Image tools: ngspice-47, xschem, magic 8.3.685, netgen 1.5.324, klayout
  0.30.12, yosys 0.70, verilator 5.052, plus vacask, pyopus, ngspyce,
  openEMS. Smoke test: the same nfet `.op` gives Id = 46.79 µA in the image
  (both PDKs) and in nix ngspice 45. The nix tools stay as a fallback.
  No GUI (no X forwarding to the Mac); xschem is used for netlisting only.
- Not yet set up: tt-support-tools for TT precheck. AlphaOneSoC's copy in
  `/home/mempool/tt` is damaged (see incident above); clone a fresh one
  under `tt-sd`'s sibling dir when the submission repo exists.
- If the box is unreachable, nothing runs: write the command and queue it.
- Don't park big downloads in the session scratchpad.

## 5. Long jobs

- **Detached and unattended:** `setsid nohup` driver writing `driver.sid`;
  driver sets its own PATH / PDK_ROOT / venv.
- **Thermal watchdog for heavy runs** (`thermal-watch.sh`, 80 °C kill; user
  rule on the AlphaOneSoC box). Starts with the driver (`launch-multi.sh`).
- **Resumable stages**: `done.<stage>` markers
  (`scripts/resumable-stages-template.sh`). After an unclean reboot, checksum
  the tree before trusting it.
- **A local waiter wakes Claude** (`scripts/wait-sandbox-example.sh` as a
  `run_in_background` script), not a polling agent. Minutes, not seconds.
- One heavy job per agent, under `timeout` + `ulimit -v`, `nice` when shared.
- **Expensive whole-system checks once, at the end.** (User rule.) Here:
  full post-PEX modulator transient + corners/MC + TT precheck after the last
  queued change is accepted, not after each one.

## 6. Agents: tiered pipeline (user rule)

> "Opus should be for thinking alone, Sonnet for writing the code, Haiku for
> running tests and reporting."

Why: usage limits ran out when one Opus agent planned, coded and waited on
sims. The main session is the **coordinator** (dispatch + ledger); subagents
cannot spawn agents.

1. **Opus specialist = planner/reviewer**, short probes only. Project agents
   in `.claude/agents/`:
   - `sd-adc-design-reviewer` — ΣΔ architecture, SC circuit, OTA, decimator,
     TT analog integration. Read-only on the design.
   - `rtl-verification-engineer` — decimator / control / chop-sequencer RTL.
   - `pd-expert` — sky130 TT flow, analog + digital layout signoff.
   Resume the same planner for its reviews via SendMessage.
2. **Sonnet coder** implements ONE work order, self-checks on the sandbox (and shows the
   check fails on the target fault), commits atomically.
3. **Haiku tester** runs the WO's acceptance commands on a frozen copy on the sandbox,
   reports PASS/FAIL per expectation, quoting deviating lines verbatim.
4. **Opus review** for "review"-tier WOs, in parallel with acceptance.
5. One committer at a time (file-disjoint path-limited commits excepted).
6. **Design reviewer on every design change**, at each milestone (design doc
   before schematic/RTL, again after it lands). Correctness and efficiency
   findings in separate sections.
7. Housekeeping: kill leftover pollers by PID; TaskStop agents that keep
   "waiting" after reporting.
8. Ledger: `work/<campaign>/AGENTS.md` + `DECISIONS.md`
   (templates in `process/export-2026-11-07/templates/`).

## 7. Work orders and handoffs

`work/<campaign>/wo/WO-nn-<slug>.md` + `INDEX.md`. Each WO: goal + measurable
target; **spec source** (doc the expectation comes from, never the author's
reasoning); exact files the coder may touch (disjoint across parallel WOs);
design with expected values; acceptance commands + expected output; commit
plan ("no attribution trailer, no push"); tier (routine / review before
accept); **budget** + stop rule. Each campaign starts from a handoff file
every agent reads first. Examples: `process/export-2026-11-07/templates/`.

## 8. House rules pasted into every agent brief

- Never run a clean target that wipes shared output dirs; each agent owns its
  output subdir (`work/<campaign>/<WO>/` or a named sim dir).
- Explicit-path staging; no `git add -A`/`-a`; no `git stash`; no
  attribution trailer; never push.
- No `pkill`/`killall`: kill exact PIDs. Never touch dirs a running sim owns.
- Nothing runs locally (user rule). One sim/EDA job each, on the sandbox,
  under `timeout` + `ulimit -v`; own output dir.
- Leave no sleep/poll loops behind.
- Durable results copied to `work/<campaign>/`.
- Do not edit design sources (schematics, netlists, RTL, layout) unless the
  WO says so. Never edit `repos/` (reference clones, read-only).
- Never write under the public TT submission repo's directory (§12).

## 9. Lean agents, budgets, rate limits

- **No open-ended, token-heavy digs.** (User rule.) Tokens are expensive;
  unattended sim time is cheap.
- Prefer a **fresh agent from a compact handoff** over resuming a bloated one.
- Every agent gets a **hard budget** and a stop rule ending "report k of N
  done, with reasons".
- Experiments only when the plan cannot be written without them, time-boxed.
- Rate-limit resume: status line saves reset times
  (`process/export-2026-11-07/home/statusline.sh`); a one-shot cron at reset
  + 3 min resumes killed agents via SendMessage. **Slow mode** near the limit:
  one coder + one checker, no new planners.

## 10. Reviews

Adversarial, by a fresh Opus agent, read-only, citing the spec (here:
`ROADMAP.md` v1 spec, `MCP3421_TARGET.md`, `SIZING.md`, PDK docs, textbook).
Separate passes for correctness and for area/power/efficiency. Every finding
marked PROVEN (reproduced in sim/model) or REASONED.

## 11. Verification discipline: green is not proof

**Digital (decimator, control, chop sequencer)** — all of these reported PASS
in AlphaOneSoC while testing nothing; apply them unchanged:
empty outputs compare equal (check line counts); comparators that drop
tokens; stale binaries/caches; stimulus not matching the test name; tests
"passing" after running 2% of themselves; audit scripts reading a missing
log; injected cases that never execute; final-state-only checks; X treated
as false in iverilog; benches printing FAIL and exiting 0; vacuous formal
(k-induction from undefined init); no non-vacuity check. Label known
failures and report "N distinct causes". Mutation testing measures the bench.

**Analog / mixed-signal (anticipated, not yet hit here — confirm and update
as they happen):**

1. **Failed `.meas` read as a number.** ngspice prints `failed` or leaves the
   variable unset; a parser defaulting to 0 or reusing the last value passes.
   Fail the script on any missing measurement.
2. **Silent non-convergence / truncated transient** ("timestep too small",
   run ends early). Check the final sim time equals the requested stop time.
3. **Wrong models or corner.** Check the `.lib` section actually loaded (tt
   vs ss/ff), temperature, and supply in the log, not the deck.
4. **Operating point never checked.** Every transistor's region (saturation
   margin Vds−Vdsat) dumped from `.op` before trusting gain or noise.
5. **Spectral artefacts.** Non-coherent tones, too few FFT points or wrong
   window inflate or hide SNDR/spurs. Coherent sampling, report bins and
   window; sanity-check against the behavioural model at the same settings.
6. **Ideal parts left in.** Ideal switches, ideal VCVS OTA, ideal reference
   sneaking into a "circuit" sim. Grep the netlist before quoting results.
7. **Monte-Carlo that isn't.** Same seed per run, or mismatch models not
   enabled → zero spread. Check the spread is non-zero and plausible.
8. **Model ↔ circuit comparisons that share code.** The reference must come
   from the spec / theory, not from the same script that post-processes the
   circuit result.
9. **Non-vacuity for analog checks too:** every pass/fail check must FAIL on
   a deliberately broken copy (e.g. OTA gain dropped 20 dB → INL check must
   fail; chop disabled → offset check must fail).

Testbench intent comes from the spec, never from the designer's reasoning.

## 12. Public TT submission repo

When the shuttle repo (from the TT analog template) exists:
- **No trace of Claude**: no `CLAUDE.md`, `.claude/`, memory, claude.ai
  links, trailers, "Claude"/"Anthropic" text.
- Only TT's own tooling in CI.
- **Do not commit there.** Leave changes uncommitted (backed up as a patch
  outside it) for the user to commit. (User rule.)
- Commits there are by feature, with no private-repo hashes or tool names.
- Scrub scan before the user commits:
  `grep -rnIiE 'claude|anthropic|localfiles|co-authored|generated with|/Users/' --exclude-dir=.git .`
- Keep the shell's cwd outside it; tell subagents not to write there.

## 13. Autonomy when the user steps away

- Keep working; don't block on questions overnight.
- Choose by the north star: **first-silicon success**, then better ΣΔ specs
  than prior TT designs, framed as learning steps. Have the reviewer check
  non-obvious choices.
- Log every non-obvious decision (reason, alternative, reversible?) in
  `DECISIONS.md`; open the final report with that list.
- Nothing outward-facing (push, submit, post) without an ask.
- Ask what an undefined word means; confirm guesses.

## 14. Project-specific rules (tt)

- Scope goes on one named shuttle; check deadlines at tinytapeout.com/runs.
- First-cut success over heroics: MIM caps (`cap_mim_m3_1`) only in the
  signal path, no MOS caps, no met5 MIM (see `memory/project-sigma-delta-tt.md`).
- Area reported as whole TT tiles + headroom; harden only at sizes TT sells.
- Sim-only improvements are rejected; changes must help the real chip.
- Not ported from the export: `area-optimizer` agent (RISC-V datapath
  specific), flip-flop/latch storage rule, Linux goal ladder, confidential
  dir handling (no NDA code in tt today).
