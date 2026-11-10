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

## Update 2026-11-09 02:05
- fast3 done (`results/s5f_tier1.md`, 8ade439).
  - Option A built from the minimum bases (OTA1 10, OTA2 15 MHz) fails N 1024: 7.6–12.5 ppm against 5.
  - The SPEC-meeting point (boosted GBW 20 / 22.5 MHz) gives 3.7 ppm, so the D39 rows hold, but the bases must rise (≈ 14 / 17.5 MHz).
  - V4m passes (0.579 ppm), so the OTA2 25 % SR margin is shown.
- Reviewer dispatched (background) on WO-14/S5f. It returns text; save it as `REVIEW-S5f-2026-11-09.md`.
- Then: tell the user whether fast mode fits 200 µA with the reviewer's sizing. If it doesn't, give them options; do not decide. Then S6.

## Update 2026-11-09 02:30
- REVIEW-S5f saved (85ddf24).
  - Gate the *boosted operating point* at every corner, not base × ratio.
  - Fast mode fits 200 µA: A ≈ 159 µA, A′ (OTA2 ×2) ≈ 172 µA.
  - INL rises with OTA2 GBW at fixed SR (M2), so the cold corner (≈ 30/34 MHz) is untested.
  - The SPEC has no β2/Cp_vg2 row (M3).
- SPEC fast-mode text refreshed (db2333d).
- WO-15 dispatched (Sonnet, background; f4e7945): cold-corner boosted points, trend discrimination, fp2 sensitivity, gm/Id tooling.
- **Asked the user:**
  1. fast-mode option A / A′ / relaxed N 1024 target;
  2. bias generator constant-gm or constant-current.
- Coordinator defaults, reversible: fold/cascode current switches with the tail in boost (keeps PM); OTA2 L < 1 µm allowed only if A0 ≥ 80 dB holds.
- Next: WO-15 result, acceptance, review; the user's answers go into SPEC (D41); add the β2 row (M3); then S6.

## Update 2026-11-09 03:00
- D42 recorded (bandgap current ref + 3-bit trim), SPEC C6 rows (b8f89e2). DESIGN_GUIDE.md added (global rationale doc; keep it updated at each decision).
- WO-15 still running in background.

## Update 2026-11-09 ~04:10: WO-15 done, UNCOMMITTED (1Password LOCKED)
- The WO-15 coder finished 4/4 items. Its 3 commits failed: "1Password: failed to fill whole buffer". Commit 1 files are staged (decks, gmid_table); the rest is in the working tree (tier1_tb.py, gen_tier1.py, test_tier1.py, results/s5g_tier1.md).
- Planned commits:
  1. `design: gm/Id decks (L 0.35/0.5, op-gm, W-bin) and boosted-point W/L table`
  2. `design: fast4 mode (boosted operating points, trend discrimination, fp2 sensitivity), gm/Id checks + tests`
  3. `v1-design: S5g results`
- Results:
  - all A′ boosted points pass (hot 1.08 ppm, cold 0.88 ppm at N 1024);
  - **solver options matter**: default reltol 1e-3 shifts INL by up to ~12 ppm;
  - fp2 must track the boosted gm (177 ppm if held at base);
  - fp2×30 gives 101–113 ppm (suspect).
- Reviewer dispatched on S5g (returns text, save as REVIEW-S5g-2026-11-09.md). Key question: which earlier tier-1 verdicts used default options, and what convergence rule to adopt.
- Next:
  1. Ask the user to unlock 1Password, then make the commits.
  2. Coordinator acceptance on a frozen copy.
  3. Act on the review: convergence-rule reruns, then S6.

## Update 2026-11-09 ~04:40 (still LOCKED)
- REVIEW-S5g saved (working tree).
  - A′ closes the cold-corner question.
  - fp2×30 is physics, not a bug: the deck needs PM ≈ 75° on OTA1, so SPEC "PM ≥ 60°" was too loose.
  - The min-W/L table is 2× too big (G-M2).
  - Solver convergence is not shown (G-M3).
- D43 (coordinator, reversible): step-settling gate per OTA; one switched bias leg feeding all mirrors; convergence rule O0–O2; 2 MHz N256 not gated. SPEC rows edited (working tree).
- WO-16 written (`wo/WO-16-S5h-convergence.md`). **Dispatch only after the WO-15 commits land**, because it touches the same files.
- **Commit order once unlocked:**
  1. WO-15 c1/c2/c3 (see the update above; the c1 files are staged);
  2. `v1-design: REVIEW-S5g, D43, WO-16` (REVIEW-S5g, DECISIONS, SPEC, wo/WO-16, wo/INDEX);
  3. RESUME.
- Then dispatch WO-16, run acceptance on a frozen copy, then S6.

## Update 2026-11-09 (unlocked)
- Committed: eee7b7a, fdc4f56, b4f93e6 (WO-15 c1–c3) and 0c719d5 (REVIEW-S5g, D43, WO-16).
- WO-16 dispatched (Sonnet, background).
  - Sandbox load was ~10 at dispatch, from AlphaOneSoC jobs (not ours; don't touch them).
  - The agent edits code locally, and runs only when the load is below 4.
  - If the load stays high, it commits the untested code and stops with a report.
- Next: WO-16 result, then acceptance on a frozen copy, then the reviewer, then S6.

## Update 2026-11-09 ~10:00 (WO-16 partial, load-blocked)
- The sandbox load stayed at about 8–10 from AlphaOneSoC jobs, against the gate of below 4.
- WO-16 committed b9e924c, untested:
  - G-M2 `per_device_current()` + hand-value test;
  - `P.option_ladder` O0–O2, `--opt` / `--method` / `--reltol-only` / `--tmax-only`;
  - `TB.converge_verdict` + test.
- `test_gmid_min_wl_per_device_hand_values` FAILS until `gmid_table` is regenerated (the JSON still holds I_tail values).
- Items 3 and 4 (reruns, fp2 window) not started.
- The agent left local wait loops behind, one of them a broken `until` that spammed ssh. Coordinator killed them. Lesson for WOs: no shell-side wait loops; check once, then stop.
- **Resume when load < 4**, in this order:
  1. sync;
  2. pytest;
  3. `tier1_tb.py --gmid --src <gmid CSV dir>`, then pytest again;
  4. smoke-test 1 job per new mode;
  5. dispatch a fresh agent for items 3–4 (WO-16 rerun set).
- Note: the tau floor makes tmax about 1–2 ns, so O1/O2 runs will be slower.

## Update 2026-11-09 13:15 (user override of load gate: pytest + table)
- pytest design/tests: 49 pass, 1 fail (the G-M2 hand test, failing on the old table as intended). After regenerating, 50 pass.
- gmid_table regenerated from `regr/tt/WO-15/gmid`. W/L at L 1 µm: OTA1 28.2, OTA2 ×2 17.5, OTA2 ×1.5 118.7. WO-16 item 1 done.
- Remaining WO-16 items: smoke-test the new modes, then items 3–4 (reruns, fp2 window). Waiting for load < 4 unless the user says otherwise.

## Update 2026-11-09 ~13:45 (smoke tests, run at load ~6.6 on user override)
- Smoke results, `--null` N256 m2 unless noted (outputs in `regr/tt/WO-16-smoke`):
  - O0 ACCEPT (4.642e-07).
  - `--tmax-only O2` ACCEPT, same error, so tmax is converged.
  - O1, O2, `gear+O1` and `--reltol-only O1` REJECT: timestep too small, singular matrix at bkp/bkn.
  - Split: reltol 1e-4 alone and chgtol 1e-16 alone each pass; the combination fails. chgtol 1e-15 + reltol 1e-4 passes.
  - The null ideal deck at reltol 1e-5 fails with trtol 1 or chgtol 1e-15. It passes only at chgtol 1e-14 + trtol 7.
  - trap on the null deck: 6.7e-05, REJECT. This is why the base method is gear.
  - Spec `--dc` deck m3 with the floor: INL 0.176 / 0.175 / 0.175 ppm at O0/O1/O2, all ACCEPT. The ladder works on the real deck.
- Fix:
  - `CHGTOL_FLOOR` 1e-15, chgtol ÷10 per step (commit after RESUME 1); D43c amended.
  - The null deck is checked at O0/O1 only.
  - pytest 50 pass. Broken copy (old ÷100) fails the ladder test.
- Remaining WO-16: items 3–4 (about 30 reruns plus the fp2 sweep). Not started; waiting for load < 4 or a user go-ahead.
- Note: the trap-vs-gear pair must use the spec deck, not null.

## Update 2026-11-09 ~14:00 (WO-16 items 3–4 running)
- Launch agent committed 6a96cb3, which adds `--point "k=v,..."`, per-OTA `fp2_mult1/2` and `--xcheck --only`. pytest: 51 pass.
- Run: sandbox `regr/tt/WO-16-run-6a96cb3`, 47 jobs, 2 at a time, timeout 7200 per job. Output goes to `summary.txt`; `done` marks the end. Per job: `out/<name>/point.json`.
- Job groups:
  - r1: ladder, 9 jobs;
  - r2: OTA2 knee, 9;
  - r3: OTA1 knee, 6;
  - r4: V4 / V4m at N4096;
  - r5: A′ c/d;
  - r6: T4 m101;
  - r7: xcheck;
  - fp2: 12 O1 + 3 O2;
  - t3: fp2×30 at O2.
- Caveat: O2 for the fp2 sweep runs at mult 3 and 30 only. If the O1 minimum is elsewhere, add one `--point` O2 job.
- Next: when `done` exists, a fresh agent analyses the results, writes `results/s5h_tier1.md` and commits. Then acceptance, reviewer, S6.
- Run at 34/47. `r6_T4_m101_N1024_g2_20_O2` failed: ngspice rc=124, from the internal `run_deck` timeout of 1500 s (`tier1_tb.py:100`), not the job timeout. T4 is informational. Rerun it after the batch, with a longer `run_deck` timeout (needs a `--deck-timeout` knob) or at O1.
- T4 rerun (user: "just do it"): 677b39f adds `--deck-timeout`, with a test and a broken-copy REJECT check; pytest 52 pass. Running on frozen copy `regr/tt/WO-16-t4-677b39f`: deck timeout 14000 s, job timeout 15000 s, at O2. Launched at load ~7.8 on user OK. That makes 3 of our processes alongside the main batch.
- **Load gate dropped (user, 2026-11-09):** run without waiting for load; still at most ~5 of our processes.
- fp2 O1 sweep, INL ppm at D39 4 MHz N1024:
  - OTA1 (OTA2 at ×3): 1.5 → 68.5, 2 → 10.9, **3 → 3.29**, 4 → 8.06, 6 → 14.7, 10 → 21.0, 30 → 28.3. The minimum at ×3 matches the ≈3.4 prediction.
  - OTA2 (OTA1 at ×3): **1.5 → 1.38**, 2 → 2.33, 3 → 3.29, 4 → 3.71, 6 → 4.12, 10 → 4.40, 30 → 4.74. Monotone, so the minimum is at the sweep edge.
  - Added jobs (`jobs_extra.txt`, same run dir; `done_extra` marks the end): `fp2_ota2_1.5_O2`, `fp2_ota2_1_O1`.

## Update 2026-11-09 (S5h analysed, OTA1 SR option 3)
- S5h results committed as 95844d9; coordinator spot-checked 8/8 values against the json. Opus reviewer running → REVIEW-S5h-2026-11-09.md.
- User chose OTA1 SR **option 3**: direct points before deciding 12.5 vs 13 V/µs.
  - Jobs (`jobs_sr1.txt`, `done_sr1` marks the end, same run dir): `r3d_N{256,1024}_sr1_{12.5,13}_O2` plus `r3d_N1024_sr1_{12.5,13}_O1` for the convergence pair.
  - Then present the INL margin to the user. **The SR decision stays with the user.**
- T4 rerun still running (`WO-16-t4-677b39f`).
- REVIEW-S5h saved. G-M3 closed for all gated rows. S6 is not blocked. 1 Major (H-M1: SPEC slew bases cite O0 numbers) and 7 minors.
- Reviewer gap jobs (`jobs_gap.txt`, 1 at a time, `done_gap` marks the end):
  - OTA2 10.8 V/µs N1024 O2;
  - A′ c/d N256 O1;
  - trap O1 on r2 N1024 13.5.
- Open after the jobs:
  - user's OTA1 SR decision (A keep 12.5 / B 13);
  - SPEC text (slew bases, PM windows OTA1 "72–77° at 20 MHz", OTA2 ~70–85°, O2 evidence note);
  - s5h doc fixes;
  - then S6.
- OTA1-only direct points (2 MHz, sr2 unset), INL ppm:

  | Point | O1 | O2 |
  |---|---|---|
  | N1024, 12.5 V/µs | 0.098 | 0.101 |
  | N1024, 13 V/µs | 0.082 | 0.083 |
  | N256, 12.5 V/µs | — | 0.359 |
  | N256, 13 V/µs | — | 0.340 |

  - At N1024 12.5 V/µs: converged, verdict 0.104 against the 1.333 slew share, **12.8× under**.
  - Neighbours at O2: N1024 10 → 1.925, 10.5 → 0.859.
  - Moving from 12.5 to 13 V/µs gains only 0.02 ppm.
  - **Waiting on the user: A (keep 12.5) or B (13).**
- Reviewer gap jobs, all closed:
  - **OTA2 at 10.8 V/µs, N1024, O2: 0.756 ppm**, under the 1.333 share. So 13.5 has ≥ 25 % margin at the gated N, measured directly.
  - **A′ N256 at O1:** c 0.403, d 1.982 against a gate of 20, ≥ 10× under. Below 6.7, so no O2 run needed. H-m2 closed.
  - **trap vs gear at O1, r2 N1024 13.5:** 0.253 vs 0.2595 (2.5 %). D43c trap/gear check closed for 2 MHz.
- Left before S7:
  - the user's OTA1 SR decision;
  - SPEC text (H-M1 slew bases, H-m3/H-m4 PM windows, O2 evidence note);
  - s5h doc fixes (H-m1, H-m6, Q5);
  - T4 rerun (informational) still running.
- **User: OTA1 SR option A (keep 12.5), recorded as D44.**
  - SPEC restated at O2: slew bases, PM windows, converged-evidence note (e5603de).
  - s5h doc fixes (f05db26). DESIGN_GUIDE updated.
- **Next: S6** (golden vectors for C9):
  - ideal-A;
  - bitstream-only u_hat with the sys sign;
  - F7 mode tag, F8 forced y[0];
  - order-1 u_corr branch.
- Then S7 (reviewer pass, then user OK).
- S6: WO-17 written and dispatched (Sonnet). Then acceptance on a frozen copy, then the reviewer, then S7.
- **S6 done (WO-17)**: commits a34b809 (model), 13f9692 (golden), 8b095d3 (results).
  - 240 mode vectors plus 2 sequences, 500 frames, `golden/s6_vectors.json` (sha256 b8bd7a93…).
  - Independent integer checker 500/500 bit-exact. Mutants 9/9 REJECT; the 24-bit accumulator ACCEPTs, as required.
  - Coordinator acceptance (in place on tt-sd, since the disk is full):
    - pytest model+design 131 pass;
    - hash matches;
    - own corruptions (acc1+1, y bit flip, frame_ctr) all caught.
  - SPEC ambiguities the agent resolved, which need SPEC rows at S7:
    - forced y[0] = +1;
    - tags: chop_sign ±1, n_code 0..3, 8-bit frame_ctr;
    - pair_idx, invalid flag on both frames, latch at the next even slot;
    - order-1 acc2 null;
    - chop-off still emits pairs.
  - The OTA-chop phase mutant cannot be expressed at tier 0.
  - Note: a sync without `golden/` present locally deletes it on the sandbox (rsync --delete).
- Reviewer (S6) running → REVIEW-S6-2026-11-09.md.
- **Sandbox disk 100 % full** (201 MB free). Our regr/tt holds 140 GB, of which ~123 GB is raw CSVs. The user OK'd deleting them; my delete was blocked by the permission check, and the user's `!` run did not take effect. Re-ask the user.
  - T4 post-processing is blocked until then (its csv is kept).
  - Future WOs: delete a job's raw csv after its json is written.
- REVIEW-S6 saved (18961a0): accepted with conditions, 3 Major (M1 forced y[0] untestable at RTL, M2 no control-trace golden, M3 short/mode not latched/tagged), 11 minor; 9 SPEC rows blocked S7.
- D45 + SPEC §3.7a (f930e94) add the digital conventions:
  - forced y[0] = +1;
  - + on even slot, +−−+ dropped;
  - frame layout 2×32 b + 16-bit tag;
  - shadow latch at the even-slot reset edge;
  - invalid after rst_n;
  - order-1 acc2 = ΣS;
  - OTA-only allowed (characterisation);
  - PGA field removed;
  - reset window 2 fs cycles, fch = fs/2;
  - accumulators unsigned by chop on chip.
  - **The user confirms (e), (g), (i) at S7.**
- WO-18 (golden v2) dispatched. It is needed before C9, not before S7.
- Open questions for the C stage (REVIEW-S6 §5):
  - How is order 1 built in the analog?
  - Is the raw pin defined during reset?
  - Frame double-buffering?
- **WO-18 done** (93e3528, 0de07b4, 95564bc).
  - 1054 frames plus a 396-cycle control trace, 777 KB, sha f08faffe….
  - Every mutant (data, sequencer, trace, offset) REJECTs. 24-bit acc2 and 14-bit acc1 ACCEPT, as required.
  - Coordinator acceptance:
    - pytest 147 pass, 2 skip;
    - hash matches;
    - own trace-bit flips (sys_swap, acc_clear, raw_pin) all caught.
  - Cycle-level choices recorded as SPEC D45(k).
- **Next: S7** = reviewer pass over SPEC v1 (all review findings closed? consistent?), then the user's OK, which includes D45 (e), (g), (i).
- REVIEW-S7 (1b6bca3): FREEZE WITH EDITS.
  - All 46 prior Critical/Major findings closed.
  - New Majors:
    - S7-M1: step gate has no threshold;
    - S7-M2: boost/trim not latched or tagged;
    - S7-M3: digital I/O undefined;
    - S7-M4: §3.4 caps wrong.
  - Plus E1–E24 text edits.
- User answers → D46 (uncommitted: 1Password LOCKED):
  - D45 e/g/i confirmed;
  - **16-bit parallel readout on uo + uio**;
  - 200 µA is a design budget;
  - full freeze.
- WO-19 written (uncommitted) and dispatched. The agent leaves its work uncommitted if signing stays locked.
- **Commit once unlocked:**
  1. D46 (`DECISIONS.md`);
  2. WO-19 + INDEX + RESUME;
  3. the WO-19 agent's commits (file lists in its report).
- Then: reviewer re-check of the S7 edits, then the user's final OK → mark SPEC v1-frozen → S→C gate.
- WO-19 done:
  - commits b3b9ea1, 335e960, b9fab0e, 9a15258, e5546f8; pytest 152 pass;
  - §3.8a digital I/O: 16-bit bus, ui_in fully allocated, 48 MHz fs_div table.
  - Flag: the step-gate OTA1 ε is an identical 1.6e-8 at 2 MHz and 4 MHz, against the hand estimate of 6e-5. Suspected numerical floor, being re-checked.
- D47 (5912796):
  - no extra analog pin;
  - trim volatile, stored in RP2040 flash, manual calibration;
  - the bias-readback oscillator is pending the user's choice.
- Pin pricing fixed (0b13d9a): €40 for pins 1–2, €100 after, so 4 pins = €280 and the total is about €560.
- Reviewer S7b re-check running → then the user's final OK to freeze.
- Golden v3 items queued for before C9:
  - boost/trim config;
  - status word / overrun;
  - readout word order.
- Disk freed by the user (322 csv deleted, 115 GB free).
- The old T4 csv was truncated (12.5 of 25.9 ms) → rerun launched in the T4 frozen dir; the csv is deleted after post-processing.
- REVIEW-S7b + D48 (3651718): small edits, then freeze.
  - Step gate option 2: in-loop transistor gate authoritative, step tb diagnostic.
  - The D39 control is not A′.
  - 0.94 µV governs.
  - Status reports the frame's boost/trim.
- S7b edit agent dispatched. After it: coordinator check, then **ask the user for the final freeze OK**.
- S7b edits done:
  - commits 52842af, 0c0392d, 3427dc7; pytest 152 pass;
  - stale-string greps all clear;
  - OTA1 macro ε_dyn is now 4.3e-9 (static A0 term removed); its broken copies REJECT.
- **Waiting on the user:**
  - (1) final SPEC v1 freeze OK;
  - (2) bias-readback oscillator: manual only, or a conditional C6 item.
- After the OK, in order:
  1. Mark SPEC v1-frozen and tag it.
  2. S→C gate.
  3. Golden v3, a C9 entry item.
  4. Stage C starts with C1 (OTA).
- User: hold the freeze until they have reviewed a report.
  - Report published (private): https://claude.ai/artifact/X5CESjvvGW8y38bwR3F2oz
  - D49: the oscillator is a conditional C6 item.
- **Waiting on the user's freeze OK.**
- T4 rerun done:
  - INL 12.40 ppm; cubic residual rms 2.72 / max 9.14 ppm;
  - smooth, odd ≈ 5th-order shape (lag-1 autocorrelation 0.96), so the old "jagged" residual was an O0 artefact;
  - informational, closed (s5h addendum 2); the csv has been deleted.

## Update 2026-11-09 — SPEC v1 FROZEN (D50), Stage C started
- Freeze: e2c025a, local tag `spec-v1`. SPEC changes now go only through the SPEC change log.
- PLAN marks the S → C gate as passed. DESIGN_GUIDE §8 updated.
- C1 step 1: WO-20 (OTA1 design note, Opus) dispatched. Next:
  1. reviewer on the note;
  2. C1b: SIZES → netlist → tbs at 45 PVT, plus the in-loop gate (B).
- WO-20 done: 30ab856 (DESIGN.md + sizes_draft.py) and the spot-check script (committed).
  - Topology: folded cascode, pfet_01v8 input pair W 40/L 1, g5v0d10v5 protection cascodes, SC CMFB on a short-L load section, chopper, ×2 boost leg.
  - **Spot sim fails on A0:** tt base 80.3, ff/125 base 75.3, tt boost 71, ss/125 boost 58 dB. Suspect a device leaving saturation.
  - fp2 at 10–12× GBW (PM 85°): too high against the S5h optimum of ~3×.
  - The protection-cascode bias needs a negative gate at ss/−40.
  - Noise 121–157 µV (≤ 250 OK). Current ≈ 52/105 µA base/boost.
  - MC timed out; some corners crashed or are non-physical (script issues).
  - Proposed SPEC change-log entries P1–P4: in-loop A(v) gate for boost, booster current, β1 ≥ 0.83, Cs2 bottom-plate rest.
- Next: reviewer on DESIGN.md (running). Then C1b: op-dump saturation margins, fp2 fix, gain boosters, script fixes. Any SPEC change needs the user's OK.
- REVIEW-C1a (0631fb0): REVISE NOTE FIRST. The A0 failure is headroom (m_pl in triode); fp2 10–12× GBW puts fast 5 ppm at risk; the cascode bias, clamp and input chopper are wrong.
- User D51: P1 accepted (boost A0 floor from scan), P2 rejected, fast-mode 5 ppm is a must (gm first), P3/P4/P5 accepted → SPEC change log CL-1 to CL-4 (e1fa63c, 659425e).
- Dispatched:
  - WO-21 (Opus): note rev B;
  - WO-22 (Sonnet): GBW sweep, pole-after-tanh, A0 floor.
- Next: WO-23 = fixed tb tooling and re-spot at 45 PVT × 2 with the rev B sizes, then reviewer.
- WO-22 partial: b4fb3d2 (fp2-after-tanh option + test). 16 sweep jobs are running in `regr/tt/WO-22-b4fb3d2` (DONE files; csv auto-deleted). A watcher is armed; resume the agent when all 16 are done.
- **Key early finding (A0 scan, `model/studies/c1_a0_scan.py`, uncommitted):**
  - With the S4 A(v) shape (A0, −5, −10, −20 dB at 0 / 1.4 / 2.0 / 3.1 V), N 1024 INL is 5.37 ppm at 80 dB and still > 3.33 ppm. Flat A0 passes even at 60 dB.
  - So INL is set by the **A(v) droop shape**, not by A0 or N. The CL-1 "≈ 72 dB" premise holds only for a milder droop.
  - Likely restatement of CL-1: gate boost like precision, i.e. model INL with the **measured boost A(v) table** ≤ 5/1.5 ppm at N 1024. Present this to the user when WO-22 lands.
- WO-21 rev B done (ca8a6f8):
  - Sizes: pair 80/0.5, m_n 72/4, m_pl 80/4 plus CMFB 15/2, cascodes at L 2, tracking bias, m_pp gate at 0 V, 3.3 V NMOS vg switches.
  - Spot results (9 PVT × 2 modes):
    - A0: precision 79.6–82.3 dB (fs/125 base 0.4 dB short); boost 80.8–85.
    - A(v) min, boost: 73.6 dB.
    - GBW boost 26.5–41 MHz; PM 77–82°, fp2/GBW 3.8–6.
    - Every device ≥ 0.09 V above Vdsat.
    - β1 0.846.
    - Fast mode ≈ 196 µA, because the bias legs are sized for 500 ns boost-toggle settling.
- SPEC CL-4/5/6 applied, D52 (790c64a).
- REVIEW-C1a-revB running. One question for the reviewer: can the 500 ns boost-toggle settling relax to "before the first valid pair"? D45(e) already flags that pair invalid, which would bring fast mode back to ≈ 189 µA.
- The WO-22 sweeps are running (watcher armed).
- REVIEW-C1a-revB (71bd8c4): proceed to C1b with conditions.
  - RB-M1: the bias diodes are inconsistent with K.
  - RB-M2: the hot-boost A(v) droop is likely > 5 ppm.
- User D53: CL-7 (boost-toggle settling 4 µs) and CL-1b (boost gain gated by table-INL) accepted (bfb7e92).
- The WO-22 sweeps finished; the agent was resumed for the O2 reruns and results.
- WO-23 (Opus, rev C) dispatched. After it: WO-24 = netlist + full 45 PVT tbs + gate B (needs C_FOLD_EXTRA from WO-22).
- 2026-11-10: the usage limit hit at ~19:50 stopped WO-23. After the reset both agents were resumed:
  - WO-23 continues rev C;
  - WO-22 finishes its O2 refinement, pytest, results and commit 2.
- WO-22 first pass (O1):
  - OTA1 GBW needed for ≤ 3.33 ppm at N 1024 / 4 MHz: ≈ 27 MHz at fp2 ×10, ≈ 28.5 MHz at ×30. Rev B worst is 26.5 MHz, just short.
  - Pole-after-tanh: the optimum stays at ×3 (3.58 ppm at 20 MHz), so the S5h result transfers.
  - S4-shape A0 scan: ≈ 84 dB would be needed, and the droop shape sets INL (consistent with CL-1b).
- **WO-22 done** (b4fb3d2, 86d1890; pytest 153):
  - GBW needed for ≤ 3.33 ppm: 26.9 MHz at fp2 ×10, 28.4 MHz at ×30 (O2).
  - Pole-after-tanh optimum at fp2/GBW ≈ 2.5 (1.2 ppm); the window is only 2.2–3.0.
  - S4-shape A0 would need 84 dB; flat passes at 60 dB.
  - Passed to WO-23: route (i) GBW ≥ 28.5 MHz, or (ii) fp2 ≈ 2.5× via C_FOLD_EXTRA.
- WO-23 is running. It committed cf81c5b (model strict A(v) range check).
- WO-23 run 1: the narrow single-finger mirror references broke the ratio; fixed with unit-finger 1:32 mirrors (I_fold/I_tail 1.27–1.36 confirmed).
- WO-23 run 2:
  - K_P 4 put m_pl/m_plc ~0.04 V into triode, so K_P goes to 6 (interpolated);
  - the A(v) sweep stuck at the rail (script), now split into 0→±1.8 V;
  - span at K_P 5 is 1.55–1.63 V.
- GBW: rev C 26.5 MHz worst; pair 120/0.5 gives 26.9 MHz (β1 0.84); 160/0.5 breaks β1.
- **User D54:** free route (120/0.5 pair plus fold-cap fp2 placement, gate B decides; current only as a fallback, with OK).
- Run 3 (K_P 6, split sweep, tables) is running; a watcher is armed. Resume the WO-23 agent when it finishes.
- Run 3 (K_P 6) done, still REJECT:
  - load margins are now 0.004–0.05 V (positive, below 50 mV);
  - 9 copies fail symmetry at 0.53–1.02 dB.
- The agent was resumed to fix the margin (K_P 7–8), diagnose the symmetry issue, switch to the D54 120/0.5 pair, run table-INL and commit.
- Watcher lesson: don't use pgrep inside an ssh watcher; it matches its own command line. Wait on EXIT markers only.
- WO-23 run 3 (K_P 6, pair 80/0.5):
  - **table-INL PASSES at all 9 PVT × 2**: boost N 1024 0.75–2.43 ppm against 3.33; precision 0.51–2.13 ppm against 5.33. Max |x1| is 1.20 V, inside the table.
  - Span at hot boost 1.48–1.56 V.
  - **But precision A0 is 68.7–74.7 dB, against the SPEC ≥ 80 dB (D15, user).** Cause: m_pl near triode, so low ro.
  - Symmetry: the failures were a vntol artefact at |v| ≤ 0.15 V; fixed with vntol 1e-10.
  - The CL-1b broken copy (m_pl L 0.5) is blind (3.02 < 3.33). A PMOS-cascode short copy was added. A CL-1b amendment is proposed and needs the user.
- Run 4 (K_P 7, pair 120/0.5, vntol fix, new mutant) is running in steps `tab_{2,3|4,0|1|5,6|7,8}.log`; a watcher is armed. Then resume the agent.
- **Likely user question:** if precision A0 stays below 80 dB while table-INL passes with large margin, either keep 80 dB (next lever: m_plc L 4 + Cc 0.2 pF) or make A0 a health row in precision too.
- WO-23 run 4:
  - K_P 7 margins 0.043 / 0.049 V at cold base, so run 5 uses split bias (K_P 8 base / 7 boost).
  - Span at hot boost 1.41–1.50 V.
  - Pair 120/0.5: GBW worst 27.0 MHz (fs/125), β1 0.831–0.846.
  - Precision A0 at K_P 8: 79.5–81.4 dB.
  - Rev C interim commit 289aec7.
- **User D55:** keep precision 80 dB and apply m_plc L 4 + Cc 0.2 pF. CL-1c: the broken copy is now a PMOS cascode short (f88de79).
- Run 5 (final tables) is running; a watcher with a marker file is armed.
- Plan:
  1. resume the WO-23 agent only to wrap up run 5 (INL + commit);
  2. then a fresh WO-24 = C1b: m_plc fix (item 0) + netlist + full 45 PVT tbs + gate B. That agent's context is large (~200k tokens), so start fresh.
- **WO-23 closed** (cf81c5b, 289aec7, 61ca6a7).
  - Run 5:
    - all 18 copies pass margins (worst 0.067 V);
    - span at hot boost 1.41 / 1.48 / 1.50 V;
    - symmetry ≤ 0.002 dB;
    - **table-INL PASS at all 9 PVT**: boost 0.38–2.31 ppm against 3.33, precision 0.31–0.81 ppm against 5.33;
    - the PMOS-cascode-short copy is REJECTED at the boost gate (9.86 ppm).
  - **Open:**
    - precision A0 fails at 3 of 9 points (fs/−40 78.4, fs/125 79.3, ff/−40 79.5 dB); D55 fix → WO-24;
    - **the precision-gate broken copy is blind** (cascode short 3.4 ppm < 5.33): a gross gain loss is flat, so its INL stays low. The A0 row catches it, but the table-INL precision gate needs a droop-type mutant (e.g. K_P lowered so the load triodes at large swing);
    - margins are thin: span 0.01 V, β1 0.001, GBW ~0;
    - no junction caps yet; ideal CMFB.
- Next: reviewer on rev C, then WO-24 (C1b).
- REVIEW-C1a-revC (d18f6e8): PROCEED TO C1b WITH CONDITIONS.
  - RC-M1: precision A0 needs K_P base 10 plus D55.
  - RC-M2: composite 1:32 references.
  - RC-M3: per-mode broken copies, now CL-1d.
  - Also CL-8 (vbpc boost increment) and D56.
  - Real-load GBW is ~1.5× the 1.4 pF number, so fp2/GBW ≈ 1.5–3.1. C_FOLD_EXTRA stays 0 until gate B.
- WO-24 (Opus) dispatched: sync, sweep, netlist, op/AC, first gate B point.
- Pending user items after the WO-24 sweep: is D55's Cc 0.2 pF still needed; does CL-4 β1 become informational if missed.
- **WO-24 BLOCKED: 1Password locked** (ssh to the sandbox and commit signing both fail).
  - All code is written but not run and not committed:
    - DESIGN.md sync, revc_inl tagging, sizes_draft (K_P 10 base, D55, 4×4 composite refs);
    - the revc_check kp mode;
    - netlist.py + test_c1_netlist.py;
    - c1b_opac.py, c1b_gateb.py;
    - gen_tier1 `ota1_xtor` hook.
  - Review Q1: tier-1 cl1 = 1.4 pF total, and macro GBW is defined at the 1.4 pF lump.
  - **Once unlocked, resume the WO-24 agent** with its resume list (sync → frozen copy → pytest → step 0 → kp sweep → opac → gate B smoke, then full), then the 4 commits.
- REVIEW-C1b-code (static, nothing run): hold the first run until must-fixes 1–10 are in.
  - Netlist core OK.
  - Problems in the tbs and broken copies: gate B rstb per-conversion (M1), sr95 rated at 1.4 pF and fail-open (M2), p15 = p30 (M3), stale loads (M4), opac/revc_inl fail-open (M5/M6).
  - D57 answers Q1–Q3.
  - The fix agent (local edits only) is dispatched. Then, once 1Password is unlocked, resume the WO-24 run list.
- Must-fixes 1–10 + the D57 DESIGN.md changes are applied (local, py_compile OK, untested, uncommitted).
  - Note: gateb uses β1 0.84 (load 0.86 pF, SR95 scale 0.221) while opac uses 0.846 (0.836 pF). Unify on the measured β1 after the first op/AC.
- **Once unlocked:**
  1. commit WO-24 work + the C1b-code review + D57 + RESUME in atomic commits;
  2. resume the WO-24 agent's run list: sync → frozen copy → pytest → revc_inl step 0 → kp sweep → opac → gate B smoke → full + sr95.

## Update 2026-11-10 ~09:40 (1Password unlocked; WO-24 runs launched)
- Committed WO-24 work: 95a8f42, 6ec3622, 5f6939c, a1a1fad, 84aca8c (untested code, review, D57, RESUME).
- Frozen copy `regr/tt/WO-24-84aca8c`.
- `s0.sh` → marker `S0DONE`: pytest (design+model) and revc_inl step 0 on r5 tables (`out/inl0` expect exit 0; `out/inl0_swap` with mutpcb2 table swapped to nominal, expect nonzero; `out/inl0_empty` expect nonzero).
- `s1.sh` → marker `S1DONE`: kp sweep (`out/kp`, logs kp_a/kp_b) then op/AC (`out/opac`, logs opac_a/opac_b), 2 chains. CSVs deleted at end.
- Next after S1DONE: gate B smoke (`c1b_gateb.py --n 64 --m 3 --deck-timeout 600`), then full N 1024 m 21 O1 in parts, then `--copy sr95`.
- S0DONE: pytest 163 passed. revc_inl step 0: r5 tables exit 0 (27 nominal ACCEPT, mutpcb2 REJECTED at 9.855 ppm); mutpcb2 swapped to the nominal table → mutant PASSED (blind) → exit 1; empty dir → exit 1. Fix 7 verified.
- Gate B smoke: first run exposed control-mode `meas ... par()` failure → fixed with `let` vectors (8ef9a7e), new frozen copy `regr/tt/WO-24-8ef9a7e`. Rerun clean (problems []); N64 INL 10.5 ppm is not gate-relevant. Out CM at release: dummy 2.61 V (start-up), then 1.538/1.553/1.551 V; island CM 1.19–1.20 V. Note the ≈ +40–50 mV out-CM offset vs V_OCM for the CMFB rows.
- `s3.sh` in WO-24-8ef9a7e → `S3DONE`: gate B nom N1024 m21 O1, 6 parts (3 parallel × 2), logs `out/gb_p<i>o6.log`. Combine = max INL over parts after checking endpoint agreement (same endpoint conversions in every part). Then `--copy sr95`.
- s1 (kp sweep → opac) still running in WO-24-84aca8c.
- S1DONE (kp sweep + op/AC): see `results/wo24/README.md`. Netlisted precision A0 fails at fs/−40 (79.47 dB) and ff/−40 (80.23 dB); ff/125 I_fold/I_tail 1.192. Spot deck: K10 alone ≥ 82 dB; D55 adds 0.5–0.7 dB but lowers f_cm. Boost fp2/GBW at the real load is 1.08–1.61 (below the WO-22 window). β1 0.831–0.845. All of this goes to the user with the gate B result.
- Reviewer diagnosed the cold A0 miss: composite refs (bulk at rail) mirror +20 % current; cascode-bias K diluted. Confirmed: single-finger refs give ff/−40 83.80 dB, fs/−40 83.66 dB, I_vdd 50.5 µA base. **User decision needed:** how to re-centre (scale I_REF by the measured ratio / replica-derived cascode bias / per-finger wells / K_P 12 patch). Gate B (s3, WO-24-8ef9a7e) still running on the composite-ref netlist.
- **D58 (user):** ref fix = scale I_REF by the measured ratio + replica-derived cascode bias; D55 reverted to p15, f_cm gets its own lever later.
- **Gate B (composite-ref netlist, fs/125 boost, N1024 m21 O1, 6 parts): all ACCEPT, INL ep 1.82–2.29 ppm (max 2.291) against gate 5.0 and share 3.33.** Still to do: check endpoint agreement across the parts, run the sr95 broken copy, and rerun after D58.
- Sandbox ssh DNS failed ("Could not resolve hostname mempool.lan") at the gate B check; retry.
- WO-25 written (wo/WO-25-C1b-ref-fix.md). Dispatch once sandbox reachable (local DNS cannot resolve mempool.lan; network changed).
- 2026-11-10 11:55: sandbox reachable again (VPN off). sr95 broken copy launched in WO-24-8ef9a7e (s5.sh → S5DONE, logs out/gbsr_p*.log). WO-25 items 1–4 dispatched to an Opus design agent (it does not touch item 0).
- pthomas learnings triaged → `LEARNINGS-pthomas-2026-11-10.md`. Determinism check s6.sh (WO-24-8ef9a7e, S6DONE): two identical smoke runs at PDK num_threads=8; compare INL digits.
- WO-25 agent done (7de6857, d07bd49, f83d326; results/wo25/README.md). D58 applied, D55 reverted. Precision A0 ≥ 80.3 at all 9 PVT (min 80.43 fs/−40, margin 0.13 dB); I_vdd 52–56 / 106–111 µA. **I_tail ±3 % exit fails at 5/9** (−4.2 % cold, +4.2 % ff/125 boost; composite ratio drifts with T) → user decision. kp_fixed broken copy blind on the K_P row (A0 row catches it). V_OCM error up to +58.8 mV hot. combine() verified (endpoint spread 0.0097 ppm; broken copies exit 2).
- WO-25 gate B queued on sandbox: starts when WO-24 sr95 writes S5DONE; marker `WO-25-d07bd49/GB_DONE`, verdict `out/gb/combine.out`. Reviewer pass on WO-25 running.
- Note: the frozen copy needs `golden/` for model/tests/test_golden.py (33 errors there are a copy artefact).
- Determinism check: two identical smoke runs (num_threads=8 from the PDK spinit, under different load, 660 s vs 138 s) gave bit-identical INL 10.4710869922615 ppm, matching the earlier smoke. Our ngspice-45 build is deterministic here; no num_threads change needed. (pthomas item closed for this machine; recheck on any other host.)
- REVIEW-WO25: hold gate B (queued waiter cancelled). Majors: A0 relies on replica error; V_OCM +58.8 mV > CL-2 ~38 mV; I_tail row = SR floor proxy (±5 % breaks SPEC row 95); K_P row blind; gate B needs 4 corners. User Q1 (ref architecture) / Q2 (K_P) pending.
- D59 (user): parallel 1:8 refs + common-centroid/dummies layout intent; K_P 12.5 + replica fix. WO-26 dispatched.
- WO-24 sr95 broken copy, old netlist: parts 0–2 REJECTED (INL 3.1–3.4 % ≫ 5 ppm, healthy). The coordinator stopped parts 3–5 (obsolete netlist).
- WO-26 done (6dccfd3, 0ed1112, b177d23, 10ffd21; results/wo26). All op/AC exits and new rows pass:
  - precision A0 ≥ 83.79 dB;
  - SR min 12.83 / 25.54 V/µs;
  - V_OCM ≤ 30.8 mV;
  - K_P tracking ≤ 0.64 %;
  - every broken copy REJECTED.
- Item-1 ratio exit fails: ratios 0.944–1.031 from the Vds offset; spread over T up to 2.85 %. The rcb leg adds 0.37 / 0.74 µA outside D59 and needs the user's OK.
- Gate B running: `WO-26-b177d23/gb.sh`, 30 parts in waves of 3, status `out/gb_status`, marker `GB_DONE`, up to about 30 h. Reviewer pass on WO-26 running.
- REVIEW-WO26: proceed, wait for gate B. Open for the user: item-1 ratio (a/a+c/b), V_OCM mismatch fix, rcb leg OK. Coordinator: sr95 also at sf/−40 after the current gate B; C6 line for boost-control level shift / break-before-make.
- D60 (user): ratio row info-only + mismatch allotments, I_REF_btp +1.9 %; CT CM error amp in the CMFB loop; rcb kept. WO-27 dispatched (≤ 2 procs; the WO-26 gate B keeps running).
- WO-27 agent stopped at the item-3 exit (exploration at tt/27 only, `regr/tt/WO-27-explore`; results/wo27/README.md):
  - CM amp (3.85 / 7.66 µA): V_OCM systematic + 3σ = 63.3 mV base / 20.7 boost, against the 10 mV target. A_cm is only about 3. Passive-loop σ ≈ 18 mV, so the passive loop also fails 38 mV at 3σ.
  - SR/ceiling 3σ rows fail: σ(I_tail) 3.4 % base / 2.4 % boost at A_VT 12.
  - tb9 start-up fails: wrong charge on the sense node, Cr refresh τ ≈ 1 µs.
  - No nominal f_cm / CM PM yet (loop-break issue).
  - **Git:** the index holds the coordinator's D60/WO-27 files AND the agent's blobs (DESIGN.md, c1b_opac.py, sizes_draft.py). Commit with explicit paths once 1Password is unlocked. The rest of WO-27 is uncommitted in the working tree.
  - User decisions pending: CMFB architecture, the SR/ceiling mismatch fix, and the V_OCM bound basis.
- D61 (user): dual-path CMFB; larger reference area for SR/ceiling 3σ. WO-28 dispatched on top of the WO-27 working tree.
- WO-28 code written, NOT run: 1Password is locked, which also blocks the sandbox ssh (signing via the 1P agent).
  - Code: dual-path CMFB (slow gm-C integrator into bli, 2 pF MIM, +0.78 / 1.56 µA; WO-27 CM amp removed), tail unit 3.75/6 (9× area), start-up clamps on ctl/bli/outputs, new rows and broken copies.
  - Hand estimates: V_OCM 3σ ≈ 6.5 mV; SR − 3σ 13.02 / 26.17 V/µs; ceiling + 3σ 19.52 / 38.46 µA.
  - Planned commits and paths: results/wo28/README.md.
  - Agent ran `python3 netlist.py` locally once (text generator only), a rule slip; noted.
  - **Once unlocked:**
    1. commit with explicit paths, in this order: D60/D61/WO-27/WO-28/INDEX/RESUME; then the WO-27 code + results/wo27; then the WO-28 code; then results/wo28;
    2. follow the results/wo28/README pickup steps (sync, frozen copy, pytest, opac idx 0, tb9 0,2,3,4 + --mut, then 9 PVT).
  - Expected user decision: f_cm likely < 9.4 MHz → Cc 0.3–0.4 pF or a CMFB split.
- 1Password unlocked; committed 073c076, 0167598, e42898f, d280b07.
- **WO-26 gate B done: all 4 corners ACCEPT.** fs/125 3.314 ppm (share 3.33), ss/−40 0.797, ss/125 1.686, tt 0.454. sr95: every part 4.4–5.5 % INL, but combine INVALID (endpoint memory 40 ppm). Needs a combine() broken-copy rule. See results/wo26/README.md.
- WO-28 run 1 (frozen WO-28-29d1fdc, tt only), logs in results/wo28/run1:
  - pytest 176 passed. fcm_hand check OK (the return-ratio extraction matches analytic within 0.01 %).
  - Nominal op/AC: A0 86.0 / 83.6 dB; base V_OCM +6.9 mV (3σ 13.9 > 10); boost 0.42 mV (3σ 7.3).
  - **Testbench bugs:**
    - the nominal CM-open helper copies are dead (V_OCM 1.7 V, margins negative), so f_cm 0.013 MHz, CM PM 19° and peaking 25 dB are artefacts. Suspect: the helper copies share bias/vocm nets with the nominal copies in the same deck, which would also explain base V_OCM 6.9 mV against 0.26 mV in the mutant decks;
    - `mrnc margin nan` in every row; `NaN V_rnd` in the mkp copies.
  - Broken copies: all REJECTED (mutnc, mutrc, mkp5, mtlo, mthi, mcc4 at 2.46 MHz).
  - Fix pass dispatched (WO-28b).
- WO-28 run 2 (c6bef6d, 48a0773, beea236 reverted in b8196f3, 8278860; results/wo28/README.md):
  - Testbench bugs fixed. The cause was op non-convergence falling back to "Transient op"; it is now a lint. Helpers run in their own deck.
  - At 9 PVT: V_OCM sys+3σ ≤ 7.84 mV; SR − 3σ ≥ 12.76 / 25.83; ceiling OK; A0 base 84.1–87.3 dB; CM PM ≥ 78°; peaking ≤ 0.4 dB.
  - **Boost f_cm 4.1–7.0 MHz < 9.4 at all corners** → user decision.
  - **tb9:** the CM step settles to 5–7.5 mV, a pass. The switched-cap transient sits +129–167 mV (tt) / +34–42 mV (hot) off V_OCM, against +0.3–0.6 mV in the averaged op. The event rows fail; sulo start-up fails 14–34 mV. Undiagnosed: SC-vs-averaged model mismatch, or the slow path not converged by 1.5 µs.
  - Open: the cold-corner op falls back to transient op (ff/−40, sf/−40). C6 reference accuracy needs a budget line (base SR − 3σ only 2.1 % above the floor).
- D62 (user): tb9 authoritative, f_cm info. WO-29 dispatched.
- WO-29 (b583094, 760d618, 9e14bed, d04a2c6; results/wo29/README.md):
  - **The tb9 offset was a testbench bug:** Cint was wired outp→inp, positive feedback, so the outputs latched. Fixed, with the old wiring kept as a broken copy.
  - **D62 was based on the latched bench.** On the fixed bench the CM step misses (14–18 mV at 22.5 ns, against f_cm ≈ 5 MHz) → revisit with the user.
  - The diff-step row measures slewing (needs redefinition).
  - Reset-assert hot 25 mV, sulo start-up 14–34 mV and end-ph1 ripple 12 mV are undiagnosed.
  - combine() broken-copy rule done and verified on the WO-26 sr95 parts.
  - Cold-corner op split: the 9 PVT opac is still running in WO-29-9e14bed (markers DONE_{1,2,3}; summary via `c1b_opac.py --summary out/opac`).
  - Gate B not launched.
- D63 (user): tb9 CM judged at the sampling instant + CM-to-DM leakage; gate B is the arbiter. WO-30 follows once the WO-29 opac (DONE_1..3) finishes.
- WO-29 opac 9 PVT on the pair-per-deck split: ACCEPT at all 9 (cold corners converge; the run-2-structure broken copy is rejected). WO-30 dispatched.
- WO-30 (8de9624, 6ee1e9d, 0fb4b5c; results/wo30/README.md): D63 tb9 rows pass at tt, ss125, fs125, sf125.
  - Rows: CM events 1.8–5.9 mV at the sampling instant; CM→DM ≤ 0.024 µV against the 0.256 µV bound; diff step 0.486 V.
  - Broken copies all REJECTED (mcc4, island masy, mio).
  - Reset-assert closed; ph1 ripple bounded (CMFB switch charge / 2Cc).
  - **Start-up row fails** on the current netlist: the Cc charge error decays only through the Cr refresh, τ ≈ 1.1 µs. Cr ×2 (caps only) passes everywhere, with 0.5 mV margin at fs/125 → user decision.
  - Gate B ready but not launched: `WO-30-6ee1e9d/gb.sh`.
- D64 (user): Cr ×2. WO-31 dispatched.
- WO-31 runs in WO-31-1cf257d (op/AC 9 PVT + tb9 + mut; markers out/DONE_{1,2,3}). Coordinator: after DONE, check the summary and tb9 VERDICTs, then launch gb.sh.
