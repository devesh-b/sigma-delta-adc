# Working principles (exported from AlphaOneSoC, 2026-11-07)

These rules came out of ~2 months of RTL + verification work with Claude Code
on a RISC-V SoC for TinyTapeout (sky130). Most are general. The ones tied to
this project are in section 14. Each rule has the reason behind it so it can
be adapted rather than copied blindly. "User rule" means the user stated it
explicitly; the rest are lessons that cost time when ignored.

Placeholders: `<sandbox>` = the remote build/regression box, `<branch>` =
working branch, `<confidential-dir>` = any third-party code under NDA.

---

## 1. Talking to the user

- **"doc" = a Markdown file. "report" = an HTML report page.** (User rule.)
  Docs go in `localFiles/` (git-ignored) unless the user names a place; ask
  before committing one. Do not use the Claude Docs connector unless asked by
  name: other agents and tools cannot read it.
- **Calm framing.** (User rule.) State deadlines, gaps and risks as facts.
  Rate severity by technical impact, not by alarm words ("at risk", "forced").
  Before assuming what a milestone means (freeze, lock, done), ask. Keep
  recommendations as options; the user owns the plan.
- **Be exact about what is fixed and what is settable.** Example: a UART
  divisor's reset value is fixed in silicon, but software can change it.
- **Multi-agent reviews: silent until done, then one document.** Shape that
  worked: verdict + per-area scorecard; severity-ranked findings table
  (where / proven-or-reasoned / fix); claim -> verdict table; verification
  gaps as a task list; "what held up"; evidence paths.
- **Sizes and metrics in the user's units.** Here: whole TinyTapeout tiles +
  the shape hardened + routing density % + utilization % + headroom left, not
  fractional tiles or raw µm². Convey the gist in prose, not a recited
  template. Generalise: find out the unit the user pays for and report in it.

## 2. Git and commits

- **Branch per topic off `main`**, named `<topic>_<github-user>`.
- **Atomic commits, made as you go, without being asked.** (User rule.) The
  smallest functional change is one commit. Split independent hunks in the
  same file into separate commits. Typical order: change -> its test -> its
  docs, each its own commit. No uncommitted work left at the end of a task.
- **Untested commits are fine** when the verify loop is slow (here: an hour+).
  (User rule.) Do not batch changes waiting on a suite; batching kills
  bisection.
- **Commit body says why, with evidence**: exact error text, file:line,
  measured before/after.
- **No attribution trailers.** (User rule.) No `Co-Authored-By`, no session
  links, no "Generated with". Set `"attribution": {"commit": "", "pr": ""}`
  in `~/.claude/settings.json`, and repeat "no attribution trailer" in every
  agent brief (older work orders may still ask for one; override them).
- **Push, open PRs, merge, force-push: only on an explicit OK.** Local commits
  on the working branch are standing permission; anything outward-facing is
  not.
- **Rebases keep dates:** `git rebase --committer-date-is-author-date`; for
  hand-made commits in a rewrite set `GIT_COMMITTER_DATE` to the author date.
  Keep a local backup ref first. Force-push only with `--force-with-lease`
  and an OK.
- **Staging: explicit paths only.** Never `git add -A` / `git commit -a`.
  Never stage the user's own files (README edits in progress) or another
  agent's memory. The coordinator commits its own files with path-limited
  `git commit -- <paths>`, which cannot sweep a coder's index.
- **No `git stash`** (it collides with concurrent agents' trees).
- **Splitting a big diff after the fact:** back up final files, reset to
  HEAD, replay as ordered groups of exact old->new replacements, run a quick
  compile + test on each intermediate state, commit each, and assert at the
  end that the tree is byte-identical to the verified one.
- `gh pr edit` was broken here; PR body/title edits went through the REST API
  (`gh api -X PATCH repos/<o>/<r>/pulls/<n>`).

## 3. Machines: the local box edits, the sandbox runs

- **User rule: every simulation, proof, synthesis, harden and regression runs
  on the sandbox, coder self-checks included. The local machine only edits,
  commits and dispatches.** Reason: the local box has 15 GB RAM, `/tmp`
  (and so the session scratchpad) is tmpfs = RAM, and the desktop crashed
  once under three parallel STA runs.
- Do not park big downloads in the scratchpad (it is RAM). Extract what is
  needed onto disk and delete the rest.
- **Access pattern** (scripts listed in the README):
  - `rt` runs commands in a persistent tmux shell on the sandbox over ssh
    (cwd, env, virtualenvs persist; `rt --bg NAME cmd`, `rt --logs NAME`).
  - `rta` = `rt` pinned to this project's own tmux session and init script,
    so it never collides with another project's session on the same box.
  - `rmount` mounts the sandbox home over sshfs, so Read/Edit/Grep work on
    remote files natively.
  - `scripts/sync-to-sandbox.sh` rsyncs the tree (`--delete`, excludes
    `build/`, `localFiles/`, `.git/`, the confidential dir) and rewrites
    absolute paths in configs that cannot be shared verbatim. `--pull` brings
    results back into a separate local dir, never over sources.
- **The sandbox copy has no trustworthy `.git`** (sync excludes it): record
  the local HEAD hash in each run's STATUS file.
- **Keep drivers and scratch outside the synced tree** (here `~/regr/`), or
  the next `rsync --delete` wipes them.
- **Per-agent sandbox dirs:** each work order owns `~/regr/<campaign>/<WO-id>/`;
  acceptance runs on a frozen tree:
  `git archive <hash> | ssh <sandbox> "mkdir -p <dir>/acc-<hash> && tar -x -C <dir>/acc-<hash>"`.
- **Fresh-box gotchas worth writing down once:** toolchain versions (an old
  distro gcc could not parse the `-march` string), private package indexes
  (an offline wheelhouse fixed it), packages missing from requirements.txt.
- Check `df` before a run: the disk is shared.

## 4. Long jobs on the sandbox

- **Run detached, unattended:** `setsid nohup` driver that writes its session
  id to `driver.sid`. A `setsid` shell does not get the rt init, so the
  driver sets PATH / venv itself.
- **Thermal watchdog is mandatory for heavy runs.** (User rule: > 80 °C kills
  the whole run.) `thermal-watch.sh` samples every coretemp sensor every 2 s;
  over the limit, or 5 unreadable samples, it `pkill -KILL -s <sid>`, sweeps
  stray tool processes whose cwd is in the project tree, writes `TRIPPED`
  and exits. The kill never depends on Claude's session. `launch-multi.sh`
  starts driver + watchdog together; a new driver must write its sid the same
  way or the watchdog refuses to arm. To change the limit mid-run, start a
  new watchdog first, then kill the old one (no unprotected gap).
- **Resumable stages.** The box lost power six times in one day. Every stage
  writes `done.<stage>` when it finishes and is skipped on relaunch
  (`resumable-stages-example.sh`). After an unclean reboot, recently written
  files can be zeroed: checksum-rsync the tree before trusting it.
- **A local waiter wakes Claude**, not a polling agent: one
  `run_in_background` script (`wait-sandbox-example.sh`) that exits on
  TRIPPED / driver gone / DONE / sandbox unreachable x5 / reboot (compares
  `uptime -s` with its start value). Polling interval minutes, not seconds.
- **One heavy job at a time per agent**, under `timeout` + `ulimit -v`, and
  `nice -n 10` when another campaign holds the cores.
- **Expensive whole-system checks once, at the end.** (User rule.) Here: one
  harden + one full lockstep regression after the last queued work order is
  accepted, not after each one.

## 5. Agents: the tiered pipeline (user rule)

> "Opus should be for thinking alone, Sonnet for writing the code, Haiku for
> running tests and reporting." Applies to every specialist agent.

Why: usage limits ran out repeatedly while one Opus agent planned, coded and
waited on sims. The tiered pipeline closed 7 work orders plus a cleanup batch
in about a day, each change reviewed and accepted on a frozen tree.

The main session is the **coordinator**: it dispatches and keeps the ledger.
Subagents cannot spawn agents, so the coordinator launches every tier.

1. **Opus specialist = planner/reviewer.** (Project agents in `agents/`:
   verification engineer, design reviewer, area optimizer, PD expert.)
   Analyses, decides, writes work orders (section 6), reviews diffs. Short,
   time-boxed probes only; no long runs. Resume the same planner for its
   reviews (keeps context), via SendMessage.
2. **Sonnet coder** (general-purpose, model sonnet) implements ONE work order,
   self-checks on the sandbox (compile + its own test + proof that the test
   fails on the target fault), commits atomically.
3. **Haiku tester** (general-purpose, model haiku) runs the WO's acceptance
   commands on a frozen `git archive` tree and reports PASS/FAIL per
   expectation, quoting deviating lines verbatim. Because its tree is frozen,
   acceptance can overlap the next WO's coding.
4. **Opus review** for "review" tier WOs runs in parallel with acceptance:
   approve, or list exact edits (blocking / non-blocking).
5. **One committer at a time** (a concurrent `git commit` sweeps the other's
   staged files). Exception: file-disjoint coders using path-limited commits
   (`git commit -- <paths>`) may run in parallel.
6. Tiny review nits found before commit go to the next coder as their own
   commits.
7. **Bring the design reviewer in on every design change**, at each milestone
   (design doc before code, again after it lands), not once at the end. Ask
   for correctness and efficiency findings in separate sections. It stays
   read-only on the design.
8. **Housekeeping:** Haiku agents leave `tail -f` / `sleep 600` pollers
   behind; check and kill them by PID. TaskStop any agent that keeps "waiting
   on background work" after it reported.
9. **Ledger:** keep `AGENTS.md` (agent id, role, state, next) and
   `DECISIONS.md` (#, decision, reason, alternative, reversible?) up to date
   in `localFiles/<campaign>/`. Examples in `templates/`.

## 6. Work orders

File: `build/wo/WO-nn-<slug>.md`, copy in `localFiles/<campaign>/wo/`, plus
an `INDEX` with order and dependencies. Contents:

- goal + measurable target (mutant IDs, metric, verdict words);
- spec source (the document the expected behaviour comes from, never the
  author's own reasoning);
- **exact files the coder may touch**, file-disjoint between parallel WOs;
- the design, with expected values;
- sandbox acceptance commands with expected output;
- commit plan (one line per commit; "no attribution trailer, no push");
- tier: "routine" (coordinator accepts) or "review before accept";
- **budget** (tool calls) and a stop rule.

Every campaign starts from a **handoff file** (`templates/HANDOFF-example.md`):
goal table with owners, sandbox paths and tools, house rules, pipeline,
pointers. Every agent reads it first.

## 7. House rules pasted into every agent brief

- Never bare `make clean` if clean is `rm -rf build/` (it deleted every
  mutation score once). Use `make BUILD_DIR=build/<own> clean`; relative
  BUILD_DIR; name the build/ subdirs each agent owns.
- Explicit-path staging only; no `git add -A`/`-a`; never stage README or
  other agents' memory; no `git stash`; no attribution trailer; never push.
- No `pkill` / `killall`: kill exact PIDs. Tell agents which dirs a running
  suite owns so they never write there or kill its simulators.
- One sim/EDA job each, under `timeout` + `ulimit -v 4000000`; on the
  sandbox, not locally; own output dir.
- Leave no sleep/poll loops behind.
- Durable results copied to `localFiles/<campaign>/` (git-ignored, survives
  `make clean`).
- Do not edit design sources unless the WO says so.
- Never name, read for copying, or sync the confidential dir.
- Never write under the public submission repo's directory.

## 8. Lean agents, budgets, rate limits

- **No open-ended, token-heavy digs.** (User rule, after one planner grew to
  ~800k tokens chasing a tool failure.) Agent tokens are the expensive
  resource; unattended sandbox time is cheap.
- Prefer a **fresh agent from a compact handoff** (state, tested results,
  lean plan, rules) over resuming a bloated one. Write the handoff to
  `build/wo/` and back it up in `localFiles/`.
- Every agent gets a **hard budget** and a stop rule that ends in "report k
  of N done, with reasons", never "investigate until closed".
- Experiments only when the plan cannot be written without them, time-boxed.
- **Rate-limit resume:** the status line script persists the 5 h / 7 d reset
  times to `~/.claude/cache/rate_limits.json`. A one-shot cron at
  reset + 3 min resumes killed agents via SendMessage (resume, do not
  respawn) and re-arms itself while agents remain. Cron jobs are
  session-only.
- **Slow mode** when the window is nearly spent (user asked for it): at most
  one coder + one checker at a time, no new planners.

## 9. Reviews

- Adversarial reviews by a fresh Opus agent, read-only, spec-cited.
- Separate passes for compliance/correctness and for area/efficiency.
- A review's output is a document (section 1), with every finding marked
  PROVEN (reproduced) or REASONED.

## 10. Verification discipline: green is not proof

Every one of these reported PASS in this project while testing nothing:

1. **Empty outputs compare equal.** Two empty trace dumps diff clean. Always
   check line counts; make the bench `$fatal` when no program loaded.
2. **A comparator that silently drops tokens** (pairing tokens with `zip`
   lost the odd last one, so AMO store values were never compared).
3. **Stale binaries / caches keyed by test name.** Rebuild when sources
   change; any cache keyed by name is stale across runs.
4. **Stimulus that is not what the test is named for** (generator bugs).
   Gate on content: assemble programs and grep for the property the stream
   claims.
5. **Tests that exit "normally" after running 2% of themselves** (early trap
   routed to the pass exit). Compare retired count against program size;
   require the normal exit path.
6. **Audit scripts reading a log file that never exists.**
7. **Tests that run and still under-test** (injected cases that never
   execute, loops that never iterate). Measure the stimulus statically and
   dynamically; re-measure after every generator change.
8. **Directed suites that check final registers only, and skip files.** Full
   trace compare; a manifest that must list every test; fail on
   empty/abort/no-exit.
9. **Memory models returning X while not ready** (`if (X)` is false in
   iverilog, hiding bugs). Add zero/stale/random not-ready modes.
10. **Benches that print FAIL and exit 0.** The make target fails on any
    `^FAIL` / `^TIMEOUT` line.
11. **Vacuous formal proofs.** k-induction with undefined initial state
    "proves" anything at length > 1. Count only length-1 induction or a
    complete engine (pdr) from a reset-reached state. A yosys hierarchical
    reference into the DUT is an undriven free wire.
12. **Non-vacuity for everything:** every new property/test must FAIL on a
    committed mutant or broken copy, and every cover must be reached.
13. **Label known failures** with detection rules and report "N distinct
    causes", never raw fail counts. Unlabelled = real divergence.
14. **Mutation testing** as the measure of a bench: a fault catalogue, a
    runner, per-mutant verdicts; a lost kill is a regression.

Testbench intent comes from the spec, never from the RTL author's reasoning
(the verification agent's charter).

## 11. Autonomy when the user steps away

- Keep working; do not block on questions overnight.
- Choose by the project's north star (here: spec-legal, Linux-compatible,
  smallest area); have the reviewer check non-obvious choices.
- Log every non-obvious decision with reason and alternative in
  `DECISIONS.md`, and open the final report with that list, marking which
  are cheap to reverse.
- No push, merge or other outward-facing step the user did not ask for.
- Ask what an undefined word means next time (once "lodestone" was taken to
  mean the north star; confirm such guesses).

## 12. Confidentiality and the public submission repo

- **Confidential third-party code** (`<confidential-dir>`, under NDA): never
  `git add` it, never name it in commits or history, never sync it to the
  sandbox. Exclude it via `.git/info/exclude` (local, leaves no trace),
  not `.gitignore`. Code copied out must be from the permissively licensed
  upstream, not the NDA'd variant.
- **Public submission repo** (separate repo, from the shuttle's template):
  - no trace of Claude: no `CLAUDE.md`, `.claude/`, agent memory,
    claude.ai links, trailers, "Claude"/"Anthropic" text;
  - only the shuttle's own tooling in CI (no private flows);
  - **do not commit there at all**: leave changes uncommitted (backed up as a
    patch outside it) for the user to commit (user rule);
  - RTL = main's RTL + comment fixes that make it correct for that repo;
    logic changes come from main first;
  - commits there are by feature (~one per main PR topic), not main's
    per-change history; messages carry no main hashes or main-only tool names;
  - scrub scan before any commit, e.g.
    `grep -rnIiE 'claude|anthropic|<private-tool>|<confidential>|localfiles|co-authored|generated with|/home/|<sandbox-user>' --exclude-dir=.git .`;
  - keep the shell's cwd in the main repo; tell subagents not to write there.

## 13. State, memory, docs

- **Memory: one fact per file**, with `name` / `description` / `type`
  frontmatter and a one-line pointer in `MEMORY.md`. Feedback memories carry
  **Why** and **How to apply**. Dates absolute. Mark the current entry point
  `RESUME HERE`. Update instead of duplicating; delete wrong ones.
- **State doc at each milestone** (`localFiles/STATE-<date>.md`): main's
  state, decisions, next work, verify commands, gotchas, evidence paths.
- Valuable results never live only under `build/`.
- Agent memory (`.claude/agent-memory/<agent>/`) holds each specialist's
  recipes (proof methods, environment notes, coverage holes); it rescued the
  headline numbers once when `build/` was wiped.

## 14. Project-specific rules (keep if the new project is similar)

- **Target and deadline drive scope**: everything goes on one named shuttle;
  the "RTL freeze" means basic functionality working, not the deadline.
  Goal ladder: bare-metal -> FreeRTOS -> NOMMU Linux, in separate PRs.
- **Area first, speed second.** Report size as whole tiles + shape + routing
  density % + utilization % + headroom; harden only at sizes the shuttle
  sells (no custom die areas).
- **Main storage must be flip-flops**; latches only on ports/output gating; a
  silicon-proven hard macro is accepted.
- Simulator-only speedups are rejected; changes must help the real chip.
- `docs/CLAUDE.md` (copied in `project-claude-md/`) shows the per-repo
  instructions: build/test commands, atomic commit policy, invariants,
  Verilog-2001 conventions.
