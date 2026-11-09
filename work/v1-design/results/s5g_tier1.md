# S5g (WO-15): boosted operating points, INL-vs-GBW2 trend, fp2 sensitivity, gm/Id tooling

Runs: `tier1_tb.py --fast4 --only <group>` and `--gmid --src <dir>` on the sandbox tree `/home/mempool/tt-sd` (unfrozen, working copy of 2026-11-09); outputs `/home/mempool/regr/tt/WO-15/` (`fast4_*.log`, `out/fast4_*.json`, `gmid/`). All `--fast4` groups exit 0, run-health ACCEPT. `--gmid` ACCEPT, pytest 37 passed.
- Deck: 4 MHz, `bst = bstgm = 1`, GBW and SR set to the absolute boosted values. Default SPICE options (gear, reltol 1e-3, tmax 10 ns) unless marked "tight" (reltol 1e-5, tmax 5 ns). 21 DC points (span 0.9). INL = endpoint, ppm FSR. Targets: N 256 <= 20, N 1024 <= 5.
- The `fp2` pole tracks GBW (`fp2 = 3 x GBW`) unless stated.

## Item 1: cold-corner boosted points (M2)
| row | OTA1 GBW / SR | OTA2 GBW / SR | N 256 default | N 256 tight | N 1024 default | N 1024 tight |
|---|---|---|---|---|---|---|
| (a) D39 control | 20 MHz / 25 | 22.5 MHz / 20.25 | 7.83 | 6.84 | **3.686** | 3.28 |
| (b) cold, A | 30 / 25 | 34 / 20.25 | 0.746 | 0.518 | 0.755 | 0.404 |
| (c) cold, A' | 30 / 25 | 34 / 27 | 1.240 | 0.463 | 0.880 | 0.188 |
| (d) hot, A' | 20 / 25 | 22.5 / 27 | 2.010 | 1.995 | 1.079 | 1.375 |

- All 16 entries are below the targets (N 256 <= 20, N 1024 <= 5).
- Control (a) at N 1024 gives 3.686 ppm, equal to the s5f `bstgm = bst` row (3.686). Within 2 %.
- Higher GBW at the cold corner (b, c) lowers INL as expected. No cold-corner penalty was seen in this deck: GBW above the D39 rows did not worsen INL at the points run. The "tight" columns are an addition to the WO (see item 2, T2).

## Item 2: trend discrimination (Q4), 4 MHz
(1) Ideal OTA1 (GBW1 1 GHz, SR1 1000 V/us), OTA2 at 20.25 V/us, default options:
| GBW2 | N 256 | N 1024 |
|---|---|---|
| 15 MHz | 24.58 | 7.99 |
| 20 MHz | 7.45 | 2.66 |
| 25 MHz | 3.19 | 1.23 |

(2) s5f x1.5 rows (OTA1 x2 current, gm ratio 1.423; OTA2 x1.5, gm ratio 1.283; GBW1 base 10 MHz, GBW2 base 15 / 20 MHz), reltol 1e-5 and maxstep halved, against s5f (default options):
| GBW2 base | N 256 s5f | N 256 tight | N 1024 s5f | N 1024 tight |
|---|---|---|---|---|
| 15 MHz | 6.70 | 18.61 | 9.95 | 14.48 |
| 20 MHz | 14.4 | 11.52 | 12.5 | 12.12 |

(3) Same rows with `fp2_mult` 30 (default options): N 256: 113.3 (15 MHz), 101.2 (20 MHz); N 1024: 110.4 (15 MHz), 106.9 (20 MHz).

(4) Signed INL(u), 101 points, default options (endpoint-line residual, ppm FSR):
| row | INL ep (101 pt) | signed min / max | residual after cubic fit, rms | max |
|---|---|---|---|---|
| N 256, 15 MHz | 5.52 | -5.52 / +3.86 | 1.24 | 5.14 |
| N 256, 20 MHz | 14.59 | -14.59 / +12.31 | 1.42 | 5.93 |
| N 1024, 15 MHz | 11.79 | -11.79 / +10.37 | 1.29 | 4.91 |
| N 1024, 20 MHz | 13.07 | -13.07 / +12.38 | 1.37 | 4.95 |

**Which hypothesis the data supports (REASONED from these runs):**
- **(b) numerical: supported, and the strongest effect.** Tightening the solver moves the s5f rows by factors of 1.4 to 2.8 (15 MHz N 256: 6.7 -> 18.6; N 1024: 9.95 -> 14.5). After the change the trend is monotone in GBW2 at both N (18.6 > 11.5; 14.5 > 12.1). The default-option s5f 15 MHz rows were optimistic by up to 12 ppm; the default-option 20 MHz rows moved by less than 3 ppm.
- **(a) cancellation with an under-spec OTA1: not excluded, but not needed.** With an ideal OTA1 at default options the trend is monotone (T1). That removes nothing from (b), because T1 also ran at the default options.
- **(c) pattern-dependent residue: partly supported.** The signed curves are smooth S-shapes with a third-order residual of about 1.3 ppm rms and 5 to 6 ppm max, i.e. a jagged component of roughly 5 ppm on top of the smooth 12 to 14 ppm. This is the same size as the option sensitivity.
- **(3) fp2_mult 30 is inconclusive.** INL jumps to about 100 ppm for both rows whether GBW2 is 15 or 20 MHz. A far second pole should not worsen settling by 10x, so this is probably numerical (a ~1 GHz pole next to 10 ns steps) or a deck artefact. The gap between the two rows is not interpretable at this level.
- Consequence for the numbers in item 1: with tight options all four rows still pass; the control moves from 3.69 to 3.28 ppm.

## Item 3: second pole held at the base gm (m3)
`fp2_fixed = (10 MHz, 15 MHz)`: the pole sits at 3 x the s5f base GBWs (30 / 45 MHz) while the GBWs are at the boosted values. Default options.
| row | N 256 held | N 256 tracking | N 1024 held | N 1024 tracking |
|---|---|---|---|---|
| (a) 20 / 22.5 MHz | 181.7 | 7.83 | 177.4 | 3.686 |
| (c) 30 / 34 MHz, OTA2 27 V/us | 67.3 | 1.24 | 62.6 | 0.880 |

- Holding the pole at the base value is a severe loss (50 to 100x the tracking case). The second pole must scale with the boosted gm; the 3 x GBW rule needs to hold at every bias point.
- The default `fp2_fixed = None` deck is bit-identical (test `test_fp2_fixed_default_bit_identical_and_holds_pole`).

## Item 4: gm/Id tooling (`gmid_table.md`, `gmid_table.json`)
- Added L = 0.35 and 0.5 um (pfet_01v8, nfet_01v8). `pfet_g5v0d10v5` has no model bin at L 0.35 (ngspice: "could not find a valid modelname"), so it stays at L 1 and 2.
- W-bin check, pfet_01v8 tt, W 2 / 5 / 20 um at L 1 and 2: all curves finite and monotone on the strong-inversion side. At 27 C the gm/Id at equal Id/(W/L) agrees within about 1 to 2 (W 2 um lowest at J = 1e-8: 20.4 vs 22.6 and 22.3), so the plateau is not a clean width effect; the full table is in `gmid_table.md`.
- gm cross-check against BSIM `gm` from `.op` (tt, 27 C; Vsg 0.6 / 0.9 / 1.3 V, or 0.9 / 1.4 / 2.2 V for g5; every L): max error 0.34 % (pfet_01v8), 0.16 % (nfet_01v8), 0.16 % (g5); limit 2 %.
- Monotonicity on the strong-inversion side: 0 violations at every device, corner, temperature and L (tolerance 1 %).
- Broken copies, all rejected: wrong column (max gm error 7109 %), nfet `.op` gm against the pfet sweep (100 %), a 20 % bump in the pfet curve (1 monotonicity violation; the clean curve has 0).
- Worst-corner gm ratios with the new L bins: OTA1 x2 at gm/Id 10: 1.415 (ss, -40 C, L 0.5); OTA2 x1.5 at 14: 1.273; x2 at 14: 1.492 (previous L 1 and 2 values: 1.423 / 1.283 / 1.513). The s5f/fast4 rows keep the old 1.423 / 1.283 as the WO states.
- `need_22p5` is replaced by the minimum W/L meeting the boosted gm/Id target at every corner (ss/tt/ff x -40/27/100/125 C), pfet_01v8:

| target | L [um] | W/L | W.L [um^2] | binding corner |
|---|---|---|---|---|
| OTA1 gm/Id >= 10.05 at 35 uA | 0.35 | 61.4 | 7.5 | ss/125 |
| | 0.5 | 54.4 | 13.6 | ss/125 |
| | 1 | 56.3 | 56.3 | ss/125 |
| | 2 | 55.3 | 221.1 | ss/125 |
| OTA2 x1.5 gm/Id >= 13.96 at 14.2 uA | 0.35 | 660.6 | 80.9 | ff/125 |
| | 0.5 | 216.0 | 54.0 | ff/125 |
| | 1 | 237.3 | 237.3 | ff/125 |
| | 2 | 217.5 | 870.1 | ff/125 |
| OTA2 x2 gm/Id >= 10.47 at 18.9 uA | 0.35 | 38.4 | 4.7 | ss/125 |
| | 0.5 | 33.7 | 8.4 | ss/125 |
| | 1 | 34.9 | 34.9 | ss/125 |
| | 2 | 34.4 | 137.5 | ss/125 |

- The x1.5 OTA2 target (13.96 at 14.2 uA) is the expensive one: the hot-ff corner has little gm/Id headroom, so W/L is about 4x that of the x2 option (and W.L at L 0.5 is 54 um^2 against 8.4). All three targets are reachable at every corner (no unreachable corners).
- Tests: `test_gmid_ratio_helper_nonvacuous` now pins 1.474 +- 1 %; `test_gmid_ratio_plateau_curve`, `test_gmid_checks_reject_broken_copies`, `test_gmid_op_check_synthetic`, `test_gmid_min_wl_target`, `test_fp2_fixed_default_bit_identical_and_holds_pole`, `test_fast4_jobs_and_signed_inl`.

## Not done / caveats
- The `.op` gm values come from `op` runs at fixed Vsg inside the decks (not from a separate `.op` card); the comparison is against the numerical gm of the 5 mV DC sweep at the same Vsg.
- Item 4 asks for the plateau ("m2") to be explained by the W-bin; the data shows no clear width trend, so m2 stays open.
- The x1.5 OTA2 target and the s5f ratio change are inputs for C1 sizing and the next review.
