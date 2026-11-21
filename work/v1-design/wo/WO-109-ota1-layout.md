# WO-109: OTA1 (C1) layout + TT precheck on frame (D100)

Agent: pd-expert. Budget: about 5 h, up to about 60 tool calls. Stop rule: hand off when OTA1 is DRC/LVS clean, or on a blocker.

Inputs:
- the WO-107 hand-off, in `work/v1-design/results/wo107/README.md`;
- the layout flow in `design/layout/` (route.tcl, run.sh, verify.tcl, floorplan.tcl);
- the OTA1 netlist, frozen at WO-52 (`design/c1_ota1`): 71 instances, about 280 fingers, 5 caps including the 2 pF integrator cap.

Scope:
1. **Router.** Extend route.tcl for shared-diffusion multi-finger rows and common-centroid or interdigitated placement, for the input pair and the mirrors. Add dummies and guard rings.
2. **OTA1 layout.**
   - Fit the 10,628 µm² slot from the frame. Caps may use MIM over circuits (D93).
   - DRC: Magic hierarchical and flat, plus KLayout, all 0.
   - LVS PASS against the frozen netlist, with the device sizes exactly as in the netlist.
   - Broken copies that must fail:
     - a finger swap must FAIL LVS;
     - a W change must FAIL LVS;
     - a DRC-bad copy must FAIL DRC.
3. **TT precheck on the frame.** Build the project directory the way `scripts/s0_precheck.sh build()` does (info.yaml etc.) and run the precheck. Add a broken copy that must FAIL.

Not in scope: C2, C3, C4 and C6 active layout (on hold under D100).
