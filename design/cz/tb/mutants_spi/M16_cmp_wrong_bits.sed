# M16 frame-counter compare on the wrong bits: always mismatches, 2 retakes, snapshot past the 32 clk budget
s/wire mism = (w_tag\[7:0\] != w_st\[7:0\]);/wire mism = (w_tag[15:8] != w_st[15:8]);/
