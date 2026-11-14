#!/usr/bin/env bash
# WO-42 jobs.  Run INSIDE IIC-OSIC-TOOLS from the frozen tb dir, one lpool line each.  Outputs under ../wo42/.
#   fcov SEED          full suite (icarus) incl. c01..c07 + r01, collector JSON in ../wo42/fcov_sSEED/fcov
#   r01 A B            R-01 seeds A..B (icarus), one dir per seed
#   soak SEED SLOTS    SOAK-01: r01 with SLOTS slots on Verilator
#   x01 SEED           X-01: Verilator --x-initial unique + rand reset, init seed SEED
#   full I/N | other   C9_FULL: d_dec01 vector shard I/N, or the other FULL items
#   test NAME SEED [TO]  one cocotb test (icarus), fcov collector in ../wo42/test_NAME_sSEED/fcov (WO-49B)
#   suite STEP     run.sh STEP (agree|lint|formal|cocotb|all), out ../wo42/suite_STEP (WO-49B)
#   fml MID            per-property PDR (mut_formal.sh); MID base|M07|M07b|M19|...
#   real [TEST]        TEST (default d_hold01_len) at PW_BITS 16 / BIAS_BITS 8 (WO-75, WO-83)
#   fmlw PW B PROP [TO]  one hold property (F18/F19), PDR, chparam PW/B, props -DF_PW/-DF_B (WO-83; 16 8 = real)
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
  test)  echo "TEST $1 s$2 $(run "$R/test_$1_s$2" C9_SEED=$2 TESTS="$1\$" timeout ${3:-7200})";;
  suite) mkdir -p "$R/suite_$1"; env C9_OUT="$R/suite_$1" ./run.sh "$1" > "$R/suite_$1/run.log" 2>&1; echo "SUITE $1 $(grep -E "^== |RUN RESULT" "$R/suite_$1/run.log" | tr "\n" " ")";;
  fml)   "$HERE/mut_formal.sh" "$1";;
  real)  T=${1:-d_hold01_len}; echo "REAL $T $(run "$R/real_$T" C9_PW_BITS=16 C9_BIAS_BITS=8 TESTS="$T\$" timeout 10800)";;   # WO-75/83: 2^16 hold at D85 values
  fmlw)  F=$R/fmlw_$1_$2_$3; rm -rf "$F"; mkdir -p "$F"; awk -v p="// $3 " '/cover *\(/ {next} /assert *\(/ && /\/\/ F[0-9]+ / && index($0, p) == 0 {next} {print}' "$HERE/formal/c9_props.sv" > "$F/c9_props.sv"   # WO-83: PW B PROP [TO]
         { printf "[options]\nmode prove\nmulticlock off\n\n[engines]\nabc pdr\n\n[script]\nread_verilog -DFORMAL c9_cfg.v c9_core.v c9_dec.v c9_fsdiv.v c9_rdbus.v c9_seq.v tt_um_sd_adc_c9.v\nread_verilog -formal -DF_PW=$1 -DF_B=$2 c9_props.sv\nchparam -set PW_BITS $1 -set BIAS_BITS $2 sd_adc_c9 c9_seq\nprep -top c9_formal\n\n[files]\nc9_props.sv\n"; for v in "$HERE"/../rtl/*.v; do echo "$v"; done; } > "$F/p.sby"
         S=$(date +%s); (cd "$F" && timeout ${4:-5400} sby -f p.sby > sby.log 2>&1); echo "FMLW $1/$2 $3 $(grep -oE "DONE \((PASS|FAIL)" "$F/sby.log" || echo TIMEOUT_OR_ERR) $(($(date +%s)-S)) s";;
  merge) python3 "$HERE/fcov.py" merge "$R";;
  *)     echo "unknown job $K"; exit 2;;
esac
