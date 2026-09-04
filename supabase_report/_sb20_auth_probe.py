# -*- coding: utf-8 -*-
"""Supabase 认证通道探针: Bearer JWT vs Cookie, platform vs v1 (零破坏只读)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, COOKIE_RAW, VDP_HEADERS, UA, API_HOST, TOKEN_EXP, ORG_SLUG, PROJECT_REF

now = int(time.time())
print('now=%d token_ttl=%ds' % (now, TOKEN_EXP - now), flush=True)
ctx = ssl.create_default_context()
out = []

def req(method, path, auth, body=None):
    c = http.client.HTTPSConnection(API_HOST, timeout=10, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(VDP_HEADERS)
    if auth == 'bearer':
        h["Authorization"] = "Bearer " + BEARER_JWT
    elif auth == 'cookie':
        h["Cookie"] = COOKIE_RAW
    elif auth == 'none':
        pass
    try:
        c.request(method, path, headers=h, body=body)
        r = c.getresponse()
        b = r.read(400).decode('utf-8', errors='replace')
        out.append('%-6s %-42s [%-7s] -> %s | %s' % (method, path, auth, r.status, b[:200].replace('\n', ' ')))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('%-6s %-42s [%-7s] -> ERR %s' % (method, path, auth, e))
        return 0, str(e)

# 1. platform 面
req('GET', '/platform/projects', 'bearer')
req('GET', '/platform/projects', 'cookie')
req('GET', '/platform/projects', 'none')
# 2. v1 面
req('GET', '/v1/projects', 'bearer')
req('GET', '/v1/profile', 'bearer')
req('GET', '/v1/projects', 'cookie')
# 3. org + project 详情
req('GET', '/platform/organizations/' + ORG_SLUG, 'bearer')
req('GET', '/platform/organizations/' + ORG_SLUG, 'cookie')
req('GET', '/platform/projects/' + PROJECT_REF, 'bearer')
# 4. v1 JIT/查询读面 (若 v1 bearer 通)
st, b = req('GET', '/v1/projects/' + PROJECT_REF + '/database/jit', 'bearer')
req('GET', '/v1/projects/' + PROJECT_REF + '/jit-access', 'bearer')
req('GET', '/v1/projects/' + PROJECT_REF + '/readonly', 'bearer')
req('GET', '/v1/snippets', 'bearer')
req('GET', '/v1/projects/' + PROJECT_REF + '/claim-token', 'bearer')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb20_probe.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
