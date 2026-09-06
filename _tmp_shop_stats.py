# -*- coding: utf-8 -*-
import json

d = json.load(open(r'F:\scan\h1kit\cache\h1_data.json', encoding='utf-8'))
progs = d['hackerone'] if isinstance(d, dict) else d
for p in progs:
    url = p.get('url') or ''
    if url.rstrip('/').endswith('/shopify'):
        for k in sorted(p.keys()):
            print('%-45s %s' % (k, str(p.get(k))[:200]))
        break
