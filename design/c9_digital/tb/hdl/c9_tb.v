// WO-75 (verification only, not design RTL): parameterised bench top. Same pins as the tt_um_ sim wrapper
// (SPEC 3.8a TT pins + port contract incl. bias_ok, D85) so the bench can shorten the CL-36 hold through
// PW_BITS / BIAS_BITS (C9_PW_BITS / C9_BIAS_BITS). Real D85 values: 16 / 8. WO-83: the values are now set in a
// generated copy of the RTL tt_um_ wrapper (run_cocotb.py; Verilator rejects hierarchical defparam), not here.
module c9_tb (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n,
    input  wire       comp_in,
    input  wire       bias_ok,
    output wire       fs_clk,
    output wire       rst_analog,
    output wire       sys_swap,
    output wire       ota_chop_phase,
    output wire       short_o,
    output wire       order_o,
    output wire       boost_o,
    output wire [2:0] trim_o,
    output wire       y_force,
    output wire       bit_valid,
    output wire       y_dac
);
    // WO-75 rerun: wraps the real tt_um_ sim wrapper (M45 survived when this file bypassed it)
    tt_um_sd_adc_c9 u_wrap (.clk(clk), .rst_n(rst_n), .ena(ena), .ui_in(ui_in), .uio_in(uio_in), .uio_oe(uio_oe),
        .comp_in(comp_in), .bias_ok(bias_ok), .uo_out(uo_out), .uio_out(uio_out), .fs_clk(fs_clk),
        .rst_analog(rst_analog), .sys_swap(sys_swap), .ota_chop_phase(ota_chop_phase), .short_o(short_o),
        .order_o(order_o), .boost_o(boost_o), .trim_o(trim_o), .y_force(y_force), .bit_valid(bit_valid),
        .y_dac(y_dac));
endmodule
