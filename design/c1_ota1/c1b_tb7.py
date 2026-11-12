#!/usr/bin/env python3
"""C1b tb7 (WO-41): OTA1 noise. `.noise` on the NETLISTED OTA1 (netlist.py, cmfb="dc"), 9 PVT x 2 modes. Sandbox only:
    python c1b_tb7.py OUTDIR CORNER_IDX      # one corner (index into revc_check.CORNERS9): base + boost copies
    python c1b_tb7.py OUTDIR mut             # broken copies at tt/27 base, own decks
    python c1b_tb7.py --summary OUTDIR       # gates, chopper-residue hand bound, tier-0 model feed (15 SPS)

One ngspice run per copy (one .noise each, so the plots are noise1 / noise2). Copies per mode (b = base 2 MHz, f = boost 4 MHz):
  int   integration-phase network (the gate): per side Cs1 0.5 pF from the vg node to a driven bottom plate, Cint1 4 pF
        vg -> opposite output, C_ROUTE on vg, output routing C_RT. The CMFB is the DC equivalent of netlist.py (Cc real, Cr
        averaged; in OTA1's integrate phase Cr is in its refresh phase, so it does not load the outputs). Chopper parked
        (chp, chlp high), island shunt open, rstb high. Device caps (Cgg of the pair, switch junctions) come from the netlist.
        DC bias of the vg nodes: 1 MH inductors (noiseless) from the c1b_opac DC servo (V_ICM -+ servo/2), so the DC op is the
        open-loop one (1 TOhm DC resistors left Newton without convergence, WO-41 smoke); L-C corner ~75 Hz, loop check at 10 kHz.
        Servo resistor rdcs is excluded from every total.
  lump  int + extra output cap so that the effective load is the SPEC 1.4 pF lump (info).
  ol    open loop, the c1b_opac servo input (DC servo, frozen at AC): inoise = en(f), differential, at the OTA input.
Quantities:
  thermal_vg = beta1 x (output rms of every non-flicker generator, 1 Hz .. 10 GHz). beta1 = Cint/(Cint + Cs1 + Cp_vg) from
  the op (same Cp_vg formula as c1b_opac). Input referral of the sampled OTA noise is ~1: the charge Cs1 x v_vg left on Cint
  when Cs1 opens gives dx = c1 v_vg, i.e. du = v_vg (Cp_vg stays connected and gives no persistent charge).
  en_white, fc: weighted LSQ fit en^2 = a + b/f over 100 Hz .. 2 MHz, en_white = sqrt(a), fc = b/a (the model's definition:
  PSD_1/f = en_white^2 fc / f).
Rows (limits from SPEC rows 92-93, DESIGN.md 2.7 and section 4 row 7, not from this code):
  thermal_vg <= 250 uV rms diff at every corner and mode (gate); fc <= 631 kHz (info);
  M8 expected-value checks, +-30 %: en_white vs 8kT gamma (1+alpha)/gm_in, thermal_vg vs 2kT gamma (1+alpha) beta/C_eff,
  gamma 2/3, alpha = (gm_n + gm_pl + gm_plc)/gm_in, C_eff = C_out_ext + Cc + Cint (1 - beta) + Cdd(m_nc) + Cdd(m_pc);
  loop closed: |H(10 kHz)| within 5 % of Cs1/Cint1; op: |Vod| <= 50 mV, |V_outcm - V_OCM| <= 38 mV; generator sum = total (2 %).
Broken copies (tt/27 base): mrg = 65 kOhm series resistor at each OTA input (DESIGN.md 4 row 7) -> thermal row and the M8 rows
must REJECT; mhalf = input pair W/2 (M 12 -> 6, WO-41 item 4) -> thermal row or the tier-0 OTA1 thermal share must REJECT.
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
TH_MAX, FC_MAX, M8_TOL, GAMMA = 250e-6, 631e3, 0.30, 2.0 / 3.0
R_MUT = 65e3
DEVS = {"min1": "m_in", "mn1": "m_n", "mpl1": "m_pl", "mplc1": "m_plc", "mnc1": "m_nc", "mpc1": "m_pc"}
SWQ = ("sci1", "sci3", "sisl1")
GROUPS = [("input pair", ("min",)), ("prot. cascode", ("mpp",)), ("tail", ("mt",)), ("sinks m_n", ("mn",)),
          ("NMOS cascodes", ("mnc",)), ("PMOS cascodes", ("mpc",)), ("loads m_pl/m_plc", ("mpl", "mplc")),
          ("CMFB integrator/clamps", ("mia", "mil", "mit", "mrst", "mrsb", "mrso", "mrin", "mrip")),
          ("switches (chopper/island)", ("sci", "scf", "sisl")), ("series R (broken)", ("rmg",))]


def par(x, inst, dev, q):
    return f"@m.x{x}.x{inst}.msky130_fd_pr__{dev}[{q}]"


def sizes_for(mut):
    z = {k: dict(v) for k, v in S.SIZES.items()}
    if mut == "mhalf":
        z["m_in"]["M"] = z["m_in"]["M"] // 2
    return z


def deck(c, t, v, x, b, kind, mut):
    sub = f"ota1_{x}"
    L = [f"* WO-41 c1b_tb7 {x} {kind}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-12 reltol=1e-6 itl1=500",
         f"Vicm vicm 0 {S.V_ICM}", f"Vicm2 icm 0 {S.V_ICM}", f"Vocm vocm 0 {S.V_OCM}", "Vlv lv 0 1.8", "Vd d 0 dc 0 ac 1",
         f"Vdd vdd 0 {v}",
         NL.build(sub, cmfb="dc", fs=FS[b], sizes=sizes_for(mut), boost=b),
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
              f"Cop outp 0 {cext:g}", f"Con outn 0 {cext:g}",
              f".nodeset v(s)=0 v({vp})={S.V_ICM} v({vn})={S.V_ICM} v(outp)={S.V_OCM} v(outn)={S.V_OCM}"]
    else:   # ol: c1b_opac servo input
        cext = integ_eff - S.C_CMFB_SENSE
        L += [f"Bip {vp} 0 V = V(icm) + 0.5*(V(d) - max(min(V(s)/1000, 0.3), -0.3))",
              f"Bin {vn} 0 V = V(icm) - 0.5*(V(d) - max(min(V(s)/1000, 0.3), -0.3))",
              "Bs 0 s I = 1e-3*(V(outp) - V(outn))", "Rdcs s 0 1e12", "Csrv s 0 1e9",
              f"Cop outp 0 {cext:g}", f"Con outn 0 {cext:g}",
              f".nodeset v(s)=0 v(outp)={S.V_OCM} v(outn)={S.V_OCM}"]
    L += [".control", "set wr_singlescale", "set wr_vecnames", "op",
          "print i(vdd) v(outp) v(outn) v(gip) v(gin)"]
    L += [f"print {par(x, i, S.SIZES[k]['dev'], q)}" for i, k in DEVS.items() for q in ("gm", "id", "cgg", "cdd")]
    L += [f"print {par(x, i, 'nfet_g5v0d10v5', q)}" for i in SWQ for q in ("cgg", "cdd", "vth")]
    fmax = "1e10" if kind != "ol" else "1e9"
    L += [f"noise v(outp,outn) vd dec 20 1 {fmax} 1", "print all", "setplot noise1",
          f"wrdata {x}_{kind}_n1.csv onoise_spectrum inoise_spectrum", "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def run(out, c, t, v, x, b, kind, mut):
    tag = f"{x}_{kind}"
    fn = os.path.join(out, tag + ".sp")
    open(fn, "w").write(deck(c, t, v, x, b, kind, mut))
    r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=1500)
    vals = {}
    for ln in r.stdout.splitlines():
        if " = " in ln:
            k, _, z = ln.partition(" = ")
            try:
                vals[k.strip().lower()] = float(z.split()[0])
            except ValueError:
                pass
    lint = [l.strip() for l in (r.stdout + r.stderr).splitlines()
            if re.search(r"(error|unknown|singular|no convergence|timestep too small|could not find|transient op)", l, re.I)]
    csv = os.path.join(out, tag + "_n1.csv")
    spec = None
    if os.path.exists(csv):
        try:
            spec = np.loadtxt(csv, skiprows=1)
        finally:
            os.remove(csv)
    return analyse(vals, lint, spec, x, b, kind, mut)


def leaves(vals):
    g = {k[len("onoise_total_"):]: z for k, z in vals.items() if k.startswith(("onoise_total_", "onoise_total."))}
    par_ = {p for p in g for q in g if q != p and q.startswith((p + "_", p + "."))}
    return {k: z for k, z in g.items() if k not in par_}


def group_of(name):
    parts = name.split(".")
    inst = parts[2][1:] if len(parts) >= 3 else re.split(r"[._]", name)[0]
    base = re.sub(r"\d+$", "", inst)
    for gname, pre in GROUPS:   # exact device-name match first (mn vs mnc), then prefixes for the multi-name groups
        if base in pre:
            return gname
    for gname, pre in GROUPS[7:]:
        if any(base.startswith(p) for p in pre):
            return gname
    return "bias/other"


def analyse(vals, lint, spec, x, b, kind, mut):
    g = lambda k: vals.get(k.lower(), float("nan"))
    res = dict(copy=x, boost=b, kind=kind, mut=mut, lint=lint[:5])
    d = {i: {q: g(par(x, i, S.SIZES[k]["dev"], q)) for q in ("gm", "id", "cgg", "cdd")} for i, k in DEVS.items()}
    sw = {i: {q: g(par(x, i, "nfet_g5v0d10v5", q)) for q in ("cgg", "cdd", "vth")} for i in SWQ}
    vod, vcm = g("v(outp)") - g("v(outn)"), 0.5 * (g("v(outp)") + g("v(outn)"))
    cpvg = d["min1"]["cgg"] + 0.5 * sw["sci1"]["cgg"] + abs(sw["sci3"]["cdd"]) + abs(sw["sisl1"]["cdd"]) + C_ROUTE
    beta = CINT1 / (CINT1 + CS1 + cpvg)
    alpha = (d["mn1"]["gm"] + d["mpl1"]["gm"] + d["mplc1"]["gm"]) / d["min1"]["gm"]
    T = 273.15 + TEMP["t"]
    res.update(vod_mV=vod * 1e3, vocm_err_mV=(vcm - S.V_OCM) * 1e3, beta1=beta, Cp_vg_fF=cpvg * 1e15, alpha=alpha,
               gm_in_uS=d["min1"]["gm"] * 1e6, idd_uA=-g("i(vdd)") * 1e6, sw=sw, dev=d)
    res["en_hand_nV"] = math.sqrt(8 * KB * T * GAMMA * (1 + alpha) / d["min1"]["gm"]) * 1e9
    lv = leaves(vals)
    tot = g("onoise_total")
    ssum = math.sqrt(sum(z * z for z in lv.values()))
    res["gen_sum_ok"] = bool(lv) and abs(ssum - tot) <= 0.02 * tot
    use = {k: z for k, z in lv.items() if "rdc" not in k}
    fl = {k: z for k, z in use.items() if k.endswith("1overf") or "flicker" in k}
    th = {k: z for k, z in use.items() if k not in fl}
    ok = np.isfinite(tot) and not lint and spec is not None and np.all(np.isfinite(spec))
    if kind in ("int", "lump"):
        th_out = math.sqrt(sum(z * z for z in th.values()))
        fl_out = math.sqrt(sum(z * z for z in fl.values()))
        res.update(thermal_vg_uV=beta * th_out * 1e6, flicker_vg_uV=beta * fl_out * 1e6, out_total_uV=tot * 1e6)
        grp = {}
        for k, z in th.items():
            grp[group_of(k)] = grp.get(group_of(k), 0.0) + z * z
        res["contrib_pct"] = {k: 100 * z / max(th_out ** 2, 1e-30) for k, z in sorted(grp.items(), key=lambda a: -a[1])}
        cext = C_RT + (max(0.0, LUMP - (CINT1 * (1 - BETA_DES) + S.C_CMFB_SENSE + C_RT)) if kind == "lump" else 0.0)
        ceff = cext + S.C_CMFB_SENSE + CINT1 * (1 - beta) + abs(d["mnc1"]["cdd"]) + abs(d["mpc1"]["cdd"])
        res["Ceff_fF"] = ceff * 1e15
        res["thermal_hand_uV"] = math.sqrt(2 * KB * T * GAMMA * (1 + alpha) * beta / ceff) * 1e6
        if spec is not None and spec.ndim == 2:
            f, on, inn = spec[:, 0], spec[:, 1], spec[:, 2]
            h1k = float(np.interp(4.0, np.log10(f), on / inn))
            res["H1k"] = h1k
            res["loop_ok"] = abs(h1k / (CS1 / CINT1) - 1) <= 0.05
        res["thermal_ok"] = bool(ok) and res["thermal_vg_uV"] <= TH_MAX * 1e6
        res["m8_ok"] = abs(res["thermal_vg_uV"] / res["thermal_hand_uV"] - 1) <= M8_TOL
    else:
        if spec is not None and spec.ndim == 2:
            f, en = spec[:, 0], spec[:, 2]
            m = (f >= 100) & (f <= 2e6)
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
    res.pop("dev")
    return res


TEMP = {"t": 27}


def corner_job(out, ci):
    c, t, v = CORNERS9[ci] if ci != "mut" else CORNERS9[0]
    TEMP["t"] = t
    tag = f"{c}_{t}_{v}".replace("-", "m").replace(".", "p")
    sub = os.path.join(out, tag + ("_mut" if ci == "mut" else ""))
    os.makedirs(sub, exist_ok=True)
    if ci == "mut":
        jobs = [(f"{m}{k}", False, k, m) for m in ("mrg", "mhalf") for k in ("int", "ol")]
    else:
        jobs = [(f"{'f' if b else 'b'}{k}", b, k, None) for b in (False, True) for k in ("int", "lump", "ol")]
    rows = []
    for x, b, kind, mut in jobs:
        r = run(sub, c, t, v, x, b, kind, mut)
        r.update(corner=f"{c}/{t}/{v}")
        rows.append(r)
        print(json.dumps(r, default=float), flush=True)
    json.dump(rows, open(os.path.join(out, f"tb7_{tag}{'_mut' if ci == 'mut' else ''}.json"), "w"), indent=1, default=float)


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
                th_conv_ok=th_c <= 1.2, th_direct_ok=th_d <= 1.2, fl_ok=fl[B.LF] <= 1.0, joint_ok=joint <= 2.5)


def summary(out):
    rows = []
    for fn in sorted(os.listdir(out)):
        if fn.startswith("tb7_") and fn.endswith(".json"):
            rows += json.load(open(os.path.join(out, fn)))
    nom = [r for r in rows if not r["mut"]]
    mut = [r for r in rows if r["mut"]]
    fails = []
    print("corner | mode | thermal_vg uV (hand) | lump uV | flick_vg uV | en_w nV (hand) | fc kHz | beta | ok")
    feed = {}
    for cn in dict.fromkeys(r["corner"] for r in nom):
        for b in (False, True):
            m = "f" if b else "b"
            ri, rl, ro = (next(r for r in nom if r["corner"] == cn and r["copy"] == m + k) for k in ("int", "lump", "ol"))
            okr = ri["thermal_ok"] and ri["op_ok"] and ri.get("loop_ok") and ri["m8_ok"] and ro["op_ok"] and ro["m8_ok"] \
                and rl["op_ok"]
            if not okr:
                fails.append(f"{cn} {m}")
            print(f"{cn} | {m} | {ri['thermal_vg_uV']:.1f} ({ri['thermal_hand_uV']:.1f}) | {rl['thermal_vg_uV']:.1f} | "
                  f"{ri['flicker_vg_uV']:.1f} | {ro['en_white_nV']:.2f} ({ro['en_hand_nV']:.2f}) | {ro['fc_kHz']:.1f} | "
                  f"{ri['beta1']:.4f} | {'ACCEPT' if okr else 'REJECT'} op{ri['op_ok']}/{ro['op_ok']} loop{ri.get('loop_ok')} "
                  f"m8 {ri['m8_ok']}/{ro['m8_ok']}")
            if not b:
                feed[cn] = (ro["en_white_nV"], ro["fc_kHz"] * 1e3, ri["thermal_vg_uV"] * 1e-6)
    r0 = next(r for r in nom if r["copy"] == "bint" and r["corner"].startswith("tt/27"))
    print("contributors tt base (thermal power %):", json.dumps({k: round(z, 1) for k, z in r0["contrib_pct"].items()}))
    wst = max((r for r in nom if r["kind"] == "int"), key=lambda r: r["thermal_vg_uV"])
    print(f"worst thermal: {wst['corner']} {wst['copy']} {wst['thermal_vg_uV']:.1f} uV; contributors",
          json.dumps({k: round(z, 1) for k, z in wst["contrib_pct"].items()}))
    ch = chopper_rows(r0, 80.3)
    chb = dict(const=chopper_rows(r0, 80.3, delta=1.0), sig=chopper_rows(r0, 41.3))
    print("chopper hand bound (tt base):", json.dumps({k: (round(z, 4) if isinstance(z, float) else z) for k, z in ch.items()}))
    print(f"chopper broken: one-sided (delta 1) const {chb['const']['const_mV']:.3f} mV ok={chb['const']['const_ok']}; "
          f"A0 41.3 dB sig {chb['sig']['sig_uV']:.3f} uV ok={chb['sig']['sig_ok']}")
    if not (ch["const_ok"] and ch["sig_ok"]):
        fails.append("chopper")
    if chb["const"]["const_ok"] or chb["sig"]["sig_ok"]:
        fails.append("chopper broken copy not rejected")
    # tier-0 feed: base mode (precision 15 SPS), every corner
    mod = {}
    for cn, (en, fc, vvg) in feed.items():
        mod[cn] = model_rows(en, fc, vvg)
        print("model", cn, json.dumps({k: (round(z, 3) if isinstance(z, float) else z) for k, z in mod[cn].items()}))
    # broken copies
    mr = {r["copy"]: r for r in mut}
    rg, ri_, ro_ = mr["mrgint"], mr["mhalfint"], mr["mhalfol"]
    rg_rej = rg["op_ok"] and not rg["thermal_ok"] and not rg["m8_ok"]
    mh = model_rows(ro_["en_white_nV"], ro_["fc_kHz"] * 1e3, ri_["thermal_vg_uV"] * 1e-6)
    mh_rej = ri_["op_ok"] and (not ri_["thermal_ok"] or not mh["th_conv_ok"])
    print(f"broken mrg: thermal {rg['thermal_vg_uV']:.1f} uV (hand {rg['thermal_hand_uV']:.1f}) en "
          f"{mr['mrgol'].get('en_white_nV', float('nan')):.2f} nV -> {'REJECTED' if rg_rej else 'NOT REJECTED'}")
    print(f"broken mhalf: thermal {ri_['thermal_vg_uV']:.1f} uV en {ro_['en_white_nV']:.2f} nV fc {ro_['fc_kHz']:.1f} kHz; "
          f"model {json.dumps({k: (round(z, 3) if isinstance(z, float) else z) for k, z in mh.items()})} -> "
          f"{'REJECTED' if mh_rej else 'NOT REJECTED'}")
    if not rg_rej:
        fails.append("mrg not rejected")
    if not mh_rej:
        fails.append("mhalf not rejected")
    json.dump(dict(rows=rows, chopper=ch, chopper_broken=chb, model=mod, model_mhalf=mh, fails=fails),
              open(os.path.join(out, "tb7_summary.json"), "w"), indent=1, default=float)
    print("VERDICT", "ACCEPT" if not fails else "REJECT " + "; ".join(fails))
    return fails


if __name__ == "__main__":
    if sys.argv[1] == "--summary":
        sys.exit(1 if summary(sys.argv[2]) else 0)
    os.makedirs(sys.argv[1], exist_ok=True)
    corner_job(sys.argv[1], sys.argv[2] if sys.argv[2] == "mut" else int(sys.argv[2]))
