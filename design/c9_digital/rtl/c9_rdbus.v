// C9 registered 16-bit read bus + debug bus. addr/dbg synchronised (2 FF); word register (valid <= 3 clk, CL-21).
module c9_rdbus (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [2:0]  addr_i,
    input  wire        dbg_i,
    input  wire [31:0] hold_acc1,
    input  wire [31:0] hold_acc2,
    input  wire [15:0] hold_tag,
    input  wire [15:0] status,
    input  wire [7:0]  dbg_hi,       // debug uo_out[7:0]
    output wire [7:0]  uo_out,
    output wire [7:0]  uio_out
);
    reg [2:0]  a1, a2;
    reg        d1, d2;
    reg [15:0] word;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a1 <= 3'd0; a2 <= 3'd0; d1 <= 1'b0; d2 <= 1'b0; word <= 16'd0;
        end else begin
            a1 <= addr_i; a2 <= a1; d1 <= dbg_i; d2 <= d1;
            case (a2)
                3'd0:    word <= hold_acc1[31:16];
                3'd1:    word <= hold_acc1[15:0];
                3'd2:    word <= hold_acc2[31:16];
                3'd3:    word <= hold_acc2[15:0];
                3'd4:    word <= hold_tag;
                3'd5:    word <= status;
                default: word <= 16'd0;
            endcase
        end
    end
    // dbg select is a flop; sources are flops (only a mode change can glitch)
    assign uo_out  = d2 ? dbg_hi        : word[15:8];
    assign uio_out = d2 ? status[7:0]   : word[7:0];
endmodule
