# WO-91 (C1): close the gate B solver convergence under D43c (precision and boost)

Coordinator-written, 2026-11-15. **Tier: design (Opus).** Fresh agent.

## Inputs
- WO-76 frozen copy `/home/mempool/regr/tt/WO-76-f00f9bf`: `out/gb/*`, `results/wo76/README.md`.
- WO-63 README.
- D43 (the D43c ladder rule), D48. REVIEW-BOOK-2026-11-15, findings M1, M7 and M9. DESIGN_BOOK III.1.8a.
- **Precision (2 MHz, N 1024, m 21), current state:**
  - ss/−40: O1 combined 1.706 ppm. **O2 combined 0.165 ppm ACCEPT**, healthy, endpoint spread 0.001 ppm (`out/gb/c1_nom_O2/combine.out`; parts 0.120–0.165).
  - fs/125: O2 p0 0.472 and p1 0.463 against O1 0.967; p2–p5 are running in `out/logs_o2` (dir `out/gb/c3_nom_O2`).
  - tt/27 and ss/125: O1 only (0.692 / 0.698).
- **Why another point is needed:** the O1→O2 step at ss/−40 is about 10×, which does not meet D43c as written. The O2 `--tight` (reltol 1e-6 / vntol 1e-8) run aborted. The ladder never tightens vntol (1e-6 V, about 0.25 ppm).

## Items
1. **Third solver point at ss/−40** on at least p0 and p2 (and p4 if budget allows). Use a setting that is stable and tighter than O2 in a different direction, e.g. O2 plus vntol 1e-7, or O2 with gear vs trap, or a smaller max step. Add the flag to `c1b_gateb.py`, cite why it is tighter, and run it.
   - **Accept rule, from D43c:** O2 and the third point agree within max(10 %·INL, 0.1·(gate − INL)).
   - If they agree, state the D43c verdict with its formula.
   - If they do not, report it plainly.
2. **fs/125 O2:** collect p2–p5 when they finish, run the combine (`--opt O2 --combine 6 --copy nom`), and apply D43c against O1.
3. **tt/27 and ss/125 precision:** run O2 (6 parts each), because O1 is under 3× margin (gate/3 = 0.444 ppm).
4. **Boost gate B on the WO-52 netlist:** run tt/27 and ss/125 (O1), and fs/125 at O2. 3.14 ppm against 5 is < 3× margin. Reuse the WO-52 frozen copy settings.
5. **Stronger precision broken copy:** srknee only rejects by 3 %. Build a copy that REJECTs with margin ≥ 1.5× the gate at the ss/−40 basis (e.g. SR 0.6× floor, or a PM-degraded copy). Run it at O2.
6. Write `results/wo91/README.md`: a verdict table per corner and mode with O1, O2, the third point, Δ, the D43c verdict and the copies. State plainly whether precision and boost gate B pass.

## Rules
- Sandbox only. No local python, not even an empty `python3 -`.
- Make a new frozen copy `/home/mempool/regr/tt/WO-91-<sha>`. Leave WO-76 untouched except for reading it, and collecting fs/125.
- Use the **repo `scripts/lpool.sh`** (global cap). Use deck timeouts ≥ 30000 s. Source the venv and nix PATH. Do not export OMP_NUM_THREADS. Use absolute paths. Wait on markers only.
- Make no OTA or netlist change.
- Write only `design/c1_ota1/c1b_gateb.py` and `results/wo91/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 40 tool calls. Report in ≤ 25 lines. If the runs take hours, write the pickup commands into the README.
