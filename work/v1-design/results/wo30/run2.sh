#!/bin/bash
# WO-30 run 2: masy broken copy moved to the island (run 1: blind on the output side), and the Cr x 2 candidate
# (TB9_SET=cr2: ev, suhi, sulo, suvb with Cr x 2, 2 T clamp) as evidence for the start-up option. Usage as run.sh.
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); cd $R
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
D=$R/design/c1_ota1; O=$R/out; mkdir -p $O/tb9 $O/tb9cr2
P=$1
st() { echo "$1 EXIT=$2 $(date +%T)" >> $O/status2_$P; }
if [ "$P" = 1 ]; then
  TB9_SET=cr2 nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9cr2 0,2 > $O/tb9cr2/nom_02.out 2>&1; st cr2_02 $?
elif [ "$P" = 2 ]; then
  TB9_SET=cr2 nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9cr2 3,4 > $O/tb9cr2/nom_34.out 2>&1; st cr2_34 $?
else
  nice -n 10 timeout 7000 python $D/c1b_tb9.py $O/tb9 0 --mut > $O/tb9/mut2.out 2>&1; st tb9_mut2 $?
fi
find $O -name "*.csv" -delete
date > $O/DONE2_$P
