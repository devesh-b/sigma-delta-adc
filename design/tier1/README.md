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
- Limits (WO-07 deck): constant A0 (no swing-dependent gain), one pole, no offsets/noise/charge injection, ideal CMFB. INL here is
  dynamic-settling INL only; the A(v) effect is in the model (S3) and goes to the transistor-level OTA tb.

## WO-08 (S5b) extensions (all off by default; the WO-07 deck is unchanged)
- `ota="v2"`: gm (diff tanh, tail-current slew, `sr_asym` option) into per-side output nodes with Cpar, Ro and an A(v) conductance. The loaded C_L is
  1.4 pF (OTA1) / 0.7 pF (OTA2) *including* the feedback network, so gm = 2 pi GBW C_L and diff SR = I_tail / C_L. Virtual-ground parasitic 0.262 pF per side
  (beta 0.84). Second pole = 3 x GBW on the gm control path (PM about 74 deg at beta 0.84). CMFB: DC loop gain 40 dB, unity-gain 10 MHz, first order,
  acts on the output CM only. `boost=True` doubles gm and tail current (D31 fast mode: spec GBW 10 / SR 12 becomes 20 / 24).
- **Static A(v) table C1 must deliver** (static vo_diff/vd_diff, not incremental): A = A0*max(0.02, 1 - 0.9*(vo/2.0 V)^2), A0 80 dB:
  0 V 80.0 dB, 0.4 V 79.7, 0.8 V 78.7, 1.2 V 76.6, 1.4 V 75.0, 1.6 V 72.6, 2.0 V 60.0 (the incremental gain is up to 3x lower; do not hand in dA/dv).
- Real references (vrefp_v 2.048, vrefn_v 0), `vin_cm`, `d12` (top plates shorted during sampling instead of tied to cm), `dem` (Cs1 +/- role swap each cycle),
  `cs1_mm` (Cs1 mismatch), offsets `vos1 vos2 vcmp`, ideal OTA chop `chop` (offset sign alternates, phase restarts each reset: nrst+n even), `noise1` (trnoise, per cycle),
  `rsrc cext` (source R and pin cap), `late` (input swap one cycle late).
- Modes: `--xcheck --av --knees2 --cm --offsets --rsrc --nonvac2`. Outputs in `/home/mempool/regr/tt/WO-08`.

## SPICE_OPTIONS_TIER1 scope and per-tier requalification rule
`params.SPICE_OPTIONS_TIER1` was qualified on this linear deck only (behavioural parts, ideal `sw` switches). It must NOT be reused as-is at tier 2.
Tier 2 (transistor switches / OTA) requalifies it with a null test using the transistor switches, over reltol {1e-3, 1e-4, 1e-5} x chgtol {1e-14, 1e-16}:
the INL change between settings must stay below 0.1 x the INL budget (0.8 ppm of the 8 ppm OTA line, 2 ppm of 20), and the tightest setting becomes the tier-2 default if the loosest differs.
