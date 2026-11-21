// MUTANT: bsel stuck at 0
module cz_bus8(input [15:0] bus, input bsel, output [7:0] data);
  wire b = 1'b0;
  assign data = b ? bus[15:8] : bus[7:0];
endmodule
