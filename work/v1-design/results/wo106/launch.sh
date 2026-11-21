#!/usr/bin/env bash
# WO-106: die 175x150 trial (commit 9650241), committed config unchanged otherwise
B=/foss/designs/regr/WO-106-9650241
cd $B/design/c9_digital/flow
librelane --manual-pdk --pdk-root /foss/pdks-tt --run-tag pnr1 config.json > $B/pnr1.log 2>&1
echo "EXIT=$?" > $B/EXIT_pnr1
