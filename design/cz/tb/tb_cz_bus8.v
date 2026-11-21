`timescale 1ns/1ps
// Spec-only bench for cz_bus8 (WO-108 part 1): data = bsel ? bus[15:8] : bus[7:0], combinational.
module tb_cz_bus8;
  reg  [15:0] bus; reg bsel; wire [7:0] data;
  cz_bus8 dut(.bus(bus), .bsel(bsel), .data(data));
  integer errs = 0, n = 0, i, k;
  reg [7:0] exp;
  task chk; begin
    #1; exp = bsel ? bus[15:8] : bus[7:0]; n = n + 1;
    if (data !== exp) begin errs = errs + 1;
      if (errs < 10) $display("MISMATCH bus=%h bsel=%b data=%h exp=%h", bus, bsel, data, exp); end
  end endtask
  initial begin
    // fully exhaustive: 2 x 65536
    for (i = 0; i < 131072; i = i + 1) begin {bsel, bus} = i[16:0]; chk; end
    // corners incl. walking bits and byte-distinct patterns, both bsel orders
    for (k = 0; k < 16; k = k + 1) begin
      bsel = 0; bus = 16'h1 << k; chk; bsel = 1; chk; bsel = 0; chk;
      bus = ~(16'h1 << k); chk; bsel = 1; chk; bsel = 0; chk;
    end
    // combinational: bsel toggles with bus fixed, and bus toggles with bsel fixed, no clock
    bus = 16'hA55C; bsel = 0; chk; bsel = 1; chk; bsel = 0; chk; bsel = 1; chk;
    bus = 16'h5CA5; chk; bus = 16'hFF00; chk; bsel = 0; chk; bus = 16'h00FF; chk; bsel = 1; chk;
    // random sequence, single-input changes, back-to-back
    for (i = 0; i < 200000; i = i + 1) begin
      case ($urandom % 3)
        0: bus = $urandom; 1: bsel = $urandom; default: begin bus = $urandom; bsel = $urandom; end
      endcase
      chk;
    end
    // zero-delay-ish settling: data must not need a clock (no clock exists in this TB)
    $display("CHECKS=%0d ERRORS=%0d", n, errs);
    if (errs == 0) $display("TB_PASS"); else $display("TB_FAIL");
    $finish;
  end
  initial begin #100000000; $display("TB_FAIL watchdog"); $finish; end
endmodule
