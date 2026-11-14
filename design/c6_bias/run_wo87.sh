#!/bin/bash
# WO-87 (C6f) run, inside the frozen copy /home/mempool/regr/tt/WO-87-<sha> (cwd = that dir).
# D89 gate + new copies. Reruns every tran row/copy and the dct hint copies; the dci/loop/dcv/dct(none,ptat,trim_open)
# decks are unchanged since WO-80 (c6_spot.py diff 1153e82..HEAD touches only tran, the copies and the dct thr guard),
# so their WO-80 .json results are copied in. Wait on out/pool/POOL_DONE; verdicts in out/summary.txt.
set -u
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A PYTHONPATH=$PWD
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit
D=$PWD; PY="python $D/design/c6_bias/c6_spot.py"; LP=$D/scripts/lpool.sh
O=$D/out; mkdir -p $O
W80=/home/mempool/regr/tt/WO-80-1153e82/out
cp $W80/tune.json $O/tune.json
for k in dci loop dcv; do cp $W80/${k}_*.json $O/ 2>/dev/null; done
for f in $W80/dct_*.json; do case $f in *hint*) ;; *) cp $f $O/;; esac; done
$PY jobs $O $O/jobs_all.txt
grep -E ' run [^ ]+ (tran |dct [a-z]+ [0-9-]+ [0-9.]+ (oldhint|zhint|zhintnk))' $O/jobs_all.txt > $O/jobs.txt
$LP $O/jobs.txt $O/pool_run
$PY summary $O > $O/summary.txt 2>&1
mkdir -p $O/pool && date > $O/pool/POOL_DONE
