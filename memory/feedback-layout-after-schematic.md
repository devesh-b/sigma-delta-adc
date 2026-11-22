---
name: feedback-layout-after-schematic
description: start a block's layout only after its schematic is verified; don't rush layout
metadata:
  type: feedback
---
Start a block's layout only once its schematic is verified (gates ACCEPT, broken copies REJECT, reviewed, frozen). Don't hurry to draw all the layout.

**Why:** the user said so on 2026-11-22, during the 10-day TT push: "dont be in a hurry to do all layout as the schematic needs to be verified first". Layout drawn on a moving netlist gets redrawn, and its LVS proves nothing. Logged as D100.

**How to apply:** keep a layout-ready list per block. Tell the layout agent when a block becomes verified. Schematic-independent work (frame, power grid, passives) may proceed. Related: [[feedback-green-is-not-proof]], [[feedback-decision-quality]].
