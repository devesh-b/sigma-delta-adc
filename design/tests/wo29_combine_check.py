#!/usr/bin/env python3
"""WO-29 item 4: combine() broken-copy rule, exercised through the c1b_gateb.py --combine CLI on real WO-26 sr95 parts.
Sandbox only:  python wo29_combine_check.py SRC_DIR WORK_DIR
SRC_DIR holds gb_sr95_O1_N1024_p<i>o6.json (read-only; copied into WORK_DIR cases). Expected (not derived from the code):
  A  sr95 parts as-is, --copy sr95        -> "broken copy REJECTED (good)", exit 0, endpoint disagreement reported as info
  B  same parts, nominal combine rule     -> COMBINE INVALID (exit 2): a nominal run still needs endpoint agreement
  C  one part carries a problem           -> broken copy INVALID (not REJECTED): unhealthy parts never count as a rejection
  D  every part's INL set to 1 ppm (< 5)  -> broken copy PASSED (check is blind), exit 1
  E  one part missing                     -> COMBINE INVALID (exit 2)
"""
import glob, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GB = os.path.join(HERE, "..", "c1_ota1", "c1b_gateb.py")


def case(work, name, src, edit=None, drop=None, copy="sr95"):
    d = os.path.join(work, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for i, f in enumerate(src):
        if drop is not None and i == drop:
            continue
        r = json.load(open(f))
        if edit:
            edit(i, r)
        nm = os.path.basename(f).replace("gb_sr95", f"gb_{copy}")
        json.dump(r, open(os.path.join(d, nm), "w"))
    p = subprocess.run([sys.executable, GB, d, "--combine", "6", "--copy", copy], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1][:300]


def main():
    src = sorted(glob.glob(os.path.join(sys.argv[1], "gb_sr95_O1_N1024_p*o6.json")))
    assert len(src) == 6, src
    work = sys.argv[2]

    def prob(i, r):
        if i == 2:
            r["problems"] = ["injected problem (WO-29 case C)"]

    def small(i, r):
        r["inl_ep_ppm"] = 1.0

    exp = {"A": (0, "REJECTED"), "B": (2, "COMBINE INVALID"), "C": (1, "INVALID"), "D": (1, "PASSED"), "E": (2, "COMBINE INVALID")}
    got = {"A": case(work, "A", src), "B": case(work, "B", src, copy="nom"), "C": case(work, "C", src, edit=prob),
           "D": case(work, "D", src, edit=small), "E": case(work, "E", src, drop=4)}
    nf = 0
    for k, (rc, last) in got.items():
        ok = rc == exp[k][0] and exp[k][1] in last and not (k == "C" and "REJECTED" in last)
        nf += not ok
        print(json.dumps(dict(case=k, exit=rc, last=last, expected=exp[k], ok=ok)))
    print("VERDICT", "ACCEPT" if nf == 0 else f"REJECT ({nf})")
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()
