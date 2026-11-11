#!/usr/bin/env bash
# C9 verification suite (WO-38).  Run INSIDE IIC-OSIC-TOOLS on the sandbox, from a frozen copy, e.g.
#   ~/bin/rta-tt 'scripts/iic "cd /foss/designs/regr/WO-38-<sha>/design/c9_digital/tb && ./run.sh all"'
# Steps: agree (Ref A vs golden v3.1 + Ref A mutants), lint, cocotb (icarus), formal (sby).  Env: QUICK=1,
# C9_FULL=1, C9_SEED, TESTS=<regex>, C9_OUT.  Exit != 0 if any step fails or a results file is missing.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RTL=${C9_RTL:-$HERE/../rtl}
TOP=${C9_TOP:-tt_um_sd_adc_c9}
export C9_OUT=${C9_OUT:-$HERE/out}
mkdir -p "$C9_OUT"
cd "$HERE"
rc=0
step() { echo "== $1: $2"; [ "$2" = PASS ] || rc=1; }
want() { [ "$WHAT" = all ] || [ "$WHAT" = "$1" ]; }
WHAT=${1:-all}
if want agree; then
  timeout 7200 nice -n 10 python3 test_refa_golden.py ${QUICK:+--quick} --out "$C9_OUT/refa.json" > "$C9_OUT/refa.log" 2>&1
  r=$?; tail -3 "$C9_OUT/refa.log"
  { [ $r = 0 ] && grep -q '"result": "PASS"' "$C9_OUT/refa.json"; } && step agree PASS || step agree FAIL
fi
if want lint; then
  timeout 300 verilator --lint-only -Wall --top-module "$TOP" "$RTL"/*.v > "$C9_OUT/lint.log" 2>&1
  [ $? = 0 ] && step lint PASS || { step lint FAIL; head -20 "$C9_OUT/lint.log"; }
  timeout 300 yosys -q -p "read_verilog $RTL/*.v; synth -top $TOP -flatten; check -assert; stat" > "$C9_OUT/yosys.log" 2>&1
  [ $? = 0 ] && step yosys-check PASS || { step yosys-check FAIL; tail -20 "$C9_OUT/yosys.log"; }
fi
if want cocotb; then
  timeout ${C9_TO:-28800} nice -n 10 python3 run_cocotb.py > "$C9_OUT/cocotb.log" 2>&1
  r=$?; grep -E 'PASS|FAIL|RESULT' "$C9_OUT/cocotb.log" | grep -vE '^\s*$' | tail -30
  [ $r = 0 ] && step cocotb PASS || step cocotb FAIL
fi
if want formal; then
  ( cd formal && rm -rf c9_props_* && timeout 3600 sby -f c9_props.sby > "$C9_OUT/formal.log" 2>&1 )
  r=$?; grep -E 'DONE|PASS|FAIL|Assert|Cover' "$C9_OUT/formal.log" | tail -20
  [ $r = 0 ] && step formal PASS || step formal FAIL
fi
echo "RUN RESULT rc=$rc"
exit $rc
