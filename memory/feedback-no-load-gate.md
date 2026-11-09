---
name: feedback-no-load-gate
description: "User dropped the sandbox \"start only below load 4\" gate (2026-11-09); still cap own processes at ~5, nice + timeout"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 79c37851-a8cf-40b2-9827-19c369783496
  modified: 2026-11-09T10:27:13.715Z
---

Don't wait for sandbox load to drop before running tt-sd jobs; run them (user, 2026-11-09: "don't wait for the load to reduce, run the tasks").

**Why:** load on the shared sandbox is mostly AlphaOneSoC jobs at 7–20 for hours; waiting stalled WO-16 for most of a day.

**How to apply:** launch immediately; still keep at most ~5 of our own processes, nice -n 10, timeout, never touch others' processes or /home/mempool/tt. Work orders should say "no load gate" instead of "start below 4". Related: [[feedback-sandbox-only]].
