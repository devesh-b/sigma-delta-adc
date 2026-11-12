# C4: switches, bottom-plate sampling, non-overlap phase generator (+ C7 level shifters): design note

WO-46 (C4a), stage 1 of the PLAN Stage C recipe: this note, hand calculations and spot sims only. The netlist and the
gate testbench come in the next WO, after `sd-adc-design-reviewer` has checked this note.
Spot-sim script: `design/c4_sw/spot.py`. Results: `work/v1-design/results/wo46/README.md` (frozen run
`/home/mempool/regr/tt/WO-46-03e28fe/spot/summary.md`).

Sources: SPEC §3.0 rows "Input switches", "Reference", "Reset", "Virtual ground", "Capacitors", "Clock"; §3.6 rule 13;
§3.8a port contract (CL-23, CL-25, D66, D67); CL-2 (Cs2 plates shorted), CL-5 (3.3 V vg switches); D12 (CM-rejecting
input switching), D22 (Cs 0.5 pF). Topology reference: `design/tier1/gen_tier1.py` (behavioural switch network) and
`design/c1_ota1/netlist.py` (C1-owned switches and their clock ports).

---

## 1. Phase naming and the C9 boundary

| Name here | Meaning | C1 port | tier-1 deck | C9 bit clock |
|---|---|---|---|---|
| φI (φIe early, φIl late) | integrate half: Cs1 → Cint1, Cs2/Ck2 → Cint2, DAC on, OTA1 integrate | `ph1` (CMFB refresh) | `phi2` | high |
| φS (φSe early, φSl late) | sample half: Cs1 samples VIN, Cs2 samples x1 (OTA1 hold), D12 top-plate short | `ph2` (CMFB share) | `phi1` / `phi1e` | low |

**Comparator timing (user D74, supersedes the earlier CL-23 reading):** the bit-clock rising edge (fs-cycle start,
C9 `fs_tick`) starts φI. x2 is final at the end of φI and **held through φS** (OTA2 in hold). The comparator strobe
φC fires **inside φS**: C4 derives it from the φSe rising edge (after the I→S gap, so x2 is complete), not from the
raw fs edge. C9 captures `comp_in` straight into the DAC flop on the next `fs_tick` (rising edge), and C4 applies y
in that cycle's φI. Budget at 4 MHz: strobe ≈ g + 1 ns after the falling edge, decision < 34 ns (SPEC comparator
row), next fs_tick ≈ t_half + g later, so the output is stable ≈ t_half − 34 ns ≈ 75 ns before capture (≈ 190 ns at
2 MHz), every corner. Loop delay equals the tier-1 deck (one decision per cycle, DAC in the next integrate half).
Every C9 control changes on the rising edge, i.e. inside the S→I dead time, where rule 13 wants the OTA-chop edge.

## 2. Switch list (per side; ×2 for the differential pair unless noted)

Ranges: VIN and VREF+ up to 1.1·VREF = 2.25 V; VREF− ≈ 0 V (ua3 Kelvin to sensor ground, D24); x1 per side
V_OCM ± 0.61 = 0.89–2.11 V; vg islands V_ICM ± 0.13 = 1.07–1.33 V (C1 sizes_draft V_ICM 1.20); D12 top-plate node
V_ICM + Vin_cm − Vref_cm = 0.18–2.22 V over Vin_cm 0…VREF (review F2 input-CM sweep).

| # | Switch (tier-1 name) | Nodes | Phase | Signal range | Type (proposal) | Owner |
|---|---|---|---|---|---|---|
| 1 | Input / sys-swap / short, **merged** (Sin1) | VIN+ or VIN− or CM → b1 (Cs1 bottom) | φSl · ¬swap / φSl · swap / φSl · short | 0–2.25 V | 3.3 V TG, ≈ 12/0.5 n + 36/0.5 p (§3) | C4 |
| 2 | DAC (Sdh1, Sdl1) | b1 → VREF+ / VREF− | φIl · y / φIl · ¬y | VREF+ 1.0–2.25, VREF− ≈ 0 | 3.3 V TG, ≈ 4/12 (both, matched injection) | C4 (C8 τ_ref tb) |
| 3 | D12 top-plate short (Stp1d), one per pair | tp1p ↔ tp1n | φSe | 0.18–2.22 V | 3.3 V TG, **small**: 2/4 (§4) | C4 |
| 4 | vg connect (Sg1) | tp1 → vg1 island | φIe | 1.07–1.33 V | 3.3 V NMOS only (CL-5 reasoning) | C4 |
| 5 | Island shunt, input chopper, fold chopper, CMFB TGs, output clamp | — | isl, chp/chn, chlp/chln, ph1/ph2(b), rstb | — | sized in C1 | C1 (C4 drives the clocks) |
| 6 | Cs2 sample (S2in) | o1 → b2 | φSl | 0.89–2.11 V | 3.3 V TG, ≈ 4/12 | C4 |
| 7 | Cs2 plate short (S2cm, CL-2), one per pair | b2p ↔ b2n | φI | 0.89–2.11 V | 3.3 V TG, ≈ 4/12 | C4 |
| 8 | D12 top-plate short stage 2 (Stp2d) | tp2p ↔ tp2n | φSe | ≈ 0.6–1.8 V | 3.3 V TG 2/4 | C4 |
| 9 | vg2 connect (Sg2) | tp2 → vg2 | φIe | 1.07–1.33 V | 3.3 V NMOS only | C4 |
| 10 | Ck2 DAC (Skh, Skl) | bk → VREF+ / VREF− | φIl · y / φIl · ¬y | as #2 | 3.3 V TG ≈ 4/12 | C4 |
| 11 | Ck2 rest (Sk0) | bk → cm (tier 1); **proposal: bkp ↔ bkn short** | φS | as #2 | 3.3 V TG ≈ 4/12 | C4 (Q3) |
| 12 | Int2 islands / reset; **order-1 per-cycle reset (D74)** | Cint2 / vg2 | rst2 (slot reset) **or** rst2_o1 (order 1, every cycle, late φS after the strobe decision) | — | C2 | C2 (C4 drives) |
| 13 | Comparator input | x2 only (**no mux**, D74) | strobe φC in φS | — | — | C3 |

Notes.
- **#1 merged (Q2):** the sys-chop swap (rule 8: on the pin side, ahead of sampling) and the internal short are done by
  gating which TG closes in φSl, not by a series switch. A series swap switch would add its Ron to the input-settling
  row (Ron ≤ 1.5 kΩ total). Cost: three TGs' junction caps on b1 (bottom plate, stray-insensitive) and on each pin.
- **#4/#9 NMOS only:** a PMOS at 1.2 V source has |Vgs| ≈ 1.2 V against |Vt| ≈ 1 V (cold ss) and is useless; NMOS-only
  at vg is the CL-5 choice. Its off leakage adds to the vg leakage row (≤ 90 pA at ff/125/3.6), so W stays small.
- **#11 (Q3):** with D12 and CL-2 only the differential charge matters, so Ck2's rest phase can short bkp ↔ bkn as
  CL-2 does for Cs2, with no CM bus.
- The comparator strobe φC (C3) and the CMFB `ph1/ph2` come from the same generator.
- **Order 1 (D74):** the comparator always reads x2; there is no input mux. Integrator 2 runs as a follower: Cint2 is
  reset every cycle and Cs2 transfers x1 in φI, so x2 = k·x1 each cycle; the Ck2 DAC (#10/#11) is held in its rest
  state (`order` = 0). Timing constraint: the per-cycle reset must not overlap the strobe, because x2 must stay held
  from the end of φI until the comparator has decided. So rst2_o1 is placed late in φS (after strobe + decision
  time, ≥ 40 ns at 4 MHz) and ends before the S→I gap; at 4 MHz that leaves ≈ 70 ns of reset, against the reset
  settling of Cint2 (≈ 1 kΩ × 1 pF, 15 τ ≈ 15 ns). The C2 reset switch must meet that; check in C4b (Q7).

## 3. TG vs NMOS-only, sizing (Ron, settling)

**Settling targets.** SPEC §3.0 "Input switches": (Ron + 500 Ω + R_src)·(5 pF + Cs) ≤ 18.75 ns and Ron_max ≤ 1.5 kΩ
over 0…VREF+ at ss/−40/3.0 including body effect. With R_src = 1 kΩ: Ron ≤ 18.75 ns / 5.5 pF − 1.5 kΩ = 1.91 kΩ, so
the 1.5 kΩ cap binds. τ = (1.5 + 0.5 + 1.0 kΩ)·5.5 pF = 16.5 ns ≤ 0.2·t_half(4 MHz) = 22.5 ns (WO item), 6.8 τ in
t_half; this is linear settling, i.e. gain error (SPEC §3.1 note), budgeted at 2 ppm INL in the row. On-chip τ alone
(Ron·Cs) = 0.75 ns.

**Why TG for #1:** VIN spans 0–2.25 V on a 3.0 V minimum supply. An NMOS-only g5v0d10v5 switch stops conducting above
≈ VDD − Vt(body) ≈ 1.8–2.0 V (spot sim: `nonly8` Ron ≈ 2e11 Ω at 2.25 V, ss/−40), so a TG is required. With 3.0 V
gates, both devices are weak near mid-rail (≈ 1.65 V: NMOS Vgs ≈ 1.35 V, PMOS Vsg ≈ 1.65 V, both near the
body-affected Vt at −40 °C), so the TG's peak Ron sits there and sets the width. The spot sims show Ron_max at
ss/−40/3.0: 8/16 → 2.47 kΩ, 8/24 → 1.78 kΩ (smoke run). The candidates 10/30 and 12/36 are in the frozen run (§9);
proposal: **the smallest of them with Ron_max ≤ 1.5 kΩ at ss/−40/3.0 and ss/125/3.0**. A bootstrapped switch is not
needed for this row and stays rejected (first-cut rule, 3.3 V device stress).

**DAC (#2, #10):** VREF+ is ratiometric 1.0–2.048 V, so the switch sees the same mid-rail weakness. τ_ref ≤ 10 ns
(SPEC "Reference" row, C8 tb): the per-pin load is Cs1 + Ck2 = 0.75 pF behind 500 Ω + 5 pF pad; charge sharing with the
pad cap, then pad recharge in 500 Ω·5.75 pF = 2.9 ns. Ron ≤ 3 kΩ gives Ron·0.75 pF ≤ 2.3 ns, so ≈ 4/12 (spot
`ref4p3`). `ref2` (2/4) read 9.8 kΩ peak at ss/−40 (7.4 ns, too close to 10 ns). The VREF− TG is the same size so
both DAC levels inject the same charge.

**Top-plate shorts (#3, #8):** τ = Ron·Cs/2 (two caps in series through driven bottom plates) = 0.25 pF·Ron. Settling
to 1e-6 needs 14 τ inside φSe (≈ t_half − early ≈ 110 ns at 4 MHz) → Ron ≤ 31 kΩ; 2/4 (spot `top2`) is far inside;
top1 read 19.4 kΩ peak at ss/−40 (τ 4.9 ns, 23 τ). The size is set by injection (§4), not by settling.

**vg switches (#4, #9), NMOS only:** in φI they carry the charge-transfer current; Ron adds to the integrator's
feedback-path τ. Target Ron ≤ 1 kΩ over 1.07–1.33 V at ss/−40/3.0 (spot column "vg" of `nonly8`, 8/0.5). Gate
cap adds to Cp_vg (β1 ≥ 0.83, Cp_vg ≤ 0.32 pF; 8/0.5 is ≈ 12 fF, inside the C1 allowance).

## 4. Charge injection and clock feedthrough

Hand numbers use Cox ≈ 3 fF/µm² for g5v0d10v5 (tox ≈ 11–12 nm; to be read from `.op` Cgg in C4b).

1. **Bottom-plate order (φSe before φSl):** the D12 top-plate short opens first. After it opens the top plates
   float and the differential charge on Cs1 is frozen; the later opening of the input TG (#1) injects into a driven
   bottom plate and the pin, not into the stored differential charge. So the input TG's signal-dependent injection
   and its Ron nonlinearity do not reach the sample (the reason for SPEC §3.3).
2. **Top-plate short injection is CM to first order:** one TG between tp1p and tp1n splits its channel charge into two
   equal impedances (Cs+ and Cs−), so it moves the top-plate CM, which D12 rejects. The residue is the split
   asymmetry: ΔV_dm ≈ (q/2Cs)·(ΔCs/Cs). Its **Vin_cm-dependent** part is what the CMRR gate sees (the constant part is
   an offset, cancelled by sys chop): dq/dVcm = (W_nL_n + W_pL_p)·Cox. For 2/4: 3 µm²·3 fF = 9 fF total, 4.5 fF per
   side on 0.5 pF = 9e-3 V/V CM; × 0.75 % (Cs 3σ) = **6.8e-5 CM→DM**, against ε_inj ≤ 2.8e-4 (SPEC "Capacitors" row):
   4× margin. An 8/24 top switch (16 µm²) would give 3.6e-4 and fail. **Rule: the top-plate short stays ≤ 2/4.**
3. **vg switch (#4) opens first in φI (φIe before φIl):** it injects into vg, which is a virtual ground at
   V_ICM ± 0.13 V, so the charge is constant (an offset, cancelled by OTA chop and sys chop). The signal-dependent part
   comes only from x1/A0 at vg (≈ 0.6 V / 1e4 = 60 µV per side): negligible. The DAC TG (#2) opens after it, into a
   floating top plate: no charge reaches Cint1.
4. **Clock feedthrough:** TG overlap caps do not cancel when W_p = 3 W_n (n and p overlaps differ). Feedthrough onto
   driven nodes (bottom plates, pins, VREF) does nothing; onto the floating top plates (#3) it is CM, as in 2.
5. **ff/125/3.6** gives the lowest Ron and the largest Vov, hence the largest channel charge (≈ 1.3× tt) and the
   largest off leakage (spot `off_leak` of an 8/16 TG, info); the C4b injection tb runs there and at ss/−40/3.0.

## 5. Non-overlap generator (delay based)

- **Where:** the fs clock crosses to 3.3 V once (one `lsbuflv2hv`), and all phases are made in the VAPWR domain from
  hvl cells. Nearly every switch is 3.3 V; making phases at 1.8 V and shifting each one would put LS-to-LS delay
  mismatch (VDPWR × VAPWR corners) directly into the dead time.
- **Structure (spot `tim`):** cross-coupled NAND pair, `a1 = NAND(fs, D(¬φSl))`, `a2 = NAND(¬fs, D(¬φIl))`, D = chain
  of K_G hvl inverters with C_G per node. Each half has an early phase (`φxe = ¬a`) and a late phase
  (`φxl = NAND(a, D_e(a))`, delayed by K_E inverters). The feedback is taken from the **late** phase, so a new phase
  starts only after the previous late phase is off. Buffers: true output 2 stages (inv_2, inv_4), complement 3 stages,
  200 fF each (estimate of the gate load per phase: up to ≈ 6 TGs of 12–48 fF plus routing).
- **Dead-time budget:** SPEC "Clock" row: g ≤ 0.025/fs at every corner (t_half = h − 2g ≥ 0.45/fs): 6.25 ns at
  4 MHz, 12.5 ns at 2 MHz, 100 ns at 0.25 MHz. A fixed delay only has to meet the 4 MHz bound at the slowest corner;
  it is far inside the bound at lower fs. The lower bound is non-overlap at the **switch thresholds**: measured as
  the gap between the 10 % crossings of the true phases (NMOS side) and the 90 % crossings of the complements (PMOS
  side), ≥ 1 ns at the fastest corner (proposal). The spread a delay chain shows over the §6 corners must fit
  between 1 ns (at switch thresholds, fast corner) and 6.25 ns (50 % points, slow corner).
- **What must fit in the S→I gap (rising fs edge):** (a) the OTA-chop edge (rule 13, §6); (b) the DAC decision y
  reaching the DAC TG gates before φIl rises (§6); (c) sys_swap / short / rst_analog changes. The I→S gap (falling
  edge) only has to separate the phases. The two gaps may differ; both stay ≤ 0.025/fs.
- **fs range:** the generator is static logic, so 0.25 MHz needs nothing extra.

## 6. Early/late phases, OTA-chop placement, y timing

- **Early/late:** φSe falls before φSl, φIe before φIl. The early phase must be fully off before the late one starts
  to turn off: early delay (50 % points) ≥ the early phase's fall time (≈ 0.8 ns at 200 fF). Proposal: ≥ 1 ns at the
  fast corner. tier 1 used 5 ns; nothing in the settling budget depends on it beyond shortening the early phase.
- **Rule 13 (OTA-chop edge only in a non-overlap interval):** `ota_chop_phase` changes on the rising edge, i.e. at the
  start of the S→I gap. C4 retimes it in the 3.3 V domain: the chopper clocks (input chopper `chp/chn` at 3.3 V,
  fold chopper `chlp/chln` at 1.8 V through one `lsbufhv2lv`) switch only after φSl is off (Cs2 has finished
  sampling x1) and before φIe rises. The chopper's own break-before-make is a small NAND pair tapped from the middle
  of the gap chain. A chop edge taken straight from the C9 edge would land while Cs2 still samples x1 (the LS delay
  is < 1 ns, φSl falls ≈ 1–2 ns later): that is the broken copy of the rule-13 check.
- **y race:** y changes at the rising edge (C9 DAC flop, clk→q ≈ 0.3–0.6 ns at ss/1.62 V), crosses its own LS and
  must be at the DAC TG gates before φIl rises: margin ≈ g − t_cq + (t_LS(fs) − t_LS(y)). With the same LS cell the
  last term is small, but LS rise and fall delays differ (smoke tt: 0.96 / 0.39 ns), so the y-rising case is the
  worst. Options: (a) rely on the gap (margin ≈ g − t_cq, ≥ 0.5 ns needed); (b) a 3.3 V latch on y, transparent in
  the gap and closed in φI (robust, one cell). A late y only closes the wrong reference briefly, which adds a larger
  step (settling/slew), it does not change the settled charge; still, C4b gates it.

## 7. Level shifters (C7), ramp order

- **Cell:** `sky130_fd_sc_hvl__lsbuflv2hv_1` (PDK cell, LVPWR = VDPWR, VPWR = VAPWR). Count: fs, y, ota_chop_phase,
  sys_swap, short, rst_analog, order (7, to C4) + boost, trim[2:0] (4, to C6, static, latched at pair boundaries).
  The 1.8 V fold-chopper clocks come back down through `lsbufhv2lv_1` so their edges are placed by the 3.3 V
  generator.
- **Delay, duty, edge (spot):** smoke tt/27: delay 0.96 ns rising / 0.39 ns falling, output 10–90 % 0.14 ns, duty
  error −0.23 % (fs 4 MHz, 0.6 ns of 250 ns). Duty error shortens one half: it is inside the t_half check (§8). All
  corners in §9, including ss/−40 with VDPWR 1.62 V and VAPWR 3.6 V (weak LV pull-down against strong HV PMOS).
- **Ramp order:** TT does not guarantee the order of VDPWR and VAPWR. (i) VAPWR up, VDPWR down: the LS inputs and
  LVPWR are 0, both input pull-downs are off and the cross-coupled latch holds an undefined state, so `isl` (CL-5:
  closed by default) is not guaranteed. Proposal: a VAPWR-domain "VDPWR present" detector (HV NMOS gated by VDPWR
  against a weak PMOS load) that forces islands closed, output clamps on, sampling/DAC/top switches open and the
  choppers parked until VDPWR is up and rst_analog is valid. (ii) VDPWR up, VAPWR down: every 3.3 V switch is off and
  the 1.8 V LS input devices see no stress; when VAPWR ramps, (i) applies until the detector releases. Both orders
  get a PWL ramp tb (pthomas learning: no `.op` handing the circuit its state).

## 8. Checks, spot limits and broken copies

Spot limits used in `spot.py` (proposals for the C4b gate; the reviewer may tighten):

| Check | Limit | Broken copy (must REJECT) |
|---|---|---|
| Input TG Ron_max over 0–2.25 V, ss/−40/3.0, body effect in | ≤ 1.5 kΩ | NMOS-only 8/0.5 (`nonly8`) |
| Dead time at switch thresholds (10 % true, 90 % complement), both gaps | ≥ 1.0 ns | feedback chains removed (`overlap`) at tt, ss/−40, ff/−40 |
| Dead time at 50 % points | ≤ 0.025/fs = 6.25 ns (4 MHz) | gap chain × 4 ≈ 0.05/fs (`gbig`), SPEC row's copy |
| Early → late delay (50 %) | ≥ 0.5 ns (spot); C4b: ≥ early fall time | late = early (`noearly`) |
| t_half of the late phases (50 %) | ≥ 0.45/fs = 112.5 ns | (covered by `gbig`) |
| Phase edges 10–90 % at 200 fF | ≤ 1.0 ns | — (info in spot; C4b copy: driver inv_1) |
| LS output edge 10–90 % | ≤ 1.0 ns | +1 pF on the LS output (`lsload`) |

**C4b testbench plan (next WO, after review), every §6 corner, 0.25 / 2 / 4 MHz:**
1. Ron DC sweep of every switch in §2 over its range (incl. F2 input-CM sweep 0…VREF for #1 and #3). Copy: NMOS-only.
2. Generator timing incl. the VDPWR axis (135 points for C7, review m7): g, t_half, early, edges, LS delay/duty.
   Copies: `overlap`, `gbig` (= g 0.05/fs, SPEC row), `noearly`.
3. Charge injection: real switches on Cs, Vin_cm sweep, Cs MC (0.75 % 3σ): ε_inj ≤ 2.8e-4. Copies: **one-sided
   injection** (top short replaced by two single-ended switches to a CM bus, i.e. D12 removed → sys-off CMRR < 60 dB)
   and **bottom-plate order inverted** (top short opens after the input TG → signal-dependent injection).
4. Input settling with the pad model (500 Ω + 5 pF, R_src 1 kΩ) at 4 MHz ss/−40/3.0. Copy: Ron × 3.
5. Rule 13: chop edges relative to φSl fall and φIe rise. Copy: chop clock from the raw C9 edge.
6. y setup to φIl at the DAC TG gates. Copy: extra 2 ns on the y LS.
7. Reset residue with real switches (D46a, r ≤ 1e-4 in 2 cycles at 4 MHz boost and 0.25 MHz). Copy: 1-cycle window.
8. Power-up ramps in both orders (§7). Copy: detector removed → isl not closed while VDPWR is low.
9. vg leakage at ff/125/3.6 and ff/100/3.6 (≤ 90 / 20 pA per node), PEX in C4c.
10. Comparator strobe placement (D74): φC rises inside φS, after φIl is off (x2 final) and with ≥ t_half − t_dec margin
    to the next fs_tick, at every corner and fs. Copy: **strobe on the wrong phase** (φC from φIe, i.e. during x2
    integration) ⇒ REJECT.
11. Order-1 follower (D74): rst2_o1 never overlaps φC + decision time; x2 = k·x1 per cycle within settling. Copy:
    rst2_o1 placed in early φS (overlapping the strobe) ⇒ REJECT.

## 9. Spot-sim results

See `work/v1-design/results/wo46/README.md` (filled from `summary.md` of the frozen run).

## 10. Questions for the reviewer

- **Q1** phase mapping in §1 (bit clock high = φI = C1 `ph1`); strobe in φS per D74.
- **Q7** order-1 per-cycle int2 reset placed late in φS (§2 notes): enough time at 4 MHz?
- **Q2** merged input / sys-swap / short switch (#1) instead of a series swap switch.
- **Q3** Ck2 rest phase as a p ↔ n short (#11), no CM bus.
- **Q4** input TG size from §9 (gate load per phase grows ×1.5 from 8/24 to 12/36).
- **Q5** spot limits of §8 (g ≥ 1 ns at thresholds, early ≥ fall time, edges ≤ 1 ns) and the y-retiming option (b).
- **Q6** VDPWR-present detector (§7) vs relying on TT's ramp order.
