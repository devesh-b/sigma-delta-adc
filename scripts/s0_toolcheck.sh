#!/usr/bin/env bash
# s0_toolcheck.sh — record tool versions (IIC image + nix fallback) and run the nfet .op smoke test.
# Run on the sandbox, from the tree you want tested:
#   ~/bin/rta-tt 'cd /home/mempool/tt-sd && OUT=/home/mempool/regr/tt/runs/mytag/tools scripts/s0_toolcheck.sh'
# OUT (outputs) is taken from the env; default /home/mempool/regr/tt/runs/<repo-basename>/tools. OUT must be
# under /home/mempool/regr/tt (the iic wrapper mounts that dir as /foss/designs/regr). The IIC part runs a copy of
# THIS script from OUT, so it tests the script of the tree it was started from, not whatever sits in /home/mempool/tt-sd.
# SMOKE_CORNER=ff (non-vacuity) must REJECT. Prints ACCEPT/REJECT; nonzero on REJECT.
# Expected Id = 46.8 uA +-1 % (WORKFLOW §4), independent of any code here.
set -uo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUT=${OUT:-/home/mempool/regr/tt/runs/$(basename "$REPO")/tools}
CORNER=${SMOKE_CORNER:-tt}
EXPECT=46.8e-6; TOL=0.01

if [ "${1:-}" = "--inner" ]; then
  # runs in either environment; prints key=value lines
  t() { timeout 60 "$@" 2>&1 | head -1 | tr -d '\r' ; }
  echo "ngspice=$(timeout 60 ngspice -v 2>&1 </dev/null | grep -m1 -i -E 'ngspice-[0-9]+|version' | sed 's/^[* ]*//')"
  echo "xschem=$(timeout 60 xschem --version 2>&1 </dev/null | grep -m1 -i -E 'xschem|[0-9]\.[0-9]')"
  echo "magic=$(t magic --version)"
  echo "netgen=$(echo quit | timeout 60 netgen -noconsole 2>&1 | grep -m1 -i -E 'netgen|[0-9]+\.[0-9]+\.[0-9]+')"
  echo "klayout=$(t klayout -v)"
  echo "yosys=$(t yosys -V)"
  echo "iverilog=$(t iverilog -V)"
  echo "verilator=$(t verilator --version)"
  echo "python=$(t python3 --version)"
  echo "numpy=$(timeout 60 python3 -c 'import numpy;print(numpy.__version__)' 2>&1 | tail -1)"
  echo "cocotb=$(timeout 60 python3 -c 'import cocotb;print(cocotb.__version__)' 2>&1 | tail -1)"
  echo "PDK_ROOT=${PDK_ROOT:-unset}"
  echo "open_pdks=$(readlink -f ${PDK_ROOT:-/nonexistent}/sky130A | grep -oE '[0-9a-f]{40}' | head -1)"
  D=$(mktemp -d); cat > $D/n.spice <<SP
* smoke
.lib ${PDK_ROOT}/sky130A/libs.tech/combined/sky130.lib.spice $CORNER
XM1 d g 0 0 sky130_fd_pr__nfet_01v8 W=1 L=0.15 nf=1
Vd d 0 1.8
Vg g 0 0.9
.control
op
let id = -i(Vd)
print id
quit
.endc
.end
SP
  echo "smoke_id=$(timeout 120 ngspice -b $D/n.spice 2>&1 | grep -m1 -E '^id *=' | awk '{print $3}')"
  rm -rf $D
  exit 0
fi

case "$OUT" in /home/mempool/regr/tt/?*) ;; *) echo "REJECT: OUT must be under /home/mempool/regr/tt (got $OUT)"; exit 2;; esac
case "$OUT" in *..*) echo "REJECT: OUT must not contain .."; exit 2;; esac
[ "$(hostname)" = mempool ] || { echo "REJECT: sandbox only"; exit 2; }
mkdir -p "$OUT"
IIC=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/iic
# run a copy of this script from OUT (visible in the container as /foss/designs/regr/...)
cp "${BASH_SOURCE[0]}" "$OUT/s0_toolcheck_inner.sh"
SELF=/foss/designs/regr/${OUT#/home/mempool/regr/tt/}/s0_toolcheck_inner.sh
nice -n 10 env SMOKE_CORNER=$CORNER timeout 300 "$IIC" "SMOKE_CORNER=$CORNER bash $SELF --inner" > "$OUT/tools_iic.txt" 2>"$OUT/tools_iic.err"
# nix fallback: needs PDK_ROOT from init-tt.sh
nice -n 10 env SMOKE_CORNER=$CORNER PDK_ROOT=${PDK_ROOT:-/home/mempool/.ciel} timeout 300 bash "${BASH_SOURCE[0]}" --inner > "$OUT/tools_nix.txt" 2>"$OUT/tools_nix.err"
{ echo "docker_tags=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E 'iic-osic|librelane' | paste -sd, -)"
  echo "open_pdks_hash=$(readlink -f /home/mempool/.ciel/sky130A | grep -oE '[0-9a-f]{40}' | head -1)"; } > "$OUT/tools_host.txt"

python3 - "$OUT" "$EXPECT" "$TOL" "$CORNER" <<'PY'
import sys, json, math, re
out, expect, tol, corner = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
def rd(f):
    d = {}
    for l in open(f"{out}/{f}"):
        if re.match(r"^[A-Za-z_]+=", l):
            k, v = l.rstrip("\n").split("=", 1); d[k] = v
    return d
rec = {"iic": rd("tools_iic.txt"), "nix": rd("tools_nix.txt"), "host": rd("tools_host.txt"),
       "smoke_corner": corner, "expected_id_A": expect, "tol": tol}
ok = True
if not re.fullmatch(r"[0-9a-f]{40}", rec["host"].get("open_pdks_hash", "")):
    print(f"host: open_pdks_hash missing/invalid: {rec['host'].get('open_pdks_hash')!r}"); ok = False
for env in ("iic", "nix"):
    try:
        i = float(rec[env]["smoke_id"])
        good = math.isfinite(i) and abs(i - expect) / expect <= tol
    except Exception:
        i, good = None, False
    rec[env]["smoke_ok"] = good
    print(f"{env}: Id={i} expect {expect} +-{tol*100}% -> {'ok' if good else 'bad'}")
    ok &= good
    if not re.fullmatch(r"[0-9a-f]{40}", rec[env].get("open_pdks", "")):
        print(f"{env}: open_pdks hash missing/invalid: {rec[env].get('open_pdks')!r}"); ok = False
    for k in ("ngspice", "magic", "netgen", "klayout", "yosys", "python"):
        if not rec[env].get(k):
            print(f"{env}: missing version {k}"); ok = False
json.dump(rec, open(f"{out}/s0_tools.json", "w"), indent=1)
print("ACCEPT" if ok else "REJECT")
sys.exit(0 if ok else 1)
PY
