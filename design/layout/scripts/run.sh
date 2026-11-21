#!/usr/bin/env bash
# WO-96/WO-100 layout run (inside IIC-OSIC-TOOLS): bash design/layout/scripts/run.sh <frozen run dir (container path)>
set -u
RUN=$1; L=$RUN/design/layout; O=$RUN/out; mkdir -p $O; cd $O
export LAYDIR=$L
RC=$PDKPATH/libs.tech/magic/sky130A.magicrc
M="magic -dnull -noconsole -rcfile $RC"
DECK=$PDKPATH/libs.tech/klayout/drc/sky130A_mr.drc
SETUP=$PDKPATH/libs.tech/netgen/sky130A_setup.tcl
S=$O/summary.txt; : > $S
(cd $RUN && timeout 300 python3 design/layout/scripts/area_est.py) > area.txt 2>&1; cat area.txt >> $S
timeout 300 $M $L/frame/floorplan.tcl > fp.log 2>&1; grep "^FP" fp.log >> $S
C9GDS=/foss/designs/regr/WO-97-6b474df/design/c9_digital/flow/runs/pnr1/final/gds/sd_adc_c9.gds timeout 600 $M $L/frame/c9_place.tcl > c9p.log 2>&1; grep "^FP" c9p.log >> $S
for g in mim c6_res c4_sw; do timeout 900 $M $L/cells/$g.tcl > build_$g.log 2>&1; echo "BUILD $g rc=$? $(grep -c -i error build_$g.log) error-lines" >> $S; grep "^ARRAY\|^MAP1\|^C6 "  build_$g.log >> $S; done
grep -o '\$[a-z_]*' $DECK | sort -u | tr '\n' ' ' > deckvars.txt
for c in tt_um_sd_adc_fp c9_place mim_u250 mim_s2 mim_s2_drcbad mim_s2_short mim_s1 mim_s1_drcbad mim_s1_short c6_res c6_res_drcbad c6_res_open c4_sw c4_sw_drcbad; do
  CELL=$c timeout 900 $M $L/scripts/verify.tcl > ver_$c.log 2>&1
  grep DRCWHY ver_$c.log >> $S; echo "$(grep MAGICDRC ver_$c.log || echo "MAGICDRC $c MISSING")" >> $S
  if [ -f $c.gds ]; then
    timeout 900 klayout -b -r $DECK -rd input=$c.gds -rd topcell=$c -rd report=$c.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd floating_metal=false > kl_$c.log 2>&1
    echo "KLDRC $c items=$( [ -f $c.lyrdb ] && grep -c "<item>" $c.lyrdb || echo MISSING) $(grep -A1 "<item>" $c.lyrdb 2>/dev/null | grep -o "<category>[^<]*" | sort | uniq -c | tr "\n" " ")" >> $S
    klayout -b -r $L/scripts/bbox.py -rd gds=$c.gds 2>/dev/null | grep BBOX >> $S
  fi
done
HVLSP=$PDKPATH/libs.ref/sky130_fd_sc_hvl/spice/sky130_fd_sc_hvl.spice
PINS=$(grep -i "^.subckt sky130_fd_sc_hvl__lsbuflv2hv_clkiso_hlkg_3 " $HVLSP | cut -d' ' -f3- | tr 'A-Z' 'a-z' | sed 's/\bvnb\b/vsub/')
{ echo "* WO-96 reference for c4_sw: c4_sw/netlist.py SW sg (5/0.5) and sin (12/36, L 0.5) devices + one LS (unwired)"
  echo ".include $HVLSP"; echo ".subckt c4_sw"
  echo "XMsg d1 g1 s1 vsub sky130_fd_pr__nfet_g5v0d10v5 w=5 l=0.5"
  echo "XMsinn d2 g2 s2 vsub sky130_fd_pr__nfet_g5v0d10v5 w=12 l=0.5"
  echo "XMsinp d3 g3 s3 nw3 sky130_fd_pr__pfet_g5v0d10v5 w=36 l=0.5"
  echo "XLS $PINS sky130_fd_sc_hvl__lsbuflv2hv_clkiso_hlkg_3"; echo ".ends"; } > c4_sw_ref.spice
cp $L/cells/mim_s1_ref.spice $L/cells/mim_s2_ref.spice $L/cells/c6_res_ref.spice .
grep -v "^XB8" mim_s2_ref.spice > mim_s2_ref_bad.spice
grep -v "^XB16 " mim_s1_ref.spice > mim_s1_ref_bad.spice
sed 's/l=144.8$/l=159.3/' c6_res_ref.spice > c6_res_ref_bad.spice
sed 's/w=5 l=0.5/w=6 l=0.5/' c4_sw_ref.spice > c4_sw_ref_bad.spice
lvs() { timeout 900 netgen -batch lvs "$1.spice $1" "$2 $3" $SETUP lvs_$4.out > lvs_$4.log 2>&1
  # WO-100: netgen prints "Netlists match with N symmetries" when symmetries are resolved; the verdict is the
  # "Final result" line, plus no property errors and no mismatch line anywhere (incl. subcircuits).
  if grep -q "^Final result: Circuits match uniquely\.$" lvs_$4.out && ! grep -q "Property errors\|Netlists do not match\|Top level cell failed" lvs_$4.out; then v=PASS; else v=FAIL; fi
  echo "LVS $4 VERDICT=$v: $(grep -E 'Netlists match|Netlists do not match|Circuits match uniquely|Property errors|Top level cell failed' lvs_$4.out | sort | uniq -c | tr '\n' ';')" >> $S; }
lvs mim_s2 mim_s2_ref.spice mim_s2 mim_s2
lvs mim_s2 mim_s2_ref_bad.spice mim_s2 mim_s2_vs_badref
lvs mim_s2_short mim_s2_ref.spice mim_s2 mim_s2_short
lvs mim_s1 mim_s1_ref.spice mim_s1 mim_s1
lvs mim_s1 mim_s1_ref_bad.spice mim_s1 mim_s1_vs_badref
lvs mim_s1_short mim_s1_ref.spice mim_s1 mim_s1_short
lvs c6_res c6_res_ref.spice c6_res c6_res
lvs c6_res c6_res_ref_bad.spice c6_res c6_res_vs_badref
lvs c6_res_open c6_res_ref.spice c6_res c6_res_open
lvs c4_sw c4_sw_ref.spice c4_sw c4_sw
lvs c4_sw c4_sw_ref_bad.spice c4_sw c4_sw_vs_badref
grep -n -i "tolerance\|res_xhigh\|cap_mim" $SETUP | head -20 >> $O/netgen_setup_probe.txt
echo EXIT=0 >> $S
