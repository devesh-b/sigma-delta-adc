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
#
# Global cap (user decision 2026-11-14): every lpool instance shares GMAX slots (default 5),
# held as flock locks on files in SLOTDIR (default /home/mempool/regr/tt/.lpool_slots). The
# main shell takes a free slot lock, the job subshell inherits the descriptor, and the parent
# closes its copy, so the lock is released only when the job (and its children) exit. Several
# pools running at once therefore never exceed GMAX jobs in total. The per-pool load rule
# still applies on top of the cap.

JOBFILE=${1:?usage: lpool.sh JOBFILE [LOGDIR]}
LOGDIR=${2:-$(dirname "$JOBFILE")/pool_logs}
NPROC=$(env -u OMP_NUM_THREADS nproc)   # GNU nproc honours OMP_NUM_THREADS; ignore it here
MAXJOBS=${MAXJOBS:-$NPROC}
MARGIN=${MARGIN:-0.5}
POLL=${POLL:-20}
GMAX=${GMAX:-5}
SLOTDIR=${SLOTDIR:-/home/mempool/regr/tt/.lpool_slots}
mkdir -p "$LOGDIR" "$SLOTDIR"
export OMP_NUM_THREADS=1
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit

mapfile -t JOBS < <(grep -v '^[[:space:]]*\(#\|$\)' "$JOBFILE")
echo "lpool start $(date +%T) jobs=${#JOBS[@]} nproc=$NPROC max=$MAXJOBS" >> "$LOGDIR/pool.status"

# Our running jobs are tracked as an explicit PID list checked with kill -0, in the main shell.
# (The old `jobs -rp` inside $(...) ran in a subshell and miscounted, so the pool over-launched;
# found 2026-11-13.)
PIDS=()
NRUN=0
count_running() {
  local alive=() p
  for p in "${PIDS[@]}"; do kill -0 "$p" 2>/dev/null && alive+=("$p"); done
  PIDS=("${alive[@]}")
  NRUN=${#PIDS[@]}
}
NSLOT=1
compute_slots() {
  local load1 free
  load1=$(cut -d' ' -f1 /proc/loadavg)
  free=$(awk -v n="$NPROC" -v l="$load1" -v m="$MARGIN" 'BEGIN{f=n-l-m; print (f<0)?0:int(f)}')
  NSLOT=$(( NRUN + free ))
  [ "$NSLOT" -lt 1 ] && NSLOT=1
  [ "$NSLOT" -gt "$MAXJOBS" ] && NSLOT=$MAXJOBS
}

SLOTFD=
GSLOT=
acquire_gslot() {   # take one free global slot lock; return 1 if all GMAX are held
  local s fd
  for ((s=0; s<GMAX; s++)); do
    exec {fd}>"$SLOTDIR/slot$s"
    if flock -n "$fd"; then SLOTFD=$fd; GSLOT=$s; return 0; fi
    exec {fd}>&-
  done
  return 1
}

i=0
for j in "${JOBS[@]}"; do
  i=$((i+1))
  while :; do
    count_running; compute_slots
    if [ "$NRUN" -lt "$NSLOT" ] && acquire_gslot; then break; fi
    sleep "$POLL"
  done
  ( nice -n 10 bash -c "$j" > "$LOGDIR/job_$i.log" 2>&1; echo "EXIT=$?" >> "$LOGDIR/job_$i.log" ) &
  PIDS+=("$!")
  exec {SLOTFD}>&-   # the job keeps the inherited lock; ours is closed
  count_running
  echo "launch $i $(date +%T) running=$NRUN slots=$NSLOT gslot=$GSLOT/$GMAX load=$(cut -d' ' -f1 /proc/loadavg) :: $j" >> "$LOGDIR/pool.status"
  sleep 30   # let load1 catch up before the next decision
done
wait
echo "lpool done $(date +%T)" >> "$LOGDIR/pool.status"
date > "$LOGDIR/POOL_DONE"
