#!/bin/bash
# Coordinator 2026-11-11: re-scheduler for gate B (same jobs, same c1b_gateb.py args as gb.sh).
# Changes: ngspice single-threaded (./.spiceinit num_threads=1; spinit's 8 OpenMP threads per job oversubscribed 6 cores)
# and a pool of POOL concurrent parts instead of fixed waves of 3. Skips parts already finished or still running.
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); cd $R
POOL=${POOL:-5}
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
printf 'set num_threads=1\n' > $R/.spiceinit
CFGS="3:nom 1:nom 2:nom 0:nom 3:sr95 8:sr95"
ours(){ local n=0; for p in $(ps -eo pid=,comm= | awk '$2=="python"||$2=="python3"{print $1}'); do
  [ "$(readlink /proc/$p/cwd 2>/dev/null)" = "$R" ] && grep -qa c1b_gateb /proc/$p/cmdline 2>/dev/null && n=$((n+1)); done; echo $n; }
running(){ for p in $(ps -eo pid=,comm= | awk '$2=="python"||$2=="python3"{print $1}'); do
  [ "$(readlink /proc/$p/cwd 2>/dev/null)" = "$R" ] && tr '\0' ' ' < /proc/$p/cmdline; echo; done; }
echo "gb2 start $(date) POOL=$POOL" >> $R/out/gb_status
for cf in $CFGS; do IFS=: read c cp <<< "$cf"; O=$R/out/gb/c${c}_$cp; mkdir -p $O
  for i in 0 1 2 3 4 5; do
    if grep -q "INL ep" $O/part$i.out 2>/dev/null; then continue; fi
    if running | grep -q -- "$O --opt O1 .* --part $i/6"; then continue; fi
    while [ "$(ours)" -ge "$POOL" ]; do sleep 30; done
    nice -n 10 timeout 11000 python design/c1_ota1/c1b_gateb.py $O --opt O1 --n 1024 --m 21 --copy $cp --corner $c \
      --part $i/6 --deck-timeout 10800 > $O/part$i.out 2>&1 &
    echo "launch c${c}_$cp p$i $(date +%T)" >> $R/out/gb_status
    sleep 5
  done; done
while [ "$(ours)" -gt 0 ]; do sleep 60; done
for cf in $CFGS; do IFS=: read c cp <<< "$cf"; O=$R/out/gb/c${c}_$cp
  for i in 0 1 2 3 4 5; do echo "part$i: $(tail -2 $O/part$i.out | tr "\n" " ")"; done > $O/parts.summary
  nice -n 10 timeout 120 python design/c1_ota1/c1b_gateb.py $O --combine 6 --copy $cp > $O/combine.out 2>&1
  echo "EXIT=$?" >> $O/combine.out
  echo "c${c}_$cp $(tail -2 $O/combine.out | tr "\n" " ")" >> $R/out/gb_status
done
date > $R/GB_DONE
