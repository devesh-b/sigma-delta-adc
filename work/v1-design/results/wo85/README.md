# WO-85 (C4e): tim-deck HV body-node abort

Commit 6aab377 (`design/c4_sw/c4_tb.py`, `results/wo85/exp85.py`). Frozen copy `/home/mempool/regr/tt/WO-85-6aab377`
(`run/`, `run_tight/`, `launch.sh`, `.spiceinit` single-thread). Experiments: `/home/mempool/regr/tt/WO-85-exp`
(`exp85.py` reuses the WO-79 `exp.py` variants, source decks are the WO-79 `run/tim_*.sp`).

## 1. `exp/pool1` check
The WO-79 gear experiment exists: it is at `/home/mempool/regr/tt/WO-79-87a05a2/exp/pool1`, not under `WO-79-139a29d`.
It ran on the **pre-soften** decks: `t_drvall`, `t_gear` and `t_drvall_gear` all ran clean to 600 ns. That run had
ideal supplies, which is what pointed at soften().

## 2. Root cause (bench, not design)
Deck `tim_ss_m40_2M_none` from WO-79 (with soften() + drv()), truncated to 120 ns, one change per run:

| variant | result |
|---|---|
| as-is (must reproduce) | ABORT 44.7 ns, `xg.xil.x2 nfet_g5v0d10v5#dbody` (reproduced) |
| `vddideal`: Rz_vdd / Rz_vdl (1 ohm) removed, every other soften() R kept | **ok**, 3278 rows (as-is used 6118 rows before it aborted) |
| `gear` (method=gear, 1 ohm kept) | ABORT 40.6 ns, `xg.xa2.x1 nfet_g5v0d10v5#sbody`: gear does **not** fix it |
| `decap=100p` on vdd / vdl behind the 1 ohm | still running at 16:41 after 42 min (the other runs took about 9 min); result not collected |
| `gear,tight`, ff_125 4M none / vddideal / gear | queued, not collected |

The trigger is WO-79's 1 ohm in series with vdd / vdl when nothing decouples them. Only device capacitance sits on
the supply node, so it has a sub-ps time constant. The HV cells' crowbar current then moves it on every edge, and
the BSIM4 body-junction internal nodes of the HV nfets in the hvl cells (nand2 `xil`, `xa2`, LS `xls_dec`) cannot
converge. No HV node floats: with ideal supplies the same netlist runs clean. So this is **not a design finding**.
The candidates in the WO are ruled out: LS edges already go through drv(), no node floats (it runs clean with ideal
supplies), and it is not trap ringing (gear also aborts).

## 3. Fix (one bench change, commit 6aab377)
`deck_tim` calls `soften(L, supplies=False)`: in tim, Vdd / Vdl stay ideal, as in WO-70. Signal sources keep their 10 ohm,
and the LS inputs keep drv(). No tolerance was changed. Other decks are unchanged (`supplies=True`).
Caveats:
- tim no longer sees any supply bounce. This is the WO-70 condition, not a looser limit.
- A realistic bond-R + decap supply model is an option for a later WO, if the decap run finishes in a sane time.
- The ideal-vs-1-ohm invariance for tim is unproven. `run_tight` gives the tolerance invariance only.

## 4. Rerun (launched 16:42 IST, not collected)
Pool `run/pool`, 54 jobs (`run/jobs_wo85.txt`), in this order:
- the 4 previously aborting good tim decks;
- 1 `C4TB_TIGHT=1` tim ss_m40 2M into `run_tight/`;
- the 23 tim broken copies;
- the other 26 good tim decks.

The box was at load about 12 and the WO-79 pool was also running, so jobs ran one at a time at about 10 min each: expect about 9 h.
At hand-off the sandbox stopped answering ssh (banner timeout), so job 1 was never read.

## 5. WO-79 pool (not done at hand-off)
`/home/mempool/regr/tt/WO-79-139a29d/run/pool` had finished 5 of 89 jobs at 15:34. Its order puts about 55 tim jobs
ahead of the inj / settle / leak / ramp jobs, and those tim jobs run the old 1 ohm deck. They will all abort and burn
hours. **Ignore every tim row from the WO-79 pool; use the WO-85 tim results.** It was not stopped (WO rule).
- The ff/100 20 pA row is still not confirmed. The WO-70 value is 23.4 pA, and the row has not been loosened.

## Pickup
1. Sandbox alive? Check `ssh sandbox uptime`.
2. Experiments: `grep -h -E "^(t|f)_" /home/mempool/regr/tt/WO-85-exp/pool1/job_*.log`.
   - Need: `t_decap_100p` (ok / slow?), `t_gear_tight`, and `f_none` (must ABORT about 155 ns), `f_vddideal` (must be ok), `f_gear`.
   - If `f_vddideal` aborts, the fix is incomplete. Reopen.
3. WO-85 tim: `ls /home/mempool/regr/tt/WO-85-6aab377/run/pool/POOL_DONE`, then:
   `. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=/home/mempool/regr/tt/WO-85-6aab377; cd /home/mempool/regr/tt/WO-85-6aab377/run; python ../design/c4_sw/c4_tb.py report .`
   - Report exits 2: the leak / inj / etc. jobs are not in this run. Read only the tim rows.
   - Every one of the 23 broken copies must REJECT on its target row, with ok true and not an abort.
   - Diff `run_tight/tim_ss_m40_2M_none.json` against `run/` (g_min, eb_min, ls_edge, glitch rows).
4. WO-79: once `/home/mempool/regr/tt/WO-79-139a29d/run/POOL_DONE` exists, follow the `results/wo79/README.md` Pickup step 2.
   - Merge: non-tim rows from WO-79 (`run`, `run_tight`), tim rows from WO-85.
   - Fill wo79 section 4 (injection, leak D78 / D82 rating, 20 pA ff/100 row, Ron, LS, non-overlap).
   - Check every json has `ok: true` and non-empty `m`.
5. Then the ready-for-review list (see the WO-85 hand-off report).
