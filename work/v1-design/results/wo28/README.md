# WO-28 results (C1b part 2d: D61 dual-path CMFB, larger tail reference, tb9 start-up fix), 2026-11-10 (run 1 blocked; run 2 below)

The sandbox was unreachable for the whole session: `ssh sandbox` fails with "sign_and_send_pubkey: signing failed ...
communication with agent failed" (1Password SSH agent locked). Nothing was simulated; no frozen copy exists; the
numbers below are hand estimates only. The code for every item is in the working tree and ready to run.

## What changed (working tree, uncommitted)
- `design/c1_ota1/sizes_draft.py`: WO-27 CM amp removed; INTEG / m_ia (W 5 L 14) / m_il (W 6 L 16) / m_it (1 m_n
  finger) / C_INT 2 pF / BLI_RST / OUT_RST / REPLICA_DV_MAX; tail unit finger 1.25/2 → 3.75/6 (m_tr, m_rt derived).
- `design/c1_ota1/netlist.py`: dual-path CMFB (DESIGN.md 1.3b), start-up clamps ctl/bli → ivbl0, outputs → vocm;
  dc model = averaged Cr as B current sources into ctl / out of bli; tokens int_off, vbl0x2; cm_open keeps the ctl load
  with a dummy m_plc pair. cm_unity / cmbw4 / cms removed.
- `design/c1_ota1/c1b_opac.py`: integrator rows (A_int, f_z ≤ f_cm/10, margins mit/mia1/mia2/mil2), dual-path V_OCM σ,
  CM peaking ≤ 1 dB, replica rows (|V_rnd − V_fa| ≤ 0.15 V, margins m_rn/m_rnc/m_rcb), `fcm_hand` behavioural
  validation of the return ratio (runs in the deck list containing tt/27), ff/125 broken copy int_off ⇒ V_OCM.
- `design/c1_ota1/c1b_tb9.py`: events from 1.5 µs; copy suvb (ivbl0 ×2); broken copies cc_div4 (events) and
  int_off+vbl0x2 (start-up).
- `design/tests/test_c1_netlist.py`: dual-path structure / broken copies, dc averaging, tail-area check, device counts.
- `design/c1_ota1/DESIGN.md` 1.3b; `results/wo28/gb.sh` (not launched).

## Hand estimates (to be replaced by the runs)
- σ(I_tail) ÷ 3 (area ×9): 1.14 % base / 0.81 % boost. With the WO-27 tt currents: SR − 3σ 13.02 / 26.17 V/µs,
  ceiling + 3σ 19.52 / 38.46 µA (limits 19.98 / 39.96). Risk: L 6 changes the systematic m_t/m_tr ratio the D60 +1.9 %
  was set for; if the ratio moves to ≈ 1.00 the base ceiling margin drops to ≈ 0.1 µA.
- V_OCM σ ≈ 2.2 mV (3σ ≈ 6.5 mV). Added current 0.78 / 1.56 µA; CM amp removed (−3.85 / −7.66 µA).
- f_cm: not measured. The WO-26 passive loop was ≈ 8 MHz (< 9.4) and m_ia adds ctl load, so the boost f_cm exit is
  expected to fail with Cc 0.1 pF; the D58 lever (Cc 0.3–0.4 pF or CMFB split) needs a coordinator/user decision.

## Pickup (sandbox)
1. `scripts/sync-to-sandbox.sh`; frozen copy `regr/tt/WO-28-<date>-1` (design/ + golden/), record `git diff --stat`.
2. `pytest -q design/tests/test_c1_netlist.py`.
3. `python design/c1_ota1/c1b_opac.py <abs out> 0` first (fcm_hand rows, tt nominal + mutants), then 1..8 in 2 procs.
4. `python design/c1_ota1/c1b_tb9.py <abs out> 0,2,3,4` and `... 0 --mut`.

## Run 2 (2026-11-10): testbench fixes, tt op/AC, tb9, 9 PVT

Frozen copies: `/home/mempool/regr/tt/WO-28-c6bef6d` (tt op/AC split + `--merged-open` broken copy, tb9 0,2,3,4 and
`--mut`), `/home/mempool/regr/tt/WO-28-48a0773` (PM fix, op/AC 9 PVT, `--summary`).

### Bug 1: dead cm_open helpers (cause found, fixed, proven)
- Cause: not shared nets. The run-1 nominal deck (8 closed + 6 cm_open copies) did not converge in Newton, dynamic gmin,
  true gmin or source stepping; ngspice silently fell back to "Transient op". A transient op leaves the huge caps at their
  initial charge: the cm_open break (1 GOhm / 1 F) kept ctlg at 0 V (V_ctlg - V_ctl = -3.93 V, m_plc fully on, V_OCM
  error +1.76 V), and the closed copies were not at a DC point either (+6.9 mV instead of +0.3 mV). The mutant deck
  converged with dynamic gmin, which is why mcc4o worked.
- Fix (`c1b_opac.py`, c6bef6d): cm_open helpers run in their own decks (one per mode); "transient op" is now lint
  (fails every row of that deck); new rows: loop break |V_ctlg - V_ctl| <= 1 mV on every helper, and helper op = closed op
  (|dV_ctl| <= 1 mV, |dV_OCM| <= 0.1 mV) before any f_cm row is computed; f_cm pairs may span decks (same AC grid checked).
- Proof (tt): split decks converge without transient op; helper dV_ctl 0 / 0.001 mV, dV_OCM 0, loop break 0 mV; nominal
  V_OCM +0.312 mV base / +0.395 mV boost, equal to the mutant-deck boost copy mcc4 (+0.395 mV, same DC circuit).
  Broken copy `--merged-open` (run-1 structure) REJECTs: lint "Transient op" on all rows, "f_cm helper invalid" (dV 1.7 V).
- PM fix (48a0773): with the dual path T ~ 1/s^2 below f_z (phase near -180 at 1 Hz, sign ambiguous), so the sweep-wide
  unwrap gave PM_cm = 447 deg. PM now = 180 - lag at the crossing; fcm_hand still matches (69.55 / 84.35 deg).
### Bug 2: `mrnc margin nan` / `NaN V_rnd`
- ivbpc is a subckt port, so `v(x<copy>.ivbpc)` does not exist: now the top-level `v(ivbpc_<copy>)`. V_rnd is only read
  when the replica exists (not kp_fixed). Port names removed from the internal-node print list. mrnc now 0.59–1.80 V at every corner.
### Op convergence at cold corners (open item)
- With the split, ff/-40 (nominal + base-open decks) and sf/-40 still fell back to transient op; the new lint and helper
  rows caught it (base f_cm rows invalid there). beea236 (ctl/bli nodeset, itl1 500) fixed sf/-40 but sent the tt mutant
  deck into transient op (all tt mutants INVALID), so it was reverted. Robust fix still to do: one closed copy + its
  cm_open twin per deck (small decks converged everywhere they were tried), or a DC-exact break (inductor) instead of 1 F.

### op/AC 9 PVT x 2 (48a0773; sf/-40 base from beea236). lump copy unless noted; f_cm integ/hold/lump in MHz
| corner | mode | f_cm i/h/l | CM PM min | peak dB | f_z MHz | V_OCM sys/3σ mV | SR / −3σ V/µs | I_tail+3σ µA | A0 dB | I_vdd µA | integ fp2/GBW, PM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tt/27 | B | 3.95/3.44/2.10 | 81.5 | 0.28 | 0.373 | 0.31/7.25 | 13.45/13.00 | 19.47 | 86.0 | 60.9 | 1.79, 64.6 |
| tt/27 | F | 5.79/5.01/3.10 | 82.4 | 0.35 | 0.554 | 0.40/7.24 | 26.85/26.22 | 38.48 | 83.5 | 123.0 | 1.45, 59.7 |
| ss/-40 | B | 4.24/3.73/2.30 | 80.4 | 0.26 | 0.434 | 0.23/7.09 | 13.25/12.76 | 19.24 | 87.3 | 60.5 | 1.35, 57.9 |
| ss/-40 | F | 6.18/5.38/3.34 | 81.7 | 0.33 | 0.636 | 0.29/7.09 | 26.53/25.84 | 38.11 | 84.4 | 122.2 | 1.03, 50.5 |
| ss/125 | B | 3.26/2.84/1.76 | 81.7 | 0.31 | 0.278 | 0.42/7.61 | 13.44/13.06 | 19.34 | 84.8 | 61.4 | 1.66, 62.9 |
| ss/125 | F | 4.81/4.17/2.61 | 82.5 | 0.38 | 0.411 | 0.55/7.63 | 26.82/26.29 | 38.28 | 82.0 | 123.6 | 1.23, 55.4 |
| fs/125 | B | 3.68/3.17/1.93 | 83.4 | 0.28 | 0.279 | 0.44/7.83 | 13.50/13.08 | 19.48 | 84.1 | 61.6 | 2.00, 66.9 |
| fs/125 | F | 5.50/4.74/2.94 | 83.4 | 0.34 | 0.412 | 0.56/7.84 | 26.92/26.33 | 38.50 | 80.7 | 123.9 | 1.44, 59.4 |
| sf/125 | B | 3.20/2.80/1.75 | 80.2 | 0.32 | 0.298 | 0.41/7.46 | 13.43/13.05 | 19.32 | 84.4 | 61.2 | 1.61, 62.2 |
| sf/125 | F | 4.71/4.08/2.54 | 81.9 | 0.40 | 0.446 | 0.54/7.47 | 26.80/26.28 | 38.25 | 82.0 | 123.4 | 1.34, 57.6 |
| ff/-40 | B | invalid (transient op) | – | – | 0.487 | (−0.59/7.42) | 13.51/12.97 | 19.66 | 86.5 | 60.6 | 1.67, 63.0 |
| ff/-40 | F | 6.88/5.95/3.63 (deck lint) | 82.3 | 0.31 | 0.724 | 0.27/7.04 | 26.94/26.17 | 38.78 | 83.5 | 122.5 | 1.41, 59.0 |
| ff/125 | B | 3.60/3.11/1.88 | 82.6 | 0.30 | 0.306 | 0.42/7.61 | 13.64/13.22 | 19.67 | 84.8 | 61.4 | 2.08, 67.8 |
| ff/125 | F | 5.41/4.66/2.87 | 83.1 | 0.36 | 0.457 | 0.52/7.60 | 27.14/26.55 | 38.81 | 82.1 | 123.9 | 1.73, 63.8 |
| fs/-40 | B | 4.79/4.16/2.50 | 82.9 | 0.24 | 0.437 | 0.25/7.24 | 13.31/12.78 | 19.38 | 86.6 | 60.8 | 1.57, 61.7 |
| fs/-40 | F | 6.97/6.02/3.70 | 83.0 | 0.30 | 0.641 | 0.30/7.24 | 26.63/25.87 | 38.34 | 82.7 | 122.7 | 1.19, 54.5 |
| sf/-40 | B | 4.14/3.66/2.30 | 78.0 | 0.27 | 0.468 | 0.23/6.97 | 13.24/12.76 | 19.22 | 85.6 | 60.1 | 1.46, 59.9 |
| sf/-40 | F | 6.09/5.33/3.30 | 80.1 | 0.34 | 0.695 | 0.28/6.97 | 26.52/25.83 | 38.09 | 83.3 | 121.8 | 1.18, 54.4 |
- Pass everywhere (valid rows): V_OCM ≤ 7.84 mV (10), CM PM ≥ 78°, peaking ≤ 0.40 dB, SR−3σ ≥ 12.76 / 25.83, ceiling,
  A0 ≥ 84.1 dB base, margins incl. mrnc. Ratio summary: info only (boost ratio_bl0 spread 2.35 %).
- **Fail: boost f_cm 4.71–6.97 MHz (integ) / 4.08–6.02 (hold) < 9.4 at every corner (worst sf/125, ×2.0 short).** STOP
  per WO-28/D58: options are Cc 0.3–0.4 pF (Cc÷4 moved f_cm only 5.79 → 2.46 MHz, so ×3–4 Cc may not reach ×2) or a
  CMFB split; user decision. f_z ≤ f_cm/10 also fails at the base lump/hold loads (f_z 0.28–0.49 MHz, f_cm 1.75–4.8).
- bkt = K_P-tracking helper with the tail reference port at ×0.95 (ibtp95). It is judged on K_P tracking only (−0.08 to
  −0.13 %, pass); its SR row is info and stacks a −5 % reference error on −3σ mismatch. Not a design miss by the rows,
  but nominal base SR−3σ is only +2.1 % above 12.5 at ss/-40 and sf/-40, so a C6 tail-reference error worse than ≈ −2 %
  would miss SPEC row 95: C6 accuracy needs a budget line.
- Broken copies (tt, ff/125 at 48a0773): mutnc, mutrc, mkp5, mtlo, mthi, mcc4, mvo all REJECTED (good);
  `--merged-open` REJECTs (above).

### tb9 (c6bef6d, boost, idx 0,2,3,4; `--mut` at tt)
- Event rows FAIL at all four corners: the SC transient settles the CM at +129…+167 mV (tt) and +34…+42 mV (hot) above
  V_OCM, while the averaged op gives +0.3…+0.6 mV; errors after 0.2·t_half up to 336 mV (reset release 2). CM step itself
  settles (5.2–7.5 mV). The SC loop and its dc model disagree, or the slow path has not converged by 1.5 µs: next to check.
- Start-up: suhi passes (5.0–6.6 mV), sulo FAILS (34.0 / 21.3 / 14.1 / 27.5 mV at 4 µs), suvb passes except fs/125 (10.28).
- Broken copies: mcc4 (Cc÷4) REJECTED and mio (int_off+vbl0x2, start-up 136 mV) REJECTED, but mcc4 fails the same event
  rows as the nominal, so the event check does not discriminate yet.
