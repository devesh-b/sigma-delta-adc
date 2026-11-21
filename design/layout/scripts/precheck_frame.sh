#!/usr/bin/env bash
# WO-107/WO-109 item 3: TT precheck (TinyTapeout/tt-support-tools precheck, under its pinned nix tools) on the frame.
# Sandbox host only (not in IIC-OSIC-TOOLS): bash precheck_frame.sh <run dir under /home/mempool/regr/tt>
# The project dirs <run>/out/precheck/proj_{ok,met5} (info.yaml, src/, gds/, lef/) are built by run.sh (PART=all) in
# the container, the way scripts/s0_precheck.sh build() does. Tools/venv recipe as s0_precheck.sh, in <run>/precheck.
# Verdict: ok must have no failed row under magic 8.3.568 / klayout 0.30.8; met5 must fail with "Forbidden layer".
set -uo pipefail
RUN=$1; W=$RUN/precheck; TOP=tt_um_sd_adc_fp
case "$RUN" in /home/mempool/regr/tt/?*) ;; *) echo "REJECT: run dir must be under /home/mempool/regr/tt"; exit 2;; esac
case "$RUN" in *..*) echo "REJECT: no .."; exit 2;; esac
[ "$(hostname)" = mempool ] || { echo "REJECT: sandbox only"; exit 2; }
export PATH=/home/mempool/.nix-profile/bin:$PATH
export PDK_ROOT=/home/mempool/.ciel PDK=sky130A
mkdir -p "$W"; cd "$W" || exit 2
[ -d tools/.git ] || timeout 300 git clone -q https://github.com/TinyTapeout/tt-support-tools.git tools || exit 3
echo "tools $(git -C tools rev-parse HEAD)"
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv && nice -n 10 timeout 900 venv/bin/pip install -q gdstk pyyaml "klayout>=0.30.8,<0.31" yowasp-yosys numpy pytest || exit 4
fi
rc_all=0
for V in ok met5; do
  P=$RUN/out/precheck/proj_$V
  [ -s "$P/gds/$TOP.gds" ] && [ -s "$P/lef/$TOP.lef" ] && [ -s "$P/info.yaml" ] || { echo "PRECHECK $V MISSING project files in $P"; rc_all=1; continue; }
  ( cd tools/precheck && rm -f reports/results.* reports/magic_drc.* reports/drc_* &&
    nice -n 10 timeout 2400 nix-shell default.nix --run "export PATH=\$PATH:$W/venv/bin; echo TOOLS magic=\$(magic --version </dev/null 2>&1 | tail -1) klayout=\$(klayout -v 2>/dev/null | tail -1); $W/venv/bin/python precheck.py --gds $P/gds/$TOP.gds" </dev/null ) > "$W/precheck_$V.log" 2>&1
  rc=$?
  cp tools/precheck/reports/results.md "$W/results_$V.md" 2>/dev/null || rm -f "$W/results_$V.md"
  failed=$(grep '❌' "$W/results_$V.md" 2>/dev/null | sed 's/^| *\([^|]*[^ |]\) *|.*/\1/' | paste -sd, -)
  tools=$(grep -m1 '^TOOLS' "$W/precheck_$V.log")
  pinned=no; echo "$tools" | grep -q 'magic=8\.3\.568 klayout=KLayout 0\.30\.8' && pinned=yes
  rows=$(grep -c '^|' "$W/results_$V.md" 2>/dev/null)
  case $V in
    ok)   [ $rc -eq 0 ] && [ -z "$failed" ] && [ $pinned = yes ] && [ "${rows:-0}" -gt 2 ] && v=PASS || v=FAIL ;;
    met5) [ $rc -ne 0 ] && grep '❌' "$W/results_$V.md" 2>/dev/null | grep -q 'Forbidden layer' && v=FAIL_AS_EXPECTED || v=UNEXPECTED ;;
  esac
  echo "PRECHECK $V VERDICT=$v rc=$rc pinned=$pinned rows=$rows failed=[$failed] $tools"
  [ "$V" = ok ] && [ $v != PASS ] && rc_all=1; [ "$V" = met5 ] && [ $v != FAIL_AS_EXPECTED ] && rc_all=1
  sed -n 1,40p "$W/results_$V.md" 2>/dev/null
  grep -m5 -i "error\|exception\|failure" "$W/precheck_$V.log"
done
echo "PRECHECK_EXIT=$rc_all"
