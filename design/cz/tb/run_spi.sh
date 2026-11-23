#!/bin/bash
# cz_spi bench (D102). SANDBOX ONLY (IIC-OSIC-TOOLS container via scripts/iic). Written 2026-11-24, NOT YET RUN.
# Usage: ./run_spi.sh [rtl_path]          env: SEEDS="1 2 3 4 5"  TO=900 (s per sim)  IVERILOG/VVP
# Expected: lint informational; real_rtl seeds = ACCEPT; real_strict = REJECT (open ambiguity SA-SPI-1, informational);
#           every mutants_spi/M*.sed = REJECT. Exit 0 only if all real seeds ACCEPT and all mutants REJECT.
cd "$(dirname "$0")" || exit 2
RTL=${1:-../rtl/cz_spi.v}
SEEDS=${SEEDS:-"1 2 3 4 5"}
TO=${TO:-900}
C9=../../c9_digital/rtl
C9F="$C9/c9_core.v $C9/c9_rdbus.v $C9/c9_dec.v $C9/c9_seq.v $C9/c9_cfg.v $C9/c9_fsdiv.v"
IV=${IVERILOG:-iverilog}; VVP=${VVP:-vvp}
W=${TMPDIR:-/tmp}/czspi_$$; mkdir -p "$W"
G=mutants_spi/gen; mkdir -p "$G"
fail=0

# run NAME RTLFILE SEED [PLUSARGS...]  -> prints ACCEPT / REJECT, returns 0 on ACCEPT
run() {
  local n=$1 f=$2 sd=$3; shift 3
  if [ ! -f "$f" ]; then echo "$n: NO-FILE"; return 2; fi
  if ! $IV -g2012 -o "$W/$n.vvp" tb_cz_spi.v "$f" ../rtl/cz_bus8.v $C9F 2>"$W/$n.err"; then
    echo "$n: REJECT (compile error: $(head -1 "$W/$n.err"))"; return 1; fi
  timeout "$TO" $VVP -n "$W/$n.vvp" +seed="$sd" "$@" > "$W/$n.log" 2>&1
  local st=$(grep -m1 CHECKS "$W/$n.log"); local e1=$(grep -m1 '^ERR' "$W/$n.log")
  if grep -q TB_PASS "$W/$n.log"; then echo "$n: ACCEPT ($st)"; return 0
  else echo "$n: REJECT ($st) ${e1:-no TB_PASS (timeout or crash)}"; return 1; fi
}

echo "== lint (informational)"
if command -v verilator >/dev/null; then
  verilator --lint-only -Wall "$RTL" --top-module cz_spi 2>&1 | grep -E '%(Warning|Error)' | head -20
  echo "lint done"
else echo "verilator not found"; fi

echo "== real RTL"
for s in $SEEDS; do
  run "real_s$s" "$RTL" "$s" || fail=1
  [ "$s" = "$(echo $SEEDS | cut -d' ' -f1)" ] && grep '^STAT' "$W/real_s$s.log"
done
echo "== real RTL with +STRICT_ONE_ACK (informational: REJECT expected while SA-SPI-1 is open)"
run real_strict "$RTL" 1 +STRICT_ONE_ACK

echo "== mutants (each must REJECT)"
nm=0; nk=0
for m in mutants_spi/M*.sed; do
  n=$(basename "$m" .sed); nm=$((nm+1))
  sed -f "$m" "$RTL" > "$G/$n.v"
  if cmp -s "$RTL" "$G/$n.v"; then echo "$n: MUTATION-NOT-APPLIED"; fail=1; continue; fi
  if run "$n" "$G/$n.v" 1 +STOP_ON_ERR; then echo "   ^ SURVIVOR"; fail=1; else nk=$((nk+1)); fi
done
echo "== mutation kill rate: $nk/$nm"
rm -rf "$W"
[ $fail -eq 0 ] && echo "RUN_SPI: OK" || echo "RUN_SPI: FAIL"
exit $fail
