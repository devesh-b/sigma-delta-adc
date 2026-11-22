# env (rtl-verification-engineer)

## Toolchain (WO-34 check 2026-11-11, IIC-OSIC-TOOLS 2026.10 via scripts/iic; re-confirmed WO-38)
- Icarus 14.0 (devel s20260301): primary cocotb sim. Verilator 5.052: lint, fast runs, --coverage.
- cocotb 2.1.0 (2.x API): cocotb.start_soon, Timer(.., unit=), Clock(sig, 20, unit="ns"), runner in
  cocotb_tools.runner (get_runner, get_results), test(test_filter=regex). timeout_unit must be one of
  step/fs/ps/ns/us/ms/sec ("hr" raises at scheduling). Read values via str(h.value) (X/Z safe).
- yosys + sby; ONLY yices-smt2 on PATH (no z3/boolector/bitwuzla): engines `smtbmc yices`, `abc pdr`.
- python3 3.12 in the container (no numpy needed by the bench).
## How to run (never local)
- push: scripts/sync-to-sandbox.sh; freeze: cp -a tt-sd/design/c9_digital/{tb,rtl} + golden/s6_vectors.json to
  /home/mempool/regr/tt/WO-38-<sha>-<x>/ (same relative layout so tb/../../../golden works).
- run: ~/bin/rta-tt 'scripts/iic "cd /foss/designs/regr/WO-38-<sha>-<x>/design/c9_digital/tb && ./run.sh <agree|lint|cocotb|formal|all>"'
  long ones with `~/bin/rta-tt --bg NAME ...`; log /tmp/rt/NAME.log on the box.
- speed: Icarus+cocotb per-clk loop ~8.3k clk/s; a reset at the default config costs 2 slots = 197k clk (~24 s).
- Ref A golden agreement: quick ~7 s, mutant self-test ~2 min (19 mutants).
## Quirks
- TESTS regex is a substring match (s01 also matches d_fs01).
- rta-tt --bg prints the log path; poll with ssh sandbox 'until grep -q "RUN RESULT" /tmp/rt/NAME.log; ...'.
## WO-40 additions (2026-11-12)
- Parallel runs: /home/mempool/tt-sd/scripts/lpool.sh JOBFILE LOGDIR (load-adaptive, <= 6 jobs, POOL_DONE, EXIT= per job).
  Launch: ssh -f sandbox "cd <frozen> && setsid nohup .../lpool.sh <jobs> <abs logdir> >/dev/null 2>&1 &".
  Each job line: cd /home/mempool/tt-sd && scripts/iic "cd /foss/designs/regr/<frozen>/design/c9_digital/tb && ./<job>.sh ARG".
- tb/mutants.py (make/tests/list/formal), mut_job.sh MID (own dir ../mut/MID, stops at first kill),
  mut_formal.sh MID (per-property abc pdr, one assert kept per run, covers dropped), cov_job.sh SEED (Verilator
  --coverage, own dir ../cov/sSEED), gl_job.sh (yosys generic netlist + simcells.v, icarus).
- run_cocotb.py: C9_BUILD_ARGS, C9_RUNDIR (sim cwd, keeps parallel runs apart).
- Local foreground `sleep N; cmd` is blocked by the harness; use run_in_background for waits.
- 2026-11-12: ssh sandbox and git commit signing both go through the 1Password agent; when it fails, both fail.
- WO-42: hand-built lpool lines with nested quotes broke (EXIT=2); put every job in wo42_job.sh instead.
## WO-49B (2026-11-13) frozen /home/mempool/regr/tt/WO-49B-968bd7a-a, job file tb/wo49b_jobs.txt, pool logs ../../../pool
- wo42_job.sh kinds added: `test NAME SEED [TO]`, `suite STEP` (run.sh STEP, out ../wo42/suite_STEP).
- Ref A captures comp at the start edge (CL-28); BFM strict: correct only on the capture clk (C9_COMP_WIN=k widens).
- mutants re-anchored on D72/D74 RTL text (A1/A2 14/25 b, h1/h2 hold regs, comp_in into y_dac); new M57 (1 fs late),
  M57b (1 clk early), W1 (acc1 13 b), W2 (acc2 24 b, equivalent: AMB-25). 65 mutants.
- Mistake log: a stray local `python3 - <<EOF` (empty no-op) ran once; never use python locally even as a fallback.
## WO-58 (2026-11-13) frozen /home/mempool/regr/tt/WO-58-a166371-a (tree a166371 + tb/wo58_jobs.txt; RTL = 346995c D77)
- The container DOES see /home/mempool/regr/tt as /foss/designs/regr (scripts/iic -v line); frozen copies there work.
- Launching lpool with `ssh sandbox "... setsid nohup lpool ... &"` (no -f) keeps the ssh open until the tool times out
  (harmless, pool runs); use `ssh -f` as in WO-40.
- New-file commit needs `git add -- PATH` first; `git commit -- PATH` alone fails on untracked files.
- Mutants re-anchored on D77: A2 = [23:0]; M01 acc2 22 b; W2 acc2 23 b (must REJECT); M04/M54 24'd0; M09 a2n[22:0].
- SOAK rate on Verilator at load ~5: ~2 slots/s (3000 slots = 1478 s). R-01 icarus seed ~34 s.
## WO-60B
- sby: a design file carrying `assert` needs `read_verilog -formal` (else "Can't resolve task name \assert").
- zsh does not word-split $VAR in for loops: generate job files under `bash -c`.
- Full-chip two-copy miter is too big for abc pdr (40 min, no result) and yices BMC (~46 steps / 90 min); use local miter + env property.
## WO-75 (2026-11-14) frozen /home/mempool/regr/tt/WO-75-6e61895-b (jobs tb/wo75_jobs.txt, pool ../../../pool)
- Bench top is now tb/hdl/c9_tb.v (C9_TOP default c9_tb; PW_BITS/BIAS_BITS from C9_PW_BITS/C9_BIAS_BITS, default 4/2).
  GL uses C9_TOP=tt_um_sd_adc_c9 + yosys chparam 4/2. Formal: chparam 3/2 in c9_props.sby and mut_formal.sh.
- wo42_job.sh kinds: real (d_hold01 at 16/8), fmlreal (F18 alone at 16/8, PDR).
- Relative C9_OUT breaks results xml lookup ("no results file"); always absolute.
- Pool launch over ssh -f returned at once; frozen copy -a (2e0a43c) = smoke only.
## WO-83 (2026-11-14) frozen /home/mempool/regr/tt/WO-83-9f4bab2 (bench 9f4bab2, RTL baa0706), jobs tb/wo83_jobs.txt, pool ../../../pool
- Bench params: run_cocotb.py generates C9_OUT/c9_tb_wrap_PW_B.v (RTL tt_um_ with #(PW,B) on u_core); no defparam (Verilator rejects hierarchical defparam).
- wo42_job.sh kinds: `real [TEST]` (16/8), `fmlw PW B PROP [TO]` (props -DF_PW/-DF_B + chparam). gl_job.sh PW B (TESTS, GL_TO env).
- Freeze: cp -a tt-sd/design/c9_digital/{rtl,tb} + tt-sd/golden into WO-83-<sha>/; launch lpool from ssh with setsid nohup ... < /dev/null & (returns at once).
- Wait: one run_in_background ssh loop `until POOL_DONE; sleep 30` (no local sleep).
