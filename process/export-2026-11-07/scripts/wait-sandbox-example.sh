#!/bin/bash
# Wakes Claude when the WO-18 sandbox campaign ends, trips, dies, reboots or goes unreachable.
boot0="2026-10-16 01:31:56"; miss=0
while :; do
  out=$(timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=10 sandbox 'W=~/regr/wo18; echo "BOOT $(uptime -s)"; [ -f $W/TRIPPED ] && echo TRIPPED; grep -q " DONE$" $W/STATUS && echo CAMPAIGN_FINISHED; pgrep -s $(cat $W/driver.sid) >/dev/null || echo DRIVER_GONE; ls $W/done 2>/dev/null | wc -l | sed "s/^/COUNT /"' 2>/dev/null)
  if [ -z "$out" ]; then miss=$((miss+1)); [ $miss -ge 5 ] && { echo "sandbox unreachable x5"; exit 0; }; sleep 60; continue; fi
  miss=0
  echo "$out" | grep -q "BOOT $boot0" || { echo "sandbox rebooted: $out"; exit 0; }
  echo "$out" | grep -qE "TRIPPED|CAMPAIGN_FINISHED|DRIVER_GONE" && { echo "$out"; exit 0; }
  sleep 120
done
