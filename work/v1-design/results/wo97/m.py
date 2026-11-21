import json,sys,glob
r=sys.argv[1]
m=json.load(open(r+"/final/metrics.json"))
keys=[k for k in m if any(s in k for s in ("setup__ws","hold__ws","setup__vio","hold__vio","max_slew","max_cap","max_fanout","floating","drc__errors","lvs__","antenna","utilization","power__total","ir__drop__worst","area","xor","route__wirelength","design__instance__count"))]
for k in sorted(keys):
  if "__corner:" in k and not any(c in k for c in ("setup__ws","hold__ws","setup__vio","hold__vio","max_slew","max_cap","max_fanout")): continue
  print(k, m[k])
