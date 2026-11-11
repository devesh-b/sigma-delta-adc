#!/bin/bash
# WO-32 run (D65): op/AC 9 PVT and tb9 (tt, ss125, fs125, sf125 + --mut, + --mm at tt and fs125). Usage (in the frozen copy R):
# setsid nohup bash run.sh P >/dev/null 2>&1 &  P = 1..4 (one process chain each). Markers: out/status_P (EXIT=), out/DONE_P.
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); cd $R
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
D=$R/design/c1_ota1; O=$R/out; mkdir -p $O/tb9 $O/opac
st() { echo "$1 EXIT=$2 $(date +%T)" >> $O/status_$P; }
P=$1
if [ "$P" = 1 ]; then
  nice -n 10 timeout 9000 python $D/c1b_opac.py $O/opac 1,2,3 > $O/opac/p123.out 2>&1; st opac_123 $?
  nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9 0,2 > $O/tb9/nom_02.out 2>&1; st tb9_02 $?
elif [ "$P" = 2 ]; then
  nice -n 10 timeout 9000 python $D/c1b_opac.py $O/opac 4,6,7 > $O/opac/p467.out 2>&1; st opac_467 $?
  nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9 3,4 > $O/tb9/nom_34.out 2>&1; st tb9_34 $?
elif [ "$P" = 3 ]; then
  nice -n 10 timeout 9000 python $D/c1b_opac.py $O/opac 0,5,8 > $O/opac/p058.out 2>&1; st opac_058 $?
  nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9 0 --mut > $O/tb9/mut.out 2>&1; st tb9_mut $?
else
  nice -n 10 timeout 12000 python $D/c1b_tb9.py $O/tb9 0,3 --mm > $O/tb9/mm_03.out 2>&1; st tb9_mm $?
fi
find $O -name "*.csv" -delete
date > $O/DONE_$P
