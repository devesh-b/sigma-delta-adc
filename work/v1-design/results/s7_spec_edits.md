# WO-19 (S7): SPEC edit log and step-gate results

## Step-settling gate (S7-M1), job `python design/tier1/step_settle.py --o1` on the sandbox (outputs `/home/mempool/regr/tt/WO-19/`, no csv, `.meas` only)

Macromodel: gen_tier1 v2 elements (diff gm, tanh tail-current slew, loaded C_L, second pole 3 x GBW), closed loop with factor beta, ideal step at t = 0, A0 = 1e8. Gate options: reltol 1e-8, vntol 1e-10, abstol 1e-15, trtol 1 (O1 reads exactly 0 for OTA1: vntol 1 uV and reltol 1e-4 are above the 1e-8 residue, so O1 is shown only as a cross-check; OTA2 O1 agrees to 3 %).

| Point | fs | GBW / SR | beta, C_L | max step | eps | eps_NL | limit (2 x) | GBW/2 | SR/2 |
|---|---|---|---|---|---|---|---|---|---|
| OTA1 base | 2 MHz | 10 MHz / 12.5 V/us | 0.84, 1.4 pF | 0.486 V | 1.62e-8 | 4.6e-10 | 4e-8 / 1e-9 | 6.4e-5 REJECT | 4.8e-8, NL 2.8e-8 REJECT |
| OTA1 boost | 4 MHz | 20 MHz / 25 V/us | 0.84, 1.4 pF | 0.486 V | 1.62e-8 | 4.6e-10 | 4e-8 / 1e-9 | 6.4e-5 REJECT | 4.8e-8 REJECT |
| OTA2 base | 2 MHz | 10 MHz / 13.5 V/us | 0.497, 0.7 pF | 1.117 V | 6.78e-4 | 1.2e-4 | 1.4e-3 / 2.5e-4 | 2.3e-2 REJECT | 8.5e-3 REJECT |
| OTA2 boost | 4 MHz | 22.5 MHz / 27 V/us | 0.497, 0.7 pF | 1.117 V | 2.96e-4 | 6.1e-5 | 6e-4 / 1.3e-4 | 1.4e-2 REJECT | 5.6e-3 REJECT |

- OTA1 worst step 0.125 x 1.9 x 2.048 = 0.486 V. OTA2 worst step (loop bound) = c2 |x1|max + (Ck2/Cint2) VREF = 0.5 x 1.21 + 0.25 x 2.048 = 1.117 V; it exceeds SR x tau (0.43 V), so OTA2 numbers are slew dominated and a typical step is much smaller (open: coordinator may restate the OTA2 gate on a typical step).
- Reviewer's hand estimate 6e-5: the macromodel at spec gives 1.6e-8 (about 4000 x lower: the hand number is what a GBW of half the spec would give, 6.4e-5). SPEC uses 6e-5 as the proposed C1 transistor-OTA limit and the 2 x macro numbers as the tier-1 macro gate.
- Tests: `design/tests/test_tier1.py` (window, metric/gate failure cases incl. NaN, ngspice points with both broken copies). pytest on the sandbox: 152 passed.

## SPEC / PLAN / DECISIONS edits (old -> new, truncated to 160 chars each; full text is in the git diff)

1. **E21 status line**  
   old: `Status: draft for design, pre-silicon. Rev 2026-11-07b: review fixes applied (VREF/model mismatch, TG input switch, PGA x1/x2 in v1, GBW/slew derivations, raw a`  
   new: `Status: v1 spec, pre-silicon, freeze candidate. Rev 2026-11-09 (S7, WO-19): REVIEW-S7 edits E1-E24 applied, digital I/O table §3.8a added, no PGA in v1 (D14, D4`
2. **E21 PGA mention**  
   old: `secondary modes (DC/ratiometric monitoring, thermocouple/shunt with PGA, analog entropy-source recovery)`  
   new: `secondary modes (DC/ratiometric monitoring, thermocouple/shunt (needs a PGA: stretch, not v1), analog entropy-source recovery)`
3. **E5 Output rate**  
   old: `| Output rate | fs/N: e.g. 2 MHz/1024 ≈ 1.95 kSPS; firmware averages K sub-conversions to reach 3.75–240 SPS | slow precision via averaging + system chop |`  
   new: `| Output rate | one frame (sub-conversion) per N + 2 fs cycles (N conversion cycles + 2-cycle reset window, §3.7a k): fs/(N+2), e.g. 2 MHz/1026 ≈ 1.95 kSPS; fir`
4. **E5 N row**  
   old: `| N (cycles/conversion) | 64 / 256 / 1024 / 4096;`  
   new: `| N (conversion cycles per sub-conversion, plus 2 reset cycles) | 64 / 256 / 1024 / 4096;`
5. **E21 PGA row**  
   old: `| PGA | **none in v1 (user Q3: shared Cs)**; ×2 / ×4 / ×8 stretch via a separate Cs:Cref ratio |`  
   new: `| PGA | **none in v1 (user Q3/D14: shared Cs; the config field is removed, D45h)**; ×2 / ×4 / ×8 stretch via a separate Cs:Cref ratio |`
6. **E17 power row**  
   old: `| Power (analog) | ≤ 200 µA | OTA dominates |`  
   new: `| Power (analog) | ≤ 200 µA design budget (D46c); ≈ 106–113 µA precision incl. bandgap, ≈ 172 µA fast (boost = 1, resets to 0) | OTA dominates; worst case after`
7. **E6 2.1 header**  
   old: `### 2.1 Full-scale, LSB, and the swing constraint`  
   new: `### 2.1 Full-scale, LSB, and the swing constraint (historical, pre-S3; §1 and §3.0 govern: VREF 2.048 V, c1 0.125, k 0.5)`
8. **E6 2.1 F2 OPEN**  
   old: `- **Input CM (review F2, OPEN — user Q1):**`  
   new: `- **Input CM (review F2; closed by D12, user Q1: CM-rejecting input switching):**`
9. **E7 2.2 header**  
   old: `### 2.2 Input-referred noise targets (model, Cs=1 pF, fs=2 MHz)`  
   new: `### 2.2 Input-referred noise targets (historical: model at Cs = 1 pF, pre-D22; §3.0 budget governs, 0.94 µV @15 SPS at Cs 0.5 pF)`
10. **E7 2.2 targets**  
   old: `Targets: **≤ 50 µV rms @ 15 SPS (v1); ≤ 5 µV (stretch).**`  
   new: `Targets (superseded by §3.0 / D27: ≤ 2.5 µV @15 SPS, ≤ 5 µV @240 SPS): ~~≤ 50 µV rms @ 15 SPS (v1); ≤ 5 µV (stretch)~~.`
11. **E8 2.3 header**  
   old: `### 2.3 Linearity vs OTA gain (swing-dependent gain, 90% loss at full swing)`  
   new: `### 2.3 Linearity vs OTA gain (historical, pre-S3: INL values are the early model; §3.0 gives A0 ≥ 80 dB and INL ≤ 8 ppm for the OTA)`
12. **E9 3.1**  
   old: `### 3.1 OTA (first integrator — the critical path, no TT precedent)`  
   new: `### 3.1 OTA (first integrator — the critical path, no TT precedent) (informative; §3.0 governs. SR 10 V/µs, PM ≥ 60° and β 0.75/0.61 below are the pre-S3 values`
13. **E9 3.2**  
   old: `### 3.2 Comparator (1-bit quantiser)`  
   new: `### 3.2 Comparator (1-bit quantiser) (informative; §3.0 governs)`
14. **E9 3.3**  
   old: `### 3.3 Switches`  
   new: `### 3.3 Switches (informative; §3.0 governs)`
15. **E9 3.5**  
   old: `### 3.5 Reference / 1-bit DAC`  
   new: `### 3.5 Reference / 1-bit DAC (informative; §3.0 governs)`
16. **E10 3.5 tau_ref**  
   old: `on-chip reference settling τ_ref ≤ 0.2·t_half (gain error only).`  
   new: `on-chip reference settling τ_ref ≤ 10 ns (§3.0 row; = 0.044·t_half at 2 MHz, 0.089·t_half at 4 MHz; gain error only; C8 tb).`
17. **E4 3.4 header**  
   old: `### 3.4 Capacitors (MIM `cap_mim_m3_1` only; no MOS caps in signal path)`  
   new: `### 3.4 Capacitors (MIM `cap_mim_m3_1` only; no MOS caps in signal path) (values per §3.0, S7-M4)`
18. **E4 Cs2**  
   old: `| Cs2 (sample, int2) | 1 pF | | | Cint2 | 2 pF | c2 = Cs2/Cint2 = 0.5 |`  
   new: `| Cs2 (sample, int2) | **0.5 pF** (§3.0) | C_side2 2.01 pF, β2 0.497 | | Cint2 | **1 pF** | c2 = Cs2/Cint2 = 0.5 | | Ck2 (k-DAC cap, int2) | **0.25 pF** (= k·Cs`
19. **E4 density**  
   old: `with stage 2 at 1/2 pF ≈ 15 pF ≈ 7,500 µm²`  
   new: `with stage 2 at 0.5/1 pF plus Ck2 0.25 pF ≈ 12 pF (≈ 6,000 µm²; MIM total with all caps ≈ 9,000 µm², §3.0)`
20. **E11 fch**  
   old: `**OTA chop** at fch above the 1/f corner (>~631 kHz, re-characterise).`  
   new: `**OTA chop** at fch = fs/2 (D45 i; 1 MHz at 2 MHz, above the 631 kHz 1/f corner (info), 125 kHz at 0.25 MHz where the 1/f corner is not a gate).`
21. **E11 rule 11**  
   old: `frame carries   chop sign and pair index;`  
   new: `frame carries   the chop sign and frame_ctr (frame_ctr[0] marks slot a/b; no pair index);`
22. **E11 rule 12**  
   old: `(12) reset window ≥ ~15 τ of Cint discharge (1 kΩ × 8 pF ≈ 120 ns) + post-swap input   settling + OTA/CMFB recovery; optional +−−+ pair ordering cancels linear `  
   new: `(12) reset window = 2 fs cycles (≥ 1 µs at 2 MHz) and covers ≥ ~15 τ of Cint discharge (1 kΩ × 4 pF = 4 ns, so 15 τ ≈ 60 ns) + post-swap input   settling + OTA/`
23. **E11 35 uV**  
   old: `(35 µV at Vos2 9 mV, c1 0.125, N 4096)`  
   new: `(52.7 µV at Vos2 9 mV, c1 0.125, N 4096: 1.5·2·Vos2/(c1(N−1)), the 1.5 from Ck sharing the OTA2 node, §3.0)`
24. **E2 rule 10**  
   old: `(10) config   changes (N, order, chop enables, fs divider) latched only at a pair boundary, first pair after a change tagged   invalid;`  
   new: `(10) config   changes (N, order, chop enables, fs divider, short, boost, trim) latched only at a pair boundary, first pair after a change tagged   invalid;`
25. **E12 order1 + accum**  
   old: `- Order-1 mode: single accumulator.`  
   new: `- Order-1 mode: single accumulator for the result (acc1); acc2 keeps accumulating ΣS (§3.7a f). Structure (REVIEW-S7 m3, model assumption): in order 1 the compa`
26. **E12 output**  
   old: `- Output: **raw accumulators** (acc1 = S, acc2 = ΣS; up to 32 b) via shift register on uo; firmware forms   u = (acc2 + (k/c1)·acc1) / (N(N−1)/2), so no on-chip`  
   new: `- Output: **raw accumulators** (acc1 = S, acc2 = ΣS; 32 b each) read as 16-bit words over the parallel bus of §3.8a (D46b); firmware forms   u = (acc2 + (k/c1)·`
27. **E12 reset depth**  
   old: `(reset depth r ≤ 2.2e-3 at N=1024, ≤ 1.4e-4 at N=64)`  
   new: `(reset residue r ≤ 1e-4 at every N, row "Reset" of §3.0 and D46a; the earlier 2.2e-3 at N 1024 and 1.4e-4 at N 64 are superseded)`
28. **E12 valid/invalid**  
   old: `- 1.8↔3.3 V level shifters between analog macro and digital.`  
   new: `- `valid` (= frame_ready) means a complete frame is in the hold register; `invalid` (tag) means do not use it (§3.7a c, e). They are independent. - 1.8↔3.3 V le`
29. **3.7a header**  
   old: `### 3.7a Digital conventions bound to the S6 golden vectors (D45, REVIEW-S6 §5)`  
   new: `### 3.7a Digital conventions bound to the S6 golden vectors (D45, REVIEW-S6 §5). **(e), (g) and (i) are user-confirmed (D46a)**; (i) is gated by the reset-settl`
30. **E18 chop tag**  
   old: ``chop` (1 b: 0 = +1, 1 = −1),`  
   new: ``chop` (1 b: 0 = +1, 1 = −1; **with sys_en = 0 the tag chop bit is 0 in every slot**, as the golden vectors implement it: the swap never happens, so both frames`
31. **E2 (d) latch set**  
   old: `Latched set: order, N, fs divider, sys_en, ota_en, short |`  
   new: `Latched set: order, N, fs divider, sys_en, ota_en, short, **boost (1 b, reset 0), trim (3 b, reset 100)** (D31, D42; §3.8a register map) |`
32. **D46 (e)**  
   old: `| e | Invalid scope | both frames`  
   new: `| e | Invalid scope (user-confirmed, D46a; also applies to a change of boost or trim) | both frames`
33. **E19 (i)**  
   old: `its phase toggles every fs cycle and is 0 at cycle 0 of every sub-conversion;`  
   new: `its phase toggles every fs cycle and is 0 at conversion cycle n = 0 (c = 2) of every sub-conversion, and 0 throughout the reset window (c = 0, 1);`
34. **(g) V4 row**  
   old: `| g | OTA-only chop | (ota_en 1, sys_en 0) allowed, characterisation-only like every sys-off mode (D4: never used for data) |`  
   new: `| g | OTA-only chop | (ota_en 1, sys_en 0) allowed, characterisation-only like every sys-off mode (D4: never used for data). Direct measurement of the lf·Vos1/(`
35. **E2 3.8**  
   old: `- Config register (via ui pins or simple SPI): order (1/2), N, fs divider, OTA-chop en,   system-chop en, internal short (no PGA field: no PGA in v1, D45h).`  
   new: `- Config register (serial write on ui_in, §3.8a; shadow register, §3.7a d): order (1/2), N, fs divider, OTA-chop en,   system-chop en, internal short, **boost (`
36. **E21 thermocouple**  
   old: `| PGA ×4/×8 (stretch);`  
   new: `| needs PGA ×4/×8 (stretch, not v1);`
37. **E20 sec 5**  
   old: `## 5. Open items to lock before tapeout 1. **VREF vs swing** (§2.1) — settle VREF in the model against measured/sim OTA output swing. 2. **OTA-chop weighting in`  
   new: `## 5. Open items: closure map (REVIEW-S7 E20) Items 1-8 of the original list are closed or owned elsewhere; none blocks the freeze. 1. VREF vs swing: **closed**`
38. **E12 fix order-1 text**  
   old: `reconstruction u = acc1·/(N c1-normalised) as in the golden `den` = N.`  
   new: `reconstruction u = acc1/N (golden `den` = N).`
39. **E1 OTA1 gate**  
   old: `**gate = closed-loop step settling** at β1, C_L, worst step, error at t = h − 2g, base 2 MHz and boost 4 MHz (D43a);`  
   new: `**gate = closed-loop step settling** at β1, C_L, worst step ≈ 0.49 V diff (= c1(u_max + 1)·VREF = 0.125·1.9·2.048), base 2 MHz and boost 4 MHz (D43a). **Definit`
40. **E15 fp2**  
   old: `(fp2 sweep, S5h: mult 2 → 10.9, 3 → 3.36, 4 → 8.06 ppm)`  
   new: `(fp2 sweep, S5h, O1 numbers: mult 2 → 10.9, 3 → 3.36, 4 → 8.06 ppm)`
41. **E1 OTA2 gate**  
   old: `gate = closed-loop step settling at β2, both modes;`  
   new: `gate = closed-loop step settling at β2, both modes, same h, g, ε, ε_NL definitions as the OTA1 row; worst step (loop bound) = c2·|x1|max + (Ck2/Cint2)·VREF = 0.`
42. **E1 clock row**  
   old: `| Clock | Phases | t_half ≥ 225 ns at 2 MHz after non-overlap; bottom-plate early phases | hand |`  
   new: `| Clock | Phases | h = 0.5/fs, g = 0.025/fs, t_half = h − 2g = 0.45/fs (225 ns at 2 MHz, 112.5 ns at 4 MHz, 1.8 µs at 0.25 MHz); **g ≤ 0.025/fs at every corner,`
43. **D46a Reset**  
   old: `| Reset | Residue / window | r ≤ 1e-4 on x1 and x2; window ≥ 2 clock cycles (≥ 1 µs at 2 MHz) | offset 1 µV; inter-conversion memory test |`  
   new: `| Reset | Residue / window | r ≤ 1e-4 on x1 and x2; window ≥ 2 clock cycles (≥ 1 µs at 2 MHz). **Settling gate (D46a): r ≤ 1e-4 within 2 fs cycles at 4 MHz boos`
44. **D46c Current**  
   old: `| Current | Analog total | ≤ 200 µA in every mode **at every corner after trim (D42; worst ≈ 189 µA fast, ≈ 113 µA precision incl. ≈ 6 µA bandgap)**.`  
   new: `| Current | Analog total | ≤ 200 µA in every mode **at every corner after trim (D42; worst ≈ 189 µA fast, ≈ 106–113 µA precision incl. ≈ 6 µA bandgap)**. **200 `
45. **E17 118**  
   old: `boost=0 (precision, fs ≤ 2 MHz), analog ≈ 118 µA.`  
   new: `boost=0 (precision, fs ≤ 2 MHz, reset value), analog ≈ 106–113 µA incl. bandgap.`
46. **D47 trim row**  
   old: `reset code 100 (mid), latched only at a pair boundary (C9) | C6 tb + MC; broken copy: one trim leg open ⇒ monotonicity REJECT |`  
   new: `reset code 100 (mid), latched only at a pair boundary (C9). **Volatile (D47):** TT has no NVM or fuses, so firmware rewrites the trim after every rst_n; the res`
47. **E24 offset**  
   old: `(1.5 from Ck sharing the OTA2 node) | model |`  
   new: `(1.5 from Ck sharing the OTA2 node) | model; C1/C2 MC ≥ 200 runs tt/27 plus ≥ 50 at the worst PVT (§6): 3σ ≤ 9 mV and every sample inside; broken copy: input-pa`
48. **E24 1/f**  
   old: `| noise 1.0 µV, offset reserve |`  
   new: `| noise 1.0 µV, offset reserve; system-level 1/f through V9 (tier 0 with PEX parameters) |`
49. **E24 comp offset**  
   old: `| ≤ 20 mV 3σ; ≤ 5 mV rms | INL 1 ppm, noise 0.3 µV |`  
   new: `| ≤ 20 mV 3σ; ≤ 5 mV rms | INL 1 ppm, noise 0.3 µV; C3 MC ≥ 200 runs (3σ offset ≤ 20 mV, `.noise` ≤ 5 mV rms), broken copy: pair mismatch ×3 ⇒ REJECT |`
50. **E24 single bit**  
   old: `| construction + test |`  
   new: `| construction + test; RTL TB drives the junk `comp_raw0` at cycle 0 and through the reset window (golden README), broken copy y0 pass-through ⇒ REJECT |`
51. **E24 kickback**  
   old: `| gain reserve |`  
   new: `| gain reserve; C3 tb with pass number: peak disturbance on x2 ≤ 5 mV and recovered within 0.5·t_half at 4 MHz ss/−40; broken copy: isolation removed ⇒ REJECT |`
52. **E24 tau_ref**  
   old: `(u³ INL ≈ 1.4 ppm) | INL 2 ppm |`  
   new: `(u³ INL ≈ 1.4 ppm) | INL 2 ppm; C8 tb: τ_ref ≤ 10 ns at ss/−40/3.0 with the 500 Ω + 5 pF pad and 10 Ω R_ext, broken copy: reference switch Ron ×3 ⇒ REJECT |`
53. **E24 noise spec**  
   old: `| Noise spec | Condition | at u = 0 (shorted input); reference noise is a board requirement | — |`  
   new: `| Noise spec | Condition | at u = 0 (shorted input); reference noise is a board requirement | V9 only (system noise is a joint, tier-0-with-PEX result; no singl`
54. **E24 CMRR D12**  
   old: `(C4 owns).`  
   new: `(C4 owns; broken copy: D12 CM-rejecting input switching removed ⇒ sys-off CMRR below 60 dB REJECT).`
55. **E24 fast INL**  
   old: `- Fast mode (4 MHz) INL: N 64 ≤ 200 ppm, N 256 ≤ 20 ppm, N 1024 ≤ 5 ppm (D28; confirmed with option A, D39). Evidence (s5f): at the D39 boosted operating point `  
   new: `- Fast mode (4 MHz) INL: N 64 ≤ 200 ppm, N 256 ≤ 20 ppm, N 1024 ≤ 5 ppm (D28; confirmed with option A, D39); **gate: V3 at 4 MHz boost for N 256 and N 1024, rep`
56. **E14 cmrr label**  
   old: `sys on cites tier-1 cm2 137–173 dB (the model's`  
   new: `sys on cites tier-1 cm2 137–173 dB (O0 numbers, quasi-static: exempt from the O1/O2 convergence rule, D43c; the model's`
57. **E14 0.13**  
   old: `(0.13 = D12 CM step + 10 mV CMFB);`  
   new: `(0.13 = D12 CM step + 10 mV CMFB; the 0.13 V step is an O0 quasi-static number, exempt per D43c);`
58. **E16 dR**  
   old: `ΔR (VIN+ vs VIN−) ≤ 330 Ω at 2 MHz (∝ 1/fs).`  
   new: `ΔR (VIN+ vs VIN−) ≤ 250 Ω at 2 MHz at the allowed Cp,top 20 fF (330 Ω only if Cp,top ≤ 15 fF) (∝ 1/fs).`
59. **E3 insert 3.8a**  
   old: `### 3.9 Physical`  
   new: `### 3.8a Digital I/O (WO-19, D46b; proposal for coordinator review, golden v3 items marked G3) Assumed TT clock **clk = 48 MHz**. TT pins: `ui_in[7:0]` in, `uo_`
60. **3.8 pointer**  
   old: `- **Internal-short input mode**`  
   new: `- I/O pin map, read bus, buffering and register map: §3.8a. - **Internal-short input mode**`
61. **E21 OPEN Q2**  
   old: `**OPEN — user Q2:** 4 MHz = fast/low-resolution mode`  
   new: `**Closed (user Q2, D28):** 4 MHz = fast/low-resolution mode`
62. **E9 PM 60**  
   old: `| Phase margin | ≥ 60° | SC stability |`  
   new: `| Phase margin | 60° minimum (pre-S3; superseded: PM informational in §3.0, step settling gates) | SC stability |`
63. **E23 user D3/D4 -> D17/D18**  
   old: `user D3 ... (SPEC rows l.18, l.23)`  
   new: `user D17`
64. **E23 D3/D4 bottom**  
   old: `**D3 → option B (VREF 2.048 V, c1 0.125, k 0.5). D4 → keep OTA chop paired with system chop.**`  
   new: `**D17 (user D3) → option B (VREF 2.048 V, c1 0.125, k 0.5). D18 (user D4) → keep OTA chop paired with system chop.**`

## PLAN / DECISIONS edits (E22, E23)
- PLAN: C1 row (A0 80 dB, PM informational with the step gate, SR 12.5/25), S6 and C10 PGA mentions removed, V-list PGA x2 replaced, 5 extremes -> extremes per section 6 (6-8 points), new rows V4a (OTA-only chop plus reset-settling gate), V4b (trim calibration, D47), V3b (fast-mode INL).
- DECISIONS: D3 'Superseded by D17', D4 'Superseded by D18', D45 note (e/g/i confirmed by D46a, readout superseded by D46b). D46 row kept untouched.

## Open items
- Section 4 fast-mode evidence numbers (3.29/3.36, 0.144/1.450, 0.403/1.982) are copied from REVIEW-S7 section 4 without their exact labels; the reviewer should confirm which job each belongs to.
- C1 transistor limits (6e-5; OTA2 = macro limits) and the section 3.8a register map, fs_div table, status word and debug bus are proposals for coordinator and reviewer review.
- Not done: E-edit wording was written from the summary, not the reviewer transcript.

## S7b (REVIEW-S7b small edits, D48; WO: apply S7b edits)

Old → new for each edit (long rows abridged to the changed text). Code: `design/tier1/step_settle.py` and `design/tests/test_tier1.py` (commit 52842af).

1. **1 OTA1 row step gate** (`SPEC.md`)  
   old: `**Definitions (S7-M1):** h = 0.5/fs (half period), g = 0.025/fs (non-overlap), the step is applied at the start of the phase and the error is read at t = h − 2g = t_half (225 ns at 2 MHz, 112.5 ns at 4 MHz). ε(t_half) = 1 − vo(t_half)/step (dynamic residue only, A0 → ∞); ε_NL = max deviation of vo(t_half) from a least-squares line over steps 0.1–1.0 × max, divided by the max step. **Gate: |ε| ≤ ε_macro and ε_NL ≤ ε_NL,macro.** Tier-1 macromodel (OTA 12.5 V/µs / 10 MHz, β 0.84, C_L 1.4 pF at 2 MHz; 25 V/µs / 20 MHz at 4 MHz boost): measured ε 1.6e-8, ε_NL 4.6e-10 (both points), so limits ε_macro = 4e-8, ε_NL,macro = 1e-9 (2 ×, job `design/tier1/step_settle.py`, WO-19; broken copies GBW/2 and ...`  
   new: `**Definitions (S7-M1, S7b):** h = 0.5/fs, g = 0.025/fs, t_half = h − 2g (225 ns at 2 MHz, 112.5 ns at 4 MHz). **(B) In-loop gate, authoritative for INL (D48(1) option 2):** transistor OTA1 in the tier-1 deck (OTA2 behavioural), N 1024, 2 MHz ≤ 1.333 ppm and 4 MHz boost ≤ 5 ppm, O1/O2 converged, at tt/27 and ss/−40/3.0. Broken copy: tail set for 9.5 V/µs ⇒ REJECT. **(A) Step tb (report-only diagnostic, `design/tier1/step_settle.py`):** steps ±{0.1…1.0} × 0.486 V (= c1(u_max + 1)·VREF) from x1 = 0 and from ±0.72 V; ε_dyn(a) = (vo(t_half + 10τ) − vo(t_half))/a, referenced to the late value so A0 and static gain error drop out; ε_NL = max deviation of a·ε_dyn(a) from its LSQ line, divided by 0.486 V. Health check |ε_dyn| ≤ 1e-4; watch level ε_NL ≤ 3e-7 (≈ 1.333/(1.9·2): the worst-case input-referred INL is 1.9·ε_NL, slot averaging takes off 2–4×; gating it would need ≳ 14 MHz GBW, so it is n...`
2. **1 OTA2 row step gate** (`SPEC.md`)  
   old: `gate = closed-loop step settling at β2, both modes, same h, g, ε, ε_NL definitions as the OTA1 row; worst step (loop bound) = c2·|x1|max + (Ck2/Cint2)·VREF = 0.5·1.21 + 0.25·2.048 ≈ 1.12 V diff, slewing since it exceeds SR·τ ≈ 0.43 V. Tier-1 macromodel (13.5 V/µs / 10 MHz at 2 MHz; 27 V/µs / 22.5 MHz at 4 MHz, β2 0.497, C_L 0.7 pF): ε 6.8e-4 / 3.0e-4, ε_NL 1.2e-4 / 6.1e-5, limits (2 ×) ε_macro 1.4e-3 / 6e-4, ε_NL,macro 2.5e-4 / 1.3e-4, C1 limit = the same numbers (open: the 1.12 V bound is not a typical step; coordinator may restate on a typical step)`  
   new: `gate = closed-loop step settling at β2, both modes, same h, g, t_half and the ε_dyn definition (late-value reference, 10τ) as the OTA1 row (A); start states x2 = 0 and ± half the x2 peak (≈ ±0.6 V diff); worst step (loop bound) = c2·|x1|max + (Ck2/Cint2)·VREF = 0.5·1.21 + 0.25·2.048 ≈ 1.12 V diff, slewing since it exceeds SR·τ ≈ 0.43 V; a typical ≈ 0.5 V step is informational only. Tier-1 macromodel (13.5 V/µs / 10 MHz at 2 MHz; 27 V/µs / 22.5 MHz at 4 MHz, β2 0.497, C_L 0.7 pF): ε_dyn 6.8e-4 / 3.0e-4, ε_NL 1.2e-4 / 6.1e-5 (report-only); limits (2 ×) on ε_dyn: ε_macro 1.4e-3 / 6e-4; C1 limit = the same ε_dyn numbers on the 1.12 V step. **Plus (B)** as a V-row: transistor OTA2 in the in-loop tier-1 deck (OTA1 behavioural or transistor), N 1024, as the OTA1 (B) INL limits, with the same pass numbers used as the reference for the transistor OTA2`
3. **3 provenance l.127** (`SPEC.md`)  
   old: `N 1024 3.29 / 3.36 ppm (verdict 3.43 ppm), A′ 0.144 / 1.450 ppm, N 256 0.403 / 1.982 ppm (figures as listed in REVIEW-S7 §4; job names in `results/s5h_tier1.md`)`  
   new: `D39 control (option-A point, OTA2 20.25 V/µs ≤ A′ 27, conservative): 3.29 / 3.36 ppm O1 / O2, verdict 3.43 ppm; A′ N 1024 (c) cold / (d) hot 0.144 / 1.450 ppm, O2 only; A′ N 256 cold / hot 0.403 / 1.982 ppm, O1 only (gate 20) (labels per REVIEW-S7b m2; job names in `results/s5h_tier1.md`)`
4. **4 l.216 50 µV** (`SPEC.md`)  
   old: `sys-only meets 50 µV even at lf 9.3`  
   new: `sys-only meets the ≤ 2.5 µV @15 SPS target even at lf 9.3`
5. **4 l.230** (`SPEC.md`)  
   old: `each word carries chop sign`  
   new: `each frame carries (tag word) chop sign`
6. **4 3.7a(c) valid pin** (`SPEC.md`)  
   old: `The `valid` pin = data-ready strobe for a complete frame.`  
   new: ``frame_ready` (status[15]; debug uo[2]) marks a complete frame.`
7. **4 l.22** (`SPEC.md`)  
   old: `**External / ratiometric only**, no bandgap in v1`  
   new: `**External / ratiometric only**, no on-chip voltage reference; bandgap-type bias current only (C6)`
8. **4 3.7a(i) duplicate hold rule** (`SPEC.md`)  
   old: ` and 0 throughout the reset window (c = 0, 1); it is held at 0 throughout the reset window (rule 7)`  
   new: ` and 0 throughout the reset window (c = 0, 1) (rule 7)`
9. **4 §1 noise** (`SPEC.md`)  
   old: `noise ota+sys 0.71 µV @15 SPS`  
   new: `noise 0.94 µV @15 SPS governs (joint model, §3.0); 0.71 µV is the kT/C-only Cs-row value`
10. **5 m6** (`SPEC.md`)  
   old: `a logic analyser samples the bit stream on the rising edge of the fs bit clock.`  
   new: `y changes on the **falling** edge of the exported bit clock (half an fs period of setup), so a logic analyser samples the bit stream on the rising edge of the fs bit clock.`
11. **5 m7** (`SPEC.md`)  
   old: ``rd` frame-ack: a rising edge clears frame_ready and overrun.`  
   new: ``rd` frame-ack: `rd` goes through a 2-FF synchroniser and a rising-edge detect; the edge clears frame_ready and overrun **only if frame_ctr is unchanged since the last status read** (otherwise a load between the status read and the rd edge would clear a new, unread frame; in that case the clear is suppressed and the new frame stays flagged).`
12. **5 m8** (`SPEC.md`)  
   old: `Slot lengths at N 4096: 2.05 ms (2 MHz), 16.4 ms (0.25 MHz).`  
   new: `Slot lengths at N 4096: 2.05 ms (2 MHz), 16.4 ms (0.25 MHz). **The host must read every frame** (PIO/DMA, or N ≥ 1024 with MicroPython at 4 MHz): a host whose read takes 1–2 slots can end up reading only even or only odd slots, which gives no complete chop pairs.`
13. **5 m9 status** (`SPEC.md`)  
   old: `[12] boost (active), [11:9] trim (active), [8] 0,`  
   new: `[12:9] boost and trim **of the frame in the hold register** (boost = [12], trim = [11:9], latched with the hold register, D48(4)), [8] 0,`
14. **5 G3 item 6** (`SPEC.md`)  
   old: `5. The OTA-only chop mode vectors already exist`  
   new: `6. Status word [12:9] reports the boost/trim of the frame in the hold register (D48(4)): vectors carry the per-frame boost/trim.
5. The OTA-only chop mode vectors already exist`
15. **2 PLAN C1** (`work/v1-design/PLAN.md`)  
   old: `PM informational (step settling is the gate, SPEC §3.0: |ε(t_half)| ≤ 6e-5, ε_NL ≤ 6e-5)`  
   new: `PM informational (the in-loop gate (B), transistor OTA1 in the tier-1 deck, is authoritative for INL, SPEC §3.0, D48(1); the step tb is a report-only diagnostic: health check |ε_dyn| ≤ 1e-4, watch level ε_NL ≤ 3e-7)`
16. **2 PLAN C9 title** (`work/v1-design/PLAN.md`)  
   old: `config, chop sequencer, shift-out (RTL)`  
   new: `config, chop sequencer, 16-bit parallel read bus (D46b) (RTL)`
17. **2 PLAN C9 gate** (`work/v1-design/PLAN.md`)  
   old: `mutants (acc width, off-by-one N, sign) caught |`  
   new: `mutants (acc width, off-by-one N, sign) caught. **Entry gate: golden v3 (G3 items 1-4 + D48(4): status reports the frame's boost/trim)** |`
18. **2 PLAN V3b title** (`work/v1-design/PLAN.md`)  
   old: `| V3b | **OTA-only characterisation (D45 g) and fast-mode INL (D28):** V3`  
   new: `| V3b | **Fast-mode INL (D28)** (OTA-only chop is V4a): V3`
19. **2 PLAN new V-row V3c** (`work/v1-design/PLAN.md`)  
   old: `(none)`  
   new: `| V3c | **In-loop transistor OTA gate (B) (D48(1)):** transistor OTA1 (OTA2 behavioural), then transistor OTA2 (OTA1 behavioural) in the tier-1 deck, N 1024, 2 MHz and 4 MHz boost | tt/27/3.3 and ss/−40/3.0 | OTA1: INL ≤ 1.333 ppm (2 MHz) / ≤ 5 ppm (boost), O1/O2 converged; OTA2: same limits (reference); broken copy: OTA1 tail set for 9.5 V/µs ⇒ REJECT |`
20. **6 DECISIONS D6 append** (`work/v1-design/DECISIONS.md`)  
   old: `irst-cut scope cuts (ROADMAP/SIZING) | x1–x8 in v1 | cheap |`  
   new: `rst-cut scope cuts (ROADMAP/SIZING) | x1–x8 in v1 | cheap (Superseded by D14.) |`
21. **6 DECISIONS D28 append** (`work/v1-design/DECISIONS.md`)  
   old: `m at 20 MHz | 10 MHz + 100 ppm; bias-boost bit | cheap now |`  
   new: ` at 20 MHz | 10 MHz + 100 ppm; bias-boost bit | cheap now (Superseded by D31, then D39, then D41.) |`
22. **6 DECISIONS D31 append** (`work/v1-design/DECISIONS.md`)  
   old: ` | always-on 20 MHz (+45 µA); 10 MHz + 100 ppm | cheap now |`  
   new: `| always-on 20 MHz (+45 µA); 10 MHz + 100 ppm | cheap now (198 µA figure superseded by D41: 172 µA fast.) |`
23. **6 DECISIONS D39 append** (`work/v1-design/DECISIONS.md`)  
   old: `BW rows only | cheap now; leakage limits checked in C4 PEX |`  
   new: `W rows only | cheap now; leakage limits checked in C4 PEX (b: superseded by D41, option A′.) |`
24. **6 DECISIONS D43 append** (`work/v1-design/DECISIONS.md`)  
   old: `1–G-M3, Q1–Q3 | PM ≥ 60° only; tail-only switching | cheap |`  
   new: `–G-M3, Q1–Q3 | PM ≥ 60° only; tail-only switching | cheap (a: PM windows superseded by D44.) |`

### Code (m1)
- `step_settle.py`: ε_dyn from the late value vo(t_half + 10τ) (4.3e-9 OTA1 both points, was 1.6e-8 with the A0 = 1e8 static term; OTA2 6.78e-4 / 2.96e-4 unchanged), start states 0 and ±x0 (OTA1 0.72, OTA2 0.6 V assumed = half the x2 peak ≈ 1.2 V; the macromodel is shift-invariant so the states do not change its numbers), ε_NL report-only ("below solver floor" under 1.2e-8), reltol/10 rerun agreement ≤ 10 % (OTA1 4.293/4.290e-9, OTA2 6.780/6.781e-4: pass), broken-copy discrimination on ε_dyn only: OTA1 limit 1e-8 (GBW/2 6.4e-5 REJECT, SR/2 6.0e-8 REJECT), OTA2 2× macro limits 1.4e-3 / 6e-4 unchanged (GBW/2 2.3e-2 / 1.4e-2, SR/2 8.5e-3 / 5.6e-3 REJECT).
- pytest on the sandbox (model/tests + design/tests): 152 passed in 63 s. Raw logs stay on the sandbox in /home/mempool/regr/tt/S7b (no csv written).

### Not applied / notes
- SPEC (B) for OTA2 is worded as a V-row with the OTA1 INL limits as reference numbers; the REVIEW gives no separate OTA2 INL limits, so coordinator to confirm. PLAN row is V3c (new).
- DECISIONS notes were appended inside the last cell of each row (end of row), nothing else changed.
- OTA2 start state ±0.6 V is an assumption (x2 peak not stated numerically in the spec).

