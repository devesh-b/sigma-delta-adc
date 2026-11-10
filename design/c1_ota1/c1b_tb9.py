#!/usr/bin/env python3
"""C1b tb9: CMFB loop transient on the NETLISTED OTA1 with the real SC CMFB and the WO-27 CM error amp. Sandbox only:
    python c1b_tb9.py OUTDIR CORNER_IDXS [--mut]        # CORNER_IDXS into revc_check.CORNERS9; --mut: broken-copy deck

Limits (expected values from SPEC row 98 / DESIGN.md 4 tb9 / REVIEW-C1a-revC RC-m2 / CL-7, not from this code):
  * CM error settles within TOL = 10 mV of its settled value by 0.2 t_half (22.5 ns at 4 MHz boost) after each event and
    stays there until the next event: conversion-reset release, a differential integration step (0.8 V diff), a 30 mV CM
    charge step at the outputs (Q = 30 mV x integrate-phase load), reset assert, reset release.
  * Start-up from both rails (outputs pre-charged to VDD and to 0, integrator held in reset, D57 start-up clamp released
    after 2 T): |V_out,cm - V_OCM| <= 10 mV over the last clock period before the CL-7 4 us.
  WO-28 (D61 dual path): the start-up clamp (rstb low) now holds ctl / bli at V_BL0 and both outputs at V_OCM, so Cc
  starts with the operating charge; events start at 1.5 us (after convergence). Copy suvb: start-up with ivbl0 x2
  (a V_BL0 error the slow path must remove). Broken copies: cc_div4 (event rows) and int_off+vbl0x2 (start-up row).
Setup per copy: OTA1 (cmfb="sc", boost, fs 4 MHz, ph1 / ph2 non-overlapping by g = 0.025/fs), Cint 4 pF out -> island
(inverting side), Cs1 0.5 pF island -> ground, output routing C_RT; reset = island shunt to V_ICM (isl) + ideal output
short (gen_tier1 style); chopper static. WO-27 broken copies (superseded by WO-28, below): cc_div4 (Cc / 4) and cmbw4 (amp
bandwidth / 4 via CM_BW4_CAP on ctl): each must REJECT on an event row with valid data.
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
CINT, CS1 = 4e-12, 0.5e-12
DV_CM, DV_DIFF = 30e-3, 0.8
T_STOP = 4.0e-6                     # CL-7
T_RST = 216e-9                      # reset window at 4 MHz (CHOP_SW island row)
DIAG = os.environ.get("TB9_DIAG", "")                       # WO-29 diagnosis copy spec (see main)
TSTOP_RUN = float(os.environ.get("TB9_TSTOP", T_STOP))      # WO-29: longer runs to tell a slow loop from an offset
DIAG_VEC = bool(DIAG) or bool(os.environ.get("TB9_VEC"))    # also log ctl / bli per half-phase
# WO-28: events start after convergence (start-up clamp released at 2 T = 0.5 us, slow path tau <= 0.4 us)
EV = [("reset release", 1.5e-6), ("diff step", 1.75e-6), ("CM step", 2.25e-6), ("reset assert", 3.0e-6),
      ("reset release 2", 3.0e-6 + T_RST)]
# WO-28 broken copies (own deck): Cc / 4 -> event rows; slow path off with a V_BL0 error (ivbl0 x2) -> start-up row
MUT = [("mcc4", "ev", "cc_div4"), ("mio", "su_hi", "int_off+vbl0x2")]
NOM = [("ev", "ev", None), ("suhi", "su_hi", None), ("sulo", "su_lo", None), ("suvb", "su_lo", "vbl0x2")]


def copy(x, kind, sub, vd, mut=None):
    L = [f"X{x} vdd 0 inp_{x} inn_{x} outp_{x} outn_{x} vicm vocm ibtp_{x} ibn_{x} ibp_{x} ivbnc_{x} ivbpc_{x} ivbl0_{x} "
         f"vdd 0 lv 0 isl_{x} ph1 ph1b ph2 ph2b rstb {sub}"]
    for p_, i_ in NL.bias_currents(True, mut).items():
        L.append(f"I{p_}_{x} {p_}_{x} 0 {i_:.6e}" if p_ in NL.SINK_PORTS else f"I{p_}_{x} vdd {p_}_{x} {i_:.6e}")
    L += [f"Cip_{x} outp_{x} inp_{x} {CINT:g}", f"Cin_{x} outn_{x} inn_{x} {CINT:g}",
          f"Csp_{x} inp_{x} 0 {CS1:g}", f"Csn_{x} inn_{x} 0 {CS1:g}",
          f"Crp_{x} outp_{x} 0 {C_RT:g}", f"Crn_{x} outn_{x} 0 {C_RT:g}",
          f"Bcm_{x} cm_{x} 0 V = 0.5*(V(outp_{x})+V(outn_{x}))"]
    if kind == "ev":
        L += [f"Bisl_{x} isl_{x} 0 V = {vd:g}*V(rsw)", f"Srs_{x} outp_{x} outn_{x} rsw 0 SWM"]
        qd, qc = DV_DIFF / 2 * CINT, DV_CM * LOADS["integ"]
        t1, t2 = EV[1][1], EV[2][1]
        L += [f"Idp_{x} 0 inp_{x} PULSE(0 {qd / 10e-9:.6e} {t1:.6e} 0.1n 0.1n 9.9n 1)",
              f"Idn_{x} inn_{x} 0 PULSE(0 {qd / 10e-9:.6e} {t1:.6e} 0.1n 0.1n 9.9n 1)",
              f"Icp_{x} 0 outp_{x} PULSE(0 {qc / 1e-9:.6e} {t2:.6e} 0.1n 0.1n 0.9n 1)",
              f"Icn_{x} 0 outn_{x} PULSE(0 {qc / 1e-9:.6e} {t2:.6e} 0.1n 0.1n 0.9n 1)"]
    else:   # start-up copy: integrator held in reset, outputs pre-charged to a rail
        rail = vd if kind == "su_hi" else 0.0
        L += [f"Visl_{x} isl_{x} 0 {vd:g}", f"Srs_{x} outp_{x} outn_{x} one 0 SWM",
              f".ic v(outp_{x})={rail:g} v(outn_{x})={rail:g}"]
    return L


def deck(c, t, vd, tag, copies):
    L = [f"* WO-27 c1b_tb9 {tag}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-15 reltol=1e-4",
         f"Vdd vdd 0 {vd}", f"Vicm vicm 0 {S.V_ICM}", f"Vocm vocm 0 {S.V_OCM}", "Vlv lv 0 1.8", "Vone one 0 1",
         ".model SWM sw vt=0.5 vh=0.1 ron=100 roff=1e12",
         f"Vrsw rsw 0 PWL(0 1 {EV[0][1]:.6e} 1 {EV[0][1] + 1e-9:.6e} 0 {EV[3][1]:.6e} 0 {EV[3][1] + 1e-9:.6e} 1 "
         f"{EV[4][1]:.6e} 1 {EV[4][1] + 1e-9:.6e} 0)",
         f"Vrstb rstb 0 PWL(0 0 {2 * T:.6e} 0 {2 * T + 1e-9:.6e} {vd:g})",
         f"Vph1 ph1 0 PULSE(0 {vd:g} {G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         f"Vph1b ph1b 0 PULSE({vd:g} 0 {G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         f"Vph2 ph2 0 PULSE(0 {vd:g} {T / 2 + G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})",
         f"Vph2b ph2b 0 PULSE({vd:g} 0 {T / 2 + G:.6e} 0.2n 0.2n {T / 2 - 2 * G:.6e} {T:.6e})"]
    L.append(".model SWI sw vt=1.5 vh=0.1 ron=2k roff=1e14")   # WO-29 diagnosis: ideal CMFB switches (sw_ideal*)
    subs = {}
    for x, kind, mut in copies:
        if mut not in subs:
            subs[mut] = f"ota1_t9_{(mut or 'nom').replace('+', '_')}"
            tk = NL.toks(mut)   # dcavg: the averaged Cr model of the op/AC decks, run in the same transient
            m2 = "+".join(sorted(tk - {"dcavg"})) or None
            L.append(NL.build(subs[mut], cmfb="dc" if "dcavg" in tk else "sc", fs=FS, mut=m2, boost=True))
        L += copy(x, kind, subs[mut], vd, mut)
    vec = " ".join(f"v(cm_{x})" for x, *_ in copies)
    if DIAG_VEC:
        vec += " " + " ".join(f"v(x{x}.ctl) v(x{x}.bli)" for x, *_ in copies)
    L += [".control", "set wr_singlescale", "set wr_vecnames", f"tran 0.1n {TSTOP_RUN:.6e} 0 0.5n",
          f"wrdata {tag}.csv {vec}", "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def check_ev(tm, cm):
    rows, fails = [], []
    for j, (nm, te) in enumerate(EV):
        tn = EV[j + 1][1] if j + 1 < len(EV) else T_STOP
        w = (tm >= te + T_SET) & (tm < tn)
        rw = (tm >= tn - min(T, (tn - te) / 2)) & (tm < tn)
        ref = float(np.mean(cm[rw]))
        err = float(np.max(np.abs(cm[w] - ref)))
        pk = float(np.max(np.abs(cm[(tm >= te) & (tm < tn)] - ref)))
        rows.append(dict(event=nm, settled_cm_mV=(ref - S.V_OCM) * 1e3, err_after_tset_mV=err * 1e3, peak_mV=pk * 1e3))
        if not err <= TOL:
            fails.append(f"{nm}: {err * 1e3:.2f} mV > {TOL * 1e3:.0f} mV at +{T_SET * 1e9:.1f} ns")
    return rows, fails


def check_su(tm, cm):
    w = tm >= T_STOP - T
    err = float(np.max(np.abs(cm[w] - S.V_OCM)))
    out = np.abs(cm - S.V_OCM) > TOL
    t_in = float(tm[np.nonzero(out)[0][-1] + 1]) if out.any() and np.nonzero(out)[0][-1] + 1 < len(tm) else float("nan")
    return dict(err_last_T_mV=err * 1e3, t_enter_band_us=t_in * 1e6), ([] if err <= TOL else [f"start-up {err * 1e3:.2f} mV"])


def main():
    out, idx, mut_deck = sys.argv[1], sys.argv[2], "--mut" in sys.argv
    os.makedirs(out, exist_ok=True)
    nfail, rows = 0, []
    for ci in idx.split(","):
        c, t, vd = CORNERS9[int(ci)]
        tag = f"tb9_{c}_{t}".replace("-", "m") + ("_mut" if mut_deck else "")
        cps = list(MUT if mut_deck else NOM)
        if DIAG:   # WO-29 diagnosis deck: TB9_DIAG="x:tok+tok,x:tok,..." ev copies only (tok '-' = nominal)
            tag += "_diag"
            cps = [(s.split(":")[0], "ev", None if s.split(":")[1] == "-" else s.split(":")[1]) for s in DIAG.split(",")]
        fn = os.path.join(out, tag + ".csv")
        if os.path.exists(fn):
            os.remove(fn)
        open(os.path.join(out, tag + ".sp"), "w").write(deck(c, t, vd, tag, cps))
        r = subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=5000)
        lint = [l.strip() for l in (r.stdout + r.stderr).splitlines()
                if re.search(r"(error|unknown|singular|no convergence|timestep too small|could not find)", l, re.I)]
        try:
            a = np.loadtxt(fn, skiprows=1)
            if DIAG_VEC:   # per copy and clock period: cm / ctl / bli at the end of ph1 and of ph2 (+ the period index)
                nc = len(cps)
                kk = np.arange(int(TSTOP_RUN / T))
                te1, te2 = kk * T + T / 2 - G - 0.5e-9, kk * T + T - G - 0.5e-9
                cols = [kk * T]
                for k in range(nc):
                    for col in (1 + k, 1 + nc + 2 * k, 2 + nc + 2 * k):
                        cols += [np.interp(te1, a[:, 0], a[:, col]), np.interp(te2, a[:, 0], a[:, col])]
                np.savetxt(os.path.join(out, tag + "_phase.txt"), np.column_stack(cols), fmt="%.6g",
                           header="t0 " + " ".join(f"{x}_{q}{p}" for x, *_ in cps for q in ("cm", "ctl", "bli") for p in (1, 2)))
                summ = {}
                for k, (x, *_r) in enumerate(cps):
                    for t0 in (1.4e-6, 3.9e-6, 7.9e-6, 11.9e-6):
                        if t0 < TSTOP_RUN:
                            j = int(t0 / T)
                            summ[f"{x}@{t0 * 1e6:.1f}us"] = {n_: round((cols[1 + 6 * k + 2 * q + p][j] - (S.V_OCM if q == 0 else 0)) * (1e3 if q == 0 else 1), 4)
                                                             for q, nq in enumerate(("cm_err_mV", "ctl_V", "bli_V")) for p, n_ in
                                                             ((0, nq + "_ph1"), (1, nq + "_ph2"))}
                print(json.dumps(dict(diag=tag, **summ)), flush=True)
                json.dump(summ, open(os.path.join(out, tag + "_phase.json"), "w"), indent=0)
            os.remove(fn)
        except Exception as e:
            print(json.dumps(dict(corner=tag, fails=[f"no data {e!r}"], lint=lint[:5], stderr=r.stderr[-600:])))
            nfail += 1
            continue
        tm = a[:, 0]
        for k, (x, kind, m) in enumerate(cps):
            cm = a[:, 1 + k]
            res, fails = check_ev(tm, cm) if kind == "ev" else check_su(tm, cm)
            row = dict(corner=c, temp=t, vdd=vd, copy=x, mut=m, result=res, fails=fails + ([f"lint {lint[:3]}"] if lint else []))
            if mut_deck:
                ok = not lint and np.all(np.isfinite(cm))
                row["mutant_verdict"] = ("REJECTED (good)" if ok and fails else "PASSED (check is blind)" if ok
                                         else "MUTANT INVALID")
                nfail += row["mutant_verdict"] != "REJECTED (good)"
            else:
                nfail += bool(row["fails"])
            rows.append(row)
            print(json.dumps(row), flush=True)
    json.dump(rows, open(os.path.join(out, f"tb9_{idx.replace(',', '_')}{'_mut' if mut_deck else ''}.json"), "w"), indent=0)
    print("VERDICT", "ACCEPT" if nfail == 0 else f"REJECT ({nfail})")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
