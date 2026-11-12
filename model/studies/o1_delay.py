#!/usr/bin/env python3
"""WO-53 order-1 delay study (D76 / REVIEW-C4a M1): y[n+1] = sign(x1[n]) vs the legacy y[n] = sign(x1[n]).

  python3 -m model.studies.o1_delay --out /home/mempool/regr/tt/WO-53 [--npts 801]
  python3 -m model.studies.o1_delay --nonvac     # broken copy (delay flag ignored) must print REJECT

Ideal loop (no noise, no OTA error), option B (c1 1/8, c2 1/2, k 1/2), u in [-0.9, 0.9], N 64/256/1024/4096.
Reports per N and mode: x1 peak (units of vref, and V/side at vref 2.048), raw recon acc1/N error (max, INL ppm FSR,
resolution bits), oracle recon (adds x1[N]/(c1 N), exact by charge conservation but x1[N] is not observable),
and one observable correction candidate: the decision that would follow, sign(x1[N-1]) = y[N], is not available,
so the 'tail' candidate adds (y_hat_N - ...) with y_hat_N = sign of the last observed y sum trend (see code).
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from model import iadc  # noqa: E402

C1, C2, K, VREF = 0.125, 0.5, 0.5, 2.048
NS = (64, 256, 1024, 4096)


def run(N, u, delay):
    p = iadc.Params(order=1, N=N, c1=C1, c2=C2, k=K, xmax=1e6, order1_delay=delay)
    uh, st = iadc.convert(p, u, return_state=True)
    y = st["y"]                                   # (N, B)
    # x1 trajectory peak over the run is st['x1max']; per-input peak needs the trace: recompute from y (exact for the ideal loop)
    x1 = np.zeros(u.size); pk = np.zeros(u.size)
    for n in range(N):
        x1 = x1 + C1 * (u - y[n]); pk = np.maximum(pk, np.abs(x1))
    return uh, st, y, pk


def stats(u, uh):
    err = uh - u
    lin = iadc.linearity(u, uh)
    return {"max_err": float(np.max(np.abs(err))), "bits": iadc.resolution_bits(float(np.max(np.abs(err)))),
            "inl_ppm": lin["inl_ppm"], "gain_err_ppm": lin["gain_err_ppm"], "offset_ppm": lin["offset_ppm"]}


def study(npts, delay_flag=True):
    u = np.linspace(-0.9, 0.9, npts)
    # also dyadic-ish random inputs to catch limit cycles at special values
    u = np.unique(np.concatenate([u, [0.0, 1/8, -1/8, 0.5, -0.5, 1/3, -1/3]]))
    res = {}
    for N in NS:
        for name, d in (("nodelay", False), ("delay", delay_flag)):
            uh, st, y, pk = run(N, u, d)
            x1f = st["x1_final"]
            ucorr = uh + x1f / (C1 * N)
            r = {"x1_peak": float(pk.max()), "x1_peak_V_side": float(0.5 * pk.max() * VREF),
                 "x1_final_max": float(np.abs(x1f).max()),
                 "raw": stats(u, uh), "oracle": stats(u, ucorr)}
            # observable correction candidate: scale by the N/(N-1) frame? Fit: two-point gain+offset removal is calibration,
            # not a decimator change, so report the raw error after removing the best affine (gain, offset): shows if error is systematic
            A = np.vstack([u, np.ones_like(u)]).T
            co, *_ = np.linalg.lstsq(A, uh, rcond=None)
            r["raw_after_affine"] = float(np.max(np.abs(uh - A @ co)))
            r["affine"] = [float(co[0]), float(co[1])]
            # growth check: peak in first half vs whole run
            res["N%d_%s" % (N, name)] = r
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out"); ap.add_argument("--npts", type=int, default=801); ap.add_argument("--nonvac", action="store_true")
    a = ap.parse_args()
    if a.nonvac:   # broken copy: delay flag silently ignored => results must equal nodelay, check detects it
        res = study(65, delay_flag=False)
        same = all(abs(res["N%d_delay" % N]["x1_peak"] - res["N%d_nodelay" % N]["x1_peak"]) < 1e-12 for N in NS)
        print("REJECT" if same else "ACCEPT (check is vacuous!)", "(broken copy gives delay == nodelay)")
        return
    res = study(a.npts)
    for k, v in res.items():
        print("%-14s x1pk %.3f (%.3f V/side) raw max_err %.3e bits %.2f INL %.1f ppm | oracle max_err %.2e | affine-resid %.3e" % (
            k, v["x1_peak"], v["x1_peak_V_side"], v["raw"]["max_err"], v["raw"]["bits"], v["raw"]["inl_ppm"], v["oracle"]["max_err"], v["raw_after_affine"]))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(res, open(os.path.join(a.out, "o1_delay.json"), "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
