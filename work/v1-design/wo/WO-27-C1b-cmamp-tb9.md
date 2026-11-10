# WO-27 (C1b part 2c): D60 recentre, CM error amplifier in the CMFB loop, tb9, mismatch allotments

Coordinator-written, 2026-11-10. **Tier: design (Opus).** Sources:
- D57–D60;
- `work/v1-design/REVIEW-WO26-2026-11-10.md`;
- `work/v1-design/results/wo26/README.md`;
- `design/c1_ota1/*`;
- SPEC rows 94, 95, 98 and CL-2;
- REVIEW-C1a-revC RC-m2 (the tb9 limit: ≤ 10 mV in 0.2·t_half at 4 MHz boost; start-up from both rails).

**Sandbox:** same rules as WO-26.
- Frozen copy `regr/tt/WO-27-<sha>` with `golden/`.
- **At most 2 of your own processes:** the WO-26 gate B (3 processes, `/home/mempool/regr/tt/WO-26-b177d23`) keeps running; do not touch it.
- Absolute paths, markers, no pgrep loops, delete csv files.

## Items
1. **D60 recentre:** I_REF_btp +1.9 %. Make the mirror-ratio row info-only, so the op/AC verdict is no longer permanently red (M3).
2. **Mismatch allotments (M1, M2):** a hand Pelgrom σ for each critical pair, with A_VT 8–12 mV·µm for g5v0d10v5 because the PDK HV MC has no Vth term. Write it into the rows:
   - SR ≥ floor at nominal − 3σ;
   - ceiling at nominal + 3σ;
   - |V_OCM err| + 3σ ≤ 38 mV (before and after the CM amp).
   Document this in DESIGN.md.
3. **CM error amplifier (D60):**
   - Design a small continuous-time CM error amp inside the SC CMFB loop. Its input is the SC-sensed CM against V_OCM; its output drives the m_plc control.
   - Target: static V_OCM error (systematic + 3σ) ≤ 10 mV, and f_cm ≥ 9.4 MHz in boost with ≥ 45° CM loop phase margin at 9 PVT.
   - Budget a few µA (report it; if it needs more than 4 µA base / 8 µA boost, stop and report).
   - Keep the start-up-only ctl clamp (D57).
   - Broken copy: the amp's gain disabled (unity buffer) ⇒ the V_OCM row REJECTs at ff/125.
4. **tb9 CMFB transient,** boost hot corners and tt: CM step and conversion reset.
   - Exit: CM settles within 10 mV by 0.2·t_half at 4 MHz.
   - Start-up from both rails (outputs pre-charged to VDD and to 0) converges to V_OCM ±10 mV within the CL-7 4 µs.
   - Broken copy: Cc ÷ 4 or amp bandwidth ÷ 4 ⇒ REJECT.
5. **Review minors:**
   - m_rcb to about 0.47 µm;
   - a replica-drain row (V_rnd vs V_fa) and margin rows for m_rn, m_rnc, m_rcb;
   - an ibtp ×0.95 K_P-tracking copy;
   - test_c1_netlist blind spots (m_rcb/m_rcp geometry, Sbkp gate and mbpxs count, source/bulk terminals in refs_ok), each with a failing broken copy.
6. **op/AC rerun** at 9 PVT × 2 × 3 C_L, with all WO-26 exits plus the new rows.
   - Report: I_vdd, f_cm, CM PM, V_OCM error per corner, and boost fp2/GBW and PM.
   - Do NOT launch gate B. The coordinator does that once the WO-26 gate B finishes. Provide a ready `gb.sh` with fs/125, ss/−40, ss/125, tt/27 + sr95 at fs/125 and sf/−40.

## Commits (explicit paths, no trailers, no push)
1. `design: C1 D60 recentre, mismatch allotments, ratio row info-only`
2. `design: C1 CMFB CM error amplifier + tb9`
3. `design: C1b review minors + op/AC rerun (WO-27)`

## Budget
At most 60 tool calls. Report in ≤ 60 lines. If an exit fails, stop and report. Do not add OTA current beyond D60.
