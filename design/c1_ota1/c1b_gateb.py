#!/usr/bin/env python3
"""C1b gate B (WO-24 item 4, REVIEW-C1a-revC Q4): tier-1 modulator deck with the NETLISTED OTA1 (netlist.py, real SC
CMFB, cmfb="sc") and the behavioural OTA2, fs/125/3.0 boost, fs 4 MHz, C_FOLD_EXTRA = 0. Sandbox only:
    python c1b_gateb.py OUTDIR --opt O1 --n 1024 --m 21 [--copy nom|sr95] [--corner 3] [--part i/k]

OTA2 at the WO-22 hot point (GBW2 22.5 MHz, SR2 27 V/us, fp2_mult2 3, absolute values: bst1 = bst2 = 1).
Gate: INL(endpoint) <= 5 ppm at 4 MHz boost; also reported against 3.33 ppm (5/1.5). Expected values from SPEC 3.0 /
CL-1b, not from this code. Broken copy --copy sr95: tail reference scaled so the boost SR is 9.5 V/us at 1.4 pF
(scale from the REAL integrate-phase load, see sr95_scale; all six bias ports scaled together) -> must REJECT. Chopper static (chp/chlp high). --part i/k runs the i-th of k slices of the u grid
(endpoints kept in every slice so each slice has its own endpoint line; combine with combine()).
"""
import argparse, ast, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, ".."), os.path.join(HERE, "..", "tier1")]
import numpy as np  # noqa: E402
import params as P  # noqa: E402
import sizes_draft as S  # noqa: E402
import netlist as NL  # noqa: E402
import tier1_tb as TB  # noqa: E402
from revc_check import CORNERS9, LIB  # noqa: E402

GATE, GATE_SHARE = 5.0, 5.0 / 1.5
C_OUT_EXT = 0.02e-12
# REVIEW-C1b M2: the real integrate-phase load, not the 1.4 pF spec basis: Cint1 (1 - beta1) + Cc + output routing (~0.84-0.86 pF)
C_INT_PHASE = P.CINT1 * (1.0 - S.BETA1) + S.C_CMFB_SENSE + C_OUT_EXT
SR95_SCALE = 9.5e6 * C_INT_PHASE / (S.I_TAIL * S.BOOST)   # ~0.22: ALL six bias ports scale together (op point stays consistent)
AUDIT_TYPES = {"X", "I"}   # the audit inventories behavioural parts only: allow exactly the netlisted-OTA element types
AUDIT_TOKENS = (".lib", ".include", "subckt", "sky130", "nfet", "pfet")


def audit_expected(msg):
    """True only for the two audit messages the netlisted OTA1 deck is expected to trigger (element types within {X, I},
    or one of the specific netlist tokens). Everything else stays a problem."""
    if msg.startswith("unexpected element types"):
        try:
            return set(ast.literal_eval(msg.split("types", 1)[1].strip())) <= AUDIT_TYPES
        except Exception:
            return False
    if msg.startswith("banned token"):
        return msg.split("token", 1)[1].strip() in AUDIT_TOKENS
    return False


def metrics(c, tag, out):
    """tier1_tb.dc_metrics with the dummy first conversion (gen_tier1, D57) discarded before INL."""
    res = TB.run_deck(c, tag, out)
    if not res.get("convs"):
        return res
    res["convs"] = res["convs"][1:]
    res["meta"]["cfg"]["u_list"] = list(res["meta"]["cfg"]["u_list"])[1:]
    uin = np.array(res["meta"]["cfg"]["u_list"], float)
    uh = TB.u_hat_of(res)
    res["u_in"], res["u_hat"], res["err"] = uin.tolist(), uh.tolist(), (uh - uin).tolist()
    res["max_abs_err"] = float(np.max(np.abs(uh - uin)))
    res.update(TB.inl_gain(uin, uh))
    return res


def cm_at_release(out, tag):
    """Output CM / island CM at each reset release (gen_tier1 .meas lines), from the ngspice log."""
    rows = {}
    try:
        for ln in open(os.path.join(out, tag + ".log")):
            m = re.match(r"\s*(ocm1|icm1)_(\d+)\s*=\s*(\S+)", ln)
            if m:
                rows.setdefault(int(m.group(2)), {})[m.group(1)] = float(m.group(3))
    except OSError:
        pass
    return rows


EP_TOL_PPM = 0.05   # endpoint agreement between parts [ppm of FSR 2]; WO-24 nom parts agree to ~0.008 ppm


def combine(paths, k=None, tol_ppm=EP_TOL_PPM, broken=False):
    """Combine --part slices (REVIEW-C1b m6). Asserts that every part has the same endpoints (u_in) and that their u_hat
    agree within tol_ppm (the endpoint conversions are the same codes / residues in each part; a part that drifted or a
    stale json fails here). Also checks the part set is complete (0..k-1, no duplicates) and that shared interior
    points agree. Returns max per-part endpoint INL (the gate value) and the INL recomputed on the union grid."""
    rows = [json.load(open(p)) for p in paths]
    k = k or len(rows)
    parts = sorted(int(r["part"].split("/")[0]) for r in rows)
    assert parts == list(range(k)) and all(int(r["part"].split("/")[1]) == k for r in rows), f"part set {parts} != 0..{k - 1}"
    pts = {}
    for r in rows:
        uin, uh = r["u_in"], r["u_hat"]
        assert len(uin) == len(uh) >= 3, f"{r['tag']}: no conversions"
        lo, hi = int(np.argmin(uin)), int(np.argmax(uin))
        for j in range(len(uin)):
            pts.setdefault(round(uin[j], 9), []).append((r["tag"], uh[j], j in (lo, hi)))
    eps = sorted({round(min(r["u_in"]), 9) for r in rows} | {round(max(r["u_in"]), 9) for r in rows})
    assert len(eps) == 2, f"endpoints differ between parts: {eps}"
    spread, disagree = 0.0, []
    for u, lst in pts.items():
        vals = [v for _, v, _ in lst]
        sp = (max(vals) - min(vals)) / TB.FS_FULL * 1e6
        spread = max(spread, sp) if u in eps else spread
        if u in eps:
            assert len(lst) == k, f"endpoint u={u} missing from some part"
        if not sp <= tol_ppm:
            msg = f"u={u}: u_hat disagrees by {sp:.4f} ppm > {tol_ppm} across {[t for t, _, _ in lst]}"
            # WO-29 item 4: a broken copy (slew-limited, memory between conversions) may disagree at the endpoints;
            # that is info there. A nominal combine still requires agreement.
            assert broken, msg
            disagree.append(msg)
    uu = np.array(sorted(pts)); uh = np.array([np.mean([v for _, v, _ in pts[u]]) for u in uu])
    union = TB.inl_gain(uu, uh)
    probs = [p for r in rows for p in r.get("problems", [])]
    inl = max(r["inl_ep_ppm"] for r in rows)
    healthy = not probs and all(math.isfinite(r["inl_ep_ppm"]) for r in rows)
    return dict(n_parts=k, n_points=len(uu), endpoint_spread_ppm=spread, inl_ep_ppm=inl, disagreement_info=disagree[:6],
                inl_ep_union_ppm=union["inl_ep_ppm"], inl_bf_union_ppm=union["inl_bf_ppm"], problems=probs,
                healthy=healthy, pass_gate=healthy and inl <= GATE, pass_share=healthy and inl <= GATE_SHARE)


def cfg(a):
    c, t, v = CORNERS9[a.corner]
    sub = os.path.join(a.out, "ota1_sc.spice")
    open(sub, "w").write(NL.build("ota1", cmfb="sc", fs=4e6, boost=True))
    bias = NL.bias_currents(True)
    if a.copy == "sr95":
        bias = {k: v * SR95_SCALE for k, v in bias.items()}   # M2: all six ports, not the tail alone
    u = TB.u_points(a.m, 0.9)
    if a.part:
        i, k = map(int, a.part.split("/"))
        u = tuple(sorted(set((u[0], u[-1]) + u[1 + i:-1:k])))
    xt = dict(subckt=sub, lib=LIB, corner=c, temp=t, vdd=v, boost=True, bias=bias, sink_ports=NL.SINK_PORTS,
              vicm=S.V_ICM, vocm=S.V_OCM, cp_vg_ext=0.035e-12, c_out_ext=C_OUT_EXT)
    return TB.v2_cfg(dict(fs=4e6, gbw=27e6, gbw2=22.5e6, sr2=27e6, fp2_mult2=3.0, bst1=1.0, bst2=1.0, ota1_xtor=xt),
                     n=a.n, m=a.m) | dict(u_list=u), (c, t, v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--opt", default="O1")
    ap.add_argument("--n", type=int, default=1024)
    ap.add_argument("--m", type=int, default=21)
    ap.add_argument("--copy", default="nom", choices=("nom", "sr95"))
    ap.add_argument("--corner", type=int, default=3)   # CORNERS9[3] = fs/125/3.0
    ap.add_argument("--part", default=None)
    ap.add_argument("--deck-timeout", type=int, default=7000)
    ap.add_argument("--combine", type=int, default=0, help="combine K part jsons of this copy/opt/n in OUT, then exit")
    a = ap.parse_args()
    if a.combine:
        import glob
        fs = sorted(glob.glob(os.path.join(a.out, f"gb_{a.copy}_{a.opt}_N{a.n}_p*o{a.combine}.json")))
        try:
            r = combine(fs, a.combine, broken=a.copy == "sr95")   # WO-29: broken copy: healthy parts > gate => REJECTED
        except AssertionError as e:
            print(f"COMBINE INVALID: {e}")
            sys.exit(2)
        print(json.dumps(r))
        if a.copy == "sr95":
            v = "REJECTED (good)" if r["healthy"] and r["inl_ep_ppm"] > GATE else ("PASSED (check is blind)" if r["healthy"] else "INVALID")
            print("broken copy", v)
            sys.exit(0 if v.startswith("REJ") else 1)
        print("VERDICT", "ACCEPT" if r["pass_gate"] else "REJECT")
        sys.exit(0 if r["pass_gate"] else 1)
    os.makedirs(a.out, exist_ok=True)
    P.SPICE_OPTIONS_TIER1.update(P.option_ladder(a.opt))
    TB.DECK_TIMEOUT_S = a.deck_timeout
    c, corner = cfg(a)
    tag = f"gb_{a.copy}_{a.opt}_N{a.n}" + (f"_p{a.part.replace('/', 'o')}" if a.part else "")
    if a.copy == "sr95":
        print(f"sr95 copy: bias scale {SR95_SCALE:.4f} on all six ports; expected boost SR {S.I_TAIL * S.BOOST * SR95_SCALE / C_INT_PHASE / 1e6:.2f} "
              f"V/us at the integrate-phase load {C_INT_PHASE * 1e12:.3f} pF (nominal {S.I_TAIL * S.BOOST / C_INT_PHASE / 1e6:.1f}); "
              f"GBW also drops (gm falls with the bias current)")
    try:
        r = metrics(c, tag, a.out)
    except Exception as e:   # a crash must never read as "rejected"
        r = dict(problems=[f"crash {e!r}"], runtime_s=0)
    r["problems"] = [p for p in r.get("problems", []) if not audit_expected(p)]
    for m_, v_ in sorted(cm_at_release(a.out, tag).items()):
        print(f"  reset release {m_}{' (dummy, discarded)' if m_ == 0 else ''}: out CM {v_.get('ocm1', float('nan')):.4f} V, "
              f"island CM {v_.get('icm1', float('nan')):.4f} V")
    csv = os.path.join(a.out, tag + ".csv")
    if os.path.exists(csv):
        os.remove(csv)   # WO rule: no raw csv
    inl = r.get("inl_ep_ppm", float("nan"))
    healthy = not r["problems"] and math.isfinite(inl)
    ok = healthy and inl <= GATE
    row = dict(TB.strip(r), corner=corner, copy=a.copy, opt=a.opt, n=a.n, m=a.m, part=a.part, gate_ppm=GATE,
               share_gate_ppm=GATE_SHARE, inl_ep_ppm=inl, pass_gate=ok, pass_share=healthy and inl <= GATE_SHARE)
    row.pop("meta", None)
    json.dump(row, open(os.path.join(a.out, tag + ".json"), "w"), indent=0, default=str)
    print(f"{tag} {corner}: INL ep {inl:.3f} ppm (gate {GATE}, share {GATE_SHARE:.2f}) runtime {r.get('runtime_s', 0):.0f}s "
          f"problems {r['problems'][:4]}")
    if a.copy == "sr95":
        if healthy and inl > GATE:
            print("broken copy REJECTED (good)")
            sys.exit(0)
        if healthy:
            print("broken copy PASSED (check is blind)")
            sys.exit(1)
        print("BROKEN COPY INVALID (crash / NaN / audit problem: neither rejected nor passed)")
        sys.exit(2)
    print("VERDICT", "ACCEPT" if ok else "REJECT")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
