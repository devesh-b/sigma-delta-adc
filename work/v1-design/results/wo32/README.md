# WO-32 results (C1b part 3a: D65 rows, SPEC CL-9..11, TG clamp, CM-to-DM bound + mismatch copy, near-knee copy), 2026-11-11

Frozen copy: `/home/mempool/regr/tt/WO-32-df4e30d` (design/, golden/ from WO-31, run.sh, gb.sh, `.spiceinit` num_threads=1
in the root, out/, out/tb9, out/opac and out/gb/*). Commit df4e30d (code, SPEC, DESIGN 2.12, scripts).
Launched 10:47 IST: run.sh chains 1-4 (op/AC 9 PVT; tb9 0,2 / 3,4 / 0 --mut / 0,3 --mm) and gb.sh (fs/125 nom + srknee,
pool = 5 minus the run chains still running). Markers: out/status_{1..4}, out/DONE_{1..4}, out/gb_status, out/gb/*/combine.out,
GB_DONE. Summary: `python design/c1_ota1/c1b_opac.py --summary out/opac`; tb9 VERDICT lines in out/tb9/*.out.

## Items 1-5: done (code and docs)
- SPEC CL-9 (SR floor 10.3 / 20.6 V/us, knee-based), CL-10 (row 98 sampling-instant text), CL-11 (start-up, CM-to-DM).
  Rows 95 and 98 edited; nothing else in SPEC.
- c1b_opac: SR_FLOOR 10.3 / 20.6 V/us (SR - 3 sigma), ceiling unchanged, info rows IREF_win_lo_pct / IREF_win_hi_pct,
  bkt = ibtp x 0.85 (window low edge, K_P tracking), SR broken copy mtlo ibtp90 -> ibtp75 (ibtp90 is inside the new window).
- netlist: output start-up clamp = TG (n W 2 / p W 4, L 0.5, local rstb inverter); tokens clamp_weak, mm3, ibtp85, ibtp75.
- tb9: start-up row at the ph2 instants vs steady state from 3.75 us; mut deck adds mclw (clamp_weak, su_lo) and the
  u-dependent masy pair (masy / masyz); --mm deck: 3 sigma mismatch twins at DM +, 0, -; u-dep row + hand Cc term.
- c1b_gateb: --copy srknee (all six ports x 0.624, 16.5 V/us at 1.4 pF = 0.8 x boost floor).

## Results (11:48 IST)
- **op/AC 9 PVT: VERDICT ACCEPT** in all three groups (TG clamp in the netlist). New SR rows pass everywhere:
  SR - 3 sigma base 12.76-13.22, boost 25.83-26.55 V/us (floors 10.3 / 20.6). Broken copies mtlo (ibtp75: 19.61 < 20.6)
  and mthi (ceiling) REJECTED. bkt (ibtp x 0.85) K_P tracking -0.20 ... -0.34 % (limit 2 %), SR - 3 sigma 10.81-11.23.
- **C6 window (info), nominal lump copies:** I_REF_btp may drop 19.3-22.4 % (floor side) and rise only +1.6 ... +4.9 %
  (ceiling side; tightest ff/125 base +1.58 %, ff/-40 base +1.62 %).
- **tb9 nominal (tt, ss125, fs125, sf125): VERDICT ACCEPT.** New start-up row (ph2 vs steady state, >= 3.75 us):
  suhi / sulo / suvb 0.03-0.21 mV; in band from 2.24-2.74 us. CM-to-DM total 0.004-0.020 uV.
- **tb9 --mm (3 sigma mismatch), tt and fs/125: ACCEPT.** Constant part d_0 0.181 / 0.155 uV (cancels); u-dependent part
  0.012 / 0.031 uV vs 0.256 (8-21x margin; linear 0.012 / 0.029, curvature 0.0005 / 0.002); eps0 6.0e-6 / 5.2e-6; hand Cc
  term 0.022 / 0.019 uV.
- **tb9 --mut: VERDICT REJECT (3), EXIT=1 (stop rule).** mcc4 and masy (u-dep row 0.549 uV) REJECTED. **mio, mcr05 and
  mclw PASS: the D65 start-up row is blind** (0.44-2.8 mV). mio settles to a steady state 119 mV off V_OCM, which a row
  judged against its own steady state cannot see; with the TG clamp, mcr05 (Cr / 2) and mclw are in band by 3.0 us.
- **Gate B (running at 11:48):** fs/125 nominal, all 6 parts done: INL 1.69-2.17 ppm (combine pending). srknee (16.5 V/us at
  1.4 pF): parts 0/1 at 10.65 / 13.50 ppm > 5 (4 parts and the combine pending). Markers out/gb/*/combine.out, GB_DONE.
