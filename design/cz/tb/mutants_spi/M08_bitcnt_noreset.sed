# M08 SCLK bit counter / pointer not reset by CS_n high (only by chip reset)
s/wire sclk_rst_n = ~cs_eff;/wire sclk_rst_n = rst_n;/
