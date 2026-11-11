// C9 digital core (one clock domain, clk = 48 MHz). Wrapper-free: the TT top is tt_um_sd_adc_c9.
module c9_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] ui_in,
    input  wire       comp_in,       // comparator output, sampled on the bit-clock falling edge
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    // analog control, all active high
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
    // reset: async assert, sync release
    reg r1, rs;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin r1 <= 1'b0; rs <= 1'b0; end
        else        begin r1 <= 1'b1; rs <= r1;   end
    end
    // input synchronisers (2 FF) for cfg_*, rd
    reg [1:0] sck, sdat, sld, srd;
    reg       rd_p;
    always @(posedge clk or negedge rs) begin
        if (!rs) begin sck <= 2'd0; sdat <= 2'd0; sld <= 2'd0; srd <= 2'd0; rd_p <= 1'b0; end
        else begin
            sck <= {sck[0], ui_in[4]}; sdat <= {sdat[0], ui_in[5]};
            sld <= {sld[0], ui_in[6]}; srd  <= {srd[0],  ui_in[3]};
            rd_p <= srd[1];
        end
    end
    wire rd_rise = srd[1] & ~rd_p;

    wire        fs_tick, s_tick, latch, load, boot, inv_pair, acc_clear;
    wire        cfg_change, sys_en_n, ota_en_n, cfg_pending;
    wire [12:0] act;
    wire [7:0]  slot_ctr;
    wire        y;
    wire [31:0] hold_acc1, hold_acc2;
    wire [15:0] hold_tag;
    wire        hold_boost, frame_ready, overrun;
    wire [2:0]  hold_trim;

    c9_fsdiv u_div (.clk(clk), .rst_n(rs), .div_code(act[9:7]), .fs_tick(fs_tick), .s_tick(s_tick), .bit_clk(fs_clk));

    c9_cfg u_cfg (.clk(clk), .rst_n(rs), .cfg_clk_s(sck[1]), .cfg_dat_s(sdat[1]), .cfg_ld_s(sld[1]),
                  .latch(latch), .act(act), .change(cfg_change), .sys_en_n(sys_en_n), .ota_en_n(ota_en_n),
                  .cfg_pending(cfg_pending));

    c9_seq u_seq (.clk(clk), .rst_n(rs), .fs_tick(fs_tick), .s_tick(s_tick), .comp_in(comp_in),
                  .n_code(act[11:10]), .sys_en_n(sys_en_n), .ota_en_n(ota_en_n), .cfg_change(cfg_change),
                  .latch(latch), .load(load), .boot(boot), .inv_pair(inv_pair), .slot_ctr(slot_ctr),
                  .rst_analog(rst_analog), .sys_swap(sys_swap), .ota_chop(ota_chop_phase), .y_force(y_force),
                  .bit_valid(bit_valid), .acc_clear(acc_clear), .y_dac(y));
    assign y_dac = y;

    // tag word: chop (= the sys_swap flop), order, n_code, sys_en, ota_en, short, invalid, frame_ctr
    wire [15:0] tag_in = {sys_swap, act[12], act[11:10], act[6], act[5], act[4], inv_pair, slot_ctr};

    c9_dec u_dec (.clk(clk), .rst_n(rs), .fs_tick(fs_tick), .acc_clear(acc_clear), .bit_valid(bit_valid), .y(y),
                  .load(load), .tag_in(tag_in), .boost_in(act[3]), .trim_in(act[2:0]), .rd_rise(rd_rise),
                  .hold_acc1(hold_acc1), .hold_acc2(hold_acc2), .hold_tag(hold_tag), .hold_boost(hold_boost),
                  .hold_trim(hold_trim), .frame_ready(frame_ready), .overrun(overrun));

    wire [15:0] status = {frame_ready, overrun, cfg_pending, hold_boost, hold_trim, 1'b0, hold_tag[7:0]};
    wire [7:0]  dbg_hi = {hold_tag[8], ota_chop_phase, sys_swap, rst_analog, fs_clk, frame_ready,
                          bit_valid, y & bit_valid};

    c9_rdbus u_bus (.clk(clk), .rst_n(rs), .addr_i(ui_in[2:0]), .dbg_i(ui_in[7]), .hold_acc1(hold_acc1),
                    .hold_acc2(hold_acc2), .hold_tag(hold_tag), .status(status), .dbg_hi(dbg_hi),
                    .uo_out(uo_out), .uio_out(uio_out));

    assign short_o = act[4];
    assign order_o = act[12];
    assign boost_o = act[3];
    assign trim_o  = act[2:0];
    // boot / acc_clear / s_tick used internally only
    wire _unused = &{1'b0, boot};
endmodule
