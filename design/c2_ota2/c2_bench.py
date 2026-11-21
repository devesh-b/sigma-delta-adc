#!/usr/bin/env python3
"""C2 bench (WO-98): transistor OTA2 (netlist_ota2.py, 9/16 OTA1 cell on OTA1's bias nets) with the transistor OTA1
(c1_ota1/netlist.py, unchanged) supplying the shared bias. Sandbox only. Every row prints ACCEPT/REJECT.

    python c2_bench.py OUT opac   CI B [MUT]        # .op/.ac/.dc, cmfb dc: A0, GBW, PM@beta2, SR=I_tail/0.7pF, swing/A(v), margins, current
    python c2_bench.py OUT tran   CI B [MUT]        # cmfb sc, clocks at fs: step eps_dyn + SR (1.12 V), comparator kick CM, OTA1<->OTA2 coupling
    python c2_bench.py OUT toggle CI 0 [MUT]        # cmfb dc: boost toggle of the shared bias (OTA1 refs x2 + bank switch), 0.1 % settling
    python c2_bench.py OUT mc     CI B SEED N [MUT] # hand-Pelgrom offset MC, N OTA2 copies on one OTA1 bias, DC unity feedback
    python c2_bench.py OUT summary                  # tables, totals, broken-copy verdicts (summary.json / summary.txt)
    python c2_bench.py OUT jobs                     # job lines for scripts/lpool.sh

CI indexes revc_check.CORNERS9; B 0 = base (2 MHz), 1 = boost (4 MHz). Topology per system x: OTA1 in a CT integrator
model (Cs1 0.5 p, Cint1 4 p, load 0.52 p, mm3 3-sigma mismatch in tran), OTA2 in a CT model of its slot (Cs2 0.5 p,
Ck2 0.25 p to V_ICM, Cint2 1 p, comparator/route 0.07 p; pair offset 3 sigma on min1 in tran). DC feedback through
1 GOhm from an ideal level shift (out - V_OCM + V_ICM) so the op is defined with offsets; 1 ms time constant.
Rows and limits: SPEC 3.0 OTA2 rows and results/wo93/README.md section 1 (values in LIM). Broken copies: BROKEN.
"""
import json, math, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "c1_ota1")]
import sizes_draft as S  # noqa: E402
import netlist as NL  # noqa: E402
import sizes_ota2 as S2  # noqa: E402
import netlist_ota2 as N2  # noqa: E402
from revc_check import CORNERS9, LIB  # noqa: E402

FS = {0: 2e6, 1: 4e6}
LIM = dict(a0_db=75.0, av_db=75.0, span=1.41, gbw={0: 10e6, 1: 22.5e6}, sr={0: 13.5e6, 1: 27e6},
           eps={0: 1.4e-3, 1: 6e-4}, cm=10e-3, vos3=15e-3, tog=4e-6, tog_tol=1e-3, coup1=1e-5, coup2=1.4e-4,
           margin=0.05, itot=200e-6)
KICK_V = 47.4e-3                     # comparator kick per fire edge, top of 38.9-47.4 mV (C3 rev f/g)
STEP2, STEP1 = 1.12, 0.49            # OTA2 worst step (SPEC), OTA1 worst step
OTHER_I = {0: 4.96e-6 + 4e-6 + 2.5e-6, 1: 4.96e-6 + 4e-6 + 5e-6}   # C6 (SIM) + V_ICM/V_OCM src + switches (HAND, wo93 4)
BROKEN = {   # tag: (test, ci, b, mut, rows that must REJECT)
    "opac_tt_b0_nc_short": ("opac", 0, 0, "nc_short", ("a0", "av")),
    "opac_tt_b0_vocmm03": ("opac", 0, 0, "vocmm03", ("span",)),
    "opac_tt_b1_cl4": ("opac", 0, 1, "cl4", ("gbw",)),
    "opac_tt_b0_tail_half": ("opac", 0, 0, "tail_half", ("sr",)),
    "tran_tt_b0_tail_half": ("tran", 0, 0, "tail_half", ("eps",)),
    "tran_tt_b1_cm_open": ("tran", 0, 1, "cm_open", ("kick_cm",)),
    "tran_tt_b1_kb": ("tran", 0, 1, "kb", ("coup1", "coup2")),
    "toggle_tt_b0_cbig3n": ("toggle", 0, 0, "cbig3n", ("tog",)),
    "mc_tt_b0_s9_pair3": ("mc", 0, 0, "pair3", ("vos",)),
}
PCH = "pfet_g5v0d10v5"
CORE = {"min1": "pfet_01v8", "mpp1": PCH, "mt": PCH, "mn1": "nfet_g5v0d10v5", "mnc1": "nfet_g5v0d10v5",
        "mpc1": PCH, "mpl1": PCH, "mplc1": PCH}


def toks(m):
    return set(m.split("+")) if m else set()


def timing(b):
    T = 1 / FS[b]
    h = T / 2
    g = 0.025 * T
    return T, h, g, h - 2 * g


def ota1_text(b, cmfb, mut=None, toggle=False):
    txt = NL.build("ota1", cmfb=cmfb, fs=FS[b], mut=mut, boost=bool(b) and not toggle)
    if toggle:   # base geometry, bank switch gates on new ports bk / bkb (C6/C8 drive them in silicon)
        for a, c in ((f".subckt ota1 {NL.PORTS}", f".subckt ota1 {NL.PORTS} bk bkb"),
                     ("XSbkn gbk vss ivbpc", "XSbkn gbk bk ivbpc"), ("XSbkp gbk vdd ivbpc", "XSbkp gbk bkb ivbpc"),
                     ("Xmbku gbk vss vdd", "Xmbku gbk bk vdd")):
            assert txt.count(a) == 1, a
            txt = txt.replace(a, c)
    return txt


def inst(kind, x, sub, vdd, vocm="vocm", extra=""):
    k = kind
    return (f"Xo{k}_{x} {vdd} 0 i{k}p_{x} i{k}n_{x} o{k}p_{x} o{k}n_{x} vicm {vocm} ibtp_{x} ibn_{x} ibp_{x} ivbnc_{x} "
            f"ivbpc_{x} ivbl0_{x} hv 0 lv 0 0 ph1 ph1b ph2 ph2b hv{extra} {sub}")


def fb(k, x, cs, cint, ck, cl, sp, sn, vocm="vocm"):
    i_p, i_n, o_p, o_n = f"i{k}p_{x}", f"i{k}n_{x}", f"o{k}p_{x}", f"o{k}n_{x}"
    L = [f"Cin{k}p_{x} {sp} {i_p} {cs:g}", f"Cin{k}n_{x} {sn} {i_n} {cs:g}",
         f"Cf{k}p_{x} {o_p} {i_n} {cint:g}", f"Cf{k}n_{x} {o_n} {i_p} {cint:g}",
         f"Efb{k}p_{x} fb{k}p_{x} vicm {o_p} {vocm} 1", f"Efb{k}n_{x} fb{k}n_{x} vicm {o_n} {vocm} 1",
         f"Rfb{k}p_{x} fb{k}p_{x} {i_n} 1e9", f"Rfb{k}n_{x} fb{k}n_{x} {i_p} 1e9",
         f"Cl{k}p_{x} {o_p} 0 {cl:g}", f"Cl{k}n_{x} {o_n} 0 {cl:g}"]
    if ck:
        L += [f"Ck{k}p_{x} {i_p} vicm {ck:g}", f"Ck{k}n_{x} {i_n} vicm {ck:g}"]
    return L


def bias(x, b, pwl=None):
    c0, c1 = NL.bias_currents(False), NL.bias_currents(True)
    L = []
    for p in ("ibtp", "ibn", "ibp", "ivbnc", "ivbpc", "ivbl0"):
        val = pwl(c0[p], c1[p]) if pwl else f"{(c1 if b else c0)[p]:.6g}"
        L.append(f"I{p}_{x} {p}_{x} 0 {val}" if p in NL.SINK_PORTS else f"I{p}_{x} 0 {p}_{x} {val}")
    return L


def head(c, t, v, b, tag, clocks=True):
    T, h, g, th = timing(b)
    L = [f"* WO-98 c2_bench {tag}", f".lib {LIB} {c}", f".temp {t}",
         ".option gmin=1e-15 reltol=1e-6 abstol=1e-14 vntol=1e-9 method=gear",
         f"Vicm vicm 0 {S.V_ICM}", f"Vocm vocm 0 {S.V_OCM}", f"Vhv hv 0 {v}", "Vlv lv 0 1.8"]
    if clocks:
        L += [f"Vph1 ph1 0 PULSE(0 {v} {g:.6g} 0.5n 0.5n {th - 0.5e-9:.6g} {T:.6g})",
              f"Vph1b ph1b 0 PULSE({v} 0 {g:.6g} 0.5n 0.5n {th - 0.5e-9:.6g} {T:.6g})",
              f"Vph2 ph2 0 PULSE(0 {v} {h + g:.6g} 0.5n 0.5n {th - 0.5e-9:.6g} {T:.6g})",
              f"Vph2b ph2b 0 PULSE({v} 0 {h + g:.6g} 0.5n 0.5n {th - 0.5e-9:.6g} {T:.6g})"]
    else:
        L += ["Vph1 ph1 0 0", f"Vph1b ph1b 0 {v}", "Vph2 ph2 0 0", f"Vph2b ph2b 0 {v}"]
    return L


def run(text, tag, out, timeout):
    fn = os.path.join(out, tag + ".sp")
    open(fn, "w").write(text)
    try:
        r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=timeout)
        so, se = r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        so, se = "", "TIMEOUT"
    open(os.path.join(out, tag + ".log"), "w").write(so + "\n--- stderr\n" + se)
    vals = {}
    for ln in so.splitlines():
        if " = " in ln:
            k, _, x = ln.partition(" = ")
            try:
                vals[k.strip().lower()] = float(x.split()[0])
            except ValueError:
                pass
    lint = [l.strip() for l in (so + se).splitlines()
            if re.search(r"(error|unknown|singular|no convergence|timestep too small|could not find|transient op|TIMEOUT)", l, re.I)]
    return vals, lint


def par(x, i, dev, q):
    return f"@m.{x}.x{i}.msky130_fd_pr__{dev}[{q}]"


def row(rows, name, val, lim, ok, unit=""):
    rows[name] = dict(val=val, lim=lim, verdict="ACCEPT" if ok else "REJECT", unit=unit)


def load_csv(fn):
    a = np.loadtxt(fn, skiprows=1)
    os.remove(fn)
    return a


def ibranch(vals, src):
    for k in (f"i({src})", f"{src}#branch"):
        if k in vals:
            return abs(vals[k])
    return float("nan")


# ---------------------------------------------------------------- opac
def t_opac(c, t, v, b, mut, tag, out):
    mt = toks(mut)
    m2 = "+".join(x for x in mt if x in N2.NL_TOKS + ("tail_half", "ota1cell")) or None
    cl = (S2.C_L2 - S.C_CMFB_SENSE) * (4 if "cl4" in mt else 1)
    L = head(c, t, v, b, tag, clocks=False)
    L += [ota1_text(b, "dc"), N2.build("ota2", cmfb="dc", fs=FS[b], mut=m2)]
    L += [f"Vdd1_s vdd1_s 0 {v}", f"Vdd2_ac vdd2_ac 0 {v}", f"Vdd2_sw vdd2_sw 0 {v}",
          f"Vocm2 vocm2 0 {S.V_OCM + (-0.3 if 'vocmm03' in mt else 0.0)}"]
    L += bias("s", b) + [inst(1, "s", "ota1", "vdd1_s")] + fb(1, "s", 0.5e-12, 4e-12, 0, 0.52e-12, "vicm", "vicm")
    for x in ("ac", "sw"):   # both OTA2 copies hang on system s's bias nets
        L.append(inst(2, x, "ota2", f"vdd2_{x}", vocm="vocm2").replace(f"ibtp_{x} ibn_{x} ibp_{x} ivbnc_{x} ivbpc_{x} ivbl0_{x}",
                                                                      "ibtp_s ibn_s ibp_s ivbnc_s ivbpc_s ivbl0_s"))
        L += [f"Clp_{x} o2p_{x} 0 {cl:g}", f"Cln_{x} o2n_{x} 0 {cl:g}"]
    L += ["Efbp_ac fbp_ac vicm o2p_ac vocm2 1", "Efbn_ac fbn_ac vicm o2n_ac vocm2 1",
          "Rfbp_ac fbp_ac i2n_ac 1e9", "Rfbn_ac fbn_ac i2p_ac 1e9",
          "Vacp acp vicm dc 0 ac 0.5", "Vacn acn vicm dc 0 ac -0.5", "Cacp i2p_ac acp 1", "Cacn i2n_ac acn 1",
          "Vvid vid 0 0", "Esp i2p_sw vicm vid 0 0.5", "Esn i2n_sw vicm vid 0 -0.5"]
    L += [".control", "set wr_singlescale", "set wr_vecnames", "op",
          "print i(vdd1_s) i(vdd2_ac)", "print v(o2p_ac) v(o2n_ac) v(o2p_sw) v(o2n_sw)"]
    L += [f"print {par('xo2_ac', i, d, q)}" for i, d in CORE.items() for q in ("vds", "vdsat", "id")]
    L += ["ac dec 40 1 1e10", f"wrdata {tag}_ac.csv v(o2p_ac,o2n_ac)",
          "dc Vvid -1e-3 1e-3 1e-6", f"wrdata {tag}_dc.csv v(o2p_sw,o2n_sw)", "quit", ".endc", ".end"]
    vals, lint = run("\n".join(L) + "\n", tag, out, 900)
    rows, res = {}, {}
    try:
        ac = load_csv(os.path.join(out, tag + "_ac.csv"))
        dc = load_csv(os.path.join(out, tag + "_dc.csv"))
    except Exception as e:
        return dict(valid=False, why=f"no data {e!r}", lint=lint[:6]), rows
    f, H = ac[:, 0], ac[:, 1] + 1j * ac[:, 2]
    mag = np.abs(H)
    ph = np.degrees(np.unwrap(np.angle(H)))
    a0 = 20 * math.log10(mag[0])

    def cross(level):
        k = np.nonzero(mag < level)[0]
        if not len(k) or k[0] == 0:
            return float("nan"), float("nan")
        i = k[0]
        x = (math.log10(level) - math.log10(mag[i - 1])) / (math.log10(mag[i]) - math.log10(mag[i - 1]))
        fx = 10 ** (math.log10(f[i - 1]) + x * (math.log10(f[i]) - math.log10(f[i - 1])))
        return fx, ph[i - 1] + x * (ph[i] - ph[i - 1])
    gbw, _ = cross(1.0)
    fb2, phb = cross(1 / S2.BETA2)
    pm = 180 + phb
    vid, vod = dc[:, 0], dc[:, 1]
    vod = vod - np.interp(0.0, vid, vod)   # systematic offset of the sweep copy removed (static gain about zero input)
    nz = np.abs(vid) > 1.5e-6
    avs = np.where(nz, vod / np.where(nz, vid, 1), np.inf)
    av_db = 20 * np.log10(np.abs(avs))
    span = {}
    for sgn in (1, -1):
        sel = (np.sign(vid) == sgn) & nz & (av_db >= LIM["av_db"])
        span[sgn] = float(np.max(np.abs(vod[sel]))) if sel.any() else 0.0
    sp = min(span.values())
    inr = nz & (np.abs(vod) <= LIM["span"] / 1.0)
    av_min = float(np.min(av_db[inr])) if inr.any() else float("nan")
    av_ok = sp >= LIM["span"] and math.isfinite(av_min) and av_min >= LIM["av_db"]
    i_tail = abs(vals.get(par("xo2_ac", "mt", PCH, "id").lower(), float("nan")))
    sr = i_tail / S2.C_L2
    marg = {i: abs(vals.get(par("xo2_ac", i, d, "vds").lower(), float("nan"))) - abs(vals.get(par("xo2_ac", i, d, "vdsat").lower(), float("nan")))
            for i, d in CORE.items()}
    mmin = min(marg.values())
    i1, i2 = ibranch(vals, "vdd1_s"), ibranch(vals, "vdd2_ac")
    row(rows, "a0", a0, LIM["a0_db"], a0 >= LIM["a0_db"], "dB")
    row(rows, "gbw", gbw, LIM["gbw"][b], gbw >= LIM["gbw"][b], "Hz")
    row(rows, "pm_info", pm, "70-85 info", True, "deg")
    row(rows, "sr", sr, LIM["sr"][b], sr >= LIM["sr"][b], "V/s")
    row(rows, "span", sp, LIM["span"], sp >= LIM["span"], "V diff")
    row(rows, "av", av_min, LIM["av_db"], av_ok, "dB (static, |v|<=1.41)")
    row(rows, "margin", mmin, LIM["margin"], mmin >= LIM["margin"], "V")
    res = dict(valid=not any("singular" in l.lower() or "no convergence" in l.lower() for l in lint) and math.isfinite(a0),
               lint=lint[:6], f_beta=fb2, i_tail2=i_tail, i_ota1=i1, i_ota2=i2, i_ibn_src=NL.bias_currents(bool(b))["ibn"],
               span_pos=span[1], span_neg=span[-1], margins=marg, vo_cm=(vals.get("v(o2p_ac)", 0) + vals.get("v(o2n_ac)", 0)) / 2)
    return res, rows


# ---------------------------------------------------------------- tran
def pwl_steps(base, events, amp, tr=1e-9):
    """events: [(t, level)], level in units of amp (per side +-amp*level/2 is applied by caller)."""
    pts, lv = [(0.0, 0.0)], 0.0
    for te, l in events:
        pts += [(te, lv), (te + tr, l)]
        lv = l
    return " ".join(f"{a:.9g} {base + amp * y:.9g}" for a, y in pts)


def t_tran(c, t, v, b, mut, tag, out):
    mt = toks(mut)
    T, h, g, th = timing(b)
    m2 = "+".join(x for x in mt if x in N2.NL_TOKS + ("tail_half", "ota1cell")) or None
    vos3 = 3 * S2.sig_vt("m_in") * math.sqrt(2)
    systems = ["a", "b", "c"] + (["d"] if c == "tt" and t == 27 and not mut else [])
    k1 = (4, 8, 12)
    d2 = {4: -0.56, 8: 0.56, 12: -0.56}           # OTA2 output targets (diff), steps at ph2 rise of cycle k
    d1 = {4: -0.245, 8: 0.245, 12: -0.245}        # OTA1 output targets, steps at ph1 rise
    kicks = range(16, 26)
    tstop = 27 * T
    L = head(c, t, v, b, tag)
    L[3] = ".option gmin=1e-15 method=gear reltol=1e-5 abstol=1e-12 vntol=1e-8 chgtol=1e-16"   # WO-98 run 1: 1e-6 / 1e-9 aborted (timestep too small)
    L += [ota1_text(b, "sc", mut="mm3"), N2.build("ota2", cmfb="sc", fs=FS[b], mut=m2, vt={"min1": vos3})]
    for x in systems:
        act1 = x in ("a", "b", "d")
        act2 = x in ("b", "c")
        L += [f"Vdd1_{x} vdd1_{x} 0 {v}", f"Vdd2_{x} vdd2_{x} 0 {v}"] + bias(x, b)
        L += [inst(1, x, "ota1", f"vdd1_{x}"), inst(2, x, "ota2", f"vdd2_{x}")]
        g1 = 4e-12 / 0.5e-12 / 2
        ev1 = [(k * T + g, d1[k]) for k in k1] if act1 else []
        ev2 = [(k * T + h + g, d2[k]) for k in k1] if act2 else []
        L += [f"Vs1p_{x} s1p_{x} 0 PWL({pwl_steps(S.V_ICM, ev1, g1)})", f"Vs1n_{x} s1n_{x} 0 PWL({pwl_steps(S.V_ICM, ev1, -g1)})",
              f"Vs2p_{x} s2p_{x} 0 PWL({pwl_steps(S.V_ICM, ev2, 1.0)})", f"Vs2n_{x} s2n_{x} 0 PWL({pwl_steps(S.V_ICM, ev2, -1.0)})"]
        L += fb(1, x, 0.5e-12, 4e-12, 0, 0.52e-12, f"s1p_{x}", f"s1n_{x}")
        L += fb(2, x, S2.CS2, S2.CINT2, S2.CK2, S2.C_EXT2, f"s2p_{x}", f"s2n_{x}")
        if x == "c":
            ik = KICK_V * S2.C_L2 / 1e-9
            L += [f"Ikp_c o2p_c 0 PULSE(0 {ik:.6g} {16 * T + g:.9g} 0.2n 0.2n 0.8n {T:.9g})",
                  f"Ikn_c o2n_c 0 PULSE(0 {ik:.6g} {16 * T + g:.9g} 0.2n 0.2n 0.8n {T:.9g})"]
        if x == "b" and "kb" in mt:
            L.append("Ckb o2p_b ibn_b 1p")
    sv = " ".join(f"v(o1p_{x}) v(o1n_{x}) v(o2p_{x}) v(o2n_{x})" for x in systems)
    sv += " " + " ".join(f"v({p}_{x})" for x in ("a", "b") for p in ("ibtp", "ibn", "ibp", "ivbpc", "ivbnc"))
    L += [".control", "set wr_singlescale", "set wr_vecnames", f"save {sv}", f"tran 0.25n {tstop:.9g} 0 0.5n",
          f"wrdata {tag}_tr.csv {sv}", "quit", ".endc", ".end"]
    vals, lint = run("\n".join(L) + "\n", tag, out, 5400)
    rows = {}
    try:
        a = load_csv(os.path.join(out, tag + "_tr.csv"))
    except Exception as e:
        return dict(valid=False, why=f"no data {e!r}", lint=lint[:6]), rows
    names = sv.split()
    tt_ = a[:, 0]
    if tt_[-1] < 0.99 * tstop:
        return dict(valid=False, why=f"tran stopped at {tt_[-1]:.4g} s", lint=lint[:6]), rows
    col = {n: a[:, 1 + i] for i, n in enumerate(names)}
    at = lambda n, ts: float(np.interp(ts, tt_, col[n]))
    vd = lambda k, x, ts: at(f"v(o{k}p_{x})", ts) - at(f"v(o{k}n_{x})", ts)
    vc = lambda k, x, ts: 0.5 * (at(f"v(o{k}p_{x})", ts) + at(f"v(o{k}n_{x})", ts))
    eps, srs, eps1 = [], [], []
    for k in (8, 12):   # OTA2 steps from -+0.56 (half x2 peak); system c (OTA1 quiet)
        t0, ts, tl = k * T + h + g, k * T + 2 * h - g, (k + 3) * T + 2 * h - g
        pre, late = vd(2, "c", t0 - 2e-9), vd(2, "c", tl)
        aa = late - pre
        eps.append(abs(late - vd(2, "c", ts)) / abs(aa))
        sel = (tt_ >= t0) & (tt_ <= ts)
        y = (col["v(o2p_c)"] - col["v(o2n_c)"])[sel]
        tt2 = tt_[sel]
        fr = (y - pre) / aa
        try:
            t20, t80 = tt2[np.nonzero(fr >= 0.2)[0][0]], tt2[np.nonzero(fr >= 0.8)[0][0]]
            srs.append(0.6 * abs(aa) / (t80 - t20))
        except IndexError:
            srs.append(0.0)
        t01, ts1, tl1 = k * T + g, k * T + h - g, (k + 3) * T + h - g
        p1, l1 = vd(1, "a", t01 - 2e-9), vd(1, "a", tl1)
        eps1.append(abs(l1 - vd(1, "a", ts1)) / abs(l1 - p1))
    c1s = [abs(vd(1, "b", ts) - vd(1, "a", ts)) / STEP1 for k in k1 for ts in (k * T + h - g, k * T + 2 * h - g)]
    c2s = [abs(vd(2, "b", k * T + 2 * h - g) - vd(2, "c", k * T + 2 * h - g)) / STEP2 for k in k1]
    floor1 = max(abs(vd(1, "d", ts) - vd(1, "a", ts)) / STEP1 for k in k1 for ts in (k * T + h - g, k * T + 2 * h - g)) \
        if "d" in systems else None
    base_cm = vc(2, "c", 15 * T + h - g)
    base_d = vd(2, "c", 15 * T + h - g)
    cms = [abs(vc(2, "c", k * T + h - g) - base_cm) for k in kicks]
    dms = [abs(vd(2, "c", k * T + h - g) - base_d) for k in kicks]
    sel = tt_ >= 16 * T
    dip = float(np.min(np.minimum(col["v(o2p_c)"][sel], col["v(o2n_c)"][sel])))
    rip = {f"{p}": float(np.max(np.abs(col[f"v({p}_b)"] - col[f"v({p}_a)"]))) for p in ("ibtp", "ibn", "ibp", "ivbpc", "ivbnc")}
    row(rows, "eps", max(eps), LIM["eps"][b], max(eps) <= LIM["eps"][b])
    row(rows, "kick_cm", max(cms), LIM["cm"], max(cms) <= LIM["cm"], "V")
    row(rows, "coup1", max(c1s), LIM["coup1"], max(c1s) <= LIM["coup1"], "rel. to 0.49 V")
    row(rows, "coup2", max(c2s), LIM["coup2"], max(c2s) <= LIM["coup2"], "rel. to 1.12 V")
    res = dict(valid=not any("timestep too small" in l.lower() or "TIMEOUT" in l for l in lint), lint=lint[:6],
               eps_list=eps, sr_tran=min(srs), eps_ota1_info=max(eps1), coup1_floor=floor1, kick_dm_max=max(dms),
               kick_min_out_V=dip, bias_ripple_b_minus_a_V=rip, vos_applied=vos3)
    return res, rows


# ---------------------------------------------------------------- toggle
def t_toggle(c, t, v, b, mut, tag, out):
    mt = toks(mut)
    t1, t2, tend, tr = 2e-6, 7e-6, 12e-6, 10e-9
    pw = lambda a0, a1: f"PWL(0 {a0:.6g} {t1:.6g} {a0:.6g} {t1 + tr:.6g} {a1:.6g} {t2:.6g} {a1:.6g} {t2 + tr:.6g} {a0:.6g})"
    L = head(c, t, v, 0, tag, clocks=False)
    L += [ota1_text(0, "dc", toggle=True), N2.build("ota2", cmfb="dc", fs=FS[0])]
    L += [f"Vdd1_t vdd1_t 0 {v}", f"Vdd2_t vdd2_t 0 {v}"] + bias("t", 0, pwl=pw)
    L += [f"Vbk bk 0 PWL(0 0 {t1:.6g} 0 {t1 + tr:.6g} {v} {t2:.6g} {v} {t2 + tr:.6g} 0)",
          f"Vbkb bkb 0 PWL(0 {v} {t1:.6g} {v} {t1 + tr:.6g} 0 {t2:.6g} 0 {t2 + tr:.6g} {v})"]
    L += [inst(1, "t", "ota1", "vdd1_t", extra=" bk bkb"), inst(2, "t", "ota2", "vdd2_t")]
    L += fb(1, "t", 0.5e-12, 4e-12, 0, 0.52e-12, "vicm", "vicm") + fb(2, "t", S2.CS2, S2.CINT2, S2.CK2, S2.C_EXT2, "vicm", "vicm")
    if "cbig3n" in mt:
        L.append("Cbig ibtp_t vdd1_t 3n")
    L += [".control", "set wr_singlescale", "set wr_vecnames", "tran 1n 12u 0 5n",
          f"wrdata {tag}_tg.csv i(vdd1_t) i(vdd2_t) v(o2p_t) v(o2n_t)", "quit", ".endc", ".end"]
    vals, lint = run("\n".join(L) + "\n", tag, out, 1800)
    rows = {}
    try:
        a = load_csv(os.path.join(out, tag + "_tg.csv"))
    except Exception as e:
        return dict(valid=False, why=f"no data {e!r}", lint=lint[:6]), rows
    tt_ = a[:, 0]
    res = dict(valid=True, lint=lint[:6])
    worst = 0.0
    for nm, ci_ in (("ota2", 2), ("ota1", 1)):
        y = np.abs(a[:, ci_])
        for e0, e1, lab in ((t1, t2, "up"), (t2, tend, "down")):
            fin = float(np.mean(y[(tt_ >= e1 - 0.5e-6) & (tt_ < e1 - 1e-9)]))
            sel = (tt_ > e0) & (tt_ < e1 - 1e-9)
            bad = np.nonzero(np.abs(y[sel] - fin) > LIM["tog_tol"] * fin)[0]
            ts = (tt_[sel][bad[-1]] - e0) if len(bad) else 0.0
            res[f"t_settle_{nm}_{lab}"] = float(ts)
            res[f"i_{nm}_{lab}_final"] = fin
            if nm == "ota2":
                worst = max(worst, ts)
    row(rows, "tog", worst, LIM["tog"], worst <= LIM["tog"], "s (OTA2 supply current, 0.1 %)")
    return res, rows


# ---------------------------------------------------------------- mc
def t_mc(c, t, v, b, mut, tag, out, seed, n):
    mt = toks(mut)
    rng = np.random.default_rng(1000 + seed)
    pm = 3.0 if "pair3" in mt else 1.0
    L = head(c, t, v, b, tag, clocks=False)
    L += [ota1_text(b, "dc"), f"Vdd1_m vdd1_m 0 {v}", f"Vdd2 vdd2 0 {v}"] + bias("m", b) + [inst(1, "m", "ota1", "vdd1_m")]
    L += fb(1, "m", 0.5e-12, 4e-12, 0, 0.52e-12, "vicm", "vicm")
    for i in range(n):
        vt = {d: float(rng.normal(0, S2.sig_vt(k) * (pm if k == "m_in" else 1.0))) for d, k in S2.MC_DEV.items()}
        L.append(N2.build(f"ota2_m{i}", cmfb="dc", fs=FS[b], vt=vt))
        L.append(inst(2, f"m{i}", f"ota2_m{i}", "vdd2").replace(f"ibtp_m{i} ibn_m{i} ibp_m{i} ivbnc_m{i} ivbpc_m{i} ivbl0_m{i}",
                                                               "ibtp_m ibn_m ibp_m ivbnc_m ivbpc_m ivbl0_m"))
        L += [f"Efbp_m{i} fbp_m{i} vicm o2p_m{i} vocm 1", f"Efbn_m{i} fbn_m{i} vicm o2n_m{i} vocm 1",
              f"Rfbp_m{i} fbp_m{i} i2n_m{i} 1e9", f"Rfbn_m{i} fbn_m{i} i2p_m{i} 1e9"]
    L += [".control", "op"] + [f"print v(o2p_m{i}) v(o2n_m{i})" for i in range(n)] + ["quit", ".endc", ".end"]
    vals, lint = run("\n".join(L) + "\n", tag, out, 1800)
    rows = {}
    vos = [vals.get(f"v(o2p_m{i})", float("nan")) - vals.get(f"v(o2n_m{i})", float("nan")) for i in range(n)]
    vos = np.array(vos)
    if not np.all(np.isfinite(vos)):
        return dict(valid=False, why="missing samples", lint=lint[:6]), rows
    s3 = 3 * float(np.std(vos, ddof=1))
    mx = float(np.max(np.abs(vos)))
    ms3 = abs(float(np.mean(vos))) + s3   # D97 / CL-40: |mu| + 3 sigma <= 15 mV and every sample <= 15 mV
    row(rows, "vos", max(ms3, mx), LIM["vos3"], ms3 <= LIM["vos3"] and mx <= LIM["vos3"], "V (max of |mu|+3 sigma, |sample|max)")
    return dict(valid=True, lint=lint[:6], vos=vos.tolist(), sigma3=s3, absmax=mx, mean=float(np.mean(vos)),
                hand_pair_3sigma=3 * S2.sig_vt("m_in") * math.sqrt(2) * pm), rows


# ---------------------------------------------------------------- summary / jobs
def jobs(out):
    me = os.path.abspath(__file__)
    py = sys.executable
    J = []
    for tag, (test, ci, b, mut, _) in BROKEN.items():
        extra = " 9 50" if test == "mc" else ""
        J.append(f"cd {out} && {py} {me} {out} {test} {ci} {b}{extra} {mut}")
    J += [f"cd {out} && {py} {me} {out} mc 0 0 {s} 50" for s in range(4)]
    J += [f"cd {out} && {py} {me} {out} mc 2 1 5 50", f"cd {out} && {py} {me} {out} mc 5 0 6 50"]
    J += [f"cd {out} && {py} {me} {out} opac {ci} {b}" for ci in range(9) for b in (0, 1)]
    J += [f"cd {out} && {py} {me} {out} toggle {ci} 0" for ci in range(9)]
    J += [f"cd {out} && {py} {me} {out} tran {ci} {b}" for b in (1, 0) for ci in range(9)]
    print("\n".join(J))


def summary(out):
    R = {}
    for fn in sorted(os.listdir(out)):
        if fn.endswith(".json") and fn != "summary.json":
            R[fn[:-5]] = json.load(open(os.path.join(out, fn)))
            r_ = R[fn[:-5]]
            if r_["test"] == "mc" and r_["res"].get("vos"):   # re-judge stored samples at the current LIM (D97)
                v_ = np.array(r_["res"]["vos"])
                ms3_, mx_ = abs(v_.mean()) + 3 * v_.std(ddof=1), np.abs(v_).max()
                r_["rows"]["vos"] = dict(val=float(max(ms3_, mx_)), lim=LIM["vos3"], unit="V",
                                         verdict="ACCEPT" if ms3_ <= LIM["vos3"] and mx_ <= LIM["vos3"] else "REJECT")
    L, S_ = [], {}
    nom = {k: r for k, r in R.items() if not r.get("mut")}
    by = {}
    for k, r in nom.items():
        for name, rw in r["rows"].items():
            key = (r["test"], r["b"], name)
            by.setdefault(key, []).append((r["corner"], rw, r["res"].get("valid", False)))
    L.append("C2 bench (WO-98) nominal rows: per test, mode, row: worst value, limit, ACCEPT count / corners, invalid")
    for (test, b, name), lst in sorted(by.items()):
        vals_ = [x[1]["val"] for x in lst]
        hi = name in ("eps", "kick_cm", "coup1", "coup2", "tog", "vos")
        w = max(vals_) if hi else min(vals_)
        wc = lst[vals_.index(w)][0]
        nacc = sum(1 for x in lst if x[1]["verdict"] == "ACCEPT" and x[2])
        L.append(f"  {test:6s} b{b} {name:8s} worst {w:.4g} @ {wc}  lim {lst[0][1]['lim']}  ACCEPT {nacc}/{len(lst)}  invalid {sum(1 for x in lst if not x[2])}")
        S_[f"{test}_b{b}_{name}"] = dict(worst=w, at=wc, accept=nacc, n=len(lst))
    L.append("Broken copies (each must REJECT its target rows with valid data):")
    for tag, (test, ci, b, mut, tgt) in BROKEN.items():
        r = next((r for r in R.values() if r["test"] == test and r["ci"] == ci and r["b"] == b and r.get("mut") == mut), None)
        if r is None:
            L.append(f"  {tag}: MISSING")
            continue
        ok = r["res"].get("valid", False) and all(r["rows"].get(x, {}).get("verdict") == "REJECT" for x in tgt)
        L.append(f"  {tag}: {'BROKEN-REJECTS (gate live)' if ok else 'BROKEN-PASSES or INVALID (gate blind)'} "
                 + ", ".join(f"{x}={r['rows'].get(x, {}).get('val')}" for x in tgt))
        S_[tag] = ok
    # totals: worst OTA1 + OTA2 + other per mode over the opac corners
    for b in (0, 1):
        tot = [(r["res"]["i_ota1"] + r["res"]["i_ota2"] + OTHER_I[b], r["corner"], r["res"]["i_ota1"], r["res"]["i_ota2"])
               for r in nom.values() if r["test"] == "opac" and r["b"] == b and r["res"].get("valid")]
        if tot:
            w = max(tot)
            L.append(f"Total current b{b}: worst {w[0] * 1e6:.1f} uA @ {w[1]} (OTA1 {w[2] * 1e6:.1f}, OTA2 {w[3] * 1e6:.1f}, other "
                     f"{OTHER_I[b] * 1e6:.2f} HAND) vs 200 uA: margin {(200e-6 - w[0]) * 1e6:.1f} uA -> "
                     f"{'ACCEPT' if w[0] <= LIM['itot'] else 'REJECT'}")
            S_[f"itot_b{b}"] = dict(worst=w[0], at=w[1], ota1=w[2], ota2=w[3])
    mc = [x for r in nom.values() if r["test"] == "mc" and r["ci"] == 0 for x in r["res"].get("vos", [])]
    if mc:
        s3 = abs(float(np.mean(mc))) + 3 * float(np.std(mc, ddof=1))
        L.append(f"MC tt/27 pooled: n {len(mc)}, |mu|+3 sigma {s3 * 1e3:.2f} mV, |max| {max(map(abs, mc)) * 1e3:.2f} mV vs {LIM['vos3'] * 1e3:g} mV (D97) -> "
                 f"{'ACCEPT' if s3 <= LIM['vos3'] and max(map(abs, mc)) <= LIM['vos3'] else 'REJECT'}")
        S_["mc_tt_pooled"] = dict(n=len(mc), sigma3=s3)
    L.append(f"OTA2 gate-area sum (no bias legs): {S2.gate_area_um2():.0f} um2")
    txt = "\n".join(L)
    print(txt)
    open(os.path.join(out, "summary.txt"), "w").write(txt + "\n")
    json.dump(S_, open(os.path.join(out, "summary.json"), "w"), indent=1, default=str)


def main():
    out, test = os.path.abspath(sys.argv[1]), sys.argv[2]
    os.makedirs(out, exist_ok=True)
    if test == "jobs":
        return jobs(out)
    if test == "summary":
        return summary(out)
    if not os.path.exists(os.path.join(out, ".spiceinit")):
        open(os.path.join(out, ".spiceinit"), "w").write("set num_threads=1\n")
    ci, b = int(sys.argv[3]), int(sys.argv[4])
    c, t, v = CORNERS9[ci]
    if test == "mc":
        seed, n = int(sys.argv[5]), int(sys.argv[6])
        mut = sys.argv[7] if len(sys.argv) > 7 else None
        tag = f"mc_{c}{t}_b{b}_s{seed}" + (f"_{mut}" if mut else "")
        res, rows = t_mc(c, t, v, b, mut, tag, out, seed, n)
    else:
        mut = sys.argv[5] if len(sys.argv) > 5 else None
        tag = f"{test}_{c}{t}_b{b}" + (f"_{mut}" if mut else "")
        res, rows = dict(opac=t_opac, tran=t_tran, toggle=t_toggle)[test](c, t, v, b, mut, tag, out)
    corner = f"{c}/{t}/{v}"
    for name, rw in rows.items():
        print(f"{rw['verdict']} {tag} {name} {rw['val']:.5g} lim {rw['lim']} {rw['unit']}")
    if not res.get("valid", False):
        print(f"INVALID {tag} {res.get('why', '')} {res.get('lint', '')}")
    json.dump(dict(test=test, ci=ci, b=b, mut=mut, corner=corner, rows=rows, res=res), open(os.path.join(out, tag + ".json"), "w"),
              indent=1, default=float)


if __name__ == "__main__":
    main()
