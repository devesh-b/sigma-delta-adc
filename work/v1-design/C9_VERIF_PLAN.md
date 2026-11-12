# C9 verification plan: CoI decimator, config, chop sequencer, frame/hold/overrun, 16-bit read bus

WO-34 (C9b), rtl-verification-engineer, 2026-11-11. Status: **plan only, no RTL exists yet.**

**Sources of intent (and only these):**
- SPEC.md §1 (N, fs, output rate), §3.6 (sequencing rules 1–13), §3.7, §3.7a (a)–(k), §3.8, §3.8a and the G3 list, §6 (VDPWR axis);
- DECISIONS D45–D48;
- PLAN row C9, V5 and "Review additions" (C9);
- golden/README.md (format 2; v3 comes from WO-33).

`model/golden.py` was read only to learn the vector format. It is used as **one of two references** (§2.4). It is not the spec, and its sequencer is itself an interpretation of the SPEC.

**Independence rule for whoever runs this plan:**
- Requirements below cite SPEC sections, never RTL.
- RTL comments, designer tests and designer assertions do not count as evidence.
- Where SPEC is silent, the item is listed in §8 as `SPEC-AMB-nn`, and the test checks the reading most likely to cause harm.

---

## 0. Toolchain (checked read-only on the sandbox, 2026-11-11, IIC-OSIC-TOOLS 2026.10 via `scripts/iic`)

| Tool | Version | Use |
|---|---|---|
| Icarus Verilog | 14.0 (devel s20260301) | primary cocotb simulator (4-state; X checks) |
| Verilator | 5.052 | lint (`--lint-only -Wall`), fast long runs, `--coverage`, random init `+verilator+rand+reset+2` |
| cocotb | 2.1.0 | TB framework. **2.x API:** `cocotb.start_soon`, `Timer(.., unit=)`, `LogicArray` values, runner in `cocotb_tools.runner`. Do not copy 1.x examples |
| yosys / sby | yosys + sby present | formal (BMC, k-induction, cover) |
| SMT solvers | **only `yices-smt2` on PATH** (no z3, boolector, bitwuzla) | sby engines: `smtbmc yices`, `abc pdr` (built into yosys). Record this in env notes |

**Runs.** Everything runs on the sandbox, inside the container, from a frozen copy `regr/tt/C9-<sha>`, with `nice` and `timeout`, at most 5 own processes.

**Proposed layout (verification tree only):**
- `verif/c9/` holds `tb/`, `ref/`, `formal/`, `mutants/` (throwaway, never committed back) and `Makefile`;
- results go to `/home/mempool/regr/tt/C9-<sha>/`.

---

## 1. Feature list and requirements

**ID scheme:** `REQ-C9-<area>-nn`.

**Timing classes:**
- **CE** = cycle-exact;
- **B** = bounded (a stated number of clk cycles);
- **EV** = eventual.

**Notation:**
- `c` = fs cycle in a slot (0 … N+1);
- `n = c − 2` = conversion cycle;
- `div` = clk per fs cycle;
- clk = 48 MHz.

### 1.1 CoI decimator (DEC)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| DEC-01 | order 2: acc1 = S = Σ y[n], acc2 = Σ S **exclusive** (`acc2 += acc1` before `acc1 += y`), y ∈ {+1, −1}, n = 0..N−1 | §3.7, §3.7a, golden README | CE per frame |
| DEC-02 | order 1: acc1 as DEC-01; **acc2 keeps accumulating ΣS exactly as in order 2** (defined value) | §3.7a f | CE |
| DEC-03 | exactly N bits accumulated per slot (bit_valid high for n = 0..N−1 only); N ∈ {64, 256, 1024, 4096} from n_code | §1, §3.7a k | CE |
| DEC-04 | acc1/acc2 output as 32-bit two's complement, **correctly sign-extended** (acc2 min ≈ −N²/2 = −8,386,560 at N 4096, so the hi word must be 0xFF80; acc1 = −4094 means hi = 0xFFFF) | §3.7, §3.7a c | CE |
| DEC-05 | no overflow or wrap at N 4096 for any bitstream (all +1, all −1 after y[0], alternating) | §3.7 width row, golden streams | CE |
| DEC-06 | accumulators clear on the edge that ends c = 1 (the edge that releases rst_analog); there is no carry-over from the previous slot | §3.6 rule 11, §3.7a i, k | CE |
| DEC-07 | no on-chip sys sign: accumulators stay in the modulator frame | §3.7a j | CE |

### 1.2 Forced y[0] and bitstream (Y)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| Y-01 | y[0] = +1 forced at n = 0 (y_force 1-cycle strobe), whatever the comparator shows at n = 0 or in the reset window | §3.7a a, k | CE |
| Y-02 | **one retimed FF** drives the DAC output, the decimator input and raw_pin (they are never different) | §3.6 rule 9, §3.7a a | CE |
| Y-03 | raw_pin = 0 while bit_valid = 0 | §3.7a k, §3.8a debug | CE |
| Y-04 | debug: y changes on the **falling** edge of the exported fs bit clock | §3.8a debug | CE (clk) |

### 1.3 Chop sequencer and reset window (SEQ)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| SEQ-01 | a slot is N+2 fs cycles; rst_analog = 1 on c = 0, 1 only | §1, §3.7a i, k | CE |
| SEQ-02 | sys_swap = 1 on odd slots iff the slot's active sys_en = 1; it changes only on c = 0 and is held for the whole slot | §3.6 seq rules, §3.7a b, k | CE |
| SEQ-03 | tag chop bit = sys_swap, from the same flop, every cycle; with sys_en = 0 the chop bit is 0 in every slot | §3.7a c, golden trace `tag_chop` | CE |
| SEQ-04 | OTA chop phase is 0 for c = 0, 1 and equals n mod 2 for n ≥ 0 when ota_en = 1; it is 0 at all times when ota_en = 0 | §3.6 rule 7, §3.7a i, k | CE |
| SEQ-05 | OTA-only mode (ota_en 1, sys_en 0) is legal and is not forced to sys | §3.7a g | CE |
| SEQ-06 | short, order (int2 hold), boost and trim outputs to the analog side follow the **active** config, change only at the latch edge | §3.7a d | CE |

### 1.4 Config: serial write, shadow, latch (CFG)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| CFG-01 | 16-bit shift register, MSB first, `cfg_dat` sampled on the rising edge of `cfg_clk`; a rising edge of `cfg_ld` copies the register into the shadow. All three inputs pass a 2-FF sync | §3.8a config | B |
| CFG-02 | a short shift (< 16 clocks) loads the last 16 bits received | §3.8a | CE |
| CFG-03 | field map: [12] order, [11:10] n_code, [9:7] fs_div, [6] sys_en, [5] ota_en, [4] short, [3] boost, [2:0] trim; [15:13] reserved | §3.8a table | CE |
| CFG-04 | reset values: order 1 (= order 2), n_code 3, fs_div 1, sys_en 1, ota_en 1, short 0, boost 0, trim 100 | §3.8a, D47 | CE |
| CFG-05 | the shadow is copied to active on the edge that starts the reset window (c = 0) of an **even** slot only; last write wins; a write on or after that edge goes to the next pair; a write in the last cycle of the previous slot latches | §3.7a d, k; golden `seq_edge`, `seq_multiwrite` | CE |
| CFG-06 | the latched set is order, N, fs_div, sys_en, ota_en, short, boost, trim (all of bits 12:0) | §3.7a d, §3.8a, G3-1 | CE |
| CFG-07 | cfg_pending (status[13]) = shadow ≠ active | §3.8a status | CE |
| CFG-08 | fs_div codes: 0 → clk/12, 1 → /24, 2 → /48, 3 → /96, 4 → /192, codes 5–7 act as 1 (/24) | §3.8a, G3-2 | CE |
| CFG-09 | cfg_clk up to clk/4 with cfg_dat stable ≥ 2 clk around the edge: no bit lost or doubled | §3.8a | B |

### 1.5 Invalid flag (INV)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| INV-01 | both frames of pair 0 after rst_n release are `invalid` | §3.7a e, D45 e, D46a | CE |
| INV-02 | both frames of the first pair after a latched change of any field of the set (including boost and trim) are `invalid` | §3.7a e, G3-1 | CE |
| INV-03 | a latched value equal to active is not a change: no invalid | §3.7a k | CE |
| INV-04 | only that pair is invalid; the next pair is valid unless another change latches | §3.7a e | CE |
| INV-05 | `invalid` and `frame_ready` are independent | §3.7, §3.7a c | CE |

### 1.6 Frame, tag, hold register, overrun (FRM)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| FRM-01 | tag word = chop[15], order[14], n_code[13:12], sys_en[11], ota_en[10], short[9], invalid[8], frame_ctr[7:0], all describing **the frame's own slot** | §3.7a c | CE |
| FRM-02 | frame_ctr +1 per sub-conversion, wraps 255 → 0, never reset by a config change, reset to 0 only by rst_n; frame_ctr[0] = slot parity | §3.7a c | CE |
| FRM-03 | hold register (acc1, acc2, tag, boost, trim) loads on the edge that ends c = N+1 of every slot | §3.8a buffering | CE |
| FRM-04 | frame_ready is set at the load and cleared by a qualified `rd` edge | §3.8a | CE/B |
| FRM-05 | a load while frame_ready = 1 overwrites the hold register with the newest frame and sets overrun; overrun is cleared by a qualified `rd` | §3.8a, G3-3 | CE |
| FRM-06 | `rd`: 2-FF sync plus rising-edge detect. It clears frame_ready and overrun **only if frame_ctr is unchanged since the last status read**; otherwise the clear is suppressed | §3.8a pins | B |
| FRM-07 | status word = [15] frame_ready, [14] overrun, [13] cfg_pending, [12] boost and [11:9] trim **of the hold-register frame**, [8] 0, [7:0] hold frame_ctr | §3.8a, D48(4), G3-6 | CE |
| FRM-08 | the hold register is stable between loads (no tearing except at the load edge) | §3.8a | CE |

### 1.7 Read bus and debug bus (BUS)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| BUS-01 | bus[15:8] = uo_out, bus[7:0] = uio_out; uio_oe = 0xFF always (including during reset) | §3.8a pins | CE |
| BUS-02 | addr 0 = acc1[31:16], 1 = acc1[15:0], 2 = acc2[31:16], 3 = acc2[15:0], 4 = tag, 5 = status, 6–7 = 0. Golden `wire` = words 0..4 concatenated | §3.8a, G3-4 | B (≤ 3 clk settle) |
| BUS-03 | dbg = 1: uo[0] raw y, [1] bit_valid, [2] frame_ready, [3] fs bit clock, [4] rst_analog, [5] sys_swap, [6] ota_chop_phase, [7] invalid (of the hold frame); uio = status[7:0] | §3.8a debug | CE |
| BUS-04 | exported fs bit clock has period = div clk exactly at every fs_div | §3.8a, §3.6 | CE |
| BUS-05 | no X or Z on uo_out/uio_out/uio_oe at any time after the first clk edge with rst_n low | TT rules, §3.8a | CE |

### 1.8 Reset (RST)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| RST-01 | rst_n asserts asynchronously and releases synchronously | §3.8a rst_n | CE |
| RST-02 | while rst_n is low: rst_analog = 1; shadow and active at reset values; accumulators and hold cleared; frame_ready = overrun = 0; frame_ctr = 0 | §3.8a | CE |
| RST-03 | after release, the first slot starts on the next fs edge; pair 0 is invalid | §3.8a, §3.7a e | B (≤ div + sync clk) |
| RST-04 | config writes while rst_n is low have no effect (registers held at reset values) | §3.8a "while low … at reset values" | CE |

### 1.9 fs divider (FS)
| ID | Requirement | Source | Timing |
|---|---|---|---|
| FS-01 | fs = clk/{12, 24, 48, 96, 192} by code; slot length = (N+2)·div clk exactly | §3.8a, §1 | CE |
| FS-02 | an fs_div change takes effect only at the latch edge, with no runt or stretched fs cycle beyond the transition rule (SPEC-AMB-04) | §3.7a d | CE |

**Out of C9 scope (owned elsewhere, listed so nobody assumes they are covered):**
- non-overlap phase generation and OTA-chop edge placement inside the non-overlap interval (§3.6 rule 13);
- level shifters (§3.7);
- the comparator itself.

If the designer puts the non-overlap generator inside the C9 RTL, add REQ-C9-NOV-01..03: no overlap; dead time ≥ spec at every fs_div; glitch-free at enable and at reset release.

---

## 2. Testbench architecture

```
              +-------------------- cocotb (Python) --------------------+
 seed/test -> | stimulus seqs | host BFM (bus/rd) | cfg BFM (serial)    |
              |      |               |                   |              |
              |  analog-side BFM: comparator driver (ybits / comp_raw0) |
              +------|---------------|-------------------|--------------+
                     v               v                   v
              [ DUT: tt_um_* wrapper  (or c9_core for formal) ]
                     |  ui_in / uo_out / uio_out / uio_oe / analog-side ports
              +------v------------------------------------------------- +
              | passive monitors: pin monitor (48 MHz), debug-bus mon,   |
              | analog-side control mon (rst_analog, sys_swap, ota_ph,   |
              | short/order/boost/trim), hold/status sampler             |
              +------|-------------------------------------------------- +
                     v
              scoreboard <- ref model A (TB, from SPEC) <- golden v3 (ref B)
              always-on protocol checkers (cocotb + SVA bind for formal)
              coverage collector (cocotb-coverage or own bins)
```

### 2.1 DUT boundaries
1. **Top: the `tt_um_*` wrapper.** All black-box tests drive and observe TT pins (ui_in, uo_out, uio_*, rst_n, clk, ena) plus the analog-side ports.
2. **Core (`c9_core`, or whatever the designer calls it).** Used for formal and for faster unit runs.

**Requirement on the designer (DfV request, not an RTL edit by verification).** The fs-rate sequencer must run off a 1-clk `fs_tick` enable, so formal can treat `fs_tick` as a free input and bind properties without an N·div-deep BMC. Without it, formal on the latch/swap rules is limited to k-induction with hand-written strengthening invariants.

### 2.2 Analog-side BFM (comparator driver)
- Drives the comparator input from golden `ybits` for n = 1..N−1.
- Drives **`comp_raw0`** at n = 0 and all through the reset window (golden README, REVIEW-S6 M1). With a pass-through RTL, y[0] is then −1 and the frame fails.
- Adversarial modes:
  - (a) junk bits in the reset window toggling every clk;
  - (b) the comparator changing at the worst clk in the fs period (just before and just after the RTL's sample edge);
  - (c) X on the comparator input during rst_n low and in the reset window, which must not propagate to acc/raw_pin/bus.
- **Blocked by SPEC-AMB-01** (comparator sample instant). The BFM must be told the sample edge from a published port contract, not from the RTL.

### 2.3 Host BFM and config BFM
- **Host BFM: legal mode.** RP2040-PIO-like. Drives addr, waits ≥ 3 clk, samples the 16-bit bus. Order: words 0..4, then status last, then rd. Implements the SPEC discard rule (overrun set, or tag frame_ctr ≠ status frame_ctr).
- **Host BFM: illegal or adversarial mode** (flagged in the log):
  - addr changed with less than 3 clk settle;
  - addr walked through Gray-unsafe transitions (3 → 4 passes 5 transiently);
  - rd pulses of 1, 2 and 3 clk;
  - rd held high across loads;
  - rd edges at load −3 … +3 clk;
  - rd with no status read since reset.
- **Config BFM:**
  - parametrised cfg_clk rate (clk/4 up to clk/400);
  - setup/hold at exactly 2 clk, plus a flagged illegal 1 clk;
  - short shifts (0, 1, 15, 17, 32 clocks);
  - cfg_ld placed with clk resolution relative to the latch edge;
  - cfg_ld with no preceding clocks;
  - cfg_ld held high;
  - glitch pulses on cfg_clk.

### 2.4 Reference models (two, both independent of RTL)
- **Ref A (`verif/c9/ref/c9_ref.py`).** Written by verification from SPEC §3.7a/§3.8a. Cycle-level at clk resolution: divider, slot/c counter, latch, invalid, tags, hold, frame_ready/overrun, rd guard, status, bus mux. Its integer CoI loop follows DEC-01 alone. It must not import `model/golden.py` or `model/iadc.py`.
- **Ref B: golden v3 vectors** (`golden/s6_vectors.json`, format 3 after WO-33). Fixed expected words for mode/offset/stream vectors, sequences and the control trace.
- **Agreement check.** Ref A must reproduce every golden v3 frame, sequence and `trace_ctl` row before it is used on random stimulus. **A disagreement is triaged as a SPEC ambiguity, not resolved by picking one.**
- **Golden is fs-cycle granular.** Write offsets, the latch edge and the trace are in fs cycles. Ref A adds clk-level behaviour (sync latency, divider phase, rd guard) that golden does not define. Those checks rest on SPEC text only and on §8.

### 2.5 Scoreboard and checkers (always on in every test)
- **Per frame:** compare acc1, acc2 (32 b), the tag, and the status-word boost/trim/frame_ctr against Ref A for **every** slot (via debug mode, or a hidden-port monitor on the hold register), and against golden where a vector exists.
- **Host side:** every frame the host reads is compared word by word. Every frame it discards must be one that the rule says to discard; a false discard is a failure.
- **Control monitor**, per fs cycle against Ref A:
  - rst_analog, acc_clear (if exposed), sys_swap, ota phase, y_force, bit_valid, raw_pin, tag_chop, cfg_latch;
  - the golden `trace_ctl` replays all 396 rows.
- **Pin-level protocol checks:**
  - uio_oe == 0xFF;
  - no X/Z on outputs after the first reset clk;
  - addr 6/7 read 0;
  - debug mapping;
  - y toggles only at the falling edge of the bit clock.
- **Watchdog.** Each test has a clk budget of 1.2 × the expected slots × (N+2) × div, plus 1000. A hang is a FAIL.
- **End-of-test checks** (§11 false-pass list):
  - frames compared ≥ the expected count (line/frame count checked; an empty compare is a FAIL);
  - no pending expected frames;
  - the test name's stimulus actually ran (the bench logs the slot count and the configs seen);
  - exit code ≠ 0 on any FAIL, checked by the runner script, which also fails on a missing results file.
- **Seeds.** Every random test logs its seed; `SEED=<n> make <test>` reproduces it.

### 2.6 Simulation cost
- **Icarus at clk level:** ≈ 0.1–0.5 Mclk/s with cocotb per-clk callbacks (estimate; measure in smoke).
- **Largest single slot:** N 4096 at fs_div 4 = 4098 × 192 ≈ 0.79 Mclk.
- **Rules:**
  - drive and sample on the fs-strobe or on monitor events, not on every clk, where possible;
  - long and soak runs use Verilator;
  - N 4096 × fs_div 4 is covered by ≥ 2 directed slots, not by random.

### 2.7 Lint and gate level
- `verilator --lint-only -Wall` must be clean or have explained waivers.
- Yosys `check -assert` reports no latches, no multi-drivers and no combinational loops.
- **GL:** LibreLane netlist with sky130 `-DFUNCTIONAL -DUNIT_DELAY`. Replay all directed tests, golden sequences, `trace_ctl`, and 20 random seeds (SDF if available).
- **VDPWR axis (§6):** STA at the 1.62/1.8/1.98 V digital corners is the signal-integrity gate. Simulation does not replace it.

---

## 3. Threat model (how C9 is most likely to fail)

| Threat | Category | Tests |
|---|---|---|
| T01 inclusive S instead of exclusive (acts like k/c1 = 5) | arithmetic | D-DEC-01, golden all |
| T02 acc2 narrower than 24 b or acc1 narrower than 14 b; sign-extension to 32 b broken (zero-extended from the internal width) | width | D-DEC-03, D-DEC-04 |
| T03 N−1 or N+1 bits accumulated; bit_valid off by one at either end | counter boundary | D-DEC-02, A-SEQ-01 |
| T04 accumulators cleared one edge early (loses n = 0) or late (carries junk), or not cleared | reset/incremental | D-DEC-05, trace |
| T05 y[0] passes the comparator through; DAC and decimator see different y | init | D-Y-01, D-Y-02 |
| T06 sys swap one fs cycle (or one clk) late or early, or toggling mid-slot | timing | A-SEQ-02, F-01 |
| T07 tag chop from a different flop than sys_swap (skewed at the edges); chop = 1 with sys_en = 0 | ordering | A-SEQ-03 |
| T08 OTA phase not restarted per slot, toggling in reset, or running with ota_en = 0 | state | A-SEQ-04 |
| T09 config latched immediately, on odd slots, or on every slot | protocol | D-CFG-05..07, F-02 |
| T10 write on the exact latch edge counted for this pair (off-by-one-clk across sync latency) | CDC/edge | A-CFG-01 |
| T11 invalid on the first frame only, not after rst_n, set on an equal write, or set on cfg_pending instead of on change | flags | D-INV-01..04 |
| T12 frame_ctr reset on config change; 7-bit; not wrapping; hold frame_ctr vs live counter confusion | counter | D-FRM-02, golden `seq_wrap` |
| T13 tag/status boost/trim from the new active config at a load edge that coincides with the latch edge (even slot start) | same-edge race | A-FRM-01 |
| T14 rd clears a frame loaded between the status read and the rd edge (lost frame); rd level-sensitive; rd unsynchronised | CDC/race | A-FRM-02..05 |
| T15 overrun not set, not sticky, or cleared by the next load | flow control | D-FRM-04, A-FRM-06 |
| T16 word order (addr 1↔2, hi↔lo) swapped; reserved addr returns garbage | mapping | D-BUS-01 |
| T17 fs_div reserved codes map to 0 (4 MHz) instead of 1 (2 MHz): runs the analog off-spec | illegal encoding | D-FS-02 |
| T18 fs_div change mid-pair, or a runt fs cycle at the change edge | clocking | A-FS-01 |
| T19 rst_n mid-slot leaves the hold, frame_ready, frame_ctr or analog reset in a partial state; release not synchronised | reset | A-RST-01..04 |
| T20 X from un-reset flops into the bus or the tag (iverilog X-as-false hides it) | X-prop | X-01 (Verilator random init × 8 seeds) |
| T21 serial config: bit lost at cfg_clk = clk/4; short shift clearing; LSB-first; cfg_ld level- not edge-triggered | protocol | D-CFG-01..04 |
| T22 status-read detection on a combinational addr that glitches through 5 | glitch/CDC | A-FRM-07 (SPEC-AMB-02) |

---

## 4. Directed and adversarial tests

**Conventions:**
- every test runs the always-on checkers of §2.5;
- "golden" means a bit-exact compare against v3;
- "ref" means a compare against Ref A.

**Prefixes:**
- `S-` smoke;
- `D-` directed;
- `A-` adversarial;
- `R-` random;
- `X-` X/init;
- `GL-` gate level.

### 4.1 Smoke
| Test | REQ | Intent | Stimulus / expect |
|---|---|---|---|
| S-01 reset & idle | RST-02, BUS-01/05, CFG-04 | the TB works | rst_n low for 10 clk: every reset value; status = 0x0000 except the reset fields; no X |
| S-02 one pair | DEC-01, INV-01, FRM-01..04 | first frames | default config (order 2, N 4096, fs_div 1); golden `o2_sys…` pair. Both frames invalid; frame_ready rises at the c = N+1 end edge |
| S-03 golden replay, quick set | all DEC/Y/FRM | bench sanity | 64 mode vectors at N 64/256 |

### 4.2 Decimator and bitstream
| Test | REQ / threat | Intent | Stimulus / expect |
|---|---|---|---|
| D-DEC-01 golden full replay | DEC-01..03, T01 | bit-exact every mode | all 320 mode + 48 offset vectors (v3 adds boost/trim variants). Every frame compared; the count of frames compared is checked |
| D-DEC-02 N boundary | DEC-03, T03 | off-by-one N | each N; ybits with a single −1 at n = N−1 and a single −1 at n = 0 (n = 0 is forced to +1, so the expected acc1 is N). A 1-bit difference in acc1 detects N±1 |
| D-DEC-03 N 4096 width | DEC-04/05, T02 | width + sign ext | golden streams `st_o2_allp` (acc2 = 8,386,560 = 0x007F F800), `st_o2_pm` (acc2 negative ≈ −8.38e6: hi word 0xFF80), `st_o2_alt`, `st_o1_allp`. Plus a TB-only stream: y[0] = +1, then all −1 at order 1 (acc1 = −4094, hi word 0xFFFF) |
| D-DEC-04 hi-word sign | DEC-04, T02 | zero-extension from 24 b | read all four acc words for every negative frame; hi words must equal the sign extension |
| D-DEC-05 back-to-back extremes | DEC-06, T04 | incremental clear | slot t all +1, slot t+1 all −1, alternating for 8 slots at N 64 and N 4096. Each frame is independent of the previous one |
| D-DEC-06 order 1 acc2 | DEC-02 | defined acc2 | order 1 golden vectors: acc2 matches ΣS (not 0, not held) |
| D-Y-01 forced y0 | Y-01, T05 | pass-through | comp = −1 (junk) on n = 0 and through c = 0, 1, in every slot. raw_pin[n = 0] = 1, acc as golden |
| D-Y-02 one FF | Y-02, Y-03 | DAC ≠ decimator | per fs cycle: DAC-feedback port = raw_pin (debug) = the bit the decimator accumulated (inferred from Ref A). raw_pin = 0 outside bit_valid |
| D-Y-03 debug y edge | Y-04, BUS-04 | setup to the bit clock | at every fs_div: y changes only within 1 clk of the bit-clock falling edge, and the bit-clock period = div |

### 4.3 Sequencer and chop
| Test | REQ / threat | Intent | Stimulus / expect |
|---|---|---|---|
| A-SEQ-01 control trace | SEQ-01..04, Y-01, CFG-05 | cycle-exact | replay golden `trace_ctl`: all 396 rows × 9 fields, per fs cycle |
| A-SEQ-02 swap timing | SEQ-02, T06 | swap late or early | every chop mode × N 64 × 8 slots. sys_swap edges occur only at c = 0 (clk-exact: the clk where c becomes 0) with rst_analog = 1. Counted: ≥ 4 rising and ≥ 4 falling edges seen, otherwise vacuous |
| A-SEQ-03 tag chop flop | SEQ-03, T07 | tag skew | at every clk, the debug sys_swap equals the live tag chop (needs a hidden-port or monitor on the tag source; fallback: status/tag at every load). With sys_en = 0, chop = 0 in every slot |
| A-SEQ-04 OTA phase | SEQ-04/05, T08 | restart | ota-only, ota+sys, off, sys × N 64/256. Phase 0 at c = 0, 1, then n mod 2; with ota_en = 0 it is 0 everywhere |
| D-SEQ-05 analog outputs follow active | SEQ-06 | early apply | write short/boost/trim/order mid-slot. The analog-side outputs change only at the next even-slot c = 0 |

### 4.4 Config
| Test | REQ / threat | Intent | Stimulus / expect |
|---|---|---|---|
| D-CFG-01 field map | CFG-01..03, T21 | MSB/LSB, field order | 13 walking-one writes, each latched. The tag fields, status boost/trim and fs period reflect exactly one field |
| D-CFG-02 short and long shifts | CFG-02 | shift semantics | shifts of 0, 1, 15, 17, 32 clocks before cfg_ld, plus two consecutive short shifts. The shadow equals the last 16 received bits (SPEC-AMB-07 decides "received since reset" vs "since the last ld") |
| D-CFG-03 rate limit | CFG-09 | sync loss | cfg_clk = clk/4 with exactly 2-clk setup/hold. Then a flagged-illegal clk/3: report only, not a fail |
| D-CFG-04 reserved bits | CFG-03 | reserved effects | bits 15:13 = 111 with the other fields equal to active. No invalid, no behaviour change; cfg_pending per SPEC-AMB-05 |
| D-CFG-05 golden sequences | CFG-05/06, INV-* | latch rules | `seq_cfgchange`, `seq_multiwrite`, `seq_edge`, `seq_short`, plus v3 boost/trim sequences; all frames and tags golden |
| D-CFG-06 write in every slot phase | CFG-05, T09 | latch slot parity | single writes at c = 0, 1, 2, N/2, N+1 of an even slot and of an odd slot. Latch slot = the next even slot strictly after the write edge |
| D-CFG-07 config write during a pair | CFG-05, SEQ-06, INV-02 | mid-pair apply | write in slot 2k (pair started) and in slot 2k+1. Pair k is unchanged and valid; pair k+1 runs the new config and is invalid |
| A-CFG-01 clk-resolution edge | CFG-05, T10 | sync-latency off-by-one | cfg_ld rising edge placed at clk offsets −6 … +6 around the even-slot c = 0 edge (accounting for 2-FF latency). Before the edge (effective shadow update before it): latches now; on or after: next pair. Ref A defines "effective" = the clk at which the synchronised ld updates the shadow (SPEC-AMB-03) |
| A-CFG-02 write-back to active | INV-03 | equal write | write X ≠ active, then write the active value before the edge: no invalid, cfg_pending 1 → 0. Also a single write equal to active: no invalid |
| A-CFG-03 write during rst_n | RST-04 | ignored | full write while rst_n is low; after release the config is at reset values and pair 1 is not invalid for a change |
| D-CFG-07b boost/trim latch | CFG-06, INV-02, G3-1 | G3 items | change boost only, and trim only, mid-pair. Latched at the pair boundary, the pair is invalid, status [12:9] of each frame = the frame's own value |

### 4.5 Invalid, frame, hold, overrun, read bus
| Test | REQ / threat | Intent | Stimulus / expect |
|---|---|---|---|
| D-INV-01 after rst_n | INV-01 | start-up | 3 resets with 1, 2 and 5 slots between them: frames 0 and 1 are invalid after each, frame 2 is valid |
| D-INV-02 each field | INV-02/04 | scope | one test per field of the latched set (8). Both frames of the pair invalid, the next pair valid |
| D-INV-03 change on consecutive pairs | INV-02 | sticky/overlap | changes latched at pairs k and k+1: both pairs invalid, k+2 valid |
| D-FRM-01 tag word | FRM-01 | field packing | every combination of order × n_code × chop mode × short at N 64 (N 4096 only for one) |
| D-FRM-02 frame_ctr wrap | FRM-02, T12 | wrap | golden `seq_wrap` (262 slots) plus config changes at slots 254–258. The counter is unaffected, wraps 255 → 0, and parity stays the slot parity |
| D-FRM-03 hold timing | FRM-03, T13 | load edge | frame_ready rises at exactly the edge ending c = N+1 (clk-exact against Ref A). Hold content = the just-finished slot's acc and tag |
| A-FRM-01 load = latch edge | FRM-01/07, T13 | same-edge race | config change latched at slot 2k. The frame of slot 2k−1 (loaded on the same edge) carries the OLD tag/boost/trim and invalid = 0 (if pair k−1 was valid) |
| D-FRM-04 overrun | FRM-05, T15 | back-to-back | host never reads for 3 slots: overrun = 1, the hold has the newest frame, frame_ctr gap = 2. After one read-and-rd: both cleared |
| A-FRM-02 rd races frame_ready | FRM-06, T14 | lost frame | read status at slot t, then rd edges placed at clk offsets −8 … +8 around the load of frame t+1. Before the load: clear. After the load: suppressed, frame t+1 stays flagged. Exactly-on-the-load clk: must not clear (SPEC-AMB-06, harmful reading) |
| A-FRM-03 rd pulse width | FRM-06 | sync miss | rd high for 1, 2, 3 clk (1 clk flagged illegal: report). rd held high for 5 slots: one edge, one clear only |
| A-FRM-04 rd without status read | FRM-06 | guard init | rd after rst_n with no status read: behaviour per SPEC-AMB-02 (logged; the harmful reading: a clear without a read loses a frame) |
| A-FRM-05 status read then two loads then rd | FRM-05/06 | guard + overrun | rd suppressed; overrun and frame_ready stay set |
| A-FRM-06 overrun + wrap | FRM-02/05 | modulo gap | overrun spanning frame_ctr 255 → 0 → 1; the host gap computed mod 256 |
| A-FRM-07 addr glitch | FRM-06, T22 | false status read | walk addr 3 → 4 with skewed bit changes (passing 5 or 7 for 1 clk) between the status read and rd. The guard must not be re-armed by a transient (SPEC-AMB-02) |
| D-BUS-01 word map | BUS-02, T16 | order | for 50 random frames, read words 0..4 and compare with golden `wire`; addr 6, 7 read 0 |
| D-BUS-02 settle | BUS-02 | latency | change addr at every clk phase. The value is correct by ≤ 3 clk; record the actual latency |
| D-BUS-03 debug map | BUS-03 | mapping | dbg = 1 for one slot at each chop mode. All 8 uo bits and uio = status[7:0] against Ref A per clk |
| A-BUS-04 dbg toggling | BUS-03 | side effects | toggle dbg every 5 clk across a load and an rd. No effect on frame_ready/overrun/frame_ctr/config |
| D-BUS-05 host discard rule | FRM-07, §3.8a | firmware contract | with a slow host (1.5 slots per frame) the discard rule never accepts a torn frame (10k frames, Verilator) |

### 4.6 Reset and fs divider
| Test | REQ / threat | Intent | Stimulus / expect |
|---|---|---|---|
| A-RST-01 rst_n mid-conversion | RST-01/02, T19 | partial state | assert rst_n at c = 0, c = 1, n = 0, n = N/2, n = N−1, and on the load edge ±1 clk. Async: outputs at reset values within the same clk (checked at the next sample, before any clk edge); all state as RST-02 |
| A-RST-02 short and glitch reset | RST-01 | async path | rst_n low for 1 clk, and low for < 1 clk between edges (async assert must still reset). Release 1 clk later |
| A-RST-03 release alignment | RST-03 | sync release | release rst_n at each clk phase within an fs period, at every fs_div. Slot 0 c = 0 begins within the bound, and the first slot has full length N+2 |
| A-RST-04 reset during cfg shift and during rd | RST-04, FRM-06 | stale sync | rst_n mid-shift: after release the shift register does not carry partial bits into a later ld (SPEC-AMB-07); rd high through the release does not produce a clear |
| D-FS-01 every code | FS-01, CFG-08, BUS-04 | divider table | codes 0..7 × N 64. fs period = 12/24/48/96/192/24/24/24 clk; slot = (N+2)·div |
| D-FS-02 reserved codes | CFG-08, T17 | illegal encoding | codes 5, 6, 7 from active 1: fs = 2 MHz. Change or not per SPEC-AMB-05 (harmful reading: no invalid flag, yet an analog change happens) |
| A-FS-01 fs_div extremes and changes | FS-02, T18 | runt cycles | 0 → 4, 4 → 0, 1 → 0 at N 64, N 4096 at code 4 (2 slots, Verilator). The bit-clock period sequence around the latch edge matches Ref A's transition rule (SPEC-AMB-04); no period shorter than min(old, new) |

### 4.7 Random, soak, X, gate level
- **R-01 constrained-random sequencer.** 200 seeds × 64 slots, N 64/256 (biased 70 % to N 64).
  - Config writes weighted toward the latch edge ±3 clk (40 %), the last cycle of an odd slot (20 %), mid-slot (40 %), with multi-writes and equal writes.
  - Random ybits with the junk comp_raw0.
  - The host reads with random latency, biased so the rd edge lands at load ±4 clk.
  - Ref A compares everything.
- **R-02 random bitstreams at N 4096.** 20 seeds × 2 slots per order. DC densities 0, 0.5, 1 and a sine.
- **SOAK-01 (Verilator).** 10⁶ slots at N 64 (≈ 0.8 Gclk at fs_div 0), all knobs on, 10 seeds. Pass = no failures in the last ≥ 20 % of the runs.
- **X-01.** Verilator `+verilator+rand+reset+2` × 8 seeds plus iverilog X-init.
  - After rst_n release, nothing on the outputs depends on the init value (Verilator runs compare bit-identical across seeds).
  - In iverilog: no X on any output after the first reset clk.
  - The iverilog checker uses `!==`/`===`; X is never treated as false.
- **GL-01.** The §2.7 GL replay set.

---

## 5. Assertions and formal properties

Written as SVA in a `bind` file (`verif/c9/formal/c9_props.sv`) for sby on `c9_core`, plus the same rules as cocotb checkers (§2.5) on the wrapper.

**Formal strategy:**
1. BMC on reduced-depth harnesses. Needs an `fs_tick` free input (§2.1 DfV) and N forced to 64 by assumption on n_code.
2. k-induction (`smtbmc yices` or `abc pdr`) for the safety set.
3. Cover properties to prove each corner is reachable.

**Non-vacuity:**
- each assert has a paired cover of its antecedent;
- an initial-state assumption is that reset is asserted in cycle 0, so k-induction does not start from an undefined state;
- each property must fail on at least one mutant in §6.

| ID | Property (informal → SVA intent) | REQ |
|---|---|---|
| F-01 | **swap only in the reset window:** `$changed(sys_swap) |-> (c == 0) && rst_analog` (on fs_tick granularity: the swap changes only on the tick that starts c = 0) | SEQ-02 |
| F-02 | **latch only at the pair boundary:** `$changed(active_cfg) |-> (c == 0) && slot_parity == 0 && $past(fs_tick)` (or rst_n low) | CFG-05 |
| F-03 | **write-to-latch:** `shadow != active && fs_tick && next c == 0 && next slot even |=> active == $past(shadow)` | CFG-05 |
| F-04 | **frame_ctr:** changes only at a hold load or rst_n; at a load, `frame_ctr == $past(frame_ctr) + 1 (mod 256)`; the hold frame_ctr[0] equals the parity of the slot just ended | FRM-02 |
| F-05 | **wrap:** `$past(frame_ctr) == 255 && load |-> frame_ctr == 0`; plus a cover | FRM-02 |
| F-06 | **invalid after change:** if a latch event changes the active set, both frames whose slots belong to that pair have tag invalid = 1, and the following pair has invalid = 0 unless another change latches | INV-02/04 |
| F-07 | **invalid after rst_n:** the first two loads after release have invalid = 1 | INV-01 |
| F-08 | rst_analog ↔ (c ∈ {0, 1}) or rst_n low; acc_clear only at c = 1 | SEQ-01, DEC-06 |
| F-09 | ota_phase == 0 whenever rst_analog or !ota_en_active | SEQ-04 |
| F-10 | tag_chop == sys_swap at every clk; `!sys_en_active |-> !sys_swap` | SEQ-03 |
| F-11 | `overrun |-> frame_ready` (overrun is set only by a load while frame_ready = 1, and both clear together) | FRM-05 |
| F-12 | the hold register is stable unless a load occurs | FRM-08 |
| F-13 | rd guard: a clear of frame_ready never happens on a clk where `frame_ctr != frame_ctr_at_last_status_read` | FRM-06 |
| F-14 | bit_valid high for exactly N fs ticks per slot (counter-based auxiliary) | DEC-03 |
| F-15 | accumulator range invariants: `−n ≤ acc1 ≤ n`, `|acc2| ≤ n(n−1)/2` at n accumulated bits (no overflow) | DEC-05 |
| F-16 | uio_oe == 8'hFF always | BUS-01 |
| F-17 | the divider's fs period equals the table at every code, under an assumption that fs_div is stable | FS-01 |

**Covers:** C-01..C-12:
- every n_code latched;
- a latch with pending in both parities;
- overrun set;
- rd suppressed by the guard;
- rd clear;
- frame_ctr wrap;
- invalid from each field;
- sys_swap rise and fall;
- OTA phase 1;
- rst_n mid-slot;
- a load on the latch edge;
- a write on the latch edge.

**If the designer does not expose `fs_tick`**, F-01..F-14 run by simulation only (the cocotb checkers). Formal is then limited to F-11, F-12, F-16 and F-17, plus BMC to a depth of 2 slots at N 64 / fs_div 0 (≈ 1600 clk), which is likely too deep for yices. This is logged as a coverage hole.

---

## 6. Mutation list

Mutants are throwaway copies under `verif/mutants/` (never committed back). Each one is run against the full regression minus soak. **Pass = killed by at least one test.** The kill rate is reported. A survivor gets a new test, or a waiver with a reason.

### 6.1 PLAN mutants (PLAN row C9, review additions)
| # | Mutant | Killing test(s) |
|---|---|---|
| M01 | acc2 width 23 b (wraps at N 4096) | D-DEC-03 (`st_o2_allp`, `st_o2_pm`), F-15 |
| M02 | acc1 width 13 b | D-DEC-03 (`st_o2_allp` acc1 = 4096) |
| M03 | N−1 bits accumulated | D-DEC-02, D-DEC-01, F-14 |
| M04 | N+1 bits accumulated (includes a reset-window bit) | D-DEC-02, D-Y-01 |
| M05 | sign: y inverted into the accumulator (−1 ↔ +1) | D-DEC-01 |
| M06 | sign: chop tag inverted (swapped slot tagged 0) | D-FRM-01, A-SEQ-03, golden offset vectors |
| M07 | sys swap one fs cycle late (changes at c = 1) | A-SEQ-01, A-SEQ-02, F-01 |
| M07b | sys swap one **clk** late (changes 1 clk after c = 0 starts) | A-SEQ-02 (clk-exact), F-01. Golden (fs-granular) cannot kill it; this checks the clk-level checker |

### 6.2 Own mutants
| # | Mutant | Killing test(s) |
|---|---|---|
| M08 | inclusive S (`acc1 += y` before `acc2 += acc1`) | D-DEC-01 |
| M09 | acc sign-extension broken (zero-extend from 24 b in the hi word) | D-DEC-03 `st_o2_pm`, D-DEC-04 |
| M10 | y[0] pass-through (no force) | D-Y-01, every golden frame |
| M11 | DAC driven from the unforced comparator, decimator from the forced bit | D-Y-02 |
| M12 | acc_clear one fs cycle early (at c = 0) | data-equivalent (bit_valid = 0 in c = 0, 1, so no bit is lost): killable only through the control trace if acc_clear is observable (A-SEQ-01 on a hidden port, F-08). If it is not observable, this is an equivalent mutant: waive with that reason |
| M13 | acc_clear one fs cycle late, or never (carry-over) | D-DEC-05 |
| M14 | raw_pin not gated by bit_valid | D-Y-02, A-SEQ-01 |
| M15 | OTA phase not restarted at n = 0 (free-running fs/2 toggle across slots) | N+2 is always even, so a free-running toggle realigns every slot and only shows as toggling inside the reset window: killed by A-SEQ-04 ("0 in reset") and F-09. A free-running phase that is not forced to 0 in reset is the variant to inject |
| M16 | OTA phase runs when ota_en = 0 | A-SEQ-04 |
| M17 | tag chop from a separate flop updated at the hold load (1 slot skew) | A-SEQ-03, D-FRM-01 |
| M18 | chop bit = slot parity regardless of sys_en | D-FRM-01 (sys_en = 0 vectors) |
| M19 | config latched immediately (at cfg_ld) | D-CFG-07, `seq_short`, F-02 |
| M20 | latch on every slot start (odd included) | D-CFG-06, F-02 |
| M21 | latch on odd slots | D-CFG-06 |
| M22 | write on the latch edge counted for the current pair | `seq_edge`, A-CFG-01 |
| M23 | write in the last clk before the edge deferred | A-CFG-01, `seq_edge` |
| M24 | invalid on the first frame of the pair only | D-INV-02, `seq_cfgchange` |
| M25 | no invalid after rst_n | D-INV-01, S-02 |
| M26 | invalid on any write (an equal write counts as a change) | A-CFG-02 |
| M27 | boost/trim excluded from the change compare | D-CFG-07b, D-INV-02 |
| M28 | boost latched mid-pair (immediate) | D-CFG-07b, D-SEQ-05 (WO-33 broken copy) |
| M29 | trim reset 000 | S-01, CFG-04 (WO-33 broken copy) |
| M30 | frame_ctr reset on config change | D-FRM-02 |
| M31 | frame_ctr 7 bits | D-FRM-02 (`seq_wrap`) |
| M32 | hold loads at c = 1 of the next slot (late, same acc values) | D-FRM-03 (frame_ready clk-exact), A-FRM-01 (tag of the new config) |
| M33 | hold loads 1 fs cycle early (misses the last bit) | D-DEC-02, D-FRM-03 |
| M34 | tag/status boost/trim taken from active, not from the hold | A-FRM-01, D-CFG-07b |
| M35 | overrun never set | D-FRM-04 |
| M36 | overrun cleared by the next load | D-FRM-04, A-FRM-05 |
| M37 | rd clears unconditionally (no frame_ctr guard) | A-FRM-02, A-FRM-05, F-13 |
| M38 | rd level-sensitive (clears while high) | A-FRM-03 (rd held high across loads) |
| M39 | rd without synchroniser (raw edge) | A-FRM-02 (clk-offset table differs by 2 clk), X-01 if metastability is modelled; **likely survivor in RTL sim → static CDC check (yosys/verilator lint rule or a manual review) as a waiver path** |
| M40 | frame_ready not cleared by rd | D-FRM-04 (WO-33 broken copy) |
| M41 | word order addr 1 ↔ 2 | D-BUS-01 (WO-33 broken copy) |
| M42 | hi/lo swapped within acc2 | D-BUS-01 |
| M43 | addr 6/7 alias addr 4/5 | D-BUS-01 |
| M44 | debug bits [5] ↔ [6] swapped | D-BUS-03 |
| M45 | uio_oe = 0x00 in reset | S-01, F-16 |
| M46 | fs_div table off by one code (0 → /24) | D-FS-01 |
| M47 | reserved fs_div → code 0 (4 MHz) | D-FS-02 |
| M48 | fs_div applied immediately (not latched) | A-FS-01, F-02 |
| M49 | serial config LSB first | D-CFG-01 |
| M50 | cfg_dat sampled on the falling cfg_clk edge | D-CFG-01, D-CFG-03 |
| M51 | cfg_ld level-sensitive | D-CFG-02 (cfg_ld held high while shifting) |
| M52 | shift register cleared at ld (short-shift semantics) | D-CFG-02 |
| M53 | synchronous rst_n assert | A-RST-01 (async check), A-RST-02 (sub-clk pulse) |
| M54 | rst_n does not clear the hold or frame_ready | A-RST-01 |
| M55 | short not in the latched set | `seq_short`, D-INV-02 |
| M56 | cfg_pending inverted, or compared against the hold config | D-CFG-04, A-CFG-02 |
| M57 | y updated on the bit-clock rising edge | D-Y-03 |
| M58 | bit clock period = div + 1 | D-FS-01, BUS-04 |
| M59 | status frame_ctr = live counter instead of the hold frame_ctr | D-FRM-03, A-FRM-01 |

**Formal-only check:** each F-xx property must fail on at least one of M07, M07b, M19–M22, M24, M30, M31, M35–M37, M45. A property that fails on none is reported as vacuous.

---

## 7. Coverage model and sign-off

### 7.1 Functional coverage bins (cocotb collector, dumped as JSON per seed and merged)
- **CV-MODE:**
  - order {1, 2} × n_code {0..3} × chop {off, sys, ota+sys, ota} × short {0, 1} = 64 bins;
  - boost {0, 1} × trim {0, 4, 7} on at least N 64 and N 4096 (G3).
- **CV-FS:** fs_div {0..7} × n_code {0, 3}, plus transitions {0 → 4, 4 → 0, 1 → 0, any → reserved}.
- **CV-WRITE-PHASE:**
  - write effective at {latch edge −3..+3 clk, even c = 0, 1, 2, mid, N+1, odd c = 0, mid, N+1 last clk};
  - × {single, multi, equal-to-active, write-back} × {field changed: each of 8};
  - × `pending at rst_n`.
- **CV-RD:**
  - rd edge at {load −8..+8 clk} × {status read since the last load: yes/no} × {frame_ready 0/1} × {overrun 0/1};
  - rd pulse width {1, 2, 3, ≥ 4 clk, held}.
- **CV-OVR:** consecutive unread loads {1, 2, 3, ≥ 10}; overrun across a frame_ctr wrap.
- **CV-CTR:** frame_ctr {0, 1, 254, 255 → 0}; a config change at the wrap.
- **CV-RST:** rst_n assert at {c = 0, c = 1, n = 0, mid, n = N−1, load edge ±1, during a cfg shift, during rd high, during dbg = 1}; release phase {each clk of an fs period at fs_div 0 and 4}.
- **CV-ADDR:** addr {0..7} × dbg {0, 1} × {stable, glitch transition}.
- **CV-DATA:** acc1 sign {+, −, 0}; acc2 {min region (< −2²²), max region (> 2²²), 0}; hi word ∈ {0x0000, 0xFFFF, 0x007F, 0xFF80}.

### 7.2 Code coverage
Verilator `--coverage` (line, toggle, branch) merged across the regression.
- Every uncovered line is reviewed and explained as unreachable or untested, and recorded in agent memory `coverage-holes.md`.
- **Toggle target:** every bit of acc1 [13:0], acc2 [23:0] and the sign bit toggles. Bits above the sign must toggle via sign-extension through negative frames.

### 7.3 Sign-off criteria (C9 is not "verified" unless all hold, or a waiver is recorded)
1. Entry gate: golden v3 landed (WO-33), sha pinned; Ref A agrees with every v3 frame, sequence and trace row.
2. **Every REQ-C9 maps to ≥ 1 passing test, ≥ 1 checker and ≥ 1 coverage bin.** The matrix is §1 × §4 × §7.1.
3. Golden replay: every v3 mode, offset, stream, sequence and trace item bit-exact. The count of compared frames equals the count in the vector file, and that count is printed.
4. Functional coverage 100 % of non-waived bins; code coverage holes explained line by line.
5. Formal: F-01..F-17 proven, either unbounded (k-induction/PDR) or at a stated BMC depth with its justification; all covers hit. Each property fails on at least one mutant.
6. Mutation: kill rate reported. Target 100 % of M01–M59. Survivors are fixed by a new test or waived with a reason (M39 is the likely candidate: a static CDC review instead).
7. Random: R-01 at 200 seeds plus SOAK-01, clean, with no new failure in the last ≥ 20 % of runs; seeds logged.
8. Lint clean (Verilator -Wall, yosys check); X-01 clean.
9. GL-01 clean on the LibreLane netlist; STA clean at VDPWR 1.62/1.8/1.98 V and all digital corners (PLAN C9).
10. Zero open Critical/High bugs; every SPEC-AMB in §8 answered by the coordinator/user, or the test is labelled "assumed reading".
11. V5 (PLAN): the transistor-top bitstream through the RTL decimator gives the Python reconstruction bit-exact. This is outside C9 sign-off, but C9 provides the RTL and the comparator BFM contract.

---

## 8. SPEC ambiguities (for the coordinator; SPEC not edited)

| ID | Where | Ambiguity | Interpretations | Harmful reading tested |
|---|---|---|---|---|
| SPEC-AMB-01 | §3.7, §3.7a a, §3.8a | **No digital ↔ analog port contract.** SPEC does not define, at clk resolution: the comparator sample instant within the fs period; the latency from comparator to DAC (one retimed FF, but on which edge); the polarity of rst_analog, sys_swap, ota phase, short, order-hold, boost and trim; or which block makes the phase clocks. A black-box TB cannot drive the comparator without it | (a) sample on the fs-cycle start edge; (b) mid-cycle (the falling bit-clock edge) | the BFM changes comp ±1 clk around both candidate edges (D-Y-01, R-01); the result must stay bit-exact for the published edge. **Needs a contract before C9 RTL tests start** |
| SPEC-AMB-02 | §3.8a `rd` | **"Unchanged since the last status read" with a combinational, strobe-less `addr`.** The chip cannot see a read. Is a "status read" = addr == 5 sampled (synchronised) for ≥ k clk? Does a transient 5 during an addr change (3 → 4 = 011 → 100) count? Does dbg = 1 (uio shows status[7:0]) count? What does the guard do before any status read? | (a) snapshot of hold frame_ctr whenever sync(addr) == 5; (b) snapshot at the last rd edge; (c) snapshot at the load | A-FRM-02/04/07: a transient or missing read must never arm a clear that drops an unread frame |
| SPEC-AMB-03 | §3.7a d, k, §3.8a config | **Write time at clk resolution.** Golden is fs-cycle granular ("a write at offset 0 goes to the next pair"). With a 2-FF sync and edge detect, which clk counts as the write: the pin edge of cfg_ld, or the shadow update 2–3 clk later? SPEC says "the write time counts as the write cycle" but does not define the write time | (a) shadow-update clk; (b) pin edge | A-CFG-01 sweeps ±6 clk; Ref A uses (a) and logs the boundary clk |
| SPEC-AMB-04 | §3.7a d, §3.8a | **fs_div change transition.** At the latch edge (c = 0 of an even slot, the start of an old-divider fs cycle), does the new divider apply to that very cycle or to the next fs edge? Is the divider counter restarted? Does the hold load use the old fs? Is the exported bit clock glitch-free? | (a) the new period starts at c = 0; (b) the old cycle completes first | A-FS-01: check for no runt period and a slot length of (N+2)·div_new for the first new slot under (a) |
| SPEC-AMB-05 | §3.8a table | **Reserved encodings.** Is a write of fs_div 5 when active = 1 a "change" (invalid, cfg_pending)? Is fs_div stored as written (5) or normalised (1)? Do the reserved bits 15:13 count for cfg_pending ("shadow differs from active")? The tag has no fs_div field, so firmware cannot see it either way | (a) stored raw: change → invalid; (b) normalised: no change | D-FS-02, D-CFG-04: the harmful case is a flag mismatch with the actual analog behaviour. Either reading is acceptable if cfg_pending and invalid agree with each other |
| SPEC-AMB-06 | §3.8a | **rd edge on the same clk as a load.** Is the guard compared against frame_ctr before or after the load? | pre-load → clears the new frame (harmful); post-load → suppressed | A-FRM-02 requires "suppressed" |
| SPEC-AMB-07 | §3.8a config | **Short shift "loads the last 16 bits received".** Since reset, or since the last cfg_ld? Is the shift register reset by rst_n (§3.8a lists shadow and active only)? | (a) a continuous shift register, not cleared at ld; (b) cleared at ld | D-CFG-02, A-RST-04: after rst_n, a short shift must not load pre-reset bits (harmful) |
| SPEC-AMB-08 | §3.8a rst_n, status | **Status and hold values after reset, before the first load.** The hold is "cleared" (tag invalid = 0, trim field = 000), yet the reset trim is 100. A firmware that polls without checking frame_ready sees an all-zero frame flagged valid | (a) hold = 0, status trim 000; (b) status trim = active reset 100; (c) hold tag invalid = 1 | S-01 records the value; recommend (c) or document that frame_ready gates everything |
| SPEC-AMB-09 | §3.8a rst_n | **"The first slot starts on the next fs edge."** Does the fs divider run during reset (so the release-to-slot latency is phase-random, up to div clk) or restart at release? | (a) restart; (b) free-running | A-RST-03 checks the bound ≤ div + 3 clk and a full-length first slot |
| SPEC-AMB-10 | §3.8a status | **Which frame_ctr does the guard compare** (the hold frame_ctr or the live slot counter)? The status word shows the hold one | hold vs live | A-FRM-02 |
| SPEC-AMB-11 | §3.8a read timing | **"≥ 3 clk settle" vs "combinational select".** If the bus is combinational, a host can see glitching words; if it is registered or synchronised, 3 clk is the latency. The read timing contract is not stated as a requirement | combinational vs registered | D-BUS-02 measures the latency and requires ≤ 3 clk |
| SPEC-AMB-12 | §3.8a pins | **TT `ena` and `uio_in` are not mentioned.** Is `ena` ignored (always 1 on TT)? Is behaviour with ena = 0 defined? | ignore vs gate | logged; S-01 runs with ena = 1 and one smoke with ena = 0 (report only) |
| SPEC-AMB-13 | §3.8a debug | **"Fs bit clock": free-running fs, or gated with bit_valid? Duty cycle?** It is needed for the logic-analyser sampling claim (y on the falling edge) | free-running 50 % | D-Y-03 |
| SPEC-AMB-14 | §3.7a e | **Change latched while the current pair is already invalid** (e.g. pair 0 after rst_n, with a write latching at slot 2): pair 1 is invalid. The golden sequencer agrees. Also: does rst_n during a pending write drop the pending write? (SPEC: the shadow is at reset values, so yes) | — | D-INV-03, A-CFG-03 (no ambiguity in effect; listed for confirmation) |
| SPEC-AMB-15 | §3.6 rule 13, scope | **Non-overlap generator and OTA-chop edge placement: C9 or analog (C7/C8)?** If the edge rule is in C9, it needs clk-level timing requirements (dead time in clk) that SPEC does not give | — | out of scope until assigned (§1.9) |
| SPEC-AMB-16 | golden README vs §3.7a d | **The golden README (v2) lists the latched set without boost/trim** (pre-G3). §3.7a d includes them | resolved by WO-33 (v3) | entry gate |

---

## 9. Order of work (when RTL lands)
1. Ref A plus its agreement with golden v3 (no RTL needed).
2. The always-on checkers and BFMs.
3. S-01..03.
4. The D- tests.
5. The A- tests.
6. R-01.
7. X-01.
8. Formal (needs the DfV `fs_tick`).
9. Mutation M01–M59.
10. SOAK.
11. GL.

**Blocked items:**
- step 2 (comparator BFM) waits for the SPEC-AMB-01 contract;
- formal waits for the DfV request;
- the A-FRM rd tests wait for SPEC-AMB-02.

## 10. What this plan does not verify (risk)
- **Metastability:** RTL sim cannot show it. The 2-FF syncs (rd, cfg_*) are checked only structurally (lint/CDC review) and by clk-offset sweeps.
- **The analog side:** level shifters, phase non-overlap and comparator timing margins. These belong to C7/C8/V-rows; at C9 only the digital contract is covered.
- **Substrate/digital noise coupling** into the first integrator (§3.9, V9).
- **Firmware:** the host discard rule is checked against a model host only.

## 11. WO-42 additions (verification, 2026-11-12)

### 11.1 Static CDC review of the async inputs (RTL structure, read-only; no tool)
| Input | Crossing in RTL (c9_core / c9_rdbus) | Verdict |
|---|---|---|
| rst_n | `r1`, `rs`: async clear, 2-FF synchronous release; every block's reset is `rs` | OK: async assert, sync release (CL-19, D70) |
| cfg_clk, cfg_dat, cfg_ld, rd | 2-FF (`sck`, `sdat`, `sld`, `srd`), reset by `rs`; edges detected after the second flop | OK, 1 b each. cfg_dat is sampled on the synchronised cfg_clk edge, so the 3.8a rule "cfg_dat stable >= 2 clk around the cfg_clk edge" is a requirement on the host |
| addr[2:0], dbg | 2-FF per bit (`a1`/`a2`, `d1`/`d2`), then the registered word | A multi-bit crossing without Gray coding or a handshake. During an addr change, a2 can hold a mixed code for 1 clk, so the bus can show a wrong word for 1 clk. That is inside the CL-21 3-clk settle; it is not a bug if the host waits 3 clk |
| comp_in | one flop `comp_s`, enabled on s_tick (falling edge of the bit clock, CL-23) | No synchroniser, by design: the comparator is clocked from the same clk domain. The analog contract must state that the comparator output is resolved before s_tick. Analog item (C7/C8), not C9 |
| uio_in, ena | unused (`_unused`) | OK (CL-20) |

Metastability itself is not simulated (waiver kept). M39 (rd without a sync) is covered by this review.

### 11.2 Functional bins as implemented (tb/fcov.py), with reductions to 7.1
- CV-WRITE-PHASE uses 15 phases × 4 kinds (60 bins) plus 8 field bins plus pending-at-rst_n. The phases are e−3..e+3 around the even latch edge (at the synchronised update), then even c0/c1/c2/mid/N+1 and odd c0/mid/N+1 outside that window. The 3-way phase × kind × field cross is split into phase × kind and field.
  - Unreachable: multi and write-back at e+0..e+3. They need a second synchronised update ≤ 3 clk after the latch edge, but cfg_ld pulses are ≥ 4 clk apart: cfg_ld uses the cfg_clk pin rate, and SPEC does not state a cfg_ld width (SPEC-AMB-24).
- CV-RD is split into the rise offset −8..+8 (17 bins) and the state {status read} × {frame_ready} × {overrun}.
  - Unreachable: frame_ready 0 with overrun 1.
- CV-RST: the release-phase bins are dropped. Under D70 the divider restarts at release, and the reset config is always fs_div 1.
- Directed coverage tests: c01_mode_sweep, c02_fs_sweep, c03_write_phase, c04_rd_bins, c05_ctr_wrap, c06_rst_pos, c07_addr. R-01 was rewritten to follow §4.7: edge, odd-last and mid write weighting, equal and multi writes, and rd aimed at load ±4.
- F-01 is strengthened: a sys_swap change is allowed only on the edge where rst_analog rises (cycle 0) and fs_clk rises. It must fail on M07, M07b and M19.
