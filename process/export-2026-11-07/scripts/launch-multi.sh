#!/bin/bash
# Starts run-multi.sh and its thermal watchdog, each in its own session.
M=~/regr/multi
mkdir -p $M
rm -f $M/TRIPPED $M/STOP $M/driver.sid $M/driver.pid $M/thermal.pid
ROUNDS=${ROUNDS:-3} setsid nohup bash ~/regr/run-multi.sh > $M/driver.log 2>&1 < /dev/null &
setsid nohup bash ~/regr/thermal-watch.sh > $M/thermal-driver.log 2>&1 < /dev/null &
sleep 3
echo "driver sid=$(cat $M/driver.sid) watchdog pid=$(cat $M/thermal.pid)"
tail -2 $M/thermal.log
