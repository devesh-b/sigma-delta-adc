# Island-switch leakage vs temperature (D39c evidence)

Run by the coordinator on the sandbox, 2026-11-08: `ngspice -b design/tier1/decks/leak_temp.sp` (output `/home/mempool/regr/tt/leak/`).

**Setup**
- Device: sky130A `ff` corner, `sky130_fd_pr__nfet_g5v0d10v5`, W 1 µm, L 0.5 µm, diffusion 0.29 µm.
- Bias: gate 0 V, bulk 0 V, held node 1.65 V.
- `.option gmin=1e-18`. The first run used the default gmin (1e-12), which added a flat ≈ 1.65 pA per junction at every temperature. That run was discarded.
- Xj: both terminals on the held node (two junctions, Vds 0).
- Xs: one terminal on the held node, the other at 1.15 V (one junction plus subthreshold).

| T (°C) | Xj (pA) | Xs (pA) | Xs relative to 125 °C |
|---|---|---|---|
| −40 | 3.3e-6 | 1.7e-6 | — |
| 27 | 2.6e-4 | 1.3e-4 | — |
| 85 | 0.313 | 0.156 | 1/42 |
| 100 | 1.39 | 0.694 | **1/9.4** |
| 125 | 13.1 | 6.53 | 1 |

**Reading the result**
- Xs ≈ Xj/2, so the leakage is junction-dominated; subthreshold is negligible at Vgs ≤ −1.15 V.
- The absolute values belong to this device size. The island switches are sized in C4.
- What carries over is the **temperature ratio** (junction physics: same model, same Eg/XTI).
- If the SPEC 100 pA/side at 125 °C is met, the same layout gives ≈ 11 pA at 100 °C.

Drift at 0.25 MHz / N 4096 (I·N/(fs·C_side), C_side 4.76 / 2.01 pF):

| Case | Stage 1 | Stage 2 |
|---|---|---|
| 100 pA, 125 °C | 344 mV | 814 mV |
| ≈ 11 pA, 100 °C | 37 mV | 86 mV |

Both rows at 100 °C are inside the 0.2 V island CM limit.

**Caveats**
- These are model numbers. The sky130 junction leakage temperature fit has not been checked against silicon here.
- The C4 PEX leakage testbench at ff/100/3.6 is the gate (≤ 20 pA per side).
