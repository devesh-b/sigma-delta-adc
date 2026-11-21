# WO-108: BIAS_EXT topology note (revision 1, after REVIEW-1.md)

Source: `design/cz/c6_cz.py` (wrapper, imports `design/c6_bias/c6_final.py` unchanged). CZ variant only. c6_cz is not used in the TT netlist: TT uses c6_bias directly (bias_sel 0, bias_ext VSSA is the CZ-pad tie, not a TT wiring).

## Topology
- Ports: c6_bias ports + `bias_ext` (current into the pin) + `bias_sel`.
- **bias_sel is a 1.8 V control input** (VDPWR domain, like boost and trim): lsbuflv2hv_1 + inv_1 inside the wrapper give a 3.3 V `sel_b`, a second inv gives `sel_i`. The bench drives bias_sel from the same VDPWR ramp as vdl. While VDPWR is absent the level-shifter output is undefined, so both transmission-gate sets may be partly on and the port state is undefined; no stress risk (all 5 V devices, every pair <= VAPWR); the harness must hold bias_sel low and keep bias_ext 0 until VDPWR is up.
- `c6_bias` is instantiated unchanged. Each of the 4 ports passes through two 3.3 V transmission gates (g5v0d10v5 N 2/0.5 + P 4/0.5): c6 path (on for sel 0) and ext path (on for sel 1).
- Ext path = replica of the C6 mirror side with **integer K = 5** (m = 5 unit fingers of the VN diode, half 2 behind a boost switch with its own lsbuflv2hv + inv), identical sink fingers (ibtp, ibp, ivbl0), 1-unit ibn feed and PMOS VP diode with the ibn fingers. The diode node is the `bias_ext` pin. Unit current stays 0.535 uA at the nominal input.
- Isolated core keeps running (own current <= 6 uA, SPEC row 104). Its sink ports self-clamp at VGND and its ibn port floats to VAPWR. All devices are 5 V class (g5v0d10v5, hvl cells), every pair <= VAPWR (3.6 V) < 4.95 V; D80/D83/D90 bind 1.8 V devices, none is used. A rail check on recorded nodes runs in every case (`stress`), with a broken copy (5.2 V node on the diode).

## Assumptions and coordinator decisions (CZ-only)
1. Control inputs (bias_sel, boost, trim) are 1.8 V.
2. Nominal bias_ext = K x I_TGT = 5 x 1.07 = **5.35 uA** gives the C6 design port currents. Fixed ratio, no selectable ratio.
3. **Gated bias_ext range 2.5-10 uA** (0.5x to 2x the OTA bias), because the OTAs are verified only at 1x and 2x. 1 uA, 20 uA, boost at 10 uA and port headroom at 10/20 uA are info rows. Boost in ext mode is gated only at 5.35 uA.
4. The harness current's off state is unknown: both open (current source 0 plus 5 nA pin leakage into the pin and 10 pF pad capacitance, kind s1) and a hard 0 V (kind s1z) are tested. The harness current may be left on while bias_sel = 0 (kinds s0e5/s0e20/lke5/lke20, 5.35 and 20 uA).
5. bias_sel changes only while rst_n is low, and the wrapper needs **>= 10 us settle with rst_n low** after a bias_sel change before bias_ok is used (m6).
6. bias_ok: sel 0 = c6 ok. sel 1 = ext-present detect: a 16-unit mirror leg of the ext diode vs a ~0.87 MOhm xhigh-poly pull-up, schmittbuf_1 + inv; ok = 1 above about 1.2 uA (resistor +-30 % gives about 0.9-1.7 uA, below the 2.5 uA gated minimum; the R_UP/4 broken copy moves it above). Independent of the C6 core (dead-core case, variant nosu).
7. Lost current is fail-safe (the diode stack discharges its own gate): gated as "ok < 0.1 VDD and ports < 20 nA 60 us after the current is removed", with pin leakage and pad capacitance in place.
8. Absolute-current limb of G2 at every corner: +-3 % at tt, +-4 % elsewhere. Resistor corners ff_ll/125/3.6 and ss_hh/-40/3.0 on s1 for the detect. fs/-40/3.0 added to s1.
9. Corners: tt/27/3.3, ss/-40 at 3.0 and 3.6, ff/125 at 3.0 and 3.6 (+ fs, ff_ll, ss_hh on s1). Broken copies at tt/27/3.3 and ff/125/3.6 (rupq: tt and ss_hh/-40/3.0).

## Gates and broken copies
| Gate | Check | Broken copy (must REJECT) |
|---|---|---|
| G1 | sel 0, bias_ext 0 / 5.35 / 20 uA: wrapper = bare c6_bias within 0.1 % (base, boost), ok high | swapsel; noiso (ext TG of ivbl0 shorted, kind s0e5) |
| G2 | sel 1, 2.5-10 uA tracking <= 2 %, ratios, boost, absolute at every corner | kwrong (diode x0.9), efinger |
| G3 | sel 1: open from power-up, ok high at 2.5/5.35 uA, lost current | nodetect; rupq (R_UP/4) |
| G4 | sel 0, ports held at the worst off-switch Vds, bias_ext 0 / 5.35 / 20 uA | leaky; noiso (kind lke20) |
| stress | recorded nodes within [-0.05, VDD+0.05] | overv |
Variant that must ACCEPT: nosu (core without start-up kick, sel 1). Compliance at the range top is the tracking at 10 uA through the TGs; port voltages at 10 and 20 uA are reported.

## Later options (not done)
Single-device switches, PMOS pull-up for the detect, core header switch (turn the isolated core off), layout of the ext replica.
