# sd-adc-design-reviewer memory (tt-iadc)

## Review 2026-11-07: SPEC.md rev 2026-11-07b + work/v1-design/PLAN.md
Review text returned to coordinator (not written by me; agent is read-only except memory).
Target path the coordinator asked for: work/v1-design/REVIEW-spec-plan-2026-11-07.md

Confirmed (held up):
- CoI reconstruction u=(sumS+(k/c1)S)/(N(N-1)/2) exact; residual = x2[N]/(c1c2 N(N-1)/2). sumS exclusive (sumS+=S before S+=y).
- Cap ratio error on k/c1 gives only ~8*eps*u/N gain error (no INL).
- kT/C 0.5 uV @15 SPS consistent by hand (157 uV/sample diff, 2 events, excess 1.5).
- 24-bit signed acc2 fits N=4096: N(N-1)/2=8,386,560 < 2^23-1 (margin 2047).
- sky130 lib has *_mm sections for every corner (MC at worst PVT feasible); passive corners are ll/hh/hl/lh and combos (ss_hh...).
- MIM model: mismatch sigma = 2.8%/sqrt(area um^2) under MC_MM_SWITCH; NO voltage coefficient, NO bottom-plate parasitic in device model (only PEX shows it).

Findings (status open unless noted):
- F1 Option B (c1=0.125,k=1) changes NTF and does not halve x2; correct scaling: c1=0.125,k=0.5 (k/c1=4 kept), x2 scale free via c2 (1-bit quantiser scale invariance). PROVEN algebra.
- F2 OTA input CM = Vcm_s + Vref_cm - Vin_cm (FD SC with single VREF pin vs GND); input CM range unspecified. REASONED.
- F3 fs=4 MHz corner inconsistent with GBW>=10 MHz / SR>=10 V/us: slew-then-settle error becomes signal dependent. Hand calc.
- F4 beta stated 0.3-0.5, actual Cint/(Cint+Cs+Cp)=0.75 (int1), 0.61 (int2). Model settle study covers input/ref RC only, not OTA.
- F5 A0>=75 dB gives model INL 71 ppm; PLAN S3 1.5x INL margin needs <=67 ppm -> spec self-inconsistent.
- F6 SPEC says shared Cs/DAC; design-point numbers run with separate caps; PGA x2 needs separate; PGA absent from model/S6/V4.
- F7 no chop-phase / mode tag in raw output frame; firmware cannot demodulate reliably.
- F8 first comparator decision after reset sees x2=0 -> metastability every conversion; DAC and decimator must use same retimed bit.
- F9 PLAN missing: reset completeness / inter-conversion memory test, reset residue offset (2*x1[0]/(c1(N-1))), CMFB startup from rails, chop toggle inside reset window, analog/digital reset alignment, TT pad path in top TB, ngspice tolerance floor (Paul used reltol 1e-4, sanity gate only), REF- pin.
- F10 V3 at N=256 has ~244 ppm quantisation floor -> cannot gate INL; use residue reconstruction with x2[N].
- D2 sound in principle but fixed 5 points miss ss/-40/3.0 (TG Ron, swing) and ff/125/3.6 (leakage, gain); pick top points from tier-2 per-spec worst corners. MC gate "one sample beyond 3 sigma" ill-defined.

## Reference-design notes
- pthomas top_tb.py: .options method=gear reltol=1e-4 vntol=1e-6 abstol=1e-10; 2048-bit window; gate SNDR>=36 dB + ones density 0.2-0.8 (sanity gate, not precision). comp_mc uses tt_mm.

## Review 2026-11-07 (2): S1 (WO-02 VREF/swing) + S2 (WO-03 chop), iadc.py blob c4269ba
Probes on sandbox (scripts /tmp/rev_probe_s1*.py, /tmp/rev_probe_s2.py on sandbox, not in tree).
Held up: 1/(N-1) OTA-chop residual (order 2) closed form; F1 bitstream equivalence; vlin in volts is the right axis; paired-differential offset method sound; shared vs separate Cs identical INL at S1 taus (12.35 vs 12.32 ppm).
Findings (open):
- S1-1 INL at N=1024 has ideal-OTA quantisation floor 6.8 ppm (PROVEN). N=4096 A0 75: A 16.3, A_half(1.2V,c1 .125,k .5) 2.1, B 6.2, C 945; A0 80: A 9.3, A_half 1.4, B 3.7. B's INL edge over A is c1 scaling, not VREF (PROVEN).
- S2-1 model lacks OTA2 offset: u err = 2*Vos2/(c1(N-1)) (17.6 uV @9mV,c1 .25,N 4096), constant -> sys chop cancels; OTA2 chop not needed (algebra PROVEN).
- S2-2 order-1 OTA-chop-only residual = lf*Vos/N, odd in Vos, bit-identical to comparator offset c1*Vos (18.92+-1.07 uV vs 17.58 @N512) -> quantiser-residue path; s2_theory misses it. Residue reconstruction would HIDE it; use as diagnostic split only.
- S2-3 C9 rules missing: chop state during reset fixed, swap point at pins side, forced/shared y[0], config change only at pair boundary + invalid flag, acc clear on reset-release edge, reset length.
- Ref recovery INL: tau_ref 100ns/cd 20p 21.7 ppm, cd 2p 66 ppm; S3 must use consistent (500 ohm, pad+on-chip C) pair. cd_ref default 20 pF = 10,000 um2 MIM.
- D3 rec given: 2.048 V, c1 .125, c2 .5, k .5 (Cs 0.5 pF option area-neutral). D4 rec: OTA1-only chop as config bit, default sys-only, keep only if chopper keeps A0>=80 dB in both modes.

## Review 2026-11-07 (3): S3 error budget (WO-05, results/s3_budget.md, model/studies/s3_budget.py)
Sandbox unreachable this review (ssh publickey refused) -> all hand calcs REASONED; TG Ron ngspice probe given as command.
Verdict: S3 closable with conditions (spec-table fixes, no new sweeps required).
Held up: beta1 0.86, CL1 1.26 pF form, SR 11.4 V/us (diff = Itail/CL correct for folded cascode), GBW 4.1-8.2 MHz,
 kickback 3.81 ppm/mV, reset/leak/offset theory checks, RSS noise no double count. Slew-then-settle INL at 2 MHz,
 GBW 10 MHz/SR 12: ~0.2 ppm (hand) -> no INL row needed; 4 MHz ~54 ppm at u .9 (fast mode only).
Findings (open):
- S3-1 OTA thermal spec/power framed continuous-time: SC sampled OTA noise ~ 2*gamma*nf*beta*kT/CL (indep. of en):
  1.72*kT/1.26pF = 5.65e-9 V2 vs switch 2 events 3.31e-8 -> excess ~1.17 (model used 2.05 at "10 nV"). Current is
  set by GBW/SR, not noise; "7 nV over 200 uA" conclusion invalid. Spec: integrated sampled noise at VG <= 250 uV rms diff.
- S3-2 OTA2 power underestimated: x2 step c2*(x1+kVREF) ~1.12 V diff in 45 ns -> 25 V/us, CL2 ~0.7 pF -> ~40 uA (vs 5.5).
- S3-3 SR 12 V/us covers integration step only; Cs2 charge-sharing on OTA1 output (phase plan unspecified) can ~double it.
- S3-4 TG Ron 820 ohm ignores body effect; with gamma~0.5 mid-rail at ss/-40/3.0 -> ~1.9 kohm > 1.5k spec; source limit ~1k.
- S3-5 Reset window 60 ns = switch RC only; OTA in reset loop needs slew 1.22V/12V/us ~100 ns + 9.2 tau(16 ns) -> >=250 ns;
  spec >= 2 clock cycles. Only non-cancelling offset term. MIM dielectric absorption unmodelled.
- S3-6 Cap-ratio gain row tautological (value = share = 3000, margin 1.00) and wrong mechanism: shared Cs -> Cs/Cint gives
  no gain error (only 8*eps*u/N ~11 ppm). PDK mismatch 2.8%/sqrt(250um2)=0.177% Cs, 0.063% Cint -> ratio 0.56% 3sigma > 0.3 % spec.
- S3-7 Missing contributors: ref avg current quadratic in u: I = fs*Cs*(VREF+ - Vcm - VREF/2*u^2) -> u^3 error 2*R_ext*1.02uA;
  10 ohm -> ~1.4 ppm INL, 50 ohm ~7 ppm (board spec: decap + R_ext). Input avg current = fs*Cs*(Vin_cm - Vref_cm) (no u term) ->
  offset via source-R mismatch, NOT cancelled by sys chop (pin-side voltage). D12 CM range / CMFB rows absent. F8 single-bit row absent.
- S3-8 OTA linearity spec "<=90 % drop at 2 V" = model parameter, untestable shape; restate at real swing: A(0)>=80, >=75 dB
  for |v|<=1.4 V diff + gate via sim A(v) LUT in model (needs iadc hook).
- S3-9 vres 5 uV physically ~0.1-1 mV (dq ~0.1 fC/0.5 pF); fine (constant, cancels) but spec signal-dependence instead.

## Review 2026-11-07 (4): S5 tier-1 ngspice deck (WO-07; gen_tier1.py/tier1_tb.py md5 2737223a/261e4a64, params d0192a4d)
Probes on sandbox: /tmp/rev_probe_s5.py (deck), /tmp/rev_probe_s5m.py (model), outputs /tmp/rev_s5 (not in tree).
Verdict: S5 closable with conditions (doc fixes + model cross-check rows + scope of SPICE_OPTIONS + deferral decisions).
Held up: deck loop algebra = x1+=c1(u-y), x2+=c2(x1[n]-k y) (charge-conservation derivation), bottom-plate phases, y[0]=+1 forced,
 residue formula exact, nonvac set real (dac_flip, c1x2, A0 50, no-residue), trap@1e-3 fails null -> null discriminates.
 My S3 hand calcs confirmed: 2 MHz slew INL ~0.2 ppm (sim 0.18), 4 MHz GBW10 ~54 ppm (sim 63).
Findings (open):
- S5-1 PROVEN null floor 4.64e-7 = Srst Roff 1e12 across Cint1: gain err k/(Roff fs Cs1)=5e-7; Roff 1e14 -> 7.3e-9.
  Real reset-switch leakage at hot is the same mechanism (spec it in C-stage).
- S5-2 PROVEN gain formula wrong: gain ~ -1.09*k/A0 (OTA1 vg error integrating mean x1 = k*u), NOT (1+c1)/(2A0).
  A60: base -5.59e-4, k .25 -2.93e-4, c1 .25 -5.51e-4 (deck); model -5.47e-4/-2.88e-4/-5.43e-4. INL deck 3.99/6.98/10.05 vs model 3.09/5.90/7.43.
  Model A80 const: gain -5.47e-5, INL 0.295 ppm -> 3.4 ppm S3 joint is A(v)+other rows, not constant A0.
- S5-3 INL from finite gain depends on STATIC vg(vo) (h(x)=x/A_static), not incremental gain; A(v) table definition must say which.
- S5-4 OTA macromodel: ideal VCVS output -> load-independent GBW/SR; Cs2-in-hold-phase (D25) load and PM/2nd pole invisible;
  tanh implies Vov=SR/(2pi GBW) (SR 3 @ GBW 10 = 48 mV, unphysical).
- S5-5 VREF in deck = CM +- VREF/2 (2.674/0.626) not chip pins (2.048/0, D24); Vin_cm=Vref_cm -> D12/F2 CM untested; no D12, no chop.
- S5-6 SPICE_OPTIONS frozen globally but qualified only for linear ideal deck (null Ron 1 ohm); chgtol 1e-14 = 1% of Cs*VREF charge;
  require per-tier requalification (tier-2 null with transistor switches + ideal OTA).
- S5-7 PLAN S5 criterion "INL and noise agree with tier 0" not done in report (my probe covers constant-A INL; noise missing).
Fast-mode GBW rec: options (a) keep 10 MHz min + fast-mode INL target >=100 ppm, (b) 20 MHz loaded min, (c) bias boost bit at 4 MHz.

## Review 2026-11-08: S4 re-gate (WO-06a e2915a0) + S5b (WO-08 c686d16)
Written (caller asked) to work/v1-design/REVIEW-S4S5b-2026-11-08.md. No runs; PROVEN = JSON arithmetic / code reading.
Verdict: S5 closable w/ conditions; S4 closable after sys-off CMRR mechanism correction (eps_Cs -> eps_eff) logged in DECISIONS.
WO-08 closed REVIEW-S5 M1,M2,m1-m6; M3/M4 done with gaps.
Findings (open):
- C-M1 knees2 sweeps SR/GBW on BOTH OTAs (gen_tier1 v2: ip=bst*c["sr"]*cl for k in 1,2) -> OTA2 at 12 vs spec 25; x2 errors enter residue as
  ~2*e2/(c1c2N) (60 ppm @N256 for 5e-4) -> knee not attributable to OTA1; grid too coarse (2M knee 8..10, 4M boost 9..12).
- C-M2 folded cascode symmetric slew needs I_fold>=I_tail (1.2x): I_tot~3.4*I_tail. 46 uA -> max 10.9 V/us symmetric @1.4pF.
  OTA1 12 V/us 57 uA, 15 -> 71; OTA2 25 V/us@0.7pF 60 uA (not 40). Boost x2 both -> ~260-320 uA > D31 200 uA.
- C-M3 deck has Cp_top=0 on floating D12 node (Cpv only on vg). eps_eff = dCp_top/Cs - (Cp_top/Cs)*eps_Cs + TG inj split
  (TG n/p charge slopes ADD vs Vcm). Cp 10-20 fF, dCp 0.5-2 fF -> 60..48 dB. Leakage island drift cancels in CMRR (Vt and vg shift together).
- C-M4 island CM = CMFB ref 1.65 V; thick-ox PMOS at ss/-40/3.0 -> ~0.05-0.25 V tail headroom; Paul used VCM 0.9. D12 island has no CM
  refresh: drift I*N/fs/9.5pF = 21 mV @2MHz/N4096/100pA, 170 mV @0.25 MHz.
- m1 CMRR metric: subtracts matched run at same Vcm (not slope); sys-on uses pair_V = gain term (-1.097e-5 all rows). Strict D12 slope 168 dB @0.75%.
- m2 CMRR gate non-discriminating (no-D12 passes 66 dB); vg range assumed 0.2-2.0.
- m3 xcheck A0 80 on Roff 1e12 floor; m4 deck INL 17-33 % above model at const A0; m5 INL non-additive (spec+A(v) 1.01 < 1.69);
  m6 D12 CM pin current ~fs*Cp_top*dVcm (~30 nA) -> sys-on ceiling 1/(dR fs Cp) ~116 dB @50 ohm; m7 "bleeder floor" text wrong (eps^2 scaling);
  m8 S4 n15 margin 0.7 %; m9 knees2 ACCEPT = run health only.
Recs: S4 model eps_eff alloc (Cp 20 fF, dCp 3sig 0.25 fF) ~65 dB; C4 target sys-off 60 min/66 design, sys-on 100 min/120 goal.
 SR: >=12 V/us slower direction every corner, I_fold>=1.2 I_tail, SR>=1.25x OTA1-only knee; fast mode needs user choice (boost OTA1 only / 3 MHz / lift cap).
Held up: D12 first-order cancel real in ideal deck; Vos2 1.5x factor (Ck shares OTA2 node); offsets closed forms; noise transfer 1.05; A(v) 13.9 %.

## Review 2026-11-08 (2): S5c (WO-09 0903e8d/fd145ac, results 6076f49) + S4 close (WO-10/11 d54d8f3, eb0b52a, d3ab346)
Not written to the tree by me (my rules: memory only); full text returned to caller for REVIEW-S5c-S4close-2026-11-08.md. No runs; one ssh grep of cm2.log.
Verdict: S5 closable w/ conditions; S4 closable w/ conditions (spec rows + test restore + C4 gate form).
Closed: C-M1 (separated knees), C-M3 (linear lumped D12 residual; 0.0 % is exact charge algebra of the same linear deck, closed form
 computed from params at tier1_tb.py:874, not from deck output; scope excludes eps_inj and Cj(V)), m1 (deck), m3, m7, m9. m6 closed via
 settling-aware form (case B 2 nF within 2 %).
Findings (open):
- R1 knee threshold 13.3 ppm = whole INL budget/1.5; SPEC INL alloc has no slew line (OTA line 8 ppm minus A(v) 5.2 worst = 2.8).
  At a 1.9 ppm slew share the OTA1 knee is ~9.8 V/us (2 MHz, N256 and N1024) -> 12 V/us margin ~22 % < 25 %. Rec SR >= 12.5.
- R2 OTA1-only-boost 12.9 ppm floor = OTA2 small-signal settling (GBW), not SR: OTA2 boosted base 12 (24 V/us, 20 MHz) 4.23 ppm vs
  unboosted 25 V/us/10 MHz 12.9 ppm (same SR). Hand: OTA2 tau 26 ns at beta .61/10 MHz, eps ~7 % at 4 MHz.
- R3 OTA2 SR 25 over-specified at 2 MHz: 12 V/us gives 1.69/0.78 ppm (N256/N1024). Rec 13.5 base (covers 4 MHz boost 2.18 ppm). ~-28 uA.
- R4 S4 sys-on residual ~8.6 uV at N256 = model reconstruction floor (~2.1 ppm FS at N256), scales 1/N^2 to ~0.03 uV at N4096
  (= full-run sys-on errors 0.002-0.07 uV). Not a CM term; test weakened to sys-off only at N256 -> restore sys-on check at N4096.
  S4 sys-on ACCEPT = metric floor under the modulator-frame hypothesis (circular); tier-1 cm2 sys-on 137-173 dB is the evidence.
  Real second-order term exists: per-u residual e*d(g_even)/du (~e*1e-5), averaged out by symmetric-u mean.
- R5 D36 RSS sound for random terms; dCp,top is mostly SYSTEMATIC layout asymmetry -> C4 gate must be |dCp_sys|/(Cs(1+r)) + RSS(random)
  + |inj| <= 1e-3: dCp_sys(PEX) <= 0.08 fF. '-' sign means area-correlated Cp cancels (good), sign irrelevant for independent draws.
- R6 stage-2 drift not gated: C_side2 2.01 pF -> 102/204/814 mV (2M N4096 / .25M N1024 / .25M N4096). N<=1024 at .25 MHz doesn't fix stage 2.
- R7 vg1 CM range with D12 [1.554,1.728] V (cm2.log), no-D12 [0.673,2.538]; no check gates it -> D12 removal passes all gates (m2 residue;
  nod12_ref sys-off 66.3 dB passes 60).
- R8 pin path with board C: 100 dB sys-on needs dR <= 1/(1e5 fs Cp_top) = 333 ohm (15 fF, 2 MHz). SPEC row 104 pin-current text pre-D12.
- R9 m4 bias still open: deck INL 26-39 % above model (rel_sym 30-33 % vs 35 % tol), gain 2-3 % more negative; Roff ruled out; suspect Cp_vg in beta.
- Drift mitigation rank: (1) leakage spec per vg node + sign (NMOS-only island switches -> one-sided downward drift, away from PMOS
  headroom limit) + corner-aware CM row (hot drift and cold headroom do not coincide); (2) N cap at .25 MHz hot (loses 15 SPS mode,
  stage 2 still fails); (3) accept documented; (4) island CM refresh mid-conversion = not v1 (injection, undoes D12).

## Review 2026-11-08 (3): S5d / WO-12 (61022f0, c33c0de, 0633796; results 8abe28b)
Returned to caller for work/v1-design/REVIEW-S5d-2026-11-08.md. Probes (sandbox /tmp/rev_r4.py, /tmp/rev_r9.py, /tmp/rev_r9b.py; not in tree).
Verdict: S4 not closable until the residue frame bug is fixed + rerun (small numeric impact); S5 closable w/ conditions (fast-mode user choice).
Findings:
- D1 PROVEN (my R4 was WRONG): s4_corners _corr / cm_err_v / static_err_corr / mc_task cv add x2_final (modulator frame) AFTER
  convert() demodulated u_hat by sys_sign -> for s=-1 the residue is added with the wrong sign (error 2*x2/(c1c2W), pair keeps
  x2_minus/(c1c2W) = raw quant residue). Reproduces WO-12 probe exactly (ideal A N256 6.274/4.182/6.015 uV; table 1.047/2.35/2.09).
  Fixed (uh + s*x2/(c1c2W)): ideal 1e-11 uV, table <=7e-4 uV N256. Offset pair mean bias N256 -3.27 uV, N4096 -0.08 uV.
  INL paths (no sys_sign) unaffected; s1_vref, tier1_tb unaffected (deck reconstructs in modulator frame). Fix: return u_corr from convert.
- D2 PROVEN: Ck in beta2 is right physics (sampled cap, enters p and g): c_eff2 = c2(1+k). But cp_vg hook is WRONG for a
  permanent vg parasitic: it only changes g, not the leak (vo'(1+(1+c+cp)/A) = vo(1+(1+cp)/A) + c vin). Deck diag A60_base_cpvg
  INL 4.007 vs 3.993 (no Cp); model with cp_vg 5.28 -> model hook overstates. Coordinator claim "S4 5.2 -> ~7 ppm" WRONG:
  Ck default at S4 points changes INL <=0.4 % (ss/125/3 .25M 5.222->5.234), S3 spec point +0.9..2.8 %. xcheck x1.2-1.4 is
  N256 const-A0 only (stage-2 leak dominates there). 35 % xcheck tol passes the uncorrected model -> tighten to ~5 %.
- D3: option (a) failure is OTA2 slew at 13.5 V/us: step 1.13 V -> 83 ns of 112.5 ns half period; my R2 "GBW only" held only at SR2 25.
- Current table: boost-both 1.4 ppm was with OTA2 at 25 base; at OTA2 13.5 base it is 2.18 (N1024)/4.21 (N256). 210 uA > D31 200 uA cap.
  Option (a) precision current = 118 (not '-'). Per-SR currents: OTA1 4.75 uA/(V/us), OTA2 2.4, overhead ~26 uA (fits user table).
- 2 MHz modes: N4096 (3.75-60 SPS), N1024 (240 SPS per S4 N240 convention). N256 at 2 MHz unspecified; OTA2 knee scales ~N^-0.55 not 1/N.

## Review 2026-11-08 (4): S5e / WO-13 (85e9e24, a3ea4eb, a8449b4, 22dab89)
No runs (sandbox saturated). Full text returned to caller for work/v1-design/REVIEW-S5e-2026-11-08.md.
Verdict: model fixes correct (C1 frame, Ck c2(1+k), cp_hold g-only, nonvac5 real). S6 not blocked. S7 blocked on fast-mode spec rows.
Held up: u_corr = s*(u_mod + x2/(c1c2W)) (order-2 V1 test fails old frame); Ck top plate on tp2 reset in phi1e -> sampled cap;
 cp_hold charge algebra; nonvac5 (0.75->0.5 stage-2 c_samp, 34 % INL at N256 const A) rejects at 5 %.
 205 dB sys-on = model e^2*f'' term (symmetric-u mean kills 2*a*u*e first-order even term); per-point ~165-170 dB; silicon ~116-173 dB.
Findings (open):
- S5e-M1 deck boost scales gm linearly with current (gen_tier1.py gmk = bst*2pi*gbw*cl). EKV: OTA2 gm/Id 14 (IC~1.5) x1.5 current -> gm x1.31
  (boosted GBW2 19.7 not 22.5) -> V5i N1024 interp ~5.3 ppm (marginal FAIL 5), N256 ~12 (pass). OTA1 gm/Id~10 (IC~4) x2 -> x1.52.
  SPEC l.117-118 C1 gate GBW ratio >= 1.9 needs IC <= ~0.07 (gm/Id ~24) -> very wide pair, Cp_vg >> 0.262 pF. Thick-ox Ispec assumption ~60 nA/sq (unverified).
- S5e-M2 V5(ii) 3 MHz 110-280 ppm is NOT a deck bug: timing fs-agnostic (gap 12.5n, tdel 5n), knee_thresholds unused by fast2.
  OTA1 slew: phase 225 ns (2M) vs 141.7 ns (3M) -> 12.5 V/us@3M ~ 7.9@2M; deck 2M OTA1 8 V/us = 143 ppm; 4M unboosted 6252 ppm.
  MY S5d 3 MHz hand estimate was WRONG (omitted OTA1 slew; used t_half 150/112.5 instead of deck h-2g 141.7/100 ns).
  3 MHz no-boost needs OTA1 SR ~20 always-on (~+36 uA precision) -> dominated by V5(i).
- minors: s3 rerun moves not attributable (results stale since d3fdf8b, script changed af85d1e; joint INL 3.41->2.03);
  V4 "headroom" is INL ratio, knee needs 10.8 V/us point; fast_task beta2 0.55 vs deck 0.497 (Cp 0.262 on vg2), SR2 27 vs chosen x1.5 = 20.25;
  order-1 u_corr branch untested; xcheck 5 % gate covers legacy OTA N256 only.

## Review 2026-11-09: S5f / WO-14 (2966c92 e95b887 6fb0a6f 0493917 925b983 05cbab2; results 8ade439)
No runs. Text returned for work/v1-design/REVIEW-S5f-2026-11-09.md.
Verdict: gm/Id table + gm_ratio sound (EKV hand check of 1.283 within 1 %); s5f sizing framing over-constrained; fast mode feasible <200 uA.
Key facts: deck gm/Id = 4*pi*GBW/SR (tanh linear range) -> OTA1 base 10MHz/12.5 = gm/Id 10; OTA2 15/13.5 = 14; NV_same row
 (bstgm=bst, 3.7 ppm) == boosted operating point gm/Id 10.05 (OTA1, 35 uA, CL 1.4p) / 13.96 (OTA2, 14.2 uA, CL .7p) at hot.
Findings (open):
- F5f-M1 PROVEN hand: s5f "bases must rise" (OTA1 14 MHz, OTA2 17.5 at every corner, min current) needs gm/Id 14.1/16.3 at 125C
  base J -> W/L ~150 / ~700 (L1) -> Cgs >> beta budgets. Gate boosted point directly: OTA1 W/L>=29 (L1, J_b<=6.1e-7, Cgs~.15p);
  OTA2 x1.5 W/L>=106 (J_b<=6.7e-8 ff/125) -> L1 Cgs ~.4p (beta2 ~.45) unless L~0.5; OTA2 x2 W/L>=18 (J_b 5.25e-7), Cgs ~.09p.
- F5f-M2: INL rises with OTA2 boosted GBW at fixed SR (19.2->25.7 MHz: N256 6.7->14.4, N1024 9.95->12.5); D39 ">=" rows proven at one
  point only; cold corner GBW ~1.5x (OTA1 ~30, OTA2 ~34 MHz) unsimulated. Cause unresolved: tests = OTA1 ideal sweep, reltol/maxstep,
  fp2_mult 30, 101-pt signed INL. Single-stage slew+settle is scale-invariant except fixed slew time -> should be monotone.
- F5f-M3: no beta2/Cp_vg2 row (deck fixes 0.262 pF on vg2 -> beta2 .497).
- minors: need_22p5 reports LARGEST gm/Id (= hot peak ceiling 20); right = smallest; 15 MHz entry vacuous; comment says g5.
  pfet_01v8 plateau 1e-8..1e-7 (ff/-40 rises 20.9->21.3), peak at J<1e-9; gmid ACCEPT check not non-vacuous; table lacks L<1.
  deck fp2 ∝ bstgm optimistic if fold not boosted. SPEC l.122 stale. My S5e-M1 5.3 ppm WRONG (ignored OTA1 ratio 1.42; deck 9.95).
- Current est boosted: x1.5 ~159-165 uA, OTA2 x2 ~172-178 uA (2.7 rule or fold sized for boost).

## Review 2026-11-09 (2): S5g / WO-15 (uncommitted working tree)
No runs. Text returned for work/v1-design/REVIEW-S5g-2026-11-09.md.
Verdict: A' cold/hot points pass with margin -> S5f M2 closable for the point check; S7 still blocked (PM window, convergence, W/L x2).
Findings (open):
- G-M1 REASONED hand calc: deck 2-pole macro (fp2 = 3*GBW, Rf 1k/Cf before tanh, gen_tier1.py:258-266) is near-critically damped
  for OTA1 (tau2*K = beta1/3 = .28, zeta .945, envelope sigma = 1/(2 tau2) ~1.8x faster than single pole K = beta*wu). fp2_mult 30 ->
  single-pole settling (~1/30-1/60 linear error ratio over 50-60 ns) -> 101-113 ppm, N- and GBW2-independent because OTA1 (14.2 MHz)
  dominates both rows. PHYSICS of macro, not a deck bug; s5g "probably numerical" is wrong. Held fp2 (a): OTA1 fp2 30 MHz vs GBW 20 ->
  PM ~63 deg, zeta .67 -> 177 ppm, yet passes SPEC l.93 "PM >= 60 deg". OTA2 at beta2 .497: tau2K .166 overdamped (zeta 1.23);
  held (45 MHz) is ~critical and FASTER. Optimum fp2 ~ 4*beta*GBW (OTA1 3.4x, OTA2 2x). SPEC needs PM window (~70-80 deg at phase beta)
  or step-settling row, both modes; OTA2 row has no PM at all. fp2_fixed used min base 10/15 MHz, not the 14 MHz implied -> worst case.
- G-M2 PROVEN code: gmid_min_wl uses I_tail (35/14.2/18.9 uA, tier1_tb.py:1460,1504) but targets are per-device (I_tail/2) -> W/L 2x
  (OTA1 L1 56 vs 29; OTA2 x2 35 vs 18; x1.5 237 vs 106). Test pins same convention (test_tier1.py:401).
- G-M3: solver convergence not shown: only 2 levels; tight tmax 5 ns ~ closed-loop tau (5.3 ns at 4 MHz); chgtol 1e-14/trtol 7 kept.
  Rule proposed: tmax <= tau_cl/10, 3-level ladder, |dINL| < 10 % or < 0.1*(gate-INL). At-risk rank: OTA2 knee N256 (5 % margin,
  shallow curve) > OTA1 25 %/26 % margin (steep, knee moves ~.2 V/us) > V4m .579 / V4 .557 (2.3-2.4x vs observed 2.8x shift) > V4 .393
  > xcheck 5 % (equilibrium, A-limited) > cm2/drift/nonvac (linear, big margins). Python model results unaffected.
- minors: 101-pt jagged residual ~5 ppm equal at N256/N1024 -> likely numerical; control gate checks reproducibility not accuracy;
  SPEC l.124 "one switched bias leg" vs D41 fold switching; L .35 needs A0 check.

## Review 2026-11-09 (3): S5h / WO-16 (6a96cb3, 677b39f; results 95844d9)
No runs (read point.json / pt.cir on sandbox WO-16-run-6a96cb3). Full text returned to caller for REVIEW-S5h-2026-11-09.md
(persona: memory-only writes; coordinator saves it).
Verdict: G-M3 closed for gated rows; D39 control 3.43 (31 %), A' c/d, V4/V4m, OTA2 N1024 hold at O2. S6 not blocked (tier-0).
S7 needs SPEC basis text + user OTA1 SR call + ~3 cheap jobs.
Key facts (PROVEN from artefacts):
- r1 O0 signed INL is jagged noise (+-2..7 ppm, no shape); O1/O2 smooth odd S-curve, gain err doubles -8.8e-5 -> -2.05e-4.
  => O0 lost the physical settling error (gear numerical damping at h*wn ~1.4 with tmax 10 ns; trap O1 18.59 > gear O1 17.28 fits)
  AND adds a numerical floor. O0 is UNCONVERGED EITHER SIGN, not "optimistic": big-INL 4 MHz rows rise (r1 x2.8, A'(d) +34 %,
  T3 +24 %, OTA1 knee +0.3-0.4), small-INL 2 MHz rows fall (V4 -43 %, A'(c) -84 %, OTA2 N256 -13..25 %).
- D43c "<3x margin" exemption is unsafe on O0 values (O0 error up to 2.8x): A' N256 fast (O0 2.0 vs 20) needs one O1 run.
- tau floor (gen_tier1.py:75) uses cfg gbw (BASE, ignores bstgm) and BETA1 for both OTAs -> r1 1.895 ns vs 1.33 ns at loaded 14.2 MHz.
  Immaterial: r1_rel_O2 (tmax 10 ns) 18.769 vs full_O2 18.775 (0.03 %). Floor only matters at reltol 1e-3. Harmless, cheap.
- r3 OTA1 knee jobs have sr2=None -> sr2 = max(sr, 25 V/us), gbw2 = gbw 10 MHz (gen_tier1.py:256-257): OTA1-only knee (correct
  definition) but s5h text says "SR2 13.5 fixed" (wrong label). r2 rows run SR1 = 12 V/us: r2 N1024 sr2 15 O2 = 0.137 ppm
  (paired) = direct bound on OTA1 at 12 (<12.5) -> >= 9.7x under the 1.333 share.
- Knee slope N1024 d lnINL/dSR = 1.61 per V/us -> 9 % INL step moves knee 0.05 V/us. Log interp knee 10.23 (N1024), 10.41 (N256).
- rev_model_inl 3.09 = hard-coded S5b pre-Ck model value (REV dict tier1_tb.py:390, tuple idx 3), printed never gated. Not a bug.
- fp2: both OTAs optimum at zeta ~0.87-0.94 (PM 72-75). OTA1 at 20 MHz fails 5 ppm at mult 2 (10.9) and 4 (8.06) -> D43a
  OTA1 70-80 window admits failing points (gate = step settling covers it). OTA2: all mult >=1.5 pass, mult 1 (65.6 deg) 5.27 fails;
  window 75-82 excludes optimum -> suggest ~70-85. Deck pole is BEFORE tanh (real fold pole after pair) -> low-mult side of the
  curves is model-specific; transistor step-settling row must decide.
- Runtime: N1024 O1 330-370 s, O2 730-810 s; N4096 O2 ~1400 s; r1 N256 O0 30 s / O2 140 s.
Open (S5h): H-M1 SPEC slew basis text cites O0 numbers; H-m1 OTA1 PM window; H-m2 A' N256 O1; H-m3 trap/gear precision mode;
 H-m4 OTA2 10.8 N1024 direct point; H-m5 point.json lacks solver options (only pt.cir); s5h doc labels.
 User decision: OTA1 SR 12.5 (basis restated, 22 % N1024) vs 13 (+2.4 uA prec, ~+4.75..5.7 uA fast -> ~194 of 200 uA).

## Review 2026-11-09 (4): S6 / WO-17 golden vectors (a34b809, 13f9692, 8b095d3)
No runs (read-only local JSON parse only, caller-allowed). Text returned for work/v1-design/REVIEW-S6-2026-11-09.md.
Verdict: S6 accepted with conditions; S7 not blocked by data, but needs ~9 SPEC rows (conventions the agent chose).
PROVEN from JSON: 500 frames; u_hat_signed*den == num_signed all; residue identity exclusive worst 0 vs inclusive 0.0268
 (convention anchor = iadc u_corr, the only truly independent tie; checker acc code is textually the same 4 lines as golden.py);
 sys-chop frame b == -frame a on 160/160 (tier-0 pair trivially symmetric, no offset to cancel); chop combos only 3
 (ota-only missing though config bits independent; V4 lists OTA mode); max|acc2| 7,533,166, max|acc1| 3686 (edges untested;
 acc1 13-bit signed would pass golden, all-ones N4096 needs 4096); frame_ctr max 11 (no wrap); ybits[0]=1 always.
Findings (open):
- S6-M1 forced y[0] not stimulus-testable at RTL: TB must drive comparator bit at cycle 0 (and reset window) with junk/!y0.
- S6-M2 control outputs (swap, OTA-chop phase, acc clear vs analog reset, y_force, tag-from-same-flop) absent; swaplate mutant
  is loop-level only, not RTL-applicable. Add cycle-level control trace golden (needs reset-window clocks, fch/fs SPEC rows).
- S6-M3 internal short/mode not in rule-10 latched set nor in tags -> short toggle mid-pair = silent wrong valid pair.
- minors: ota-only combo; order-1 acc2 null -> define; invalid after rst_n; cycle-level latch definition; +- order / +--+ rule 12;
  wire format/widths/"valid" pin vs invalid tag; PGA row; nm1/np1 reject via den (add stream-truncate, no-clear mutants);
  synthetic all-ones edge vectors; frame_ctr wrap (>=258 frames); dyadic offset vectors to exercise pair cancellation.
- Efficiency: pair_idx redundant with frame_ctr LSB + invalid.

## Review 2026-11-09 (5): S7 SPEC v1 freeze gate (SPEC @4de617b, DECISIONS D1-D45, all REVIEW-*)
No runs (read-only, 25-call budget). Text returned for work/v1-design/REVIEW-S7-2026-11-09.md.
Verdict: FREEZE WITH EDITS (text only, no sims). All prior Critical/Major closed in SPEC/DECISIONS/results except as below.
New findings (open):
- S7-M1 PROVEN(file): step-settling gate (D43a, SPEC OTA1/OTA2 rows) has NO threshold and g undefined -> cannot fail.
  Proposed h=0.5/fs, g=0.025/fs (h-2g = t_half 225/112.5 ns); limit from tier-1 macromodel step at gated point (eps and its
  nonlinearity vs step), or transistor OTA in tier-1 deck. Hand single-pole est ~6e-5 at both modes (REASONED).
- S7-M2 PROVEN(file): boost (D31) and trim (D42) said "latched at pair boundary" but absent from §3.8 config list, §3.7a(d)
  latched set, (e) invalid scope, tags, and golden config (README l.37/55). Boost reset value unstated (untrimmed hi corner 265 uA).
- S7-M3 REASONED: digital I/O undefined (ui/uo/uio map, config iface "ui pins or SPI", shift clock, buffering, fs_div codes).
  80-bit frame vs N64 slot 66 fs cycles -> fs-clocked serial cannot keep up; needs ext shift clock >= 80 fs/(N+2) (4.85 MHz) or byte bus.
- S7-M4 PROVEN(file): §3.4 Cs2 1 pF/Cint2 2 pF contradicts §3.0 0.5/1 (C_side2 2.01, beta2 .497); Ck2 0.25 pF missing.
Minor: pin-path dR 330 ohm uses Cp 15 fF but cap row allows 20 fF -> 250 ohm; §2.1/2.2/2.3/3.1/3.5/3.6/3.7/§5 stale text
 (VREF 1.2 provisional, F2/Q2 OPEN, Cs 1 pF noise, 50 uV target, PM>=60, SR>=10, beta .75, tau_ref .2 t_half, fch>631k vs fs/2,
 pair index, +--+, 8 pF Cint, r<=2.2e-3, 35 vs 52.7 uV, data-ready vs valid); fast-mode bullet cites s5f O0 3.7 ppm and "Open before
 S7" (closed by s5h r5 0.144/1.450, D39 control O2 verdict 3.43); cm2 137-173 dB is O0 (exempt quasi-static, label it);
 fp2 10.9/8.06 are O1; PLAN C1 row stale (A0 75, PM 60, SR 10) + PGA items in PLAN review additions; DECISIONS lacks supersession
 notes (D3->D17, D6->D14, D28->D31->D39->D41, D43a windows->D44); chop tag when sys_en=0 undefined; order-1 analog build undefined;
 chopper toggle vs Cs2 sampling OTA1 hold output (C5/C8 timing).
D45 user points rec: (e) confirm; (g) confirm (+golden vector, V4 row; silicon check of lf*Vos/(N-1)); (i) confirm with C1/C4
 gate reset residue <=1e-4 in 2 cycles at 4 MHz boost, chop edges in non-overlap gaps.

## Review 2026-11-09 (6): S7b re-check after WO-19 (b3b9ea1..5912796, D46, D47)
No runs. Text returned for work/v1-design/REVIEW-S7b-2026-11-09.md. Verdict: SMALL EDITS then FREEZE (step-gate text needs coordinator pick).
- E1-E24: applied except E13 labels wrong, E22 partial (PLAN C9 "shift-out"), E23 partial (no supersession on D6, D28, D31, D39b, D43a),
  leftovers l.216 "50 uV", l.230 "each word carries", 3.7a(c) "valid pin", l.22 "no bandgap" vs C6 bandgap current ref. S7-M2/M3/M4 closed.
- step_settle.py: OTA1 2 MHz == 4 MHz boost is exact time scaling (gm, ip, fp2 x2, ts /2; tmax 0.5 ns both) -> not a bug. PROVEN by code.
  1.6e-8 is real 2-pole physics (zeta 0.945, decay p2/2 = 9.4e7/s vs beta*wu 5.3e7) but only 1.6x the solver tolerance
  (reltol 1e-8 x 0.486 V = 4.9e-9 V); eps_NL 4.6e-10 (2.2e-10 V) is 20x BELOW tolerance -> numerical floor; O1 "exactly 0" = bypass.
- S7b-M1: SPEC transistor limit eps_NL <= 6e-5 -> INL bound ~1.9*eps_NL = 114 ppm vs 1.333 share. Proposed eps_NL <= 3e-7, |eps_dyn| <= 1e-4,
  eps_dyn vs same-run vo(inf) (removes 1/(beta A0)), steps both signs from x1 0 / +-0.72 V, reltol <= 1e-8 + /10 rerun.
- S7b-M2: step from rest is blind to in-loop slew knee: SR/2 copy eps_NL 2.8e-8 (passes any INL-derived limit) vs loop r3 SR 9.5 -> 4.6 ppm.
  Need in-loop gate: transistor OTA1 in tier-1 deck N1024 2 MHz (<=1.333) and 4 MHz boost (<=5), O1/O2. Mechanism unknown (Cs2 kick? hypothesis).
- OTA2 gate: 2x macro at 1.117 V loop-bound step is OK (resolvable, slew-sensitive, tied to 13.5->0.253 / 10.8->0.756 ppm).
- Provenance: 3.29/3.36 = D39 control fp2 x3/x3 N1024 4 MHz O1/O2 (verdict 3.434); 0.144/1.450 = A' (c) cold/(d) hot N1024 O2-only;
  0.403/1.982 = A' N256 (c)/(d) O1-only. SPEC "O1/O2 converged" true only for the first.
- 3.8a minors: debug y vs bit-clock edge race; rd needs sync; rd-clear race after status read; slow host reading every other frame -> zero
  complete pairs; status boost/trim = active not frame's. 48 MHz exact on demo board (firmware picks sysclk 96 MHz).

## Review 2026-11-09 (7): C1a OTA1+CMFB design note (WO-20; design/c1_ota1/DESIGN.md, sizes_draft.py, op_ac_check.py, run3.log)
No runs (read-only; ssh cat of run3.log + PDK grep). Text returned for work/v1-design/REVIEW-C1a-2026-11-09.md.
Verdict: REVISE NOTE FIRST (one short rev + re-spot at full sec.6 PVT), C1b tooling may start in parallel.
PROVEN from run3 op dump:
- A0 root cause = headroom, not topology: long ss/125 boost m_pl Vsd 0.453 (3.0-v(sa) 2.547) < vdsat 0.456 (triode, gds 10.8u vs 0.88u tt base),
  m_n Vds 0.4525 vs vdsat 0.339 (gds 9.2u). Hand A0 from op gm/gds: 57.2 dB vs SIM 58.3. tt boost m_pl margin 0.085 V -> 69.8 hand vs 71.
  Long variant halves m_pl W/L (40/4 vs 40/2) -> vdsat x1.4 -> why longer L did not help hot boost. Fixed V_SDL=V_FOLD=0.45 V don't track vdsat.
- ff/125 base 75.3 dB is genuine hot gm*ro (margins ok) -> longer cascodes; hot boost after headroom fix est. ~69-75 dB -> boost needs P1-type floor.
- V_PC at V_DIN 1.25 still -0.03 V at ss/-40 boost (note adds +0.15 twice). Pair saturation limit uses |Vt| 0.45 but SIM Vsg 0.86-1.24 V
  -> real lower-CM limit V_DIN <= ~1.5 V. Rec: m_pp gate to fixed low V (0 V), V_DIN floats = Vsg_pp 0.80-1.29.
- Tail clamp "PMOS diode tail->2.9 V" never conducts (needs tail > 2.9+|Vt| ~3.8 V). Fault reachable at power-up via Cint coupling.
- Noise mutants wrong: sinks W/4 LOWERS noise; 4 kOhm/gate +7.9 % only (140 uV). Servo-cap noise hypothesis falsified by hand
  (servo UGF ~1e-9 Hz); bad points have en(1k) ~5e7 nV, PSD slope ~f^-2.5, long variant only -> device-noise-model/bin suspect.
- Script: static A(v) uses target Vt not measured Vod (dc[:,2] unused); ss/125 base "empty array" = mag[0]<1 (dead OTA), not tooling.
- PDK: pfet_g5v0d10v5 vth0_slope 0.0 (invariant.spice:4942), mismatch via toxe/voff/nfactor; pfet_01v8 0.005856 confirmed.
REASONED: input chopper nfet_01v8 W1 at vg 1.2 V with 1.8 V drive (1.62 min) ~off (body effect) -> needs 3.3 V device + level shift;
 S5h x30 (28.5 ppm) is pole-order independent -> real FC at fp2/GBW 10-12 likely >5 ppm at hot boost 21.8 MHz; low-mult side not transferable.
 SPEC (B) corners tt/ss-40 miss hot (lowest GBW) corner. Cc 0.2 pF/side proposal eats C_L headroom (SR 18.5/1.5=12.3 <12.5).
P1 accept-modified (numeric boost floor from model N1024 + B at hot), P2 reject (premature), P3 accept, P4 accept as bound/plate-short rule.

## Review 2026-11-09 (8): C1a rev B (ca8a6f8; DESIGN.md rev B, sizes_draft, op_ac_check, WO-21 r1a-d/u1 logs)
No runs (read-only; ssh grep of WO-21 logs). Text returned for work/v1-design/REVIEW-C1a-revB-2026-11-09.md.
Verdict: PROCEED TO C1b WITH CONDITIONS (2 Major, cheap, before netlist freeze). No Critical.
Closed: M1, M3, M5, M6, m1, m4, m5, m7; M4 by rule (tb10 pending); M7 op/AC part (r1a = pre-clamp run, tt base REJECT seen; r1c rerun ok; mutant REJECTED).
Open: M2 (WO-22 + (B)), M8 (tb7 not run), m2 partial (f_cm vs m_plc L), m6 (tb8b).
New:
- RB-M1 PROVEN arith: DESIGN 2.9 vbnc/vbpc legs at I_nc/32 (0.49 uA) with diode geometry 5/16, 5/10 gives K_N 1.0, K_P 1.25
  (K is set by diode current / finger current x L ratio; spot deck used I_nc/4, I_nc/8). As written -> m_n/m_pl ~triode (rev A failure).
  Keeping spot geometry costs 5.9/11.8 uA -> fast ~206 uA, not 196. Fix: diode W/L /8 and /4 (narrow W, re-run unit K check) + restate current.
- RB-M2 REASONED: model uses SECANT A(|x|) (iadc._leaky table, vg=-vo/A), same as spot A_static (secant vs vod(0), dc vt +-1.4 step .1).
  Edge d(1/A): rev B ss/125 boost (81.2->73.6) 1.22e-4 vs S4 shape at 80 dB (->75 @1.4 V) 0.78e-4 -> likely > 5 ppm N1024 boost. Swing fix is correctness.
  np.interp clamps beyond table -> silent optimism; tables (csv) not kept in WO-21 r1 dir.
- Swing span (top-bottom) hot boost 1.32/1.37/1.34 V (ss/fs/sf 125) vs 1.40 need -> V_OCM shift alone cannot fix (bottom margin .01); K_P 4 alone ~0-0.06 margin.
  Option: m_pc W x2 (Vdsat_pc -0.09, plus V_sa up via tracking) ~+0.15 V, A0 up.
- m_plc L4 W30: +1.2 dB A0 (ro ~ L/I) but Cgg x4 -> k .77->.45, f_cm ~4 MHz base (tau 39 ns > 34 ns for 38->10 mV in 45 ns). Pair with Cc .2 pF (C_L sum 1.40) or L3.
- Boost-toggle 500 ns not needed: boost in latched set, first pair after change invalid (SPEC 3.7a e) -> >= 2 slots (33 us at N64/4 MHz). Integrators, islands reset each slot.
- Minors: OTA chop fs/2 at vg -> per-toggle injection integrates (not one-shot 60 uV); constant -> sys chop removes; sizes_draft CHOP_SW input W 2 vs DESIGN 4,
  CMFB_SPLIT .5 vs LOAD_FIXED .75; island 2/0.5 Ron ~2x table; fold chopper caps not in deck; V_BL0 replica leg not in bias budget; level-shifter skew 3.3 vs 1.8 V
  chopper inside g (6.25 ns at 4 MHz); V_ICM net must be bounded when bias invalid; C8 default with VDPWR off; A(v) must be with real SC CMFB.

## Review 2026-11-10 (9): C1a rev C (289aec7, 61ca6a7; DESIGN rev C + 2.10, sizes_draft, revc_check/inl, wo23 r5 json)
No runs. Text returned for work/v1-design/REVIEW-C1a-revC-2026-11-10.md. Verdict: PROCEED TO C1b WITH CONDITIONS.
Closed: RB-M1 (K by geometry, margins >= 0.067 V r5), RB-M2 at spot (boost table-INL <= 2.31 ppm, ideal CMFB), RB-m3, RB-m4.
Open/carried: RB-m1 (tb13), RB-m2 -> RC-M1, RB-m5 (C8 timing), RB-m6 (tb10 row text lacks VDPWR-off/floating V_ICM), RB-m7 (junction caps), RB-m8 (tables ideal CMFB).
New:
- RC-M1 PROVEN arith: precision A0 on m_pl soft-saturation cliff: r4 K_P 7->8 base = +3.0..3.5 dB. D55 (+1.16 at best, less on cliff) leaves
  fs/-40 ~79.6 < 80. Rec: K_P base 8->10 (vbpc I_NC/22.4, BOOST_SCALE 0.7 keeps boost K 7; 0 uA/0 area) + D55; sweep K_P 8..11 first.
  Reject m_pl L6: W120 to keep Vdsat -> bp C x2.25 -> ~5.9 us > CL-7 4 us; W80 -> Vdsat +22 %, boost span loss.
- RC-M2 REASONED (A_VT 8 assumption): 1:32 single unit-finger refs: tail ref 2.5 um2 sigma ~2.9 %, sink ~1.9 % -> 3 sigma I_fold/I_tail ~1.21,
  SR 13.2 -> ~12.1, GBW -9 %. Fix: series-parallel composite of unit fingers (area only). tb8b must measure ref->mirror ratio, not pairs.
- RC-M3 PROVEN(json): precision INL gate has no rejecting copy; mutant corners confounded (boost pc-short at ss/125, precision at tt/27).
  Flat gain cannot fail INL (52 dB -> 3.4 ppm; WO-22 flat 60 dB 1.47). Rec: per-mode CL-1c; precision = droop copy at ss/125 base
  (V_OCM +0.5 V or vbpc base /4, pre-predicted >= 1.5x gate) + synthetic S4-shape@76 dB table KAT (8.5/8.3 ppm); A0 row catches pc short.
- Q4: fp2/GBW quoted at 1.4 pF lump; real per-phase C_L 0.78/0.90 -> real GBW ~1.5x, fp2/GBW_real ~0.64x (+junction 0.7-0.8x) -> ~1.5-3.1.
  Do NOT size C_FOLD_EXTRA from lump numbers; first gate B fs/125 boost with C_FOLD_EXTRA 0 + absolute fp2/GBW at real loads; check tier-1 macro C_L definition.
- Minors: split-K departs from D43b x2 leg (vbpc boost x1.75) -> C6 spec + tb12; D55 f_cm boost ~8 MHz vs >= 9.4 needed for 38->10 mV in 0.2 t_half@4 MHz,
  scale Cr with Cc; beta1 0.001 on a proxy; span 1.41 is vs +-1.4 V table target, signal needs 1.2 (per-side check with V_OCM tol);
  revc_inl counts m_pl L0.5 rows as must-reject -> always exit 1; DESIGN header/1.1/1.2/2.9/3/5 + rev C table (m_bpc 1.25/6) stale.
Pattern: spot-deck "margin" numbers quoted against conservative lumps (1.4 pF, +-1.4 V) — always ask which reference the gate really uses.

## Review 2026-11-10: WO-24 C1b part 1 code, static (sandbox unreachable, nothing run; all REASONED or by-inspection)
Target: work/v1-design/REVIEW-C1b-code-2026-11-10.md (coordinator saves). Files: netlist.py, c1b_opac.py, c1b_gateb.py,
revc_check kp, revc_inl role(), test_c1_netlist.py, gen_tier1 ota1_xtor (uncommitted on 3492e65).
Held up: core connectivity (pair/pp/sinks/fold chopper/nc/pc/pl/plc), chopper pairing (chp+chlp straight = non-inverting
inp->outp), xtor inserted inverted (inp=vg1n) = macro sign; SC CMFB polarity (sc and dc eq); K_P 10/7 and vbl0 1:30 density
arithmetic; composite W/L = finger; bulk-at-rail composite = exact series-parallel equivalence (Galup-Montoro JSSC 1994);
flagged (1) CM-only DC eq correct (avg R per side 10 MOhm base would fake ~15 dB A0 loss; Cr is a settling load, linear).
Findings (open):
- C1b-M1 gate B: Brstb = per-conversion rst -> ctl clamped each reset, CM loop open with diff short; op at t=0 CM unregulated;
  first block (u=-0.9 endpoint) starts with CM transient (~0.85x into island CM). Fix: start-up-only rstb + dummy conversion.
- C1b-M2 sr95 copy rated at 1.4 pF; real integ load ~0.84 pF -> ~16 V/us (likely blind); tail-only cut raises I_NC; crash counts as REJECTED.
- C1b-M3 PROVEN by inspection: revc_check kp "p15" == 30/4 (SIZES already 30/4, override {}); needs dict(M=3, L=2.0).
- C1b-M4 opac LOADS 0.78/0.90 stale vs D55 (Cc .2, Cr .05): ~0.84/0.99 pF.
- C1b-M5..7 fail-open broken-copy verdicts: opac mutant any-fail, gateb sr95 crash, revc_inl empty dir / missing mutpcb2 -> exit 0.
- Minor: test refs_ok blind to series wiring; Cp_vg undercount (closed-switch full Cgg, Sci4, junctions, pair Cgd Miller ~+30 fF);
  audit filter masks all; no servo-lost row; stale csv; combine() missing; fold chopper 1.8 V overstress at bias start-up;
  load/cascode offset+1/f unchopped in OTA-chop mode; c_out_ext 0.02 pF low.
Pattern: broken-copy verdicts written as "not ok" -> crash = good. Check every mutant path for this.

## Review 2026-11-10: WO-24 netlisted OTA1 A0 gap (opac vs revc_check kp spot), read-only, logs in work/v1-design/results/wo24
- ROOT CAUSE (PROVEN from logs): composite 4x4 refs (netlist.py:60-72,105-107; REF_COMPOSITE sizes_draft.py:118) mirror
  MORE current than single unit-finger refs: I_tail 21.3-23.1 uA vs design 18.5 (spot 18.64); I_NC actual/design
  1.14-1.19 at -40, 1.02-1.09 at 125 (temp-dependent ratio error). Cascode-bias diodes m_bpc/m_bnc stay single-finger at
  fixed I_REF (I_NC_design/22.4) -> effective K_P 10 -> ~8.4-8.8 at cold (boost 7 -> ~5.9). Spot ff/-40 K8p30 79.92 dB
  ~= netlist 80.23. A0_hand matches AC (+0.4) so not topology (fold Ron, junction caps, CMFB DC-eq excluded).
  Mechanism (stack body effect, bulk at rail / CLM-DIBL per finger) REASONED. I_vdd 60 vs 47.5 uA expected: +10/+20 uA unintended.
- Spot kp fs/-40 baseline invalid: .op failed (NaN margins), A0 from AC's own op; clean pair is ff/-40.
- mut="ref_single" exists in netlist.py but is unused by any tb/test.
- Gate B smoke (real SC CMFB, fs/125 boost): out CM 1.538-1.553 vs 1.50 (+38-53 mV), dummy-conv 2.61 V.
- Boost fp2/GBW 1.08-1.61 at integ load vs WO-22 window 2.2-3.0 (defined at lump); gate B covers fs/125 only (PM 58.8), not ss/-40 (PM 52).
Status: open; options given (re-centre composite refs / I_REF; K_P up; Cc up as joint f_cm + fp2 lever).

## Review 2026-11-10: WO-25 (D58 ref trim + replica cascode bias, D55 revert; 7de6857 d07bd49 f83d326), read-only, logs results/wo25
Verdict: HOLD before gate B (no Critical). Replica topology correct (KCL (2I_SINK-I_TAIL)/32 = I_NC/16, polarity, no zero-current state).
- W25-M1 (PROVEN from logs): precision A0 margin is load-bearing on the replica's systematic +5-9 % K_P error (m_rn drain ~2 V, CLM,
  x1.59 leverage of subtraction). kp_fixed K_P 9.73 vs 10.93 at ff/-40 -> A0 78.79 vs 81.78: ~2.5 dB per K_P unit at cold.
  Replica single unit fingers (m_rt 1, m_rn 2; not composite) sigma_K ~2.7 % REASONED -> sigma_A0 ~0.7 dB. Fix: raise base K_P by
  design (bank 5->4, K_P 12.5; base span 1.756 vs 1.6 has room), then cascode/Vds-match m_rn; more replica fingers.
- W25-M2 (PROVEN arith from logged ratios): V_OCM err +58.8 mV ff/125 boost > CL-2 38 mV bound (SPEC row 98). Cause: tail/sink/plr
  composite ratios drift in opposite directions over T (tail 1.15->1.25, sink 1.19->1.11, plr 1.09->1.15); m_plc (25 %) absorbs
  the I_NC error x4: ff/125 base plc needs -31 %. vbl0 trim is a minor term (+-4 % of plc). Fix: replica-referenced V_BL0
  (I_NC replica minus fixed-load replica), or parallel-only unit-finger refs (tracking by count).
- W25-M3: I_tail +-3 % row is a proxy; real floor = SR boost 25 V/us at 1.4 pF: 35.09/1.4 = 25.06 (0.25 % margin). +-5 % would
  allow 23.9 < 25. Replace with asymmetric derived row (SR floor, current ceiling); shift trim up ~2 %. Per-finger B-S composites
  unsound (mechanism is DIBL/CLM at low per-finger Vds; common-bulk equivalence already exact for body effect); C6 compensating drift unsound.
- W25-M4: K_P row cannot reject kp_fixed (old wiring is closer to target than design). Proposed tracking row: ibn x1.05 copy,
  |dK_P/K_P| <= 2 % (replica ~0, fixed ~-7.6 %).
- W25-M5: gb.sh runs fs/125 boost only; SPEC (B) lists tt/27, ss/-40, ss/125, fs/125; worst PM ss/-40 boost (52.6, fp2/GBW 1.11).
- minors: bank switch -> switch gates not source path; m_rt/m_rn sizes hand-copied (derive from m_t/m_n, test equality);
  REF_TRIM base-only (boost plr/vbl0 ratios 1.134/1.105 vs 1.121/1.081); no MC of replica; A0 gap vs WO-24 single-finger 83.66.

## Review 2026-11-10: WO-26 (D59 parallel 1:8 refs, K_P 12.5, rcb replica cascode, gate-path bank; 6dccfd3 0ed1112 b177d23 10ffd21)
Verdict: PROCEED to gate B results (running, wave 1 of 10 at review time); no Critical. Item-1 ratio exit: accept systematic
offsets (a), but re-gate on dependent rows + mismatch allotment; ratio exit as written keeps op/AC EXIT=1 forever (blind gate).
- W26-M1 PDK FACT (PROVEN, installed PDK .ciel/sky130A invariant.spice): pfet/nfet_g5v0d10v5 vth0_slope = 0.0; HV MC mismatch
  only via toxe_slope (p 0.012, n 0.008/0.0205) + nfactor_slope (p 0.02, n 0.12) / sqrt(l*w*mult). PDK MC on HV devices
  likely UNDER-reports Vth mismatch -> "fake MC" risk; cross-check with hand Pelgrom (thick ox A_VT ~ 8-12 mV.um, REASONED).
- W26-M2 (REASONED): nominal-only margins thin vs mismatch: boost SR 25.54 (2.2 %) sf/-40; m_tr 4 fingers 10 um2 sigma_I ~1.5-2 %.
  V_OCM 30.8 vs 38 mV ff/125 base; m_bl0 = ONE m_plc finger (3.75 um2) -> sigma dV ~ 3-6 mV straight into V_OCM.
  SR row is a 1.4 pF proxy (real load 0.84-0.99 pF) -> real risk is V_OCM, not SR.
- W26-M3: op/AC exit permanently red (18 ratio REJECTs per group) -> same pattern as revc_inl always-exit-1.
- minors: no row on V_rnd/V_fa or replica-device margins (run-1 failure caught only via K_P row); replica_sizes_ok skips
  m_rcb/m_rcp; bank_ok skips Sbkp gate + mbpxs count; rcb density 9.4 vs m_bnd 12.6 uA/(W/L) -> V_rnd 40-100 mV below fa;
  K_P tracking only for ibn, not ibtp; f_cm not re-measured; bank control needs 3.3 V level shift (static in sim).
Held up: rcb leg (no zero state: ibp from fixed I_REF), gate-path bank switch, A0 gap explanation, broken copies all REJECT.
Pattern (recurring): exits defined as proxies (ratio, I_tail +-3 %) get replaced by derived rows; keep asking for MC allotment.

## Review 2026-11-11: C1b milestone after WO-27..31 (D59-D64), read-only; logs regr/tt/WO-31-1cf257d/out/{opac,tb9,gb}
Verdict: PROCEED (no Critical); C1b not closable yet. Dual-path CMFB topology checked: m_ia follower (mia2 diode on bli) = unity
follower ctl->bli, Cr refresh to (vocm,bli) => outcm-vocm = (ctl-bli) + q_inj/Cr; sign correct; nominal CM PM >= 77 (sf/-40 binteg),
peak <= 0.58 dB; f_z/f_cm ~0.1. Pelgrom rows reproduce (A_VT 12: m_t 720 / m_tr 90 um2 -> sigma 1.11 % base; m_ia 70 um2 -> 2.0 mV).
- W31-M1 (REASONED, bkt log PROVEN): SR-3sig / ceiling+3sig leave I_REF_btp window ~ -2 % / +1.6 % (bkt x0.95 -> 12.11-12.42 < 12.5).
  Untrimmed sky130 reference cannot hold that -> C6 spec issue. Options: I_REF trim, re-base SR floor on gate-B knee (10.2 V/us base), ext ref.
- W31-M2 (REASONED, masy log): CM-to-DM row nominal = numerical floor (symmetric netlist); masy 1e-4 -> 0.55 uV vs 0.256 bound,
  so realistic MIM/pair mismatch ~1e-3 -> ~5 uV under the worst-case bound. Needs mismatch copy + signal-dependent-CM bound
  (Cc/Cr p/n mismatch converts DM swing to CM; op/AC DC model CM-only, gate B symmetric -> both blind).
- W31-m3 (PROVEN logs): start-up row (tb9 check_su, |cm-V_OCM| max over last T at 4 us) reads the ripple floor: sulo8 (settled)
  9.06 vs sulo 9.56 at fs/125; all su copies 6.9-9.6. 4 us = CL-7 toggle number, not a power-up need (dummy conv >= 256 us). D64 kept (benign).
- minors: SPEC.md:98 still says "<= 10 mV in 0.2 t_half" (D63 changed); sr95 at 9.5 V/us = 38 % of floor (gross only, INL 5 %);
  gate B corners lack sf/-40, ff/-40 nominal; output clamp PMOS W4 L0.5 to V_OCM 1.5 V weak (TG option); Sbk/mbku need BBM + LS.
Next-WO order given: row fixes -> noise -> tb12/tb11 + C6 interface -> delvto hand-MC -> stress -> 45 PVT + gate B extra corners.

## Review 2026-11-12: C3 stage-1 design note (WO-44; DESIGN.md, sizes_draft, spot_tran, results/wo44 13/13 decks)
No runs (read-only). Verdict: REVISE (interface), circuit OK to netlist after phase decision.
- C3-C1 CRITICAL PROVEN by inspection: strobe phase contradiction. c9_seq.v:41 comp_s<=comp_in at s_tick (bit-clock fall), :51 y_dac<=comp_s at fs_tick.
  C4 DESIGN.md:22-26 fires strobe from phiIl FALL (after s_tick) -> C9 captures previous decision -> +1 full cycle loop delay.
  C3 DESIGN.md:42-43 wants fire >=0.4 t_half BEFORE capture "while x2 held" -- impossible: x2 integrates in phiI (bit clock high).
  Options: (a) capture comp_in at fs_tick (rising) straight into y_dac (CL-23/D66 AMB-01 change; F8 single flop), fire in phiS on held x2 [recommended];
  (b) keep RTL, fire mid-phiI on unsettled x2 (decision on settling residue; needs C9-derived early strobe, analog delay can't hold 45 ns window).
- Offset: PDK HV nfet mismatch toxe-only; probe was 1 geometry (5/0.5, 10 uA, diode) -> A_VT-eq 9.29 not proven area-scaled/bias-valid.
  T3 as written (tt_mm + injected 12) double counts: RSS 15.2 -> set A 3sigma ~24 mV REJECT, set B 18.2 (20.9 slope1). Rec: inject sqrt(12^2-9.3^2)=7.6
  so total 12, or tt (no mm) for HV + injected 12. Rec set A' = IN x4 (kick unchanged) + latch 4/0.5: 17.7 mV (20.5 slope1). Row 105 soft (SPEC 3.2 "don't overspend"; sys chop removes).
- brk_starve 6.4 ns vs 33.75 blind (spot 1.12-1.39 ns ss). T6 starve also blind (t_int not tau_reg). Rec: requirement copy that breaks timing (wrong strobe phase in T10; weak strobe level) + band row t_dec within [0.5,3]x of spot/hand.
- HV tail unnecessary REASONED: tl only charges via M1/M2 from dp/dn <= VDPWR (DESIGN:36 "tl ~2.6 V" wrong). Efficiency.
- CM kick 45 mV (hand 25-30 low); x2 not sampled in order 2 and vg charge conserved -> no state error; T5 symmetric node hides CM->DM; behavioural R gives CM recovery via diff R (optimistic).
- Open Qs: order-1 comparator input path x1 (mux R adds to kickback); q load 5 fF vs routed comp_in.

## Review 2026-11-13: C4a stage-1 note (design/c4_sw/DESIGN.md, spot.py @03e28fe, results/wo46) — read-only, no runs
Verdict: proceed to netlist after doc revisions (no re-spot needed except optional Sg leakage spot). All REASONED except PDK cell list (PROVEN).
Findings (open):
- C4-M1 order-1 loop delay: comparator reads x2 = c2*x1 sampled in previous phiS -> y[n+1]=sign(x1[n]) vs model iadc.py:9 y[n]=sign(x1[n]) -> one extra delay in order 1 (order 2 matches). Model/golden/order-1 study must add it or swing/resolution claims for order 1 are unverified.
- C4-M2 early->late (bottom-plate order) margin at thresholds ~0.1-0.25 ns at ff/-40 (early50 0.70, edge 0.57, t-c skew <=0.24 ns); limits measured at 50 %. Gate at thresholds, lengthen K_E.
- C4-M3 injection tb #3 sweeps CM only; top-short charge split depends on bottom-path Ron (12/36 TG, ~0.4-1.25k) which varies with differential input; Ron*Cs ~0.2-0.6 ns ~ edge -> odd-order DM error not cancelled by sys chop. Add differential sweep + INL readout.
- C4-M4 VDPWR-missing: CL-5 'isl closed while rst_n low' unmeetable without detector (rst_n is 1.8 V). PDK has lsbuflv2hv_isosrchvaon_1 / clkiso_hlkg_3 (SLEEP_B) and lsbuflv2hv_symmetric_1 (PROVEN, IIC PDK).
- m: gated phases (phiSl*swap, phiIl*y) not in spot, feedback from ungated -> g at switch gates smaller; control LS edges arrive before phiSl falls (DESIGN 5(c) claim wrong; harmless only because swap/short change in reset window).
- m: g metric g_n/g_p separately, no cross n-of-A vs p-of-B; edge_max 1 ns limit not derived (SC, not CT like pthomas) -> demote or derive; Sg off Vds = Vin_cm-Vref_cm -> CM-dependent subthreshold leak, T-switch option; vg Ron 1k over-tight (pole 1/(2pi Ron Cs) 318 MHz) -> W 4-6 OK.
- m: phi_C needs hv2lv LS (C3 is 1.8 V) not in C7 list; SPEC 3.8a line 298 still CL-23 falling-edge text (D74 not in SPEC); C3 DESIGN l.41 g=0.05T vs SPEC 0.025/fs; S2cm/Sk0 phases must be late (phiIl/phiSl).
- Q7 int2 order-1 reset: accuracy irrelevant (x2 unused in order-1 reconstruction; error at quantizer is shaped) -> 70 ns ample if reset switch is directly across Cint2; rst2_o1 delay can be ~10 ns min (t_dec 0.6-3.4 ns), self-timed option.

## Review 2026-11-13: DESIGN_BOOK.md accuracy (book commit 253d9bf), read-only, no runs; ~60 numbers sampled
Errors found (open, book-level; several inherited from sources):
- L59 resolution formula log2(FSR/vrms) wrong vs its numbers (CTX:119 same): numbers = log2(FSR/(sqrt12*vrms)); 1.5 uV -> 21.4 b by stated formula.
- L85 "2nd-order 1-bit OSR128 ~85 dB in theory" (NOTES:47) contradicts book's own formula (100.3 dB).
- kT/C-only noise has 3 values: S3 base 0.556 (s3_budget:31), C1 n_ktc 0.556-0.559; SPEC:25 + book call 0.71 "kT/C-only" but D22 says 0.71 = ota+sys model; SPEC:18 0.54->0.76.
- L254 S2 13.79/7.20 uV include vres 5 uV (closed form alone 8.80/2.20).
- C9 PnR "PENDING" stale: wo58b README EXIT=2, setup -1.60 ns @ss_100C_1v40 (44.6 MHz), TT 2x rule fails; run commit 3e1e9ea not a166371; D79/WO-60 exist.
- Order-1 follower "x2 = k*x1" (C4 DESIGN:67) physically c2*x1 (equal 0.5).
- Pelgrom form sqrt(1/WLa+1/WLb) => project A_VT is per-device (x sqrt2 vs Pelgrom pair def).
Confirmed real gaps: no transistor 2 MHz gate-B (<=1.333 ppm) in any WO README (only tier-1 D44 0.10 ppm);
 fast current: OTA1 netlist boost 122-124 uA of the 172 uA system estimate -> ~180 uA nominal est. with OTA2 x2 (REASONED).
Held up: D62->D63 story, WO-50 nonphysical .dc, CL index vs SPEC:390-419, S3/S4/S1/leak/WO-26/31/41/43/53 numbers, reconstruction == iadc.py:350.

## Review 2026-11-15: DESIGN_BOOK.md accuracy (commit c1fa950, Proposal summary for Chipalooza)
No runs. Returned to caller only. Key findings (open):
- CRIT novelty: "no earlier TT ΣΔ has an on-chip decimator" false per NOTES (TTSKY26A-ADC-8BIT sinc1 counter on chip; tt09 decimation filters). Scope to analog modulator + CoI in same tile; firmware does normalisation + chop demod.
- C1: book calls O2 trigger "gate/2 (D48 rule)"; D43c trigger is <3x margin (gate/3). Boost gate B on WO-52 netlist = fs/125 3.14 + ss/-40 0.71 only, O1, fs/125 needs O2; tt/ss125 not run on current netlist. "O2 is then the converged result" contradicts D43c (|O2-O1| 10x, tight O2 aborted, vntol never tightened; O2 0.14-0.16 ppm below vntol-equiv 0.25 ppm).
- C3 mechanism: "only the keeper pulls op back" wrong per netlist: R0 (pfet 1.0/0.15, gate clk) is on in precharge; keeper dominates only while R0 turns on during the edge.
- PDK device page: nfet/pfet_01v8 SPICE valid Vds/Vgs to 1.95 V, Vbs to -1.95 V; project limits 1.98 V and junction 4.95 V (CL-33) are outside model-validity range -> project rules, not PDK ratings.
- Proposal: supply row compares 200 uA analog vs MCP 145 uA total while C9 est 1.705 mW (~0.95 mA @1.8 V); "all PVT + MC" is plan not fact; T3 "pass" while plaus limb REJECTs; T2 cyc rows never run on rev f; area (C9 40 % + MIM 12 % + C6 <=10 %) and digital coupling missing from top risks.
- Template: TT tools tt_analog_2x2_3v3.def = 319.24 x 225.76; ttsky-sigma-delta copy says 334.88 (old). SPEC still ~334.

## Review 2026-11-22: WO-108 BIAS_EXT pre-sim (design/cz/c6_cz.py @5735005, results/wo108/README.md, D99)
Read-only; probe deck /tmp/rev_wo108 on sandbox (TG Ioff/Ron, xhigh_po 670 um). Verdict: fix bench/gates first, then GO.
Port currents (sizes_draft): ibtp 2.357, ibn 3.122, ibp 1.475, ivbl0 0.492 uA base -> ivbl0 at 1 uA ext = 98 nA (2 % = 2 nA; G4 0.1 % = 0.5 nA).
C6 compl margins WO-99 (1x): min 0.67-0.97 V on ibn (tt 0.84, fs/-40 0.67) -> TG drop small vs margin at 1x; 4x/8x unverified.
Findings (open):
- B1 bias_sel is a CZ "Control input" (1.8 V) but wrapper feeds it straight into an hvl inv (bench drives it at VAPWR); no LS anywhere (no top uses c6_cz).
- B2 G4 / "missing isolation switch" vacuous: with bias_ext held 0 V the ext mirrors are off, so the ext TGs isolate nothing; need sel 0 with bias_ext driven (CZ harness left on) + ext-TG-shorted broken copy.
- B3 kwrong REJECTs only via tt absolute limb -> DOES NOT REJECT at ff/125/3.6 mutant corner; ext absolute = mirror ratio only -> abs limb valid at all corners.
- B4 README item 4 wrong: diode-connected ext stack self-discharges its gate (I(t) ~ C nVT / t) -> ports and ok drop within ns-us after bias_ext lost; no bleeder needed; make info_reopen a gated row.
- B5 detect: no hysteresis (slow edge into C9 via lsbufhv2lv), xhigh_po corners not in tt/ss/ff libs (passives typ) -> threshold spread only hand-argued; no broken copy on the present limb.
- B6 corners miss fs/-40 (C6 ibn CLM worst +4.2 %) for 20 uA tracking; boost at 20 uA (8x) claimed but not run; dead-core fallback (nosu core) not run; no pin leakage / pad C on bias_ext.
- Options: K integer (I_NOM 5.35 uA -> K 5, or 4.28 -> 4) for unit-finger layout; PMOS-only sink switches / NMOS-only ibn; core header switch in sel 1 (covers hog/oscillating C6); long-L PMOS pull-up vs 670 um xhigh R; Schmitt (hvl schmittbuf_1 exists).
Held up: hvl pin orders (inv_1, mux2_1, lsbuflv2hv_1) PROVEN vs PDK; replica topology = C6 mirror side (unit current bias_ext/(2K) = 0.535 uA at 5 uA); swapsel/efinger(-36 %)/nodetect/leaky(0.75-0.83 %)/overv REJECT by hand; stress claim right (all nodes bounded by VAPWR, diode always on pin).
- Probe note: TG Ioff/Ron + xhigh_po probe (3 decks, timeout 500 s) produced no output: sandbox load ~12, ngspice at ~15 % CPU, killed before flush.
  Next time: write results with `echo`/wrdata to a file early, and use timeout >= 900 s under load. Leakage numbers stay REASONED.
- Severity given: Major B1 (LS on bias_sel), B2 (ext isolation untested), B3 (kwrong vacuous at ff). Rec: bench fixes B2/B3 + gated reopen row, decide B1, then GO.
