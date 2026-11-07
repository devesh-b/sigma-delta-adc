---
name: feedback-sandbox-only
description: User rule — run everything (sims, model, EDA, agent checks) on the sandbox; nothing runs on the local Mac
metadata:
  type: feedback
---

Run everything on the sandbox, nothing on the local system (user, 2026-11-07). This covers ngspice, the Python model in `model/`, sweeps, synthesis, DRC/LVS/PEX, and every agent self-check or acceptance run. The local machine only edits, reads results and dispatches.

**Why:** The user said so. The AlphaOneSoC rule had the same basis: the desktop crashed under parallel heavy runs. This Mac has 8 GB RAM and no EDA tools.
**How to apply:** The sandbox is the AlphaOneSoC box (`ssh sandbox` = mempool@mempool.lan; the user chose it on 2026-11-07). It authenticates with the 1Password key "Abhiram Dasika". Push with `scripts/sync-to-sandbox.sh` to `/home/mempool/tt-sd` (never `/home/mempool/tt`, which is AlphaOneSoC's) and run with `~/bin/rta-tt`. EDA tools come from IIC-OSIC-TOOLS 2026.10 via `scripts/iic`, using the TT-pinned sky130 PDK in `~/.ciel`. Outputs go to `/home/mempool/regr/tt`. Never touch the box's other tmux sessions. As of 2026-11-07 the bridge is verified working. The box has no analog EDA tools or PDK yet, and its disk is 95% full (52 GB free). If the box is unreachable, don't run locally: queue the command instead. Details are in `WORKFLOW.md` §4–5. See [[feedback-tiered-lean-agents]].
