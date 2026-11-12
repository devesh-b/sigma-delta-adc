#!/bin/bash
# WO-45 spot sims, run inside the frozen copy /home/mempool/regr/tt/WO-45-<sha> (cwd = that dir).
# Stage 1: tt/27 R2/R1 tune (sequential, ~13 fast DC runs). Stage 2: lpool over the corner/start-up jobs.
# Wait on out/pool/POOL_DONE; the verdict table lands in out/summary.txt (and golden/summary.txt).
set -u
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A OMP_NUM_THREADS=1
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit
mkdir -p out golden
nice -n 10 timeout 1800 python design/c6_bias/c6_spot.py tune out > out/tune.log 2>&1 || echo "TUNE_FAIL" >> out/tune.log
python design/c6_bias/c6_spot.py jobs out out/jobs.txt
/home/mempool/tt-sd/scripts/lpool.sh out/jobs.txt out/pool_run
python design/c6_bias/c6_spot.py summary out > out/summary.txt 2>&1
cp out/summary.txt out/tune.json golden/ 2>/dev/null
mkdir -p out/pool && date > out/pool/POOL_DONE
