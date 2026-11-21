#!/usr/bin/env python3
"""WO-94: emit xschem .sch + .sym from a reference SPICE file (refnets.py output). Sandbox only (IIC-OSIC-TOOLS).

    python3 sch_gen.py REF.spice OUTDIR [--break INST:ATTR=VAL]

Every .subckt in REF becomes OUTDIR/<cell>.sch and OUTDIR/<cell>.sym. Devices use the sky130A PDK symbols
(sky130_fd_pr/*.sym: MOS, res_xhigh_po_*, pnp_05v5, cap_mim_m3_1) and devices/res.sym, capa.sym for ideal R / C;
sky130_fd_sc_* standard cells get a primitive symbol OUTDIR/cells/<cell>.sym (pins from the PDK spice library).
Each device pin gets a short wire and a lab_pin with its net name; ports are iopin. Placement is a plain grid
(readable, not pretty): connectivity is by net label only. Sizes are copied verbatim from REF.
--break changes one attribute of one instance (broken copy for the LVS check).
"""
import os
import re
import sys

PDK = os.path.join(os.environ.get("PDK_ROOT", "/foss/pdks"), os.environ.get("PDK", "sky130A"))
XS = PDK + "/libs.tech/xschem"
DEV = "/foss/tools/xschem/share/xschem/xschem_library/devices"
LIBS = [PDK + "/libs.ref/sky130_fd_sc_hvl/spice/sky130_fd_sc_hvl.spice",
        PDK + "/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"]
HDR = "v {xschem version=3.4.5 file_version=1.2}\nG {}\n"


def sym_pins(path):
    pins = {}
    for ln in open(path):
        m = re.match(r"B 5 (\S+) (\S+) (\S+) (\S+) \{.*?name=(\S+?)[ }]", ln)
        if m:
            x1, y1, x2, y2 = map(float, m.groups()[:4])
            pins[m.group(5)] = ((x1 + x2) / 2, (y1 + y2) / 2)
    return pins


def lib_ports():
    p = {}
    for f in LIBS:
        for ln in open(f):
            if ln.lower().startswith(".subckt"):
                t = ln.split()
                p[t[1]] = t[2:]
    return p


def parse(path):
    cells, cur = {}, None
    for ln in open(path):
        t = ln.split()
        if not t or t[0].startswith("*"):
            continue
        if t[0].lower() == ".subckt":
            cur = t[1]
            cells[cur] = dict(ports=t[2:], el=[])
        elif t[0].lower() == ".ends":
            cur = None
        elif cur and t[0][0] in "XxRrCc":
            cells[cur]["el"].append(t)
    return cells


def gen_sym(path, name, ports, primitive=False):
    """Box symbol: first half of the ports on the left, rest on the right, 20 grid. Pin order = SPICE order."""
    nl = (len(ports) + 1) // 2
    h = 20 * max(nl, len(ports) - nl) + 20
    pins, body = {}, []
    for i, p in enumerate(ports):
        x, y = (-80, 20 * i + 20) if i < nl else (80, 20 * (i - nl) + 20)
        pins[p] = (x, y)
        body.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={p} dir=inout}}")
        body.append(f"L 4 {x} {y} {x + (20 if x < 0 else -20)} {y} {{}}")
        body.append(f"T {{{p}}} {x + (25 if x < 0 else -25)} {y - 6} 0 {0 if x < 0 else 1} 0.2 0.2 {{}}")
    if primitive:
        k = ("type=primitive\nformat=\"@name " + " ".join(f"@@{p}" for p in ports) + f" {name}\"\n"
             "template=\"name=X1\"")
    else:
        k = "type=subcircuit\nformat=\"@name @pinlist @symname\"\ntemplate=\"name=x1\""
    s = [HDR + "K {" + k + "\n}\nV {}\nS {}\nE {}", f"B 4 -60 0 60 {h} {{}}",
         f"T {{@symname}} 0 {-28} 0 0 0.3 0.3 {{hcenter=true}}", f"T {{@name}} 0 {h + 4} 0 0 0.2 0.2 {{hcenter=true}}"]
    open(path, "w").write("\n".join(s + body) + "\n")
    return pins, h


def kv(toks):
    return {a.split("=", 1)[0].lower(): a.split("=", 1)[1] for a in toks if "=" in a}


def classify(t, cells, lports, outdir):
    """-> (symbol ref, pin names in SPICE order, attr string, sym pin coords, height)."""
    name = t[0]
    if t[0][0] in "Rr":
        return "res.sym", ["P", "M"], f"name={name} value={t[3]} m=1", sym_pins(DEV + "/res.sym"), 60
    if t[0][0] in "Cc":
        return "capa.sym", ["p", "m"], f"name={name} value={t[3]} m=1", sym_pins(DEV + "/capa.sym"), 60
    k = max(i for i, x in enumerate(t) if "=" not in x)
    model, p = t[k], kv(t[k + 1:])
    nm = name[1:]
    if model.startswith("sky130_fd_pr__"):
        dev = model[len("sky130_fd_pr__"):]
        if "fet" in dev:
            s = f"sky130_fd_pr/{dev}.sym"
            a = f"name={nm} L={p['l']} W={p['w']} nf=1 mult={p.get('m', '1')} model={dev} spiceprefix=X"
            return s, ["D", "G", "S", "B"], a, sym_pins(f"{XS}/{s}"), 60
        if dev.startswith("res_xhigh_po"):
            s = f"sky130_fd_pr/{dev}.sym"
            a = f"name={nm} L={p['l']} mult={p.get('m', '1')} model={dev} spiceprefix=X"
            return s, ["P", "M", "B"], a, sym_pins(f"{XS}/{s}"), 60
        if dev.startswith("pnp_05v5"):
            s = "sky130_fd_pr/pnp_05v5.sym"
            a = f"name={nm} model={dev} m={p.get('m', '1')} spiceprefix=X"
            return s, ["collector", "base", "emitter"], a, sym_pins(f"{XS}/{s}"), 60
        if dev == "cap_mim_m3_1":
            s = "sky130_fd_pr/cap_mim_m3_1.sym"
            a = f"name={nm} W={p['w']} L={p['l']} MF={p.get('mf', '1')} model={dev} spiceprefix=X"
            return s, ["c0", "c1"], a, sym_pins(f"{XS}/{s}"), 60
        raise ValueError(model)
    if model.startswith("sky130_fd_sc_"):
        os.makedirs(os.path.join(outdir, "cells"), exist_ok=True)
        pins, h = gen_sym(os.path.join(outdir, "cells", model + ".sym"), model, lports[model], primitive=True)
        return f"cells/{model}.sym", lports[model], f"name={name}", pins, h
    pins, h = gen_sym(os.path.join(outdir, model + ".sym"), model, cells[model]["ports"])
    return f"{model}.sym", cells[model]["ports"], f"name={name}", pins, h


def gen_sch(cell, c, cells, lports, outdir, brk):
    out = [HDR + "K {}\nV {}\nS {}\nE {}"]
    lab = 0
    for i, p in enumerate(c["ports"]):
        y = 40 * i
        out += [f"N -440 {y} -400 {y} {{lab={p}}}", f"C {{iopin.sym}} -440 {y} 0 0 {{name=p{i} lab={p}}}",
                f"C {{lab_pin.sym}} -400 {y} 0 0 {{name=lp{i} lab={p}}}"]
    x, y, colh = 0, 0, 0
    for t in c["el"]:
        sym, pn, attr, pins, h = classify(t, cells, lports, outdir)
        if brk and cell == brk[2] and brk[0] in (t[0], t[0][1:]) and "done" not in brk:
            a, v = brk[1].split("=")
            attr, n = re.subn(rf"\b{a}=\S+", f"{a}={v}", attr)
            assert n == 1, (brk, attr)
            brk.append("done")
        k = max(i for i, z in enumerate(t) if "=" not in z) if t[0][0] in "Xx" else 3
        nets = t[1:k]
        assert len(nets) == len(pn), (t, pn)
        if y + h > 3000:
            x, y = x + 400, 0
        ox, oy = x + 100, y + 60
        out.append(f"C {{{sym}}} {ox} {oy} 0 0 {{{attr}}}")
        for pname, net in zip(pn, nets):
            px, py = pins[pname]
            ax, ay = ox + px, oy + py
            if px < 0:
                bx, by = ax - 20, ay
            elif px > 0:
                bx, by = ax + 20, ay
            else:
                bx, by = ax, ay + (-20 if py < 0 else 20)
            lab += 1
            out += [f"N {ax:g} {ay:g} {bx:g} {by:g} {{lab={net}}}",
                    f"C {{lab_pin.sym}} {bx:g} {by:g} 0 0 {{name=l{lab} lab={net}}}"]
        y += h + 100
    open(os.path.join(outdir, cell + ".sch"), "w").write("\n".join(out) + "\n")


def main(argv):
    ref, outdir = argv[0], argv[1]
    brk = argv[3].replace("/", ":", 1).split(":") if len(argv) > 3 and argv[2] == "--break" else None
    if brk:
        brk = [brk[1], brk[2], brk[0]]          # inst, attr=val, cell (CELL/INST:ATTR=VAL)
    os.makedirs(outdir, exist_ok=True)
    cells, lports = parse(ref), lib_ports()
    for cell, c in cells.items():
        gen_sym(os.path.join(outdir, cell + ".sym"), cell, c["ports"])
        gen_sch(cell, c, cells, lports, outdir, brk)
    if brk and "done" not in brk:
        sys.exit(f"sch_gen: --break target not found: {brk}")


if __name__ == "__main__":
    main(sys.argv[1:])
