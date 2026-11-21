#!/usr/bin/env python3
"""WO-95: full-chip transistor-level top bench (analog top at transistor level, ideal digital loop logic).

    python top_bench.py OUT GATE [--corner tt --temp 27 --vdd 3.3] [--copy nom|<broken>] [--n 1024] [--opt O1]
    GATE: smoke | a (start-up) | bc (DC function + INL spot points) | d (chop pair) | e (overload / recovery)

Transistor level: OTA1 and OTA2 (both the C1 `ota1` cell, design/c1_ota1/netlist.py, cmfb="sc", base geometry;
OTA2 = OTA1-cell reuse until WO-93 decides), comparator C3 (design/c3_comp/netlist.py, default sizes = rev g),
every SC switch at the C4 sizes (design/c4_sw/netlist.py SW, L 0.5, 3.3 V TG / NMOS) driven by the C4 phase
generator c4_gen (HVL cells, level shifters, VDPWR detector, chopper latch, strobe), C6 option (c) core
(design/c6_bias/c6_spot.py deck(), skewed-amp Banba + core-derived bias_ok, code 100) with the C6.3 port mirrors
(sinks: NMOS from VN, W = 2 um x I_port / I_TGT at L 4; sources: PMOS units from VG, m = round(I_port / I_unit)).
These mirrors are a bench stand-in for the not-yet-netlisted C6.3 distribution (uncascoded; their error is reported).

Ideal (behavioural) parts: the C9 loop logic only - fs bit clock (1.8 V, low = sample phase, high = integrate),
the DAC flop (comparator q captured on the fs rising edge, forced +1 in reset and for slot 0), rst_analog
schedule, swap pin, dec = NAND(q, qb); the bias_ok reset hold (rst forced high while bias_ok is low, plus a fixed
release time t_rel); ideal supplies VAPWR (ramp) / VDPWR 1.8 V, ideal V_ICM / V_OCM, VIN / VREF sources behind
the 500 ohm + 5 pF pads, per-OTA output reset short (TG 4/12 on C4 r2) as in gate B.

Hold scaling (D85/D88): on silicon rst_analog is held for the C9 VAPWR-good count (2^16 fs cycles after rst_n) plus
256 fs cycles after the final bias_ok rise. Here the release is at t_rel (default 100 us = 200 fs cycles at 2 MHz,
1/329 of the 65 792-cycle hold); gate (a) checks that bias_ok is up and the bias current within +-1 % of its final
value at t_rel, so the shortened hold is valid only if (a) passes.

Decimation: residue estimate u_hat = SPEC 3.7 reconstruction with x2[N] from the sim (tier1_tb.reconstruct, as gate
B) for INL; bits-only code (what C9 / Ref A accumulates: same formula without the x2 term) against the bits-only code
of the ideal discrete loop (tier1_tb.ideal_loop, the golden recursion) for the DC-function row.
"""
import argparse, json, math, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..")
sys.path[:0] = [os.path.join(D, "c1_ota1"), D, os.path.join(D, "tier1"), os.path.join(D, "c6_bias")]
import numpy as np  # noqa: E402
import params as P  # noqa: E402
import sizes_draft as S  # noqa: E402   (C1 sizes)
import netlist as NL  # noqa: E402      (C1 netlist)
import tier1_tb as TB  # noqa: E402
import c6_spot as C6  # noqa: E402
from revc_check import LIB  # noqa: E402

PY = sys.executable
HVN, HVP, PRE, LSW, DX = "nfet_g5v0d10v5", "pfet_g5v0d10v5", "sky130_fd_pr__", 0.5, 0.29
VREFP, VREFN = 2.048, 0.0
VREF = VREFP - VREFN
VINCM = VREF / 2
VDL = 1.8
U_OFF5 = 5e-6 / VREF        # SPEC offset 5 uV, in u (u = Vdiff / VREF)
GAIN_TOL = 0.005            # SPEC gain 0.5 %
INL_BUDGET = 20e-6 * 2      # SPEC all-block INL 20 ppm of FSR (FSR = 2 in u)
INL_GATE = 1.333            # ppm, precision gate B number (SPEC row 94), used for (c)
# C6 tune (WO-64, used unchanged by WO-80 / WO-87: out/tune.json): R2/R1 2.45, R1 144.8 um
C6_RATIO, C6_R1 = 2.45, 144.8
BROKEN = dict(a="nosu", bc="dacswap", c="ota2dead", d="noswap", e="noreset")

with open(os.path.join(D, "c4_sw", "netlist.py")) as f:   # C4 SW sizes / PH list (no import: module-name clash)
    _src = f.read()
_ns = {}
exec(compile(_src.split("def mos(")[0].replace("import os\nimport sys", "import os, sys"), "c4sizes", "exec"), _ns)
SW, PH, HVL = _ns["SW"], _ns["PH"], _ns["HVL"]


def mos(name, d, g, s, b, dev, w, l):
    return (f"X{name} {d} {g} {s} {b} {PRE}{dev} w={w:g} l={l:g} m=1 ad={w * DX:.4g} as={w * DX:.4g} "
            f"pd={2 * (w + DX):.4g} ps={2 * (w + DX):.4g}")


def sw(name, a, b, ph, key, swap_dev=False):
    """C4 switch at the SW[key] sizes on phase ph (ph_t NMOS gate, ph_c PMOS gate)."""
    wn, wp = SW[key]
    out = [mos(name + "n", a, f"{ph}_t", b, "0", HVN, wn, LSW)]
    if wp:
        out.append(mos(name + "p", a, f"{ph}_c", b, "vdd", HVP, wp, LSW))
    return out


def sub_text(cmd):
    return subprocess.run([PY] + cmd, capture_output=True, text=True, check=True).stdout


def c6_subckt(corner, temp, vdd, mut, tr):
    """Wrap the c6_spot tran deck devices (code 100) as .subckt c6core vdd vg vn ok."""
    txt, _ = C6.deck("tran", corner, temp, vdd, mut=mut, tr=tr, ratio=C6_RATIO, r1=C6_R1)
    keep = [ln for ln in txt.splitlines() if ln[:1] in ("X", "C", "R") or ln.startswith(("Vlk", "Vsm"))]
    return ".subckt c6core vdd vg vn ok\n" + "\n".join(keep) + "\n.ends c6core\n"


def schedule(n, nrst, T, t_rel, us):
    """Block m: reset [b_m, b_m + nrst T), conversion t0_m = b_m + nrst T, b_m = t_rel + m (nrst + n) T (b_0 = t_rel - nrst T + nrst T)."""
    blk = (nrst + n) * T
    t0 = [t_rel + nrst * T + m * blk for m in range(len(us))]
    return blk, t0


def pwl(pts):
    return " ".join(f"{t:.9e} {v:.9g}" for t, v in pts)


def steps(t_list, vals, v0, dt=0.1, T=None):
    """Piecewise-constant PWL that changes to vals[m] around t_list[m] (ramp T*dt)."""
    pts, cur = [(0.0, v0)], v0
    for t, v in zip(t_list, vals):
        if v != cur:
            pts += [(t, cur), (t + 0.1 * T, v)]
            cur = v
    return pts


def build(a, us, swaps=None, vos=None, t_rel=None):
    """Return (deck, meta). us: u per conversion (first one = dummy, discarded); swaps / vos: per conversion."""
    fs, n, nrst = a.fs, a.n, 3
    T = 1.0 / fs
    t_rel = a.t_rel if t_rel is None else t_rel
    t_rel = math.ceil(t_rel / T) * T
    blk, t0 = schedule(n, nrst, T, t_rel, us)
    tstop = t0[-1] + n * T + 0.5 * T
    toks = set(a.copy.split("+")) if a.copy != "nom" else set()
    o = P.option_ladder(a.opt)
    tmax = o["tmax_ns"] * 1e-9
    if o.get("tau_floor_div"):
        tmax = min(tmax, 1.0 / (2 * math.pi * P.TIER1_BETA1 * 10e6) / o["tau_floor_div"])
    L = [f"* WO-95 full-chip top bench (design/top/top_bench.py) gate {a.gate} copy {a.copy} {a.corner}/{a.temp}/{a.vdd}",
         f".options method={o['method']} reltol={o['reltol']:g} chgtol={o['chgtol']:g} vntol={o['vntol']:g} "
         f"abstol={o['abstol']:g} trtol={o['trtol']:g}",
         f".lib {LIB} {a.corner}", f".include {HVL}", f".temp {a.temp:g}",
         ".model SWL SW(Vt=0.5 Vh=0.0 Ron=10 Roff=1e12)"]
    # blocks
    L.append(NL.build("ota1", cmfb="sc", fs=fs, boost=False))
    if a.ota2_sub:   # D91: WO-98 OTA2 subckt (same port order as ota1), swapped in by path
        L.append(open(a.ota2_sub).read())
    L.append(sub_text([os.path.join(D, "c3_comp", "netlist.py")]))
    L.append(sub_text([os.path.join(D, "c4_sw", "netlist.py")]).replace("\n.subckt", "\n.subckt", 1))
    L.append(c6_subckt(a.corner, a.temp, a.vdd, "nosu" if "nosu" in toks else "none", a.tramp))
    # supplies: VAPWR ramp (from 50 mV like C6, through 1 ohm), VDPWR ideal 1.8 V
    L += [f"Vvap vap 0 PWL(0 {C6.VPRE} 10n {C6.VPRE} {10e-9 + a.tramp:.6e} {a.vdd:g})", "Rvap vap vdd 1",
          f"Vvdl vdl 0 {VDL:g}", f"Vicm vicm 0 {S.V_ICM:g}", f"Vocm vocm 0 {S.V_OCM:g}", f"Vcmin vcmin 0 {VINCM:g}"]
    # C6 core + C6.3 bench mirrors to both OTAs' ports
    L.append("Xc6 vdd vg vn ok c6core")
    iu = C6.I_TGT / (C6.G0 + C6.CODE_RESET)
    ports = NL.bias_currents(False)
    meta_ports = {}
    for k in ((1,) if a.ota2_shared else (1, 2)):
        sc = 0.1 if (k == 2 and "ota2dead" in toks) else 1.0
        for prt, i_ in ports.items():
            node = f"b{k}_{prt}"
            if i_ < 1e-9:
                meta_ports[node] = 0.0
                continue
            r = i_ * sc / C6.I_TGT
            if prt in NL.SINK_PORTS:
                L.append(mos(f"mir{k}{prt}", f"{node}_m", "vn", "0", "0", HVN, C6.MN_W * r, C6.MN_L))
                meta_ports[node] = C6.I_TGT * r
            else:
                m = max(1, round(i_ * sc / iu))
                L.append(f"Xmir{k}{prt} {node}_m vg vdd vdd {PRE}{HVP} w={C6.UW:g} l={C6.UL:g} m={m}")
                meta_ports[node] = iu * m
            L.append(f"Vm{k}{prt} {node} {node}_m 0")
    # C4 phase generator (VAPWR domain), C9-side inputs at 1.8 V
    L.append("Xg vdd vdl 0 fs y swap short chop rst order dec " + " ".join(f"{x}_t {x}_c" for x in PH)
             + " isl rstb chp chn chlp chln phc pwrok fsh c4_gen")
    L += [f"Vfs fs 0 PULSE(0 {VDL} {T / 2:.6e} 1n 1n {T / 2 - 1e-9:.6e} {T:.6e})",
          "Vshort short 0 0", "Vchop chop 0 0", f"Vorder order 0 {VDL}"]
    # ideal C9 loop logic: rst schedule (0/1), slot-0 force window, bias_ok hold
    rs, fr = [(0.0, 1.0)], [(0.0, 1.0)]
    for m, t in enumerate(t0):
        tb = t - nrst * T
        if m and "noreset" not in toks:
            rs += [(tb, 0.0), (tb + 1e-10, 1.0)]
            fr += [(tb, 0.0), (tb + 1e-10, 1.0)]
        if m == 0 or "noreset" not in toks:
            rs += [(t, 1.0), (t + 1e-10, 0.0)]
        fr += [(t + 0.75 * T, 1.0), (t + 0.75 * T + 1e-10, 0.0)]
    L += [f"Vrss rss 0 PWL({pwl(rs)})", f"Vfrs frs 0 PWL({pwl(fr)})",
          "Bbok bok 0 V = u(V(ok)-1.5)",
          f"Brst rst 0 V = {VDL}*max(V(rss),1-V(bok))",
          "Bfrc frc 0 V = max(V(frs),1-V(bok))",
          f"Bdec dec 0 V = {VDL}*(1-u(V(q)-0.9)*u(V(qb)-0.9))",
          "Bcmpv cmpv 0 V = V(frc)+(1-V(frc))*(2*u(V(q)-0.9)-1)",
          f"Vcap cap 0 PULSE(0 1 {T / 2 - 2.5e-9:.6e} 0.2n 0.2n 1.5n {T:.6e})",
          "Slat cmpv yq cap 0 SWL", "Chold yq 0 1p", f"By y 0 V = {VDL}*u(V(yq))"]
    sws = swaps or [0] * len(us)
    if "noswap" in toks:
        sws = [0] * len(us)
    L.append(f"Vswap swap 0 PWL({pwl(steps([t - nrst * T + 0.05 * T for t in t0], [VDL * s for s in sws], VDL * sws[0], T=T))})")
    # inputs + pads, references + pads
    for nm, sgn in (("vinp", 1), ("vinn", -1)):
        pts = steps([t - nrst * T + 0.1 * T for t in t0], [VINCM + sgn * u * VREF / 2 for u in us], VINCM + sgn * us[0] * VREF / 2, T=T)
        L += [f"V{nm}_s {nm}_s 0 PWL({pwl(pts)})", f"Rpad_{nm} {nm}_s {nm} {P.PAD_R:g}", f"Cpad_{nm} {nm} 0 {P.PAD_C:g}"]
    for nm, v in (("vrefp", VREFP), ("vrefn", VREFN)):
        L += [f"V{nm}_s {nm}_s 0 {v:g}", f"Rpad_{nm} {nm}_s {nm} {P.PAD_R:g}", f"Cpad_{nm} {nm} 0 {P.PAD_C:g}"]
    # stage 1 / stage 2 SC network (C4 switch table DESIGN.md 2; D12 top-plate shorts)
    dsw = "dacswap" in toks
    for s, o_ in (("p", "n"), ("n", "p")):
        hi, lo = ("vrefp", "vrefn") if s == "p" else ("vrefn", "vrefp")
        dh, dl = ("dl", "dh") if dsw else ("dh", "dl")
        L += sw(f"sin{s}", f"vin{s}", f"b1{s}", "pas", "sin") + sw(f"ssw{s}", f"vin{o_}", f"b1{s}", "swp", "sin")
        L += sw(f"ssh{s}", "vcmin", f"b1{s}", "sho", "sin")
        L += sw(f"sdh{s}", f"b1{s}", hi, dh, "sdh" if hi == "vrefp" else "sdl")
        L += sw(f"sdl{s}", f"b1{s}", lo, dl, "sdl" if lo == "vrefn" else "sdh")
        L += sw(f"sg1{s}", f"tp1{s}", f"vg1{s}", "ie", "sg")
        L += [f"Cs1{s} b1{s} tp1{s} {P.CS1:g}", f"Cint1{s} vg1{s} o1{s} {P.CINT1:g}", f"Cpv1{s} vg1{s} 0 0.035p"]
        L += sw(f"s2in{s}", f"o1{s}", f"b2{s}", "sl", "s2in")
        L += sw(f"sg2{s}", f"tp2{s}", f"vg2{s}", "ie", "sg")
        L += sw(f"skh{s}", f"bk{s}", hi, "kh", "skh" if hi == "vrefp" else "skl")
        L += sw(f"skl{s}", f"bk{s}", lo, "kl", "skl" if lo == "vrefn" else "skh")
        L += [f"Cs2{s} b2{s} tp2{s} {P.CS2:g}", f"Ck{s} bk{s} tp2{s} {P.K * P.CS2:g}", f"Cint2{s} vg2{s} o2{s} {P.CINT2:g}",
              f"Cpv2{s} vg2{s} 0 0.035p", f"Cxo1{s} o1{s} 0 0.02p", f"Cxo2{s} o2{s} 0 0.02p"]
    L += sw("stp1", "tp1p", "tp1n", "se", "stp") + sw("stp2", "tp2p", "tp2n", "se", "stp")
    L += sw("s2cm", "b2p", "b2n", "il", "s2cm") + sw("sk0", "bkp", "bkn", "k0", "sk0")
    L += sw("so1", "o1p", "o1n", "r2", "s2cm") + sw("so2", "o2p", "o2n", "r2", "s2cm")
    # optional bench offset at OTA1's input (chop-pair gate): vg1n -> OTA inp through a PWL source
    if vos:
        vp = steps([t - nrst * T + 0.1 * T for t in t0], vos, vos[0], T=T)
        L.append(f"Vos1 vg1n vg1nx PWL({pwl(vp)})")
        i1 = "vg1nx"
    else:
        i1 = "vg1n"
    b2 = 1 if a.ota2_shared else 2   # D91: OTA2 shares OTA1's bias nets (WO-98 cell); OTA1-cell stand-in: own mirrors
    tail = "chp chn chlp chln isl il_t il_c sl_t sl_c rstb ota1"
    L.append(f"Xota1 vdd 0 {i1} vg1p o1p o1n vicm vocm " + " ".join(f"b1_{p}" for p in ports) + f" {tail}")
    L.append("Xota2 vdd 0 vg2n vg2p o2p o2n vicm vocm " + " ".join(f"b{b2}_{p}" for p in ports)
             + " " + tail.replace(" ota1", " " + (a.ota2_name if a.ota2_sub else "ota1")))
    L.append("Xc3 o2p o2n phc q qb vdl 0 c3_comp")
    L += ["Cq q 0 20f", "Cqb qb 0 20f", ".ic v(yq)=1"]
    L.append(f".tran 1n {tstop:.9e} 0 {tmax:.6e}")
    vecs = ["v(yq)", "v(o2p)", "v(o2n)", "v(o1p)", "v(o1n)", "v(ok)", "i(vm1ibtp)", "v(vdd)", "v(q)"]
    L += [".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=8", "run",
          "echo FINAL_TIME_CHECK", "print time[length(time)-1]", f"wrdata {a.csv} " + " ".join(vecs), "quit", ".endc", ".end"]
    meta = dict(T=T, n=n, nrst=nrst, t0=t0, t_rel=t_rel, tstop=tstop, u=list(us), swaps=list(sws), vos=vos, ports=meta_ports,
                tmax=tmax, opt=o)
    return "\n".join(L) + "\n", meta


def run(a, us, tag, **kw):
    os.makedirs(a.out, exist_ok=True)
    a.csv = os.path.join(a.out, tag + ".csv")
    cir, log = os.path.join(a.out, tag + ".cir"), os.path.join(a.out, tag + ".log")
    deck, meta = build(a, us, **kw)
    open(cir, "w").write(deck)
    t_s = time.time()
    p = subprocess.run(["timeout", str(a.deck_timeout), os.environ.get("NGSPICE", "ngspice"), "-b", "-o", log, cir],
                       capture_output=True, text=True, cwd=a.out)
    res = dict(tag=tag, runtime_s=time.time() - t_s, rc=p.returncode, problems=[], meta=meta)
    txt = open(log).read() if os.path.exists(log) else ""
    res["problems"] += [f"log: {l.strip()}" for l in txt.splitlines() if TB.BAD_LOG.search(l)
                        and "gmin" not in l.lower()][:5]
    if re.search(r"transient op", txt, re.I) or re.search(r"(gmin|source) stepping", txt, re.I):
        res["problems"].append("log: transient-op / stepping fallback")
    if f"reltol={meta['opt']['reltol']:g}" not in txt.lower():
        res["problems"].append("log does not echo the reltol option")
    if not os.path.exists(a.csv) or os.path.getsize(a.csv) < 1000:
        res["problems"].append(f"no / empty data file (rc {p.returncode})")
        return res, None
    d = np.loadtxt(a.csv, skiprows=1)
    os.remove(a.csv)
    t = d[:, 0]
    if abs(t[-1] - meta["tstop"]) > 1e-9 * meta["tstop"] + 1e-12:
        res["problems"].append(f"final time {t[-1]:.6e} != tstop {meta['tstop']:.6e}")
    if not np.all(np.isfinite(d)):
        res["problems"].append("NaN/inf in data")
    cols = dict(t=t, yq=d[:, 1], o2p=d[:, 2], o2n=d[:, 3], o1p=d[:, 4], o1n=d[:, 5], ok=d[:, 6], ib=d[:, 7], vdd=d[:, 8])
    res["npts"] = int(len(t))
    T, n = meta["T"], meta["n"]
    convs = []
    for m, t0 in enumerate(meta["t0"]):
        y = np.interp(t0 + np.arange(n) * T + 0.75 * T, t, cols["yq"])
        if np.max(np.abs(np.abs(y) - 1)) > 0.05:
            res["problems"].append(f"conv {m}: bits not +-1")
        y = np.where(y > 0, 1.0, -1.0)
        te = t0 + n * T - 5e-9
        x2 = (np.interp(te, t, cols["o2p"]) - np.interp(te, t, cols["o2n"])) / VREF
        x1 = (np.interp(te, t, cols["o1p"]) - np.interp(te, t, cols["o1n"])) / VREF
        cm = lambda p_, n_, tt: 0.5 * (np.interp(tt, t, cols[p_]) + np.interp(tt, t, cols[n_]))
        uh = TB.reconstruct(y, x2, n, P.C1, P.C2, P.K)
        ub = TB.reconstruct(y, 0.0, n, P.C1, P.C2, P.K)
        yi, x2i = TB.ideal_loop(meta["u"][m], n, P.C1, P.C2, P.K)
        ug = TB.reconstruct(yi, 0.0, n, P.C1, P.C2, P.K)
        convs.append(dict(u=meta["u"][m], u_hat=float(uh), code_bits=float(ub), code_gold=float(ug), x1n=float(x1), x2n=float(x2),
                          ones=float(np.mean(y > 0)), ocm1=float(cm("o1p", "o1n", t0)), ocm2=float(cm("o2p", "o2n", t0)),
                          bits_differ_gold=int(np.sum(y != yi))))
    res["convs"] = convs
    # start-up record (gate a): bias_ok rises, master-port current settle
    ok = cols["ok"] > 1.5
    rises = np.where(np.diff(ok.astype(int)) == 1)[0]
    drops = np.where(np.diff(ok.astype(int)) == -1)[0]
    ib = -cols["ib"]   # current into the sink mirror drain node (Vm from port to mirror drain): sign-normalised below
    ib = ib if np.median(ib[t > meta["t_rel"]]) > 0 else -ib
    ifin = float(np.median(ib[t > meta["t0"][0]]))
    rel = meta["t_rel"]
    res["startup"] = dict(ok_rises_us=[float(t[i] * 1e6) for i in rises[:6]], ok_drops_us=[float(t[i] * 1e6) for i in drops[:6]],
                          ok_at_rel=bool(np.interp(rel, t, cols["ok"]) > 1.5), ib_final=ifin, ib_design=meta["ports"]["b1_ibtp"],
                          ib_at_rel_err=float(np.interp(rel, t, ib) / ifin - 1), ib_range_after_rel=float((ib[t > rel].max() - ib[t > rel].min()) / ifin))
    within = np.abs(ib / ifin - 1) <= 0.01
    last_out = np.where(~within)[0]
    res["startup"]["t_settle_1pct_us"] = float(t[last_out[-1] + 1] * 1e6) if len(last_out) and last_out[-1] + 1 < len(t) else float("nan")
    return res, cols


def healthy(res):
    return not res["problems"] and res.get("convs")


def verdict(a, ok, res, extra):
    hl = healthy(res)
    row = dict(gate=a.gate, copy=a.copy, ota2=a.ota2_id, corner=f"{a.corner}/{a.temp}/{a.vdd}", n=a.n, opt=a.opt, healthy=bool(hl), pass_gate=bool(hl and ok),
               runtime_s=res["runtime_s"], npts=res.get("npts"), problems=res["problems"], convs=res.get("convs"),
               startup=res.get("startup"), ports=res["meta"]["ports"], t_rel_us=res["meta"]["t_rel"] * 1e6, sim_time_s=res["meta"]["tstop"]) | extra
    json.dump(row, open(os.path.join(a.out, res["tag"] + ".json"), "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in row.items() if k not in ("convs", "ports")}, default=str))
    if a.copy != "nom":
        if hl and not ok:
            print("broken copy REJECTED (good)"); sys.exit(0)
        if hl:
            print("broken copy PASSED (check is blind)"); sys.exit(1)
        print("BROKEN COPY INVALID (unhealthy run)"); sys.exit(2)
    print("VERDICT", "ACCEPT" if hl and ok else "REJECT")
    sys.exit(0 if hl and ok else 1)


def fn_tol(u):
    return GAIN_TOL * abs(u) + U_OFF5 + INL_BUDGET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("gate", choices=("smoke", "a", "bc", "d", "e"))
    ap.add_argument("--corner", default="tt"); ap.add_argument("--temp", type=float, default=27); ap.add_argument("--vdd", type=float, default=3.3)
    ap.add_argument("--copy", default="nom"); ap.add_argument("--n", type=int, default=1024); ap.add_argument("--m", type=int, default=7)
    ap.add_argument("--fs", type=float, default=2e6); ap.add_argument("--opt", default="O1")
    ap.add_argument("--t-rel", dest="t_rel", type=float, default=100e-6); ap.add_argument("--tramp", type=float, default=1e-6)
    ap.add_argument("--ota2-sub", default=None, help="D91: WO-98 OTA2 subckt file (ota1 port order); default = OTA1 cell")
    ap.add_argument("--ota2-name", default="ota2"); ap.add_argument("--ota2-shared", action="store_true", help="OTA2 on OTA1's bias nets")
    ap.add_argument("--deck-timeout", type=int, default=250000)
    a = ap.parse_args()
    a.ota2_id = ("ota2-" + os.path.basename(a.ota2_sub).split(".")[0]) if a.ota2_sub else "ota2-ota1cell"
    tag = f"g{a.gate}_{a.copy}_{a.ota2_id}_{a.corner}{a.temp:g}_N{a.n}_{a.opt}"
    if a.gate == "smoke":
        res, _ = run(a, (0.5, 0.5, -0.3), tag)
        c = res.get("convs") or []
        ok = bool(c) and all(abs(x["u_hat"] - x["u"]) <= fn_tol(x["u"]) for x in c[1:])
        verdict(a, ok, res, dict(sec_per_conv=res["runtime_s"] / max(len(c), 1)))
    if a.gate == "a":       # start-up -> first valid conversion (u 0.5), no dummy discarded: the first conversion IS the gate
        res, _ = run(a, (0.5, -0.3), tag)
        su, c = res.get("startup", {}), res.get("convs") or []
        chk = dict(ok_up_at_rel=su.get("ok_at_rel", False), no_ok_drop_after_rel=all(x < res["meta"]["t_rel"] * 1e6 for x in su.get("ok_drops_us", [])),
                   ib_settled_at_rel=abs(su.get("ib_at_rel_err", 1)) <= 0.01, ib_steady=su.get("ib_range_after_rel", 1) <= 0.01,
                   cm_ok=all(abs(x["ocm1"] - S.V_OCM) <= 0.05 and abs(x["ocm2"] - S.V_OCM) <= 0.05 for x in c),
                   first_conv_ok=bool(c) and abs(c[0]["u_hat"] - c[0]["u"]) <= fn_tol(c[0]["u"]),
                   second_conv_ok=len(c) > 1 and abs(c[1]["u_hat"] - c[1]["u"]) <= fn_tol(c[1]["u"]))
        verdict(a, all(chk.values()), res, dict(checks=chk))
    if a.gate == "bc":      # DC function at m points (b) and endpoint INL (c) from the same conversions; dummy first
        u = TB.u_points(a.m, 0.9)
        res, _ = run(a, (u[0],) + tuple(u), tag)
        c = (res.get("convs") or [])[1:]
        extra = {}
        if c:
            uin = np.array([x["u"] for x in c]); uh = np.array([x["u_hat"] for x in c])
            g = TB.inl_gain(uin, uh)
            nb = TB.reconstruct(np.ones(a.n), 1.0, a.n, P.C1, P.C2, P.K) - TB.reconstruct(np.ones(a.n), 0.0, a.n, P.C1, P.C2, P.K)
            fb = [abs(x["u_hat"] - x["u"]) <= fn_tol(x["u"]) for x in c]
            fg = [abs(x["code_bits"] - x["code_gold"]) <= fn_tol(x["u"]) + 2 * nb for x in c]
            extra = dict(inl_ep_ppm=g["inl_ep_ppm"], inl=g, b_function=fb, b_vs_golden=fg, inl_gate_ppm=INL_GATE,
                         pass_b=all(fb) and all(fg), pass_c=g["inl_ep_ppm"] <= INL_GATE)
            ok = extra["pass_b"] and extra["pass_c"]
        else:
            ok = False
        verdict(a, ok, res, extra)
    if a.gate == "d":       # chop pair: (A,B) no offset, (C,D) +2 mV bench offset at OTA1's input; B, D swapped
        u0, vo = 0.3, 2e-3
        res, _ = run(a, (u0, u0, u0, u0, u0), tag, swaps=[0, 0, 1, 0, 1], vos=[0, 0, 0, vo, vo])
        c = (res.get("convs") or [])[1:]
        extra, ok = {}, False
        if len(c) == 4:
            A, B, C, Dd = (x["u_hat"] for x in c)
            p0, p1, f0, f1 = (A - B) / 2, (C - Dd) / 2, (A + B) / 2, (C + Dd) / 2
            extra = dict(pair0=p0, pair1=p1, off0=f0, off1=f1, pair_shift_uV=(p1 - p0) * VREF * 1e6, offset_seen_uV=(f1 - f0) * VREF * 1e6,
                         pair0_err=p0 - u0)
            ok = abs(p1 - p0) <= U_OFF5 and abs(f1 - f0) >= 10 * U_OFF5 and abs(p0 - u0) <= fn_tol(u0)
        verdict(a, ok, res, extra)
    if a.gate == "e":       # overload 1.1 VREF and recovery; references before, recoveries after
        us = (0.5, 0.5, 1.1, 0.5, -0.5, -1.1, -0.5)
        res, _ = run(a, us, tag)
        c = (res.get("convs") or [])[1:]
        extra, ok = {}, False
        if len(c) == 6:
            r1, r2 = c[2]["u_hat"] - c[0]["u_hat"], c[5]["u_hat"] - c[3]["u_hat"]
            extra = dict(recov_pos_ppm=r1 / 2 * 1e6, recov_neg_ppm=r2 / 2 * 1e6, over_pos=c[1]["u_hat"], over_neg=c[4]["u_hat"],
                         x_after=[(x["x1n"], x["x2n"]) for x in c])
            ok = abs(r1) <= 2e-6 and abs(r2) <= 2e-6 and c[1]["u_hat"] >= 0.95 and c[4]["u_hat"] <= -0.95
        verdict(a, ok, res, extra)


if __name__ == "__main__":
    main()
