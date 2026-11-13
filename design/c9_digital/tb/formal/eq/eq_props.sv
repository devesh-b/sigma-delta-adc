// WO-60B retime equivalence (verification only).  Pre-retime reference = c9_fsdiv_e450ae2.v (git HEAD e450ae2),
// every module renamed *_o by eq_job.sh.  All C9 flops have an async reset, so after the step-0 reset both
// copies are in identical states; any pin difference afterwards is a real non-equivalence.
`ifdef EQ_TOP
// Full-chip miter: new tt_um_sd_adc_c9 vs the e450ae2 tree, shared free inputs, every output compared every clk.
module eq_top (input wire clk, input wire rst_n, input wire ena, input wire [7:0] ui_in,
               input wire [7:0] uio_in, input wire comp_in);
  wire [7:0] a_uo, a_uio, a_oe, b_uo, b_uio, b_oe; wire [2:0] a_tr, b_tr;
  wire [10:0] a_s, b_s;
  tt_um_sd_adc_c9 n (.ui_in(ui_in), .uo_out(a_uo), .uio_in(uio_in), .uio_out(a_uio), .uio_oe(a_oe),
    .ena(ena), .clk(clk), .rst_n(rst_n), .comp_in(comp_in), .fs_clk(a_s[0]), .rst_analog(a_s[1]),
    .sys_swap(a_s[2]), .ota_chop_phase(a_s[3]), .short_o(a_s[4]), .order_o(a_s[5]),
    .boost_o(a_s[6]), .trim_o(a_tr), .y_force(a_s[7]), .bit_valid(a_s[8]), .y_dac(a_s[9]));
  tt_um_sd_adc_c9_o o (.ui_in(ui_in), .uo_out(b_uo), .uio_in(uio_in), .uio_out(b_uio), .uio_oe(b_oe),
    .ena(ena), .clk(clk), .rst_n(rst_n), .comp_in(comp_in), .fs_clk(b_s[0]), .rst_analog(b_s[1]),
    .sys_swap(b_s[2]), .ota_chop_phase(b_s[3]), .short_o(b_s[4]), .order_o(b_s[5]),
    .boost_o(b_s[6]), .trim_o(b_tr), .y_force(b_s[7]), .bit_valid(b_s[8]), .y_dac(b_s[9]));
  assign a_s[10] = 1'b0; assign b_s[10] = 1'b0;
  initial assume (!rst_n);
  always @* assert ({a_uo, a_uio, a_oe, a_tr, a_s} == {b_uo, b_uio, b_oe, b_tr, b_s});   // EQ-TOP
endmodule
`else
// Divider-local miter.  Environment: div_code changes only on the clk after fs_tick (the latch edge) or around
// reset (proven separately on the real core by EQ-ENV).  -DUNCONSTR drops it (must FAIL: shows the miter bites).
module eq_div (input wire clk, input wire rst_n, input wire [2:0] div_code);
  wire tn, bn, to, bo;
  c9_fsdiv   n (.clk(clk), .rst_n(rst_n), .div_code(div_code), .fs_tick(tn), .bit_clk(bn));
  c9_fsdiv_o o (.clk(clk), .rst_n(rst_n), .div_code(div_code), .fs_tick(to), .bit_clk(bo));
  reg pv = 0, p_rst = 0, p_tick = 0; reg [2:0] p_div = 0;
  always @(posedge clk) begin pv <= 1; p_rst <= rst_n; p_tick <= to; p_div <= div_code; end
  initial assume (!rst_n);
`ifndef UNCONSTR
  always @* if (pv && rst_n && p_rst) assume (div_code == p_div || p_tick);
`endif
  always @* assert (tn == to && bn == bo);   // EQ-DIV
  always @* cover (pv && rst_n && p_rst && div_code != p_div);
endmodule
`endif
