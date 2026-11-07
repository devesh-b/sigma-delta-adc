# Working-principles export (AlphaOneSoC, 2026-11-07)

Read `PRINCIPLES.md` first: every rule for sandbox use, commits, agents,
verification, autonomy and confidentiality, with the reason for each.
Everything else here is a working file that the principles point to.

The confidential vendor directory's name is replaced with `<confidential-dir>`
in every copy.

## What is here

| Path | What | Adapt before use |
|---|---|---|
| `PRINCIPLES.md` | All rules, grouped by topic | Section 14 is project-specific |
| `agents/*.md` | The 4 Opus specialist agent definitions (verification engineer, design reviewer, area optimizer, PD expert) | Paths, PDK, tile budget, reference cores. Goes in `<repo>/.claude/agents/` |
| `project-claude-md/CLAUDE.md` | This repo's `docs/CLAUDE.md` (build commands, atomic commit policy, invariants, conventions) | Shows the shape only; rewrite for the new repo |
| `scripts/sync-to-sandbox.sh` | rsync tree to sandbox, rewrite absolute paths in configs, `--pull` results | Host, remote root, excludes |
| `scripts/thermal-watch.sh` | 80 °C watchdog: kills the driver's session, writes TRIPPED | `M=` dir, project path in the stray sweep |
| `scripts/launch-multi.sh` | Starts driver + watchdog, each in its own session | Driver name |
| `scripts/run-multi-example.sh` | A real multi-round regression driver (writes driver.sid, STATUS) | Example only |
| `scripts/resumable-stages-template.sh` | Generic skeleton: `done.<stage>` markers, STATUS, driver.sid | Stages, PATH |
| `scripts/wait-sandbox-example.sh` | Local `run_in_background` waiter: exits on TRIPPED / DONE / driver gone / reboot / unreachable | Paths, boot time |
| `templates/HANDOFF-example.md` | Campaign handoff every agent reads first (goal table, sandbox, house rules, pipeline) | Example |
| `templates/WO-INDEX-example.md` | Work-order index: order, files, tier, dependencies, decisions, questions | Example |
| `templates/WO-example-routine.md` | A routine work order (coordinator accepts) | Example |
| `templates/WO-example-review.md` | A review-tier work order (planner reviews before accept) | Example |
| `templates/FRESH-AGENT-HANDOFF-example.md` | Compact handoff used to restart a bloated agent fresh | Example |
| `templates/AGENTS-ledger-example.md` | Coordinator's ledger of agent ids, roles, states, next steps | Example |
| `templates/DECISIONS-example.md` | Decision log: decision, reason, alternative, reversible | Example |

## Home-directory files (`home/`, copied by the user)

| File in `home/` | Install to | What |
|---|---|---|
| `rt` | `~/bin/rt` | Persistent remote tmux shell over ssh (`rt cmd`, `rt --bg NAME cmd`, `rt --logs NAME`, `rt --doctor`) |
| `rta` | `~/bin/rta` | `rt` pinned to this project's tmux session + init script; copy and rename per project |
| `rmount` | `~/bin/rmount` | sshfs mount of the sandbox home at `~/sandbox` |
| `init-alpha.sh` | `~/.config/rt/init-<project>.sh` | Session init run inside the remote shell (cd, venv, toolchain PATH) |
| `env` | `~/.config/rt/env` | RT_HOST / RT_WORKDIR / RT_MOUNT defaults for interactive shells |
| `statusline.sh` | `~/.claude/statusline.sh` | Status line; also saves the rate-limit reset times to `~/.claude/cache/rate_limits.json` for the resume cron |
| `settings.json` | `~/.claude/settings.json` (merge, do not overwrite) | `attribution` blanked (no trailers), model/effort per model, status line, plugins; its `autoMode.environment` block describes THIS repo, so rewrite it |

## Still not copied

| File | What |
|---|---|
| `~/.claude/projects/-home-alfadelta10010-projects-AlphaOneSoC/memory/` | Raw memory files behind PRINCIPLES.md. Rule files: `commit-style-atomic`, `feedback-*`, `tiered-agent-pipeline`, `local-machine-heavy-jobs`, `sandbox-*`, `autonomous-decision-mode`, `doc-means-markdown`, `review-as-doc`, `use-design-reviewer-agent`, `verification-false-passes`, `regression-failure-labels`, `area-in-tiles`, `make-clean-wipes-build`, `rate-limit-watcher`, `submission-repo-rules`, `latch-rule-clarified`. Three name the confidential dir (`commit-style-atomic`, `sandbox-regression-server`, `submission-repo-rules`): scrub before moving |
| sandbox `~/regr/rfm/scripts/verify-pr2.sh` | The real resumable-stage driver the template is based on |

## Setting up the new system

1. Put the relevant parts of PRINCIPLES.md sections 1-13 into the new repo's
   `CLAUDE.md`, or into the new project's memory as feedback files.
2. Copy `agents/` into `<new repo>/.claude/agents/` and rewrite each agent's
   domain section.
3. Install `rt` / `rta` / `rmount`, write a new `init-<project>.sh`, and give
   the project its own tmux session name.
4. On the sandbox: `~/regr/` for drivers and scratch (outside the synced
   tree), the thermal watchdog, and an offline wheelhouse if packages are
   private.
5. Set `"attribution": {"commit": "", "pr": ""}` in `~/.claude/settings.json`.
6. Add the confidential dir to `.git/info/exclude` and to the sync excludes.
