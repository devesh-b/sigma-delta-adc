// Spec-written known-good reference (control: bench must ACCEPT)
module cz_bus8(input [15:0] bus, input bsel, output [7:0] data);
  assign data = bsel ? bus[15:8] : bus[7:0];
endmodule
