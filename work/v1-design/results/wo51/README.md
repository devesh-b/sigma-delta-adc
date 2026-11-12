# WO-51 (C3c) results: offset limit (D75), T8 stress fix, T5 asymmetry

Commits: 81c5fe3 (offset limit, testbench changes, SPEC CL-30), c88268b (HV cascode, T8 fix).
Frozen copy: `/home/mempool/regr/tt/WO-51-c88268b` (`c3_comp/`, `.spiceinit` `num_threads=1`). Full run `run/`: 57 decks, lpool launched detached 2026-11-13 04:39 IST, logs `run/pool_logs/`.
Model: `offset_loop.json` (from `design/c3_comp/offset_loop.py`, run in `/home/mempool/regr/tt/WO-51-scratch`).

## Pending: collect when `run/pool_logs/POOL_DONE` exists
    cd /home/mempool/regr/tt/WO-51-c88268b && . /home/mempool/tt-sd/.venv-sbx/bin/activate && python c3_comp/c3_tb.py collect run
Copy `run/summary.txt` here as `summary.txt`. Exit 0 means every nominal row ACCEPTs and every broken copy REJECTs. Rows marked `(i)` are info only.

## Item 1: offset limit (DESIGN.md §3.1b)
- x2 headroom: peak |x2| is ≈ 1.41 V diff for every non-zero |Vos| ≤ 90 mV (flat), 1.435 V at 135 mV, 1.66 V at 200 mV. **Limit: |μ| + 3σ ≤ 60 mV** (2/3 of 90 mV).
- Chop residue: the constant part cancels exactly. Residue ≤ 0.74 ppm FS at N 1024 and ≤ 0.055 ppm at N 4096 for any Vos ≤ 200 mV (the floor of the metric, not Vos-dependent). Under the 1 ppm share.
- WO-48 MC re-judged: tt |μ| + 3σ 44.8 mV, ss/−40 45.0 mV ⇒ ACCEPT on mu3s. The old run clipped at ±40 mV, so the range is now ±200 mV at 0.1 mV (rerun).
- Broken copy: ×3 gives ≈ 62 mV, which sits at the limit, so it is now info only; the gating copy is ×6.
- Dominant device: `sens_tt` (+5 mV VT per device) × `pdk_tt` (σ(Vgs) per type, 60 each), in the summary line "T3 sensitivity".
- C2 finding: the realistic x2 peak is ≈ 1.41 V diff, not 1.21 V, at the edge of the OTA 1.4 V A ≥ 75 dB range.

## Item 2: T8
- Smoke (`WO-51-scratch/smoke`, rev b, no cascode): with x2 at the OTA2 slew (27 V/µs per side) through R_X2/C_X2, moving only in φI, dn still reached **2.351 V** (M4 source-body). The async copy reached 2.350 V. The kick does not depend on edge speed: x2 slew is charge-coupled into the floating dp/dn while the pair device is off, and the R_X2/C_X2 tail still moves x2 into φS.
- Fix applied: an HV cascode (`nfet_g5v0d10v5` 5/0.5 ×4, gate = VDPWR) between each pair drain and dp/dn. The full run shows whether it ACCEPTs; `st_nocas_tt27_a` (info) is rev b on the gate stimulus. Cost: 2 HV devices (≈ 20 µm² gate) and one extra node per side; effect on t_dec, kick and offset is read from the full run.

## Item 3: T5
- Mechanism: CM-to-DM conversion of the ≈ 41 mV CM kick through the per-side x2 impedance: 2·δc·41 mV ≈ 8.2 mV at ±10 %, and unequal τ in recovery (≈ 1.2 mV at 0.5·t_half). Details in DESIGN.md §3.4b.
- Gate is now R ±5 % / C ±1 %, the realistic OTA2 mismatch; ±10 % is an info copy. Smoke (rev b): peak 1.57 / 3.24 mV, recovery 0.40 / 0.38 mV ⇒ ACCEPT, but recovery margin is only 20 %.
- Fix options and costs: DESIGN.md §3.4b (halve the pair; neutralisation pair; a preamp is rejected).
