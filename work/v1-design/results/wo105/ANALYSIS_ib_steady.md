# WO-105b gate (a): ib_steady REJECT analysis (2026-11-24)

The analysis was done by an Opus analyst, read-only. Nothing was run. Sources on the sandbox:
- `/home/mempool/regr/tt/WO-105b-cc5472e/out/g/a_nom/ga_nom_ota2-ota2_tt27_N16_O1.{json,csv,cir}`
- `a_nosu/`

Bench: `design/top/top_bench.py`, lines 314–331 and 380–388.

**Verdict:** the REJECT comes from the bench's metric. It is not bias drift.

## Q1: drift or artefact?
It is an artefact.
- ib_steady takes the raw max − min of the `b1_ibtp` port current after t_rel.
- Between clock edges the current is flat at 2.6088–2.6089 µA.
- The range comes from 5–8 ns spikes after the edges:
  - ±1–2 % at every 2 MHz clock edge;
  - ±4 % at the integrator-reset edges.
- The 8.58 % range is the spike at the 50.0 µs reset edge (2.716 and 2.492 µA). The 3.47 % hold range is clock-edge spikes.
- The same zero-mean ±55 nA spikes are present from 2 to 19 µs, while the bias is off. They are charge moving through the gate capacitance of the OTA tail mirrors.
- t_settle_1pct = 59.5 µs is also an artefact: it reports the last raw sample outside 1 %, which is always the latest spike.
- **The one real slow part** is C6's own loop ringing after the zero-state escape:
  - about 170–180 kHz, ζ ≈ 0.25, τ ≈ 3.7 µs;
  - peaks: 4.88 µA at 21.5 µs, 2.98 at 29, 2.69 at 34.5, 2.627 at 40.5, 2.6125 at 46.
- It is not the OTA common-mode loop. ngspice has no thermal node.
- **With the edge spikes excluded:**

  | Quantity | Value |
  |---|---|
  | Max / min after t_rel | +0.744 % / −0.271 % |
  | Range after t_rel | 1.015 % |
  | Range in the hold window | 0.65 % |
  | Inside ±1 % from | 38.24 µs (17.6 µs after the final bias_ok rise) |
  | Inside ±0.1 % from | 47.3 µs |
  | Per-cycle means, 46 µs to end | within ±0.15 % (no drift) |

- ib_final (the median during the conversions) and ib_design refer to the same sink, so both are correct.
- ib_at_rel_err (0.75 %) is right only by luck: it is a single sample, interpolated on a clock edge.

## Q2: why is ib_final 10.7 % above design?
It is not C6.
- C6 at tt/27: the master current is 1.0677 µA, −0.21 % (WO-80). The cascoded sinks pass the ±3 % port gate (WO-99).
- The top bench uses the c6_spot stand-in instead: a plain W2/L4 NMOS diode and a W4.40/L4 sink, with no cascode.
- The diode sits at about 0.9–1 V Vds, while the port sits at about 2.1 V. On an L4 device, channel-length modulation gives a gain of about this size. WO-104 measured +2.4 % on an L16 mirror for about 0.9 V; the effect scales about as 1/L.
- **Caveat:** this is inferred by elimination. v(vn) and v(b1_ibtp) are not saved.
- **Impact:** harmless at tt (the converter is ratiometric and the conversions are correct). It is not representative at the corners: WO-32 allows I_REF_btp only +1.6 % at ff/125.

## Q3: is the limit right against SPEC?
No.
- SPEC row 104, amended by CL-38/D89, asks that the **master** current settle to ±1 % within 4.1 ms of the final bias_ok rise and stay within ±1 % from rstb release on. That is a 2 %-wide band on a DC quantity.
- The bench gates a ≤ 1 % peak-to-peak range instead, half the SPEC width, and reads the raw port current including switching transients. CL-11/D65 already fixed the same mistake for the CM start-up row.
- Under the SPEC metric (cycle-averaged, ±1 %), a_nom passes: max deviation 0.74 %, margin 0.26 % at tt.

## Q4: options
Cost basis: about 70 s per simulated µs, about 70 min per job.

| Option | What | Cost | Outcome |
|---|---|---|---|
| **A. Fix the bench (recommended)** | Per-clock-cycle means of ib, all within ±1 % of ib_final; ib_settled_at_rel on a one-cycle mean; t_settle_1pct on the cycle means; raw peak-to-peak and ib_final/ib_design as report rows (the latter becomes a ±3 % gate once cascoded sinks are in); a `--rescore` mode | 0 sim hours (re-score the kept csv) | a_nom ACCEPT expected, a_nosu still REJECT |
| B. Fix the design | Damp the C6 loop, decap or cascode the bias lines | A C6 campaign plus about 70 min | Not warranted: C6 meets row 104 by a wide margin (17.6 µs vs 4.1 ms) |
| C. Extend the sim | t_rel 50 / 60 µs | +12 / +23 min per job | Still REJECT, because the edge spikes persist. Useful only as extra margin, together with A |

## Q5: runs needed later, each with a broken copy that must REJECT
1. **Re-score a_nom with the option A checks** (0 h). Broken copies, all 0 h:
   - evaluation t_rel at 30 µs (inside the ringing);
   - a +2 % ramp after t_rel;
   - a +2 % step for one full cycle at 50 µs;
   - re-score a_nosu.
2. **a_slow** (about 70 min). It needs a one-line bench change to pass the `slow` token to `c6_subckt` (the c6_spot WO-87 mutant: master-leg RC, τ 1.2 ms). It must REJECT on ib_settled_at_rel / ib_steady.
3. **Port accuracy** (about 70 min). Run a_nom with cascoded sinks (c6_final once WO-104 is accepted), saving v(vn) and v(b1_ibtp). Pass: within ±3 % of ib_design. Broken copy: `finger` (one ibtp unit finger missing), about 70 min, run in parallel with it.
4. **c/a_ss at ss/−40/3.0** with the new checks (70–82 min); optionally t_rel 50 µs, because the tt margin is only 0.26 %. Broken copy: re-score at 30 µs.

Minimum to close gate (a) at tt: items 1 and 2, which is one job of about 70 min.

## Open points
- The +10.7 % attribution is unconfirmed until item 3 runs.
- The ±1 % margin at ss/−40 is unknown (item 4).
- The WO-105 README still says t_rel = 20 µs for gate (a).
