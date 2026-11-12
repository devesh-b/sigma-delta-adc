#!/usr/bin/env bash
# WO-40: Verilator line/toggle/branch coverage, full quick suite, one seed, own dir ../cov/s<seed>.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); S=$1
D=$HERE/../cov/s$S; rm -rf "$D"; mkdir -p "$D"
SIM=verilator C9_SEED=$S C9_OUT=$D C9_RUNDIR=$D C9_BUILD_ARGS="--coverage --timescale 1ns/1ps -Wno-fatal" \
  timeout 7200 python3 "$HERE/run_cocotb.py" > "$D/cocotb.log" 2>&1
echo "COV seed $S rc=$? $(grep -E 'RESULT' "$D/cocotb.log" | tail -1)"
ls "$D"/*.dat 2>/dev/null
