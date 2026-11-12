# WO-52 results (C1, D75): sink L 8, noise row re-base, tb7 op fix, reruns. 2026-11-13

Code commit bf4a565. Frozen copy `/home/mempool/regr/tt/WO-52-bf4a565` (design/, golden/, model/, `.spiceinit` num_threads=1,
`jobs.txt`, 36 jobs), lpool launched 04:39 IST, logs `out/logs/job_N.log` (EXIT=), marker `out/logs/POOL_DONE`.
Status at hand-off: RUNNING (gate B parts take up to ~3 h each).

## Changes
- `sizes_draft.py`: m_n unit finger L 4 -> 8 (W 72). m_nr / m_rn / m_it derive from it (K_N tracking kept). 0 uA.
- Noise row (DESIGN.md 2.7a, SPEC CL-30): v_vg <= 390 uV rms diff, derived from the 1.2 uV direct-path share
  (th_direct = n_ktc v_vg / sqrt(4kT/Cs1), n_ktc 0.559 uV from the WO-41 model rows, sqrt(4kT/Cs1) 182.0 uV -> 391 uV).
  The 250 uV row is KEPT AS INFO (column flag `>250(info)`), not a gate. The 200 uV D71 target is dropped.
  Gates: 390 uV row + tier-0 direct thermal <= 1.2 uV, joint <= 2.5 uV, 1/f <= 1.0 uV.
- tb7 op fix. Cause (spot runs on the WO-43 c1 fs/125 deck, `/home/mempool/regr/tt/wo52-dbg`): the nodeset did reach the
  subckt (30 nodes, names right). (a) With the 1 MH DC inductors Newton failed at `op` even with the nodeset (an R in their
  place converged directly; with no nodeset the inductor deck converged slowly). (b) The `.noise` analysis repeats the op from a
  fresh start and fell back to transient op even when the `op` before it had converged (also as the first analysis).
  Fix: noiseless 1 GOhm (`noisy=0`) instead of the inductors (pole ~35 Hz, 0.35 % at the 10 kHz loop check); each copy runs
  as two decks, `op` (gated op and lint, no fallback allowed) and `noise`. A transient-op fallback in the noise deck is
  accepted only if gm of every DEVS device matches the op deck within 0.1 % (`noise_op_match`; summary column `nfb`).
  Broken copy of the match check: a 1 % shifted op must not match (in the summary).
- M8 int row is like for like: hand G (pair, sinks, loads) vs the sim thermal of those groups (contrib_pct). The ol M8 row
  stays on the total.
- Broken copies: mrg must REJECT the 390 uV row, the tier-0 direct row and the ol M8 row. msink cannot cross 390 uV (sink share
  ~1/3, +15 % expected); it is now a sensitivity check (rise >= half of sqrt(1 + share) - 1).
- `test_c1_netlist.py`: the 2 failures were stale expectations after D65 (TG output clamp + local rstb inverter):
  dualpath now checks the TG and inverter; device count +3 n / +1 p. New broken copies: clamp_weak, clamp_stuck (dualpath),
  clamp_weak and inverter removed (count). 20 passed on the sandbox.

## Pickup (after POOL_DONE)
```
ssh sandbox; R=/home/mempool/regr/tt/WO-52-bf4a565; cd $R; ls out/logs/POOL_DONE; grep -L "EXIT=0" out/logs/job_*.log
. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R
python design/c1_ota1/c1b_tb7.py --summary out/tb7 > out/tb7_summary.txt
for i in 3 1; do python design/c1_ota1/c1b_gateb.py out/gb/c${i}_nom --combine 6 --copy nom > out/gb/c${i}_nom/combine.out 2>&1; echo EXIT=$? >> out/gb/c${i}_nom/combine.out; done
grep -h VERDICT out/logs/job_*.log out/gb/*/combine.out; find out -name '*.csv' -delete
```
op/AC (jobs 22-30) and tb9 (jobs 31-35, incl. --mut) verdicts are in their job logs. Not yet run: the gate B sr95 broken
copy (WO asked for nominal only); the tb7 docstring header still names the 250/200 uV rows (code constants are current).
