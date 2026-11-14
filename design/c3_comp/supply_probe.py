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


def _wrap(split=False, reltol=None):
    def f(*a, **k):
        text, meta = st_deck(*a, **k)
        if split:
            text = _split(text)
        if reltol:
            text = text.replace("reltol=1e-5", f"reltol={reltol:g}")
        meta["probe"] = dict(split=split, reltol=reltol)
        return text, meta
    return f


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


def gen(out):
    c3_tb.deck_list = deck_list
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
        if x is None:
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


if __name__ == "__main__":
    {"gen": gen, "ipost": ipost}[sys.argv[1]](sys.argv[2])
