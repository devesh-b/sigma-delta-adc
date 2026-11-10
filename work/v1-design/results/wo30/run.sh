#!/bin/bash
# WO-30 run: tb9 on the D63 basis (sampling-instant rows, CM-to-DM twin row, 0.486 V diff step, 8 T start-up clamp)
# + ripple diagnosis (ideal CMFB share switch on ctl). Usage (in the frozen copy R):
#   setsid nohup bash run.sh P >/dev/null 2>&1 &   with P = 1, 2 or 3 (one process chain each)
# Markers: out/status_P (EXIT= per step), out/DONE_P.
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); cd $R
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
D=$R/design/c1_ota1; O=$R/out; mkdir -p $O/tb9 $O/diag
P=$1
st() { echo "$1 EXIT=$2 $(date +%T)" >> $O/status_$P; }
if [ "$P" = 1 ]; then
  nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9 0,2 > $O/tb9/nom_02.out 2>&1; st tb9_nom_02 $?
elif [ "$P" = 2 ]; then
  nice -n 10 timeout 9000 python $D/c1b_tb9.py $O/tb9 3,4 > $O/tb9/nom_34.out 2>&1; st tb9_nom_34 $?
else
  nice -n 10 timeout 7000 python $D/c1b_tb9.py $O/tb9 0 --mut > $O/tb9/mut.out 2>&1; st tb9_mut $?
  TB9_TSTOP=3e-6 TB9_DIAG="a:-,b:sw_ideal_ctl,c:sw_ideal" nice -n 10 timeout 5000 python $D/c1b_tb9.py $O/diag 0,3 \
    > $O/diag/ripple.out 2>&1; st diag_ripple $?
fi
find $O -name "*.csv" -delete
date > $O/DONE_$P
