# -*- coding: utf-8 -*-
"""token 状态检查 + anon key signup 重试"""
import http.client, ssl, json, time, os, sys, random, string
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', host=API_HOST, headers_extra=None):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(host, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers_extra:
        h.update(headers_extra)
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(6000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 1. token 状态 (mgmt)
req('GET', '/v1/projects/%s' % PROJECT_REF, None, 'token-check',
    headers_extra={"Authorization": "Bearer " + BEARER_JWT})
# 2. signup with apikey (GoTrue)
suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
TEST_EMAIL = 'sbx_au_%s@example.com' % suffix
print('TEST_EMAIL=%s' % TEST_EMAIL)
st, b = req('POST', '/auth/v1/signup', {"email": TEST_EMAIL, "password": "Sbxtest123!"},
            'signup', host='%s.supabase.co' % PROJECT_REF,
            headers_extra={"apikey": ANON_KEY})

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb63_signup2.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
