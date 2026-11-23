# M06 dbg not forced to 0 in SPI mode
s/assign dbg_o *= spi_en ? 1'b0 *: dbg_i;/assign dbg_o  = dbg_i;/
