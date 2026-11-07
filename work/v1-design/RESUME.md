# RESUME: where to pick up (updated 2026-11-08)

Read this, then `CONTEXT.md`, then `work/v1-design/AGENTS.md` (ledger).

## State at last update
- HEAD b990304. S5b (WO-08) committed as c686d16. S4 re-gate (WO-06a) committed as e2915a0.
- Running when this was written (background agents; may have died with the session):
  1. Haiku acceptance WO-06a: frozen copy `/home/mempool/regr/tt/acc06a-b990304`. Writes `results/ACCEPT-WO06a-b990304.md`.
  2. Haiku acceptance WO-08: frozen copy `/home/mempool/regr/tt/acc08-b990304`. Writes `results/ACCEPT-WO08-b990304.md`.
  3. Opus review S4+S5b: writes `work/v1-design/REVIEW-S4S5b-2026-11-08.md`.
- Pending user decision: **slew-rate spec**.
  - (a) ≥ 15 V/µs both directions, about +11 µA. Boost mode would be about 220 µA, over the 200 µA cap.
  - (b) Keep 12 V/µs (thin margin).
  - (c) Boost more than 2×.
  - The user said they will answer soon. Don't decide it for them.

## Resume procedure
1. `git log --oneline -5`; `git status --short`.
2. For each of the three outputs above, check whether its file exists.
   - **Missing:** check the sandbox logs (`ssh sandbox ls /home/mempool/regr/tt/acc06a-b990304 /home/mempool/regr/tt/acc08-b990304`).
   - **Logs complete:** fill the ACCEPT file from them.
   - **Run died:** re-dispatch the same agent with the same prompt shape (see the ledger rows), using a fresh frozen copy name.
3. Once all three exist: commit them (explicit paths), and update the ledger.
4. Apply the review's SPEC §3.0 rows. Leave out the SR row until the user decides; that row is the only part waiting on the user.
   - PMOS input CM range
   - static A(v) table
   - OTA2 offset ×1.5
   - CMRR evidence + C4 caveat
   - reconciliation of the S4 CMRR sys-off gate
5. Report to the user in plain language: the gate verdicts for S4 and S5, plus anything still open.
6. Next stages: S6 (golden vectors for the C9 decimator), then S7 (SPEC v1 freeze plus reviewer pass), then ask the user for OK on the S → C gate.

## Standing rules (short)
- Sandbox only.
- Never touch `/home/mempool/tt`.
- No push, no attribution trailers.
- Explicit-path commits.
- If 1Password fails, ask the user to unlock.
- Nothing outward-facing without asking.
