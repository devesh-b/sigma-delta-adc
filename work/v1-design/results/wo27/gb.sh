#!/bin/bash
# WO-27 item 6: gate B on the WO-27 netlist (D60 recentre + CM error amp), boost, N 1024, m 21, O1, 6 parts per config,
# waves of 3 (process cap). Configs: fs/125 (3), ss/-40 (1), ss/125 (2), tt/27 (0) nom + sr95 broken copy at fs/125 (3)
# and sf/-40 (8, lowest SR current, REVIEW-WO26 Q4). Combine per config. NOT launched by WO-27 (coordinator launches it
# after the WO-26 gate B finishes). Usage: bash gb.sh   (R = the frozen copy this file sits in)
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd $R
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
CFGS="3:nom 1:nom 2:nom 0:nom 3:sr95 8:sr95"
JOBS=()
for cf in $CFGS; do for i in 0 1 2 3 4 5; do JOBS+=("$cf:$i"); done; done
mkdir -p $R/out
echo "start $(date) ${#JOBS[@]} jobs" > $R/out/gb_status
n=0
for j in "${JOBS[@]}"; do
  IFS=: read c cp i <<< "$j"
  O=$R/out/gb/c${c}_$cp; mkdir -p $O
  nice -n 10 timeout 11000 python design/c1_ota1/c1b_gateb.py $O --opt O1 --n 1024 --m 21 --copy $cp --corner $c \
    --part $i/6 --deck-timeout 10800 > $O/part$i.out 2>&1 &
  n=$((n+1))
  if [ $((n % 3)) -eq 0 ]; then wait; echo "wave $((n/3)) done $(date)" >> $R/out/gb_status; fi
done
wait
for cf in $CFGS; do
  IFS=: read c cp <<< "$cf"; O=$R/out/gb/c${c}_$cp
  for i in 0 1 2 3 4 5; do echo "part$i: $(tail -2 $O/part$i.out | tr "\n" " ")"; done > $O/parts.summary
  nice -n 10 timeout 120 python design/c1_ota1/c1b_gateb.py $O --combine 6 --copy $cp > $O/combine.out 2>&1
  echo "EXIT=$?" >> $O/combine.out
  echo "c${c}_$cp $(tail -2 $O/combine.out | tr "\n" " ")" >> $R/out/gb_status
done
date > $R/GB_DONE
