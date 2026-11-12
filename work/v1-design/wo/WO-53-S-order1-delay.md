# WO-53 (S-model): order-1 mode with the extra loop delay (D76)

Coordinator-written, 2026-11-13. **Tier: code (Sonnet).** Sources:
- D74, D76;
- `work/v1-design/REVIEW-C4a-2026-11-13.md` (M1);
- `model/iadc.py`, `model/golden.py`, `model/studies/`;
- SPEC §3.7a (order-1 conventions).

## Background
- In order 1 the comparator reads x2 = c2·x1 from the previous φS, so y[n+1] = sign(x1[n]).
- The model has y[n] = sign(x1[n]).
- A first-order loop with one extra delay has NTF denominator 1 − z⁻¹ + z⁻²: its poles sit on the unit circle.

## Items
1. Add an opt-in `order1_delay` parameter to `iadc.py`, with the default unchanged. Add a test for it.
2. Study it at N 64 / 256 / 1024 / 4096, u ∈ [−0.9, 0.9]:
   - stability: |x1| bounded, no limit cycles that grow;
   - x1 peak against the OTA1 swing;
   - resolution and INL of order 1 with the CoI decimator (order-1 reconstruction = acc1 / N), compared with the no-delay model;
   - whether a corrected reconstruction (accounting for the delay) recovers accuracy.
3. Verdict:
   - **Pass:** order 1 with the delay is stable, x1 stays within swing, and accuracy meets the order-1 role in SPEC (characterisation mode).
   - **Fail:** recommend the comparator mux.
4. If it passes: make golden order-1 vectors under the delay (a v3.2 bump, regenerated on the sandbox, re-pinned sha, subset proof).

Report what changes for C9/RTL. The RTL already has DAC = y from the latest capture, so check whether the order-1 bitstream timing changes at all.

## Rules
- Sandbox only (`.venv-sbx`), no local python, explicit-path commits, no push.
- Do not touch `design/`.

## Budget
At most 30 tool calls. Report in ≤ 30 lines.
