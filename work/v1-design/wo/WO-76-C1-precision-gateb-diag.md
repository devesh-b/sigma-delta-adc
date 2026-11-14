# WO-76 (C1): precision gate B fails at ss/-40; diagnose, then list options

Coordinator-written, 2026-11-14. **Tier: design (Opus).** Fresh agent.

## Input: WO-63 result
Frozen copy `/home/mempool/regr/tt/WO-63-e450ae2`, `out/gb/*/combine.out`, `results/wo63/README.md`.

Setup: 2 MHz, N 1024, m 21, O1, 6 parts, endpoint INL, gate 1.333 ppm.

| corner | INL | verdict |
|---|---|---|
| tt/27/3.3 | 0.69 ppm | ACCEPT |
| **ss/−40/3.0** | **1.71 ppm** | **REJECT** |
| ss/125/3.0 | 0.70 ppm | ACCEPT |
| fs/125/3.0 | 0.97 ppm | ACCEPT; ≥ gate/2, so O2 needed |
| srknee broken copy (fs/125) | 1.37 ppm | REJECT (good) |

Boost gate B at ss/−40 was 0.71 ppm against its 5 ppm gate (WO-52).

## Items
1. **Fill the tables in `results/wo63/README.md`** from the combine.out files. Commit.
2. **Rule out a numerical cause before calling it a design failure (lesson 1, 2).**
   - Run ss/−40 and fs/125 at O2 (the gate rule requires it anyway).
   - If budget allows, also run ss/−40 at a tighter reltol or a smaller max step on 1–2 parts.
   - State whether the 1.71 ppm moves.
3. **Mechanism.** Find which OTA property limits ss/−40 precision: slew, settling (GBW·β), A0 / gain nonlinearity, or the CMFB. Use the per-point INL shape, the OTA1 op at that corner (tb op/AC data, WO-61 in `/home/mempool/regr/tt/WO-52-bf4a565`), and if needed one diagnostic deck with the OTA2/macromodel point held fixed. Explain why it is fine at tt and 125 °C and in boost.
4. **Broken-copy strength.** srknee at fs/125 sits at only 1.37 ppm, close to the gate, and ss/−40 nominal is worse than that. Say whether the copy discriminates well enough, and propose a stronger one if not. Do not run it.
5. **Options**, each with its cost (current, area, schedule, risk) and an expected INL:
   - examples: a precision-mode bias tweak, sizing, raising the bias only at cold (PTAT share), or a gate/basis change, which is a user decision;
   - check every current option against the fast-mode budget: ≈ 180 µA REASONED, 200 µA budget.
   - **Make no OTA or current change.** Recommend one option.

## Rules
- Sandbox only. No local python, not even an empty one.
- Runs go through `scripts/lpool.sh`. Source the venv and the nix PATH in the launcher. Do not export OMP_NUM_THREADS. Use absolute out paths.
- Make a new frozen copy `/home/mempool/regr/tt/WO-76-<sha>`. Never write in `/home/mempool/tt`.
- Wait on EXIT/POOL_DONE markers. No pgrep/pkill loops over ssh.
- Write only `results/wo76/` and `results/wo63/README.md`, plus `design/c1_ota1/c1b_gateb.py` if O2/tolerance flags are needed.
- Commit with explicit paths, no trailers, no push. If signing blocks, list the paths.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, hand off with exact pickup commands in the README.
