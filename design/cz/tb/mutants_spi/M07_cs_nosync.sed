# M07 CS_n synchroniser bypassed: fall detected from the raw pin
s/wire cs_fall = cs_q3 & ~cs_q2;/wire cs_fall = cs_q1 \& ~cs_eff;/
