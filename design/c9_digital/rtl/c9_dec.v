// C9 CoI accumulators (exclusive acc2), hold register, frame_ready / overrun, rd guard (D66). D72: acc1 14 b, acc2 25 b
// (enough for N <= 4096), sign-extended to 32 b on the hold outputs so the frame words are unchanged.
module c9_dec (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        fs_tick,
    input  wire        acc_clear,
    input  wire        bit_valid,
    input  wire        y,
    input  wire        load,
    input  wire [15:0] tag_in,      // tag of the slot being closed
    input  wire        boost_in,
    input  wire [2:0]  trim_in,
    input  wire        rd_rise,
    output wire [31:0] hold_acc1,
    output wire [31:0] hold_acc2,
    output reg  [15:0] hold_tag,
    output reg         hold_boost,
    output reg  [2:0]  hold_trim,
    output reg         frame_ready,
    output reg         overrun
);
    reg [13:0] acc1, h1;
    reg [24:0] acc2, h2;
    assign hold_acc1 = {{18{h1[13]}}, h1};
    assign hold_acc2 = {{7{h2[24]}}, h2};
    reg [7:0]  snap;
    reg        clr_pend;
    wire [13:0] a1n = acc1 + (y ? 14'd1 : 14'h3FFF);
    wire [24:0] a2n = acc2 + {{11{acc1[13]}}, acc1};          // exclusive: old acc1, sign-extended
    wire        load_now = fs_tick & load;
    wire [7:0]  hctr_n = load_now ? tag_in[7:0] : hold_tag[7:0];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc1 <= 14'd0; acc2 <= 25'd0;
            h1 <= 14'd0; h2 <= 25'd0;
            hold_tag <= 16'h0100;                               // invalid = 1 after rst (CL-17)
            hold_boost <= 1'b0; hold_trim <= 3'd4;
            frame_ready <= 1'b0; overrun <= 1'b0; snap <= 8'd0; clr_pend <= 1'b0;
        end else begin
            if (fs_tick) begin
                if (acc_clear) begin acc1 <= 14'd0; acc2 <= 25'd0; end
                else if (bit_valid) begin acc1 <= a1n; acc2 <= a2n; end
            end
            // rd guard: snapshot on the rd edge, clear next clk only if the post-load frame_ctr is unchanged
            clr_pend <= rd_rise;
            if (rd_rise) snap <= hold_tag[7:0];
            if (clr_pend && hctr_n == snap) begin
                frame_ready <= 1'b0;
                overrun     <= 1'b0;
            end
            if (load_now) begin
                h1         <= a1n;                              // includes the last conversion cycle
                h2         <= a2n;
                hold_tag   <= tag_in;
                hold_boost <= boost_in;
                hold_trim  <= trim_in;
                frame_ready <= 1'b1;
                if (frame_ready) overrun <= 1'b1;
            end
        end
    end
endmodule
