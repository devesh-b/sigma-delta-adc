#!/usr/bin/env bash
# s0_precheck.sh — TT analog template (2x2, 3v3) dummy project through TT's own sky130 precheck.
# Sandbox only. Everything lives under /home/mempool/regr/tt/WO-01/tt (never /home/mempool/tt).
#   scripts/s0_precheck.sh ok     dummy project           -> ACCEPT if TT precheck passes
#   scripts/s0_precheck.sh met5   same + one met5 rect    -> REJECT expected (nonzero exit)
#   scripts/s0_precheck.sh all    both; ACCEPT only if ok passes AND met5 fails on the forbidden-layer check
# Template: TinyTapeout/ttsky-analog-template (shuttle ttsky26d); tools: TinyTapeout/tt-support-tools main.
set -uo pipefail
MODE=${1:-ok}
W=/home/mempool/regr/tt/WO-01/tt
TOP=tt_um_sd_dummy
export PATH=/home/mempool/.nix-profile/bin:$PATH
export PATH=/home/mempool/regr/tt/WO-01/tt/venv/bin:$PATH
export PDK_ROOT=/home/mempool/.ciel PDK=sky130A
[ "$(hostname)" = mempool ] || { echo "REJECT: sandbox only"; exit 2; }
mkdir -p "$W"; cd "$W" || exit 2

setup() {
  [ -d tpl/.git ] || timeout 200 git clone -q --depth 1 https://github.com/TinyTapeout/ttsky-analog-template.git tpl || return 1
  [ -d tools/.git ] || timeout 300 git clone -q https://github.com/TinyTapeout/tt-support-tools.git tools || return 1
  echo "template $(git -C tpl remote get-url origin) $(git -C tpl rev-parse HEAD)"
  echo "tools    $(git -C tools remote get-url origin) $(git -C tools rev-parse HEAD)"
  if [ ! -x venv/bin/python ]; then
    python3 -m venv venv && nice -n 10 timeout 600 venv/bin/pip install -q gdstk pyyaml "klayout>=0.30.8,<0.31" yowasp-yosys numpy pytest || return 1
  fi
}

build() {  # $1 = variant dir name (ok|met5)
  local V=$1 P=$W/proj_$1
  rm -rf "$P"; mkdir -p "$P/src" "$P/gds" "$P/lef"
  cat > "$P/src/project.v" <<V
\`default_nettype none
module $TOP (
    input  wire       VGND,
    input  wire       VDPWR,
    input  wire       VAPWR,
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    inout  wire [7:0] ua,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
  assign uo_out  = 8'b0;
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;
endmodule
V
  cp "$P/src/project.v" "$P/gds/$TOP.v"
  cat > "$P/info.yaml" <<Y
project:
  title: "sd dummy"
  author: "x"
  discord: ""
  description: "S0 precheck dummy"
  language: "Analog"
  clock_hz: 0
  tiles: "2x2"
  analog_pins: 3
  uses_vapwr: true
  top_module: "$TOP"
  source_files:
    - "project.v"
pinout:
  ua[0]: "VIN+"
  ua[1]: "VIN-"
  ua[2]: "VREF"
yaml_version: 6
Y
  cat > "$P/build.tcl" <<T
def read $W/tools/tech/sky130A/def/analog/tt_analog_2x2_3v3.def
cellname rename tt_um_template $TOP
proc stripe {name x} {
  box \$x 5um \$x 220.76um
  box width 2um
  paint met4
  label \$name FreeSans 0.25u -met4
  port make
  port use [expr {\$name eq "VGND" ? "ground" : "power"}]
  port class bidirectional
  port connections n s e w
}
stripe VDPWR 1um
stripe VGND 4um
stripe VAPWR 7um
# ua0..ua2: met4 stubs on the TT pin rectangles (x centres from the template DEF)
foreach x {136.62 117.3 97.98} {
  box [expr {\$x-0.45}]um 0um [expr {\$x+0.45}]um 10um
  paint met4
}
T
  [ "$V" = met5 ] && cat >> "$P/build.tcl" <<T
box 20um 100um 30um 110um
paint met5
T
  cat >> "$P/build.tcl" <<T
save $TOP
gds write gds/$TOP.gds
lef write lef/$TOP.lef -hide -pinonly
quit -noprompt
T
  (cd "$P" && nice -n 10 timeout 300 magic -noconsole -dnull -rcfile $PDK_ROOT/$PDK/libs.tech/magic/$PDK.magicrc build.tcl </dev/null > build.log 2>&1)
  echo "magic build rc=$? log=$P/build.log"
  [ -s "$P/gds/$TOP.gds" ] && [ -s "$P/lef/$TOP.lef" ]
}

run_precheck() {  # $1 = variant; prints verdict, returns precheck rc
  local V=$1 P=$W/proj_$1
  ( cd "$W/tools/precheck" && rm -f reports/results.* reports/magic_drc.* reports/drc_* &&
    nice -n 10 timeout 900 "$W/venv/bin/python" precheck.py --gds "$P/gds/$TOP.gds" </dev/null ) > "$P/precheck.log" 2>&1
  local rc=$?
  cp "$W/tools/precheck/reports/results.md" "$P/results.md" 2>/dev/null
  echo "precheck[$V] rc=$rc log=$P/precheck.log"; cat "$P/results.md" 2>/dev/null | sed -n 3,40p
  return $rc
}

setup || { echo "REJECT: setup failed (network/clone/pip)"; exit 1; }
case $MODE in
  ok|met5)
    build $MODE || { echo "REJECT: build failed"; exit 1; }
    run_precheck $MODE && { echo "ACCEPT: TT precheck passed ($MODE)"; exit 0; }
    echo "REJECT: TT precheck failed ($MODE)"; exit 1 ;;
  all)
    build ok && build met5 || { echo "REJECT: build failed"; exit 1; }
    run_precheck ok; rc_ok=$?
    run_precheck met5; rc_m5=$?
    if [ $rc_ok -eq 0 ] && [ $rc_m5 -ne 0 ] && grep -q "Forbidden layer" "$W/proj_met5/results.md"; then
      echo "ACCEPT: ok passes, met5 copy fails on Forbidden layer"; exit 0
    fi
    echo "REJECT: ok_rc=$rc_ok met5_rc=$rc_m5"; exit 1 ;;
  *) echo "usage: $0 ok|met5|all"; exit 2 ;;
esac
