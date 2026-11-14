# WO-77 results (C1): tb7 noise-op fix, mutant bench fixes. 2026-11-14. Reruns RUNNING at hand-off.

Base commit 87a05a2. Frozen copy `/home/mempool/regr/tt/WO-77-87a05a2` (design/ golden/ model/ scripts/, `.spiceinit` num_threads=1;
the two edited files below were rsynced into it afterwards). Jobs `jobs77.txt` (tb7 idx 0..8 + mut, opac idx 0), launcher `run77.sh`,
logs `out/logs/job_N.log`, marker `out/logs/POOL_DONE`, started 14:50 IST (box load ~5.3, lpool allowed 1 slot at a time).
No OTA sizing change.

## Causes and fixes
1. tb7 `noise op != op`. Spot run on the WO-52 fs/125 fint decks: the `op` deck converges directly (gm_in 252.52 uS), but the
   `.noise` deck repeats the op from a fresh start, Newton + dynamic/true gmin + source stepping all fail, ngspice takes the op from a
   transient ramp ("Transient op finished") and lands elsewhere: gm_in 250.93 uS (-0.6 %; gm_plc +0.9 %, gm_nc +0.2 %). The vg nodes sit
   behind the 1 GOhm bias R (~35 Hz pole), so the transient op is not DC-settled. The 0.1 % tolerance is right (a 0.6 % op shift moves
   thermal noise); not loosened. Fix (`c1b_tb7.py`): `op` deck prints all nodes for every kind; its converged node voltages become the
   `.nodeset` of the noise deck (replacing the ol / default nodesets), so the noise op starts at the solution. If the noise deck still
   falls back and lands off by > 0.1 % in gm, `noise op != op` still REJECTs (op_match broken copy unchanged).
2. tb7 mrg / msink "NOT REJECTED": both failed only because `op_ok` was False through the same lint (rg_rej / rs_rej require op_ok);
   thermal 561 uV (mrg) and +19.8 % (msink) were already past their criteria. No logic change: with item 1 their op is valid and they
   must REJECT on thermal > 390 uV + tier-0 direct + ol M8 (mrg) and on rise >= half the hand rise (msink). To be CONFIRMED by the rerun.
3. op/AC job 11 (idx 0, tt/27): ALL mutants (mutnc, mutrc, mkp5, mtlo, mthi, mcc4 pair) were INVALID, not only mtlo / mthi: one merged
   `_mut` deck fell to transient op (the mcc4o 1 F loop break and 1e9 F servo caps keep initial charge). Their target rows did fire
   (SR 20.16 < 20.6 for mtlo; I_tail ceiling 42.09 > 39.96 for mthi), but the lint, kept strict, invalidated them. Fix (`c1b_opac.py`):
   one deck per mutant (`<tag>_mut_<name>`), the cm_open pair mcc4 / mcc4o together; lint unchanged (a mutant op must converge directly).

## Pickup
```
ssh sandbox; R=/home/mempool/regr/tt/WO-77-87a05a2; cd $R; ls out/logs/POOL_DONE; grep -L "EXIT=0" out/logs/job_*.log
. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R
python design/c1_ota1/c1b_tb7.py --summary out/tb7 > out/tb7_summary.txt
grep -h '"mutant_verdict"' out/logs/job_11.log | grep -o '"copy": "[a-z0-9]*"\|"mutant_verdict": "[^"]*"'   # opac mutants
grep -h VERDICT out/logs/job_*.log; find out -name '*.csv' -delete
```
Expected: 18 tb7 rows without `noise op != op`; thermal per corner vs the 390 uV row (D75 / CL-31) in the summary; mrg and msink REJECTED
(op True); opac mtlo REJECTED on SR, mthi on I_tail ceiling. If any is still INVALID, check `Transient op` in that deck's own log.
Results tables NOT yet filled (no verified numbers).
