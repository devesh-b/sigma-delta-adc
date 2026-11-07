# WO-03 (S2): chopping study (OTA chop vs system chop in incremental mode)

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer reviews it before accept.
**Spec source:** SPEC.md §3.6, §5 items 2 and 6; PLAN.md S2; DECISIONS D4.
Read `work/v1-design/HANDOFF.md` first.

## Why
In incremental mode the CoI reconstruction weights samples unequally, so OTA chopping at fs/2 may leave a residual offset of roughly Vos/N instead of cancelling. System chop (input swap between sub-conversions) is expected to be the robust path. This WO quantifies both and recommends whether OTA chop stays in v1 (D4).

## Files you may touch (nothing else)
- `model/studies/s2_chop.py` (new)
- `model/studies/s2_theory.py` (new)
- `work/v1-design/results/s2_chop.md` (new)
- `work/v1-design/results/s2_chop.json` (new)

**Do not edit `model/iadc.py`.** WO-02 owns it. If you need a model change, stop and report it as an open issue.
If `model/studies/__init__.py` does not exist yet (WO-02 creates it), run your study as a script (`python3 model/studies/s2_chop.py`). Don't create `__init__.py` yourself.

## Theory first (`s2_theory.py`, independent of iadc.py)
Write the analytic residual offset for an order-2 CIFB incremental loop with CoI reconstruction. It is independent of the model code.
- **Order-2 case:** constant offset Vos at the first-integrator input with OTA chop ±1 alternating per cycle. The residual is the weighted sum Σ (−1)^n·w_n / Σ w_n, with CoI weights w_n ∝ (N − n).
- **Order-1 case:** the same, with equal weights.
- **System-chop case:** the residual after averaging two sub-conversions with swapped input polarity is ideally 0.

Give closed forms vs N for N = 64…4096. These are the **expected values** for the model comparison.

## Study (`s2_chop.py`, uses iadc.py as is)
**Grid:**
- chop mode ∈ {none, ota, sys, ota + sys}
- Vos ∈ {1, 3, 9 mV} (9 mV ≈ 3σ guess)
- N ∈ {256, 1024, 4096}
- vres ∈ {0, 5, 20 µV}
- order ∈ {1, 2}
- fs = 2 MHz, Cs = 1 pF, flicker on, lf_gain 1 and 5.3

**Report:**
- mean offset (µV) and rms noise (µV) at 15 SPS and 240 SPS
- model vs theory residual for the ota-only case (agreement within 20 %, or explain why not)

**Pass criteria:**
- **ota + sys** and **sys**: |offset| ≤ 5 µV at Vos = 9 mV, all N, vres ≤ 5 µV.
- **ota-only**: no pass target; it is reported for D4.
- Print `ACCEPT`/`REJECT` per mode.

**Non-vacuity:** the sys-mode offset check must REJECT when sys_chop is disabled (none mode at Vos = 3 mV must exceed 5 µV).

**Also note** (reasoned, not modelled): chop-sequencer timing relative to reset and conversion boundaries. Can a system-chop swap happen mid-conversion? List the sequencing rules the digital sequencer (C9) must obey and the integrator-reset requirement between swapped sub-conversions.

**Recommendation:** keep or drop OTA chop in v1, with numbers. The user and the reviewer decide (D4).

## Acceptance (Haiku, sandbox, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `python3 model/studies/s2_theory.py` | prints closed-form table, residual ∝ 1/N for order 2 ota-only |
| 2 | `python3 model/studies/s2_chop.py --out /home/mempool/regr/tt/WO-03` | md + json; sys and ota + sys ACCEPT; model-vs-theory lines present |
| 3 | `s2_chop.py --nonvac` | none mode REJECT on the offset criterion |

Use `--bg`; the grid may take tens of minutes. Reduce `m_out` only if the run exceeds 60 min, and state that you did.

## Commits (explicit paths, no attribution trailer, no push)
1. `model: S2 chop theory (independent closed form)`
2. `model: S2 chop study + results`

## Budget and stop rule
At most 50 tool calls. Finish by reporting "k of 2 commits done, with reasons".
