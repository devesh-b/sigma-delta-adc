# WO-27 results (C1b part 2c: D60 recentre, CM error amp, tb9), 2026-11-10 — STOPPED at the item-3 exit

Exploration runs only (tree copy, `regr/tt/WO-27-explore`, tt/27; logs in `explore/`). No frozen copy, no 9-PVT run:
the CM-amp exit fails structurally, so the WO stop rule applies. `gb.sh` is ready but gate B should not run on this netlist.

## Item 3 exit (V_OCM |err| + 3σ ≤ 10 mV): FAILS at tt/27
| copy | V_OCM err | σ (hand, A_VT 12) | err+3σ | A_cm | I_amp |
|---|---|---|---|---|---|
| base | +40.2 mV | 7.63 mV | 63.3 mV | 2.74 | 3.85 µA |
| boost | +1.6 mV | 6.38 mV | 20.7 mV | 3.14 | 7.66 µA |
- σ budget: pair 2.69 mV (1:1); fold-node current error needs σ(Δctl) ≈ 17–18 mV, ÷ A_cm ≈ 6 mV. Passive loop (no amp) σ ≈ 18–19 mV.
- Reaching ≤ 10 mV needs A_cm ≳ 10 (σ) and ≳ 30–50 (base systematic, ≈ 110 mV of Δctl), with the amp pole above f_cm.
  At the 2 × 15/2 m_plc gate load that is ≳ 150 MHz amp GBW, i.e. > 8 µA boost (WO cap). Options: a folded-branch replica
  for the CMFB reference (removes the systematic Δctl), or a slow high-gain integrating path beside the fast passive path.

## Item 2 rows (D60 allotments), tt/27
- σ(I_tail) 3.43 % base / 2.42 % boost (A_VT 12). SR − 3σ: 12.09 < 12.5 (base), 24.87 < 25 (boost). Ceiling + 3σ: 20.81 > 19.98, 40.26 > 39.96 µA. Both FAIL (the D60 +1.9 % covers ≈ 1σ).
- I_vdd tt: 63.4 µA base, 128.6 µA boost (incl. CM amp).

## f_cm / CM PM
- Return-ratio row works on the Cc ÷ 4 copy (3.83 MHz, PM 62.6°, T_dc 78.7 dB → REJECT, good); on the nominal copies it
  found no clean unity crossing (open item, to inspect from the AC data).

## tb9 (tt/27, boost)
- All copies, incl. the WO-26 passive loop (`cm_unity`), show a slow CM drift: at t = 0 (clamps on, SC open) the output
  CM sits at 2.9 V (no CM loop during the clamp), then relaxes at the Cr refresh rate (τ ≈ 1 µs): 1.68 V at 3.8 µs.
  Start-up from 3.3 V / 0 V: 76 / 55 mV off V_OCM at 4 µs (FAIL). The event windows are dominated by this drift, so the
  event numbers are not valid. Testbench fix: start events after convergence. Design fix: clamp the outputs/cms
  consistently during start-up, or a larger Cr.

## Broken copies (op/AC, tt): nc_short, ref_composite (→ ceiling), kp_fixed+ibn105, ibtp90, ibtp112, cc_div4: all REJECTED.
## Tests: test_c1_netlist.py 17 passed (new blind-spot checks each with a failing broken copy).
