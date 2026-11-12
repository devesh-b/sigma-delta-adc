# WO-43 results (C1: D71 sink noise, tb7 fixes), 2026-11-12

Commits: 44a6fa7 (code), 2b6fa35 (gamma decks one device per run, PMOS bias signs).

## Code (items 1 and 2)
- `sizes_draft.sink_variant(z, L, WF, RS, wmult, bnd_wf)`: re-sizes the whole sink family together (m_n, reference m_nr,
  replica m_rn, integrator tail m_it; `SINK_FAMILY`), so the 1:8 ratio, the replica (K_N tracking) and the integrator tail
  current are kept. `bnd_wf` sets the vbnc diode m_bnd (K_N = 8 x 1.25 / bnd_wf: raises the fold node for headroom).
- `netlist.py`: optional source degeneration `RS` on the sink family (resistor per device = RS x M_n / M, the same I.R drop per
  finger). Ideal R in this sweep (no TC / spread); a PDK poly resistor is a follow-up if RS is chosen.
- `c1b_opac.py`: m_n / m_rn margins use the device Vds when RS is on.
- `c1b_tb7.py` (D71):
  - ol copy runs first; its op (every node) becomes the `.nodeset` of the int / lump copies (fixes the transient-op fallback).
    `transient op` stays in the lint, so a fallback still fails op_ok.
  - gamma decks: one device per class (m_in, m_n, m_pl) at the ol vgs / vds, drain held by a source, S_id at 100 MHz ->
    gamma = S_id / (4kT gm). The M8 hand rows use G = gamma_in + (gamma_n gm_n + gamma_p (gm_pl + gm_plc)) / gm_in, +-30 %.
    Smoke at tt (RS 2 kOhm op): gamma pfet_01v8 0.58, nfet_g5v0d10v5 1.31 (the 2/3 hand value explains most of the WO-41 gap).
  - rows: 250 uV SPEC gate plus the D71 200 uV design target (gate); tier-0 DIRECT path is the gate (thermal share <= 1.2 uV,
    joint <= 2.5 uV, flicker <= 1.0 uV); conventional path is info. Info columns: m_n margin, V_fa, span.
  - broken copies: mrg (tt, 65 kOhm) unchanged; msink (fs/125 base, sink family W x 4, same currents) replaces mhalf and must
    REJECT on the thermal rows. --fast drops the lump copy (sweep only).
- Pre-existing: `design/tests/test_c1_netlist.py` has 2 failures (test_dualpath_structure, test_device_count) in the WO-41
  frozen copy too; not caused by WO-43.

## Item 1 sweep (RUNNING)
Frozen copy `/home/mempool/regr/tt/WO-43-2b6fa35-s`, `sweep_jobs.txt` (15 jobs, lpool), launched 23:13 IST.
Corners fs/125 (3), ss/125 (2), tt (0), both modes, --fast. Candidates (out/sweep/cN):
| cand | sink change | note |
|---|---|---|
| c0 | none | baseline with the new tb7 |
| c1 | L 4 -> 8 (W 72) | option A |
| c2 | L 8, m_bnd W 1.25 -> 0.95 (K_N ~10.5) | option A + fold node up |
| c3 | RS 2.5 kOhm (62 mV base), m_bnd 0.95 | option B |
| c4 | L 6, RS 1.5 kOhm, m_bnd 0.95 | A + B |
Markers: `out/sweep_logs/POOL_DONE`, job_N.log (EXIT=). Summary per candidate:
`python design/c1_ota1/c1b_tb7.py --summary out/sweep/cN` (broken copies are not in the sweep).

Hand headroom note (WO-32 op/AC): m_n margin 0.14-0.23 V (row >= 0.05), base span >= 1.735 V (row 1.6), boost hot span
>= 1.481 V (row 1.40). The 200 uV target at fs/125 needs the sink noise power at ~0.40 x today (gm_n / 2.5); a longer L alone
eats the m_n margin, so the fold node has to rise (K_N), which costs boost span. Expect a tight fit.
