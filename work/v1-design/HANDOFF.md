# v1-design handoff: every agent reads this first

**Project.** A precision incremental ΣΔ ADC on Tiny Tapeout sky130A. It is a learning project.
- The spec is `SPEC.md`, which is authoritative.
- The plan is `work/v1-design/PLAN.md`: gated stages S → C → V. A gate passes only if every check passes at every corner.
- Decisions are in `work/v1-design/DECISIONS.md`.
- Working rules are in `WORKFLOW.md`. §4 covers the sandbox, §8 the house rules, §11 the rule that green is not proof.

**Machines**
- Local Mac: edit, read and dispatch only. **Nothing runs locally**: no python, no ngspice.
- Sandbox: `ssh sandbox`.
  - Push the tree with `scripts/sync-to-sandbox.sh`. It lands in `/home/mempool/tt-sd`.
  - Run with `~/bin/rta-tt '<cmd>'` (`--bg NAME` for long jobs, `--logs NAME` to read them).
  - The EDA image is `~/bin/rta-tt 'scripts/iic "<cmd>"'`. Inside it, `tt-sd` is at `/foss/designs/tt-sd` and outputs go to `/foss/designs/regr`, which is `/home/mempool/regr/tt`.
  - Python on the box: `.venv-sbx` (activated by rta-tt init).
- **`/home/mempool/tt` belongs to AlphaOneSoC. Never read-write it, sync to it or delete in it.**
  - Your outputs go to `/home/mempool/regr/tt/<WO-id>/`.
  - Run heavy work with `nice -n 10` and `timeout`.
  - Never kill a PID you did not start.
- Bring results back with `scripts/sync-to-sandbox.sh --pull` into `sandbox-out/`. Copy durable numbers plus the exact command into `work/v1-design/results/`.

**Git.** The local repo is `~/projects/tt`.
- Commit atomically with explicit-path staging: `git add <paths>`, never `-A` or `-a`.
- No stash, **no attribution trailer, no push**.
- Commit only the files your WO lists.

**Verification discipline**
- Every check prints `ACCEPT` or `REJECT` and exits nonzero on REJECT.
- Every check must REJECT on a deliberately broken copy. Show that in your report.
- Expected values come from SPEC.md or theory, never from the code under test.
- Fail on any missing or NaN measurement.

**Report format** (last message): WO id; done k of N items; commits (hashes); each acceptance row with PASS/FAIL and the evidence path; open issues; anything you could not do and why.
