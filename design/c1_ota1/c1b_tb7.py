#!/usr/bin/env python3
"""C1b tb7 (WO-41, WO-43): OTA1 noise. `.noise` on the NETLISTED OTA1 (netlist.py, cmfb="dc"), 9 PVT x 2 modes. Sandbox only:
    python c1b_tb7.py OUTDIR CORNER_IDX [--sink k=v,..] [--fast]   # one corner (index into revc_check.CORNERS9)
    python c1b_tb7.py OUTDIR mut [--sink k=v,..]                    # broken copies, own decks
    python c1b_tb7.py --summary OUTDIR                              # gates, chopper-residue hand bound, tier-0 feed
--sink: sizes_draft.sink_variant() keywords for the WO-43 sweep (L, WF, RS, bnd_wf), e.g. --sink L=8,bnd_wf=0.95.
--fast: no lump copy (sweep only; the summary then skips the lump op row).

One ngspice run per copy (one .noise each, so the plots are noise1 / noise2). Copies per mode (b = base 2 MHz, f = boost 4 MHz):
  ol    open loop, the c1b_opac servo input (DC servo, frozen at AC): inoise = en(f), differential, at the OTA input.
        Runs FIRST: its op (every node) is the .nodeset of the int / lump copies of the same mode (WO-43, D71: the int copy
        fell back to "transient op" at most corners in WO-41).
  gam   gamma deck (WO-43, D71): one device of each class (m_in pfet_01v8, m_n nfet_g5v0d10v5, m_pl pfet_g5v0d10v5) at the
        same geometry and at the vgs / vds of the ol op, source = bulk = 0, drain held by a voltage source; drain-current
        noise at 100 MHz (white, above the flicker corners) -> gamma = S_id / (4 k T gm). These PDK gammas feed the M8 hand rows.
  int   integration-phase network (the gate): per side Cs1 0.5 pF from the vg node to a driven bottom plate, Cint1 4 pF
        vg -> opposite output, C_ROUTE on vg, output routing C_RT. The CMFB is the DC equivalent of netlist.py (Cc real, Cr
        averaged; in OTA1's integrate phase Cr is in its refresh phase, so it does not load the outputs). Chopper parked
        (chp, chlp high), island shunt open, rstb high. Device caps (Cgg of the pair, switch junctions) come from the netlist.
        DC bias of the vg nodes: 1 MH inductors (noiseless) from the c1b_opac DC servo (V_ICM -+ servo/2), so the DC op is the
        open-loop one; L-C corner ~75 Hz, loop check at 10 kHz. Servo resistor rdcs is excluded from every total.
  lump  int + extra output cap so that the effective load is the SPEC 1.4 pF lump (info).
Quantities:
  thermal_vg = beta1 x (output rms of every non-flicker generator, 1 kHz .. 10 GHz). beta1 = Cint/(Cint + Cs1 + Cp_vg) from
  the op (same Cp_vg formula as c1b_opac). Input referral of the sampled OTA noise is ~1.
  en_white, fc: weighted LSQ fit en^2 = a + b/f over 1 kHz .. 2 MHz, en_white = sqrt(a), fc = b/a.
Rows (limits from SPEC rows 92-93, DESIGN.md 2.7 and section 4 row 7, D71; not from this code):
  thermal_vg <= 250 uV rms diff (SPEC gate) and <= 200 uV (D71 design target, >= 20 % margin) at every corner and mode;
  fc <= 631 kHz (info); M8 expected-value checks +-30 % with the PDK gammas: en_white vs 8kT G/gm_in, thermal_vg vs
  2kT G beta/C_eff, G = gamma_in + (gamma_n gm_n + gamma_p (gm_pl + gm_plc))/gm_in,
  C_eff = C_out_ext + Cc + Cint (1 - beta) + Cdd(m_nc) + Cdd(m_pc);
  loop closed: |H(10 kHz)| within 5 % of Cs1/Cint1; op: no lint (no transient-op fallback), |Vod| <= 50 mV,
  |V_outcm - V_OCM| <= 38 mV; generator sum = total (2 %).
  Tier-0 (D71): the DIRECT path (sampled v_vg into ktc_excess) is the gate: OTA1 thermal share <= 1.2 uV and joint <= 2.5 uV
  at 15 SPS; the conventional noise-gain path is info. Info columns: m_n Vds - Vdsat, V_fa, span (c1b_opac formula).
Broken copies: mrg (tt/27 base) = 65 kOhm series resistor at each OTA input (DESIGN.md 4 row 7) -> thermal row and the M8
rows must REJECT; msink (fs/125 base, the worst nominal corner) = sink family W x 4 (same currents, gm_n ~x2, sink noise
PSD ~x2, D71) -> the thermal rows (250 / 200 uV) must REJECT.
"""
import json, math, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import sizes_draft as S  # noqa: E402
import netlist as NL  # noqa: E402
from revc_check import CORNERS9, LIB  # noqa: E402

KB = 1.380649e-23
FS = {False: 2e6, True: 4e6}
CINT1, CS1 = 4.0e-12, 0.5e-12
C_ROUTE, C_RT = 0.035e-12, 0.02e-12     # vg and output routing per side (c1b_opac)
BETA_DES = 0.846
LUMP = 1.4e-12
TH_MAX, TH_TGT, FC_MAX, M8_TOL, GAMMA = 250e-6, 200e-6, 631e3, 0.30, 2.0 / 3.0
R_MUT = 65e3
F_GAM = 1e8
DEVS = {"min1": "m_in", "mn1": "m_n", "mpl1": "m_pl", "mplc1": "m_plc", "mnc1": "m_nc", "mpc1": "m_pc"}
DQ = ("gm", "id", "cgg", "cdd", "vgs", "vds", "vdsat")
GAMDEV = {"min1": "m_in", "mn1": "m_n", "mpl1": "m_pl"}
SWQ = ("sci1", "sci3", "sisl1")
TOPN = ("outp", "outn", "gip", "gin", "vgp", "vgn", "s", "ibtp", "ibn", "ibp", "ivbnc", "ivbpc", "ivbl0")
MUTS = {"mrg": 0, "msink": 3}    # broken copy -> CORNERS9 index (tt/27, fs/125)
GROUPS = [("input pair", ("min",)), ("prot. cascode", ("mpp",)), ("tail", ("mt",)), ("sinks m_n", ("mn", "rmn")),
          ("NMOS cascodes", ("mnc",)), ("PMOS cascodes", ("mpc",)), ("loads m_pl/m_plc", ("mpl", "mplc")),
          ("CMFB integrator/clamps", ("mia", "mil", "mit", "mrst", "mrsb", "mrso", "mrin", "mrip")),
          ("switches (chopper/island)", ("sci", "scf", "sisl")), ("series R (broken)", ("rmg",))]
SINK = {}


def par(x, inst, dev, q):
    return f"@m.x{x}.x{inst}.msky130_fd_pr__{dev}[{q}]"


def sizes_for(mut):
    z = S.sink_variant(S.SIZES, **SINK)
    if mut == "msink":
        z = S.sink_variant(z, wmult=4)
    return z


def deck(c, t, v, x, b, kind, mut, nodesets=None):
    sub = f"ota1_{x}"
    z = sizes_for(mut)
    L = [f"* WO-43 c1b_tb7 {x} {kind}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-12 reltol=1e-6 itl1=500",
         f"Vicm vicm 0 {S.V_ICM}", f"Vicm2 icm 0 {S.V_ICM}", f"Vocm vocm 0 {S.V_OCM}", "Vlv lv 0 1.8", "Vd d 0 dc 0 ac 1",
         f"Vdd vdd 0 {v}",
         NL.build(sub, cmfb="dc", fs=FS[b], sizes=z, boost=b),
         f"X{x} vdd 0 gip gin outp outn vicm vocm ibtp ibn ibp ivbnc ivbpc ivbl0 vdd 0 lv 0 0 0 vdd 0 vdd vdd {sub}"]
    for p_, i_ in NL.bias_currents(b).items():
        L.append(f"I{p_} {p_} 0 {i_:.6e}" if p_ in NL.SINK_PORTS else f"I{p_} vdd {p_} {i_:.6e}")
    if mut == "mrg":
        L += [f"Rmgp vgp gip {R_MUT:g}", f"Rmgn vgn gin {R_MUT:g}"]
    vp, vn = ("vgp", "vgn") if mut == "mrg" else ("gip", "gin")
    integ_eff = CINT1 * (1.0 - BETA_DES) + S.C_CMFB_SENSE + C_RT
    if kind in ("int", "lump"):
        cext = C_RT + (max(0.0, LUMP - integ_eff) if kind == "lump" else 0.0)
        L += [f"Csp {vp} bpp {CS1:g}", f"Csn {vn} bpn {CS1:g}",
              "Bbpp bpp 0 V = V(icm) + 0.5*V(d)", "Bbpn bpn 0 V = V(icm) - 0.5*V(d)",
              f"Cip {vp} outn {CINT1:g}", f"Cin {vn} outp {CINT1:g}", f"Cpp {vp} 0 {C_ROUTE:g}", f"Cpn {vn} 0 {C_ROUTE:g}",
              f"Bdp dp 0 V = V(icm) - 0.5*max(min(V(s)/1000, 0.3), -0.3)", f"Bdn dn 0 V = V(icm) + 0.5*max(min(V(s)/1000, 0.3), -0.3)",
              f"Ldcp dp {vp} 1e6", f"Ldcn dn {vn} 1e6", "Bs 0 s I = 1e-3*(V(outp) - V(outn))", "Rdcs s 0 1e12", "Csrv s 0 1e9",
              f"Cop outp 0 {cext:g}", f"Con outn 0 {cext:g}"]
        if nodesets:   # WO-43: the open-loop op of the same mode (D71)
            L += [".nodeset " + " ".join(f"v({k})={z_:.6g}" for k, z_ in nodesets.items())]
        else:
            L += [f".nodeset v(s)=0 v({vp})={S.V_ICM} v({vn})={S.V_ICM} v(outp)={S.V_OCM} v(outn)={S.V_OCM}"]
    else:   # ol: c1b_opac servo input
        cext = integ_eff - S.C_CMFB_SENSE
        L += [f"Bip {vp} 0 V = V(icm) + 0.5*(V(d) - max(min(V(s)/1000, 0.3), -0.3))",
              f"Bin {vn} 0 V = V(icm) - 0.5*(V(d) - max(min(V(s)/1000, 0.3), -0.3))",
              "Bs 0 s I = 1e-3*(V(outp) - V(outn))", "Rdcs s 0 1e12", "Csrv s 0 1e9",
              f"Cop outp 0 {cext:g}", f"Con outn 0 {cext:g}",
              f".nodeset v(s)=0 v(outp)={S.V_OCM} v(outn)={S.V_OCM}"]
    L += [".control", "set wr_singlescale", "set wr_vecnames", "op",
          "print i(vdd) v(outp) v(outn) v(gip) v(gin)"]
    if kind == "ol":
        L += ["print all"]
    L += [f"print {par(x, i, z[k]['dev'], q)}" for i, k in DEVS.items() for q in DQ]
    L += [f"print {par(x, i, 'nfet_g5v0d10v5', q)}" for i in SWQ for q in ("cgg", "cdd", "vth")]
    L += [f"print v(x{x}.{n})" for n in ("fa", "xa", "sa")]
    fmax = "1e10" if kind != "ol" else "1e9"
    L += [f"noise v(outp,outn) vd dec 20 1e3 {fmax} 1", "print all", "setplot noise1",
          f"wrdata {x}_{kind}_n1.csv onoise_spectrum inoise_spectrum", "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def parse(stdout):
    vals = {}
    for ln in stdout.splitlines():
        if " = " in ln:
            k, _, z = ln.partition(" = ")
            try:
                vals[k.strip().lower()] = float(z.split()[0])
            except (ValueError, IndexError):
                pass
    return vals


LINT = r"(error|unknown|singular|no convergence|timestep too small|could not find|transient op)"


def run(out, c, t, v, x, b, kind, mut, nodesets=None):
    tag = f"{x}_{kind}"
    fn = os.path.join(out, tag + ".sp")
    open(fn, "w").write(deck(c, t, v, x, b, kind, mut, nodesets))
    r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=1500)
    vals = parse(r.stdout)
    lint = [l.strip() for l in (r.stdout + r.stderr).splitlines() if re.search(LINT, l, re.I)]
    csv = os.path.join(out, tag + "_n1.csv")
    spec = None
    if os.path.exists(csv):
        try:
            spec = np.loadtxt(csv, skiprows=1)
        finally:
            os.remove(csv)
    nodes = None
    if kind == "ol":   # every node of the op (top level + this copy's subckt), for the int / lump nodesets
        nodes = {}
        for k, z_ in vals.items():
            n = k[2:-1] if k.startswith("v(") and k.endswith(")") else k
            if "#" in n or "[" in n or n.startswith("@"):
                continue
            if n.startswith(f"x{x}.") or n in TOPN:
                nodes[n] = z_
    res = analyse(vals, lint, spec, x, b, kind, mut)
    return res, nodes, vals


def gamma(out, c, t, v, b, mut, ol_vals, x_ol):
    """PDK gamma per device class at the ol op (WO-43, D71)."""
    z = sizes_for(mut)
    T = 273.15 + t
    gam = {}
    for i, (inst, key) in enumerate(GAMDEV.items()):   # one deck per device (one .noise per run, plots noise1 / noise2)
        p = z[key]
        g_ = lambda q: ol_vals.get(par(x_ol, inst, p["dev"], q).lower(), float("nan"))
        sg = -1.0 if p["dev"].startswith("pfet") else 1.0   # BSIM prints |vgs|, |vds| for PMOS; source = bulk = 0 here
        vgs, vds = sg * abs(g_("vgs")), sg * abs(g_("vds"))
        fn = os.path.join(out, f"{'f' if b else 'b'}{mut or ''}_gam{i}.sp")
        L = ["* WO-43 c1b_tb7 gamma deck", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-12 reltol=1e-6",
             f"Vg g 0 dc {vgs:.6g} ac 1", f"Vd d 0 dc {vds:.6g}", "H1 o 0 Vd 1",
             NL.mos("g", "d", "g", "0", "0", p["dev"], p["WF"], p["L"], p["M"]),
             ".control", "op", f"print @m.xg.msky130_fd_pr__{p['dev']}[gm]", f"print @m.xg.msky130_fd_pr__{p['dev']}[id]",
             f"noise v(o) vg lin 1 {F_GAM:g} {F_GAM:g}", "setplot noise1", "print onoise_spectrum", "quit", ".endc", ".end"]
        open(fn, "w").write("\n".join(L) + "\n")
        r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=600)
        vals = parse(r.stdout)
        gm = vals.get(f"@m.xg.msky130_fd_pr__{p['dev']}[gm]", float("nan"))
        sp = vals.get("onoise_spectrum", float("nan"))
        gam[inst] = sp ** 2 / (4 * KB * T * gm) if gm == gm and gm > 0 else float("nan")
        gam[inst + "_id_uA"] = abs(vals.get(f"@m.xg.msky130_fd_pr__{p['dev']}[id]", float("nan"))) * 1e6
    return gam


def leaves(vals):
    g = {k[len("onoise_total_"):]: z for k, z in vals.items() if k.startswith(("onoise_total_", "onoise_total."))}
    par_ = {p for p in g for q in g if q != p and q.startswith((p + "_", p + "."))}
    return {k: z for k, z in g.items() if k not in par_}


def group_of(name):
    parts = name.split(".")
    inst = parts[2][1:] if len(parts) >= 3 else re.split(r"[._]", name)[0]
    if len(parts) >= 2 and parts[-1].startswith("rmn"):   # WO-43 degeneration resistors of the sinks
        return "sinks m_n"
    base = re.sub(r"\d+$", "", inst)
    for gname, pre in GROUPS:   # exact device-name match first (mn vs mnc), then prefixes for the multi-name groups
        if base in pre:
            return gname
    for gname, pre in GROUPS[7:]:
        if any(base.startswith(p) for p in pre):
            return gname
    return "bias/other"


GAM = {}
TEMP = {"t": 27}


def gfac(d):
    """G = gamma_in + (gamma_n gm_n + gamma_p (gm_pl + gm_plc)) / gm_in, PDK gammas (falls back to 2/3)."""
    gi, gn, gp = (GAM.get(k, GAMMA) if GAM.get(k, GAMMA) == GAM.get(k, GAMMA) else GAMMA for k in ("min1", "mn1", "mpl1"))
    return gi + (gn * d["mn1"]["gm"] + gp * (d["mpl1"]["gm"] + d["mplc1"]["gm"])) / d["min1"]["gm"]


def analyse(vals, lint, spec, x, b, kind, mut):
    g = lambda k: vals.get(k.lower(), float("nan"))
    z = sizes_for(mut)
    res = dict(copy=x, boost=b, kind=kind, mut=mut, lint=lint[:5], sink=dict(SINK))
    d = {i: {q: g(par(x, i, z[k]["dev"], q)) for q in DQ} for i, k in DEVS.items()}
    sw = {i: {q: g(par(x, i, "nfet_g5v0d10v5", q)) for q in ("cgg", "cdd", "vth")} for i in SWQ}
    vod, vcm = g("v(outp)") - g("v(outn)"), 0.5 * (g("v(outp)") + g("v(outn)"))
    cpvg = d["min1"]["cgg"] + 0.5 * sw["sci1"]["cgg"] + abs(sw["sci3"]["cdd"]) + abs(sw["sisl1"]["cdd"]) + C_ROUTE
    beta = CINT1 / (CINT1 + CS1 + cpvg)
    alpha = (d["mn1"]["gm"] + d["mpl1"]["gm"] + d["mplc1"]["gm"]) / d["min1"]["gm"]
    T = 273.15 + TEMP["t"]
    G = gfac(d)
    vx = lambda n: g(f"v(x{x}.{n})")
    bottom = vx("xa") + abs(d["mnc1"]["vdsat"]) + 0.05
    top = vx("sa") - abs(d["mpc1"]["vdsat"]) - 0.05
    res.update(vod_mV=vod * 1e3, vocm_err_mV=(vcm - S.V_OCM) * 1e3, beta1=beta, Cp_vg_fF=cpvg * 1e15, alpha=alpha,
               gm_in_uS=d["min1"]["gm"] * 1e6, gm_n_uS=d["mn1"]["gm"] * 1e6, G=G, gam=dict(GAM),
               idd_uA=-g("i(vdd)") * 1e6, sw=sw, mn_margin=d["mn1"]["vds"] - abs(d["mn1"]["vdsat"]),
               mn_vdsat=abs(d["mn1"]["vdsat"]), V_fa=vx("fa"), span=top - bottom)
    res["en_hand_nV"] = math.sqrt(8 * KB * T * G / d["min1"]["gm"]) * 1e9
    lv = leaves(vals)
    tot = g("onoise_total")
    ssum = math.sqrt(sum(z_ * z_ for z_ in lv.values() if math.isfinite(z_)))
    res["gen_sum_ok"] = bool(lv) and abs(ssum - tot) <= 0.02 * tot
    res["nan_gens"] = [k for k, z_ in lv.items() if not math.isfinite(z_)][:5]
    lv = {k: z_ for k, z_ in lv.items() if math.isfinite(z_)}
    use = {k: z_ for k, z_ in lv.items() if "rdc" not in k}
    fl = {k: z_ for k, z_ in use.items() if k.endswith("1overf") or "flicker" in k}
    th = {k: z_ for k, z_ in use.items() if k not in fl}
    ok = np.isfinite(tot) and not lint and spec is not None and np.all(np.isfinite(spec))
    if kind in ("int", "lump"):
        th_out = math.sqrt(sum(z_ * z_ for z_ in th.values()))
        fl_out = math.sqrt(sum(z_ * z_ for z_ in fl.values()))
        res.update(thermal_vg_uV=beta * th_out * 1e6, flicker_vg_uV=beta * fl_out * 1e6, out_total_uV=tot * 1e6)
        grp = {}
        for k, z_ in th.items():
            grp[group_of(k)] = grp.get(group_of(k), 0.0) + z_ * z_
        res["contrib_pct"] = {k: 100 * z_ / max(th_out ** 2, 1e-30) for k, z_ in sorted(grp.items(), key=lambda a: -a[1])}
        cext = C_RT + (max(0.0, LUMP - (CINT1 * (1 - BETA_DES) + S.C_CMFB_SENSE + C_RT)) if kind == "lump" else 0.0)
        ceff = cext + S.C_CMFB_SENSE + CINT1 * (1 - beta) + abs(d["mnc1"]["cdd"]) + abs(d["mpc1"]["cdd"])
        res["Ceff_fF"] = ceff * 1e15
        res["thermal_hand_uV"] = math.sqrt(2 * KB * T * G * beta / ceff) * 1e6
        if spec is not None and spec.ndim == 2:
            f, on, inn = spec[:, 0], spec[:, 1], spec[:, 2]
            h1k = float(np.interp(4.0, np.log10(f), on / inn))
            res["H1k"] = h1k
            res["loop_ok"] = abs(h1k / (CS1 / CINT1) - 1) <= 0.05
        res["thermal_ok"] = bool(ok) and res["thermal_vg_uV"] <= TH_MAX * 1e6
        res["thermal_tgt_ok"] = bool(ok) and res["thermal_vg_uV"] <= TH_TGT * 1e6
        res["m8_ok"] = abs(res["thermal_vg_uV"] / res["thermal_hand_uV"] - 1) <= M8_TOL
    else:
        if spec is not None and spec.ndim == 2:
            f, en = spec[:, 0], spec[:, 2]
            m = (f >= 1e3) & (f <= 2e6)
            A = np.vstack([np.ones(m.sum()), 1.0 / f[m]]).T / (en[m] ** 2)[:, None]
            a, bb = np.linalg.lstsq(A, np.ones(m.sum()), rcond=None)[0]
            res.update(en_white_nV=math.sqrt(a) * 1e9, fc_kHz=bb / a / 1e3,
                       en_1k_nV=float(np.interp(3, np.log10(f), en)) * 1e9,
                       en_100k_nV=float(np.interp(5, np.log10(f), en)) * 1e9,
                       en_1M_nV=float(np.interp(6, np.log10(f), en)) * 1e9,
                       en_10M_nV=float(np.interp(7, np.log10(f), en)) * 1e9)
            res["fc_ok"] = res["fc_kHz"] * 1e3 <= FC_MAX
            res["m8_ok"] = abs(res["en_white_nV"] / res["en_hand_nV"] - 1) <= M8_TOL
    res["op_ok"] = bool(ok) and abs(res["vod_mV"]) <= 50 and abs(res["vocm_err_mV"]) <= 38 and (res["gen_sum_ok"] or kind == "ol")
    return res


def mode_jobs(sub, c, t, v, pre, b, mut, fast):
    """ol first (op -> nodesets, gammas), then int (and lump)."""
    x_ol = f"{pre}ol"
    rows = []
    r, nodes, ovals = run(sub, c, t, v, x_ol, b, "ol", mut)
    GAM.clear()
    GAM.update(gamma(sub, c, t, v, b, mut, ovals, x_ol))
    # the ol hand row is recomputed below with the PDK gammas (the ol run was analysed before the gamma deck)
    rows.append(r)
    for kind in (("int",) if fast else ("int", "lump")):
        x = f"{pre}{kind}"
        ns = {(f"x{x}." + k[len(f"x{x_ol}."):] if k.startswith(f"x{x_ol}.") else k): z_ for k, z_ in (nodes or {}).items()}
        ri, _, _ = run(sub, c, t, v, x, b, kind, mut, ns)
        rows.append(ri)
    # ol hand row with the gammas: en_hand = sqrt(8kT G / gm_in), G from the int copy's op (same op by construction)
    ri = rows[1]
    rows[0]["G"] = ri["G"]
    rows[0]["en_hand_nV"] = math.sqrt(8 * KB * (273.15 + t) * ri["G"] / (ri["gm_in_uS"] * 1e-6)) * 1e9
    if "en_white_nV" in rows[0]:
        rows[0]["m8_ok"] = abs(rows[0]["en_white_nV"] / rows[0]["en_hand_nV"] - 1) <= M8_TOL
    for r_ in rows:
        r_["gam"] = dict(GAM)
    return rows


def corner_job(out, ci, fast):
    rows = []
    if ci == "mut":
        for m, idx in MUTS.items():
            c, t, v = CORNERS9[idx]
            TEMP["t"] = t
            sub = os.path.join(out, f"{c}_{t}_{v}".replace("-", "m").replace(".", "p") + "_mut")
            os.makedirs(sub, exist_ok=True)
            for r in mode_jobs(sub, c, t, v, m, False, m, True):
                r.update(corner=f"{c}/{t}/{v}")
                rows.append(r)
                print(json.dumps(r, default=float), flush=True)
        tag = "mut"
    else:
        c, t, v = CORNERS9[ci]
        TEMP["t"] = t
        tag = f"{c}_{t}_{v}".replace("-", "m").replace(".", "p")
        sub = os.path.join(out, tag)
        os.makedirs(sub, exist_ok=True)
        for b in (False, True):
            for r in mode_jobs(sub, c, t, v, "f" if b else "b", b, None, fast):
                r.update(corner=f"{c}/{t}/{v}")
                rows.append(r)
                print(json.dumps(r, default=float), flush=True)
    json.dump(rows, open(os.path.join(out, f"tb7_{tag}.json"), "w"), indent=1, default=float)


# ----------------------------------------------------------------------------- summary: chopper hand bound + tier-0 feed
def chopper_rows(r, a0_db, delta=None):
    """Hand bound from the op of the parked chopper (the closed input switch sci1 at vg CM). Conservative: one-edge channel
    charge, no on/off cancellation. Constant: dQ = 0.5 Q_ch x delta (3 sigma pair mismatch); signal-dependent: the vg
    excursion (x1 peak 1.21 V diff / A0) changes each switch's channel charge by Cgg_on dV/2, half of it into vg."""
    sw = r["sw"]["sci1"]
    w, l = S.CHOP_SW["input"]["W"], S.CHOP_SW["input"]["L"]
    vov = 3.3 - S.V_ICM - sw["vth"]
    q = sw["cgg"] * vov
    if delta is None:
        delta = 3 * math.hypot(S.A_VT_HV * math.sqrt(2 / (w * l)) / vov, S.A_B_HV * math.sqrt(2 / (w * l)))
    res_c = 0.5 * q * delta / CS1
    dv = 1.21 / 10 ** (a0_db / 20)
    res_s = 0.5 * sw["cgg"] * dv / 2 / CS1
    return dict(Qch_fC=q * 1e15, vov=vov, delta=delta, const_mV=res_c * 1e3, sig_uV=res_s * 1e6,
                const_ok=res_c <= 1e-3, sig_ok=res_s <= 1e-6)


def model_rows(en_nV, fc, vvg):
    from model.studies import s3_budget as B
    nb = B.noise_uv(B.ideal_base(), 15, B.N_PREC)
    n_conv = B.noise_uv(B.ideal_base(ktc_excess=B.excess_from_en(en_nV)), 15, B.N_PREC)
    exc_d = 1.0 + vvg ** 2 / (2 * 2 * KB * 300 / CS1)
    n_dir = B.noise_uv(B.ideal_base(ktc_excess=exc_d, white_ng_ref=0.0), 15, B.N_PREC)
    fl = {lf: B.noise_uv(B.ideal_base(ktc_on=False, flicker_on=True, ota_white=en_nV * 1e-9, ota_fc=fc, lf_gain=lf,
                                      vres=5e-6), 15, B.N_PREC) for lf in (1.0, B.LF)}
    joint = B.noise_uv(B.m.with_(B.spec_point(ota_en=en_nV, fc=fc), ota_white=en_nV * 1e-9), 15, B.N_PREC)
    joint_d = B.noise_uv(B.m.with_(B.spec_point(fc=fc), ota_white=en_nV * 1e-9, ktc_excess=exc_d, white_ng_ref=0.0), 15,
                         B.N_PREC)
    th_c, th_d = B.contrib_noise(n_conv, nb), B.contrib_noise(n_dir, nb)
    return dict(ktc_uV=nb, th_conv_uV=th_c, th_direct_uV=th_d, exc_direct=exc_d, fl_lf1_uV=fl[1.0], fl_lf93_uV=fl[B.LF],
                joint_conv_uV=joint, joint_direct_uV=joint_d,
                th_conv_ok=th_c <= 1.2, th_direct_ok=th_d <= 1.2, fl_ok=fl[B.LF] <= 1.0, joint_ok=joint <= 2.5,
                joint_direct_ok=joint_d <= 2.5)


def summary(out):
    rows = []
    for fn in sorted(os.listdir(out)):
        if fn.startswith("tb7_") and fn.endswith(".json") and fn != "tb7_summary.json":
            rows += json.load(open(os.path.join(out, fn)))
    nom = [r for r in rows if not r["mut"]]
    mut = [r for r in rows if r["mut"]]
    fails = []
    print("corner | mode | thermal_vg uV (hand) | lump uV | flick_vg uV | en_w nV (hand) | fc kHz | beta | gam in/n/p | "
          "m_n margin V, V_fa, span | ok")
    feed = {}
    for cn in dict.fromkeys(r["corner"] for r in nom):
        for b in (False, True):
            m = "f" if b else "b"
            pick = lambda k: next((r for r in nom if r["corner"] == cn and r["copy"] == m + k), None)
            ri, rl, ro = pick("int"), pick("lump"), pick("ol")
            okr = ri["thermal_ok"] and ri["thermal_tgt_ok"] and ri["op_ok"] and ri.get("loop_ok") and ri["m8_ok"] \
                and ro["op_ok"] and ro["m8_ok"] and (rl is None or rl["op_ok"])
            if not okr:
                fails.append(f"{cn} {m}")
            gm_ = ri.get("gam", {})
            print(f"{cn} | {m} | {ri['thermal_vg_uV']:.1f} ({ri['thermal_hand_uV']:.1f}) | "
                  f"{(rl['thermal_vg_uV'] if rl else float('nan')):.1f} | {ri['flicker_vg_uV']:.1f} | "
                  f"{ro['en_white_nV']:.2f} ({ro['en_hand_nV']:.2f}) | {ro['fc_kHz']:.1f} | {ri['beta1']:.4f} | "
                  f"{gm_.get('min1', float('nan')):.2f}/{gm_.get('mn1', float('nan')):.2f}/{gm_.get('mpl1', float('nan')):.2f} | "
                  f"{ri['mn_margin']:.3f}, {ri['V_fa']:.3f}, {ri['span']:.3f} | {'ACCEPT' if okr else 'REJECT'} "
                  f"op{ri['op_ok']}/{ro['op_ok']}{'' if rl is None else '/' + str(rl['op_ok'])} loop{ri.get('loop_ok')} "
                  f"m8 {ri['m8_ok']}/{ro['m8_ok']} lint {ri['lint'][:1]}")
            if not b:
                feed[cn] = (ro["en_white_nV"], ro["fc_kHz"] * 1e3, ri["thermal_vg_uV"] * 1e-6)
    r0 = next((r for r in nom if r["copy"] == "bint" and r["corner"].startswith("tt/27")), None) or \
        next(r for r in nom if r["copy"] == "bint")
    print(f"contributors {r0['corner']} base (thermal power %):", json.dumps({k: round(z, 1) for k, z in r0["contrib_pct"].items()}))
    wst = max((r for r in nom if r["kind"] == "int"), key=lambda r: r["thermal_vg_uV"])
    print(f"worst thermal: {wst['corner']} {wst['copy']} {wst['thermal_vg_uV']:.1f} uV; contributors",
          json.dumps({k: round(z, 1) for k, z in wst["contrib_pct"].items()}))
    ch = chopper_rows(r0, 80.3)
    chb = dict(const=chopper_rows(r0, 80.3, delta=1.0), sig=chopper_rows(r0, 41.3))
    print("chopper hand bound:", json.dumps({k: (round(z, 4) if isinstance(z, float) else z) for k, z in ch.items()}))
    print(f"chopper broken: one-sided (delta 1) const {chb['const']['const_mV']:.3f} mV ok={chb['const']['const_ok']}; "
          f"A0 41.3 dB sig {chb['sig']['sig_uV']:.3f} uV ok={chb['sig']['sig_ok']}")
    if not (ch["const_ok"] and ch["sig_ok"]):
        fails.append("chopper")
    if chb["const"]["const_ok"] or chb["sig"]["sig_ok"]:
        fails.append("chopper broken copy not rejected")
    # tier-0 feed: base mode (precision 15 SPS), every corner. D71: direct path = gate, conventional = info
    mod = {}
    for cn, (en, fc, vvg) in feed.items():
        mod[cn] = model_rows(en, fc, vvg)
        okm = mod[cn]["th_direct_ok"] and mod[cn]["joint_direct_ok"] and mod[cn]["fl_ok"]
        if not okm:
            fails.append(f"tier-0 direct {cn}")
        print("model", cn, "ACCEPT" if okm else "REJECT",
              json.dumps({k: (round(z, 3) if isinstance(z, float) else z) for k, z in mod[cn].items()}))
    # broken copies
    mr = {r["copy"]: r for r in mut}
    if mr:
        rg, rs = mr["mrgint"], mr["msinkint"]
        rg_rej = rg["op_ok"] and not rg["thermal_ok"] and not rg["m8_ok"]
        rs_rej = rs["op_ok"] and not (rs["thermal_ok"] and rs["thermal_tgt_ok"])
        nomw = next((r for r in nom if r["copy"] == "bint" and r["corner"] == rs["corner"]), None)
        print(f"broken mrg: thermal {rg['thermal_vg_uV']:.1f} uV (hand {rg['thermal_hand_uV']:.1f}) en "
              f"{mr['mrgol'].get('en_white_nV', float('nan')):.2f} nV -> {'REJECTED' if rg_rej else 'NOT REJECTED'}")
        print(f"broken msink ({rs['corner']} base, sink W x4, gm_n {rs['gm_n_uS']:.1f} uS vs nominal "
              f"{(nomw['gm_n_uS'] if nomw else float('nan')):.1f}): thermal {rs['thermal_vg_uV']:.1f} uV vs nominal "
              f"{(nomw['thermal_vg_uV'] if nomw else float('nan')):.1f}, sink share {rs['contrib_pct'].get('sinks m_n', 0):.1f} % "
              f"-> {'REJECTED' if rs_rej else 'NOT REJECTED'} (op {rs['op_ok']})")
        if not rg_rej:
            fails.append("mrg not rejected")
        if not rs_rej:
            fails.append("msink not rejected")
    else:
        print("broken copies: not run (sweep)")
    json.dump(dict(rows=rows, chopper=ch, chopper_broken=chb, model=mod, fails=fails),
              open(os.path.join(out, "tb7_summary.json"), "w"), indent=1, default=float)
    print("VERDICT", "ACCEPT" if not fails else "REJECT " + "; ".join(fails))
    return fails


if __name__ == "__main__":
    if sys.argv[1] == "--summary":
        sys.exit(1 if summary(sys.argv[2]) else 0)
    if "--sink" in sys.argv:
        for kv in sys.argv[sys.argv.index("--sink") + 1].split(","):
            k, _, z_ = kv.partition("=")
            SINK[k] = float(z_)
    os.makedirs(sys.argv[1], exist_ok=True)
    corner_job(sys.argv[1], sys.argv[2] if sys.argv[2] == "mut" else int(sys.argv[2]), "--fast" in sys.argv)
