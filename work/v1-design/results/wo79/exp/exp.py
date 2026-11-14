#!/usr/bin/env python3
"""WO-79 timestep-abort experiments: apply bench-only variants to an existing WO-70 deck, run ngspice, report.

    python exp.py SRC_DECK OUTDIR TAG VARIANT[,VARIANT...]

Variants (each is a bench change, never a design change):
  none          deck as-is (must reproduce the abort: proves the experiment can fail)
  gear          add method=gear to the first .option line
  drvall        every bare digital-input source (yin swin shin chin rsin ordin) -> source, 100 ohm, 5 fF (as drv())
  opbw          1e5 E-source integrators -> 1e5 gain, one pole at 10 kHz (GBW 1 GHz), unity buffer
  swsmooth      ideal `sw` switches -> smooth B-source conductance (ron 10, roff 1e12, tanh over 50 mV)
  rsrc=N1:N2    series 10 ohm at the named source nodes (e.g. Vinp/Vinn), source moved to node_s
  tstop=X       truncate the transient
  tight         reltol and abstol / 10 (tolerance invariance check, only after a variant runs)
Prints one line: TAG ok|ABORT time trouble-node rows.
"""
import os
import re
import subprocess
import sys


def apply(lines, v):
    if v == "gear":
        for i, ln in enumerate(lines):
            if ln.startswith(".option") and "method" not in ln:
                lines[i] = ln + " method=gear"
                break
    elif v == "drvall":
        out = []
        for ln in lines:
            m = re.match(r"^(V(?:y|sw|sh|ch|rs|ord))\s+((?:yin|swin|shin|chin|rsin|ordin))\s+0\s+(.*)$", ln)
            if m:
                n = m.group(2)
                out += [f"{m.group(1)} {n}_s 0 {m.group(3)}", f"Rdrv_{n} {n}_s {n} 100", f"Cdrv_{n} {n} 0 5f"]
            else:
                out.append(ln)
        lines[:] = out
    elif v == "opbw":
        out = []
        for ln in lines:
            m = re.match(r"^E(i?op)(\w)\s+(\S+)\s+0\s+vicm\s+(\S+)\s+1e5$", ln)
            if m:
                k = m.group(1) + m.group(2)
                out += [f"E{k} {k}_a 0 vicm {m.group(4)} 1e5", f"R{k}p {k}_a {k}_b 1e6", f"C{k}p {k}_b 0 15.9p",
                        f"E{k}o {m.group(3)} 0 {k}_b 0 1"]
            else:
                out.append(ln)
        lines[:] = out
    elif v == "swsmooth":
        out = []
        for ln in lines:
            m = re.match(r"^S(\w+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(SWI|SWR)$", ln)
            if m:
                vt = "VTI" if m.group(6) == "SWI" else "0.5"
                a, b, c, r = m.group(2), m.group(3), m.group(4), m.group(5)
                out.append(f"BS{m.group(1)} {a} {b} I = (V({a})-V({b}))*(1e-12 + 0.1*0.5*(1+tanh((V({c})-V({r})-{vt})/0.05)))")
            else:
                out.append(ln)
        vti = next((re.search(r"vt=(\S+)", ln).group(1) for ln in lines if ln.startswith(".model SWI")), "1.65")
        lines[:] = [ln.replace("VTI", vti) for ln in out]
    elif v.startswith("rsrc="):
        for n in v[5:].split(":"):
            for i, ln in enumerate(lines):
                m = re.match(rf"^(V\w+)\s+{n}\s+0\s+(.*)$", ln)
                if m:
                    lines[i] = f"{m.group(1)} {n}_s 0 {m.group(2)}\nRsrc_{n} {n}_s {n} 10"
    elif v.startswith("tstop="):
        for i, ln in enumerate(lines):
            if ln.startswith(".tran"):
                p = ln.split()
                p[2] = v[6:]
                lines[i] = " ".join(p)
    elif v == "tight":
        for i, ln in enumerate(lines):
            if ln.startswith(".option"):
                def sc(m):
                    return f"{m.group(1)}={float(m.group(2)) / 10:g}"
                ln = re.sub(r"(reltol|abstol)=([0-9.eE+-]+)", sc, ln)
                if "reltol" not in ln:
                    ln += " reltol=1e-5"
                if "abstol" not in ln:
                    ln += " abstol=1e-13"
                lines[i] = ln
                break
    elif v != "none":
        raise SystemExit("unknown variant " + v)


def main():
    src, out, tag, vs = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    lines = open(src).read().splitlines()
    for v in vs.split(","):
        apply(lines, v)
    txt = "\n".join(lines) + "\n"
    txt = re.sub(r"wrdata \S+", f"wrdata {os.path.join(out, tag)}.csv", txt)
    open(os.path.join(out, ".spiceinit"), "w").write("set num_threads=1\n")
    open(os.path.join(out, tag + ".sp"), "w").write(txt)
    r = subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=5400)
    log = r.stdout + r.stderr
    open(os.path.join(out, tag + ".log"), "w").write(log)
    ab = [ln for ln in log.splitlines() if "timestep too small" in ln.lower()]
    csv = os.path.join(out, tag + ".csv")
    rows = sum(1 for _ in open(csv)) if os.path.exists(csv) else 0
    print(tag, "ABORT " + ab[0].split("time =")[1].strip() if ab else "ok", f"rc={r.returncode} rows={rows}")


if __name__ == "__main__":
    main()
