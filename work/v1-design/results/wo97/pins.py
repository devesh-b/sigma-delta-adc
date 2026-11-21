import re,sys
t=open(sys.argv[1]).read()
for m in re.finditer(r"PIN (\S+)(.*?)END \1",t,re.S):
    r=re.search(r"LAYER (\S+) ;\s*RECT ([\d.\s-]+);",m.group(2))
    if r: x0,y0,x1,y1=map(float,r.group(2).split()); print(f"{m.group(1):16s} {r.group(1):5s} {(x0+x1)/2:8.3f} {(y0+y1)/2:8.3f}")
    else: print(m.group(1),"(no simple rect)")
