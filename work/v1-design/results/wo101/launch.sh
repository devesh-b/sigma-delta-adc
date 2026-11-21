#!/usr/bin/env bash
# WO-101: $1 = tag (pnrA die-only density 60 | pnr1 committed config)
B=/foss/designs/regr/WO-101-7646108
cd $B/design/c9_digital/flow
CFG=config.json
if [ "$1" = pnrA ]; then sed 's/"PL_TARGET_DENSITY_PCT": 75,/"PL_TARGET_DENSITY_PCT": 60,/' config.json > config_a.json; CFG=config_a.json; fi
librelane --manual-pdk --pdk-root /foss/pdks-tt --run-tag $1 $CFG > $B/$1.log 2>&1
echo "EXIT=$?" > $B/EXIT_$1
