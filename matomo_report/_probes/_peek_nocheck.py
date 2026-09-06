# -*- coding: utf-8 -*-
import json

d = json.load(open('_nocheck_methods.json', encoding='utf-8'))
print('type:', type(d).__name__)
if isinstance(d, dict):
    print('keys:', len(d))
    for k, v in list(d.items())[:5]:
        print(k, '->', json.dumps(v, ensure_ascii=False)[:200])
else:
    print('n =', len(d))
    for v in d[:5]:
        print(json.dumps(v, ensure_ascii=False)[:200])
