#!/bin/bash
# WO-32 gate B: fs/125 nominal (TG clamp changed the netlist) and the near-knee copy srknee (0.8 x the boost floor).
# Pool of single-thread parts; the pool size is 5 minus the run.sh chains still running (own-process cap 5).
R=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); cd $R
pool(){ local r=0; for p in 1 2 3 4; do [ -f $R/out/DONE_$p ] || r=$((r+1)); done; echo $((5 - r)); }
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$R/design
printf 'set num_threads=1\n' > $R/.spiceinit
CFGS="3:nom 3:srknee"
ours(){ local n=0; for p in $(ps -eo pid=,comm= | awk '$2=="python"||$2=="python3"{print $1}'); do
  [ "$(readlink /proc/$p/cwd 2>/dev/null)" = "$R" ] && grep -qa c1b_gateb /proc/$p/cmdline 2>/dev/null && n=$((n+1)); done; echo $n; }
running(){ for p in $(ps -eo pid=,comm= | awk '$2=="python"||$2=="python3"{print $1}'); do
  [ "$(readlink /proc/$p/cwd 2>/dev/null)" = "$R" ] && tr '\0' ' ' < /proc/$p/cmdline; echo; done; }
echo "gb2 start $(date) pool $(pool)" >> $R/out/gb_status
for cf in $CFGS; do IFS=: read c cp <<< "$cf"; O=$R/out/gb/c${c}_$cp; mkdir -p $O; cp $R/.spiceinit $O/
  for i in 0 1 2 3 4 5; do
    if grep -q "INL ep" $O/part$i.out 2>/dev/null; then continue; fi
    if running | grep -q -- "$O --opt O1 .* --part $i/6"; then continue; fi
    while [ "$(ours)" -ge "$(pool)" ]; do sleep 30; done
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
