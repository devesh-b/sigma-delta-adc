# WO-28 results (C1b part 2d: D61 dual-path CMFB, larger tail reference, tb9 start-up fix), 2026-11-10 — BLOCKED before any run

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
