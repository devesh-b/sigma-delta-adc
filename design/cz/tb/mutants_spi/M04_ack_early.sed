# M04 ack (rd) raised at the CS_n fall, before the snapshot is valid
s/snap_valid <= 1'b0; torn <= 1'b0; st <= S_CAP;/snap_valid <= 1'b0; torn <= 1'b0; st <= S_CAP; rd_r <= 1'b1;/
