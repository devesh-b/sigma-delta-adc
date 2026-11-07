---
name: feedback-communication
description: User rules on wording — "doc" = Markdown file, "report" = HTML page, no Docs connector unless named; calm factual framing; user's units
metadata:
  type: feedback
---

- "doc" means a Markdown file and "report" means an HTML report page. Don't use the Claude Docs connector unless the user asks for it by name.
- Use calm framing. State risks and gaps as facts and rate severity by technical impact. Ask what a milestone word means before assuming. Recommendations stay options; the user owns the plan.
- Report in the user's units: whole TT tiles, ENOB, µV rms, ppm INL, SPS, µW.
- A multi-agent review stays silent until it is done, then delivers one document (verdict, scorecard, ranked findings marked PROVEN or REASONED, gaps, what held up, evidence).

**Why:** These are user rules carried over from the AlphaOneSoC export (`process/export-2026-11-07/PRINCIPLES.md` §1). Other agents and tools cannot read Docs-connector docs.
**How to apply:** Applies to every response and deliverable in tt. See `WORKFLOW.md` §1.
