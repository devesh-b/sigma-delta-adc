#!/usr/bin/env python3
"""WO-103: C4 delay caps MIM -> MOS (D93). Sandbox only.

    python run103.py size OUT                    # chain-delay sizing sweep (tt / ss_m40 / ff_m40) -> OUT/size.json
    python run103.py jobs OUT                    # OUT/jobs.txt for lpool.sh (tim: mim / none / nocap)
    python run103.py run CORNER FS MUT OUT       # one tim job via c4_tb.run (mut tokens mim / nocap enabled)
    python run103.py report OUT                  # OUT/table.md + table.json; exit 2 on a gate fail or missing job

Gate per (corner, fs), MOS (`none`) against the MIM reference (`mim`), same deck:
  every dead-time row x in DT: |x - x_mim| <= max(10 % |x_mim|, 0.15 ns), and a missing value fails;
  every c4_tb tim check that passes with MIM passes with MOS (no new failures).
Broken copy `nocap` (first cs-chain cap removed) must REJECT on the same gate (the g rows).
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "design", "c4_sw"))
import netlist as N  # noqa: E402
import c4_tb as TB  # noqa: E402

TB.GEN_MUTS = TB.GEN_MUTS + ("mim", "nocap")
CHAINS = dict(g=(N.K_G, N.C_G), e=(N.K_E, N.C_E), s=(N.K_S, N.C_S))
NCAP = dict(g=2 * N.K_G, e=2 * N.K_E, s=N.K_S)            # caps per chain kind in the generator (14 total)
WS = (2.0, 3.0, 4.0, 6.0, 8.0, 10.0)
L_C = 2.0
SIZE_CORNERS = ("tt_27",)        # sizing at tt only (WO); corners are checked in tim
CORN = TB.TIM_CORNERS
FS2 = ("ff_m40", "ss_125")          # 4M aborted there in WO-85 (bench); 2M added as the fallback pair
DT = ("g_min", "g50_max", "eb_min", "strobe_pre", "o1_pre", "r13_pre", "r13_post")
TOL_REL, TOL_ABS = 0.10, 0.15e-9


def size_deck(corner, kind, dev):
    p, t, va, _ = TB.CORNERS[corner]
    k, c = CHAINS[kind]
    L = [f"* WO-103 size {corner} {kind} {dev}", f'.lib "{N.LIB}" {p}', f".include {N.HVL}", f".temp {t}",
         f"Vdd vdd 0 {va}", "Vss vss 0 0", f"Vin in_s 0 PULSE(0 {va} 2n 0.2n 0.2n 20n 40n)", "Rin in_s in 10",
         "Cin in 0 5f", N.inv("drv", "in", "a")] + N.chain("x", "a", "y", k, c, dev) + [N.inv("ld", "y", "yl")]
    h = va / 2
    L += [".tran 5p 45n", f".meas tran dfall TRIG v(a) VAL={h} FALL=1 TARG v(y) VAL={h} FALL=1",
          f".meas tran drise TRIG v(a) VAL={h} RISE=1 TARG v(y) VAL={h} RISE=1", ".end"]
    return "\n".join(L) + "\n"


def size(out):
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, ".spiceinit"), "w").write("set num_threads=1\n")
    res = {}
    for corner in SIZE_CORNERS:
        for kind in CHAINS:
            for dev in [None] + [(w, L_C) for w in WS]:
                tag = f"size_{corner}_{kind}_{'mim' if dev is None else 'w%g' % dev[0]}"
                open(os.path.join(out, tag + ".sp"), "w").write(size_deck(corner, kind, dev))
                r = subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=600)
                v = {}
                for nm in ("dfall", "drise"):
                    mm = re.search(rf"^{nm}\s*=\s*([-+0-9.eE]+)", r.stdout, re.M)
                    v[nm] = float(mm.group(1)) if mm else None
                res[tag] = v
    pick = {}
    for kind in CHAINS:
        tgt = sum(res[f"size_tt_27_{kind}_mim"].values()) / 2
        pts = [(w, sum(res[f"size_tt_27_{kind}_w{w:g}"].values()) / 2) for w in WS]
        w_sel = None
        for (w0, d0), (w1, d1) in zip(pts, pts[1:]):
            if d0 <= tgt <= d1:
                w_sel = w0 + (tgt - d0) * (w1 - w0) / (d1 - d0)
        pick[kind] = dict(target=tgt, w=None if w_sel is None else round(w_sel + 0.005, 2), l=L_C)
    json.dump(dict(res=res, pick=pick), open(os.path.join(out, "size.json"), "w"), indent=1)
    for kind, p in pick.items():
        print(f"{kind}: target {p['target'] * 1e9:.3f} ns -> W {p['w']} L {p['l']}")


def jobs(out):
    me = os.path.abspath(__file__)
    pairs = [(c, "4M") for c in CORN] + [(c, "2M") for c in FS2]
    j = [(c, f, m) for c, f in pairs for m in ("mim", "none")]
    j += [(c, f, "nocap") for c, f in (("tt_27", "4M"), ("ss_m40", "4M"), ("ff_m40", "2M"))]
    open(os.path.join(out, "jobs.txt"), "w").write("".join(f"python {me} run {c} {f} {m} {out}\n" for c, f, m in j))
    print(len(j), "jobs")


def load(out, c, f, m):
    p = os.path.join(out, f"tim_{c}_{f}_{m}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def gate(x, ref):
    """-> (pass, list of failing items). x / ref are c4_tb result dicts."""
    if not x or not ref or not x["ok"] or not ref["ok"]:
        return False, ["MISSING/ABORT " + ("mim" if not ref or not ref["ok"] else "x")]
    bad = []
    for r in DT:
        a, b = x["m"].get(r), ref["m"].get(r)
        if a is None or b is None or abs(a - b) > max(TOL_REL * abs(b), TOL_ABS):
            bad.append(r)
    bad += [f"new fail {k}" for k, (_, okr) in ref["ck"].items() if okr and not x["ck"][k][1]]
    return not bad, bad


def ns(v):
    return "MISSING" if v is None else f"{v * 1e9:.3f}"


def report(out):
    pairs = [(c, "4M") for c in CORN] + [(c, "2M") for c in FS2]
    L = ["| corner | fs | " + " | ".join(f"{r} MIM / MOS (ns)" for r in DT) + " | c4_tb fails (MIM ; MOS) | gate |",
         "|" + "---|" * (len(DT) + 4)]
    js, fail = {}, []
    for c, f in pairs:
        ref, x = load(out, c, f, "mim"), load(out, c, f, "none")
        ok, bad = gate(x, ref)
        js[f"{c}_{f}"] = dict(ok=ok, bad=bad)
        cells = [f"{ns(ref['m'].get(r) if ref and ref['ok'] else None)} / {ns(x['m'].get(r) if x and x['ok'] else None)}"
                 for r in DT]
        fl = lambda d: ",".join(k for k, v in d["ck"].items() if not v[1]) if d and d["ok"] else "ABORT"  # noqa: E731
        L.append(f"| {c} | {f} | " + " | ".join(cells) + f" | {fl(ref)} ; {fl(x)} | {'PASS' if ok else 'FAIL ' + ','.join(bad)} |")
        if not ok:
            fail.append(f"{c}_{f}: {bad}")
    L += ["", "| broken copy | corner | fs | gate vs MIM | verdict |", "|---|---|---|---|---|"]
    for c, f in (("tt_27", "4M"), ("ss_m40", "4M"), ("ff_m40", "2M")):
        ref, x = load(out, c, f, "mim"), load(out, c, f, "nocap")
        ok, bad = gate(x, ref)
        aborted = any(b.startswith("MISSING") for b in bad)
        v = "MISSING" if aborted else ("NOT REJECTED" if ok else "REJECT (good)")
        g = ",".join(f"{r} {ns(x['m'].get(r))}" for r in ("g_min", "g50_max")) if x and x["ok"] else "-"
        L.append(f"| nocap | {c} | {f} | {','.join(bad) or 'pass'} ({g}) | {v} |")
        js[f"nocap_{c}_{f}"] = dict(ok=ok, bad=bad)
        if v != "REJECT (good)":
            fail.append(f"nocap {c}_{f}: {v}")
    open(os.path.join(out, "table.md"), "w").write("\n".join(L) + "\n")
    json.dump(js, open(os.path.join(out, "table.json"), "w"), indent=1)
    print("\n".join(L))
    print("FAILS:", fail or "none")
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "size":
        size(a[1])
    elif a[0] == "jobs":
        jobs(a[1])
    elif a[0] == "run":
        sz = os.path.join(a[4], "..", "size", "size.json")    # tt sizing result overrides the committed DCAP
        if a[3] != "mim" and os.path.exists(sz):
            N.DCAP.update({k: (p["w"], p["l"]) for k, p in json.load(open(sz))["pick"].items() if p["w"]})
        TB.run("tim", a[1], a[2], a[3], a[4])
    elif a[0] == "report":
        report(a[1])
