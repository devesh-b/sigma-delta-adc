---
name: feedback-agent-resume-vs-new
description: New work orders get fresh agents; rate-limited or interrupted agents are resumed via SendMessage, not replaced
metadata:
  type: feedback
---
Start a **new** agent for every new work order. Never reuse an old agent for new work. When an agent stopped because of a rate limit, usage limit or session end mid-WO, **resume that same agent** with SendMessage so it continues from its saved state.

**Why:** user (2026-11-13): "i hope you create new agents instead of resuming old ones in case of new work orders, i want you to resume these rate-limited sessions though".

**How to apply:** After a limit reset or a new session, list the agents whose WO is unfinished and SendMessage each one to continue. For any new WO (including follow-ups like WO-NNb), spawn a fresh agent. Related: [[feedback-tiered-lean-agents]].
