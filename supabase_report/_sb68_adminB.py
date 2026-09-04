# -*- coding: utf-8 -*-
"""admin API 创建用户 B (email_confirm=true 不发信) + 保存 tokens"""
import http.client, ssl, json, time, os, sys, random, string, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
AUTH_HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', headers_extra=None, maxb=8000):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(AUTH_HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers_extra:
        h.update(headers_extra)
    if body_j:
        h["Content-Type"] = "application/json"
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        time.sleep(2)
        return 0, str(e)

suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
B_EMAIL = 'sbx_c%s@qq.com' % suffix
B_PASS = 'Sbxtest123!'
print('B_EMAIL=%s' % B_EMAIL)
# 1. admin create user (service_role, email_confirm=true)
st, b = req('POST', '/auth/v1/admin/users',
            {"email": B_EMAIL, "password": B_PASS, "email_confirm": True},
            'admin-create', headers_extra={"apikey": SR_KEY, "Authorization": "Bearer " + SR_KEY})
m = re.search(r'"id":"([0-9a-f-]{36})"', b or '')
B_ID = m.group(1) if m else ''
print('B_ID=%s' % B_ID)
# 2. password grant
st2, b2 = req('POST', '/auth/v1/token?grant_type=password',
              {"email": B_EMAIL, "password": B_PASS},
              'grant-B', headers_extra={"apikey": ANON_KEY})
m2 = re.search(r'"access_token":"([^"]+)"', b2 or '')
B_TOKEN = m2.group(1) if m2 else ''
print('B_TOKEN_LEN=%d' % len(B_TOKEN))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb_tokens.json'), 'w').write(json.dumps({
    'B_EMAIL': B_EMAIL, 'B_PASS': B_PASS, 'B_ID': B_ID, 'B_TOKEN': B_TOKEN}))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb68_adminB.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
