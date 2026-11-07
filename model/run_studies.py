"""Phase-1 system studies for the TT sky130 incremental ΣΔ ADC.

Usage:  python run_studies.py [quant|gain|noise|settle|design|all]
Writes figures and out/report_<study>.md into model/out/.
"""

import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import iadc as m

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
BASE = m.Params()
MCP_RATES = [240, 60, 15, 3.75]            # MCP3421 modes (SPS)
MCP_BITS = {240: 12, 60: 14, 15: 16, 3.75: 18}


def md_table(header, rows):
    s = "| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n"
    for r in rows:
        s += "| " + " | ".join(str(x) for x in r) + " |\n"
    return s


def write(name, text):
    (OUT / f"report_{name}.md").write_text(text)
    print(text)


# --------------------------------------------------------------------- quant
def study_quant():
    """Ideal quantisation-limited resolution vs N and order."""
    Ns = [64, 128, 256, 512, 1024, 2048, 4096, 8192]
    rows, res = [], {1: [], 2: []}
    for order in (1, 2):
        for N in Ns:
            p = m.with_(BASE, order=order, N=N, xmax=100)
            u, uh, st = m.dc_sweep(p, umax=0.9, npts=801)
            b = m.resolution_bits(np.max(np.abs(uh - u)))
            res[order].append(b)
            rows.append([order, N, f"{1e6 / N:.0f}", f"{b:.1f}",
                         f"{st['x1max']:.2f}", f"{st['x2max']:.2f}"])
    plt.figure(figsize=(6, 4))
    for order in (1, 2):
        plt.semilogx(Ns, res[order], "o-", base=2, label=f"order {order}")
    plt.xlabel("N cycles per conversion"); plt.ylabel("quantisation-limited bits")
    plt.grid(True, which="both", alpha=.3); plt.legend(); plt.title("Ideal incremental ΣΔ, |u|≤0.9")
    plt.tight_layout(); plt.savefig(OUT / "quant.png", dpi=120); plt.close()
    txt = "# Study: quantisation vs N\n\nIdeal loop, c1=0.25 c2=0.5 k=1, 801-point DC sweep over ±0.9·VREF. " \
          "Bits = log2(1/max|err|) (peak error = ½ LSB over FSR 2).\n\n"
    txt += md_table(["order", "N", "rate @1 MHz", "bits", "max|x1|", "max|x2|"], rows)
    txt += "\n![](quant.png)\n"
    write("quant", txt)


# ---------------------------------------------------------------------- gain
def study_gain():
    """Finite OTA DC gain -> INL / gain error, order 2."""
    gains = [50, 60, 70, 80, 90, 100, 120]
    Ns = [256, 1024, 4096]
    rows = []
    plt.figure(figsize=(6, 4))
    for N in Ns:
        inls = []
        for a in gains:
            p = m.with_(BASE, N=N, a0_db=a)
            u, uh, _ = m.dc_sweep(p, umax=0.9, npts=401)
            lin = m.linearity(u, uh)
            inls.append(lin["inl_ppm"])
            rows.append([N, a, f"{lin['inl_ppm']:.1f}", f"{lin['gain_err_ppm']:.0f}",
                         f"{lin['offset_ppm']:.1f}"])
        plt.semilogy(gains, inls, "o-", label=f"N={N}")
    plt.axhline(100, ls="--", c="gray"); plt.axhline(10, ls=":", c="gray")
    plt.xlabel("OTA DC gain A0 [dB]"); plt.ylabel("INL [ppm FSR] (incl. quantisation)")
    plt.grid(True, which="both", alpha=.3); plt.legend(); plt.title("Finite gain, order 2")
    plt.tight_layout(); plt.savefig(OUT / "gain.png", dpi=120); plt.close()
    txt = "# Study: OTA DC gain\n\nOrder 2, both OTAs at A0, no noise. INL is endpoint-fit over ±0.9·VREF and " \
          "includes quantisation error (floor at high A0). Gain error is linear and calibratable.\n\n"
    txt += md_table(["N", "A0 dB", "INL ppm", "gain err ppm", "offset ppm"], rows)
    txt += "\n![](gain.png)\n"

    # swing-dependent gain: the realistic INL mechanism
    rows2 = []
    plt.figure(figsize=(6, 4))
    for drop in (0.5, 0.9, 0.99):
        inls = []
        for a in gains:
            p = m.with_(BASE, N=1024, a0_db=a, a0_drop=drop, xswing=1.2)
            u, uh, _ = m.dc_sweep(p, umax=0.9, npts=401)
            lin = m.linearity(u, uh)
            inls.append(lin["inl_ppm"])
            rows2.append([f"{drop:g}", a, f"{lin['inl_ppm']:.1f}", f"{lin['gain_err_ppm']:.0f}"])
        plt.semilogy(gains, inls, "o-", label=f"gain loss {drop:.0%} at full swing")
    plt.axhline(100, ls="--", c="gray"); plt.axhline(10, ls=":", c="gray")
    plt.xlabel("OTA DC gain A0 at mid-swing [dB]"); plt.ylabel("INL [ppm FSR]")
    plt.grid(True, which="both", alpha=.3); plt.legend(); plt.title("Swing-dependent gain, order 2, N=1024")
    plt.tight_layout(); plt.savefig(OUT / "gain_swing.png", dpi=120); plt.close()
    txt += ("\n## Swing-dependent gain (realistic)\n\nA(x) = A0·(1 − drop·(x/1.2)²), N=1024. "
            "drop=0.9 means the OTA keeps only 10 % of its gain at the edge of the integrator swing.\n\n")
    txt += md_table(["drop", "A0 dB", "INL ppm", "gain err ppm"], rows2)
    txt += "\n![](gain_swing.png)\n"
    write("gain", txt)


# --------------------------------------------------------------------- noise
NOISE_CASES = [
    # label, overrides
    ("kT/C only", dict(ktc_on=True)),
    ("kT/C + 1/f, no chop", dict(ktc_on=True, flicker_on=True)),
    ("kT/C + 1/f + 3 mV offset, no chop", dict(ktc_on=True, flicker_on=True, vos=3e-3)),
    ("+ system chop", dict(ktc_on=True, flicker_on=True, vos=3e-3, sys_chop=True)),
    ("+ OTA chop (fs/2), 5 µV residual", dict(ktc_on=True, flicker_on=True, vos=3e-3, chop=True, vres=5e-6)),
    ("+ OTA chop + system chop", dict(ktc_on=True, flicker_on=True, vos=3e-3, chop=True, vres=5e-6,
                                     sys_chop=True)),
]


def study_noise(fs_list=(1e6, 2e6), N=1024, cs=1e-12, m_out=24, lf_gains=(1.0, BASE.noise_gain)):
    rows = []
    for lf in lf_gains:
        for fs in fs_list:
            for label, ov in NOISE_CASES:
                for rate in MCP_RATES:
                    rows.append(_noise_row(lf, fs, label, ov, rate, N, cs, m_out))
    txt = (f"# Study: noise and offset\n\nOrder 2, N={N}, Cs={cs * 1e12:g} pF/side, c1=0.25, OTA white "
           "6.9 nV/√Hz, 1/f corner 631 kHz (pthomas sky130 measurement). `lf gain` = input referral of slow "
           f"OTA errors: 1 for bottom-plate SC (expected), {BASE.noise_gain:.2f} = pessimistic bound. Each output = "
           f"mean of K consecutive sub-conversions; rms over {m_out} outputs. Effective resolution = "
           "log2(4.096 V / rms). Mean = residual offset (the ~−2 µV floor is deterministic quantisation error at "
           "the 0.1·VREF test input). MCP3421 column: its no-missing-codes bits at that rate (its noise is "
           "1.5 µV at 3.75 SPS).\n\n")
    txt += md_table(["lf gain", "fs MHz", "case", "rate SPS", "K", "rms µV", "eff. res. bits", "offset µV",
                     "MCP3421 bits"], rows)
    write("noise", txt)


def _noise_row(lf, fs, label, ov, rate, N, cs, m_out):
    p = m.with_(BASE, fs=fs, N=N, cs=cs, lf_gain=lf, **ov)
    k_avg = max(1, round(fs / (rate * N)))
    t0 = time.time()
    r = m.measure_noise(p, k_avg, m_out=m_out)
    print(f"  lf={lf:.2f} fs={fs:g} {label:40s} rate={r['rate']:.2f} rms={r['rms_v'] * 1e6:.2f}uV "
          f"({time.time() - t0:.1f}s)", flush=True)
    return [f"{lf:.2f}", f"{fs / 1e6:g}", label, f"{r['rate']:.2f}", r["k_avg"],
            f"{r['rms_v'] * 1e6:.2f}", f"{m.eff_res_bits(r['rms_v']):.1f}",
            f"{r['mean_v'] * 1e6:.1f}", MCP_BITS[rate]]


# -------------------------------------------------------------------- settle
def study_settle():
    """Input / reference incomplete settling -> INL, shared vs separate caps."""
    ratios = [0.02, 0.05, 0.08, 0.1, 0.15, 0.2]       # tau / t_half
    rows = []
    for fs in (1e6, 2e6):
        for mode in ("shared", "separate"):
            for which in ("tau_in", "tau_ref"):
                for r in ratios:
                    p = m.with_(BASE, fs=fs, N=1024, ref_mode=mode)
                    p = m.with_(p, **{which: r * p.t_half})
                    u, uh, _ = m.dc_sweep(p, umax=0.9, npts=201)
                    lin = m.linearity(u, uh)
                    tau = r * p.t_half
                    hint = ""
                    if which == "tau_in":
                        hint = f"{tau / (p.cs + 5e-12) / 1e3:.1f} kΩ"
                    else:
                        hint = f"{tau / p.cd_ref:.0f} Ω"
                    rows.append([f"{fs / 1e6:g}", mode, which, f"{r:.2f}", f"{tau * 1e9:.0f}", hint,
                                 f"{lin['inl_ppm']:.1f}", f"{lin['gain_err_ppm']:.0f}"])
    txt = ("# Study: settling (input source / reference)\n\nOrder 2, N=1024. τ is the sampling/recovery time "
           "constant; t_half = 0.45/fs. `shared`: one Cs samples Vin then ±VREF (input sees the previous ±VREF "
           "→ signal-dependent). `separate`: Cin and Cref reset to CM each cycle. Equivalent R: τ_in over "
           "(Cs + 5 pF pad), τ_ref over the 20 pF ref decap. INL includes the quantisation floor (~16 b).\n\n")
    txt += md_table(["fs MHz", "caps", "which", "τ/t_half", "τ ns", "equiv. R", "INL ppm", "gain err ppm"], rows)
    write("settle", txt)


# -------------------------------------------------------------------- design
def study_design():
    """Candidate v1 point vs MCP3421 modes."""
    p0 = m.with_(BASE, fs=2e6, N=1024, cs=1e-12, a0_db=75, a0_drop=0.9, ktc_on=True, flicker_on=True, vos=3e-3,
                 chop=True, vres=5e-6, sys_chop=True, ref_mode="separate", tau_in=20e-9, tau_ref=10e-9)
    u, uh, _ = m.dc_sweep(m.with_(p0, ktc_on=False, flicker_on=False, vos=0, vres=0), umax=0.9, npts=401)
    lin = m.linearity(u, uh)
    rows = []
    for rate in MCP_RATES:
        k_avg = max(1, round(p0.fs / (rate * p0.N)))
        r = m.measure_noise(p0, k_avg, m_out=24)
        rows.append([rate, f"{r['rate']:.2f}", r["k_avg"], f"{r['rms_v'] * 1e6:.2f}",
                     f"{m.eff_res_bits(r['rms_v']):.1f}", f"{r['mean_v'] * 1e6:.1f}", MCP_BITS[rate]])
    txt = ("# Candidate v1 design point\n\n"
           f"fs={p0.fs / 1e6:g} MHz, order 2, N={p0.N}, Cs=1 pF, A0={p0.a0_db} dB at mid-swing (90 % gain loss at full swing), OTA chop + system chop, "
           "separate input/ref caps, τ_in=20 ns, τ_ref=10 ns, 3 mV OTA offset, 5 µV chopper residual. `error @0.1·VREF` = mean output error at the test input, dominated by the (calibratable) gain error.\n\n"
           f"**Static: INL {lin['inl_ppm']:.1f} ppm FSR, gain error {lin['gain_err_ppm']:.0f} ppm "
           f"(calibratable), offset {lin['offset_ppm']:.1f} ppm.**\n\n")
    txt += md_table(["MCP3421 rate", "our rate", "K", "rms µV", "eff. res. bits", "error @0.1·VREF µV",
                     "MCP3421 bits"], rows)
    write("design", txt)


STUDIES = {"quant": study_quant, "gain": study_gain, "noise": study_noise,
           "settle": study_settle, "design": study_design}

if __name__ == "__main__":
    which = sys.argv[1:] or ["all"]
    for name in (STUDIES if which == ["all"] else which):
        t = time.time()
        print(f"=== {name}")
        STUDIES[name]()
        print(f"=== {name} done in {time.time() - t:.0f}s\n")
