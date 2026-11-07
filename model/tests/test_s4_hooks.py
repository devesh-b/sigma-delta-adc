"""WO-06 iadc hooks: OTA2 gain, A(v) table, ref-pin R_ext, reset memory (all default off).

Expected values come from theory / the S3 review, not from the code under test:
  - R_ext: INL ~ 1.4 ppm at 10 ohm, ~7 ppm at 50 ohm (review S3-7a, +-30 %); u^3 shape, INL proportional to R
  - reset memory: offset 2 r x1_prev / (c1 (N-1))
  - table: a flat table is the constant-gain OTA; a table sampled from A0 (1 - drop (v/vlin)^2) is that OTA
Each check is a function returning (ok, text) so that the same function is run on a deliberately broken copy
(the hook silently ignored) and must return not ok.
"""
import numpy as np
import pytest

from model import iadc as m
from model.studies import s1_vref as s1
from model.studies import s3_budget as s3


def _ideal(**kw):
    return s3.ideal_base(ktc_on=False, chop=False, sys_chop=False, **kw)


def _sweep(p, npts=161, umax=0.9):
    u = np.linspace(-umax, umax, npts)
    return u, m.convert(p, u, rng=np.random.default_rng(2))


# ---------------------------------------------------------------- (a) OTA2 gain
def check_a0_db2(mut=lambda p: p):
    base = _ideal(N=1024)
    u, ideal = _sweep(base)
    u, st1 = _sweep(mut(m.with_(base, a0_db=40.0, a0_db2=np.inf)))       # only OTA1 leaky
    u, st2 = _sweep(mut(m.with_(base, a0_db=np.inf, a0_db2=40.0)))       # only OTA2 leaky
    u, both = _sweep(m.with_(base, a0_db=40.0))
    u, same = _sweep(m.with_(base, a0_db=40.0, a0_db2=40.0, a0_drop2=0.0))
    ok = (np.max(np.abs(st2 - ideal)) > 1e-7                       # OTA2 gain alone matters
          and np.max(np.abs(st1 - st2)) > 1e-7                     # stages are separate
          and np.array_equal(both, same))                         # default a0_db2=None == same as OTA1
    return ok, f"|ota2-only - ideal| {np.max(np.abs(st2 - ideal)):.2e}, |ota1-only - ota2-only| {np.max(np.abs(st1 - st2)):.2e}"


def test_a0_db2():
    ok, t = check_a0_db2()
    assert ok, t


def test_a0_db2_broken_copy_fails():
    # broken copy: a0_db2 ignored (None) => OTA2 stays ideal, check must fail
    ok, _ = check_a0_db2(lambda p: m.with_(p, a0_db2=None) if p.a0_db2 is not None and not np.isfinite(p.a0_db) else p)
    assert not ok


# ---------------------------------------------------------------- (b) A(v) table
VLIN, DROP, A0 = 2.0, 0.9, 80.0


def _table_from_quadratic():
    v = np.linspace(0.0, 3.1, 311)
    a = A0_lin() * np.maximum(0.02, 1.0 - DROP * (v / VLIN) ** 2)
    return tuple((float(x), float(20 * np.log10(y))) for x, y in zip(v, a))


def A0_lin():
    return 10 ** (A0 / 20)


def check_table(mut=lambda p: p):
    base = _ideal(N=1024)
    u, flat_ref = _sweep(m.with_(base, a0_db=A0))
    u, flat_tab = _sweep(mut(m.with_(base, a0_db=np.inf, av_table1=((0.0, A0), (3.0, A0)), av_table2=((0.0, A0), (3.0, A0)))))
    u, quad_ref = _sweep(m.with_(base, a0_db=A0, a0_drop=DROP, vlin_diff=VLIN))
    tab = _table_from_quadratic()
    u, quad_tab = _sweep(mut(m.with_(base, a0_db=np.inf, av_table1=tab, av_table2=tab)))
    u, bad_tab = _sweep(mut(m.with_(base, a0_db=np.inf, av_table1=((0.0, 80.0), (1.4, 60.0), (3.0, 50.0)),
                                    av_table2=((0.0, 80.0), (1.4, 60.0), (3.0, 50.0)))))
    inl = lambda uh: m.linearity(u, uh)["inl_ppm"]
    ok = (np.max(np.abs(flat_tab - flat_ref)) < 1e-9                    # flat table == constant-gain OTA
          and abs(inl(quad_tab) - inl(quad_ref)) < 0.02 * inl(quad_ref)  # tabulated quadratic == quadratic drop
          and inl(bad_tab) > 3 * inl(flat_ref) + 1.0)                    # a table that drops to 60 dB at 1.4 V is worse
    return ok, f"flat diff {np.max(np.abs(flat_tab - flat_ref)):.1e}; INL quad {inl(quad_ref):.3f} vs table {inl(quad_tab):.3f}; 60 dB table {inl(bad_tab):.2f}"


def test_av_table():
    ok, t = check_table()
    assert ok, t


def test_av_table_broken_copy_fails():
    ok, _ = check_table(lambda p: m.with_(p, av_table1=None, av_table2=None))
    assert not ok


def test_table_holds_end_values_and_interpolates_db():
    # |x| = 1 normalised at vref 2.048 V is 2.048 V; midpoint of (1.0 V, 60 dB)-(3.0 V, 40 dB) at 2.0 V is 50 dB
    p, g = m._leaky(0, 0.125, np.array([1.0]), table=((1.0, 60.0), (3.0, 40.0)), vref=2.0)
    a = 50.0
    A = 10 ** (a / 20)
    assert np.isclose(g[0], 1.0 / (1.0 + 1.125 / A))
    p0, g0 = m._leaky(0, 0.125, np.array([0.0]), table=((1.0, 60.0), (3.0, 40.0)), vref=2.0)
    assert np.isclose(g0[0], 1.0 / (1.0 + 1.125 / 10 ** 3))          # held at 60 dB below the first node


# ---------------------------------------------------------------- (c) R_ext on reference pins
def check_rext(mut=lambda p: p):
    out = {}
    for R in (10.0, 50.0):
        p = mut(_ideal(N=4096, r_ext_ref=R))
        out[R] = s1.inl_v2(p, 4096, True)["inl_ppm"]
    ok = (0.7 * 1.4 <= out[10.0] <= 1.3 * 1.4) and (0.7 * 7.0 <= out[50.0] <= 1.3 * 7.0) and (4.5 <= out[50.0] / out[10.0] <= 5.5)
    return ok, f"INL {out[10.0]:.2f} ppm @10 ohm (theory 1.4), {out[50.0]:.2f} @50 ohm (theory 7)"


def test_rext_inl():
    ok, t = check_rext()
    assert ok, t


def test_rext_broken_copy_fails():
    ok, _ = check_rext(lambda p: m.with_(p, r_ext_ref=0.0))
    assert not ok


def test_rext_default_off_identical():
    p = _ideal(N=256)
    u = np.linspace(-0.9, 0.9, 41)
    assert np.array_equal(m.convert(p, u), m.convert(m.with_(p, r_ext_ref=0.0), u))


# ---------------------------------------------------------------- (d) inter-conversion memory
def check_memory(mut=lambda p: p, r=0.1, N=256, n=1000):
    p = _ideal(N=N)
    rng = np.random.default_rng(7)
    u = rng.uniform(-0.9, 0.9, n)
    uh0, st0 = m.convert(p, u, return_state=True)                   # independent conversions (reset_r = 0)
    uhr, _ = m.convert(mut(m.with_(p, reset_r=r)), u, return_state=True)
    d = (uhr - uh0)[1:]
    pred = 2 * r * st0["x1_final"][:-1] / (p.c1 * (N - 1))          # theory: 2 r x1_prev / (c1 (N-1))
    slope = float(np.sum(d * pred) / np.sum(pred * pred))
    first_same = bool(uhr[0] == uh0[0])                             # first conversion of the chain starts from zero
    ok = 0.85 <= slope <= 1.15 and first_same
    return ok, f"slope of (u_hat_mem - u_hat_0) on 2 r x1_prev/(c1(N-1)) = {slope:.3f} (theory 1), first conversion unaffected {first_same}"


def test_memory():
    ok, t = check_memory()
    assert ok, t


def test_memory_broken_copy_fails():
    ok, _ = check_memory(lambda p: m.with_(p, reset_r=0.0))
    assert not ok


def test_memory_default_off_identical_and_chain_matches_loop():
    p = _ideal(N=128)
    u = np.linspace(-0.9, 0.9, 20)
    assert np.array_equal(m.convert(p, u), m.convert(m.with_(p, reset_r=0.0), u))
    # chain with 2 chains of L=2 equals the sequential batch for each chain
    q = m.with_(p, reset_r=0.2)
    U = np.array([[0.5, 0.1], [-0.7, 0.3]])
    ch = m.convert_chain(q, U)
    for c in range(2):
        assert np.array_equal(ch[c], m.convert(q, U[c]))


# ---------------------------------------------------------------- legacy configs unchanged
GOLDEN_SHA256 = "a20759418171ca17354d28f548701f6a44b18b8d3909ae07f415c22667606361"   # computed with iadc.py at commit bd93ecf (before the hooks)


def _legacy_digest():
    import hashlib
    base = dict(order=2, N=256, fs=2e6, vref=2.048, c1=0.125, c2=0.5, k=0.5, cs=0.5e-12)
    cfgs = [dict(), dict(a0_db=75, a0_drop=0.9, vlin_diff=2.0), dict(a0_db=80, a0_drop=0.5),
            dict(ktc_on=True, flicker_on=True, vos=3e-3, vos2=2e-3, chop=True, sys_chop=True, vres=5e-6, ref_mode="separate", tau_in=20e-9, tau_ref=10e-9),
            dict(comp_offset=0.01, comp_noise=0.002, x1_offset=1e-3, tau_in=18e-9, tau_ref=5e-9, cd_ref=5e-12, ref_mode="shared", a0_db=70),
            dict(order=1, a0_db=60)]
    h = hashlib.sha256()
    for c in cfgs:
        p = m.Params(**{**base, **c})
        u = np.linspace(-0.9, 0.9, 33)
        nz = m.ota_noise_block(p, 33, np.random.default_rng(1)) if (p.flicker_on or p.vos) else None
        sg = np.where(np.arange(33) % 2 == 0, 1.0, -1.0) if p.sys_chop else None
        uh, st = m.convert(p, u, rng=np.random.default_rng(3), ota_noise=nz, sys_sign=sg, return_state=True)
        h.update(uh.tobytes()); h.update(st["x1_final"].tobytes()); h.update(st["x2_final"].tobytes())
    return h.hexdigest()


def test_legacy_outputs_bit_identical():
    assert _legacy_digest() == GOLDEN_SHA256
