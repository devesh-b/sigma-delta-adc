# WO-82 (C9u): D88 bias-count restart on drop (RTL and SPEC CL-37)

Coordinator-written, 2026-11-14. **Tier: code (Sonnet).** Fresh agent.

## Change (D88)
- **AMB-30.** In `design/c9_digital/rtl/c9_seq.v`, `b_ctr` stops counting once `b_ctr[BIAS_BITS]` is set (see around line 51). It must instead:
  - clear on any low `bias_ok_s` sample until release, so release needs `bias_ok` high for the last 256 consecutive fs cycles;
  - keep counting while high, saturating at done; it must not wrap.

  `pw_ctr` behaviour and the sticky-after-release behaviour are unchanged.
- **AMB-31.** fs_clk keeps toggling during the hold. That is the current behaviour; no RTL change.

## Items
1. Make the RTL change: the smallest edit, with parameters unchanged. Run lint and synth on the sandbox (IIC-OSIC-TOOLS via `scripts/iic`). Report the FF/cell delta against df9bded (259 FF, 1068 cells).
2. **SPEC:**
   - Add CL-37 (D88) to the change log. It replaces the sticky wording in CL-36 (b).
   - In the §3.8a rst_n paragraph (SPEC.md ~line 295):
     - slot 0 = the first fs_tick whose pre-edge state has pw done AND a bias run ≥ 256;
     - a bias_ok drop during the hold restarts the bias count;
     - sticky only after release;
     - fs_clk toggles during the hold (AMB-31).
   - Give the updated slot-0 formula in place of max(2^16, J)+1, where J is now the tick at which the **last** uninterrupted 256-run completes.
3. Say exactly what the bench, Ref A, mutants (M66, M68) and F18 must change. Do not touch `tb/`; the verification agent handles it next.

## Rules
- Sandbox only. No local tool runs and no local python.
- Never write in `/home/mempool/tt`.
- Write only `design/c9_digital/rtl/` and `SPEC.md`.
- Commit with explicit paths, no trailers, no push. If signing blocks, list the paths.

## Budget
At most 20 tool calls. Report in ≤ 15 lines.
