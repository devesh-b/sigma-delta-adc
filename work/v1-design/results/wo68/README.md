# WO-68 (C3f): latch Vds, T5 per D81 — C3 NOT closed (T8 needs a decision)

Commit 764fd1c (rev e + T5 checkers + probe). Frozen copies: `/home/mempool/regr/tt/WO-68-d972dda-wt` (probe1, rev d) and `/home/mempool/regr/tt/WO-68-764fd1c` (probe2 + full rerun, launcher `launch.sh`). Probe: `design/c3_comp/probe_latch.py`; it writes no raw data (it deletes the wrdata file). The run in WO-68-764fd1c used a probe version that crashed after its per-device table on the port node `q`. The table and node extremes were already printed. Fixed afterwards.

## Item 1: diagnosis (probe1, st_tt27_a, rev d)
- The node outside 0…VDPWR is the NAND stack node `sb`/`sq`, held at **−0.345 V for 105 ns** (the whole strobe-high phase). At that time qlb/ql = 1.98 V, so Vds(Sb3/Sq3) = 2.32 V. Supply ramp and the x2 −0.5 V step are not the cause.
- When it happens: on every latch flip, and after a set-set glitch (both ob2/nb2 low at the start of regeneration). Example for sb: ql falls while nb2 is low, so Sb3 is off. As ql falls, Sb4 turns off and puts its channel charge on the floating sb. The S/D junction (pw2nd) then clamps sb at −0.345 V. The node stays there until nb2 rises at precharge. This is a functional-mode event, which is why rev b/c show it too.
- Fix (rev e): add a clamp NMOS `S{q,b}5` from each stack node to vss (0.42/0.15), with its gate on the complement of that NAND's set input (ob1/nb1).
  - The clamp is on exactly while the top device is off, so the NAND logic is unchanged.
  - The `noclamp` mutation keeps the rev d latch as a T8 info copy (`st_noclamp_tt27_a`).
- Result (probe2):

  | | sq/sb min | Sq3/Sb3 max Vds | time above 1.98 V |
  |---|---|---|---|
  | rev e, tt27 | −0.056 V | 2.047 / 2.049 V | ≤ 0.65 ns |
  | noclamp | −0.346 V | 2.320 / 2.324 V | 105 / 380 ns |

  ff-40: 2.037 V.

## New finding: the 1.98 V Vds limb has no margin by construction
With the 2.32 V gone, the next worst values are 2.02–2.06 V at the edges, at tt27 and ff-40. They come from Miller/edge overshoot of 1.8 V nodes above VDPWR, and they are in rev d too, hidden under the 2.32 V before.

| Device | Node | Vds |
|---|---|---|
| Bo2n/Bn2n | ob2/nb2 | 2.064 V |
| Oq1n | qo1 | 2.046 V |
| R2/R3 | dp/dn | 2.054 V |
| M3–M6 | op/on/dp | 2.025 V |

- The limit equals the supply maximum (1.98 V), so any overshoot of a digital node above VDPWR, or any undershoot of a node below vss, fails. Also, vdd itself sits a few µV above 1.98 V while the S/D diodes inject current, so on-state inverters read "over" for hundreds of ns at the µV level.
- **The T8 gate decks will therefore still REJECT, at about 2.06 V.** Neither the limit nor the class split was changed (D40/D80, never loosen). This needs a coordinator/user decision. Options:
  - (a) Keep the strict limit and redesign every edge to stay inside the rails. The probe suggests this is not practical for CMOS at 1.98 V.
  - (b) Define the Vds limb on quasi-static Vds (for example a minimum duration). That changes the rule, so it is not mine to make.
  - (c) Judge Vds at a stated overshoot allowance, with a checker copy.

## Item 2: T5 per D81 (in c3_tb.py)
- `one_brk_nohvc` is now `one_info_nohvc`.
- New checker copies:
  - `one_chk_kick1`: the one_fs+125_198 deck judged at a 1 mV kick limit (WO-65 data 1.82 mV, expect REJECT `over:kick`).
  - `one_chk_rec02`: the one_ss40_asym deck judged at a 0.2 mV recovery limit (0.40 mV, expect REJECT `over:rec`).
- `cm_peak_mV` is still reported (about 40–48 mV) for C2.

## Item 3: full rerun — RUNNING
- Rev e changes the subckt of every deck, so all decks rerun with no reuse.
- The run is in `WO-68-764fd1c/run`. WO-56 took about 5.3 h. The pool runs 1 slot at load ≈ 6.
- Expected result: T8 gate rows REJECT on the Vds limb (above). Every other row still has to be confirmed.
- Pickup: wait for `run/pool_logs/POOL_DONE`, then read `run/collect.log`. Check that cyc T1/T2/T7/T10/T10nz ACCEPT with the clamp, that `one_chk_*` REJECT, and the max18ox of `st_*` vs `st_noclamp_tt27_a`. Then copy the summary here as `summary.txt` and delete any csv.
- Reviewer pass: not requested yet, because the exit is not met (T8). Request it on rev e after the T8 decision and the rerun.
