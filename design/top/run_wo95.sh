#!/bin/bash
# WO-95 orchestrator (sandbox). Waits for the smoke pool, and only if the smoke deck is healthy launches the
# precision-mode gate pool (PRIO=high) and then the corner pool (PRIO=low). Detached; writes markers only.
#   setsid nohup bash design/top/run_wo95.sh /home/mempool/regr/tt/WO-95-<sha> > /dev/null 2>&1 < /dev/null &
# Markers: $F/out/SMOKE_OK | SMOKE_FAIL, $F/out/gates/pool/POOL_DONE, $F/out/corners/pool/POOL_DONE
F=${1:?frozen dir}
. "$F/env.sh"
B="python3 $F/design/top/top_bench.py"
while [ ! -f "$F/out/smoke/pool/POOL_DONE" ]; do sleep 60; done
if grep -q '"healthy": true' "$F"/out/smoke/gsmoke_*.json 2>/dev/null; then touch "$F/out/SMOKE_OK"; else touch "$F/out/SMOKE_FAIL"; exit 1; fi
mk() {   # mk DIR GATE ARGS...  -> one job line
  local d=$1; shift
  echo "mkdir -p $F/out/$d && cd $F/out/$d && cp $F/.spiceinit . && . $F/env.sh && $B $F/out/$d $* > run.txt 2>&1"
}
G=$F/out/gates; mkdir -p "$G"
{
  mk a_nom a
  mk a_nosu a --copy nosu
  mk bc_nom_tt bc --m 7
  mk bc_nom_ss bc --m 7 --corner ss --temp -40 --vdd 3.0
  mk bc_dacswap bc --m 3 --copy dacswap
  mk bc_ota2dead bc --m 3 --copy ota2dead
  mk d_nom d
  mk d_noswap d --copy noswap
  mk e_nom e
  mk e_noreset e --copy noreset
} > "$G/jobs.txt"
cd "$G" && PRIO=high SKIPDONE=1 bash "$F/scripts/lpool.sh" "$G/jobs.txt" "$G/pool" > "$G/pool.out" 2>&1 &
C=$F/out/corners; mkdir -p "$C"
{
  mk a_ss a --corner ss --temp -40 --vdd 3.0
  mk d_ss d --corner ss --temp -40 --vdd 3.0
  mk e_ss e --corner ss --temp -40 --vdd 3.0
} > "$C/jobs.txt"
cd "$C" && PRIO=low SKIPDONE=1 bash "$F/scripts/lpool.sh" "$C/jobs.txt" "$C/pool" > "$C/pool.out" 2>&1 &
wait
