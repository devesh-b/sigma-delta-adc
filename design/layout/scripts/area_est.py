#!/usr/bin/env python3
"""Pre-layout area estimate per analog block from the block netlist generators (WO-96 item 1).
Run on the sandbox (IIC container) from the frozen tree root:  python3 design/layout/scripts/area_est.py
Footprint per MOS finger group: (W/nf + 2*ext_w) x (nf*(L+0.45) + 0.6) um, ext_w 0.6 (LV) / 1.0 (HV incl. guard share).
Block estimate = footprint x K (K 2.0 low / 3.0 high: routing, guard rings, dummies, matching); hvl std cells at LEF size x 1.3.
MIM caps at 2.0 fF/um2 + 0.19 fF/um perimeter for 0.25 pF units, pitch overhead x 1.5. Estimates only (no layout)."""
import os, re, subprocess, sys
ROOT = os.getcwd()
PDK = os.environ.get("PDK_ROOT", "/foss/pdks-tt") + "/sky130A"
LEF = PDK + "/libs.ref/sky130_fd_sc_hvl/lef/sky130_fd_sc_hvl.lef"

def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120).stdout

def num(v):
    v = v.lower().rstrip("u")
    m = re.match(r"^([-+0-9.e]+)([fpnum]?)$", v)
    if not m: return None
    x = float(m.group(1)); s = m.group(2)
    x *= {"": 1, "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}[s]
    return x

def hvl_sizes():
    d, cur = {}, None
    for ln in open(LEF):
        m = re.match(r"\s*MACRO (\S+)", ln)
        if m: cur = m.group(1)
        m = re.match(r"\s*SIZE ([0-9.]+) BY ([0-9.]+)", ln)
        if m and cur: d[cur] = float(m.group(1)) * float(m.group(2))
    return d

def parse(txt, hv):
    mos = foot = cells = 0.0; ncells = {}; caps = []
    for ln in txt.splitlines():
        t = ln.split()
        if not t: continue
        if t[0][0] in "Xx":
            kv = dict(x.split("=", 1) for x in t if "=" in x)
            model = next((x for x in t[1:] if not "=" in x and ("sky130" in x)), "")
            if "sky130_fd_sc_hvl" in model:
                ncells[model] = ncells.get(model, 0) + 1; continue
            if "w" in kv and "l" in kv and ("fet" in model):
                w, l = num(kv["w"]), num(kv["l"])
                if w is None or l is None: continue
                if w < 1e-3: w *= 1e6; l *= 1e6
                nf = int(float(kv.get("nf", 1))); m = float(kv.get("m", 1))
                ext = 1.0 if "g5v0" in model else 0.6
                foot += m * (w / nf + 2 * ext) * (nf * (l + 0.45) + 0.6); mos += m * w * l
            elif "cap_mim" in model:
                caps.append(ln)
        elif t[0][0] in "Cc" and len(t) >= 4:
            c = num(t[3]) if num(t[3]) is not None else None
            if c: caps.append(c)
    return mos, foot, ncells, caps

blocks = {
    "C1 OTA1": (["python3", "netlist.py", "/tmp/c1.sp"], "design/c1_ota1", "/tmp/c1.sp"),
    "C3 comparator": (["python3", "netlist.py"], "design/c3_comp", None),
    "C4 phase gen + switches + LS": (["python3", "netlist.py", "/tmp/c4.sp"], "design/c4_sw", "/tmp/c4.sp"),
}
hs = hvl_sizes()
print(f"{'block':32s} {'MOS WL um2':>10s} {'foot um2':>9s} {'hvl um2':>8s} {'caps':>5s} {'Ctot pF':>8s} {'est lo':>7s} {'est hi':>7s}")
for k, (cmd, cwd, f) in blocks.items():
    out = run(cmd, os.path.join(ROOT, cwd))
    txt = open(f).read() if f and os.path.exists(f) else out
    if not txt.strip(): print(k, "NO NETLIST"); continue
    mos, foot, nc, caps = parse(txt, True)
    hvl = sum(hs.get(c, 0) * n for c, n in nc.items()) * 1.3
    cnum = [c for c in caps if isinstance(c, float)]
    ct = sum(cnum) * 1e12
    print(f"{k:32s} {mos:10.0f} {foot:9.0f} {hvl:8.0f} {len(caps):5d} {ct:8.3f} {2*foot+hvl:7.0f} {3*foot+hvl:7.0f}")
    if nc: print("   hvl cells:", ", ".join(f"{c.replace('sky130_fd_sc_hvl__','')} x{n}" for c, n in sorted(nc.items())))
    if cnum: print("   caps (pF):", " ".join(f"{c*1e12:.3g}" for c in cnum))
# MIM core array: per side Cs1 0.5, Cint1 4, Cs2 0.5, Cint2 1, Ck2 0.25 pF -> x2 diff
u = 0.25; s = (-0.76 + (0.76**2 + 8 * u * 1e3) ** 0.5) / 4
n = int(round(2 * (0.5 + 4 + 0.5 + 1 + 0.25) / u))
print(f"MIM core: unit {u} pF = {s:.2f} um square; {n} units; drawn {n*s*s:.0f} um2; at pitch {s+2.5:.1f} um: {n*(s+2.5)**2:.0f} um2")
