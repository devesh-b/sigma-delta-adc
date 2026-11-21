#!/usr/bin/env bash
# WO-96/WO-100 layout run (inside IIC-OSIC-TOOLS): bash design/layout/scripts/run.sh <frozen run dir (container path)>
set -u
# PART=all (default) or new (WO-107 cells C4/C3 only, for iterations; the final run is PART=all)
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
fi
GEN="mim c6_res c4_sw c3_comp"; [ $PART = all ] || GEN="c4_sw c3_comp"
for g in $GEN; do timeout 900 $M $L/cells/$g.tcl > build_$g.log 2>&1; echo "BUILD $g rc=$? $(grep -c -i error build_$g.log) error-lines" >> $S; grep "^ARRAY\|^MAP1\|^C6 "  build_$g.log >> $S; done
grep -o '\$[a-z_]*' $DECK | sort -u | tr '\n' ' ' > deckvars.txt
CELLS="tt_um_sd_adc_fp c9_place mim_u250 mim_s2 mim_s2_drcbad mim_s2_short mim_s1 mim_s1_drcbad mim_s1_short c6_res c6_res_drcbad c6_res_open"; [ $PART = all ] || CELLS=""
for c in $CELLS c4_sw c4_sw_drcbad c4_sw_nostrap c3_comp c3_comp_drcbad c3_comp_swap; do
  CELL=$c timeout 900 $M $L/scripts/verify.tcl > ver_$c.log 2>&1
  grep DRCWHY ver_$c.log >> $S; echo "$(grep MAGICDRC ver_$c.log || echo "MAGICDRC $c MISSING")" >> $S
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
lvs() { timeout 900 netgen -batch lvs "$1.spice $1" "$2 $3" $SETUP lvs_$4.out > lvs_$4.log 2>&1
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
lvs c4_sw c4_sw_ref.spice c4_sw c4_sw
lvs c4_sw c4_sw_ref_bad.spice c4_sw c4_sw_vs_badref
lvs c4_sw_nostrap c4_sw_ref.spice c4_sw c4_sw_nostrap
lvs c3_comp c3_comp_ref.spice c3_comp c3_comp
lvs c3_comp c3_comp_ref_bad.spice c3_comp c3_comp_vs_badref
lvs c3_comp_swap c3_comp_ref.spice c3_comp c3_comp_swap
echo "C3REF $(grep -c "^X" c3_comp_ref.spice) devices; bad ref diff: $(diff c3_comp_ref.spice c3_comp_ref_bad.spice | grep -c "^>")" >> $S
grep -n -i "tolerance\|res_xhigh\|cap_mim" $SETUP | head -20 >> $O/netgen_setup_probe.txt
echo EXIT=0 >> $S
