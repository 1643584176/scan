# -*- coding: utf-8 -*-
"""下载 Neon OpenAPI v2 spec + api.md 离线分析"""
import http.client, ssl, json, re

ctx = ssl.create_default_context()

def get(path):
    conn = http.client.HTTPSConnection('neon.com', context=ctx, timeout=60)
    conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0'})
    r = conn.getresponse(); raw = r.read(); conn.close()
    return r.status, raw

st, raw = get('/api_spec/release/v2.json')
print('v2.json:', st, len(raw))
if st == 200:
    open(r'D:\scan\neon_report\_openapi_v2.json', 'wb').write(raw)
    spec = json.loads(raw)
    print('openapi:', spec.get('openapi'), '| servers:', spec.get('servers'))
    paths = spec.get('paths', {})
    print('paths total:', len(paths))
    # 按 tag 聚合
    from collections import Counter, defaultdict
    tagc = Counter()
    for p, ops in paths.items():
        for m, o in ops.items():
            if isinstance(o, dict) and 'operationId' in o:
                for t in o.get('tags', ['_untagged']):
                    tagc[t] += 1
    for t, c in tagc.most_common(60):
        print('TAG %-28s %d' % (t, c))

st2, raw2 = get('/docs/reference/api.md')
print('api.md:', st2, len(raw2))
if st2 == 200:
    open(r'D:\scan\neon_report\_api_doc.md', 'wb').write(raw2)
