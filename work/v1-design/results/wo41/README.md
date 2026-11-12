# WO-41 results: OTA1 noise (tb7), 9 PVT × 2 modes (frozen copy WO-41-b86c69a, lpool 10 jobs)

Full output: `summary.txt`. Coordinator summary, 2026-11-12:
- **Thermal at the virtual ground (gate ≤ 250 µV rms):** 160–241.5 µV.
  - Worst: fs/125 base, 241.5 µV, 3.4 % margin.
  - Hand estimate (M8) is 27–35 % low at every corner; the HV sink noise is under-counted.
- **Contributors (tt base, thermal power):**
  - NMOS sinks m_n 53.8 %;
  - loads 14.5 %;
  - input pair 14.5 %;
  - NMOS cascodes 8.6 %;
  - PMOS cascodes 5.1 %;
  - switches 3.4 %;
  - CMFB ≈ 0.
- **1/f:** fc 17–61 kHz (info row ≤ 631 kHz OK); flicker at vg 14–20 µV.
- **Chopper residue (hand bound):** constant 0.20 mV (≤ 1 mV), signal-dependent 0.25 µV (≤ 1 µV). Broken copies (one-sided switch, A0 41 dB) REJECT.
- **Tier-0 at 15 SPS (block share 1.2 µV thermal, 1.0 µV 1/f; total ≤ 2.5 µV):**
  - conventional path (S3 noise-gain scaling): thermal 1.45–2.65 µV, **over the 1.2 share**; joint 1.54–2.70 µV;
  - direct path (sampled v_vg into ktc_excess): thermal 0.52–0.71 µV; joint 0.75–0.92 µV, inside.
  - 1/f contribution 0.10–0.16 µV.
- **VERDICT REJECT at every corner.** The causes are not the thermal gate (which passes):
  - (a) the integration-phase copy fell back to "transient op" at most corners (op_ok False);
  - (b) the M8 hand row is off by 27–35 %;
  - (c) the conventional tier-0 path is over the share.
- **Broken copies:**
  - mrg (65 kΩ series R) REJECTED at 542 µV.
  - mhalf (input pair W/2) gives 210 µV, about the same as nominal (200 µV), because the sinks dominate. As a broken copy it is weak.
