#!/usr/bin/env python3
"""Tier-1 OTA closed-loop step-settling gate (WO-19 / S7-M1).

One OTA macromodel (same elements as gen_tier1 ota="v2": diff gm with tanh tail-current slew into a loaded
node C_L, second pole at fp2_mult x GBW, static gain A0) in a capacitive feedback loop of factor beta, driven by an
ideal step of amplitude a at t = 0. Differential-lumped: the diff node carries C_L (per-side C_L, diff SR = I/C_L),
so diff slope = I_tail/C_L as in gen_tier1.

    eps(a)  = 1 - vo(t_set)/a          relative settling error at t_set = h - 2g
    eps_NL  = max_a |vo(a) - (g*a + b)| / a_max, LS line over a = 0.1..1.0 x a_max (deviation from linearity)

h = 0.5/fs, g = 0.025/fs (non-overlap), so t_set = 0.45/fs = 225 ns at 2 MHz, 112.5 ns at 4 MHz.
A0 is 1e8 here so eps is the dynamic residue only (static 1/(beta A0) gain error is a separate, calibratable item).
No csv is written: ngspice .meas reads the numbers from the log.

CLI: python step_settle.py [--outdir DIR] ; prints ACCEPT/REJECT per point, exits 1 on any REJECT or broken-copy ACCEPT.
"""
import math
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import params as P  # noqa: E402

NGSPICE = os.environ.get("NGSPICE", "ngspice")
TWO_PI = 2.0 * math.pi
FRACS = (0.1, 0.28, 0.46, 0.64, 0.82, 1.0)
# O1 options (D43c ladder): reltol 1e-4, tmax 5 ns, capped at tau/10, chgtol floor.
OPTS_O1 = P.option_ladder("O1")
# O1 cannot resolve eps ~ 1e-5 (vntol 1 uV, reltol 1e-4 sit above it: it reads exactly 0), so the gate uses a tight set;
# `--o1` reruns with O1 as the cross-check (D43c rule: report both, the gate number is the tight one).
OPTS_TIGHT = dict(method="gear", reltol=1e-8, chgtol=1e-16, vntol=1e-10, abstol=1e-15, trtol=1.0, tmax_ns=0.5, tau_floor_div=10.0)

# Gated points: name -> (fs, GBW, SR, beta, C_L, worst diff step a_max).  Limits below are filled from the WO-19 run.
# OTA1 a_max = c1 (u_max + 1) VREF = 0.125 x 1.9 x 2.048 = 0.486 V.
# OTA2 a_max = c2 |x1|max + (Ck/Cint2) VREF = 0.5 x 1.21 + 0.25 x 2.048 = 1.117 V (loop bound, not a typical step).
POINTS = {
    "ota1_2M":   dict(fs=2e6, gbw=10e6, sr=12.5e6, beta=0.84,  cl=1.4e-12, amax=0.486),
    "ota1_4Mb":  dict(fs=4e6, gbw=20e6, sr=25e6,   beta=0.84,  cl=1.4e-12, amax=0.486),
    "ota2_2M":   dict(fs=2e6, gbw=10e6, sr=13.5e6, beta=0.497, cl=0.7e-12, amax=1.117),
    "ota2_4Mb":  dict(fs=4e6, gbw=22.5e6, sr=27e6, beta=0.497, cl=0.7e-12, amax=1.117),
}
# Limits (2 x measured macro value, rounded up; see work/v1-design/results/s7_spec_edits.md). Filled after the run.
LIMITS = {
    "ota1_2M":  dict(eps=4e-8, eps_nl=1e-9),
    "ota1_4Mb": dict(eps=4e-8, eps_nl=1e-9),
    "ota2_2M":  dict(eps=1.4e-3, eps_nl=2.5e-4),
    "ota2_4Mb": dict(eps=6e-4, eps_nl=1.3e-4),
}
# Broken copies that every point must REJECT: GBW halved (slower linear settling) and SR halved (longer slewing).
BROKEN = {"gbw_half": dict(gbw_scale=0.5), "sr_half": dict(sr_scale=0.5)}


def t_set(fs):
    return 0.5 / fs - 2 * 0.025 / fs


def build_deck(pt, fracs=FRACS, sr_scale=1.0, gbw_scale=1.0, opts=None, a0=1e8):
    opts = opts or OPTS_TIGHT
    fs, beta, cl = pt["fs"], pt["beta"], pt["cl"]
    gbw, sr = pt["gbw"] * gbw_scale, pt["sr"] * sr_scale
    gm = TWO_PI * gbw * cl
    ip = sr * cl
    fp2 = 3.0 * gbw
    cf = 1.0 / (TWO_PI * fp2 * 1e3)
    g0 = gm / a0
    ts = t_set(fs)
    tau = 1.0 / (TWO_PI * beta * gbw)
    tmax = min(opts.get("tmax_ns", 10.0) * 1e-9, tau / 10.0)
    L = ["* tier-1 OTA closed-loop step (WO-19)", ".model swm sw",
         f".options method={opts['method']} reltol={opts['reltol']:g} chgtol={opts['chgtol']:g} "
         f"vntol={opts['vntol']:g} abstol={opts['abstol']:g} trtol={opts.get('trtol', 7.0):g}"]
    for i, fr in enumerate(fracs):
        a = fr * pt["amax"]
        L += [f"Vs{i} s{i} 0 PWL(0 0 1p {a:.9g})",
              f"Bdr{i} dr{i} 0 V = {beta:.9g}*(V(s{i})-V(vo{i}))",
              f"Rf{i} dr{i} f{i} 1k", f"Cf{i} f{i} 0 {cf:.6e}",
              f"Bg{i} 0 vo{i} I = {ip:.9e}*tanh({gm:.9e}*V(f{i})/{ip:.9e})",
              f"Bro{i} vo{i} 0 I = V(vo{i})*{g0:.9e}",
              f"Cl{i} vo{i} 0 {cl:.6e}",
              f".meas tran vat{i} find par('v(s{i})-v(vo{i})') at={ts:.9e}"]   # absolute error s-vo, full precision
    L += [f".tran 1n {ts * 1.2:.6e} 0 {tmax:.6e}", ".end"]
    return "\n".join(L) + "\n"


def run_point(pt, tag, outdir, **kw):
    os.makedirs(outdir, exist_ok=True)
    cir, log = os.path.join(outdir, tag + ".cir"), os.path.join(outdir, tag + ".log")
    open(cir, "w").write(build_deck(pt, **kw))
    subprocess.run(["nice", "-n", "10", "timeout", "300", NGSPICE, "-b", "-o", log, cir], capture_output=True, text=True)
    txt = open(log).read() if os.path.exists(log) else ""
    got = {int(m.group(1)): float(m.group(2)) for m in re.finditer(r"^vat(\d+)\s*=\s*([-+0-9.eE]+)", txt, re.M)}
    if len(got) != len(FRACS):
        raise RuntimeError(f"{tag}: missing .meas results ({sorted(got)}); see {log}")
    vo = np.array(FRACS) * pt["amax"] - np.array([got[i] for i in range(len(FRACS))])   # meas is the error s - vo
    return eps_metrics(vo, pt["amax"], FRACS)


def eps_metrics(vo, amax, fracs=FRACS):
    """eps at the max step, and nonlinearity of vo vs a (LS line with offset), relative to amax."""
    a = np.asarray(fracs) * amax
    if not np.all(np.isfinite(vo)):
        return dict(eps=float("nan"), eps_nl=float("nan"), eps_all=[float("nan")] * len(a))
    eps_all = 1.0 - np.asarray(vo) / a
    p = np.polyfit(a, vo, 1)
    nl = float(np.max(np.abs(vo - np.polyval(p, a))) / amax)
    return dict(eps=float(eps_all[-1]), eps_nl=nl, eps_all=[float(e) for e in eps_all])


def gate(m, lim):
    """ACCEPT iff both numbers are finite and inside the limits."""
    if not (np.isfinite(m["eps"]) and np.isfinite(m["eps_nl"])):
        return False
    return abs(m["eps"]) <= lim["eps"] and m["eps_nl"] <= lim["eps_nl"]


def main(argv=None):
    outdir = "/home/mempool/regr/tt/WO-19"
    if argv and "--outdir" in argv:
        outdir = argv[argv.index("--outdir") + 1]
    bad = 0
    for name, pt in POINTS.items():
        m = run_point(pt, name, outdir)
        if "--o1" in (argv or []):
            mo = run_point(pt, name + "_O1", outdir, opts=OPTS_O1)
            print(f"  O1 cross-check {name}: eps={mo['eps']:.3e} eps_NL={mo['eps_nl']:.3e}")
        lim = LIMITS.get(name)
        line = f"{name}: eps={m['eps']:.3e} eps_NL={m['eps_nl']:.3e}"
        if lim is None:
            print(line + "  (no limit set: measurement only)")
            continue
        ok = gate(m, lim)
        print(f"{line} -> {'ACCEPT' if ok else 'REJECT'}")
        bad += (not ok)
        for bn, kw in BROKEN.items():
            mb = run_point(pt, f"{name}_{bn}", outdir, **kw)
            okb = gate(mb, lim)
            print(f"  broken {bn}: eps={mb['eps']:.3e} eps_NL={mb['eps_nl']:.3e} -> "
                  f"{'REJECT' if not okb else 'ACCEPT (this broken copy is not caught)'}")
            bad += okb
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
