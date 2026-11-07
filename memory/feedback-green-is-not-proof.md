---
name: feedback-green-is-not-proof
description: Verification discipline — a PASS counts only if the check is shown to fail on a broken copy; analog false-pass traps listed in WORKFLOW §11
metadata:
  type: feedback
---

Every test, property or analog pass/fail check must be shown to FAIL on a deliberately broken copy before its PASS counts. Testbench intent comes from the spec, never from the designer's reasoning. Report known failures as "N distinct causes", not as raw counts.

**Why:** In AlphaOneSoC, 14 kinds of checks reported PASS while testing nothing (empty outputs compared equal, vacuous formal proofs, benches that exited 0 on FAIL, and others).
**How to apply:** Use the digital list for the decimator and control RTL. For analog work, use the anticipated list in `WORKFLOW.md` §11: failed `.meas` read as a number, truncated transients, wrong corner, unchecked `.op`, non-coherent FFT, ideal parts left in, fake Monte Carlo. Record new false passes there when they happen.
