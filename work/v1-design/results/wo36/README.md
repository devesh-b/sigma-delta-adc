# WO-36 results (C1: D68 start-up row, new start-up broken copies), 2026-11-11

Frozen copy: `/home/mempool/regr/tt/WO-36-18af22a` (design/, golden/, run.sh, `.spiceinit` num_threads=1, out/tb9).
Commit 18af22a. Launched 12:14 IST: run.sh P = 1 (tb9 0,2 = tt, fs125), 2 (3,4 = ss125, sf125), 3 (0 --mut).
Markers: out/status_{1..3} (EXIT=), out/DONE_{1..3}; VERDICT lines in out/tb9/{nom_02,nom_34,mut}.out; csv deleted.

## Changes
- tb9 check_su (D68): start-up row = ph2 instants within 10 mV of steady state from 3.75 us **and**
  |steady state - V_OCM| <= 10 mV (fail text "start-up abs: ..."). mio must REJECT on the abs term (EXPECT "start-up abs").
- Broken copies mcr05 and mclw dropped. New (su_lo kind, EXPECT "start-up"):
  mcnr = clamp never released (rstb held low, tb token rst_never); mcst = output TG gates tied on (netlist clamp_stuck;
  ctl / bli clamps still release); mclv = output clamp reference at V_OCM + 50 mV (netlist clamp_lv50, released at 2 T).
- Expectation going in (not yet measured): a TG clamp held at the right level is itself a CM source at V_OCM, so mcnr / mcst
  may read in band on a CM-only row; mclv is released at 2 T and the CMFB should pull it back by 4 us. Any of the three
  passing means the CM row cannot see that defect, which is reported as such (not argued away).

## Results
(pending)
