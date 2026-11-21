# WO-99 results: C6 final subckt, VICM/VOCM, Cint2 reset, top-choice review

Status 2026-11-21: **sources committed (69c59b9), runs QUEUED, no verdicts yet.** The pool was launched at 12:13 with 46 jobs. It had
not started a single job about 15 min later: the sandbox load was 13–14 on 6 cores, and the global lpool slots (GMAX 5) were held by
the WO-95/96/97 pools. The pool keeps running detached and its outputs land in the frozen copy.

Frozen copy `/home/mempool/regr/tt/WO-99-69c59b9`, outputs `out/{c6,c57,r2}`, marker `out/pool_logs/POOL_DONE`.
Summaries (run in the frozen copy with the venv): `python design/c6_bias/c6_final.py summary out/c6`,
`python design/c5c7_ref/c5c7_ref.py summary out/c57`, `python design/c4_sw/r2_reset.py summary out/r2`.

## 1. C6 final (`design/c6_bias/c6_final.py`, subckt `c6_bias vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok`)
- Core and start-up are the c6_spot tran core at R1 144.8 µm and R2/R1 2.45. The c6_spot defaults have been changed to these values (they were 94 / 4.6).
- Master leg: G0 17 units, plus trim legs of 1/2/4 units. Code 100 gives 21 units, the same as the spot master.
- VN is a cascoded NMOS diode in 2 halves. Boost opens half 2 (an NMOS switch, gate NOT boost), which doubles every port. Mk is W ×2, so R_K stays at 0.525.
- Sinks (ibtp 4.405, ibp 2.756, ivbl0 0.919 units of W 2/L 4): cascoded NMOS mirrors.
- ibn (11.67 PMOS units W 2/L 16) is mirrored from VP, which is fed by 0.5 × master. It is not cascoded: a stacked PMOS cascode would put the VP feed below its own compliance at ss/−40/3.0.
- boost and trim come in at 1.8 V and are level-shifted by `lsbuflv2hv_1` + `inv_1` (pin order checked against the PDK).
- Port currents are OTA1's `I_REF`. **OTA2 (`design/c2_ota2/ota2.spice`) has no bias diodes** (checked: no gate=drain device on the bias nets), so per D91 the port currents need no change for OTA2. OTA2 adds only gate load on VN/VNC-fed nodes; the toggle bench loads the OTA1 diodes only, so the WO-95 top must confirm the toggle with OTA2 attached.
- Gates per run: start, port (tt ±3 %, ratios ±3 %, boost 2 ± 4 %), compliance ≥ 0.2 V (base and boost, swept probe copies), toggle 0.1 % in 4 µs, trim (monotonic, step ≤ 6 %, I7/I0 ≥ 1.38, residual ≤ 3 %), own current ≤ 6 µA excluding the mirrors.
- 9 corners. Broken copies at tt/27 and ss/−40, each paired with the gate it must fail: finger→port, trim_open→trim, slowvn→toggle, hog→own, stack3→compl, nosu→start.

## 2. VICM/VOCM (`design/c5c7_ref/c5c7_ref.py`, subckt `c5c7_ref vref vss vocm vicm vscm`)
- Circuit: a 44-unit xhigh-poly string from **VREF+ (ua2)**, about 4 µA, with 1 pF of MIM per tap. Taps: vscm 1.024 V (VREF/2), vicm 1.210 V, vocm 1.489 V.
- Why not VAPWR: a VAPWR ratio cannot keep V_ICM within 1.1–1.3 V (D34) over 3.0–3.6 V.
- Current: 0 µA from VAPWR, against the WO-93 placeholder of 2 µA per OTA. The cost is about 4 µA DC load on the external VREF (≈ 2 mV across the 500 Ω pad, a gain term only).
- Gates: DC levels; loaded shift ≤ 2 mV on vscm and ≤ 10 mV on vicm/vocm. Ripple is reported only.
- Broken copies: shortvicm (the WO-94 wiring) and tap.

## 3. Cint2 reset (`design/c4_sw/netlist.py` `SW['sr2'] = 8/24`, bench `design/c4_sw/r2_reset.py`)
- Circuit: an x2p↔x2n output-short TG on r2, plus OTA2 `isl` driven by r2_t.
- Rejected alternative, a plate short across Cint2: with the islands on, it fights the CMFB and pushes current into vicm.
- Gate: slot residue ≤ 1e-4 at 500 ns. The order-1 residue at 15 ns is reported only, because no model tolerance exists for it yet. Broken copy: nosr2.

## 4. WO-94 top review: patch list for `design/xschem/gen/refnets.py` (WO-94 owner) and the WO-95 deck
1. `ssh{p,n}` short CM: vicm → **vscm**. At VREF/2 the short-mode DAC charge is zero; on vicm it is ≈ 0.7 µA at 4 MHz, which pulls the island CM by about −90 mV.
2. **Ck2 DAC polarity is wrong in the WO-94 top.** Cint is crossed there (vg1p→x1n, vg2p→x2n), which flips both integrators, so the direct Ck2 term must be the opposite of stage 1: side p `bkp` → VREF− on `kh`, i.e. swap `khi/klo` for both sides. The stage-1 DAC and comparator polarity are correct. WO-95 uses non-crossed Cint, so the mirrored polarity is right there.
3. Add `sw(f"sr2", "x2p", "x2n", "r2", "sr2")`, and drive OTA2's `isl` from `r2_t` (OTA2 keeps the C4 `rstb`).
4. `Xbias` → `c6_bias VAPWR VGND VDPWR boost trim0 trim1 trim2 o1_ibtp o1_ibn o1_ibp o1_ivbl0 ok`. Add top ports `boost trim0 trim1 trim2` from C9. Add `Xref ua2 VGND vocm vicm vscm c5c7_ref`.
5. `dec` = hd nand2_1 on VDPWR: OK (C3 is a 1.8 V cell, and C4 takes a 1.8 V dec). `bias_ok` lsbufhv2lv_1 pin order checked: OK.
6. WO-95 deck: `so1` (the o1 short) is on r2. In order 1 that resets integrator 1 every cycle. It should be on `rst`, or removed in favour of the C1 clamp.
7. Open for C1/WO-98: the OTA generator bakes `boost` in statically (no bank-switch port), so the C6.5 vbpc ×1.75 bank drive has nothing to connect to.

## 5. Not done (budget)
- D93 added scope, not started: the C4 delay caps MIM→MOS and the dead-time table. It needs a fresh WO/agent.
- All verdicts above are pending the queued runs.

## 6. Results (pool at 40/42 jobs with an EXIT line; job_5 and job_41 have no EXIT=0. The tap and nosr2 broken copies are missing from the summaries.)
**C6: not accepted.**
- **Toggle fails at every corner:** worst deviation in the 4–10 µs window after a toggle is 6–15 % (gate 0.1 %). Not diagnosed: it may be a real slow settling node (vn2 / vnc / the OTA diode nodes) or the bench window. That is the next item.
- **Trim:** cover is 1.408–1.417 (gate ≥ 1.38), but the max step is 0.057–0.061, so tt/27, ss/−40 and fs/−40 fail the 6 % step limit.
- **Port** fails at ss/−40 and fs/−40 (cold; which sub-row was not separated).
- **Passing:** compliance margin 0.67–0.97 V (gate 0.2), own current 4.25–4.72 µA core / 4.78–5.25 µA total (gate 6), and start at all 9 corners.
- **Broken copies:** 11 of 12 fail their own gate. The exception is stack3 at tt/27, which **does not** fail compliance (margin 0.615 V); stack3 fails it only at ss/−40.

**C5/C7:**
- DC passes at every corner: vicm 1.209, vocm 1.488, vscm 1.023 V, I_vref 3.5–4.4 µA.
- Loaded shift: vicm 4.8–5.2 mV and vocm 2.8–3.0 mV pass the 10 mV limit. **vscm 3.4–3.6 mV fails the 2 mV limit**, so the verdict is REJECT. The 2 mV limit is my own choice: the 10 mV CM tolerance would pass.
- The shortvicm broken copy fails as required (vicm −27.5 mV), which confirms that the WO-94 short node is wrong.

**r2:**
- Slot residue at 500 ns is about 0 at 9/9 corners (ACCEPT), but the nosr2 broken copy result is missing, so the gate is unproven.
- Order-1 residue at 15 ns is 7.5e-6 to 9.4e-2 (hot slow corners are worst).

**ivbnc / ivbpc (WO-102):** OTA1 generates both internally. Xmbpd is the ivbpc diode, fed by the replica Xmrt/Xmrnc. Xmbnd is the ivbnc diode, fed by Xmbpx (with the gbk bank devices Xmbpds/Xmbpxs). OTA2 (`design/c2_ota2/ota2.spice`) has no driver on either net. C6 needs no new ports: in the top, wire OTA1 pins `ivbnc`/`ivbpc` to nets `o1_ivbnc`/`o1_ivbpc` (OTA1 is the source) and OTA2's `ivbnc`/`ivbpc` pins to the same nets.
