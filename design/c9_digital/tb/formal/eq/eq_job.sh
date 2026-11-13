#!/usr/bin/env bash
# WO-60B retime equivalence jobs.  Run INSIDE IIC-OSIC-TOOLS from the frozen tb dir: formal/eq/eq_job.sh KIND
#   top        full-chip miter new vs e450ae2 (abc pdr)          must PASS
#   topbmc     same, smtbmc yices BMC depth 400                  must PASS
#   div        fsdiv miter under the latch-edge environment      must PASS
#   unconstr   fsdiv miter, environment dropped                  must FAIL (the miter can fail)
#   M62|M63    fsdiv miter on retime mutants                      must FAIL
#   M64        fsdiv miter, constants pipelined one more clk      expected PASS (documents the margin)
#   env        EQ-ENV on the real core: act[9:7] changes only on the clk after fs_tick   must PASS
#   envmut     EQ-ENV with latch not gated by fs_tick             must FAIL
# Prints "EQ <kind> PASS|FAIL|ERR".  Work dir ../eq/<kind> (relative to tb).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); TB=$HERE/../..; RTL=$TB/../rtl; K=$1
W=$TB/../eq/$K; rm -rf "$W"; mkdir -p "$W/n" "$W/o"
cp "$RTL"/*.v "$W/n/"
for f in "$RTL"/*.v; do b=$(basename "$f" .v); cp "$f" "$W/o/${b}_o.v"; done
cp "$HERE/c9_fsdiv_e450ae2.v" "$W/o/c9_fsdiv_o.v"
sed -i -E 's/\b(c9_cfg|sd_adc_c9|c9_dec|c9_fsdiv|c9_rdbus|c9_seq|tt_um_sd_adc_c9)\b/\1_o/g' "$W"/o/*.v
D=$W/n/c9_fsdiv.v; cp "$D" "$W/fsdiv.orig"
case $K in
  M62) sed -i 's/fs_tick <= (dc == tc_fs);/fs_tick <= (dc == tc_fs + 8'"'"'d1);/' "$D";;          # tc_fs = div-1
  M63) sed -i -e 's/tc_fs   <= fs_c;/if (fs_tick) tc_fs <= fs_c;/' \
              -e 's/tc_half <= half_c;/if (fs_tick) tc_half <= half_c;/' "$D";;                # stale constant for a period
  M64) sed -i -e 's/reg s_tick; /reg s_tick; reg [7:0] fs_p, hp; /' \
              -e 's/tc_half <= 8'"'"'d10;/tc_half <= 8'"'"'d10; fs_p <= 8'"'"'d22; hp <= 8'"'"'d10;/' \
              -e 's/tc_fs   <= fs_c;/tc_fs <= fs_p; fs_p <= fs_c;/' \
              -e 's/tc_half <= half_c;/tc_half <= hp; hp <= half_c;/' "$D";;                  # constants 1 clk staler
esac
case $K in M6*) cmp -s "$D" "$W/fsdiv.orig" && { echo "EQ $K ERR mutant edit did not apply"; exit 2; };; esac
TO=5400; [ "$K" = top ] && TO=2400; RVF=""; DEF=""; MODE="prove"; ENG="abc pdr"; TOP=eq_div; SRC="c9_fsdiv.v c9_fsdiv_o.v"; FILES="$W/n/c9_fsdiv.v $W/o/c9_fsdiv_o.v"
NEWALL="c9_cfg.v c9_core.v c9_dec.v c9_fsdiv.v c9_rdbus.v c9_seq.v tt_um_sd_adc_c9.v"
case $K in
  top|topbmc) DEF="-DEQ_TOP"; TOP=eq_top; SRC="$NEWALL $(echo $NEWALL | sed 's/\.v/_o.v/g')"; FILES="$(ls "$W"/n/*.v "$W"/o/*.v)"
              [ $K = topbmc ] && { MODE="bmc\ndepth 400"; ENG="smtbmc yices"; };;
  unconstr)   DEF="-DUNCONSTR";;
  env|envmut) TOP=sd_adc_c9; RVF="-formal "; SRC="c9_cfg.v c9_core.v c9_dec.v c9_fsdiv.v c9_rdbus.v c9_seq.v"; FILES="$(ls "$W"/n/c9_*.v)"
    [ $K = envmut ] && { sed -i 's/assign latch = fs_tick & slot_start & ~ctr_n\[0\];/assign latch = slot_start \& ~ctr_n[0];/' "$W/n/c9_seq.v"
                         grep -q "assign latch = slot_start" "$W/n/c9_seq.v" || { echo "EQ $K ERR edit"; exit 2; }; }
    sed -i 's/^endmodule/`ifdef FORMAL\n  reg ep_v = 0, ep_t = 0, ep_r = 0; reg [2:0] ep_a = 0;\n  always @(posedge clk) begin ep_v <= 1; ep_t <= fs_tick; ep_r <= rs; ep_a <= act[9:7]; end\n  always @* if (ep_v \&\& ep_r \&\& rs) assert (act[9:7] == ep_a || ep_t);   \/\/ EQ-ENV\n`endif\nendmodule/' "$W/n/c9_core.v";;
esac
{ printf "[options]\nmode $MODE\nmulticlock off\n\n[engines]\n$ENG\n\n[script]\nread_verilog $RVF-DFORMAL $SRC\n"
  case $K in env|envmut) ;; *) printf "read_verilog -formal $DEF eq_props.sv\n";; esac
  printf "prep -top $TOP\n\n[files]\n"
  case $K in env|envmut) ;; *) echo "$HERE/eq_props.sv";; esac
  for f in $FILES; do echo "$f"; done; } > "$W/eq.sby"
(cd "$W" && timeout $TO sby -f eq.sby > sby.log 2>&1)
if grep -q "DONE (PASS" "$W/sby.log"; then s=PASS; elif grep -q "DONE (FAIL" "$W/sby.log"; then s=FAIL; else s=ERR; fi
echo "EQ $K $s $(grep -m1 -oE 'Assert failed in [^ ]+|failed assertion [^ ]+' "$W/sby.log")"
