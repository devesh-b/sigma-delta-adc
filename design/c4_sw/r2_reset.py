#!/usr/bin/env python3
"""Int2 reset switch #12 (WO-99): residue bench for SW['sr2'] (x2p <-> x2n output short on r2, OTA2 islands on r2).

  python r2_reset.py run OUT CORNER TEMP VDD [MUT]     # MUT: none | nosr2 (short removed) | w4 (sr2 at 1/4 W, info)
  python r2_reset.py summary OUT

Choice (SPEC row 112, C4 table #12, D74/D76): r2 = rst OR rst2_o1 drives (a) a TG output short x2p <-> x2n (this switch,
C4 rules: 3.3 V TG, L 0.5, sized like #1 scaled to the 1 pF Cint2) and (b) OTA2's island shunt `isl` (inputs -> vicm,
C1 Sisl NMOS W 2 / L 0.5, not resized). Together they zero the differential Cint2 charge without a CM fight: the
short is differential (OTA2's CMFB keeps the output CM at vocm) and the islands load vicm with gates only. A
plate short across Cint2 (vg2 <-> x2) was rejected: with the islands on it ties x2 to vicm against the CMFB (vocm),
which pushes OTA output current into the vicm string.
Bench: Cint2 1 pF per side (vg2p -> x2n, vg2n -> x2p) + 0.1 pF per node; islands to an ideal 1.2 V; OTA2 = CM-only
(1 MOhm per output to 1.5 V, no differential drive: conservative); start x2 = +-0.6 V/side. r2 rises at 1 ns.
Gate: slot reset residue r <= 1e-4 within 2 fs cycles at 4 MHz (500 ns) at every corner. Order-1 per-cycle residue at
15 ns (the D76 minimum r2 width) is reported, not gated (no model tolerance exists yet; WO-95 / model to set it).
Broken copy nosr2 -> REJECT.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import netlist as N  # noqa: E402

LIM_SLOT, T_SLOT, T_O1 = 1e-4, 500e-9, 15e-9
CORNERS9 = [("tt", 27, 3.3)] + [(c, t, 3.6 if c == "ff" else 3.0) for c in ("ss", "ff", "sf", "fs") for t in (-40, 125)]


def deck(corner, temp, vdd, mut, csv):
    L = [f"* WO-99 r2 reset {corner} {temp} {vdd} {mut}", f'.lib "{N.LIB}" {corner}', f".temp {temp}",
         f"Vdd vdd 0 {vdd}", f"Vt r2_t 0 PWL(0 0 1n 0 1.2n {vdd})", f"Vc r2_c 0 PWL(0 {vdd} 1n {vdd} 1.2n 0)",
         "Vicm vicm 0 1.2", "Vocm vocm 0 1.5",
         "Cip vg2p x2n 1p", "Cin vg2n x2p 1p"] + [f"Cp{n} {n} 0 0.1p" for n in ("vg2p", "vg2n", "x2p", "x2n")]
    L += ["Rcp x2p vocm 1e6", "Rcn x2n vocm 1e6"]
    L += [N.mos(f"isl{s}", f"vg2{s}", "r2_t", "vicm", "0", N.HVN, 2.0, 0.5) for s in ("p", "n")]
    if mut != "nosr2":
        wn, wp = N.SW["sr2"]
        if mut == "w4":
            wn, wp = wn / 4, wp / 4
        L += N.switch("sr2", "x2p", "x2n", "r2_t", "r2_c", wn=wn, wp=wp)
    L += [".ic v(x2p)=2.1 v(x2n)=0.9 v(vg2p)=1.2 v(vg2n)=1.2", ".control", "set wr_singlescale", "set wr_vecnames",
          "tran 0.05n 600n 0 0.05n uic", f"wrdata {csv} v(vg2p) v(vg2n) v(x2p) v(x2n)", ".endc", ".end"]
    return "\n".join(L) + "\n"


def run(out, corner, temp, vdd, mut="none"):
    import numpy as np
    tag = f"r2_{corner}_{float(temp):g}_{float(vdd):g}_{mut}"
    base = os.path.join(out, tag)
    open(base + ".cir", "w").write(deck(corner, temp, vdd, mut, base + ".txt"))
    p = subprocess.run(["ngspice", "-b", base + ".cir"], capture_output=True, text=True, timeout=1800)
    open(base + ".log", "w").write(p.stdout[-3000:] + p.stderr[-3000:])
    d = np.loadtxt(base + ".txt", skiprows=1)
    t = d[:, 0]
    vc = (d[:, 1] - d[:, 4]) - (d[:, 2] - d[:, 3])          # differential Cint2 voltage
    v0 = abs(vc[0])
    r = lambda tt: float(abs(np.interp(1e-9 + tt, t, vc)) / v0)  # noqa: E731
    res = dict(tag=tag, mut=mut, v0=float(vc[0]), r_o1_15ns=r(T_O1), r_slot_500ns=r(T_SLOT))
    res["pass"] = bool(res["r_slot_500ns"] <= LIM_SLOT)
    res["verdict"] = "ACCEPT" if res["pass"] else "REJECT"
    json.dump(res, open(base + ".json", "w"), indent=1)
    return res


def summary(out):
    print("| run | r(15 ns) order-1, info | r(500 ns) slot, gate <= 1e-4 | verdict |")
    print("|---|---|---|---|")
    for f in sorted(os.listdir(out)):
        if f.startswith("r2_") and f.endswith(".json"):
            r = json.load(open(os.path.join(out, f)))
            print(f"| {r['tag']} | {r['r_o1_15ns']:.3e} | {r['r_slot_500ns']:.3e} | {r['verdict']} |")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "run":
        print(run(*a[1:])["verdict"])
    elif a[0] == "summary":
        summary(a[1])
