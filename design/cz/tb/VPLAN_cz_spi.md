# VPLAN — cz_spi (D102 SPI read port, Chipalooza variant)

Status 2026-11-24: plan, bench (`tb_cz_spi.v`), run script (`run_spi.sh`) and 16 mutants (`mutants_spi/`) are written.
**Nothing has been run** (user rule: no sims until sandbox runs are allowed). Every "status" below is `written`.
No requirement is verified yet.

## 1. Spec sources (intent; the RTL is not the spec)

| Tag | Source |
|---|---|
| D102 | `work/v1-design/DECISIONS.md`, D102 row |
| PROP | `PROPOSAL_CHIPALOOZA4.md`, "SPI read port" bullets |
| REV | design review 2026-11-23, findings SPI-1..SPI-5 (`.claude/agent-memory/sd-adc-design-reviewer/MEMORY.md`) |
| NOTES | `design/cz/rtl/cz_top_wrap_notes.md` (connection, pin map, timing, open questions) |
| C9 | frozen C9 read-port behaviour (addr 2-FF + word reg, rd 2-FF + guard D66, status = {fr, ov, cfg_pending, boost, trim, 0, ctr}) |

## 2. Bench architecture

- DUT side: the **real frozen C9** (`sd_adc_c9`, PW_BITS 8 / BIAS_BITS 2 so the power-good hold is 256 fs ticks) +
  `cz_bus8` + `cz_spi`, wired as NOTES: C9 `ui_in = {dbg_o, cfg[6:4], rd_o, addr_o}`, `bus = {uo_out, uio_out}`,
  `data_in = cz_bus8(bus, bsel)`.
- **Twin**: a second C9 + cz_bus8 with the same clk/rst/cfg/comp and the same rd (the DUT's `rd_o` in SPI mode, the
  rd pin in parallel mode), but no wrapper. It is (a) the "slot without the wrapper" reference for spi_en = 0, and
  (b) the parallel-bus reader for "the same frame" (T02). Its state (hold, frame_ready, overrun) is compared with the
  DUT-side C9 every clk.
- Config: N = 64, fs = clk/12 → a frame every 792 clk (16.5 µs, the 60 kSPS fast mode). Comparator input = seeded
  random bits, so acc1/acc2 differ per frame.
- Scoreboard: frame history from the C9 hold register at every load, indexed by the 8-bit frame counter.
- SPI host BFM: mode 0, MSB first, samples MISO at the rising edge, programmable half period, ±jitter, CS_n setup,
  random CS_n phase vs clk, bit count (0 = abort, 1..95 = partial, 96 = full).
- Always-on checkers: lockstep, pass-through, SPI-mode pin rules, mode-0 MISO edge rule, CDC latency, ack/loss
  accounting (every frame_ready clear in SPI mode must be attributable).
- Seeds via `+seed=N`; `+STOP_ON_ERR` for mutants; `+STRICT_ONE_ACK` for the SA-SPI-1 interpretation; watchdog 150 ms.

## 3. Requirements → test → checker → coverage

| REQ | Requirement (source) | Test | Checker | Coverage / vacuity guard |
|---|---|---|---|---|
| REQ-FRM-001 | Frame = 96 bits, order status(16) acc1(32) acc2(32) tag(16), MSB first (D102, PROP) | T02–T14 | `check_frame`: content vs hold history by tag ctr | n_full ≥ 200 |
| REQ-FRM-002 | SPI frame equals the parallel-bus read of the same frame (user) | T02 | `rx === pf` (twin, byte bus, both bsel), all 96 bits | 4 frames |
| REQ-FRM-003 | Snapshot is the current frame: ctr at CS_n fall, or one loaded before the snapshot completed | all reads | freshness `c - ctr_fall ≤ ctr_rise - ctr_fall` | T06 hits both |
| REQ-FRM-004 | status word is one C9 presented during the capture; status[12:8] matches the frame | all reads | 128-clk ring membership; `h_st` | — |
| REQ-SNAP-001 | Never torn: tag ctr = status ctr, acc from the same frame (D102, PROP, REV SPI-2) | T06 sweep, all | `check_frame` torn + content | T06 load at every clk offset −4..40 |
| REQ-SNAP-002 | Load during capture forces a retake (D102) | T06 | ack latency > 20 clk ⇒ retake counted | `n_retake ≥ 1` (fails if 0) |
| REQ-SNAP-003 | Load during the shift does not change the shifted data (PROP) | T07, T04 slow | `check_frame` + mode-0 monitor | `n_shift_loads ≥ 2` |
| REQ-M0-001 | Bit 95 valid before the first SCLK rise when setup ≥ 32 clk (PROP, NOTES) | all non-relaxed reads | MISO last change ≥ min(th, 1 clk) before first rise; sampled value checked | — |
| REQ-M0-002 | MISO changes only at a falling SCLK edge (mode 0) | all non-relaxed reads | `always @(miso)` edge rule | — |
| REQ-M0-003 | SCLK asynchronous to clk, up to 12 MHz; random phase | T04, T14 | as above | 250 kHz, 1 MHz, 6 MHz, 12 MHz (clk/4), 16, 24, 40 MHz, ±10 % jitter |
| REQ-TIM-001 | CS_n setup exactly 32 clk passes, incl. with a retake (D102, REV SPI-1) | T05, T06 | full checks | 8 + 90 reads at 32.000 clk |
| REQ-TIM-002 | Shorter setup: behaviour documented, not judged | T05 | `STAT short_setup` table | 4..28 clk |
| REQ-TIM-003 | CS_n high ≥ 8 clk between reads works (D102) | T13, T09, T08 | full checks | exactly 8 clk |
| REQ-TIM-004 | Snapshot + ack inside the 32-clk setup budget | all full reads | ack latency ≤ 32 clk | `STAT ack_latency` |
| REQ-CDC-001 | CS_n reaches the clk domain through a 2-FF synchroniser (NOTES Q3) | all SPI reads | first addr_o/rd_o reaction ≥ 3rd clk edge | `STAT min_cs_to_clkdomain_edges` |
| REQ-ACK-001 | Frame acknowledged at snapshot: frame_ready (and overrun) cleared, one ack per read (D102, PROP, REV SPI-3) | all full reads | ready-at-snapshot ⇒ exactly 1 rd pulse; frame_ready = 0 at CS_n rise if no newer frame; ≤ 1 ack | — |
| REQ-ACK-002 | No unread frame silently cleared, except the documented residual window; measure it (NOTES Q4) | T06, all | `ctx_close` attribution; window width ≤ 6 clk (5 documented + 1 sync phase) | `n_win ≥ 1` (fails if 0) |
| REQ-ACK-003 | Overrun reported and cleared by the ack (PROP "lost frame = gap") | T08 | status[15:14] = 11 after 3 unread frames; 00 on re-read; flags 0 after ack | — |
| REQ-ACK-004 | Partial read can be repeated: same data, no harmful second ack (D102, PROP) | T09, T08, T14 | bits equal except live flags; loss monitor; `STAT reacks` | 20-, 1-, 0-bit partials |
| REQ-ABT-001 | CS_n high mid-capture = abort, no ack (NOTES) | T10, T14 | CS_n low ≤ 8 clk ⇒ 0 rd pulses, frame_ready still 1 | k = 1..30, `STAT abort` bitmap |
| REQ-EN0-001 | spi_en = 0: addr/rd/dbg/data pass straight through, SPI pins ignored | T01, T15 | comb check after every pin change; negedge check | 5000 random pin events |
| REQ-EN0-002 | spi_en = 0: slot outputs identical to C9 + cz_bus8 without the wrapper | T01, T15 | `data_o/uo/uio === twin` | after spi_en 1→0 too |
| REQ-EN1-001 | spi_en = 1: external addr/rd/dbg/bsel ignored | T04, T11, T14 | mid-cycle pin change ⇒ C9 inputs unchanged; lockstep; loss monitor; content | noise + held dbg = 1, addr = 7 |
| REQ-EN1-002 | spi_en = 1: dbg forced 0 (REV SPI-4) | all SPI | `dbg_o === 0` every clk | — |
| REQ-EN1-003 | spi_en = 1: data[7:1] = 0, MISO on data[0] | all SPI | every clk | — |
| REQ-RST-001 | Reset mid-shift / mid-capture: recovers, next read correct | T12 | full checks on the next read | 2 cases + reset with CS_n high |
| REQ-RST-002 | No X on data pins in SPI mode, incl. around reset | always | `^data_o !== x` | — |

## 4. Threat model → tests

| Threat | Test |
|---|---|
| Hold reload between word captures (torn frame) | T06 (every clk offset, two sub-clk phases) |
| Ack clears a frame loaded during the read (REV SPI-3) | T06, T07, loss monitor; mutant M15 |
| Ack before the snapshot is valid | T06; mutant M04 |
| CS_n async edge near clk edge; sync bypass | random sub-ns CS_n phase everywhere; REQ-CDC-001; mutant M07 |
| SCLK faster than clk/4, jitter, slow SCLK across many frames | T04, T07, T14 |
| Short CS_n setup / short CS_n high | T05, T13, T10 |
| Partial read, re-read, abort at every capture cycle | T09, T10, T14 |
| External pins hostile in SPI mode (dbg = 1 puts the debug bus on C9's outputs) | T11, noise |
| Reset mid-transaction, reset release with CS_n low | T12 |
| Bit counter not restarted between reads | every back-to-back read; mutant M08 |

## 5. Mutants (`mutants_spi/*.sed`, applied by `run_spi.sh` to a copy; each must REJECT)

| ID | Fault | Expected killer |
|---|---|---|
| M01 | status/tag swapped in the shift order | content check (every read) |
| M02 | MISO pointer on the rising SCLK edge | mode-0 edge monitor, content |
| M03 | retake disabled | T06 torn check |
| M04 | rd raised at CS_n fall (ack before snapshot) | T06: retaken frame left ready / unread frame cleared |
| M05 | no ack | frame_ready still 1 after read |
| M06 | dbg not forced 0 | dbg_o check, content with dbg pin = 1 |
| M07 | CS_n synchroniser bypassed (fall from raw pin) | REQ-CDC-001 latency / no capture |
| M08 | bit counter reset only by rst_n | 2nd read shifts zeros |
| M09 | tag word sampled 1 clk early | content |
| M10 | LSB first | content |
| M11 | CS_n high does not abort a capture | T10 (ack on abort) |
| M12 | data[7:1] not zeroed | SPI-mode pin check |
| M13 | external rd leaks to C9 | T11, loss monitor, ack count |
| M14 | external addr leaks to C9 | content under addr noise / addr = 7 |
| M15 | ack on CS_n rise (the SPI-3 design the review rejected) | frame_ready at CS_n rise, T07 silent clear |
| M16 | counter compare on wrong bits (always retakes, 3 attempts) | snapshot later than 32 clk: MISO not settled / content |

Known not killable in RTL simulation: removing **one** of the two CS_n synchroniser flops (shifts latency by 1 clk,
still ≥ 3 edges). That needs CDC lint/STA (NOTES Q3). Waived for sim; listed as a hole.

## 6. Spec ambiguities (open; tested interpretation stated)

- **SA-SPI-1 second ack on re-read.** Spec: "acknowledged at snapshot; partial reads repeatable". Every CS_n fall
  takes a new snapshot, so every read pulses rd, including a re-read of an already acknowledged frame. The C9 counter
  guard makes this harmless (it only clears a frame whose counter is unchanged, and that frame was just snapshotted).
  Default bench: a second ack is allowed if it never clears an undelivered frame (loss monitor), and it is counted
  (`STAT reacks`). `+STRICT_ONE_ACK` treats any rd pulse on a re-read as an error; it is expected to REJECT the current
  RTL. Decide which is intended.
- **SA-SPI-2 "same data" on re-read.** status[15:14] (frame_ready, overrun) are live and change after the first
  read's ack, and a re-read after a new load returns the new frame. Bench checks: identical except status[15:14] when no
  load happened in between; otherwise the newest frame.
- **SA-SPI-3 DRDY pin.** D102/PROP: "frame_ready acts as DRDY (a level)". In SPI mode data[7:1] are 0 and dbg is
  forced 0, so frame_ready is not on any wrapper output; NOTES says "no extra output". Unless the slot routes
  frame_ready to one of the other outputs, the host can only poll status[15] over SPI. Not testable at this level.
- **SA-SPI-4 residual window width.** NOTES Q4 says "about 5 clk". Bench limit: width ≤ 6 clk measured from the CS_n
  fall (5 + 1 clk of synchroniser phase). The window is reported, not just bounded.
- **SA-SPI-5 bits after 96.** Not specified; RTL gives 0. Not checked.
- **SA-SPI-6 reset release with CS_n held low.** Not specified. The wrapper starts a capture (its synchroniser resets
  to "high"), mid-frame for the host. T12 observes only; the next read after CS_n high must be correct.

## 7. Coverage holes / waivers (current)

- Nothing run: no line, toggle or FSM coverage yet. Plan: Verilator `--coverage` run of the same bench (later).
- X-init / random-init of the SCLK-domain flops (no rst_n on rcnt/ptr) not exercised in Icarus.
- The 3rd capture attempt (2 retakes, torn accepted) is unreachable with a 792-clk frame period; not covered.
- Gate-level and SDF: none (no netlist).
- Metastability: modelled only as random CS_n phase; real sync depth needs CDC lint/STA.
- Pad/crossbar timing for 12 MHz (REV SPI-5) is outside RTL sim.

## 8. Sign-off (for later)

real RTL ACCEPT on ≥ 5 seeds; all 16 mutants REJECT; cover guards hit (retake, window, shift loads, ≥ 200 full
reads); STAT window ≤ 6 clk; lint reviewed; SA-SPI-1..3 decided; design review of the bench.

## 9. Commands (sandbox only)

```
scripts/sync-to-sandbox.sh
~/bin/rta-tt 'scripts/iic "cd /foss/designs/tt-sd/design/cz/tb && ./run_spi.sh"'     # path as mounted in the container
SEEDS="1 2 3 4 5 6 7 8" TO=900 ./run_spi.sh ../rtl/cz_spi.v                          # inside the container
```
