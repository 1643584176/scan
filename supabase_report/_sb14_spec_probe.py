# -*- coding: utf-8 -*-
"""公开侦察14: Management API OpenAPI spec 公开 URL 探测 (零破坏)"""
import http.client, ssl, os

here = os.path.dirname(os.path.abspath(__file__))
cands = [
    ("api.supabase.com", "/openapi.json"),
    ("api.supabase.com", "/api/openapi.json"),
    ("api.supabase.com", "/api/v1/openapi.json"),
    ("api.supabase.com", "/v1/openapi.json"),
    ("api.supabase.com", "/api/v1-og.json"),
    ("api.supabase.com", "/swagger.json"),
    ("api.supabase.com", "/api/swagger.json"),
    ("api.supabase.com", "/api/v1/swagger.json"),
    ("api.supabase.com", "/api/v1/docs.json"),
    ("api.supabase.com", "/v1/docs.json"),
    ("supabase.com", "/docs/openapi.json"),
    ("supabase.com", "/docs/reference/api/openapi.json"),
    ("supabase.com", "/docs/reference/api/reference/openapi.json"),
]
out = []
ctx = ssl.create_default_context()
for host, path in cands:
    try:
        c = http.client.HTTPSConnection(host, timeout=8, context=ctx)
        c.request("GET", path, headers={"User-Agent": "Mozilla/5.0"})
        r = c.getresponse()
        body = r.read(300).decode('utf-8', errors='replace')
        out.append('%-22s %-42s %s %s | %s' % (
            host, path, r.status, r.getheader('Content-Type', '')[:30], body[:180].replace('\n', ' ')))
        c.close()
    except Exception as e:
        out.append('%-22s %-42s ERR %s' % (host, path, e))
open(os.path.join(here, '_sb14_spec.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
