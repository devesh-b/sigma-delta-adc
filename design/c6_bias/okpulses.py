#!/usr/bin/env python3
"""WO-80 diagnostic (sandbox only): bias_ok high pulses in a raw c6_spot tran csv (kept by a direct ngspice run).

  python okpulses.py CSV [CSV ...]
Prints every high pulse (ok > VDD/2 with VDD > 1 V, as tran_eval), plus the ok level while VDD < 1 V.
"""
import sys

for path in sys.argv[1:]:
    rows = [ln.split() for ln in open(path)]
    h, data = rows[0], [list(map(float, r)) for r in rows[1:] if r]
    col = {n: i for i, n in enumerate(h)}
    t = [r[0] for r in data]
    g = lambda n: [r[col[n]] for r in data]
    I, ok, vd, tsu, vg = g("i(vsm)"), g("v(ok)"), g("v(vdd)"), g("v(tsu)"), g("v(vg)")
    iend = I[-1]
    hi = [vd[k] > 1.0 and ok[k] > 0.5 * vd[k] for k in range(len(t))]
    lowmax = max(((ok[k] / max(vd[k], 1e-3)), vd[k], t[k]) for k in range(len(t)) if vd[k] <= 1.0 and vd[k] > 0.3)
    print(f"== {path}: rows {len(t)} t_end {t[-1]*1e6:.1f} us Iend {iend*1e6:.4f} uA; "
          f"max ok/VDD while 0.3<VDD<=1 V: {lowmax[0]:.2f} at VDD {lowmax[1]:.2f}")
    k0 = None
    for k in range(len(t) + 1):
        hh = k < len(t) and hi[k]
        if hh and k0 is None:
            k0 = k
        elif not hh and k0 is not None:
            kk = k - 1
            print(f"  pulse rise {t[k0]*1e6:9.3f} us fall {t[kk]*1e6:9.3f} us width {(t[kk]-t[k0])*1e6:8.3f} us "
                  f"VDD {vd[k0]:.3f}->{vd[kk]:.3f} I/Iend {I[k0]/iend:.3f}->{I[kk]/iend:.3f} tsu {tsu[k0]:.3f}->{tsu[kk]:.3f} "
                  f"vg {vg[k0]:.3f}" + (" FINAL" if k == len(t) else ""))
            k0 = None
