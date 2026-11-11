"""Ref A <-> golden v3.1 agreement (no RTL needed), plus the proof that the agreement can fail.

  python3 test_refa_golden.py [--quick] [--out results.json]

Exit 0 only if: every golden item agrees, the compared counts equal the counts in the file (no empty
compare), and every Ref A mutant is rejected by at least one item.
"""
import json
import sys
import time

import golden_harness as gh
from ref_a import MUTANTS, RESET_CFG, DIV, HOLD_RESET_TAG, RefA


def agreement(g, mut=None, quick=False, junk="raw0"):
    mism, counts = [], dict(vec_frames=0, seq_frames=0, hold=0, trace_rows=0, cfg_shift=0, static=0)
    # static items
    if mut is None:
        for code, d in g["fs_div_table"].items():
            if code.isdigit() and DIV[int(code)] != d["div"]:
                mism.append(f"fs_div_table {code}: {DIV[int(code)]} != {d['div']}")
        counts["static"] += 1
    r = gh.released_ref(mut)
    hr = g["hold_reset"]
    if r.word(4) != gh.h16(hr["tag_word"]) or r.status() != gh.h16(hr["status_word"]) or r.word(0) or r.word(3):
        mism.append(f"hold_reset tag {r.word(4):04x} status {r.status():04x}")
    counts["static"] += 1
    rc = g["reset"]
    exp_rst, _ = gh.cfg_word(dict(rc, cfg_word=None))
    if RefA(mut=mut).active != exp_rst & 0x1FFF:
        mism.append(f"reset cfg {RefA(mut=mut).active:04x} != {exp_rst:04x}")
    counts["static"] += 1
    # vectors
    for v in g["vectors"]:
        if quick and v["config"]["N"] > 256 and v["kind"] in ("mode", "offset"):
            continue
        run = gh.run_vector(v, mut, junk=junk)
        counts["vec_frames"] += gh.cmp_frames(v["id"], v["frames"], run, mism)
    for s in g.get("streams", []):
        run = gh.run_vector(s, mut, junk=junk)
        counts["vec_frames"] += gh.cmp_frames(s["id"], s["frames"], run, mism)
    # sequences (incl. hold/rd/overrun/cfg_pending)
    for s in g["sequences"]:
        run = gh.run_sequence(s, mut)
        counts["seq_frames"] += gh.cmp_frames(s["id"], s["frames"], run, mism)
        counts["hold"] += gh.cmp_hold(s["id"], s, run, mism)
        run0 = gh.run_sequence(s, mut, wofs=0)          # writes exactly on the start edge: frames only
        counts["seq_frames_edge"] = counts.get("seq_frames_edge", 0) + gh.cmp_frames(s["id"] + "@edge", s["frames"], run0, mism, check_status=False)
    # control trace
    for tr in g["traces"]:
        run = gh.run_trace(tr, mut)
        rows = tr["trace"]["rows"]
        got = run.rows[:len(rows)]
        for i, (a, b) in enumerate(zip(got, rows)):
            if a != b:
                mism.append(f"{tr['id']} row {i} (slot {i // 66} c {i % 66}): {a} != {b}")
        if len(got) != len(rows):
            mism.append(f"{tr['id']}: {len(got)} rows != {len(rows)}")
        counts["trace_rows"] += len(got)
        counts["seq_frames"] += gh.cmp_frames(tr["id"], tr.get("frames", []), run, mism)
    # serial shift register
    for case in g["cfg_shift"]:
        got = gh.run_cfg_shift(case, mut)
        if got != case["expect"]:
            mism.append(f"cfg_shift {case['id']}: {got} != {case['expect']}")
        counts["cfg_shift"] += 1
    return mism, counts


def expected_counts(g, quick):
    vf = sum(len(v["frames"]) for v in g["vectors"]
             if not (quick and v["config"]["N"] > 256 and v["kind"] in ("mode", "offset")))
    vf += sum(len(s["frames"]) for s in g.get("streams", []))
    sf = sum(len(s["frames"]) for s in g["sequences"]) + sum(len(t.get("frames", [])) for t in g["traces"])
    return dict(vec_frames=vf, seq_frames=sf, hold=sum(len(s.get("hold", [])) for s in g["sequences"]),
                trace_rows=sum(len(t["trace"]["rows"]) for t in g["traces"]), cfg_shift=len(g["cfg_shift"]))


def main():
    quick = "--quick" in sys.argv
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    g = gh.load_golden()
    print(f"golden rev {g.get('rev')} format {g.get('format')} file {gh.GOLDEN}")
    t0 = time.time()
    res = dict(rev=g.get("rev"), quick=quick)
    ok = True
    for junk in ("raw0", "toggle"):
        mism, counts = agreement(g, quick=quick, junk=junk)
        exp = expected_counts(g, quick)
        short = {k: (counts[k], exp[k]) for k in exp if counts[k] != exp[k]}
        print(f"[agree junk={junk}] mismatches {len(mism)}; counts {counts}; expected {exp}; "
              f"{time.time() - t0:.1f}s")
        for m in mism[:25]:
            print("  MISMATCH", m)
        if mism or short:
            ok = False
            if short:
                print("  COUNT SHORTFALL", short)
        res[f"agree_{junk}"] = dict(mismatches=mism[:200], n_mism=len(mism), counts=counts, expected=exp)
        if quick:
            break
    # mutants: each must be rejected (quick subset is enough to kill; full set when not quick)
    killed, surv = {}, []
    for m in MUTANTS:
        mism, _ = agreement(g, mut=m, quick=True)
        killed[m] = len(mism)
        if not mism:
            surv.append(m)
        print(f"[mutant {m}] {'KILLED' if mism else 'SURVIVED'} ({len(mism)} mismatches; first: "
              f"{mism[0] if mism else '-'})")
    res["mutants"] = dict(killed=killed, survivors=surv, rate=f"{len(MUTANTS) - len(surv)}/{len(MUTANTS)}")
    if surv:
        ok = False
    print(f"mutant kill rate {len(MUTANTS) - len(surv)}/{len(MUTANTS)}; survivors {surv}")
    print("RESULT", "PASS" if ok else "FAIL", f"{time.time() - t0:.1f}s")
    if out:
        with open(out, "w") as f:
            json.dump(dict(res, result="PASS" if ok else "FAIL"), f, indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
