// C9 fs divider + bit clock + fs_tick enable (DfV, CL-26).
// fs_tick is high for the last clk of each fs cycle: the edge that ends it is the fs-cycle start edge,
// where every sequencer register updates. bit_clk rises on that edge (50 % duty, even divisors).
// s_tick is high on the last clk of the high half: the edge that ends it is the bit-clock falling edge
// (comparator sample edge, CL-23). Held in reset until rst release (CL-19); a divider change is applied
// by the sequencer only at a tick, so the new period starts at c = 0 with no runt (CL-15).
module c9_fsdiv (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [2:0] div_code,   // 0..4 = clk/12, /24, /48, /96, /192 (5..7 already normalised to 1)
    output wire       fs_tick,
    output wire       s_tick,
    output reg        bit_clk
);
    reg [7:0] dc;
    reg [7:0] div_m1;   // div - 1
    reg [7:0] half_m1;  // div/2 - 1
    always @* begin
        case (div_code)
            3'd0:    begin div_m1 = 8'd11;  half_m1 = 8'd5;  end
            3'd2:    begin div_m1 = 8'd47;  half_m1 = 8'd23; end
            3'd3:    begin div_m1 = 8'd95;  half_m1 = 8'd47; end
            3'd4:    begin div_m1 = 8'd191; half_m1 = 8'd95; end
            default: begin div_m1 = 8'd23;  half_m1 = 8'd11; end
        endcase
    end
    assign fs_tick = (dc == div_m1);
    assign s_tick  = (dc == half_m1);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dc      <= 8'd0;
            bit_clk <= 1'b0;
        end else begin
            dc <= fs_tick ? 8'd0 : dc + 8'd1;
            if (fs_tick)      bit_clk <= 1'b1;
            else if (s_tick)  bit_clk <= 1'b0;
        end
    end
endmodule
