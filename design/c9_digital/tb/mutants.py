"""C9 RTL mutants (C9_VERIF_PLAN section 6, M01-M59 + M07b), WO-40.  Throwaway copies only.

    python3 mutants.py make MID DEST     copy ../rtl to DEST/rtl and apply mutant MID (each edit must match once)
    python3 mutants.py tests MID         planned killing tests first, then every other test (space separated)
    python3 mutants.py list              all mutant ids
    python3 mutants.py formal            mutants that also get the per-property formal run

Never writes to ../rtl.  Each mutant = list of (file, old, new) exact substring edits on the pristine RTL.
"""
import os
import shutil
import sys

ALL_TESTS = ["s01_reset_idle", "s02_reset_pair_golden", "d_dec01_golden_vectors", "d_dec03_streams",
             "a_seq01_trace_ctl", "d_cfg05_sequences", "d_cfg02_shift", "a_cfg01_edge_sweep", "a_frm02_rd_race",
             "d_frm04_overrun", "d_fs01_div_codes", "a_rst01_async_mid", "d_bus03_debug", "d_inv02_each_field",
             "d_bus02_latency", "r01_random"]
DEC, SEQ, CFG = "c9_dec.v", "c9_seq.v", "c9_cfg.v"
CORE, BUS, DIV, TOP = "c9_core.v", "c9_rdbus.v", "c9_fsdiv.v", "tt_um_sd_adc_c9.v"
GOLD = ["s02_reset_pair_golden", "d_dec01_golden_vectors", "d_dec03_streams"]
A1 = "wire [31:0] a1n = acc1 + (y ? 32'd1 : 32'hFFFFFFFF);"
A2 = "wire [31:0] a2n = acc2 + acc1;"
SW = "if (slot_start) sys_swap <= sys_en_n & ctr_n[0];"
ACTN = "wire [12:0] act_n    = latch ? shadow : act;"
ACTQ = "act         <= act_n;"
CTR = "wire [7:0] ctr_n   = (slot_start & ~boot) ? slot_ctr + 8'd1 : slot_ctr;"
TAG = "wire [15:0] tag_in = {sys_swap, act[12], act[11:10], act[6], act[5], act[4], inv_pair, slot_ctr};"
RDR = "wire rd_rise = srd[1] & ~rd_p;"
LDR = "wire       ld_rise = cfg_ld_s  & ~ld_p;"

M = {
    "M01": ([(DEC, A2, "wire [22:0] a2t = acc2[22:0] + acc1[22:0]; wire [31:0] a2n = {{9{a2t[22]}}, a2t};")],
            ["d_dec03_streams", "d_dec01_golden_vectors"]),
    "M02": ([(DEC, A1, "wire [12:0] a1t = acc1[12:0] + (y ? 13'd1 : 13'h1FFF); wire [31:0] a1n = {{19{a1t[12]}}, a1t};")],
            ["d_dec03_streams"]),
    "M03": ([(SEQ, "bit_valid  <= ~rst_n_nx;", "bit_valid  <= ~rst_n_nx & ~(c == 13'd1);")], GOLD),
    "M04": ([(DEC, "if (acc_clear) begin acc1 <= 32'd0; acc2 <= 32'd0; end",
              "if (acc_clear) begin acc1 <= (y ? 32'd1 : 32'hFFFFFFFF); acc2 <= 32'd0; end")], GOLD),
    "M05": ([(DEC, "(y ? 32'd1 : 32'hFFFFFFFF)", "(y ? 32'hFFFFFFFF : 32'd1)")], GOLD),
    "M06": ([(CORE, "tag_in = {sys_swap,", "tag_in = {~sys_swap,")], GOLD + ["a_seq01_trace_ctl"]),
    "M07": ([(SEQ, SW, "if (c == 13'd0 && !boot) sys_swap <= sys_en_n & slot_ctr[0];")], ["a_seq01_trace_ctl"]),
    "M07b": ([(SEQ, "reg        comp_s;", "reg        comp_s; reg sw_d;\n    always @(posedge clk or negedge rst_n) "
               "if (!rst_n) sys_swap <= 1'b0; else sys_swap <= sw_d;"),
              (SEQ, "rst_analog <= 1'b1; sys_swap <= 1'b0;", "rst_analog <= 1'b1; sw_d <= 1'b0;"),
              (SEQ, SW, "if (slot_start) sw_d <= sys_en_n & ctr_n[0];")], ["a_seq01_trace_ctl"]),
    "M08": ([(DEC, A2, "wire [31:0] a2n = acc2 + a1n;")], GOLD),
    "M09": ([(DEC, "hold_acc2  <= a2n;", "hold_acc2  <= {8'd0, a2n[23:0]};")], ["d_dec03_streams"] + GOLD),
    "M10": ([(SEQ, "y_dac      <= (c == 13'd1) ? 1'b1 : comp_s;", "y_dac      <= comp_s;")], GOLD),
    "M11": ([(CORE, "assign y_dac = y;", "assign y_dac = y & ~y_force;")], ["a_seq01_trace_ctl", "d_bus03_debug"]),
    "M12": ([(SEQ, "acc_clear  <= (c == 13'd0) & ~slot_start;", "acc_clear  <= slot_start;")],
            ["a_seq01_trace_ctl"] + GOLD),
    "M13": ([(DEC, "if (acc_clear) begin acc1", "if (1'b0) begin acc1")], GOLD),
    "M14": ([(CORE, "bit_valid, y & bit_valid};", "bit_valid, y};")], ["d_bus03_debug", "a_seq01_trace_ctl"]),
    "M15": ([(SEQ, "ota_chop   <= ota_en_n & ~rst_n_nx & c_n[0];", "ota_chop   <= ota_en_n & ~ota_chop;")],
            ["a_seq01_trace_ctl"]),
    "M16": ([(SEQ, "ota_chop   <= ota_en_n & ~rst_n_nx & c_n[0];", "ota_chop   <= ~rst_n_nx & c_n[0];")],
            ["a_seq01_trace_ctl"]),
    "M17": ([(CORE, TAG, "reg tchop; always @(posedge clk) if (load & fs_tick) tchop <= sys_swap;\n    "
              + TAG.replace("{sys_swap,", "{tchop,"))], GOLD + ["a_seq01_trace_ctl"]),
    "M18": ([(CORE, "tag_in = {sys_swap,", "tag_in = {slot_ctr[0],")], GOLD + ["d_cfg05_sequences"]),
    "M19": ([(CFG, ACTN, "wire [12:0] act_n    = ld_rise ? shift_eff : act;")], ["d_cfg05_sequences", "a_cfg01_edge_sweep"]),
    "M20": ([(SEQ, "assign latch = fs_tick & slot_start & ~ctr_n[0];", "assign latch = fs_tick & slot_start;")],
            ["d_cfg05_sequences", "d_inv02_each_field"]),
    "M21": ([(SEQ, "assign latch = fs_tick & slot_start & ~ctr_n[0];", "assign latch = fs_tick & slot_start & ctr_n[0];")],
            ["d_cfg05_sequences"]),
    "M22": ([(CFG, ACTN, "wire [12:0] act_n    = latch ? shadow_n : act;")], ["a_cfg01_edge_sweep", "d_cfg05_sequences"]),
    "M23": ([(CFG, "reg        ck_p, ld_p;", "reg        ck_p, ld_p, ld_p2;"),
             (CFG, LDR, "wire       ld_rise = ld_p & ~ld_p2;"),
             (CFG, "ck_p <= cfg_clk_s; ld_p <= cfg_ld_s;", "ck_p <= cfg_clk_s; ld_p <= cfg_ld_s; ld_p2 <= ld_p;"),
             (CFG, "ck_p <= 1'b0; ld_p <= 1'b0;", "ck_p <= 1'b0; ld_p <= 1'b0; ld_p2 <= 1'b0;")],
            ["a_cfg01_edge_sweep"]),
    "M24": ([(CORE, "act[4], inv_pair, slot_ctr};", "act[4], inv_pair & ~slot_ctr[0], slot_ctr};")],
            ["d_inv02_each_field", "d_cfg05_sequences"]),
    "M25": ([(SEQ, "if (latch) inv_pair <= boot | cfg_change;", "if (latch) inv_pair <= cfg_change;")],
            ["s02_reset_pair_golden", "s01_reset_idle"]),
    "M26": ([(CFG, "reg        ck_p, ld_p;", "reg        ck_p, ld_p; reg wr;"),
             (CFG, "assign change   = (shadow != act);", "assign change   = (shadow != act) | wr;"),
             (CFG, "shadow      <= shadow_n;", "shadow      <= shadow_n; wr <= ld_rise ? 1'b1 : (latch ? 1'b0 : wr);"),
             (CFG, "cfg_pending <= 1'b0;", "cfg_pending <= 1'b0; wr <= 1'b0;")], ["d_inv02_each_field"]),
    "M27": ([(CFG, "assign change   = (shadow != act);", "assign change   = (shadow[12:4] != act[12:4]);")],
            ["d_inv02_each_field"]),
    "M28": ([(CFG, ACTQ, "act         <= {act_n[12:4], shadow_n[3], act_n[2:0]};")], ["d_inv02_each_field"]),
    "M29": ([(CFG, "1'b0, 1'b0, 3'd4};", "1'b0, 1'b0, 3'd0};")], ["s01_reset_idle"]),
    "M30": ([(SEQ, CTR, "wire [7:0] ctr_n   = (slot_start & ~boot) ? ((cfg_change & slot_ctr[0]) ? 8'd0 : "
              "slot_ctr + 8'd1) : slot_ctr;")], ["d_cfg05_sequences", "d_inv02_each_field"]),
    "M31": ([(SEQ, CTR, "wire [7:0] ctr_n   = (slot_start & ~boot) ? {1'b0, slot_ctr[6:0] + 7'd1} : slot_ctr;")],
            ["d_cfg05_sequences", "r01_random"]),
    "M32": ([(DEC, "wire        load_now = fs_tick & load;",
              "reg ld_dly = 1'b0; always @(posedge clk) if (fs_tick) ld_dly <= load;\n    "
              "wire        load_now = fs_tick & ld_dly;"),
             (DEC, "hold_acc1  <= a1n;", "hold_acc1  <= acc1;"), (DEC, "hold_acc2  <= a2n;", "hold_acc2  <= acc2;")],
            GOLD),
    "M33": ([(DEC, "hold_acc1  <= a1n;", "hold_acc1  <= acc1;"), (DEC, "hold_acc2  <= a2n;", "hold_acc2  <= acc2;")],
            GOLD),
    "M34": ([(CORE, "cfg_pending, hold_boost, hold_trim,", "cfg_pending, act[3], act[2:0],")],
            ["d_inv02_each_field", "d_dec01_golden_vectors"]),
    "M35": ([(DEC, "if (frame_ready) overrun <= 1'b1;", "if (1'b0) overrun <= 1'b1;")], ["d_frm04_overrun"]),
    "M36": ([(DEC, "if (frame_ready) overrun <= 1'b1;", "overrun <= frame_ready & ~overrun;")], ["d_frm04_overrun"]),
    "M37": ([(DEC, "if (clr_pend && hctr_n == snap) begin", "if (clr_pend) begin")], ["a_frm02_rd_race"]),
    "M38": ([(CORE, RDR, "wire rd_rise = srd[1];")], ["a_frm02_rd_race", "d_frm04_overrun"]),
    "M39": ([(CORE, RDR, "wire rd_rise = ui_in[3] & ~srd[0];")], ["a_frm02_rd_race"]),
    "M40": ([(DEC, "                frame_ready <= 1'b0;\n                overrun     <= 1'b0;",
              "                overrun     <= 1'b0;")], ["d_frm04_overrun", "a_frm02_rd_race"]),
    "M41": ([(BUS, "3'd1:    word <= hold_acc1[15:0];", "3'd1:    word <= hold_acc2[31:16];"),
             (BUS, "3'd2:    word <= hold_acc2[31:16];", "3'd2:    word <= hold_acc1[15:0];")], GOLD),
    "M42": ([(BUS, "3'd2:    word <= hold_acc2[31:16];", "3'd2:    word <= hold_acc2[15:0];"),
             (BUS, "3'd3:    word <= hold_acc2[15:0];", "3'd3:    word <= hold_acc2[31:16];")], GOLD),
    "M43": ([(BUS, "default: word <= 16'd0;", "default: word <= a2[0] ? status : hold_tag;")],
            ["d_bus02_latency", "s01_reset_idle"]),
    "M44": ([(CORE, "ota_chop_phase, sys_swap, rst_analog", "sys_swap, ota_chop_phase, rst_analog")], ["d_bus03_debug"]),
    "M45": ([(TOP, "assign uio_oe = 8'hFF;", "assign uio_oe = rst_n ? 8'hFF : 8'h00;")], ["s01_reset_idle"]),
    "M46": ([(DIV, "3'd0:    begin div_m1 = 8'd11;  half_m1 = 8'd5;  end",
              "3'd0:    begin div_m1 = 8'd23;  half_m1 = 8'd11;  end")], ["d_fs01_div_codes"]),
    "M47": ([(CFG, "? 3'd1 : fsd_raw", "? 3'd0 : fsd_raw")], ["d_fs01_div_codes", "d_cfg05_sequences"]),
    "M48": ([(CFG, ACTQ, "act         <= {act_n[12:10], shadow_n[9:7], act_n[6:0]};")],
            ["d_fs01_div_codes", "d_cfg05_sequences"]),
    "M49": ([(CFG, "shift <= {shift[14:0], cfg_dat_s};", "shift <= {cfg_dat_s, shift[15:1]};")], ["d_cfg02_shift"]),
    "M50": ([(CFG, "wire       ck_rise = cfg_clk_s & ~ck_p;", "wire       ck_rise = ~cfg_clk_s & ck_p;")],
            ["d_cfg02_shift"]),
    "M51": ([(CFG, LDR, "wire       ld_rise = cfg_ld_s;")], ["d_cfg02_shift"]),
    "M52": ([(CFG, "if (ld_rise)       shift <= 16'd0;", "if (1'b0)       shift <= 16'd0;")], ["d_cfg02_shift"]),
    "M53": ([(CORE, "always @(posedge clk or negedge rst_n) begin\n        if (!rst_n) begin r1",
              "always @(posedge clk) begin\n        if (!rst_n) begin r1")], ["a_rst01_async_mid"]),
    "M54": ([(DEC, "hold_acc1 <= 32'd0; hold_acc2 <= 32'd0;", ""),
             (DEC, "frame_ready <= 1'b0; overrun <= 1'b0; snap", "overrun <= 1'b0; snap")],
            ["a_rst01_async_mid", "s01_reset_idle"]),
    "M55": ([(CFG, ACTQ, "act         <= {act_n[12:5], shadow_n[4], act_n[3:0]};")],
            ["d_inv02_each_field", "d_cfg05_sequences"]),
    "M56": ([(CFG, "cfg_pending <= (shadow_n != act_n);", "cfg_pending <= (shadow_n == act_n);")],
            ["d_cfg05_sequences", "s01_reset_idle"]),
    "M57": ([(SEQ, "if (s_tick) comp_s <= comp_in;", "if (fs_tick) comp_s <= comp_in;")], GOLD),
    "M58": ([(DIV, "default: begin div_m1 = 8'd23;", "default: begin div_m1 = 8'd24;")],
            ["s01_reset_idle", "d_fs01_div_codes"]),
    "M59": ([(CORE, "1'b0, hold_tag[7:0]};", "1'b0, slot_ctr};")], ["d_dec01_golden_vectors", "d_frm04_overrun"]),
    # WO-40 additions: give F17 and F10 a mutant (no plan mutant breaks them)
    "M60": ([(SEQ, "rst_analog <= 1'b1; sys_swap <= 1'b0;", "rst_analog <= 1'b0; sys_swap <= 1'b0;")], ["s01_reset_idle"]),
    "M61": ([(SEQ, "bit_valid  <= ~rst_n_nx;", "bit_valid  <= ~rst_n_nx & ~(c == 13'd5);")], ["a_seq01_trace_ctl"]),
}
FORMAL = ["M07", "M07b", "M19", "M20", "M21", "M22", "M24", "M30", "M31", "M35", "M36", "M37", "M45",
          "M03", "M10", "M15", "M16", "M53", "M58", "M60", "M61"]


def make(mid, dest):
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "..", "rtl")
    out = os.path.join(dest, "rtl")
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(src, out)
    for f, old, new in M[mid][0]:
        p = os.path.join(out, f)
        txt = open(p).read()
        n = txt.count(old)
        if n != 1:
            sys.exit(f"{mid}: edit in {f} matches {n} times: {old!r}")
        open(p, "w").write(txt.replace(old, new))
    print(f"{mid}: {len(M[mid][0])} edit(s) -> {out}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "make":
        make(sys.argv[2], sys.argv[3])
    elif cmd == "tests":
        first = M[sys.argv[2]][1]
        print(" ".join(first + [t for t in ALL_TESTS if t not in first]))
    elif cmd == "list":
        print(" ".join(M))
    elif cmd == "formal":
        print(" ".join(FORMAL))
