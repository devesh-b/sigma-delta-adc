# WO-26 results (C1b part 2b: D59 parallel 1:8 references, K_P 12.5, replica fix), 2026-11-10

Frozen copies: `regr/tt/WO-26-0ed1112` (run 1, rejected), `regr/tt/WO-26-b177d23` (run 2, op/AC + gate B). Logs here (JSON lines): `opac_{a,b,c}.log` (run 2), `run1/` (run 1), `summary.txt`, `ratio_summary.txt`.
Commits: 6dccfd3 (D59 refs, K_P 12.5, replica, gate-path bank switch, tests), 0ed1112 (SR / ceiling / K_P tracking / V_OCM / ratio rows + broken copies), b177d23 (replica cascode gate from an ibp-fed diode).

## Design changes
- m_tr / m_nr / m_plr: 4 parallel unit fingers each (1:8); V_BL0 replica m_bl0 = 1 finger of m_plc, re-fingered 3 × 5/2 → 8 × 1.875/2. All derived in code. I_REF = design / 8. REF_TRIM removed.
- K_P 12.5 base (m_bpd 4 × 1.5/15, I_NC/8), 7.14 boost (7 fingers). Replica: 2 m_t + 4 m_n unit fingers. Copy bank m_bpx 0.75/15 (I_NC/16 to m_bnd, K_N 8).
- Sink replica cascode m_rnc (1 m_nc finger). Run 1 had its gate on V_ICM: the replica drain fell to 0.09–0.16 V in boost / cold while the fold node rose. Result: boost K_P 3.6–6.2, m_pl / m_plc in triode at ss/−40 and fs/−40, PM 47.6°. **Rejected.**
- Run 2: the gate is rcb, a diode with m_bnc geometry fed by one m_pl unit finger (gate ibp, +0.37 µA base / +0.74 µA boost). This avoids the zero-current state an ivbnc gate would add. Replica drain is now 0.19–0.46 V against fa 0.23–0.56 V.
- Bank switch moved to the gate path: the boost-only fingers sit on node gbk, with a TG to ivbpc and a pull-up to vdd. Base leakage of the off fingers is about 1e-17 A.
- Layout intent (common-centroid, edge dummies, C7) is in DESIGN.md §1.1.

## Item 1 exit (mirror ratios): FAILS
- The ratio is I_mirror / (8 · I_port), nominal 1.000.
- Range over 9 PVT × 2 modes:
  - m_tr 0.966–1.031 (spread 6.0 %);
  - m_nr 0.951–0.985;
  - m_plr 0.965–0.982 (spread 1.4 %, OK);
  - V_BL0 0.944–0.973.
- Spread over temperature: m_tr 2.85 %, V_BL0 2.53 %, m_nr 2.03 % base (limit 2 %).
- Cause: systematic Vds mismatch between each diode reference (Vds = Vgs ≈ 0.8–1 V) and its mirror (m_n Vds = fa 0.23–0.56 V; m_pl near Vdsat + 0.1 V; m_t Vsd set by V_ICM + Vsg(in), process-dependent). The same per-finger geometry gives the same numbers as the WO-25 single-finger refs (0.963 / 0.970). This is CLM / DIBL, not finger mismatch.
- Options for the coordinator:
  - (a) accept the offsets, since the rows that depend on them pass;
  - (b) Vds-matched references (cascoded diode refs);
  - (c) a fixed design correction (a trim, which D59 removed; needs the user).

## Item 3 rows (run 2): all met
- SR: base min 12.83 V/µs (sf/−40), boost min 25.54 (sf/−40). Ceiling I_tail ≤ 1.08 × design: max 19.08 / 37.90 µA.
- K_P tracking (ibn × 1.05): −0.34 % to −0.64 % at all 9 corners.
- V_OCM error: max +30.8 mV base (ff/125), boost −4.8…+7.4 mV.
- Broken copies (own deck, converged), all **REJECTED**:
  - tt nc_short → A0 69.1 dB;
  - tt ref_composite → ratios 1.20 / 1.155 / 1.126 (and ceiling);
  - tt kp_fixed + ibn105 → K_P tracking −7.24 %;
  - tt ibtp90 boost → SR 23.71;
  - tt ibtp112 boost → ceiling 41.2 µA;
  - ff/125 vbl0x4 boost → V_OCM +289 mV.

## Item 4 op/AC (run 2): all exits met
- Precision A0 min 83.79 dB (fs/125), so ≥ 3.5 dB margin.
- Minimum margin 87 mV (fs/−40 boost m_pl).
- I_fold/I_tail min 1.277; β1 min 0.832.
- Base span min 1.689 V; boost hot span min 1.414 V (ss/125).
- I_vdd: base 58.0–61.7 µA, boost 118.9–123.7 µA (WO-25: 52–56 / 106–111).
- The only REJECT lines are the ratio row: 18 per group = every nominal copy. There are no other nominal fails.

## Boost at the integrate load

| corner | GBW [MHz] | fp2/GBW | PM |
|---|---|---|---|
| tt/27 | 60.6 | 1.47 | 60.0° |
| ss/−40 | 74.9 | 1.06 | 51.3° |
| ss/125 | 49.9 | 1.25 | 55.8° |
| fs/125 | 48.1 | 1.46 | 59.7° |
| sf/125 | 52.1 | 1.36 | 58.0° |
| ff/−40 | 76.8 | 1.41 | 59.1° |
| ff/125 | 51.5 | 1.72 | 63.7° |
| fs/−40 | 74.5 | 1.22 | 55.1° |
| sf/−40 | 71.2 | 1.21 | 55.0° |

## A0 gap (WO-24 → WO-25, about 2.6 dB beyond D55): explained and gone
- WO-25 fs/−40 ran at I_fold/I_tail 1.448 against 1.319 with single-finger refs. The composite m_nr ratio rose to 1.19 at cold (trimmed at tt for 1.155) while m_tr fell to 1.158 (trim 1.202).
- So I_NC was about +14 %, and R_up fell (Rdn/Rup 3.58 against 2.51), on top of the D55 revert (m_plc margin 94 mV).
- Run 2 fs/−40: I_fold/I_tail 1.322, K_P 12.0, A0 85.91 dB. That is above the WO-24 single-finger 83.66, so the gap is gone.

## Item 5 gate B: launched (detached)
- `regr/tt/WO-26-b177d23/gb.sh` runs 30 parts in waves of 3:
  - fs/125, ss/−40, ss/125 and tt/27, nom, boost;
  - fs/125 sr95;
  - each N 1024, m 21, O1, 6 parts, then `--combine 6` per config.
- Markers:
  - progress in `out/gb_status`, one line per wave plus a combine line per config;
  - per config `out/gb/c{3,1,2,0}_nom/combine.out` and `out/gb/c3_sr95/combine.out`, each ending in `EXIT=`;
  - final marker `GB_DONE`.
- Launched because every item-4 op/AC exit passed. The item-1 ratio exit failure is flagged above.

## Gate B (WO-26 netlist, boost, N 1024, m 21, O1, 6 parts each, combine())
| corner | INL ep [ppm] | gate 5 / share 3.33 | endpoint spread [ppm] |
|---|---|---|---|
| fs/125 (c3) | **3.314** | ACCEPT / just inside (0.02 margin) | 0.027 |
| ss/−40 (c1) | 0.797 | ACCEPT | 0.014 |
| ss/125 (c2) | 1.686 | ACCEPT | 0.001 |
| tt/27 (c0) | 0.454 | ACCEPT | 0.002 |

- **sr95 broken copy at fs/125:** all 6 parts are healthy with INL 43 600–54 600 ppm (≫ 5). combine() returns **INVALID** (exit 2) because the endpoint u = 0.9 disagrees by 40 ppm across parts: the slew-limited copy carries memory from one conversion to the next, so endpoint results depend on the sequence.
  - Rejected in substance. combine() needs a broken-copy rule: when every part is healthy and > gate, report REJECTED even if the endpoints disagree.
- fs/125 INL rose from 2.29 ppm (WO-24 netlist) to 3.31 ppm (WO-26). It is within the 5 ppm gate, but at the 3.33 share. This needs watching on the WO-28 netlist.
