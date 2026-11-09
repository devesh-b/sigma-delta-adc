#!/usr/bin/env python3
"""C1a rev C spot check (WO-23; NOT a C1b gate). Sandbox only:
    python revc_check.py OUTDIR k   CORNER_IDXS     # K / swing / GBW variant sweep: .op + .ac, no DC
    python revc_check.py OUTDIR tab  CORNER_IDXS    # rev C sizes, base + boost: .op + .ac + A(v) DC table +-1.8 V

CORNER_IDXS = comma list into CORNERS9. Every corner/copy prints one json line; tab mode writes avtab_<corner>.json
(small tables; raw csv deleted). Ideal pieces (C1b replaces them): ideal reference currents into the 1:32 reference
diodes; CMFB = ideal B-source on the m_plc gates (marked cmfb="ideal" in every table); protection cascode gate V_PC.

A(v) (CL-1b): servo forces V(op,om) = vt, vt swept -1.8..1.8 V in 0.05 V steps; vin = -x (servo input).
Secant gain A(v) = |vod - vod(0)| / |vin - vin(0)| (offset removed). A point counts only if the servo holds lock
(|vod - vt| < 1 mV) and A >= 40 dB; each sign's table ends at the first point that fails. Symmetry |A+ - A-| <= 0.5 dB
over the common range. The model table is min(A+, A-) per |v|; the v = 0 entry repeats the 0.05 V value.
REJECT on lost lock inside |v| <= 1.4 V, NaN, missing data, symmetry > 0.5 dB, margin < 50 mV, span < 1.40 V (boost).
Broken copy (tab mode, tt base and ss/125 boost): m_pl L 0.5 -> its table must fail the INL gate (revc_inl.py).
"""
import json, math, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sizes_draft as S

LIB = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.tech/ngspice/sky130.lib.spice"
CORNERS9 = [("tt", 27, 3.3), ("ss", -40, 3.0), ("ss", 125, 3.0), ("fs", 125, 3.0), ("sf", 125, 3.0),
            ("ff", -40, 3.6), ("ff", 125, 3.6), ("fs", -40, 3.0), ("sf", -40, 3.0)]
HOT = {("ss", 125), ("fs", 125), ("sf", 125)}
DEVQ = ("gm", "gds", "gmbs", "id", "vdsat", "cgg", "cdd")
CORE = ("in1", "pp1", "t", "n1", "nc1", "pc1", "pl1", "plc1")
KEY = {"in": "m_in", "pp": "m_pp", "t": "m_t", "n": "m_n", "nc": "m_nc", "pc": "m_pc", "pl": "m_pl", "plc": "m_plc"}


def sz(over):
    d = {k: dict(v) for k, v in S.SIZES.items()}
    for k, v in over.items():
        if k.startswith("_"):
            d[k] = v
        else:
            d[k].update(v)
    return d


# K / swing / GBW variants (k mode). Diode currents stay at I_NC/32; K is set by diode geometry.
VARIANTS = {
    "C": {},                                                              # rev C: K_N 8, K_P 6, m_pc 80/2, pair 80/0.5
    "KP5": {"m_bpc": dict(L=5.0)},                                        # K_P 5
    "KP4": {"m_bpc": dict(L=4.0)},                                        # K_P 4
    "KN6": {"m_bnc": dict(L=12.0)},                                       # K_N 6
    "pc40": {"m_pc": dict(M=8), "m_bpc": dict(WF=0.625, L=4.0)},          # rev B m_pc 40/2 with K_P 4 (swing reference)
    "in120": {"m_in": dict(M=12)},                                        # wider pair, same current (GBW route i)
    "in160": {"m_in": dict(M=16)},
    "in120s": {"m_in": dict(M=12, L=0.35)},
    "in160s": {"m_in": dict(M=16, L=0.35)},
}
MUT = {"m_pl": dict(L=0.5), "m_plr": dict(L=0.5)}   # CL-1b broken copy (ref follows: same current, low ro).
# Run 3: this copy only drops A0 by 4-7 dB (the PMOS cascode still multiplies ro_pl) and PASSED the INL gate (blind
# copy, 3.02 ppm vs 3.33 at ss/125 boost). Added a destructive copy: PMOS cascodes shorted D-S (as rev B's m_nc short).
MUT_PC = {"_short": "pc"}


def mos(name, d, g, s, b, p):
    return f"{name} {d} {g} {s} {b} sky130_fd_pr__{p['dev']} w={p['WF']} l={p['L']} m={p['M']}"


def par(inst, dev, q):
    return f"@m.x{inst}.msky130_fd_pr__{dev}[{q}]"


def ota(sfx, vdd, bst, z):
    n = lambda x: x if x in ("0", "vdd", "vpc") else f"{x}_{sfx}"
    X = lambda nm, d, g, s_, b, k: mos(f"X{nm}{sfx}", n(d), n(g), n(s_), n(b), z[k])
    I = {k: v * bst * (S.BOOST_SCALE.get(k, 1.0) if bst > 1 else 1.0) for k, v in S.I_REF.items()}
    return [X("tr", "btp", "btp", "vdd", "vdd", "m_tr"), f"Itr{sfx} {n('btp')} 0 {I['btp']:.6e}",
            X("t", "tail", "btp", "vdd", "vdd", "m_t"),
            X("in1", "da", "gp", "tail", "tail", "m_in"), X("in2", "db", "gm", "tail", "tail", "m_in"),
            X("pp1", "fa", "vpc", "da", "da", "m_pp"), X("pp2", "fb", "vpc", "db", "db", "m_pp"),
            X("nr", "bn", "bn", "0", "0", "m_nr"), f"Inr{sfx} vdd {n('bn')} {I['bn']:.6e}",
            X("n1", "fa", "bn", "0", "0", "m_n"), X("n2", "fb", "bn", "0", "0", "m_n"),
            X("nc1", "om", "vbnc", "fa", "0", "m_nc"), X("nc2", "op", "vbnc", "fb", "0", "m_nc"),
            X("pc1", "om", "vbpc", "sa", "sa", "m_pc"), X("pc2", "op", "vbpc", "sb", "sb", "m_pc"),
            X("plr", "bp", "bp", "vdd", "vdd", "m_plr"), f"Iplr{sfx} {n('bp')} 0 {I['bp']:.6e}",
            X("pl1", "sa", "bp", "vdd", "vdd", "m_pl"), X("pl2", "sb", "bp", "vdd", "vdd", "m_pl"),
            X("plc1", "sa", "ctl", "vdd", "vdd", "m_plc"), X("plc2", "sb", "ctl", "vdd", "vdd", "m_plc"),
            X("bnc", "vbnc", "vbnc", "0", "0", "m_bnc"), f"Ibnc{sfx} vdd {n('vbnc')} {I['vbnc']:.6e}",
            X("bpc", "vbpc", "vbpc", "vdd", "vdd", "m_bpc"), f"Ibpc{sfx} {n('vbpc')} 0 {I['vbpc']:.6e}",
            f"Bcm{sfx} {n('ctl')} 0 V = {vdd - 1.0} + 50*(0.5*(V({n('op')})+V({n('om')})) - {S.V_OCM})",
            f"Cfa{sfx} {n('fa')} 0 {S.C_FOLD_EXTRA + 1e-18}", f"Cfb{sfx} {n('fb')} 0 {S.C_FOLD_EXTRA + 1e-18}",
            f"Bgp{sfx} {n('gp')} 0 V = V(icm) + 0.5*(V(d) - max(min(V({n('x')})/1000, 0.3), -0.3))",   # x = 1000 vin
            f"Bgm{sfx} {n('gm')} 0 V = V(icm) - 0.5*(V(d) - max(min(V({n('x')})/1000, 0.3), -0.3))",
            f".nodeset v({n('x')})=0 v({n('tail')})={S.V_ICM + 0.9} v({n('om')})={S.V_OCM} v({n('op')})={S.V_OCM}",
            f"Bx{sfx} 0 {n('x')} I = 1e-3*(V({n('op')}) - V({n('om')}) - V(vt))", f"Rx{sfx} {n('x')} 0 1e12",
            f"Cx{sfx} {n('x')} 0 1e9", f"Clp{sfx} {n('op')} 0 {S.C_L}", f"Clm{sfx} {n('om')} 0 {S.C_L}"] + (
            [f"Rmut1{sfx} {n('om')} {n('sa')} 1", f"Rmut2{sfx} {n('op')} {n('sb')} 1"] if z.get("_short") == "pc" else [])


NODES = ("tail", "da", "fa", "sa", "om", "op", "x", "vbnc", "vbpc", "bp", "ctl")


def deck(c, t, v, tag, copies, dc):
    L = [f"* WO-23 {tag}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-15 reltol=1e-6",
         f"Vdd vdd 0 {v}", f"Vpc vpc 0 {S.V_PC}", f"Vicm icm 0 {S.V_ICM}", "Vid d 0 dc 0 ac 1", "Vvt vt 0 0"]
    for sfx, bst, z in copies:
        L += ota(sfx, v, bst, z)
    L += [".control", "set wr_singlescale", "set wr_vecnames", "op"]
    for sfx, _, z in copies:
        L += [f"print v({x}_{sfx})" for x in NODES]
        L += [f"print {par(nm + sfx, z[KEY[nm[:-1] if nm[-1] == '1' else nm]]['dev'], q)}" for nm in CORE for q in DEVQ]
    acv = " ".join(f"v(op_{s},om_{s})" for s, _, _ in copies)
    if dc:
        # two sweeps outward from 0 V (a single -1.8 -> 1.8 sweep starts in the clipped state and the servo stays in the
        # rail state: WO-23 run 2 lost lock at 0.05 V at every corner; tool error, not a design result)
        w = " ".join(f"v(x_{s}) v(op_{s},om_{s})" for s, _, _ in copies)
        L += ["dc Vvt 0 1.8 0.05", f"wrdata {tag}_dcp.csv {w}", "dc Vvt 0 -1.8 -0.05", f"wrdata {tag}_dcn.csv {w}"]
    L += ["ac dec 40 1 1e10", f"wrdata {tag}_ac.csv {acv}", "quit", ".endc", ".end"]
    return "\n".join(L)


def run(text, tag, out):
    fn = os.path.abspath(os.path.join(out, tag + ".sp"))
    open(fn, "w").write(text)
    r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=560)
    vals = {}
    for ln in r.stdout.splitlines():
        if " = " in ln:
            k, _, x = ln.partition(" = ")
            try:
                vals[k.strip()] = float(x.split()[0])
            except ValueError:
                pass
    return vals, r


def load(fn):
    a = np.loadtxt(fn, skiprows=1)
    os.remove(fn)   # WO rule: no raw csv kept
    return a


def op_ac(vals, sfx, z, k, ac, vdd, bst):
    fails = []
    g = lambda key: vals.get(key.lower(), float("nan"))
    v = lambda x: g(f"v({x}_{sfx})")
    d = {nm: {q: g(par(nm + sfx, z[KEY[nm[:-1] if nm[-1] == '1' else nm]]['dev'], q)) for q in DEVQ} for nm in CORE}
    vds = {"in1": v("tail") - v("da"), "pp1": v("da") - v("fa"), "t": vdd - v("tail"), "n1": v("fa"),
           "nc1": v("om") - v("fa"), "pc1": v("sa") - v("om"), "pl1": vdd - v("sa"), "plc1": vdd - v("sa")}
    res = {"margins": {}, "vdsat": {}}
    for nm in CORE:
        mg = vds[nm] - abs(d[nm]["vdsat"])
        res["margins"][nm] = mg
        res["vdsat"][nm] = abs(d[nm]["vdsat"])
        if not mg >= 0.05:
            fails.append(f"{nm} margin {mg:.3f}")
    res["V_fold"], res["V_sa"] = v("fa"), v("sa")
    res["bottom"] = v("fa") + abs(d["nc1"]["vdsat"]) + 0.05
    res["top"] = v("sa") - abs(d["pc1"]["vdsat"]) - 0.05
    res["span"] = res["top"] - res["bottom"]
    res["I_fold_over_I_tail"] = abs(d["n1"]["id"]) / abs(d["t"]["id"])
    res["I_core_uA"] = (abs(d["t"]["id"]) + 2 * abs(d["pl1"]["id"]) + 2 * abs(d["plc1"]["id"])) * 1e6
    res["I_tail_uA"] = abs(d["t"]["id"]) * 1e6
    res["gm1_uS"] = d["in1"]["gm"] * 1e6
    res["cgg_in_fF"] = d["in1"]["cgg"] * 1e15
    res["beta1_est"] = 4.0 / (4.5 + 0.23 + (d["in1"]["cgg"] * 1e12 - 0.189))   # DESIGN 2.2: Cp_vg 0.23 pF at Cgg 189 fF
    f, h = ac[:, 0], ac[:, 1 + 2 * k] + 1j * ac[:, 2 + 2 * k]
    mag = np.abs(h)
    res["A0_dB"] = 20 * np.log10(mag[0])
    if not mag[0] > 1.0 or not np.any(mag < 1.0):
        fails.append("dead OTA or no unity crossing")
        return res, fails
    i = np.argmax(mag < 1.0)
    res["GBW_MHz"] = float(np.exp(np.interp(0.0, -np.log(mag[i-1:i+1]), np.log(f[i-1:i+1])))) / 1e6
    ph = np.unwrap(np.angle(h)) * 180 / np.pi
    j = np.argmax(mag * S.BETA1 < 1.0)
    fb = np.exp(np.interp(0.0, -np.log(mag[j-1:j+1] * S.BETA1), np.log(f[j-1:j+1])))
    res["PM_deg"] = 180.0 + (np.interp(np.log(fb), np.log(f), ph) - ph[0])
    ex = 90.0 - res["PM_deg"]
    res["fp2_over_GBW"] = (fb / np.tan(np.radians(ex))) / (res["GBW_MHz"] * 1e6) if ex > 0.1 else float("inf")
    return res, fails


def table(dc, k):
    vt, x, vod = dc[:, 0], dc[:, 1 + 2 * k], dc[:, 2 + 2 * k]
    vin = -x / 1000.0   # servo node is scaled x1000 (resolution: vntol 1 uV -> 1 nV on vin)
    i0 = int(np.argmin(np.abs(vt)))
    out, fails = {}, []
    for sgn in (1, -1):
        rows = []
        for i in (range(i0 + 1, len(vt)) if sgn > 0 else range(i0 - 1, -1, -1)):
            lock = abs(vod[i] - vt[i])
            a = abs((vod[i] - vod[i0]) / (vin[i] - vin[i0])) if vin[i] != vin[i0] else float("inf")
            adb = 20 * math.log10(a) if a > 0 else -999
            if not (lock < 1e-3 and adb >= 40 and np.isfinite(adb)):
                if abs(vt[i]) <= 1.4 + 1e-9:
                    fails.append(f"sign {sgn}: lock {lock*1e3:.1f} mV / A {adb:.1f} dB at {vt[i]:.2f} V (inside 1.4 V)")
                break
            rows.append((round(abs(float(vt[i])), 3), adb))
        out[sgn] = rows
    nmin = min(len(out[1]), len(out[-1]))
    sym = max((abs(out[1][i][1] - out[-1][i][1]) for i in range(nmin)), default=float("nan"))
    if not sym <= 0.5:
        fails.append(f"symmetry {sym:.2f} dB > 0.5")
    tab = [(out[1][i][0], min(out[1][i][1], out[-1][i][1])) for i in range(nmin)]
    if not tab:
        fails.append("empty table")
        return {"fails": fails}
    tab = [(0.0, tab[0][1])] + tab
    return {"table": [(v, round(a, 3)) for v, a in tab], "vmax": tab[-1][0], "sym_dB": sym,
            "Amin_1p4_dB": min(a for v, a in tab if v <= 1.4 + 1e-9),
            "pos": [(v, round(a, 3)) for v, a in out[1]], "neg": [(v, round(a, 3)) for v, a in out[-1]], "fails": fails}


def main():
    out, mode, idx = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    nfail = 0
    for ci in idx.split(","):
        c, t, v = CORNERS9[int(ci)]
        tag = f"{mode}_{c}_{t}_{v}".replace("-", "m").replace(".", "p")
        if mode == "k":
            if (c, t) in HOT:
                copies = [(nm, 2.0, sz(o)) for nm, o in VARIANTS.items()]
            else:
                copies = [(nm, 1.0, sz(VARIANTS[nm])) for nm in ("C", "KP5", "KN6", "pc40", "in120s")]
        else:
            copies = [("b1", 1.0, sz({})), ("b2", 2.0, sz({}))]
            if (c, t) == ("tt", 27):
                copies += [("mutb1", 1.0, sz(MUT)), ("mutpcb1", 1.0, sz(MUT_PC))]
            if (c, t) == ("ss", 125):
                copies += [("mutb2", 2.0, sz(MUT)), ("mutpcb2", 2.0, sz(MUT_PC))]
        vals, r = run(deck(c, t, v, tag, copies, mode == "tab"), tag, out)
        try:
            ac = load(os.path.join(out, tag + "_ac.csv"))
            dc = None
            if mode == "tab":
                dp, dn = load(os.path.join(out, tag + "_dcp.csv")), load(os.path.join(out, tag + "_dcn.csv"))
                dc = np.vstack([dn[::-1], dp[1:]])   # ascending vt, one 0 V point
        except Exception as e:
            print(json.dumps({"corner": tag, "fails": [f"no data {e!r}"], "stderr": r.stderr[-600:]}), flush=True)
            nfail += 1
            continue
        tabs = {}
        for k, (sfx, bst, z) in enumerate(copies):
            try:
                res, fails = op_ac(vals, sfx, z, k, ac, v, bst)
                if mode == "tab":
                    tb = table(dc, k)
                    fails += tb.pop("fails")
                    res.update({kk: tb[kk] for kk in ("vmax", "sym_dB", "Amin_1p4_dB") if kk in tb})
                    tabs[sfx] = dict(tb, corner=c, temp=t, vdd=v, boost=bst, mutant=sfx.startswith("mut"), info=sfx.startswith("var"),
                                     cmfb="ideal B-source (C1b: real SC CMFB)", A0_ac_dB=res.get("A0_dB"))
                if bst == 2.0 and (c, t) in HOT and not res["span"] >= 1.40:
                    fails.append(f"span {res['span']:.3f} < 1.40")
            except Exception as e:
                res, fails = {}, [f"analysis error {e!r}"]
            for kk, x in list(res.items()):
                if isinstance(x, float) and math.isnan(x):
                    fails.append(f"NaN {kk}")
            if not sfx.startswith(("mut", "var")):
                nfail += bool(fails)
            res.update(corner=c, temp=t, vdd=v, boost=bst, copy=sfx, fails=fails)
            rnd = lambda x: float(f"{x:.4g}") if isinstance(x, float) else ({a: rnd(b) for a, b in x.items()} if isinstance(x, dict) else x)
            print(json.dumps(rnd(res)), flush=True)
        if tabs:
            json.dump(tabs, open(os.path.join(out, f"avtab_{c}_{t}_{v}.json".replace("-", "m")), "w"), indent=0)
    print("VERDICT", "ACCEPT" if nfail == 0 else f"REJECT ({nfail} copies fail; spot run, not a gate)")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
