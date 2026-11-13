#!/bin/bash
# WO-64 (C6d) run, inside the frozen copy /home/mempool/regr/tt/WO-64-<sha> (cwd = that dir).
#   run_wo64.sh smoke : out_smoke/ (fixed guess ratio 2.2 / R1 165) + tune stage-1 grid, through lpool
#   run_wo64.sh full  : two-stage R2/R1 + R1 tune (lpool), then the full pool. Wait on out/pool/POOL_DONE.
set -u
. /home/mempool/tt-sd/.venv-sbx/bin/activate
export PATH=$HOME/.nix-profile/bin:$PATH PDK_ROOT=/home/mempool/.ciel PDK=sky130A
[ -f .spiceinit ] || printf 'set num_threads=1\n' > .spiceinit
D=$PWD; PY="python $D/design/c6_bias/c6_spot.py"; LP=/home/mempool/tt-sd/scripts/lpool.sh
if [ "${1:-full}" = smoke ]; then
  S=$D/out_smoke; mkdir -p $S
  printf '{"ratio": 2.2, "r1": 165.0}\n' > $S/tune.json
  {
    for f in op gmin; do echo "C6_TRANFIX=$f $PY run $S tran tt 125 3.0 none 1e-06 && mv $S/tran_tt_125_3_none_1e-06.json $S/tran_tt_125_3_none_1e-06.$f.jsn"; done
    echo "$PY run $S tran ff 125 3.0 nosu 1e-06"
    echo "$PY run $S tran tt 27 3.3 none 1e-06"
    echo "$PY run $S tran tt 27 3.3 hy1 1e-06"
    echo "$PY run $S tran sf -40 3.0 none 1e-06"
    echo "$PY run $S dct sf 27 3.0 none"
    echo "$PY run $S dct sf 27 3.0 oldhint"
  } > $S/jobs.txt
  $PY tunejobs $D/out_t1 1 $S/tune1_jobs.txt; mkdir -p $D/out_t1
  cat $S/tune1_jobs.txt >> $S/jobs.txt
  $LP $S/jobs.txt $S/pool_run
  $PY tunepick $D/out_t1 1 > $S/tune1.txt 2>&1
  $PY summary $S > $S/summary.txt 2>&1
  mkdir -p $S/pool && date > $S/pool/POOL_DONE
  exit 0
fi
O=$D/out; mkdir -p $O golden
$PY tunejobs $O 1 $O/tune1_jobs.txt && $LP $O/tune1_jobs.txt $O/tune1_run && $PY tunepick $O 1 > $O/tune.log 2>&1
$PY tunejobs $O 2 $O/tune2_jobs.txt && $LP $O/tune2_jobs.txt $O/tune2_run && $PY tunepick $O 2 >> $O/tune.log 2>&1
$PY jobs $O $O/jobs.txt
$LP $O/jobs.txt $O/pool_run      # lpool sets OMP_NUM_THREADS itself
$PY summary $O > $O/summary.txt 2>&1
cp $O/summary.txt $O/tune.json $O/tune1.json $O/tune.log golden/ 2>/dev/null
mkdir -p $O/pool && date > $O/pool/POOL_DONE
