# M14 external addr leaks to C9 in SPI mode
s/assign addr_o = spi_en ? addr_r : addr_i;/assign addr_o = spi_en ? (addr_r | addr_i) : addr_i;/
