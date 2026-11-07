# v1-design decisions (coordinator), 2026-11-07

| # | Decision | Reason | Alternative | Reversible |
|---|---|---|---|---|
| D1 | USER: gated flow system → component → verification suite; proceed only if every check passes at every corner; verification copies Paul Thomas's method (params.py single source, tiered sims, per-block tb + xcheck + MC + PEX re-sim, ACCEPT/REJECT gates, top PEX acceptance) | user rule 2026-11-07 | — | user decision |
| D2 | USER OK 2026-11-07: "all corners" = full 45 PVT + MC for tier-0 system specs and every tier-2 block (schematic and PEX); top-level transistor runs at 5 extreme points with ≤2048-cycle windows | full-matrix long top transients are infeasible in ngspice (TilesOS 8192-bit failure; Paul gated on 2048 bits) | full 45 PVT on the transistor top (weeks of sandbox time, likely non-convergence) | cheap |
| D3 | SPEC VREF 1.2 V provisional; S1 compares it with 2.048 V + c1 = 0.125; user picks if both pass | model ran at 2.048 V; swing at 2.048 V/c1 = 0.25 is marginal for a cascoded OTA | lock 1.2 V now | cheap |
| D4 | OTA chop stays in SPEC pending S2; system chop is mandatory | OTA-chop-only residual ≈ Vos/N in incremental mode | drop OTA chop now | cheap |
| D5 | Input switch: 3.3 V TG, bootstrap only if C4 shows need | full settling makes Ron nonlinearity irrelevant; bootstrap adds device stress and sim work | bootstrapped (previous SPEC) | cheap |
| D6 | PGA x1/x2 in v1, x4/x8 stretch; entropy section of PUBLICATION_PLAN optional | consistent with first-cut scope cuts (ROADMAP/SIZING) | x1–x8 in v1 | cheap |
| D7 | Corner set (SPEC §6): tt/ss/ff/sf/fs, −40/27/125 °C, VAPWR 3.0/3.3/3.6, VDPWR 1.62/1.8/1.98, MC ≥200 at tt + ≥50 at worst PVT, fs 0.25/2/4 MHz | ROADMAP Phase 2 corner list + ±10 % supplies | 0–85 °C | cheap |
| D8 | `git init` of ~/projects/tt (repos/, pcb/, .venv excluded via .gitignore); initial commit 48a75e6 | WOs need atomic commits (WORKFLOW §3) | separate design repo | cheap |
| D9 | WO-01/02/03 run in parallel as file-disjoint WOs; commits path-limited (`git commit -- <paths>`) | S0 (infra) and S1/S2 (model) share no files; WO-02 alone owns iadc.py | serial | cheap |
