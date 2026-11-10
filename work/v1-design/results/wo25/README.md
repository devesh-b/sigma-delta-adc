# WO-25 results (C1b part 2a: D58 reference fix, D55 revert), 2026-11-10

Frozen copies: `regr/tt/WO-25-pass1` (untrimmed ratio measurement, tt only), `regr/tt/WO-25-d07bd49` (op/AC 9 PVT × 2 modes × 3 C_L). Raw logs here (JSON lines). Commits: 7de6857 (D58 + D55 revert + op/AC rows), d07bd49 (gate B `combine()`).

## Item 0 (part): gate B `combine()`
- `c1b_gateb.py --combine K`: asserts a complete part set, the same endpoints in every part, and u_hat agreement ≤ 0.05 ppm of FSR at every shared point. Gate value = max per-part endpoint INL; the union-grid INL is reported too.
- WO-24-8ef9a7e nom (6 parts, read-only): endpoint spread 0.0097 ppm, INL 2.29 ppm max part (2.29 union, 1.87 best fit), **ACCEPT**.
- Broken copies: one part's +0.9 endpoint u_hat moved by 4e-7 → INVALID (0.20 ppm disagreement), exit 2. One part missing → INVALID, exit 2.
- The sr95 copy is the coordinator's run (WO-24-8ef9a7e); not run here.

## Item 1: D58 reference fix
- (a) Untrimmed tt/27 ratios (`pass1_tt_untrimmed.log`), base / boost: m_tr 1.202 / 1.185, m_nr 1.155 / 1.153, m_plr 1.121 / 1.134, V_BL0 replica 1.081 / 1.105. Single-finger refs (ref_single): 1.002 / 0.963 / 0.970 (composites cause the error).
- (b) REF_TRIM = 1 / (tt base ratio) on btp, bn, bp, vbl0.
- (c) vbpc / vbnc diodes fed from a folded-branch replica: tail replica (1 m_t finger, gate ibtp) + sink replica (2 m_n fingers, gate ibn) on ivbpc → m_bpd bank carries (2 I_SINK − I_TAIL)/32 = I_NC/16 of the actual mirrors; copy bank m_bpx → m_bnd. CL-8 boost step = bank 5 → 7 fingers (K_P 10 → 7.14); K_N 8 in both modes.
- (d) V_BL0 replica trimmed by its tt ratio (1.081). Its ratio still moves 1.044–1.134 over PVT.

Ratios after trim (ratio is mirror current / (fingers × port current), so the trim does not change it):

| corner | m_tr b/f | m_nr b/f | m_plr b/f | V_BL0 b/f |
|---|---|---|---|---|
| tt/27/3.3 | 1.201/1.193 | 1.152/1.156 | 1.114/1.133 | 1.073/1.101 |
| ss/−40/3.0 | 1.154/1.142 | 1.191/1.180 | 1.099/1.109 | 1.063/1.091 |
| ss/125/3.0 | 1.217/1.210 | 1.125/1.136 | 1.128/1.158 | 1.106/1.134 |
| fs/125/3.0 | 1.215/1.225 | 1.128/1.138 | 1.113/1.152 | 1.093/1.125 |
| sf/125/3.0 | 1.215/1.207 | 1.109/1.128 | 1.128/1.157 | 1.106/1.134 |
| ff/−40/3.6 | 1.190/1.185 | 1.180/1.175 | 1.090/1.105 | 1.050/1.081 |
| ff/125/3.6 | 1.244/1.252 | 1.111/1.128 | 1.115/1.153 | 1.093/1.126 |
| fs/−40/3.0 | 1.158/1.153 | 1.193/1.181 | 1.089/1.103 | 1.048/1.079 |
| sf/−40/3.0 | 1.152/1.140 | 1.179/1.176 | 1.099/1.109 | 1.064/1.092 |

## Items 2–3: D55 revert + op/AC (lump 1.4 pF rows; DC is load-independent)

| corner | I_tail b/f [µA] | I_fold/I_tail | K_P eff b/f (tgt 10/7.14) | K_N b/f | A0 b/f [dB] | hand Δ | min margin [mV] | V_OCM err b/f [mV] | I_vdd b/f [µA] | β1 | boost integ GBW / fp2/GBW / PM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tt/27 | 18.48/36.72 | 1.349 | 10.70/7.47 | 8.60/8.38 | 83.02/81.86 | +0.3 | 113 | −1.5/3.3 | 54.2/108.8 | 0.838 | 60.4 / 1.48 / 60.2° |
| ss/−40 | **17.76/35.16** | 1.449 | 10.51/7.34 | 8.41/8.20 | 83.67/82.58 | +0.3 | 115 | −28.6/−29.8 | 56.0/110.9 | 0.832 | 74.3 / 1.11 / 52.6° |
| ss/125 | 18.73/37.26 | 1.299 | 10.48/7.32 | 8.39/8.17 | 83.47/81.61 | +0.3 | 152 | 28.9/43.6 | 53.0/106.8 | 0.839 | 50.6 / 1.24 / 55.4° |
| fs/125 | 18.70/37.70 | 1.304 | 10.58/7.40 | 8.49/8.28 | 81.14/78.71 | +0.3 | 100 | 18.2/38.9 | 53.1/107.0 | 0.843 | 48.7 / 1.42 / 59.1° |
| sf/125 | 18.69/37.15 | 1.283 | 10.54/7.34 | 8.45/8.21 | 83.48/81.81 | +0.3 | 153 | 40.7/50.4 | 52.2/106.1 | 0.839 | 52.8 / 1.34 / 57.7° |
| ff/−40 | 18.32/36.48 | 1.393 | 10.93/7.62 | 8.82/8.58 | 81.78/80.50 | +0.3 | 81 | −20.4/−19.3 | 55.6/110.6 | 0.835 | 75.6 / 1.45 / 59.7° |
| ff/125 | **19.14/38.55** | 1.255 | 10.88/7.59 | 8.78/8.55 | 82.64/80.91 | +0.3 | 105 | 38.2/58.8 | 52.3/106.1 | 0.842 | 52.1 / 1.66 / 62.9° |
| fs/−40 | **17.82/35.50** | 1.439 | 10.60/7.41 | 8.49/8.29 | **80.43**/78.42 | +0.3 | 70 (boost mplc1) | −29.8/−28.9 | 56.1/111.1 | 0.835 | 73.2 / 1.24 / 55.6° |
| sf/−40 | **17.73/35.09** | 1.437 | 10.60/7.38 | 8.49/8.25 | 82.72/81.94 | +0.3 | 119 | −24.3/−28.3 | 55.5/110.6 | 0.833 | 70.7 / 1.28 / 56.6° |

Exits:
- Precision A0 ≥ 80.3 dB: **met at all 9** (min 80.43 at fs/−40; was 79.47 in WO-24).
- I_fold/I_tail ≥ 1.2 (min 1.255), margins ≥ 50 mV incl. boost m_plc (min 70 mV), hand A0 ±1 dB (+0.24…+0.33), β1 ≥ 0.83 (min 0.832), base span ≥ 1.6 V (min 1.756), boost hot span ≥ 1.40 V (min 1.414 ss/125): **met**.
- Effective K_P ±10 %: **met** (base 10.48–10.93, boost 7.32–7.62). The replica runs ~+5–9 % high (sink-replica drain at ~2 V against ~0.5 V on m_n).
- **I_tail ±3 %: fails at 5 of 9** (−4.0 % to −4.2 % at the −40 °C corners, +3.5 / +4.2 % at ff/125). The m_tr ratio itself moves 1.14–1.25 over PVT, so a single tt trim cannot hold ±3 %.
- I_vdd base 52.2–56.1 µA (≈ 50 target; replica legs ≈ +1.4 µA), boost 106–111 µA.

Broken copies (own decks):
- tt nc_short → precision A0 68.5 dB: **REJECTED**.
- tt ref_single (wired in, item 3) → I_tail 15.43 µA: **REJECTED** on the I_tail row.
- ff/−40 kp_fixed (old wiring) → K_P 9.73: **K_P row blind** (PASSED). With REF_TRIM the fixed current is close to the real I_NC, so K_P stays inside ±10 %. The precision A0 row catches it (78.79 dB, K_N 7.79), but the WO's target row does not.

## Item 4: gate B
Not launched: a design exit (I_tail ±3 %) failed, so per the WO rule the run stops here. `regr/tt/WO-25-d07bd49/gb.sh` is ready (fs/125 boost, N 1024, m 21, O1, 6 parts as 3 × 2 waves, then `--combine 6`; marker `GB_DONE`, results `out/gb/combine.out`).
