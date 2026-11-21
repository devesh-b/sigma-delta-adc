#!/usr/bin/env bash
# WO-107 item 3: TT precheck (TinyTapeout/tt-support-tools precheck, its pinned nix tools) on the frame GDS.
# Sandbox host only (not in IIC-OSIC-TOOLS): bash precheck_frame.sh <frame gds> <work dir under /home/mempool/regr/tt>
# Setup follows scripts/s0_precheck.sh (same template / tools / venv recipe), in its own work dir.
set -uo pipefail
G=$1; W=$2
case "$W" in /home/mempool/regr/tt/?*) ;; *) echo "REJECT: W must be under /home/mempool/regr/tt"; exit 2;; esac
[ "$(hostname)" = mempool ] || { echo "REJECT: sandbox only"; exit 2; }
export PATH=/home/mempool/.nix-profile/bin:$PATH
export PDK_ROOT=/home/mempool/.ciel PDK=sky130A
mkdir -p "$W"; cd "$W" || exit 2
[ -d tools/.git ] || timeout 300 git clone -q https://github.com/TinyTapeout/tt-support-tools.git tools || exit 3
echo "tools $(git -C tools rev-parse HEAD)"
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv && nice -n 10 timeout 900 venv/bin/pip install -q gdstk pyyaml "klayout>=0.30.8,<0.31" yowasp-yosys numpy pytest || exit 4
fi
cp "$G" "$W/frame.gds"
( cd tools/precheck && rm -f reports/results.* && nice -n 10 timeout 2400 nix-shell default.nix --run "export PATH=\$PATH:$W/venv/bin; echo TOOLS magic=\$(magic --version </dev/null 2>&1 | tail -1) klayout=\$(klayout -v 2>/dev/null | tail -1); $W/venv/bin/python precheck.py --gds $W/frame.gds" </dev/null ) > precheck.log 2>&1
echo "precheck rc=$?"; grep -m1 '^TOOLS' precheck.log
cp tools/precheck/reports/results.md . 2>/dev/null && sed -n 1,40p results.md
