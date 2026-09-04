# -*- coding: utf-8 -*-
"""重试 pw-grant 拿 authenticated token"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
AUTH_HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', host=AUTH_HOST):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(host, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "apikey": ANON_KEY}
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(10000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:4000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

st, b = req('POST', '/auth/v1/token?grant_type=password',
            {"email": "sbx_auvjijfz@qq.com", "password": "Sbxtest123!"}, 'pw-grant')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb65_grant.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
