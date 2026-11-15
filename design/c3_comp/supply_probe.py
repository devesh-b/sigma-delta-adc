#!/usr/bin/env python3
"""WO-84 (C3i) probe: T8 supply basis (D87 a), rev f residuals, keeper candidate kp2. Sandbox only.

    python supply_probe.py gen OUT      # deck dirs + OUT/jobs.txt (run with scripts/lpool.sh), then
    python c3_tb.py collect OUT         # standard judge (T8 / T2 / T5 rows)
    python supply_probe.py ipost DIR    # (inside the job, before c3_tb post) supply-current split + nb2/op residual

Split decks ("_split"): every subckt terminal tied to vdd gets its own 0 V ammeter VI<dev><term> (vdd -> terminal),
so the current each device draws from (+) or returns into (-) the vdd node is seen. Labelled probe, not design.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c3_tb  # noqa: E402
from c3_tb import st_deck, one_deck, cyc_deck, SS40  # noqa: E402
_DL0 = c3_tb.deck_list   # the c3_tb list (gen() rebinds c3_tb.deck_list)


def _split(text):
    out, br, insub = [], [], False
    for ln in text.splitlines():
        if ln.startswith(".subckt c3_comp"):
            insub = True
        elif ln.startswith(".ends"):
            insub = False
        if insub and ln.startswith("X"):
            tk = ln.split()
            n = tk[0][1:]
            for i, t in ((1, "d"), (2, "g"), (3, "s"), (4, "b")):
                if tk[i] == "vdd":
                    nd = f"vdd_{n}_{t}".lower()
                    out.append(f"VI{n}{t} vdd {nd} 0")
                    br.append(f"v.xc.vi{n}{t}#branch".lower())
                    tk[i] = nd
            ln = " ".join(tk)
        if ln.startswith("write st.raw"):
            ln += " vdds#branch " + " ".join(br) + " v(xc.nb2) v(xc.ob2) v(xc.op) v(xc.on) v(xc.ap) v(xc.an) v(xc.dp) v(xc.dn)"
        out.append(ln)
    return "\n".join(out) + "\n"


def _supply(text, sup, order, vd, ron):
    """sup 'sw': 10 ohm feed for the power-up ramp (numerics, the ideal-pin abort at the ramp corner), then a switch
    of ron in parallel closes 100 ns after the ramp ends (a: 600 ns, b: 300 ns): from then on vdd is a stiff pin.
    sup 'ideal': VDDS straight on vdd (no feed R), ramp as a 32-point raised cosine (no slope corner)."""
    import math
    L = text.splitlines()
    i = next(j for j, x in enumerate(L) if x.startswith("VDDS "))
    if sup == "sw":
        ton = 600e-9 if order == "a" else 300e-9
        L[i + 1] = "RVDD vdds vdd 10"
        L.insert(i + 2, f"VSWC swc 0 PWL(0 0 {ton:.4e} 0 {ton + 10e-9:.4e} 1)\nSVDD vdds vdd swc 0 swst\n"
                        f".model swst sw vt=0.5 vh=0.2 ron={ron:g} roff=1e12")
    elif sup == "ideal":
        t0, t1 = (400e-9, 500e-9) if order == "a" else (100e-9, 200e-9)
        pts = [(0.0, 0.0)] + [(t0 + (t1 - t0) * n / 32, vd * 0.5 * (1 - math.cos(math.pi * n / 32))) for n in range(33)]
        L[i] = "VDDS vdd 0 PWL(" + " ".join(f"{t:.6e} {v:.9f}" for t, v in pts) + ")"
        L[i + 1] = "* RVDD removed (ideal pin)"
    return "\n".join(L) + "\n"


def _wrap(split=False, reltol=None, sup=None, ron=1e-3):
    def f(*a, **k):
        text, meta = st_deck(*a, **k)
        if sup:
            text = _supply(text, sup, a[2], meta["vdd"], ron)
            meta["rv"] = f"{sup}:{ron:g}"
        if split:
            text = _split(text)
        if reltol:
            text = text.replace("reltol=1e-5", f"reltol={reltol:g}")
        meta["probe"] = dict(split=split, reltol=reltol, sup=sup, ron=ron)
        return text, meta
    return f


def deck_list2():
    """Second set (after st_r001_split aborted at the 400 ns ramp corner, 'v.xc.viob2pb#branch')."""
    T, B = ("tt", 27, "a"), ("ff", -40, "b")
    st, k = {"T8": "pass"}, dict(sub=False)
    D = {
        "st_sw_split": (_wrap(True, sup="sw"), T, dict(k), st),
        "st_sw": (_wrap(sup="sw"), T, dict(k), st),
        "st_kp2_sw": (_wrap(sup="sw"), T, dict(k, mut="kp2"), st),
        "st_ideal": (_wrap(sup="ideal"), T, dict(k), st),
        "st_sw_ron01m": (_wrap(sup="sw", ron=1e-4), T, dict(k), st),                       # tighter: 10x stiffer
        "st_sw_rt6": (_wrap(sup="sw", reltol=1e-6), T, dict(k), st),                     # tighter: reltol 1e-6
        "st_brk_noclamp_sw": (_wrap(sup="sw"), T, dict(k, mut="noclamp"), {"T8": "reject"}),
        "st_brk_vdd200_sw": (_wrap(sup="sw"), T, dict(k, vd=2.0), {"T8": "reject"}),
        "st_kp2_ff-40_b_sw": (_wrap(sup="sw"), B, dict(k, mut="kp2"), st),
        "st_ff-40_b_sw": (_wrap(sup="sw"), B, dict(k), st),
    }
    for base in ("st_sw", "st_kp2_sw"):
        for nm, kw in (("sus195", dict(sus_lim=1.95)), ("cap20", dict(cap=2.0)), ("dur01", dict(dur_max=0.1e-9))):
            fn, a, kk, _ = D[base]
            D[f"st_chk_{nm}_{base[3:]}"] = (fn, a, kk, {"T8": "reject"}, dict(judge_from=base, **kw))
    return D


def deck_list():
    T = ("tt", 27, "a")
    st = {"T8": "pass"}
    D = {
        "st_r001_split": (_wrap(True), T, dict(rv=0.01, sub=False), st),
        "st_p10_split": (_wrap(True), T, dict(rv=10.0, sub=True), st),         # WO-81 basis, reproduces 600c547
        "st_kp2_r001": (_wrap(), T, dict(mut="kp2", rv=0.01, sub=False), st),
        "st_r01": (_wrap(), T, dict(rv=0.1, sub=False), st),
        "st_r001_rt6": (_wrap(reltol=1e-6), T, dict(rv=0.01, sub=False), st),
        "st_r1": (_wrap(), T, dict(rv=1.0, sub=False), st),
        "st_brk_noclamp_r001": (_wrap(), T, dict(mut="noclamp", rv=0.01, sub=False), {"T8": "reject"}),
        "st_brk_vdd200_r001": (_wrap(), T, dict(vd=2.0, rv=0.01, sub=False), {"T8": "reject"}),
        "st_kp2_ff-40_b_r001": (_wrap(), ("ff", -40, "b"), dict(mut="kp2", rv=0.01, sub=False), st),
        "one_kp2_ss-40_162": (one_deck, (*SS40, 1.5, 4e6), dict(mut="kp2"), {"T5": "pass", "T2band": "pass"}),
        "one_kp2_fs+125_198": (one_deck, ("fs", 125, 1.98, 1.5, 4e6), dict(mut="kp2"), {"T5": "pass"}),
        "cyc_kp2_ss-40_162": (cyc_deck, (*SS40, 1.5, 4e6), dict(mut="kp2"),
                              {"T1": "pass", "T2": "pass", "T7": "pass", "T10": "pass", "T10nz": "pass"}),
    }
    # D81 checker copies, judge-only, on both stiff-basis base rows (live only where the base row passes)
    for base in ("st_r001_split", "st_kp2_r001"):
        for nm, kw in (("sus195", dict(sus_lim=1.95)), ("cap20", dict(cap=2.0)), ("dur01", dict(dur_max=0.1e-9))):
            fn, a, k, _ = D[base]
            D[f"st_chk_{nm}_{base[3:]}"] = (fn, a, k, {"T8": "reject"}, dict(judge_from=base, **kw))
    return D


def gen(out, dl=None):
    c3_tb.deck_list = dl or deck_list
    c3_tb.gen(out)
    jf = os.path.join(os.path.abspath(out), "jobs.txt")
    me = os.path.abspath(__file__)
    J = []
    for ln in open(jf).read().split("\n"):
        if "_split" in ln and "ngspice" in ln:
            d = ln.split()[1]
            ln = ln.replace(f"; {sys.executable}", f"; {sys.executable} {me} ipost {d} > {d}/ipost.log 2>&1; {sys.executable}", 1)
        J.append(ln)
    open(jf, "w").write("\n".join(J))


def _runs(t, ab):
    import numpy as np
    d = np.diff(np.concatenate(([0], ab.astype(np.int8), [0])))
    st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0] - 1
    return [(t[i], t[j]) for i, j in zip(st, en)]


def ipost(d):
    import numpy as np
    w = c3_tb._read_raw(os.path.join(d, "st.raw"))
    m = json.load(open(os.path.join(d, "meta.json")))
    t, vdd, vs = w["time"], w["vdd"], m["vdd"]
    L = [f"meta rv={m['rv']} sub={m['sub']} vd={vs} npts={len(t)}"]
    ss = t > 600e-9                        # after both power-up orders
    hi = ss & (vdd > vs + 1e-6)
    dtw = np.gradient(t)
    L.append(f"vdd max {vdd.max():.7f} at {t[np.argmax(vdd)] * 1e9:.2f} ns; time with vdd > set+1uV (t>600ns) "
             f"{(dtw[hi]).sum() * 1e9:.1f} of {(dtw[ss]).sum() * 1e9:.1f} ns")
    rr = [(a, b) for a, b in _runs(t, ss & (vdd > vs + 10e-6)) if b - a > 1e-9]
    L.append(f"intervals vdd > set+10uV longer than 1 ns: {len(rr)}; first: "
             + "; ".join(f"{a * 1e9:.1f}-{b * 1e9:.1f}" for a, b in rr[:12]))
    avg = lambda x, msk: float((x[msk] * dtw[msk]).sum() / dtw[msk].sum()) if msk.any() else float("nan")
    br = {k: v for k, v in w.items() if k.endswith("#branch")}
    msk = hi if hi.any() else ss
    L.append(f"mask = {'vdd above set' if hi.any() else 't>600ns'}; i(VDDS) mean {avg(br.get('vdds#branch', t * 0), msk) * 1e6:.2f} uA"
             " (ngspice sign: + = current into the source + terminal from the circuit, i.e. reverse into the supply)")
    rows = sorted(((avg(v, msk), avg(v, ss), k) for k, v in br.items() if k.startswith("v.xc.vi")))
    L.append("per terminal mean current over mask / over t>600ns (uA), + = drawn from vdd, - = returned into vdd:")
    for r in rows[:10] + [None] + rows[-6:]:
        if r is None:
            L.append("  ...")
        else:
            a, b, k = r
            L.append(f"  {k[7:-7]:10s} {a * 1e6:9.2f} {b * 1e6:9.2f}")
    # node residuals vs vdd (Sb3 gb = nb2 - vss; op/on M4 gb)
    for nd in ("nb2", "ob2", "op", "on", "ap", "an", "dp", "dn"):
        x = w.get(f"xc.{nd}")
        if x is None or not ss.any():
            continue
        e = x - vdd
        exc = np.maximum(0.0, vdd - vs) if m["sub"] else 0.0
        xj = x - exc
        runs = sorted(((b - a, a, b) for a, b in _runs(t, xj > 1.98)), reverse=True)[:1]
        s = ""
        if runs:
            _, a, b = runs[0]
            k = (t >= a) & (t <= b)
            s = (f" longest judged>1.98 {(b - a) * 1e9:.1f} ns {a * 1e9:.1f}-{b * 1e9:.1f}: {nd}-vdd max {e[k].max() * 1e6:.2f} uV"
                 f" mean {avg(e, k) * 1e6:.2f} uV, vdd mean {avg(vdd, k):.7f}")
        L.append(f"{nd}: max {x.max():.5f} V at {t[np.argmax(x)] * 1e9:.2f} ns, max({nd}-vdd) t>600ns "
                 f"{e[ss].max() * 1e3:.3f} mV{s}")
    open(os.path.join(d, "probe.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))



# WO-86 (C3j) set 3: device terminal currents (no ammeters: an ideal source on vdd aborts at the ramp corner).
IDEV = {  # instance -> PDK inner model (the m-line inside the PDK subckt)
    **{n: "nfet_01v8" for n in ("M3", "M4", "Bn2n", "Bo2n", "Bo1n", "Bn1n", "Sb3", "Sq3")},
    **{n: "pfet_01v8" for n in ("M5", "M6", "R0", "R1", "R2", "R3", "KPo", "KPn", "Bn2p", "Bo2p", "Bo1p", "Bn1p",
                                "Sb1", "Sq1")},
    **{n: "nfet_g5v0d10v5" for n in ("M1", "M2", "K1", "K2")},
    **{n: "pfet_g5v0d10v5" for n in ("P1", "P2")},
}


def _ivec(n, term):
    return f"@m.xc.x{n.lower()}.msky130_fd_pr__{IDEV[n]}[i{term}]"


def _isave(fn):
    def f(*a, **k):
        text, meta = fn(*a, **k)
        vec = " ".join(_ivec(n, "d") for n in IDEV)   # WO-88 smoke: [is]/[ib] are 0-long in tran (write aborts)
        out = []
        for ln in text.splitlines():
            if ln.startswith("tran ") and not out[-1].startswith("save all"):
                out.append("save all " + vec)
            if ln.startswith("write st.raw"):
                ln += " " + vec
            out.append(ln)
        meta["probe"] = dict(meta.get("probe", {}), isave=True)
        return "\n".join(out) + "\n", meta
    return f


def deck_list3():
    T = ("tt", 27, "a")
    return {"st_sw_icur": (_isave(_wrap(sup="sw")), T, dict(sub=False), {"T8": "pass"}),
            "st_kp2_sw_icur": (_isave(_wrap(sup="sw")), T, dict(sub=False, mut="kp2"), {"T8": "pass"})}


def _iget(w, n, tm):
    """WO-92: the WO-88 probe found no device vector by exact name (raw naming differs from the display name), so
    match on the instance path and the terminal tag instead; None if absent."""
    v = w.get(_ivec(n, tm).lower())
    if v is not None:
        return v
    hit = [k for k in w if f"xc.x{n.lower()}.msky130_fd_pr__" in k and f"[i{tm}]" in k]
    return w[hit[0]] if len(hit) == 1 else None


def dpost(d):
    """Longest run with node > vdd (t > 600 ns) for op/on/nb2/ob2/dp/dn/ap/an; mean excess and the mean drain /
    source / bulk current of every saved device over that run (ngspice sign: + = into the terminal)."""
    import numpy as np
    w = c3_tb._read_raw(os.path.join(d, "st.raw"))
    t, vdd = w["time"], w["vdd"]
    ss = t > 600e-9
    dtw = np.gradient(t)
    avg = lambda x, k: float((x[k] * dtw[k]).sum() / dtw[k].sum())
    term = {"d": 1, "g": 2, "s": 3, "b": 4}
    deck = open(os.path.join(d, "deck.sp")).read().splitlines()
    pins = {ln.split()[0][1:]: ln.split()[1:5] for ln in deck if ln.startswith("X") and ln.split()[0][1:] in IDEV}
    L = [f"npts={len(t)} vdd max {vdd[ss].max():.7f}"]
    L.append("current vectors in raw: " + (", ".join(k for k in w if "[i" in k or k.startswith("i(")) or "NONE"))
    for nd in ("op", "on", "nb2", "ob2", "dp", "dn", "ap", "an"):
        x = w.get(f"xc.{nd}")
        if x is None:
            continue
        e = x - vdd
        runs = sorted(((b - a, a, b) for a, b in _runs(t, ss & (e > 0)) if b > a), reverse=True)
        if not runs:
            L.append(f"{nd}: never above vdd after 600 ns (max {e[ss].max() * 1e6:.2f} uV)")
            continue
        _, a, b = runs[0]
        k = (t >= a) & (t <= b)
        L.append(f"{nd}: longest above vdd {(b - a) * 1e9:.1f} ns ({a * 1e9:.1f}-{b * 1e9:.1f}), excess mean "
                 f"{avg(e, k) * 1e6:.2f} uV max {e[k].max() * 1e6:.2f} uV; V(clk) mean {avg(w['clk'], k):.3f}; "
                 f"x2p/x2n {avg(w['x2p'], k):.3f}/{avg(w['x2n'], k):.3f}; ap/an {avg(w['xc.ap'], k):.4f}/"
                 f"{avg(w['xc.an'], k):.4f}; dp/dn {avg(w['xc.dp'], k):.5f}/{avg(w['xc.dn'], k):.5f}")
        rows = []
        for n, p in pins.items():
            for tm in ("d", "s", "b"):
                if p[term[tm] - 1] == nd:
                    v = _iget(w, n, tm)
                    if v is not None:
                        rows.append((avg(v, k), f"{n}.{tm}"))
        L.append("   into-terminal mean currents on this node (nA; - = device pushes current into the node): "
                 + ", ".join(f"{nm} {c * 1e9:.3f}" for c, nm in sorted(rows)))
    open(os.path.join(d, "dpost.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def gen3(out, dl=None):
    gen(out, dl or deck_list3)
    jf = os.path.join(os.path.abspath(out), "jobs.txt")
    me = os.path.abspath(__file__)
    J = []
    for ln in open(jf).read().split("\n"):
        if "_icur" in ln and "ngspice" in ln:
            d = ln.split()[1]
            ln = ln.replace(f"; {sys.executable}", f"; {sys.executable} {me} dpost {d} > {d}/dpost.log 2>&1; {sys.executable}", 1)
        J.append(ln)
    open(jf, "w").write("\n".join(J))


def deck_list5():
    """WO-88 pool A: cap candidates on top of kp2 (st on the stiff switched pin at tt/27 a and ff/-40 b, T5/T2band at
    ss/-40 and fs/125), kp3 info, the rev f cyc rows never run (WO-86 item 1) and the device-current probe."""
    T, B, st, k = ("tt", 27, "a"), ("ff", -40, "b"), {"T8": "pass"}, dict(sub=False)
    D = {}
    for c in ("kp2_rsoW05", "kp2_rsoL03", "kp2_rsoL05", "kp3"):
        D[f"st_{c}_sw"] = (_wrap(sup="sw"), T, dict(k, mut=c), st)
        D[f"st_{c}_ff-40_b_sw"] = (_wrap(sup="sw"), B, dict(k, mut=c), st)
        D[f"one_{c}_ss-40_162"] = (one_deck, (*SS40, 1.5, 4e6), dict(mut=c), {"T5": "pass", "T2band": "pass"})
        D[f"one_{c}_fs+125_198"] = (one_deck, ("fs", 125, 1.98, 1.5, 4e6), dict(mut=c), {"T5": "pass"})
    D.update({f"{n}_revf": v for n, v in _DL0().items() if n.startswith("cyc_") and "info" not in n})
    D["st_sw_icur"] = (_isave(_wrap(sup="sw")), T, dict(k), {"T8": "pass"})
    return D


def deck_list4():
    """WO-88 full C3 set on the current default netlist: every one/cyc/mc/sens/pdk deck of c3_tb, and the T8 rows on
    the D90 basis (stiff switched pin) with the D83/D90 checker copies judged against a passing base."""
    T, A, B, st, k = ("tt", 27, "a"), ("ff", -40, "a"), ("ff", -40, "b"), {"T8": "pass"}, dict(sub=False)
    D = {n: v for n, v in _DL0().items() if not n.startswith("st_")}
    D.update({
        "st_tt27_a_sw": (_wrap(sup="sw"), T, dict(k), st),
        "st_tt27_b_sw": (_wrap(sup="sw"), ("tt", 27, "b"), dict(k), st),
        "st_ff-40_a_sw": (_wrap(sup="sw"), A, dict(k), st),
        "st_ff-40_b_sw": (_wrap(sup="sw"), B, dict(k), st),
        "st_ff125_b_sw": (_wrap(sup="sw"), ("ff", 125, "b"), dict(k), st),
        "st_brk_noclamp_sw": (_wrap(sup="sw"), T, dict(k, mut="noclamp"), {"T8": "reject"}),
        "st_brk_vdd200_sw": (_wrap(sup="sw"), T, dict(k, vd=2.0), {"T8": "reject"}),
        "st_chk_sus1985_sw": (_wrap(sup="sw"), T, dict(k, vd=1.985), {"T8": "reject"}),   # D90: S ~1.985 V
        "st_brk_in18_sw": (_wrap(sup="sw"), T, dict(k, mut="in18"), {"T8": "reject"}),
        "st_revf_ff-40_b_sw": (_wrap(sup="sw"), B, dict(k, mut="revf"), {"T8": "info"}),
        "st_info_edge01_tt27_a_sw": (_wrap(sup="sw"), T, dict(k, edge="ideal"), {"T8": "info"}),
        "st_sw_icur": (_isave(_wrap(sup="sw")), T, dict(k), {"T8": "info"}),   # WO-92: leak-path probe rerun (rev g)
    })
    for nm, kw in (("sus195", dict(sus_lim=1.95)), ("cap20", dict(cap=2.0)), ("dur01", dict(dur_max=0.1e-9)),
                   ("jn20", dict(jlim=2.0))):
        fn, a, kk, _ = D["st_tt27_a_sw"]
        D[f"st_chk_{nm}_sw"] = (fn, a, kk, {"T8": "reject"}, dict(judge_from="st_tt27_a_sw", **kw))
    return D


def gen5(out, dl):
    gen3(out, dl)      # gen + the dpost hook on any _icur deck


if __name__ == "__main__":
    {"gen": gen, "gen2": lambda o: gen(o, deck_list2), "gen3": gen3, "gen4": lambda o: gen5(o, deck_list4),
     "gen5": lambda o: gen5(o, deck_list5), "ipost": ipost, "dpost": dpost}[sys.argv[1]](sys.argv[2])
