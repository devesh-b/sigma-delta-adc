#!/usr/bin/env python3
"""Tier-1 OTA closed-loop step-settling gate (WO-19 / S7-M1).

One OTA macromodel (same elements as gen_tier1 ota="v2": diff gm with tanh tail-current slew into a loaded
node C_L, second pole at fp2_mult x GBW, static gain A0) in a capacitive feedback loop of factor beta, driven by an
ideal step of amplitude a at t = 0. Differential-lumped: the diff node carries C_L (per-side C_L, diff SR = I/C_L),
so diff slope = I_tail/C_L as in gen_tier1.

    eps_dyn(a) = (vo(t_set + 10 tau) - vo(t_set))/a   dynamic residue at t_set = h - 2g, referenced to the late value
                                                      (REVIEW-S7b 1a (A); A0 and static gain error drop out)
    eps_NL     = max_a |a*eps_dyn(a) - LSQ line| / a_max over a = 0.1..1.0 x a_max (REPORT-ONLY watch level 3e-7)
    start states x0: step applied from x0 = 0 and +-x0_hi (macromodel is shift-invariant; the transistor tb is not)

h = 0.5/fs, g = 0.025/fs (non-overlap), so t_set = 0.45/fs = 225 ns at 2 MHz, 112.5 ns at 4 MHz.
A0 is 1e8 here; eps_dyn is the dynamic residue only (static 1/(beta A0) gain error is a separate, calibratable item).
D48(1) option 2: this tb is a REPORT-ONLY diagnostic for the transistor OTAs (in-loop gate (B) is authoritative for INL).
Only the broken-copy discrimination (eps vs DISC limits) and a reltol/10 convergence rerun (<= 10 % agreement on eps,
or both below the solver floor) pass/fail here. eps_NL is reported, never gated; below the solver floor it prints
"below solver floor".
No csv is written: ngspice .meas reads the numbers from the log.

CLI: python step_settle.py [--outdir DIR] ; prints ACCEPT/REJECT per point, exits 1 on any REJECT, broken-copy ACCEPT or
convergence disagreement.
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
    "ota1_2M":   dict(fs=2e6, gbw=10e6, sr=12.5e6, beta=0.84,  cl=1.4e-12, amax=0.486, x0=0.72),
    "ota1_4Mb":  dict(fs=4e6, gbw=20e6, sr=25e6,   beta=0.84,  cl=1.4e-12, amax=0.486, x0=0.72),
    "ota2_2M":   dict(fs=2e6, gbw=10e6, sr=13.5e6, beta=0.497, cl=0.7e-12, amax=1.117, x0=0.6),   # x0 = half x2 peak (~1.2 V diff)
    "ota2_4Mb":  dict(fs=4e6, gbw=22.5e6, sr=27e6, beta=0.497, cl=0.7e-12, amax=1.117, x0=0.6),
}
# eps_dyn (late-value reference) drops the static 1/(beta A0) term that was most of the old 1.6e-8: macro OTA1 eps_dyn 4.3e-9.
# DISC = broken-copy discrimination limits on eps_dyn ONLY (not SPEC gates; D48(1) option 2: macro values are
# reported, the in-loop gate (B) decides INL). OTA1 macro eps_dyn 4.3e-9 is below the nominal solver floor (1.2e-8) but
# the reltol/10 rerun agrees to 0.1 %, so it is resolved; limit 1e-8 (2.3 x macro) catches GBW/2 (6e-5) and SR/2 (6e-8).
# OTA2 limits = 2 x macro eps_dyn (6.8e-4 / 3.0e-4), unchanged.
LIMITS = {
    "ota1_2M":  dict(eps=1e-8),
    "ota1_4Mb": dict(eps=1e-8),
    "ota2_2M":  dict(eps=1.4e-3),
    "ota2_4Mb": dict(eps=6e-4),
}
# Broken copies that every point must REJECT: GBW halved (slower linear settling) and SR halved (longer slewing).
BROKEN = {"gbw_half": dict(gbw_scale=0.5), "sr_half": dict(sr_scale=0.5)}


def t_set(fs):
    return 0.5 / fs - 2 * 0.025 / fs


def tau_cl(pt, gbw_scale=1.0):
    return 1.0 / (TWO_PI * pt["beta"] * pt["gbw"] * gbw_scale)


def states(pt):
    return (0.0, pt.get("x0", 0.0), -pt.get("x0", 0.0))


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
    tl = ts + 10.0 * tau_cl(pt)          # late reference, 10 tau of the NOMINAL loop (same time for broken copies)
    tmax = min(opts.get("tmax_ns", 10.0) * 1e-9, tau / 10.0)
    L = ["* tier-1 OTA closed-loop step (WO-19)", ".model swm sw",
         f".options method={opts['method']} reltol={opts['reltol']:g} chgtol={opts['chgtol']:g} "
         f"vntol={opts['vntol']:g} abstol={opts['abstol']:g} trtol={opts.get('trtol', 7.0):g}"]
    n = 0
    for x0 in states(pt):
        for fr in fracs:
            a = fr * pt["amax"]
            L += [f"Vs{n} s{n} 0 PWL(0 {x0:.9g} 1p {x0 + a:.9g})",
                  f"Bdr{n} dr{n} 0 V = {beta:.9g}*(V(s{n})-V(vo{n}))",
                  f"Rf{n} dr{n} f{n} 1k", f"Cf{n} f{n} 0 {cf:.6e}",
                  f"Bg{n} 0 vo{n} I = {ip:.9e}*tanh({gm:.9e}*V(f{n})/{ip:.9e})",
                  f"Bro{n} vo{n} 0 I = V(vo{n})*{g0:.9e}",
                  f"Cl{n} vo{n} 0 {cl:.6e}",
                  f".meas tran vat{n} find par('v(s{n})-v(vo{n})') at={ts:.9e}",    # absolute error s-vo, full precision
                  f".meas tran vlt{n} find par('v(s{n})-v(vo{n})') at={tl:.9e}"]
            n += 1
    L += [f".tran 1n {tl * 1.05:.6e} 0 {tmax:.6e}", ".end"]
    return "\n".join(L) + "\n"


def run_point(pt, tag, outdir, **kw):
    os.makedirs(outdir, exist_ok=True)
    opts = kw.get("opts") or OPTS_TIGHT
    cir, log = os.path.join(outdir, tag + ".cir"), os.path.join(outdir, tag + ".log")
    open(cir, "w").write(build_deck(pt, **kw))
    subprocess.run(["nice", "-n", "10", "timeout", "600", NGSPICE, "-b", "-o", log, cir], capture_output=True, text=True)
    txt = open(log).read() if os.path.exists(log) else ""
    rd = lambda k: {int(m.group(1)): float(m.group(2)) for m in re.finditer(rf"^{k}(\d+)\s*=\s*([-+0-9.eE]+)", txt, re.M)}
    e_ts, e_tl = rd("vat"), rd("vlt")
    nst = len(states(pt))
    if len(e_ts) != len(FRACS) * nst or len(e_tl) != len(e_ts):
        raise RuntimeError(f"{tag}: missing .meas results ({len(e_ts)}/{len(FRACS) * nst}); see {log}")
    dv = np.array([e_ts[i] - e_tl[i] for i in range(len(e_ts))])   # vo(tl) - vo(ts), V
    m = eps_metrics(dv, pt["amax"], FRACS, nst, floor_v=opts["reltol"] * pt["amax"] + opts["vntol"])
    return m


def eps_metrics(dv, amax, fracs=FRACS, nst=1, floor_v=0.0):
    """dv = vo(t_set+10tau) - vo(t_set) per (state, step). eps_dyn = dv/a. eps = worst |eps_dyn| at the largest step
    over states; eps_nl = worst LSQ deviation of a*eps_dyn(a) vs a (per state) / amax. Floor = solver resolution."""
    dv = np.asarray(dv, float).reshape(nst, len(fracs))
    a = np.asarray(fracs) * amax
    if not np.all(np.isfinite(dv)):
        return dict(eps=float("nan"), eps_nl=float("nan"), eps_all=[float("nan")] * len(a), floor=floor_v / amax)
    eps_all = dv / a
    nl = 0.0
    for r in dv:
        p = np.polyfit(a, r, 1)
        nl = max(nl, float(np.max(np.abs(r - np.polyval(p, a))) / amax))
    return dict(eps=float(np.max(np.abs(eps_all[:, -1]))), eps_nl=nl, eps_all=[float(e) for e in eps_all[0]],
                floor=floor_v / amax)


def fmt_nl(m):
    return "below solver floor (<%.1e)" % m["floor"] if m["eps_nl"] < m["floor"] else "%.3e" % m["eps_nl"]


def converged(m1, m2, tol=0.10):
    """reltol/10 rerun: eps agrees within 10 % (this, not the nominal floor, is what shows eps itself is resolved)."""
    return abs(m1["eps"] - m2["eps"]) <= tol * abs(m2["eps"])


def gate(m, lim):
    """Broken-copy discrimination: ACCEPT iff eps_dyn is finite and <= lim['eps']. eps_NL is report-only (D48(1))."""
    if not np.isfinite(m["eps"]):
        return False
    return abs(m["eps"]) <= lim["eps"]


def tight_div(opts, d=10.0):
    o = dict(opts)
    o["reltol"] = opts["reltol"] / d
    return o


def main(argv=None):
    outdir = "/home/mempool/regr/tt/WO-19"
    if argv and "--outdir" in argv:
        outdir = argv[argv.index("--outdir") + 1]
    bad = 0
    for name, pt in POINTS.items():
        m = run_point(pt, name, outdir)
        m2 = run_point(pt, name + "_rel10", outdir, opts=tight_div(OPTS_TIGHT))
        conv = converged(m, m2)
        if "--o1" in (argv or []):
            mo = run_point(pt, name + "_O1", outdir, opts=OPTS_O1)
            print(f"  O1 cross-check {name}: eps={mo['eps']:.3e} eps_NL={mo['eps_nl']:.3e}")
        lim = LIMITS[name]
        line = (f"{name}: eps_dyn={m['eps']:.3e} (reltol/10: {m2['eps']:.3e}, {'agree' if conv else 'DISAGREE'}, "
                f"floor {m['floor']:.1e}) eps_NL={fmt_nl(m)} (report-only)")
        ok = gate(m, lim) and conv
        print(f"{line} -> {'ACCEPT' if ok else 'REJECT'}")
        bad += (not ok)
        for bn, kw in BROKEN.items():
            mb = run_point(pt, f"{name}_{bn}", outdir, **kw)
            okb = gate(mb, lim)
            print(f"  broken {bn}: eps_dyn={mb['eps']:.3e} eps_NL={fmt_nl(mb)} -> "
                  f"{'REJECT' if not okb else 'ACCEPT (this broken copy is not caught)'}")
            bad += okb
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
