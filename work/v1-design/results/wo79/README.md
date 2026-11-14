# WO-79 (C4d): WO-70 triage, timestep-abort fix, D82 rating check, rerun

Commit 139a29d (`design/c4_sw/c4_tb.py`). Frozen copy `/home/mempool/regr/tt/WO-79-139a29d` (`run/`, `run_tight/`,
`launch.sh`, `.spiceinit` single-thread). Experiments: `/home/mempool/regr/tt/WO-79-87a05a2/exp` (`exp/exp.py` here).
Triage of the 28 WO-70 EXIT=1 jobs: `results/wo70/README.md` section 4 (all timestep aborts, bench artefacts).

## 1. Root cause of the timestep aborts (bench, not design)

Experiments on the WO-70 `injdm_tt_27_4M_none` deck, truncated to 1.2 us (`exp.py`, pool `exp/pool1`):

| variant | result |
|---|---|
| as-is (must reproduce) | ABORT t = 20 ns, vinn#branch |
| integrator E-source with one pole (GBW 1 GHz) + buffer | ABORT t = 20 ns, vinn#branch |
| ideal `sw` switches -> smooth tanh conductance | ABORT t = 20 ns, vinn#branch |
| both | ABORT t = 20 ns, vinn#branch |
| 10 ohm source impedance on Vinp / Vinn | ABORT t = 20 ns, **vcmin#branch** (moves to the next ideal source on the node) |

The abort happens at the fs-edge breakpoint before any node moves (ox flat at 1.19999 V). An ideal source tied straight
to pF of device / Cs capacitance has a branch current C*dV/dt that is numerical noise at the 1e-22 s steps after a
breakpoint and cannot meet abstol (1e-15 in inj / settle), so the step collapses. The same pattern names vord, vdl, vtpb,
vadn (an ammeter between ideal sources) in the other decks.

Fix (`soften()`, one bench change): every grounded independent source of the transient decks (inj, settle, tim, ramp)
gets a series R, 10 ohm for signals, 1 ohm for vdd / vdl (bond + package). tim LS inputs now go through `drv()`
(100 ohm + 5 fF) as the other decks already did. The settle pad model stays exactly R_src 1k + 500 ohm + 5 pF.
**No tolerance was changed.** `C4TB_TIGHT=1` reruns six decks with reltol and abstol / 10 (`run_tight/`) to show the
results do not move. ron and leak are .dc decks and are unchanged.

## 2. D82 rating check (CL-34)

`leak` deck: I_tot = Sg + C1 vg-node devices (same sign). Row `rating`: drift = I_tot * N_rated / (0.25 MHz * 2.01 pF)
<= 0.2 V, N_rated 256 at ff/125, 1024 at ff/100. At ff/100 the 20 pA row (N 4096, D39) is still checked (`leak`, D78
split). Broken copies on `rating` at ff/125: `noderate` (N 1024 at 125 C, no derate; expected ~0.31 V) and `sgx6` (Sg W x6).
The old `tg` copy is dropped (it lowered |I|; WO-70 caveat).
Expected from the WO-70 numbers (to be confirmed by the rerun): ff/125 I_tot ~150 pA -> 0.076 V PASS; ff/100 23.4 pA ->
N 1024 0.048 V PASS, but the 20 pA row FAILs (23.4 pA; N 4096 drift 0.19 V against 0.2 V).

## 3. Rerun

Pool `run/pool` (89 jobs: 83 changed decks, previously failed ones first, then 6 `C4TB_TIGHT=1` copies into
`run_tight/`) launched 15:04 IST. Box load 8-9 from other users, so lpool runs one job at a time: expect several hours.
ron JSONs are copied from WO-70 (deck unchanged).

**Status at hand-off:**
```
i_none ABORT 2e-08, timestep = 6.25e-23: trouble with node "vinn#branch" rc=1 rows=433
i_opbw ABORT 2e-08, timestep = 6.25e-23: trouble with node "vinn#branch" rc=1 rows=416
i_swsmooth ABORT 2e-08, timestep = 6.25e-23: trouble with node "vinn#branch" rc=1 rows=422
i_opbw_swsmooth ABORT 2e-08, timestep = 6.25e-23: trouble with node "vinn#branch" rc=1 rows=419
i_rsrc_vinp_vinn ABORT 2e-08, timestep = 6.25e-23: trouble with node "vcmin#branch" rc=1 rows=472
t_none ABORT 2.88554e-07, timestep = 6.25e-23: trouble with node "vord#branch" rc=1 rows=7930
pool: 0 EXIT=0, 1 EXIT=1 of 89 at 15:09
```
First result: `tim ss_m40 2M none` no longer aborts on vord#branch. It now aborts at 44.7 ns inside the HV device model
(`m.xg.xil.x2.msky130_fd_pr__nfet_g5v0d10v5#dbody`, body-diode node of an LS / inverter device in the generator).
So the tim decks have a second numerical cause that the source fix does not cover. Candidates, in order:
(1) `method=gear` (tim is the only transient family still on trap; experiments `t_gear` and `t_drvall_gear` in
`exp/pool1` answer this); (2) a tmax / rise-time change at 0.25 MHz; (3) as a last resort and only with an invariance
run, a tolerance change. The inj / settle / ramp / leak results in this pool remain valid (only tim decks are affected).

## Pickup
1. Experiments: `ssh sandbox 'grep -h -E "^(i|t|s)_" /home/mempool/regr/tt/WO-79-87a05a2/exp/pool1/job_*.log'`
   (t_none reproduces the abort; read t_drvall / t_gear / t_drvall_gear and s_none / s_rsrc_tpa_tpb).
2. When `/home/mempool/regr/tt/WO-79-139a29d/run/pool/POOL_DONE` exists:
   `ssh sandbox '. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PYTHONPATH=/home/mempool/regr/tt/WO-79-139a29d; cd /home/mempool/regr/tt/WO-79-139a29d/run; python ../design/c4_sw/c4_tb.py report .'`
   then compare `run_tight/*.json` with the same tags in `run/` (inl_ppm, eps_inj, tau_eff, drift_rated_V, ramp rows).
   Check every json has `ok: true` and non-empty metrics before using numbers.
3. If gear clears tim: add `method=gear` to the deck_tim `head()` (one change, stated), commit, new frozen copy, rerun
   only the tim jobs (`c4_tb.py jobs OUT tim`) plus one TIGHT tim copy.
4. Fill section 4 (rows vs SPEC: charge injection INL / eps_inj, leak D78 / D82 rating, Ron, LS, non-overlap), then the
   ready-for-review list.
