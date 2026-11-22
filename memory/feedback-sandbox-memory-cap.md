---
name: feedback-sandbox-memory-cap
description: "Limit sandbox runs by memory, not just CPU; full-top ngspice uses ~4 GB each, 16 GB box hangs/reboots"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 79c37851-a8cf-40b2-9827-19c369783496
  modified: 2026-11-22T05:26:16.074Z
---

User (2026-11-22): "limit how many runs you start on the sandbox, you're causing it to hang".

Sandbox has 6 cores and 16 GB RAM. Full-top gate ngspice runs (WO-105b) take 3–4.4 GB each and grow with sim time. With four at once, 14.4 GB was used and the box was swapping. That probably caused the 2026-11-21 20:05 and 2026-11-22 ~10:10 reboots. lpool (GMAX 5, CPU-load slots) never checks memory.

**Why:** a hang kills every pool and loses hours of runs, and the user has to recover the box.

**How to apply:**
- Before launching, check `free -m` and the RSS of running ngspice processes. Keep at least 4 GB available.
- Run full-top/gate sims at most 2 at a time. Small block benches may run more, but never so the total exceeds about 10 GB.
- Never relaunch several pools at once after a reboot. Start one, watch memory, then add the next.
- Prefer MAXJOBS=1 or 2 on heavy pools. Agents launching pools must be told this cap.

Related: [[feedback-load-adaptive-parallel]], [[feedback-no-load-gate]].
