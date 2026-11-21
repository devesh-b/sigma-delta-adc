# WO-99: missing glue blocks for the top: C6 output stage, VICM/VOCM, Cint2 reset, top-choice review

Coordinator-written, 2026-11-21. **Tier: design (Opus).** Fresh agent. Plan: `TAPEOUT_10D.md`.

## Why
WO-94 (a9a416f, `results/wo94/README.md`) found that the top cannot simulate as-is:
- (1) There is no final C6 subckt. The xschem c6_bias was built from the c6_spot tran core at R1 144.8 / ratio 2.45; the generator defaults are 94 / 4.6, a disagreement.
- (2) C6 has no **port mirrors to the OTA bias nets (`o1_*`)**, no **boost**, and no **3-bit trim**. `vicm`/`vocm` have no source.
- (3) There is no Cint2 reset switch: `r2_t`/`r2_c` are unconnected.
- (4) Several top choices are not defined by any generator: the internal-short node = vicm; DAC and Ck2 polarity per side; an hd nand2 for `dec`; lsbufhv2lv_1 for bias_ok.

## Items
1. **C6 final subckt** (`design/c6_bias/`): the option (c) core at the WO-80/87 values (R1 144.8 µm, R2/R1 2.45), with the generator defaults made to agree.
   - Output stage: a mirror per bias port that OTA1 and OTA2 need (from the C1 port list; D91 says the mirrors are shared), with per-port currents per SPEC/C1.
   - The boost switch per D-boost.
   - The 3-bit trim (±19 %, D73).
   - The real `bias_ok`.
   - Verify: port currents at 9 corners, compliance, trim steps, boost toggle settling ≤ 4 µs, and own current ≤ 6 µA (the mirror current is separate).
   - Each gate needs a broken copy.
2. **VICM/VOCM generation:** the source of the input CM and the output CM references for both OTAs, per SPEC/II.2.10 (C5/C7). Choose the simplest compliant circuit, for example a resistor divider plus a buffer, or a diode reference. State its current against the "2 µA per OTA" placeholder in WO-93.
3. **Cint2 reset switch:** size it from the C4 switch rules, and connect r2_t/r2_c per SPEC (incremental reset of integrator 2; order-1 follower mode, D74).
4. **Review the WO-94 top choices** against SPEC/DESIGN_BOOK: the vicm short node, DAC and Ck2 polarity, `dec` gate, and the bias_ok level shift. Fix any that are wrong, and state each fix.
5. **Hand-off:** the subckt files, and a one-line patch list for xschem regeneration (WO-94's `sch_gen.py`) and for the WO-95 top deck.
6. Write `results/wo99/README.md`.

## Rules
- Sandbox only. Connect with `ssh -o HostName=49.207.248.15 -p 22181 -o HostKeyAlias=mempool.lan sandbox`.
- Frozen copy `/home/mempool/regr/tt/WO-99-<sha>`. Use lpool v3 with `PRIO=high`. Source the venv and nix PATH. Use absolute paths. Wait on markers only.
- No local python. Do not change OTA1, OTA2 or C3 sizes.
- Write only `design/c6_bias/`, `design/c4_sw/` (the reset switch only), a new `design/c5c7_ref/`, and `results/wo99/`.
- Commit with explicit paths, no trailers, no push.

## Budget
At most 45 tool calls. Report in ≤ 25 lines. Target D2–D3.
