# M02 MISO pointer advances on the rising SCLK edge (mode 0 needs falling)
s/always @(negedge spi_sck or negedge sclk_rst_n)/always @(posedge spi_sck or negedge sclk_rst_n)/
