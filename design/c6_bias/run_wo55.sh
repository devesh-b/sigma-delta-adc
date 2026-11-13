#!/bin/bash
# WO-55 (C6c) robust start-up spot sims, run inside the frozen copy /home/mempool/regr/tt/WO-55-<sha> (cwd = that dir).
# Re-tunes R2/R1 first (the skewed amp adds a PTAT-like offset to the core), then all jobs through lpool.
# Wait on out/pool/POOL_DONE; verdict table in out/summary.txt (and golden/summary.txt).
set -u
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit
mkdir -p out golden
OMP_NUM_THREADS=1 nice -n 10 python design/c6_bias/c6_spot.py tune out > out/tune.log 2>&1
python design/c6_bias/c6_spot.py jobs out out/jobs.txt
/home/mempool/tt-sd/scripts/lpool.sh out/jobs.txt out/pool_run   # lpool sets OMP_NUM_THREADS itself
python design/c6_bias/c6_spot.py summary out > out/summary.txt 2>&1
cp out/summary.txt out/tune.json golden/ 2>/dev/null
mkdir -p out/pool && date > out/pool/POOL_DONE
