#!/usr/bin/env python3
"""C1b tb9: CMFB loop transient on the NETLISTED OTA1 with the real SC CMFB (D61 dual path). Sandbox only:
    python c1b_tb9.py OUTDIR CORNER_IDXS [--mut]        # CORNER_IDXS into revc_check.CORNERS9; --mut: broken-copy deck

WO-30 rows (D63 basis; expected values from SPEC row 98 / D63 / CL-2 / CL-7 / SPEC sec. 3 loop bound, not from this code):
  Sampling instants t_k = end of each half-phase (0.5 ns before the ph1 / ph2 falling edge). The integrator charge is taken
  in ph1 (OTA1 integrate) and x1 is sampled by Cs2 in ph2 (OTA1 hold, D25), so both half-phase ends are sampling instants.
  * Event rows (gate): for each event, every t_k from the end of the first ph1 that starts after the event up to the next
    event: |V_cm(t_k) - V_cm,ss(phase of t_k)| <= 10 mV. V_cm,ss = the settled per-phase CM (mean of the last two ends of
    that phase in the run). The 22.5 ns (0.2 t_half) error is kept as info.
  * Static CM rows (gate): |V_cm,ss(ph2) - V_OCM| <= 10 mV (the instant Cs2 samples x1); |V_cm,ss(ph1) - V_OCM| <= 28 mV
    (headroom: CL-2 V_OCM bound 38 mV minus the 10 mV static V_OCM allotment of the op/AC row). The end-ph1 offset is a
    charge packet on ctl (CMFB share switch opening, divided by 2 Cc: WO-30 item 2).
  * CM-to-DM row (gate): twin copies in the same deck, ev (with the CM step) and ev0 (identical, no CM step), both at the
    DM operating point left by the diff step. dDM(t_k) = V_dm,ev - V_dm,ev0 at every ph2 end from the first judged instant
    after the CM step to reset assert. Bound (S-model, model/iadc.py): an error d [V diff] on x1 enters the estimate as an
    input error d / (c1 VREF) (x1 is in VREF units; u_hat weights a one-sample x1 error by (N - k)/W, summing to 1 when it
    recurs every sample). INL is in ppm of FSR = 2, so a fully signal-dependent per-sample error gives
    INL = d / (2 c1 VREF). Limit = 0.1 x the OTA1 boost INL share (5 ppm, SPEC OTA1 GBW row (B)):
    d <= 0.1 * 5e-6 * 2 * 0.125 * 2.048 V = 0.256 uV per CM-step event (worst case: the CM step treated as recurring every
    cycle with full signal dependence). The pre-step twin difference is the numerical floor (must be <= limit / 10).
  * Diff step = the real worst per-cycle step, c1 (u_max + 1) VREF = 0.486 V diff (SPEC OTA1 GBW row; loop bound), as a
    10 ns charge pulse at the period start. The WO-27..29 0.8 V step overstated the per-cycle charge by 1.65x and was still
    slewing at +22.5 ns; at the sampling instants slewing has ended. TB9_DV_DIFF overrides (info runs).
  * Start-up (gate): outputs pre-charged to VDD / 0, integrator held in reset, start-up clamp (rstb low: ctl, bli -> V_BL0,
    outputs -> V_OCM) held 8 T (= 2 us at 4 MHz; D57: the clamp is held while rst_n is low or the bias is invalid, and
    power-up bias settling alone is >= CL-7 4 us, so 8 T is a conservative minimum); |V_cm - V_OCM| <= 10 mV over the last
    clock period before 4 us. Copies with the old 2 T clamp and a Cr x 2 copy run as info (WO-30 item 2 evidence).
  Events start at 3.0 us (2.5 us after the 2 T clamp release of the ev copies; the Cc charge mode decays with
  tau = T Cc / Cr ~ 1.1 us, WO-30), run to 5.5 us.
Broken copies (own deck, each must REJECT on the stated row): mcc4 = Cc / 4 (any row; the ph1 static row: the charge
packet / 2 Cc grows 4x), masy = 1e-4 of the CM-step charge onto one island (CM-to-DM row), mio = int_off + vbl0x2 (start-up).
Setup per copy: OTA1 (cmfb="sc", boost, fs 4 MHz, ph1 / ph2 non-overlapping by g = 0.025/fs), Cint 4 pF out -> island
(negative feedback, WO-29), Cs1 0.5 pF island -> ground, output routing C_RT; reset = island shunt to V_ICM (isl) + ideal
output short (gen_tier1 style); chopper static.
"""
import json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..")]
import numpy as np  # noqa: E402
import sizes_draft as S  # noqa: E402
import netlist as NL  # noqa: E402
from revc_check import CORNERS9, LIB  # noqa: E402
from c1b_opac import LOADS, C_RT  # noqa: E402

FS = 4e6
T, G = 1 / FS, 0.025 / FS
T_HALF = 0.5 / FS - 2 * G
T_SET, TOL = 0.2 * T_HALF, 10e-3
TOL_PH1 = 28e-3                     # CL-2 38 mV - 10 mV static V_OCM allotment
CINT, CS1 = 4e-12, 0.5e-12
C1, VREF, U_MAX = 0.125, 2.048, 0.9
DV_CM = 30e-3
DV_DIFF = float(os.environ.get("TB9_DV_DIFF", C1 * (U_MAX + 1) * VREF))   # 0.486 V, real worst per-cycle step
INL_SHARE = 5e-6                    # OTA1 boost INL gate (SPEC OTA1 GBW row (B))
LIM_CMDM = 0.1 * INL_SHARE * 2 * C1 * VREF   # 0.256 uV
ASYM = 1e-4                         # masy broken copy: CM-step charge imbalance n/p
T_STOP = 4.0e-6                     # CL-7 (start-up rows)
T_RST = 216e-9                      # reset window at 4 MHz (CHOP_SW island row)
N_CLAMP, N_CLAMP_SU = 2, 8          # rstb low: ev copies / start-up gate copies
T0 = 3.0e-6
EV = [("reset release", T0), ("diff step", T0 + T), ("CM step", T0 + 3 * T), ("reset assert", T0 + 6 * T),
      ("reset release 2", T0 + 6 * T + T_RST)]
T_EVSTOP = T0 + 10 * T
DIAG = os.environ.get("TB9_DIAG", "")                       # diagnosis copies "x:tok+tok,x:-" (ev kind, no rows)
TSTOP_RUN = float(os.environ.get("TB9_TSTOP", T_EVSTOP))
DIAG_VEC = bool(DIAG) or bool(os.environ.get("TB9_VEC"))    # also log ctl / bli
# kinds: ev, ev0 (twin without CM step), su_hi / su_lo (+ "8": 8 T clamp). info copies are reported, not gated.
NOM = [("ev", "ev", None), ("ev0", "ev0", None), ("suhi", "su_hi8", None), ("sulo", "su_lo8", None),
       ("suvb", "su_lo8", "vbl0x2"), ("sulo2t", "su_lo", None), ("suvb2t", "su_lo", "vbl0x2"), ("sulocr2", "su_lo", "cr_x2")]
if os.environ.get("TB9_SET") == "cr2":   # WO-30 candidate (option, not adopted): Cr x 2 everywhere, 2 T start-up clamp
    NOM = [("ev", "ev", "cr_x2"), ("ev0", "ev0", "cr_x2"), ("suhi", "su_hi", "cr_x2"), ("sulo", "su_lo", "cr_x2"),
           ("suvb", "su_lo", "vbl0x2+cr_x2")]
INFO = {"ev0", "sulo2t", "suvb2t", "sulocr2", "masy0"}
MUT = [("mcc4", "ev", "cc_div4"), ("masy", "ev", "cm_asym"), ("masy0", "ev0", None), ("mio", "su_hi8", "int_off+vbl0x2")]
EXPECT = {"mcc4": "", "masy": "CM-to-DM", "mio": "start-up"}
TWIN = {"ev": "ev0", "masy": "masy0"}


def copy(x, kind, sub, vd, mut=None):
    rst = "rstb8" if kind.endswith("8") else "rstb"
    L = [f"X{x} vdd 0 inp_{x} inn_{x} outp_{x} outn_{x} vicm vocm ibtp_{x} ibn_{x} ibp_{x} ivbnc_{x} ivbpc_{x} ivbl0_{x} "
         f"vdd 0 lv 0 isl_{x} ph1 ph1b ph2 ph2b {rst} {sub}"]
    for p_, i_ in NL.bias_currents(True, mut).items():
        L.append(f"I{p_}_{x} {p_}_{x} 0 {i_:.6e}" if p_ in NL.SINK_PORTS else f"I{p_}_{x} vdd {p_}_{x} {i_:.6e}")
    # WO-29: Cint closes NEGATIVE feedback, outp -> inn and outn -> inp (gen_tier1). TB9_POL_OLD=1: old positive wiring.
    a_, b_ = ("inp", "inn") if os.environ.get("TB9_POL_OLD") else ("inn", "inp")
    L += [f"Cip_{x} outp_{x} {a_}_{x} {CINT:g}", f"Cin_{x} outn_{x} {b_}_{x} {CINT:g}",
          f"Csp_{x} inp_{x} 0 {CS1:g}", f"Csn_{x} inn_{x} 0 {CS1:g}",
          f"Crp_{x} outp_{x} 0 {C_RT:g}", f"Crn_{x} outn_{x} 0 {C_RT:g}",
          f"Bcm_{x} cm_{x} 0 V = 0.5*(V(outp_{x})+V(outn_{x}))"]
    if kind in ("ev", "ev0"):
        L += [f"Bisl_{x} isl_{x} 0 V = {vd:g}*V(rsw)", f"Srs_{x} outp_{x} outn_{x} rsw 0 SWM"]
        qd, qc = DV_DIFF / 2 * CINT, DV_CM * LOADS["integ"]
        t1, t2 = EV[1][1], EV[2][1]
        L += [f"Idp_{x} 0 inp_{x} PULSE(0 {qd / 10e-9:.6e} {t1:.6e} 0.1n 0.1n 9.9n 1)",
              f"Idn_{x} inn_{x} 0 PULSE(0 {qd / 10e-9:.6e} {t1:.6e} 0.1n 0.1n 9.9n 1)"]
        if kind == "ev":
            L += [f"Icp_{x} 0 outp_{x} PULSE(0 {qc / 1e-9:.9e} {t2:.6e} 0.1n 0.1n 0.9n 1)",
                  f"Icn_{x} 0 outn_{x} PULSE(0 {qc / 1e-9:.9e} {t2:.6e} 0.1n 0.1n 0.9n 1)"]
            if "cm_asym" in NL.toks(mut):
                # WO-30 run 1: an n/p imbalance of the OUTPUT charge left no DM at the sampling instants (masy PASSED,
                # 0.01 uV): the DM output is set by the island charge, and output-side charge settles out. A CM event
                # leaks to DM only as island charge, so the broken copy puts ASYM x the CM-step charge on one island
                # (DM ~ ASYM qc / Cint = 0.58 uV, 2.3x the limit)
                L += [f"Ica_{x} 0 inp_{x} PULSE(0 {ASYM * qc / 1e-9:.9e} {t2:.6e} 0.1n 0.1n 0.9n 1)"]
    else:   # start-up copy: integrator held in reset, outputs pre-charged to a rail
        rail = vd if kind.startswith("su_hi") else 0.0
        L += [f"Visl_{x} isl_{x} 0 {vd:g}", f"Srs_{x} outp_{x} outn_{x} one 0 SWM",
              f".ic v(outp_{x})={rail:g} v(outn_{x})={rail:g}"]
    return L


def deck(c, t, vd, tag, copies):
    L = [f"* WO-30 c1b_tb9 {tag}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-15 reltol=1e-4",
         f"Vdd vdd 0 {vd}", f"Vicm vicm 0 {S.V_ICM}", f"Vocm vocm 0 {S.V_OCM}", "Vlv lv 0 1.8", "Vone one 0 1",
         ".model SWM sw vt=0.5 vh=0.1 ron=100 roff=1e12",
         f"Vrsw rsw 0 PWL(0 1 {EV[0][1]:.6e} 1 {EV[0][1] + 1e-9:.6e} 0 {EV[3][1]:.6e} 0 {EV[3][1] + 1e-9:.6e} 1 "
         f"{EV[4][1]:.6e} 1 {EV[4][1] + 1e-9:.6e} 0)",
         f"Vrstb rstb 0 PWL(0 0 {N_CLAMP * T:.6e} 0 {N_CLAMP * T + 1e-9:.6e} {vd:g})",
         f"Vrstb8 rstb8 0 PWL(0 0 {N_CLAMP_SU * T:.6e} 0 {N_CLAMP_SU * T + 1e-9:.6e} {vd:g})",
         f"Vph1 ph1 0 PULSE(0 {vd:g} {G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         f"Vph1b ph1b 0 PULSE({vd:g} 0 {G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         f"Vph2 ph2 0 PULSE(0 {vd:g} {T / 2 + G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         f"Vph2b ph2b 0 PULSE({vd:g} 0 {T / 2 + G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         ".model SWI sw vt=1.5 vh=0.1 ron=2k roff=1e14"]   # WO-29 diagnosis: ideal CMFB switches (sw_ideal*)
    subs = {}
    for x, kind, mut in copies:
        tk = NL.toks(mut) - {"cm_asym"}
        key = "+".join(sorted(tk)) or None
        if key not in subs:
            subs[key] = f"ota1_t9_{(key or 'nom').replace('+', '_')}"
            m2 = "+".join(sorted(tk - {"dcavg"})) or None   # dcavg: averaged Cr model (op/AC) in the same transient
            L.append(NL.build(subs[key], cmfb="dc" if "dcavg" in tk else "sc", fs=FS, mut=m2, boost=True))
        L += copy(x, kind, subs[key], vd, mut)
    vec = vecs(copies)
    L += [".control", "set wr_singlescale", "set wr_vecnames", f"tran 0.1n {TSTOP_RUN:.6e} 0 0.5n",
          f"wrdata {tag}.csv {' '.join(v for _, v in vec)}", "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def vecs(copies):
    """[(name, ngspice vector)]: cm of every copy, V_dm of ev-kind copies, ctl / bli with DIAG_VEC."""
    out = [(f"{x}_cm", f"v(cm_{x})") for x, *_ in copies]
    out += [(f"{x}_dm", f"v(outp_{x},outn_{x})") for x, k, _ in copies if k in ("ev", "ev0")]
    if DIAG_VEC:
        out += [(f"{x}_{q}", f"v(x{x}.{q})") for x, *_ in copies for q in ("ctl", "bli")]
    return out


def instants(tstop):
    """Sampling instants (time, phase, ph1-start of that period), sorted."""
    k = np.arange(int(round(tstop / T)))
    t = np.concatenate([k * T + T / 2 - G - 0.5e-9, k * T + T - G - 0.5e-9])
    ph = np.concatenate([np.ones(len(k), int), 2 * np.ones(len(k), int)])
    o = np.argsort(t)
    return t[o], ph[o]


def first_judged(te):
    """End of the first ph1 (integrate) that starts after the event."""
    k0 = math.ceil((te - G) / T - 1e-9)
    return k0 * T + T / 2 - G - 0.5e-9


def check_ev(tm, cm, dm=None, dm0=None):
    ts, ph = instants(TSTOP_RUN)
    v = np.interp(ts, tm, cm)
    ss = {p: float(np.mean(v[ph == p][-2:])) for p in (1, 2)}
    rows, fails = [], []
    for j, (nm, te) in enumerate(EV):
        tn = EV[j + 1][1] if j + 1 < len(EV) else TSTOP_RUN
        sel = (ts >= first_judged(te) - 1e-12) & (ts < tn)
        e = np.array([v[i] - ss[ph[i]] for i in np.nonzero(sel)[0]])
        err = float(np.max(np.abs(e))) if len(e) else float("nan")
        # info: WO-29 metric (max |cm - mean of last period before the next event| after 0.2 t_half)
        w = (tm >= te + T_SET) & (tm < tn)
        rw = (tm >= tn - min(T, (tn - te) / 2)) & (tm < tn)
        e22 = float(np.max(np.abs(cm[w] - np.mean(cm[rw]))))
        rows.append(dict(event=nm, n_inst=int(sel.sum()), err_sampling_mV=round(err * 1e3, 3),
                         err_first_inst_mV=round(float(e[0]) * 1e3, 3) if len(e) else None, info_err_22ns_mV=round(e22 * 1e3, 2)))
        if not err <= TOL:
            fails.append(f"{nm}: {err * 1e3:.2f} mV > {TOL * 1e3:.0f} mV at the sampling instants")
    st = dict(cm_ss_ph1_mV=round((ss[1] - S.V_OCM) * 1e3, 3), cm_ss_ph2_mV=round((ss[2] - S.V_OCM) * 1e3, 3))
    if not abs(ss[2] - S.V_OCM) <= TOL:
        fails.append(f"static ph2: {st['cm_ss_ph2_mV']} mV > {TOL * 1e3:.0f} mV")
    if not abs(ss[1] - S.V_OCM) <= TOL_PH1:
        fails.append(f"static ph1: {st['cm_ss_ph1_mV']} mV > {TOL_PH1 * 1e3:.0f} mV")
    if dm is not None and dm0 is not None:
        d = np.interp(ts, tm, dm) - np.interp(ts, tm, dm0)
        s_ = (ph == 2) & (ts >= first_judged(EV[2][1]) - 1e-12) & (ts < EV[3][1])
        f_ = (ph == 2) & (ts >= first_judged(EV[1][1]) - 1e-12) & (ts < EV[2][1])
        dmax, floor = float(np.max(np.abs(d[s_]))), float(np.max(np.abs(d[f_])))
        st.update(cmdm_uV=round(dmax * 1e6, 4), cmdm_floor_uV=round(floor * 1e6, 4), cmdm_limit_uV=round(LIM_CMDM * 1e6, 4),
                  cmdm_first_uV=round(float(d[s_][0]) * 1e6, 4))
        if not dmax <= LIM_CMDM:
            fails.append(f"CM-to-DM: {dmax * 1e6:.4f} uV > {LIM_CMDM * 1e6:.3f} uV")
        if not floor <= LIM_CMDM / 10:
            fails.append(f"CM-to-DM floor {floor * 1e6:.4f} uV > limit/10 (row invalid)")
    return dict(events=rows, **st), fails


def check_su(tm, cm):
    w = (tm >= T_STOP - T) & (tm < T_STOP)
    err = float(np.max(np.abs(cm[w] - S.V_OCM)))
    out = np.nonzero(np.abs(cm - S.V_OCM) > TOL)[0]
    t_in = float(tm[out[-1] + 1]) if len(out) and out[-1] + 1 < len(tm) else float("nan")
    return (dict(err_last_T_mV=round(err * 1e3, 3), t_enter_band_us=round(t_in * 1e6, 3)),
            [] if err <= TOL else [f"start-up {err * 1e3:.2f} mV"])


def main():
    out, idx, mut_deck = sys.argv[1], sys.argv[2], "--mut" in sys.argv
    os.makedirs(out, exist_ok=True)
    nfail, rows = 0, []
    for ci in idx.split(","):
        c, t, vd = CORNERS9[int(ci)]
        tag = f"tb9_{c}_{t}".replace("-", "m") + ("_mut" if mut_deck else "")
        cps = list(MUT if mut_deck else NOM)
        if DIAG:
            tag += "_diag"
            cps = [(s.split(":")[0], "ev", None if s.split(":")[1] == "-" else s.split(":")[1]) for s in DIAG.split(",")]
        fn = os.path.join(out, tag + ".csv")
        if os.path.exists(fn):
            os.remove(fn)
        open(os.path.join(out, tag + ".sp"), "w").write(deck(c, t, vd, tag, cps))
        r = subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=7000)
        lint = [l.strip() for l in (r.stdout + r.stderr).splitlines()
                if re.search(r"(error|unknown|singular|no convergence|timestep too small|could not find)", l, re.I)]
        names = [n for n, _ in vecs(cps)]
        try:
            a = np.loadtxt(fn, skiprows=1)
            col = {n: a[:, 1 + i] for i, n in enumerate(names)}
            ts, ph = instants(TSTOP_RUN)
            np.savetxt(os.path.join(out, tag + "_phase.txt"),
                       np.column_stack([ts, ph] + [np.interp(ts, a[:, 0], col[n]) for n in names]), fmt="%.9g",
                       header="t ph " + " ".join(names))
            os.remove(fn)
        except Exception as e:
            print(json.dumps(dict(corner=tag, fails=[f"no data {e!r}"], lint=lint[:5], stderr=r.stderr[-600:])))
            nfail += 1
            continue
        tm = a[:, 0]
        if DIAG:   # per copy: settled end-ph1 / end-ph2 CM before the first event and the ph1 - ph2 ripple
            pre = (ts < T0) & (ts >= T0 - 2 * T)
            d = {x: {f"cm_ph{p}_mV": round((float(np.mean(np.interp(ts[pre & (ph == p)], tm, col[x + "_cm"]))) - S.V_OCM) * 1e3, 3)
                     for p in (1, 2)} for x, *_ in cps}
            print(json.dumps(dict(diag=tag, **d)), flush=True)
            json.dump(d, open(os.path.join(out, tag + "_diag.json"), "w"), indent=0)
            continue
        for x, kind, m in cps:
            cm = col[x + "_cm"]
            if kind == "ev0":
                continue
            if kind == "ev":
                tw = TWIN.get(x)
                res, fails = check_ev(tm, cm, col.get(x + "_dm"), col.get(f"{tw}_dm") if tw else None)
            else:
                res, fails = check_su(tm, cm)
            row = dict(corner=c, temp=t, vdd=vd, copy=x, mut=m, info=x in INFO, result=res,
                       fails=fails + ([f"lint {lint[:3]}"] if lint else []))
            if mut_deck:
                ok = not lint and np.all(np.isfinite(cm))
                hit = [f for f in fails if EXPECT[x] in f]
                row["mutant_verdict"] = ("REJECTED (good)" if ok and hit else "PASSED (check is blind)" if ok
                                         else "MUTANT INVALID")
                nfail += row["mutant_verdict"] != "REJECTED (good)"
            elif not row["info"]:
                nfail += bool(row["fails"])
            rows.append(row)
            print(json.dumps(row), flush=True)
    json.dump(rows, open(os.path.join(out, f"tb9_{idx.replace(',', '_')}{'_mut' if mut_deck else ''}.json"), "w"), indent=0)
    print("VERDICT", "ACCEPT" if nfail == 0 else f"REJECT ({nfail})")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
