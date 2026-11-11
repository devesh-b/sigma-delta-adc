// C9 serial config: shift register, shadow, active, cfg_pending (SPEC 3.7a d, 3.8a).
// Inputs cfg_clk / cfg_dat / cfg_ld are already synchronised to clk.
module c9_cfg (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cfg_clk_s,
    input  wire        cfg_dat_s,
    input  wire        cfg_ld_s,
    input  wire        latch,      // shadow -> active this edge (even-slot start)
    output reg  [12:0] act,        // {order, n_code[1:0], fs_div[2:0], sys_en, ota_en, short, boost, trim[2:0]}
    output wire        change,     // effective change shadow != active (uses pre-edge shadow)
    output wire        sys_en_n,   // sys_en / ota_en as they will be after this edge
    output wire        ota_en_n,
    output reg         cfg_pending
);
    localparam [12:0] RST_CFG = {1'b1, 2'd3, 3'd1, 1'b1, 1'b1, 1'b0, 1'b0, 3'd4};
    reg [15:0] shift;
    reg [12:0] shadow;
    reg        ck_p, ld_p;
    wire       ck_rise = cfg_clk_s & ~ck_p;
    wire       ld_rise = cfg_ld_s  & ~ld_p;
    wire [2:0] fsd_raw = shift[9:7];
    wire [2:0] fsd_nrm = (fsd_raw > 3'd4) ? 3'd1 : fsd_raw;   // CL-16
    wire [12:0] shift_eff = {shift[12:10], fsd_nrm, shift[6:0]};
    wire [12:0] shadow_n = ld_rise ? shift_eff : shadow;
    wire [12:0] act_n    = latch ? shadow : act;               // old shadow: a write on the edge goes to the next pair
    assign change   = (shadow != act);
    assign sys_en_n = act_n[6];
    assign ota_en_n = act_n[5];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift <= 16'd0; shadow <= RST_CFG; act <= RST_CFG;
            ck_p <= 1'b0; ld_p <= 1'b0; cfg_pending <= 1'b0;
        end else begin
            ck_p <= cfg_clk_s; ld_p <= cfg_ld_s;
            if (ld_rise)       shift <= 16'd0;                 // CL-18
            else if (ck_rise)  shift <= {shift[14:0], cfg_dat_s};
            shadow      <= shadow_n;
            act         <= act_n;
            cfg_pending <= (shadow_n != act_n);                 // post-latch (CL-24)
        end
    end
endmodule
