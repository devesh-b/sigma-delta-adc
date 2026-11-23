# M09 tag word sampled one clk early (before the C9 word is valid)
s/4'd4: w_tag <= bus;/4'd3: w_tag <= bus;/
