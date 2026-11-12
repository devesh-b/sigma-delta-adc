#!/usr/bin/env bash
# WO-40: yosys generic-cell netlist (synth -flatten, abc) + yosys simcells, quick suite on icarus. Own dir ../gl.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); D=$HERE/../gl; rm -rf "$D"; mkdir -p "$D/net"
yosys -q -p "read_verilog $HERE/../rtl/*.v; synth -top tt_um_sd_adc_c9 -flatten; opt_clean -purge; stat; write_verilog -noattr $D/net/tt_um_sd_adc_c9_gl.v" > "$D/yosys.log" 2>&1 || { echo "GL yosys FAIL"; tail "$D/yosys.log"; exit 2; }
cp "$(yosys-config --datdir)/simcells.v" "$D/net/"
grep -cE '^\s*\\\$_' "$D/net/tt_um_sd_adc_c9_gl.v" | sed 's/^/GL cell instances: /'
C9_RTL=$D/net C9_OUT=$D/out C9_RUNDIR=$D timeout 7200 python3 "$HERE/run_cocotb.py" > "$D/cocotb.log" 2>&1
echo "GL rc=$? $(grep RESULT "$D/cocotb.log" | tail -1)"
