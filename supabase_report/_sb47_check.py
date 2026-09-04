# -*- coding: utf-8 -*-
"""token 有效性快速校验"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
c = http.client.HTTPSConnection(API_HOST, timeout=15, context=ctx)
h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
h.update(VDP_HEADERS)
t0 = time.time()
c.request('GET', '/v1/projects/%s' % PROJECT_REF, headers=h)
r = c.getresponse()
b = r.read(2000).decode('utf-8', errors='replace')
print('status=%s (%.1fs)' % (r.status, time.time() - t0))
print(b[:800])
