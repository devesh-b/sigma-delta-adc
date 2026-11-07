# s0_precheck.sh — TT analog template (2x2, 3v3) dummy project through TT's own sky130 precheck.
# Sandbox only. Runs against the tree this script lives in; nothing is shared between runs unless you ask.
#   scripts/s0_precheck.sh ok        dummy project (digital pins tied to VGND in the GDS) -> ACCEPT if TT precheck passes
#   scripts/s0_precheck.sh <broken>  dummy + one defect -> REJECT expected (nonzero exit); broken in:
#       met5     one met5 rect             must fail "KLayout Checks" (Forbidden layer)
#       drcbeol  met4 wire 0.2 um wide     must fail "Magic DRC" + "KLayout BEOL"
#       drcfeol  poly sliver 0.1 um wide   must fail "KLayout FEOL" (+ "Magic DRC": poly width is in both decks)
#       apin     ua[2] stub removed        must fail "Analog pin check" naming ua[2]
#       apinx    extra stub on ua[3]       must fail "Analog pin check" naming ua[3]
#   scripts/s0_precheck.sh all       ok + every broken variant. ACCEPT only if ok is clean and each broken
#                                    variant fails EXACTLY its expected rows (others stay green).
# Env: W (work dir, default /home/mempool/regr/tt/runs/$RUN_TAG/precheck; must be under /home/mempool/regr/tt),
#      RUN_TAG (default = basename of the repo root this script lives in).
# Precheck runs in TT's own nix-shell (tt-support-tools/precheck/default.nix: magic 8.3.568, klayout 0.30.8) with venv
# python for the pip modules. The dummy layout is BUILT with the newer nix-profile magic (build tools may be newer).
# Template: TinyTapeout/ttsky-analog-template (shuttle ttsky26d); tools: TinyTapeout/tt-support-tools main.
set -uo pipefail
MODE=${1:-ok}
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RUN_TAG=${RUN_TAG:-$(basename "$REPO")}
W=${W:-/home/mempool/regr/tt/runs/$RUN_TAG/precheck}
TOP=tt_um_sd_dummy
case "$W" in /home/mempool/regr/tt/?*) ;; *) echo "REJECT: W must be under /home/mempool/regr/tt (got $W)"; exit 2;; esac
case "$W" in *..*) echo "REJECT: W must not contain .."; exit 2;; esac
export PATH=/home/mempool/.nix-profile/bin:$PATH
export PDK_ROOT=${PDK_ROOT:-/home/mempool/.ciel} PDK=sky130A
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

build() {  # $1 = variant: ok|met5|drcbeol|drcfeol|apin|apinx
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
T
  local STUBS="136.62 117.3 97.98"
  [ "$V" = apin ] && STUBS="136.62 117.3"          # ua[2] stub removed
  [ "$V" = apinx ] && STUBS="136.62 117.3 97.98 78.66"   # extra stub on ua[3]
  for x in $STUBS; do cat >> "$P/build.tcl" <<T
box [expr {$x-0.45}]um 0um [expr {$x+0.45}]um 10um
paint met4
T
  done
  # S-2: tie uo_out[7:0], uio_out[7:0], uio_oe[7:0] to VGND in the layout, as project.v does. The 24 pins sit
  # on the top edge at x = 15.18 + 2.76*k um (k=0..23, from the DEF). Each gets a 0.3 um met4 stub, joined by
  # a met4 bar (above the power stripes, y>=222) that links down to the VGND stripe (x 4..6 um).
  # TT precheck does NOT check this; the V8 GDS-vs-Verilog tie check covers it.
  cat >> "$P/build.tcl" <<T
box 4.5um 219um 5.5um 223.3um
paint met4
box 4.5um 222um 78.81um 223.3um
paint met4
for {set k 0} {\$k < 24} {incr k} {
  set x [expr {15.18 + 2.76*\$k}]
  box [expr {\$x-0.15}]um 222um [expr {\$x+0.15}]um 225.76um
  paint met4
}
T
  case "$V" in
    met5)    printf 'box 20um 100um 30um 110um\npaint met5\n' >> "$P/build.tcl" ;;
    drcbeol) printf 'box 30um 100um 30.2um 120um\npaint met4\n' >> "$P/build.tcl" ;;
    drcfeol) printf 'box 30um 100um 30.1um 110um\npaint poly\n' >> "$P/build.tcl" ;;
  esac
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

expect_for() {  # variant -> "rows;regex-on-those-rows" ; rows separated by ','
  case $1 in
    ok)      echo ";" ;;
    met5)    echo "KLayout Checks;Forbidden layer met5" ;;
    drcbeol) echo "Magic DRC,KLayout BEOL;" ;;
    drcfeol) echo "Magic DRC,KLayout FEOL;" ;;  # poly width rule is in both decks
    apin)    echo "Analog pin check;ua\\[2\\]" ;;
    apinx)   echo "Analog pin check;ua\\[3\\]" ;;
  esac
}
failed_rows() {  # results.md -> failed row names, comma separated, in file order
  grep '❌' "$1" | sed 's/^| *\([^|]*[^ |]\) *|.*/\1/' | paste -sd, -
}

run_precheck() {  # $1 = variant; prints verdict, returns precheck rc
  local V=$1 P=$W/proj_$1
  ( cd "$W/tools/precheck" && rm -f reports/results.* reports/magic_drc.* reports/drc_* &&
    nice -n 10 timeout 1500 nix-shell default.nix --run "export PATH=\$PATH:$W/venv/bin; echo TOOLS magic=\$(magic --version </dev/null 2>&1 | tail -1) klayout=\$(klayout -v 2>/dev/null | tail -1); $W/venv/bin/python precheck.py --gds $P/gds/$TOP.gds" </dev/null ) > "$P/precheck.log" 2>&1
  local rc=$?
  cp "$W/tools/precheck/reports/results.md" "$P/results.md" 2>/dev/null || rm -f "$P/results.md"
  echo "precheck[$V] rc=$rc log=$P/precheck.log $(grep -m1 '^TOOLS' "$P/precheck.log")"; sed -n 3,40p "$P/results.md" 2>/dev/null
  return $rc
}

tools_ok() {  # the precheck must have run under TT's pinned tools
  grep -q '^TOOLS magic=8\.3\.568 klayout=KLayout 0\.30\.8' "$W/proj_$1/precheck.log"
}

# judge a variant: 0 if it behaves as expected. ok: clean + pinned tools. broken: fails exactly the expected rows.
judge() {
  local V=$1 P=$W/proj_$1 exp rows rx got
  exp=$(expect_for $V); rows=${exp%%;*}; rx=${exp#*;}
  tools_ok $V || { echo "  [$V] FAIL: precheck did not run under magic 8.3.568 / klayout 0.30.8"; return 1; }
  [ -s "$P/results.md" ] || { echo "  [$V] FAIL: no results.md"; return 1; }
  got=$(failed_rows "$P/results.md")
  [ "$got" = "$rows" ] || { echo "  [$V] FAIL: failed rows '[$got]' != expected '[$rows]'"; return 1; }
  if [ -n "$rx" ]; then grep '❌' "$P/results.md" | grep -qE "$rx" || { echo "  [$V] FAIL: message does not match /$rx/"; return 1; }; fi
  echo "  [$V] as expected: failed rows = [$got]"
}

setup || { echo "REJECT: setup failed (network/clone/pip)"; exit 1; }
case $MODE in
  ok|met5|drcbeol|drcfeol|apin|apinx)
    build $MODE || { echo "REJECT: build failed"; exit 1; }
    run_precheck $MODE && { judge $MODE && { echo "ACCEPT: TT precheck passed ($MODE)"; exit 0; }; echo "REJECT: tool check failed ($MODE)"; exit 1; }
    echo "REJECT: TT precheck failed ($MODE); $(judge $MODE | tail -1)"; exit 1 ;;
  all)
    bad=0
    for v in ok met5 drcbeol drcfeol apin apinx; do
      build $v || { echo "REJECT: build failed ($v)"; exit 1; }
      run_precheck $v >/dev/null; judge $v || bad=1
    done
    if [ $bad -eq 0 ]; then echo "ACCEPT: ok clean under pinned tools; every broken copy fails exactly its named rows"; exit 0; fi
    echo "REJECT: see FAIL lines above"; exit 1 ;;
  *) echo "usage: $0 ok|met5|drcbeol|drcfeol|apin|apinx|all"; exit 2 ;;
esac
