#!/usr/bin/env python3
"""WO-94/WO-102 reference netlists, taken from the Python generators (the source of truth). Sandbox only.

    python3 refnets.py OUTDIR

Writes OUTDIR/<cell>.spice for ota1, ota2, c3_comp, c4_gen, c6_bias, c5c7_ref, the MIM cells and sd_mod_top (top + all blocks).
No sizes live here except the MIM unit (W = L = MIM_UNIT um) and the unit counts, which follow SPEC 3.4
(Cs 0.5 pF = 2 units, Cint1 4 pF = 16, Cint2 1 pF = 4, Ck2 0.25 pF = 1).

WO-102: c6_bias = design/c6_bias/c6_final.py `netlist` (subckt with boost/trim ports), c5c7_ref = design/c5c7_ref/c5c7_ref.py
`netlist`, ota2 = design/c2_ota2/ota2.spice (D91 sizes, generated file), SW['sr2'] comes from c4_sw/netlist.py.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.normpath(os.path.join(HERE, "..", ".."))       # design/
sys.path.insert(0, os.path.join(D, "c4_sw"))
import netlist as N  # noqa: E402  (c4_sw/netlist.py: switch sizes SW, PORTS, PH)

MIM_UNIT = 11.0            # um; ~0.25 pF at ~2 fF/um2 + perimeter (to be confirmed by sim, WO-95/96)
MIM = dict(mim_cs=2, mim_cint1=16, mim_cint2=4, mim_ck2=1)


def run(py, *args):
    return subprocess.run([sys.executable, py, *args], check=True, capture_output=True, text=True).stdout


def ota2():
    """D91 OTA2 from the generated file design/c2_ota2/ota2.spice (no PENDING flag any more).
    The file carries 0 V wire sources (Vwi1/Vwi2 inp-gp/inn-gm, Vwf1/Vwf2 fa-xa/fb-xb) that the schematic does not
    draw; they are merged here (second node renamed to the first, source dropped), the same as the C6 ammeters."""
    ren, keep = {}, []
    for ln in open(os.path.join(D, "c2_ota2", "ota2.spice")).read().splitlines():
        t = ln.split()
        if t and t[0].startswith("Vw"):
            assert t[3] == "0", ln
            ren[t[2]] = t[1]
        else:
            keep.append(ln)
    out = []
    for ln in keep:
        t = ln.split()
        if t and t[0][0] in "XC" and not ln.startswith("*"):
            k = max(i for i, z in enumerate(t) if "=" not in z) if t[0][0] == "X" else 3
            t[1:k] = [ren.get(n, n) for n in t[1:k]]
            ln = " ".join(t)
        out.append(ln)
    return "\n".join(out) + "\n"


def mim(name, n):
    return (f".subckt {name} top bot\nXc top bot sky130_fd_pr__cap_mim_m3_1 W={MIM_UNIT:g} L={MIM_UNIT:g} "
            f"MF={n} m={n}\n.ends {name}\n")


TOP_PORTS = "ua0 ua1 ua2 ua3 VAPWR VDPWR VGND fs y swap short chop rst_analog order boost trim0 trim1 trim2 comp_out bias_ok"
BULK = {"0": "VGND", "vdd": "VAPWR"}


def sw(name, a, b, ph, key):
    out = []
    for ln in N.switch(name, a, b, ph + "_t", ph + "_c", key=key):
        t = ln.split()
        t[4] = BULK.get(t[4], t[4])
        out.append(" ".join(t))
    return out


def top():
    L = [f".subckt sd_mod_top {TOP_PORTS}"]
    vin = dict(p="ua0", n="ua1")
    for s, o in (("p", "n"), ("n", "p")):
        hi, lo = ("dh", "dl") if s == "p" else ("dl", "dh")       # 1-bit DAC: side p to VREF+ on y, side n on not y
        khi, klo = ("kl", "kh") if s == "p" else ("kh", "kl")     # WO-99 item 2: Cint crossed, so Ck2 polarity is opposite to stage 1
        L += sw(f"sin{s}", vin[s], f"b1{s}", "pas", "sin")      # 1  merged input / sys-swap / short
        L += sw(f"ssw{s}", vin[o], f"b1{s}", "swp", "sin")
        L += sw(f"ssh{s}", "vscm", f"b1{s}", "sho", "sin")   # WO-99 item 1: short CM = vscm (VREF/2)
        L += sw(f"sdh{s}", "ua2", f"b1{s}", hi, "sdh")          # 2  DAC
        L += sw(f"sdl{s}", "ua3", f"b1{s}", lo, "sdl")
        L.append(f"Xcs1{s} tp1{s} b1{s} mim_cs")                # Cs1 0.5 pF, bottom plate on the driven side
        L += sw(f"sg1{s}", f"tp1{s}", f"vg1{s}", "ie", "sg")    # 4  vg connect
        L.append(f"Xci1{s} vg1{s} x1{o} mim_cint1")             # Cint1 4 pF, vg1p -> x1n, vg1n -> x1p
        L += sw(f"s2in{s}", f"x1{s}", f"b2{s}", "sl", "s2in")   # 6  Cs2 sample
        L.append(f"Xcs2{s} tp2{s} b2{s} mim_cs")                # Cs2 0.5 pF
        L += sw(f"sg2{s}", f"tp2{s}", f"vg2{s}", "ie", "sg")    # 9  vg2 connect
        L += sw(f"skh{s}", "ua2", f"bk{s}", khi, "skh")         # 10 Ck2 DAC
        L += sw(f"skl{s}", "ua3", f"bk{s}", klo, "skl")
        L.append(f"Xck2{s} vg2{s} bk{s} mim_ck2")               # Ck2 0.25 pF on the OTA2 node
        L.append(f"Xci2{s} vg2{s} x2{o} mim_cint2")             # Cint2 1 pF
    L += sw("stp1", "tp1p", "tp1n", "se", "stp")                # 3  D12 top-plate short
    L += sw("s2cm", "b2p", "b2n", "il", "s2cm")                 # 7  Cs2 plate short (CL-2)
    L += sw("stp2", "tp2p", "tp2n", "se", "stp")                # 8
    L += sw("sk0", "bkp", "bkn", "k0", "sk0")                   # 11 Ck2 rest short
    L += sw("sr2", "x2p", "x2n", "r2", "sr2")                   # 12 Cint2 reset: x2p <-> x2n short (WO-99 item 3)
    cm = "vicm vocm"
    ctl = "chp chn chlp chln isl il_t il_c sl_t sl_c rstb"     # CMFB ph1 = il (integrate), ph2 = sl (hold)
    b = " ".join(f"o1_{p}" for p in ("ibtp", "ibn", "ibp", "ivbnc", "ivbpc", "ivbl0"))   # D91: OTA2 shares OTA1 bias
    for i in (1, 2):                                            # own CMFB inside each cell
        c = ctl.replace(" isl ", " r2_t ") if i == 2 else ctl   # OTA2 isl driven by r2_t (rstb stays C4's)
        L.append(f"Xota{i} VAPWR VGND vg{i}p vg{i}n x{i}p x{i}n {cm} {b} {c} ota{i}")
    L.append("Xcmp x2p x2n phc comp_out qb VDPWR VGND c3_comp")
    L.append("Xdec comp_out qb VGND VGND VDPWR VDPWR dec sky130_fd_sc_hd__nand2_1")   # dec = NAND(q, qb), 1.8 V
    ph = " ".join(f"{x}_t {x}_c" for x in N.PH)
    L.append(f"Xgen VAPWR VDPWR VGND fs y swap short chop rst_analog order dec {ph} "
             "isl rstb chp chn chlp chln phc pwrok fsh c4_gen")
    L.append("Xbias VAPWR VGND VDPWR boost trim0 trim1 trim2 o1_ibtp o1_ibn o1_ibp o1_ivbl0 ok c6_bias")
    L.append("Xref ua2 VGND vocm vicm vscm c5c7_ref")
    L.append("Xlsok ok VDPWR VGND VGND VAPWR VAPWR bias_ok sky130_fd_sc_hvl__lsbufhv2lv_1")   # bias_ok to 1.8 V
    return "\n".join(L + [".ends sd_mod_top"]) + "\n"


def main(out):
    os.makedirs(out, exist_ok=True)
    cells = {"ota1": run(os.path.join(D, "c1_ota1", "netlist.py")),
             "ota2": ota2(),
             "c3_comp": run(os.path.join(D, "c3_comp", "netlist.py")),
             "c4_gen": run(os.path.join(D, "c4_sw", "netlist.py")),
             "c6_bias": run(os.path.join(D, "c6_bias", "c6_final.py"), "netlist"),
             "c5c7_ref": run(os.path.join(D, "c5c7_ref", "c5c7_ref.py"), "netlist")}
    cells.update({k: mim(k, n) for k, n in MIM.items()})
    for k, v in cells.items():
        open(os.path.join(out, k + ".spice"), "w").write(v)
    open(os.path.join(out, "sd_mod_top.spice"), "w").write(top() + "".join(cells.values()))


if __name__ == "__main__":
    main(sys.argv[1])
