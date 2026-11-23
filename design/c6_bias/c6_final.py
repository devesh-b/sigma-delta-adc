#!/usr/bin/env python3
"""C6 final subckt `c6_bias` and its bench (WO-99). Sandbox only (ngspice, sky130A via PDK_ROOT).

  python c6_final.py netlist [OUT.spice] [MUT]        # the subckt (default: stdout)
  python c6_final.py jobs OUT FROZEN JOBFILE           # lpool job list: 9 corners + broken copies
  python c6_final.py run OUT CORNER TEMP VDD [MUT]     # one transient bench -> OUT/<tag>.json
  python c6_final.py summary OUT                       # verdict table -> stdout

Subckt: .subckt c6_bias vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok
  vdd/vss VAPWR/VGND, vdl VDPWR (1.8 V, level-shifter low side); boost, trim[2:0] 1.8 V from C9 (static, latched at a
  pair boundary; reset boost 0, trim 100); ibtp/ibp/ivbl0 sinks and ibn source to the OTA bias diodes (OTA2 shares them,
  D91); ok = bias_ok (3.3 V; the top shifts it down with lsbufhv2lv_1).
Core = c6_spot.deck('tran') core and start-up at the WO-80/87 values (R1 144.8 um, R2/R1 2.45; c6_spot defaults now agree).
Changes against the spot deck (DESIGN.md 4-5):
  * master leg = G0 17 VG units + trim legs 1/2/4 units through PMOS switches (gate = NOT trim bit): code 100 = 21 units,
    the spot deck's fixed master (D73: I7/I0 = 24/17).
  * VN = cascoded NMOS diode in two halves (main W 2/L 4, cascode W 2/L 1 on VNC); half 2 is a cascoded copy behind an
    NMOS switch (gate NOT boost). boost = 1 opens it: the master current flows through half 1 only and every port doubles
    (D43b, one switched leg). Mk (core-off flag) W x2 so R_K stays 0.525 of the base diode.
  * sinks ibtp/ibp/ivbl0: cascoded NMOS mirrors (VN/VNC), unit fingers W 2 plus one trimmed-width finger.
  * ibn: VP = PMOS diode (2 x W 2/L 16) fed by a 1-unit cascoded NMOS sink (0.5 x master); ibn = PMOS mirror from VP
    (uncascoded, L 16: a stacked PMOS cascode would leave the VP feed below its own compliance at ss/-40/3.0).
  * boost / trim cross up through sky130_fd_sc_hvl__lsbuflv2hv_1 + inv_1 (static controls).
Bench timeline (us): ramp 0->VDD 1 us; [140,150] start-up check; [151,249] port probe sweep base; 250 boost on;
[260,360] sweep boost; 360 boost off; codes 0..7 base 25 us each from 370; 570 boost on, codes 0..7 boost to 770.
Port loads = the OTA1 bias diodes (Xmtr, Xmnr, Xmplr, Xmbl0) copied from design/xschem/sd_mod_top.spice.
Gates (WO-99 item 1): start (bias_ok high from 140 us, I settled 1 %), port (tt +-3 % of I_REF; port ratios +-3 % and
boost/base 2 +-4 % at every corner), compl (>= 0.2 V from the 1 % knee, base and boost), toggle (0.1 % within 4 us,
both directions), trim (monotonic, step <= 6 %, I7/I0 >= 1.38, best-code residual <= 3 %), own (<= 6 us excl. mirrors).
Broken copies (each must REJECT its gate): finger (ibtp one unit finger missing -> port), trim_open (LSB leg open ->
trim), slowvn (400 pF on VN -> toggle), hog (1.1 MOhm VDD-VSS -> own), stack3 (cascode bias one Vgs high -> compl),
nosu (start-up kick removed -> start).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "design", "c1_ota1"))
import c6_spot as B  # noqa: E402
import sizes_draft as S  # noqa: E402

R1, RATIO = 144.8, 2.45
I_TGT = B.I_TGT
PORT_I = dict(ibtp=S.I_REF["btp"], ibn=S.I_REF["bn"], ibp=S.I_REF["bp"], ivbl0=S.I_REF["vbl0"])
SINKS = ("ibtp", "ibp", "ivbl0")
NW, NL, NCL = 2.0, 4.0, 1.0      # NMOS mirror unit (main W/L, cascode L)
PW, PL = 2.0, 16.0               # PMOS VP / ibn unit
N_DIODE, N_FEED, N_VP = 2, 1.0, 2
# WO-104 item 1: ibn = uncascoded PMOS mirror, VSD(out) ~ 2 V vs VSG(VP diode) ~ 1.1 V -> CLM gain +0.3..+4.2 % over the
# 9 corners (WO-99: ibn/ibtp ratio error, fs/-40 +4.2 %, ss/-40 +3.4 %, tt +2.4 %, sf/125 +0.3 %). Centre it: ibn units x 0.978.
IBN_K = 0.978
# WO-104 item 2: trim legs re-sized by L (W is 0.42 minimum) to equal-ratio weights b0 0.937, b1 1.926, b2 3.957 units
# (s = 5.5 % per step, cover 1.40, code 100 unchanged). WO-99 effective weights at L 20: b0 1.03-1.07, b1 1.995, b2 3.96.
TRIM_L = {0: 22.5, 1: 20.7, 2: 20.0}
HVL = os.environ.get("PDK_ROOT", "/home/mempool/.ciel") + "/sky130A/libs.ref/sky130_fd_sc_hvl/spice/sky130_fd_sc_hvl.spice"
LS, INV = "sky130_fd_sc_hvl__lsbuflv2hv_1", "sky130_fd_sc_hvl__inv_1"
PORTS = "vdd vss vdl boost trim0 trim1 trim2 ibtp ibn ibp ivbl0 ok"
PROBES = " pr_ibtp pr_ibn pr_ibp pr_ivbl0"
MUTS = ("finger", "trim_open", "slowvn", "hog", "stack4", "nosu")
TARGET = dict(finger="port", trim_open="trim", slowvn="toggle", hog="own", stack4="compl", nosu="start")
CORNERS9 = [("tt", 27, 3.3)] + [(c, t, 3.6 if c == "ff" else 3.0) for c in ("ss", "ff", "sf", "fs") for t in (-40, 125)]
MUT_CORNERS = [("tt", 27, 3.3), ("ss", -40, 3.0)]
# v99 = WO-99 sizing (IBN_K 1, trim L 20) under the WO-104 bench: separates the bench fix from the two sizing changes.
LIM = dict(tt=0.03, ratio=0.03, boost=0.04, compl=0.2, toggle=1e-3, t_tog=4e-6, step=0.06, cover=1.38, resid=0.03,
           own=B.OWN_MAX, start=0.01)
U = 1e-6
# WO-104 item 4: trap integration left a non-decaying point-to-point ringing (1.48 / 2.28 uA alternating each 20 ns
# step, mean correct) on the port currents after every boost toggle -> the WO-99 toggle FAILs were bench artefacts.
# Gear-2 damps it. gmin 1e-11 at 125 C (WO-87 precedent): WO-99 ff/125 aborted, timestep too small at 4.1 us.
METHOD = os.environ.get("C6_METHOD", "gear")


def units(port, mut="none"):
    i = PORT_I[port]
    return N_DIODE * i / I_TGT if port in SINKS else (1.0 if mut == "v99" else IBN_K) * N_VP * i / (I_TGT * N_FEED / N_DIODE)


def fingers(n, w):
    k, f = int(n), n - int(n)
    ws = [w] * k
    if f * w >= 0.42:
        ws.append(round(f * w, 3))
    elif ws:
        ws[-1] = round(ws[-1] + f * w, 3)
    else:
        ws = [max(round(f * w, 3), 0.42)]
    return ws


def core_lines(mut):
    txt, _ = B.deck("tran", "tt", 27, 3.3, mut="nosu" if mut == "nosu" else "none", r1=R1, ratio=RATIO)
    ren = {"0": "vss", "lk0": "vdd"}
    out = []
    for ln in txt.splitlines():
        if not ln or ln[0] not in "XC":
            continue
        t = ln.split()
        if t[0] in ("Xmm", "Xmn"):          # fixed master leg and single diode: replaced below
            continue
        k = max(i for i, s in enumerate(t) if "=" not in s) if t[0][0] == "X" else 3
        t[1:k] = [ren.get(n, n) for n in t[1:k]]
        if t[0] == "Xmk":                   # diode is now 2 halves: keep R_K = 0.525 of the base diode
            t = [f"w={2 * B.MK_W:g}" if s.startswith("w=") else s for s in t]
        out.append(" ".join(t))
    return out


def build(mut="none", probe=False):
    x, P5, N5 = B.x, B.P5, B.N5
    L = [f".subckt c6_bias {PORTS}{PROBES if probe else ''}",
         f"* WO-99 C6 final (R1 {R1} um, R2/R1 {RATIO}); mut {mut}; port units "
         + " ".join(f"{p} {units(p, mut):.3f}" for p in PORT_I)]
    L += core_lines(mut)
    for s in ("boost", "trim0", "trim1", "trim2"):
        L += [f"Xls_{s} {s} vdl vss vss vdd vdd {s}_h {LS}", f"Xiv_{s} {s}_h vss vss vdd vdd {s}_b {INV}"]
    L.append(x("mm", "vnc", "vg", "vdd", "vdd", P5, B.UW, B.UL, B.G0))
    for bit, w in ((0, 1), (1, 2), (2, 4)):
        if mut == "trim_open" and bit == 0:
            continue
        L += [x(f"mt{bit}", f"ts{bit}", "vg", "vdd", "vdd", P5, B.UW, 20.0 if mut == "v99" else TRIM_L[bit], w),
              x(f"mw{bit}", "vnc", f"trim{bit}_b", f"ts{bit}", "vdd", P5, 1, 0.5)]
    if mut == "stack4":   # WO-104: two extra diodes (vnc two Vgs high); one (WO-99 stack3) left 0.615 V margin at tt
        L += [x("mdx", "vnc", "vnc", "vnx", "vss", N5, NW, NCL), x("mdy", "vnx", "vnx", "vny", "vss", N5, NW, NCL),
              x("mdc1", "vny", "vny", "vn", "vss", N5, NW, NCL)]
    else:
        L.append(x("mdc1", "vnc", "vnc", "vn", "vss", N5, NW, NCL))
    L += [x("mdm1", "vn", "vn", "vss", "vss", N5, NW, NL), x("msb", "vnc", "boost_b", "vns", "vss", N5, 2, 0.5),
          x("mdc2", "vns", "vnc", "vn2", "vss", N5, NW, NCL), x("mdm2", "vn2", "vn", "vss", "vss", N5, NW, NL)]
    copies = (("", ""), ("q", "pr_")) if probe else (("", ""),)
    for p in SINKS:
        ws = fingers(units(p, mut), NW)
        if mut == "finger" and p == "ibtp":
            ws = ws[1:]
        for tag, pre in copies:
            for i, w in enumerate(ws):
                L += [x(f"m{tag}{p}{i}", f"{tag}{p}m", "vn", "vss", "vss", N5, w, NL),
                      x(f"c{tag}{p}{i}", pre + p, "vnc", f"{tag}{p}m", "vss", N5, w, NCL)]
    L += [x("mfm", "vfm", "vn", "vss", "vss", N5, NW, NL), x("mfc", "vp", "vnc", "vfm", "vss", N5, NW, NCL),
          x("mvp", "vp", "vp", "vdd", "vdd", P5, PW, PL, N_VP)]
    for tag, pre in copies:
        for i, w in enumerate(fingers(units("ibn", mut), PW)):
            L.append(x(f"m{tag}ibn{i}", pre + "ibn", "vp", "vdd", "vdd", P5, w, PL))
    if mut == "slowvn":
        L.append("Cslow vn vss 400p")
    if mut == "hog":
        L.append("Rhog vdd vss 1.1e6")
    return "\n".join(L + [".ends c6_bias"]) + "\n"


def ota_diodes():
    """OTA1 bias diodes from the WO-94 top netlist (ports renamed to the bench load nodes)."""
    txt = open(os.path.join(ROOT, "design", "xschem", "sd_mod_top.spice")).read()
    body = re.search(r"^\.subckt ota1 .*?^\.ends", txt, re.S | re.M).group(0)
    lines = body.splitlines()
    out = []
    for nm, port, node in (("Xmtr", "ibtp", "dtp"), ("Xmnr", "ibn", "dn"), ("Xmplr", "ibp", "dp"), ("Xmbl0", "ivbl0", "dbl")):
        i = next(j for j, ln in enumerate(lines) if ln.split() and ln.split()[0] == nm)
        ln = lines[i]
        j = i + 1
        while j < len(lines) and lines[j].startswith("+"):
            ln += " " + lines[j][1:]
            j += 1
        t = ln.split()
        t[1:5] = [{port: node, "vdd": "vdo", "vss": "0"}.get(n, n) for n in t[1:5]]
        out.append(" ".join(t))
    return out


def pwl(pts):
    return " ".join(f"{t:.9g} {v:.6g}" for t, v in pts)


def steps(t_v, v0, edge=1e-9):
    pts, cur = [(0, v0)], v0
    for t, v in t_v:
        pts += [(t, cur), (t + edge, v)]
        cur = v
    return pts


def code_at():
    seq = [(370 * U + 25 * U * k, k) for k in range(8)] + [(570 * U + 25 * U * k, k) for k in range(8)]
    return seq


def deck(corner, temp, vdd, mut, csv):
    L = [f"* WO-99 c6_final bench {corner} {temp} {vdd} {mut}", f".lib {B.LIB} {corner}", f".include {HVL}",
         f".temp {temp}", f".option gmin={1e-11 if temp > 100 else 1e-15} reltol=1e-5 abstol=1e-14 method={METHOD}"]
    ramp = f"pwl(0 {B.VPRE} 10n {B.VPRE} 1.01u {vdd})"
    L += [f"Vdd vdd 0 {ramp}", f"Vdo vdo 0 {ramp}", "Vdl vdl 0 1.8"]
    L.append(f"Vbst boost 0 PWL({pwl(steps([(250 * U, 1.8), (360 * U, 0), (570 * U, 1.8)], 0))})")
    for b in range(3):
        L.append(f"Vt{b} trim{b} 0 PWL({pwl(steps([(t, 1.8 * ((k >> b) & 1)) for t, k in code_at()], 1.8 * ((4 >> b) & 1)))})")
    L.append("Xc6 vdd 0 vdl boost trim0 trim1 trim2 pibtp pibn pibp pivbl0 ok pr_ibtp pr_ibn pr_ibp pr_ivbl0 c6_bias")
    L += ["Vmtp dtp pibtp 0", "Vmp dp pibp 0", "Vmbl dbl pivbl0 0", "Vmn pibn dn 0"] + ota_diodes()
    for p, hold in (("ibtp", 2.0), ("ibp", 2.0), ("ivbl0", 2.0), ("ibn", 1.0)):
        pts = [(0, hold), (150 * U, hold), (151 * U, 0), (249 * U, vdd), (249.5 * U, hold), (260 * U, hold),
               (261 * U, 0), (359 * U, vdd), (359.5 * U, hold)]
        L.append(f"Vpr_{p} pr_{p} 0 PWL({pwl(pts)})")
    vecs = ("i(vmtp) i(vmp) i(vmbl) i(vmn) i(vdd) v(pibtp) v(pibp) v(pivbl0) v(pibn) v(ok) "
            "i(vpr_ibtp) i(vpr_ibp) i(vpr_ivbl0) i(vpr_ibn)")
    L += [".control", "set wr_singlescale", "set wr_vecnames", "tran 20n 770u 0 20n", f"wrdata {csv} {vecs}", ".endc"]
    return "\n".join(L) + "\n" + build(mut, probe=True) + ".end\n"


def run(out, corner, temp, vdd, mut="none"):
    import numpy as np
    temp, vdd = float(temp), float(vdd)
    tag = f"c6f_{corner}_{temp:g}_{vdd:g}_{mut}"
    base = os.path.join(out, tag)
    with open(base + ".cir", "w") as f:
        f.write(deck(corner, temp, vdd, mut, base + ".txt"))
    p = subprocess.run(["ngspice", "-b", base + ".cir"], capture_output=True, text=True, timeout=5400)
    open(base + ".log", "w").write(p.stdout[-6000:] + p.stderr[-4000:])
    r = dict(tag=tag, corner=corner, temp=temp, vdd=vdd, mut=mut)
    try:
        d = np.loadtxt(base + ".txt", skiprows=1)
    except Exception as e:                     # noqa: BLE001
        r.update(verdict="REJECT", error=f"no data: {e}")
        json.dump(r, open(base + ".json", "w"), indent=1)
        return r
    t = d[:, 0]
    col = dict(ibtp=d[:, 1], ibp=d[:, 2], ivbl0=d[:, 3], ibn=d[:, 4])
    vport = dict(ibtp=d[:, 6], ibp=d[:, 7], ivbl0=d[:, 8], ibn=d[:, 9])
    ok, ivdd = d[:, 10], -d[:, 5]
    prb = dict(ibtp=-d[:, 11], ibp=-d[:, 12], ivbl0=-d[:, 13], ibn=d[:, 14])

    def win(y, a, b):
        m = (t >= a) & (t <= b)
        return float(y[m].mean())
    g = {}
    # start
    st = {p: win(col[p], 140 * U, 150 * U) for p in PORT_I}
    ref = {p: win(col[p], 366 * U, 370 * U) for p in PORT_I}
    okmin = float(ok[t >= 140 * U].min())
    dst = max(abs(st[p] / ref[p] - 1) if ref[p] > 0 else 1.0 for p in PORT_I)
    g["start"] = dict(ok_min=okmin, dev=dst, pass_=bool(okmin >= 0.9 * vdd and dst <= LIM["start"] and ref["ibtp"] > 0.3e-6))
    # port
    bst = {p: win(col[p], 256 * U, 260 * U) for p in PORT_I}
    rel = {p: st[p] / PORT_I[p] for p in PORT_I}
    rat = {p: (st[p] / st["ibtp"]) / (PORT_I[p] / PORT_I["ibtp"]) - 1 for p in PORT_I if p != "ibtp"}
    br = {p: bst[p] / st[p] if st[p] > 0 else 0 for p in PORT_I}
    pp = all(abs(v) <= LIM["ratio"] for v in rat.values()) and all(abs(v / 2 - 1) <= LIM["boost"] / 2 for v in br.values())
    if corner == "tt":
        pp = pp and all(abs(v - 1) <= LIM["tt"] for v in rel.values())
    g["port"] = dict(I=st, I_boost=bst, rel=rel, ratio_err=rat, boost_ratio=br, pass_=bool(pp))
    # compliance
    cm = {}
    for mode, (a, b, va, vb) in dict(base=(151 * U, 249 * U, 140 * U, 150 * U), boost=(261 * U, 359 * U, 256 * U, 260 * U)).items():
        m = (t >= a + 0.5 * U) & (t <= b - 0.5 * U)
        vs = vdd * (t[m] - a) / (b - a)
        for p in PORT_I:
            va_ = win(vport[p], va, vb)
            ip = prb[p][m]
            iref = float(np.interp(va_, vs, ip))
            if p in SINKS:
                bad = vs[(vs < va_) & (ip < 0.99 * iref)]
                vk = float(bad.max()) if bad.size else 0.0
                mg = va_ - vk
            else:
                bad = vs[(vs > va_) & (ip < 0.99 * iref)]
                vk = float(bad.min()) if bad.size else vdd
                mg = vk - va_
            cm[f"{mode}_{p}"] = dict(v_port=va_, v_knee=vk, margin=mg)
    g["compl"] = dict(rows=cm, min_margin=min(v["margin"] for v in cm.values()),
                      pass_=bool(all(v["margin"] >= LIM["compl"] for v in cm.values())))
    # toggle
    tg = {}
    for t0, nm in ((250 * U, "up"), (360 * U, "down")):
        for p in PORT_I:
            fin = win(col[p], t0 + 8 * U, t0 + 10 * U)
            m = (t >= t0 + LIM["t_tog"]) & (t <= t0 + 10 * U)
            tg[f"{nm}_{p}"] = float(np.max(np.abs(col[p][m] / fin - 1))) if fin > 0 else 1.0
    g["toggle"] = dict(dev=tg, worst=max(tg.values()), pass_=bool(max(tg.values()) <= LIM["toggle"]))
    # trim
    cb = [win(col["ibtp"], 370 * U + 25 * U * k + 22 * U, 370 * U + 25 * U * (k + 1)) for k in range(8)]
    cbo = [win(col["ibtp"], 570 * U + 25 * U * k + 22 * U, 570 * U + 25 * U * (k + 1)) for k in range(8)]
    stp = [cb[k + 1] / cb[k] - 1 if cb[k] > 0 else 0 for k in range(7)]
    stpo = [cbo[k + 1] / cbo[k] - 1 if cbo[k] > 0 else 0 for k in range(7)]
    cov = cb[7] / cb[0] if cb[0] > 0 else 0
    res = min(abs(v / PORT_I["ibtp"] - 1) for v in cb)
    g["trim"] = dict(I_codes=cb, I_codes_boost=cbo, steps=stp, steps_boost=stpo, cover=cov, best_resid=res,
                     pass_=bool(min(stp) > 0 and max(stp) <= LIM["step"] and min(stpo) > 0 and cov >= LIM["cover"]
                                and res <= LIM["resid"]))
    # own current
    own_t = win(ivdd - col["ibn"] - prb["ibn"], 140 * U, 150 * U)
    feed = (st["ibn"] + win(prb["ibn"], 140 * U, 150 * U)) / (2 * units("ibn", mut) / N_VP)
    own_b = win(ivdd - col["ibn"] - prb["ibn"], 256 * U, 260 * U)
    g["own"] = dict(own_total=own_t, vp_feed=feed, own_core=own_t - feed, own_total_boost=own_b,
                    pass_=bool(own_t - feed <= LIM["own"]))
    r["gates"] = g
    r["verdict"] = "ACCEPT" if all(v["pass_"] for v in g.values()) else "REJECT"
    if mut in TARGET:
        r["target"] = TARGET[mut]
        r["target_rejects"] = not g[TARGET[mut]]["pass_"]
    json.dump(r, open(base + ".json", "w"), indent=1)
    return r


DIAG_NODES = "vn vnc vns vn2 vp vg tsu q ok ibtpm boost_b boost_h".split()


def diag(out, corner, temp, vdd, mut="none"):
    """WO-104 toggle diagnosis: boost on at 30 us, off at 60 us, probes held, code 100; internal nodes saved."""
    temp, vdd = float(temp), float(vdd)
    tag = f"c6d_{corner}_{temp:g}_{vdd:g}_{mut}"
    base = os.path.join(out, tag)
    txt = deck(corner, temp, vdd, mut, base + ".txt")
    txt = re.sub(r"^Vbst .*$", f"Vbst boost 0 PWL({pwl(steps([(30 * U, 1.8), (60 * U, 0)], 0))})", txt, flags=re.M)
    txt = re.sub(r"^Vt(\d) (trim\d) 0 PWL.*$", lambda m: f"Vt{m[1]} {m[2]} 0 {1.8 * ((4 >> int(m[1])) & 1):g}", txt, flags=re.M)
    txt = re.sub(r"^Vpr_(\w+) (pr_\w+) 0 PWL.*$", lambda m: f"Vpr_{m[1]} {m[2]} 0 {1.0 if m[1] == 'ibn' else 2.0}", txt,
                 flags=re.M)
    vecs = "i(vmtp) i(vmn) i(vdd) i(vpr_ibtp) i(vpr_ibn) " + " ".join(f"v({n})" if n in PORTS.split() else f"v(xc6.{n})" for n in DIAG_NODES)  # ports (ok) are top-level nodes
    txt = re.sub(r"^tran .*$", "tran 20n 90u 0 20n", txt, flags=re.M)
    txt = re.sub(r"^wrdata .*$", f"wrdata {base}.txt {vecs}", txt, flags=re.M)
    open(base + ".cir", "w").write(txt)
    p = subprocess.run(["ngspice", "-b", base + ".cir"], capture_output=True, text=True, timeout=5400)
    open(base + ".log", "w").write(p.stdout[-6000:] + p.stderr[-4000:])
    import numpy as np
    d = np.loadtxt(base + ".txt", skiprows=1)
    t = d[:, 0]
    names = ["ibtp", "ibn", "ivdd", "pr_ibtp", "pr_ibn"] + DIAG_NODES
    sign = [1, 1, -1, -1, 1] + [1] * len(DIAG_NODES)
    lines = []
    for x in (25, 29.9, 30.2, 30.5, 31, 32, 34, 38, 45, 55, 59.9, 60.2, 60.5, 61, 62, 64, 68, 75, 89):
        i = int(np.argmin(abs(t - x * U)))
        lines.append(f"{x:5g} " + " ".join(f"{n}={sign[k] * d[i, 1 + k]:.5g}"
                                            for k, n in enumerate(names)))
    for t0 in (30 * U, 60 * U):
        m = (t >= t0 + 4 * U) & (t <= t0 + 10 * U)
        fin = d[(t >= t0 + 8 * U) & (t <= t0 + 10 * U), 1].mean()
        lines.append(f"toggle t0={t0 / U:g}us ibtp dev={np.max(np.abs(d[m, 1] / fin - 1)):.3e} "
                     f"step-to-step max={np.max(np.abs(np.diff(d[m, 1]))) / fin:.3e}")
    open(base + ".sum", "w").write("\n".join(lines) + "\n")


def summary(out):
    rows = [json.load(open(os.path.join(out, f))) for f in sorted(os.listdir(out)) if f.startswith("c6f_") and f.endswith(".json")]
    print("| run | start | port | compl (min margin V) | toggle (worst) | trim (cover, max step) | own core / total uA | verdict |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        if "gates" not in r:
            print(f"| {r['tag']} | {r.get('error')} | | | | | | {r['verdict']} |")
            continue
        g = r["gates"]
        f = lambda k: "ok" if g[k]["pass_"] else "FAIL"  # noqa: E731
        v = r["verdict"] if r["mut"] not in TARGET else ("REJECTS target " + r["target"] if r["target_rejects"]
                                                      else "DOES NOT REJECT " + r["target"])
        print(f"| {r['tag']} | {f('start')} | {f('port')} | {f('compl')} {g['compl']['min_margin']:.3f} | "
              f"{f('toggle')} {g['toggle']['worst']:.2e} | {f('trim')} {g['trim']['cover']:.3f}, "
              f"{max(g['trim']['steps']):.3f} | {f('own')} {g['own']['own_core'] * 1e6:.2f} / "
              f"{g['own']['own_total'] * 1e6:.2f} | {v} |")


def jobs(out, frozen, jobfile):
    env = (f". {frozen}/../../../tt-sd/.venv-sbx/bin/activate 2>/dev/null || . /home/mempool/tt-sd/.venv-sbx/bin/activate; "
           f"export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A; cd {frozen}")
    L = [f"{env}; C6_METHOD=trap nice python design/c6_bias/c6_final.py diag {out} tt 27 3.3 trap",
         f"{env}; nice python design/c6_bias/c6_final.py diag {out} tt 27 3.3"]
    L += [f"{env}; nice python design/c6_bias/c6_final.py run {out} {c} {t} {v}" for c, t, v in CORNERS9]
    L += [f"{env}; nice python design/c6_bias/c6_final.py run {out} {c} {t} {v} {m}" for m in MUTS for c, t, v in MUT_CORNERS]
    L += [f"{env}; nice python design/c6_bias/c6_final.py run {out} {c} {t} {v} v99" for c, t, v in
          (("tt", 27, 3.3), ("ss", -40, 3.0), ("fs", -40, 3.0))]
    open(jobfile, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "netlist":
        txt = build(a[2] if len(a) > 2 else "none")
        (open(a[1], "w").write(txt) if len(a) > 1 else sys.stdout.write(txt))
    elif a[0] == "jobs":
        jobs(*a[1:4])
    elif a[0] == "run":
        print(json.dumps(run(*a[1:]).get("verdict")))
    elif a[0] == "diag":
        diag(*a[1:])
    elif a[0] == "summary":
        summary(a[1])
