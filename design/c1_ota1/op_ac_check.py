#!/usr/bin/env python3
"""WO-20 spot check of the C1a hand numbers (NOT a C1b gate): .op / static A(v) / .ac / .noise of the OTA1 core.

Ideal pieces (stated, C1b replaces them): bias currents from ideal sources into mirror diodes, cascode and
protection gate voltages from replica diodes at the DESIGN.md target node voltages (ideal sources), CMFB = ideal
B-source on the PMOS load gates, DC offset servo through a 1e12 ohm || 1 F integrator (open for f >= 1 mHz).
Run on the sandbox only:  python design/c1_ota1/op_ac_check.py OUTDIR
"""
import json, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sizes_draft as S

LIB = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.tech/ngspice/sky130.lib.spice"
KT = 1.380649e-23


def mos(name, d, g, s, b, p):
    return f"{name} {d} {g} {s} {b} sky130_fd_pr__{p['dev']} w={p['WF']} l={p['L']} m={p['M']}"


def deck(sz, corner, temp, vdd, bst, tag, mc=0):
    it, isk = S.I_TAIL * bst, S.I_SINK * bst
    il = isk - it / 2
    L = [f"* WO-20 {tag}", f".lib {LIB} {corner}", f".temp {temp}", ".option gmin=1e-15 reltol=1e-6",
         f"Vdd vdd 0 {vdd}", f"Vddb vddb 0 {vdd}",
         # tail mirror
         mos("Xtr", "btp", "btp", "vddb", "vddb", sz["m_tr"]), f"Itr btp 0 {it*sz['m_tr']['M']/sz['m_t']['M']:.6e}",
         mos("Xt", "tail", "btp", "vdd", "vdd", sz["m_t"]),
         # input pair (bulk = tail), protection cascodes
         mos("Xm1", "da", "gp", "tail", "tail", sz["m_in"]), mos("Xm2", "db", "gm", "tail", "tail", sz["m_in"]),
         mos("Xpp1", "fa", "vpc", "da", "da", sz["m_pp"]), mos("Xpp2", "fb", "vpc", "db", "db", sz["m_pp"]),
         # sinks
         mos("Xnr", "bn", "bn", "0", "0", sz["m_nr"]), f"Inr vddb bn {isk*sz['m_nr']['M']/sz['m_n']['M']:.6e}",
         mos("Xn1", "fa", "bn", "0", "0", sz["m_n"]), mos("Xn2", "fb", "bn", "0", "0", sz["m_n"]),
         # cascodes and loads (side a fold -> output om, side b -> op)
         mos("Xnc1", "om", "vbnc", "fa", "0", sz["m_nc"]), mos("Xnc2", "op", "vbnc", "fb", "0", sz["m_nc"]),
         mos("Xpc1", "om", "vbpc", "sa", "sa", sz["m_pc"]), mos("Xpc2", "op", "vbpc", "sb", "sb", sz["m_pc"]),
         mos("Xpl1", "sa", "ctl", "vdd", "vdd", sz["m_pl"]), mos("Xpl2", "sb", "ctl", "vdd", "vdd", sz["m_pl"]),
         # replica bias: NMOS cascode gate, PMOS cascode gate, protection gate
         f"Vrf rf 0 {S.V_FOLD}", mos("Xrnc", "vbnc", "vbnc", "rf", "0", sz["m_nc"]), f"Irnc vddb vbnc {il:.6e}",
         f"Vrs vddb rs {S.V_SDL}", mos("Xrpc", "vbpc", "vbpc", "rs", "rs", sz["m_pc"]), f"Irpc vbpc 0 {il:.6e}",
         f"Vrd rd 0 {S.V_DIN}", mos("Xrpp", "vpc", "vpc", "rd", "rd", sz["m_pp"]), f"Irpp vpc 0 {it/2:.6e}",
         # ideal CMFB on the load gates
         f"Bcm ctl 0 V = {vdd - 1.0} + 50*(0.5*(V(op)+V(om)) - {S.V_OCM})",
         # inputs: servo node x, AC/noise source Vid, static target Vt
         f"Vicm icm 0 {S.V_ICM}", "Vid d 0 dc 0 ac 1", "Vvt vt 0 0",
         "Bgp gp 0 V = V(icm) + 0.5*(V(d) - V(x))", "Bgm gm 0 V = V(icm) - 0.5*(V(d) - V(x))",
         "Bx 0 x I = 1e-3*(V(op) - V(om) - V(vt))", "Rx x 0 1e12", "Cx x 0 1e9",
         f"Clp op 0 {S.C_L}", f"Clm om 0 {S.C_L}"]
    pi, pn, pnc, ppc, ppl, ppp = (f"@m.x{n}.msky130_fd_pr__{sz[k]['dev']}" for n, k in
                                  (("m1", "m_in"), ("n1", "m_n"), ("nc1", "m_nc"), ("pc1", "m_pc"), ("pl1", "m_pl"), ("pp1", "m_pp")))
    pars = [f"{p}[{q}]" for p in (pi, pn, pnc, ppc, ppl, ppp) for q in ("gm", "gds", "id", "vdsat", "cgg")]
    L += [".control", "set wr_singlescale", "set wr_vecnames"]
    if mc:
        L += [f"let k = 0", f"repeat {mc}", "op", "print v(x)", "reset", "end", "quit", ".endc", ".end"]
        return "\n".join(L)
    L += ["save all " + " ".join(pars), "op",
          "print v(tail) v(da) v(fa) v(sa) v(om) v(op) v(x) v(vpc) v(vbnc) v(vbpc) v(ctl) i(Vdd)"]
    L += [f"print {p}" for p in pars]
    L += ["dc Vvt -1.4 1.4 0.1", f"wrdata {tag}_dc.csv v(x) v(op,om)",
          "ac dec 40 1 1e10", f"wrdata {tag}_ac.csv v(op,om)",
          "noise v(op,om) Vid dec 20 10 1e9", "setplot noise1", f"wrdata {tag}_nz.csv inoise_spectrum",
          "quit", ".endc", ".end"]
    return "\n".join(L)


def run(text, tag, out):
    fn = os.path.join(out, tag + ".sp")
    open(fn, "w").write(text)
    r = subprocess.run(["ngspice", "-b", fn], cwd=out, capture_output=True, text=True, timeout=600)
    vals = {}
    for ln in r.stdout.splitlines():
        if " = " in ln:
            k, _, v = ln.partition(" = ")
            try:
                vals.setdefault(k.strip(), []).append(float(v.split()[0]))
            except ValueError:
                pass
    return vals, r


def load(fn):
    a = np.loadtxt(fn, skiprows=1)
    os.remove(fn)   # WO rule: delete raw csv after reading
    return a


def analyse(vals, tag, out, sz, temp, bst):
    g = lambda k: vals.get(k, [float("nan")])[-1]
    res = {k: g(k) for k in ("v(tail)", "v(da)", "v(fa)", "v(sa)", "v(om)", "v(op)", "v(x)", "v(vpc)", "v(vbnc)",
                             "v(vbpc)", "v(ctl)", "i(vdd)")}
    for k, v in vals.items():
        if k.startswith("@m."):
            res[k.split(".")[1] + "." + k.split("[")[1].rstrip("]")] = v[-1]
    dc = load(os.path.join(out, tag + "_dc.csv"))
    vt, vid = dc[:, 0], -dc[:, 1]
    vid0 = np.interp(0.0, vt, vid)
    m = np.abs(vt) > 0.05
    a_static = np.abs(vt[m] / (vid[m] - vid0))
    res["vos_servo"] = vid0
    res["A_static_min_dB_1p4"] = 20 * np.log10(a_static.min())
    ac = load(os.path.join(out, tag + "_ac.csv"))
    f, h = ac[:, 0], ac[:, 1] + 1j * ac[:, 2]
    mag = np.abs(h)
    res["A0_dB"] = 20 * np.log10(mag[0])
    i = np.argmax(mag < 1.0)
    ugf = np.exp(np.interp(0.0, -np.log(mag[i-1:i+1]), np.log(f[i-1:i+1])))
    ph = np.unwrap(np.angle(h)) * 180 / np.pi
    res["GBW_loaded_MHz"] = ugf / 1e6
    # loop PM at beta1: unity of beta*A
    j = np.argmax(mag * S.BETA1 < 1.0)
    fb = np.exp(np.interp(0.0, -np.log(mag[j-1:j+1] * S.BETA1), np.log(f[j-1:j+1])))
    phb = np.interp(np.log(fb), np.log(f), ph)
    res["PM_beta1_deg"] = 180.0 + (phb - ph[0])
    res["phase_dc_deg"] = ph[0]
    # equivalent fp2 from excess phase at the loop crossover (two-pole fit)
    ex = 90.0 - res["PM_beta1_deg"]
    res["fp2_eq_MHz"] = fb / np.tan(np.radians(ex)) / 1e6 if ex > 0.1 else float("inf")
    nz = load(os.path.join(out, tag + "_nz.csv"))
    fn, en = nz[:, 0], nz[:, 1]
    sw = np.interp(np.log(3e6), np.log(fn), en) ** 2
    res["en_3MHz_nV"] = np.sqrt(sw) * 1e9
    res["en_1kHz_nV"] = np.interp(np.log(1e3), np.log(fn), en) * 1e9
    k = np.argmax(en ** 2 < 2 * sw)
    res["fc_kHz"] = fn[k] / 1e3
    res["vn_sampled_uV"] = np.sqrt(sw * (np.pi / 2) * S.BETA1 * ugf) * 1e6
    gm1 = res.get("xm1.gm", float("nan"))
    res["gm1_uS"] = gm1 * 1e6
    res["gm_over_id_in"] = gm1 / abs(res.get("xm1.id", float("nan")))
    return res


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    corners = [("tt", 27, 3.3), ("ss", -40, 3.0), ("ss", 125, 3.0), ("ff", -40, 3.6), ("ff", 125, 3.6)]
    allres = []
    for vname, sz in (("long", S.SIZES), ("short", S.SIZES_SHORT)):
        for (c, t, v) in corners:
            for bst in (1.0, S.BOOST):
                tag = f"{vname}_{c}_{t}_{v}_b{int(bst)}".replace("-", "m").replace(".", "p")
                vals, r = run(deck(sz, c, t, v, bst, tag), tag, out)
                try:
                    res = analyse(vals, tag, out, sz, t, bst)
                except Exception as e:  # report, never silently pass
                    res = {"error": repr(e), "stderr": r.stderr[-800:]}
                res.update(variant=vname, corner=c, temp=t, vdd=v, boost=bst)
                allres.append(res)
                print(json.dumps({k: (float(f"{x:.4g}") if isinstance(x, float) else x) for k, x in res.items()}), flush=True)
    # mismatch spot check: input offset over MC runs (tt_mm, long, base)
    vals, r = run(deck(S.SIZES, "tt_mm", 27, 3.3, 1.0, "mc", mc=60), "mc", out)
    xs = np.array(vals.get("v(x)", []))
    mc = {"mc_n": int(xs.size), "mc_sigma_mV": float(np.std(xs) * 1e3) if xs.size else float("nan"),
          "mc_mean_mV": float(np.mean(xs) * 1e3) if xs.size else float("nan")}
    print(json.dumps(mc))
    json.dump({"runs": allres, "mc": mc}, open(os.path.join(out, "op_ac_check.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
