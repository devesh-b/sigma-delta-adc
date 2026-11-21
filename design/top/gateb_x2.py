#!/usr/bin/env python3
"""WO-105 item 3 (D95): precision gate B (c1b_gateb.py --mode prec: 2 MHz, base bias, 1.333 ppm) with OTA1 AND OTA2 at
transistor level. OTA2 = the D91 cell (design/c2_ota2/ota2.spice, ota1 port order) on OTA1's bias nets, through the
gen_tier1 ota2_xtor hook (island shunt + output short reset, stage-2 top plates / bleeders on V_ICM). Sandbox only:
    python gateb_x2.py OUTDIR --mode prec --opt O2 --n 1024 --m 21 --corner 0 --part i/6 [--ota2-sub PATH]
    python gateb_x2.py OUTDIR --mode prec --opt O2 --n 1024 --combine 6
All c1b_gateb arguments pass through; use an OUT dir of its own (the tags are c1b_gateb's gbp_*)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "c1_ota1")]
import c1b_gateb as G  # noqa: E402

SUB = os.path.join(HERE, "..", "c2_ota2", "ota2.spice")
if "--ota2-sub" in sys.argv:
    i = sys.argv.index("--ota2-sub")
    SUB = sys.argv[i + 1]
    del sys.argv[i:i + 2]
SUB = os.path.abspath(SUB)
_cfg = G.cfg


def cfg(a):
    if a.mode != "prec":
        raise SystemExit("WO-105 OTA2 hook: prec mode only (D91 OTA2 at base bias, no boost leg)")
    c, corner = _cfg(a)
    c = dict(c, ota2_xtor=dict(subckt=SUB, name="ota2", cp_vg_ext=0.035e-12, c_out_ext=G.C_OUT_EXT))
    print(f"WO-105: transistor OTA2 {SUB} on OTA1 bias nets")
    return c, corner


G.cfg = cfg

if __name__ == "__main__":
    G.main()
