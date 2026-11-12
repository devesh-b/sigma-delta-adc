"""WO-53: order1_delay (D76). Independent integer reference of y[n+1] = sign(x1[n]); default unchanged; non-vacuity."""
import numpy as np

from model import iadc as m

C1 = 0.125


def ref_bits(N, u, delay):
    x1 = 0.0; xp = 0.0; ys = []
    for n in range(N):
        q = xp if delay else x1
        y = 1.0 if q >= 0 else -1.0
        ys.append(y)
        xp = x1
        x1 = x1 + C1 * (u - y)
    return np.array(ys)


def conv(N, u, delay):
    p = m.Params(order=1, N=N, c1=C1, c2=0.5, k=0.5, xmax=1e6, order1_delay=delay)
    return m.convert(p, np.array(u), return_state=True)


def test_delay_matches_reference_bits():
    us = [-0.9, -0.3, 0.0, 0.2, 0.77]
    _, st = conv(256, us, True)
    for i, u in enumerate(us):
        assert np.array_equal(st["y"][:, i], ref_bits(256, u, True))


def test_default_is_legacy_and_differs_from_delay():
    us = [-0.5, 0.123, 0.6]
    p0 = m.Params(order=1, N=256, c1=C1, c2=0.5, k=0.5, xmax=1e6)
    assert p0.order1_delay is False
    _, s0 = m.convert(p0, np.array(us), return_state=True)
    for i, u in enumerate(us):
        assert np.array_equal(s0["y"][:, i], ref_bits(256, u, False))
    _, s1 = conv(256, us, True)
    assert not np.array_equal(s0["y"], s1["y"])        # non-vacuity: the flag changes the bitstream


def test_order2_unaffected():
    p = m.Params(order=2, N=64, c1=C1, c2=0.5, k=0.5, xmax=1e6)
    u = np.array([0.3, -0.7])
    a, _ = m.convert(p, u, return_state=True)
    b, _ = m.convert(m.with_(p, order1_delay=True), u, return_state=True)
    assert np.array_equal(a, b)
