# -*- coding: utf-8 -*-
"""调用 kf1 invocation_url:对比 无/有 X-Bug-Bounty header 的 403 差异"""
import http.client, ssl
ctx = ssl.create_default_context()
HOST = 'br-wandering-field-w2ob6mpn-kf1.compute.c-1.us-east-2.aws.neon.build'

for tag, hdrs in [('no-header', {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}),
                  ('xbb', {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'X-Bug-Bounty': 'xxbo'})]:
    c = http.client.HTTPSConnection(HOST, context=ctx, timeout=30)
    c.request('GET', '/', headers=hdrs)
    r = c.getresponse(); raw = r.read(); st = r.status; ch = dict(r.getheaders()); c.close()
    print('[%s] status: %d | server: %s' % (tag, st, ch.get('Server')))
    print('   body:', raw.decode(errors='replace')[:800])
