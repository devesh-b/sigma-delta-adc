# Run on the sandbox only. Emits vec.vh: one golden mode vector at the reset config (N 4096, order 2, sys+ota, fs_div 1).
import json, sys
d = json.load(open(sys.argv[1]))
for v in d['vectors']:
    c = v['config']
    if v.get('kind') == 'mode' and c['N'] == 4096 and c['order'] == 2 and c['chop_mode'] == 'ota+sys' \
       and not c['short'] and c['fs_div'] == 1 and c['boost'] == 0 and c['trim'] == 4:
        f = v['frames'][0]
        yb = int(f['ybits'], 16)
        nb = 4 * len(f['ybits'])
        assert nb == 4096
        with open(sys.argv[2], 'w') as o:
            o.write('localparam [4095:0] YBITS = 4096\'h%s;\n' % f['ybits'])
            o.write('localparam [79:0] WIRE = 80\'h%s;\n' % f['wire'])
            o.write('// id %s\n' % v['id'])
        print('vector', v['id'], 'wire', f['wire'])
        break
else:
    sys.exit('no vector')
