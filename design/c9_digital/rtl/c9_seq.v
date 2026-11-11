// C9 fs_tick sequencer: slot counter c (slot = N+2 fs cycles), frame_ctr, reset window, chop,
// forced y[0] / retime flop, analog control outputs (all active high). All updates on fs_tick.
module c9_seq (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        fs_tick,
    input  wire        s_tick,       // bit-clock falling edge
    input  wire        comp_in,
    input  wire [1:0]  n_code,       // active config
    input  wire        sys_en_n,
    input  wire        ota_en_n,
    input  wire        cfg_change,
    output wire        latch,        // this fs_tick starts an even slot (pair boundary)
    output wire        load,         // this fs_tick ends a slot (hold load), not the boot tick
    output reg         boot,         // waiting for the first slot after rst
    output reg         inv_pair,     // current pair is invalid (D45 e)
    output reg [7:0]   slot_ctr,     // frame_ctr of the current slot
    output reg         rst_analog,
    output reg         sys_swap,
    output reg         ota_chop,
    output reg         y_force,
    output reg         bit_valid,
    output reg         acc_clear,    // c == 1: the edge that ends it clears the accumulators
    output reg         y_dac         // the retimed DAC flop = decimator input = raw bit
);
    reg [12:0] c;
    reg        comp_s;
    wire [12:0] c_last = (13'd64 << {n_code, 1'b0}) + 13'd1;   // N + 1
    wire       slot_start = boot | (c == c_last);
    wire [12:0] c_n    = slot_start ? 13'd0 : c + 13'd1;
    wire [7:0] ctr_n   = (slot_start & ~boot) ? slot_ctr + 8'd1 : slot_ctr;
    assign load  = fs_tick & slot_start & ~boot;
    assign latch = fs_tick & slot_start & ~ctr_n[0];
    wire rst_n_nx = slot_start | (c == 13'd0);                 // c_n is 0 or 1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            c <= 13'd0; boot <= 1'b1; inv_pair <= 1'b1; slot_ctr <= 8'd0;
            rst_analog <= 1'b1; sys_swap <= 1'b0; ota_chop <= 1'b0; y_force <= 1'b0;
            bit_valid <= 1'b0; acc_clear <= 1'b0; y_dac <= 1'b0; comp_s <= 1'b0;
        end else begin
            if (s_tick) comp_s <= comp_in;                      // falling edge of bit clock (CL-23)
            if (fs_tick) begin
                boot       <= 1'b0;
                c          <= c_n;
                slot_ctr   <= ctr_n;
                if (latch) inv_pair <= boot | cfg_change;       // first pair after rst, or after a change
                rst_analog <= rst_n_nx;
                bit_valid  <= ~rst_n_nx;
                acc_clear  <= (c == 13'd0) & ~slot_start;
                y_force    <= (c == 13'd1);
                y_dac      <= (c == 13'd1) ? 1'b1 : comp_s;     // forced y[0] = +1 (3.7a a)
                ota_chop   <= ota_en_n & ~rst_n_nx & c_n[0];    // n mod 2 = c mod 2, 0 in reset
                if (slot_start) sys_swap <= sys_en_n & ctr_n[0];
            end
        end
    end
endmodule
