# M13 external rd leaks to C9 in SPI mode
s/assign rd_o *= spi_en ? rd_r *: rd_i;/assign rd_o   = spi_en ? (rd_r | rd_i) : rd_i;/
