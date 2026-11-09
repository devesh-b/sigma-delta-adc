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
