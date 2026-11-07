---
name: feedback-tiered-lean-agents
description: User rule — Opus plans/reviews, Sonnet codes, Haiku runs tests; every agent gets a hard budget, no open-ended digs
metadata:
  type: feedback
---

"Opus should be for thinking alone, Sonnet for writing the code, Haiku for running tests and reporting." The main session coordinates and keeps the ledger (`work/<campaign>/AGENTS.md`, `DECISIONS.md`). Work orders and handoffs use the templates in `process/export-2026-11-07/templates/`. Every agent gets a hard budget and a stop rule ("report k of N done"). Never run an open-ended, token-heavy dig; prefer a fresh agent started from a compact handoff. Bring `sd-adc-design-reviewer` in on every design change, both before and after it lands.

**Why:** In AlphaOneSoC, usage limits ran out while one Opus agent planned, coded and waited on sims, and one planner grew to about 800k tokens. The tiered pipeline closed 7 work orders in about a day.
**How to apply:** Use this whenever work is split across agents. Paste the house rules from `WORKFLOW.md` §8 into every brief. See `WORKFLOW.md` §6–9 and [[feedback-sandbox-only]].
