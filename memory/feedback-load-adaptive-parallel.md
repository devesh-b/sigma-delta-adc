---
name: feedback-load-adaptive-parallel
description: Parallelise sandbox runs by current server load (scripts/lpool.sh), single-threaded ngspice; supersedes the fixed ≤5 process cap
metadata:
  type: feedback
---
Run sandbox jobs in parallel sized to the server's free capacity: slots = our running + (nproc − load1 − 0.5), clamped 1..nproc. Use `scripts/lpool.sh JOBFILE [LOGDIR]` (writes POOL_DONE, per-job EXIT=). Every job single-threaded (OMP_NUM_THREADS=1 and `.spiceinit` with `set num_threads=1`).

**Why:** user (2026-11-12) "parallelise based on load on server if possible", after asking to cut sim wall time (2026-11-11). ngspice's default spinit sets num_threads=8, which oversubscribed the 6-core box (load 16 with only 3 jobs).

**How to apply:** use it in every WO with more than ~3 sim jobs, and tell agents to use it. This replaces the fixed "≤5 own processes" from [[feedback-no-load-gate]]. Still nice, timeouts, markers, and no pgrep wait loops over ssh.
