# WO-108: BIAS_EXT topology note (for design review, before any simulation)

Source: `design/cz/c6_cz.py` (wrapper, imports `design/c6_bias/c6_final.py` unchanged). CZ variant only; TT unchanged (bias_sel 0, bias_ext at VSSA).

## Topology
- `c6_cz` ports: c6_bias ports (vdd vss vdl boost trim0..2 ibtp ibn ibp ivbl0 ok) + `bias_ext` (current into the pin) + `bias_sel` (3.3 V = VAPWR domain, static).
- `c6_bias` is instantiated as is. Each of the 4 ports passes through two 3.3 V transmission gates (g5v0d10v5 N 2/0.5 + P 4/0.5): the c6 path (on for sel 0) and the ext path (on for sel 1). `sel_b`/`sel_i` come from two hvl inverters in the VAPWR domain, so no level shifter is needed inside the wrapper.
- Ext path = replica of the C6 mirror side, scaled by K = I_NOM / I_TGT = 5 uA / 1.07 uA = 4.67: cascoded NMOS diode (the VN diode, half 2 behind a boost switch with its own lsbuflv2hv + inv from `boost`), identical sink fingers (ibtp, ibp, ivbl0), the 1-unit ibn feed and the PMOS VP diode with the ibn fingers. The diode input node is the `bias_ext` pin itself.
- Isolated core: runs unchanged, burning its own current (<= 6 uA, SPEC row 104). Its sink ports self-clamp at VGND (the sink drives its own drain down), its ibn port floats to VAPWR. All devices are 5 V class (g5v0d10v5, hvl cells), every pair <= VAPWR (3.6 V) < 4.95 V. The 1.8 V stress rules (D80/D83/D90) bind 1.8 V devices; none is used. A recorded-node rail check is still part of every run (`stress`), with a broken copy (5.2 V node tied to the diode) that must REJECT.

## Assumptions (to confirm in review)
1. bias_ext range 1-20 uA, nominal 5 uA, fixed mirror ratio 1:K (K 4.67): nominal bias_ext gives exactly the C6 design port currents; 1-20 uA scales ports 0.2x to 4x (master 0.21-4.3 uA). No selectable ratio. Boost works in ext mode (half 2 of the ext diode, same switch rule).
2. bias_sel changes only while rst_n is low (D99). Not glitch-safe while running.
3. bias_ok, sel 0: the c6 ok. Sel 1: ext-present detect (a 16-unit mirror leg of the ext diode vs a ~1.9 MOhm xhigh-poly pull-up, 3.3 V inverter); ok = 1 above about 0.5 uA of bias_ext. It does not depend on the C6 core (the fallback case: dead core). Mux = hvl mux2.
4. G3 covers bias_ext open from power-up (gates discharged: ports 0 A, ok low = stated safe state). Open after a good current: the diode gate holds its charge (leakage-limited, ms) and ok stays high until then. A bleeder cannot be added without breaking the 2 % ratio at 1 uA (2 % of the 0.1 uA unit current = 2 nA). Procedure: harness current present before rst_n release; this is an open item.
5. Ratio checks: tracking (p(I)/p(5 uA))/(I/5 uA) - 1 <= 2 % at 1, 2, 10, 20 uA and the repeat; absolute +-3 % at tt/5 uA; port ratios +-3 %; boost/base 2 +-4 %.
6. Corners: tt/27/3.3, ss/-40 at 3.0 and 3.6, ff/125 at 3.0 and 3.6. Broken copies at tt/27/3.3 and ff/125/3.6.

## Gates and broken copies
| Gate | Check | Broken copy (must REJECT) |
|---|---|---|
| G1 | sel 0 wrapper = bare c6_bias within 0.1 % (base, boost), ok high from 140 us | swapsel: c6 path of ibp gated by sel |
| G2 | sel 1 tracking <= 2 %, abs/ratio as above | kwrong (diode x0.9), efinger (one ibp finger missing) |
| G3 | sel 1, open: ok < 0.1 VDD, ports < 20 nA; ok >= 0.9 VDD at 1 and 5 uA | nodetect (ok forced high) |
| G4 | leakage: sel 0, ports held at the worst off-switch Vds, wrapper = bare within 0.1 % | leaky (0.5 % of ibtp to VGND) |
| stress | all recorded nodes within [-0.05, VDD+0.05] | overv |

## Open items
- Ext-open after good current (item 4). Core burning ~own current in ext mode (item 1 of topology).
- Pull-up R (~1.9 MOhm, 670 um xhigh poly) tolerance: ok threshold 0.5 uA nominal, +-30 % tolerance leaves >= 2x margin at 1 uA.
- Layout of the ext replica (K 4.67 on the diode) not done; not in WO scope.
