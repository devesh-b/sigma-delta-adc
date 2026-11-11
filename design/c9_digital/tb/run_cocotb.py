"""cocotb 2.x runner for the C9 bench.  Env: SIM (icarus|verilator), C9_TOP, C9_RTL, TESTS (regex),
C9_SEED, C9_FULL, C9_COMP, C9_OUT.  Exit 1 on any failure, on zero tests, or on a missing results file."""
import glob
import os
import sys

from cocotb_tools.runner import get_results, get_runner

here = os.path.dirname(os.path.abspath(__file__))
rtl = os.environ.get("C9_RTL", os.path.join(here, "..", "rtl"))
top = os.environ.get("C9_TOP", "tt_um_sd_adc_c9")
sim = os.environ.get("SIM", "icarus")
out = os.environ.get("C9_OUT", os.path.join(here, "out"))
srcs = sorted(glob.glob(os.path.join(rtl, "*.v")))
if not srcs:
    print(f"no RTL in {rtl}")
    sys.exit(2)
bd = os.path.join(out, f"build_{sim}")
r = get_runner(sim)
kw = dict(timescale=("1ns", "1ps")) if sim == "icarus" else {}
r.build(sources=srcs, hdl_toplevel=top, build_dir=bd, always=True, **kw)
xml = os.path.join(out, f"results_{sim}_{os.environ.get('C9_SEED', '1')}.xml")
if os.path.exists(xml):
    os.remove(xml)
env = {k: v for k, v in os.environ.items() if k.startswith("C9_")}
env["PYTHONPATH"] = here + os.pathsep + os.environ.get("PYTHONPATH", "")
tf = os.environ.get("TESTS")
r.test(hdl_toplevel=top, test_module="test_c9", test_dir=here, build_dir=bd, results_xml=xml,
       extra_env=env, test_filter=tf if tf else None)
if not os.path.exists(xml):
    print("RESULT FAIL: no results file")
    sys.exit(1)
n, nf = get_results(xml)
print(f"RESULT {'PASS' if (n and not nf) else 'FAIL'}: {n} tests, {nf} failed ({xml})")
sys.exit(0 if (n and not nf) else 1)
