// Black-box port properties for C9 (WO-38, from SPEC 3.7a k / 3.8a port contract, D66/D67).
// Free inputs: ui_in, rst_n, comp_in, uio_in, ena.  Only TT pins and contract ports are referenced.
module c9_formal (input wire clk, input wire rst_n, input wire ena, input wire [7:0] ui_in,
                  input wire [7:0] uio_in, input wire comp_in);
  wire [7:0] uo_out, uio_out, uio_oe; wire [2:0] trim_o;
  wire fs_clk, rst_analog, sys_swap, ota_chop_phase, short_o, order_o, boost_o, y_force, bit_valid, y_dac;
  tt_um_sd_adc_c9 dut (.ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe),
    .ena(ena), .clk(clk), .rst_n(rst_n), .comp_in(comp_in), .fs_clk(fs_clk), .rst_analog(rst_analog),
    .sys_swap(sys_swap), .ota_chop_phase(ota_chop_phase), .short_o(short_o), .order_o(order_o),
    .boost_o(boost_o), .trim_o(trim_o), .y_force(y_force), .bit_valid(bit_valid), .y_dac(y_dac));
  reg pv = 0;
  always @(posedge clk) pv <= 1;
  initial assume (!rst_n);
  wire stable = pv && rst_n && $past(rst_n);
  always @(posedge clk) begin
    F16_uio_oe:   assert (uio_oe == 8'hFF);                                   // BUS-01
    if (pv && $past(!rst_n)) F17_rst: assert (rst_analog && !bit_valid);      // RST-02
    F03_excl:     assert (!(rst_analog && bit_valid));                        // SEQ-01 / 3.7a k
    F05_yforce:   assert (!y_force || bit_valid);                             // y_force only at n = 0
    F09_ota_rst:  assert (!rst_analog || !ota_chop_phase);                    // 3.7a i: 0 in reset
    if (stable && sys_swap != $past(sys_swap)) F01_swap: assert (rst_analog && $past(bit_valid));
    if (stable && {short_o, order_o, boost_o, trim_o} != $past({short_o, order_o, boost_o, trim_o}))
      F02_cfg_at_latch: assert (rst_analog && $past(bit_valid));             // only on the even-slot c = 0 edge
    if (stable && bit_valid && !$past(bit_valid)) F08_n0: assert (y_force && $past(rst_analog));
    if (stable && y_force) F06_yforce_y: assert (y_dac);                     // forced y[0] = +1
    if (stable && !bit_valid && $past(bit_valid)) F10_end: assert (rst_analog);
  end
  always @(posedge clk) begin
    if (stable) begin
      C1: cover (bit_valid && ota_chop_phase);
      C2: cover (y_force);
      C3: cover (bit_valid && !y_force && !y_dac);
    end
  end
endmodule
