# design/tier1 - tier-1 behavioural SC modulator in ngspice (WO-07 / S5)

Independent SPICE implementation of the decided loop (order-2 CIFB, c1 .125 / c2 .5 / k .5, Cs1 .5p/Cint1 4p,
Cs2 .5p/Cint2 1p, separate k-DAC cap 0.25p on full VREF, shared Cs1 for input and DAC). Does not import model/iadc.py.

- `gen_tier1.py` writes the deck from `design/params.py`. Parts: `sw` switches (Ron/Roff), B-source OTA
  (finite A0, one pole for GBW, tanh slew limit, hard output clamp, ideal CMFB), ideal comparator +
  hold-cap latch (forced +1 in reset), 500 ohm + 5 pF pads on VIN+- and VREF+-, 3-cycle reset between conversions.
  Phases: phi1 sample (top plate opens first), phi2 transfer (DAC reference selected by y); Cs2 samples x1 in OTA1's hold phase.
- `tier1_tb.py` runs ngspice and checks: `--null` `--options` `--dc` `--sweep` `--nonvac` (ACCEPT/REJECT, nonzero exit on REJECT;
  `--nonvac` exits 1 when every broken deck was rejected, as the WO specifies).
- Expected values: u_hat = (sum S + (k/c1) S + x2[N]/(c1 c2)) / (N(N-1)/2), x2[N] read from the sim; ideal transfer u_hat = u_in.
- INL: endpoint, ppm of FSR (= 2 in u), like the model. Null tolerance 2e-6 in u.
- Run on the sandbox (nix ngspice 45): `python3 design/tier1/tier1_tb.py --null`; outputs go to `/home/mempool/regr/tt/WO-07`.
- Limits: constant A0 (no swing-dependent gain), one pole, no offsets/noise/charge injection, ideal CMFB. INL here is
  dynamic-settling INL only; the A(v) effect is in the model (S3) and goes to the transistor-level OTA tb.
