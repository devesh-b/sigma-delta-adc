# WO-56 (C3d): comparator stress fix without breaking function

Commit 2e55372 (rev d netlist, sizes, testbench). Design note: `design/c3_comp/DESIGN.md` §4b.
Frozen copy: `/home/mempool/regr/tt/WO-56-2e55372` (`c3_comp/`, `.spiceinit` `num_threads=1`), launcher `/home/mempool/regr/tt/wo56_launch.sh`. Full run `run/`: 60 decks, lpool launched detached 2026-11-13 10:40 IST (box load ≈ 7 on 6 cores from other users, so the pool started with 1 slot). Job order `run/jobs_ord.txt`: priority decks first (one_ss-40_162, st_tt27_a, st_ff-40_a, st_revc_tt27_a, cyc_ss-40_162, cyc_tt+27_180, cyc_info_revc_ss-40_162, cyc_brk_nobuf), then the rest. WO-51 took 2 h 45 min at ≈ 3–6 slots.

## Pending: collect when `run/pool_logs/POOL_DONE` exists
    cd /home/mempool/regr/tt/WO-56-2e55372 && . /home/mempool/tt-sd/.venv-sbx/bin/activate && python c3_comp/c3_tb.py collect run
Copy `run/summary.txt` here as `summary.txt`, then delete raw files if any (`find run -name '*.csv' -delete`). Exit 0 means every nominal row ACCEPTs and every broken copy REJECTs. Rows marked `(i)` are info only.
Read from the summary: `ap_an_pre_fire_mV` on `cyc_info_revc_*` (rev c, expect tens–hundreds of mV after the ±0.3 V cycles c0/c3) vs `cyc_*` (rev d, expect ≈ 0) = item 1 evidence; `st_*` max18 for item 2; `mc_*` (offset MC recomputed, core changed); `one_ss-40_162` T2band (HV tail, band 0.56–3.36 ns).

## Item 1: diagnosis (hypothesis, to be confirmed by the probe)
Rev c had no precharge on the cascode nodes ap/an. They charged only through K1/K2 to VDPWR − VT,HV, ending in subthreshold, so after a big decision ap ≠ an at the next strobe. The lower node turns its cascode on first and favours the previous decision: the small cycles after ±0.3 V (c1, c4) read the wrong sign and q moves only on the next big cycle (t_dec ≈ 500 / 250 ns in WO-51). Matches: T7 fails c1/c4 at all 9 PVT, T1 (cycles after small ones) passes, CM 1.8 V passes (more overdrive pulls both nodes to tl every decision).
T8 in rev c moved to `st_t_ds`: tl followed the floating ap/an up with x2 high; in rev b, dp/dn were diode-clamped by the precharge PMOS and tl followed them.

## Item 2: fix (rev d)
HV PMOS precharge P1/P2 (pfet_g5v0d10v5 2/0.5, gate = strobe) on ap/an, and the tail made HV (nfet_g5v0d10v5 5/0.5 ×4). tl, ap, an then touch only HV devices; dp/dn stay behind the cascode and their precharge PMOS. Options compared in DESIGN.md §4b (cascode fix chosen; input R + clamp, fully HV core, sequencing rejected or not needed). `starve` broken copy re-based on the HV tail (64× less W/L). New info copies: `st_revc_tt27_a`, `cyc_info_revc_ss-40_162`, `cyc_info_revc_tt+27_180`.
