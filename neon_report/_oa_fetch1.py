# -*- coding: utf-8 -*-
"""抓取 Neon API OpenAPI 规范(公开资产侦察)"""
import http.client, ssl, json

ctx = ssl.create_default_context()

def get(host, path, hdr=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': '*/*'}
        if hdr: h.update(hdr)
        conn.request('GET', path, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw
    except Exception as e:
        return 0, str(e).encode()

cands = [
    ('api-docs.neon.tech', '/openapi.json', None),
    ('api-docs.neon.tech', '/openapi/2.json', None),
    ('api-docs.neon.tech', '/openapi/2', None),
    ('raw.githubusercontent.com', '/api-evangelist/neon/main/apis.yml', None),
]
for host, path, hdr in cands:
    st, raw = get(host, path, hdr)
    print('==', host + path, '->', st, len(raw))
    if st == 200 and (raw[:1] in (b'{', b'[') or b'openapi' in raw[:500].lower() or b'swagger' in raw[:500].lower()):
        fn = r'D:\scan\neon_report\_openapi_dl.json' if b'json' in raw[:1] or raw[:1] in (b'{',) else r'D:\scan\neon_report\_openapi_dl.yaml'
        open(fn, 'wb').write(raw)
        print('saved', fn, raw[:200])
        break
    if st == 200:
        print('  head:', raw[:300])
