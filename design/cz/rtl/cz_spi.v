// cz_spi (D102): SPI read-port wrapper for the Chipalooza variant. Sits outside the hardened C9 macro, next to cz_bus8.
// NOT YET SIMULATED OR LINTED.
//
// Function: SPI target, mode 0 (CPOL 0, CPHA 0), MSB first, read-only. Shift order on MISO:
//   status(16) acc1(32) acc2(32) tag(16) = 96 bits. acc1/acc2 are the 32-bit sign-extended hold words of C9.
// When spi_en = 1 the wrapper drives C9's addr[2:0], rd and dbg (dbg forced 0); the external addr/rd/dbg are ignored.
// data_o[0] = MISO, data_o[7:1] = 0. When spi_en = 0 everything passes through (data_o = data_in, addr_o = addr_i ...).
// spi_en is static and may change only while spi_cs_n is high. MISO is not tri-stated.
//
// C9 read-port facts used (design/c9_digital/rtl/c9_rdbus.v, c9_core.v, c9_dec.v):
//   - addr_i is 2-FF synchronised (a1,a2), then a 16-bit word register: a word is valid on bus[15:0] 3 clk after the
//     addr flop changes, i.e. it is stable in the 4th cycle. bus = {uo_out, uio_out} with dbg = 0.
//   - addr map: 0 acc1[31:16], 1 acc1[15:0], 2 acc2[31:16], 3 acc2[15:0], 4 tag, 5 status; status[7:0] = tag[7:0]
//     (frame counter), so tag and status carry the same 8-bit frame counter when no frame loaded in between.
//   - rd (ui_in[3]) is 2-FF synchronised and edge detected (rd_rise). Only the rising edge matters; C9 snapshots
//     hold_tag[7:0] on rd_rise and clears frame_ready/overrun one clk later if the counter is unchanged (rd guard, D66).
//     rd is held 2 clk here (one would do; two is margin) and is low otherwise.
//
// ---- clk-domain capture engine (FSM IDLE -> CAP -> ACK -> DONE) ----
//   CS_n sync: cs_q1, cs_q2 (2 FF), cs_q3 = delayed copy; fall = cs_q3 & ~cs_q2.
//   Addresses are issued pipelined, one per clk, in the order tag(4), acc1h(0), acc1l(1), acc2h(2), acc2l(3), status(5)
//   (tag first, status last). addr_r is a flop. Address issued in CAP cycle c is visible to C9 in cycle c+1 and its
//   word is stable in cycle c+4, so the word of the address issued at c is sampled at the end of cycle c+4:
//   samples in cycles 4..9, compare of the two frame counters in cycle 10.
//   If tag[7:0] != status[7:0] (a frame loaded during capture) the whole snapshot is retaken (up to 2 retakes).
//   Else snap_valid <= 1 and rd is pulsed (ACK, 2 clk). Snapshot registers are written only in CAP and are static
//   from snap_valid until the next CS_n fall, so the SCLK domain can read them without a CDC.
//
// ---- worst-case timing in clk (budget: complete within 32 clk of the CS_n fall) ----
//   async CS_n fall -> FSM leaves IDLE: <= 4 clk  (up to 1 clk until the first edge, edges e1 e2 sync, e3 FSM)
//   CAP cycles 0..10 = 11 clk  -> snap_valid set at end of cycle 10
//   no retake : snapshot complete (all words sampled) <= 4+10 = 14 clk, snap_valid <= 15 clk, rd to C9 at 15..16
//   one retake: +11 clk -> snap_valid <= 26 clk (< 32 budget). A retake needs a frame load inside the 11 clk window;
//               the frame period is >= 16.5 us (about 790 clk at 48 MHz) so a second retake is not credible.
//   two retakes (defined, practically impossible): snap_valid <= 37 clk; after the 3rd attempt the snapshot is
//               accepted as is (torn, internal flag only) so the FSM cannot hang.
//   The host must wait >= 32 clk from CS_n fall to the first SCLK rising edge (documented limit).
//
// ---- defined behaviour on abnormal CS_n ----
//   CS_n rises (seen in cs_q2) during CAP: capture aborted, snap_valid <= 0, no ack, FSM -> IDLE. The next fall restarts.
//   CS_n high time must be >= 8 clk (>= 2 clk is needed by the synchroniser; a shorter pulse may be missed).
//   CS_n falls again before the snapshot finished = the above (it must have risen first). snap_valid is 0 until a
//   good snapshot exists; MISO reads 0 while snap_valid = 0.
//   CS_n rises during ACK: the ack completes (the snapshot was already good); FSM then waits in DONE until CS_n is high.
//   Partial read: SCLK stops, CS_n rises, snapshot stays; no ack until the next CS_n fall (the next read re-acks,
//   which is harmless as the counter guard in C9 only clears a frame whose counter matches).
//   Residual race (C9 unchanged): a frame loaded between the status sample and the rd edge arriving at C9's guard
//   (about 5 clk) can be cleared without having been read; the host sees it as a gap in the frame counter (tag).
//
// ---- SCLK domain ----
//   rcnt: counts rising SCLK edges, async reset (to 0) while CS_n is high (or spi_en = 0); saturates at 96.
//   ptr (negedge SCLK flop, same async reset): ptr <= rcnt at each falling edge, so MISO changes only after a falling
//   edge. MISO = snap[95 - ptr] (combinational mux on static data), 0 when ptr >= 96 or snap_valid = 0.
//   Before the first SCLK edge ptr = 0, hence bit 95 (status[15]) is on MISO before the first rising edge as long as
//   the snapshot has completed (the 32 clk setup rule). snap_valid is a clk-domain level read asynchronously by the
//   MISO mux; it is stable for the whole read when the setup rule is met.
module cz_spi (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        spi_en,
    input  wire        spi_sck,
    input  wire        spi_cs_n,
    // external C9 read-port pins (pass-through when spi_en = 0)
    input  wire [2:0]  addr_i,
    input  wire        rd_i,
    input  wire        dbg_i,
    // C9 registered read bus {uo_out, uio_out} (word valid 3 clk after addr change) and cz_bus8 output
    input  wire [15:0] bus,
    input  wire [7:0]  data_in,
    // to C9 inputs and to the data[7:0] pins
    output wire [2:0]  addr_o,
    output wire        rd_o,
    output wire        dbg_o,
    output wire [7:0]  data_o
);
    localparam [1:0] S_IDLE = 2'd0, S_CAP = 2'd1, S_ACK = 2'd2, S_DONE = 2'd3;

    // ---- CS_n synchroniser (clk domain). spi_en = 0 keeps the engine idle by forcing "CS_n high".
    wire cs_eff = spi_cs_n | ~spi_en;
    reg  cs_q1, cs_q2, cs_q3;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin cs_q1 <= 1'b1; cs_q2 <= 1'b1; cs_q3 <= 1'b1; end
        else        begin cs_q1 <= cs_eff; cs_q2 <= cs_q1; cs_q3 <= cs_q2; end
    end
    wire cs_fall = cs_q3 & ~cs_q2;

    // ---- capture FSM
    reg [1:0]  st;
    reg [3:0]  cnt;
    reg [1:0]  att;
    reg [2:0]  addr_r;
    reg        rd_r;
    reg        snap_valid;
    reg        torn;                       // internal: snapshot accepted after the last retake with mismatching counters
    reg [15:0] w_tag, w_a1h, w_a1l, w_a2h, w_a2l, w_st;

    reg [2:0] seq;                         // address issued in CAP cycle cnt
    always @* begin
        case (cnt)
            4'd0:    seq = 3'd4;           // tag first
            4'd1:    seq = 3'd0;           // acc1[31:16]
            4'd2:    seq = 3'd1;           // acc1[15:0]
            4'd3:    seq = 3'd2;           // acc2[31:16]
            4'd4:    seq = 3'd3;           // acc2[15:0]
            default: seq = 3'd5;           // status last (cnt = 5)
        endcase
    end

    wire mism = (w_tag[7:0] != w_st[7:0]);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= S_IDLE; cnt <= 4'd0; att <= 2'd0; addr_r <= 3'd0; rd_r <= 1'b0;
            snap_valid <= 1'b0; torn <= 1'b0;
            w_tag <= 16'd0; w_a1h <= 16'd0; w_a1l <= 16'd0; w_a2h <= 16'd0; w_a2l <= 16'd0; w_st <= 16'd0;
        end else begin
            case (st)
                S_IDLE: begin
                    cnt <= 4'd0; att <= 2'd0; rd_r <= 1'b0; addr_r <= 3'd0;
                    if (cs_fall) begin
                        snap_valid <= 1'b0; torn <= 1'b0; st <= S_CAP;
                    end
                end
                S_CAP: begin
                    if (cs_q2) begin                       // CS_n went high: abort, no ack
                        st <= S_IDLE; snap_valid <= 1'b0; cnt <= 4'd0; addr_r <= 3'd0;
                    end else begin
                        cnt <= cnt + 4'd1;
                        if (cnt <= 4'd5) addr_r <= seq;
                        case (cnt)
                            4'd4: w_tag <= bus;
                            4'd5: w_a1h <= bus;
                            4'd6: w_a1l <= bus;
                            4'd7: w_a2h <= bus;
                            4'd8: w_a2l <= bus;
                            4'd9: w_st  <= bus;
                            default: ;
                        endcase
                        if (cnt == 4'd10) begin
                            if (mism && att != 2'd2) begin // frame loaded during capture: retake whole snapshot
                                att <= att + 2'd1; cnt <= 4'd0;
                            end else begin
                                torn <= mism; snap_valid <= 1'b1; rd_r <= 1'b1; cnt <= 4'd0; st <= S_ACK;
                            end
                        end
                    end
                end
                S_ACK: begin                               // rd high for 2 clk (cnt 0,1)
                    cnt <= cnt + 4'd1;
                    if (cnt == 4'd1) begin rd_r <= 1'b0; st <= S_DONE; end
                end
                default: begin                             // S_DONE: wait for CS_n high
                    if (cs_q2) st <= S_IDLE;
                end
            endcase
        end
    end

    // ---- snapshot, MSB first: status, acc1, acc2, tag
    wire [95:0] snap = {w_st, w_a1h, w_a1l, w_a2h, w_a2l, w_tag};

    // ---- SCLK domain
    wire sclk_rst_n = ~cs_eff;                 // async reset while CS_n high; deasserts on CS_n fall (SCLK idle low)
    reg [6:0] rcnt, ptr;
    always @(posedge spi_sck or negedge sclk_rst_n) begin
        if (!sclk_rst_n)       rcnt <= 7'd0;
        else if (rcnt != 7'd96) rcnt <= rcnt + 7'd1;
    end
    always @(negedge spi_sck or negedge sclk_rst_n) begin
        if (!sclk_rst_n) ptr <= 7'd0;
        else             ptr <= rcnt;
    end
    wire miso = (snap_valid && ptr < 7'd96) ? snap[7'd95 - ptr] : 1'b0;

    // ---- outputs
    assign addr_o = spi_en ? addr_r : addr_i;
    assign rd_o   = spi_en ? rd_r   : rd_i;
    assign dbg_o  = spi_en ? 1'b0   : dbg_i;
    assign data_o = spi_en ? {7'd0, miso} : data_in;
endmodule
