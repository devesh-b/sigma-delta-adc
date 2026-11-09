#!/usr/bin/env python3
"""WO-21 (C1a rev B) device-level .op spot checks (NOT a C1b gate). Sandbox only:
    python revb_unit_checks.py OUTDIR

Three small decks per corner, all .op:
  (a) input-pair candidates (pfet_01v8, bulk = source) at I_TAIL/2 base and boost: gm, gm/Id, Cgg, Vdsat, Vsg;
  (b) stacked m_n + m_nc and m_pl + m_pc with the Vdsat-tracking diode bias (density factor K) -> Vds - Vdsat;
  (c) vg switches (input chopper / island): nfet_01v8 1.8 V-driven (the rejected rev-A device), nfet_g5v0d10v5,
      and a g5v0d10v5 TG, all driven from VAPWR, Ron at vg CM 1.07 / 1.20 / 1.33 V; terminal C.
Every number printed is checked for NaN; a missing value prints MISSING and the exit code is nonzero.
"""
import json, math, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sizes_draft as S

LIB = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.tech/ngspice/sky130.lib.spice"
CORNERS = [("tt", 27, 3.3), ("ss", -40, 3.0), ("ss", 125, 3.0), ("fs", 125, 3.0), ("sf", 125, 3.0),
           ("ff", -40, 3.6), ("ff", 125, 3.6)]
PAIRS = {"W40L1": (10, 4, 1.0), "W80L1": (10, 8, 1.0), "W80L0p5": (10, 8, 0.5),
         "W120L0p5": (10, 12, 0.5), "W160L0p5": (10, 16, 0.5), "W120L0p75": (10, 12, 0.75)}
KS = (3.0, 4.0, 6.0)
VCMS = (1.07, 1.20, 1.33)
SW = {"n18": ("nfet_01v8", 1.0, 0.15), "n33": ("nfet_g5v0d10v5", 4.0, 0.5),
      "tgn": ("nfet_g5v0d10v5", 2.0, 0.5), "tgp": ("pfet_g5v0d10v5", 4.0, 0.5)}
Q = ("gm", "gds", "id", "vdsat", "cgg", "cgs", "cgd", "cdd", "cbd", "cbs")


def mos(n, d, g, s, b, dev, wf, m, l):
    return f"X{n} {d} {g} {s} {b} sky130_fd_pr__{dev} w={wf} l={l} m={m}"


def par(n, dev, q):
    return f"@m.x{n}.msky130_fd_pr__{dev}[{q}]"


def deck(c, t, v):
    L = [f"* WO-21 unit {c} {t} {v}", f".lib {LIB} {c}", f".temp {t}", ".option gmin=1e-15",
         f"Vdd vdd 0 {v}", f"Vg18 g18 0 1.62", "Vicm icm 0 1.2", "Vdin din 0 1.1", "Vo ocm 0 1.5"]
    saves = []
    # (a) pairs
    for k, (wf, m, l) in PAIRS.items():
        for b in (1, 2):
            n = f"p{k}b{b}".lower()
            L += [mos(n, "din", "icm", f"s{n}", f"s{n}", "pfet_01v8", wf, m, l), f"I{n} vdd s{n} {S.I_TAIL/2*b:.6e}"]
            saves += [(n, "pfet_01v8", q) for q in ("gm", "id", "vdsat", "cgg")] + [(n, None, f"v(s{n})")]
    # (b) cascode stacks with tracking bias, both modes, each K
    sn, snc, spl, spls, spc = (S.SIZES[x] for x in ("m_n", "m_nc", "m_pl", "m_plc", "m_pc"))
    for kf in KS:
        for b in (1, 2):
            tg = f"k{int(kf)}b{b}"
            isk, it = S.I_SINK * b, S.I_TAIL * b
            inc = isk - it / 2
            L += [mos(f"nr{tg}", f"bn{tg}", f"bn{tg}", "0", "0", sn["dev"], sn["WF"], sn["M"] // 4, sn["L"]),
                  f"Inr{tg} vdd bn{tg} {isk/4:.6e}",
                  mos(f"n{tg}", f"f{tg}", f"bn{tg}", "0", "0", sn["dev"], sn["WF"], sn["M"], sn["L"]),
                  f"Iinj{tg} vdd f{tg} {it/2:.6e}",
                  # diode: W of m_nc / 8 at L = K * L_nc  -> current density K x below... see DESIGN.md 2.4
                  mos(f"bnc{tg}", f"vbnc{tg}", f"vbnc{tg}", "0", "0", snc["dev"], snc["WF"], 1, snc["L"] * kf),
                  f"Ibnc{tg} vdd vbnc{tg} {inc*snc['WF']/(snc['WF']*snc['M']):.6e}",
                  mos(f"nc{tg}", "ocm", f"vbnc{tg}", f"f{tg}", "0", snc["dev"], snc["WF"], snc["M"], snc["L"]),
                  # PMOS side: fixed load (gate from diode at I_LOAD*share) + CMFB section on the same gate here
                  mos(f"plr{tg}", f"bp{tg}", f"bp{tg}", "vdd", "vdd", spl["dev"], spl["WF"], spl["M"] // 4, spl["L"]),
                  f"Iplr{tg} bp{tg} 0 {inc*S.LOAD_FIXED/4:.6e}",
                  mos(f"pl{tg}", f"sl{tg}", f"bp{tg}", "vdd", "vdd", spl["dev"], spl["WF"], spl["M"], spl["L"]),
                  f"Iplc{tg} vdd sl{tg} {inc*(1-S.LOAD_FIXED):.6e}",   # CMFB section current (sources into sl), ideal here
                  mos(f"bpc{tg}", f"vbpc{tg}", f"vbpc{tg}", "vdd", "vdd", spc["dev"], spc["WF"], 1, spc["L"] * kf),
                  f"Ibpc{tg} vbpc{tg} 0 {inc*spc['WF']/(spc['WF']*spc['M']):.6e}",
                  mos(f"pc{tg}", f"opc{tg}", f"vbpc{tg}", f"sl{tg}", f"sl{tg}", spc["dev"], spc["WF"], spc["M"], spc["L"]),
                  f"Vopc{tg} opc{tg} 0 1.5"]
            saves += [(f"n{tg}", sn["dev"], "vdsat"), (f"pl{tg}", spl["dev"], "vdsat"),
                      (f"nc{tg}", snc["dev"], "vdsat"), (f"pc{tg}", spc["dev"], "vdsat"),
                      (f"n{tg}", sn["dev"], "cgg"), (f"pl{tg}", spl["dev"], "cgg"),
                      (None, None, f"v(f{tg})"), (None, None, f"v(sl{tg})"), (None, None, f"v(vbnc{tg})"), (None, None, f"v(vbpc{tg})")]
    # (c) switches: 1 mV across, at each CM
    for i, vc in enumerate(VCMS):
        L += [f"Va{i} a{i} 0 {vc+0.0005}", f"Vb{i} b{i} 0 {vc-0.0005}"]
        for k, (dev, w, l) in SW.items():
            gate = "g18" if k == "n18" else ("0" if k == "tgp" else "vdd")
            bulk = "vdd" if k == "tgp" else "0"
            L += [mos(f"s{k}{i}", f"a{i}", gate, f"b{i}", bulk, dev, w, 1, l)]
            saves += [(f"s{k}{i}", dev, q) for q in ("id", "cgg", "cgs", "cgd", "cbd", "cbs")]
    L += [".control", "op"]
    for n, dev, q in saves:
        L.append(f"print {q}" if n is None or dev is None else f"print {par(n, dev, q)}")
    L += ["quit", ".endc", ".end"]
    return "\n".join(L)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    bad = 0
    res = {}
    for c, t, v in CORNERS:
        tag = f"{c}_{t}_{v}".replace("-", "m").replace(".", "p")
        fn = os.path.join(out, f"unit_{tag}.sp")
        open(fn, "w").write(deck(c, t, v))
        r = subprocess.run(["ngspice", "-b", os.path.abspath(fn)], cwd=out, capture_output=True, text=True, timeout=600)
        vals = {}
        for ln in r.stdout.splitlines():
            if " = " in ln:
                k, _, x = ln.partition(" = ")
                try:
                    vals[k.strip()] = float(x.split()[0])
                except ValueError:
                    pass
        g = lambda k: vals.get(k, float("nan"))
        d = {}
        for k, (wf, m, l) in PAIRS.items():
            for b in (1, 2):
                n = f"p{k}b{b}".lower()
                p = lambda q: g(par(n, "pfet_01v8", q))
                gm, i_d = p("gm"), abs(p("id"))
                d[f"pair_{k}_b{b}"] = dict(gm_uS=gm * 1e6, gmid=gm / i_d if i_d else float("nan"),
                                           cgg_fF=p("cgg") * 1e15, vdsat=p("vdsat"), vsg=g(f"v(s{n})") - 1.2,
                                           vsd=g(f"v(s{n})") - 1.1)
        for kf in KS:
            for b in (1, 2):
                tg = f"k{int(kf)}b{b}"
                q = lambda n, dev, x: g(par(n + tg, S.SIZES[dev]["dev"], x))
                vf, vsl = g(f"v(f{tg})"), v - g(f"v(sl{tg})")
                d[f"bias_{tg}"] = dict(v_fold=vf, vds_n_minus_vdsat=vf - q("n", "m_n", "vdsat"),
                                       vsd_pl=vsl, vsd_pl_minus_vdsat=vsl - abs(q("pl", "m_pl", "vdsat")),
                                       vds_nc_minus_vdsat=(1.5 - vf) - q("nc", "m_nc", "vdsat"),
                                       vsd_pc_minus_vdsat=(g(f"v(sl{tg})") - 1.5) - abs(q("pc", "m_pc", "vdsat")),
                                       vdsat_n=q("n", "m_n", "vdsat"), vdsat_pl=abs(q("pl", "m_pl", "vdsat")),
                                       cgg_n_fF=q("n", "m_n", "cgg") * 1e15, cgg_pl_fF=q("pl", "m_pl", "cgg") * 1e15)
        for i, vc in enumerate(VCMS):
            for k, (dev, w, l) in SW.items():
                p = lambda x: g(par(f"s{k}{i}", dev, x))
                d[f"sw_{k}_{vc}"] = dict(ron_ohm=1e-3 / abs(p("id")) if p("id") else float("inf"),
                                        cgg_fF=p("cgg") * 1e15, cbd_fF=p("cbd") * 1e15, cbs_fF=p("cbs") * 1e15)
            # TG = parallel n + p
            gn, gp = abs(g(par(f"stgn{i}", "nfet_g5v0d10v5", "id"))), abs(g(par(f"stgp{i}", "pfet_g5v0d10v5", "id")))
            d[f"sw_tg_{vc}"] = dict(ron_ohm=1e-3 / (gn + gp) if gn + gp else float("inf"))
        for k1, dd in d.items():
            for k2, x in dd.items():
                if isinstance(x, float) and math.isnan(x):
                    print(f"MISSING {tag} {k1}.{k2}")
                    bad += 1
        res[tag] = d
        print(json.dumps({tag: {k: {a: float(f"{b:.4g}") for a, b in x.items()} for k, x in d.items()}}), flush=True)
        if r.returncode:
            print("NGSPICE_ERR", tag, r.stderr[-600:])
            bad += 1
    json.dump(res, open(os.path.join(out, "revb_unit.json"), "w"), indent=1)
    print("VERDICT", "ACCEPT" if bad == 0 else f"REJECT ({bad} missing/err)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
