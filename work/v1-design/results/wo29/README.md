# WO-29 results (C1b part 2e: tb9 CM offset, cold-corner op, combine() rule), 2026-11-10

Frozen copies: `/home/mempool/regr/tt/WO-29-b583094` (diagnosis decks, `out/diag/{a,b,c}`),
`/home/mempool/regr/tt/WO-29-9e14bed` (tb9 fix, diag2, combine check, op/AC 9 PVT still running at hand-off).
Commits: b583094 (diag tokens), 760d618 (D62 info rows, pair-per-deck op split, combine rule + check), 9e14bed (tb9 Cint
polarity, run.sh / gb.sh).

## Item 2: tb9 CM offset = testbench bug (Cint positive feedback), not the CMFB
- Diagnosis decks (12 µs, boost): nominal SC, averaged-Cr copy (`dcavg`, the op/AC model in the same transient), all-ideal
  CMFB switches, ideal ctl-side only, ideal bli-side only, min-W TGs. At tt every copy pins at **+155.8 mV** with `ctl`
  ramping 2.11 → 2.9 V (windup); at fs/125 all copies agree within 2 mV (+24…+38 mV, decaying). Switch injection, Cr
  phasing and the B-source model are ruled out (the averaged and ideal-switch copies show the same offset).
- Mechanism: tb9 wired Cint outp → inp. inp → outp is non-inverting (PMOS pair, folded: inp↑ ⇒ I(min1)↓ ⇒ outn↓, outp↑);
  gen_tier1 / gate B wire it correctly (Xota1 inp = vg1n, Cint1p vg1p–o1p). Positive differential feedback latched the
  outputs to the rails after reset release (diag2/old: V_diff = **3.107 V** at 3.9 µs, CM +160 mV); a saturated pair pins
  its CM, so the CMFB winds up.
- Fix (9e14bed): Cint outp → inn, outn → inp. Broken copy `TB9_POL_OLD=1` reproduces the latch and REJECTs.
  diag2/new (tt, 8 µs): V_diff 0, averaged copy +0.32 / +0.39 mV (= op +0.31…0.40), SC copy end-ph2 +2.0 / +1.1 mV,
  **end-ph1 −10.6 / −11.8 mV** (ph1 ripple 12 mV: the exit "within 10 mV at the end of each half-phase" misses by ≤ 1.8 mV).

### tb9 with the fixed bench (boost, settled CM / error after 22.5 ns, mV)
| corner | reset rel | diff step | CM step | reset assert | reset rel 2 | suhi | sulo | suvb |
|---|---|---|---|---|---|---|---|---|
| tt/27 | 9.7 / 9.0 | 1.4 / **69.8** | −2.4 / **14.6** | −0.6 / 9.5 | −5.0 / 8.8 | 4.96 | **34.04** | 5.81 |
| ss/125 | 7.6 / 9.2 | 1.3 / **64.5** | −1.6 / **17.6** | −1.5 / **24.7** | −4.3 / 9.2 | 6.46 | **21.41** | 8.73 |
| fs/125 | 6.7 / **11.8** | 0.0 / **70.8** | −2.6 / **14.1** | −3.6 / **25.3** | −5.1 / **10.8** | 5.84 | **14.07** | **10.42** |
| sf/125 | 7.7 / 9.0 | 0.8 / **77.2** | −1.6 / **17.9** | 0.1 / 10.1 | −4.1 / 9.0 | 6.60 | **27.50** | 6.23 |
- Broken copies (tt): mcc4 (Cc ÷ 4) REJECTED and now discriminates: reset release 28.2 mV and reset release 2 22.7 mV
  vs nominal 9.0 / 8.8 (pass); mio (int_off + vbl0×2) REJECTED (start-up 135.7 mV).
- **Exit not met.** Open, each needing a coordinator call:
  - CM step 14–18 mV at 22.5 ns: 30 mV × e^(−22.5 ns/τ) with f_cm ≈ 5 MHz gives ≈ 15 mV, i.e. the f_cm shortfall. **D62's
    basis ("tb9 CM step settles to 5–7.5 mV") came from the latched bench**, so D62 needs a revisit; the lever is the D58
    f_cm one (Cc 0.3–0.4 pF or CMFB split), which this WO may not change.
  - diff step 64–77 mV: a 0.8 V step at SR ≈ 26 V/µs is still slewing at +22.5 ns (10 ns pulse + ≈ 15 ns slew). Options:
    measure from end of slewing, or use the real worst per-cycle step instead of 0.8 V.
  - reset assert at hot 25 mV; sulo 14–34 mV (not in band at 4 µs); end-ph1 ripple ≈ 12 mV. Not diagnosed (budget).

## Item 1 (D62): f_cm ≥ 9.4 and f_z ≤ f_cm/10 now `info` entries; CM PM / peaking gates; opac mcc4 is a helper (its
broken-copy role is the tb9 event rows, above).

## Item 3: op decks = one closed copy + its cm_open twin per deck, K_P tracking copies in their own deck; tt mutant deck
unchanged; transient-op lint kept. Broken copy: `--split-run2` at ff/−40 (`out/opac_brk`). **Results pending** (op/AC
was still running at hand-off).

## Item 4: combine() broken-copy rule (760d618), `design/tests/wo29_combine_check.py` on WO-26 c3_sr95 (read-only): ACCEPT
A sr95 as-is → REJECTED (good), endpoint disagreement (40.1 ppm at u = 0.9) as info; B same parts, nominal rule → INVALID;
C one part with a problem → INVALID (not REJECTED); D INL 1 ppm → PASSED (check is blind); E missing part → INVALID.

## Item 5: gate B NOT launched (item 2 exit not met). `gb.sh` is in the frozen copy, ready.
Markers for the running op/AC: `WO-29-9e14bed/out/status_{1,2,3}` (`EXIT=` per step), `out/DONE_{1,2,3}`; then
`python design/c1_ota1/c1b_opac.py --summary out/opac`.

## op/AC 9 PVT on the closed+open pair-per-deck split (coordinator, after hand-off)
- p058, p123, p467: **VERDICT ACCEPT** at all 9 PVT, including ff/−40 and sf/−40 (no transient-op fallback in the nominal decks).
- Broken copy `--split-run2` (the run-2 deck structure) at ff/−40: the transient-op lint fires, and its helper is dead (ΔV_ctl 1.78 V) → REJECT. The guard works.
- The bkt SR rows (ibtp ×0.95 stacked on −3σ) give 12.11–12.42 V/µs. These rows are info by design (K_P-tracking helper). They show that a C6 reference error worse than about −2 % breaks SPEC row 95.
- Ratio rows (info, D60): spreads 1.2–2.9 %.
