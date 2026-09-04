# -*- coding: utf-8 -*-
"""公开侦察1: Supabase Management API OpenAPI 定位下载(公开资源)
候选: api.supabase.com/v1/openapi.json / docs 的 spec 路径"""
import http.client, ssl, json, os

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))

def get(host, path):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        r = conn.getresponse()
        raw = r.read()
        conn.close()
        return r.status, raw[:2000]
    except Exception as e:
        return -1, str(e).encode()

cands = [
    ('api.supabase.com', '/v1/openapi.json'),
    ('api.supabase.com', '/v1/'),
    ('api.supabase.com', '/v1/openapi'),
    ('supabase.com', '/docs/reference/api/openapi.json'),
    ('supabase.com', '/docs/_next/data/landing-v2.0.0/en/docs/reference/api.json'),
]
for h, p in cands:
    st, b = get(h, p)
    print('%-30s %-45s %s %s' % (h, p, st, b[:200].decode('utf-8', 'ignore').replace('\n', ' ')), flush=True)
