#!/usr/bin/env bash
# WO-40 (WO-83: optional args PW B, default 4 2; TESTS env passes through): yosys generic-cell netlist (synth -flatten, abc) + yosys simcells, quick suite on icarus. Own dir ../gl.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); PW=${1:-4}; BB=${2:-2}; D=$HERE/../gl; [ "$PW" = 4 ] || D=$HERE/../gl_${PW}_$BB; rm -rf "$D"; mkdir -p "$D/net"
yosys -q -p "read_verilog $HERE/../rtl/*.v; chparam -set PW_BITS $PW -set BIAS_BITS $BB sd_adc_c9; synth -top tt_um_sd_adc_c9 -flatten; opt_clean -purge; stat; write_verilog -noattr $D/net/tt_um_sd_adc_c9_gl.v" > "$D/yosys.log" 2>&1 || { echo "GL yosys FAIL"; tail "$D/yosys.log"; exit 2; }
cp "$(yosys-config --datdir)/simcells.v" "$D/net/"
grep -cE '^\s*\\\$_' "$D/net/tt_um_sd_adc_c9_gl.v" | sed 's/^/GL cell instances: /'
C9_TOP=tt_um_sd_adc_c9 C9_PW_BITS=$PW C9_BIAS_BITS=$BB C9_RTL=$D/net C9_OUT=$D/out C9_RUNDIR=$D timeout ${GL_TO:-7200} python3 "$HERE/run_cocotb.py" > "$D/cocotb.log" 2>&1
echo "GL rc=$? $(grep RESULT "$D/cocotb.log" | tail -1)"
