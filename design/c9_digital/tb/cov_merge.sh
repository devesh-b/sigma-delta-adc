#!/usr/bin/env bash
# WO-40: merge Verilator coverage of ../cov/s*/ and annotate the RTL (lines with %000000 = never hit).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); D=$HERE/../cov
dats=$(find "$D" -name '*.dat' | sort); [ -n "$dats" ] || { echo "COV no .dat"; exit 2; }
verilator_coverage --write "$D/merged.dat" $dats > "$D/merge.log" 2>&1
rm -rf "$D/annot"; verilator_coverage --annotate "$D/annot" --annotate-min 1 "$D/merged.dat" 2>&1 | tail -3
for t in line toggle branch; do echo "COV $t: $(verilator_coverage --filter-type $t --annotate /tmp/a_$t --annotate-min 1 "$D/merged.dat" 2>&1 | grep -i 'total' | tail -1)"; done
echo "== un-hit points (file:line text)"
grep -nH '%000000' "$D"/annot/*.v | sed 's/  */ /g' | cut -c1-150
