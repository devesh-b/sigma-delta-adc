#!/usr/bin/env bash
# WO-94: generate schematics from the Python generators, netlist them with xschem, LVS (netgen) against the
# generator netlists, and run one broken copy (one size changed) per cell that must MISMATCH.
# Run inside IIC-OSIC-TOOLS from the tree root:  scripts/iic "bash design/xschem/run_wo94.sh OUT"
set -uo pipefail
X=$(cd "$(dirname "$0")" && pwd); OUT=${1:-$X/out}; mkdir -p "$OUT"
SETUP=$PDK_ROOT/$PDK/libs.tech/netgen/sky130A_setup.tcl
python3 "$X/gen/refnets.py" "$OUT/ref" || exit 1
python3 "$X/gen/sch_gen.py" "$OUT/ref/sd_mod_top.spice" "$X/sch" || exit 1
CELLS="ota1 ota2 c3_comp c4_gen c6_bias mim_cs mim_cint1 mim_cint2 mim_ck2 sd_mod_top"
declare -A BRK=([ota1]=mtr:W=4 [ota2]=mtr:W=4 [c3_comp]=M1:W=4.5 [c4_gen]=mdp:W=0.5 [c6_bias]=m1:mult=16
  [mim_cs]=c:MF=3 [mim_cint1]=c:MF=15 [mim_cint2]=c:MF=5 [mim_ck2]=c:W=12 [sd_mod_top]=sinpn:W=11)
verdict() { grep -q "Final result: Circuits match uniquely\.$" "$1" && ! grep -q "Property errors were found" "$1" && echo MATCH || echo MISMATCH; }
lvs() {  # sch_dir cell tag
  local d=$OUT/$3; mkdir -p "$d"
  WO94_SCH=$1 xschem -q -x -r -n -s --rcfile "$X/xschemrc" -o "$d" -N "$2.spice" "$1/$2.sch" > "$d/$2.xschem.log" 2>&1
  [ -s "$d/$2.spice" ] || { echo "NOXSCHEM"; return; }
  netgen -batch lvs "$d/$2.spice $2" "$OUT/ref/$2.spice $2" "$SETUP" "$d/$2.lvs" > "$d/$2.netgen.log" 2>&1
  [ -s "$d/$2.lvs" ] && verdict "$d/$2.lvs" || echo NOLVS
}
printf "%-11s %-6s %-9s %-22s %-9s %s\n" cell elems good broken_copy broken result > "$OUT/summary.txt"
for c in $CELLS; do
  g=$(lvs "$X/sch" "$c" good)
  python3 "$X/gen/sch_gen.py" "$OUT/ref/sd_mod_top.spice" "$OUT/sch_brk_$c" --break "$c/${BRK[$c]}" > "$OUT/brk_$c.log" 2>&1
  b=$(lvs "$OUT/sch_brk_$c" "$c" "brk_$c")
  n=$(awk -v c="$c" '$1==".subckt"{f=($2==c)} f&&/^[XRC]/{k++} END{print k+0}' "$OUT/ref/sd_mod_top.spice")
  r=REJECT; [ "$g" = MATCH ] && [ "$b" = MISMATCH ] && r=ACCEPT
  printf "%-11s %-6s %-9s %-22s %-9s %s\n" "$c" "$n" "$g" "${BRK[$c]}" "$b" "$r" >> "$OUT/summary.txt"
done
cp "$OUT/good/sd_mod_top.spice" "$X/sd_mod_top.spice"
cat "$OUT/summary.txt"; ! grep -q REJECT "$OUT/summary.txt"
