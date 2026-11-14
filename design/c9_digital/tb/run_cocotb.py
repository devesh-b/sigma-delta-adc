"""cocotb 2.x runner for the C9 bench.  Env: SIM (icarus|verilator), C9_TOP, C9_RTL, TESTS (regex),
C9_SEED, C9_FULL, C9_PW_BITS, C9_BIAS_BITS (WO-75 hold length, default 4/2), C9_COMP, C9_OUT, C9_BUILD_ARGS (extra build flags, e.g. --coverage), C9_RUNDIR (sim cwd).  Exit 1 on any failure, on zero tests, or on a missing results file."""
import glob
import os
import sys
from pathlib import Path

from cocotb_tools.runner import get_results, get_runner

here = os.path.dirname(os.path.abspath(__file__))
rtl = os.environ.get("C9_RTL", os.path.join(here, "..", "rtl"))
top = os.environ.get("C9_TOP", "c9_tb")   # WO-75: parameterised bench top (tb/hdl/c9_tb.v); GL uses tt_um_sd_adc_c9
sim = os.environ.get("SIM", "icarus")
out = os.environ.get("C9_OUT", os.path.join(here, "out"))
srcs = sorted(glob.glob(os.path.join(rtl, "*.v")))
if not srcs:
    print(f"no RTL in {rtl}")
    sys.exit(2)
if top == "c9_tb":
    srcs.append(os.path.join(here, "hdl", "c9_tb.v"))
bd = os.path.join(out, f"build_{sim}")
r = get_runner(sim)
kw = dict(timescale=("1ns", "1ps")) if sim == "icarus" else {}
ba = os.environ.get("C9_BUILD_ARGS", "").split()
if top == "c9_tb":   # CL-36 hold length for the bench (Ref A reads the same env, test_c9.HOLD_*)
    kw["parameters"] = dict(PW_BITS=int(os.environ.get("C9_PW_BITS", "4")), BIAS_BITS=int(os.environ.get("C9_BIAS_BITS", "2")))
if ba:
    kw["build_args"] = ba
r.build(sources=srcs, hdl_toplevel=top, build_dir=bd, always=True, **kw)
xml = os.path.join(out, f"results_{sim}_{os.environ.get('C9_SEED', '1')}.xml")
if os.path.exists(xml):
    os.remove(xml)
env = {k: v for k, v in os.environ.items() if k.startswith("C9_")}
env["PYTHONPATH"] = here + os.pathsep + os.environ.get("PYTHONPATH", "")
pa = os.environ.get("C9_PLUSARGS", "").split()   # e.g. +verilator+rand+reset+2 (X-01)
if pa:
    env_pa = dict(plusargs=pa)
else:
    env_pa = {}
tf = os.environ.get("TESTS")
r.test(hdl_toplevel=top, test_module="test_c9", test_dir=os.environ.get("C9_RUNDIR", here), build_dir=bd, results_xml=xml,
       extra_env=env, test_filter=tf if tf else None, **env_pa)
if not os.path.exists(xml):
    print("RESULT FAIL: no results file")
    sys.exit(1)
n, nf = get_results(Path(xml))   # cocotb 2.1 wants a Path
print(f"RESULT {'PASS' if (n and not nf) else 'FAIL'}: {n} tests, {nf} failed ({xml})")
sys.exit(0 if (n and not nf) else 1)
