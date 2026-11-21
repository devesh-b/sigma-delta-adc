// cz_bus8 (WO-108, D99a): byte-select read bus for the Chipalooza variant. Sits outside the hardened C9 macro.
//   data[7:0] = bsel ? bus[15:8] : bus[7:0]
// bus is the registered C9 read bus (16 bits). Pure combinational: no state, no clock. A valid byte appears one mux
// delay (gate delay, no clock) after a change of bsel; a change of bus propagates the same way. The consumer samples
// data only after bsel has been stable for at least that delay. Debug mode passes through unchanged: the bus then
// carries the debug signals and the mux selects the byte as above. No change to design/c9_digital/**.
module cz_bus8 (
    input  wire [15:0] bus,
    input  wire        bsel,
    output wire [7:0]  data
);
  assign data = bsel ? bus[15:8] : bus[7:0];
endmodule
