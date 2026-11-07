# Study: settling (input source / reference)

Order 2, N=1024. τ is the sampling/recovery time constant; t_half = 0.45/fs. `shared`: one Cs samples Vin then ±VREF (input sees the previous ±VREF → signal-dependent). `separate`: Cin and Cref reset to CM each cycle. Equivalent R: τ_in over (Cs + 5 pF pad), τ_ref over the 20 pF ref decap. INL includes the quantisation floor (~16 b).

| fs MHz | caps | which | τ/t_half | τ ns | equiv. R | INL ppm | gain err ppm |
|---|---|---|---|---|---|---|---|
| 1 | shared | tau_in | 0.02 | 9 | 1.5 kΩ | 7.2 | -14 |
| 1 | shared | tau_in | 0.05 | 23 | 3.8 kΩ | 7.2 | -14 |
| 1 | shared | tau_in | 0.08 | 36 | 6.0 kΩ | 6.8 | -14 |
| 1 | shared | tau_in | 0.10 | 45 | 7.5 kΩ | 8.0 | -18 |
| 1 | shared | tau_in | 0.15 | 68 | 11.3 kΩ | 6.2 | -26 |
| 1 | shared | tau_in | 0.20 | 90 | 15.0 kΩ | 7.3 | -81 |
| 1 | shared | tau_ref | 0.02 | 9 | 450 Ω | 7.2 | -14 |
| 1 | shared | tau_ref | 0.05 | 23 | 1125 Ω | 7.2 | -14 |
| 1 | shared | tau_ref | 0.08 | 36 | 1800 Ω | 7.2 | -14 |
| 1 | shared | tau_ref | 0.10 | 45 | 2250 Ω | 7.2 | -14 |
| 1 | shared | tau_ref | 0.15 | 68 | 3375 Ω | 8.0 | -18 |
| 1 | shared | tau_ref | 0.20 | 90 | 4500 Ω | 6.9 | -18 |
| 1 | separate | tau_in | 0.02 | 9 | 1.5 kΩ | 7.2 | -14 |
| 1 | separate | tau_in | 0.05 | 23 | 3.8 kΩ | 7.2 | -14 |
| 1 | separate | tau_in | 0.08 | 36 | 6.0 kΩ | 6.6 | -18 |
| 1 | separate | tau_in | 0.10 | 45 | 7.5 kΩ | 6.9 | -60 |
| 1 | separate | tau_in | 0.15 | 68 | 11.3 kΩ | 7.3 | -1286 |
| 1 | separate | tau_in | 0.20 | 90 | 15.0 kΩ | 6.6 | -6751 |
| 1 | separate | tau_ref | 0.02 | 9 | 450 Ω | 7.2 | -14 |
| 1 | separate | tau_ref | 0.05 | 23 | 1125 Ω | 7.2 | -14 |
| 1 | separate | tau_ref | 0.08 | 36 | 1800 Ω | 6.8 | -14 |
| 1 | separate | tau_ref | 0.10 | 45 | 2250 Ω | 6.8 | -14 |
| 1 | separate | tau_ref | 0.15 | 68 | 3375 Ω | 6.9 | 46 |
| 1 | separate | tau_ref | 0.20 | 90 | 4500 Ω | 8.0 | 300 |
| 2 | shared | tau_in | 0.02 | 5 | 0.8 kΩ | 7.2 | -14 |
| 2 | shared | tau_in | 0.05 | 11 | 1.9 kΩ | 7.2 | -14 |
| 2 | shared | tau_in | 0.08 | 18 | 3.0 kΩ | 6.8 | -14 |
| 2 | shared | tau_in | 0.10 | 23 | 3.8 kΩ | 8.0 | -18 |
| 2 | shared | tau_in | 0.15 | 34 | 5.6 kΩ | 6.2 | -26 |
| 2 | shared | tau_in | 0.20 | 45 | 7.5 kΩ | 7.3 | -81 |
| 2 | shared | tau_ref | 0.02 | 5 | 225 Ω | 7.2 | -14 |
| 2 | shared | tau_ref | 0.05 | 11 | 563 Ω | 7.2 | -14 |
| 2 | shared | tau_ref | 0.08 | 18 | 900 Ω | 7.2 | -14 |
| 2 | shared | tau_ref | 0.10 | 23 | 1125 Ω | 7.2 | -14 |
| 2 | shared | tau_ref | 0.15 | 34 | 1688 Ω | 8.0 | -18 |
| 2 | shared | tau_ref | 0.20 | 45 | 2250 Ω | 6.9 | -18 |
| 2 | separate | tau_in | 0.02 | 5 | 0.8 kΩ | 7.2 | -14 |
| 2 | separate | tau_in | 0.05 | 11 | 1.9 kΩ | 7.2 | -14 |
| 2 | separate | tau_in | 0.08 | 18 | 3.0 kΩ | 6.6 | -18 |
| 2 | separate | tau_in | 0.10 | 23 | 3.8 kΩ | 6.9 | -60 |
| 2 | separate | tau_in | 0.15 | 34 | 5.6 kΩ | 7.3 | -1286 |
| 2 | separate | tau_in | 0.20 | 45 | 7.5 kΩ | 6.6 | -6751 |
| 2 | separate | tau_ref | 0.02 | 5 | 225 Ω | 7.2 | -14 |
| 2 | separate | tau_ref | 0.05 | 11 | 563 Ω | 7.2 | -14 |
| 2 | separate | tau_ref | 0.08 | 18 | 900 Ω | 6.8 | -14 |
| 2 | separate | tau_ref | 0.10 | 23 | 1125 Ω | 6.8 | -14 |
| 2 | separate | tau_ref | 0.15 | 34 | 1688 Ω | 6.9 | 46 |
| 2 | separate | tau_ref | 0.20 | 45 | 2250 Ω | 8.0 | 300 |
