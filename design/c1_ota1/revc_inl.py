#!/usr/bin/env python3
"""WO-23 item 5, WO-24 role tagging (CL-1b/1c/1d): push each measured OTA1 A(v) table through the model INL in strict mode. Sandbox only:
    PYTHONPATH=<dir holding model/> python revc_inl.py AVTAB_DIR

Table on stage 1 only (OTA1 under test; OTA2 ideal, a0_db2 = inf); av_strict=True, so an integrator state outside the
table range raises -> REJECT (no np.interp clamp). Static INL = s1_vref.inl_v2 (u +-0.9, 401 points, residue on).
Gates (share/1.5, SPEC 3.0 OTA row 8 ppm, CL-1b): boost N 1024 at 4 MHz <= 3.33 ppm; precision N 1024 and N 4096 <= 5.33 ppm.
Row roles (RC-m5, CL-1c/CL-1d per-mode broken copies), from the copy name and mode:
  info     = sensitivity rows, reported only: m_pl L 0.5 copies ("mutb*", D55: sensitivity row) and every precision-mode
             (boost 1.0) mutant (the PMOS cascode short belongs to the precision A0 row, CL-1d, not to the INL gate);
  mutant   = boost-mode broken copies (PMOS cascode short "mutpcb2" at ss/125 boost): must REJECT, a pass is a blind check;
  nominal  = every other row: must ACCEPT.
Exit 0 only if every nominal row ACCEPTs and every must-reject mutant REJECTs, AND the expected row set is present
(REVIEW-C1b M6): 9 corners x (precision 2 N-gates + boost 1 N-gate) = 27 evaluated nominal rows, at least one evaluated
must-reject mutant (mutpcb2 at ss/125 boost), a mutant with no table counts as bad, and an empty directory REJECTs.
"""
import glob, json, os, sys
import numpy as np
from model import iadc as m
from model.studies import s1_vref as s1
from model.studies import s3_budget as s3

GATE = {2.0: [(1024, 5.0 / 1.5)], 1.0: [(1024, 8.0 / 1.5), (4096, 8.0 / 1.5)]}
N_CORNERS = 9   # revc_check.CORNERS9
EXPECT_NOMINAL = N_CORNERS * sum(len(v) for v in GATE.values())   # corners x modes x N-gates (b1 + b2 per corner)
MUST_REJECT = "mutpcb2"   # PMOS cascode short, ss/125 boost


def role(sfx, t):
    if t.get("info") or sfx.startswith("mutb") or (t.get("mutant") and t.get("boost") != 2.0):
        return "info"
    return "mutant" if t.get("mutant") else "nominal"


def inl(tab, N, fs):
    p = s3.ideal_base(fs=fs, N=N, a0_db=np.inf, av_table1=tuple(map(tuple, tab)), av_strict=True)
    try:
        r = s1.inl_v2(p, N, True)["inl_ppm"]
        return r, None, dict(m.LAST_RUN)
    except m.AvTableRangeError as e:
        return float("nan"), str(e), dict(m.LAST_RUN)


def main():
    rows, bad, n_nom, n_mut = [], 0, 0, 0
    files = sorted(glob.glob(os.path.join(sys.argv[1], "avtab_*.json")))
    if not files:
        print("no avtab_*.json in", sys.argv[1])
        bad += 1
    for fn in files:
        for sfx, t in json.load(open(fn)).items():
            if "table" not in t:
                rows.append(dict(corner=f"{t['corner']}/{t['temp']}", copy=sfx, verdict="REJECT (no table)"))
                bad += role(sfx, t) in ("nominal", "mutant")   # a mutant with no table is a bad run, not a rejection
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
                rl = role(sfx, t)
                if rl == "info":
                    r["info_only"] = True
                elif rl == "mutant":
                    n_mut += sfx == MUST_REJECT
                    r["mutant_verdict"] = "REJECTED (good)" if not ok else "PASSED (check is blind)"
                    bad += ok
                else:
                    n_nom += 1
                    bad += not ok
                rows.append(r)
                print(json.dumps(r), flush=True)
    if files and n_nom != EXPECT_NOMINAL:
        print(f"nominal rows evaluated {n_nom} != expected {EXPECT_NOMINAL}")
        bad += 1
    if files and n_mut < 1:
        print(f"no evaluated must-reject mutant ({MUST_REJECT} at ss/125 boost)")
        bad += 1
    json.dump(rows, open(os.path.join(sys.argv[1], "table_inl.json"), "w"), indent=0)
    print("VERDICT", "ACCEPT" if bad == 0 else f"REJECT ({bad})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
