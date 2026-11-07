#!/usr/bin/env python3
"""S2 theory: residual offset of OTA chopping / system chopping in an
incremental sigma-delta with cascade-of-integrators (CoI) reconstruction.

INDEPENDENT of iadc.py: this is the expected-value source for s2_chop.py.

Derivation (order 2, loop as in SPEC 3.2: x1 += c1(u+e-y), x2 += c2(x1 - k y)):
  x2[N] = c1 c2 sum_m (N-1-m)(u_m + e_m - y_m) - c2 k sum_m y_m
  Setting the residual state x2[N] ~ 0 gives the reconstruction
      sum_m w_m y_m + (k/c1) sum y = sum_m w_m (u_m + e_m),  w_m = N-1-m
  so u_hat = sum w_m (u_m+e_m) / sum w_m, sum w_m = N(N-1)/2.
  An input-referred error e_m therefore enters with weight w_m / sum(w).
  Order 1: weights are equal (w_m = 1).

Offset Vos (input-referred to the first integrator, times lf_gain) with OTA
chop ((-1)^m, m = 0 at the first cycle after reset):
  residual = lf * Vos * sum (-1)^m w_m / sum w_m
  order 2, N even: pairs (N-1-2j) - (N-2-2j) = 1, N/2 pairs -> (N/2)/(N(N-1)/2)
                   = 1/(N-1)
  order 2, N odd : (N-1)/2 / (N(N-1)/2) = 1/N
  order 1, N even: 0 ;  N odd: 1/N
The unchopped residual vres (from the chopper itself) is not alternated: it
passes with weight 1.
System chop (input polarity swapped between two sub-conversions, offset NOT
swapped): out_i = u + s_i * off, mean of the two = u + (off_1 - off_2)/2 -> 0
when the offset is identical in both sub-conversions (including the OTA-chop
phase restart at each reset, or N even).
"""
import numpy as np


def weights(order, N):
    n = np.arange(N)
    return (N - 1 - n).astype(float) if order == 2 else np.ones(N)


def kernel_brute(order, N):
    """sum (-1)^n w_n / sum w_n by direct summation."""
    w = weights(order, N)
    return float(np.sum(w * (-1.0) ** np.arange(N)) / np.sum(w))


def kernel_closed(order, N):
    if order == 2:
        return 1.0 / (N - 1) if N % 2 == 0 else 1.0 / N
    return 0.0 if N % 2 == 0 else 1.0 / N


def e2_error(N, c1, e2_v):
    """Input-referred output error [V] of a constant offset e2_v [V] at the
    input of integrator 2 (OTA2 input offset, or a constant offset on x1).
    Order 2, x2 += c2 (x1 - k y + e2/vref): zeroing x2[N] gives
      sum w y + (k/c1) sum y = sum w u + N e2/c1  ->  u_err = N e2 / (c1 N(N-1)/2)
    = 2 e2 / (c1 (N-1)) (in volts, independent of VREF). Not cancelled by OTA
    chop (constant); cancelled by system chop (same sign in both polarities
    after the output sign flip, so it averages out in a pair)."""
    return 2.0 * e2_v / (c1 * (N - 1))


def order1_residue(N, vos, lf):
    """Order 1, OTA chop only [V]: lf*Vos/N for N even, 0 for N odd.
    u_hat = sum(y)/N = u + mean(e) - x1[N]/(c1 N). The equal-weight mean of the
    chopped offset is 0 (N even) or Vos/N (N odd). The final-state term
    -x1[N]/(c1 N) ~ -e_{N-1}/N: the last cycle's chopped offset (-Vos for N even,
    +Vos for N odd) is not yet integrated out, the same effect as a comparator
    offset of c1*Vos. Even: 0 + Vos/N. Odd: Vos/N - Vos/N = 0.
    (The chip has no x1[N]; this is NOT corrected in the output.)"""
    return lf * vos / N if N % 2 == 0 else 0.0


def predict(order, N, mode, vos, vres, lf):
    """Expected mean input-referred offset [V] for a mode in
    {none, ota, sys, ota+sys}. vos, vres in volts."""
    if mode in ("sys", "ota+sys"):
        return 0.0
    if mode == "none":
        return lf * (vos + vres)
    return lf * (vos * kernel_closed(order, N) + vres)       # ota only


if __name__ == "__main__":
    ok = True
    print("OTA-chop-only residual factor r(N) = sum(-1)^n w_n / sum w_n  (offset = lf*Vos*r + lf*vres)")
    print(f"{'N':>6} {'ord2 closed':>12} {'ord2 brute':>12} {'N*r2':>8} {'ord1 closed':>12} {'ord1 brute':>12}"
          f" {'Vos=9mV,lf=1 ord2 [uV]':>24}")
    for N in (64, 128, 256, 512, 1024, 2048, 4096):
        c2, b2 = kernel_closed(2, N), kernel_brute(2, N)
        c1, b1 = kernel_closed(1, N), kernel_brute(1, N)
        if abs(c2 - b2) > 1e-12 or abs(c1 - b1) > 1e-12:
            ok = False
        print(f"{N:6d} {c2:12.4e} {b2:12.4e} {N*c2:8.4f} {c1:12.1e} {b1:12.1e} {9e-3*c2*1e6:24.2f}")
    # 1/N scaling: doubling N halves the residual (order 2)
    scal = all(abs(kernel_closed(2, 2 * N) * (2 * N - 1) - 1) < 1e-12 for N in (64, 256, 1024))
    ok &= scal
    print("sys / ota+sys : 0 (offset identical in both sub-conversions)")
    print("residual ~ 1/(N-1) for order 2 (checked):", scal)
    print("ACCEPT" if ok else "REJECT")
    raise SystemExit(0 if ok else 1)
