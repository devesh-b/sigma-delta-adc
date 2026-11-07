#!/bin/bash
# resumable-stages-template.sh -- skeleton for a long sandbox job that survives
# unclean reboots. Each finished stage leaves done.<stage>; a relaunch skips it.
# Launch detached so the thermal watchdog can arm on driver.sid:
#   OUT=~/regr/<campaign>/<run> setsid nohup bash resumable-stages-template.sh \
#       > $OUT/driver.log 2>&1 < /dev/null &
#   M=$OUT setsid nohup bash ~/regr/thermal-watch.sh > $OUT/thermal-driver.log 2>&1 < /dev/null &
set -u
OUT=${OUT:?set OUT}
TREE=${TREE:-$OUT/tree}            # frozen tree (git archive <hash> | tar -x)
S=$OUT/STATUS
mkdir -p "$OUT"
ps -o sid= $$ | tr -d ' ' > "$OUT/driver.sid"   # the watchdog kills this session
st() { echo "$(date -Is) $*" >> "$S"; }

# setsid shells do not get the interactive init: set the environment here.
export PATH=/path/to/toolchain/bin:$PATH

st "start host=$(hostname) boot=$(uptime -s) code=$(cat "$OUT/CODE" 2>/dev/null || echo '?')"
st "done so far: $(ls "$OUT" | grep '^done\.' | tr '\n' ' ')"

run() {  # run <stage> <function>
  local s=$1; shift
  [ -f "$OUT/done.$s" ] && { st "[$s] already done, skipped"; return; }
  if "$@"; then touch "$OUT/done.$s"; st "[$s] PASS"; else st "[$s] FAIL rc=$?"; fi
}

stage_unit()   { cd "$TREE" && timeout 3600 make BUILD_DIR=build/unit test-all > "$OUT/unit.log" 2>&1; }
stage_suite()  { cd "$TREE" && timeout 7200 ./tests/run.sh > "$OUT/suite.log" 2>&1; }

run unit  stage_unit
run suite stage_suite
st "DONE"     # the local waiter looks for a line ending in DONE
