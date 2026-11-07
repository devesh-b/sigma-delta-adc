# WO-10 (S4 close): D12 residual ε_eff in the S4 CMRR term

Coordinator-written, 2026-11-08. **Tier: routine.**
**Spec source:** DECISIONS D33; REVIEW-S4S5b-2026-11-08.md C-M3, §5, m8.
Read `work/v1-design/HANDOFF.md` first, including the **sandbox runs without the rta-tt lock** section.

## Files you may touch (nothing else)
- `model/studies/s4_corners.py`
- `model/tests/test_s4_corners.py`
- `work/v1-design/results/s4_corners.{md,json}`

## Items
1. **ε_eff term (D33).** Replace the CM→diff coefficient ε_Cs with

   ε_eff = |ΔCp,top/Cs| + |(Cp,top/Cs)·ε_Cs| + ε_inj

   - Signs are combined worst-case until WO-09 settles them.
   - **MC draws:**
     - ε_Cs as now (0.75 % 3σ);
     - ΔCp,top Gaussian with 3σ 0.25 fF;
     - Cp,top 20 fF per side (fixed, the allocation);
     - ε_inj allocation 2.8e-4 (fixed, worst sign).
   - Corner points: use the 3σ values.
   - Keep the gate: sys off ≥ 60 dB, sys on ≥ 100 dB. Also report the margin against the **66 dB design target**, informational.
   - Keep the old ε_Cs·ΔVcm result in the md as "superseded (D33)".
2. **Theory check.** At the 3σ allocation, ε_eff ≈ 5e-4 to 6e-4, which is ≈ 64–66 dB. The printed value must agree with a hand calculation in the md, within 10 %.
3. **Margin column (m8).** Add a margin column (limit/value − 1, in %) to the noise and INL row tables.
4. **Non-vacuity.**
   - Keep all existing broken copies.
   - Add a copy with ΔCp,top 3σ 2 fF. It must REJECT sys-off.
   - The existing "Cs mismatch 3 %" copy must still REJECT under the new term. If it no longer does, replace it with one that does (e.g. Cp,top 100 fF), and say why.
5. **Re-run the full S4.** Expect ACCEPT, exit 0. If anything fails, report it as a finding.

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest model/tests -q` | pass |
| 2 | `s4_corners --out <dir>` | ACCEPT, exit 0; CMRR on ε_eff; margin columns |
| 3 | `s4_corners --nonvac` | REJECT, naming the ΔCp 2 fF copy; exit 1 |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `model: S4 CMRR on D12 residual eps_eff (D33), margin columns + results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget and stop rule
At most 40 tool calls. The full run takes about 10 min on a loaded box: use direct ssh + nohup, never a poll loop inside rta-tt. Finish by reporting "k of 5 items done".
