# WO-53 result: order 1 with the extra loop delay (D76, REVIEW-C4a M1)

Verdict: **PASS**. Frozen copy `/home/mempool/regr/tt/WO-53-750a2c1` (sandbox); study `model/studies/o1_delay.py`, raw numbers `study.txt`, `o1_delay.json`.

Ideal loop, option B (c1 1/8), u in [-0.9, 0.9] (1207 points), y[n+1] = sign(x1[n]):
- Stability: |x1| peak 0.475 vref = 0.486 V/side at VREF 2.048, identical at N 64/256/1024/4096 (bounded, no growth). No-delay peak 0.237 (0.243 V/side). Order-2 peak 0.61 V/side, so order 1 with the delay is within the OTA1 swing.
- Reason it is bounded: the comparator, not the linear NTF, limits the state; the poles on the unit circle do not give a growing limit cycle here.
- Raw acc1/N max error (no-delay -> delay), resolution bits = log2(1/err):
  N64 2.9e-2 -> 5.6e-2 (5.1 -> 4.2); N256 7.3e-3 -> 1.36e-2 (7.1 -> 6.2); N1024 1.8e-3 -> 3.4e-3 (9.1 -> 8.2); N4096 4.5e-4 -> 8.6e-4 (11.1 -> 10.2).
  Delay costs about 1 bit (error x1.9). INL (endpoint) N4096: 174 -> 308 ppm FSR.
- Corrected reconstruction: u = acc1/N + x1[N]/(c1 N) is exact (1e-16) for the delay loop too, but x1[N] is not observable (the comparator sees x1[N-1] one cycle late). An affine (gain, offset) calibration removes about 40 percent of the max error (N4096 5.0e-4); no on-chip decimator change is recommended.
- Accuracy meets the order-1 role (characterisation only, SPEC 1 / D21): about 10 bits at N 4096.

Impact on C9/RTL: none. The RTL takes y from the comparator pin (DAC = latest capture), so the order-1 bitstream timing is whatever the analog produces; only the golden/model order-1 bitstreams change. acc1/acc2 conventions, den = N unchanged. Order 2 untouched.

Golden: v3.2 adds top-level `o1d_vectors` (72 rows, order 1, delay). v3.1 rows unchanged (legacy order-1 rows kept as the no-delay ideal loop so the v2/v3 subset proofs hold). sha 6ae28d76... (was 04bcce89...), regeneration byte-identical on the sandbox.

Checks (sandbox): 108 tests pass (`model/tests` minus `test_s4_corners.py`, which fails to import in the frozen copy; not from this WO, not investigated). New: `test_order1_delay.py` (independent loop, default unchanged, flag non-vacuous, order 2 unaffected), `test_golden_o1d.py`. Study `--nonvac` (flag ignored) prints REJECT.
