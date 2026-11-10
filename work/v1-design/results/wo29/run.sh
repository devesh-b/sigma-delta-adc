#!/bin/bash
# WO-29 run: tb9 (fixed Cint polarity) + diagnosis evidence, combine() rule check, op/AC 9 PVT with the pair-per-deck split.
# Usage (in the frozen copy R): setsid nohup bash run.sh P >/dev/null 2>&1 &   with P = 1, 2 or 3 (one process chain each)
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); cd $R
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
D=$R/design/c1_ota1; O=$R/out; mkdir -p $O/tb9 $O/diag2 $O/opac $O/opac_brk $O/comb
st() { echo "$1 EXIT=$2 $(date +%T)" >> $O/status_$P; }
P=$1
if [ "$P" = 1 ]; then
  TB9_VEC=1 nice -n 10 timeout 5000 python $D/c1b_tb9.py $O/tb9 0,2,3,4 > $O/tb9/nom.out 2>&1; st tb9_nom $?
  nice -n 10 timeout 9000 python $D/c1b_opac.py $O/opac 1,2,3 > $O/opac/p123.out 2>&1; st opac_123 $?
elif [ "$P" = 2 ]; then
  TB9_VEC=1 nice -n 10 timeout 3000 python $D/c1b_tb9.py $O/tb9 0 --mut > $O/tb9/mut.out 2>&1; st tb9_mut $?
  TB9_POL_OLD=1 TB9_DIAG="ev:-" nice -n 10 timeout 3000 python $D/c1b_tb9.py $O/diag2/old 0 > $O/diag2/old.out 2>&1; st diag_old $?
  TB9_TSTOP=8e-6 TB9_DIAG="ev:-,evd:dcavg" nice -n 10 timeout 3000 python $D/c1b_tb9.py $O/diag2/new 0 > $O/diag2/new.out 2>&1; st diag_new $?
  nice -n 10 timeout 9000 python $D/c1b_opac.py $O/opac 4,6,7 > $O/opac/p467.out 2>&1; st opac_467 $?
else
  nice -n 10 timeout 300 python $R/design/tests/wo29_combine_check.py /home/mempool/regr/tt/WO-26-b177d23/out/gb/c3_sr95 $O/comb \
    > $O/comb/check.out 2>&1; st combine $?
  nice -n 10 timeout 9000 python $D/c1b_opac.py $O/opac 0,5,8 > $O/opac/p058.out 2>&1; st opac_058 $?
  nice -n 10 timeout 3000 python $D/c1b_opac.py $O/opac_brk 5 --split-run2 > $O/opac_brk/p5.out 2>&1; st opac_brk_split_run2 $?
fi
find $O -name "*.csv" -delete
date > $O/DONE_$P
