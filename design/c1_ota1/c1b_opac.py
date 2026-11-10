#!/usr/bin/env python3
"""C1b tb1/tb2: .op + .ac of the NETLISTED OTA1 (netlist.py, cmfb="dc"), 9 PVT x 2 modes (WO-24 items 2-3). Sandbox only:
    python c1b_opac.py OUTDIR CORNER_IDXS            # CORNER_IDXS = comma list into revc_check.CORNERS9

Per corner one deck: base and boost copies, each at three output loads per side (C_L total, incl. Cc of the CMFB):
  lump 1.4 pF (SPEC 3.0 / tier-1 macro basis, kept as the spec basis), integ and hold per-phase loads DERIVED from the sizes
  (REVIEW-C1b M4, D55: ~0.84 / 0.99 pF; see LOADS below).
  External cap per side = C_L - Cc (Cc is inside the subckt, output -> ctl). Junction caps come from ad/as/pd/ps.
tt/27 adds the broken copy mut_nc (NMOS cascode D-S short, base) in its OWN deck: it counts as rejected only if its op
converged, A0 is finite and A0 < A0_MIN; anything else (lint, NaN, no data) is INVALID and fails the run.
CMFB DC equivalent: netlist.py docstring (R = 1/(fs*2Cr) on ctl, CM only); fs 2 MHz base, 4 MHz boost.
Chopper static (chp, chlp high); island shunt open; rstb high.

WO-25 (D58) rows: the four composite-to-mirror ratios (I_mirror / (fingers x I_port): m_tr -> m_t, m_nr -> m_n, m_plr ->
m_pl, V_BL0 replica -> m_plc via a top-level probe copy of m_plc with gate ivbl0 and drain forced to V(sa)); I_tail
within +-3 % of I_TAIL (x BOOST); effective K_P = (I_bpd / (W/L)_bpd) / (I_pc / (W/L)_pc) within +-10 % of
K_BIAS_P x KP_BANK base / fingers (10 base, 7.14 boost); K_N (I_bnd vs I_nc, target K_BIAS_N) reported.
Broken copies, each in its own deck, each must fail its TARGET row with a converged op: tt nc_short -> precision A0;
tt ref_single -> I_tail; ff/-40 kp_fixed (old wiring) -> K_P.

WO-26 (D59) rows replace the I_tail +-3 % row and the blind K_P row:
  mirror ratios I_mirror / (RATIO x I_port) within +-2 % (RATIO_TOL) at every corner and mode, and their spread over the 9
  corners per mode <= 2 % (--summary); SR = I_tail / 1.4 pF >= 12.5 V/us base, >= 25 V/us boost (SPEC row 95) and
  I_tail <= I_TAIL_CEIL x I_TAIL (x BOOST); K_P tracking: copy "bkp" (ibn x1.05, I_NC ~+8 %) vs "blump", |dK_P/K_P| <= 2 %;
  |V_OCM error| <= 38 mV (SPEC row 98 / CL-2) at every copy. K_P +-10 % of target stays as a row.
  Broken copies (own deck, each must fail its TARGET row with a converged op): tt nc_short -> precision A0; tt
  ref_composite -> ratio; tt kp_fixed+ibn105 vs kp_fixed (helper) -> K_P tracking; tt boost ibtp90 -> SR; tt boost
  ibtp112 -> I_tail ceiling; ff/125 boost vbl0x4 -> V_OCM.

Rows (expected values from SPEC / CL / RC-M1, not from this code):
  op converges, no NaN; core device margins Vds - Vdsat >= 50 mV (switches are triode by design, composite-reference
  inner fingers are triode by design: excluded); I_fold/I_tail >= 1.2; base span >= 1.6 V (RC-M1); boost span >= 1.40 V
  at the hot corners; precision (base) A0 >= 80.3 dB (RC-M1); |A0_hand - A0_ac| <= 1 dB; boost GBW reported at all three
  loads (gate B decides); fp2 = equivalent second pole from PM at the beta1 crossing.
  A0_hand = gm_in * (R_up || R_dn), R_up = r_l (1 + gm_pc r_pc) + r_pc, r_l = 1/(gds_pl + gds_plc);
  R_dn = r_n (1 + (gm_nc + gmbs_nc) r_nc) + r_nc, r_n = 1/gds_n (m_pp drain impedance and fold-switch Ron neglected).
  beta1 (CL-4) = Cint / (Cint + Cs1 + Cp_vg), Cp_vg = Cgg(m_in) + Cgg/2(closed chopper) + Cdd(open chopper)
  + Cdd(island) + C_ROUTE (vg routing estimate).
"""
import json, math, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import params as P  # noqa: E402
import sizes_draft as S  # noqa: E402
import netlist as NL  # noqa: E402
from revc_check import CORNERS9, HOT, LIB  # noqa: E402

FS = {False: 2e6, True: 4e6}
CINT1, CS1 = 4.0e-12, 0.5e-12
BETA1_DESIGN = 0.846     # DESIGN.md 2.2 design value (Cp_vg ~0.23 pF)
C_RT = 0.02e-12          # output routing per side (same as c1b_gateb c_out_ext)
CP_VG_DES = CINT1 * (1.0 / BETA1_DESIGN - 1.0) - CS1
# REVIEW-C1b M4 / D55: per-phase loads derived from the sizes (Cc 0.2 pF, Cr 0.05 pF): integrate = Cint (1 - beta1) + Cc + route
# (~0.84 pF); hold = Cint Cp/(Cint + Cp) + Cs2 + Cc + Cr + route with Cp = Cp_vg (~0.99 pF). "lump" 1.4 pF stays the SPEC basis.
LOADS = {"lump": 1.4e-12,
         "integ": CINT1 * (1.0 - BETA1_DESIGN) + S.C_CMFB_SENSE + C_RT,
         "hold": CINT1 * CP_VG_DES / (CINT1 + CP_VG_DES) + P.CS2 + S.C_CMFB_SENSE + S.C_CMFB_REFRESH + C_RT}
C_ROUTE = 0.035e-12      # vg routing estimate per side (CL-4; pair 12 fingers, ~100 um met2 to Cs1/Cint, top-plate parasitics)
A0_MIN = 80.3
K_TOL = 0.10
RATIO_TOL, RATIO_SPREAD = 0.02, 0.02
SR_FLOOR = {False: 12.5e6, True: 25e6}     # V/s at C_SR (SPEC row 95)
C_SR = 1.4e-12
I_TAIL_CEIL = 1.08                         # I_tail ceiling, x design (power / CL-8 budget; reviewer: +-4 % costs nothing)
VOCM_MAX = 38e-3                           # SPEC row 98 / CL-2 (passive SC CMFB, before the CM amp: info since WO-27)
VOCM_AMP_MAX = 10e-3                       # WO-27 / D60: |V_OCM err| + 3 sigma with the CM error amp
FCM_MIN, PMCM_MIN = 9.4e6, 45.0            # WO-27: boost f_cm (tb9 basis) at the real per-phase loads; CM PM every copy
FCM_LOADS = ("integ", "hold")
KP_TRACK_TOL = 0.02
SIG_INFO_AVT = S.A_VT_HV_LO   # info column: the same allotments at the optimistic A_VT


def area(key, m=None):
    z = S.SIZES[key]
    return z["WF"] * z["L"] * (z["M"] if m is None else m)


def sig_vt(a1, a2, avt=None):
    """Hand Pelgrom sigma of the VT difference between two device groups of gate area a1, a2 [um^2] (D60, M1)."""
    return (avt or S.A_VT_HV) * math.sqrt(1.0 / a1 + 1.0 / a2)


def sig_i(gm_i, a1, a2, avt=None):
    """Relative current sigma of a mirror pair: VT term through gm/I plus the current-factor term."""
    return math.hypot(gm_i * sig_vt(a1, a2, avt), S.A_B_HV * math.sqrt(1.0 / a1 + 1.0 / a2))
# (copy, mut tokens, target row or None = helper copy (no verdict), boost)
MUTANTS = {("tt", 27): [("mutnc", "nc_short", "precision A0", False), ("mutrc", "ref_composite", "I_tail ceiling", False),
                        ("mkp0", "kp_fixed", None, False), ("mkp5", "kp_fixed+ibn105", "K_P tracking", False),
                        ("mtlo", "ibtp90", "SR", True), ("mthi", "ibtp112", "I_tail ceiling", True)],
           ("ff", 125): [("mvo", "int_off", "V_OCM", False)]}   # WO-28: slow path off -> passive loop
# WO-27: f_cm broken copy (Cc / 4, boost, integrate load) with its loop-break helper; appended to the tt mutant deck
MUTANTS[("tt", 27)] += [("mcc4", "cc_div4", "f_cm", True, "integ"), ("mcc4o", "cc_div4+cm_open", None, True, "integ")]
OPEN = {"mcc4": "mcc4o"}   # closed copy -> its cm_open twin (nominal pairs added in copies_for)
TRACK = {"bkp": "blump", "bkt": "blump", "mkp5": "mkp0"}   # K_P tracking pairs: perturbed copy -> its reference copy
DEVQ = ("gm", "gds", "gmbs", "id", "vdsat", "cgg", "cdd")
CORE = {"min1": "m_in", "mpp1": "m_pp", "mt": "m_t", "mn1": "m_n", "mnc1": "m_nc", "mpc1": "m_pc", "mpl1": "m_pl",
        "mplc1": "m_plc"}
SWQ = {"sci1": "nfet_g5v0d10v5", "sci3": "nfet_g5v0d10v5", "sisl1": "nfet_g5v0d10v5"}
BIASQ = {"mbpd": "m_bpd", "mbpds": "m_bpd", "mbnd": "m_bnd"}
INTQ = {"mia1": "m_ia", "mia2": "m_ia", "mit": "m_it", "mil1": "m_il", "mil2": "m_il"}   # WO-28 slow-path integrator
REPQ = {"mrn": "m_rn", "mrnc": "m_rnc", "mrcb": "m_rcb"}                                  # WO-28 item 4 replica margins
NODES = ("tail", "da", "fa", "xa", "sa", "ctl", "rnd", "rcb", "bli", "cid", "cit")   # subckt-internal only (ports: top level)
BRK_MAX = 1e-3          # WO-28 run 2: cm_open loop break must be DC-transparent, |V(ctlg) - V(ctl)| <= 1 mV
HELPER_DCTL, HELPER_DOCM = 1e-3, 0.1e-3   # helper op vs closed-loop op: |dV_ctl| <= 1 mV, |dV_OCM| <= 0.1 mV
FZ_RATIO = 10.0          # WO-28: slow-path PI zero f_z <= f_cm / 10
PEAK_MAX_DB = 1.0        # WO-28: closed-loop CM |T / (1 + T)| peaking


def par(x, inst, dev, q):
    return f"@m.x{x}.x{inst}.msky130_fd_pr__{dev}[{q}]"


def copy_lines(x, boost, cl, sub, mut=None):
    vd = "vdd_" + x
    L = [f"X{x} {vd} 0 inp_{x} inn_{x} outp_{x} outn_{x} vicm vocm ibtp_{x} ibn_{x} ibp_{x} ivbnc_{x} ivbpc_{x} ivbl0_{x} "
         f"{vd} 0 lv 0 0 0 {vd} 0 {vd} {vd} {sub}"]
    for p_, i_ in NL.bias_currents(boost, mut).items():
        L.append(f"I{p_}_{x} {p_}_{x} 0 {i_:.6e}" if p_ in NL.SINK_PORTS else f"I{p_}_{x} {vd} {p_}_{x} {i_:.6e}")
    ce = cl - S.C_CMFB_SENSE
    L += [f"Cxp_{x} outp_{x} 0 {ce:g}", f"Cxn_{x} outn_{x} 0 {ce:g}",
          f"Bip_{x} inp_{x} 0 V = V(icm) + 0.5*(V(d) - max(min(V(s_{x})/1000, 0.3), -0.3))",
          f"Bin_{x} inn_{x} 0 V = V(icm) - 0.5*(V(d) - max(min(V(s_{x})/1000, 0.3), -0.3))",
          f"Bs_{x} 0 s_{x} I = 1e-3*(V(outp_{x}) - V(outn_{x}))", f"Rs_{x} s_{x} 0 1e12", f"Cs_{x} s_{x} 0 1e9",
          f".nodeset v(s_{x})=0 v(outp_{x})={S.V_OCM} v(outn_{x})={S.V_OCM}",
          f"Icmp_{x} 0 outp_{x} dc 0 ac 1e-6", f"Icmn_{x} 0 outn_{x} dc 0 ac 1e-6",   # WO-27 CM injection (f_cm)
          f"Bcmo_{x} cmo_{x} 0 V = 0.5*(V(outp_{x})+V(outn_{x}))"]
    pc = S.SIZES["m_plc"]   # V_BL0 ratio probe: m_plc copy, gate ivbl0, drain forced to V(sa), own supply
    L += [f"Vprb_{x} vprb_{x} 0 {vd_val(x)}", f"Bdp_{x} dp_{x} 0 V = v(x{x}.sa)",
          NL.mos(f"prb_{x}", f"dp_{x}", f"ivbl0_{x}", f"vprb_{x}", f"vprb_{x}", pc["dev"], pc["WF"], pc["L"], pc["M"])]
    return L


VDD_NOW = {}


def vd_val(x):
    return VDD_NOW["v"]


def copies_for(c, t):
    cp = [(f"{m}{ld}", b, LOADS[ld], None) for m, b in (("b", False), ("f", True)) for ld in LOADS]
    op = [(f"o{m}{ld}", b, LOADS[ld], "cm_open") for m, b in (("b", False), ("f", True)) for ld in LOADS]
    for m in ("b", "f"):
        for ld in LOADS:
            OPEN[f"{m}{ld}"] = f"o{m}{ld}"
    # K_P tracking copies (ibn x1.05, ibtp x0.95) and the cm_open loop-break helpers (f_cm return ratio)
    return cp + [("bkp", False, LOADS["lump"], "ibn105"), ("bkt", False, LOADS["lump"], "ibtp95")] + op


def mutant_copies(c, t):
    """Own deck (REVIEW-C1b M5): a mutant must not share a deck with the nominal corner copies."""
    return [(e[0], e[3], LOADS[e[4] if len(e) > 4 else "lump"], e[1]) for e in MUTANTS.get((c, t), [])]


def deck(c, t, v, tag, copies):
    VDD_NOW["v"] = v
    L = [f"* WO-25 c1b_opac {tag}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-15 reltol=1e-6",
         f"Vicm vicm 0 {S.V_ICM}", f"Vicm2 icm 0 {S.V_ICM}", f"Vocm vocm 0 {S.V_OCM}", "Vlv lv 0 1.8", "Vd d 0 dc 0 ac 1"]
    subs = {}
    for x, b, cl, mut in copies:
        key = (b, mut)
        if key not in subs:
            nm = f"ota1_{'f' if b else 'b'}{'_' + mut if mut else ''}"
            subs[key] = nm
            L.append(NL.build(nm, cmfb="dc", fs=FS[b], mut=mut, boost=b))
        L.append(f"Vdd_{x} vdd_{x} 0 {v}")
        L += copy_lines(x, b, cl, subs[key], mut)
    L += [".control", "set wr_singlescale", "set wr_vecnames", "op"]
    for x, b, cl, mut in copies:
        L.append(f"print i(vdd_{x})")
        L += [f"print v(x{x}.{n})" for n in NODES] + [f"print v(outp_{x}) v(outn_{x}) v(s_{x}) v(ivbpc_{x})"]
        if "cm_open" in NL.toks(mut):
            L.append(f"print v(x{x}.ctlg)")
        L += [f"print {par(x, i, S.SIZES[k]['dev'], q)}" for i, k in CORE.items() for q in DEVQ]
        L += [f"print {par(x, i, d, q)}" for i, d in SWQ.items() for q in ("cgg", "cdd")]
        L += [f"print {par(x, i, S.SIZES[k]['dev'], 'id')}" for i, k in BIASQ.items()]
        L.append(f"print @m.xprb_{x}.msky130_fd_pr__{S.SIZES['m_plc']['dev']}[id]")
        if "int_off" not in NL.toks(mut):
            L += [f"print {par(x, i, S.SIZES[k]['dev'], q)}" for i, k in INTQ.items() for q in ("gm", "gds", "id", "vdsat")]
        if "kp_fixed" not in NL.toks(mut):
            L += [f"print {par(x, i, S.SIZES[k]['dev'], q)}" for i, k in REPQ.items() for q in ("id", "vdsat")]
    L += ["ac dec 40 1 1e10", "wrdata " + tag + "_ac.csv " + " ".join(f"v(outp_{x},outn_{x})" for x, *_ in copies)
          + " " + " ".join(f"v(cmo_{x})" for x, *_ in copies),
          "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def run(text, tag, out):
    fn = os.path.join(out, tag + ".sp")
    open(fn, "w").write(text)
    r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=560)
    vals = {}
    for ln in r.stdout.splitlines():
        if " = " in ln:
            k, _, x = ln.partition(" = ")
            try:
                vals[k.strip().lower()] = float(x.split()[0])
            except ValueError:
                pass
    lint = [l.strip() for l in (r.stdout + r.stderr).splitlines()
            if re.search(r"(error|unknown|singular|no convergence|timestep too small|could not find|transient op)", l, re.I)]
    # WO-28 run 2: "transient op" = Newton, gmin and source stepping all failed and ngspice took the op from a transient
    # ramp; huge caps (cm_open 1 F break, servo 1e9 F) then keep their initial charge, so the op is not a DC point -> lint
    return vals, r, lint


def analyse(vals, x, b, cl, mut, ac, k, vdd, hot):
    g = lambda key: vals.get(key.lower(), float("nan"))
    v = lambda n: g(f"v(x{x}.{n})")
    d = {i: {q: g(par(x, i, S.SIZES[kk]["dev"], q)) for q in DEVQ} for i, kk in CORE.items()}
    on, op_ = g(f"v(outn_{x})"), g(f"v(outp_{x})")
    vds = {"mt": vdd - v("tail"), "min1": v("tail") - v("da"), "mpp1": v("da") - v("fa"), "mn1": v("fa"),
           "mnc1": on - v("xa"), "mpc1": v("sa") - on, "mpl1": vdd - v("sa"), "mplc1": vdd - v("sa")}
    res, fails = {"margins": {}}, []
    for i in CORE:
        mg = vds[i] - abs(d[i]["vdsat"])
        res["margins"][i] = mg
        if not mg >= 0.05:
            fails.append(f"{i} margin {mg:.3f}")
    vod = op_ - on
    res["vod_mV"] = vod * 1e3
    res["servo_s"] = g(f"v(s_{x})")
    # m4 servo-lost row: the servo must hold |vod| <= 1 mV without sitting at its clamp (|s|/1000 = 0.3)
    if not (abs(vod) <= 1e-3 and abs(res["servo_s"]) / 1000 < 0.299):
        fails.append(f"servo lost: vod {vod * 1e3:.3f} mV, s {res['servo_s']:.4g}")
    res["V_ocm_err_mV"] = (0.5 * (op_ + on) - S.V_OCM) * 1e3
    res["V_fa"], res["V_ctl"] = v("fa"), v("ctl")
    if "cm_open" in NL.toks(mut):   # loop break must not move the DC op
        res["V_ctlg_minus_ctl_mV"] = (v("ctlg") - v("ctl")) * 1e3
        if not abs(v("ctlg") - v("ctl")) <= BRK_MAX:
            fails.append(f"loop-break DC |V_ctlg - V_ctl| {abs(v('ctlg') - v('ctl')) * 1e3:.3g} mV > {BRK_MAX * 1e3:.0f}")
    res["bottom"] = v("xa") + abs(d["mnc1"]["vdsat"]) + 0.05
    res["top"] = v("sa") - abs(d["mpc1"]["vdsat"]) - 0.05
    res["span"] = res["top"] - res["bottom"]
    res["I_fold_over_I_tail"] = abs(d["mn1"]["id"]) / abs(d["mt"]["id"])
    res["I_vdd_uA"] = abs(g(f"i(vdd_{x})")) * 1e6
    res["I_tail_uA"] = abs(d["mt"]["id"]) * 1e6
    # D58 rows: composite-to-mirror ratios, I_tail, effective K_P / K_N
    ib = NL.bias_currents(b, mut)
    z = S.SIZES
    rr = lambda mir, ref_: z[mir]["M"] / z[ref_]["M"]   # nominal 1:8 (D59)
    res["ratio_tr"] = abs(d["mt"]["id"]) / (rr("m_t", "m_tr") * ib["ibtp"])
    res["ratio_nr"] = abs(d["mn1"]["id"]) / (rr("m_n", "m_nr") * ib["ibn"])
    res["ratio_plr"] = abs(d["mpl1"]["id"]) / (rr("m_pl", "m_plr") * ib["ibp"])
    res["ratio_bl0"] = abs(g(f"@m.xprb_{x}.msky130_fd_pr__{z['m_plc']['dev']}[id]")) / (rr("m_plc", "m_bl0") * ib["ivbl0"])
    # D60: the mirror-ratio rows are INFO only (systematic CLM/DIBL accepted; REVIEW-WO26 M3). The dependent rows (SR,
    # ceiling, K_P tracking, V_OCM) carry the gate, each with a hand-Pelgrom 3 sigma allotment (below).
    res["ratio_info_outside_2pct"] = [kk for kk in RATIO_KEYS if not abs(res[kk] - 1) <= RATIO_TOL]
    # D60 mismatch allotments (hand Pelgrom, DESIGN.md 2.11). Tail: m_t (all fingers) vs m_tr. Sinks / fixed loads: the CM
    # (two-side) mirror vs its reference. Sigma of the relative current, then V_OCM via the CMFB device.
    gi = lambda i: abs(d[i]["gm"] / d[i]["id"])
    a_t, a_tr = area("m_t"), area("m_tr")
    res["sig_Itail_pct"] = sig_i(gi("mt"), a_t, a_tr) * 100
    res["sig_Itail_pct_avt8"] = sig_i(gi("mt"), a_t, a_tr, SIG_INFO_AVT) * 100
    s_pl = sig_i(gi("mpl1"), 2 * area("m_pl"), area("m_plr"))
    s_n = sig_i(gi("mn1"), 2 * area("m_n"), area("m_nr"))
    s_t = res["sig_Itail_pct"] / 100
    di = math.sqrt((abs(d["mpl1"]["id"]) * s_pl) ** 2 + (abs(d["mn1"]["id"]) * s_n) ** 2 + (abs(d["mt"]["id"]) / 2 * s_t) ** 2)
    res["sig_dI_sa_nA"] = di * 1e9
    res["sig_ctl_need_mV"] = di / abs(d["mplc1"]["gm"]) * 1e3            # ctl shift the CMFB must supply
    res["sig_bl0_mV"] = sig_vt(area("m_bl0"), 2 * area("m_plc")) * 1e3      # V_BL0 replica vs m_plc (passive CMFB)
    res["sig_vocm_passive_mV"] = math.hypot(res["sig_ctl_need_mV"], res["sig_bl0_mV"])
    res["V_ocm_3sig_passive_mV"] = abs(res["V_ocm_err_mV"]) + S.N_SIGMA * res["sig_vocm_passive_mV"]   # info vs 38 mV
    t_ = NL.toks(mut)
    if "int_off" in t_:
        res["sig_vocm_mV"] = res["sig_vocm_passive_mV"]
    else:   # WO-28 dual path (DESIGN.md 1.3b / 2.11): integrator pair 1:1, its loads referred by I/gm_ia, the fold-node
        # current term (passive sigma) and the V_BL0 replica are divided by A_int (bli absorbs them)
        a = {i: {q: g(par(x, i, S.SIZES[k]["dev"], q)) for q in ("gm", "gds", "id", "vdsat")} for i, k in INTQ.items()}
        gm_a = abs(a["mia1"]["gm"])
        res["A_int"] = gm_a / (abs(a["mia2"]["gds"]) + abs(a["mil2"]["gds"]))
        res["I_int_uA"] = abs(a["mit"]["id"]) * 1e6
        res["gm_ia_uS"] = gm_a * 1e6
        res["f_z_MHz"] = gm_a / (2 * math.pi * S.C_INT) / 1e6
        res["V_bli_minus_ctl_mV"] = (v("bli") - v("ctl")) * 1e3
        vd_ = {"mit": v("cit"), "mia1": v("cid") - v("cit"), "mia2": v("bli") - v("cit"), "mil2": vdd - v("bli")}
        for i_, vv in vd_.items():
            res["margins"][i_] = vv - abs(a[i_]["vdsat"])
            if not res["margins"][i_] >= 0.05:
                fails.append(f"{i_} margin {res['margins'][i_]:.3f}")
        i_a = abs(a["mia1"]["id"])
        s_pair = math.hypot(sig_vt(area("m_ia"), area("m_ia")), S.A_B_HV * math.sqrt(2 / area("m_ia")) * i_a / gm_a)
        s_load = sig_i(abs(a["mil1"]["gm"]) / abs(a["mil1"]["id"]), area("m_il"), area("m_il")) * i_a / gm_a
        s_res = res["sig_vocm_passive_mV"] * 1e-3 / res["A_int"]
        res["sig_int_pair_mV"], res["sig_int_load_mV"] = s_pair * 1e3, s_load * 1e3
        res["sig_vocm_mV"] = math.sqrt(s_pair ** 2 + s_load ** 2 + s_res ** 2) * 1e3
    if "kp_fixed" not in t_:   # WO-28 item 4: sink-replica drain vs m_n drain, margins of m_rn / m_rnc / m_rcb
        rq = {i: {q: g(par(x, i, S.SIZES[k]["dev"], q)) for q in ("id", "vdsat")} for i, k in REPQ.items()}
        res["V_rnd"] = v("rnd")   # sink-replica drain vs m_n drain (D59 replica fix); kp_fixed has no replica
        res["V_rnd_minus_V_fa_mV"] = (v("rnd") - v("fa")) * 1e3
        if not abs(v("rnd") - v("fa")) <= S.REPLICA_DV_MAX:
            fails.append(f"replica drain |V_rnd - V_fa| {abs(v('rnd') - v('fa')) * 1e3:.0f} mV > {S.REPLICA_DV_MAX * 1e3:.0f}")
        for i_, vv in {"mrn": v("rnd"), "mrnc": g(f"v(ivbpc_{x})") - v("rnd"), "mrcb": v("rcb")}.items():
            res["margins"][i_] = vv - abs(rq[i_]["vdsat"])
            if not res["margins"][i_] >= 0.05:
                fails.append(f"{i_} margin {res['margins'][i_]:.3f}")
    res["V_ocm_3sig_mV"] = abs(res["V_ocm_err_mV"]) + S.N_SIGMA * res["sig_vocm_mV"]
    if not res["V_ocm_3sig_mV"] <= VOCM_AMP_MAX * 1e3:
        fails.append(f"V_OCM |err| {abs(res['V_ocm_err_mV']):.2f} + 3sig = {res['V_ocm_3sig_mV']:.2f} mV > {VOCM_AMP_MAX * 1e3:.0f}")
    nb = S.KP_BANK["boost" if b else "base"]
    wl = lambda k_, m_=None: z[k_]["WF"] * (m_ or z[k_]["M"]) / z[k_]["L"]
    i_bpd = abs(g(par(x, "mbpd", z["m_bpd"]["dev"], "id"))) + abs(g(par(x, "mbpds", z["m_bpd"]["dev"], "id")))
    res["I_bpds_off_nA"] = 0.0 if b else abs(g(par(x, "mbpds", z["m_bpd"]["dev"], "id"))) * 1e9   # base: switched fingers off
    i_bnd = abs(g(par(x, "mbnd", z["m_bnd"]["dev"], "id")))
    res["I_bpd_uA"], res["I_bnd_uA"] = i_bpd * 1e6, i_bnd * 1e6
    res["K_P_eff"] = (i_bpd / wl("m_bpd", nb)) / (abs(d["mpc1"]["id"]) / wl("m_pc"))
    res["K_P_target"] = S.K_BIAS_P * S.KP_BANK["base"] / nb
    res["K_N_eff"] = (i_bnd / wl("m_bnd")) / (abs(d["mnc1"]["id"]) / wl("m_nc"))
    it_t = S.I_TAIL * (S.BOOST if b else 1.0)
    res["SR_Vus"] = res["I_tail_uA"] * 1e-6 / C_SR / 1e6
    k3 = S.N_SIGMA * res["sig_Itail_pct"] / 100
    res["SR_m3sig_Vus"] = res["SR_Vus"] * (1 - k3)          # D60 row: nominal - 3 sigma >= floor (SPEC row 95, 1.4 pF)
    res["SR_m3sig_avt8_Vus"] = res["SR_Vus"] * (1 - S.N_SIGMA * res["sig_Itail_pct_avt8"] / 100)   # info
    res["SR_integ_m3sig_Vus"] = res["SR_m3sig_Vus"] * C_SR / LOADS["integ"]                       # info, real load
    res["I_tail_p3sig_uA"] = res["I_tail_uA"] * (1 + k3)
    if not res["SR_m3sig_Vus"] * 1e6 >= SR_FLOOR[b]:
        fails.append(f"SR {res['SR_Vus']:.2f} V/us, -3sig {res['SR_m3sig_Vus']:.2f} < {SR_FLOOR[b] / 1e6:.1f} at {C_SR * 1e12:.1f} pF")
    if not res["I_tail_p3sig_uA"] * 1e-6 <= I_TAIL_CEIL * it_t:
        fails.append(f"I_tail ceiling {res['I_tail_uA']:.2f} uA, +3sig {res['I_tail_p3sig_uA']:.2f} > {I_TAIL_CEIL * it_t * 1e6:.2f}")
    if not abs(res["K_P_eff"] / res["K_P_target"] - 1) <= K_TOL:
        fails.append(f"K_P {res['K_P_eff']:.2f} vs {res['K_P_target']:.2f} (+-10 %)")
    # hand A0
    gi = d["min1"]["gm"]
    r_l = 1 / (d["mpl1"]["gds"] + d["mplc1"]["gds"])
    rpc = 1 / d["mpc1"]["gds"]
    r_up = r_l * (1 + d["mpc1"]["gm"] * rpc) + rpc
    rnc, r_n = 1 / d["mnc1"]["gds"], 1 / d["mn1"]["gds"]
    r_dn = r_n * (1 + (d["mnc1"]["gm"] + d["mnc1"]["gmbs"]) * rnc) + rnc
    res["A0_hand_dB"] = 20 * math.log10(gi * r_up * r_dn / (r_up + r_dn))
    res["Rdn_over_Rup"] = r_dn / r_up
    # beta1 (CL-4)
    sw = {i: {q: g(par(x, i, dv, q)) for q in ("cgg", "cdd")} for i, dv in SWQ.items()}
    cpvg = d["min1"]["cgg"] + 0.5 * sw["sci1"]["cgg"] + abs(sw["sci3"]["cdd"]) + abs(sw["sisl1"]["cdd"]) + C_ROUTE
    res["Cp_vg_fF"] = cpvg * 1e15
    res["beta1"] = CINT1 / (CINT1 + CS1 + cpvg)
    # AC
    f, h = ac[:, 0], ac[:, 1 + 2 * k] + 1j * ac[:, 2 + 2 * k]
    mag = np.abs(h)
    res["A0_dB"] = 20 * math.log10(mag[0])
    if not (mag[0] > 1 and np.any(mag < 1)):
        fails.append("dead OTA / no unity crossing")
        return res, fails
    i = int(np.argmax(mag < 1))
    res["GBW_MHz"] = float(np.exp(np.interp(0.0, -np.log(mag[i - 1:i + 1]), np.log(f[i - 1:i + 1])))) / 1e6
    ph = np.unwrap(np.angle(h)) * 180 / np.pi
    bt = res["beta1"]
    j = int(np.argmax(mag * bt < 1))
    fb = float(np.exp(np.interp(0.0, -np.log(mag[j - 1:j + 1] * bt), np.log(f[j - 1:j + 1]))))
    res["fu_beta_MHz"] = fb / 1e6
    res["PM_deg"] = 180.0 + (float(np.interp(np.log(fb), np.log(f), ph)) - ph[0])
    ex = 90.0 - res["PM_deg"]
    res["fp2_MHz"] = fb / math.tan(math.radians(ex)) / 1e6 if ex > 0.1 else float("inf")
    res["fp2_over_GBW"] = res["fp2_MHz"] / res["GBW_MHz"]
    # rows
    if not b and not res["A0_dB"] >= A0_MIN:
        fails.append(f"precision A0 {res['A0_dB']:.2f} < {A0_MIN}")
    if not abs(res["A0_hand_dB"] - res["A0_dB"]) <= 1.0:
        fails.append(f"hand A0 {res['A0_hand_dB']:.2f} vs AC {res['A0_dB']:.2f} > 1 dB")
    if not res["I_fold_over_I_tail"] >= 1.2:
        fails.append(f"I_fold/I_tail {res['I_fold_over_I_tail']:.3f}")
    if not b and not res["span"] >= 1.6:
        fails.append(f"base span {res['span']:.3f} < 1.6")
    if b and hot and not res["span"] >= 1.40:
        fails.append(f"boost span {res['span']:.3f} < 1.40")
    for kk, xx in res.items():
        if isinstance(xx, float) and math.isnan(xx):
            fails.append(f"NaN {kk}")
    return res, fails


def fcm(ac, kc, ko):
    """Both vectors from one AC csv (vector indices kc, ko)."""
    return fcm_z(ac[:, 0], ac[:, 1 + 2 * kc] + 1j * ac[:, 2 + 2 * kc], ac[:, 1 + 2 * ko] + 1j * ac[:, 2 + 2 * ko])


def fcm_z(f, zc, zo):
    """CM loop gain from the closed- and open-loop CM output impedance (same CM current injection), unity crossing and PM."""
    t_ = zo / zc - 1.0
    m = np.abs(t_)
    i = int(np.argmax((m[:-1] >= 1) & (m[1:] < 1))) + 1
    if not (m[i - 1] >= 1 > m[i]):
        raise ValueError("no CM unity crossing")
    fu = float(np.exp(np.interp(0.0, -np.log(m[i - 1:i + 1]), np.log(f[i - 1:i + 1]))))
    # WO-28 run 2: PM from the phase LAG at the crossing, lag in [0, 360). The old whole-sweep unwrap anchored at 1 Hz broke
    # with the dual path: below f_z T is ~1/s^2 (phase near -180 deg, sign ambiguous at 1 Hz), giving PM = 447 deg.
    a = float(np.interp(np.log(fu), np.log(f[i - 1:i + 1]), np.unwrap(np.angle(t_[i - 1:i + 1])))) * 180 / np.pi
    lag = (-a) % 360.0
    tc = np.abs(t_ / (1.0 + t_))
    return {"f_cm_MHz": fu / 1e6, "PM_cm_deg": 180.0 - lag,
            "T_cm_dc_dB": 20 * math.log10(m[0]), "cm_peak_dB": 20 * math.log10(float(np.max(tc)))}


def fcm_hand(out):
    """WO-28: hand-solvable validation of fcm() (and of the Z_ol / Z_cl pairing). Behavioural CM loop: node o, C_H to
    ground, CM current injection; sense e = V(o) through an RC pole f_p; control current -G_H * V(e) into o. Open copy:
    the control reads e through 1 GOhm / 1 F (as cm_open). Exact T = G_H R_H / ((1 + s R_H C_H)(1 + s / w_p)); the
    extracted f_cm / PM must match the analytic solution within 1 % / 0.5 deg, for two G_H values."""
    R_H, C_H, F_P = 1e9, 1e-12, 20e6
    rows = []
    for gh in (50e-6, 12.5e-6):
        L = [f"* fcm_hand gh={gh:g}", "Vd d 0 dc 0 ac 1"]
        for x, op in (("c", False), ("o", True)):
            L += [f"Ri{x} o{x} 0 {R_H:g}", f"Ci{x} o{x} 0 {C_H:g}", f"Ii{x} 0 o{x} dc 0 ac 1e-6",
                  f"Bs{x} s{x} 0 V = V(o{x})", f"Rp{x} s{x} e{x} 1e3", f"Cp{x} e{x} 0 {1 / (2 * math.pi * 1e3 * F_P):g}"]
            ctl = f"e{x}"
            if op:
                L += [f"Rb{x} e{x} g{x} 1e9", f"Cb{x} g{x} 0 1"]
                ctl = f"g{x}"
            L += [f"G{x} o{x} 0 {ctl} 0 {gh:g}"]
        tag = f"fcmhand_{int(gh * 1e7)}"
        fn = os.path.join(out, tag + "_ac.csv")
        L += [".control", "set wr_singlescale", "set wr_vecnames", "ac dec 40 1 1e10",
              f"wrdata {tag}_ac.csv v(oc) v(oo)", "quit", ".endc", ".end"]
        open(os.path.join(out, tag + ".sp"), "w").write("\n".join(L) + "\n")
        subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=120)
        ac = np.loadtxt(fn, skiprows=1)
        os.remove(fn)
        got = fcm(ac, 0, 1)   # columns (f, re, im per vector): closed = v(oc) vector 0, open = v(oo) vector 1
        ff = np.logspace(0, 10, 200001)
        tt_ = gh * R_H / ((1 + 2j * math.pi * ff * R_H * C_H) * (1 + 1j * ff / F_P))
        k = int(np.argmax(np.abs(tt_) < 1))
        fu, pm = ff[k], 180.0 + math.degrees(np.angle(tt_[k]))
        ok = abs(got["f_cm_MHz"] * 1e6 / fu - 1) <= 0.01 and abs(got["PM_cm_deg"] - pm) <= 0.5
        rows.append(dict(gh_uS=gh * 1e6, f_cm_MHz=got["f_cm_MHz"], f_hand_MHz=fu / 1e6, PM=got["PM_cm_deg"], PM_hand=pm, ok=ok))
    return rows


def run_deck_group(c, t, v, tag, cps, out):
    """One deck: returns (rows, lint, err). The AC csv is deleted BEFORE ngspice runs (REVIEW-C1b m5: no stale reuse)."""
    fn = os.path.join(out, tag + "_ac.csv")
    if os.path.exists(fn):
        os.remove(fn)
    vals, r, lint = run(deck(c, t, v, tag, cps), tag, out)
    try:
        ac = np.loadtxt(fn, skiprows=1)
        os.remove(fn)
    except Exception as e:
        return [], lint, dict(corner=tag, fails=[f"no data {e!r}"], lint=lint[:5], stderr=r.stderr[-600:]), None
    rows = []
    for k, (x, b, cl, mut) in enumerate(cps):
        try:
            res, fails = analyse(vals, x, b, cl, mut, ac, k, v, (c, t) in HOT)
        except Exception as e:
            res, fails = {}, [f"analysis error {e!r}"]
        if lint:
            fails.append(f"lint: {lint[:3]}")
        rows.append((x, b, cl, mut, res, fails))
    return rows, lint, None, ac


def cm_rows(grows, acmap):
    """WO-27/28 f_cm / CM PM rows for every closed copy with a cm_open twin. WO-28 run 2: the twin may sit in another deck
    (acmap: copy -> (ac, vector index of its CM output)); its op must equal the closed-loop op (else the return ratio is
    taken around a different bias point: run 1 found the twins 1.7 V off after a transient op), and a lint / loop-break
    failure of the twin invalidates the row."""
    byx = {r[0]: r for r in grows}
    for x, b, cl, mut, res, fails in grows:
        if x not in OPEN or OPEN[x] not in byx:
            continue
        xo = OPEN[x]
        ro, fo = byx[xo][4], byx[xo][5]
        bad = [f_ for f_ in fo if f_.startswith(("lint", "loop-break", "analysis error"))]
        dctl = abs(ro.get("V_ctl", float("nan")) - res.get("V_ctl", float("nan")))
        docm = abs(ro.get("V_ocm_err_mV", float("nan")) - res.get("V_ocm_err_mV", float("nan"))) * 1e-3
        res["helper_dV_ctl_mV"], res["helper_dV_ocm_mV"] = dctl * 1e3, docm * 1e3
        if bad or not (dctl <= HELPER_DCTL and docm <= HELPER_DOCM):
            fails.append(f"f_cm helper invalid ({xo}: dV_ctl {dctl * 1e3:.3g} mV, dV_OCM {docm * 1e3:.3g} mV, {bad[:2]})")
            continue
        try:
            (ac, kc), (aco, ko) = acmap[x], acmap[xo]
            if not (ac.shape[0] == aco.shape[0] and np.allclose(ac[:, 0], aco[:, 0], rtol=1e-9)):
                raise ValueError("AC frequency grids differ")
            res.update(fcm_z(ac[:, 0], ac[:, 1 + 2 * kc] + 1j * ac[:, 2 + 2 * kc], aco[:, 1 + 2 * ko] + 1j * aco[:, 2 + 2 * ko]))
            ld = [l_ for l_ in LOADS if abs(LOADS[l_] - cl) < 1e-18]
            if not res["PM_cm_deg"] >= PMCM_MIN:
                fails.append(f"CM PM {res['PM_cm_deg']:.1f} deg < {PMCM_MIN:.0f}")
            if b and ld and ld[0] in FCM_LOADS and not res["f_cm_MHz"] * 1e6 >= FCM_MIN:
                fails.append(f"f_cm {res['f_cm_MHz']:.2f} MHz < {FCM_MIN / 1e6:.1f} (boost, {ld[0]})")
            if not res["cm_peak_dB"] <= PEAK_MAX_DB:
                fails.append(f"CM peaking {res['cm_peak_dB']:.2f} dB > {PEAK_MAX_DB:.0f}")
            if "f_z_MHz" in res and not res["f_z_MHz"] * FZ_RATIO <= res["f_cm_MHz"]:
                fails.append(f"f_z {res['f_z_MHz']:.3f} MHz > f_cm / {FZ_RATIO:.0f}")
        except Exception as e:
            fails.append(f"f_cm analysis error {e!r}")


RATIO_KEYS = ("ratio_tr", "ratio_nr", "ratio_plr", "ratio_bl0")


def summary(out):
    """WO-26 item 1 exit: per mode, spread (max - min) of each mirror ratio over all corners of the nominal lump copies
    <= RATIO_SPREAD, and over temperature per process (-40 vs 125 at ss/fs/sf/ff). Returns the number of failures."""
    import glob
    rows = [r for f in sorted(glob.glob(os.path.join(out, "opac_*.json"))) for r in json.load(open(f))
            if r.get("copy") in ("blump", "flump")]
    nf = 0
    for b in (False, True):
        rb = [r for r in rows if r["boost"] == b]
        for k in RATIO_KEYS:
            v = [r[k] for r in rb]
            sp = (max(v) - min(v)) if v else float("nan")
            tsp = max([abs(r1[k] - r2[k]) for r1 in rb for r2 in rb if r1["corner"] == r2["corner"]
                       and r1["temp"] != r2["temp"]] or [float("nan")])
            tt = [r[k] for r in rb if r["corner"] == "tt"]
            dtt = max(abs(x / tt[0] - 1) for x in v) if tt else float("nan")   # info: deviation from the tt/27 value
            ok = len(v) == 9 and sp <= RATIO_SPREAD and (tsp <= RATIO_SPREAD)   # D60: info only, not counted
            print(f"{'boost' if b else 'base '} {k:9s} n={len(v)} min {min(v):.4f} max {max(v):.4f} spread {sp * 100:.2f} % "
                  f"temp spread {tsp * 100:.2f} % max dev from tt {dtt * 100:.2f} % (info) {'OK' if ok else 'FAIL'}")
    print("SUMMARY (ratio rows info only, D60)")
    return nf


def main():
    if sys.argv[1] == "--summary":
        sys.exit(1 if summary(sys.argv[2]) else 0)
    out, idx = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    nfail, rows = 0, []
    if "0" in idx.split(","):   # WO-28: validate the return-ratio extraction on the hand-solvable behavioural loop first
        for hr in fcm_hand(out):
            print(json.dumps(dict(fcm_hand=hr)), flush=True)
            nfail += not hr["ok"]
            rows.append(dict(copy="fcm_hand", **hr))
    rnd = lambda y: float(f"{y:.4g}") if isinstance(y, float) else ({a: rnd(z) for a, z in y.items()} if isinstance(y, dict) else y)
    for ci in idx.split(","):
        c, t, v = CORNERS9[int(ci)]
        tag = f"c1b_{c}_{t}_{v}".replace("-", "m").replace(".", "p")
        cps = copies_for(c, t)
        if "--merged-open" in sys.argv:   # broken copy of the deck split: run-1 structure, helpers in the nominal deck
            groups = [(tag + "_merged", cps)]
        else:   # WO-28 run 2: cm_open helpers in their own decks (per mode), never in the nominal deck
            groups = [(tag, [q for q in cps if q[3] != "cm_open"])] + [
                (f"{tag}_open{m}", [q for q in cps if q[3] == "cm_open" and q[1] == bb]) for m, bb in (("b", False), ("f", True))]
        if mutant_copies(c, t):
            groups.append((tag + "_mut", mutant_copies(c, t)))
        grows, acmap = [], {}
        for gtag, gcps in groups:
            gr, lint, err, ac = run_deck_group(c, t, v, gtag, gcps, out)
            if err:
                print(json.dumps(err))
                nfail += 1
                continue
            grows += gr
            acmap.update({q[0]: (ac, len(gcps) + k) for k, q in enumerate(gcps)})
        cm_rows(grows, acmap)
        if True:
            kp = {x: res.get("K_P_eff", float("nan")) for x, b, cl, mut, res, fails in grows}
            for x, b, cl, mut, res, fails in grows:
                if x in TRACK:
                    dk = kp[x] / kp.get(TRACK[x], float("nan")) - 1
                    res["dKP_track_pct"] = dk * 100
                    if not abs(dk) <= KP_TRACK_TOL:
                        fails.append(f"K_P tracking {dk * 100:+.2f} % (ibn x1.05) > {KP_TRACK_TOL:.0%}")
            for x, b, cl, mut, res, fails in grows:
                mrow = {m_[0]: m_ for m_ in MUTANTS.get((c, t), [])}.get(x)
                if x.startswith("o") and mut == "cm_open":
                    res["mutant_verdict"] = "helper copy (cm_open loop break, no verdict)"
                elif mrow and mrow[2] is None:
                    res["mutant_verdict"] = "helper copy (reference of a tracking pair, no verdict)"
                elif mrow:
                    target = mrow[2]
                    a0 = res.get("A0_dB", float("nan"))
                    converged = bool(not any(f_.startswith("lint") for f_ in fails) and res and math.isfinite(res.get("I_vdd_uA", float("nan"))))
                    hit = any(f_.startswith(target) for f_ in fails)
                    res["mutant_target_row"] = target
                    if converged and math.isfinite(a0) and hit:
                        res["mutant_verdict"] = "REJECTED (good)"
                    elif converged and math.isfinite(a0):
                        res["mutant_verdict"] = "PASSED (check is blind)"
                        nfail += 1
                    else:
                        res["mutant_verdict"] = "MUTANT INVALID (op failed / NaN / lint: neither rejected nor passed)"
                        nfail += 1
                else:
                    # the tracking copy (ibn x1.05) is judged on the tracking row only; its other rows are info
                    nfail += bool([f_ for f_ in fails if f_.startswith("K_P tracking")] if x in TRACK else fails)
                row = rnd(dict(res, corner=c, temp=t, vdd=v, boost=b, C_L_pF=cl * 1e12, copy=x, fails=fails))
                rows.append(row)
                print(json.dumps(row), flush=True)
    json.dump(rows, open(os.path.join(out, f"opac_{idx.replace(',', '_')}.json"), "w"), indent=0)
    print("VERDICT", "ACCEPT" if nfail == 0 else f"REJECT ({nfail})")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
