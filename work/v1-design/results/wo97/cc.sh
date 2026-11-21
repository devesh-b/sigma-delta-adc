#!/usr/bin/env bash
# compile-only smoke of the routed-GL source set (no sim): catches model/SDF syntax issues before the pool slot opens
B=/foss/designs/regr/WO-97-6b474df; R=$B/design/c9_digital/flow/runs/pnr1; V=/foss/pdks-tt/sky130A/libs.ref/sky130_fd_sc_hd/verilog
D=$B/cc; rm -rf $D; mkdir -p $D; printf '`define UNIT_DELAY\n' > $D/00_defines.v
sed "/^endmodule/i\\    initial \$sdf_annotate(\"$R/final/sdf/nom_tt_025C_1v80/sd_adc_c9__nom_tt_025C_1v80.sdf\", u_core);" $B/design/c9_digital/rtl/tt_um_sd_adc_c9.v > $D/tt_um.v
cd $D && timeout 900 iverilog -g2012 -gspecify -ginterconnect -o cc.vvp -s tt_um_sd_adc_c9 00_defines.v $V/primitives.v $V/sky130_fd_sc_hd.v $R/final/nl/sd_adc_c9.nl.v tt_um.v > cc.log 2>&1; echo "iverilog rc=$?"; grep -ci warning cc.log; grep -i error cc.log | head -5
timeout 300 vvp -n cc.vvp +dummy > run.log 2>&1 & sleep 60; kill %1 2>/dev/null; grep -iE "sdf|error" run.log | sort | uniq -c | sort -rn | head -8
