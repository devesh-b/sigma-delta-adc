#!/bin/bash
# lpool.sh - load-adaptive job pool for sandbox runs (user request 2026-11-12: parallelise by server load).
#
# Usage:  lpool.sh JOBFILE [LOGDIR]
#   JOBFILE: one shell command per line (blank lines and lines starting with # are skipped).
#   Each job runs as `nice -n 10 bash -c "<line>"`, its output in LOGDIR/job_<n>.log, with an
#   `EXIT=<code>` line appended. When all jobs end, LOGDIR/POOL_DONE is written.
#
# Concurrency is re-evaluated before every launch:
#   free  = NPROC - load1 (the 1-min load average, which includes our own running jobs)
#   slots = ours_running + floor(free - MARGIN), clamped to [1, MAXJOBS]
# So when other users load the box we run fewer jobs, and when it is idle we use every core.
# Knobs (env): MAXJOBS (default nproc), MARGIN (default 0.5 core kept free), POLL (default 20 s).
# Every job is single-threaded: OMP_NUM_THREADS=1, plus a .spiceinit with `set num_threads=1`
# in the job's working directory (the caller's cwd). ngspice otherwise starts 8 OpenMP threads
# per job and oversubscribes the 6 cores.
# Notes: our jobs are counted from this script's own children (no pgrep, so no self-match).
# load1 lags by about a minute, which is why there is a short settle sleep after each launch.

JOBFILE=${1:?usage: lpool.sh JOBFILE [LOGDIR]}
LOGDIR=${2:-$(dirname "$JOBFILE")/pool_logs}
NPROC=$(nproc)
MAXJOBS=${MAXJOBS:-$NPROC}
MARGIN=${MARGIN:-0.5}
POLL=${POLL:-20}
mkdir -p "$LOGDIR"
export OMP_NUM_THREADS=1
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit

mapfile -t JOBS < <(grep -v '^[[:space:]]*\(#\|$\)' "$JOBFILE")
echo "lpool start $(date +%T) jobs=${#JOBS[@]} nproc=$NPROC max=$MAXJOBS" >> "$LOGDIR/pool.status"

running() { jobs -rp | wc -l; }
slots() {
  local load1 free s
  load1=$(cut -d' ' -f1 /proc/loadavg)
  free=$(awk -v n="$NPROC" -v l="$load1" -v m="$MARGIN" 'BEGIN{f=n-l-m; print (f<0)?0:int(f)}')
  s=$(( $(running) + free ))
  [ "$s" -lt 1 ] && s=1
  [ "$s" -gt "$MAXJOBS" ] && s=$MAXJOBS
  echo "$s"
}

i=0
for j in "${JOBS[@]}"; do
  i=$((i+1))
  while [ "$(running)" -ge "$(slots)" ]; do sleep "$POLL"; done
  ( nice -n 10 bash -c "$j" > "$LOGDIR/job_$i.log" 2>&1; echo "EXIT=$?" >> "$LOGDIR/job_$i.log" ) &
  echo "launch $i $(date +%T) running=$(running) load=$(cut -d' ' -f1 /proc/loadavg) :: $j" >> "$LOGDIR/pool.status"
  sleep 5
done
wait
echo "lpool done $(date +%T)" >> "$LOGDIR/pool.status"
date > "$LOGDIR/POOL_DONE"
