#!/usr/bin/env python3
"""BIAS_EXT wrapper `c6_cz` around `c6_bias` (WO-108, D99b). Sandbox only (ngspice, sky130A via PDK_ROOT).
c6_final.py is imported unchanged (WO-104 owns it).

  python c6_cz.py netlist [OUT.spice] [MUT]          # c6_bias + c6_cz subckts (default: stdout)
  python c6_cz.py jobs OUT FROZEN JOBFILE            # lpool job list: 5 corners x 3 kinds + broken copies
  python c6_cz.py run OUT KIND CORNER TEMP VDD [MUT] # one transient bench -> OUT/<tag>.json
        KIND s0 = sel 0, OTA1 bias diodes as loads, bare c6_bias next to the wrapper (G1)
             lk = sel 0, ports held at fixed voltages (worst off-switch Vds), bare next to the wrapper (G4)
             s1 = sel 1, bias_ext stepped 0/5/1/2/10/20/5 uA, boost, 0 again (G2, G3)
  python c6_cz.py summary OUT                        # verdict table -> stdout

Subckt: .subckt c6_cz vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok bias_ext bias_sel
  The c6_bias ports plus bias_ext (current into the pin, harness bandgap-referenced source) and bias_sel (static, 3.3 V domain
  = VAPWR, changes only while rst_n is low). TT: bias_sel 0, bias_ext VSSA.
Topology (results/wo108/README.md): c6_bias is instantiated unchanged. Every port goes through two 3.3 V transmission gates (5 V
  devices): c6 path (on for sel 0) and ext path (on for sel 1). The ext path is a replica of the mirror side of C6: a cascoded NMOS
  diode (the C6 two-half VN diode, boost half 2 switched by boost, scaled x K = I_NOM / I_TGT) with bias_ext as its input, the
  same sink fingers, ibn feed unit and PMOS VP diode. Ratio fixed at 1:K: bias_ext = I_NOM (5 uA) gives the C6 design port
  currents. The isolated core keeps running (own current ~ the c6 own current, no state to restore); its sink ports self-clamp at
  VGND, its ibn port floats up to VAPWR (all 5 V devices, every pair <= VAPWR + 0.3 V < 4.95 V).
  bias_ok: sel 0 = c6 ok; sel 1 = ext-present detect: a 16-unit mirror leg of the ext diode against a resistor pull-up, 3.3 V
  inverter; ok = 1 for bias_ext above ~0.5 uA.
Gates (WO-108 item 3; tt/27/3.3, ss/-40/3.0+3.6, ff/125/3.0+3.6):
  G1 (s0): wrapper port currents = bare c6_bias within 0.1 %, base and boost; ok high from 140 us.
  G2 (s1): tracking err (p(I)/p(5 uA))/(I/5 uA) - 1 <= 2 % for 1, 2, 10, 20 uA and the repeated 5 uA; port ratios +-3 %, boost/base
           2 +-4 %, tt absolute +-3 % of I_REF at 5 uA.
  G3 (s1): bias_ext open from power-up, sel 1: ok low (< 0.1 VDD) and port currents < 20 nA; ok >= 0.9 VDD at 1 and 5 uA.
           (Loss of the current after it was present: info only, the mirror gate holds its charge, see README.)
  G4 (lk): wrapper port currents = bare within 0.1 % with the ports held at VDD-0.3 (sinks) / 0.3 V (ibn).
  stress : every recorded wrapper node within [-0.05, VDD+0.05] V (all pairs <= VAPWR, devices 5 V class; the 1.8 V stress
           rules D80/D83/D90 apply to 1.8 V devices and none is used here).
Broken copies (each must REJECT its gate): swapsel (c6 path of ibp gated by sel -> G1), kwrong (ext diode x0.9 -> G2),
efinger (one ibp finger missing on the ext path -> G2), nodetect (ok forced high on the ext path -> G3), leaky (0.5 % of ibtp
leaks to VGND -> G4), overv (a 5.2 V node tied to the ext diode through 1 kOhm -> stress).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "design", "c6_bias"))
sys.path.insert(0, os.path.join(ROOT, "design", "c1_ota1"))
import c6_final as F  # noqa: E402
import c6_spot as B  # noqa: E402

x, P5, N5 = B.x, B.P5, B.N5
PORT_I = F.PORT_I
SINKS, PORTS_ALL = F.SINKS, tuple(F.PORT_I)
I_NOM = 5e-6                       # bias_ext giving the C6 design currents
K_EXT = I_NOM / B.I_TGT            # ext diode scale vs the C6 VN diode (4.67)
N_SENSE = 16                       # sense leg units (NW/NL unit each)
R_UP_L = 670.0                     # um xhigh_po 0p69 (about 1.9 MOhm): ext-present threshold ~0.5 uA
HVL = F.HVL
LS, INV, MUX = F.LS, F.INV, "sky130_fd_sc_hvl__mux2_1"
CPORTS = "vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok bias_ext bias_sel"
MUTS = ("swapsel", "kwrong", "efinger", "nodetect", "leaky", "overv")
TARGET = dict(swapsel="G1", kwrong="G2", efinger="G2", nodetect="G3", leaky="G4", overv="stress")
KIND_OF = dict(swapsel="s0", kwrong="s1", efinger="s1", nodetect="s1", leaky="lk", overv="s1")
CORNERS5 = [("tt", 27, 3.3), ("ss", -40, 3.0), ("ss", -40, 3.6), ("ff", 125, 3.0), ("ff", 125, 3.6)]
MUT_CORNERS = [("tt", 27, 3.3), ("ff", 125, 3.6)]
LIM = dict(g1=1e-3, track=0.02, ratio=0.03, boost=0.04, tt=0.03, ok_lo=0.1, ok_hi=0.9, i_open=20e-9, g4=1e-3,
           rail=0.05)
U = 1e-6
STEPS = [(0, 0.0), (20, 5.0), (60, 1.0), (90, 2.0), (120, 10.0), (150, 20.0), (180, 5.0), (240, 5.0), (270, 0.0)]  # us, uA
T_BOOST = (210, 240)
T_END = 300
WIN = 4.0                          # us averaging window at the end of each step


def tg(name, a, b, gn, gp):
    return [x(f"{name}n", a, gn, b, "vss", N5, 2.0, 0.5), x(f"{name}p", a, gp, b, "vdd", P5, 4.0, 0.5)]


def build_cz(mut="none"):
    """The c6_cz subckt text (c6_bias must be defined alongside); the ext diode node IS bias_ext."""
    k = K_EXT * (0.9 if mut == "kwrong" else 1.0)
    L = [f".subckt c6_cz {CPORTS}", f"* WO-108 BIAS_EXT wrapper; mut {mut}; K_ext {k:.4f} (bias_ext {I_NOM * 1e6:g} uA = C6 master)",
         f"Xcore vdd vss vdl boost trim0 trim1 trim2 c_ibtp c_ibn c_ibp c_ivbl0 c_ok c6_bias",
         f"Xsi0 bias_sel vss vss vdd vdd sel_b {INV}", f"Xsi1 sel_b vss vss vdd vdd sel_i {INV}"]
    # ---- port switches
    for p in PORTS_ALL:
        cn, cp = ("sel_i", "sel_b") if (mut == "swapsel" and p == "ibp") else ("sel_b", "sel_i")
        L += tg(f"tc_{p}", f"c_{p}", p, cn, cp)
        L += tg(f"te_{p}", f"e_{p}", p, "sel_i", "sel_b")
    # ---- ext replica (mirror side of C6, x K)
    L += [f"Xlsb boost vdl vss vss vdd vdd eboost_h {LS}", f"Xivb eboost_h vss vss vdd vdd eboost_b {INV}"]
    L += [x("emdc1", "bias_ext", "bias_ext", "vne", "vss", N5, F.NW * k, F.NCL), x("emdm1", "vne", "vne", "vss", "vss", N5, F.NW * k, F.NL),
          x("emsb", "bias_ext", "eboost_b", "vnse", "vss", N5, 2 * k, 0.5),
          x("emdc2", "vnse", "bias_ext", "vn2e", "vss", N5, F.NW * k, F.NCL), x("emdm2", "vn2e", "vne", "vss", "vss", N5, F.NW * k, F.NL)]
    for p in SINKS:
        ws = F.fingers(F.units(p), F.NW)
        if mut == "efinger" and p == "ibp":
            ws = ws[1:]
        for i, w in enumerate(ws):
            L += [x(f"emm{p}{i}", f"e{p}m", "vne", "vss", "vss", N5, w, F.NL),
                  x(f"emc{p}{i}", f"e_{p}", "bias_ext", f"e{p}m", "vss", N5, w, F.NCL)]
    L += [x("emfm", "vfme", "vne", "vss", "vss", N5, F.NW, F.NL), x("emfc", "vpe", "bias_ext", "vfme", "vss", N5, F.NW, F.NCL),
          x("emvp", "vpe", "vpe", "vdd", "vdd", P5, F.PW, F.PL, F.N_VP)]
    for i, w in enumerate(F.fingers(F.units("ibn"), F.PW)):
        L.append(x(f"emibn{i}", "e_ibn", "vpe", "vdd", "vdd", P5, w, F.PL))
    # ---- ext-present detect and ok mux
    L += [x("esm", "esd", "vne", "vss", "vss", N5, F.NW, F.NL, N_SENSE), x("esc", "esn", "bias_ext", "esd", "vss", N5, F.NW, F.NCL, N_SENSE),
          f"Xrup vdd esn vss {B.RX} l={R_UP_L:g}"]
    if mut == "nodetect":
        L.append("Rnd ok_e vdd 1m")
    else:
        L.append(f"Xdet esn vss vss vdd vdd ok_e {INV}")
    L.append(f"Xmx c_ok ok_e sel_i vss vss vdd vdd ok {MUX}")
    if mut == "leaky":
        L.append(f"Rleak ibtp vss {2.0 / (0.005 * PORT_I['ibtp']):.6g}")
    if mut == "overv":
        L += ["Vhi hi vss 5.2", "Rhi hi vne 1k"]
    return "\n".join(L + [".ends c6_cz"]) + "\n"


def netlist(mut="none"):
    return F.build("none") + build_cz(mut)


def load_lines(pre):
    """OTA1 bias diodes (c6_final.ota_diodes) with instance and node names prefixed."""
    ren = {"dtp", "dn", "dp", "dbl"}
    out = []
    for ln in F.ota_diodes():
        t = ln.split()
        t[0] = "X" + pre + t[0][1:]
        out.append(" ".join(pre + s if s in ren else s for s in t))
    return out


def fixed_lines(pre, vdd):
    out = []
    for p, node in (("ibtp", "dtp"), ("ibp", "dp"), ("ivbl0", "dbl")):
        out.append(f"V{pre}fx_{p} {pre}{node} 0 {vdd - 0.3:g}")
    out.append(f"V{pre}fx_ibn {pre}dn 0 0.3")
    return out


def stepwave(vals_us):
    """PWL (seconds, amps) with 1 ns edges from [(t_us, I_uA)]."""
    pts, cur = [(0, vals_us[0][1] * 1e-6)], vals_us[0][1] * 1e-6
    for t, v in vals_us[1:]:
        pts += [(t * U, cur), (t * U + 1e-9, v * 1e-6)]
        cur = v * 1e-6
    return F.pwl(pts)


def deck(kind, corner, temp, vdd, mut, csv):
    L = [f"* c6_cz {kind} {corner} {temp} {vdd} {mut}", f".lib {B.LIB} {corner}", f".include {HVL}", f".temp {temp}",
         f".option gmin={1e-11 if temp > 100 else 1e-15} reltol=1e-5 abstol=1e-14 method={F.METHOD}"]
    ramp = f"pwl(0 {B.VPRE} 10n {B.VPRE} 1.01u {vdd})"
    L += [f"Vdd vdd 0 {ramp}", f"Vdo vdo 0 {ramp}", "Vdl vdl 0 1.8"]
    if kind == "s1":
        bst = [(0, 0.0), (T_BOOST[0] * U, 1.8), (T_BOOST[1] * U, 0.0)]
        L.append(f"Vbst boost 0 PWL({F.pwl(F.steps(bst[1:], 0))})")
    else:
        L.append(f"Vbst boost 0 PWL({F.pwl(F.steps([(250 * U, 1.8)], 0))})")
    for b in range(3):
        L.append(f"Vt{b} trim{b} 0 {1.8 * ((4 >> b) & 1):g}")
    if kind == "s1":
        L.append(f"Vsel bias_sel 0 {ramp}")
        L.append(f"Iext 0 bias_ext PWL({stepwave(STEPS)})")
        L.append("Xz vdd 0 vdl boost trim0 trim1 trim2 zibtp zibn zibp zivbl0 zok bias_ext bias_sel c6_cz")
        L += ["Vzmtp zdtp zibtp 0", "Vzmp zdp zibp 0", "Vzmbl zdbl zivbl0 0", "Vzmn zibn zdn 0"] + load_lines("z")
        vecs = ("i(vzmtp) i(vzmp) i(vzmbl) i(vzmn) v(zok) v(bias_ext) v(zibtp) v(zibp) v(zivbl0) v(zibn) "
                "v(xz.vne) v(xz.vn2e) v(xz.vpe) v(xz.esn) v(xz.ok_e) v(xz.e_ibtp) v(xz.e_ibn) v(xz.c_ibn)")
        tend = T_END
    else:
        L += ["Vext bias_ext 0 0", "Vsel bias_sel 0 0"]
        L.append("Xb vdd 0 vdl boost trim0 trim1 trim2 bibtp bibn bibp bivbl0 bok c6_bias")
        L.append("Xz vdd 0 vdl boost trim0 trim1 trim2 zibtp zibn zibp zivbl0 zok bias_ext bias_sel c6_cz")
        for pre in ("b", "z"):
            L += ["V%smtp %sdtp %sibtp 0" % (pre, pre, pre), "V%smp %sdp %sibp 0" % (pre, pre, pre),
                  "V%smbl %sdbl %sivbl0 0" % (pre, pre, pre), "V%smn %sibn %sdn 0" % (pre, pre, pre)]
            L += load_lines(pre) if kind == "s0" else fixed_lines(pre, vdd)
        vecs = ("i(vbmtp) i(vbmp) i(vbmbl) i(vbmn) i(vzmtp) i(vzmp) i(vzmbl) i(vzmn) v(bok) v(zok) v(bibtp) v(zibtp) "
                "v(zibn) v(xz.vne) v(xz.esn) v(xz.e_ibn)")
        tend = 270
    L += [".control", "set wr_singlescale", "set wr_vecnames", f"tran 20n {tend}u 0 20n", f"wrdata {csv} {vecs}", ".endc"]
    return "\n".join(L) + "\n" + netlist(mut) + ".end\n"


def run(out, kind, corner, temp, vdd, mut="none"):
    import numpy as np
    temp, vdd = float(temp), float(vdd)
    tag = f"cz_{kind}_{corner}_{temp:g}_{vdd:g}_{mut}"
    base = os.path.join(out, tag)
    with open(base + ".cir", "w") as f:
        f.write(deck(kind, corner, temp, vdd, mut, base + ".txt"))
    p = subprocess.run(["ngspice", "-b", base + ".cir"], capture_output=True, text=True, timeout=5400)
    open(base + ".log", "w").write(p.stdout[-6000:] + p.stderr[-4000:])
    r = dict(tag=tag, kind=kind, corner=corner, temp=temp, vdd=vdd, mut=mut)
    try:
        d = np.loadtxt(base + ".txt", skiprows=1)
    except Exception as e:                     # noqa: BLE001
        r.update(verdict="REJECT", error=f"no data: {e}")
        json.dump(r, open(base + ".json", "w"), indent=1)
        return r
    t = d[:, 0]

    def win(y, a, b):
        m = (t >= a * U) & (t <= b * U)
        return float(y[m].mean())

    def mx(y, a, b):
        m = (t >= a * U) & (t <= b * U)
        return float(y[m].max()), float(y[m].min())
    g = {}
    if kind in ("s0", "lk"):
        names = ("ibtp", "ibp", "ivbl0", "ibn")
        bare = {n: d[:, 1 + i] for i, n in enumerate(names)}
        wrap = {n: d[:, 5 + i] for i, n in enumerate(names)}
        bok, zok = d[:, 9], d[:, 10]
        res = {}
        for lab, (a, b) in dict(base=(140, 150), boost=(256, 260)).items():
            for n in names:
                ib, iz = win(bare[n], a, b), win(wrap[n], a, b)
                res[f"{lab}_{n}"] = dict(bare=ib, wrap=iz, dev=(iz / ib - 1) if ib > 0 else 1.0, diff_nA=(iz - ib) * 1e9)
        alive = res["base_ibtp"]["bare"] > 0.3e-6
        okmin = float(min(bok[t >= 140 * U].min(), zok[t >= 140 * U].min()))
        lim = LIM["g1"] if kind == "s0" else LIM["g4"]
        worst = max(abs(v["dev"]) for v in res.values())
        gate = "G1" if kind == "s0" else "G4"
        g[gate] = dict(rows=res, worst=worst, ok_min=okmin, pass_=bool(alive and worst <= lim and okmin >= 0.9 * vdd))
        nodes = [d[:, 11 + i] for i in range(6)]
    else:
        names = ("ibtp", "ibp", "ivbl0", "ibn")
        col = {n: d[:, 1 + i] for i, n in enumerate(names)}
        ok = d[:, 5]
        steps = {5.0: 60, 1.0: 90, 2.0: 120, 10.0: 150, 20.0: 180}
        cur = {I: {n: win(col[n], e - WIN, e) for n in names} for I, e in steps.items()}
        cur["5b"] = {n: win(col[n], T_BOOST[0] - WIN, T_BOOST[0]) for n in names}      # 5 uA again, boost still off
        cur["bst"] = {n: win(col[n], T_BOOST[1] - WIN, T_BOOST[1]) for n in names}     # boost on 210..240 (5 uA)
        trk = {}
        for I in (1.0, 2.0, 10.0, 20.0, "5b"):
            Iv = 5.0 if I == "5b" else I
            for n in names:
                trk[f"{I}_{n}"] = (cur[I][n] / cur[5.0][n]) / (Iv / 5.0) - 1 if cur[5.0][n] > 0 else 1.0
        rel = {n: cur[5.0][n] / PORT_I[n] for n in names}
        rat = {n: (cur[5.0][n] / cur[5.0]["ibtp"]) / (PORT_I[n] / PORT_I["ibtp"]) - 1 for n in names if n != "ibtp"}
        br = {n: cur["bst"][n] / cur[5.0][n] if cur[5.0][n] > 0 else 0 for n in names}
        pp = (max(abs(v) for v in trk.values()) <= LIM["track"] and all(abs(v) <= LIM["ratio"] for v in rat.values())
              and all(abs(v / 2 - 1) <= LIM["boost"] / 2 for v in br.values()))
        if corner == "tt":
            pp = pp and all(abs(v - 1) <= LIM["tt"] for v in rel.values())
        g["G2"] = dict(I=cur, track=trk, worst_track=max(abs(v) for v in trk.values()), rel=rel, ratio_err=rat, boost_ratio=br,
                       pass_=bool(pp))
        ok_open = mx(ok, 10, 20)[0]
        i_open = max(abs(win(col[n], 10, 20)) for n in names)
        ok_hi = min(win(ok, 55, 60), win(ok, 85, 90), win(ok, T_BOOST[0] - WIN, T_BOOST[0]))
        g["G3"] = dict(ok_open_max=ok_open, i_open=i_open, ok_present_min=ok_hi,
                       info_reopen=dict(ok=win(ok, 296, 300), ibtp=win(col["ibtp"], 296, 300)),
                       pass_=bool(ok_open <= LIM["ok_lo"] * vdd and i_open <= LIM["i_open"] and ok_hi >= LIM["ok_hi"] * vdd))
        nodes = [d[:, 6 + i] for i in range(13)]
    hi = max(float(n.max()) for n in nodes)
    lo = min(float(n.min()) for n in nodes)
    g["stress"] = dict(v_max=hi, v_min=lo, pass_=bool(hi <= vdd + LIM["rail"] and lo >= -LIM["rail"]))
    r["gates"] = g
    r["verdict"] = "ACCEPT" if all(v["pass_"] for v in g.values()) else "REJECT"
    if mut in TARGET:
        r["target"] = TARGET[mut]
        r["target_rejects"] = (TARGET[mut] in g) and not g[TARGET[mut]]["pass_"]
    json.dump(r, open(base + ".json", "w"), indent=1)
    return r


def summary(out):
    rows = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out)) if f.startswith("cz_") and f.endswith(".json")]
    print("| run | gate | detail | verdict |")
    print("|---|---|---|---|")
    for r in rows:
        if "gates" not in r:
            print(f"| {r['tag']} | | {r.get('error')} | {r['verdict']} |")
            continue
        g = r["gates"]
        det = []
        for k in ("G1", "G4"):
            if k in g:
                det.append(f"{k} {'ok' if g[k]['pass_'] else 'FAIL'} worst {g[k]['worst']:.2e} okmin {g[k]['ok_min']:.2f}")
        if "G2" in g:
            det.append(f"G2 {'ok' if g['G2']['pass_'] else 'FAIL'} track {g['G2']['worst_track']:.3f}")
            det.append(f"G3 {'ok' if g['G3']['pass_'] else 'FAIL'} ok_open {g['G3']['ok_open_max']:.2f} "
                       f"i_open {g['G3']['i_open'] * 1e9:.1f}nA ok_on {g['G3']['ok_present_min']:.2f}")
        det.append(f"stress {'ok' if g['stress']['pass_'] else 'FAIL'} [{g['stress']['v_min']:.2f},{g['stress']['v_max']:.2f}]")
        v = r["verdict"] if r["mut"] not in TARGET else ("REJECTS target " + r["target"] if r["target_rejects"]
                                                      else "DOES NOT REJECT " + r["target"])
        print(f"| {r['tag']} | {r['kind']} | {'; '.join(det)} | {v} |")


def jobs(out, frozen, jobfile):
    env = (". /home/mempool/tt-sd/.venv-sbx/bin/activate; "
           f"export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A; cd {frozen}")
    cmd = f"{env}; nice python design/cz/c6_cz.py run {out}"
    L = [f"{cmd} {k} {c} {t} {v}" for c, t, v in CORNERS5 for k in ("s0", "lk", "s1")]
    L += [f"{cmd} {KIND_OF[m]} {c} {t} {v} {m}" for m in MUTS for c, t, v in MUT_CORNERS]
    open(jobfile, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "netlist":
        txt = netlist(a[2] if len(a) > 2 else "none")
        (open(a[1], "w").write(txt) if len(a) > 1 and a[1] != "-" else sys.stdout.write(txt))
    elif a[0] == "jobs":
        jobs(*a[1:4])
    elif a[0] == "run":
        print(json.dumps(run(*a[1:]).get("verdict")))
    elif a[0] == "summary":
        summary(a[1])
