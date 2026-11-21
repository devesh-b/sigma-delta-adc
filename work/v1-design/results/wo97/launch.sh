#!/usr/bin/env bash
cd /foss/designs/regr/WO-97-6b474df/design/c9_digital/flow
librelane --manual-pdk --pdk-root /foss/pdks-tt --run-tag pnr1 config.json > /foss/designs/regr/WO-97-6b474df/pnr1.log 2>&1
echo "EXIT=$?" > /foss/designs/regr/WO-97-6b474df/EXIT
