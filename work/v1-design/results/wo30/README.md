# WO-30 results (C1b part 2f: tb9 on the D63 basis, open tb9 items, gate B), 2026-11-10

Frozen copies: `/home/mempool/regr/tt/WO-30-8de9624` (run 1: D63 rows, 4 corners, mut, ripple diag),
`/home/mempool/regr/tt/WO-30-6ee1e9d` (run 2: island-side masy broken copy, Cr x 2 candidate; gb.sh ready, not launched).
Commits: 8de9624 (tb9 D63 rows, cr_x2 token, run.sh), 6ee1e9d (masy on the island, TB9_SET=cr2, run2.sh, gb.sh),
plus this README / DESIGN.md.

## Item 1: tb9 rows (definitions in `design/c1_ota1/c1b_tb9.py` docstring)
- Sampling instants: end of each half-phase (ph1 integrate, ph2 hold where Cs2 samples x1), 0.5 ns before the edge.
  Event rows judged from the end of the first ph1 that starts after the event to the next event,
  |CM(t_k) - CM_ss(phase)| <= 10 mV (CM_ss = settled per-phase CM at the end of the run). 22.5 ns value kept as info.
- Static rows: |CM_ss(ph2) - V_OCM| <= 10 mV; |CM_ss(ph1) - V_OCM| <= 28 mV (CL-2 38 mV - 10 mV op/AC allotment).
- CM-to-DM row: twin copies in one deck (ev with the CM step, ev0 without), dDM at the ph2 ends after the CM step.
  Bound from the S-model (model/iadc.py): x1 is in VREF units and u_hat weights a one-sample x1 error by (N-k)/W
  (sum 1 if it recurs every sample), so a per-sample error d [V diff] is an input error d/(c1 VREF); INL in ppm of
  FSR 2 gives INL = d/(2 c1 VREF). Limit 0.1 x 5 ppm (OTA1 boost INL gate) => d <= 0.256 uV (worst case: CM step
  recurring every cycle, fully signal-dependent). Floor = twin difference before the step (0.0 uV).
- Diff step = real worst per-cycle step c1 (u_max + 1) VREF = 0.486 V (loop bound; the 0.8 V step overstated the charge
  1.65x and was still slewing at 22.5 ns; the sampling-instant rule already excludes slewing).
- Events moved to 3.0 us (Cc charge mode tau ~ 1.1 us after the 2 T clamp release), run 5.5 us.

### Per-corner tb9 (boost, nominal, run 1; mV unless noted; worst sampling-instant error per event)
| corner | reset rel | diff step | CM step | reset assert | reset rel 2 | CM_ss ph1 / ph2 | CM-to-DM uV | suhi / sulo (8 T) | suvb (8 T) |
|---|---|---|---|---|---|---|---|---|---|
| tt/27 | 4.07 | 2.51 | 2.07 | 5.70 | 0.11 | -11.5 / 1.3 | 0.009 | 3.7 / 5.5 | **74.2** |
| ss/125 | 3.37 | 2.47 | 2.04 | 5.17 | 0.20 | -10.6 / 1.6 | 0.024 | 4.6 / 7.2 | **97.0** |
| fs/125 | 3.37 | 1.94 | 1.80 | 5.45 | 0.36 | -12.8 / 2.3 | 0.020 | 7.2 / 8.1 | **75.3** |
| sf/125 | 3.38 | 3.37 | 2.17 | 5.87 | 0.16 | -10.3 / 1.5 | 0.006 | 3.8 / 7.1 | **96.5** |
Info (22.5 ns metric): diff step 34-54, CM step 12.7-16.4, reset assert 4.8-9.8.
Start-up info copies (2 T clamp): sulo2t 14.2-34.0 (fail), suvb2t 5.8-10.2, sulocr2 (Cr x 2) 6.9-9.6 mV.
suvb (8 T) at release + 3.5 us (5.25-5.5 us): 11.1-14.2 mV (still fails); suhi/sulo there 4.5-6.8 mV.

### Broken copies (tt)
- mcc4 (Cc / 4): REJECTED: static ph1 -41.9 mV (> 28), reset release 12.7, reset assert 25.3 (nominal 4.1 / 5.7).
- masy run 1 (1e-4 n/p imbalance of the output CM charge): PASSED (0.01 uV) - the check was blind to it, because the
  DM output is set by the island charge and output-side charge settles out. Moved to the island (run 2, below).
- mio (int_off + vbl0x2): REJECTED, start-up 157.9 mV.

## Item 2: open tb9 items
- Reset assert 25 mV at hot (WO-29): a transient 22.5 ns after the output short collapses the DM. At the sampling
  instant it is 5.2-5.9 mV at all four corners (pass). Closed by the D63 rule; no design change.
- End-ph1 ripple (~12 mV): CMFB TG charge packet on `ctl`, divided by 2 Cc. Evidence: ph1 offset scales 1/Cc
  (-11.5 mV nominal, -41.9 mV at Cc / 4, i.e. ~2.3 fC); diag (in reset, 2.5-3.0 us, tt / fs125): nominal ph1-ph2
  4.2 / 5.4 mV, all CMFB TGs ideal 0.35 / 0.11 mV, only Sr2b (ctl-side share switch) ideal 1.6 / 0.5 mV (but the static
  CM moves by -31 mV, so Sr2b's packet is also part of the DC balance). Bounded: ph1 is not where x1 is sampled; the
  ph1 static row (headroom, <= 28 mV) passes at 10.3-12.8 mV, ph2 static 1.3-2.3 mV. Fix options if wanted: Cc up
  (D63 fallback), Sr2b n/p re-balance or a half-size dummy.
- sulo start-up: diagnosed. With the 2 T clamp the output clamp (PMOS W 4) has only pulled the outputs to ~0.9 V at
  release, so Cc carries a ~0.6 V charge error; the Cc charge mode decays only via the Cr refresh (measured 0.79 per
  cycle = Cc/(Cc + Cr), tau ~ 1.1 us) and the slow path does not act on it. 8 T clamp (D57: clamp held while bias
  invalid) fixes sulo/suhi (3.7-8.1 mV), but suvb (V_BL0 x2) then fails (74-97 mV at 4 us, 11-14 mV even 3.5 us after
  release). Not closed within the rules -> options below.

## Run 2 (WO-30-6ee1e9d)
- masy (1e-4 of the CM-step charge onto one island): **REJECTED (good)**, CM-to-DM 0.550 uV > 0.256 uV (nominal
  0.006-0.024 uV); mcc4 and mio REJECTED as in run 1. Mut deck VERDICT ACCEPT.
- Cr x 2 candidate (TB9_SET=cr2, 2 T clamp, every copy), VERDICT ACCEPT at tt/27, ss/125, fs/125, sf/125:
  events 0.05-4.9 mV, CM_ss ph1 -10.9...-13.7 / ph2 0.9-1.6 mV, CM-to-DM 0.006-0.019 uV,
  start-up suhi / sulo / suvb 7.5-9.3 / 6.9-9.5 / 7.4-9.2 mV (fs/125 margin ~0.5 mV).

## Options for the start-up row (coordinator call; none adopted)
1. Cr 0.025 -> 0.05 pF per side (cap only, no current): tb9 passes at 4 corners with the 2 T clamp. Needs the op/AC
   9 PVT rerun (the dc model R = 1/(2 fs Cr) halves: CM PM, peaking, V_OCM rows) and gate B on that netlist. Margin
   at fs/125 is thin (9.5 mV).
2. 8 T clamp (C9/C6 sequencer line, no circuit change): fixes sulo/suhi, breaks suvb unless the start-up window is
   counted from clamp release and lengthened (> 3.5 us); a criterion change.
3. Larger output clamp PMOS (switch size, beyond caps): not simulated.
4. Combine 1 + 2 for margin.

## Item 3: gate B NOT launched
Items 1-2 do not all pass on the current netlist (start-up row). `gb.sh` (WO-29 logic unchanged) sits in
`/home/mempool/regr/tt/WO-30-6ee1e9d/gb.sh`; launch with `setsid nohup bash gb.sh` after the start-up decision (if
option 1 is taken, refreeze with the new Cr first). Markers: out/gb_status, out/gb/*/combine.out (EXIT=), GB_DONE.
