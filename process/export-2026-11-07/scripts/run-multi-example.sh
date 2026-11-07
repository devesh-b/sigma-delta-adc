#!/bin/bash
# Multi-round regression on the sandbox.
#   stage conf   : riscv_tests + riscof once (deterministic suites)
#   stage randN  : rrag + riscv_dv, fresh random seeds each round, own work_dir
# generate -> compile per stage; compile runs the comparison.
# Usage: ROUNDS=3 setsid nohup bash ~/regr/run-multi.sh > ~/regr/multi/driver.log 2>&1 < /dev/null &
# Poll ~/regr/multi/STATUS. `touch ~/regr/multi/STOP` ends it after the current stage.
R=/home/mempool/AlphaOneSoC
M=~/regr/multi
S=$M/STATUS
ROUNDS=${ROUNDS:-3}
MIN_FREE_GB=${MIN_FREE_GB:-40}
# Same environment as the rt/rta session init (~/.config/rt/init-alpha.sh).
export PYENV_ROOT=/home/mempool/.pyenv
PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"; eval "$(pyenv virtualenv-init -)"; pyenv activate rivercore 2>/dev/null || true
PATH="/home/mempool/tools/rv64-gcc-elf/bin:/home/mempool/tools/rv32-isa-sim/bin:$PATH"
export PATH ALPHA_ROOT=$R
set -u
mkdir -p $M
# thermal-watch.sh kills this whole session (setsid) if the CPU runs hot.
echo $$ > $M/driver.pid; ps -o sid= -p $$ | tr -d " " > $M/driver.sid
cd $R/plugins
st() { echo "$(date -Is) $*" >> $S; }
free_gb() { df -BG --output=avail /home/mempool | tail -1 | tr -dc 0-9; }

stage() {  # stage <name> <generators>
  local name=$1 gens=$2 W=$R/build/mywork-$1 ini=river-config-$1.ini
  [ -d $W ] && mv $W $W-$(date +%Y%m%d-%H%M%S)
  sed -e "s#^work_dir = .*#work_dir = ../build/mywork-$name#" \
      -e "s#^generator = .*#generator = $gens#" river-config.ini > $ini
  st "[$name] generate: $gens"
  river_core generate -c $ini -v info > $M/$name-generate.log 2>&1
  local rc=$? N
  N=$(python -c "import yaml,sys; print(len(yaml.safe_load(open('$W/test_list.yaml')) or {}))" 2>/dev/null || echo 0)
  st "[$name] generate exit=$rc tests=$N"
  sed "s/\x1b\[[0-9;]*m//g" $M/$name-generate.log | grep -h "GENERATION GAP\|riscv-dv produced\|rrag.*produced\|ERROR" | tail -4 | sed "s/^/    /" >> $S
  if [ "$N" -eq 0 ]; then st "[$name] ABORT no tests"; return 1; fi
  st "[$name] compile"
  river_core compile -c $ini -t $W/test_list.yaml --timeout 900 --nproc 6 -v info > $M/$name-compile.log 2>&1
  st "[$name] compile exit=$? passed=$(grep -c 'TEST PASSED' $M/$name-compile.log) failed=$(grep -c 'TEST FAILED' $M/$name-compile.log)"
  python $R/scripts/audit-regression.py $W/test_list.yaml --csv $M/$name-audit.csv > $M/$name-audit.txt 2>&1
  st "[$name] audit exit=$? $(grep -m2 "^total\|^=== river_core PASSED" $M/$name-audit.txt | tr "\n" " ")"
  st "[$name] disk free=$(free_gb)G"
}

guard() {
  [ -e $M/STOP ] && { st "STOP file present, ending"; return 1; }
  [ "$(free_gb)" -lt "$MIN_FREE_GB" ] && { st "disk free $(free_gb)G < ${MIN_FREE_GB}G, ending"; return 1; }
  return 0
}

st "start code=$(cat $M/CODE 2>/dev/null) rounds=$ROUNDS gcc=$(command -v riscv64-unknown-elf-gcc) spike=$(command -v spike) iverilog=$(iverilog -V 2>/dev/null | head -1 | cut -d' ' -f4) free=$(free_gb)G"
guard && stage conf "riscv_tests, riscof"
for r in $(seq 1 $ROUNDS); do
  guard || break
  stage rand$r "rrag, riscv_dv"
done
st "DONE"
