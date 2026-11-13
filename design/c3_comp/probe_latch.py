#!/usr/bin/env python3
"""WO-68 probe (sandbox only, labelled diagnosis, not a gate): where and when the SR-latch NMOS Sq3/Sb3 Vds exceeds
1.98 V in the T8 st deck (WO-65 finding: 2.32-2.33 V on drain ql/qlb, source sq/sb).

    python probe_latch.py OUTDIR CORNER TEMP ORDER [MUT]

Writes OUTDIR/<tag>/deck.sp (the c3_tb st deck plus extremes of every internal node and a wrdata of the latch nets),
runs ngspice, prints each node outside 0..VDPWR and every |Vds| > 1.98 V event of the four latch NMOS with the
waveform context, then deletes the wrdata file (no raw data is kept).
"""
import os, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c3_tb import st_deck, tim, SPICEINIT, V18_MAX  # noqa: E402
from netlist import devices  # noqa: E402

PORTS = {"inp", "inn", "clk", "q", "qb", "vdd", "vss"}


def main(out, corner, temp, order, mut=""):
    tag = f"{corner}{temp}_{order}_{mut or 'nom'}"
    d = os.path.join(out, tag)
    os.makedirs(d, exist_ok=True)
    txt, meta = st_deck(corner, temp, order, mut=mut)
    devs = devices(mut=mut)
    nodes = sorted({n for dv in devs for n in dv[2:6]} - PORTS)
    lat = [dv for dv in devs if dv[0][0] == "S" and dv[1].endswith("nfet_01v8")]   # Sq3 Sq4 Sb3 Sb4
    sig = ["vdd", "clk", "x2p", "x2n"] + [f"xc.{n}" for n in nodes]
    add = []
    for n in nodes:
        add += [f"let mx_{n} = vecmax(v(xc.{n}))", f"let mn_{n} = vecmin(v(xc.{n}))",
                f'echo "EXT {n} $&mn_{n} $&mx_{n}"']
    add += ["let mx_vdd = vecmax(v(vdd))", 'echo "EXT vdd 0 $&mx_vdd"', "set wr_singlescale", "set wr_vecnames",
            "wrdata w.txt " + " ".join(f"v({s})" for s in sig)]
    assert txt.count(".endc") == 1
    txt = txt.replace(".endc", "\n".join(add) + "\n.endc")
    open(os.path.join(d, "deck.sp"), "w").write(txt)
    open(os.path.join(d, ".spiceinit"), "w").write(SPICEINIT)
    with open(os.path.join(d, "deck.log"), "w") as lg:
        subprocess.run(["ngspice", "-b", "deck.sp"], cwd=d, stdout=lg, stderr=subprocess.STDOUT)
    log = open(os.path.join(d, "deck.log")).read().splitlines()
    vmax = 1.98
    print(f"== {tag}  vdd={vmax}")
    print("nodes outside [-0.05, vdd+0.05] (min, max):")
    for ln in log:
        if ln.startswith("EXT "):
            _, n, lo, hi = ln.split()
            if float(lo) < -0.05 or float(hi) > vmax + 0.05:
                print(f"   {n:6s} {float(lo):+.3f} {float(hi):+.3f}")
    w = os.path.join(d, "w.txt")
    a = np.loadtxt(w, skiprows=1)
    os.remove(w)
    t = a[:, 0]
    col = {s: a[:, 1 + i] for i, s in enumerate(sig)}
    v = lambda n: col["vdd"] * 0 if n == "vss" else col["vdd"] if n == "vdd" else col[f"xc.{n}"]
    dt_ = np.diff(t, append=t[-1])
    print(f"1.8 V devices with max|Vds| > {V18_MAX} V (max, time above limit):")
    for (nm, model, dn, gn, sn, _, _) in devs:
        if "g5v0" in model:
            continue
        ads = np.abs(v(dn) - v(sn))
        if ads.max() > V18_MAX:
            print(f"   {nm:5s} d={dn:5s} s={sn:5s} {ads.max():.3f} V  {dt_[ads > V18_MAX].sum() * 1e12:.0f} ps")
    T, g, th, _ = tim(4e6)
    rise, fall = T / 2 + g + 1e-9, T - g / 2
    show = ["vdd", "clk", "x2p", "x2n", "xc.op", "xc.on", "xc.ob2", "xc.nb2", "xc.ql", "xc.qlb", "xc.sq", "xc.sb"]
    print("cols: " + " ".join(s.replace("xc.", "") for s in show))
    for (nm, _, dn, gn, sn, _, _) in lat:
        ds = v(dn) - v(sn)
        idx = np.nonzero(np.abs(ds) > V18_MAX)[0]
        ev = []
        for k in idx:
            if not ev or t[k] - t[ev[-1][-1]] > 1e-9:
                ev.append([k])
            else:
                ev[-1].append(k)
        print(f"{nm} (d={dn} g={gn} s={sn}): max|Vds|={np.abs(ds).max():.3f} V, {len(ev)} events > {V18_MAX} V")
        for e in ev[:6]:
            k = e[int(np.argmax(np.abs(ds[e])))]
            ph = t[k] % T
            print(f"  peak {ds[k]:+.3f} V at {t[k] * 1e9:.3f} ns (cycle phase {ph * 1e9:.2f} ns; strobe rise "
                  f"{rise * 1e9:.2f}, fall {fall * 1e9:.2f}), above limit {(t[e[-1]] - t[e[0]]) * 1e12:.0f} ps")
            for dt in (-2e-9, -0.3e-9, -0.1e-9, -0.03e-9, 0.0, 0.1e-9, 1e-9):
                j = min(len(t) - 1, max(0, int(np.searchsorted(t, t[k] + dt))))
                print(f"    {dt * 1e9:+.2f}ns " + " ".join(f"{col[s][j]:+.3f}" for s in show))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]), a[3], a[4] if len(a) > 4 else "")
