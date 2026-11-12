#!/usr/bin/env python3
"""C3 spot sims (WO-44 item 2/3): decision time, polarity, kickback on a behavioural x2 node, PDK mismatch probe.

    python spot_tran.py gen OUTDIR       # one dir + deck per point, OUTDIR/jobs.txt for scripts/lpool.sh
    python spot_tran.py collect OUTDIR   # parse logs -> OUTDIR/spot.json, ACCEPT/REJECT rows, exit 1 on fail

Sandbox only. One ngspice process per decision point, tmax 1 ps, 10 ohm in series with ideal sources
(LEARNINGS-pthomas). No raw/csv files are written (all numbers come from .meas / print).

Behavioural x2 node (DESIGN.md 4.4): per side an ideal source through R_X2 = 20 kohm (closed-loop OTA2
output resistance 1/(beta2 gm2) at the 4 MHz boost point) with C_X2 = 0.7 pF to ground (OTA2 C_L).
Probes kd = |v(x2p) - v(x2n) - dlt| and kc = |vcm(x2) - vcm| are B-sources that only read voltages.
"""
import json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sizes_draft import comp_subckt, C_Q_LOAD, PRE

LIB = os.path.join(os.environ.get("PDK_ROOT", "/home/mempool/.ciel"), os.environ.get("PDK", "sky130A"),
                   "libs.tech/ngspice/sky130.lib.spice")
SPICEINIT = "set ngbehavior=hsa\nset skywaterpdk\nset ng_nomodcheck\nset num_threads=1\n"
FS = 4e6
T_HALF = 0.45 / FS                      # 112.5 ns (SPEC §3.0 Clock row)
T_FIRE = 20e-9                          # clk 50 % at T_FIRE + 50 ps
T_RST = T_FIRE + T_HALF                 # clk falls (precharge)
TSTOP = T_RST + 62.5e-9
R_X2, C_X2 = 20e3, 0.7e-12
T_DEC_MAX = 0.3 * T_HALF                # 33.75 ns (SPEC row 106: < 34 ns at 4 MHz)
KICK_MAX, KICK_REC = 5e-3, 0.5e-3       # V: SPEC row 108 peak; recovered = within 10 % of the limit by 0.5 t_half

# name: (corner, temp, vdd, dlt, vcm, mut, expect)   expect: "pass" nominal, "reject" broken copy, "info"
POINTS = {
    "tt27_p1": ("tt", 27, 1.80, +1e-3, 1.5, "", "pass"),
    "tt27_m1": ("tt", 27, 1.80, -1e-3, 1.5, "", "pass"),
    "tt27_z":  ("tt", 27, 1.80, 0.0, 1.5, "", "info"),
    "ss40_p1": ("ss", -40, 1.62, +1e-3, 1.5, "", "pass"),
    "ss40_m1": ("ss", -40, 1.62, -1e-3, 1.5, "", "pass"),
    "ss40_z":  ("ss", -40, 1.62, 0.0, 1.5, "", "info"),
    "ss40_p1_cm12": ("ss", -40, 1.62, +1e-3, 1.2, "", "pass"),
    "ss40_m1_cm18": ("ss", -40, 1.62, -1e-3, 1.8, "", "pass"),
    "brk_starve": ("ss", -40, 1.62, +1e-3, 1.5, "starve", "reject"),
    "brk_qswap":  ("ss", -40, 1.62, +1e-3, 1.5, "qswap", "reject"),
    "brk_cl10":   ("ss", -40, 1.62, +1e-3, 1.5, "cl10", "reject"),
}
# PDK mismatch probe: 60 diode-connected instances per type, one .op; broken copy = tt (no mismatch)
MM_TYPES = {  # key: (model, W, L, I, supply, hand sigma range [V] from the PDK vth0 slopes / sqrt(WL))
    "hn": ("nfet_g5v0d10v5", 5.0, 0.5, 10e-6, "va", None),          # vth0_slope = 0 in this PDK (toxe only)
    "hp": ("pfet_g5v0d10v5", 5.0, 0.5, 5e-6, "va", None),
    "ln": ("nfet_01v8", 2.0, 0.5, 5e-6, "vd", (3.356e-3, 7.356e-3)),
    "lp": ("pfet_01v8", 2.0, 0.5, 2e-6, "vd", (4.356e-3, 7.356e-3)),
}
MM_N = 60
MM_POINTS = {"mm_tt": ("tt_mm", "pass"), "brk_mm_off": ("tt", "reject")}


def tran_deck(name, corner, temp, vdd, dlt, vcm, mut):
    cx = C_X2 / 10 if "cl10" in mut else C_X2
    vh = vdd / 2
    tq_sig = "qb" if dlt < 0 else "q"
    f = lambda x: f"{x:.6e}"
    return f"""* C3 spot {name} (WO-44)
.lib {LIB} {corner}
.temp {temp}
{comp_subckt(mut=mut)}
.options method=gear reltol=1e-5 vntol=1e-9 abstol=1e-14
VDDS vdds 0 {vdd}
RVDD vdds vdd 10
CDD vdd 0 2p
VCLK clkr 0 PULSE(0 {vdd} {f(T_FIRE)} 0.1n 0.1n {f(T_HALF - 0.1e-9)} {f(1 / FS)})
RCLK clkr clk 10
VXP sxp 0 {vcm + dlt / 2:.9f}
RXP sxp x2p {R_X2}
CXP x2p 0 {cx}
VXN sxn 0 {vcm - dlt / 2:.9f}
RXN sxn x2n {R_X2}
CXN x2n 0 {cx}
XC x2p x2n clk q qb vdd 0 c3_comp
CQ q 0 {C_Q_LOAD}
CQB qb 0 {C_Q_LOAD}
Bkd kd 0 V=abs(v(x2p)-v(x2n)-({dlt:.9f}))
Bkc kc 0 V=abs((v(x2p)+v(x2n))/2-{vcm})
.ic v(q)={0 if dlt >= 0 else vdd} v(qb)={vdd if dlt >= 0 else 0}
.control
tran 5p {f(TSTOP)} 0 1p
meas tran tq when v({tq_sig})={vh} rise=1 td={f(T_FIRE)}
meas tran tqz when v(q)={vh} rise=1 td={f(T_FIRE)}
meas tran tqbz when v(qb)={vh} rise=1 td={f(T_FIRE)}
meas tran q_end find v(q) at={f(T_RST - 1e-9)}
meas tran qb_end find v(qb) at={f(T_RST - 1e-9)}
meas tran kpk1 max v(kd) from={f(T_FIRE)} to={f(T_RST)}
meas tran krec1 find v(kd) at={f(T_FIRE + T_HALF / 2)}
meas tran kpk2 max v(kd) from={f(T_RST)} to={f(TSTOP)}
meas tran krec2 find v(kd) at={f(T_RST + T_HALF / 2)}
meas tran kcm max v(kc) from={f(T_FIRE)} to={f(TSTOP)}
meas tran qdd integ i(VDDS) from=0 to={f(TSTOP)}
let tend = vecmax(time)
echo "RES tend $&tend"
echo "RES tq $&tq"
echo "RES tqz $&tqz"
echo "RES tqbz $&tqbz"
echo "RES q_end $&q_end"
echo "RES qb_end $&qb_end"
echo "RES kpk1 $&kpk1"
echo "RES krec1 $&krec1"
echo "RES kpk2 $&kpk2"
echo "RES krec2 $&krec2"
echo "RES kcm $&kcm"
echo "RES qdd $&qdd"
.endc
.end
"""


def mm_deck(corner):
    L = [f"* C3 PDK mismatch probe ({corner})", f".lib {LIB} {corner}", ".temp 27",
         "VA va 0 3.3", "VD vd 0 1.8"]
    for k, (model, w, l, i, sup, _) in MM_TYPES.items():
        for n in range(MM_N):
            g = f"g{k}{n}"
            if model.startswith("n"):
                L += [f"I{g} {sup} {g} {i}", f"X{g} {g} {g} 0 0 {PRE}{model} W={w} L={l} nf=1 m=1"]
            else:
                L += [f"I{g} {g} 0 {i}", f"X{g} {g} {g} {sup} {sup} {PRE}{model} W={w} L={l} nf=1 m=1"]
    L += [".control", "op", "print all", ".endc", ".end"]
    return "\n".join(L) + "\n"


def gen(out):
    os.makedirs(out, exist_ok=True)
    jobs = []
    decks = {k: tran_deck(k, *v[:6]) for k, v in POINTS.items()}
    decks.update({k: mm_deck(v[0]) for k, v in MM_POINTS.items()})
    for k, text in decks.items():
        d = os.path.join(os.path.abspath(out), k)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "deck.sp"), "w").write(text)
        open(os.path.join(d, ".spiceinit"), "w").write(SPICEINIT)
        for stale in ("deck.log",):
            if os.path.exists(os.path.join(d, stale)):
                os.remove(os.path.join(d, stale))
        jobs.append(f"cd {d} && timeout 1500 ngspice -b deck.sp > deck.log 2>&1")
    open(os.path.join(out, "jobs.txt"), "w").write("\n".join(jobs) + "\n")
    print(f"{len(jobs)} decks -> {out}/jobs.txt")


def _res(log):
    r = {}
    for ln in open(log, errors="replace"):
        m = re.match(r"RES (\w+) (\S+)", ln.strip())
        if m:
            try:
                r[m.group(1)] = float(m.group(2))
            except ValueError:
                r[m.group(1)] = None
    return r


def collect(out):
    rows, res, bad = [], {}, 0
    for k, (corner, temp, vdd, dlt, vcm, mut, exp) in POINTS.items():
        log = os.path.join(out, k, "deck.log")
        r = _res(log) if os.path.exists(log) else {}
        res[k] = r
        need = ["tend", "q_end", "qb_end", "kpk1", "krec1", "kpk2", "krec2", "kcm", "qdd"]
        miss = [x for x in need if r.get(x) is None]
        ok_end = r.get("tend") is not None and r["tend"] >= TSTOP * (1 - 1e-6)
        checks = {}
        if exp == "info":
            checks["info"] = True
        else:
            tq = r.get("tq")
            tdec = None if tq is None else tq - (T_FIRE + 0.05e-9)
            r["tdec"] = tdec
            hi, lo = 0.9 * vdd, 0.1 * vdd
            want_q = dlt > 0
            pol = (r.get("q_end") is not None and r.get("qb_end") is not None and
                   ((r["q_end"] > hi and r["qb_end"] < lo) if want_q else (r["q_end"] < lo and r["qb_end"] > hi)))
            checks["polarity"] = pol
            checks["t_dec"] = tdec is not None and 0 < tdec < T_DEC_MAX
            checks["kick_peak"] = not miss and max(r["kpk1"], r["kpk2"]) <= KICK_MAX
            checks["kick_rec"] = not miss and max(r["krec1"], r["krec2"]) <= KICK_REC
        verdict = "ACCEPT" if (not miss and ok_end and all(checks.values())) else "REJECT"
        if exp == "pass" and verdict != "ACCEPT" or exp == "reject" and verdict != "REJECT":
            bad += 1
        r["checks"], r["missing"], r["verdict"], r["expect"] = checks, miss, verdict, exp
        if r.get("qdd") is not None:
            r["i_avg_uA"] = abs(r["qdd"]) * FS * 1e6
        rows.append(f"{k:14s} {verdict:6s} exp={exp:6s} tdec={_ns(r.get('tdec'))} "
                    f"kpk={_mv(r.get('kpk1'))}/{_mv(r.get('kpk2'))} krec={_mv(r.get('krec1'))}/{_mv(r.get('krec2'))} "
                    f"kcm={_mv(r.get('kcm'))} q={r.get('q_end')} qb={r.get('qb_end')} tqz={_ns(_sub(r.get('tqz')))} "
                    f"tqbz={_ns(_sub(r.get('tqbz')))} Iavg={r.get('i_avg_uA')} fail={[c for c, v in checks.items() if not v]} miss={miss}")
    for k, (corner, exp) in MM_POINTS.items():
        log = os.path.join(out, k, "deck.log")
        v = {}
        if os.path.exists(log):
            for ln in open(log, errors="replace"):
                m = re.match(r"\s*g(hn|hp|ln|lp)(\d+)\s*=\s*([-+0-9.eE]+)", ln)
                if m:
                    v.setdefault(m.group(1), []).append(float(m.group(3)))
        st, ok = {}, True
        for t, (_, w, l, _, _, rng) in MM_TYPES.items():
            x = v.get(t, [])
            if len(x) != MM_N:
                ok = False
                st[t] = {"n": len(x)}
                continue
            mu = sum(x) / len(x)
            sd = math.sqrt(sum((y - mu) ** 2 for y in x) / (len(x) - 1))
            st[t] = {"n": len(x), "mean": mu, "sigma_mV": sd * 1e3, "avt_mVum": sd * 1e3 * math.sqrt(w * l)}
            if rng is not None:  # 1.8 V devices: sigma(Vgs) within [0.5 lo, 2 hi] of the PDK slope / sqrt(WL)
                h_lo, h_hi = rng[0] / math.sqrt(w * l), rng[1] / math.sqrt(w * l)
                ok &= 0.5 * h_lo <= sd <= 2 * h_hi
        verdict = "ACCEPT" if ok else "REJECT"
        if exp == "pass" and verdict != "ACCEPT" or exp == "reject" and verdict != "REJECT":
            bad += 1
        res[k] = {"stats": st, "verdict": verdict, "expect": exp}
        rows.append(f"{k:14s} {verdict:6s} exp={exp:6s} " + " ".join(
            f"{t}:sig={s.get('sigma_mV', float('nan')):.3f}mV,Avt={s.get('avt_mVum', float('nan')):.2f}" for t, s in st.items()))
    json.dump(res, open(os.path.join(out, "spot.json"), "w"), indent=1, default=str)
    print("\n".join(rows))
    print(f"SUMMARY {'ACCEPT' if bad == 0 else 'REJECT'} ({bad} rows off expectation)")
    sys.exit(1 if bad else 0)


def _sub(t):
    return None if t is None else t - (T_FIRE + 0.05e-9)


def _ns(t):
    return "NA" if t is None else f"{t * 1e9:.3f}ns"


def _mv(x):
    return "NA" if x is None else f"{x * 1e3:.3f}mV"


if __name__ == "__main__":
    {"gen": gen, "collect": collect}[sys.argv[1]](sys.argv[2])
