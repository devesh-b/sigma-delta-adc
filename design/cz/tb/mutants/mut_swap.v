// MUTANT: halves swapped
module cz_bus8(input [15:0] bus, input bsel, output [7:0] data);
  assign data = bsel ? bus[7:0] : bus[15:8];
endmodule
