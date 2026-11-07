#!/usr/bin/env bash
# s0_toolcheck.sh — record tool versions (IIC image + nix fallback) and run the nfet .op smoke test.
# Run on the sandbox: ~/bin/rta-tt 'cd /home/mempool/tt-sd && scripts/s0_toolcheck.sh'
# SMOKE_CORNER=ff (non-vacuity) must REJECT. Prints ACCEPT/REJECT; nonzero on REJECT.
# Expected Id = 46.8 uA +-1 % (WORKFLOW §4), independent of any code here.
set -uo pipefail
OUT=${OUT:-/home/mempool/regr/tt/WO-01}
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
  echo "open_pdks=$(cat ${PDK_ROOT:-/nonexistent}/sky130A/SOURCES 2>/dev/null | grep -m1 open_pdks || echo n/a)"
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

mkdir -p "$OUT"
IIC=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/iic
SELF=/foss/designs/tt-sd/scripts/s0_toolcheck.sh
nice -n 10 env SMOKE_CORNER=$CORNER timeout 300 "$IIC" "SMOKE_CORNER=$CORNER bash $SELF --inner" > "$OUT/tools_iic.txt" 2>"$OUT/tools_iic.err"
# nix fallback: needs PDK_ROOT from init-tt.sh
nice -n 10 env SMOKE_CORNER=$CORNER PDK_ROOT=${PDK_ROOT:-/home/mempool/.ciel} timeout 300 bash "$0" --inner > "$OUT/tools_nix.txt" 2>"$OUT/tools_nix.err"
{ echo "docker_tags=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E 'iic-osic|librelane' | paste -sd, -)"
  echo "open_pdks_hash=$(cat /home/mempool/.ciel/sky130A/.. 2>/dev/null; ls /home/mempool/.ciel/ciel/sky130/versions 2>/dev/null | head -1)"; } > "$OUT/tools_host.txt"

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
for env in ("iic", "nix"):
    try:
        i = float(rec[env]["smoke_id"])
        good = math.isfinite(i) and abs(i - expect) / expect <= tol
    except Exception:
        i, good = None, False
    rec[env]["smoke_ok"] = good
    print(f"{env}: Id={i} expect {expect} +-{tol*100}% -> {'ok' if good else 'bad'}")
    ok &= good
    for k in ("ngspice", "magic", "netgen", "klayout", "yosys", "python"):
        if not rec[env].get(k):
            print(f"{env}: missing version {k}"); ok = False
json.dump(rec, open(f"{out}/s0_tools.json", "w"), indent=1)
print("ACCEPT" if ok else "REJECT")
sys.exit(0 if ok else 1)
PY
