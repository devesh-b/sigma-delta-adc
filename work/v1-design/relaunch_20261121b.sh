#!/bin/bash
# Relaunch after the 2026-11-21 20:05 sandbox reboot (second one). SKIPDONE=1; killed logs set aside.
set -u
R=/home/mempool/regr/tt
LP=/home/mempool/tt-sd/scripts/lpool.sh
log() { echo "$(date +%T) $*" >> $R/relaunch_20261121b.log; }
clean() { local dir=$1 f n=0
  for f in "$dir"/job_*.log; do [ -f "$f" ] || continue
    grep -q '^EXIT=' "$f" || { mv "$f" "$f.killed2"; n=$((n+1)); }; done
  rm -f "$dir/POOL_DONE"; log "clean $dir: $n killed"; }
launch() { local name=$1 prio=$2 cwd=$3; shift 3
  ( cd "$cwd" && PRIO=$prio SKIPDONE=1 setsid nohup "$@" > $R/relaunch2_$name.out 2>&1 < /dev/null & )
  log "launch $name prio=$prio :: $*"; }
ENV103='. /home/mempool/tt-sd/.venv-sbx/bin/activate; export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=/home/mempool/regr/tt/WO-103-c95c384;'
# high: fast checks
clean $R/WO-106-9650241/gl;        launch wo106gl high $R/WO-106-9650241 bash $LP $R/WO-106-9650241/gl_jobs.txt $R/WO-106-9650241/gl
clean $R/WO-98-c0bbaff/pool;       launch wo98 high $R/WO-98-c0bbaff bash $LP $R/WO-98-c0bbaff/jobs.txt $R/WO-98-c0bbaff/pool
clean $R/WO-105-b7cb88d/out/gates/pool; launch wo105g high $R/WO-105-b7cb88d bash $LP $R/WO-105-b7cb88d/out/gates/jobs.txt $R/WO-105-b7cb88d/out/gates/pool
clean $R/WO-104-b239f85/out/pool_logs;  launch wo104 high $R/WO-104-b239f85 bash $LP $R/WO-104-b239f85/out/jobs.txt $R/WO-104-b239f85/out/pool_logs
clean $R/WO-103-c95c384/run/pool;  launch wo103 high $R/WO-103-c95c384 bash -c "$ENV103 exec $LP $R/WO-103-c95c384/run/jobs.txt $R/WO-103-c95c384/run/pool"
# low: long top sims
clean $R/WO-105-b7cb88d/out/t1/pool;      launch wo105t1 low $R/WO-105-b7cb88d bash $LP $R/WO-105-b7cb88d/out/t1/jobs.txt $R/WO-105-b7cb88d/out/t1/pool
clean $R/WO-105-b7cb88d/out/corners/pool; launch wo105c low $R/WO-105-b7cb88d bash $LP $R/WO-105-b7cb88d/out/corners/jobs.txt $R/WO-105-b7cb88d/out/corners/pool
clean $R/WO-95-b4b44f4/out/smoke/pool;    launch wo95 low $R/WO-95-b4b44f4 bash $LP $R/WO-95-b4b44f4/jobs_smoke.txt $R/WO-95-b4b44f4/out/smoke/pool
