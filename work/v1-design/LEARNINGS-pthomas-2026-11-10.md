# Learnings from the ttsky-pthomas session (Paul Thomas, ttsky-sigma-delta), triaged for v1, 2026-11-10

Source: the ttsky-pthomas session's summary of `repos/sd-analog/ttsky-sigma-delta/` (DESIGN.md, STATUS.md, docs/09b-testplan.md, tt_frame/build_frame.tcl, sim/top_tb.py, sim/bias_tb.py). Its report: `reports/pthomas-ct-sigma-delta.html`. His design is simulated and extracted only; there is no silicon yet. The silicon items come from his survey of 83 TT analog projects on tt06–09.

## Already covered in v1
- gear integration over trap: D43c.
- Delete stale csv before each run: REVIEW-C1b m5 and the WO sandbox rules.
- Linear settling becomes gain error, slew is what hurts: WO-22 and D44.
- Pin pricing €40/€40/€100/€100: SPEC and bias_bgr_area.md.
- Separate `.noise` bench (tran has no device noise): tb7 is planned.

## Act now (C1/C1b)
1. **ngspice determinism (checked 2026-11-10: bit-identical on the sandbox, closed).** The sandbox PDK `.spiceinit` sets `num_threads=8` on a 6-core box, and we run 3–5 decks in parallel. He found that the OpenMP summation order changed results from machine to machine.
   - Action: rerun one gate B part and compare INL to the last digit. If it differs, set `num_threads=1` through a per-run `.spiceinit` in the deck cwd. This also removes CPU oversubscription.
   - Add `abstol`, `itl4` and a source R on ideal sources only if the rerun shows drift.
2. **Bias start-up proof.** Ramp the rails with PWL in both orders (analog first, digital first), with no `.op` handing the bias its state. Check that no start-up leaker stays on after start-up: his "weak always-on" leaker injected 17 % error. Check that the start-up PMOS bulk goes to VDD. This joins REVIEW-C1b m7 and the start-up tb (items 11–15).
3. **Output-sense assertions.** He found a Q/QB swap that golden, schematic and LVS all missed, because they shared one source; only a closed-loop sim caught it. Our tier-1 transistor decks must assert loop polarity: y vs u sign and the integrator output direction on a known input. That is a cheap row in gate B and in C3 (comparator).

## Carry into later blocks
- **C2/C3 comparator, latch, clocks:**
  - One ngspice process per decision point, tmax 1 ps through regeneration, and 10 Ω in series with ideal sources. Treat sub-mV sign verdicts as solver noise.
  - StrongARM clocked on the wrong phase cost half a cycle of excess loop delay (about 4 dB).
  - A NOR SR latch on the regeneration nodes caused hysteresis; use inverter buffers and a NAND latch.
  - Check level-shifted 3.3 V clock edges in-chip: a 545 ps edge cost him 1.3 dB. Our CL-5 switches use level-shifted clocks.
- **C5 bias/BGR and the D47 3-bit trim:**
  - res_high_po R = 256.2 + 230.06·L Ω (1p41 bin). Magic extraction misses the ~256 Ω end term, so size from the model inverse. Nothing below about 310 Ω is realizable.
  - Uncascoded 5 V mirrors at L 1 ran 43 % hot and tracked VDD; cascode them.
  - Constant-gm bias tracked corners better than ideal bias did. That supports the D58 replica approach.
- **PEX:** ext2spice writes caps in hash order, so convergence varies between extractions. Sort and round the PEX netlist canonically and commit it as a golden.
- **Decimator timing (C4/C6):** SAR silicon ran about 2× the tt-corner timing. Close timing at ss with margin.
- **Integration and layout (C7, pd-expert):**
  - Extract the framed top and prove pin connectivity with merge plus equiv records. A missing via killed a tt08 ring oscillator.
  - Magic: run `select top cell; expand` before `drc check`; use `save cell`, not `writeall force`; watch the "Scaled ... by factor of 2" warning; magscale differs per file.
  - Run the antenna check ourselves; TT precheck does not do it for sky130.
  - Power labels must span the full stripe (within 10 µm of both tile edges).
  - Set both `uses_vapwr` and `uses_3v3` in info.yaml.
  - Tie unused uo/uio_out/uio_oe to GND; precheck does not catch floating outputs.
  - Pin tt-support-tools to a version; upstream changes can turn CI red.
- **Bench and bring-up (PUBLICATION_PLAN, test plan):**
  - Read back tt_um_chip_rom first.
  - Measure the analog mux path R on an unused pin, then correct gain/offset.
  - Remove demo-board passives on analog pins.
  - Leave DNP footprints for about 10 pF C0G input caps.
  - Treat sim 1/f as an upper bound.
  - SNDR windows ≥ 2048 bits, gates at measured − 2 dB.

## Not applicable
- Single-ended, no chopper, no CMFB in his v1: no data for our CMFB/chopper questions.
- His monitor pin (unbuffered OTA output on ua[1]): we have no analog monitor pin (D47). If one comes back, buffer it and simulate the real < 500 Ω / < 5 pF + board load.
