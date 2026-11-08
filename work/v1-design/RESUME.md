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

## Update 2026-11-08 ~01:45
- Haiku testers stalled on the rta-tt lock and were stopped. The coordinator now runs rows directly with `ssh sandbox` and nohup.
  - The env must be sourced: `.venv-sbx` and `~/.nix-profile/bin` on PATH.
  - S4 row1 PASS (54 tests).
  - S4 row2 exit 1. Every gate ACCEPTs except CMRR sys-off: 44.0 dB vs 60 at 16 points. This is the known finding.
  - S4 row3 (`--nonvac`): log `acc06a-b990304/row3.log`.
  - WO-08 rows 2–8: runner `acc08-b990304/run_rows.sh`, logs `rowN.log`. `rows.done` appears when all are finished.
- Review done: `REVIEW-S4S5b-2026-11-08.md` (6137e42).
  - S5 can close with conditions. S4 can close once the CMRR term is corrected to ε_eff (ΔCp,top). Expect about 65 dB.
  - The earlier 132–152 dB SPICE CMRR was overstated. The deck had Cp,top = 0 and the metric was wrong.
  - Symmetric slew is costly: precision mode about 145–170 µA. Boost ×2 on both OTAs gives 260–320 µA, which breaks 200 µA.
- **New user questions (asked 2026-11-08):** slew spec; the 200 µA cap (hard?) and fast-mode option; reset CM / input pair.
- Follow-ups to write as WOs:
  - C-M1: OTA1-only vs OTA2-only SR/GBW sweep, about 40 runs.
  - m1: CMRR metric fix.
  - m3: xcheck A0-80 row at Roff 1e14.
  - m9: knees exit code.
  - S4 ε_eff term.

## Update 2026-11-08 ~01:40
- Acceptance done (667605b): WO-08 8/8. WO-06a only REJECTs on CMRR sys-off, which D33 covers.
- D33 (ε_eff CMRR term) and D34 (no freeze of the SR/CM/CMRR rows before WO-09) are in DECISIONS.
- Dispatched (Sonnet, background):
  - WO-09: S5c tier-1 follow-ups, outputs in /home/mempool/regr/tt/WO-09.
  - WO-10: S4 ε_eff, outputs in /home/mempool/regr/tt/WO-10.
- If they died: check `git log` for their commits and the sandbox output directories, then re-dispatch from the WO file.
- After both: Haiku acceptance (direct ssh, not rta-tt), then a reviewer pass. S4 then closes; S5 closes with D34. Then S6.

## Update 2026-11-08 ~01:50: SANDBOX DOWN
- mempool.lan does not answer ping or ssh, so nothing can run. Never run locally.
- **WO-10:** code committed as d54d8f3 (WIP, unrun). Once the sandbox is back:
  1. sync;
  2. `pytest model/tests`;
  3. full s4_corners run to /home/mempool/regr/tt/WO-10/s4;
  4. `--nonvac`;
  5. results md/json, then commit.
- **WO-10 finding (my D33 error):**
  - D33's linear worst-case sum gives 5e-4 + 3e-4 + 2.8e-4 = 1.08e-3, i.e. 59.3 dB. That REJECTs 60 dB.
  - The review's ≈ 65 dB was an RSS that dropped one term.
  - The terms are independent, so the statistically correct form is RSS(ΔCp/Cs, (Cp/Cs)·ε_Cs) + |inj|: 5.8e-4 + 2.8e-4 = 8.6e-4, i.e. 61.3 dB.
  - Signed sum per MC draw once WO-09 gives the signs.
  - Decide after WO-09's sign result. Options: tighter ΔCp allocation (≤ 0.15 fF), larger Cs, or RSS amendment to D33.
- **WO-09:** running at dispatch time. It will hit the same outage, so check what it committed.

## Update 2026-11-08 ~02:15
- Sandbox still down.
- WO-09 code committed (0903e8d, fd145ac), unrun. WO-10 code d54d8f3, unrun. D35 records the provisional calls (ε_eff sign, rsrc2 gate, per-side leakage, the S4 combination method).
- **When the sandbox is back:**
  1. sync;
  2. `pytest design/tests model/tests`;
  3. WO-09 modes via nohup (`--knees3` first, ~26 min, then `--cm2 --drift --rsrc2 --xcheck --nonvac3`; out /home/mempool/regr/tt/WO-09);
  4. the WO-10 full s4 run plus `--nonvac`;
  5. fix any breakage;
  6. write s5c_tier1 and s4_corners results;
  7. Haiku acceptance (direct ssh);
  8. reviewer pass.
- It is fine to resume the same coder agents or dispatch fresh ones from the WO files.

## Update 2026-11-08 17:22: sandbox back (rebooted about 17:06)
- The sandbox has 6 cores and 15 GB. Keep about 5 processes total. Disk / is 95 % full (50 GB free).
- pytest design+model: 90 passed with the full env (PATH nix, PDK_ROOT /home/mempool/.ciel).
- Runner: `/home/mempool/regr/tt/run_wo0910.sh` (nohup).
  - Queue A, WO-09 modes: knees3 cm2 drift rsrc2 xcheck nonvac3. Logs `/home/mempool/regr/tt/WO-09/<mode>.log`.
  - Queue B, WO-10: s4 (`--procs 2`), then nonvac. Logs `WO-10/s4.log`, `WO-10/nonvac.log`.
  - `ALLDONE` markers appear in each directory when its queue finishes.
- Next: read the logs, write results md/json (s5c_tier1, s4_corners), fix any breakage, settle D35(d), then acceptance and reviewer.

## Update 2026-11-08 ~17:50
- **WO-09 runs all ACCEPT** (logs in /home/mempool/regr/tt/WO-09).
  - **Knees, OTA1 the limiter:**
    - 2 MHz: knee 8.9 V/µs, so 12 V/µs has 35 % margin.
    - 4 MHz boost: knee 10.9, 10 % margin.
    - Boosting OTA1 alone floors at about 12 ppm (> 5 at N 1024).
  - **ε_eff sign "−" confirmed** (D36).
  - **Drift:** 344 mV at 0.25 MHz/N 4096, 100 pA per side (FLAG, needs a user/C-stage decision).
- WO-10 S4 committed eb0b52a (59.3 dB REJECT on the linear sum).
- WO-11 dispatched: S5c write-up + S4 RSS per D36. After it: Haiku acceptance for WO-09/10/11, then the reviewer.
- **User decisions pending:**
  1. SR: 12 V/µs symmetric now has 35 % margin at 2 MHz. Fast mode needs about 13.6 V/µs base for 25 % margin.
  2. The 200 µA cap; OTA1-only boost is not enough.
  3. The 0.25 MHz/N 4096 leakage drift.

## Update 2026-11-08 18:10
- WO-11 done: 6076f49 (s5c results), d3ab346 (S4 D36: ACCEPT, sys-off 61.5 dB; nonvac 8/8 REJECT).
- Watch item: WO-11 weakened one test assertion. At the ΔCp 0.05 fF case sys-on came out at 99.4 dB, which should not depend on ε. The reviewer is asked to explain it.
- Acceptance launched on the frozen copy `/home/mempool/regr/tt/acc0911-d3ab346`: `acc.sh`, writes `ALLDONE`. Logs: pytest, the 6 tier1 modes, s4, s4nv.
- Reviewer dispatched, writing `REVIEW-S5c-S4close-2026-11-08.md`.
- Next:
  1. Fill `results/ACCEPT-WO09-11-d3ab346.md` from the logs.
  2. Commit the review.
  3. Apply the SPEC §3.0 rows that don't wait on user decisions.
  4. Report the user decisions (SR, the 200 µA cap / fast mode, drift).

## Update 2026-11-08 ~18:30
- Review saved (3e2b326). S4 and S5 closable with conditions. The weakened test is a metric floor, not physics (R4).
- D37 recorded.
- WO-12 dispatched (S5d gaps R1 R2 R4 R6 R7 R9). It waits for acc0911 `ALLDONE` before running sims.
- **User decisions pending (as presented):**
  1. Fast mode, option (a)–(d). (a) = OTA1-only boost + OTA2 GBW 20 MHz at base bias, ≈ 180 µA; WO-12 R2 tests it.
  2. Is 0.25 MHz/N 4096 needed at 125 °C?
  3. Accept the review's SR rows (OTA1 12.5, OTA2 13.5 V/µs; base ≈ 118 µA).
- Acceptance acc0911 is still running. Fill `results/ACCEPT-WO09-11-d3ab346.md` when it is done.

## Update 2026-11-08 ~18:45
- Acceptance WO-09..11: 9/9 (64053c4).
- WO-12 coder stopped (budget). Commits: 61022f0, c33c0de, 0633796 (tier1 WIP).
- WO-12 runs in progress: `/home/mempool/regr/tt/WO-12/run.sh`, `ALLDONE` marker.
  - cm2, drift, nonvac4 and probe are done and OK.
  - xcheck, knees4, s4 and s4nv are still pending.
- **To finish:**
  1. Read the logs.
  2. Write `results/s5d_tier1.{md,json}`, and refresh `s4_corners.{md,json}` from `WO-12/out_s4`.
  3. Commit.
  4. Reviewer pass.
- Open finding for the reviewer: the R4 explanation (A(v) floor) is not supported. Ideal-A error is not ≈ 0. Suspect `_corr` uses x2_final only.
- R9: the xcheck decks have Cp,vg = 0, so the suspect is the Ck loading on the stage-2 node. The model has (1+c2) where the deck has 1+c2(1+k).

## Update 2026-11-08 ~19:00
- WO-12 results are written (8abe28b, `results/s5d_tier1.md`). All runs completed.
  - R2: option (a) fails (21–56 ppm at N1024).
  - R9: solved by adding Ck loading on the stage-2 node; the iadc default needs the change, then rerun S3/S4.
  - R4: cause still unknown (`_corr`?).
- Reviewer dispatched for WO-12. The review comes back in its final message; save it as `REVIEW-S5d-2026-11-08.md`.
- **User decisions asked** (fast-mode options table in chat; recommended: boost both, allow ≈ 210 µA in fast mode only):
  1. fast mode;
  2. SR 12.5 / 13.5;
  3. 0.25 MHz/N 4096 at 125 °C.
- Next after the review: WO-13, covering the iadc Ck default, the `_corr` fix if needed, and the S3/S4 rerun. Then apply the SPEC §3.0 rows (after the user's decisions), then S6.

## Update 2026-11-08 ~19:50
- REVIEW-S5d saved, D38 recorded (583f955).
  - S4 sys-on floor = residue-frame bug, C1 (fix in WO-13).
  - Ck becomes the topology default.
  - 240 SPS = N1024.
  - Goldens are ideal-A.
  - **Corrected my earlier user numbers** (INL ≈ 7 ppm was wrong; boost-both is 2.2/4.2 ppm).
- WO-13 dispatched (caac987): model fixes, S3/S4 reruns, xcheck 5 % gate, fast-mode runs (OTA2 boost ×1.5; 3 MHz no boost). Outputs in /home/mempool/regr/tt/WO-13.
- After WO-13: acceptance (direct ssh, frozen copy), then reviewer. Then the user's fast-mode decision with real numbers, then the SPEC §3.0 rows, then S6.

## Update 2026-11-08 20:05: 1PASSWORD LOCKED
- WO-13 commit 1 landed (85e9e24, C1 fix).
- Commit 2 (Ck topology) is STAGED but failed on signing. Its message is in the conversation: "model: stage-2 Ck loading from topology c2(1+k) default, cp_hold g-only term; re-baseline regressions" + the old→new table.
- Uncommitted working-tree edits: s4_corners.py, gen_tier1.py, tier1_tb.py.
- Coder stopped. The coordinator launched `/home/mempool/regr/tt/WO-13/rerun.sh`:
  1. pytest;
  2. s4 + nonvac;
  3. s3;
  4. waits for fast2, then xcheck + nonvac5;
  5. touches `ALLDONE`.
- Next:
  1. Ask the user to unlock 1Password.
  2. Commit 2, then commit the rest per the WO-13 commit list.
  3. Write `results/{s3_budget,s4_corners,s5e_tier1}`.
  4. Acceptance, then reviewer.

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

## Update 2026-11-08 22:55: WO-13 committed
- Signing unlocked. Commits: a3ea4eb (Ck default, cp_hold), a8449b4 (S3/S4 reruns + results), 22dab89 (tier-1 xcheck/nonvac5/fast2 + s5e results).
- Acceptance of WO-13 **deferred**: sandbox saturated by another project's jobs (load 6+ on 6 cores, not ours). Launch when load < 3: frozen copy `/home/mempool/regr/tt/acc13-22dab89`, rows = WO-13 `rerun.sh` set (pytest, s4, s4 --nonvac, s3, xcheck, nonvac5). Write `results/ACCEPT-WO13-22dab89.md`.
- Reviewer dispatched (background): writes `REVIEW-S5e-2026-11-08.md` (C1 fix, Ck, 3 MHz suspect, GBW2 feasibility, S6/S7 blockers).
- Decision summary sent to the user (fast mode / SR rows / 0.25 MHz at 125 °C). Waiting on their answer before SPEC §3.0 rows, S6, S7.

## Update 2026-11-08 23:10: user decisions in (D39)
- User: SR 12.5/13.5 V/µs; fast mode option A; 0.25 MHz N 4096 capped at 100 °C (85 °C if the model doesn't support 100).
- REVIEW-S5e saved (b02e092): model fixes correct; C-M1 = boost gm grows slower than current, so option A needs absolute boosted-GBW rows (OTA1 ≥ 20, OTA2 ≥ 22.5 MHz); 3 MHz explained (OTA1 slew), dropped.
- Leakage check (results/leak_temp.md): sky130 junction leakage 125→100 °C ÷9.4, so 100 °C cap holds (drift 37/86 mV).
- SPEC §3.0 + §6 rows applied, D39 recorded (d3634f0). Leakage rows: ≤ 90 pA ff/125, ≤ 20 pA ff/100.
- WO-14 dispatched (Sonnet, background; 2b5a53d): gm/Id table, V5 rerun with real gm boost, V4 10.8 V/µs point, S3 A/B, order-1 test, fast_task constants, s5e relabel. Waits for sandbox load < 4.
- WO-13 acceptance still deferred (sandbox load ~6.5 from another project). Run with WO-14 acceptance on one frozen copy.
- Next: WO-14 result → acceptance (frozen copy) → reviewer → S6 golden vectors (ideal-A; decimator output = bitstream-only u_hat with sys sign, not u_corr; close F7/F8) → S7 SPEC freeze (user OK).

## Update 2026-11-08 23:20
- D40 (user): 1.8 V input devices + SC CMFB. SPEC rows added; WO-14 coder told to use pfet_01v8/nfet_01v8 for the gm/Id table.

## Update 2026-11-08 23:45: WO-14 coded, runs gated on sandbox load
- WO-14 coder (2966c92, e95b887, 6fb0a6f, 0493917): items 1–7 coded; only item 7 (s5e relabel) is complete; nothing run (load 5.9–6.7 for 30 min, another project). Coordinator fixed the s5e option-(a) wording.
- **Runner launched (nohup):** frozen copy `/home/mempool/regr/tt/acc14-cb14f34/acc.sh`. It waits for 1-min load < 4 before each step (max 12 h, then `LOAD TIMEOUT` in STATUS). Steps:
  - pytest;
  - queue A: 9 gm/Id decks, `--gmid`, `--fast3`, `--xcheck`, `--nonvac5`;
  - queue B: s4, s4 `--nonvac`, s3, then the S3 A/B (iadc from a3ea4eb^ and a3ea4eb in `ab/pre`, `ab/post`).
  - Progress in `STATUS`, logs `<step>.log`, and `ALLDONE` when finished.
- When ALLDONE:
  1. read the logs;
  2. write `results/ACCEPT-WO13-14-cb14f34.md`, `gmid_table.{md,json}` (from out_gmid), `s5f_tier1.md` (fast3: V5 with real gm boost, V4m 10.8 V/µs point) and `s3_ab.md`;
  3. reviewer pass;
  4. then S6.
- Known risks (coder): nfet deck sign/column, numerical gm at low current, `gm_ratio` helper. Fix any breakage before trusting the numbers.

## Update 2026-11-09 01:55
- Acceptance done: `results/ACCEPT-WO13-14-cb14f34.md` (1633ab5). All green.
- Two gm/Id bugs fixed: ngspice `{$t}` (925b983), singlescale columns (05cbab2).
- gm/Id table committed. Worst-case pfet_01v8 gm ratio: OTA2 ×1.5 at gm/Id 14 = 1.283, ×2 = 1.513; OTA1 ×2 at 10 = 1.423 (ff/−40).
- S3 A/B: Ck moves S3 ≤ 0.6 %.
- **Running:** `--fast3` in `/home/mempool/regr/tt/acc14c-05cbab2` (nohup `f3.sh`, `fast3.log`, ALLDONE marker).
- When it's done:
  1. write `results/s5f_tier1.md` (V5 with the real gm ratios, the OTA2 ×2 row, non-vacuity rows, V4m);
  2. reviewer pass on WO-14;
  3. if option A fails N 1024 ≤ 5 ppm: present the fix options to the user (OTA2 ×2 boost using the SC-CMFB headroom, or a larger OTA2 base GBW). Do not decide.
