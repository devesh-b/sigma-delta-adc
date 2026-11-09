"""WO-22 item 3: tier-0 INL vs OTA1/OTA2 A0 for the CL-1 boost floor (fast mode N 1024, precision cross-check N 4096).
Table shape = S4 worst-corner shape anchored at A0 (|Vout| 0/1.4/2.0/3.1 V -> A0, A0-5, A0-10, A0-20 dB), i.e. CL-1 'A0 and A0-5 dB for A(v)'.
Also flat A0 and flat A0-5 for reference. fs 4 MHz; finite gain INL is fs independent in the model. Prints a markdown table."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import iadc as m
import s1_vref as s1
import s3_budget as s3

SHAPE = ((0.0, 0.0), (1.4, -5.0), (2.0, -10.0), (3.1, -20.0))


def inl(a0, shape, N):
    tab = tuple((v, a0 + d) for v, d in shape)
    p = s3.ideal_base(fs=4e6, N=N, a0_db=np.inf, av_table1=tab, av_table2=tab)
    return s1.inl_v2(m.with_(p, ktc_on=False, flicker_on=False), N, True)["inl_ppm"]


if __name__ == "__main__":
    flat0 = tuple((v, 0.0) for v in (0.0, 3.1))
    flat5 = tuple((v, -5.0 if v else 0.0) for v in (0.0, 0.01, 3.1))
    flat5 = ((0.0, -5.0), (3.1, -5.0))
    print("| A0 dB | N1024 S4 shape | N1024 flat A0 | N1024 flat A0-5 | N4096 S4 shape | N4096 flat A0 | N4096 flat A0-5 |\n|---|---|---|---|---|---|---|")
    for a in (60, 64, 68, 72, 76, 80, 84, 88, 92):
        r = [inl(a, sh, N) for N in (1024, 4096) for sh in (SHAPE, flat0, flat5)]
        print(f"| {a} | " + " | ".join(f"{x:.3f}" for x in r[:3] + r[3:]) + " |")
