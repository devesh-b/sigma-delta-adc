#!/bin/bash
# Thermal watchdog for run-multi.sh. Samples every coretemp sensor every 2 s;
# any reading above LIMIT_MC (millidegrees, default 80000 = 80 C) -- or 5
# unreadable samples in a row -- SIGKILLs the driver's whole session plus any
# stray tool process still running from the project tree, writes TRIPPED and
# exits. Exits quietly once the driver's session is empty.
M=~/regr/multi
LIMIT=${LIMIT_MC:-80000}
LOG=$M/thermal.log
echo $$ > $M/thermal.pid
for i in $(seq 60); do [ -s $M/driver.sid ] && break; sleep 1; done
SID=$(cat $M/driver.sid 2>/dev/null)
[ -n "$SID" ] || { echo "$(date -Is) no driver.sid, watchdog not armed" >> $LOG; exit 1; }
hw=$(grep -l '^coretemp$' /sys/class/hwmon/hwmon*/name | head -1); hw=${hw%/name}
echo "$(date -Is) armed sid=$SID limit=$((LIMIT/1000))C sensors=$hw" >> $LOG
fails=0; n=0; peak=0
while :; do
  max=0
  for t in $hw/temp*_input; do
    v=$(cat $t 2>/dev/null) || continue
    [ "$v" -gt "$max" ] && max=$v
  done
  if [ "$max" -eq 0 ]; then fails=$((fails+1)); else fails=0; fi
  [ "$max" -gt "$peak" ] && peak=$max
  if [ "$max" -gt "$LIMIT" ] || [ "$fails" -ge 5 ]; then
    if [ "$fails" -ge 5 ]; then why="sensors unreadable x5"; else why="cpu $((max/1000))C > $((LIMIT/1000))C"; fi
    pkill -KILL -s "$SID"
    # Strays outside the session (e.g. a spike that outlived a crashed stage):
    # any non-shell process whose cwd is in the project tree.
    for p in /proc/[0-9]*; do
      pid=${p#/proc/}; [ "$pid" = $$ ] && continue
      case "$(readlink $p/cwd 2>/dev/null)" in /home/mempool/AlphaOneSoC*) ;; *) continue;; esac
      case "$(cat $p/comm 2>/dev/null)" in bash|sh|zsh|tmux*|ssh|sshd) continue;; esac
      kill -KILL "$pid" 2>/dev/null
    done
    sleep 2
    left=$(pgrep -c -s "$SID")
    msg="$(date -Is) TRIPPED: $why -- killed session $SID (left=$left), peak=$((peak/1000))C"
    echo "$msg" >> $LOG; echo "$msg" >> $M/STATUS; echo "$msg" > $M/TRIPPED
    sensors 2>/dev/null >> $LOG
    exit 0
  fi
  n=$((n+1))
  [ $((n % 30)) -eq 0 ] && echo "$(date -Is) max=$((max/1000))C peak=$((peak/1000))C" >> $LOG
  pgrep -s "$SID" > /dev/null || { echo "$(date -Is) driver session empty, watchdog exits, peak=$((peak/1000))C" >> $LOG; exit 0; }
  sleep 2
done
