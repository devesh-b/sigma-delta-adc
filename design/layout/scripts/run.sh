#!/usr/bin/env bash
# WO-96/WO-100 layout run (inside IIC-OSIC-TOOLS): bash design/layout/scripts/run.sh <frozen run dir (container path)>
set -u
# PART=all (default), new (WO-107 cells C4/C3 only) or ota1 (WO-109 C1 OTA1 only), for iterations; final run = all
RUN=$1; PART=${2:-all}; L=$RUN/design/layout; O=$RUN/out; mkdir -p $O; cd $O
export LAYDIR=$L
RC=$PDKPATH/libs.tech/magic/sky130A.magicrc
M="magic -dnull -noconsole -rcfile $RC"
DECK=$PDKPATH/libs.tech/klayout/drc/sky130A_mr.drc
SETUP=$PDKPATH/libs.tech/netgen/sky130A_setup.tcl
S=$O/summary.txt; : > $S
# D98: C9 is the WO-106 175 x 150 macro
C9G=/foss/designs/regr/WO-106-9650241/design/c9_digital/flow/runs/pnr1/final/gds/sd_adc_c9.gds
if [ $PART = all ]; then
(cd $RUN && timeout 300 python3 design/layout/scripts/area_est.py) > area.txt 2>&1; cat area.txt >> $S
timeout 300 $M $L/frame/floorplan.tcl > fp.log 2>&1; grep "^FP" fp.log >> $S
C9GDS=$C9G timeout 600 $M $L/frame/c9_place.tcl > c9p.log 2>&1; grep "^FP" c9p.log >> $S
# WO-109: TT precheck project dirs for the frame + C9 (as scripts/s0_precheck.sh build()); precheck itself runs on the
# host (scripts/precheck_frame.sh <run dir>). proj_met5 = broken copy (one met5 rect).
for V in ok met5; do
  PJ=$O/precheck/proj_$V; rm -rf $PJ; mkdir -p $PJ/src $PJ/gds $PJ/lef
  printf '%s\n' '`default_nettype none' 'module tt_um_sd_adc_fp (' '    input  wire       VGND,' '    input  wire       VDPWR,' \
    '    input  wire       VAPWR,' '    input  wire [7:0] ui_in,' '    output wire [7:0] uo_out,' '    input  wire [7:0] uio_in,' \
    '    output wire [7:0] uio_out,' '    output wire [7:0] uio_oe,' '    inout  wire [7:0] ua,' '    input  wire       ena,' \
    '    input  wire       clk,' '    input  wire       rst_n' ');' "  assign uo_out  = 8'b0;" "  assign uio_out = 8'b0;" \
    "  assign uio_oe  = 8'b0;" 'endmodule' > $PJ/src/project.v
  cp $PJ/src/project.v $PJ/gds/tt_um_sd_adc_fp.v
  printf '%s\n' 'project:' '  title: "sd adc frame"' '  author: "x"' '  discord: ""' '  description: "WO-109 frame precheck"' \
    '  language: "Analog"' '  clock_hz: 0' '  tiles: "2x2"' '  analog_pins: 0' '  uses_vapwr: true' \
    '  top_module: "tt_um_sd_adc_fp"' '  source_files:' '    - "project.v"' 'pinout:' 'yaml_version: 6' > $PJ/info.yaml
  B=""; [ $V = met5 ] && B=met5
  PROJ=$PJ BROKEN=$B C9GDS=$C9G timeout 600 $M $L/frame/precheck_top.tcl > $O/precheck/build_$V.log 2>&1
  echo "PRECHECK_BUILD $V rc=$? gds=$(stat -c %s $PJ/gds/tt_um_sd_adc_fp.gds 2>/dev/null || echo MISSING) lef=$(stat -c %s $PJ/lef/tt_um_sd_adc_fp.lef 2>/dev/null || echo MISSING)" >> $S
done
fi
GEN="mim c6_res c4_sw c3_comp c1_ota1"; [ $PART = new ] && GEN="c4_sw c3_comp"; [ $PART = ota1 ] && GEN="c1_ota1"
for g in $GEN; do timeout 1800 $M $L/cells/$g.tcl > build_$g.log 2>&1; echo "BUILD $g rc=$? $(grep -c -i error build_$g.log) error-lines" >> $S; grep "^ARRAY\|^MAP1\|^C6 \|^R2"  build_$g.log >> $S; done
grep -o '\$[a-z_]*' $DECK | sort -u | tr '\n' ' ' > deckvars.txt
CELLS="tt_um_sd_adc_fp c9_place mim_u250 mim_s2 mim_s2_drcbad mim_s2_short mim_s1 mim_s1_drcbad mim_s1_short c6_res c6_res_drcbad c6_res_open"; [ $PART = all ] || CELLS=""
C34="c4_sw c4_sw_drcbad c4_sw_nostrap c3_comp c3_comp_drcbad c3_comp_swap"; C1="c1_ota1 c1_ota1_drcbad c1_ota1_swap"
[ $PART = ota1 ] && C34=""; [ $PART = new ] && C1=""
for c in $CELLS $C34 $C1; do
  CELL=$c timeout 900 $M $L/scripts/verify.tcl > ver_$c.log 2>&1
  grep "DRCWHY\|DRCCELL" ver_$c.log >> $S; echo "$(grep MAGICDRC ver_$c.log || echo "MAGICDRC $c MISSING")" >> $S
  if [ -f $c.gds ]; then
    timeout 900 klayout -b -r $DECK -rd input=$c.gds -rd topcell=$c -rd report=$c.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd floating_metal=false > kl_$c.log 2>&1
    echo "KLDRC $c items=$( [ -f $c.lyrdb ] && grep -c "<item>" $c.lyrdb || echo MISSING) $(grep -A1 "<item>" $c.lyrdb 2>/dev/null | grep -o "<category>[^<]*" | sort | uniq -c | tr "\n" " ")" >> $S
    klayout -b -r $L/scripts/bbox.py -rd gds=$c.gds 2>/dev/null | grep BBOX >> $S
  fi
done
# control: KLayout on the unmodified macro GDS (what c9_place must reproduce). WO-107: the report path must be
# absolute; the deck writes a relative report next to the input GDS (WO-100 wrote c9_orig.lyrdb into the WO-97 run dir).
if [ $PART = all ]; then
timeout 900 klayout -b -r $DECK -rd input=$C9G -rd topcell=sd_adc_c9 -rd report=$O/c9_orig.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd floating_metal=false > kl_c9_orig.log 2>&1
echo "KLDRC c9_orig(WO-106 GDS) items=$(grep -c "<item>" c9_orig.lyrdb) $(grep -o "<category>[^<]*" c9_orig.lyrdb | sort | uniq -c | tr "\n" " ")" >> $S
for c in c9_place c6_res mim_s1 mim_s2; do echo "KLCAT $c $(grep -o "<category>[^<]*" $c.lyrdb 2>/dev/null | sort | uniq -c | tr "\n" " ")" >> $S; done
fi
HVLSP=$PDKPATH/libs.ref/sky130_fd_sc_hvl/spice/sky130_fd_sc_hvl.spice
# WO-107 C4 reference: netlist.py SW sg (5/0.5) and the sin TG (12/36, L 0.5) wired as in the layout, plus the
# netlist.py default ls_up cell lsbuflv2hv_1 (D78; pins A LVPWR VGND VNB VPB VPWR X; VNB = substrate = vss).
{ echo "* WO-107 reference for c4_sw (design/c4_sw/netlist.py SW sizes, ls_up default cell)"
  echo ".include $HVLSP"; echo ".subckt c4_sw a b pas_t pas_c vg sg_t xs fs fsh vdd vdl vss"
  echo "XMsg vg sg_t xs vss sky130_fd_pr__nfet_g5v0d10v5 w=5 l=0.5"
  echo "XMsinn a pas_t b vss sky130_fd_pr__nfet_g5v0d10v5 w=12 l=0.5"
  echo "XMsinp a pas_c b vdd sky130_fd_pr__pfet_g5v0d10v5 w=36 l=0.5"
  echo "XLS fs vdl vss vss vdd vdd fsh sky130_fd_sc_hvl__lsbuflv2hv_1"; echo ".ends"; } > c4_sw_ref.spice
# WO-107 C3 reference: the netlist.py rev g output (golden) plus the two end dummies of the pair row (layout-only,
# all terminals vss). Bad ref: keeper W 0.84 -> 0.42 (rev f value).
(cd $RUN/design/c3_comp && timeout 120 python3 netlist.py) > c3_netlist_py.spice
sed '/^\.ends/i XDUM vss vss vss vss sky130_fd_pr__nfet_g5v0d10v5 W=5.0 L=0.5 nf=1 m=2' c3_netlist_py.spice > c3_comp_ref.spice
sed 's/^\(XKP[on] .*\)W=0.84/\1W=0.42/' c3_comp_ref.spice > c3_comp_ref_bad.spice
cp $L/cells/mim_s1_ref.spice $L/cells/mim_s2_ref.spice $L/cells/c6_res_ref.spice .
grep -v "^XB8" mim_s2_ref.spice > mim_s2_ref_bad.spice
grep -v "^XB16 " mim_s1_ref.spice > mim_s1_ref_bad.spice
sed 's/l=144.8$/l=159.3/' c6_res_ref.spice > c6_res_ref_bad.spice
sed 's/w=5 l=0.5/w=6 l=0.5/' c4_sw_ref.spice > c4_sw_ref_bad.spice
lvs() { timeout 900 netgen -batch lvs "$1.spice $1" "$2 $3" ${5:-$SETUP} lvs_$4.out > lvs_$4.log 2>&1
  # WO-100: netgen prints "Netlists match with N symmetries" when symmetries are resolved; the verdict is the
  # "Final result" line, plus no property errors and no mismatch line anywhere (incl. subcircuits).
  if grep -q "^Final result: Circuits match uniquely\.$" lvs_$4.out && ! grep -q "Property errors\|Netlists do not match\|Top level cell failed" lvs_$4.out; then v=PASS; else v=FAIL; fi
  echo "LVS $4 VERDICT=$v: $(grep -E 'Netlists match|Netlists do not match|Circuits match uniquely|Property errors|Top level cell failed' lvs_$4.out | sort | uniq -c | tr '\n' ';')" >> $S; }
if [ $PART = all ]; then
lvs mim_s2 mim_s2_ref.spice mim_s2 mim_s2
lvs mim_s2 mim_s2_ref_bad.spice mim_s2 mim_s2_vs_badref
lvs mim_s2_short mim_s2_ref.spice mim_s2 mim_s2_short
lvs mim_s1 mim_s1_ref.spice mim_s1 mim_s1
lvs mim_s1 mim_s1_ref_bad.spice mim_s1 mim_s1_vs_badref
lvs mim_s1_short mim_s1_ref.spice mim_s1 mim_s1_short
lvs c6_res c6_res_ref.spice c6_res c6_res
lvs c6_res c6_res_ref_bad.spice c6_res c6_res_vs_badref
lvs c6_res_open c6_res_ref.spice c6_res c6_res_open
fi
if [ $PART != ota1 ]; then
lvs c4_sw c4_sw_ref.spice c4_sw c4_sw $L/cells/c4_setup.tcl
lvs c4_sw c4_sw_ref_bad.spice c4_sw c4_sw_vs_badref $L/cells/c4_setup.tcl
lvs c4_sw_nostrap c4_sw_ref.spice c4_sw c4_sw_nostrap $L/cells/c4_setup.tcl
lvs c3_comp c3_comp_ref.spice c3_comp c3_comp
lvs c3_comp c3_comp_ref_bad.spice c3_comp c3_comp_vs_badref
lvs c3_comp_swap c3_comp_ref.spice c3_comp c3_comp_swap
echo "C3REF $(grep -c "^X" c3_comp_ref.spice) devices; bad ref diff: $(diff c3_comp_ref.spice c3_comp_ref_bad.spice | grep -c "^>")" >> $S
fi
grep -n -i "tolerance\|res_xhigh\|cap_mim" $SETUP | head -20 >> $O/netgen_setup_probe.txt
# WO-109 C1 OTA1 reference: the frozen WO-52 netlist.py default build (golden), caps mapped to the drawn
# cap_mim_m3_1 (c1 = top plate met4, c2 = bottom met3; sizes in cells/c1_ota1.tcl), plus the 2 input-pair end dummies
# (layout-only, nf 2 each, all terminals on tail). Bad ref: min1 W 10 -> 9.5.
if [ $PART != new ]; then
(cd $RUN/design/c1_ota1 && timeout 120 python3 netlist.py) > c1_netlist_py.spice
sed -e 's/^Ccp outp ctl 1e-13$/XCcp ctl outp sky130_fd_pr__cap_mim_m3_1 w=6.885 l=6.885/' \
    -e 's/^Ccn outn ctl 1e-13$/XCcn ctl outn sky130_fd_pr__cap_mim_m3_1 w=6.885 l=6.885/' \
    -e 's/^Crp rap rbp 5e-14$/XCrp rbp rap sky130_fd_pr__cap_mim_m3_1 w=4.815 l=4.815/' \
    -e 's/^Crn ran rbn 5e-14$/XCrn rbn ran sky130_fd_pr__cap_mim_m3_1 w=4.815 l=4.815/' \
    -e 's/^Cint bli vdd 2e-12$/XCint bli vdd sky130_fd_pr__cap_mim_m3_1 w=22.17 l=22.17 m=2/' \
    -e '/^\.ends/i XDUMP tail tail tail tail sky130_fd_pr__pfet_01v8 w=10 l=0.5 m=4' c1_netlist_py.spice > c1_ota1_ref.spice
sed 's/^\(Xmin1 .*\)w=10 /\1w=9.5 /' c1_ota1_ref.spice > c1_ota1_ref_bad.spice
lvs c1_ota1 c1_ota1_ref.spice ota1 c1_ota1
lvs c1_ota1 c1_ota1_ref_bad.spice ota1 c1_ota1_vs_badref
lvs c1_ota1_swap c1_ota1_ref.spice ota1 c1_ota1_swap
echo "C1REF $(grep -c "^X" c1_ota1_ref.spice) X-lines, $(grep -c "^C" c1_ota1_ref.spice) C-lines left; bad ref diff: $(diff c1_ota1_ref.spice c1_ota1_ref_bad.spice | grep -c "^>")" >> $S
grep -n "property\|delete\|ignore\|permute" $SETUP | head -40 > $O/netgen_setup_props.txt
fi
echo EXIT=0 >> $S
