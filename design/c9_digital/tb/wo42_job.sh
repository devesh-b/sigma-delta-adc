#!/usr/bin/env bash
# WO-42 jobs.  Run INSIDE IIC-OSIC-TOOLS from the frozen tb dir, one lpool line each.  Outputs under ../wo42/.
#   fcov SEED          full suite (icarus) incl. c01..c07 + r01, collector JSON in ../wo42/fcov_sSEED/fcov
#   r01 A B            R-01 seeds A..B (icarus), one dir per seed
#   soak SEED SLOTS    SOAK-01: r01 with SLOTS slots on Verilator
#   x01 SEED           X-01: Verilator --x-initial unique + rand reset, init seed SEED
#   full I/N | other   C9_FULL: d_dec01 vector shard I/N, or the other FULL items
#   fml MID            per-property PDR (mut_formal.sh); MID base|M07|M07b|M19|...
#   merge              fcov merge of every ../wo42/**/fcov
set -u
HERE=$(cd "$(dirname "$0")" && pwd); K=$1; shift
R=$HERE/../wo42; mkdir -p "$R"
run() { D=$1; shift; rm -rf "$D"; mkdir -p "$D"; env C9_OUT="$D" C9_RUNDIR="$D" "$@" python3 "$HERE/run_cocotb.py" > "$D/cocotb.log" 2>&1; echo "rc=$? $(grep RESULT "$D/cocotb.log" | tail -1)"; }
VB="--timescale 1ns/1ps -Wno-fatal"
case $K in
  fcov)  echo "FCOV s$1 $(run "$R/fcov_s$1" C9_SEED=$1 timeout 14400)";;
  r01)   for S in $(seq "$1" "$2"); do echo "R01 s$S $(run "$R/r01/s$S" C9_SEED=$S TESTS='r01_random$' timeout 1800)"; done;;
  soak)  echo "SOAK s$1 $(run "$R/soak_s$1" SIM=verilator C9_SEED=$1 C9_R01_SLOTS=$2 C9_R01_TO=1000000 C9_BUILD_ARGS="$VB" TESTS='r01_random$' timeout 7200)";;
  x01)   echo "X01 s$1 $(run "$R/x01_s$1" SIM=verilator C9_SEED=1 C9_BUILD_ARGS="--x-assign unique --x-initial unique $VB" C9_PLUSARGS="+verilator+rand+reset+2 +verilator+seed+$1" TESTS='(s01_reset_idle|s02_reset_pair_golden|a_seq01_trace_ctl|a_rst01_async_mid|d_bus03_debug|d_inv02_each_field|c07_addr)$' timeout 3600)";;
  full)  if [ "$1" = other ]; then T='(d_dec03_streams|d_cfg05_sequences|d_cfg02_shift|d_frm04_overrun)$'; V=; else T='d_dec01_golden_vectors$'; V=$1; fi
         echo "FULL $1 $(run "$R/full_${1//\//of}" C9_FULL=1 C9_VSHARD=$V TESTS="$T" timeout 14400)";;
  fml)   "$HERE/mut_formal.sh" "$1";;
  merge) python3 "$HERE/fcov.py" merge "$R";;
  *)     echo "unknown job $K"; exit 2;;
esac
