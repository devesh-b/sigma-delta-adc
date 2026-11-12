#!/bin/bash
# WO-50 (C6b) start-up spot sims, run inside the frozen copy /home/mempool/regr/tt/WO-50-<sha> (cwd = that dir).
# No re-tune: R2/R1 is taken from the WO-45 golden (the start-up is off in the steady state).
# All jobs through lpool; wait on out/pool/POOL_DONE; verdict table in out/summary.txt (and golden/summary.txt).
set -u
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A OMP_NUM_THREADS=1
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit
mkdir -p out golden
cp /home/mempool/regr/tt/WO-45-0fb6db0/golden/tune.json out/tune.json
python design/c6_bias/c6_spot.py jobs out out/jobs.txt
env -u OMP_NUM_THREADS /home/mempool/tt-sd/scripts/lpool.sh out/jobs.txt out/pool_run  # nproc honours OMP_NUM_THREADS (WO-45/50 first pool ran with nproc=1)
python design/c6_bias/c6_spot.py summary out > out/summary.txt 2>&1
cp out/summary.txt out/tune.json golden/ 2>/dev/null
mkdir -p out/pool && date > out/pool/POOL_DONE
