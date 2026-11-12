// Black-box port properties for C9 (WO-38, from SPEC 3.7a k / 3.8a port contract, D66/D67).
// Free inputs: ui_in, rst_n, comp_in, uio_in, ena.  Only TT pins and contract ports are referenced.
// Property IDs map to C9_VERIF_PLAN F-xx; each must fail on >= 1 mutant before it counts.
module c9_formal (input wire clk, input wire rst_n, input wire ena, input wire [7:0] ui_in,
                  input wire [7:0] uio_in, input wire comp_in);
  wire [7:0] uo_out, uio_out, uio_oe; wire [2:0] trim_o;
  wire fs_clk, rst_analog, sys_swap, ota_chop_phase, short_o, order_o, boost_o, y_force, bit_valid, y_dac;
  tt_um_sd_adc_c9 dut (.ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe),
    .ena(ena), .clk(clk), .rst_n(rst_n), .comp_in(comp_in), .fs_clk(fs_clk), .rst_analog(rst_analog),
    .sys_swap(sys_swap), .ota_chop_phase(ota_chop_phase), .short_o(short_o), .order_o(order_o),
    .boost_o(boost_o), .trim_o(trim_o), .y_force(y_force), .bit_valid(bit_valid), .y_dac(y_dac));
  reg p_fs_clk = 0;
  reg pv = 0, p_rst_n = 0, p_rst_n2 = 0, p_sys_swap = 0, p_bit_valid = 0, p_rst_analog = 1;
  reg [5:0] p_cfg = 0;
  wire [5:0] cfg = {short_o, order_o, boost_o, trim_o};
  always @(posedge clk) begin
    pv <= 1; p_rst_n <= rst_n; p_rst_n2 <= p_rst_n; p_sys_swap <= sys_swap; p_bit_valid <= bit_valid;
    p_rst_analog <= rst_analog; p_cfg <= cfg; p_fs_clk <= fs_clk;
  end
  initial assume (!rst_n);
  wire stable = pv && rst_n && p_rst_n && p_rst_n2;
  always @(posedge clk) begin
    assert (uio_oe == 8'hFF);                                                  // F16 BUS-01
    if (pv && !p_rst_n) assert (rst_analog && !bit_valid);                    // F17 RST-02
    assert (!(rst_analog && bit_valid));                                       // F03 SEQ-01
    assert (!y_force || bit_valid);                                            // F05 y_force only at n = 0
    assert (!rst_analog || !ota_chop_phase);                                   // F09 3.7a i
    if (stable && sys_swap != p_sys_swap) assert (rst_analog && !p_rst_analog && fs_clk && !p_fs_clk); // F01 WO-42: swap only on the cycle-0 edge (rst_analog rise = fs start edge)
    if (stable && cfg != p_cfg) assert (rst_analog && fs_clk && !p_fs_clk);  // F02 cfg outs only on a start edge in reset (CL-23)
    if (stable && bit_valid && !p_bit_valid) assert (y_force && p_rst_analog);// F08 n = 0 follows reset window
    if (stable && y_force) assert (y_dac);                                     // F06 forced y[0] = +1
    if (stable && !bit_valid && p_bit_valid) assert (rst_analog);             // F10 slot end -> reset window
    if (stable) begin
      cover (bit_valid && ota_chop_phase);
      cover (y_force);
      cover (bit_valid && !y_force && !y_dac);
    end
  end
endmodule
