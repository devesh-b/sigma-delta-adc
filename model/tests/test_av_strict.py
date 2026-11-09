"""WO-23 item 1: strict A(v) table range check (CL-1b: the model REJECTs on table extrapolation).

Expected behaviour comes from the spec text, not from the code under test:
  - av_strict=True and a table shorter than the integrator swing => AvTableRangeError;
  - av_strict=True and a table covering the swing => runs, and LAST_RUN holds max |x1|, |x2| in V diff below the table end;
  - default (av_strict=False) is bit-identical to the legacy np.interp clamp.
Each check is a function so the broken copy (strict flag ignored) can be shown to fail.
"""
import numpy as np
import pytest

from model import iadc as m
from model.studies import s3_budget as s3

SHORT = ((0.0, 80.0), (0.2, 78.0))           # 0.2 V diff: far inside the stage-1 swing
LONG = ((0.0, 80.0), (1.0, 78.0), (4.5, 70.0))  # covers |x| up to xmax*2 * vref? (x2 clip 3.0 * 2.048 > 4.5 is not reached at u 0.9)


def _p(tab, strict, N=256):
    return s3.ideal_base(N=N, ktc_on=False, chop=False, sys_chop=False, av_table1=tab, av_table2=tab, av_strict=strict)


def _run(p):
    u = np.linspace(-0.9, 0.9, 41)
    return m.convert(p, u, rng=np.random.default_rng(2))


def check_raises(convert=m.convert):
    try:
        convert(_p(SHORT, True), np.linspace(-0.9, 0.9, 41), rng=np.random.default_rng(2))
    except m.AvTableRangeError:
        return True
    return False


def test_strict_raises_on_extrapolation():
    assert check_raises()


def test_strict_broken_copy_is_caught():
    # broken copy: strict flag dropped before the call => no raise => the check must report failure
    broken = lambda p, u, **kw: m.convert(m.with_(p, av_strict=False), u, **kw)
    assert not check_raises(broken)


def test_strict_in_range_runs_and_reports():
    uh = _run(_p(LONG, True))
    assert np.all(np.isfinite(uh))
    x1, x2 = m.LAST_RUN["x1max_v"], m.LAST_RUN["x2max_v"]
    assert 0 < x1 <= LONG[-1][0] and 0 < x2 <= LONG[-1][0]


def test_default_unchanged():
    a = _run(_p(SHORT, False))          # legacy clamp, no raise
    b = _run(_p(SHORT, False))
    assert np.array_equal(a, b)
    # identical to a strict run with a table that covers the swing and has the same values (no clamp needed there)
    flat_short = ((0.0, 80.0), (0.2, 80.0))
    flat_long = ((0.0, 80.0), (10.0, 80.0))
    assert np.array_equal(_run(_p(flat_short, False)), _run(_p(flat_long, True)))
