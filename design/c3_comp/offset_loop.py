#!/usr/bin/env python3
"""C3 comparator offset: loop impact (WO-51 item 1, D75). Sandbox only.

    python offset_loop.py OUT.json

Model: model/iadc.py, v1 loop (order 2, c1 0.125, c2 0.5, k 0.5, VREF 2.048 V), comp_offset added to x2 at the
decision (units of vref, differential). Two questions (DESIGN.md 3.1b):
  (a) x2 headroom: peak |x2| (differential volts) vs comparator offset, over u in [-0.9, 0.9] FS, against the
      OTA2 linear range 1.4 V diff (SPEC OTA DC-gain row: A >= 75 dB for |Vout,diff| <= 1.4 V).
  (b) chop residue: system chop (two sub-conversions, input polarity swapped, demodulated, averaged).
      err(u) = chop(u) - u; residue = err(u; Vos) - err(u; 0). The quantisation pattern moves with Vos, so the raw
      difference is a +-1 LSB-scale sawtooth; the systematic part is its moving average over 101 points of a
      4001-point grid (0.045 FS window). Reported: unchopped mean shift (what chop removes), chopped mean shift,
      max |smoothed residue| (INL-like), in uV input-referred and ppm FS (FS = 2 vref).
Gain cases: ideal OTAs, and A0 80 dB falling to 75 dB at 1.4 V diff (a0_drop 0.44, vlin_diff 1.4) so the offset
moves x2 into the compressed region.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "model"))
import iadc as M  # noqa: E402

VREF = 2.048
VOS_MV = [0.0, 15.0, 45.0, -45.0, 90.0, 135.0, 200.0]
U = np.linspace(-0.9, 0.9, 4001)
WIN = 101
GAINS = {"ideal": {}, "A80_75at1v4": dict(a0_db=80.0, a0_drop=1 - 10 ** (-5 / 20), vlin_diff=1.4)}


def run(N, gk, vos):
    p = M.with_(M.Params(order=2, N=N, c1=0.125, c2=0.5, k=0.5, vref=VREF, fs=2e6), comp_offset=vos * 1e-3 / VREF,
                **GAINS[gk])
    uh = {}
    x2m = 0.0
    for s in (1.0, -1.0):
        r, st = M.convert(p, U, rng=np.random.default_rng(1), sys_sign=np.full(U.size, s), return_state=True)
        uh[s] = r
        x2m = max(x2m, st["x2max"] * VREF)
    return uh, x2m


def main(out):
    res = {}
    for N in (1024, 4096):
        for gk in GAINS:
            base, x2m0 = run(N, gk, 0.0)
            e0c = (base[1.0] + base[-1.0]) / 2 - U
            e0u = base[1.0] - U
            for vos in VOS_MV:
                uh, x2m = (base, x2m0) if vos == 0 else run(N, gk, vos)
                ec = (uh[1.0] + uh[-1.0]) / 2 - U
                eu = uh[1.0] - U
                d = ec - e0c
                sm = np.convolve(d, np.ones(WIN) / WIN, mode="valid")
                r = dict(N=N, gain=gk, vos_mV=vos, x2max_V=x2m,
                         unchopped_mean_uV=float(np.mean(eu - e0u) * VREF * 1e6),
                         chopped_mean_uV=float(np.mean(d) * VREF * 1e6),
                         chopped_resid_max_uV=float(np.max(np.abs(sm)) * VREF * 1e6),
                         chopped_resid_max_ppm=float(np.max(np.abs(sm)) / 2 * 1e6),
                         raw_pp_uV=float((d.max() - d.min()) * VREF * 1e6))
                res[f"N{N}_{gk}_{vos:g}"] = r
                print(f"N {N:5d} {gk:12s} Vos {vos:7.1f} mV  x2max {x2m:.4f} V  unchopped {r['unchopped_mean_uV']:9.4f} uV"
                      f"  chopped mean {r['chopped_mean_uV']:9.5f} uV  resid max {r['chopped_resid_max_uV']:8.5f} uV"
                      f" ({r['chopped_resid_max_ppm']:.4f} ppm)  raw p-p {r['raw_pp_uV']:.3f} uV", flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
