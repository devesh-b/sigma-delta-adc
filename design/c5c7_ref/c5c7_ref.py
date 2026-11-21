#!/usr/bin/env python3
"""C5/C7 CM references (WO-99): V_ICM, V_OCM and the internal-short CM node, from one resistor string on VREF+.

  python c5c7_ref.py netlist [OUT.spice] [MUT]
  python c5c7_ref.py run OUT CORNER TEMP VDD [MUT]
  python c5c7_ref.py summary OUT

.subckt c5c7_ref vref vss vocm vicm vscm
  44 equal xhigh-poly units (0p69, L RU_L) from vref (ua2, VREF+ 2.048 V) to VGND; taps from the bottom:
  vscm 22 (= VREF/2, 1.024 V), vicm 26 (1.210 V), vocm 32 (1.489 V); a 4-unit MIM decap (~1 pF) on each tap.
Why the string sits on VREF+ (not VAPWR): a VAPWR ratio cannot hold V_ICM in 1.1-1.3 V (D34) over 3.0-3.6 V
(needs r >= 0.3667 and <= 0.3611). VREF is the ratiometric reference the loop already uses, its current is not in the
200 uA VAPWR budget, and the DC load (~4 uA) is a constant gain term at the pad (500 Ohm -> ~2 mV, cancels ratiometrically
only in part: a gain error, not INL). No buffer: every load is a gate or an SC kick (below).
vscm is the internal-short CM (SPEC 290 'VIN to CM'): at VREF/2 the short-mode DAC charge per cycle,
Cs (VREF+ + VREF- - 2 V_cm), is zero, so the node carries no average current. On vicm (the WO-94 choice) it is
0.5 pF x (2.048 - 2.42) per cycle, ~0.7 uA at 4 MHz into ~120 kOhm: ~ -90 mV on the OTA island CM.
Bench: VREF 2.048 V through the 500 Ohm pad; short-mode SC load on vscm (2 x 0.5 pF, VREF+/VREF- <-> CM at 4 MHz),
an island stand-in on vicm (1.3 pF per side toggling to vicm + 10 mV every cycle, the order-1 r2 case), a CMFB Cr
stand-in on vocm (2 x 0.1 pF toggling to vocm +- 50 mV). Gates: DC (vicm in 1.1-1.3, |vocm - 1.5| <= 50 mV,
|vscm - VREF/2| <= 2 mV, I_vref <= 5 uA); loaded average shift <= 10 mV on vscm (WO-104 ruling; was 2 mV) and on vicm / vocm (the SPEC
CM rows' 10 mV). Ripple is reported (info; WO-95 reads the real kicks). Broken copies: shortvicm (short load on vicm,
the WO-94 wiring) -> vicm shift REJECT; tap (vicm tap at 22) -> DC REJECT.
"""
import json
import os
import subprocess
import sys

LIB = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.tech/ngspice/sky130.lib.spice"
RX = "sky130_fd_pr__res_xhigh_po_0p69"
NU, TAPS = 44, dict(vscm=22, vicm=26, vocm=32)
RU_L = 4.0
NDEC = 4
VREF, PAD_R = 2.048, 500.0
FS = 4e6
LIM = dict(vicm=(1.10, 1.30), vocm=0.05, vscm=2e-3, ivref=5e-6, d_vscm=10e-3, d_cm=10e-3)  # WO-104: coordinator ruling, vscm shift limit = 10 mV CM tolerance (was 2 mV)
CORNERS9 = [("tt", 27, 3.3)] + [(c, t, 3.6 if c == "ff" else 3.0) for c in ("ss", "ff", "sf", "fs") for t in (-40, 125)]
MUTS = dict(shortvicm="load", tap="dc")


def build(mut="none"):
    taps = dict(TAPS)
    if mut == "tap":
        taps["vicm"] = 21
    name = {0: "vss", NU: "vref"}
    for k, v in taps.items():
        name[v] = k
    nd = lambda i: name.get(i, f"n{i}")  # noqa: E731
    L = [".subckt c5c7_ref vref vss vocm vicm vscm", f"* WO-99 C5/C7 CM string, {NU} x {RX} L {RU_L}, taps {taps}"]
    L += [f"Xr{i} {nd(i + 1)} {nd(i)} vss {RX} l={RU_L:g}" for i in range(NU)]
    L += [f"Xd{k} {k} vss sky130_fd_pr__cap_mim_m3_1 W=11 L=11 MF={NDEC} m={NDEC}" for k in TAPS]
    return "\n".join(L + [".ends c5c7_ref"]) + "\n"


def deck(corner, temp, vdd, mut, csv):
    T = 1 / FS
    ld = "vicm" if mut == "shortvicm" else "vscm"
    L = [f"* WO-99 c5c7 bench {corner} {temp} {vdd} {mut}", f".lib {LIB} {corner}", f".temp {temp}",
         f"Vref vrs 0 {VREF}", f"Rpad vrs ua2 {PAD_R}", "Xr ua2 0 vocm vicm vscm c5c7_ref",
         ".model SWM sw vt=0.5 vh=0.01 ron=1k roff=1e12",
         f"Va pa 0 PULSE(0 1 5u 1n 1n {T / 2 - 4e-9:.6g} {T:.6g})",
         f"Vb pb 0 PULSE(0 1 {5e-6 + T / 2:.6g} 1n 1n {T / 2 - 4e-9:.6g} {T:.6g})",
         "Vtop top 0 1.2",
         # short-mode SC load: bottom plates to CM in A, to VREF+ / VREF- in B
         "Csp bp top 0.5p", "Csn bn top 0.5p",
         f"S1 bp {ld} pa 0 SWM", f"S2 bn {ld} pa 0 SWM", "S3 bp ua2 pb 0 SWM", "S4 bn 0 pb 0 SWM",
         # island stand-in on vicm (vg2 node, 1.3 pF per side, 10 mV off), CMFB Cr stand-in on vocm
         "Vio vio 0 1.22", "Cip ip 0 1.3p", "Cin in 0 1.3p",
         "S5 ip vicm pa 0 SWM", "S6 in vicm pa 0 SWM", "S7 ip vio pb 0 SWM", "S8 in vio pb 0 SWM",
         "Vro1 vro1 0 1.54", "Vro2 vro2 0 1.44", "Crp rp 0 0.1p", "Crn rn 0 0.1p",
         "S9 rp vocm pa 0 SWM", "S10 rn vocm pa 0 SWM", "S11 rp vro1 pb 0 SWM", "S12 rn vro2 pb 0 SWM",
         ".control", "set wr_singlescale", "set wr_vecnames", "tran 1n 25u 0 1n",
         f"wrdata {csv} v(vicm) v(vocm) v(vscm) v(ua2) i(vref)", ".endc"]
    return "\n".join(L) + "\n" + build(mut) + ".end\n"


def run(out, corner, temp, vdd, mut="none"):
    import numpy as np
    tag = f"c57_{corner}_{float(temp):g}_{float(vdd):g}_{mut}"
    base = os.path.join(out, tag)
    open(base + ".cir", "w").write(deck(corner, temp, vdd, mut, base + ".txt"))
    p = subprocess.run(["ngspice", "-b", base + ".cir"], capture_output=True, text=True, timeout=3600)
    open(base + ".log", "w").write(p.stdout[-4000:] + p.stderr[-3000:])
    d = np.loadtxt(base + ".txt", skiprows=1)
    t = d[:, 0]
    w = lambda c, a, b: d[(t >= a) & (t <= b), c]  # noqa: E731
    dc = {k: float(w(i, 3e-6, 5e-6).mean()) for k, i in (("vicm", 1), ("vocm", 2), ("vscm", 3), ("ua2", 4))}
    dc["ivref"] = float(-w(5, 3e-6, 5e-6).mean())
    ld = {k: float(w(i, 20e-6, 25e-6).mean()) for k, i in (("vicm", 1), ("vocm", 2), ("vscm", 3))}
    rip = {k: float(np.ptp(w(i, 20e-6, 25e-6))) for k, i in (("vicm", 1), ("vocm", 2), ("vscm", 3))}
    sh = {k: ld[k] - dc[k] for k in ld}
    g = dict(dc=bool(LIM["vicm"][0] <= dc["vicm"] <= LIM["vicm"][1] and abs(dc["vocm"] - 1.5) <= LIM["vocm"]
                     and abs(dc["vscm"] - dc["ua2"] / 2) <= LIM["vscm"] and dc["ivref"] <= LIM["ivref"]),
             load=bool(abs(sh["vscm"]) <= LIM["d_vscm"] and abs(sh["vicm"]) <= LIM["d_cm"] and abs(sh["vocm"]) <= LIM["d_cm"]))
    r = dict(tag=tag, mut=mut, dc=dc, loaded=ld, shift=sh, ripple_pp=rip, gates=g,
             verdict="ACCEPT" if all(g.values()) else "REJECT")
    if mut != "none":
        r["target"], r["target_rejects"] = MUTS[mut], not g[MUTS[mut]]
    json.dump(r, open(base + ".json", "w"), indent=1)
    return r


def summary(out):
    print("| run | vicm / vocm / vscm DC (V) | I_vref uA | shift vicm / vocm / vscm mV | ripple pp mV | verdict |")
    print("|---|---|---|---|---|---|")
    for f in sorted(os.listdir(out)):
        if not (f.startswith("c57_") and f.endswith(".json")):
            continue
        r = json.load(open(os.path.join(out, f)))
        dc, sh, rp = r["dc"], r["shift"], r["ripple_pp"]
        g = dict(r["gates"], load=bool(abs(sh["vscm"]) <= LIM["d_vscm"] and abs(sh["vicm"]) <= LIM["d_cm"]
                                       and abs(sh["vocm"]) <= LIM["d_cm"]))   # re-judge stored shifts at the current LIM
        r["verdict"] = "ACCEPT" if all(g.values()) else "REJECT"
        if r["mut"] != "none":
            r["target_rejects"] = not g[r["target"]]
        v = r["verdict"] if r["mut"] == "none" else ("REJECTS " + r["target"] if r["target_rejects"] else "DOES NOT REJECT")
        print(f"| {r['tag']} | {dc['vicm']:.4f} / {dc['vocm']:.4f} / {dc['vscm']:.4f} | {dc['ivref'] * 1e6:.2f} | "
              f"{sh['vicm'] * 1e3:.2f} / {sh['vocm'] * 1e3:.2f} / {sh['vscm'] * 1e3:.2f} | "
              f"{rp['vicm'] * 1e3:.1f} / {rp['vocm'] * 1e3:.1f} / {rp['vscm'] * 1e3:.1f} | {v} |")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "netlist":
        txt = build(a[2] if len(a) > 2 else "none")
        (open(a[1], "w").write(txt) if len(a) > 1 else sys.stdout.write(txt))
    elif a[0] == "run":
        print(run(*a[1:])["verdict"])
    elif a[0] == "summary":
        summary(a[1])
