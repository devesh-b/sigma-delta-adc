#!/usr/bin/env bash
# WO-40: per-property PDR on one mutant (run mut_job.sh make first or this makes it).  Prints "FML <mid> <prop> PASS|FAIL|ERR".
set -u
HERE=$(cd "$(dirname "$0")" && pwd); MID=$1
D=$HERE/../mut/$MID; mkdir -p "$D"
[ "$MID" = base ] || [ -d "$D/rtl" ] || python3 "$HERE/mutants.py" make "$MID" "$D" > /dev/null || exit 2
[ "$MID" = base ] && { rm -rf "$D/rtl"; cp -a "$HERE/../rtl" "$D/rtl"; }
for P in F01 F02 F03 F05 F06 F08 F09 F10 F16 F17; do
  F=$D/f_$P; rm -rf "$F"; mkdir -p "$F"
  awk -v p="// $P " '/cover *\(/ {next} /assert *\(/ && /\/\/ F[0-9]+ / && index($0, p) == 0 {next} {print}' \
      "$HERE/formal/c9_props.sv" > "$F/c9_props.sv"
  { printf '[options]\nmode prove\nmulticlock off\n\n[engines]\nabc pdr\n\n[script]\n'
    printf 'read_verilog -DFORMAL c9_cfg.v c9_core.v c9_dec.v c9_fsdiv.v c9_rdbus.v c9_seq.v tt_um_sd_adc_c9.v\n'
    printf 'read_verilog -formal c9_props.sv\nprep -top c9_formal\n\n[files]\nc9_props.sv\n'
    for v in "$D"/rtl/*.v; do echo "$v"; done; } > "$F/p.sby"
  (cd "$F" && timeout 1200 sby -f p.sby > sby.log 2>&1)
  if grep -q "DONE (PASS" "$F/sby.log"; then s=PASS; elif grep -q "DONE (FAIL" "$F/sby.log"; then s=FAIL; else s=ERR; fi
  echo "FML $MID $P $s"
done
