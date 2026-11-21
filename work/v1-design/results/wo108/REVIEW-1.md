# WO-108 BIAS_EXT: review 1 summary (sd-adc-design-reviewer), verdict GO after the fixes below

Must fix
- M1: bias_sel is a 1.8 V control input; the wrapper had no level shifter. Add lsbuflv2hv_1 + inv_1 as for boost; bench drives bias_sel from a VDPWR source; state the state while VDPWR is absent.
- M2: G4 is blind to ext-side isolation when bias_ext sits at 0 V (no ext current to leak). Run s0/lk with bias_ext at 5 and 20 uA; broken copy "noiso" (one ext TG shorted) must REJECT G1 or G4.
- M3: kwrong is vacuous at ff: the G2 limbs are ratiometric except the tt-only absolute limb. Apply the absolute-current limb at every corner.
Minor
- m1: lost-current case is fail-safe (the diode stack discharges its own gate in ~100 ns to us): gate it, drop the open item.
- m2: xhigh_po +-30 % spread not simulated; no R_UP broken copy; no hysteresis (schmittbuf_1 if cheap).
- m3: no fs/-40; no boost at the range top; no compliance check at 4x/8x through the TGs.
- m4: dead core (no start-up) not exercised with sel 1.
- m5: pin leakage and pad capacitance not modelled.
- m6: no settle time stated after a bias_sel change.
- m7: K 4.67 is not unit fingers.
Efficiency options (later): single-device switches, MOS pull-up for the detect, core header switch.
