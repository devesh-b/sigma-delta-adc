#!/usr/bin/env python3
"""WO-85 tim-abort experiments on the WO-79 tim decks (bench-only variants, one change per run).

    python exp85.py SRC_DECK OUTDIR TAG VARIANT[,VARIANT...]

Adds to the WO-79 exp.py variants (none, gear, tight, tstop=X, ...):
  vddideal   undo soften() on the supplies only: Vdd / Vdl straight on vdd / vdl again (Rz_vdd / Rz_vdl removed)
  decap=C    shunt C on vdd and vdl (on-chip decoupling behind the 1 ohm bond R)
Prints one line: TAG ok|ABORT time trouble-node rows.
"""
import os
import re
import sys

sys.path.insert(0, "/home/mempool/regr/tt/WO-79-87a05a2/exp")
import exp  # noqa: E402


def apply(lines, v):
    if v == "vddideal":
        out = []
        for ln in lines:
            if re.match(r"^Rz_(vdd|vdl)\s", ln):
                continue
            out.append(re.sub(r"^(Vd[dl])\s+(vd[dl])_z\s+0\s", r"\1 \2 0 ", ln))
        lines[:] = out
    elif v.startswith("decap="):
        c = v[6:]
        i = next(i for i, ln in enumerate(lines) if ln.startswith("Rz_vdl"))
        lines[i + 1:i + 1] = [f"Cdec_vdd vdd 0 {c}", f"Cdec_vdl vdl 0 {c}"]
    else:
        exp.apply(lines, v)


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
    r = exp.subprocess.run(["ngspice", "-b", tag + ".sp"], cwd=out, capture_output=True, text=True, timeout=5400)
    log = r.stdout + r.stderr
    open(os.path.join(out, tag + ".log"), "w").write(log)
    ab = [ln for ln in log.splitlines() if "timestep too small" in ln.lower()]
    csv = os.path.join(out, tag + ".csv")
    rows = sum(1 for _ in open(csv)) if os.path.exists(csv) else 0
    print(tag, "ABORT " + ab[0].split("time =")[1].strip() if ab else "ok", f"rc={r.returncode} rows={rows}")


if __name__ == "__main__":
    main()
