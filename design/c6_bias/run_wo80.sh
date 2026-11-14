#!/bin/bash
# WO-80 (C6e) run, inside the frozen copy /home/mempool/regr/tt/WO-80-<sha> (cwd = that dir).
# No re-tune: R1 144.8 / R2/R1 2.45 from the WO-64 tune (tune.json copied in), full pool through lpool.
# Wait on out/pool/POOL_DONE; verdicts in out/summary.txt.
set -u
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit
D=$PWD; PY="python $D/design/c6_bias/c6_spot.py"; LP=/home/mempool/tt-sd/scripts/lpool.sh
O=$D/out; mkdir -p $O
cp /home/mempool/regr/tt/WO-64-e450ae2w/out/tune.json $O/tune.json
$PY jobs $O $O/jobs.txt
$LP $O/jobs.txt $O/pool_run      # lpool sets OMP_NUM_THREADS itself
$PY summary $O > $O/summary.txt 2>&1
mkdir -p $O/pool && date > $O/pool/POOL_DONE
