# -*- coding: utf-8 -*-
"""重试: 注册用户 B + 确认 + grant token"""
import http.client, ssl, json, time, os, sys, random, string, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
AUTH_HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', host=AUTH_HOST, headers_extra=None):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers_extra:
        h.update(headers_extra)
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    for attempt in range(3):
        try:
            c.request(method, path, headers=h, body=body_j)
            r = c.getresponse()
            b = r.read(8000).decode('utf-8', errors='replace')
            out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
            c.close()
            return r.status, b
        except Exception as e:
            out.append('### [%s] %s %s attempt%d ERR %s' % (tag, method, path, attempt + 1, e))
            time.sleep(2)
            c = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    return 0, ''

suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
B_EMAIL = 'sbx_b%s@qq.com' % suffix
B_PASS = 'Sbxtest123!'
print('B_EMAIL=%s' % B_EMAIL)
st, b = req('POST', '/auth/v1/signup', {"email": B_EMAIL, "password": B_PASS}, 'signup-B', headers_extra={"apikey": ANON_KEY})
m = re.search(r'"id":"([0-9a-f-]{36})"', b or '')
B_ID = m.group(1) if m else ''
# DB 确认需要 mgmt token - 可能已过期, 用 service_role admin API 确认
print('B_ID=%s' % B_ID)
st2, b2 = req('POST', '/auth/v1/token?grant_type=password', {"email": B_EMAIL, "password": B_PASS}, 'grant-B', headers_extra={"apikey": ANON_KEY})
m2 = re.search(r'"access_token":"([^"]+)"', b2 or '')
B_TOKEN = m2.group(1) if m2 else ''
if not B_TOKEN:
    out.append('### 未确认用户, grant 失败, 尝试 admin verify (service_role)')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb67_retry.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
