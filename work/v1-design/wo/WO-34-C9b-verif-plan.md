# WO-34 (C9b): independent verification plan for the C9 digital block

Coordinator-written, 2026-11-11. **Agent: rtl-verification-engineer (read-only on design).** Runs in parallel with WO-33. Sources:
- SPEC.md §3.7a, §3.8, §3.8a, G3 list;
- D45–D48;
- PLAN.md row C9 and the review additions (C9: chop swap only in the reset window + "swap one cycle late" mutant; frame tags);
- `golden/README.md`;
- `model/golden.py` (reference only).

Derive intent from SPEC, not from any RTL (none exists yet).

## Deliverable
`work/v1-design/C9_VERIF_PLAN.md`, covering:
1. **Feature list:**
   - CoI decimator, order 1/2, N 64–4096;
   - exclusive acc2;
   - forced y[0];
   - chop sequencer and reset window;
   - shadow-latch config over the serial interface, with boost/trim;
   - frame build + tag;
   - hold register / overrun;
   - 16-bit parallel read bus (addr/rd);
   - fs_div;
   - debug bus;
   - rst_n behaviour and invalid flags.
2. **Testbench architecture:** cocotb + iverilog/verilator in IIC-OSIC-TOOLS; golden-vector replay; scoreboard; reference model use.
3. **Directed and adversarial tests,** including corner cases:
   - N = 4096 accumulator width and overflow;
   - config write during a pair;
   - rd racing frame_ready;
   - back-to-back frames / overrun;
   - rst_n mid-conversion;
   - fs_div extremes;
   - chop swap timing.
4. **Assertions / formal properties** (SVA or cocotb checks):
   - chop swap only in the reset window;
   - latched config only at a pair boundary;
   - frame_ctr wrap;
   - invalid after change.
5. **Mutation list:** every PLAN mutant (acc width, off-by-one N, sign, swap one cycle late) plus your own, each with the test that kills it.
6. **Coverage model and sign-off criteria.**
7. **SPEC ambiguities found:** list them; do not edit SPEC.

Budget: at most 25 tool calls. Report in ≤ 40 lines with the file path.
