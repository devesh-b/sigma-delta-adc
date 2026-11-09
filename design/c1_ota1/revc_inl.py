#!/usr/bin/env python3
"""WO-23 item 5 (CL-1b): push each measured OTA1 A(v) table through the model INL in strict mode. Sandbox only:
    PYTHONPATH=<dir holding model/> python revc_inl.py AVTAB_DIR

Table on stage 1 only (OTA1 under test; OTA2 ideal, a0_db2 = inf); av_strict=True, so an integrator state outside the
table range raises -> REJECT (no np.interp clamp). Static INL = s1_vref.inl_v2 (u +-0.9, 401 points, residue on).
Gates (share/1.5, SPEC 3.0 OTA row 8 ppm, CL-1b): boost N 1024 at 4 MHz <= 3.33 ppm; precision N 1024 and N 4096 <= 5.33 ppm.
Broken copies (mutant tables, m_pl L 0.5) must REJECT; a passing mutant makes the exit code nonzero (blind check).
"""
import glob, json, os, sys
import numpy as np
from model import iadc as m
from model.studies import s1_vref as s1
from model.studies import s3_budget as s3

GATE = {2.0: [(1024, 5.0 / 1.5)], 1.0: [(1024, 8.0 / 1.5), (4096, 8.0 / 1.5)]}


def inl(tab, N, fs):
    p = s3.ideal_base(fs=fs, N=N, a0_db=np.inf, av_table1=tuple(map(tuple, tab)), av_strict=True)
    try:
        r = s1.inl_v2(p, N, True)["inl_ppm"]
        return r, None, dict(m.LAST_RUN)
    except m.AvTableRangeError as e:
        return float("nan"), str(e), dict(m.LAST_RUN)


def main():
    rows, bad = [], 0
    for fn in sorted(glob.glob(os.path.join(sys.argv[1], "avtab_*.json"))):
        for sfx, t in json.load(open(fn)).items():
            if "table" not in t:
                rows.append(dict(corner=f"{t['corner']}/{t['temp']}", copy=sfx, verdict="REJECT (no table)"))
                bad += not (t.get("mutant") or t.get("info"))
                continue
            for N, gate in GATE[t["boost"]]:
                fs = 4e6 if t["boost"] == 2.0 else s3.FS
                v, err, lr = inl(t["table"], N, fs)
                ok = err is None and np.isfinite(v) and v <= gate
                r = dict(corner=f"{t['corner']}/{t['temp']}/{t['vdd']}", copy=sfx, boost=t["boost"], N=N, fs_MHz=fs / 1e6,
                         inl_ppm=round(v, 3) if np.isfinite(v) else None, gate_ppm=round(gate, 3), table_vmax=t["vmax"],
                         x1max_v=round(lr["x1max_v"], 4), x2max_v=round(lr["x2max_v"], 4), err=err,
                         A0_ac_dB=round(t["A0_ac_dB"], 2), Amin_1p4_dB=round(min(a for x, a in t["table"] if x <= 1.4), 2),
                         verdict="ACCEPT" if ok else "REJECT")
                if t.get("info"):
                    r["info_only"] = True
                elif t.get("mutant"):
                    r["mutant_verdict"] = "REJECTED (good)" if not ok else "PASSED (check is blind)"
                    bad += ok
                else:
                    bad += not ok
                rows.append(r)
                print(json.dumps(r), flush=True)
    json.dump(rows, open(os.path.join(sys.argv[1], "table_inl.json"), "w"), indent=0)
    print("VERDICT", "ACCEPT" if bad == 0 else f"REJECT ({bad})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
