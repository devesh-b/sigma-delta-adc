# Candidate v1 design point

fs=2 MHz, order 2, N=1024, Cs=1 pF, A0=75 dB at mid-swing (90 % gain loss at full swing), OTA chop + system chop, separate input/ref caps, τ_in=20 ns, τ_ref=10 ns, 3 mV OTA offset, 5 µV chopper residual. `error @0.1·VREF` = mean output error at the test input, dominated by the (calibratable) gain error.

**Static: INL 71.3 ppm FSR, gain error -459 ppm (calibratable), offset 0.0 ppm.**

| MCP3421 rate | our rate | K | rms µV | eff. res. bits | error @0.1·VREF µV | MCP3421 bits |
|---|---|---|---|---|---|---|
| 240 | 244.14 | 8 | 2.51 | 20.6 | -35.7 | 12 |
| 60 | 57.44 | 34 | 1.31 | 21.6 | -35.8 | 14 |
| 15 | 15.02 | 130 | 0.51 | 22.9 | -36.1 | 16 |
| 3.75 | 3.74 | 522 | 0.26 | 23.9 | -36.0 | 18 |
