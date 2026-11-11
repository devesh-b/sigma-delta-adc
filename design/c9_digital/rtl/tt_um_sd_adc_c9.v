// TT-style top wrapper for the C9 digital block. The analog-side pins are extra ports here: in the final
// top they connect to the analog macro (level shifters in C4). `ena` is ignored (CL-20).
module tt_um_sd_adc_c9 (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n,
    // analog interface (not TT pins)
    input  wire       comp_in,
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
    wire _unused = &{1'b0, ena, uio_in};
    assign uio_oe = 8'hFF;
    c9_core u_core (.clk(clk), .rst_n(rst_n), .ui_in(ui_in), .comp_in(comp_in), .uo_out(uo_out),
                    .uio_out(uio_out), .fs_clk(fs_clk), .rst_analog(rst_analog), .sys_swap(sys_swap),
                    .ota_chop_phase(ota_chop_phase), .short_o(short_o), .order_o(order_o), .boost_o(boost_o),
                    .trim_o(trim_o), .y_force(y_force), .bit_valid(bit_valid), .y_dac(y_dac));
endmodule
