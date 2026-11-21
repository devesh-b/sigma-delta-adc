#!/usr/bin/env bash
# WO-97: C9 bench on the ROUTED netlist (LibreLane final/nl) with sky130_fd_sc_hd timing models (specify) and optional SDF.
# Usage (inside IIC, from the frozen tree's design/c9_digital/tb): gl_routed.sh RUNDIR TAG SDF|none ; TESTS env selects tests.
# The routed netlist has the RTL default widths (PW_BITS 16, BIAS_BITS 8) baked in, so the bench runs at 16/8.
# Icarus applies SDF IOPATH/INTERCONNECT delays but does not evaluate $setuphold timing checks: this proves function
# with back-annotated delays, not timing (timing = STA).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); RUN=$1; TAG=$2; SDF=$3
V=/foss/pdks-tt/sky130A/libs.ref/sky130_fd_sc_hd/verilog
D=$HERE/../gl_routed_$TAG; rm -rf "$D"; mkdir -p "$D/net"
printf '`define UNIT_DELAY\n' > "$D/net/00_defines.v"
cp "$V/primitives.v" "$D/net/01_primitives.v"; cp "$V/sky130_fd_sc_hd.v" "$D/net/02_sky130_fd_sc_hd.v"
cp "$RUN/final/nl/sd_adc_c9.nl.v" "$D/net/" || { echo "no routed netlist"; exit 2; }
if [ "$SDF" = none ]; then cp "$HERE/../rtl/tt_um_sd_adc_c9.v" "$D/net/"
else sed "/^endmodule/i\\    initial \$sdf_annotate(\"$SDF\", u_core, , \"$D/sdf_annotate.log\");" "$HERE/../rtl/tt_um_sd_adc_c9.v" > "$D/net/tt_um_sd_adc_c9.v"; fi
grep -c "sky130_fd_sc_hd__" "$D/net/sd_adc_c9.nl.v" | sed 's/^/routed cell refs: /'
C9_TOP=tt_um_sd_adc_c9 C9_PW_BITS=16 C9_BIAS_BITS=8 C9_BUILD_ARGS="-gspecify -ginterconnect" C9_RTL=$D/net C9_OUT=$D/out C9_RUNDIR=$D \
  timeout ${GL_TO:-86400} python3 "$HERE/run_cocotb.py" > "$D/cocotb.log" 2>&1
echo "GLR $TAG rc=$? $(grep RESULT "$D/cocotb.log" | tail -1)"
