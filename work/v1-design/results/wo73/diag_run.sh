# WO-73 item 1 driver (inside IIC-OSIC-TOOLS). Reads WO-72 run read-only; writes only to WO-73 dir.
P=/foss/designs/regr/WO-72/8898159/c9_digital/flow/runs/pnr1
D=/foss/designs/regr/WO-73/diag
export ODB=$P/final/odb/sd_adc_c9.odb SDC=/foss/designs/regr/WO-72/8898159/c9_digital/flow/c9.sdc
for m in placement grt spef; do
  export MODE=$m SPEF=$P/final/spef/max/sd_adc_c9.max.spef
  openroad -exit $D/diag_slew.tcl > $D/diag_$m.log 2>&1; echo "$m rc=$?"
done
export MODE=spef SPEF=$P/final/spef/nom/sd_adc_c9.nom.spef; openroad -exit $D/diag_slew.tcl > $D/diag_spefnom.log 2>&1; echo "spefnom rc=$?"
grep -h "WORST_SLEW\|err\|^--- \|max slew\|^Pin  *Limit" $D/diag_*.log; for f in $D/diag_*.log; do echo $f; grep -c VIOLATED $f; grep -A3 "^Pin  *Limit\|Slew  *Slack" $f | head -4; done
