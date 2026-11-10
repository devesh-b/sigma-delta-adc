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
VOCM_MAX = 38e-3                           # SPEC row 98 / CL-2
KP_TRACK_TOL = 0.02
# (copy, mut tokens, target row or None = helper copy (no verdict), boost)
MUTANTS = {("tt", 27): [("mutnc", "nc_short", "precision A0", False), ("mutrc", "ref_composite", "ratio", False),
                        ("mkp0", "kp_fixed", None, False), ("mkp5", "kp_fixed+ibn105", "K_P tracking", False),
                        ("mtlo", "ibtp90", "SR", True), ("mthi", "ibtp112", "I_tail ceiling", True)],
           ("ff", 125): [("mvo", "vbl0x4", "V_OCM", True)]}
TRACK = {"bkp": "blump", "mkp5": "mkp0"}   # K_P tracking pairs: perturbed copy -> its reference copy
DEVQ = ("gm", "gds", "gmbs", "id", "vdsat", "cgg", "cdd")
CORE = {"min1": "m_in", "mpp1": "m_pp", "mt": "m_t", "mn1": "m_n", "mnc1": "m_nc", "mpc1": "m_pc", "mpl1": "m_pl",
        "mplc1": "m_plc"}
SWQ = {"sci1": "nfet_g5v0d10v5", "sci3": "nfet_g5v0d10v5", "sisl1": "nfet_g5v0d10v5"}
BIASQ = {"mbpd": "m_bpd", "mbpds": "m_bpd", "mbnd": "m_bnd"}
NODES = ("tail", "da", "fa", "xa", "sa", "ctl", "ibn", "ibp", "ivbnc", "ivbpc", "ivbl0", "rnd")


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
          f".nodeset v(s_{x})=0 v(outp_{x})={S.V_OCM} v(outn_{x})={S.V_OCM}"]
    pc = S.SIZES["m_plc"]   # V_BL0 ratio probe: m_plc copy, gate ivbl0, drain forced to V(sa), own supply
    L += [f"Vprb_{x} vprb_{x} 0 {vd_val(x)}", f"Bdp_{x} dp_{x} 0 V = v(x{x}.sa)",
          NL.mos(f"prb_{x}", f"dp_{x}", f"ivbl0_{x}", f"vprb_{x}", f"vprb_{x}", pc["dev"], pc["WF"], pc["L"], pc["M"])]
    return L


VDD_NOW = {}


def vd_val(x):
    return VDD_NOW["v"]


def copies_for(c, t):
    cp = [(f"{m}{ld}", b, LOADS[ld], None) for m, b in (("b", False), ("f", True)) for ld in LOADS]
    return cp + [("bkp", False, LOADS["lump"], "ibn105")]   # K_P tracking copy


def mutant_copies(c, t):
    """Own deck (REVIEW-C1b M5): a mutant must not share a deck with the nominal corner copies."""
    return [(x, b, LOADS["lump"], m) for x, m, _, b in MUTANTS.get((c, t), [])]


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
        L += [f"print v(x{x}.{n})" for n in NODES] + [f"print v(outp_{x}) v(outn_{x}) v(s_{x})"]
        L += [f"print {par(x, i, S.SIZES[k]['dev'], q)}" for i, k in CORE.items() for q in DEVQ]
        L += [f"print {par(x, i, d, q)}" for i, d in SWQ.items() for q in ("cgg", "cdd")]
        L += [f"print {par(x, i, S.SIZES[k]['dev'], 'id')}" for i, k in BIASQ.items()]
        L.append(f"print @m.xprb_{x}.msky130_fd_pr__{S.SIZES['m_plc']['dev']}[id]")
    L += ["ac dec 40 1 1e10", "wrdata " + tag + "_ac.csv " + " ".join(f"v(outp_{x},outn_{x})" for x, *_ in copies),
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
            if re.search(r"(error|unknown|singular|no convergence|timestep too small|could not find)", l, re.I)]
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
    if not abs(res["V_ocm_err_mV"]) <= VOCM_MAX * 1e3:
        fails.append(f"V_OCM err {res['V_ocm_err_mV']:.1f} mV > {VOCM_MAX * 1e3:.0f}")
    res["V_rnd"], res["V_fa"] = v("rnd"), v("fa")   # sink-replica drain vs m_n drain (D59 replica fix)
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
    for kk in ("ratio_tr", "ratio_nr", "ratio_plr", "ratio_bl0"):
        if not abs(res[kk] - 1) <= RATIO_TOL:
            fails.append(f"ratio {kk} {res[kk]:.4f} (+-{RATIO_TOL:.0%})")
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
    if not res["SR_Vus"] * 1e6 >= SR_FLOOR[b]:
        fails.append(f"SR {res['SR_Vus']:.2f} V/us < {SR_FLOOR[b] / 1e6:.1f} at {C_SR * 1e12:.1f} pF")
    if not res["I_tail_uA"] * 1e-6 <= I_TAIL_CEIL * it_t:
        fails.append(f"I_tail ceiling {res['I_tail_uA']:.2f} uA > {I_TAIL_CEIL * it_t * 1e6:.2f}")
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
        return [], lint, dict(corner=tag, fails=[f"no data {e!r}"], lint=lint[:5], stderr=r.stderr[-600:])
    rows = []
    for k, (x, b, cl, mut) in enumerate(cps):
        try:
            res, fails = analyse(vals, x, b, cl, mut, ac, k, v, (c, t) in HOT)
        except Exception as e:
            res, fails = {}, [f"analysis error {e!r}"]
        if lint:
            fails.append(f"lint: {lint[:3]}")
        rows.append((x, b, cl, mut, res, fails))
    return rows, lint, None


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
            ok = len(v) == 9 and sp <= RATIO_SPREAD and (tsp <= RATIO_SPREAD)
            nf += not ok
            print(f"{'boost' if b else 'base '} {k:9s} n={len(v)} min {min(v):.4f} max {max(v):.4f} spread {sp * 100:.2f} % "
                  f"temp spread {tsp * 100:.2f} % max dev from tt {dtt * 100:.2f} % (info) {'OK' if ok else 'FAIL'}")
    print("SUMMARY", "ACCEPT" if nf == 0 else f"REJECT ({nf})")
    return nf


def main():
    if sys.argv[1] == "--summary":
        sys.exit(1 if summary(sys.argv[2]) else 0)
    out, idx = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    nfail, rows = 0, []
    rnd = lambda y: float(f"{y:.4g}") if isinstance(y, float) else ({a: rnd(z) for a, z in y.items()} if isinstance(y, dict) else y)
    for ci in idx.split(","):
        c, t, v = CORNERS9[int(ci)]
        tag = f"c1b_{c}_{t}_{v}".replace("-", "m").replace(".", "p")
        groups = [(tag, copies_for(c, t))]
        if mutant_copies(c, t):
            groups.append((tag + "_mut", mutant_copies(c, t)))
        for gtag, cps in groups:
            grows, lint, err = run_deck_group(c, t, v, gtag, cps, out)
            if err:
                print(json.dumps(err))
                nfail += 1
                continue
            kp = {x: res.get("K_P_eff", float("nan")) for x, b, cl, mut, res, fails in grows}
            for x, b, cl, mut, res, fails in grows:
                if x in TRACK:
                    dk = kp[x] / kp.get(TRACK[x], float("nan")) - 1
                    res["dKP_track_pct"] = dk * 100
                    if not abs(dk) <= KP_TRACK_TOL:
                        fails.append(f"K_P tracking {dk * 100:+.2f} % (ibn x1.05) > {KP_TRACK_TOL:.0%}")
            for x, b, cl, mut, res, fails in grows:
                mrow = {m_[0]: m_ for m_ in MUTANTS.get((c, t), [])}.get(x)
                if mrow and mrow[2] is None:
                    res["mutant_verdict"] = "helper copy (reference of a tracking pair, no verdict)"
                elif mrow:
                    target = mrow[2]
                    a0 = res.get("A0_dB", float("nan"))
                    converged = bool(not lint and res and math.isfinite(res.get("I_vdd_uA", float("nan"))))
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
