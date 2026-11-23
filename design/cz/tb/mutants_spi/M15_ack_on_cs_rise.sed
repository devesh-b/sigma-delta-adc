# M15 ack on CS_n rise instead of at the snapshot (review finding SPI-3)
s/snap_valid <= 1'b1; rd_r <= 1'b1;/snap_valid <= 1'b1; rd_r <= 1'b0;/
s/if (cs_q2) st <= S_IDLE;/if (cs_q2) begin st <= S_IDLE; rd_r <= 1'b1; end/
