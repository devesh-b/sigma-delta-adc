#!/usr/bin/env python3
"""Tier-1 behavioural SC modulator: ngspice deck generator (WO-07 / S5).

Fully differential order-2 CIFB incremental modulator at the SPEC design point
(c1 .125, c2 .5, k .5; Cs1 .5p/Cint1 4p; Cs2 .5p/Cint2 1p; Ck .25p), built from
design/params.py. Independent of model/iadc.py. Pattern (only) from Paul Thomas's
tier1_sdm.sch.

Topology (per differential side, p shown; n mirrors):
  Stage 1  phi1: Cs1 bottom <- pad VIN, top -> cm (phi1e, opens first = bottom-plate sampling)
           phi2: Cs1 top -> OTA1 virtual ground, bottom -> VREF+ or VREF- by y (shared Cs: charge = Cs1*(Vin-Vdac))
  Stage 2  phi1: Cs2 bottom <- OTA1 output (x1[n], OTA1 holds), top -> cm
           phi2: Cs2 bottom -> cm, top -> OTA2 virtual ground; Ck (k-DAC, own cap) bottom -> +-VREF/2 by y
  OTA      B-source behavioural: gm*tanh slew limit into (Ro||Cc) single pole, hard output clamp,
           ideal CMFB (outputs symmetric about cm). inverting convention vo = -A*(vgp-vgn).
  Comparator: ideal, tracks x2 diff, latched onto a hold cap near the end of phi2; forced +1 in reset.
Loop in units of VREF: x1[n+1]=x1[n]+c1(u-y[n]); x2[n+1]=x2[n]+c2(x1[n]-k y[n]); y[n]=sgn x2[n], y[0]=+1.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import params as P  # noqa: E402

# Parts the audit expects to see in a tier-1 deck (WORKFLOW 11 item 6: ideal parts left in).
IDEAL_PARTS = ("sw switches (Ron/Roff), B-source OTA (finite A0, 1 pole, slew, clamp), "
               "B-source ideal comparator + hold cap latch, ideal sources")

DEFAULT = dict(
    fs=P.FS_NOM, n=256, nrst=3, u_list=(0.0,), vref=P.VREF_NOM, cm=P.CM,
    cs1=P.CS1, cint1=P.CINT1, cs2=P.CS2, cint2=P.CINT2, ck=P.K * P.CS2,  # separate k-DAC cap = k*Cs2 (D25) -> c2*k = Ck/Cint2
    a0_db=P.OTA_A0_DB_MIN, gbw=P.OTA_GBW_MIN, sr=12e6, vcl=1.4,
    ron=1000.0, roff=1e12, pad_r=P.PAD_R, pad_c=P.PAD_C,
    gap=12.5e-9, tdel=5e-9, cc=1e-12,
    dac_flip=False, options=None, tmax=None, extra=(),
    # --- WO-08 extensions (all default to the WO-07 deck) ---
    ota="ideal",            # "ideal" = WO-07 load-independent VCVS output; "v2" = gm into loaded output, 2nd pole, tail slew, CMFB
    boost=False,            # v2: bias-boost bit, 2x gm and 2x tail current (D31, fast mode)
    sr_asym=1.0,            # v2: negative-direction tail current = sr_asym * positive
    avdrop=0.0, vsw=2.0,    # v2: static A(v) = A0*max(0.02, 1-avdrop*(vo_diff/vsw)^2)
    cl1=P.TIER1_CL1, cl2=P.TIER1_CL2, cp_vg=None, fp2_mult=P.TIER1_FP2_MULT,
    cmfb_db=P.TIER1_CMFB_DB, cmfb_bw=P.TIER1_CMFB_BW,
    vrefp_v=None, vrefn_v=None,   # absolute reference pin voltages (default cm +- vref/2)
    vin_cm=None,            # input common mode (default cm)
    d12=False,              # top-plate shorting during sampling (D12/D25) instead of tying the top plates to cm
    dem=False,              # stage-1 Cs+/Cs- role swap every cycle (CM-error rejection variant)
    cs1_mm=0.0,             # Cs1+/Cs1- mismatch: Cs+ = Cs(1+mm/2), Cs- = Cs(1-mm/2)
    vos1=0.0, vos2=0.0, vcmp=0.0, chop=False,   # OTA input offsets [V], comparator offset [V diff], ideal OTA chop at fs/2
    noise1=0.0, noise_seed=12345,               # trnoise rms [V] at OTA1 input (per-cycle white)
    rsrc=0.0, cext=0.0,     # source resistance and pin capacitor on VIN+-
    late=False,             # input step one cycle after reset release (broken sys-chop swap)
    # --- WO-09 (S5c) extensions (all default to the WO-08 deck, except sr2/gbw2 below) ---
    sr2=None, gbw2=None,    # v2: OTA2's own SR [V/s] and GBW [Hz] (C-M1). None: sr2 = max(sr, TIER1_SR2 = 25 V/us), gbw2 = gbw
    boost1_only=False,      # v2: with boost, only OTA1 is boosted (OTA2 stays at its base bias)
    bstgm1=None, bstgm2=None,  # v2 (WO-14, C-M1): per-OTA gm boost factor, separate from the tail-current boost bst (gm scales sub-linearly with current). None: = bst
    fp2_mult1=None, fp2_mult2=None,   # WO-16: per-OTA override of fp2_mult (None = fp2_mult)
    fp2_after1=False, fp2_after2=False,   # WO-22: place the Rf/Cf second pole AFTER the tanh stage (folded-cascode style, in the current path); False = before (S5h default)
    fp2_fixed=None,         # v2 (WO-15 m3): None = second pole = fp2_mult*GBW*bstgm (tracks the boost); (g1, g2) [Hz] = hold the pole at fp2_mult*g_k, i.e. at the base gm
    bst1=None, bst2=None,   # v2: explicit per-OTA boost factor (gm and tail current x bst); None = derived from boost/boost1_only (2.0 or 1.0)
    cptop=0.0, dcptop=0.0,  # D12 floating top-plate parasitic to ground, stage 1 [F]: Cp+ = cptop + dcptop/2, Cp- = cptop - dcptop/2
    rbl=1e12, rfl=1e13,     # island bleeders: vg -> cm (0 = removed) and floating plates -> cm (0 = removed)
    ileak=0.0,              # leakage current drawn from each vg1+-/vg2+- node to ground [A] (same sign both sides: island CM drifts)
    drsrc=0.0,              # extra source R in series with VIN- (drsrc > 0) or VIN+ (drsrc < 0) [ohm]
)


def merged(cfg):
    c = dict(DEFAULT)
    c.update(cfg or {})
    if c["options"] is None:
        c["options"] = dict(P.SPICE_OPTIONS_TIER1)
    if c["tmax"] is None:
        c["tmax"] = c["options"].get("tmax_ns", 10.0) * 1e-9
        div = c["options"].get("tau_floor_div")
        if div:       # ladder floor: tmax <= tau_cl / div
            gb = min(c["gbw"], c["gbw2"] if c["gbw2"] is not None else c["gbw"])
            c["tmax"] = min(c["tmax"], 1.0 / (6.283185307179586 * P.TIER1_BETA1 * gb) / div)
    return c


def timing(c):
    T = 1.0 / c["fs"]
    blk = (c["nrst"] + c["n"]) * T
    return T, blk, [(m * blk + c["nrst"] * T) for m in range(len(c["u_list"]))]


def build_deck(cfg=None, rawfile=None):
    """Returns (deck_text, meta). meta carries t0 per conversion, T, tstop, etc."""
    c = merged(cfg)
    T, blk, t0s = timing(c)
    h, g, tdel = T / 2, c["gap"], c["tdel"]
    tstop = len(c["u_list"]) * blk
    a0 = 10 ** (c["a0_db"] / 20.0)
    cc = c["cc"]
    gm = 6.283185307179586 * c["gbw"] * cc
    ro = a0 / gm
    imax = c["sr"] * cc
    o = c["options"]
    v2 = c["ota"] == "v2"
    if (c["chop"] or c["dem"]) and ((c["nrst"] + c["n"]) % 2):
        raise ValueError("chop needs nrst+n even so the chop phase restarts with each reset")
    vinc = c["cm"] if c["vin_cm"] is None else c["vin_cm"]
    vrp = c["cm"] + c["vref"] / 2 if c["vrefp_v"] is None else c["vrefp_v"]
    vrn = c["cm"] - c["vref"] / 2 if c["vrefn_v"] is None else c["vrefn_v"]
    cp = (P.TIER1_CP_VG if v2 else 0.0) if c["cp_vg"] is None else c["cp_vg"]
    L = []
    w = L.append
    w("* tier-1 behavioural SC modulator (generated by design/tier1/gen_tier1.py) - do not edit")
    w(f".options method={o['method']} reltol={o['reltol']:g} chgtol={o['chgtol']:g} "
      f"vntol={o['vntol']:g} abstol={o['abstol']:g} trtol={o['trtol']:g}")
    w(f".model SWM SW(Vt=0.5 Vh=0.0 Ron={c['ron']:g} Roff={c['roff']:g})")
    w(f".model SWL SW(Vt=0.5 Vh=0.0 Ron=10 Roff=1e12)")
    w(f".param cm={c['cm']:g} vref={c['vref']:g}")
    w("Vcm cm 0 {cm}")
    # clock phases (per-cycle PULSE; period T)
    tr = 0.5e-9

    def pulse(name, td, pw):
        w(f"V{name} {name} 0 PULSE(0 1 {td:.6e} {tr:.3e} {tr:.3e} {pw:.6e} {T:.6e})")
    pulse("phi1", g, h - 2 * g)
    pulse("phi1e", g, h - 2 * g - tdel)
    pulse("phi2", h + g, h - 2 * g)
    pulse("phl", T - g + 2e-9, g - 3.5e-9)   # latch closes after phi2 ends, opens before rst edge / next phi1
    w(f"Vrst rst 0 PULSE(1 0 {c['nrst'] * T:.6e} 0.1n 0.1n {c['n'] * T:.6e} {blk:.6e})")
    # inputs: differential u*VREF/2 about cm, PWL step in the first reset cycle of each block
    pts_p, pts_n = [], []
    for pts, sgn in ((pts_p, +1), (pts_n, -1)):
        us = c["u_list"]
        pts.append((0.0, vinc + sgn * us[0] * c["vref"] / 2))
        late = (c["nrst"] + 1) * T if c["late"] else 0.0
        for m in range(1, len(us)):
            pts.append((m * blk + 0.1 * T + late, vinc + sgn * us[m - 1] * c["vref"] / 2))
            pts.append((m * blk + 0.2 * T + late, vinc + sgn * us[m] * c["vref"] / 2))
    def pwl(pts):
        return " ".join(f"{t:.6e} {v:.9f}" for t, v in pts)
    w(f"Vinp_s vinp_s 0 PWL({pwl(pts_p)})")
    w(f"Vinn_s vinn_s 0 PWL({pwl(pts_n)})")
    w(f"Vrefp_s vrefp_s 0 {vrp:.9g}")
    w(f"Vrefn_s vrefn_s 0 {vrn:.9g}")
    for nm in ("vinp", "vinn", "vrefp", "vrefn"):
        src = f"{nm}_s"
        rs_ = c["rsrc"] + (max(c["drsrc"], 0.0) if nm == "vinn" else max(-c["drsrc"], 0.0) if nm == "vinp" else 0.0)
        if rs_ and nm.startswith("vin"):
            w(f"Rsrc_{nm} {nm}_s {nm}_pin {rs_:g}")
            src = f"{nm}_pin"
            if c["cext"]:
                w(f"Cext_{nm} {nm}_pin 0 {c['cext']:g}")
        w(f"Rpad_{nm} {src} {nm} {c['pad_r']:g}")
        w(f"Cpad_{nm} {nm} 0 {c['pad_c']:g}")
    if c["chop"] or c["dem"]:
        w(f"Vchp chp 0 PULSE(-1 1 {c['nrst'] * T:.6e} 0.5n 0.5n {T - 1e-9:.6e} {2 * T:.6e})")
    noise_e = None
    if c["noise1"]:
        # per-cycle white gaussian noise as a deterministic PWL (ngspice trnoise aborts with "timestep too small" here)
        import numpy as _np
        ncyc = len(c["u_list"]) * (c["nrst"] + c["n"])
        gv = _np.random.default_rng(c["noise_seed"]).standard_normal(ncyc) * c["noise1"]
        pts = []
        for gi, v in enumerate(gv):
            pts.append(f"{gi * T + 1e-9:.9e} {v:.6e} {(gi + 1) * T:.9e} {v:.6e}")
        w("Vnz1 nz1 0 PWL(" + "\n+ ".join(pts) + ")")
        noise_e = gv.reshape(len(c["u_list"]), c["nrst"] + c["n"])[:, c["nrst"]:]
    if c["dem"]:
        w("BcA cA 0 V = u(V(chp))")
        w("BcB cB 0 V = 1-u(V(chp))")
        for nm, a in (("g1", "phi1"), ("g2", "phi2"), ("gdh", "cdph"), ("gdl", "cdpl")):
            w(f"B{nm}A {nm}A 0 V = V({a})*V(cA)")
            w(f"B{nm}B {nm}B 0 V = V({a})*V(cB)")
    # DAC steering controls (y held on yq; +-1)
    pol = (lambda a, b: (b, a)) if c["dac_flip"] else (lambda a, b: (a, b))
    w("Bypos ypos 0 V = u(V(yq))")
    w("Byneg yneg 0 V = 1-u(V(yq))")
    sel_p, sel_n = pol("ypos", "yneg")
    w(f"Bd_p_hi cdph 0 V = V(phi2)*V({sel_p})")
    w(f"Bd_p_lo cdpl 0 V = V(phi2)*V({sel_n})")
    # stage 1 / stage 2 switched-capacitor network
    d12, dem = c["d12"], c["dem"]
    mm = c["cs1_mm"]
    for s, side in (("p", "p"), ("n", "n")):
        hi, lo = ("vrefp", "vrefn") if s == "p" else ("vrefn", "vrefp")
        # stage 1 (cap s; with dem the cap also runs as the opposite side on odd cycles)
        cs1v = c["cs1"] * (1 + mm / 2 if s == "p" else 1 - mm / 2)
        modes = [("", s, "phi1", "phi2", "cdph", "cdpl")]
        if dem:
            o_ = "n" if s == "p" else "p"
            modes = [("A", s, "g1A", "g2A", "gdhA", "gdlA"), ("B", o_, "g1B", "g2B", "gdhB", "gdlB")]
        for tag, se, g1, g2, gh, gl in modes:
            hi_, lo_ = ("vrefp", "vrefn") if se == "p" else ("vrefn", "vrefp")
            w(f"Sin1{s}{tag} vin{se} b1{s} {g1} 0 SWM")
            w(f"Sdh1{s}{tag} b1{s} {hi_} {gh} 0 SWM")
            w(f"Sdl1{s}{tag} b1{s} {lo_} {gl} 0 SWM")
            w(f"Sg1{s}{tag} tp1{s} vg1{se} {g2} 0 SWM")
        if not d12:
            w(f"Stp1{s} tp1{s} cm phi1e 0 SWM")
        w(f"Cs1{s} b1{s} tp1{s} {cs1v:g}")
        w(f"Cint1{s} vg1{s} o1{s} {c['cint1']:g}")
        w(f"Srst1{s} vg1{s} o1{s} rst 0 SWM")
        if c["rbl"]:
            w(f"Rbl1{s} vg1{s} cm {c['rbl']:g}")
        if cp:
            w(f"Cpv1{s} vg1{s} 0 {cp:g}")
            w(f"Cpv2{s} vg2{s} 0 {cp:g}")
        for nd in (f"b1{s}", f"tp1{s}", f"b2{s}", f"tp2{s}", f"bk{s}"):
            if c["rfl"]:
                w(f"Rfl_{nd} {nd} cm {c['rfl']:g}")   # DC path for floating plates (gmin-level, ~0.04 ppm effect)
        # stage 2
        w(f"S2in{s} o1{s} b2{s} phi1 0 SWM")
        w(f"S2cm{s} b2{s} cm phi2 0 SWM")
        if not d12:
            w(f"Stp2{s} tp2{s} cm phi1e 0 SWM")
        w(f"Sg2{s} tp2{s} vg2{s} phi2 0 SWM")
        w(f"Cs2{s} b2{s} tp2{s} {c['cs2']:g}")
        w(f"Sk0{s} bk{s} cm phi1 0 SWM")
        w(f"Skh{s} bk{s} {hi} cdph 0 SWM")
        w(f"Skl{s} bk{s} {lo} cdpl 0 SWM")
        w(f"Ck{s} bk{s} tp2{s} {c['ck']:g}")
        w(f"Cint2{s} vg2{s} o2{s} {c['cint2']:g}")
        w(f"Srst2{s} vg2{s} o2{s} rst 0 SWM")
        if c["rbl"]:
            w(f"Rbl2{s} vg2{s} cm {c['rbl']:g}")
        if c["ileak"]:
            w(f"Blk1{s} vg1{s} 0 I = {c['ileak']:.6e}")
            w(f"Blk2{s} vg2{s} 0 I = {c['ileak']:.6e}")
        if c["cptop"] or c["dcptop"]:
            cpt = c["cptop"] + (c["dcptop"] / 2 if s == "p" else -c["dcptop"] / 2)
            w(f"Cptop1{s} tp1{s} 0 {cpt:.6e}")
    if d12:
        w("Stp1d tp1p tp1n phi1e 0 SWM")   # D12: top plates shorted (floating) during sampling
        w("Stp2d tp2p tp2n phi1e 0 SWM")
    # behavioural OTAs
    def vd_expr(k):
        e = f"V(vg{k}p)-V(vg{k}n)"
        vos = c["vos1"] if k == 1 else c["vos2"]
        if vos:
            # ramp the offset in over the first microsecond (reset phase): a 9 mV step at the 180 dB open-loop DC point makes the DC op fail
            e += f"+{vos:.9g}*min(1,time*1e6)" + ("*V(chp)" if c["chop"] else "")
        if k == 1 and c["noise1"]:
            e += "+V(nz1)"
        return e
    for k in (1, 2):
        if not v2:
            w(f"Bgm{k} 0 int{k} I = -{imax:.9e}*tanh({gm:.9e}*({vd_expr(k)})/{imax:.9e})")
            w(f"Ro{k} int{k} 0 {ro:.9e}")
            w(f"Cc{k} int{k} 0 {cc:g}")
            w(f"Bo{k}p o{k}p 0 V = {{cm}}+0.5*max(-{c['vcl']:g},min({c['vcl']:g},V(int{k})))")
            w(f"Bo{k}n o{k}n 0 V = {{cm}}-0.5*max(-{c['vcl']:g},min({c['vcl']:g},V(int{k})))")
            continue
        # v2: gm into loaded output nodes. C_L is the loaded value (output parasitic + feedback network) at the spec load.
        cl = c["cl1"] if k == 1 else c["cl2"]
        cin = c["cs1"] if k == 1 else (c["cs2"] + c["ck"])
        cint = c["cint1"] if k == 1 else c["cint2"]
        net = cint * (cin + cp) / (cint + cin + cp)
        cpo = max(cl - net, 0.05e-12)
        bst = 2.0 if (c["boost"] and not (c["boost1_only"] and k == 2)) else 1.0
        if c["bst%d" % k] is not None:
            bst = float(c["bst%d" % k])
        gbw_k = c["gbw"] if (k == 1 or c["gbw2"] is None) else c["gbw2"]
        sr_k = c["sr"] if k == 1 else (c["sr2"] if c["sr2"] is not None else max(c["sr"], P.TIER1_SR2))
        bstgm = bst if c["bstgm%d" % k] is None else float(c["bstgm%d" % k])
        gmk = bstgm * 6.283185307179586 * gbw_k * cl
        ip = bst * sr_k * cl                       # diff SR = I_tail / C_side
        im = ip * c["sr_asym"]
        g0 = gmk / a0
        fpm = c["fp2_mult"] if c["fp2_mult%d" % k] is None else float(c["fp2_mult%d" % k])
        if c["fp2_fixed"] is None:
            cf = 1.0 / (6.283185307179586 * fpm * gbw_k * bstgm * 1e3)
        else:
            cf = 1.0 / (6.283185307179586 * fpm * float(c["fp2_fixed"][k - 1]) * 1e3)
        gcm = 6.283185307179586 * c["cmfb_bw"] * cl
        gtot = gcm * (1.0 + 10 ** (-c["cmfb_db"] / 20.0))
        w(f"Bdr{k} dr{k} 0 V = {vd_expr(k)}")
        if c["fp2_after%d" % k]:
            # pole after the tanh: unit-gain current lowpass (1k, Cf) on the tanh output current
            x = f"{gmk:.9e}*V(dr{k})"
            idx = (f"(u({x})*{ip:.9e}*tanh(({x})/{ip:.9e})+(1-u({x}))*{im:.9e}*tanh(({x})/{im:.9e}))")
            w(f"Bq{k} 0 f{k} I = {idx}")
            w(f"Rf{k} f{k} 0 1k")
            w(f"Cf{k} f{k} 0 {cf:.6e}")
            idx = f"V(f{k})/1k"
        else:
            w(f"Rf{k} dr{k} f{k} 1k")
            w(f"Cf{k} f{k} 0 {cf:.6e}")
            x = f"{gmk:.9e}*V(f{k})"
            idx = (f"(u({x})*{ip:.9e}*tanh(({x})/{ip:.9e})+(1-u({x}))*{im:.9e}*tanh(({x})/{im:.9e}))")
        w(f"Bgp{k} 0 o{k}p I = -0.5*{idx}")
        w(f"Bgn{k} 0 o{k}n I = 0.5*{idx}")
        vo = f"(V(o{k}p)-V(o{k}n))"
        fa = f"max(0.02,1-{c['avdrop']:.6g}*({vo}/{c['vsw']:.6g})^2)" if c["avdrop"] else "1"
        w(f"Bro{k}p o{k}p 0 I = 0.5*{vo}*{g0:.9e}/({fa})")
        w(f"Bro{k}n o{k}n 0 I = -0.5*{vo}*{g0:.9e}/({fa})")
        w(f"Bcm{k}p o{k}p 0 I = {gtot:.9e}*(0.5*(V(o{k}p)+V(o{k}n))-{{cm}})")
        w(f"Bcm{k}n o{k}n 0 I = {gtot:.9e}*(0.5*(V(o{k}p)+V(o{k}n))-{{cm}})")
        w(f"Cpo{k}p o{k}p 0 {cpo:.6e}")
        w(f"Cpo{k}n o{k}n 0 {cpo:.6e}")
        if c["vcl"] < 100:
            gcl = 5e-3
            w(f"Bcl{k}p o{k}p 0 I = 0.5*{gcl}*(max({vo}-{c['vcl']:g},0)+min({vo}+{c['vcl']:g},0))")
            w(f"Bcl{k}n o{k}n 0 I = -0.5*{gcl}*(max({vo}-{c['vcl']:g},0)+min({vo}+{c['vcl']:g},0))")
    # comparator + latch (forced +1 in reset)
    w("Bx2d x2d 0 V = V(o2p)-V(o2n)")
    w(f"Bcmp cmpo 0 V = V(rst)+(1-V(rst))*(2*u(V(x2d)-{c['vcmp']:.9g}-1e-12)-1)")
    w("Slat cmpo yq phl 0 SWL")
    w("Chold yq 0 1p")
    w(".ic v(yq)=1")
    w(f".tran 1n {tstop:.9e} 0 {c['tmax']:.6e}")
    w(".save v(yq) v(o2p) v(o2n) v(o1p) v(o1n) " + " ".join(f"v({x})" for x in c["extra"]))
    w(".control")
    w("set wr_singlescale")
    w("set wr_vecnames")
    w("listing")
    w("run")
    w("echo FINAL_TIME_CHECK")
    w("print time[length(time)-1]")
    w(f"wrdata {rawfile or 'out.csv'} v(yq) v(o2p) v(o2n) v(o1p) v(o1n) " + " ".join(f"v({x})" for x in c["extra"]))
    w("quit")
    w(".endc")
    w(".end")
    meta = dict(T=T, blk=blk, t0=t0s, tstop=tstop, n=c["n"], nrst=c["nrst"], gm=gm, ro=ro, imax=imax,
                a0=a0, noise_e=noise_e, cfg={k: v for k, v in c.items() if k != "options"}, options=dict(o))
    return "\n".join(L) + "\n", meta


if __name__ == "__main__":
    txt, meta = build_deck({"u_list": (0.3,), "n": 16})
    sys.stdout.write(txt)
