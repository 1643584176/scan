# -*- coding: utf-8 -*-
import json, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_q1_paths.json')
d = json.load(open(p, encoding='utf-8'))
print('TYPE:', type(d))
if isinstance(d, dict):
    ks = list(d.keys())
    print('KEYS(%d):' % len(ks), ks[:30])
    # 打印第一个值样例
    k0 = ks[0]
    v0 = d[k0]
    print('SAMPLE[%s]:' % k0, str(v0)[:300])
elif isinstance(d, list):
    print('LEN:', len(d))
    print('SAMPLE[0]:', str(d[0])[:300])
    if len(d) > 1:
        print('SAMPLE[1]:', str(d[1])[:300])
