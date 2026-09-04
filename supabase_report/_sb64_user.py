# -*- coding: utf-8 -*-
"""signup qq.com 域 + 若需确认则 DB/admin 确认 + password grant 拿 authenticated token"""
import http.client, ssl, json, time, os, sys, random, string
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
AUTH_HOST = '%s.supabase.co' % PROJECT_REF
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
        b = r.read(8000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:3000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

def q(sql, tag):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s]\n%s | %s' % (tag, r.status, b[:2000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))
        return 0, str(e)

suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
TEST_EMAIL = 'sbx_au%s@qq.com' % suffix
PASS = 'Sbxtest123!'
print('TEST_EMAIL=%s' % TEST_EMAIL)
# 1. signup
st, b = req('POST', '/auth/v1/signup', {"email": TEST_EMAIL, "password": PASS}, 'signup',
            host=AUTH_HOST, headers_extra={"apikey": ANON_KEY})
# 2. DB 看用户状态
st2, b2 = q("select id, email, email_confirmed_at, created_at, role from auth.users where email='%s';" % TEST_EMAIL, 'user-state')
# 3. 若未确认: DB 直接确认 (postgres 权限面测试)
if '"id"' in b2 or 'user' in b2.lower():
    q("update auth.users set email_confirmed_at = now() where email='%s' returning id;" % TEST_EMAIL, 'db-confirm')
# 4. password grant 拿 authenticated token
st3, b3 = req('POST', '/auth/v1/token?grant_type=password', {"email": TEST_EMAIL, "password": PASS},
              'pw-grant', host=AUTH_HOST, headers_extra={"apikey": ANON_KEY})

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb64_user.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
