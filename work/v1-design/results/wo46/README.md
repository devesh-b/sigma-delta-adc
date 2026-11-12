# WO-46 (C4a) spot-sim results

Frozen run: `/home/mempool/regr/tt/WO-46-03e28fe` (script `design/c4_sw/spot.py` @ 03e28fe; 22/22 jobs EXIT=0,
POOL_DONE, report exit 0, raw csv deleted). Full tables: `.../spot/summary.md`, `summary.json`. Smoke run (tt tim,
ss/−40 ron, first size set): `/home/mempool/regr/tt/WO-46-dbdcc80/smoke`. Design note: `design/c4_sw/DESIGN.md`.
These are spot sims for the design note (stage 1), not the C4 gate.

## TG Ron, DC, body effect in (ohm; peak over 0–2.25 V, top*: 0.18–2.22 V; "vg": peak over 1.07–1.33 V)

| TG (W_n/W_p, L 0.5) | tt/27/3.3 | ss/−40/3.0 | ss/125/3.0 | ff/125/3.6 |
|---|---|---|---|---|
| in8 8/16 | 833 | 2466 | 1565 | 525 |
| in8p3 8/24 | 569 | 1784 | 1078 | 420 |
| in10p3 10/30 | 459 | **1490** | 872 | 333 |
| in12p3 12/36 | 382 | **1247** | 727 | 276 |
| ref4p3 4/12 | 1153 | 3607 | 2237 | 859 |
| top2 2/4 | 3453 | 9845 | 6353 | 2163 |
| top1 1/2 | 7110 | 19420 | 12958 | 4362 |
| nonly8 8/0 (broken copy) | 3.6e5 | 2.2e11 | 1.2e7 | 1547 |
| nonly8, vg band | 503 | 773 | 1232 | 473 |

- Peak Ron sits near mid-rail (1.6–1.8 V) at ss; ss/−40/3.0 is the worst corner.
- Input-switch row (≤ 1.5 kΩ at ss/−40/3.0): in10p3 passes with 0.7 % margin; **in12p3 passes with 17 % margin
  (proposal)**. in8p3 fails. Broken copy nonly8 → 2.2e11 Ω, REJECT.
- ref4p3: 3.6 kΩ at ss/−40, above the 3 kΩ DAC target in DESIGN §3 → DAC TG needs ≈ 6/18.
- vg NMOS-only 8/0.5: 1.23 kΩ at ss/125, above the 1 kΩ target → W ≈ 10–12.
- Off leakage of an 8/16 TG (far side 1.0 V): 2.9 pA tt, **1.08 nA ff/125/3.6** (junction). That is on a bottom
  plate here (harmless); the same junction on a vg node would break the 90 pA vg row, so the vg switches must stay
  NMOS-only and small, with the leakage tb (C4b #9).

## LS (lsbuflv2hv_1) + non-overlap generator, 4 MHz, 200 fF per phase output (ns)

| corner (VA/VD) | LS delay r/f | LS edge | duty err % | g at thresholds (min) | g50 | early | t_half min | edge max | verdict |
|---|---|---|---|---|---|---|---|---|---|
| tt/27 3.3/1.8 | 0.96/0.39 | 0.14 | −0.23 | 2.59 | 3.44 | 1.01 | 120.9 | 0.81 | PASS |
| ss/−40 3.0/1.62 | 1.50/0.77 | 0.16 | −0.29 | 3.20 | 4.17 | 1.24 | 120.0 | 0.91 | PASS |
| ss/125 3.0/1.62 | 1.83/0.62 | 0.25 | −0.48 | 4.27 | **5.50** | 1.67 | 118.1 | **1.22** | FAIL edge_max |
| ff/−40 3.6/1.98 | 0.57/0.27 | 0.09 | −0.12 | **1.82** | 2.41 | **0.70** | 122.2 | 0.57 | PASS |
| ff/125 3.6/1.98 | 0.75/0.27 | 0.14 | −0.19 | 2.33 | 3.11 | 0.92 | 121.3 | 0.77 | PASS |
| sf/27 | 1.13/0.43 | 0.17 | −0.28 | 2.37 | 3.49 | 0.99 | 120.7 | 0.95 | PASS |
| fs/27 | 0.89/0.38 | 0.13 | −0.21 | 2.79 | 3.50 | 1.08 | 120.9 | 0.77 | PASS |
| ss/−40 3.6/1.62 (LS worst) | 1.31/0.77 | 0.13 | −0.22 | 2.55 | 3.30 | 0.98 | 121.1 | 0.73 | PASS |
| ff/−40 3.0/1.98 | 0.66/0.27 | 0.11 | −0.16 | 2.14 | 2.87 | 0.83 | 121.7 | 0.68 | PASS |

- Dead time spread 1.82 ns (thresholds, ff/−40) to 5.50 ns (50 %, ss/125): inside [1.0, 6.25] ns, margin 0.8 ns at
  the fast end and 0.75 ns at the slow end. g scales ≈ 2.3× over the corners.
- One FAIL: phase edge 1.22 ns at ss/125 against the 1.0 ns spot limit (inv_4 into 200 fF). Fix in C4b: inv_8
  final drivers, or the reviewer sets the limit; the gap and t_half are unaffected.
- LS: edges ≤ 0.25 ns, duty error ≤ 0.48 % (1.2 ns of 250 ns, inside t_half ≥ 112.5 ns). Rise delay is 2–3× the fall
  delay (y-rising is the worst y-race case, DESIGN §6).
- t_half of the late phases ≥ 118.1 ns ≥ 112.5 ns at every corner.

## Broken copies (each must REJECT on its own check): all 9 REJECT

| copy | corners | result |
|---|---|---|
| overlap (feedback removed) | tt, ss/−40, ff/−40 | g −1.1 … −2.1 ns → REJECT g_min |
| gbig (gap chain × 4 ≈ 0.05/fs) | tt, ff/−40 | g50 13.1 / 9.2 ns → REJECT g50_max |
| noearly | tt, ff/−40 | early 0.12 / 0.07 ns → REJECT early_min |
| lsload (+1 pF) | tt, ff/−40 | LS edge 15.9 / 11.2 ns → REJECT ls_edge_max |
| nonly8 | ss/−40 | Ron 2.2e11 Ω → REJECT ron_max |

Not checked here (next WO): edge_max has no broken copy yet; the corners are 9 of the §6 set; VDPWR is not swept
separately at fixed VAPWR except the two LS points; the hvl cell timing is schematic-level (no PEX).
