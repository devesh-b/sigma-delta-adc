#!/usr/bin/env bash
# WO-40 mutation job: one mutant, own dir ../mut/<MID>.  Run INSIDE IIC-OSIC-TOOLS from the frozen tb dir.
# Planned killing tests first, then the rest; stops at the first killing test.  Prints "MUT <id> <KILLED|SURVIVED|ERROR> ..."
set -u
HERE=$(cd "$(dirname "$0")" && pwd); MID=$1
D=$HERE/../mut/$MID; mkdir -p "$D"
python3 "$HERE/mutants.py" make "$MID" "$D" > "$D/make.log" 2>&1 || { echo "MUT $MID ERROR make"; cat "$D/make.log"; exit 2; }
iverilog -g2012 -o "$D/chk.vvp" "$D"/rtl/*.v > "$D/compile.log" 2>&1 || { echo "MUT $MID ERROR compile"; cat "$D/compile.log"; exit 2; }
res=SURVIVED; by=""; ran=""
for t in $(python3 "$HERE/mutants.py" tests "$MID"); do
  C9_RTL=$D/rtl C9_OUT=$D/out_$t C9_RUNDIR=$D TESTS="${t}\$" timeout 2400 python3 "$HERE/run_cocotb.py" > "$D/$t.log" 2>&1
  r=$?; ran="$ran $t"
  grep -q "RESULT PASS: 1 tests" "$D/$t.log" && continue
  if grep -q "RESULT FAIL: 1 tests, 1 failed" "$D/$t.log" || [ $r = 124 ]; then
    res=KILLED; by=$t; [ $r = 124 ] && by="$t(timeout)"
    msg=$(grep -m1 -oE "ERROR +cocotb\.[a-z_0-9]+ +\[.*" "$D/$t.log" | cut -c1-160)
    break
  fi
  res=ERROR; by="$t(no result rc=$r)"; break
done
echo "MUT $MID $res $by | ${msg:-}"
