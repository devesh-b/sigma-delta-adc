`timescale 1ns/1ps
// tb_cz_spi.v -- spec-derived bench for cz_spi (D102 SPI read port, Chipalooza variant). NOT YET RUN.
// Spec sources: work/v1-design/DECISIONS.md D102; PROPOSAL_CHIPALOOZA4.md "SPI read port"; design-review findings
// SPI-1..5 (2026-11-23); design/cz/rtl/cz_top_wrap_notes.md. Requirement IDs and the test map: VPLAN_cz_spi.md.
//
// Structure: the real frozen C9 (sd_adc_c9, PW_BITS 8 / BIAS_BITS 2 for a short power-good hold) + cz_bus8 + the DUT,
// wired as in cz_top_wrap_notes.md. A second C9 + cz_bus8 ("twin") gets the same clk/rst/cfg/comp inputs and the
// same rd, but no wrapper: it is the reference for the pass-through mode (slot must behave as without the wrapper)
// and the parallel-bus reader for "the same frame". Its state is checked in lockstep with the DUT-side C9 every clk.
// Frame history (scoreboard) is taken from the C9 hold register at every load; every SPI frame is compared with it.
//
// Plusargs: +seed=N   +STOP_ON_ERR (mutant runs)   +STRICT_ONE_ACK (a re-read of an already acknowledged frame
//           must not pulse rd; expected to REJECT the current RTL, see VPLAN SA-SPI-1).
// Output: "CHECKS=n ERRORS=m", STAT lines, then TB_PASS or TB_FAIL.

`define ERR(m) begin errs = errs + 1; if (errs <= 60) begin $write("ERR t=%0t: ", $time); $display m ; end end
`define CHK(c, m) begin checks = checks + 1; if (!(c)) `ERR(m) end
`define QCHK(c, m) begin checks = checks + 1; if (!(c)) begin if (quiet) qbad = qbad + 1; else `ERR(m) end end

module tb_cz_spi;
  localparam real TCLK = 20.834;            // 48 MHz
  localparam real THC  = 10.417;
  localparam real T12  = 41.667;            // SCLK half period at 12 MHz (spec maximum, = clk/4)
  // order 1, n_code 0 (N = 64), fs_div 0 (clk/12), sys_en 1, ota_en 1, short 0, boost 0, trim 4 -> slot 66*12 = 792 clk
  localparam [15:0] CFG = 16'h1064;

  integer errs = 0, checks = 0, qbad = 0;
  reg     quiet = 1'b0;
  integer seed = 1, seed_c = 77;
  reg     strict_ack = 1'b0, stop_on_err = 1'b0;

  // ---------------------------------------------------------------- clocks and pins
  reg clk = 1'b0;
  always #(THC) clk = ~clk;
  reg rst_n = 1'b0;
  reg spi_en = 1'b0, spi_sck = 1'b0, spi_cs_n = 1'b1;
  reg [2:0] addr_p = 3'd0;
  reg rd_p = 1'b0, dbg_p = 1'b0, bsel = 1'b0;
  reg cfg_ck = 1'b0, cfg_dat = 1'b0, cfg_ld = 1'b0;
  reg comp = 1'b0;
  reg [2:0] tw_addr = 3'd0;
  reg tw_bsel = 1'b0;
  always @(posedge clk) comp <= $random(seed_c);

  function integer rnd(input integer n);
    begin rnd = {$random(seed)} % n; end
  endfunction
  function real jh(input real th, input integer jit);      // half period with +-jit % jitter
    begin jh = th * (1.0 + ((jit > 0) ? (rnd(2 * jit + 1) - jit) / 100.0 : 0.0)); end
  endfunction

  // ---------------------------------------------------------------- DUT side: C9 + cz_bus8 + cz_spi
  wire [2:0] addr_c9; wire rd_c9, dbg_c9;
  wire [7:0] uo, uio, data8, data_o;
  wire [15:0] bus = {uo, uio};
  sd_adc_c9 #(.PW_BITS(8), .BIAS_BITS(2)) u_c9 (
    .clk(clk), .rst_n(rst_n), .ui_in({dbg_c9, cfg_ld, cfg_dat, cfg_ck, rd_c9, addr_c9}), .comp_in(comp),
    .bias_ok(1'b1), .uo_out(uo), .uio_out(uio), .fs_clk(), .rst_analog(), .sys_swap(), .ota_chop_phase(),
    .short_o(), .order_o(), .boost_o(), .trim_o(), .y_force(), .bit_valid(), .y_dac());
  cz_bus8 u_b8 (.bus(bus), .bsel(bsel), .data(data8));
  cz_spi dut (.clk(clk), .rst_n(rst_n), .spi_en(spi_en), .spi_sck(spi_sck), .spi_cs_n(spi_cs_n),
              .addr_i(addr_p), .rd_i(rd_p), .dbg_i(dbg_p), .bus(bus), .data_in(data8),
              .addr_o(addr_c9), .rd_o(rd_c9), .dbg_o(dbg_c9), .data_o(data_o));
  wire miso = data_o[0];

  // ---------------------------------------------------------------- twin: C9 + cz_bus8 without the wrapper
  wire [7:0] tuo, tuio, tdata8;
  wire [2:0] t_addr = spi_en ? tw_addr : addr_p;
  wire       t_rd   = spi_en ? rd_c9   : rd_p;      // same rd as the DUT-side C9 -> same state (lockstep)
  wire       t_dbg  = spi_en ? 1'b0    : dbg_p;
  wire       t_bsel = spi_en ? tw_bsel : bsel;
  sd_adc_c9 #(.PW_BITS(8), .BIAS_BITS(2)) u_tw (
    .clk(clk), .rst_n(rst_n), .ui_in({t_dbg, cfg_ld, cfg_dat, cfg_ck, t_rd, t_addr}), .comp_in(comp),
    .bias_ok(1'b1), .uo_out(tuo), .uio_out(tuio), .fs_clk(), .rst_analog(), .sys_swap(), .ota_chop_phase(),
    .short_o(), .order_o(), .boost_o(), .trim_o(), .y_force(), .bit_valid(), .y_dac());
  cz_bus8 u_tb8 (.bus({tuo, tuio}), .bsel(t_bsel), .data(tdata8));

  // ---------------------------------------------------------------- frame history (scoreboard reference)
  reg [15:0] h_tag [0:255];
  reg [31:0] h_a1  [0:255];
  reg [31:0] h_a2  [0:255];
  reg [4:0]  h_st  [0:255];                 // status[12:8] = {hold_boost, hold_trim, 0}
  reg        h_v   [0:255];
  real       h_t   [0:255];                 // time of the load edge
  integer n_loads = 0, nl_rst = 0;
  real    last_load_t = 0.0, slot_t = 0.0;
  reg     load_pend = 1'b0;
  reg [7:0] hc;
  event   ev_load;
  always @(negedge clk) begin
    if (!rst_n) load_pend = 1'b0;
    else begin
      if (load_pend) begin
        hc = u_c9.hold_tag[7:0];
        h_tag[hc] = u_c9.hold_tag; h_a1[hc] = u_c9.hold_acc1; h_a2[hc] = u_c9.hold_acc2; h_st[hc] = u_c9.status[12:8];
        h_v[hc] = 1'b1; h_t[hc] = $realtime - THC;
        if (nl_rst > 0) slot_t = h_t[hc] - last_load_t;
        last_load_t = h_t[hc]; n_loads = n_loads + 1; nl_rst = nl_rst + 1;
        -> ev_load;
      end
      load_pend = u_c9.fs_tick & u_c9.load;
    end
  end

  // status values C9 presented in the last 128 clk (the snapshot status must be one of them)
  reg [15:0] ring  [0:127];
  reg [15:0] ringc [0:127];
  integer rp = 0;
  always @(negedge clk) begin ring[rp] = u_c9.status; rp = (rp + 1) % 128; end

  // ---------------------------------------------------------------- always-on checkers
  integer en_age = 0; reg en_prev = 1'b0;
  always @(posedge clk) begin if (spi_en !== en_prev) en_age = 0; else en_age = en_age + 1; en_prev = spi_en; end

  always @(negedge clk) if (rst_n) begin
    // REQ-ACK-*, REQ-EN1-002: DUT-side C9 state must equal the twin (same rd) in every mode
    `CHK((u_c9.frame_ready === u_tw.frame_ready) && (u_c9.overrun === u_tw.overrun) && (u_c9.hold_tag === u_tw.hold_tag)
         && (u_c9.hold_acc1 === u_tw.hold_acc1) && (u_c9.hold_acc2 === u_tw.hold_acc2), ("lockstep: DUT-side C9 state != twin C9"))
    if (!spi_en) begin
      // REQ-EN0-001/002: full pass-through, slot outputs identical to C9 + cz_bus8 without the wrapper
      `CHK((addr_c9 === addr_p) && (rd_c9 === rd_p) && (dbg_c9 === dbg_p) && (data_o === data8), ("pass-through: wrapper outputs != pins"))
      if (en_age >= 4)
        `CHK((data_o === tdata8) && (uo === tuo) && (uio === tuio), ("pass-through: slot outputs differ from C9 without wrapper"))
    end else begin
      // REQ-EN1-001/003, REQ-RST-002: data[7:1] = 0, dbg forced 0, no X on the pins
      `CHK((data_o[7:1] === 7'd0) && (dbg_c9 === 1'b0) && (^data_o !== 1'bx), ("SPI mode: data_o=%b dbg_o=%b (want 0000000m, 0, no X)", data_o, dbg_c9))
    end
  end

  // REQ-M0-002: after the first SCLK rise MISO may change only at a falling SCLK edge
  real    t_last_fall = -1.0, t_last_miso = 0.0;
  integer rises = 0;
  reg     relaxed = 1'b0;                   // abnormal-protocol tests (short setup, reset): observe, do not judge
  always @(miso) begin
    t_last_miso = $realtime;
    if (spi_en && !spi_cs_n && rises > 0 && !relaxed && rst_n) begin
      if (spi_sck !== 1'b0) `ERR(("mode 0: MISO changed while SCLK high"))
      else if ($realtime != t_last_fall) `ERR(("mode 0: MISO changed without a falling SCLK edge"))
    end
  end

  // REQ-CDC-001: CS_n is asynchronous; with a 2-FF synchroniser no clk-domain output reacts before the 3rd edge
  integer lat_cnt = 0, lat_min = 1000; reg lat_arm = 1'b0; reg [2:0] lat_a0;
  always @(negedge spi_cs_n) if (spi_en) begin lat_arm = 1'b1; lat_cnt = 0; lat_a0 = addr_c9; end
  always @(posedge spi_cs_n) lat_arm = 1'b0;
  always @(posedge clk) if (lat_arm) lat_cnt = lat_cnt + 1;
  always @(negedge clk) if (lat_arm && rst_n && ((addr_c9 !== lat_a0) || (rd_c9 === 1'b1))) begin
    `CHK(lat_cnt >= 3, ("CS_n fall reached addr/rd after %0d clk edges (2-FF sync needs >= 3)", lat_cnt))
    if (lat_cnt < lat_min) lat_min = lat_cnt;
    lat_arm = 1'b0;
  end

  // ---------------------------------------------------------------- read context, ack and loss accounting
  reg [95:0] rx; integer nrx = 0;
  reg        ctx_valid = 1'b0;
  real       ctx_tfall = 0.0, ctx_t_rd = -1.0;
  integer    ctx_rdp = 0;
  reg [7:0]  ctx_cf = 8'd0, ctx_cr = 8'd0, ctx_deliv = 8'd0;
  reg        ctx_frf = 1'b0, ctx_deliv_ok = 1'b0, ctx_nodeliv_ok = 1'b0;
  reg [7:0]  clr_ctr [0:15];
  integer    n_clr = 0;
  integer n_reads = 0, n_full = 0, n_retake = 0, n_win = 0, n_reack = 0, n_nodeliv = 0, n_shift_loads = 0;
  real    win_min = 1.0e9, win_max = -1.0e9, ack_lat_max = 0.0, ack_lat_min = 1.0e9;

  always @(posedge rd_c9) if (spi_en && ctx_valid) begin
    ctx_rdp = ctx_rdp + 1;
    if (ctx_t_rd < 0.0) ctx_t_rd = $realtime;
  end

  // REQ-ACK-003: every frame_ready clear in SPI mode must be attributable (see ctx_close)
  reg fr_prev = 1'b0;
  always @(negedge clk) begin
    if (!rst_n) fr_prev = 1'b0;
    else begin
      if (spi_en && en_age > 4 && fr_prev && !u_c9.frame_ready) begin
        if (!ctx_valid) `ERR(("frame %0d cleared with no SPI read since reset", u_c9.hold_tag[7:0]))
        else if (n_clr < 16) begin clr_ctr[n_clr] = u_c9.hold_tag[7:0]; n_clr = n_clr + 1; end
      end
      fr_prev = u_c9.frame_ready;
    end
  end

  task ctx_close;
    integer k; real off; reg [7:0] nx;
    begin
      if (ctx_valid) for (k = 0; k < n_clr; k = k + 1) begin
        nx = ctx_deliv + 8'd1;
        if (ctx_deliv_ok && (clr_ctr[k] == ctx_deliv)) ;                    // acked the frame it delivered
        else if (ctx_deliv_ok && (clr_ctr[k] == nx) && h_v[nx] && (h_t[nx] >= ctx_tfall)
                 && ((h_t[nx] - ctx_tfall) <= 32.0 * TCLK)) begin            // documented residual window
          n_win = n_win + 1; off = (h_t[nx] - ctx_tfall) / TCLK;
          if (off < win_min) win_min = off;
          if (off > win_max) win_max = off;
        end else if (ctx_nodeliv_ok) n_nodeliv = n_nodeliv + 1;              // abort/partial/abnormal: ack allowed
        else `ERR(("silent clear: frame %0d cleared but not read (this read delivered %0d)", clr_ctr[k], ctx_deliv))
      end
      ctx_valid = 1'b0; n_clr = 0;
    end
  endtask

  task check_frame(input [95:0] f);
    reg [15:0] st, tg; reg [31:0] a1, a2; reg [7:0] c, d1, d2; integer k; reg found;
    begin
      st = f[95:80]; a1 = f[79:48]; a2 = f[47:16]; tg = f[15:0]; c = tg[7:0];
      `QCHK(st[7:0] == tg[7:0], ("torn snapshot: status ctr %0d != tag ctr %0d", st[7:0], tg[7:0]))
      `QCHK(h_v[c] === 1'b1, ("frame ctr %0d was never loaded", c))
      `QCHK((h_tag[c] === tg) && (h_a1[c] === a1) && (h_a2[c] === a2),
            ("frame %0d content: got tag %h acc1 %h acc2 %h, hold had %h %h %h", c, tg, a1, a2, h_tag[c], h_a1[c], h_a2[c]))
      `QCHK(st[12:8] === h_st[c], ("frame %0d status[12:8] %b, hold had %b", c, st[12:8], h_st[c]))
      d1 = c - ctx_cf; d2 = ctx_cr - ctx_cf;
      `QCHK(d1 <= d2, ("stale or future frame: got %0d, ctr at CS_n fall %0d, at first SCLK %0d", c, ctx_cf, ctx_cr))
      found = 1'b0;
      for (k = 0; k < 128; k = k + 1) if (ringc[k] === st) found = 1'b1;
      `QCHK(found, ("status %h was never presented by C9 in the 128 clk before the first SCLK", st))
      if (ctx_frf && (c == ctx_cf)) `QCHK(st[15] === 1'b1, ("fresh frame %0d read with status frame_ready = 0", c))
    end
  endtask

  // ---------------------------------------------------------------- SPI host BFM (mode 0, MSB first)
  // nbits = 0: CS_n low for tsu then high (abort). tsu = CS_n fall to the first SCLK rise.
  task spi_xfer(input integer nbits, input real th, input real tsu, input integer jit);
    integer i, k, j, nl0; real lat; reg [7:0] d1, d2; reg [79:0] e80;
    begin
      ctx_close;
      rises = 0; rx = 96'd0; nrx = 0;
      ctx_cf = u_c9.hold_tag[7:0]; ctx_frf = u_c9.frame_ready;
      ctx_deliv_ok = 1'b0; ctx_nodeliv_ok = relaxed || (nbits < 16);
      ctx_rdp = 0; ctx_t_rd = -1.0; n_clr = 0;
      spi_cs_n = 1'b0; ctx_tfall = $realtime; ctx_valid = 1'b1;
      n_reads = n_reads + 1;
      #(tsu);
      ctx_cr = u_c9.hold_tag[7:0]; nl0 = n_loads;
      for (k = 0; k < 128; k = k + 1) ringc[k] = ring[k];
      // REQ-M0-001: bit 95 settled before the first rising edge (setup rule met)
      if (nbits > 0 && !relaxed && tsu >= 32.0 * TCLK - 0.001)
        `CHK(($realtime - t_last_miso) >= ((th < TCLK) ? th : TCLK), ("mode 0: MISO not settled before the first SCLK rise"))
      for (i = 0; i < nbits; i = i + 1) begin
        rx = {rx[94:0], miso}; nrx = nrx + 1;             // host samples on the rising edge
        spi_sck = 1'b1; rises = rises + 1;
        #(jh(th, jit));
        t_last_fall = $realtime; spi_sck = 1'b0;
        #(jh(th, jit));
      end
      spi_cs_n = 1'b1;
      if (n_loads - nl0 > 0) n_shift_loads = n_shift_loads + 1;
      if (nbits >= 16) begin ctx_deliv_ok = 1'b1; ctx_deliv = rx[nbits - 9 -: 8]; end
      // partial read: delivered bits must be a prefix of a real, fresh frame
      if (nbits >= 16 && nbits < 96 && !relaxed) begin
        d1 = ctx_deliv - ctx_cf; d2 = ctx_cr - ctx_cf;
        `CHK((h_v[ctx_deliv] === 1'b1) && (d1 <= d2), ("partial read: status ctr %0d not a fresh frame", ctx_deliv))
        e80 = {h_a1[ctx_deliv], h_a2[ctx_deliv], h_tag[ctx_deliv]};
        for (j = 0; j < nbits - 16; j = j + 1)
          `CHK(rx[j] === e80[96 - nbits + j], ("partial read (%0d bits): bit %0d wrong", nbits, 96 - nbits + j))
      end
      if (nbits == 96 && !relaxed) begin
        n_full = n_full + 1;
        check_frame(rx);
        `CHK(ctx_rdp <= 1, ("%0d acks in one CS_n low period", ctx_rdp))
        if (rx[95]) `CHK(ctx_rdp == 1, ("frame %0d was ready at snapshot but was not acknowledged", rx[7:0]))
        if (u_c9.hold_tag[7:0] == rx[7:0])
          `CHK(u_c9.frame_ready === 1'b0, ("frame %0d still ready after a complete read (no ack)", rx[7:0]))
        if (ctx_rdp > 0) begin
          lat = (ctx_t_rd - ctx_tfall) / TCLK;
          `CHK(lat <= 32.0, ("ack %0.1f clk after CS_n fall (> 32 clk setup budget)", lat))
          if (lat > ack_lat_max) ack_lat_max = lat;
          if (lat < ack_lat_min) ack_lat_min = lat;
          if (lat > 20.0) n_retake = n_retake + 1;
          if (!rx[95]) begin
            n_reack = n_reack + 1;
            if (strict_ack) `ERR(("STRICT_ONE_ACK: re-read of acknowledged frame %0d pulsed rd", rx[7:0]))
          end
        end
      end
    end
  endtask

  // ---------------------------------------------------------------- helpers
  task clk_n(input integer n); begin repeat (n) @(posedge clk); #1; end endtask
  task gap(input integer mn, input integer mx); begin #(TCLK * (mn + rnd(mx - mn + 1)) + rnd(1000) * 0.02); end endtask

  task cfg_write(input [15:0] v);
    integer k;
    begin
      clk_n(6);
      for (k = 15; k >= 0; k = k - 1) begin cfg_dat = v[k]; clk_n(4); cfg_ck = 1'b1; clk_n(4); cfg_ck = 1'b0; end
      clk_n(4); cfg_ld = 1'b1; clk_n(4); cfg_ld = 1'b0; clk_n(4);
    end
  endtask

  task hist_reset; integer i; begin
    for (i = 0; i < 256; i = i + 1) h_v[i] = 1'b0;
    ctx_valid = 1'b0; n_clr = 0; nl_rst = 0;
  end endtask
  task pulse_reset(input real tlow); begin       // asynchronous assert at the current (random) time
    rst_n = 1'b0; hist_reset; #(tlow); rst_n = 1'b1;
    h_tag[0] = 16'h0100; h_a1[0] = 32'd0; h_a2[0] = 32'd0; h_st[0] = {1'b0, 3'd4, 1'b0}; h_v[0] = 1'b1; h_t[0] = $realtime;
  end endtask
  task do_reset; begin
    pulse_reset(TCLK * (2.0 + rnd(5)) + rnd(1000) * 0.02);
    cfg_write(CFG);                              // during the power-good hold: applied at boot (latch every boot tick)
    repeat (3) @(ev_load);
    clk_n(2);
  end endtask

  task par_read(input twin, output [95:0] f);    // parallel byte-bus read: status, acc1h, acc1l, acc2h, acc2l, tag
    integer k; reg [2:0] a; reg [15:0] w;
    begin
      f = 96'd0;
      for (k = 0; k < 6; k = k + 1) begin
        case (k) 0: a = 3'd5; 1: a = 3'd0; 2: a = 3'd1; 3: a = 3'd2; 4: a = 3'd3; default: a = 3'd4; endcase
        @(negedge clk); if (twin) tw_addr = a; else addr_p = a;
        repeat (5) @(posedge clk); @(negedge clk);
        if (twin) begin tw_bsel = 1'b1; #1 w[15:8] = tdata8; tw_bsel = 1'b0; #1 w[7:0] = tdata8; end
        else      begin bsel = 1'b1;    #1 w[15:8] = data_o; bsel = 1'b0;    #1 w[7:0] = data_o; end
        f = {f[79:0], w};
      end
    end
  endtask
  task check_par(input [95:0] f); begin
    `CHK(f[87:80] == f[7:0], ("parallel read torn"))
    `CHK((h_v[f[7:0]] === 1'b1) && (h_tag[f[7:0]] === f[15:0]) && (h_a1[f[7:0]] === f[79:48]) && (h_a2[f[7:0]] === f[47:16]),
         ("parallel-bus frame differs from the C9 hold history (ctr %0d)", f[7:0]))
  end endtask

  task pass_through(input integer n);            // spi_en = 0: random pins incl. SPI pins, comb checks
    integer i;
    begin
      for (i = 0; i < n; i = i + 1) begin
        @(negedge clk); #(1.0 + rnd(8));
        case (rnd(6))
          0: addr_p = rnd(8); 1: rd_p = rnd(2); 2: dbg_p = rnd(2); 3: bsel = rnd(2); 4: spi_cs_n = rnd(2);
          default: spi_sck = rnd(2);
        endcase
        #0.01 `CHK((addr_c9 === addr_p) && (rd_c9 === rd_p) && (dbg_c9 === dbg_p) && (data_o === data8), ("pass-through (comb) broken"))
      end
      rd_p = 1'b0; dbg_p = 1'b0; spi_cs_n = 1'b1; spi_sck = 1'b0; clk_n(4);
    end
  endtask

  // SPI mode: external addr/rd/dbg/bsel noise mid-cycle; must not reach C9 or data[7:1] at all
  reg noise_en = 1'b0;
  reg [2:0] na; reg nr, nd; reg [6:0] ndh;
  always begin
    @(negedge clk); #(3.0);
    if (noise_en && spi_en && (rnd(3) == 0)) begin
      na = addr_c9; nr = rd_c9; nd = dbg_c9; ndh = data_o[7:1];
      addr_p = rnd(8); rd_p = rnd(2); dbg_p = rnd(2); bsel = rnd(2);
      #0.01 `CHK((addr_c9 === na) && (rd_c9 === nr) && (dbg_c9 === nd) && (data_o[7:1] === ndh),
                 ("SPI mode: external addr/rd/dbg/bsel pin reached the C9 inputs or data pins"))
    end
  end

  task report; begin
    $display("STAT reads=%0d full=%0d loads=%0d retakes=%0d window_losses=%0d window_offset_clk=[%0.2f, %0.2f] reacks=%0d nodeliv_acks=%0d shift_loads=%0d",
             n_reads, n_full, n_loads, n_retake, n_win, win_min, win_max, n_reack, n_nodeliv, n_shift_loads);
    $display("STAT ack_latency_clk=[%0.1f, %0.1f] min_cs_to_clkdomain_edges=%0d", ack_lat_min, ack_lat_max, lat_min);
    $display("CHECKS=%0d ERRORS=%0d", checks, errs);
    if (errs == 0) $display("TB_PASS"); else $display("TB_FAIL");
  end endtask
  always @(errs) if (stop_on_err && errs > 0) begin report; $display("(stopped on first error)"); $finish; end
  initial begin #(150_000_000.0); `ERR(("watchdog: bench hung")) report; $finish; end

  // ---------------------------------------------------------------- tests
  reg [95:0] pf, r1;
  integer i, k, s, okc, nb, sbits;
  real ths [0:6]; real tq, th;
  reg [31:0] abort_ack;
  initial begin
    if ($value$plusargs("seed=%d", seed)) ;
    if ($test$plusargs("STRICT_ONE_ACK")) strict_ack = 1'b1;
    if ($test$plusargs("STOP_ON_ERR"))    stop_on_err = 1'b1;
    seed_c = seed * 7 + 3;
    $display("tb_cz_spi seed=%0d strict_ack=%0d", seed, strict_ack);
    ths[0] = 2000.0; ths[1] = 500.0; ths[2] = 83.333; ths[3] = T12; ths[4] = 31.25; ths[5] = 20.834; ths[6] = 12.5;

    // T00 reset + config, steady frames (792 clk)
    #(TCLK * 5.3); do_reset;
    `CHK((slot_t > 791.0 * TCLK) && (slot_t < 793.0 * TCLK), ("bench: slot period %0.1f ns, expected 792 clk", slot_t))

    // T01 spi_en = 0: pass-through, SPI pins toggling must be ignored; parallel read through the slot vs history
    $display("T01 pass-through");
    pass_through(4000);
    for (i = 0; i < 3; i = i + 1) begin @(ev_load); clk_n(5); par_read(1'b0, pf); check_par(pf); end

    // T02 spi_en = 1: SPI frame equals the parallel-bus read (twin) of the same frame, all 96 bits
    $display("T02 SPI vs parallel bus");
    @(negedge clk); spi_en = 1'b1; addr_p = 3'd0; clk_n(10);
    for (i = 0; i < 4; i = i + 1) begin
      @(ev_load); clk_n(5); par_read(1'b1, pf); check_par(pf);
      #(rnd(1000) * 0.02);
      spi_xfer(96, T12, 32.0 * TCLK, 0);
      `CHK(rx === pf, ("SPI frame %h != parallel-bus frame %h", rx, pf))
    end

    // T03 smoke, 12 MHz, setup 32 clk
    $display("T03 smoke");
    for (i = 0; i < 5; i = i + 1) begin gap(8, 100); spi_xfer(96, T12, 32.0 * TCLK, 0); end

    // T04 SCLK frequency / phase / jitter sweep, external pin noise on
    $display("T04 SCLK sweep");
    noise_en = 1'b1;
    for (s = 0; s < 7; s = s + 1)
      for (k = 0; k < 6; k = k + 1) begin gap(8, 300); spi_xfer(96, ths[s], (32 + rnd(8)) * TCLK + rnd(100) * 0.2, 10); end
    noise_en = 1'b0;

    // T05 CS_n setup: exactly 32 clk must pass; shorter is observed and reported (not judged)
    $display("T05 setup");
    for (i = 0; i < 8; i = i + 1) begin gap(8, 400); spi_xfer(96, T12, 32.0 * TCLK, 0); end
    relaxed = 1'b1; quiet = 1'b1;
    for (s = 4; s <= 28; s = s + 4) begin
      okc = 0;
      for (k = 0; k < 4; k = k + 1) begin
        @(ev_load); clk_n(20); #(rnd(1000) * 0.02);
        spi_xfer(96, T12, s * TCLK, 0); qbad = 0; check_frame(rx); if (qbad == 0) okc = okc + 1;
      end
      $display("STAT short_setup=%0d clk: correct frames %0d/4", s, okc);
    end
    relaxed = 1'b0; quiet = 1'b0; gap(8, 20);

    // T06 frame load at every clk offset around the capture (retake, residual window), setup exactly 32 clk
    $display("T06 load-in-capture sweep");
    for (k = 0; k < 2; k = k + 1)
      for (s = -4; s <= 40; s = s + 1) begin
        @(ev_load);
        tq = last_load_t + slot_t - s * TCLK + rnd(1000) * TCLK / 1000.0;
        if (tq > $realtime) #(tq - $realtime);
        spi_xfer(96, T12, 32.0 * TCLK, 0);
      end
    `CHK(n_retake >= 1, ("cover: no retake observed (vacuous REQ-SNAP-002)"))
    `CHK(n_win >= 1, ("cover: residual window never hit (window not measured)"))
    `CHK((n_win == 0) || (win_max - win_min <= 6.0), ("residual loss window %0.2f..%0.2f clk wider than documented ~5 clk", win_min, win_max))
    $display("STAT T06 retakes=%0d window_losses=%0d window=[%0.2f, %0.2f] clk after CS_n fall", n_retake, n_win, win_min, win_max);

    // T07 frame loads during the shift (slow SCLK): data must stay the snapshot
    $display("T07 load during shift");
    @(ev_load); clk_n(10); spi_xfer(96, 2000.0, 32.0 * TCLK, 10);
    gap(8, 20); @(ev_load); clk_n(100); spi_xfer(96, 500.0, 40.0 * TCLK, 10);
    `CHK(n_shift_loads >= 2, ("cover: no frame load during a shift"))

    // T08 overrun: 3 frames unread, then read; then immediate re-read
    $display("T08 overrun");
    gap(8, 20); repeat (3) @(ev_load); clk_n(5);
    spi_xfer(96, T12, 32.0 * TCLK, 0); r1 = rx;
    `CHK(rx[95:94] === 2'b11, ("overrun: status[15:14] = %b after 3 unread frames, want 11", rx[95:94]))
    `CHK((u_c9.overrun === 1'b0) && (u_c9.frame_ready === 1'b0), ("overrun / frame_ready not cleared by the ack"))
    #(8.0 * TCLK + rnd(1000) * 0.02);
    spi_xfer(96, T12, 32.0 * TCLK, 0);
    `CHK((rx[93:0] === r1[93:0]) && (rx[95:94] === 2'b00), ("re-read after ack: %h, first read %h", rx, r1))

    // T09 partial read then re-read (same data, flags show the ack); 1-bit and 0-bit partials
    $display("T09 partial + re-read");
    @(ev_load); clk_n(5);
    spi_xfer(20, T12, 32.0 * TCLK, 0); r1 = rx;
    #(8.0 * TCLK + rnd(1000) * 0.02);
    spi_xfer(96, T12, 32.0 * TCLK, 0);
    `CHK(rx[93:76] === r1[17:0], ("re-read after a partial read returned different data"))
    `CHK(r1[19] === 1'b1, ("partial read of a fresh frame: frame_ready bit = 0"))
    `CHK(rx[95] === 1'b0, ("re-read after a partial read: frame still flagged ready (first read did not ack)"))
    @(ev_load); clk_n(5);
    spi_xfer(1, T12, 32.0 * TCLK, 0);
    `CHK(rx[0] === 1'b1, ("1-bit read of a fresh frame: bit 95 (frame_ready) = 0"))
    gap(8, 30); spi_xfer(0, T12, 40.0 * TCLK, 0);
    gap(8, 30); spi_xfer(96, T12, 32.0 * TCLK, 0);

    // T10 CS_n high mid-capture: abort, no ack (k <= 8 clk); k = 9..30 reported
    $display("T10 abort");
    abort_ack = 32'd0;
    for (k = 1; k <= 30; k = k + 1) begin
      @(ev_load); clk_n(3);
      spi_xfer(0, T12, k * TCLK + rnd(900) * 0.02, 0);
      clk_n(40);
      if (k <= 8) begin
        `CHK(ctx_rdp == 0, ("CS_n low %0d clk (abort) still acknowledged", k))
        `CHK(u_c9.frame_ready === 1'b1, ("CS_n low %0d clk (abort) cleared frame_ready", k))
      end
      abort_ack[k] = (ctx_rdp != 0);
    end
    $display("STAT abort ack by CS_n-low length (bit k = k clk): %b", abort_ack);
    gap(8, 30); spi_xfer(96, T12, 32.0 * TCLK, 0);

    // T11 SPI mode, hostile external pins held: dbg=1, addr=7, bsel=1; external rd pulses while CS_n high
    $display("T11 pin abuse");
    dbg_p = 1'b1; addr_p = 3'd7; bsel = 1'b1; rd_p = 1'b0;
    for (i = 0; i < 3; i = i + 1) begin gap(8, 200); spi_xfer(96, T12, 32.0 * TCLK, 0); end
    @(ev_load); clk_n(5);
    for (i = 0; i < 3; i = i + 1) begin rd_p = 1'b1; clk_n(4); rd_p = 1'b0; clk_n(4); end
    `CHK(u_c9.frame_ready === 1'b1, ("SPI mode: external rd pin cleared a frame"))
    dbg_p = 1'b0; addr_p = 3'd0; bsel = 1'b0;
    gap(8, 30); spi_xfer(96, T12, 32.0 * TCLK, 0);

    // T12 reset in the middle of a transaction (shift, capture), then recovery
    $display("T12 reset mid-transaction");
    relaxed = 1'b1;
    gap(8, 30);
    fork
      spi_xfer(96, 500.0, 32.0 * TCLK, 5);
      begin #(TCLK * (40 + rnd(2000))); pulse_reset(TCLK * (1 + rnd(6)) + rnd(1000) * 0.02); cfg_write(CFG); end
    join
    relaxed = 1'b0;
    repeat (3) @(ev_load); clk_n(5); spi_xfer(96, T12, 32.0 * TCLK, 0);
    @(ev_load); clk_n(5);
    relaxed = 1'b1;
    fork
      spi_xfer(0, T12, 60.0 * TCLK, 0);
      begin #(TCLK * (2 + rnd(14)) + rnd(1000) * 0.02); pulse_reset(3.0 * TCLK); cfg_write(CFG); end
    join
    relaxed = 1'b0;
    repeat (3) @(ev_load); clk_n(5); spi_xfer(96, T12, 32.0 * TCLK, 0);
    gap(8, 30); do_reset; gap(8, 30); spi_xfer(96, T12, 32.0 * TCLK, 0);

    // T13 back-to-back reads, CS_n high exactly 8 clk
    $display("T13 back-to-back");
    for (i = 0; i < 12; i = i + 1) begin spi_xfer(96, T12, 32.0 * TCLK, 5); #(8.0 * TCLK + rnd(1000) * 0.02); end

    // T14 random soak: frequency, setup, partial, abort, gaps, pin noise
    $display("T14 soak");
    noise_en = 1'b1;
    for (i = 0; i < 150; i = i + 1) begin
      gap(8, 400);
      k = rnd(20); th = ths[1 + rnd(6)];
      if (k < 14) spi_xfer(96, th, (32 + rnd(30)) * TCLK + rnd(1000) * 0.02, 10);
      else if (k < 17) begin nb = 1 + rnd(95); spi_xfer(nb, th, (32 + rnd(30)) * TCLK, 10); end
      else begin
        sbits = 1 + rnd(60); spi_xfer(0, th, sbits * TCLK + rnd(1000) * 0.02, 0); clk_n(40);
        if (sbits <= 8) `CHK(ctx_rdp == 0, ("soak: CS_n low %0d clk (abort) acknowledged", sbits))
      end
    end
    noise_en = 1'b0;

    // T15 back to spi_en = 0: pass-through again (lockstep with the twin)
    $display("T15 pass-through again");
    gap(8, 30); rd_p = 1'b0; dbg_p = 1'b0; ctx_close;
    @(negedge clk); spi_en = 1'b0; clk_n(6);
    pass_through(1000);

    `CHK(n_full >= 200, ("cover: only %0d complete reads", n_full))
    report;
    $finish;
  end
endmodule
