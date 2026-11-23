# bugs (C9)
No DUT bug confirmed as of 2026-11-11 (WO-38). TB bugs found and fixed in WO-38 (all triaged TB, not DUT):
- TB-1 vectors: golden frame status_word assumes the host acks every frame (no rd -> overrun); harness now acks.
- TB-2 golden off-0 writes placed exactly on the latch edge changed cfg_pending at the load (golden places them
  after); now 1 clk after, plus an extra exactly-on-edge frames-only run.
- TB-3 bus lag picked from a constant value; now only from a unique match.
- TB-4 Ref A stepped test-coroutine pin writes one edge early (rst_n/ui); now uses the values applied to the DUT.
  Caused false fails in d_cfg05, r01 (reset edge) and d_bus02 (latency 4).
- TB-5 host-read tasks survived a reset; now flushed.
- TB-6 formal F02 too strict at the first latch after reset (legal ld pulse loads 0); now tied to the fs start edge.
Observation (not a bug): DUT clears frame_ready 1 clk after the synchronised rd rise (allowed by CL-12).
## TB-BUG (WO-40, 2026-11-12, fixed in 6575b78): a_rst01_async_mid drove dut.rst_n = 0 mid-clk directly but left
tb.a_rst_n = 1, so Ref A stepped one edge un-reset while the DUT was in reset (22 mismatches, WO-38-...-d rerun).
Release latency was deterministic 25 = 1 + div(24) in every reset, i.e. already the D70 value. Fix: set a_rst_n = 0.
Also tightened: release latency must now equal Ref A's D70 value exactly (was: deterministic and <= div+4).
## WO-42 TB bugs (no DUT bug): TB-7 host read queued by a load on the edge between tb.reset() and rst_n at the pin -> stale
ref frame vs post-reset bus (SOAK s1, 1 of 18.25M clk checks; DUT bus = reset values = correct). Fixed a429510.
TB-8 p_wphase parsed even_* as edge phase (c03 crash); TB-9 g_place aim check 1 edge late. Fixed 36b3642.
## WO-75 TB bugs (no DUT bug): TB-10 X-01 s2 s01 edge-1 fail: rst_n=0 from t=0 gives no negedge, Verilator rand-init flops
not cleared before the first edge (sim artifact); fixed 87a05a2 (rst_n 1 -> 0 at 1 ns). TB-11 bench top bypassed the tt_um wrapper
(M45 survived); fixed 87a05a2 via defparam (Icarus OK, Verilator rejects it: open).

- 2026-11-14 WO-83: no new RTL bug. Stale RTL comment c9_seq.v:29 "sticky done flag (counter freezes)" contradicts D88 (Low, comment only).

## cz_spi (D102) read-only review 2026-11-24 (no sim). No functional bug found by reading. Candidates logged as ambiguities:
- SA-SPI-3 (potential Medium): DRDY (frame_ready) is on no wrapper output in SPI mode (data[7:1]=0, dbg forced 0).
- Low: stale snapshot bit 95 visible on MISO ~3-4 clk after CS_n fall (snap_valid cleared only at sync'd fall); only
  matters when the 32-clk setup rule is violated. Low: reset release with CS_n low starts a capture mid-frame.
- Low/lint: reg `torn` set but never read (torn 3rd-attempt snapshot has no flag besides tag/status ctr mismatch).
