// C9 fs divider + bit clock + fs_tick enable (DfV, CL-26). WO-60B: fs_tick / s_tick are registered one clk early.
// fs_tick is high for the last clk of each fs cycle: the edge that ends it is the fs-cycle start edge,
// where every sequencer register updates. bit_clk rises on that edge (50 % duty, even divisors).
// s_tick (internal) is high on the last clk of the high half: the edge that ends it is the bit-clock falling edge.
// Held in reset until rst release (CL-19); a divider change is applied
// by the sequencer only at a tick, so the new period starts at c = 0 with no runt (CL-15).
//
// Retiming (cycle-exact vs the old comb compare fs_tick = (dc == div-1)):
//  - fs_tick_r <= (dc == div-2): dc increments by 1 each clk, so this is true exactly when dc == div-1 next clk.
//    At the tick clk dc == div-1 != div-2, so the flop clears and dc restarts at 0 (div >= 12 so 0 never terminal).
//  - the terminal constants tc_fs/tc_half are registered from div_code. div_code (act) only changes on a tick
//    edge, when dc restarts at 0. In the clk with dc == 0 the stale constants are compared against 0 (always
//    false for both old and new div, constants >= 4), and they are refreshed by the end of that clk, i.e.
//    valid from dc == 1. So act no longer feeds the compare combinationally.
module c9_fsdiv (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [2:0] div_code,   // 0..4 = clk/12, /24, /48, /96, /192 (5..7 already normalised to 1)
    output reg        fs_tick,
    output reg        bit_clk
);
    reg [7:0] dc;
    reg [7:0] tc_fs;     // div - 2
    reg [7:0] tc_half;   // div/2 - 2
    reg [7:0] fs_c, half_c;
    always @* begin
        case (div_code)
            3'd0:    begin fs_c = 8'd10;  half_c = 8'd4;  end
            3'd2:    begin fs_c = 8'd46;  half_c = 8'd22; end
            3'd3:    begin fs_c = 8'd94;  half_c = 8'd46; end
            3'd4:    begin fs_c = 8'd190; half_c = 8'd94; end
            default: begin fs_c = 8'd22;  half_c = 8'd10; end
        endcase
    end
    reg s_tick;   // internal: bit clock falls (D74: no longer a capture strobe)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dc      <= 8'd0;
            bit_clk <= 1'b0;
            fs_tick <= 1'b0;
            s_tick  <= 1'b0;
            tc_fs   <= 8'd22;   // RST_CFG fs_div = 1 (clk/24)
            tc_half <= 8'd10;
        end else begin
            tc_fs   <= fs_c;
            tc_half <= half_c;
            dc      <= fs_tick ? 8'd0 : dc + 8'd1;
            fs_tick <= (dc == tc_fs);
            s_tick  <= (dc == tc_half);
            if (fs_tick)      bit_clk <= 1'b1;
            else if (s_tick)  bit_clk <= 1'b0;
        end
    end
endmodule
