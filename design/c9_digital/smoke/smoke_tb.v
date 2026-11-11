`timescale 1ns/1ps
// WO-37 smoke: one golden vector (frame 0, reset config) through tt_um_sd_adc_c9. Not the verification TB.
module smoke_tb;
    `include "vec.vh"
    reg clk = 0, rst_n = 0;
    reg [7:0] ui = 8'd0;
    reg comp = 0;
    wire [7:0] uo, uio, oe;
    wire fs_clk, rsta, swap, och, sh, ord, bst, yf, bv, ydac;
    wire [2:0] trim;
    tt_um_sd_adc_c9 dut (.ui_in(ui), .uo_out(uo), .uio_in(8'd0), .uio_out(uio), .uio_oe(oe), .ena(1'b1),
        .clk(clk), .rst_n(rst_n), .comp_in(comp), .fs_clk(fs_clk), .rst_analog(rsta), .sys_swap(swap),
        .ota_chop_phase(och), .short_o(sh), .order_o(ord), .boost_o(bst), .trim_o(trim), .y_force(yf),
        .bit_valid(bv), .y_dac(ydac));
    always #10.416 clk = ~clk;
    integer n = 0, i;
    reg [79:0] got;
    reg [15:0] w;
    // comparator: during conv cycle n it presents y[n+1] (loaded into the DAC flop at the start of n+1)
    always @(posedge fs_clk) begin
        #2;
        if (bv) begin
            n = n + 1;                         // n now = index of the NEXT bit
            comp = (n < 4096) ? YBITS[4095 - n] : 1'b0;
        end else begin n = 0; comp = 1'b0; end
    end
    initial begin
        #100 rst_n = 1;
        wait (dut.u_core.frame_ready === 1'b1);
        for (i = 0; i < 5; i = i + 1) begin
            ui[2:0] = i; repeat (6) @(posedge clk); #1;
            w = {uo, uio};
            got = {got[63:0], w};
        end
        $display("got  %h", got);
        $display("want %h", WIRE);
        if (got === WIRE) $display("SMOKE PASS"); else $display("SMOKE FAIL");
        $finish;
    end
    initial begin #400000000; $display("SMOKE TIMEOUT"); $finish; end
endmodule
