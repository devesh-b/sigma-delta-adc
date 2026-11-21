#!/bin/bash
# Usage (on sandbox, in tool container or oss-cad): ./run.sh [rtl_path]
# Prints ACCEPT/REJECT per case. Expected: real=ACCEPT, ref_good=ACCEPT, mutants=REJECT.
cd "$(dirname "$0")"
RTL=${1:-../rtl/cz_bus8.v}
IV=${IVERILOG:-iverilog}; VVP=${VVP:-vvp}
run() { # name file
  if [ ! -f "$2" ]; then echo "$1: NO-FILE"; return; fi
  $IV -g2012 -o /tmp/czb8_$$.vvp tb_cz_bus8.v "$2" 2>/tmp/czb8_$$.err || { echo "$1: REJECT (compile error)"; return; }
  out=$($VVP /tmp/czb8_$$.vvp)
  if echo "$out" | grep -q TB_PASS; then echo "$1: ACCEPT ($(echo "$out"|grep CHECKS))"; else echo "$1: REJECT ($(echo "$out"|grep CHECKS))"; fi
}
run real_rtl "$RTL"
run ref_good mutants/ref_good.v
run mut_swap mutants/mut_swap.v
run mut_bsel0 mutants/mut_bsel0.v
rm -f /tmp/czb8_$$.*
