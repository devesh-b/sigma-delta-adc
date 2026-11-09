#!/usr/bin/env python3
"""C1a rev B spot check (WO-21; NOT a C1b gate): .op / static A(v) / .ac of the OTA1 core, rev B sizes.

Rev B vs WO-20 (REVIEW-C1a M7): A(v) uses the MEASURED V(op,om), not the servo target; a lost servo, a dead OTA
(|H(f_min)| < 1), a missing unity crossing, NaN or a missing measurement is REJECT, never a number. MC and .noise
are dropped here (WO-23). One broken copy (m_nc drain-source short at tt base) must REJECT on A0.

Ideal pieces (C1b replaces them): bias reference currents are ideal sources into the mirror/bias diodes; the CMFB
is an ideal B-source on the CMFB load section m_plc only (the fixed 75 % load half is a mirror). The cascode biases
are the rev B Vdsat-tracking diodes (m_bnc / m_bpc), the protection cascode gate is tied to V_PC = 0 V.
Run on the sandbox only:  python op_ac_check.py OUTDIR [all | comma list of corner indexes 0-8]
"""
import json, math, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sizes_draft as S

LIB = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.tech/ngspice/sky130.lib.spice"
CORNERS = [[("tt", 27, 3.3), ("ss", -40, 3.0), ("ss", 125, 3.0), ("fs", 125, 3.0), ("sf", 125, 3.0)],
           [("ff", -40, 3.6), ("ff", 125, 3.6), ("fs", -40, 3.0), ("sf", -40, 3.0)]]
DEV = {"in": "m_in", "pp": "m_pp", "t": "m_t", "n": "m_n", "nc": "m_nc", "pc": "m_pc", "pl": "m_pl", "plc": "m_plc"}


def mos(name, d, g, s, b, p, m=None):
    return f"{name} {d} {g} {s} {b} sky130_fd_pr__{p['dev']} w={p['WF']} l={p['L']} m={p['M'] if m is None else m}"


def par(n, k, q):
    return f"@m.x{n}.msky130_fd_pr__{S.SIZES[k]['dev']}[{q}]"


def ota(sfx, vdd, bst, mutant=""):
    """One OTA copy with its own bias legs; every node and device carries the suffix sfx."""
    sz = S.SIZES
    it, isk = S.I_TAIL * bst, S.I_SINK * bst
    inc = isk - it / 2
    n = lambda x: f"{x}_{sfx}"
    X = lambda nm, d, g, s_, b, k, m=None: mos(f"X{nm}{sfx}", n(d) if d not in ("0", "vdd", "vddb", "vpc") else d,
                                               n(g) if g not in ("0", "vpc") else g,
                                               n(s_) if s_ not in ("0", "vdd", "vddb") else s_,
                                               n(b) if b not in ("0", "vdd", "vddb") else b, sz[k], m)
    L = [X("tr", "btp", "btp", "vddb", "vddb", "m_tr"), f"Itr{sfx} {n('btp')} 0 {it*sz['m_tr']['M']/sz['m_t']['M']:.6e}",
         X("t", "tail", "btp", "vdd", "vdd", "m_t"),
         X("in1", "da", "gp", "tail", "tail", "m_in"), X("in2", "db", "gm", "tail", "tail", "m_in"),
         X("pp1", "fa", "vpc", "da", "da", "m_pp"), X("pp2", "fb", "vpc", "db", "db", "m_pp"),
         X("nr", "bn", "bn", "0", "0", "m_nr"), f"Inr{sfx} vddb {n('bn')} {isk*sz['m_nr']['M']/sz['m_n']['M']:.6e}",
         X("n1", "fa", "bn", "0", "0", "m_n"), X("n2", "fb", "bn", "0", "0", "m_n"),
         X("nc1", "om", "vbnc", "fa", "0", "m_nc"), X("nc2", "op", "vbnc", "fb", "0", "m_nc"),
         X("pc1", "om", "vbpc", "sa", "sa", "m_pc"), X("pc2", "op", "vbpc", "sb", "sb", "m_pc"),
         X("plr", "bp", "bp", "vddb", "vddb", "m_pl", sz["m_pl"]["M"] // 4), f"Iplr{sfx} {n('bp')} 0 {inc*S.LOAD_FIXED/4:.6e}",
         X("pl1", "sa", "bp", "vdd", "vdd", "m_pl"), X("pl2", "sb", "bp", "vdd", "vdd", "m_pl"),
         X("plc1", "sa", "ctl", "vdd", "vdd", "m_plc"), X("plc2", "sb", "ctl", "vdd", "vdd", "m_plc"),
         X("bnc", "vbnc", "vbnc", "0", "0", "m_bnc"), f"Ibnc{sfx} vddb {n('vbnc')} {inc/sz['m_nc']['M']:.6e}",
         X("bpc", "vbpc", "vbpc", "vddb", "vddb", "m_bpc"), f"Ibpc{sfx} {n('vbpc')} 0 {inc/sz['m_pc']['M']:.6e}",
         f"Bcm{sfx} {n('ctl')} 0 V = {vdd - 1.0} + 50*(0.5*(V({n('op')})+V({n('om')})) - {S.V_OCM})",
         f"Cfa{sfx} {n('fa')} 0 {S.C_FOLD_EXTRA + 1e-18}", f"Cfb{sfx} {n('fb')} 0 {S.C_FOLD_EXTRA + 1e-18}",
         # servo correction clamped to +-0.3 V (offset is mV): a run-away x (WO-21 r1, tt base copy) cannot
         # push a gate to a nonsense voltage; inside the clamp the AC gain is unchanged
         f"Bgp{sfx} {n('gp')} 0 V = V(icm) + 0.5*(V(d) - max(min(V({n('x')}), 0.3), -0.3))",
         f"Bgm{sfx} {n('gm')} 0 V = V(icm) - 0.5*(V(d) - max(min(V({n('x')}), 0.3), -0.3))",
         f".nodeset v({n('x')})=0 v({n('tail')})={S.V_ICM + 0.9} v({n('om')})={S.V_OCM} v({n('op')})={S.V_OCM}",
         f"Bx{sfx} 0 {n('x')} I = 1e-3*(V({n('op')}) - V({n('om')}) - V(vt))", f"Rx{sfx} {n('x')} 0 1e12",
         f"Cx{sfx} {n('x')} 0 1e9", f"Clp{sfx} {n('op')} 0 {S.C_L}", f"Clm{sfx} {n('om')} 0 {S.C_L}"]
    if mutant == "nc_short":   # broken copy: NMOS cascodes shorted D-S -> A0 must collapse
        L += [f"Rmut1{sfx} {n('om')} {n('fa')} 1", f"Rmut2{sfx} {n('op')} {n('fb')} 1"]
    return L


COPIES = [("b1", 1.0, ""), ("b2", 2.0, "")]
NODES = ("tail", "da", "fa", "sa", "om", "op", "x", "vbnc", "vbpc", "bp", "ctl")


def deck(corner, temp, vdd, tag, copies):
    L = [f"* WO-21 {tag}", f".lib {LIB} {corner}", f".temp {temp}", ".option gmin=1e-15 reltol=1e-6",
         f"Vdd vdd 0 {vdd}", f"Vddb vddb 0 {vdd}", f"Vpc vpc 0 {S.V_PC}",
         f"Vicm icm 0 {S.V_ICM}", "Vid d 0 dc 0 ac 1", "Vvt vt 0 0"]
    for sfx, bst, mut in copies:
        L += ota(sfx, vdd, bst, mut)
    L += [".control", "set wr_singlescale", "set wr_vecnames", "op", "print i(Vdd) i(Vddb)"]
    for sfx, _, _ in copies:
        L += [f"print v({x}_{sfx})" for x in NODES]
        L += [f"print {par(nm + sfx, DEV[nm[:-1] if nm[-1] == '1' else nm], q)}"
              for nm in ("in1", "pp1", "t", "n1", "nc1", "pc1", "pl1", "plc1")
              for q in ("gm", "gds", "gmbs", "id", "vdsat", "cgg", "cdd")]
    dcv = " ".join(f"v(x_{s}) v(op_{s},om_{s})" for s, _, _ in copies)
    acv = " ".join(f"v(op_{s},om_{s})" for s, _, _ in copies)
    L += ["dc Vvt -1.4 1.4 0.1", f"wrdata {tag}_dc.csv {dcv}",
          "ac dec 40 1 1e10", f"wrdata {tag}_ac.csv {acv}", "quit", ".endc", ".end"]
    return "\n".join(L)


def run(text, tag, out):
    fn = os.path.abspath(os.path.join(out, tag + ".sp"))
    open(fn, "w").write(text)
    r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=300)
    vals = {}
    for ln in r.stdout.splitlines():
        if " = " in ln:
            k, _, v = ln.partition(" = ")
            try:
                vals[k.strip()] = float(v.split()[0])
            except ValueError:
                pass
    return vals, r


def load(fn):
    a = np.loadtxt(fn, skiprows=1)
    os.remove(fn)   # WO rule: delete raw csv after reading
    return a


def analyse(vals, sfx, k, dc, ac, vdd, bst):
    fails = []
    g = lambda k: vals.get(k.lower(), float("nan"))
    res = {f"v({x})": g(f"v({x}_{sfx})") for x in NODES}
    d = {}
    for n in ("in1", "pp1", "t", "n1", "nc1", "pc1", "pl1", "plc1"):
        d[n] = {q: g(par(n + sfx, DEV[n[:-1] if n[-1] == "1" else n], q)) for q in ("gm", "gds", "gmbs", "id", "vdsat", "cgg", "cdd")}
    v = lambda k: res[f"v({k})"]
    vds = {"in1": v("tail") - v("da"), "pp1": v("da") - v("fa"), "t": vdd - v("tail"), "n1": v("fa"),
           "nc1": v("om") - v("fa"), "pc1": v("sa") - v("om"), "pl1": vdd - v("sa"), "plc1": vdd - v("sa")}
    for n in d:
        d[n]["vds"] = vds[n]
        d[n]["margin"] = vds[n] - abs(d[n]["vdsat"])
        if not d[n]["margin"] >= 0.05:
            fails.append(f"{n} Vds-Vdsat {d[n]['margin']:.3f} < 0.05")
    res["dev"] = d
    # hand A0 from op numbers
    ro = lambda n: 1.0 / d[n]["gds"]
    par2 = lambda a, b: a * b / (a + b)
    r_dn = (d["nc1"]["gm"] + d["nc1"]["gmbs"]) * ro("nc1") * ro("n1")
    r_up = d["pc1"]["gm"] * ro("pc1") * par2(ro("pl1"), ro("plc1"))
    res["R_dn_MOhm"], res["R_up_MOhm"] = r_dn / 1e6, r_up / 1e6
    res["A0_hand_dB"] = 20 * np.log10(d["in1"]["gm"] * par2(r_dn, r_up))
    res["gm1_uS"] = d["in1"]["gm"] * 1e6
    res["gmid_in"] = d["in1"]["gm"] / abs(d["in1"]["id"])
    res["cgg_in_fF"] = d["in1"]["cgg"] * 1e15
    res["V_DIN"] = v("da")
    res["vsg_in"] = v("tail") - S.V_ICM
    # input-CM limits (SPEC CM row): lower = lowest vg keeping m_in Vsd >= Vdsat + 50 mV; upper headroom
    res["vg_cm_min"] = S.V_ICM - (d["in1"]["margin"] - 0.05)
    res["tail_headroom_at_+0.13"] = vdd - v("tail") - 0.13
    res["I_core_uA"] = (abs(d["t"]["id"]) + 2 * abs(d["pl1"]["id"]) + 2 * abs(d["plc1"]["id"])) * 1e6
    inc = (S.I_SINK - S.I_TAIL / 2) * bst
    res["I_bias_uA"] = bst * 1e6 * (S.I_TAIL / 4 + S.I_SINK / 4) + 1e6 * inc * (S.LOAD_FIXED / 4 + 1 / 4 + 1 / 8)
    vt, vin, vod = dc[:, 0], -dc[:, 1 + 2 * k], dc[:, 2 + 2 * k]
    lock = np.max(np.abs(vod - vt))
    res["servo_lock_err_mV"] = lock * 1e3
    if not lock < 1e-3:
        fails.append(f"servo lost lock {lock*1e3:.1f} mV")
    i0 = np.argmin(np.abs(vt))
    m = np.abs(vt) > 0.05
    a = np.abs((vod[m] - vod[i0]) / (vin[m] - vin[i0]))
    res["A_static_min_dB_1p4"] = 20 * np.log10(a.min())
    f, h = ac[:, 0], ac[:, 1 + 2 * k] + 1j * ac[:, 2 + 2 * k]
    mag = np.abs(h)
    res["A0_dB"] = 20 * np.log10(mag[0])
    if not mag[0] > 1.0 or not np.any(mag < 1.0):
        fails.append("dead OTA or no unity crossing")
        res["fails"] = fails
        return res
    i = np.argmax(mag < 1.0)
    ugf = np.exp(np.interp(0.0, -np.log(mag[i-1:i+1]), np.log(f[i-1:i+1])))
    ph = np.unwrap(np.angle(h)) * 180 / np.pi
    res["GBW_loaded_MHz"] = ugf / 1e6
    j = np.argmax(mag * S.BETA1 < 1.0)
    fb = np.exp(np.interp(0.0, -np.log(mag[j-1:j+1] * S.BETA1), np.log(f[j-1:j+1])))
    res["PM_beta1_deg"] = 180.0 + (np.interp(np.log(fb), np.log(f), ph) - ph[0])
    ex = 90.0 - res["PM_beta1_deg"]
    res["fp2_eq_MHz"] = fb / np.tan(np.radians(ex)) / 1e6 if ex > 0.1 else float("inf")
    for k, x in res.items():
        if isinstance(x, float) and math.isnan(x):
            fails.append(f"NaN {k}")
    res["fails"] = fails
    return res


def main():
    out = sys.argv[1]
    grp = sys.argv[2] if len(sys.argv) > 2 else "all"
    os.makedirs(out, exist_ok=True)
    flat9 = CORNERS[0] + CORNERS[1]   # grp = "all" or comma list of indexes into these 9 corners
    corners = flat9 if grp == "all" else [flat9[int(i)] for i in grp.split(",")]
    allres, nfail = [], 0
    for (c, t, v) in corners:
        copies = COPIES + ([("mut", 1.0, "nc_short")] if (c, t) == ("tt", 27) else [])
        tag = f"{c}_{t}_{v}".replace("-", "m").replace(".", "p")
        vals, r = run(deck(c, t, v, tag, copies), tag, out)
        try:
            dc, ac = load(os.path.join(out, tag + "_dc.csv")), load(os.path.join(out, tag + "_ac.csv"))
        except Exception as e:
            dc = ac = None
            print(json.dumps({"corner": tag, "fails": [f"no data {e!r}"], "stderr": r.stderr[-600:]}), flush=True)
            nfail += 1
            continue
        for k, (sfx, bst, mut) in enumerate(copies):
            try:
                res = analyse(vals, sfx, k, dc, ac, v, bst)
            except Exception as e:  # report, never silently pass
                res = {"fails": [f"analysis error {e!r}"]}
            res.update(corner=c, temp=t, vdd=v, boost=bst, mutant=mut)
            if mut:   # the broken copy must REJECT on A0 (expected about 40 dB)
                ok = res.get("A0_dB", 0) < 60
                res["mutant_verdict"] = "REJECTED (good)" if ok else "PASSED (check is blind)"
                nfail += 0 if ok else 1
            else:
                nfail += bool(res["fails"])
            allres.append(res)
            flat = {k2: (float(f"{x:.4g}") if isinstance(x, float) else x) for k2, x in res.items() if k2 != "dev"}
            flat["margins"] = {n: float(f"{dd['margin']:.3f}") for n, dd in res.get("dev", {}).items()}
            flat["vdsat"] = {n: float(f"{abs(dd['vdsat']):.3f}") for n, dd in res.get("dev", {}).items()}
            flat["cdd_fF"] = {n: float(f"{abs(dd['cdd'])*1e15:.1f}") for n, dd in res.get("dev", {}).items()}
            print(json.dumps(flat), flush=True)
    json.dump(allres, open(os.path.join(out, f"op_ac_revb_{grp.replace(',', '-')}.json"), "w"), indent=1, default=float)
    print("VERDICT", "ACCEPT" if nfail == 0 else f"REJECT ({nfail} points fail; spot run, not a gate)")


if __name__ == "__main__":
    main()
