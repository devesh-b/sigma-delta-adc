# tt — Sigma-delta ADC on Tiny Tapeout (sky130) — learning project

Goal: learn by designing a sigma-delta ADC for Tiny Tapeout on sky130A. **Not a competition, it's for learning.** Focus: sigma-delta ADCs with better specs than prior TT attempts (all of them are 1st order and none have an on-chip decimator).

Persistent memory for this project lives in `memory/` (index: `memory/MEMORY.md`). Read it at session start.

## Working rules (full text + reasons: `WORKFLOW.md`)
- **Run everything on the sandbox, nothing on the local system** (user rule): sims, model runs, sweeps, EDA, agent self-checks. Local = edit, read, dispatch. Sandbox = `ssh sandbox` (mempool@mempool.lan); push with `scripts/sync-to-sandbox.sh`, run with `~/bin/rta-tt <cmd>` (`--bg NAME`); EDA via IIC-OSIC-TOOLS: `~/bin/rta-tt 'scripts/iic "<cmd>"'` (TT-pinned sky130 PDK), tree at `/home/mempool/tt-sd` (`/home/mempool/tt` is AlphaOneSoC's, never touch), outputs to `/home/mempool/regr/tt`, `--pull` into `sandbox-out/`. Details `WORKFLOW.md` §4.
- "doc" = Markdown file, "report" = HTML page. No Claude Docs connector unless asked by name. Calm, factual framing; recommendations are options.
- Tiered agents: Opus plans/reviews, Sonnet codes, Haiku runs tests. Main session coordinates. `sd-adc-design-reviewer` on every design change.
- Lean agents: hard budget + stop rule, no open-ended digs; fresh agent from a handoff over a bloated one.
- Git (once a repo exists): atomic commits as you go, untested OK, explicit-path staging, no stash, **no attribution trailers**, push/PR only on OK.
- Green is not proof: every check must fail on a broken copy; analog false-pass list in `WORKFLOW.md` §11.
- Public TT submission repo: no Claude traces, don't commit there, scrub scan.
- Campaign state (ledger, decisions, work orders, STATE docs) goes in `work/<campaign>/`.

## Layout
- `CONTEXT.md` — **single-file snapshot of all context, decisions, learnings, corrections, model results, next steps. Read first in a new session.**
- `SPEC.md` — design spec, authoritative block targets + corner set (§6)
- `PUBLICATION_PLAN.md` — characterization paper plan
- `work/v1-design/RESUME.md` — **after an interruption, read this first: exact pickup steps.**
- `work/v1-design/PLAN.md` — **gated design plan (system → component → verification, all corners, Paul Thomas style). RESUME HERE.**
- `NOTES.md` — survey of prior TT shuttles, specs of key repos, applications, TT PCB / analog constraints. **Start here.**
- `ROADMAP.md` — draft tapeout direction: fs trade-offs, comparison with Paul Thomas, research angle, v1 spec, phases 0–5
- `ACHIEVABILITY.md` — evidence-based block-by-block gap analysis vs cloned repos, noise numbers from Paul's 1/f data, sim feasibility, silicon lessons, scorecard, work breakdown
- `model/` — Phase-1 Python behavioural model (`iadc.py`, `run_studies.py`, findings in `model/README.md`, reports in `model/out/`). Runs on the sandbox only (local `.venv/` kept for editing tools).
- `SIZING.md` — cap/noise/N/OTA/area sizing, speed trade-offs, ranked challenges, first-cut simplifications
- `MCP3421_TARGET.md` — case-study target specs (MCP3421) + TT feasibility; datasheet in `datasheets/`
- `.venv/` — python venv (pypdf installed)
- `WORKFLOW.md` — working rules (agents, work orders, sandbox runs, verification discipline, commits, submission repo)
- `process/export-2026-11-07/` — unchanged AlphaOneSoC working-principles export (source of `WORKFLOW.md`): templates (handoff, WO, ledger, decisions), sandbox scripts, `home/` bridge files (`rt`, `rta`, `rmount`). Archive; don't edit.
- `.claude/agents/` — `sd-adc-design-reviewer`, `rtl-verification-engineer`, `pd-expert`; their notes in `.claude/agent-memory/<agent>/`
- `scripts/sync-to-sandbox.sh` — push tree to the sandbox / pull results
- `scripts/iic` — run one command in the IIC-OSIC-TOOLS container on the sandbox (batch)
- `sandbox-out/` — results pulled from the sandbox (created on first pull)
- `work/` — per-campaign state (empty until a campaign starts)
- `data/` — TinyTapeout shuttle index JSONs (`idx_<shuttle>.json`, from https://index.tinytapeout.com/<id>.json), `root.json` (shuttle list), `hits.txt` (ADC keyword matches).
- `repos/sd-analog/` — true analog sigma-delta modulators on sky130 (main references)
- `repos/sd-digital/` — digital-only / external-RC sigma-delta designs, plus a noise-shaping DS DAC
- `repos/decimation/` — decimation / CIC filters
- `repos/adc-ref/` — mature analog sky130 ADCs (SAR, flash) as references for pads, comparator, and layout flow
- `repos/sd-ihp/` — sigma-delta designs on IHP SG13G2
- `pcb/` — TinyTapeout tt-demo-pcb, breakout-pcb, tt-micropython-firmware

All repos are shallow clones (`--depth 1`).
